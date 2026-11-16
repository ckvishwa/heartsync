// Wi-Fi credentials set up over BLE, kept in NVS namespace "hs-wifi".
// Plain NVS on the bench boards until flash encryption (ADR 0009, release-build
// gate in docs/phases.md). Never log the password.
#pragma once

#include "setup/SetupCodec.h"

namespace hs {
namespace wifistore {

// False if nothing is stored.
bool load(setup::WifiCreds& out);
void save(const setup::WifiCreds& creds);
void erase();

}  // namespace wifistore

// Setup-mode flags in NVS namespace "hs-setup".
namespace setupstore {

uint8_t fails();
void setFails(uint8_t n);
// Set by the BOOT hold: the next boot enters setup mode even if Wi-Fi is known
// (bench boards fall back to secrets.h Wi-Fi otherwise).
bool forced();
void setForced(bool on);

}  // namespace setupstore
}  // namespace hs
