// Security rules tests. Run with `npm test` in cloud/ (starts the emulators).
// Every rule gets an allow test and a deny test. Data model: docs/protocol.md.
import { readFileSync } from "node:fs";
import { after, before, beforeEach, describe, test } from "node:test";
import { fileURLToPath } from "node:url";

import {
  assertFails,
  assertSucceeds,
  initializeTestEnvironment,
} from "@firebase/rules-unit-testing";
import {
  addDoc,
  collection,
  collectionGroup,
  deleteDoc,
  doc,
  getDoc,
  getDocs,
  serverTimestamp,
  setDoc,
  setLogLevel,
  updateDoc,
} from "firebase/firestore";
import { getBytes, ref, uploadString } from "firebase/storage";

// Expected denials would otherwise flood the output with PERMISSION_DENIED logs.
setLogLevel("silent");

const read = (path) => readFileSync(fileURLToPath(new URL(path, import.meta.url)), "utf8");

// alice + bob are couple c1. mallory + trent are couple c2 (strangers to c1).
let env;
const as = (uid) => env.authenticatedContext(uid).firestore();
const anon = () => env.unauthenticatedContext().firestore();
const heartFrom = (uid) => ({ type: "heart", from: uid, payload: {}, createdAt: serverTimestamp() });

before(async () => {
  env = await initializeTestEnvironment({
    projectId: "demo-heartsync",
    firestore: { rules: read("../firestore.rules") },
    storage: { rules: read("../storage.rules") },
  });
});

after(async () => {
  await env.cleanup();
});

beforeEach(async () => {
  await env.clearFirestore();
  await env.clearStorage();
  await env.withSecurityRulesDisabled(async (ctx) => {
    const db = ctx.firestore();
    await setDoc(doc(db, "users/alice"), { displayName: "Alice", coupleId: "c1" });
    await setDoc(doc(db, "users/bob"), { displayName: "Bob", coupleId: "c1" });
    await setDoc(doc(db, "users/mallory"), { displayName: "Mallory", coupleId: "c2" });
    await setDoc(doc(db, "users/solo"), { displayName: "Solo" });
    await setDoc(doc(db, "couples/c1"), { members: ["alice", "bob"] });
    await setDoc(doc(db, "couples/c2"), { members: ["mallory", "trent"] });
    await setDoc(doc(db, "couples/c1/devices/hs-a"), { owner: "alice", online: true });
    await setDoc(doc(db, "couples/c1/events/e1"), {
      type: "heart",
      from: "alice",
      payload: {},
      createdAt: new Date(),
    });
    await setDoc(doc(db, "users/alice/private/cycle"), { sharingEnabled: true, note: "x" });
    await setDoc(doc(db, "users/alice/private/other"), { note: "y" });
    await uploadString(ref(ctx.storage(), "couples/c1/art/a.txt"), "art");
    await uploadString(ref(ctx.storage(), "firmware/0.1.0/firmware.bin"), "bin");
  });
});

describe("default deny", () => {
  test("unauthenticated users can read nothing", async () => {
    await assertFails(getDoc(doc(anon(), "users/alice")));
    await assertFails(getDoc(doc(anon(), "couples/c1")));
    await assertFails(getDocs(collection(anon(), "couples/c1/events")));
    await assertFails(getDoc(doc(anon(), "users/alice/private/cycle")));
  });

  test("unknown collections are denied even when signed in", async () => {
    await assertFails(getDoc(doc(as("alice"), "anything/else")));
    await assertFails(setDoc(doc(as("alice"), "anything/else"), { a: 1 }));
  });
});

