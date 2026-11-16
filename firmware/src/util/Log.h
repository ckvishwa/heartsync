// Serial log macros. Format: [millis][level][tag] message
//   [    1234][I][wifi] connected, ip=192.168.1.20
// Never log secrets or cycle data. Never log from an ISR.
#pragma once

#include <stdio.h>

#ifdef ARDUINO
#include <Arduino.h>
#define HS_LOG_WRITE(...) Serial.printf(__VA_ARGS__)
#define HS_LOG_MILLIS() ((unsigned long)millis())
#else
#define HS_LOG_WRITE(...) printf(__VA_ARGS__)
#define HS_LOG_MILLIS() (0UL)
#endif

#define HS_LOG(level, tag, fmt, ...) \
    HS_LOG_WRITE("[%8lu][%c][%s] " fmt "\n", HS_LOG_MILLIS(), level, tag, ##__VA_ARGS__)

#define LOGE(tag, fmt, ...) HS_LOG('E', tag, fmt, ##__VA_ARGS__)
#define LOGW(tag, fmt, ...) HS_LOG('W', tag, fmt, ##__VA_ARGS__)
#define LOGI(tag, fmt, ...) HS_LOG('I', tag, fmt, ##__VA_ARGS__)
#define LOGD(tag, fmt, ...) HS_LOG('D', tag, fmt, ##__VA_ARGS__)
