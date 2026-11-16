// heartsync firmware configuration.
//
// ALL pins and hardware constants live here, one section per board.
// Keep docs/hardware/pinout.md in sync. Never put a pin number anywhere else.
#pragma once

#define HS_FW_VERSION "0.1.0"

// ---------------------------------------------------------------------------
// Display driver selection: -DDISPLAY_DRIVER=small_led | hub75 (platformio.ini)
// ---------------------------------------------------------------------------
#define HS_DISPLAY_ID_small_led 1
#define HS_DISPLAY_ID_hub75 2
#define HS_CAT_(a, b) a##b
#define HS_CAT(a, b) HS_CAT_(a, b)
#ifndef DISPLAY_DRIVER
#define DISPLAY_DRIVER small_led
#endif
#define HS_DISPLAY_ID HS_CAT(HS_DISPLAY_ID_, DISPLAY_DRIVER)
#define HS_DISPLAY_IS_SMALL_LED (HS_DISPLAY_ID == HS_DISPLAY_ID_small_led)
#define HS_DISPLAY_IS_HUB75 (HS_DISPLAY_ID == HS_DISPLAY_ID_hub75)

// ---------------------------------------------------------------------------
// Board: ESP32-S3 DevKitC-1
// ---------------------------------------------------------------------------
#if defined(HS_BOARD_ESP32_S3_DEVKITC)
#define HS_BOARD_NAME "esp32-s3-devkitc-1"
#define HS_PIN_LED_DATA 5

// ---------------------------------------------------------------------------
// Board: classic ESP32 DevKit
// ---------------------------------------------------------------------------
#elif defined(HS_BOARD_ESP32_DEV)
#define HS_BOARD_NAME "esp32dev"
#define HS_PIN_LED_DATA 4

// ---------------------------------------------------------------------------
// Host (native tests): no pins
// ---------------------------------------------------------------------------
#elif defined(HS_NATIVE)
#define HS_BOARD_NAME "native"

#else
#error "No board selected. Add a section to config.h and a -DHS_BOARD_... flag in platformio.ini."
#endif

// ---------------------------------------------------------------------------
// Small LED display (assumption: 8x8 WS2812B matrix, see docs/phases.md)
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
// Power limits. Do not raise until power is characterised in Phase 8.
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
