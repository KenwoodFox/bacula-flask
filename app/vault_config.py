"""
Vault drive names — edit this file when labels change.

Drive bay names match volumename/slot text, or storage.name to pick the
mounted volume (also older names like Drive-9-LTO-3 when config says
Drive-9-LTO-4 — same Drive-N bay). Only that volume is hidden from the grid.

Optional .env overrides (comma-separated lists):
  VAULT_AUTOCHANGER_DRIVES
  VAULT_STANDALONE_DRIVES
  VAULT_LIBRARY_DRIVE_NAME   (legacy: single autochanger drive)
"""

import os


def _parse_names(raw):
    return [n.strip() for n in raw.split(",") if n.strip()]


AUTOCHANGER_DRIVES = ["Drive-1-LTO"]
STANDALONE_DRIVES = ["Drive-9-LTO"]

if raw := os.getenv("VAULT_AUTOCHANGER_DRIVES"):
    AUTOCHANGER_DRIVES = _parse_names(raw)
elif name := os.getenv("VAULT_LIBRARY_DRIVE_NAME"):
    AUTOCHANGER_DRIVES = [name]

if raw := os.getenv("VAULT_STANDALONE_DRIVES"):
    STANDALONE_DRIVES = _parse_names(raw)


def all_drive_names():
    names = []
    for name in [*AUTOCHANGER_DRIVES, *STANDALONE_DRIVES]:
        if name and name not in names:
            names.append(name)
    return names
