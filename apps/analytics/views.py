# apps/analytics/views.py
from django.http import JsonResponse
from apps.analytics.ga import get_summary, get_timeseries

def traffic_api(request, days=None):
    # accept ?days=7 or /traffic/7, default to 7 if bad/missing
    raw = request.GET.get("days") or days or 7
    try:
        d = int(raw)
    except (TypeError, ValueError):
        d = 7  # fallback

    try:
        return JsonResponse({
            "summary": get_summary(d),
            "timeseries": get_timeseries(d),
        })
    except Exception as e:
        return JsonResponse({"message": f"Input Error = {e}", "success": False}, status=500)
