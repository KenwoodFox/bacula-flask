import subprocess
import shlex

def run_bconsole_command(command, timeout=10):
    try:
        process = subprocess.run(
            shlex.split(f"bconsole -c '{command}'"),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout
        )
        return process.stdout.strip()
    except subprocess.TimeoutExpired:
        return "Command timed out"
    except Exception as e:
        return str(e)

def parse_job_list(output):
    lines = output.splitlines()
    jobs = []
    for line in lines:
        if "|" in line and "jobid" not in line.lower():
            fields = [field.strip() for field in line.split("|") if field.strip()]
            jobs.append({
                "jobid": fields[0],
                "name": fields[1],
                "starttime": fields[2],
                "type": fields[3],
                "level": fields[4],
                "jobfiles": fields[5],
                "jobbytes": fields[6],
                "jobstatus": fields[7],
            })
    return jobs
