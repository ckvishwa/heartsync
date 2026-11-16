#include "events/EventBus.h"

namespace hs {

bool EventBus::subscribe(Handler handler, void* context) {
    if (handler == nullptr || count_ >= kMaxSubscribers) {
        return false;
    }
    slots_[count_++] = Slot{handler, context};
    return true;
}

void EventBus::publish(const Event& event) const {
    for (size_t i = 0; i < count_; ++i) {
        slots_[i].handler(event, slots_[i].context);
    }
}

}  // namespace hs
