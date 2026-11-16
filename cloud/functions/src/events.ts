// Event functions. Data model: docs/protocol.md.
import { FieldValue, getFirestore } from "firebase-admin/firestore";
import { onCall } from "firebase-functions/v2/https";

import { resolveCaller } from "./caller";

/**
 * sendHeart: writes a `heart` event to the caller's couple event stream.
 * The partner's app and device listen for events where `from` is not themselves.
 *
 * Callers are people or boards. A board posts as its owner (the `owner` claim);
 * see resolveCaller for the checks. The couple is derived from server data, never
 * from client input, and membership is re-checked against the couple document.
 */
export const sendHeart = onCall(async (request) => {
  const { personUid, coupleId } = await resolveCaller(request);
  const ref = await getFirestore().collection(`couples/${coupleId}/events`).add({
    type: "heart",
    from: personUid,
    payload: {},
    createdAt: FieldValue.serverTimestamp(),
  });
  return { eventId: ref.id };
});
