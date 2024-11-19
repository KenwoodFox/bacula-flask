from flask import Blueprint, render_template, jsonify
from .utils import (
    run_bconsole_command,
    parse_list_jobs,
    parse_show_jobs,
    merge_job_data,
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

    # Merge data
    jobs = merge_job_data(configured_jobs, recent_jobs)

    return render_template("index.html", jobs=jobs)


@bp.route("/job/<jobid>")
def job_details(jobid):
    command_output = run_bconsole_command(f"list jobid={jobid}")
    return jsonify({"jobid": jobid, "details": command_output})
