#pragma once
#include "hal_types.h"

namespace smt4::hal {

enum class PlatformId : u32 {
    Nintendo3DS = 0,
    NativeHost  = 1,
};

struct SystemInfo {
    PlatformId platform;
    u32 memory_total_mb;
    u32 memory_available_mb;
    bool has_hardware_3d;
};

bool System_Init();
void System_Shutdown();
SystemInfo System_GetInfo();

u64 GetTimeNanoseconds();
u64 GetTimeMilliseconds();
void SleepMilliseconds(u32 ms);

} // namespace smt4::hal
