// Minimal in-process publish/subscribe for events. Hardware-free.
//
// publish() calls handlers synchronously on the caller's task. It is NOT safe
// to call from an ISR or from two tasks at once. If cross-task delivery is
// needed later, put a FreeRTOS queue in front of it.
#pragma once

#include <stddef.h>

#include "events/Event.h"

namespace hs {

class EventBus {
public:
    using Handler = void (*)(const Event& event, void* context);

    static constexpr size_t kMaxSubscribers = 8;

    // Returns false if the handler is null or the bus is full.
    bool subscribe(Handler handler, void* context = nullptr);

    // Deliver the event to every subscriber, in subscription order.
    void publish(const Event& event) const;

    size_t subscriberCount() const { return count_; }

private:
    struct Slot {
        Handler handler;
        void* context;
    };
    Slot slots_[kMaxSubscribers] = {};
    size_t count_ = 0;
};

}  // namespace hs
