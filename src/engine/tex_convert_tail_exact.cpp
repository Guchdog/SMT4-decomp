// Five callable initialization/teardown thunks embedded after the third
// texture-conversion leaf block. Literal pairs between them stay data rows.
// DECOMP_FUNC(0x0017f5c0, 12)
__attribute__((used)) void func_0017f5c0(unsigned int* object) {
    *object = 0;
}
// DECOMP_FUNC(0x0017f5cc, 20)
__attribute__((naked, used)) void func_0017f5cc() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x7f5cc, 20\n");
}
// DECOMP_FUNC(0x0017f5e8, 16)
__attribute__((naked, used)) void func_0017f5e8() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x7f5e8, 16\n");
}
// DECOMP_FUNC(0x0017f5f8, 16)
__attribute__((naked, used)) void func_0017f5f8() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x7f5f8, 16\n");
}
// DECOMP_FUNC(0x0017f608, 20)
__attribute__((naked, used)) void func_0017f608() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x7f608, 20\n");
}
