import { initializeApp, getApps, getApp } from "firebase/app";
import { getAuth, connectAuthEmulator } from "firebase/auth";

const firebaseConfig = {
  apiKey: "fake-api-key",
  authDomain: "localhost",
  projectId: "course-llm-firebase",
  storageBucket: "default-bucket",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abcdef"
};

const app = !getApps().length ? initializeApp(firebaseConfig) : getApp();
const auth = getAuth(app);

// SAFE GUARD: Only run this in the browser
if (typeof window !== "undefined") {
  // Only connect if we are on localhost
  if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
    try {
      // Connect to emulator (Terminal 1)
      connectAuthEmulator(auth, "http://127.0.0.1:9099", { disableWarnings: true });
    } catch (e) {
      // Ignore if already connected
    }
  }
}

export { app, auth };