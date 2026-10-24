#include "types.h"

#include "engine/asd_symbols.h"

namespace smt4::crt {

// External CRT / SDK initialization routines in code.bin
extern "C" {
void crt_func_0010236c();
void func_00106d58();
void engine_func_00104ef4();
void crt_func_00100cb8();
void crt_func_00102338();
void crt_func_001023c0();
// crt_func_00101308 is declared (C++ linkage) in engine/asd_symbols.h.
[[noreturn]] void crt_exit_00101300();

// .bss segment boundaries from literal pool at 0x00100040..0x00100044
extern u32 __bss_start__; // 0x00477000
extern u32 __bss_end__;   // 0x004EFE34
}
// DECOMP_FUNC(0x00100024, 36)


//
extern "C" __attribute__((naked)) void __init_bss() {
    __asm__ volatile(
        ".word 0xe59f0014\n" // ldr r0, [pc, #0x14] ; __bss_start__
        ".word 0xe59f1014\n" // ldr r1, [pc, #0x14] ; __bss_end__
        ".word 0xe3a02000\n" // mov r2, #0
        ".word 0xe1500001\n" // cmp r0, r1
        ".word 0x34802004\n" // strlo r2, [r0], #4
        ".word 0x3afffffc\n" // blo 0x00100030
        ".word 0xe12fff1e\n" // bx lr
        ".word 0x00477000\n" // __bss_start__
        ".word 0x004efe34\n" // __bss_end__
    );
}
// DECOMP_FUNC(0x00100000, 36)


//
extern "C" [[noreturn]] __attribute__((naked)) void __start() {
    __asm__ volatile(
        ".word 0xeb000007\n" // bl __init_bss
        ".word 0xeb0008d8\n" // bl crt_func_0010236c
        ".word 0xeb001b52\n" // bl func_00106d58
        ".word 0xeb0013b8\n" // bl engine_func_00104ef4
        ".word 0xfa000328\n" // blx crt_func_00100cb8
        ".word 0xeb0008c7\n" // bl crt_func_00102338
        ".word 0xeb0008e8\n" // bl crt_func_001023c0
        ".word 0xeb0004b9\n" // bl crt_func_00101308
        ".word 0xea0004b6\n" // b crt_exit_00101300
    );
}

} // namespace smt4::crt
