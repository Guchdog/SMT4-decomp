#include <cstdint>
typedef uint8_t u8;
typedef uint32_t u32;

extern "C" const u8* h16_asddata_getbase_candidate(const u8* self) {
    u32 offset = *reinterpret_cast<const u32*>(self + 0x18);
    return self + 8 + offset;
}

extern "C" const u8* h16_asddata_getbase_mutation(const u8* self) {
    return nullptr;
}
