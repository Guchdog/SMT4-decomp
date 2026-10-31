#include <cstdint>
typedef uint8_t u8;
typedef uint32_t u32;

struct AsdSoundConfig {
    u8 pad0[0x44];
    u32 rate;
    u8 pad1[0x5D - 0x48];
    u8 channels;
};

extern "C" u32 h16_asdsoundeffect_getbuffersize_promoted(const AsdSoundConfig* self) {
    u32 prod = self->rate * static_cast<u32>(self->channels);
    return ((prod * 5) << 7) + 0x20;
}

extern "C" u32 h16_asdsoundeffect_getbuffersize_mutation(const AsdSoundConfig* self) {
    return 0;
}
