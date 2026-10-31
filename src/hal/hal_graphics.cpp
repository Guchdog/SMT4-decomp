#include "hal/hal_graphics.h"

#if defined(__arm__)

namespace smt4::hal {

static bool s_gfx_init = false;
static bool s_3d_mode = false;
static u64 s_present_count = 0;
static FramebufferConfig s_targets[3]{};

bool Graphics_Init() {
    s_gfx_init = true;
    s_3d_mode = false;
    s_present_count = 0;
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
    s_present_count++;
}

void Graphics_WaitForVBlank() {
    // VSync barrier for 3DS PICA200 / GSP
}

u64 Graphics_GetPresentCount() {
    return s_present_count;
}

const FramebufferConfig* Graphics_GetFramebuffer(DisplayTarget target) {
    u32 idx = static_cast<u32>(target);
    if (idx < 3) return &s_targets[idx];
    return nullptr;
}

} // namespace smt4::hal

#else // Native Host (Windows / Linux / macOS)

#include <chrono>
#include <thread>
#include <cstring>

namespace smt4::hal {

static bool s_gfx_init = false;
static bool s_3d_mode = false;
static u64 s_present_count = 0;
static FramebufferConfig s_targets[3]{};
static std::chrono::steady_clock::time_point s_last_vblank{};

bool Graphics_Init() {
    s_gfx_init = true;
    s_3d_mode = false;
    s_present_count = 0;
    std::memset(s_targets, 0, sizeof(s_targets));
    s_last_vblank = std::chrono::steady_clock::now();
    return true;
}

void Graphics_Shutdown() {
    s_gfx_init = false;
    s_present_count = 0;
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
    if (!s_gfx_init) return;
    s_present_count++;
}

void Graphics_WaitForVBlank() {
    if (!s_gfx_init) return;
    auto now = std::chrono::steady_clock::now();
    auto elapsed = std::chrono::duration_cast<std::chrono::microseconds>(now - s_last_vblank).count();
    const s64 frame_time_us = 16666; // 60 Hz frame step (~16.666 ms)
    if (elapsed < frame_time_us) {
        std::this_thread::sleep_for(std::chrono::microseconds(frame_time_us - elapsed));
    }
    s_last_vblank = std::chrono::steady_clock::now();
}

u64 Graphics_GetPresentCount() {
    return s_present_count;
}

const FramebufferConfig* Graphics_GetFramebuffer(DisplayTarget target) {
    u32 idx = static_cast<u32>(target);
    if (idx < 3) return &s_targets[idx];
    return nullptr;
}

} // namespace smt4::hal

#endif
