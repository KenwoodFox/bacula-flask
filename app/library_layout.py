"""2U library slot grid and drive bays."""

from .vault_config import all_drive_names

# storage slot number -> (row, col)
SLOT_POS = {
    8: (0, 0),
    9: (0, 1),
    10: (0, 2),
    11: (0, 3),
    4: (1, 0),
    5: (1, 1),
    6: (1, 2),
    7: (1, 3),
    1: (2, 1),
    2: (2, 2),
    3: (2, 3),
    23: (0, 4),
    22: (0, 5),
    21: (0, 6),
    20: (0, 7),
    19: (1, 4),
    18: (1, 5),
    17: (1, 6),
    16: (1, 7),
    15: (2, 4),
    14: (2, 5),
    13: (2, 6),
    12: (2, 7),
}


def _slot_text(slot):
    if slot is None or slot == "":
        return ""
    return str(slot).strip()


def tape_matches_drive_name(tape, drive_name):
    """Match drive name against media.volumename or media.slot."""
    key = drive_name.lower()
    vol = (tape.get("volumename") or "").lower()
    slot = _slot_text(tape.get("slot")).lower()
    return key in vol or vol == key or key in slot or slot == key


def tape_drive_name(tape):
    for name in all_drive_names():
        if tape_matches_drive_name(tape, name):
            return name
    return None


def build_drives(tapes, names):
    """Drive bays for a name list: [{name, tape}, ...]."""
    return [
        {
            "name": name,
            "tape": next(
                (t for t in tapes if tape_matches_drive_name(t, name)),
                None,
            ),
        }
        for name in names
        if name
    ]


def parse_slot(slot):
    """Return int magazine slot number, or None."""
    text = _slot_text(slot)
    if not text or not text.isdigit():
        return None
    return int(text)


def build_library_grid(tapes):
    """3×8 magazine grid."""
    by_slot = {}
    for tape in tapes:
        if tape_drive_name(tape):
            continue
        key = parse_slot(tape.get("slot"))
        if isinstance(key, int):
            by_slot[key] = tape

    grid = []
    for row in range(3):
        line = []
        for col in range(8):
            if row == 2 and col == 0:
                line.append(_cell(row, col, "io", label="I/O"))
                continue

            slot = _slot_at(row, col)
            if slot:
                line.append(
                    _cell(
                        row,
                        col,
                        "tape",
                        slot=slot,
                        label=str(slot),
                        tape=by_slot.get(slot),
                    )
                )
            else:
                line.append(_cell(row, col, "empty"))
        grid.append(line)

    return grid


def _slot_at(row, col):
    for num, (r, c) in SLOT_POS.items():
        if r == row and c == col:
            return num
    return None


def _cell(row, col, kind, slot=None, label="", tape=None, colspan=1):
    return {
        "row": row,
        "col": col,
        "colspan": colspan,
        "kind": kind,
        "slot": slot,
        "label": label,
        "tape": tape,
    }


def has_slotted_tapes(tapes):
    return any(parse_slot(t.get("slot")) is not None for t in tapes)
