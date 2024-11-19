def process_job_history(job_history):
    """
    Processes job history to inject time skip rows for consecutive zero-byte jobs
    with significant gaps, overwriting skipped jobs with a summary element.
    """

    processed_history = []
    skip_start = None
    skip_end = None
    skipped_jobs = 0
    stacked_jobs = []  # Temporary spot for jobs we're iterating over

    for i, job in enumerate(job_history):
        if job["job_bytes"] == "0 B" and job["job_status"] == "T":
            # Start a new skip range
            if skip_start is None:
                skip_start = job["start_time"]
            skip_end = job["start_time"]
            skipped_jobs += 1
            stacked_jobs.append(job)
        else:
            # Check if we need to add a skipped jobs chunk
            if skip_start and skipped_jobs > 3:
                processed_history.append(
                    {
                        "time_skip": True,
                        "skip_start": skip_start,
                        "skip_end": skip_end,
                        "skipped_jobs": skipped_jobs,
                    }
                )

                # Reset counters after appending the skip or the block not being big enough
                skip_start = None
                skip_end = None
                skipped_jobs = 0

            else:
                # Skip wasn't big enough,
                for job in stacked_jobs:
                    processed_history.append(job)
                stacked_jobs = []
                skip_start = None
                skip_end = None
                skipped_jobs = 0

            # Add the current non-zero-byte job
            processed_history.append(job)

    # Handle a trailing skip if the last jobs were zero-byte jobs
    if skip_start and skipped_jobs > 1:
        processed_history.append(
            {
                "time_skip": True,
                "skip_start": skip_start,
                "skip_end": skip_end,
                "skipped_jobs": skipped_jobs,
            }
        )

    return processed_history
