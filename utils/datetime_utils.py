"""Datetime utilities for the Dashboard UI."""

from datetime import datetime
from zoneinfo import ZoneInfo

def format_timestamp(value, timezone="Asia/Colombo"):
    """Format an ISO timestamp into a local timezone string."""
    if not value or str(value).upper() in ("NOT_AVAILABLE", "NOT_EXECUTED", "UNKNOWN"):
        return "N/A"

    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))

        local_dt = dt.astimezone(ZoneInfo(timezone))
        return local_dt.strftime("%d %b %Y %H:%M:%S")
    except (ValueError, TypeError):
        return str(value)

def calculate_duration(start, end):
    """Calculate the duration between two ISO timestamps."""
    if not start or not end or str(start).upper() == "NOT_AVAILABLE" or str(end).upper() == "NOT_AVAILABLE":
        return "N/A"
        
    try:
        start_dt = datetime.fromisoformat(str(start).replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(str(end).replace("Z", "+00:00"))
        
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=ZoneInfo("UTC"))
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=ZoneInfo("UTC"))
            
        delta = end_dt - start_dt
        seconds = int(delta.total_seconds())
        
        if seconds < 0:
            return "N/A"
            
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
            
    except (ValueError, TypeError):
        return "N/A"
