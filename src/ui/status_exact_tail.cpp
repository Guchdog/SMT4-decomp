// UIFade's separately referenced calculation callback and its literal pool.
// DECOMP_FUNC(0x001907e8, 168)
extern "C" __attribute__((naked, used)) void UIFade_CalcTaskCallback() {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x907e8, 168\n");
}
