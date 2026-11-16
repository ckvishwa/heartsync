#!/usr/bin/env bash
# AVD regression suite: real app + real Firebase emulators + simulated board.
# Needs: emulators running and seeded (cd cloud && npm run emulators; npm run seed),
# an Android emulator running (adb devices shows emulator-NNNN).
# Screenshots: build/avd_screens/*.png
set -euo pipefail
cd "$(dirname "$0")/.."
device="${1:-$(adb devices | awk '/^emulator-/{print $1; exit}')}"
if [ -z "$device" ]; then echo "no Android emulator running" >&2; exit 1; fi
rm -rf build/avd_screens
flutter drive -d "$device" \
  --driver=test_driver/integration_test.dart \
  --target=integration_test/app_test.dart \
  --dart-define-from-file=config/emulator.json \
  --dart-define=SIMULATED_BOARD=true
