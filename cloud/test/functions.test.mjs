// Callable tests (sendHeart, registerDevice), against the Functions, Auth, and
// Firestore emulators.
// Run with `npm test` in cloud/.
import assert from "node:assert/strict";
import { after, before, test } from "node:test";

import { deleteApp as deleteAdminApp, initializeApp as initializeAdminApp } from "firebase-admin/app";
import { getAuth as getAdminAuth } from "firebase-admin/auth";
import { getFirestore } from "firebase-admin/firestore";
import { deleteApp, initializeApp } from "firebase/app";
import {
  connectAuthEmulator,
  getAuth,
  signInWithCustomToken,
  signInWithEmailAndPassword,
  signOut,
} from "firebase/auth";
import { connectFunctionsEmulator, getFunctions, httpsCallable } from "firebase/functions";

const PROJECT_ID = "demo-heartsync";
const PASSWORD = "test-password";
const COUPLE = "fn-couple";
const OTHER = "fn-other";
const BOARD = "hs-0000000000a1";
const BOARD2 = "hs-0000000000b2";

process.env.FIRESTORE_EMULATOR_HOST ??= "127.0.0.1:8080";
process.env.FIREBASE_AUTH_EMULATOR_HOST ??= "127.0.0.1:9099";

let adminApp, db, app, auth, sendHeart, registerDevice, functionsHost;
const extraApps = [];

before(async () => {
  adminApp = initializeAdminApp({ projectId: PROJECT_ID }, "functions-test-admin");
  db = getFirestore(adminApp);
  const adminAuth = getAdminAuth(adminApp);
  for (const uid of ["fn-alice", "fn-bob", "fn-solo", "fn-mallory"]) {
    await adminAuth.deleteUser(uid).catch(() => {});
    await adminAuth.createUser({ uid, email: `${uid}@example.com`, password: PASSWORD });
  }
  await db.doc("users/fn-alice").set({ coupleId: COUPLE });
  await db.doc("users/fn-bob").set({ coupleId: COUPLE });
  await db.doc("users/fn-solo").set({ displayName: "Solo" });
  await db.doc(`couples/${COUPLE}`).set({ members: ["fn-alice", "fn-bob"] });
  await db.doc("users/fn-mallory").set({ coupleId: OTHER });
  await db.doc(`couples/${OTHER}`).set({ members: ["fn-mallory"] });
  for (const id of [BOARD, BOARD2]) {
    await db.doc(`deviceRegistry/${id}`).delete();
    await db.doc(`couples/${COUPLE}/devices/${id}`).delete();
    await db.doc(`couples/${OTHER}/devices/${id}`).delete();
  }

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
  registerDevice = httpsCallable(functions, "registerDevice");
  functionsHost = { host: fn.host ?? "127.0.0.1", port: fn.port };
});

