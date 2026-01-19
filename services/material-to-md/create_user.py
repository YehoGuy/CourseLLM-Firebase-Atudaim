import firebase_admin
from firebase_admin import auth, credentials
import os

# Tell the script to talk to the Emulator, not the cloud
os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = "127.0.0.1:9099"

# Initialize with a dummy project ID
if not firebase_admin._apps:
    firebase_admin.initialize_app(options={'projectId': 'course-llm-firebase'})

def create_test_user():
    try:
        user = auth.create_user(
            email='test@example.com',
            password='password123'
        )
        print(f"Successfully created user: {user.uid}")
    except Exception as e:
        print(f"User might already exist or error occurred: {e}")

if __name__ == "__main__":
    create_test_user()