# Project Setup & Instructions

## 1. Prerequisites
* **Python:** 3.14 (or 3.12+)
* **Node.js:** Latest LTS
* **Firebase CLI:** `npm install -g firebase-tools`

## 2. Backend Setup (material-to-md)
1.  Navigate to the backend folder:
    ```bash
    cd services/material-to-md
    ```
2.  Install Python dependencies:
    ```bash
    py -m pip install -r requirements.txt
    ```
3.  Create a `.env` file in the `services/material-to-md` folder:
    ```ini
    FIRESTORE_EMULATOR_HOST="127.0.0.1:8080"
    FIREBASE_STORAGE_EMULATOR_HOST="127.0.0.1:9199"
    FIREBASE_AUTH_EMULATOR_HOST="127.0.0.1:9099"
    PROJECT_ID="demo-project"
    ```
4. backend:
   ```bash
   cd services/material-to-md
   py -m uvicorn app:app --reload --port 8000
   ```

5. emulators (material-to-md):
   ```bash
   cd services/material-to-md
   firebase emulators:start
   ```
   - Emulator config lives in `services/material-to-md/emulators/`
   - Emulator logs are written to `services/material-to-md/emulators/logs/`

6. frontend:
   ```bash
   pnpm run dev
   ```

Material-to-MD docs/specs live in `services/material-to-md/docs/`.
## 3. Running Tests
To verify the backend is working, run the automated test suite:
```bash
cd services/material-to-md
python -m pytest
```

For E2E tests (Playwright):
```bash
pnpm exec playwright install chromium
$env:FIREBASE_SERVICE_ACCOUNT_PATH="C:\path\to\firebase-admin.json"
pnpm test:e2e
```

Playwright reports are written to `misc/playwright-report/` and test artifacts to `misc/test-results/`.


# 2.5. Running in GitHub Codespaces
1.  **Create Codespace**: Click **Code** -> **Codespaces** -> **Create codespace on main**.
2.  **Wait for Setup**: The environment will automatically install `firebase-tools`, `pnpm`, and Python dependencies.
    - *Note:* If commands are missing, the setup script may have been skipped. Run manually:
      ```bash
      npm install -g firebase-tools pnpm && pnpm install && pip install -r services/material-to-md/requirements.txt
      ```
3.  **Setup Environment**:
    Create a `.env.local` file in the root directory for your Firebase client keys (API Key, Project ID, etc.).
    *Note:* Codespaces do not inherit your local `.env.local` or `.env` files for security.

4.  **Start Emulators & Backend**:
    ```bash
    cd services/material-to-md
    firebase emulators:start
    ```
    *(Open a new terminal)*
    ```bash
    cd services/material-to-md
    python -m uvicorn app:app --reload --port 8000
    ```
5.  **Start Frontend**:
    *(Open a new terminal)*
    ```bash
    pnpm run dev
    ```

## 2.6. Troubleshooting
- **"Port taken" / "Address already in use"**: Run `pkill -f node && pkill -f java` to kill stuck emulator processes.
- **"PERMISSION_DENIED" on writes**: Ensure `services/material-to-md/emulators/firestore.rules` is up to date and not expired.
- **"127.0.0.1 refused to connect"**: Ensure your `firebase.ts` supports dynamic Codespace URLs (already configured in `src/lib/firebase.ts`).

# PR Checklist (Project Hygiene)
- Codespace works: if not, document exact setup steps and required env vars for others.
- Env files:
  - `.env.local` for local Next.js dev/emulator config.
  - `services/material-to-md/.env` for the Material-to-MD emulator setup.
  - Production: configure env vars in Firebase/hosting; do not commit secrets.
- Install/build:
  - Root (Next + Playwright): `pnpm install`
  - Functions emulator: `npm install` in `services/firebase-functions`
  - Material-to-MD: `py -m pip install -r services/material-to-md/requirements.txt`
  - Docker: not used; document if introduced.
  - Genkit: uses Google GenAI plugin; configure API credentials per Genkit docs (not committed).
- Tests:
  - Unit/Converter: `py -m pytest test_converter.py` (from `services/material-to-md`)
  - API/Pipeline: `py -m pytest test_pipeline.py` (from `services/material-to-md`)
  - End-to-end: `pnpm test:e2e` (requires Playwright install + service account)
- Documentation:
  - API docs: `http://localhost:8000/docs` (Material-to-MD)
  - README accuracy check after changes
- Login/roles:
  - Users sign in with Google; onboarding assigns role/department/courses.
  - No predefined users; for tests use `/api/test-token` with `ENABLE_TEST_AUTH=true`.
- Cleanup:
  - Remove unnecessary files (e.g., `CLINE.md`, `.clinerules`, `database.rules.json`) if not used.
- Specs/guardrails:
  - `openspec/` present and up to date; verify `openspec/AGENTS.md`.
  - `.gitignore` verified.
- DataConnect:
  - Schema in `dataconnect/`; generated types in `src/dataconnect-generated/`.

# CourseLLM

## Purpose
CourseLLM (Coursewise) is an educational platform that leverages AI to provide personalized learning experiences. 
It is intended for Undergraduate University Courses and is being tested on Computer Science courses.

The project provides role-based dashboards for students and teachers, integrated authentication via Firebase, and AI-powered course assessment and tutoring. 

The core goals are to:
- Enable personalized learning assessment and recommendations for students
- Provide Socratic-style course tutoring through AI chat
- Keep track of the history of students interactions with the system to enable teachers to monitor quality, intervene when needed, and obtain fine-grained analytics on learning trajectories.
- Support both student and teacher workflows
- Ensure secure, role-based access control

## Tech Stack
- **Frontend Framework**: Next.js 15 with React 18 (TypeScript)
- **Styling**: Tailwind CSS with Radix UI components
- **Backend/Functions**: Firebase Cloud Functions, Firebase Admin SDK
- **Backend**: FastAPI Python micro-services hosted on Google Cloud Run.
- **Database**: Firestore (NoSQL document database)
- **Authentication**: Firebase Authentication (Google OAuth)
- **AI/ML**: Google Genkit 1.20.0 with Google GenAI models (default: gemini-2.5-flash) and DSPy.ai for complex 
- **Data**: Firebase DataConnect (GraphQL layer over Firestore)
- **Testing**: Playwright for E2E tests
- **Dev Tools**: TypeScript 5, pnpm workspace, Node.js
- **Deployment**: Firebase Hosting, App Hosting

More technical details are available in openspec/project.md

