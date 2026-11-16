// Event functions. Data model: docs/protocol.md.
import { FieldValue, getFirestore } from "firebase-admin/firestore";
import { HttpsError, onCall } from "firebase-functions/v2/https";

/**
 * sendHeart: writes a `heart` event to the caller's couple event stream.
 * The partner's app and device listen for events where `from` is not themselves.
 *
 * The couple is derived from server data (users/{uid}.coupleId), never from
 * client input, and membership is re-checked against the couple document.
 */
export const sendHeart = onCall(async (request) => {
  const uid = request.auth?.uid;
  if (!uid) {
    throw new HttpsError("unauthenticated", "Sign in to send a heart.");
  }

  const db = getFirestore();
  const coupleId: unknown = (await db.doc(`users/${uid}`).get()).get("coupleId");
  if (typeof coupleId !== "string" || coupleId.length === 0) {
    throw new HttpsError("failed-precondition", "You are not paired yet.");
  }

  const members: unknown = (await db.doc(`couples/${coupleId}`).get()).get("members");
  if (!Array.isArray(members) || !members.includes(uid)) {
    throw new HttpsError("permission-denied", "You are not a member of this couple.");
  }

  const ref = await db.collection(`couples/${coupleId}/events`).add({
    type: "heart",
    from: uid,
    payload: {},
    createdAt: FieldValue.serverTimestamp(),
  });
  return { eventId: ref.id };
});
