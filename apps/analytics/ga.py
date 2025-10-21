# apps/pages/ga.py
import os
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Metric, Dimension, RunReportRequest, RunRealtimeReportRequest
from google.api_core.exceptions import GoogleAPICallError

PROPERTY_ID = os.getenv("GA4_PROPERTY_ID", "")
_client = None

def _client():
    global _client
    if _client is None:
        _client = BetaAnalyticsDataClient()
    return _client

def _fmt_secs_to_hms(sec):
    try:
        sec = float(sec or 0)
        m, s = divmod(int(round(sec)), 60)
        h, m = divmod(m, 60)
        return f"{h:d}:{m:02d}:{s:02d}"
    except:
        return "0:00:00"

def get_timeseries_30d():
    req = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[Dimension(name="date")],
        metrics=[Metric(name="sessions"), Metric(name="activeUsers")],
        date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
    )
    res = _client().run_report(req)
    out = []
    for r in res.rows:
        d = r.dimension_values[0].value
        out.append({
            "date": f"{d[0:4]}-{d[4:6]}-{d[6:8]}",
            "sessions": int(float(r.metric_values[0].value or 0)),
            "activeUsers": int(float(r.metric_values[1].value or 0)),
        })
    return out

def get_devices_7d():
    req = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[Dimension(name="deviceCategory")],
        metrics=[Metric(name="sessions")],
        date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
    )
    res = _client().run_report(req)
    return [{"label": r.dimension_values[0].value, "value": int(float(r.metric_values[0].value or 0))} for r in res.rows]

def get_countries_7d(limit=10):
    req = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[Dimension(name="country")],
        metrics=[Metric(name="sessions")],
        date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
        limit=limit,
        order_bys=[{"desc": True, "metric": {"metric_name": "sessions"}}],
    )
    res = _client().run_report(req)
    return [{"label": r.dimension_values[0].value, "value": int(float(r.metric_values[0].value or 0))} for r in res.rows]

def get_top_pages_7d(limit=10):
    req = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[Dimension(name="pageTitle"), Dimension(name="pagePathPlusQueryString")],
        metrics=[Metric(name="screenPageViews")],
        date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
        limit=limit,
        order_bys=[{"desc": True, "metric": {"metric_name": "screenPageViews"}}],
    )
    res = _client().run_report(req)
    return [{
        "title": r.dimension_values[0].value or "(untitled)",
        "path": r.dimension_values[1].value or "/",
        "views": int(float(r.metric_values[0].value or 0))
    } for r in res.rows]

def get_sources_7d(limit=10):
    req = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[Dimension(name="sessionSource"), Dimension(name="sessionMedium")],
        metrics=[Metric(name="sessions"), Metric(name="conversions")],
        date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
        limit=limit,
        order_bys=[{"desc": True, "metric": {"metric_name": "sessions"}}],
    )
    res = _client().run_report(req)
    rows = []
    for r in res.rows:
        rows.append({
            "source": r.dimension_values[0].value,
            "medium": r.dimension_values[1].value,
            "sessions": int(float(r.metric_values[0].value or 0)),
            "conversions": int(float(r.metric_values[1].value or 0)),
        })
    return rows

def get_realtime_active():
    req = RunRealtimeReportRequest(
        property=f"properties/{PROPERTY_ID}",
        metrics=[Metric(name="activeUsers")],
    )
    res = _client().run_realtime_report(req)
    return int(float(res.rows[0].metric_values[0].value)) if res.rows else 0

def get_nonzero_overview_7d():
    """
    Try a rich set of metrics; if API rejects some, fall back to a safe subset.
    Returns list of metric dicts with non-zero values only.
    """
    full = [
        "activeUsers", "newUsers", "sessions", "screenPageViews",
        "eventCount", "conversions", "totalRevenue",
        "userEngagementDuration", "averageSessionDuration",
        "sessionsPerUser", "engagementRate", "bounceRate"
    ]
    subsets = [full,
               ["activeUsers","newUsers","sessions","screenPageViews","eventCount","averageSessionDuration","engagementRate"],
               ["activeUsers","sessions","screenPageViews"]]

    for metric_names in subsets:
        try:
            req = RunReportRequest(
                property=f"properties/{PROPERTY_ID}",
                dimensions=[],
                metrics=[Metric(name=m) for m in metric_names],
                date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
            )
            res = _client().run_report(req)
            vals = {}
            for i, m in enumerate(metric_names):
                raw = res.rows[0].metric_values[i].value if res.rows else "0"
                vals[m] = raw
            # Build pretty cards & filter non-zero
            out = []
            for key, raw in vals.items():
                # convert & pretty
                if key in ("engagementRate","bounceRate"):
                    num = float(raw or 0) * 100
                    pretty = f"{num:.1f}%"
                elif key in ("averageSessionDuration","userEngagementDuration"):
                    num = float(raw or 0)
                    pretty = _fmt_secs_to_hms(num)
                elif key in ("sessionsPerUser",):
                    num = float(raw or 0)
                    pretty = f"{num:.2f}"
                elif key in ("totalRevenue",):
                    num = float(raw or 0)
                    pretty = f"{num:,.2f}"
                else:
                    num = float(raw or 0)
                    pretty = f"{int(num):,}"

                if num > 0:
                    out.append({"key": key, "value": num, "pretty": pretty})
            # sort by value desc
            out.sort(key=lambda x: x["value"], reverse=True)
            return out
        except GoogleAPICallError:
            continue
    return []
