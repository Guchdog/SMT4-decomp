#include <cstdint>
typedef uint8_t u8;
typedef uint32_t u32;

extern "C" u32 h16_asddata_getcount_candidate(const u8* self) {
    u32 offset = *reinterpret_cast<const u32*>(self + 0x18);
    const u8* base = self + 8 + offset;
    return *reinterpret_cast<const u32*>(base + 0x14);
}

extern "C" u32 h16_asddata_getcount_mutation(const u8* self) {
    return 0;
}
