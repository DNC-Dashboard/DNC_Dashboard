# apps/analytics/onepage.py
# ONE-PAGE GA4 ANALYTICS VIEW (server-rendered, no separate template)
#
# Requirements (one-time):
#   pip install google-analytics-data
#   Environment:
#     GA4_PROPERTY_ID=<your numeric property id, e.g., 123456789>
#     GOOGLE_APPLICATION_CREDENTIALS=<absolute path to your service-account JSON>
#
# URL wiring (in config/urls.py):
#   from apps.analytics.onepage import analytics_page
#   urlpatterns += [ path("analytics/", analytics_page, name="analytics_page") ]
#
# Visit: /analytics/?days=7  (try 14 or 30)

import os, html, json
from django.http import HttpResponse, HttpResponseBadRequest
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest

PROPERTY_ID = os.getenv("GA4_PROPERTY_ID", "").strip()

def _fetch_timeseries(days: int):
    if not PROPERTY_ID:
        raise RuntimeError("GA4_PROPERTY_ID is not set in the environment.")
    client = BetaAnalyticsDataClient()
    req = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="today")],
        dimensions=[Dimension(name="date")],
        metrics=[Metric(name="sessions"), Metric(name="activeUsers"), Metric(name="screenPageViews")],
    )
    resp = client.run_report(req)

    labels, sessions = [], []
    total_sessions = total_users = total_views = 0
    for row in (resp.rows or []):
        d = row.dimension_values[0].value  # YYYYMMDD
        s = int(row.metric_values[0].value or 0)
        u = int(row.metric_values[1].value or 0)
        v = int(row.metric_values[2].value or 0)
        labels.append(d)
        sessions.append(s)
        total_sessions += s
        total_users += u
        total_views += v

    return {
        "summary": {"sessions": total_sessions, "activeUsers": total_users, "pageviews": total_views},
        "timeseries": {"labels": labels, "data": sessions},
    }

def analytics_page(request):
    # parse days
    try:
        days = int(request.GET.get("days", "7"))
        if days not in (7, 14, 30):  # keep it simple for the demo buttons
            days = 7
    except Exception:
        return HttpResponseBadRequest("Invalid 'days' parameter")

    try:
        payload = _fetch_timeseries(days)
    except Exception as e:
        # Show a friendly error card if GA fails
        err = html.escape(str(e))
        return HttpResponse(f"""
<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Analytics – Error</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/admin-lte@3.2/dist/css/adminlte.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@5.15.4/css/all.min.css">
</head><body class="hold-transition sidebar-mini">
<div class="content-wrapper p-4">
  <div class="alert alert-danger">
    <h4 class="mb-2"><i class="fas fa-exclamation-triangle mr-2"></i>GA4 Error</h4>
    <div>{err}</div>
    <div class="mt-2 text-muted">Check GA4 property access for the service account, env vars, and credentials path.</div>
  </div>
</div>
</body></html>""")

    # embed the data for Chart.js
    json_data = json.dumps(payload)

    # full HTML (AdminLTE look via CDN, no external template)
    html_out = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Analytics</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/admin-lte@3.2/dist/css/adminlte.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@5.15.4/css/all.min.css">
<style>
  .content-wrapper {{ min-height: 100vh; background: #f4f6f9; }}
  .small-box .inner h3 {{ font-weight: 700; }}
  .btn-outline-primary {{ margin-left: .25rem; }}
</style>
</head>
<body class="hold-transition sidebar-mini">
<div class="content-wrapper">
  <div class="content-header">
    <div class="container-fluid">
      <div class="row mb-2">
        <div class="col-sm-6"><h1 class="m-0">Analytics</h1></div>
        <div class="col-sm-6">
          <ol class="breadcrumb float-sm-right">
            <li class="breadcrumb-item"><a href="#">Home</a></li>
            <li class="breadcrumb-item active">Analytics</li>
          </ol>
        </div>
      </div>
    </div>
  </div>

  <section class="content">
    <div class="container-fluid">

      <!-- Cards -->
      <div class="row" id="ga-traffic">
        <div class="col-md-4">
          <div class="small-box bg-info">
            <div class="inner">
              <h3 id="ga-sessions">–</h3>
              <p>Sessions (last <span id="ga-days-label-c1">{days}</span> days)</p>
            </div>
            <div class="icon"><i class="fas fa-chart-line"></i></div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="small-box bg-success">
            <div class="inner">
              <h3 id="ga-users">–</h3>
              <p>Active Users (last <span id="ga-days-label-c2">{days}</span> days)</p>
            </div>
            <div class="icon"><i class="fas fa-user-friends"></i></div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="small-box bg-warning">
            <div class="inner">
              <h3 id="ga-pageviews">–</h3>
              <p>Pageviews (last <span id="ga-days-label-c3">{days}</span> days)</p>
            </div>
            <div class="icon"><i class="fas fa-eye"></i></div>
          </div>
        </div>
      </div>

      <!-- Chart card -->
      <div class="card">
        <div class="card-header d-flex align-items-center justify-content-between">
          <h3 class="card-title m-0">
            Sessions (Last <span id="ga-days-label">{days}</span> Days)
          </h3>
          <div>
            <a class="btn btn-sm btn-outline-primary" href="?days=7">7d</a>
            <a class="btn btn-sm btn-outline-primary" href="?days=14">14d</a>
            <a class="btn btn-sm btn-outline-primary" href="?days=30">30d</a>
          </div>
        </div>
        <div class="card-body">
          <canvas id="gaSessionsChart" height="120"></canvas>
        </div>
      </div>

    </div>
  </section>
</div>

<!-- Chart.js -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>

<script>
  // Injected GA data from server:
  const GA = {json_data};

  // Update cards
  document.getElementById("ga-sessions").textContent  = (GA.summary.sessions || 0).toLocaleString();
  document.getElementById("ga-users").textContent     = (GA.summary.activeUsers || 0).toLocaleString();
  document.getElementById("ga-pageviews").textContent = (GA.summary.pageviews || 0).toLocaleString();

  // Convert YYYYMMDD -> "DD Mon"
  function labelify(yyyymmdd) {{
    const y = yyyymmdd.slice(0,4), m = yyyymmdd.slice(4,6), d = yyyymmdd.slice(6,8);
    const dt = new Date(Date.UTC(+y, +m-1, +d));
    return dt.toLocaleDateString(undefined, {{ day:"2-digit", month:"short" }});
  }}

  const labels = (GA.timeseries.labels || []).map(labelify);
  const data   = (GA.timeseries.data || []);

  const ctx = document.getElementById("gaSessionsChart");
  new Chart(ctx, {{
    type: "line",
    data: {{ labels, datasets: [{{ label: "Sessions", data, fill: false, tension: 0.3 }}] }},
    options: {{
      responsive: true,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{ y: {{ beginAtZero: true }} }}
    }}
  }});
</script>

</body>
</html>
"""
    return HttpResponse(html_out)