describe("users", () => {
  test("a user can read and update their own profile", async () => {
    await assertSucceeds(getDoc(doc(as("alice"), "users/alice")));
    await assertSucceeds(updateDoc(doc(as("alice"), "users/alice"), { displayName: "A" }));
  });

  test("the partner can read the profile, a stranger cannot", async () => {
    await assertSucceeds(getDoc(doc(as("bob"), "users/alice")));
    await assertFails(getDoc(doc(as("mallory"), "users/alice")));
    await assertFails(getDoc(doc(as("solo"), "users/alice")));
  });

  test("nobody can write another person's profile", async () => {
    await assertFails(updateDoc(doc(as("bob"), "users/alice"), { displayName: "hacked" }));
    await assertFails(setDoc(doc(as("mallory"), "users/alice"), { displayName: "hacked" }));
  });

  test("a new user can create their profile, but not with a coupleId", async () => {
    await assertSucceeds(setDoc(doc(as("carol"), "users/carol"), { displayName: "Carol" }));
    await assertFails(setDoc(doc(as("dave"), "users/dave"), { displayName: "D", coupleId: "c1" }));
  });

  test("a user cannot set or change their own coupleId", async () => {
    await assertFails(updateDoc(doc(as("mallory"), "users/mallory"), { coupleId: "c1" }));
    await assertFails(updateDoc(doc(as("solo"), "users/solo"), { coupleId: "c1" }));
  });

  test("profiles cannot be listed or deleted", async () => {
    await assertFails(getDocs(collection(as("alice"), "users")));
    await assertFails(deleteDoc(doc(as("alice"), "users/alice")));
  });
});

describe("couples", () => {
  test("members can read their couple, strangers cannot", async () => {
    await assertSucceeds(getDoc(doc(as("alice"), "couples/c1")));
    await assertSucceeds(getDoc(doc(as("bob"), "couples/c1")));
    await assertFails(getDoc(doc(as("mallory"), "couples/c1")));
  });

  test("no client can write a couple, not even a member", async () => {
    await assertFails(updateDoc(doc(as("alice"), "couples/c1"), { members: ["alice"] }));
    await assertFails(updateDoc(doc(as("mallory"), "couples/c1"), { members: ["alice", "mallory"] }));
    await assertFails(setDoc(doc(as("solo"), "couples/c3"), { members: ["solo", "alice"] }));
    await assertFails(deleteDoc(doc(as("alice"), "couples/c1")));
  });
});

describe("devices", () => {
  test("members can read devices, strangers cannot", async () => {
    await assertSucceeds(getDocs(collection(as("bob"), "couples/c1/devices")));
    await assertFails(getDocs(collection(as("mallory"), "couples/c1/devices")));
  });

  test("a device can be written as its owner", async () => {
    await assertSucceeds(updateDoc(doc(as("alice"), "couples/c1/devices/hs-a"), { online: false }));
    await assertSucceeds(setDoc(doc(as("bob"), "couples/c1/devices/hs-b"), { owner: "bob" }));
  });

  test("a device cannot be written as someone else", async () => {
    // bob registering a device in alice's name
    await assertFails(setDoc(doc(as("bob"), "couples/c1/devices/hs-x"), { owner: "alice" }));
    // bob updating alice's device
    await assertFails(updateDoc(doc(as("bob"), "couples/c1/devices/hs-a"), { online: false }));
    // bob taking over alice's device
    await assertFails(updateDoc(doc(as("bob"), "couples/c1/devices/hs-a"), { owner: "bob" }));
    // alice giving her device away
    await assertFails(updateDoc(doc(as("alice"), "couples/c1/devices/hs-a"), { owner: "bob" }));
  });

  test("strangers cannot register devices, and nobody can delete one", async () => {
    await assertFails(setDoc(doc(as("mallory"), "couples/c1/devices/hs-m"), { owner: "mallory" }));
    await assertFails(deleteDoc(doc(as("alice"), "couples/c1/devices/hs-a")));
  });
});

