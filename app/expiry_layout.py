"""Group catalog media by retention expiry for off-site planning."""

from datetime import datetime, timedelta


def volume_expires_at(lastwritten, volretention, pool_volretention):
    if not lastwritten:
        return None
    sec = int(volretention or 0) or int(pool_volretention or 0)
    if sec <= 0:
        return None
    return lastwritten + timedelta(seconds=sec)


def _volstatus_key(tape) -> str:
    return (tape.get("volstatus") or "").strip().lower()


def _is_full_tape(tape) -> bool:
    return _volstatus_key(tape) == "full"


def _is_archived_tape(tape) -> bool:
    status = _volstatus_key(tape)
    if status in {"archive", "read-only"}:
        return True
    return (tape.get("status_class") or "") in {"archive", "read-only"}


def enrich_tape_expiry(tape, *, volretention=0, pool_volretention=0):
    """Add expires_at / expire_year / expires_label on a tape dict."""
    expires = volume_expires_at(
        tape.get("lastwritten"),
        volretention,
        pool_volretention,
    )
    tape["expires_at"] = expires
    tape["expire_year"] = expires.year if expires else None
    tape["expires_label"] = expires.strftime("%Y-%m-%d") if expires else ""
    return tape


def _apply_relocate_hints(tapes):
    """In-changer tapes expiring after the earliest year → move with that cohort."""
    years = [
        t["expire_year"]
        for t in tapes
        if t.get("in_changer")
        and t.get("expire_year")
        and not t.get("is_cleaning")
    ]
    if not years:
        return
    min_year = min(years)
    for tape in tapes:
        year = tape.get("expire_year")
        if (
            tape.get("in_changer")
            and year
            and year > min_year
            and not tape.get("is_cleaning")
        ):
            tape["relocate_hint"] = year


def _sort_by_expiry_then_name(tapes):
    dated = [t for t in tapes if t.get("expires_at")]
    unknown = [t for t in tapes if not t.get("expires_at")]
    dated.sort(key=lambda t: t["expires_at"])
    unknown.sort(key=lambda t: (t.get("volumename") or "").lower())
    return dated + unknown


def build_expiry_groups(tapes):
    """Full volumes by expiry year; Archive / Read-Only in a bottom section."""
    full_tapes = [t for t in tapes if _is_full_tape(t)]
    archived_tapes = [t for t in tapes if _is_archived_tape(t)]

    dated = [t for t in full_tapes if t.get("expires_at")]
    unknown = [t for t in full_tapes if not t.get("expires_at")]

    dated.sort(key=lambda t: t["expires_at"])
    unknown.sort(key=lambda t: (t.get("volumename") or "").lower())

    by_year = {}
    for tape in dated:
        by_year.setdefault(tape["expire_year"], []).append(tape)

    groups = []
    for year in sorted(by_year):
        groups.append(
            {
                "year": year,
                "label": str(year),
                "tapes": by_year[year],
            }
        )
    if unknown:
        groups.append({"year": None, "label": "Unknown", "tapes": unknown})

    _apply_relocate_hints(full_tapes)

    return {
        "expiry_groups": groups,
        "archived_tapes": _sort_by_expiry_then_name(archived_tapes),
    }
