def process_job_history(job_history):
    """
    Processes job history to inject time skip rows for consecutive zero-byte jobs
    with significant gaps, overwriting skipped jobs with a summary element.
    """

    processed_history = []
    skip_start = None
    skip_end = None
    skipped_jobs = 0

    for i, job in enumerate(job_history):
        if job["job_bytes"] == "0 B":
            # Start a new skip range
            if skip_start is None:
                skip_start = job["start_time"]
            skip_end = job["start_time"]
            skipped_jobs += 1
        else:
            # Check if we need to add a skipped jobs chunk
            if skip_start and skipped_jobs > 1:
                processed_history.append(
                    {
                        "time_skip": True,
                        "skip_start": skip_start,
                        "skip_end": skip_end,
                        "skipped_jobs": skipped_jobs,
                    }
                )
                # Reset counters after appending the skip
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
