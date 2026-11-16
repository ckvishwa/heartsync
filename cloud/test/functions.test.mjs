// sendHeart callable test, against the Functions, Auth, and Firestore emulators.
// Run with `npm test` in cloud/.
import assert from "node:assert/strict";
import { after, before, test } from "node:test";

import { deleteApp as deleteAdminApp, initializeApp as initializeAdminApp } from "firebase-admin/app";
import { getAuth as getAdminAuth } from "firebase-admin/auth";
import { getFirestore } from "firebase-admin/firestore";
import { deleteApp, initializeApp } from "firebase/app";
import { connectAuthEmulator, getAuth, signInWithEmailAndPassword, signOut } from "firebase/auth";
import { connectFunctionsEmulator, getFunctions, httpsCallable } from "firebase/functions";

const PROJECT_ID = "demo-heartsync";
const PASSWORD = "test-password";
const COUPLE = "fn-couple";

process.env.FIRESTORE_EMULATOR_HOST ??= "127.0.0.1:8080";
process.env.FIREBASE_AUTH_EMULATOR_HOST ??= "127.0.0.1:9099";

let adminApp, db, app, auth, sendHeart;

before(async () => {
  adminApp = initializeAdminApp({ projectId: PROJECT_ID }, "functions-test-admin");
  db = getFirestore(adminApp);
  const adminAuth = getAdminAuth(adminApp);
  for (const uid of ["fn-alice", "fn-bob", "fn-solo"]) {
    await adminAuth.deleteUser(uid).catch(() => {});
    await adminAuth.createUser({ uid, email: `${uid}@example.com`, password: PASSWORD });
  }
  await db.doc("users/fn-alice").set({ coupleId: COUPLE });
  await db.doc("users/fn-bob").set({ coupleId: COUPLE });
  await db.doc("users/fn-solo").set({ displayName: "Solo" });
  await db.doc(`couples/${COUPLE}`).set({ members: ["fn-alice", "fn-bob"] });

  app = initializeApp({ projectId: PROJECT_ID, apiKey: "demo-key" }, "functions-test-client");
  auth = getAuth(app);
  connectAuthEmulator(auth, `http://${process.env.FIREBASE_AUTH_EMULATOR_HOST}`, {
    disableWarnings: true,
  });
  const functions = getFunctions(app, "us-central1");
  // Ask the emulator hub where Functions runs: npm test uses firebase.test.json,
  // whose ports differ from the dev emulators so both can run at once.
  // Never fall back silently: that could hit the dev emulators instead.
  const hubHost = process.env.FIREBASE_EMULATOR_HUB;
  if (!hubHost) throw new Error("FIREBASE_EMULATOR_HUB not set: run through `npm test`");
  const res = await fetch(`http://${hubHost}/emulators`);
  if (!res.ok) throw new Error(`emulator hub lookup failed: HTTP ${res.status}`);
  const fn = (await res.json()).functions;
  if (!fn?.port) throw new Error("emulator hub lists no Functions emulator");
  connectFunctionsEmulator(functions, fn.host ?? "127.0.0.1", fn.port);
  sendHeart = httpsCallable(functions, "sendHeart");
});

after(async () => {
  await deleteApp(app);
  await deleteAdminApp(adminApp);
});

test("sendHeart writes a heart event from the caller to the couple's stream", async () => {
  await signInWithEmailAndPassword(auth, "fn-alice@example.com", PASSWORD);
  const { data } = await sendHeart();
  assert.equal(typeof data.eventId, "string");

  const event = (await db.doc(`couples/${COUPLE}/events/${data.eventId}`).get()).data();
  assert.equal(event.type, "heart");
  assert.equal(event.from, "fn-alice");
  assert.deepEqual(event.payload, {});
  assert.ok(event.createdAt, "createdAt is set by the server");

  // The partner's listener query (events not from me) finds it.
  const forBob = await db
    .collection(`couples/${COUPLE}/events`)
    .where("from", "!=", "fn-bob")
    .get();
  assert.ok(forBob.docs.some((d) => d.id === data.eventId));
});

test("sendHeart rejects a signed-out caller", async () => {
  await signOut(auth);
  await assert.rejects(sendHeart(), { code: "functions/unauthenticated" });
});

test("sendHeart rejects a user who is not paired", async () => {
  await signInWithEmailAndPassword(auth, "fn-solo@example.com", PASSWORD);
  await assert.rejects(sendHeart(), { code: "functions/failed-precondition" });
});

test("sendHeart rejects a forged coupleId that the couple does not confirm", async () => {
  // A user document pointing at a couple that does not list the user.
  await db.doc("users/fn-solo").set({ coupleId: COUPLE });
  await signInWithEmailAndPassword(auth, "fn-solo@example.com", PASSWORD);
  await assert.rejects(sendHeart(), { code: "functions/permission-denied" });
  await db.doc("users/fn-solo").set({ displayName: "Solo" });
});
