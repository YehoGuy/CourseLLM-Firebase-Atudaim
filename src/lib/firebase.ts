import { initializeApp } from "firebase/app";
import { connectAuthEmulator, getAuth, GoogleAuthProvider } from "firebase/auth";
import { connectFirestoreEmulator, getFirestore, enableIndexedDbPersistence } from "firebase/firestore";
import { connectStorageEmulator, getStorage } from "firebase/storage";

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

const app = initializeApp(firebaseConfig);

export const auth = getAuth(app);
export const db = getFirestore(app);
export const storage = getStorage(app);

// Connect to emulators if in development
if (process.env.NODE_ENV === "development" && typeof window !== "undefined") {
  console.log("Connecting to Firebase Emulators...");

  const isCodespace = window.location.hostname.includes("app.github.dev");

  if (isCodespace) {
    // We are in a Codespace, we need to construct the forwarded URLs
    // Format: <name>-<port>.app.github.dev
    // Current hostname example: fictional-winner-9002.app.github.dev

    // Extract the base name (everything before the last dash-port)
    const match = window.location.hostname.match(/^(.*)-(\d+)\.app\.github\.dev$/);

    if (match) {
      const baseName = match[1];

      const authHost = `https://${baseName}-9099.app.github.dev`;
      // Note: allow mismatching domain for auth in dev if needed, but the SDK handles the passed URL
      connectAuthEmulator(auth, authHost);

      const firestoreHost = `${baseName}-8080.app.github.dev`;
      connectFirestoreEmulator(db, firestoreHost, 443);

      const storageHost = `${baseName}-9199.app.github.dev`;
      connectStorageEmulator(storage, storageHost, 443);

      console.log(`Connected to Codespace Emulators: ${baseName}`);
    } else {
      // Fallback if regex fails but we think it's codespace
      console.warn("Could not parse Codespace hostname, falling back to localhost.");
      connectAuthEmulator(auth, "http://127.0.0.1:9099");
      connectFirestoreEmulator(db, "127.0.0.1", 8080);
      connectStorageEmulator(storage, "127.0.0.1", 9199);
    }
  } else {
    // Standard Localhost
    connectAuthEmulator(auth, "http://127.0.0.1:9099");
    connectFirestoreEmulator(db, "127.0.0.1", 8080);
    connectStorageEmulator(storage, "127.0.0.1", 9199);
  }
}

// Enable offline persistence so reads can be served from cache when offline.
// This is a best-effort call: it will fail in some environments (e.g. Safari private mode)
// and when multiple tabs conflict. We catch and ignore expected errors.
try {
  enableIndexedDbPersistence(db).catch((err) => {
    // failed-precondition: multiple tabs open, unimplemented: browser not supported
    console.warn("Could not enable IndexedDB persistence:", err.code || err.message || err);
  });
} catch (e) {
  // Ignore synchronous errors
  console.warn("Persistence enable failed:", e);
}

export const googleProvider = new GoogleAuthProvider();

export default app;
