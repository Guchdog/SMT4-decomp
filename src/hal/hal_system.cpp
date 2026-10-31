#include "hal/hal_system.h"

namespace smt4::hal {

static bool s_initialized = false;
static u64 s_start_time_ns = 0;

bool System_Init() {
    s_initialized = true;
    s_start_time_ns = 1000000000ULL;
    return true;
}

void System_Shutdown() {
    s_initialized = false;
}

SystemInfo System_GetInfo() {
    SystemInfo info{};
    info.platform = PlatformId::NativeHost;
    info.memory_total_mb = 128;
    info.memory_available_mb = 96;
    info.has_hardware_3d = true;
    return info;
}

u64 GetTimeNanoseconds() {
    return s_start_time_ns += 16666666ULL; // 60 Hz frame step
}

u64 GetTimeMilliseconds() {
    return GetTimeNanoseconds() / 1000000ULL;
}

void SleepMilliseconds(u32 ms) {
    // Monotonic simulation advance
    s_start_time_ns += static_cast<u64>(ms) * 1000000ULL;
}

} // namespace smt4::hal
