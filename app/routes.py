from flask import Blueprint, render_template, jsonify
from .utils import run_bconsole_command, parse_job_list

bp = Blueprint("main", __name__)

@bp.route("/")
def index():
    command_output = run_bconsole_command("list jobs")
    jobs = parse_job_list(command_output)
    return render_template("index.html", jobs=jobs)

@bp.route("/job/<jobid>")
def job_details(jobid):
    command_output = run_bconsole_command(f"list jobid={jobid}")
    return jsonify({"jobid": jobid, "details": command_output})
