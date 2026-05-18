"""
Vault drive names — edit this file when labels change.

Volumes match if the drive name appears in media.volumename or media.slot.

Optional .env overrides (comma-separated lists):
  VAULT_AUTOCHANGER_DRIVES
  VAULT_STANDALONE_DRIVES
  VAULT_LIBRARY_DRIVE_NAME   (legacy: single autochanger drive)
"""

import os


def _parse_names(raw):
    return [n.strip() for n in raw.split(",") if n.strip()]


# In-library autochanger (row above the slot grid)
AUTOCHANGER_DRIVES = [
    "LTO-4-1",
]

# Stand-alone drives (section above the library)
STANDALONE_DRIVES = [
    "LTO-4-9",
]

if raw := os.getenv("VAULT_AUTOCHANGER_DRIVES"):
    AUTOCHANGER_DRIVES = _parse_names(raw)
elif name := os.getenv("VAULT_LIBRARY_DRIVE_NAME"):
    AUTOCHANGER_DRIVES = [name]

if raw := os.getenv("VAULT_STANDALONE_DRIVES"):
    STANDALONE_DRIVES = _parse_names(raw)


def all_drive_names():
    """Every configured drive (autochanger first, then stand-alone)."""
    names = []
    for name in [*AUTOCHANGER_DRIVES, *STANDALONE_DRIVES]:
        if name and name not in names:
            names.append(name)
    return names