after(async () => {
  for (const a of extraApps) await deleteApp(a);
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

// ---- boards (ADR 0009): own uid dev_<deviceId>, claims {deviceId, coupleId, owner} ----

let boardCount = 0;

/** Signs a custom token into a separate client app, as a board would. */
async function boardSession(customToken) {
  const a = initializeApp({ projectId: PROJECT_ID, apiKey: "demo-key" }, `board-${boardCount++}`);
  extraApps.push(a);
  const boardAuth = getAuth(a);
  connectAuthEmulator(boardAuth, `http://${process.env.FIREBASE_AUTH_EMULATOR_HOST}`, {
    disableWarnings: true,
  });
  const cred = await signInWithCustomToken(boardAuth, customToken);
  const f = getFunctions(a, "us-central1");
  connectFunctionsEmulator(f, functionsHost.host, functionsHost.port);
  return {
    user: cred.user,
    sendHeart: httpsCallable(f, "sendHeart"),
    registerDevice: httpsCallable(f, "registerDevice"),
  };
}

const mint = (uid, claims) => getAdminAuth(adminApp).createCustomToken(uid, claims);

test("registerDevice mints a board token for dev_<deviceId> with owner claims", async () => {
  await signInWithEmailAndPassword(auth, "fn-alice@example.com", PASSWORD);
  const { data } = await registerDevice({ deviceId: BOARD });
  assert.equal(typeof data.token, "string");

  const board = await boardSession(data.token);
  assert.equal(board.user.uid, `dev_${BOARD}`);
  const { claims } = await board.user.getIdTokenResult();
  assert.equal(claims.deviceId, BOARD);
  assert.equal(claims.coupleId, COUPLE);
  assert.equal(claims.owner, "fn-alice");

  const record = (await db.doc(`couples/${COUPLE}/devices/${BOARD}`).get()).data();
  assert.equal(record.owner, "fn-alice");
  assert.equal(record.online, false);
  const reg = (await db.doc(`deviceRegistry/${BOARD}`).get()).data();
  assert.equal(reg.owner, "fn-alice");
  assert.equal(reg.coupleId, COUPLE);
});

test("a board's sendHeart posts as its owner", async () => {
  await signInWithEmailAndPassword(auth, "fn-alice@example.com", PASSWORD);
  const board = await boardSession((await registerDevice({ deviceId: BOARD })).data.token);
  const res = await board.sendHeart();
  const event = (await db.doc(`couples/${COUPLE}/events/${res.data.eventId}`).get()).data();
  assert.equal(event.from, "fn-alice");
});

test("re-registering your own board revokes its old session", async () => {
  await signInWithEmailAndPassword(auth, "fn-alice@example.com", PASSWORD);
  const first = await boardSession((await registerDevice({ deviceId: BOARD })).data.token);
  const oldIdToken = await first.user.getIdToken();
  const adminAuth = getAdminAuth(adminApp);
  await adminAuth.verifyIdToken(oldIdToken, true); // valid before re-registering
  // Revocation has one-second granularity: let the old session age past it.
  await new Promise((r) => setTimeout(r, 1100));
  await registerDevice({ deviceId: BOARD });
  // The Auth emulator still refreshes revoked sessions (production does not), so
  // check the revocation itself: the old session's tokens are now revoked.
  await assert.rejects(adminAuth.verifyIdToken(oldIdToken, true), {
    code: "auth/id-token-revoked",
  });
});

test("registerDevice refuses a board owned by someone else", async () => {
  await signInWithEmailAndPassword(auth, "fn-alice@example.com", PASSWORD);
  await registerDevice({ deviceId: BOARD2 });
  // The partner, same couple: still not the owner.
  await signInWithEmailAndPassword(auth, "fn-bob@example.com", PASSWORD);
  await assert.rejects(registerDevice({ deviceId: BOARD2 }), { code: "functions/already-exists" });
  // Another couple cannot claim it either.
  await signInWithEmailAndPassword(auth, "fn-mallory@example.com", PASSWORD);
  await assert.rejects(registerDevice({ deviceId: BOARD2 }), { code: "functions/already-exists" });
  assert.equal((await db.doc(`couples/${OTHER}/devices/${BOARD2}`).get()).exists, false);
});

test("registerDevice validates input and the caller", async () => {
  await signOut(auth);
  await assert.rejects(registerDevice({ deviceId: BOARD }), { code: "functions/unauthenticated" });
  await signInWithEmailAndPassword(auth, "fn-alice@example.com", PASSWORD);
  for (const deviceId of [undefined, "", "hs-XYZ", "hs-0000000000A1", "hs-0000000000a1x", 7]) {
    await assert.rejects(registerDevice({ deviceId }), { code: "functions/invalid-argument" });
  }
  await signInWithEmailAndPassword(auth, "fn-solo@example.com", PASSWORD);
  await assert.rejects(registerDevice({ deviceId: BOARD }), { code: "functions/failed-precondition" });
});

test("a board cannot register boards", async () => {
  const board = await boardSession(
    await mint(`dev_${BOARD}`, { deviceId: BOARD, coupleId: COUPLE, owner: "fn-alice" }),
  );
  await assert.rejects(board.registerDevice({ deviceId: BOARD2 }), {
    code: "functions/permission-denied",
  });
});

test("sendHeart refuses malformed or mismatched board tokens", async () => {
  const cases = [
    // uid is not dev_<deviceId>
    ["fn-alice", { deviceId: BOARD, coupleId: COUPLE, owner: "fn-alice" }],
    [`dev_${BOARD2}`, { deviceId: BOARD, coupleId: COUPLE, owner: "fn-alice" }],
    // no owner claim
    [`dev_${BOARD}`, { deviceId: BOARD, coupleId: COUPLE }],
    // coupleId claim does not match the owner's couple (auditor finding 2)
    [`dev_${BOARD}`, { deviceId: BOARD, coupleId: OTHER, owner: "fn-alice" }],
    // owner belongs to another couple
    [`dev_${BOARD}`, { deviceId: BOARD, coupleId: COUPLE, owner: "fn-mallory" }],
  ];
  for (const [uid, claims] of cases) {
    const board = await boardSession(await mint(uid, claims));
    await assert.rejects(board.sendHeart(), { code: "functions/permission-denied" }, JSON.stringify(claims));
  }
});
