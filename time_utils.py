from datetime import datetime, timedelta


def to_minutes(hour, minute):
    if hour < 6:
        hour += 24
    return hour * 60 + minute


def to_time(minutes):
    hour = (minutes // 60) % 24
    minute = minutes % 60
    return f"{hour:02d}:{minute:02d}"


def now_minutes_japan():
    now = datetime.utcnow() + timedelta(hours=9)
    return to_minutes(now.hour, now.minute)