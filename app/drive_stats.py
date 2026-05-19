"""Live-ish drive stats from the catalog (polled by the vault UI)."""

import time

from .catalog import fetch_media_tapes
from .library_layout import tape_for_drive
from .utils import human_readable_bytes

_prev_bytes: dict[str, tuple[float, int]] = {}


def _format_rate(bytes_per_sec: float | None) -> str | None:
    if bytes_per_sec is None or bytes_per_sec <= 0:
        return None
    return f"{human_readable_bytes(bytes_per_sec)}/s"


def _format_duration(usec: int | None) -> str | None:
    if not usec:
        return None
    sec = usec / 1_000_000
    if sec < 120:
        return f"{sec:.0f}s write time"
    if sec < 7200:
        return f"{sec / 60:.1f}m write time"
    return f"{sec / 3600:.1f}h write time"


def fetch_drive_stats(drive_name: str) -> dict:
    tape = tape_for_drive(fetch_media_tapes(), drive_name)
    if not tape:
        return {"drive": drive_name, "mounted": False}

    volbytes = int(tape.get("volbytes") or 0)
    now = time.time()
    rate = None
    prev = _prev_bytes.get(drive_name)
    if prev:
        dt = now - prev[0]
        if dt >= 1:
            delta = volbytes - prev[1]
            if delta >= 0:
                rate = delta / dt
    _prev_bytes[drive_name] = (now, volbytes)

    endfile = tape.get("endfile")
    endblock = tape.get("endblock")
    lines = [f"file {endfile} · blk {endblock}"]
    size_bit = human_readable_bytes(volbytes)
    rate_s = _format_rate(rate)
    if rate_s:
        lines.append(f"{size_bit} · {rate_s}")
    else:
        lines.append(size_bit)
    if wt := _format_duration(tape.get("volwritetime")):
        lines.append(wt)

    return {
        "drive": drive_name,
        "mounted": True,
        "volume": tape["volumename"],
        "pool": tape.get("pool_name") or "—",
        "mediatype": tape.get("mediatype") or "—",
        "file": endfile,
        "block": endblock,
        "bytes": size_bit,
        "rate": rate_s,
        "lines": lines,
    }
