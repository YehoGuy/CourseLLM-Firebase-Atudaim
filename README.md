# CourseLLM

## Purpose
CourseLLM (Coursewise) is an educational platform that leverages AI to provide personalized learning experiences. 
It is intended for Undergraduate University Courses and is being tested on Computer Science courses.

The project provides role-based dashboards for students and teachers, integrated authentication via Firebase, and AI-powered course assessment and tutoring. 

Our core goals are to:
- Provide teachers the ability to convert their files to markdown files
- Provide a monitoring of the system health, while the teachers are using our service.

# Project Setup & Instructions

## 1. Prerequisites
* **Python:** 3.14 (or 3.12+)
* **Node.js:** Latest LTS
* **Firebase CLI:** `npm install -g firebase-tools`
npm install -g pnpm
npx playwright install                                       


## 2. Backend Setup (material-to-md)
1.  Navigate to the backend folder:
    ```bash
    cd services/material-to-md
    ```
2.  Install Python dependencies:
    ```bash
    py -m pip install -r requirements.txt
    ```
3.  Look a `.env` file in the `services/material-to-md` folder:
    We have created the env file as it not containing any leaked data

    In addition, go to .env.local.example in the root and copy the template from there to .env.local
    in the mail we provided you an example, just remember to change the "FIREBASE_SERVICE_ACCOUNT_JSON" to the path
    of the admin sdk for firbase which also provided in the mail. Make sure you downloaded to the root.

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
make sure that the emulators are running!

```bash
cd services/material-to-md

python -m pytest 
or
py -m pytest
```

For E2E tests (Playwright):
Remember to do Ctrl+c in the termianl where you started the frontend (where you run npm run dev)!
```bash
pnpm exec playwright install chromium
$env:FIREBASE_SERVICE_ACCOUNT_PATH="C:\path\to\firebase-admin.json"
pnpm test:e2e
```

Playwright reports are written to `misc/playwright-report/` and test artifacts to `misc/test-results/`.

4.  **Start Frontend**:
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

# Explanation about the microservice
**1. Project Definition (OpenSpec)**

 This project utilizes the OpenSpec methodology for planning and architecture.Methodology: All changes, from architecture shifts to new capabilities, are first documented as proposals in the openspec/ folder.Status: The core project definition and technical conventions are maintained in @/openspec/project.md.Evaluation: The platform successfully integrates AI tutoring and role-based access; future improvements focus on expanded analytics and deeper integration between the Socratic chat and course materials.

**2. Specification & Connectivity (REST API)**

CourseLLM is a multi-service architecture that relies on RESTful communication.Inter-Service Connectivity: The Next.js frontend calls the FastAPI Python microservice (Material-to-MD) for complex document conversions.AI Orchestration: Frontend interactions trigger Genkit flows (running on Firebase Functions) which orchestrate calls to Google GenAI models (Gemini).Data Flow: The frontend communicates with Firestore via a GraphQL layer (Firebase DataConnect) for strongly-typed data management.

**3. Architecture Specification**

***3.1 Key React Components & API*** 

InteractionComponentFunctionAPI / Service InvokedChatPanelSocratic tutoring interfaceGenkit Flow: socratic-course-chatAssessmentClientKnowledge testingGenkit Flow: personalized-learning-assessmentMaterialToMdPageMaterial upload/conversionFastAPI: /api/material-to-md/convertAuthProviderClientAuth state managementFirebase Auth SDKRoleGuardClientAccess controlFirestore user profile validation

***3.2 Backend FunctionsMaterial-to-MD (Python/FastAPI)*** Handles conversion of PDF, DOCX, and PPTX to Markdown using PyMuPDF, python-docx, and markdownify.Firebase Functions: Executes Genkit AI flows and handles server-side Admin SDK operations.

**4. Implementation & Cleanup**

 The repository has been cleaned to ensure project hygiene:Redundancy: Duplicate logic and unused files (e.g., CLINE.md, .clinerules, or unused database.rules.json) have been removed.Code Quality: Strict TypeScript mode is enabled, and component architecture follows the Client.tsx suffix convention for interactive parts.

**5. Testing & Automatic ValidationWe**

 employ a multi-layered testing strategy to ensure reliability.

***5.1 Test SuitesFrontend Unit Tests***

 Uses Jest with mocks to simulate API responses for isolated component testing.Backend Pytest:Bashcd services/material-to-md
python -m pytest # Runs unit and API pipeline tests
End-to-End (E2E): Powered by Playwright.Bashpnpm test:e2e # Runs user flows from login to dashboard

***5.2 Repeatability & CleanupTests are designed to be repeatable***

 After execution, scripts are included to clean up temporary artifacts in misc/test-results/ and reset emulator state to ensure a clean baseline for subsequent runs.
 
 **6. Monitoring & HealthTo ensure system stability**
 
  we monitor the "Health of the App":System Metrics: The Python backend uses psutil to track CPU, RAM, and Storage usage.Health Dashboard: Real-time health metrics are available via the monitoring API (Port 8001).Teacher Analytics: Teachers can monitor student learning trajectories and AI tutoring quality via the Monitoring dashboard.
  
  **7. Project Report & AI Process Analysis**
  
  The full narrative of the development journey, including the "story" of how the AI agent helped with specific prompts, testing, and architecture, can be found in AI_REPORT.md. This includes a reflection on the experience and what we would change in future iterations.Maintenance CommandsStop Emulators: pkill -f node && pkill -f java.Clean Artifacts: rm -rf misc/test-results/ misc/playwright-report/.

 