import os
from firebase_setup import firebase_app
from google.cloud import firestore

project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
print("Using project:", project_id)

db = firestore.Client(project=project_id)

doc = db.collection("test").document("hello")
doc.set({"message": "world"})

print("Document written to emulator for project:", project_id)
