#include <cstdint>
typedef uint32_t u32;

extern "C" u32 g_sound_sub_00141924(void* obj);

extern "C" u32 h16_asdsound_getdatasize_candidate(void* /*self*/, void* obj) {
    u32 count = g_sound_sub_00141924(obj);
    return (4 + (count * 4) + 3) & ~3u;
}

extern "C" u32 h16_asdsound_getdatasize_mutation(void* /*self*/, void* obj) {
    return 0;
}
