#include <stdint.h>

using u8 = uint8_t;
using u32 = uint32_t;

#define DEFINE_SELF_POINTER_INIT(name)                                      \
    extern "C" __attribute__((noinline, used)) volatile u32* name(          \
        volatile u32* destination) {                                         \
        destination[0] = 0;                                                  \
        reinterpret_cast<volatile u8*>(destination)[4] = 1;                 \
        destination[2] = static_cast<u32>(                                  \
            reinterpret_cast<uintptr_t>(destination) + 8u);                 \
        destination[4] = 0;                                                  \
        destination[3] = static_cast<u32>(                                  \
            reinterpret_cast<uintptr_t>(destination) + 8u);                 \
        return destination;                                                  \
    }

DEFINE_SELF_POINTER_INIT(candidate_00237f10)
DEFINE_SELF_POINTER_INIT(candidate_003f7394)

extern "C" __attribute__((noinline, used)) volatile u32* negative_wide_flag(
    volatile u32* destination) {
    destination[0] = 0;
    destination[1] = 1;
    destination[2] = static_cast<u32>(reinterpret_cast<uintptr_t>(destination) + 8u);
    destination[4] = 0;
    destination[3] = static_cast<u32>(reinterpret_cast<uintptr_t>(destination) + 8u);
    return destination;
}

extern "C" __attribute__((noinline, used)) volatile u32* negative_wrong_self_pointer(
    volatile u32* destination) {
    destination[0] = 0;
    reinterpret_cast<volatile u8*>(destination)[4] = 1;
    destination[2] = static_cast<u32>(reinterpret_cast<uintptr_t>(destination));
    destination[4] = 0;
    destination[3] = static_cast<u32>(reinterpret_cast<uintptr_t>(destination) + 8u);
    return destination;
}

extern "C" __attribute__((noinline, used)) volatile u32* negative_reordered_stores(
    volatile u32* destination) {
    destination[0] = 0;
    reinterpret_cast<volatile u8*>(destination)[4] = 1;
    destination[2] = static_cast<u32>(reinterpret_cast<uintptr_t>(destination) + 8u);
    destination[3] = static_cast<u32>(reinterpret_cast<uintptr_t>(destination) + 8u);
    destination[4] = 0;
    return destination;
}

extern "C" __attribute__((noinline, used)) volatile u32* negative_missing_zero(
    volatile u32* destination) {
    destination[0] = 0;
    reinterpret_cast<volatile u8*>(destination)[4] = 1;
    destination[2] = static_cast<u32>(reinterpret_cast<uintptr_t>(destination) + 8u);
    destination[3] = static_cast<u32>(reinterpret_cast<uintptr_t>(destination) + 8u);
    return destination;
}
