from .job_status_map import format_job_level, format_job_status, is_ok_job_status


def human_readable_bytes(size_in_bytes):
    try:
        size_in_bytes = float(str(size_in_bytes).replace(",", ""))
    except (TypeError, ValueError):
        return "Invalid size"

    if size_in_bytes == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB", "PB", "EB"]
    i = 0
    size = size_in_bytes

    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1

    return f"{size:.2f} {units[i]}"


def job_row_to_dict(row):
    purged = bool(row.get("purgedfiles"))
    volumes = [] if purged else row.get("volumes") or []
    if isinstance(volumes, str):
        volumes = [volumes]

    status = row.get("jobstatus") or ""
    level = row.get("level") if row.get("level") is not None else ""

    return {
        "job_id": row["jobid"],
        "name": row["name"],
        "start_time": row["starttime"],
        "type": row.get("type") or "",
        "level": level,
        "level_label": format_job_level(level),
        "job_files": row.get("jobfiles") or 0,
        "job_bytes": human_readable_bytes(row.get("jobbytes") or 0),
        "job_status": status,
        "job_status_label": format_job_status(status),
        "job_status_ok": is_ok_job_status(status),
        "purged": purged,
        "volumes": list(volumes),
    }
