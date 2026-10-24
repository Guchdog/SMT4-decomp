// Three independently bounded ARM routines with their adjacent literal pools.
// DECOMP_FUNC(0x003ee314, 44)
__attribute__((naked, used)) void func_003ee314() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x2ee314, 44\n");
}

// DECOMP_FUNC(0x003ee340, 44)
__attribute__((naked, used)) void func_003ee340() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x2ee340, 44\n");
}

// DECOMP_FUNC(0x003ee36c, 44)
__attribute__((naked, used)) void func_003ee36c() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x2ee36c, 44\n");
}
