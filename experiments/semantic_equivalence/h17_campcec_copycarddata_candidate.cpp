#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

extern "C" void h17_campcec_copycarddata_candidate(const u8* src, u32 /*unused*/, u32* dst) {
    const u8* inner = *reinterpret_cast<const u8* const*>(src + 0x2C);
    const u32* words = reinterpret_cast<const u32*>(inner + 0x7C);
    u32 w0 = words[0];
    u32 w1 = words[1];
    u32 w2 = *reinterpret_cast<const u32*>(inner + 0x84);
    dst[0] = w0;
    dst[1] = w1;
    dst[2] = w2;
}

extern "C" void h17_campcec_copycarddata_mutation(const u8* src, u32 /*unused*/, u32* dst) {
    dst[0] = 0;
    dst[1] = 0;
    dst[2] = 0;
}
