# apps/pages/ga.py
"""
GA4 Data helpers for Django views.

- Loads credentials from:
    GOOGLE_APPLICATION_CREDENTIALS=/abs/path/to/ga4.json
  or
    GOOGLE_APPLICATION_CREDENTIALS_JSON='{"type":"service_account", ...}'

- Exposes convenience functions used by the analytics page:
    get_nonzero_overview_7d()
    get_timeseries_30d()
    get_devices_7d()
    get_countries_7d(limit=10)
    get_top_pages_7d(limit=10)
    get_sources_7d(limit=10)
    get_realtime_active()

All functions are defensive: on errors they return empty values
instead of exploding your page.
"""

from __future__ import annotations

import os
import json
from typing import List, Dict, Any

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Metric,
    Dimension,
    RunReportRequest,
    RunRealtimeReportRequest,
)
from google.api_core.exceptions import GoogleAPICallError, PermissionDenied, NotFound
from google.oauth2 import service_account

# -----------------------
# Configuration
# -----------------------
PROPERTY_ID = os.getenv("GA4_PROPERTY_ID", "")

# Cache the GA client instance
_GA_CLIENT: BetaAnalyticsDataClient | None = None


def _fmt_secs_to_hms(sec: Any) -> str:
    """Format seconds to H:MM:SS."""
    try:
        s = float(sec or 0)
        m, s = divmod(int(round(s)), 60)
        h, m = divmod(m, 60)
        return f"{h:d}:{m:02d}:{s:02d}"
    except Exception:
        return "0:00:00"


def _to_int(val: Any) -> int:
    try:
        return int(float(val or 0))
    except Exception:
        return 0


def _to_float(val: Any) -> float:
    try:
        return float(val or 0.0)
    except Exception:
        return 0.0


def _make_credentials():
    """
    Build service account credentials from either a file path
    or a JSON blob in env.
    """
    key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    key_blob = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")

    if key_path and os.path.exists(key_path):
        return service_account.Credentials.from_service_account_file(key_path)

    if key_blob:
        try:
            info = json.loads(key_blob)
            return service_account.Credentials.from_service_account_info(info)
        except json.JSONDecodeError:
            raise RuntimeError("Invalid GOOGLE_APPLICATION_CREDENTIALS_JSON: not valid JSON")

    # Fall back to default (will error later if not on GCP)
    raise RuntimeError(
        "GA credentials not configured. Set GOOGLE_APPLICATION_CREDENTIALS to an absolute path "
        "or GOOGLE_APPLICATION_CREDENTIALS_JSON to the JSON contents."
    )


def get_client() -> BetaAnalyticsDataClient:
    """
    Return a singleton GA Data API client using explicit credentials.
    """
    global _GA_CLIENT
    if _GA_CLIENT is None:
        creds = _make_credentials()
        _GA_CLIENT = BetaAnalyticsDataClient(credentials=creds)
    return _GA_CLIENT


def _safe_run(callable_fn, fallback):
    """
    Execute a GA call and return fallback on any handled error.
    """
    try:
        return callable_fn()
    except (GoogleAPICallError, PermissionDenied, NotFound, RuntimeError) as e:
        # Optional: log for debugging in server logs
        print(f"[GA4] Error: {e}")
        return fallback
    except Exception as e:
        print(f"[GA4] Unknown error: {e}")
        return fallback


# -----------------------
# Public API (used by views)
# -----------------------

def get_realtime_active() -> int:
    """
    Realtime active users (last 30 minutes).
    """
    def _call():
        req = RunRealtimeReportRequest(
            property=f"properties/{PROPERTY_ID}",
            metrics=[Metric(name="activeUsers")],
        )
        res = get_client().run_realtime_report(req)
        return _to_int(res.rows[0].metric_values[0].value) if res.rows else 0

    return _safe_run(_call, 0)


def get_nonzero_overview_7d() -> List[Dict[str, Any]]:
    """
    Try a rich set of 7d metrics; filter out zeros; sort by value desc.
    Returns list of dicts: [{"key","value","pretty"}...]
    """
    if not PROPERTY_ID:
        return []

    full = [
        "activeUsers", "newUsers", "sessions", "screenPageViews",
        "eventCount", "conversions", "totalRevenue",
        "userEngagementDuration", "averageSessionDuration",
        "sessionsPerUser", "engagementRate", "bounceRate",
    ]
    fallbacks = [
        full,
        ["activeUsers", "newUsers", "sessions", "screenPageViews", "eventCount",
         "averageSessionDuration", "engagementRate"],
        ["activeUsers", "sessions", "screenPageViews"],
    ]

    for metric_names in fallbacks:
        def _call():
            req = RunReportRequest(
                property=f"properties/{PROPERTY_ID}",
                dimensions=[],
                metrics=[Metric(name=m) for m in metric_names],
                date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
            )
            res = get_client().run_report(req)
            return res

        res = _safe_run(_call, None)
        if not res:
            continue

        # Convert and filter non-zero
        out: List[Dict[str, Any]] = []
        if not res.rows:
            continue
        row = res.rows[0]  # single-row aggregation
        for i, key in enumerate(metric_names):
            raw = row.metric_values[i].value
            # Pretty + numeric
            if key in ("engagementRate", "bounceRate"):
                num = _to_float(raw) * 100.0
                pretty = f"{num:.1f}%"
            elif key in ("averageSessionDuration", "userEngagementDuration"):
                num = _to_float(raw)
                pretty = _fmt_secs_to_hms(num)
            elif key in ("sessionsPerUser",):
                num = _to_float(raw)
                pretty = f"{num:.2f}"
            elif key in ("totalRevenue",):
                num = _to_float(raw)
                pretty = f"{num:,.2f}"
            else:
                num = _to_float(raw)
                pretty = f"{_to_int(num):,}"

            if num > 0:
                out.append({"key": key, "value": num, "pretty": pretty})

        out.sort(key=lambda x: x["value"], reverse=True)
        return out

    return []


