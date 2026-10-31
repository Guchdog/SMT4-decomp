#include "hal/hal_system.h"

#if defined(__arm__)

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
    info.platform = PlatformId::Nintendo3DS;
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
    s_start_time_ns += static_cast<u64>(ms) * 1000000ULL;
}

} // namespace smt4::hal

#else // Native Host (Windows / Linux / macOS)

#include <chrono>
#include <thread>

#if defined(_WIN32)
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#endif

namespace smt4::hal {

static bool s_initialized = false;
static std::chrono::steady_clock::time_point s_init_time{};

bool System_Init() {
    s_initialized = true;
    s_init_time = std::chrono::steady_clock::now();
    return true;
}

void System_Shutdown() {
    s_initialized = false;
}

SystemInfo System_GetInfo() {
    SystemInfo info{};
    info.platform = PlatformId::NativeHost;
    info.has_hardware_3d = false;

#if defined(_WIN32)
    MEMORYSTATUSEX mem{};
    mem.dwLength = sizeof(mem);
    if (GlobalMemoryStatusEx(&mem)) {
        info.memory_total_mb = static_cast<u32>(mem.ullTotalPhys / (1024 * 1024));
        info.memory_available_mb = static_cast<u32>(mem.ullAvailPhys / (1024 * 1024));
    } else {
        info.memory_total_mb = 4096;
        info.memory_available_mb = 2048;
    }
#else
    info.memory_total_mb = 4096;
    info.memory_available_mb = 2048;
#endif

    return info;
}

u64 GetTimeNanoseconds() {
    if (!s_initialized) return 0;
    auto now = std::chrono::steady_clock::now();
    return static_cast<u64>(std::chrono::duration_cast<std::chrono::nanoseconds>(now - s_init_time).count());
}

u64 GetTimeMilliseconds() {
    return GetTimeNanoseconds() / 1000000ULL;
}

void SleepMilliseconds(u32 ms) {
    std::this_thread::sleep_for(std::chrono::milliseconds(ms));
}

} // namespace smt4::hal

#endif
