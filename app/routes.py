from flask import Blueprint, render_template, jsonify
from .utils import (
    run_bconsole_command,
    parse_list_jobs,
    parse_show_jobs,
    merge_job_data,
    parse_jobtotals,
)

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    # Get configured jobs
    show_jobs_output = run_bconsole_command("show jobs")
    configured_jobs = parse_show_jobs(show_jobs_output)

    # Get recent job run details
    list_jobs_output = run_bconsole_command("list jobs days=10")
    recent_jobs = parse_list_jobs(list_jobs_output)

    # Get job totals
    jobtotals_output = run_bconsole_command("list jobtotals")
    job_totals = parse_jobtotals(jobtotals_output)

    print(job_totals)

    # Merge data
    jobs = merge_job_data(configured_jobs, recent_jobs, job_totals)

    return render_template("index.html", jobs=jobs)


@bp.route("/job/<job_name>")
def job_details(job_name):
    """
    Displays the history of a specific job, including volumes used.
    """

    # Run the `list jobs job=<name>` command
    command_output = run_bconsole_command(f"list jobs job={job_name}")
    job_history = parse_list_jobs(command_output)

    print(job_history)

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
