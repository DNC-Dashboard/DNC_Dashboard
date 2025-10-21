# test_ga.py
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Metric, Dimension, RunReportRequest
import os

# 1) Check credentials path
print("Credentials Path:", os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))

# 2) Init GA4 client
client = BetaAnalyticsDataClient()

# 3) Your GA4 Property ID (numbers only)
PROPERTY_ID = "508548249"   # <-- replace if needed

# 4) Simple report: active users by date (last 7 days)
request = RunReportRequest(
    property=f"properties/{PROPERTY_ID}",
    dimensions=[Dimension(name="date")],
    metrics=[Metric(name="activeUsers")],
    date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
)

response = client.run_report(request)

# 5) Print results
for row in response.rows:
    date = row.dimension_values[0].value
    users = row.metric_values[0].value
    print(date, users)
