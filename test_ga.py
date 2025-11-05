import os
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Metric, RunReportRequest
from google.oauth2 import service_account

creds = service_account.Credentials.from_service_account_file(
    os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
    scopes=["https://www.googleapis.com/auth/analytics.readonly"]
)

client = BetaAnalyticsDataClient(credentials=creds)

request = RunReportRequest(
    property=f"properties/{os.getenv('GA4_PROPERTY_ID')}",
    date_ranges=[DateRange(start_date="yesterday", end_date="today")],
    metrics=[Metric(name="activeUsers")]
)

response = client.run_report(request)
print("Active users yesterday:", response.rows[0].metric_values[0].value)
