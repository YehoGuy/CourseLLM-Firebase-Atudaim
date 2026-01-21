**1. The Development Story**


The development of CourseLLM (Coursewise) began with the goal of creating a personalized educational platform for university students, specifically within Computer Science. The project was built using a modern full-stack approach: Next.js 15 for the frontend, Firebase for backend services (Auth, Firestore, Functions), and a specialized FastAPI service for processing academic materials.

Key milestones included:

Architecture Definition: Establishing a multi-tier system where AI flows are orchestrated via Google Genkit.

Feature Implementation: Developing the Socratic tutoring chat and the automated material-to-markdown conversion pipeline.

Validation: Implementing a robust testing strategy including unit tests with Jest, backend tests with Pytest, and full user-flow validation with Playwright.


**2. AI Assistance Analysis**
The AI agent served as a "co-pilot" throughout the lifecycle of the project, focusing on four primary areas:

***2.1 Planning and Specification***

The AI helped implement the OpenSpec methodology. By analyzing requirements, the AI generated design documents and change proposals in the openspec/ directory, ensuring that architectural decisions were documented before implementation.

***2.2 Code Structure and Cleanliness***

In alignment with the PR Checklist, the AI identified redundant files and suggested a cleaner repository structure. It enforced naming conventions (e.g., the Client.tsx suffix for interactive components) and ensured that server/client components were used correctly according to React 18 patterns.

***2.3 Testing and Validation***

The AI played a critical role in defining the testing strategy:

Frontend: Suggesting the use of Jest mocks to isolate components from live API calls.

Backend: Assisting in the creation of Pytest suites for the FastAPI service.

E2E: Providing templates for Playwright tests that cover first-time login and role-based redirects.

***2.4 Documentation***

The AI consolidated technical details into a comprehensive README.md, ensuring all environment variables, setup steps, and monitoring procedures were clearly documented for other developers.

**3. Effective Prompts**

The following prompt types were most effective during development:

Architectural Proposals: "Based on the project requirements, create an OpenSpec proposal for a new microservice that handles PDF to Markdown conversion."

Refactoring & Cleanup: "Review the current file structure and identify unnecessary files or redundant logic as per the PR Checklist".

Environment Setup: "Write detailed setup instructions for a new developer using GitHub Codespaces, including all required secrets".

**4. Experience Reflection**

What Worked Well
Genkit Flows: The integration of Genkit allowed for a structured way to handle complex AI interactions like Socratic questioning.

Firebase Emulators: Running the entire stack locally via emulators provided a fast and safe development environment.

Challenges
Role-Based Security: Ensuring that Firestore security rules and frontend guards were perfectly synced required multiple iterations.

Dynamic URLs: Configuring the system to support dynamic GitHub Codespace URLs for local testing required specific configuration in src/lib/firebase.ts.

**5. Future Changes and Improvements**

Monitoring Expansion: While basic CPU and RAM monitoring is implemented via psutil, future versions should include more granular AI performance tracking (e.g., token usage and response latency).

Automated Cleanup: Further automate the post-test cleanup process to ensure the storage and database emulators are reset instantly after E2E runs.

Teacher Analytics: Enhance the teacher dashboard to provide deeper insights into student learning trajectories based on their chat history.

