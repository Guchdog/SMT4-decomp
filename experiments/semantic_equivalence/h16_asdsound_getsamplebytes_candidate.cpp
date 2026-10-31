#include <cstdint>
typedef uint32_t u32;

extern "C" int g_sound_sub_001419bc(void* obj, void* out_buf);

extern "C" u32 h16_asdsound_getsamplebytes_candidate(void* /*self*/, void* obj) {
    u32 buf[8];
    u32 r4 = 0;
    if (g_sound_sub_001419bc(obj, buf) != 0) {
        r4 = buf[4];
    }
    return (r4 * 5) << 13;
}

extern "C" u32 h16_asdsound_getsamplebytes_mutation(void* /*self*/, void* obj) {
    return 0;
}
