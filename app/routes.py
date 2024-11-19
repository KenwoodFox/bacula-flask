from flask import Blueprint, render_template, jsonify
from .utils import (
    run_bconsole_command,
    parse_list_jobs,
    parse_show_jobs,
    merge_job_data,
    parse_jobtotals,
)
from .process_job_history import process_job_history
from .time import format_timestamp

bp = Blueprint("main", __name__)

DAYS_TO_LIST = 360


@bp.route("/")
def index():
    # Get configured jobs
    show_jobs_output = run_bconsole_command("show jobs")
    configured_jobs = parse_show_jobs(show_jobs_output)

    # Get recent job run details
    list_jobs_output = run_bconsole_command("list jobs days=25")
    recent_jobs = parse_list_jobs(list_jobs_output)

    # Get job totals
    jobtotals_output = run_bconsole_command("list jobtotals")
    job_totals, summary_totals = parse_jobtotals(jobtotals_output)

    # Merge data
    jobs = merge_job_data(configured_jobs, recent_jobs, job_totals)

    # Format timestamps
    for job in jobs:
        try:
            job["formatted_time"] = format_timestamp(job["last_run_time"])
        except KeyError:
            job["formatted_time"] = "N/A"

    # For now, set a static percentage for testing
    for job in jobs:
        try:
            # print(job_totals[job["name"]])
            jobdata = job_totals[job["name"]]
            job["percentage"] = (
                jobdata["total_bytes"] / summary_totals["total_bytes"]
            ) * 100
        except KeyError:
            job["percentage"] = 0

    return render_template("index.html", jobs=jobs)


@bp.route("/job/<job_name>")
def job_details(job_name):
    """
    Displays the history of a specific job, including volumes used and time skips.
    """
    job_output = run_bconsole_command(f"list job={job_name}")
    job_history = parse_list_jobs(job_output)

    # Process the job history to include time skips
    # job_history = process_job_history(job_history) # Fix me later

    return render_template(
        "job_details.html", job_name=job_name, job_history=job_history
    )


@bp.route("/volume/<volume_id>")
def volume_details(volume_id):
    """
    Displays details for a specific volume.
    """
    # Run a command to get volume details (e.g., `list volumes volume=<volume_id>`)
    command_output = run_bconsole_command(f"list volume={volume_id}")
    volume_info = parse_volume_details(command_output)

    return render_template(
        "volume_details.html", volume_id=volume_id, volume_info=volume_info
    )