describe("events", () => {
  test("members can read events, strangers cannot", async () => {
    await assertSucceeds(getDocs(collection(as("bob"), "couples/c1/events")));
    await assertFails(getDocs(collection(as("mallory"), "couples/c1/events")));
  });

  test("a member can send an event as themselves", async () => {
    await assertSucceeds(addDoc(collection(as("alice"), "couples/c1/events"), heartFrom("alice")));
    await assertSucceeds(addDoc(collection(as("bob"), "couples/c1/events"), heartFrom("bob")));
  });

  test("nobody can write another person's events", async () => {
    await assertFails(addDoc(collection(as("bob"), "couples/c1/events"), heartFrom("alice")));
    await assertFails(addDoc(collection(as("mallory"), "couples/c1/events"), heartFrom("alice")));
    await assertFails(addDoc(collection(as("mallory"), "couples/c1/events"), heartFrom("mallory")));
  });

  test("events are validated", async () => {
    const events = collection(as("alice"), "couples/c1/events");
    await assertFails(addDoc(events, { ...heartFrom("alice"), type: "explode" }));
    await assertFails(addDoc(events, { ...heartFrom("alice"), extra: 1 }));
    await assertFails(addDoc(events, { ...heartFrom("alice"), payload: "nope" }));
    await assertFails(addDoc(events, { ...heartFrom("alice"), createdAt: new Date(0) }));
    await assertFails(addDoc(events, { type: "heart", from: "alice" }));
  });

  test("events are immutable", async () => {
    await assertFails(updateDoc(doc(as("alice"), "couples/c1/events/e1"), { type: "mood" }));
    await assertFails(deleteDoc(doc(as("alice"), "couples/c1/events/e1")));
  });
});

describe("cycle data (health data)", () => {
  const cycle = (uid) => doc(as(uid), "users/alice/private/cycle");

  test("the owner can read and write it", async () => {
    await assertSucceeds(getDoc(cycle("alice")));
    await assertSucceeds(setDoc(cycle("alice"), { sharingEnabled: true, note: "z" }));
    await assertSucceeds(updateDoc(cycle("alice"), { sharingEnabled: false }));
  });

  test("the partner can read it while sharing is on", async () => {
    await assertSucceeds(getDoc(cycle("bob")));
  });

  test("the partner cannot read it once sharing is turned off", async () => {
    await updateDoc(cycle("alice"), { sharingEnabled: false });
    await assertFails(getDoc(cycle("bob")));
  });

  test("the partner can never write it, including the sharing toggle", async () => {
    await assertFails(updateDoc(cycle("bob"), { note: "edited" }));
    await updateDoc(cycle("alice"), { sharingEnabled: false });
    await assertFails(updateDoc(cycle("bob"), { sharingEnabled: true }));
    await assertFails(deleteDoc(cycle("bob")));
  });

  test("strangers and signed-out users cannot read it", async () => {
    await assertFails(getDoc(cycle("mallory")));
    await assertFails(getDoc(cycle("solo")));
    await assertFails(getDoc(doc(anon(), "users/alice/private/cycle")));
  });

  test("sharingEnabled must be a bool on every write", async () => {
    await assertFails(setDoc(cycle("alice"), { note: "no flag" }));
    await assertFails(updateDoc(cycle("alice"), { sharingEnabled: "yes" }));
  });

  test("the partner cannot list or read other private documents", async () => {
    await assertFails(getDocs(collection(as("bob"), "users/alice/private")));
    await assertFails(getDoc(doc(as("bob"), "users/alice/private/other")));
    await assertSucceeds(getDoc(doc(as("alice"), "users/alice/private/other")));
  });
});

describe("releases", () => {
  test("signed-in users can read, nobody can write", async () => {
    await assertSucceeds(getDoc(doc(as("alice"), "releases/0.1.0")));
    await assertFails(getDoc(doc(anon(), "releases/0.1.0")));
    await assertFails(setDoc(doc(as("alice"), "releases/0.1.0"), { version: "0.1.0" }));
  });
});

