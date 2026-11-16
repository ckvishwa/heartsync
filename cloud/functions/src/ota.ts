// STUB, filled in Phase 2b (signed OTA).
//
// Plan: publish a release record (releases/{version}) from a signed manifest
// produced by firmware/tools/sign_firmware.py, after re-verifying the signature
// server-side. Devices read the record, download from Storage `firmware/`, and
// verify the signature again before switching slots.
// Never publish a release without a valid signature.
export {};
