using u8 = unsigned char;
using u32 = unsigned int;

struct MapTriggerHandler {
    u8 pad_00[0x20];
    u32 flags;
};

struct MapContextManager {
    u32 pad_00;
    u32 pad_04;
    MapTriggerHandler* trigger_handler;
};

struct MapContextWork {
    u32 pad_00;
    MapContextManager* manager;
};

extern "C" {
    extern MapContextWork g_MapContextWork_0044cfd0;
    void TriggerHandler_SetPendingFlag_003ba944(MapTriggerHandler* handler);

    void h4_map_dispatch_trigger_candidate();
    void h4_map_dispatch_trigger_mutation();
}

void h4_map_dispatch_trigger_candidate() {
    MapContextManager* manager = g_MapContextWork_0044cfd0.manager;
    if (manager != 0) {
        MapTriggerHandler* handler = manager->trigger_handler;
        if (handler != 0) {
            TriggerHandler_SetPendingFlag_003ba944(handler);
        }
    }
}

void h4_map_dispatch_trigger_mutation() {
    MapContextManager* manager = g_MapContextWork_0044cfd0.manager;
    if (manager != 0) {
        MapTriggerHandler* handler = manager->trigger_handler;
        if (handler == 0) { // Mutated condition
            TriggerHandler_SetPendingFlag_003ba944(handler);
        }
    }
}
