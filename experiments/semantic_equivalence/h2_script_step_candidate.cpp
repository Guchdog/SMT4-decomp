// Bounded readable reconstruction of the script-step dispatcher at 0x0019DFBC.
using u16 = unsigned short;
using u32 = unsigned int;
using s32 = int;

using ScriptStepHandler = s32 (*)(void* work);

extern "C" __attribute__((used, noinline)) s32 candidate_0019dfbc(void* work) {
    auto* const bytes = static_cast<unsigned char*>(work);
    auto* const method_table = *reinterpret_cast<u32**>(bytes + 0xBCu);
    auto* const handler_table = reinterpret_cast<ScriptStepHandler*>(0x0044DED0u);

    for (;;) {
        const u32 instruction = *reinterpret_cast<u32*>(bytes + 0x18u);
        const u16 handler_id = *reinterpret_cast<u16*>(method_table + instruction);
        const s32 result = handler_table[handler_id](work);

        if (result == 0) {
            *reinterpret_cast<u32*>(bytes + 0xD0u) = 0;
            return 2;
        }
        if (result == 2) {
            ++*reinterpret_cast<u32*>(bytes + 0xCCu);
            ++*reinterpret_cast<u32*>(bytes + 0xD0u);
            return 1;
        }
        if (result == 1) {
            *reinterpret_cast<u32*>(bytes + 0xD0u) = 0;
        }
        // Other callback results continue through the script dispatcher too.
    }
}

extern "C" __attribute__((used, noinline)) s32 candidate_0019dfbc_bad(void* work) {
    (void)work;
    // Deliberately wrong negative control for the result-2 return branch.
    return 2;
}
