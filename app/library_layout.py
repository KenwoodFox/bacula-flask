"""2U library slot grid and drive bays."""

import re

from .vault_config import (
    AUTOCHANGER_DRIVES,
    STANDALONE_DRIVES,
    all_drive_names,
)

IO_SLOT = 24

SLOT_POS = {
    8: (0, 0), 9: (0, 1), 10: (0, 2), 11: (0, 3),
    4: (1, 0), 5: (1, 1), 6: (1, 2), 7: (1, 3),
    1: (2, 1), 2: (2, 2), 3: (2, 3),
    23: (0, 4), 22: (0, 5), 21: (0, 6), 20: (0, 7),
    19: (1, 4), 18: (1, 5), 17: (1, 6), 16: (1, 7),
    15: (2, 4), 14: (2, 5), 13: (2, 6), 12: (2, 7),
    24: (2, 0),
}


def _slot_text(slot):
    if slot is None or slot == "":
        return ""
    return str(slot).strip()


def _drive_bay_prefix(name):
    """Drive-9-LTO-4 -> drive-9 (same bay after LTO generation renames)."""
    m = re.match(r"^(drive-\d+)", (name or "").lower())
    return m.group(1) if m else ""


def _storage_matches_drive(storage_name, drive_name):
    storage = (storage_name or "").lower()
    key = drive_name.lower()
    if not storage:
        return False
    if key == storage or key in storage:
        return True
    bay = _drive_bay_prefix(key)
    return bool(bay and bay == _drive_bay_prefix(storage))


def _changer_storage_for_drive(drive_name):
    """TL2000-Drive-0 -> TL2000 (changer Storage, not the drive device)."""
    m = re.match(r"^(.+)-drive-\d+$", (drive_name or "").lower())
    return m.group(1) if m else None


def _tape_in_changer_drive(tape, drive_name):
    """Mounted in a changer drive; catalog slot is often stale."""
    changer = _changer_storage_for_drive(drive_name)
    if not changer or (tape.get("storage_name") or "").lower() != changer:
        return False
    slot = _slot_text(tape.get("slot"))
    status = (tape.get("volstatus") or "").lower()
    if slot == "0":
        return True
    # I/O port: only treat as drive while actively appending (else show in grid)
    if slot == str(IO_SLOT):
        return status == "append"
    if tape.get("in_changer") is False:
        return True
    # Magazine slot + Append + no lastwritten yet → writing in drive, slot not updated
    if status == "append" and tape.get("lastwritten") is None:
        return True
    return False


def _drive_match(tape, name, *, storage=False):
    key = name.lower()
    vol = (tape.get("volumename") or "").lower()
    slot = _slot_text(tape.get("slot")).lower()
    if key in vol or vol == key or key in slot or slot == key:
        return True
    if storage:
        return _storage_matches_drive(tape.get("storage_name"), name)
    return False


def _drive_match_rank(tape):
    slot = _slot_text(tape.get("slot"))
    if slot == str(IO_SLOT):
        return 0
    if slot == "0":
        return 1
    if tape.get("in_changer") is False:
        return 2
    return 3


def tape_for_drive(tapes, name):
    if _changer_storage_for_drive(name):
        matches = [
            t
            for t in tapes
            if _tape_in_changer_drive(t, name)
            or _storage_matches_drive(t.get("storage_name"), name)
        ]
    else:
        matches = [t for t in tapes if _drive_match(t, name, storage=True)]
    if not matches:
        return None
    if len(matches) == 1:
        return matches[0]

    def sort_key(tape):
        append = 0 if (tape.get("volstatus") or "").lower() == "append" else 1
        written = tape.get("lastwritten")
        ts = -(written.timestamp() if written else 0)
        return (_drive_match_rank(tape), append, ts)

    return min(matches, key=sort_key)


def drive_tape_mediaids(tapes):
    ids = set()
    for name in all_drive_names():
        tape = tape_for_drive(tapes, name)
        if tape and tape.get("mediaid") is not None:
            ids.add(tape["mediaid"])
    return ids


def build_drives(tapes, names):
    return [{"name": n, "tape": tape_for_drive(tapes, n)} for n in names if n]


def parse_slot(slot):
    text = _slot_text(slot)
    if not text or not text.isdigit():
        return None
    num = int(text)
    return None if num == 0 else num


def build_library_grid(tapes):
    by_slot = {}
    for tape in tapes:
        key = parse_slot(tape.get("slot"))
        if key is not None:
            by_slot[key] = tape

    grid = []
    for row in range(3):
        line = []
        for col in range(8):
            slot = _slot_at(row, col)
            if slot == IO_SLOT:
                tape = by_slot.get(IO_SLOT)
                if tape:
                    line.append(
                        _cell(row, col, "tape", slot=IO_SLOT, label="I/O", tape=tape)
                    )
                else:
                    line.append(_cell(row, col, "io", label="I/O"))
            elif slot:
                line.append(
                    _cell(row, col, "tape", slot=slot, label=str(slot), tape=by_slot.get(slot))
                )
            else:
                line.append(_cell(row, col, "empty"))
        grid.append(line)
    return grid


def has_slotted_tapes(tapes):
    return any(parse_slot(t.get("slot")) is not None for t in tapes)


def build_vault_layout(tapes):
    """Sections, magazine grid, and drive-bay exclusions for /vault."""
    in_drive = drive_tape_mediaids(tapes)
    library_tapes = [t for t in tapes if t["mediaid"] not in in_drive]
    sections = []

    if STANDALONE_DRIVES:
        sections.append(
            {"title": "Standalone", "drives": build_drives(tapes, STANDALONE_DRIVES)}
        )

    if has_slotted_tapes(tapes) or AUTOCHANGER_DRIVES:
        sections.append(
            {
                "title": "Autochanger",
                "drives": build_drives(tapes, AUTOCHANGER_DRIVES),
                "library_grid": build_library_grid(library_tapes),
            }
        )

    return {"vault_sections": sections}


def _slot_at(row, col):
    for num, (r, c) in SLOT_POS.items():
        if r == row and c == col:
            return num
    return None


def _cell(row, col, kind, slot=None, label="", tape=None, colspan=1):
    return {
        "row": row, "col": col, "colspan": colspan, "kind": kind,
        "slot": slot, "label": label, "tape": tape,
    }
