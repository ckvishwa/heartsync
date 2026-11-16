// Loads emulator/seed.json into the RUNNING emulators (Auth + Firestore).
//   npm run emulators      (terminal 1)
//   npm run seed           (terminal 2)
//
// Emulator only: the emulator hosts are forced below, so this script cannot
// reach a real project. Use tools/seed_couple.py for a real project.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { initializeApp } from "firebase-admin/app";
import { getAuth } from "firebase-admin/auth";
import { FieldValue, getFirestore } from "firebase-admin/firestore";

process.env.FIRESTORE_EMULATOR_HOST ??= "127.0.0.1:8080";
process.env.FIREBASE_AUTH_EMULATOR_HOST ??= "127.0.0.1:9099";

const seed = JSON.parse(
  readFileSync(fileURLToPath(new URL("./seed.json", import.meta.url)), "utf8"),
);

initializeApp({ projectId: seed.projectId });
const auth = getAuth();
const db = getFirestore();

for (const user of seed.users) {
  const { uid, email, password, displayName } = user;
  try {
    await auth.createUser({ uid, email, password, displayName });
  } catch (error) {
    if (error.code !== "auth/uid-already-exists" && error.code !== "auth/email-already-exists") {
      throw error;
    }
    await auth.updateUser(uid, { email, password, displayName });
  }
  await db.doc(`users/${uid}`).set({ displayName, coupleId: seed.couple.id }, { merge: true });
  console.log(`user   ${email} (uid ${uid})`);
}

await db.doc(`couples/${seed.couple.id}`).set({
  members: seed.couple.members,
  createdAt: FieldValue.serverTimestamp(),
});
console.log(`couple ${seed.couple.id}`);

for (const { id, ...device } of seed.devices) {
  await db
    .doc(`couples/${seed.couple.id}/devices/${id}`)
    .set({ ...device, lastSeen: FieldValue.serverTimestamp() });
  await db.doc(`deviceRegistry/${id}`).set({
    owner: device.owner,
    coupleId: seed.couple.id,
    registeredAt: FieldValue.serverTimestamp(),
  });
  console.log(`device ${id} (owner ${device.owner})`);
}

console.log("Seeded. Log in with any user above; the password is in seed.json.");
