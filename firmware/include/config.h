// heartsync firmware configuration.
//
// ALL pins and hardware constants live here, one section per board.
// Keep docs/hardware/pinout.md in sync. Never put a pin number anywhere else.
#pragma once

#define HS_FW_VERSION "0.1.0"

// ---------------------------------------------------------------------------
// Display driver selection: -DDISPLAY_DRIVER=ssd1306 | small_led | hub75 (platformio.ini)
// ---------------------------------------------------------------------------
#define HS_DISPLAY_ID_small_led 1
#define HS_DISPLAY_ID_hub75 2
#define HS_DISPLAY_ID_ssd1306 3
#define HS_CAT_(a, b) a##b
#define HS_CAT(a, b) HS_CAT_(a, b)
#ifndef DISPLAY_DRIVER
#define DISPLAY_DRIVER ssd1306
#endif
#define HS_DISPLAY_ID HS_CAT(HS_DISPLAY_ID_, DISPLAY_DRIVER)
#define HS_DISPLAY_IS_SMALL_LED (HS_DISPLAY_ID == HS_DISPLAY_ID_small_led)
#define HS_DISPLAY_IS_HUB75 (HS_DISPLAY_ID == HS_DISPLAY_ID_hub75)
#define HS_DISPLAY_IS_SSD1306 (HS_DISPLAY_ID == HS_DISPLAY_ID_ssd1306)

// ---------------------------------------------------------------------------
// Board: ESP32-S3 DevKitC-1
// ---------------------------------------------------------------------------
#if defined(HS_BOARD_ESP32_S3_DEVKITC)
#define HS_BOARD_NAME "esp32-s3-devkitc-1"
#define HS_PIN_LED_DATA 5    // small_led driver only
#define HS_PIN_I2C_SDA 8     // OLED SDA
#define HS_PIN_I2C_SCL 9     // OLED SCL
#define HS_PIN_BUTTON 0      // BOOT button, active low, input only

// ---------------------------------------------------------------------------
// Board: classic ESP32 DevKit
// ---------------------------------------------------------------------------
#elif defined(HS_BOARD_ESP32_DEV)
#define HS_BOARD_NAME "esp32dev"
#define HS_PIN_LED_DATA 4    // small_led driver only
#define HS_PIN_I2C_SDA 21    // OLED SDA
#define HS_PIN_I2C_SCL 22    // OLED SCL
#define HS_PIN_BUTTON 0      // BOOT button, active low, input only

// ---------------------------------------------------------------------------
// Host (native tests): no pins
// ---------------------------------------------------------------------------
#elif defined(HS_NATIVE)
#define HS_BOARD_NAME "native"

#else
#error "No board selected. Add a section to config.h and a -DHS_BOARD_... flag in platformio.ini."
#endif

// ---------------------------------------------------------------------------
// Logical canvas. Art and game logic always draw at this size, the size of the
// final 64x32 P2 HUB75 panel. Drivers scale it to their hardware.
// ---------------------------------------------------------------------------
#define HS_LOGICAL_WIDTH 64
#define HS_LOGICAL_HEIGHT 32

// ---------------------------------------------------------------------------
// SSD1306 OLED (bench display): 0.96 inch, 128x64, monochrome, I2C.
// The 64x32 logical canvas is scaled 2x (each logical pixel is a 2x2 block).
// ---------------------------------------------------------------------------
#define HS_OLED_WIDTH 128
#define HS_OLED_HEIGHT 64
#define HS_OLED_SCALE 2
#define HS_OLED_I2C_HZ 400000
#define HS_OLED_FLIP 0                 // 1: rotate 180 degrees (hardware flip)
#define HS_MONO_THRESHOLD 24           // luma 0..255; above this a pixel is on
#define HS_OLED_IDLE_DIM_MS 30000      // contrast drops after this much idle time
#define HS_OLED_IDLE_OFF_MS 600000     // panel off after this much idle time (burn-in)
#define HS_OLED_DIM_PERCENT 5          // contrast while dimmed
#define HS_OLED_CONTRAST_DEFAULT_PERCENT 100

// ---------------------------------------------------------------------------
// Input: BOOT button debounce
// ---------------------------------------------------------------------------
#define HS_BUTTON_DEBOUNCE_MS 30
#define HS_SERIAL_LINE_MAX 2048        // longest serial command (custom tokens are ~1 KB)

