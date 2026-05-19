import re

from .db import get_connection
from .utils import human_readable_bytes, job_row_to_dict


def _tape_flags(volumename: str, slot: str, inchanger) -> dict:
    """inchanger: 1 = in library, 0 = not (e.g. in drive or exported)."""
    vol = (volumename or "").upper()
    in_changer = None if inchanger is None else int(inchanger) == 1
    in_magazine = bool(slot and slot.isdigit() and int(slot) > 0)
    return {
        "in_changer": in_changer,
        "is_cleaning": vol.startswith("CLN"),
        "out_of_changer": in_changer is False and in_magazine,
    }


def _volstatus_class(volstatus: str | None) -> str:
    raw = (volstatus or "unknown").strip().lower()
    aliases = {
        "a": "append",
        "append": "append",
        "appended": "append",
        "f": "full",
        "fu": "full",
        "full": "full",
        "purged": "purged",
        "recycle": "recycle",
        "recycled": "recycle",
    }
    if raw in aliases:
        return aliases[raw]
    slug = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")
    return slug or "unknown"


def fetch_dashboard_jobs():
    """Job names with totals and most recent run, for the index page."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                WITH latest AS (
                    SELECT DISTINCT ON (name)
                        name, jobstatus, starttime
                    FROM job
                    ORDER BY name, starttime DESC
                ),
                totals AS (
                    SELECT
                        name,
                        COUNT(*)::int AS total_jobs,
                        COALESCE(SUM(jobfiles), 0)::bigint AS total_files,
                        COALESCE(SUM(jobbytes), 0)::bigint AS total_bytes
                    FROM job
                    GROUP BY name
                )
                SELECT
                    t.name,
                    t.total_jobs,
                    t.total_files,
                    t.total_bytes,
                    l.jobstatus,
                    l.starttime AS last_run_time
                FROM totals t
                LEFT JOIN latest l ON l.name = t.name
                ORDER BY l.starttime DESC NULLS LAST
                """
            )
            jobs = cur.fetchall()

            cur.execute("SELECT COALESCE(SUM(jobbytes), 0)::bigint AS total_bytes FROM job")
            summary = cur.fetchone()

    summary_bytes = summary["total_bytes"] or 0
    result = []
    for row in jobs:
        total_bytes = row["total_bytes"] or 0
        result.append(
            {
                "name": row["name"],
                "total_jobs": row["total_jobs"],
                "total_files": row["total_files"],
                "total_bytes": human_readable_bytes(total_bytes),
                "job_status": row["jobstatus"],
                "last_run_time": row["last_run_time"],
                "percentage": (total_bytes / summary_bytes * 100) if summary_bytes else 0,
            }
        )
    return result


