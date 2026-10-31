#include <cstdint>

typedef uint32_t u32;

struct CombatChannelContext {
    char pad[0x15C];
    u32 channel0; // +0x15C
    u32 channel1; // +0x160
};

extern "C" {
    extern CombatChannelContext g_CombatChannelContext_004c6290;
}

extern "C" void h5_btl_set_channel_param_candidate(u32 mode, u32 val) {
    auto& ctx = g_CombatChannelContext_004c6290;
    if (mode == 0x400 || mode == 0x402) {
        ctx.channel0 = val;
    }
    if (mode == 0x401 || mode == 0x402) {
        ctx.channel1 = val;
    }
}

extern "C" void h5_btl_set_channel_param_mutation(u32 mode, u32 val) {
    auto& ctx = g_CombatChannelContext_004c6290;
    ctx.channel0 = 0;
}
