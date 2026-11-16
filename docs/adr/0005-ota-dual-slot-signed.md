# 0005: OTA uses two app slots, rollback, and signed releases

- **Date:** 2026-11-16
- **Status:** Accepted

## Decision

- The partition table (`firmware/partitions.csv`) has two app slots (`ota_0`,
  `ota_1`) plus NVS, OTA data, and a user data partition.
- New firmware boots in a pending state and must mark itself healthy within
  **60 seconds**. If it does not, the device rolls back to the previous slot.
- Every release is signed with **ECDSA P-256 over SHA-256**. The device holds the
  public key and verifies the binary before switching slots. There is no unsigned
  update path, not even for development; development flashing is over USB.

## Why

- The devices are a gift and will be far from the bench. A bad update must not
  brick them.
- Signing means a compromised Storage bucket or a network attacker cannot install
  firmware.
- P-256 is verified by mbedTLS, which is already in the ESP32 Arduino core. No
  extra library.

## Alternatives

- **Single slot:** no rollback. Rejected.
- **Ed25519:** smaller and simpler, but needs an extra library on the device.
- **ESP-IDF secure boot and flash encryption:** stronger, but burns eFuses
  irreversibly. Consider for Phase 11 only.
- **HTTPS only, no signature:** trusts the bucket and the CA store. Not enough.

## Consequences

- Each app slot is 1.75 MB on 4 MB flash. Watch the binary size as BLE and cloud
  code land. Larger flash on the final board allows bigger slots.
- The private key never enters the repo or CI logs. It lives outside the repo, and
  `firmware/keys/` is git-ignored as a guard.
- "Healthy" must be defined carefully. For now: display initialised and the main
  loop running. Phase 2b adds "cloud reachable or Wi-Fi unavailable for a known reason".
- The rollback health check is implemented now (`net/Ota.cpp`); the download and
  verify path is Phase 2b.
- Rollback relies on the bootloader's rollback support in the Arduino core;
  confirm on real hardware during bring-up.
