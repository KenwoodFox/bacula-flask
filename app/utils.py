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
    volumes = row.get("volumes") or []
    if isinstance(volumes, str):
        volumes = [volumes]

    return {
        "job_id": row["jobid"],
        "name": row["name"],
        "start_time": row["starttime"],
        "type": row.get("type") or "",
        "level": row.get("level") if row.get("level") is not None else "",
        "job_files": row.get("jobfiles") or 0,
        "job_bytes": human_readable_bytes(row.get("jobbytes") or 0),
        "job_status": row.get("jobstatus") or "",
        "volumes": list(volumes),
    }
