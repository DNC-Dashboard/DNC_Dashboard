# apps/pages/views.py
import os, json
from django.utils.safestring import mark_safe
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .ga import (
    get_overview_7d, get_timeseries_30d,
    get_top_pages_7d, get_devices_7d, get_countries_7d,
    get_realtime_active
)

def _num(v):
    try: return float(v)
    except: return 0.0

@login_required(login_url="/login/")
def analytics_page(request):
    # --- GA data ---
    overview   = get_overview_7d()          # sessions, users, pageviews, avgSession, engagementRate, newUsers
    series30   = get_timeseries_30d()       # [{date, sessions, activeUsers}, ...]
    top_pages  = get_top_pages_7d(limit=10)
    devices    = get_devices_7d()
    countries  = get_countries_7d(limit=10)
    realtime   = get_realtime_active()

    # --- Biz KPIs (7d) from env (can be replaced by DB later) ---
    total_cost = _num(os.getenv("TOTAL_COST_7D", "0"))
    leads      = _num(os.getenv("LEADS_7D", "0"))
    sales      = _num(os.getenv("SALES_7D", "0"))

    cpl  = (total_cost / leads) if leads > 0 else None
    cps  = (total_cost / sales) if sales > 0 else None

    # --- handle GA errors gracefully ---
    error = None
    for block in (overview, series30, top_pages, devices, countries, realtime):
        if isinstance(block, dict) and block.get("error"):
            error = block["error"]

    # --- series for charts ---
    labels30       = [] if isinstance(series30, dict) else [r["date"] for r in series30]
    seriesSessions = [] if isinstance(series30, dict) else [r["sessions"] for r in series30]
    seriesUsers    = [] if isinstance(series30, dict) else [r["activeUsers"] for r in series30]

    devicesLabels  = [] if isinstance(devices, dict) else [d["device"] for d in devices]
    devicesValues  = [] if isinstance(devices, dict) else [d["sessions"] for d in devices]
    countriesLbl   = [] if isinstance(countries, dict) else [c["country"] for c in countries]
    countriesVal   = [] if isinstance(countries, dict) else [c["sessions"] for c in countries]

    ctx = {
        "error": error,
        "realtime": 0 if isinstance(realtime, dict) else realtime,
        "kpi": {} if isinstance(overview, dict) else overview,

        # biz KPIs
        "total_cost": total_cost,
        "leads": int(leads),
        "sales": int(sales),
        "cpl": cpl,  # may be None
        "cps": cps,  # may be None

        # tables
        "top_pages": [] if isinstance(top_pages, dict) else top_pages,

        # charts (JSON for safe injection)
        "series_labels_json":   mark_safe(json.dumps(labels30)),
        "series_sessions_json": mark_safe(json.dumps(seriesSessions)),
        "series_users_json":    mark_safe(json.dumps(seriesUsers)),
        "devices_labels_json":  mark_safe(json.dumps(devicesLabels)),
        "devices_values_json":  mark_safe(json.dumps(devicesValues)),
        "countries_labels_json":mark_safe(json.dumps(countriesLbl)),
        "countries_values_json":mark_safe(json.dumps(countriesVal)),
    }
    return render(request, "pages/analytics.html", ctx)




def register(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # go to login after successful signup
    else:
        form = UserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})






@login_required(login_url='/login/')
def index(request):
    return render(request, 'pages/index.html')

@login_required(login_url='/login/')
def members(request):
    return render(request, 'pages/members.html')

# Analytics
@login_required(login_url='/login/')
def analytics(request):
    return render(request, "pages/analytics.html")

@login_required(login_url='/login/')
def task_management(request):
    return render(request, "pages/kanban.html")

@login_required(login_url='/login/')
def projects(request):
    return render(request, "pages/projects.html")

@login_required(login_url='/login/')
def campaigns(request):
    return render(request, "pages/campaigns.html")

# Profile (this fixes the {% url 'profile' %} error)
@login_required(login_url='/login/')
def profile(request):
    return render(request, "pages/profile.html")

@login_required(login_url='/login/')
def configuration(request):
    return render(request, "pages/configuration.html")

@login_required(login_url='/login/')
def assets(request):
    return render(request, "pages/assets.html")

    overview   = get_overview_7d()
    series30   = get_timeseries_30d()
    top_pages  = get_top_pages_7d(limit=10)
    devices    = get_devices_7d()
    countries  = get_countries_7d(limit=10)
    realtime   = get_realtime_active()

    # Handle any API errors gracefully
    error = None
    for block in (overview, series30, top_pages, devices, countries, realtime):
        if isinstance(block, dict) and block.get("error"):
            error = block["error"]

    ctx = {
        "error": error,
        "realtime": 0 if isinstance(realtime, dict) else realtime,
        "kpi": {} if isinstance(overview, dict) else overview,
        "series_labels": [] if isinstance(series30, dict) else [r["date"] for r in series30],
        "series_sessions": [] if isinstance(series30, dict) else [r["sessions"] for r in series30],
        "series_users": [] if isinstance(series30, dict) else [r["activeUsers"] for r in series30],
        "top_pages": [] if isinstance(top_pages, dict) else top_pages,
        "devices_labels": [] if isinstance(devices, dict) else [d["device"] for d in devices],
        "devices_values": [] if isinstance(devices, dict) else [d["sessions"] for d in devices],
        "countries_labels": [] if isinstance(countries, dict) else [c["country"] for c in countries],
        "countries_values": [] if isinstance(countries, dict) else [c["sessions"] for c in countries],
    }
    return render(request, "pages/analytics.html", ctx)