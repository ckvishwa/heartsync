// STUB, filled in Phase 2. See CloudClient.h for the plan.
#include "net/CloudClient.h"

#include "util/Log.h"

namespace hs {

void CloudClient::begin(const char* deviceId) {
    deviceId_ = deviceId;
    (void)bus_;
    LOGI("cloud", "sync not implemented yet (Phase 2), device=%s", deviceId_);
}

void CloudClient::loop() {}

bool CloudClient::sendHeart() {
    LOGW("cloud", "sendHeart not implemented yet (Phase 2)");
    return false;
}

}  // namespace hs
