from flask import Blueprint, abort, render_template

from .catalog import fetch_dashboard_jobs, fetch_job_history, fetch_volume
from .time import format_timestamp

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    jobs = fetch_dashboard_jobs()

    for job in jobs:
        if job.get("last_run_time"):
            job["formatted_time"] = format_timestamp(job["last_run_time"])
        else:
            job["formatted_time"] = "N/A"

    return render_template("index.html", jobs=jobs)


@bp.route("/job/<job_name>")
def job_details(job_name):
    job_history = fetch_job_history(job_name)
    return render_template(
        "job_details.html", job_name=job_name, job_history=job_history
    )


@bp.route("/volume/<volume_id>")
def volume_details(volume_id):
    volume_info = fetch_volume(volume_id)
    if volume_info is None:
        abort(404)

    return render_template(
        "volume_details.html", volume_id=volume_id, volume_info=volume_info
    )
