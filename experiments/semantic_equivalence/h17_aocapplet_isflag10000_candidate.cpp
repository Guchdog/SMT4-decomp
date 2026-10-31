#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

extern "C" u32 h17_aocapplet_isflag10000_candidate(const u8* applet) {
    u32 flags = *reinterpret_cast<const u32*>(applet + 0x754);
    return (flags & 0x10000u) >> 16;
}

extern "C" u32 h17_aocapplet_isflag10000_mutation(const u8* applet) {
    return 0;
}
