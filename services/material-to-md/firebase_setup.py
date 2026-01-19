from dotenv import load_dotenv
load_dotenv()   # Load .env so emulator env vars take effect

import os
import firebase_admin
from firebase_admin import credentials

# Use application default credentials (or your service account)
cred = credentials.ApplicationDefault()

# Figure out project + bucket
project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCLOUD_PROJECT")
bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET") or f"{project_id}.appspot.com"

# Initialize Firebase Admin with Storage bucket
firebase_app = firebase_admin.initialize_app(cred, {
    "storageBucket": bucket_name
})
