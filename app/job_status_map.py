"""
Bacula job level, type, and status codes.

Source: https://www.bacula.org/15.0.x-manuals/en/main/Job_status_Error_codes.html
"""

# Job levels
JOB_LEVEL = {
    "F": "Full backup",
    "I": "Incremental",
    "D": "Differential",
    "S": "Since",
    "f": "Virtual full backup",
    "C": "Verify from Catalog",
    "V": "Verify: Init database",
    "O": "Verify volume to Catalog entries",
    "d": "Verify disk attributes to Catalog",
    "A": "Verify data on volume",
    "B": "Base level job",
    "--": "None",
}

# Job types
JOB_TYPE = {
    "B": "Backup Job",
    "V": "Verify Job",
    "R": "Restore Job",
    "D": "Admin job",
    "C": "Copy of a Job",
    "c": "Copy Job",
    "M": "Migrated backup job",
    "g": "Migration Job",
    "A": "Archive Job",
    "S": "Scan Job",
    "U": "Console program",
    "I": "Internal system job",
}

# Job status (single character in catalog jobstatus column)
JOB_STATUS = {
    "A": "Job canceled by user",
    "B": "Job blocked",
    "C": "Job created but not yet running",
    "D": "Verify differences",
    "E": "Job terminated in error",
    "F": "Job waiting on File daemon",
    "I": "Incomplete Job",
    "L": "Committing data (last despool)",
    "M": "Job waiting for Mount",
    "R": "Job running",
    "S": "Job waiting on the Storage daemon",
    "T": "Job terminated normally",
    "W": "Job terminated normally with warnings",
    "a": "SD despooling attributes",
    "c": "Waiting for Client resource",
    "d": "Waiting for maximum jobs",
    "e": "Non-fatal error",
    "f": "Fatal error",
    "i": "Doing batch insert file records",
    "j": "Waiting for job resource",
    "l": "Doing data despooling",
    "m": "Waiting for new media",
    "p": "Waiting for higher priority jobs to finish",
    "q": "Queued waiting for device",
    "s": "Waiting for storage resource",
    "t": "Waiting for start time",
}

_OK_STATUS = frozenset({"T", "W"})


def format_job_status(code: str | None) -> str:
    raw = (code or "").strip()
    if not raw:
        return "Unknown"
    return JOB_STATUS.get(raw, raw)


def format_job_level(code: str | None) -> str:
    raw = (code or "").strip()
    if not raw:
        return "Unknown"
    return JOB_LEVEL.get(raw, raw)


def format_job_type(code: str | None) -> str:
    raw = (code or "").strip()
    if not raw:
        return "Unknown"
    return JOB_TYPE.get(raw, raw)


def is_ok_job_status(code: str | None) -> bool:
    return (code or "").strip() in _OK_STATUS
