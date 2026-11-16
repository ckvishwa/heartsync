// Who is calling a callable, and for which couple. Data model: docs/protocol.md.
import { getFirestore } from "firebase-admin/firestore";
import { CallableRequest, HttpsError } from "firebase-functions/v2/https";

/** A board's own uid: one account per board, never its owner's (ADR 0009). */
export const boardUid = (deviceId: string): string => `dev_${deviceId}`;

/** Board ids are "hs-" + 12 lowercase hex digits of the MAC. */
export const DEVICE_ID_RE = /^hs-[0-9a-f]{12}$/;

export interface Caller {
  /** The person the call acts for: the caller, or the board's owner. */
  personUid: string;
  /** The couple, from server data and re-checked against its members. */
  coupleId: string;
  /** Set when the caller is a board token. */
  deviceId?: string;
}

/**
 * Resolves the caller to a person and their couple.
 *
 * - Person tokens: the couple comes from users/{uid}.coupleId.
 * - Board tokens (any token with a deviceId claim): the uid must be
 *   dev_<deviceId>, the owner claim must be set, and the coupleId claim must equal
 *   the owner's current couple (a board set up before a re-pair is refused).
 *
 * In both cases membership is re-checked against couples/{id}.members.
 */
export async function resolveCaller(request: CallableRequest<unknown>): Promise<Caller> {
  const auth = request.auth;
  if (!auth?.uid) {
    throw new HttpsError("unauthenticated", "Sign in first.");
  }
  const token = auth.token as Record<string, unknown>;
  const db = getFirestore();

  let personUid = auth.uid;
  let deviceId: string | undefined;
  if ("deviceId" in token) {
    const claimed = token.deviceId;
    const owner = token.owner;
    if (
      typeof claimed !== "string" ||
      auth.uid !== boardUid(claimed) ||
      typeof owner !== "string" ||
      owner.length === 0 ||
      typeof token.coupleId !== "string"
    ) {
      throw new HttpsError("permission-denied", "Malformed board token.");
    }
    personUid = owner;
    deviceId = claimed;
  }

  const coupleId: unknown = (await db.doc(`users/${personUid}`).get()).get("coupleId");
  if (typeof coupleId !== "string" || coupleId.length === 0) {
    throw new HttpsError("failed-precondition", "You are not paired yet.");
  }
  if (deviceId !== undefined && token.coupleId !== coupleId) {
    throw new HttpsError("permission-denied", "This board belongs to another couple.");
  }

  const members: unknown = (await db.doc(`couples/${coupleId}`).get()).get("members");
  if (!Array.isArray(members) || !members.includes(personUid)) {
    throw new HttpsError("permission-denied", "You are not a member of this couple.");
  }
  return { personUid, coupleId, deviceId };
}
