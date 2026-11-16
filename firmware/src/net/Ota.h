// OTA health check and rollback. See docs/adr/0005-ota-dual-slot-signed.md.
//
// Implemented now: after an OTA update the new firmware boots "pending verify".
// It must call reportHealthy() within HS_OTA_HEALTH_TIMEOUT_MS (60 s) or the
// device rolls back to the previous slot and reboots.
//
// Phase 2b: download, ECDSA P-256 signature verification, slot switch.
// There is deliberately no update path until signature verification exists.
#pragma once

namespace hs {
namespace ota {

// Call early in setup(). Arms the rollback timer if this boot is pending verify.
void begin();

// Call once the firmware knows it works (display up, main loop running).
void reportHealthy();

// True while this boot is still waiting to be marked healthy.
bool pendingVerify();

// Always refuses until Phase 2b adds signature verification.
bool startUpdate(const char* manifestUrl);

}  // namespace ota
}  // namespace hs
