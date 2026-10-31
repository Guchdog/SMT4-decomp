#pragma once
#include "hal_types.h"

namespace smt4::hal {

enum class DisplayTarget : u32 {
    TopLeftScreen     = 0,
    TopRightScreen    = 1,
    BottomScreen      = 2,
};

struct FramebufferConfig {
    u32 width;
    u32 height;
    u32 stride;
    void* buffer_ptr;
};

bool Graphics_Init();
void Graphics_Shutdown();

void Graphics_Set3DMode(bool enabled);
bool Graphics_Is3DMode();

void Graphics_SetFramebuffer(DisplayTarget target, const FramebufferConfig& config);
void Graphics_Present();
void Graphics_WaitForVBlank();

} // namespace smt4::hal
