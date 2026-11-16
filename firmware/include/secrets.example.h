// Copy this file to secrets.h and fill it in. secrets.h is git-ignored.
//   cp include/secrets.example.h include/secrets.h
// Never commit real values. Never log them.
#pragma once

#define HS_WIFI_SSID "your-wifi-name"
#define HS_WIFI_PASSWORD "your-wifi-password"

// Phase 2 (CloudClient), emulator. Set the PC's LAN IP running the Firebase
// emulators, e.g. "10.0.0.18". Empty disables sync.
#define HS_FIREBASE_EMULATOR_HOST ""
#define HS_FIREBASE_PROJECT_ID "demo-heartsync"
#define HS_FIREBASE_API_KEY ""  // empty is fine for the emulator

// The device's custom token is NOT stored here (one secrets.h serves both boards).
// It is provisioned per board over serial into NVS: tools/provision_device.py.
// The device finds its couple from users/{uid}.coupleId.
