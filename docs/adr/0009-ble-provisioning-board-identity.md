# 0009: BLE Wi-Fi setup and a board identity of its own

- **Date:** 2026-11-16
- **Status:** Accepted (built; hardware test pending). Amended 2026-11-16:
  pairing changed to numeric comparison with a BOOT confirm (setup protocol 2).

## Decision

A board in setup mode exposes one BLE GATT service. The app pairs with it by
numeric comparison (the same code on the OLED and the phone, confirmed with a BOOT
tap on the board), sends the Wi-Fi details, calls `registerDevice`, and hands the
board a Firebase custom token over the encrypted link.

The token is for the board's **own uid** `dev_<deviceId>`, with claims
`{deviceId, coupleId, owner}`. The board exchanges it for a refresh token at once,
and from then on acts for its owner only through the `owner` claim. It never holds
the owner's account.

Wire format: `docs/protocol.md` "BLE provisioning". Rules: "Device tokens".

## Why

- **Least privilege.** A board signed in as its owner could call Firebase Auth
  account APIs (set a password, delete the account) that security rules never see.
  A separate uid limits a stolen board to its couple's events and its own device
  record. The rules check `uid == "dev_" + deviceId` plus the `owner` claim, and
  `cloud-rules-auditor` reviewed them.
- **No per-board files.** Wi-Fi and credentials no longer come from `secrets.h` or
  USB serial. A new board needs only the app.
- **Numeric comparison, confirmed with BOOT** (amended; it was passkey entry).
  - At the user's request ("pairing should just match, not typing"), both sides
    are DisplayYesNo: the same 6-digit code shows on the OLED and on the phone.
    The user taps Pair on the phone and BOOT on the board. Still LE Secure
    Connections and still an authenticated (MITM-protected) link.
  - Why the BOOT tap: without a "yes" on the board, anyone in radio range could
    pair while the board advertises. The tap keeps physical presence, which the
    typed passkey gave before. It counts only while a pairing is waiting, only
    for a press that began after the code appeared, and is never queued. It
    protects only if the user compares the codes: a blind tap accepts a
    stranger's request. No tap within 25 s rejects the pairing.
  - LE Secure Connections only: `CONFIG_BT_NIMBLE_SM_SC_ONLY` in the NimBLE host,
    and the callback also checks for a 16-byte key.
  - Every characteristic needs an encrypted, authenticated link.
  - A new code per pairing (the SMP exchange makes it). Bonds are deleted at
    every setup start and after every session.
  - Lockout after 3 failed pairings, stored in NVS, until BOOT is held. A phone
    that connects but never pairs is dropped after 60 s. Someone nearby can burn
    the 3 tries on purpose (a nuisance, no access); a BOOT hold clears it.
    Accepted.
- **BOOT hold while running, not at power-up.** GPIO 0 is a strapping pin. Held at
  power-up, the ESP32 enters its ROM download mode. So a 5 s hold while running
  wipes Wi-Fi and tokens and restarts into setup, and a short tap still sends a
  heart.
- **Board-side protocol facts** found while building:
  - A BLE attribute value is at most 512 bytes. The custom token (~1 KB) is
    therefore sent in numbered 180-byte chunks plus an end frame with length
    and CRC32 (proto 2), rather than one long write.
  - A notification holds only MTU-3 bytes (about 182 on a default iOS link), so
    the Wi-Fi list is paged and the notify is only a "page ready" signal; the
    app reads each page.
  - Board tokens cannot read `users/` or the couple document. The board therefore
    takes its couple and owner from its ID token claims, and polls all events after
    its cursor, skipping its owner's own. The cursor also advances past skipped
    events.
- **`deviceRegistry/{deviceId}`** (server only) stops one couple from claiming, or
  revoking the sessions of, a board another couple owns. Only `registerDevice` or
  the board itself creates device records. Without that, a partner could pre-claim
  the other's board id.

## Accepted risks (user decisions, 2026-11-16)

- **B. Custom token lifetime is fixed at 1 h** by Firebase, and a custom token
  is **reusable** within that hour (it is not single use): anyone who copied it
  could sign in as the board until it expires. Mitigations:
  - It travels only over the encrypted BLE link, within seconds.
  - The board holds it in RAM, signs in with it once and wipes it. It is never
    written to NVS on the BLE path.
  - Re-registering a board revokes its older sessions. Revocation stops
    refreshes only: the security rules do not check revocation, so a revoked
    board's ID token already issued keeps working for up to 1 h.
  - The Auth emulator does not enforce revocation on refresh, so tests check
    `verifyIdToken(..., checkRevoked)`.
- **C. Wi-Fi password and refresh token sit in plain NVS** on the bench boards. The
  flash and NVS encryption eFuses are burned only after the release-build gate in
  `docs/phases.md` (Phase 11).
- **Board-id squatting (open, auditor finding 1).** Board ids come from the MAC and
  are visible over BLE. A paired user could register a stranger's board first, and
  the real owner then gets "registered to someone else". No data leaks: the squatter
  gets a token for their own couple only. Fix later with a proof-of-possession
  challenge (a per-board key signs a server nonce) plus an admin unregister path.
- **Re-pairing an owner to a new couple** cannot re-register their board yet: the
  registry keeps the old couple. Unregister comes with the partner-invite work.
- **flutter_blue_plus 2.x license.** The app passes `License.nonprofit` (personal
  use). Any commercial use needs a paid FBP license or another BLE plugin.

## Alternatives

- **Owner uid plus claims.** Simpler, but leaves Auth account APIs open to a board.
  Rejected (decision A).
- **Board stores the custom token and signs in later.** It would sit in NVS for up
  to an hour. Rejected: RAM only, used at once.
- **Long write for the token.** BLE caps attribute values at 512 bytes. Rejected for
  framed chunks.
- **Passkey entry (proto 1).** Physical presence by typing the OLED PIN. Replaced
  at the user's request by numeric comparison plus a BOOT tap, which keeps
  presence with less typing.
- **Numeric comparison without a board-side confirm** (auto-accept). Anyone in
  range could pair. Rejected.
- **Wi-Fi SoftAP captive portal.** It needs the phone to leave its network, and it
  has no passkey binding to the device's own display. Rejected.

## Consequences

- Bench boards provisioned before this hold plain owner tokens. The new firmware
  refuses them (wrong uid, no claims) and shows `SETUP NEEDED`. Set them up again
  over BLE, or use `seed_couple.py --mint-tokens` (now minting board identities)
  with serial provisioning on bench builds.
- Bench-only build flags (`HS_DEV_WIFI_FALLBACK`, `HS_DEV_SERIAL_TOKEN`) exist on
  `esp32dev` only and must never reach a release env.
- NimBLE adds about 280 KB flash on esp32dev (47% to 63%) and 10 KB static RAM.
  Runtime heap with BLE plus Wi-Fi is measured on the bench (`status` prints free
  and minimum heap).
- OTA (Phase 2b) still needs an explicit, tested exception for board tokens to read
  releases or firmware.
