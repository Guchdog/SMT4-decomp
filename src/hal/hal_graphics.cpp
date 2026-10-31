#include "hal/hal_graphics.h"

namespace smt4::hal {

static bool s_gfx_init = false;
static bool s_3d_mode = false;
static FramebufferConfig s_targets[3]{};

bool Graphics_Init() {
    s_gfx_init = true;
    s_3d_mode = false;
    return true;
}

void Graphics_Shutdown() {
    s_gfx_init = false;
}

void Graphics_Set3DMode(bool enabled) {
    s_3d_mode = enabled;
}

bool Graphics_Is3DMode() {
    return s_3d_mode;
}

void Graphics_SetFramebuffer(DisplayTarget target, const FramebufferConfig& config) {
    u32 idx = static_cast<u32>(target);
    if (idx < 3) {
        s_targets[idx] = config;
    }
}

void Graphics_Present() {
    // Platform flip simulation
}

void Graphics_WaitForVBlank() {
    // VSync barrier
}

} // namespace smt4::hal