// ---------------------------------------------------------------------------
// Small LED display, small_led driver only (assumption: 8x8 WS2812B matrix, see docs/phases.md)
// ---------------------------------------------------------------------------
#define HS_MATRIX_WIDTH 8
#define HS_MATRIX_HEIGHT 8      // set to 1 for a strip
#define HS_MATRIX_SERPENTINE 1  // 1: odd rows run right to left; 0: all rows left to right
#define HS_LED_CHIPSET WS2812B
#define HS_LED_COLOR_ORDER GRB

// ---------------------------------------------------------------------------
// HUB75 panel (Phase 1b). Pins are assigned when the panel arrives.
// ---------------------------------------------------------------------------
#define HS_HUB75_WIDTH 64
#define HS_HUB75_HEIGHT 32

// ---------------------------------------------------------------------------
// LED power limits (small_led and hub75 drivers). Do not raise until power is
// characterised in Phase 8. The OLED draws a few mA and maps brightness
// straight to its contrast register.
// ---------------------------------------------------------------------------
#define HS_BRIGHTNESS_CAP_PERCENT 25
#define HS_BRIGHTNESS_DEFAULT_PERCENT 25
#define HS_LED_SUPPLY_VOLTS 5
#define HS_LED_MAX_MILLIAMPS 400  // USB bench power budget for the LED

// ---------------------------------------------------------------------------
// Network and OTA
// ---------------------------------------------------------------------------
#define HS_WIFI_RETRY_MS 15000
#define HS_OTA_HEALTH_TIMEOUT_MS 60000  // roll back if not healthy by then
#define HS_SERIAL_BAUD 115200

// ---------------------------------------------------------------------------
// Cloud sync (Phase 2). Emulator host and Wi-Fi come from secrets.h.
// ---------------------------------------------------------------------------
#define HS_EMU_PORT_AUTH 9099          // must match cloud/firebase.json
#define HS_EMU_PORT_FIRESTORE 8080
#define HS_EMU_PORT_FUNCTIONS 5001
#define HS_FUNCTIONS_REGION "us-central1"
#define HS_CLOUD_POLL_MS 2000          // event poll interval
#define HS_CLOUD_HEARTBEAT_MS 60000    // device heartbeat interval
#define HS_CLOUD_HTTP_TIMEOUT_MS 3000
#define HS_CLOUD_CALL_TIMEOUT_MS 10000  // sendHeart: a cold function can take several seconds
#define HS_CLOUD_RETRY_MIN_MS 2000
#define HS_CLOUD_RETRY_MAX_MS 30000

// ---------------------------------------------------------------------------
// BLE Wi-Fi setup (Phase 3, ADR 0009). Mirrored in docs/protocol.md
// "BLE provisioning" and in the app (lib/data/board_setup_protocol.dart).
// UUIDs: one random base, the first group numbers the characteristic.
// ---------------------------------------------------------------------------
#define HS_SETUP_PROTO 2   // 2: numeric comparison pairing, paged Wi-Fi list
#define HS_SETUP_NAME_PREFIX "heartsync-"      // + last 4 hex of the device id
#define HS_SETUP_UUID_SERVICE "6a350000-4898-4679-a24f-021d40cfd52a"
#define HS_SETUP_UUID_INFO "6a350001-4898-4679-a24f-021d40cfd52a"
#define HS_SETUP_UUID_WIFI_SCAN "6a350002-4898-4679-a24f-021d40cfd52a"
#define HS_SETUP_UUID_WIFI_LIST "6a350003-4898-4679-a24f-021d40cfd52a"
#define HS_SETUP_UUID_WIFI_CREDS "6a350004-4898-4679-a24f-021d40cfd52a"
#define HS_SETUP_UUID_TOKEN "6a350005-4898-4679-a24f-021d40cfd52a"
#define HS_SETUP_UUID_STATUS "6a350006-4898-4679-a24f-021d40cfd52a"
#define HS_SETUP_LONG_PRESS_MS 5000            // hold BOOT this long (while running) to reset
#define HS_SETUP_TAP_MAX_MS 1000               // shorter press = tap (send heart)
#define HS_SETUP_WINDOW_MS (15UL * 60UL * 1000UL)  // advertise this long, then stop
#define HS_SETUP_MAX_FAILS 3                   // wrong passkeys before lockout
#define HS_SETUP_MTU 247
#define HS_SETUP_TOKEN_MAX 1536                // custom token, bytes
#define HS_SETUP_WIFI_LIST_MAX 40
#define HS_SETUP_CONFIRM_MS 25000              // time to tap BOOT to confirm the pairing code
                                               // (under the 30 s SMP timeout, so ours fires)
#define HS_SETUP_WIFI_CONNECT_MS 20000         // give up on a Wi-Fi test after this
#define HS_SETUP_REBOOT_DELAY_MS 3000          // after signed_in, then reboot to normal
