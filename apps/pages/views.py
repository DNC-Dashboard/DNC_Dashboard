from django.shortcuts import render
from django.contrib.auth.decorators import login_required


from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
# ----------------
from django.utils.safestring import mark_safe
import json
from .ga import (
    get_nonzero_overview_7d, get_timeseries_30d, get_devices_7d,
    get_countries_7d, get_top_pages_7d, get_sources_7d, get_realtime_active
)



ICON_MAP = {
    "activeUsers": "fas fa-user-check",
    "newUsers": "fas fa-user-plus",
    "sessions": "fas fa-chart-line",
    "screenPageViews": "far fa-file-alt",
    "eventCount": "fas fa-bolt",
    "conversions": "fas fa-flag-checkered",
    "totalRevenue": "fas fa-dollar-sign",
    "userEngagementDuration": "far fa-clock",
    "averageSessionDuration": "far fa-clock",
    "sessionsPerUser": "fas fa-user-friends",
    "engagementRate": "fas fa-magnet",
    "bounceRate": "fas fa-sign-out-alt",
}

LABEL_MAP = {
    "activeUsers": "Active Users (7d)",
    "newUsers": "New Users (7d)",
    "sessions": "Sessions (7d)",
    "screenPageViews": "Pageviews (7d)",
    "eventCount": "Events (7d)",
    "conversions": "Conversions (7d)",
    "totalRevenue": "Revenue (7d)",
    "userEngagementDuration": "Engagement Time (7d)",
    "averageSessionDuration": "Avg. Session (7d)",
    "sessionsPerUser": "Sessions / User (7d)",
    "engagementRate": "Engagement Rate (7d)",
    "bounceRate": "Bounce Rate (7d)",
}

ACCENTS = ["#5E60CE","#6930C3","#4EA8DE","#64DFDF","#80FFDB","#FF7B54","#FFD56F","#6BCB77","#4D96FF","#B8C0FF"]




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
# @login_required(login_url='/login/')
# def analytics(request):
#     return render(request, "pages/analytics.html")

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






@login_required(login_url="/login/")
def analytics(request):
    realtime   = get_realtime_active()
    metrics    = get_nonzero_overview_7d()           # already filtered > 0
    series30   = get_timeseries_30d()
    devices    = get_devices_7d()
    countries  = get_countries_7d(limit=10)
    pages      = get_top_pages_7d(limit=10)
    sources    = get_sources_7d(limit=10)

    # prettify cards with icon/label/accent
    for i, m in enumerate(metrics):
        m["icon"]  = ICON_MAP.get(m["key"], "fas fa-dot-circle")
        m["label"] = LABEL_MAP.get(m["key"], m["key"])
        m["accent"]= ACCENTS[i % len(ACCENTS)]

    ctx = {
        "realtime": realtime,
        "metric_cards": metrics,                    # non-zero metrics only
        "pages": pages,
        "sources": [s for s in sources if s["sessions"] > 0],

        # charts data
        "series_labels_json":   mark_safe(json.dumps([r["date"] for r in series30])),
        "series_sessions_json": mark_safe(json.dumps([r["sessions"] for r in series30])),
        "series_users_json":    mark_safe(json.dumps([r["activeUsers"] for r in series30])),
        "devices_labels_json":  mark_safe(json.dumps([d["label"] for d in devices])),
        "devices_values_json":  mark_safe(json.dumps([d["value"] for d in devices])),
        "countries_labels_json":mark_safe(json.dumps([c["label"] for c in countries])),
        "countries_values_json":mark_safe(json.dumps([c["value"] for c in countries])),
    }
    return render(request, "pages/analytics.html", ctx)
