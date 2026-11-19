---
name: release-firmware
description: Build, sign, record, and version-bump a firmware release
argument-hint: <version, e.g. 0.2.0>
disable-model-invocation: true
---

Release firmware version "$ARGUMENTS".

1. Check the working tree is clean and `pio test -e native` passes (in `firmware/`). Stop if not.
2. Set `HS_FW_VERSION` in `firmware/include/config.h` to "$ARGUMENTS".
3. Build: `pio run -e esp32-s3-devkitc-1` (and any other release env I name).
4. Sign: `python firmware/tools/sign_firmware.py sign --key <private key path I give you> --version $ARGUMENTS --env <env> firmware/.pio/build/<env>/firmware.bin`. Never read or print the private key. The script writes `firmware/release/<version>/` with the binary, signature, and `manifest.json`.
5. Verify: `python firmware/tools/sign_firmware.py verify ...` with the public key. Stop if it fails.
6. Upload the release record: show me the manifest and the planned Storage path (`firmware/<version>/`) and Firestore doc (`releases/<version>`), then **ask before uploading**. Uploads to a real project go through CI or my explicit go-ahead.
7. Commit the version bump as `firmware: release v$ARGUMENTS` and suggest the git tag. Do not push.

Never produce or upload an unsigned release.
