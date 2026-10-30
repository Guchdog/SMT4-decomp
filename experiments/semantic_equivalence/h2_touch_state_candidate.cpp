// Bounded readable reconstruction of UiTouch_GetRegionTouchState (0x0029D8FC).
// The touch manager is expected to have been initialized by IfTouch_Init.

using u8 = unsigned char;
using s16 = short;
using s32 = int;

extern "C" __attribute__((used, noinline)) s32 candidate_0029d8fc(s16 handle) {
    auto* const manager = *reinterpret_cast<void* volatile*>(0x0043DCB4u);
    auto* const bytes = static_cast<volatile u8*>(manager);
    const s16 active_panel = *reinterpret_cast<volatile s16*>(bytes + 0x64Eu);
    if (active_panel != handle) {
        return 0;
    }
    return bytes[0x08u];
}

extern "C" __attribute__((used, noinline)) s32 candidate_0029d8fc_bad(s16 handle) {
    (void)handle;
    // Deliberately wrong: return the manager's byte regardless of active index.
    auto* const manager = *reinterpret_cast<void* volatile*>(0x0043DCB4u);
    auto* const bytes = static_cast<volatile u8*>(manager);
    return bytes[0x08u];
}