def fetch_job_history(job_name, limit=1000):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    j.jobid,
                    j.name,
                    j.starttime,
                    j.type,
                    j.level,
                    j.jobfiles,
                    j.jobbytes,
                    j.jobstatus,
                    COALESCE(
                        array_agg(DISTINCT m.volumename)
                            FILTER (WHERE m.volumename IS NOT NULL),
                        '{}'
                    ) AS volumes
                FROM job j
                LEFT JOIN jobmedia jm ON jm.jobid = j.jobid
                LEFT JOIN media m ON m.mediaid = jm.mediaid
                WHERE j.name = %s
                GROUP BY
                    j.jobid, j.name, j.starttime, j.type, j.level,
                    j.jobfiles, j.jobbytes, j.jobstatus
                ORDER BY j.starttime DESC
                LIMIT %s
                """,
                (job_name, limit),
            )
            rows = cur.fetchall()

    return [job_row_to_dict(row) for row in rows]


def fetch_media_by_pool():
    """All volumes grouped by pool, ordered for shelf-style display."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    p.poolid,
                    p.name AS pool_name,
                    m.mediaid,
                    m.volumename,
                    m.slot,
                    m.volstatus,
                    m.volbytes,
                    m.lastwritten,
                    m.mediatype,
                    m.inchanger,
                    s.name AS storage_name
                FROM media m
                LEFT JOIN pool p ON p.poolid = m.poolid
                LEFT JOIN storage s ON s.storageid = m.storageid
                ORDER BY
                    p.name NULLS LAST,
                    NULLIF(
                        regexp_replace(COALESCE(m.slot::text, ''), '[^0-9]', '', 'g'),
                        ''
                    )::int,
                    m.slot::text,
                    m.volumename
                """
            )
            rows = cur.fetchall()

    pools = []
    pool_index = {}

    for row in rows:
        pool_key = row["poolid"]
        pool_name = row["pool_name"] or "Unassigned"

        if pool_key not in pool_index:
            pool_index[pool_key] = len(pools)
            pools.append(
                {
                    "pool_id": pool_key,
                    "name": pool_name,
                    "media": [],
                }
            )

        slot = "" if row["slot"] is None else str(row["slot"]).strip()
        pools[pool_index[pool_key]]["media"].append(
            {
                "mediaid": row["mediaid"],
                "volumename": row["volumename"],
                "slot": slot,
                "volstatus": row["volstatus"] or "",
                "status_class": _volstatus_class(row["volstatus"]),
                "volbytes": human_readable_bytes(row["volbytes"] or 0),
                "lastwritten": row["lastwritten"],
                "mediatype": row["mediatype"] or "",
                "storage_name": row["storage_name"] or "",
                **_tape_flags(row["volumename"], slot, row["inchanger"]),
            }
        )

    return pools


def fetch_media_tapes():
    """Flat media list for layout and drive stats (raw byte counts)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    m.mediaid,
                    m.volumename,
                    m.slot,
                    m.volstatus,
                    m.volbytes,
                    m.lastwritten,
                    m.mediatype,
                    m.endfile,
                    m.endblock,
                    m.volwrites,
                    m.volwritetime,
                    m.inchanger,
                    s.name AS storage_name,
                    p.name AS pool_name
                FROM media m
                LEFT JOIN pool p ON p.poolid = m.poolid
                LEFT JOIN storage s ON s.storageid = m.storageid
                """
            )
            rows = cur.fetchall()

    tapes = []
    for row in rows:
        slot = "" if row["slot"] is None else str(row["slot"]).strip()
        tapes.append(
            {
                "mediaid": row["mediaid"],
                "volumename": row["volumename"],
                "slot": slot,
                "volstatus": row["volstatus"] or "",
                "volbytes": row["volbytes"] or 0,
                "lastwritten": row["lastwritten"],
                "mediatype": row["mediatype"] or "",
                "endfile": row["endfile"],
                "endblock": row["endblock"],
                "volwrites": row["volwrites"],
                "volwritetime": row["volwritetime"],
                "storage_name": row["storage_name"] or "",
                "pool_name": row["pool_name"] or "",
                **_tape_flags(row["volumename"], slot, row["inchanger"]),
            }
        )
    return tapes


def fetch_volumes_for_labels(pool_name=None):
    """(volumename, pool_name) pairs for label generation."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            if pool_name:
                cur.execute(
                    """
                    SELECT m.volumename, p.name AS pool_name
                    FROM media m
                    LEFT JOIN pool p ON p.poolid = m.poolid
                    WHERE p.name = %s
                    ORDER BY
                        NULLIF(
                            regexp_replace(COALESCE(m.slot::text, ''), '[^0-9]', '', 'g'),
                            ''
                        )::int,
                        m.slot::text,
                        m.volumename
                    """,
                    (pool_name,),
                )
            else:
                cur.execute(
                    """
                    SELECT m.volumename, p.name AS pool_name
                    FROM media m
                    LEFT JOIN pool p ON p.poolid = m.poolid
                    ORDER BY p.name, m.volumename
                    """
                )
            return [(r["volumename"], r["pool_name"]) for r in cur.fetchall()]


def fetch_volume(volumename):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    m.mediaid,
                    m.volumename,
                    m.slot,
                    m.mediatype,
                    m.firstwritten,
                    m.lastwritten,
                    m.labeldate,
                    m.volstatus,
                    m.volfiles,
                    m.volbytes,
                    m.volerrors,
                    m.volwritetime,
                    m.volretention,
                    m.enabled,
                    m.inchanger,
                    p.name AS pool
                FROM media m
                LEFT JOIN pool p ON p.poolid = m.poolid
                WHERE m.volumename = %s
                """,
                (volumename,),
            )
            row = cur.fetchone()

    if not row:
        return None

    return {
        "Media ID": row["mediaid"],
        "Volume": row["volumename"],
        "Pool": row["pool"],
        "Slot": row["slot"],
        "In changer": "yes" if row["inchanger"] == 1 else "no",
        "Media Type": row["mediatype"],
        "First Written": row["firstwritten"],
        "Last Written": row["lastwritten"],
        "Label Date": row["labeldate"],
        "Status": row["volstatus"],
        "Files": row["volfiles"],
        "Bytes": human_readable_bytes(row["volbytes"] or 0),
        "Errors": row["volerrors"],
        "Write Time": row["volwritetime"],
        "Retention": row["volretention"],
        "Enabled": row["enabled"],
    }
