#include <cstdint>
typedef uint8_t u8;
typedef uint32_t u32;

struct AsdSoundEffect2 {
    u8 pad[0x30];
    void* buffer;
    u32 size;
};

extern "C" __attribute__((naked)) u32 h16_asdsoundeffect2_setbuffer_candidate(AsdSoundEffect2* self, void* buffer, u32 size) {
    asm(
        "cmp r1, #0\n\t"
        "addne r0, r0, #0x30\n\t"
        "moveq r0, #0\n\t"
        "stmne r0, {r1, r2}\n\t"
        "movne r0, #1\n\t"
        "bx lr"
    );
}

extern "C" u32 h16_asdsoundeffect2_setbuffer_mutation(AsdSoundEffect2* self, void* buffer, u32 size) {
    if (!buffer) return 1;
    return 0;
}
