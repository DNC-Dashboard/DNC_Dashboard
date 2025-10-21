import os, math
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Metric, Dimension, RunReportRequest, RunRealtimeReportRequest
from google.api_core.exceptions import GoogleAPICallError, PermissionDenied, NotFound

PROPERTY_ID = os.getenv("GA4_PROPERTY_ID", "")
_client = None
def client():
    global _client
    if _client is None:
        _client = BetaAnalyticsDataClient()
    return _client

def _run(req):
    try:
        return client().run_report(req)
    except (GoogleAPICallError, PermissionDenied, NotFound) as e:
        return e  # bubble to view

def to_num(v):
    try: return int(float(v or 0))
    except: return 0

def fmt_duration(sec):
    try:
        sec = float(sec or 0)
        m, s = divmod(int(round(sec)), 60)
        h, m = divmod(m, 60)
        return f"{h:d}:{m:02d}:{s:02d}"
    except: return "0:00:00"

# ---- Overview KPIs (last 7 days) ----
def get_overview_7d():
    req = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[],
        metrics=[
            Metric(name="sessions"),
            Metric(name="activeUsers"),
            Metric(name="newUsers"),
            Metric(name="screenPageViews"),
            Metric(name="averageSessionDuration"),
            Metric(name="engagementRate"),
        ],
        date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
    )
    res = _run(req)
    if isinstance(res, Exception): return {"error": str(res)}
    m = res.rows[0].metric_values
    return {
        "sessions": to_num(m[0].value),
        "activeUsers": to_num(m[1].value),
        "newUsers": to_num(m[2].value),
        "pageviews": to_num(m[3].value),
        "avgSession": fmt_duration(m[4].value),
        "engagementRate": f"{round(float(m[5].value or 0)*100,1)}%",
    }

# ---- Time series (last 30 days) ----
def get_timeseries_30d():
    req = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[Dimension(name="date")],
        metrics=[Metric(name="sessions"), Metric(name="activeUsers")],
        date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
    )
    res = _run(req)
    if isinstance(res, Exception): return {"error": str(res)}
    rows = []
    for r in res.rows:
        d = r.dimension_values[0].value
        rows.append({
            "date": f"{d[0:4]}-{d[4:6]}-{d[6:8]}",
            "sessions": to_num(r.metric_values[0].value),
            "activeUsers": to_num(r.metric_values[1].value),
        })
    return rows

# ---- Top pages ----
def get_top_pages_7d(limit=10):
    req = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[Dimension(name="pageTitle"), Dimension(name="pagePathPlusQueryString")],
        metrics=[Metric(name="screenPageViews")],
        date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
        order_bys=[{"desc": True, "metric": {"metric_name": "screenPageViews"}}],
        limit=limit,
    )
    res = _run(req)
    if isinstance(res, Exception): return {"error": str(res)}
    out=[]
    for r in res.rows:
        out.append({
            "title": r.dimension_values[0].value or "(untitled)",
            "path": r.dimension_values[1].value or "/",
            "views": to_num(r.metric_values[0].value),
        })
    return out

# ---- Devices & Countries ----
def get_devices_7d():
    req = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[Dimension(name="deviceCategory")],
        metrics=[Metric(name="sessions")],
        date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
        order_bys=[{"desc": True, "metric": {"metric_name": "sessions"}}],
    )
    res = _run(req)
    if isinstance(res, Exception): return {"error": str(res)}
    return [{"device": r.dimension_values[0].value, "sessions": to_num(r.metric_values[0].value)} for r in res.rows]

def get_countries_7d(limit=10):
    req = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[Dimension(name="country")],
        metrics=[Metric(name="sessions")],
        date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
        order_bys=[{"desc": True, "metric": {"metric_name": "sessions"}}],
        limit=limit,
    )
    res = _run(req)
    if isinstance(res, Exception): return {"error": str(res)}
    return [{"country": r.dimension_values[0].value, "sessions": to_num(r.metric_values[0].value)} for r in res.rows]

# ---- Realtime ----
def get_realtime_active():
    req = RunRealtimeReportRequest(
        property=f"properties/{PROPERTY_ID}",
        metrics=[Metric(name="activeUsers")],
    )
    try:
        res = client().run_realtime_report(req)
        return to_num(res.rows[0].metric_values[0].value) if res.rows else 0
    except Exception as e:
        return {"error": str(e)}
