import subprocess
import shlex
from datetime import datetime


def human_readable_bytes(size_in_bytes: str):
    """
    Converts a size in bytes to a human-readable format (KB, MB, GB, TB).

    :param size_in_bytes: The size in bytes. (can be 123,456)
    :return: A string representing the size in a human-readable format.
    """

    try:
        # Remove commas and convert to a float
        size_in_bytes = float(str(size_in_bytes).replace(",", ""))
    except ValueError:
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


def run_bconsole_command(cmd, timeout=10):
    """
    Executes a Bacula bconsole command and returns its output.

    :param cmd: The bconsole command to execute.
    :param timeout: The maximum time in seconds to allow the command to run.
    :return: The cleaned stdout from the bconsole command.
    :raises: Exception on failure or timeout.
    """
    try:
        # Prepare the command to run bconsole with input piped
        process = subprocess.Popen(
            f"echo {cmd} | bconsole",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
        )

        # Collect stdout and stderr
        stdout, stderr = process.communicate(timeout=timeout)

        # Trim output to remove Bacula headers or connection messages
        if stdout:
            cleaned_stdout = (
                stdout.partition(b"\n" + bytes(cmd, "utf-8") + b"\n")[2]
                .decode("utf-8")
                .strip()
            )
            return cleaned_stdout

        return ""
    except subprocess.TimeoutExpired:
        return "Command timed out"
    except Exception as e:
        return str(e)


def parse_list_jobs(output):
    lines = output.splitlines()
    jobs = []
    for line in lines:
        if "|" in line and "jobid" not in line.lower():
            fields = [field.strip() for field in line.split("|") if field.strip()]
            jobs.append(
                {
                    "job_id": fields[0],
                    "name": fields[1],
                    "start_time": datetime.strptime(fields[2], "%Y-%m-%d %H:%M:%S"),
                    "type": fields[3],
                    "level": fields[4],
                    "job_files": fields[5],
                    "job_bytes": human_readable_bytes(fields[6]),
                    "job_status": fields[7],
                    "volumes": [],
                }
            )

    return sorted(jobs, key=lambda x: x["start_time"], reverse=True)


def parse_show_jobs(output):
    """
    Parses the output of `show jobs` to extract job details for display.

    :param output: Raw output from `show jobs`.
    :return: A list of dictionaries containing job configuration details.
    """
    jobs = []
    current_job = {}

    for line in output.splitlines():
        line = line.strip()

        # Start of a new job
        if line.startswith("Job:"):
            if current_job:  # Save the previous job if it exists
                jobs.append(current_job)
            current_job = {
                "name": None,
                "enabled": None,
                "client": None,
                "schedule": None,
                "fileset": None,
            }

            # Extract the job name
            parts = line.split()
            for part in parts:
                if part.startswith("name="):
                    current_job["name"] = part.split("=", 1)[1]
                if part.startswith("Enabled="):
                    current_job["enabled"] = bool(int(part.split("=", 1)[1]))

        # Extract Client
        if line.startswith("--> Client:"):
            parts = line.split()
            for part in parts:
                if part.startswith("Name="):
                    current_job["client"] = part.split("=", 1)[1]

        # Extract Schedule
        if line.startswith("--> Schedule:"):
            parts = line.split()
            for part in parts:
                if part.startswith("Name="):
                    current_job["schedule"] = part.split("=", 1)[1]

        # Extract FileSet
        if line.startswith("--> FileSet:"):
            parts = line.split()
            for part in parts:
                if part.startswith("name="):
                    current_job["fileset"] = part.split("=", 1)[1]

    # Add the last job
    if current_job:
        jobs.append(current_job)

    return jobs


def parse_volume_details(output):
    """
    Parses the output of a volume details command to extract relevant info.

    :param output: Raw output from the `list volume=<volume_id>` command.
    :return: A dictionary with volume details.
    """
    volume_info = {}
    for line in output.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            volume_info[key.strip()] = value.strip()
    return volume_info


def parse_jobtotals(output):
    """
    Parses the output of `list jobtotals` to extract total bytes for each job.

    :param output: Raw output from the `list jobtotals` command.
    :return: A dictionary mapping job names to their total job bytes and files.
    """

    job_totals = {}

    lines = output.splitlines()
    for line in lines:
        # Skip header or separator lines
        if line.startswith("+") or "jobs" in line.lower():
            continue

        # Parse job data
        fields = [field.strip() for field in line.split("|") if field.strip()]
        if len(fields) == 4:  # Ensure the line contains expected columns
            job_totals[fields[3]] = {
                "total_jobs": int(fields[0]),
                "total_files": int(fields[1].replace(",", "")),
                "total_bytes": int(fields[2].replace(",", "")),
            }

    return job_totals


def get_volumes_for_job(jobid):
    """
    Runs `list volumes jobid=<jobid>` to extract the volumes used by the job.

    :param jobid: The job ID to query.
    :return: A list of volumes used by the job.
    """

    command = f"list volumes jobid={jobid}"
    output = run_bconsole_command(command)

    # Parse the output
    volumes = []
    for line in output.splitlines():
        if "Volume(s):" in line:
            # Extract volumes after 'Volume(s):'
            volumes = [vol.strip() for vol in line.split(":")[1].split(",")]

    return volumes


def merge_job_data(configured_jobs, recent_jobs, job_totals={}):
    """
    Merges configured jobs with recent job details and sorts them by most recent run time.
    """

    for job in configured_jobs:
        for recent_job in recent_jobs:
            if job["name"] == recent_job["name"]:
                job.update(
                    {
                        "last_run_time": recent_job["start_time"],
                        "job_status": recent_job["job_status"],
                        "job_bytes": recent_job["job_bytes"],
                    }
                )

        # Add job totals
        if job["name"] in job_totals:
            job.update(
                {
                    "total_jobs": job_totals[job["name"]]["total_jobs"],
                    "total_files": job_totals[job["name"]]["total_files"],
                    "total_bytes": human_readable_bytes(
                        job_totals[job["name"]]["total_bytes"]
                    ),
                }
            )

    return sorted(
        configured_jobs,
        key=lambda x: x.get("last_run_time", datetime.min),
        reverse=True,
    )
