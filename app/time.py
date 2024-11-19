from datetime import datetime, timedelta


def format_timestamp(timestamp):
    """
    Formats a datetime object into a human-readable string.

    :param timestamp: A datetime object.
    :return: A formatted string like "Sunday, March 15th (24 days ago)" or "Today, 8 Hours ago".
    """
    now = datetime.now()
    delta = now - timestamp

    # Format the date part
    day_suffix = lambda d: (
        "th" if 11 <= d <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(d % 10, "th")
    )
    formatted_date = timestamp.strftime(
        f"%A, %B %-d{day_suffix(timestamp.day)} %I:%M %p"
    )

    # Calculate relative time
    if delta.days == 0:
        # Same day: Calculate hours ago
        hours_ago = delta.seconds // 3600
        if hours_ago > 0:
            return f"Today, {hours_ago} Hours ago"
        else:
            minutes_ago = delta.seconds // 60
            return f"Today, {minutes_ago} Minutes ago"
    elif delta.days == 1:
        return f"Yesterday"
    else:
        # Multiple days ago
        return f"{formatted_date} ({delta.days} days ago)"
