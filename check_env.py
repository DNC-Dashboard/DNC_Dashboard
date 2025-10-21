import os, pathlib
print("GA4_PROPERTY_ID=", os.getenv("GA4_PROPERTY_ID"))
p = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
print("GOOGLE_APPLICATION_CREDENTIALS=", p)
print("Key exists=", pathlib.Path(p.strip('"')).exists())
