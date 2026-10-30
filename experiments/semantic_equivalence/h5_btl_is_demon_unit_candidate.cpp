#include <cstdint>

typedef uint32_t u32;

extern "C" __attribute__((naked)) u32 h5_btl_is_demon_unit_candidate(u32 unit_id) {
    asm volatile(
        "cmp r0, #0x190\n\t"
        "movhi r0, #1\n\t"
        "movls r0, #0\n\t"
        "bx lr\n\t"
    );
}

extern "C" u32 h5_btl_is_demon_unit_mutation(u32 unit_id) {
    return 0;
}