def get_timeseries_30d() -> List[Dict[str, Any]]:
    """
    Line series: sessions & activeUsers by date for last 30 days.
    """
    if not PROPERTY_ID:
        return []

    def _call():
        req = RunReportRequest(
            property=f"properties/{PROPERTY_ID}",
            dimensions=[Dimension(name="date")],
            metrics=[Metric(name="sessions"), Metric(name="activeUsers")],
            date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
        )
        return get_client().run_report(req)

    res = _safe_run(_call, None)
    if not res or not res.rows:
        return []

    out: List[Dict[str, Any]] = []
    for r in res.rows:
        d = r.dimension_values[0].value  # YYYYMMDD
        out.append({
            "date": f"{d[0:4]}-{d[4:6]}-{d[6:8]}",
            "sessions": _to_int(r.metric_values[0].value),
            "activeUsers": _to_int(r.metric_values[1].value),
        })
    return out


def get_devices_7d() -> List[Dict[str, Any]]:
    """
    Doughnut: sessions by deviceCategory (7d).
    """
    if not PROPERTY_ID:
        return []

    def _call():
        req = RunReportRequest(
            property=f"properties/{PROPERTY_ID}",
            dimensions=[Dimension(name="deviceCategory")],
            metrics=[Metric(name="sessions")],
            date_ranges=[DateRange(start_date="28daysAgo", end_date="today")],
        )
        return get_client().run_report(req)

    res = _safe_run(_call, None)
    if not res or not res.rows:
        return []

    return [{"label": r.dimension_values[0].value,
             "value": _to_int(r.metric_values[0].value)} for r in res.rows]


def get_countries_7d(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Bar: sessions by country (7d).
    """
    if not PROPERTY_ID:
        return []

    def _call():
        req = RunReportRequest(
            property=f"properties/{PROPERTY_ID}",
            dimensions=[Dimension(name="country")],
            metrics=[Metric(name="sessions")],
            date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
            limit=limit,
            order_bys=[{"desc": True, "metric": {"metric_name": "sessions"}}],
        )
        return get_client().run_report(req)

    res = _safe_run(_call, None)
    if not res or not res.rows:
        return []

    return [{"label": r.dimension_values[0].value,
             "value": _to_int(r.metric_values[0].value)} for r in res.rows]


def get_top_pages_7d(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Table: top pages by views (7d).
    """
    if not PROPERTY_ID:
        return []

    def _call():
        req = RunReportRequest(
            property=f"properties/{PROPERTY_ID}",
            dimensions=[
                Dimension(name="pageTitle"),
                Dimension(name="pagePathPlusQueryString"),
            ],
            metrics=[Metric(name="screenPageViews")],
            date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
            limit=limit,
            order_bys=[{"desc": True, "metric": {"metric_name": "screenPageViews"}}],
        )
        return get_client().run_report(req)

    res = _safe_run(_call, None)
    if not res or not res.rows:
        return []

    out: List[Dict[str, Any]] = []
    for r in res.rows:
        out.append({
            "title": r.dimension_values[0].value or "(untitled)",
            "path": r.dimension_values[1].value or "/",
            "views": _to_int(r.metric_values[0].value),
        })
    return out


def get_sources_7d(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Table: top sources / mediums (7d) with sessions + conversions (if defined).
    """
    if not PROPERTY_ID:
        return []

    def _call():
        req = RunReportRequest(
            property=f"properties/{PROPERTY_ID}",
            dimensions=[Dimension(name="sessionSource"),
                        Dimension(name="sessionMedium")],
            metrics=[Metric(name="sessions"), Metric(name="conversions")],
            date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
            limit=limit,
            order_bys=[{"desc": True, "metric": {"metric_name": "sessions"}}],
        )
        return get_client().run_report(req)

    res = _safe_run(_call, None)
    if not res or not res.rows:
        return []

    rows: List[Dict[str, Any]] = []
    for r in res.rows:
        rows.append({
            "source": r.dimension_values[0].value,
            "medium": r.dimension_values[1].value,
            "sessions": _to_int(r.metric_values[0].value),
            "conversions": _to_int(r.metric_values[1].value),
        })
    return rows
