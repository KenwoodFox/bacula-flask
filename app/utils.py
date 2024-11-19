import subprocess
import shlex


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
                    "jobid": fields[0],
                    "name": fields[1],
                    "starttime": fields[2],
                    "type": fields[3],
                    "level": fields[4],
                    "jobfiles": fields[5],
                    "jobbytes": fields[6],
                    "jobstatus": fields[7],
                }
            )
    return jobs


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


def merge_job_data(configured_jobs, recent_jobs):
    """
    Merges configured jobs with recent job details.
    """
    for job in configured_jobs:
        for recent_job in recent_jobs:
            if job["name"] == recent_job["name"]:
                job.update(
                    {
                        "last_run_time": recent_job["starttime"],
                        "job_status": recent_job["jobstatus"],
                        "job_bytes": recent_job["jobbytes"],
                    }
                )
    return configured_jobs