describe("storage", () => {
  const storageAs = (uid) => env.authenticatedContext(uid).storage();

  test("members can read and write their couple's objects", async () => {
    await assertSucceeds(getBytes(ref(storageAs("bob"), "couples/c1/art/a.txt")));
    await assertSucceeds(uploadString(ref(storageAs("alice"), "couples/c1/art/b.txt"), "hi"));
  });

  test("strangers and signed-out users cannot touch a couple's objects", async () => {
    await assertFails(getBytes(ref(storageAs("mallory"), "couples/c1/art/a.txt")));
    await assertFails(uploadString(ref(storageAs("mallory"), "couples/c1/art/m.txt"), "hi"));
    await assertFails(getBytes(ref(env.unauthenticatedContext().storage(), "couples/c1/art/a.txt")));
  });

  test("firmware is read-only for clients; other paths are denied", async () => {
    await assertSucceeds(getBytes(ref(storageAs("alice"), "firmware/0.1.0/firmware.bin")));
    await assertFails(uploadString(ref(storageAs("alice"), "firmware/0.1.0/firmware.bin"), "evil"));
    await assertFails(uploadString(ref(storageAs("alice"), "elsewhere/x.txt"), "hi"));
  });
});

// Board tokens: custom tokens minted by registerDevice for uid "dev_<deviceId>" with
// the claims deviceId, coupleId and owner. They act for the owner but may only use
// their couple's events and their own device record. See docs/protocol.md
// "Device tokens". Pass null to leave a claim out; `uid` overrides the board uid.
describe("device-scoped tokens", () => {
  const boardCtx = ({ owner = "alice", deviceId = "hs-a", coupleId = "c1", uid } = {}) => {
    const claims = { deviceId };
    if (coupleId !== null) claims.coupleId = coupleId;
    if (owner !== null) claims.owner = owner;
    return env.authenticatedContext(uid ?? `dev_${deviceId}`, claims);
  };
  const device = (opts) => boardCtx(opts).firestore();
  const deviceStorage = (opts) => boardCtx(opts).storage();

  test("a board can read its couple's events and post as its owner", async () => {
    await assertSucceeds(getDocs(collection(device(), "couples/c1/events")));
    await assertSucceeds(addDoc(collection(device(), "couples/c1/events"), heartFrom("alice")));
    await assertFails(addDoc(collection(device(), "couples/c1/events"), heartFrom("bob")));
  });

  test("a board can read and heartbeat its own device record only", async () => {
    await assertSucceeds(getDoc(doc(device(), "couples/c1/devices/hs-a")));
    await assertSucceeds(
      updateDoc(doc(device(), "couples/c1/devices/hs-a"), { online: true, lastSeen: serverTimestamp() }),
    );
    await env.withSecurityRulesDisabled(async (ctx) => {
      await setDoc(doc(ctx.firestore(), "couples/c1/devices/hs-b"), { owner: "alice", online: false });
    });
    // Same owner, other board: still denied.
    await assertFails(getDoc(doc(device(), "couples/c1/devices/hs-b")));
    await assertFails(updateDoc(doc(device(), "couples/c1/devices/hs-b"), { online: true }));
    await assertFails(setDoc(doc(device(), "couples/c1/devices/hs-new"), { owner: "alice" }));
    await assertFails(getDocs(collection(device(), "couples/c1/devices")));
  });

  test("a board cannot read or write anything under users/, cycle data included", async () => {
    await assertFails(getDoc(doc(device(), "users/alice")));
    await assertFails(getDoc(doc(device(), "users/bob")));
    await assertFails(updateDoc(doc(device(), "users/alice"), { displayName: "x" }));
    // Partner's cycle data is readable by the partner person while sharing is on,
    // but never by a board, whichever owner it belongs to.
    await assertSucceeds(getDoc(doc(as("bob"), "users/alice/private/cycle")));
    await assertFails(getDoc(doc(device({ owner: "bob", deviceId: "hs-b" }), "users/alice/private/cycle")));
    await assertFails(getDoc(doc(device(), "users/alice/private/cycle")));
    await assertFails(setDoc(doc(device(), "users/alice/private/cycle"), { sharingEnabled: false }));
    await assertFails(getDoc(doc(device(), "users/alice/private/other")));
    await assertFails(setDoc(doc(device(), "users/alice/private/other"), { note: "z" }));
  });

  test("a board cannot read the couple document, releases, or other couples", async () => {
    await assertFails(getDoc(doc(device(), "couples/c1")));
    await assertFails(getDoc(doc(device(), "releases/0.1.0")));
    await assertFails(getDocs(collection(device(), "couples/c2/events")));
  });

  test("the coupleId claim must match the path", async () => {
    const wrong = { coupleId: "c2" };
    await assertFails(getDocs(collection(device(wrong), "couples/c1/events")));
    await assertFails(getDoc(doc(device(wrong), "couples/c1/devices/hs-a")));
    const none = { coupleId: null };
    await assertFails(getDocs(collection(device(none), "couples/c1/events")));
  });

  test("a board has no Storage access", async () => {
    await assertFails(getBytes(ref(deviceStorage(), "couples/c1/art/a.txt")));
    await assertFails(uploadString(ref(deviceStorage(), "couples/c1/art/d.txt"), "x"));
    await assertFails(getBytes(ref(deviceStorage(), "firmware/0.1.0/firmware.bin")));
  });

  test("people's tokens are unchanged", async () => {
    await assertSucceeds(getDoc(doc(as("alice"), "couples/c1")));
    await assertSucceeds(getDocs(collection(as("alice"), "couples/c1/devices")));
    await assertSucceeds(getDoc(doc(as("alice"), "users/alice/private/other")));
  });

  // Gaps listed by cloud-rules-auditor.
  test("a board creates its own record as its owner, with allowed fields only", async () => {
    const newBoard = device({ deviceId: "hs-new" });
    await assertSucceeds(
      setDoc(doc(newBoard, "couples/c1/devices/hs-new"), { owner: "alice", online: true, firmwareVersion: "0.1.0" }),
    );
    const other = device({ deviceId: "hs-n2" });
    await assertFails(setDoc(doc(other, "couples/c1/devices/hs-n2"), { owner: "bob" }));
    await assertFails(setDoc(doc(other, "couples/c1/devices/hs-n2"), { owner: "alice", coupleId: "c9" }));
  });

  test("a board cannot change owner, extra fields, or another owner's record, nor delete", async () => {
    await assertFails(updateDoc(doc(device(), "couples/c1/devices/hs-a"), { owner: "bob" }));
    await assertFails(updateDoc(doc(device(), "couples/c1/devices/hs-a"), { coupleId: "c2" }));
    const bobAsHsA = device({ owner: "bob" });
    await assertFails(updateDoc(doc(bobAsHsA, "couples/c1/devices/hs-a"), { online: false }));
    await assertFails(deleteDoc(doc(device(), "couples/c1/devices/hs-a")));
  });

  test("a board whose owner is not a member gets nothing in that couple", async () => {
    const m = device({ owner: "mallory", deviceId: "hs-m" });
    await assertFails(getDocs(collection(m, "couples/c1/events")));
    await assertFails(addDoc(collection(m, "couples/c1/events"), heartFrom("mallory")));
    await assertFails(setDoc(doc(m, "couples/c1/devices/hs-m"), { owner: "mallory" }));
  });

  test("writes also need the coupleId claim to match", async () => {
    for (const c of [{ coupleId: "c2" }, { coupleId: null }]) {
      const d = device(c);
      await assertFails(addDoc(collection(d, "couples/c1/events"), heartFrom("alice")));
      await assertFails(updateDoc(doc(d, "couples/c1/devices/hs-a"), { online: true }));
      await assertFails(setDoc(doc(d, "couples/c1/devices/hs-x"), { owner: "alice" }));
    }
  });

  test("a board cannot change, delete, or malform events", async () => {
    await assertFails(updateDoc(doc(device(), "couples/c1/events/e1"), { type: "touch" }));
    await assertFails(deleteDoc(doc(device(), "couples/c1/events/e1")));
    await assertFails(
      addDoc(collection(device(), "couples/c1/events"), { ...heartFrom("alice"), extra: 1 }),
    );
    await assertFails(
      addDoc(collection(device(), "couples/c1/events"), { ...heartFrom("alice"), createdAt: new Date(0) }),
    );
  });

  test("a board cannot create, list, or delete anything under users/", async () => {
    await assertFails(setDoc(doc(device({ owner: "carol", deviceId: "hs-c" }), "users/carol"), { displayName: "C" }));
    await assertFails(getDocs(collection(device(), "users/alice/private")));
    await assertFails(deleteDoc(doc(device(), "users/alice/private/cycle")));
    await env.withSecurityRulesDisabled(async (ctx) => {
      await setDoc(doc(ctx.firestore(), "users/alice/private/cycle"), { sharingEnabled: false });
    });
    await assertFails(updateDoc(doc(device(), "users/alice/private/cycle"), { sharingEnabled: true }));
  });

  test("a board cannot run collection-group queries", async () => {
    await assertFails(getDocs(collectionGroup(device(), "events")));
    await assertFails(getDocs(collectionGroup(device(), "private")));
    await assertFails(getDocs(collectionGroup(device(), "cycle")));
  });

  test("a board cannot write the couple document or releases", async () => {
    await assertFails(setDoc(doc(device(), "couples/c1"), { members: ["alice", "mallory"] }));
    await assertFails(setDoc(doc(device(), "releases/0.1.0"), { version: "0.1.0" }));
  });

  test("a board cannot upload to firmware/ or unmatched Storage paths", async () => {
    await assertFails(uploadString(ref(deviceStorage(), "firmware/0.1.0/firmware.bin"), "evil"));
    await assertFails(uploadString(ref(deviceStorage(), "elsewhere/x.txt"), "x"));
  });

  test("only the deviceId claim switches a token into board mode", async () => {
    const admin = env.authenticatedContext("alice", { admin: true }).firestore();
    await assertSucceeds(getDoc(doc(admin, "users/alice")));
    await assertSucceeds(getDoc(doc(admin, "couples/c1")));
    await assertSucceeds(getDoc(doc(admin, "users/alice/private/other")));
  });
  test("a board's owner claim decides who it acts for", async () => {
    // Events must be from the owner: not the board uid, not the partner.
    await assertFails(addDoc(collection(device(), "couples/c1/events"), heartFrom("dev_hs-a")));
    await assertFails(addDoc(collection(device(), "couples/c1/events"), heartFrom("bob")));
    await assertSucceeds(
      addDoc(collection(device({ owner: "bob", deviceId: "hs-b" }), "couples/c1/events"), heartFrom("bob")),
    );
    // A record owned by the board uid is refused.
    await assertFails(
      setDoc(doc(device({ deviceId: "hs-z" }), "couples/c1/devices/hs-z"), { owner: "dev_hs-z" }),
    );
  });

  test("a board without an owner claim gets nothing", async () => {
    const d = device({ owner: null });
    await assertFails(getDocs(collection(d, "couples/c1/events")));
    await assertFails(addDoc(collection(d, "couples/c1/events"), heartFrom("alice")));
    await assertFails(getDoc(doc(d, "couples/c1/devices/hs-a")));
    await assertFails(updateDoc(doc(d, "couples/c1/devices/hs-a"), { online: true }));
  });

  test("a board whose uid is not dev_<deviceId> gets nothing", async () => {
    for (const uid of ["alice", "dev_hs-b", "hs-a", "dev_"]) {
      const d = device({ uid });
      await assertFails(getDocs(collection(d, "couples/c1/events")));
      await assertFails(addDoc(collection(d, "couples/c1/events"), heartFrom("alice")));
      await assertFails(getDoc(doc(d, "couples/c1/devices/hs-a")));
      await assertFails(getDoc(doc(d, "users/alice")));
    }
  });

  test("a board cannot use a person's own paths even with the owner's uid", async () => {
    // A token for uid alice with board claims stays in board mode (no person access).
    const d = device({ uid: "alice" });
    await assertFails(getDoc(doc(d, "users/alice")));
    await assertFails(getDoc(doc(d, "couples/c1")));
  });
});
