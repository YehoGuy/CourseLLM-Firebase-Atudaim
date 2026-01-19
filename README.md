# Project Setup & Instructions

## 1. Prerequisites
* **Python:** 3.14 (or 3.12+)
* **Node.js:** Latest LTS
* **Firebase CLI:** `npm install -g firebase-tools`

## 2. Backend Setup (materialToMD)
1.  Navigate to the backend folder:
    ```bash
    cd materialToMD
    ```
2.  Install Python dependencies:
    ```bash
    py -m pip install -r requirements.txt
    ```
3.  Create a `.env` file in the `materialToMD` folder:
    ```ini
    FIRESTORE_EMULATOR_HOST="127.0.0.1:8080"
    FIREBASE_STORAGE_EMULATOR_HOST="127.0.0.1:9199"
    FIREBASE_AUTH_EMULATOR_HOST="127.0.0.1:9099"
    PROJECT_ID="demo-project"
    ```
4. backend:
cd materialToMD
 py -m uvicorn app:app --reload --port 8000

 5. emualtors:
 cd materialToMD
 firebase emulators:start

 6. frontend:
    npm run dev
## 3. Running Tests
To verify the backend is working, run the automated test suite:
```bash
cd materialToMD
python -m pytest