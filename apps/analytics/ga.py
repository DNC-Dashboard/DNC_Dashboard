# apps/analytics/ga.py  (TEMP STUB FOR TESTING)
from typing import Dict, List
from datetime import date, timedelta

def get_summary(days: int = 7) -> Dict[str, int]:
    # return fake numbers so we can confirm the endpoint works
    return {"sessions": 123, "activeUsers": 45, "pageviews": 678, "days": days}

def get_timeseries(days: int = 7) -> Dict[str, List]:
    labels = []
    data = []
    today = date.today()
    for i in range(days):
        d = today - timedelta(days=days - 1 - i)
        labels.append(d.isoformat())
        data.append(10 + i)
    return {"labels": labels, "data": data}
