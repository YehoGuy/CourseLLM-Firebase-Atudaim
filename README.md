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

More technical details are available in openspecs/specs/project.md

