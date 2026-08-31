"""Hide retired / archived job names from the main dashboard."""

from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path

import yaml

_CONFIG_PATH = Path(__file__).resolve().parent / "hidden_jobs.yaml"


@lru_cache(maxsize=1)
def _load_config():
    if not _CONFIG_PATH.is_file():
        return {"jobs": set(), "hide_after_days": 7}
    with _CONFIG_PATH.open() as fh:
        data = yaml.safe_load(fh) or {}
    jobs = {str(name).strip() for name in (data.get("jobs") or []) if str(name).strip()}
    days = int(data.get("hide_after_days") or 7)
    return {"jobs": jobs, "hide_after_days": max(days, 0)}


def should_hide_job(name: str, last_run_time) -> bool:
    """True if name is listed and last run is older than hide_after_days (or never)."""
    cfg = _load_config()
    if name not in cfg["jobs"]:
        return False
    if last_run_time is None:
        return True
    cutoff = datetime.now() - timedelta(days=cfg["hide_after_days"])
    return last_run_time < cutoff


def filter_dashboard_jobs(jobs: list) -> list:
    return [j for j in jobs if not should_hide_job(j.get("name") or "", j.get("last_run_time"))]
