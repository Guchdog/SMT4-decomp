// Exact byte carriers for code.bin ranges that are data or fragments, not
// independently established callable functions. Each row is verified by the
// same ARMv6K object-byte matcher as DECOMP_FUNC entries.
// DECOMP_SPAN(0x001729bc, 212)
extern "C" __attribute__((naked, used)) void span_001729bc() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x729bc, 212\n");
}

// DECOMP_SPAN(0x00178fbc, 212)
extern "C" __attribute__((naked, used)) void span_00178fbc() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x78fbc, 212\n");
}

// DECOMP_SPAN(0x0017f5bc, 4)
extern "C" __attribute__((naked, used)) void span_0017f5bc() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x7f5bc, 4\n");
}

// DECOMP_SPAN(0x0017f5e0, 8)
extern "C" __attribute__((naked, used)) void span_0017f5e0() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x7f5e0, 8\n");
}

// DECOMP_SPAN(0x0017f61c, 8)
extern "C" __attribute__((naked, used)) void span_0017f61c() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x7f61c, 8\n");
}

// DECOMP_SPAN(0x001907dc, 12)
extern "C" __attribute__((naked, used)) void span_001907dc() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x907dc, 12\n");
}

// DECOMP_SPAN(0x003f0030, 16)
extern "C" __attribute__((naked, used)) void span_003f0030() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x2f0030, 16\n");
}

// DECOMP_SPAN(0x003f1458, 12)
extern "C" __attribute__((naked, used)) void span_003f1458() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x2f1458, 12\n");
}
