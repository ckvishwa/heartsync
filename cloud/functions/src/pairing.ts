// Pairing functions. Data model: docs/protocol.md, ADR 0009.
//
// registerDevice (Phase 3): the app calls it during BLE setup and hands the
// returned custom token to the board over the encrypted BLE link.
//
// Still to come: callables to create a couple and invite or accept a partner.
// They will be the only writers of `couples/{id}.members` and
// `users/{uid}.coupleId`. Until then couples come from cloud/emulator/seed.mjs
// (emulator) and tools/seed_couple.py (real project).
import { getAuth } from "firebase-admin/auth";
import { FieldValue, getFirestore } from "firebase-admin/firestore";
import { HttpsError, onCall } from "firebase-functions/v2/https";

import { DEVICE_ID_RE, boardUid, resolveCaller } from "./caller";

/**
 * registerDevice({deviceId}) -> {token}
 *
 * Records the board under the caller's couple and mints a custom token for the
 * board's own uid dev_<deviceId> with claims {deviceId, coupleId, owner}. The
 * board exchanges it for a refresh token at once. Custom tokens live 1 h
 * (fixed by Firebase).
 *
 * - People only: a board token cannot register boards.
 * - A board registered to another owner is refused.
 * - Re-registering your own board revokes its old sessions first.
 *
 * Never logs the token. Never calls setCustomUserClaims (that would put the
 * caller's own phone sessions into board mode).
 */
export const registerDevice = onCall(async (request) => {
  if (request.auth?.token?.deviceId !== undefined) {
    throw new HttpsError("permission-denied", "Boards cannot register boards.");
  }
  const data = request.data as { deviceId?: unknown } | undefined;
  const deviceId = data?.deviceId;
  if (typeof deviceId !== "string" || !DEVICE_ID_RE.test(deviceId)) {
    throw new HttpsError("invalid-argument", "deviceId must be hs- and 12 hex digits.");
  }
  const { personUid, coupleId } = await resolveCaller(request);

  const db = getFirestore();
  // deviceRegistry/{deviceId} is global and server-only (no client rule): it stops
  // one couple from claiming, or revoking, a board another couple owns.
  const registry = db.doc(`deviceRegistry/${deviceId}`);
  const ref = db.doc(`couples/${coupleId}/devices/${deviceId}`);
  await db.runTransaction(async (tx) => {
    const reg = await tx.get(registry);
    const snap = await tx.get(ref);
    if (reg.exists && (reg.get("owner") !== personUid || reg.get("coupleId") !== coupleId)) {
      throw new HttpsError("already-exists", "This board is registered to someone else.");
    }
    const owner: unknown = snap.get("owner");
    if (snap.exists && owner !== personUid) {
      throw new HttpsError("already-exists", "This board is registered to someone else.");
    }
    if (!reg.exists) {
      tx.create(registry, {
        owner: personUid,
        coupleId,
        registeredAt: FieldValue.serverTimestamp(),
      });
    }
    if (snap.exists) {
      tx.update(ref, { online: false, lastSeen: FieldValue.serverTimestamp() });
    } else {
      tx.create(ref, {
        owner: personUid,
        firmwareVersion: "unknown",
        online: false,
        lastSeen: FieldValue.serverTimestamp(),
      });
    }
  });

  const auth = getAuth();
  const uid = boardUid(deviceId);
  try {
    await auth.revokeRefreshTokens(uid);
  } catch (e) {
    if ((e as { code?: string }).code !== "auth/user-not-found") {
      throw e;
    }
  }
  const token = await auth.createCustomToken(uid, { deviceId, coupleId, owner: personUid });
  return { token };
});
