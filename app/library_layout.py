"""2U library slot grid — drive on top, magazines below."""

import re

# slot number -> (row, col)   row 0 = drive, rows 1-3 = magazines
SLOT_POS = {
    8: (1, 0),
    9: (1, 1),
    10: (1, 2),
    11: (1, 3),
    4: (2, 0),
    5: (2, 1),
    6: (2, 2),
    7: (2, 3),
    1: (3, 1),
    2: (3, 2),
    3: (3, 3),
    23: (1, 4),
    22: (1, 5),
    21: (1, 6),
    20: (1, 7),
    19: (2, 4),
    18: (2, 5),
    17: (2, 6),
    16: (2, 7),
    15: (3, 4),
    14: (3, 5),
    13: (3, 6),
    12: (3, 7),
}


def parse_slot(slot):
    """Return int slot, 'drive', or None."""
    if slot is None or slot == "":
        return None
    text = str(slot).strip()
    if "drive" in text.lower():
        return "drive"
    digits = re.sub(r"[^0-9]", "", text)
    if digits:
        return int(digits)
    return None


def build_library_grid(tapes):
    """4×8 grid: drive row on top, then left + right magazines."""
    by_slot = {}
    drive_tape = None
    for tape in tapes:
        key = parse_slot(tape.get("slot"))
        if key == "drive":
            drive_tape = tape
        elif isinstance(key, int):
            by_slot[key] = tape

    grid = []

    # row 0 — drive ~1.5 slots wide, centered (spans 2 cols, styled at 75% width)
    grid.append([_cell(0, 3, "drive", label="Drive", tape=drive_tape, colspan=2)])

    for row in range(1, 4):
        line = []
        for col in range(8):
            if row == 3 and col == 0:
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
