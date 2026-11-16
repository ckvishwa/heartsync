#include "net/Ota.h"

#include <Arduino.h>
#include <esp_ota_ops.h>
#include <esp_timer.h>

#include "config.h"
#include "util/Log.h"

// The Arduino core marks a pending image valid during startup unless this
// returns true. We return true so that the firmware has to prove it is healthy.
extern "C" bool verifyRollbackLater() { return true; }

namespace hs {
namespace ota {

namespace {

volatile bool s_pending = false;
esp_timer_handle_t s_timer = nullptr;

// Runs on the esp_timer task, so it fires even if setup() or loop() hangs.
void onHealthTimeout(void*) {
    if (!s_pending) {
        return;
    }
    LOGE("ota", "not healthy after %d ms: rolling back", HS_OTA_HEALTH_TIMEOUT_MS);
    esp_ota_mark_app_invalid_rollback_and_reboot();
}

}  // namespace

void begin() {
    const esp_partition_t* running = esp_ota_get_running_partition();
    esp_ota_img_states_t state = ESP_OTA_IMG_UNDEFINED;
    if (running != nullptr && esp_ota_get_state_partition(running, &state) == ESP_OK &&
        state == ESP_OTA_IMG_PENDING_VERIFY) {
        s_pending = true;
        const int64_t elapsedUs = esp_timer_get_time();
        const int64_t budgetUs = static_cast<int64_t>(HS_OTA_HEALTH_TIMEOUT_MS) * 1000;
        const int64_t remainingUs = budgetUs > elapsedUs ? budgetUs - elapsedUs : 1;
        const esp_timer_create_args_t args = {
            .callback = &onHealthTimeout,
            .arg = nullptr,
            .dispatch_method = ESP_TIMER_TASK,
            .name = "ota_health",
            .skip_unhandled_events = false,
        };
        if (esp_timer_create(&args, &s_timer) != ESP_OK ||
            esp_timer_start_once(s_timer, static_cast<uint64_t>(remainingUs)) != ESP_OK) {
            // Without a timer we cannot guarantee the 60 s rule. Fail safe.
            LOGE("ota", "cannot arm health timer: rolling back");
            esp_ota_mark_app_invalid_rollback_and_reboot();
        }
        LOGW("ota", "new firmware pending verify, slot=%s", running->label);
    } else {
        LOGI("ota", "running slot=%s", running != nullptr ? running->label : "?");
    }
}

void reportHealthy() {
    if (!s_pending) {
        return;
    }
    s_pending = false;
    if (s_timer != nullptr) {
        esp_timer_stop(s_timer);
    }
    esp_ota_mark_app_valid_cancel_rollback();
    LOGI("ota", "firmware marked healthy");
}

bool pendingVerify() { return s_pending; }

bool startUpdate(const char* manifestUrl) {
    (void)manifestUrl;
    LOGE("ota", "update refused: signature verification not implemented (Phase 2b)");
    return false;
}

}  // namespace ota
}  // namespace hs
