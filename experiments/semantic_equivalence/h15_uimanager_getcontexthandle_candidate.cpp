#include <cstdint>
typedef uint32_t u32;

struct UiContextManager {
    u32 pad;
    u32 handle;
};

extern "C" {
    extern UiContextManager g_UiContextManager_0043e2a8;
}

extern "C" u32 h15_uimanager_getcontexthandle_candidate() {
    return g_UiContextManager_0043e2a8.handle;
}

extern "C" u32 h15_uimanager_getcontexthandle_mutation() {
    return g_UiContextManager_0043e2a8.handle ^ 1;
}
