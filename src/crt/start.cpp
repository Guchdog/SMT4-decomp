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
extern "C" void __init_bss() {
    u32* dst = &__bss_start__;
    u32* end = &__bss_end__;
    while (dst < end) {
        *dst++ = 0;
    }
}

// DECOMP_FUNC(0x00100000, 36)
extern "C" [[noreturn]] void __start() {
    __init_bss();
    crt_func_0010236c();
    func_00106d58();
    engine_func_00104ef4();
    crt_func_00100cb8();
    crt_func_00102338();
    crt_func_001023c0();
    smt4::engine::crt_func_00101308();
    crt_exit_00101300();
}

} // namespace smt4::crt
