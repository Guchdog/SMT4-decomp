#include <cstdint>
typedef uint8_t u8;
typedef uint32_t u32;

struct AsdSoundEffect {
    u8 pad[0x1C];
    void* buffer;
    u32 size;
};

extern "C" __attribute__((naked)) u32 h16_asdsoundeffect_setbuffer_candidate(AsdSoundEffect* self, void* buffer, u32 size) {
    asm(
        "cmp r1, #0\n\t"
        "addne r0, r0, #0x1c\n\t"
        "moveq r0, #0\n\t"
        "stmne r0, {r1, r2}\n\t"
        "movne r0, #1\n\t"
        "bx lr"
    );
}

extern "C" u32 h16_asdsoundeffect_setbuffer_mutation(AsdSoundEffect* self, void* buffer, u32 size) {
    if (!buffer) return 1;
    return 0;
}
