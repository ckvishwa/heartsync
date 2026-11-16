// Firebase client init. Import `auth` and `db` from here, only in client
// components ("use client"). Defaults to the local emulators and the
// demo-heartsync project; see env.example for the real project.
import { getApp, getApps, initializeApp } from "firebase/app";
import { connectAuthEmulator, getAuth } from "firebase/auth";
import { connectFirestoreEmulator, getFirestore } from "firebase/firestore";

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY ?? "demo-key",
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN ?? "demo-heartsync.firebaseapp.com",
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID ?? "demo-heartsync",
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET ?? "demo-heartsync.appspot.com",
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

export const useEmulator = process.env.NEXT_PUBLIC_USE_EMULATOR !== "false";

const app = getApps().length > 0 ? getApp() : initializeApp(firebaseConfig);

export const auth = getAuth(app);
export const db = getFirestore(app);

// Connect to the emulators once, even when hot reload re-evaluates this module.
const globalFlags = globalThis as typeof globalThis & { __heartsyncEmulators?: boolean };
if (useEmulator && !globalFlags.__heartsyncEmulators) {
  globalFlags.__heartsyncEmulators = true;
  connectAuthEmulator(auth, "http://127.0.0.1:9099", { disableWarnings: true });
  connectFirestoreEmulator(db, "127.0.0.1", 8080);
}
