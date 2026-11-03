#include "types.h"

// Batch 30 C: redirected to 0x00200000-0x002fffff; exact ARM bytes and bounded literal tails.

// DECOMP_FUNC(0x00207d84, 128)
extern "C" u32 ui_func_002c5218();
extern "C" void ui_func_0026330c(float* output, u32 index, u32 context,
                                  const float* input);

extern "C" __attribute__((minsize)) float ui_func_00207d84() {
    constexpr u32 kVectorAddress = 0x004EA91Cu;
    constexpr u32 kScratchAddress = 0x00472550u;
    auto* const vector = reinterpret_cast<volatile u32*>(kVectorAddress);
    auto* const scratch = reinterpret_cast<volatile u32*>(kScratchAddress);
    const u32 context = ui_func_002c5218();

    for (u32 word = 0; word < 4; ++word) {
        scratch[word] = vector[word];
    }

    alignas(8) u32 frame[8];
    auto* const input_words = reinterpret_cast<volatile u32*>(frame + 4);
    input_words[0] = scratch[0];
    input_words[1] = scratch[1];
    input_words[2] = scratch[2];

    ui_func_0026330c(reinterpret_cast<float*>(frame), 0, context,
                     reinterpret_cast<const float*>(frame + 4));
    frame[3] = 0;
    vector[0] = frame[0];
    vector[1] = frame[1];
    vector[2] = frame[2];
    vector[3] = frame[3];

    register u32 return_r0 asm("r0") = kVectorAddress;
    asm volatile("" : "+r"(return_r0));
    return *reinterpret_cast<float*>(&frame[2]);
}

// DECOMP_FUNC(0x0020e9ac, 152)
extern "C" __attribute__((naked)) void engine_func_0020e9ac() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe59f5088\n.inst 0xe5954004\n.inst 0xe3540000\n.inst 0x0a00001b\n.inst 0xe5940000\n.inst 0xeb028ed9\n.inst 0xe3500000\n.inst 0x1a000019\n.inst 0xe5d40004\n.inst 0xe3500000\n.inst 0x0a000016\n.inst 0xe5954004\n.inst 0xe3540000\n.inst 0x0a000011\n.inst 0xe3a00001\n.inst 0xe5c40004\n.inst 0xe5940008\n.inst 0xe3a06000\n.inst 0xe3500000\n.inst 0x0a000008\n.inst 0xeb02645d\n.inst 0xe5940008\n.inst 0xe3500000\n.inst 0x0a000003\n.inst 0xe2800e11\n.inst 0xeb015511\n.inst 0xe2400e11\n.inst 0xeb028ebf\n.inst 0xe5846008\n.inst 0xe5950004\n.inst 0xeb02d64c\n.inst 0xe5856004\n.inst 0xe3a00000\n.inst 0xe8bd8070\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.word 0x0044cfd0\n");
}

// DECOMP_FUNC(0x0020eac4, 148)
extern "C" __attribute__((naked)) void engine_func_0020eac4() {
    asm volatile(".arm\n.inst 0xe3a00001\n.inst 0xe92d4010\n.inst 0xeb022123\n.inst 0xe1a04000\n.inst 0xeb01ead9\n.inst 0xe3500000\n.inst 0x0a000009\n.inst 0xe3a00000\n.inst 0xeb02a87e\n.inst 0xe3500000\n.inst 0x0a000017\n.inst 0xe3a00000\n.inst 0xeb02a87a\n.inst 0xe3500000\n.inst 0x0a000013\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0xe320f000\n.inst 0xeb02cd05\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x1afffff8\n.inst 0xe3a00000\n.inst 0xeb02210e\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000001\n.inst 0xe3500001\n.inst 0x1afffff1\n.inst 0xe1a01004\n.inst 0xe3a00000\n.inst 0xeb0246cc\n.inst 0xe1a01004\n.inst 0xe3a00001\n.inst 0xeb0246c9\n.inst 0xe3a00000\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x002100f8, 144)
extern "C" __attribute__((naked)) void ui_func_002100f8() {
    asm volatile(".arm\n.inst 0xe92d40f0\n.inst 0xee701aa1\n.inst 0xee301a01\n.inst 0xed2d8b02\n.inst 0xe24dd03c\n.inst 0xe28d4028\n.inst 0xeeb08b42\n.inst 0xe884000f\n.inst 0xe28d4010\n.inst 0xe28d7020\n.inst 0xe58d0038\n.inst 0xe1a0600d\n.inst 0xec8d0a02\n.inst 0xe28d5028\n.inst 0xed8d0a02\n.inst 0xedcd1a03\n.inst 0xec841a02\n.inst 0xe3a04000\n.inst 0xed8d1a06\n.inst 0xedcd0a07\n.inst 0xec870a02\n.inst 0xe3a07004\n.inst 0xe0860184\n.inst 0xe0851104\n.inst 0xec900a04\n.inst 0xeef02a68\n.inst 0xeeb02a48\n.inst 0xe5911004\n.inst 0xe7950104\n.inst 0xeb014c38\n.inst 0xe2844001\n.inst 0xe1540007\n.inst 0xbafffff4\n.inst 0xe28dd03c\n.inst 0xecbd8b02\n.inst 0xe8bd80f0\n");
}

// DECOMP_FUNC(0x002118a0, 148)
extern "C" __attribute__((naked)) void engine_func_002118a0() {
    asm volatile(".arm\n.inst 0xe92d40f0\n.inst 0xe24dd00c\n.inst 0xe3a00000\n.inst 0xeb01f1a2\n.inst 0xeb01df62\n.inst 0xe3500000\n.inst 0x1a000005\n.inst 0xe59f006c\n.inst 0xe3a01001\n.inst 0xe5900008\n.inst 0xe3500000\n.inst 0x15c01030\n.inst 0xe5c01031\n.inst 0xe320f000\n.inst 0xeb01d3e8\n.inst 0xe3500014\n.inst 0x03a00005\n.inst 0xe1a05000\n.inst 0xe3a04001\n.inst 0xeb01d3de\n.inst 0xe1a07000\n.inst 0xe3a00000\n.inst 0xeb021598\n.inst 0xe1a06000\n.inst 0xe320f000\n.inst 0xeb01df4d\n.inst 0xe3a01000\n.inst 0xe1a02000\n.inst 0xe58d1004\n.inst 0xe1a03005\n.inst 0xe1a01006\n.inst 0xe1a00007\n.inst 0xe58d4000\n.inst 0xeb01d3ff\n.inst 0xe28dd00c\n.inst 0xe8bd80f0\n.word 0x0043e188\n");
}

// DECOMP_FUNC(0x00211c50, 148)
extern "C" __attribute__((naked)) void battle_func_00211c50() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xeb042858\n.inst 0xe1a05000\n.inst 0xeb02b5ee\n.inst 0xe3500000\n.inst 0x0a00001a\n.inst 0xe1a00005\n.inst 0xeb02bb95\n.inst 0xe1a04000\n.inst 0xe590000c\n.inst 0xe3500001\n.inst 0x0a000007\n.inst 0xe5d40064\n.inst 0xe3a05001\n.inst 0xe3500000\n.inst 0x0a00000d\n.inst 0xeb01de6a\n.inst 0xe3500000\n.inst 0x0a000005\n.inst 0xea000007\n.inst 0xe3a01000\n.inst 0xe1a00005\n.inst 0xeb02ca42\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.inst 0xed9f0a08\n.inst 0xe5c45030\n.inst 0xed840a0a\n.inst 0xe3a00000\n.inst 0xe8bd8070\n.inst 0xed9f0a04\n.inst 0xe5c45030\n.inst 0xed840a0a\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.word 0xbdcccccd\n.word 0xbe800000\n");
}

// DECOMP_FUNC(0x00211f8c, 152)
extern "C" __attribute__((naked)) void camp_func_00211f8c() {
    asm volatile(".arm\n.inst 0xe59f008c\n.inst 0xe92d4070\n.inst 0xe3a04000\n.inst 0xe5900004\n.inst 0xe2805090\n.inst 0xeb01634e\n.inst 0xe2401001\n.inst 0xe3510000\n.inst 0xe1a0c000\n.inst 0xda000012\n.inst 0xe31c0001\n.inst 0xe2850076\n.inst 0x1a000002\n.inst 0xe1f020b2\n.inst 0xe3520000\n.inst 0x13a04001\n.inst 0xe1d030b2\n.inst 0xe1b010c1\n.inst 0xe3a02000\n.inst 0x0a000007\n.inst 0xe3530000\n.inst 0xe1f030b4\n.inst 0x12844001\n.inst 0xe3530000\n.inst 0xe1d030b2\n.inst 0x12822001\n.inst 0xe2511001\n.inst 0x1afffff7\n.inst 0xe0844002\n.inst 0xe25c0001\n.inst 0x4a000003\n.inst 0xe0850080\n.inst 0xe1d007b8\n.inst 0xe3500000\n.inst 0x12844001\n.inst 0xe1a00004\n.inst 0xe8bd8070\n.word 0x0043e2a8\n");
}

// DECOMP_FUNC(0x00215bd8, 148)
extern "C" __attribute__((naked)) void script_vm_func_00215bd8() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3a06001\n.inst 0xe1a05000\n.inst 0xe59f7078\n.inst 0xe5974000\n.inst 0xe5c465f2\n.inst 0xeb020d8b\n.inst 0xe59f106c\n.inst 0xe5c405c4\n.inst 0xe18150b4\n.inst 0xeb00eb74\n.inst 0xe3a01001\n.inst 0xe1a00005\n.inst 0xeb01e927\n.inst 0xe3a02000\n.inst 0xe1a01002\n.inst 0xe2840034\n.inst 0xeb029fa7\n.inst 0xe5970000\n.inst 0xe3a01001\n.inst 0xe5902004\n.inst 0xe5802008\n.inst 0xe5a01004\n.inst 0xe3a02000\n.inst 0xe580200c\n.inst 0xe3a0001d\n.inst 0xe584000c\n.inst 0xe1a00005\n.inst 0xeb0282ac\n.inst 0xe5d00007\n.inst 0xe3100040\n.inst 0x13a00002\n.inst 0x158405c8\n.inst 0x058465c8\n.inst 0xe8bd81f0\n.word 0x0043dd50\n.word 0x0000097e\n");
}

// DECOMP_FUNC(0x00219624, 128)
extern "C" u32 func_0029ed08(u16 key);
extern "C" const u8* func_002b9364(u16 key);

extern "C" __attribute__((minsize)) s32 camp_func_00219624(const u16* a, const u16* b) {
    const u32 flag_a = func_0029ed08(*a);
    const u32 flag_b = func_0029ed08(*b);
    if (flag_b > flag_a) {
        return -1;
    }
    if (flag_a > flag_b) {
        return 1;
    }

    const u8* const rec_a = func_002b9364(*a);
    const u8* const rec_b = func_002b9364(*b);

    const s32 diff2 = static_cast<s32>(rec_a[2]) - static_cast<s32>(rec_b[2]);
    if (diff2 != 0) {
        return diff2;
    }

    const s32 diff3 = static_cast<s32>(rec_b[3]) - static_cast<s32>(rec_a[3]);
    if (diff3 != 0) {
        return diff3;
    }

    return static_cast<s32>(*reinterpret_cast<const u16*>(rec_a)) -
           static_cast<s32>(*reinterpret_cast<const u16*>(rec_b));
}

extern "C" uint32_t h2_set_global(uint32_t) __asm__("ui_func_0028df3c");
extern "C" uint32_t h2_get_state(uint32_t) __asm__("engine_func_00289640");
extern "C" uint32_t h2_get_context(uint32_t) __asm__("func_0028686c");
extern "C" uint32_t h2_select_value(uint32_t) __asm__("engine_func_00296f60");
extern "C" uint32_t h2_final_helper(uint32_t, uint32_t, uint32_t, uint32_t, uint32_t, uint32_t) __asm__("engine_func_00286928");
// DECOMP_FUNC(0x00221168, 148)
extern "C" uint32_t engine_func_00221168() {
    auto slots = reinterpret_cast<uint32_t*>(0x0043e188);
    uint32_t state = h2_get_state(h2_set_global(0));
    if (state == 0) {
        auto object = reinterpret_cast<uint8_t*>(slots[2]);
        if (object != nullptr) object[0x30] = 1;
        object[0x31] = 1;
    }
    auto object = reinterpret_cast<uint8_t*>(slots[1]);
    if (object != nullptr) object[0xa11] = 0x14;
    uint32_t context = h2_get_context(reinterpret_cast<uint32_t>(object));
    uint32_t value = h2_select_value(0);
    uint32_t current = h2_get_state(value);
    return h2_final_helper(context, value, current, 6, 1, 0);
}

// DECOMP_FUNC(0x00221fb4, 128)
extern "C" u32 engine_func_00259510(u32);
extern "C" u32 engine_func_00296f60(u32);
extern "C" u32 engine_func_00289640();
extern "C" u32 battle_func_002bf41c(u32);
extern "C" u32 _3dEventEffect_func_0030a28c(u32, u32, u32, u32);

extern "C" __attribute__((minsize)) u32 engine_func_00221fb4() {
    auto* const global_handle = reinterpret_cast<volatile u32*>(0x0043DF58u);
    const u32 arg0 = engine_func_00259510(0);
    const u32 arg1 = engine_func_00296f60(1);
    const u32 arg2 = engine_func_00296f60(2);
    const u32 arg3 = engine_func_00296f60(3);

    if (engine_func_00289640() != 0) {
        if (battle_func_002bf41c(*global_handle) == 0) {
            return 1;
        }
        return 0;
    }

    *global_handle = _3dEventEffect_func_0030a28c(arg0, arg1, arg2, arg3);
    return 0;
}

// DECOMP_FUNC(0x002220a8, 140)
extern "C" __attribute__((naked)) void ui_func_002220a8() {
    asm volatile(".arm\n.inst 0xe92d4030\n.inst 0xe24dd00c\n.inst 0xe3a00000\n.inst 0xeb01d3a9\n.inst 0xe1a04000\n.inst 0xe3a00001\n.inst 0xeb01d3a6\n.inst 0xe59f2060\n.inst 0xee000a10\n.inst 0xe59f505c\n.inst 0xe8920007\n.inst 0xeef80ac0\n.inst 0xe88d0007\n.inst 0xe1a0000d\n.inst 0xe0800104\n.inst 0xed900a00\n.inst 0xe5950000\n.inst 0xe2801b01\n.inst 0xe2800b01\n.inst 0xe2811fcf\n.inst 0xe2800fce\n.inst 0xeb032743\n.inst 0xe1a04000\n.inst 0xeb0274c4\n.inst 0xe3500000\n.inst 0x0a000003\n.inst 0xe5950000\n.inst 0xe1a01004\n.inst 0xe5900000\n.inst 0xeb0288cf\n.inst 0xe28dd00c\n.inst 0xe3a00001\n.inst 0xe8bd8030\n.word 0x00403788\n.word 0x0043dfc0\n");
}

// DECOMP_FUNC(0x00224730, 152)
extern "C" __attribute__((naked)) void engine_func_00224730() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xeb0270e3\n.inst 0xe1a04000\n.inst 0xe5900004\n.inst 0xe3500000\n.inst 0x0a000002\n.inst 0xe3500001\n.inst 0x1a00001a\n.inst 0xea000011\n.inst 0xe5940008\n.inst 0xe3500000\n.inst 0x0a000016\n.inst 0xe3a05001\n.inst 0xe5845004\n.inst 0xeb02029b\n.inst 0xe284101c\n.inst 0xe584000c\n.inst 0xeb01fd75\n.inst 0xe594000c\n.inst 0xed9f0a10\n.inst 0xeb01fc85\n.inst 0xe594000c\n.inst 0xe320f000\n.inst 0xebffd6f6\n.inst 0xe5840018\n.inst 0xe5c45010\n.inst 0xea000007\n.inst 0xe594000c\n.inst 0xeb01759e\n.inst 0xe594000c\n.inst 0xe320f000\n.inst 0xeb033a1e\n.inst 0xe3500000\n.inst 0x13e00000\n.inst 0x1a000000\n.inst 0xe3a00000\n.inst 0xe8bd8070\n.word 0x3f000000\n");
}

// DECOMP_FUNC(0x002277fc, 144)
extern "C" __attribute__((naked)) void ui_func_002277fc() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe2804b07\n.inst 0xe28440fc\n.inst 0xe5940000\n.inst 0xe3500000\n.inst 0x0a000003\n.inst 0xeb01b11f\n.inst 0xeb01af2d\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xe3e00000\n.inst 0xe8bd8010\n.inst 0xe5943000\n.inst 0xe3a00000\n.inst 0xe59f104c\n.inst 0xe1d326f8\n.inst 0xe1d31afa\n.inst 0xe3520000\n.inst 0xa3520000\n.inst 0xc1a00002\n.inst 0xe1d327fe\n.inst 0xe3520000\n.inst 0xa1520000\n.inst 0xc1a00002\n.inst 0xe1d329f4\n.inst 0xe3520000\n.inst 0xa1520000\n.inst 0xc1a00002\n.inst 0xe3510000\n.inst 0xa1510000\n.inst 0xc1a00001\n.inst 0xe3500000\n.inst 0xd3a00e19\n.inst 0xd19000f3\n.inst 0xe8bd8010\n.word 0x0000270f\n");
}

// DECOMP_FUNC(0x00227f50, 144)
extern "C" __attribute__((naked)) void engine_func_00227f50() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe2806b07\n.inst 0xe28660fc\n.inst 0xe5960000\n.inst 0xe3500000\n.inst 0x0a000018\n.inst 0xeb01af4a\n.inst 0xeb01ad58\n.inst 0xe3500000\n.inst 0x1a000014\n.inst 0xe59f705c\n.inst 0xe3a04000\n.inst 0xe3a08058\n.inst 0xe0840084\n.inst 0xe5961000\n.inst 0xe0800184\n.inst 0xe0880080\n.inst 0xe0915000\n.inst 0x0a000008\n.inst 0xe597000c\n.inst 0xeb026cba\n.inst 0xe1a02000\n.inst 0xe597100c\n.inst 0xe1a00005\n.inst 0xeb023190\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000004\n.inst 0xe2844001\n.inst 0xe3540004\n.inst 0xbaffffed\n.inst 0xe3e00000\n.inst 0xe8bd81f0\n.inst 0xe1d501f0\n.inst 0xe8bd81f0\n.word 0x00435d00\n");
}

// DECOMP_FUNC(0x00227fe0, 128)
extern "C" u32 engine_func_002c3290(u32 context);
extern "C" u32 engine_func_002b45f8(const void* entry, u32 context, u32 aux);

extern "C" __attribute__((minsize)) s32 engine_func_00227fe0(const u8* object) {
    auto* const base = *reinterpret_cast<const u8* const*>(object + 0x1cfcu);
    if (base == nullptr) {
        return -1;
    }

    const u32 context = *reinterpret_cast<const u32*>(0x00435D00u + 0x0Cu);

    for (u32 i = 0; i < 4; ++i) {
        const u8* const entry = base + 0x58u + i * 22u;
        const u32 aux = engine_func_002c3290(context);
        if (engine_func_002b45f8(entry, context, aux) == 0) {
            return *reinterpret_cast<const u16*>(entry + 0x12u);
        }
    }

    return -1;
}

// DECOMP_FUNC(0x002282a0, 152)
extern "C" __attribute__((naked)) void ui_func_002282a0() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe2804b07\n.inst 0xe28440fc\n.inst 0xe1a05001\n.inst 0xe5940000\n.inst 0xe3500000\n.inst 0x0a000018\n.inst 0xe2800c01\n.inst 0xe1d009f0\n.inst 0xe3500000\n.inst 0xba000014\n.inst 0xeb01ae71\n.inst 0xeb01ac7f\n.inst 0xe3500000\n.inst 0x0a000007\n.inst 0xeb01ae6d\n.inst 0xe2800b11\n.inst 0xe28000ac\n.inst 0xe5900000\n.inst 0xe2000002\n.inst 0xe1b00000\n.inst 0x13a00000\n.inst 0x1a000009\n.inst 0xe3550000\n.inst 0x0a000008\n.inst 0xeb01ae63\n.inst 0xe320f000\n.inst 0xe320f000\n.inst 0xeb01ac6f\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000001\n.inst 0xe3e00000\n.inst 0xe8bd8070\n.inst 0xe5940000\n.inst 0xe2800c01\n.inst 0xe1d009f0\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x0022922c, 128)
extern "C" __attribute__((minsize)) void func_0022922c(const uintptr_t* obj) {
    const auto base_addr = *reinterpret_cast<const uintptr_t*>(*obj + 0x1fc0u);
    auto* const array = reinterpret_cast<uint8_t*>(base_addr);
    for (uint32_t i = 0; i < 109; ++i) {
        auto* const word = reinterpret_cast<uint32_t*>(array + i * 648u);
        *word &= ~0x400u;
    }
}

// DECOMP_FUNC(0x00229aa8, 132)
extern "C" void* ui_func_00282b94(void* inner, s32 idx);

extern "C" u32 ui_func_00229aa8(void* const* obj, const void* table, s32 default_idx) {
    void* const inner = *obj;
    void* const node = ui_func_00282b94(inner, default_idx);

    s32 idx = default_idx;
    if (node != nullptr) {
        idx = static_cast<s32>(*reinterpret_cast<const s16*>(static_cast<const u8*>(node) + 0x6E));
    }

    const auto* const tbl = static_cast<const u8*>(table);
    const u16 flag = *reinterpret_cast<const u16*>(tbl + 0x9D4 + idx * 10);
    if (flag == 0) {
        const auto* const entity_table = *reinterpret_cast<const u8* const*>(static_cast<const u8*>(inner) + 0x1FC0);
        const auto* const elem = entity_table + idx * 648;
        const u32 elem_flags = *reinterpret_cast<const u32*>(elem);

        if ((elem_flags & 1u) != 0 && (elem_flags & 0x400000u) == 0) {
            const s32 timer = *reinterpret_cast<const s32*>(elem + 0xC8);
            if (timer <= 0) {
                return 1;
            }
        }
    }
    return 0;
}

// DECOMP_FUNC(0x00229b2c, 140)
extern "C" __attribute__((naked)) void script_vm_func_00229b2c() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe24ddf6d\n.inst 0xe3a03000\n.inst 0xe5901000\n.inst 0xe59f2070\n.inst 0xe3a0506d\n.inst 0xe2811d7f\n.inst 0xe1a0600d\n.inst 0xe5911000\n.inst 0xe281cf6d\n.inst 0xe281406e\n.inst 0xe5917000\n.inst 0xe3170b01\n.inst 0x0a000006\n.inst 0xe1dc70f0\n.inst 0xe1570002\n.inst 0xca000003\n.inst 0xe1d480f0\n.inst 0xe1a02007\n.inst 0xe7868103\n.inst 0xe2833001\n.inst 0xe2555001\n.inst 0xe2811fa2\n.inst 0xe28ccfa2\n.inst 0xe2844fa2\n.inst 0x1afffff0\n.inst 0xeb0153ff\n.inst 0xe0861103\n.inst 0xe2800038\n.inst 0xe5111004\n.inst 0xe3a02001\n.inst 0xe7c12000\n.inst 0xe28ddf6d\n.inst 0xe8bd81f0\n.word 0x000186a0\n");
}

// DECOMP_FUNC(0x00229bd0, 152)
extern "C" __attribute__((naked)) void battle_func_00229bd0() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe1a04003\n.inst 0xe1a03001\n.inst 0xe59f7080\n.inst 0xe6bf1070\n.inst 0xe1a06002\n.inst 0xe59d5018\n.inst 0xe5970000\n.inst 0xe3a02000\n.inst 0xebfff3cc\n.inst 0xe3550000\n.inst 0x0a000013\n.inst 0xe5971000\n.inst 0xe5911008\n.inst 0xe3510000\n.inst 0x0a00000f\n.inst 0xe5d13004\n.inst 0xe591200c\n.inst 0xe353000e\n.inst 0x05913028\n.inst 0x03530000\n.inst 0x0591104c\n.inst 0x01510004\n.inst 0x1a000005\n.inst 0xe1d010f2\n.inst 0xe3510000\n.inst 0xba000002\n.inst 0xe3e01000\n.inst 0xe1c010b2\n.inst 0xea000001\n.inst 0xe1b01002\n.inst 0x1affffef\n.inst 0xe3a0100e\n.inst 0xe5806028\n.inst 0xe5c01004\n.inst 0xe580404c\n.inst 0xe8bd81f0\n.word 0x00434290\n");
}

// DECOMP_FUNC(0x0022b9d0, 132)
extern "C" void engine_func_0022b9d0(const void* src, float* out) {
    const float* src_coords = reinterpret_cast<const float*>(static_cast<const u8*>(src) + 0x50);
    const float limit_x = static_cast<float>(static_cast<s32>(src_coords[0] - 400.0f));
    const float limit_y = static_cast<float>(static_cast<s32>(src_coords[1] - 240.0f));

    float x = out[0];
    if (x <= 0.0f) {
        x = 0.0f;
    }
    if (x > limit_x) {
        x = limit_x;
    }
    out[0] = x;

    float y = out[1];
    if (y <= 0.0f) {
        y = 0.0f;
    }
    if (y > limit_y) {
        y = limit_y;
    }
    out[1] = y;
}

// DECOMP_FUNC(0x0022df7c, 140)
extern "C" __attribute__((naked)) void unite_func_0022df7c() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe1a05001\n.inst 0xe1a00001\n.inst 0xeb022cf4\n.inst 0xe3500000\n.inst 0x0a000015\n.inst 0xe1d009b0\n.inst 0xe3500e16\n.inst 0x33a00000\n.inst 0x33a02001\n.inst 0x2a000010\n.inst 0xe0841080\n.inst 0xe1d110f0\n.inst 0xe1510005\n.inst 0x1a000001\n.inst 0xe0800004\n.inst 0xea00000e\n.inst 0xe2800001\n.inst 0xe3500010\n.inst 0xbafffff6\n.inst 0xe3a00000\n.inst 0xe0841080\n.inst 0xe1d110f0\n.inst 0xe3710001\n.inst 0x0a000003\n.inst 0xe2800001\n.inst 0xe3500010\n.inst 0xbafffff8\n.inst 0xe8bd8070\n.inst 0xe0841080\n.inst 0xe0800004\n.inst 0xe1c150b0\n.inst 0xe5c02020\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002306ec, 144)
extern "C" __attribute__((naked)) void engine_func_002306ec() {
    asm volatile(".arm\n.inst 0xe3500000\n.inst 0xe59f0080\n.inst 0xe92d4038\n.inst 0xe3a0100b\n.inst 0xed9f0a1c\n.inst 0xe5904008\n.inst 0x0a00000c\n.inst 0xe3a00001\n.inst 0xe5c40082\n.inst 0xe58d1000\n.inst 0xe28430a4\n.inst 0xe3a02000\n.inst 0xe3a0100e\n.inst 0xe2840e7e\n.inst 0xeb023500\n.inst 0xe3a02000\n.inst 0xe3a01008\n.inst 0xe2840e7e\n.inst 0xeb0234e1\n.inst 0xea00000b\n.inst 0xe3a00002\n.inst 0xe5c40082\n.inst 0xe58d1000\n.inst 0xe28430a4\n.inst 0xe3a02000\n.inst 0xe3a0100e\n.inst 0xe2840e7e\n.inst 0xeb0234f3\n.inst 0xe3a02000\n.inst 0xe3a01009\n.inst 0xe2840e7e\n.inst 0xeb0234d4\n.inst 0xe3a00001\n.inst 0xe8bd8038\n.word 0x3f800000\n.word 0x0043e188\n");
}

// DECOMP_FUNC(0x0023d230, 132)
extern "C" __attribute__((minsize)) void func_0023d230(void* out, u32 packed) {
    auto* const out_words = reinterpret_cast<u32*>(out);
    auto* const out_floats = reinterpret_cast<float*>(out_words + 2);

    const u8 tag = *reinterpret_cast<const u8*>(0x00490E46u);
    out_words[0] = static_cast<u32>(tag) | 0x80000000u;
    out_words[1] = 0x804F02C0u;

    constexpr float kInv255 = 1.0f / 255.0f;
    out_floats[0] = static_cast<float>(packed & 0xFFu) * kInv255;
    out_floats[1] = static_cast<float>((packed >> 8) & 0xFFu) * kInv255;
    out_floats[2] = static_cast<float>((packed >> 16) & 0xFFu) * kInv255;
    out_floats[3] = static_cast<float>((packed >> 24) & 0xFFu) * kInv255;
}

// DECOMP_FUNC(0x0024095c, 128)
extern "C" __attribute__((minsize)) void func_0024095c(u8* obj, u32 param_1) {
    *reinterpret_cast<u32*>(obj + 0x72C) = param_1;
    *reinterpret_cast<u32*>(obj + 0x728) = 0;

    u32 flags = *reinterpret_cast<u32*>(obj + 0x634);
    flags |= 0x80000u;
    *reinterpret_cast<u32*>(obj + 0x634) = flags;

    float p0[2];
    __builtin_memcpy(p0, obj + 0xC, sizeof(p0));

    float s2, s1;
    __asm__("vldr %0, [%1, #0x18]" : "=t"(s2) : "r"(obj));
    __asm__("vldr %0, [%1, #0x1c]" : "=t"(s1) : "r"(obj));

    float diff0 = p0[0] - s2;
    float diff1 = p0[1] - s1;
    float dist_sq = diff0 * diff0 + diff1 * diff1;

    float dist;
    __asm__("vsqrt.f32 %0, %1" : "=t"(dist) : "t"(dist_sq));

    u32 dist_raw;
    __asm__("vmov %0, %1" : "=r"(dist_raw) : "t"(dist));

    if (dist_raw <= 0xBC23D70Au) {
        if (dist_raw <= 0x3C23D70Au) {
            flags &= ~0x80000u;
            *reinterpret_cast<u32*>(obj + 0x634) = flags;
        }
    }
}

// DECOMP_FUNC(0x00247d64, 128)
extern "C" u8* ui_func_002c0ac8(u32 id);

extern "C" __attribute__((minsize)) void engine_func_00247d64(u32 id, s32 duration, s32 reverse_flag) {
    u8* const target = ui_func_002c0ac8(id);
    float* const val_ptr = reinterpret_cast<float*>(target + 0x24);
    float* const step_ptr = reinterpret_cast<float*>(target + 0x28);

    if (reverse_flag != 0) {
        if (duration == 0) {
            *val_ptr = 0.0f;
            *step_ptr = 0.0f;
        } else {
            *val_ptr = 1.0f;
            *step_ptr = -1.0f / static_cast<float>(duration);
        }
    } else {
        if (duration == 0) {
            *val_ptr = 1.0f;
            *step_ptr = 0.0f;
        } else {
            *val_ptr = 0.0f;
            *step_ptr = 1.0f / static_cast<float>(duration);
        }
    }
}

// DECOMP_FUNC(0x0024baf4, 140)
extern "C" __attribute__((naked)) void ui_func_0024baf4() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xeb012066\n.inst 0xe2800a02\n.inst 0xe5904234\n.inst 0xeb00001d\n.inst 0xe1a01000\n.inst 0xe1a00004\n.inst 0xe8bd4010\n.inst 0xe1a00000\n.inst 0xe92d4030\n.inst 0xe1b04000\n.inst 0xe24dd00c\n.inst 0xe1a05001\n.inst 0x1a000001\n.inst 0xeb00eb4e\n.inst 0xe1a04000\n.inst 0xe59f0040\n.inst 0xe590000c\n.inst 0xe5805024\n.inst 0xe3a00000\n.inst 0xeb012d05\n.inst 0xe1a05000\n.inst 0xe320f000\n.inst 0xeb00f6ba\n.inst 0xe3a01000\n.inst 0xe1a02000\n.inst 0xe58d1000\n.inst 0xe58d1004\n.inst 0xe3a0300c\n.inst 0xe1a01005\n.inst 0xe1a00004\n.inst 0xeb00eb6c\n.inst 0xe28dd00c\n.inst 0xe8bd8030\n.word 0x0043e188\n");
}

// DECOMP_FUNC(0x0024c3f8, 148)
extern "C" __attribute__((naked)) void engine_func_0024c3f8() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a06001\n.inst 0xe1a04002\n.inst 0xe1a05003\n.inst 0xeb018f5e\n.inst 0xe59f2074\n.inst 0xe5903004\n.inst 0xe3e0107c\n.inst 0xe0c02692\n.inst 0xe5932000\n.inst 0xe1a03340\n.inst 0xe0430fc0\n.inst 0xe0000190\n.inst 0xe0860180\n.inst 0xe0800100\n.inst 0xe0820100\n.inst 0xe1d010b4\n.inst 0xe1d020b6\n.inst 0xe590000c\n.inst 0xe3c11902\n.inst 0xe3c22902\n.inst 0xe3500000\n.inst 0x0a000007\n.inst 0xe1d030b4\n.inst 0xe3530001\n.inst 0x0a000002\n.inst 0xe5d0300c\n.inst 0xe3130001\n.inst 0x0a000001\n.inst 0xe1d010f0\n.inst 0xe1d020f2\n.inst 0xe3540000\n.inst 0x15841000\n.inst 0xe3550000\n.inst 0x15852000\n.inst 0xe8bd8070\n.word 0x10624dd3\n");
}

// DECOMP_FUNC(0x0024de78, 136)
extern "C" __attribute__((naked)) void engine_func_0024de78() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3a06000\n.inst 0xe1a04006\n.inst 0xe59f706c\n.inst 0xe5970000\n.inst 0xe3500000\n.inst 0xc59f8064\n.inst 0xda000012\n.inst 0xe0840184\n.inst 0xe0800284\n.inst 0xe0885180\n.inst 0xe595013c\n.inst 0xe3500000\n.inst 0x0a000002\n.inst 0xeb01d92a\n.inst 0xe585613c\n.inst 0xe5856028\n.inst 0xe5950024\n.inst 0xe3500000\n.inst 0x0a000002\n.inst 0xeb01d924\n.inst 0xe5856024\n.inst 0xe5856020\n.inst 0xe5970000\n.inst 0xe2844001\n.inst 0xe1540000\n.inst 0xbaffffec\n.inst 0xe59f0010\n.inst 0xe3a01c52\n.inst 0xeb01db0f\n.inst 0xe5876000\n.inst 0xe8bd81f0\n.word 0x00433278\n.word 0x00478000\n");
}

// DECOMP_FUNC(0x0024fd10, 148)
extern "C" __attribute__((naked)) void engine_func_0024fd10() {
    asm volatile(".arm\n.inst 0xe92d40f0\n.inst 0xe24dd00c\n.inst 0xe3a06038\n.inst 0xe5902020\n.inst 0xe5901024\n.inst 0xe3520000\n.inst 0x059000b8\n.inst 0x10050192\n.inst 0x00050190\n.inst 0xe59f105c\n.inst 0xe59f005c\n.inst 0xe3550064\n.inst 0x83a05064\n.inst 0xe1a00000\n.inst 0xe3a07001\n.inst 0xe3a00010\n.inst 0xe88d0081\n.inst 0xe1a03006\n.inst 0xe3a02000\n.inst 0xe3a01c01\n.inst 0xe3a00801\n.inst 0xeb01cdce\n.inst 0xe1a04000\n.inst 0xe1a01006\n.inst 0xeb01cf74\n.inst 0xe3e01000\n.inst 0xed9f0a08\n.inst 0xe5841004\n.inst 0xe5845000\n.inst 0xed840a02\n.inst 0xe1c473b4\n.inst 0xe28dd00c\n.inst 0xe1a00004\n.inst 0xe8bd80f0\n.word 0x000001c2\n.word 0x004102c4\n.word 0x3f800000\n");
}

// DECOMP_FUNC(0x002502e8, 128)
extern "C" void engine_func_00256c3c(float* dst_matrix);
extern "C" void func_003f6ea8();
extern "C" void ui_func_002a2f1c();

extern "C" __attribute__((minsize)) void engine_func_002502e8(float* dst, const float* src_quat) {
    engine_func_00256c3c(dst);

    auto* const context_base = reinterpret_cast<uint8_t*>(0x004EA81Cu);
    float* const quat_scratch = reinterpret_cast<float*>(context_base + 0x100u);
    __builtin_memcpy(quat_scratch, src_quat, 4 * sizeof(float));

    func_003f6ea8();
    ui_func_002a2f1c();

    for (int i = 0; i < 3; ++i) {
        const float* const src_row = reinterpret_cast<const float*>(context_base + 0x140u + i * 16);
        float* const dst_row = dst + i * 4;
        dst_row[0] = src_row[0];
        dst_row[1] = src_row[1];
        dst_row[2] = src_row[2];
    }

    dst[12] = 0.0f;
    dst[13] = 0.0f;
    dst[14] = 0.0f;
}

// DECOMP_FUNC(0x00252630, 140)
extern "C" __attribute__((naked)) void script_vm_func_00252630() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe59f6078\n.inst 0xe5965000\n.inst 0xe1b04005\n.inst 0x0a00001a\n.inst 0xe59512f8\n.inst 0xe3a07000\n.inst 0xe3510000\n.inst 0xba00000f\n.inst 0xe3a00018\n.inst 0xeb017133\n.inst 0xe5960000\n.inst 0xe3a01000\n.inst 0xe3500000\n.inst 0x15c012f4\n.inst 0xe59f0044\n.inst 0xe59422f8\n.inst 0xe3a01018\n.inst 0xe5900000\n.inst 0xeb014f63\n.inst 0xe3e00000\n.inst 0xe58402f8\n.inst 0xe2844fba\n.inst 0xe3a00003\n.inst 0xe8840081\n.inst 0xe3a01000\n.inst 0xe59502e4\n.inst 0xeb01c7c5\n.inst 0xe1a00005\n.inst 0xe320f000\n.inst 0xeb01c72c\n.inst 0xe5867000\n.inst 0xe8bd81f0\n.word 0x00434210\n.word 0x00433158\n");
}

// DECOMP_FUNC(0x00256524, 140)
extern "C" __attribute__((naked)) void func_00256524() {
    asm volatile(".arm\n.inst 0xe59f2078\n.inst 0xe3510000\n.inst 0x03a00000\n.inst 0xe5922000\n.inst 0xe2822903\n.inst 0xe2822d33\n.inst 0x05c20000\n.inst 0x0a000016\n.inst 0xe3a03001\n.inst 0xe5c23000\n.inst 0xe59f2050\n.inst 0xe3500000\n.inst 0x03e00000\n.inst 0xed9f0a13\n.inst 0xe5922000\n.inst 0xe2822b33\n.inst 0xe1c20cb2\n.inst 0xe0810101\n.inst 0xe59f1034\n.inst 0xe1a00080\n.inst 0xe6bf0070\n.inst 0xe1c20cb6\n.inst 0xe1a03100\n.inst 0xed820a33\n.inst 0xe0c01391\n.inst 0xed820a34\n.inst 0xed820a35\n.inst 0xe1a01140\n.inst 0xe0410fc0\n.inst 0xe1c20cb4\n.inst 0xe1c20cb8\n.inst 0xe12fff1e\n.word 0x00447a78\n.word 0x66666667\n.word 0x00000000\n");
}

// DECOMP_FUNC(0x00262664, 140)
extern "C" __attribute__((naked)) void func_00262664() {
    asm volatile(".arm\n.inst 0xe59f107c\n.inst 0xe92d0030\n.inst 0xe1d041fc\n.inst 0xe5912000\n.inst 0xe3520000\n.inst 0x15921064\n.inst 0x13510015\n.inst 0x0a000015\n.inst 0xe2822d7f\n.inst 0xe3a01000\n.inst 0xe592c000\n.inst 0xe0812201\n.inst 0xe0822301\n.inst 0xe08c2182\n.inst 0xe5923000\n.inst 0xe3130001\n.inst 0x0a000009\n.inst 0xe3130040\n.inst 0x1a000007\n.inst 0xe3130002\n.inst 0x0a000005\n.inst 0xe5923278\n.inst 0xe1530000\n.inst 0x1a000002\n.inst 0xe59f0020\n.inst 0xe19040f2\n.inst 0xea000002\n.inst 0xe2811001\n.inst 0xe351006d\n.inst 0xbaffffec\n.inst 0xe1a00004\n.inst 0xe8bd0030\n.inst 0xe12fff1e\n.word 0x00435d90\n.word 0x000001b6\n");
}

// DECOMP_FUNC(0x00262edc, 144)
extern "C" __attribute__((naked)) void camp_func_00262edc() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe59f007c\n.inst 0xe5900004\n.inst 0xe2805090\n.inst 0xeb001f7a\n.inst 0xe2502000\n.inst 0xd3a00000\n.inst 0xda00000a\n.inst 0xe2020001\n.inst 0xe3500000\n.inst 0xe3a01000\n.inst 0xda000006\n.inst 0xe0853081\n.inst 0xe1d337b8\n.inst 0xe1530004\n.inst 0x0a00000a\n.inst 0xe2811001\n.inst 0xe1500001\n.inst 0xcafffff8\n.inst 0xe1500002\n.inst 0xaa00000a\n.inst 0xe0851080\n.inst 0xe1d137b8\n.inst 0xe1530004\n.inst 0x11d117ba\n.inst 0x11510004\n.inst 0x1a000001\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.inst 0xe2800002\n.inst 0xe1520000\n.inst 0xcafffff4\n.inst 0xe3a00000\n.inst 0xe8bd8070\n.word 0x0043e2a8\n");
}

// DECOMP_FUNC(0x002642d0, 152)
extern "C" __attribute__((naked)) void script_vm_func_002642d0() {
    asm volatile(".arm\n.inst 0xe92d4038\n.inst 0xe5900000\n.inst 0xe7900101\n.inst 0xe590400c\n.inst 0xe3540000\n.inst 0x0a000019\n.inst 0xe58d0000\n.inst 0xe594101c\n.inst 0xe5942018\n.inst 0xe1a0300d\n.inst 0xe1520001\n.inst 0x0a000004\n.inst 0xe5920000\n.inst 0xe59dc000\n.inst 0xe150000c\n.inst 0x12822004\n.inst 0x1afffff8\n.inst 0xe1520001\n.inst 0x0a000002\n.inst 0xe2820004\n.inst 0xeb014d39\n.inst 0xe1a02000\n.inst 0xe594001c\n.inst 0xe584201c\n.inst 0xe1500002\n.inst 0x13a00001\n.inst 0x03a00000\n.inst 0xe3500000\n.inst 0x0a000002\n.inst 0xe59d0000\n.inst 0xe3a01000\n.inst 0xe580100c\n.inst 0xe59f000c\n.inst 0xe5901000\n.inst 0xe2411001\n.inst 0xe5801000\n.inst 0xe8bd8038\n.word 0x004dad80\n");
}

// DECOMP_FUNC(0x002649c0, 136)
extern "C" __attribute__((naked)) void script_vm_func_002649c0() {
    asm volatile(".arm\n.inst 0xe59f107c\n.inst 0xe59f0070\n.inst 0xe3a03001\n.inst 0xe59f206c\n.inst 0xe5911000\n.inst 0xe5c032f8\n.inst 0xe5913040\n.inst 0xe58032fc\n.inst 0xe5913048\n.inst 0xe5803300\n.inst 0xe5903008\n.inst 0xe5803304\n.inst 0xe5922000\n.inst 0xe282301c\n.inst 0xec930a03\n.inst 0xe2803fc2\n.inst 0xec830a03\n.inst 0xe592304c\n.inst 0xe5803314\n.inst 0xe5913040\n.inst 0xe580331c\n.inst 0xe5911048\n.inst 0xe5801320\n.inst 0xe282101c\n.inst 0xe891100a\n.inst 0xe5801324\n.inst 0xe2801fca\n.inst 0xe8811008\n.inst 0xe592104c\n.inst 0xe5801330\n.inst 0xe12fff1e\n.word 0x0049f91c\n.word 0x00447e88\n.word 0x00447060\n");
}

// DECOMP_FUNC(0x00269e54, 140)
extern "C" __attribute__((naked)) void func_00269e54() {
    asm volatile(".arm\n.inst 0xe59f107c\n.inst 0xe92d0030\n.inst 0xe1d040fe\n.inst 0xe5912000\n.inst 0xe3520000\n.inst 0x15921064\n.inst 0x13510015\n.inst 0x0a000015\n.inst 0xe2822d7f\n.inst 0xe3a01000\n.inst 0xe592c000\n.inst 0xe0812201\n.inst 0xe0822301\n.inst 0xe08c2182\n.inst 0xe5923000\n.inst 0xe3130001\n.inst 0x0a000009\n.inst 0xe3130040\n.inst 0x1a000007\n.inst 0xe3130008\n.inst 0x0a000005\n.inst 0xe592327c\n.inst 0xe1530000\n.inst 0x1a000002\n.inst 0xe59f0020\n.inst 0xe19040f2\n.inst 0xea000002\n.inst 0xe2811001\n.inst 0xe351006d\n.inst 0xbaffffec\n.inst 0xe1a00004\n.inst 0xe8bd0030\n.inst 0xe12fff1e\n.word 0x00435d90\n.word 0x000001b6\n");
}

// DECOMP_FUNC(0x0026b734, 152)
extern "C" __attribute__((naked)) void ui_func_0026b734() {
    asm volatile(".arm\n.inst 0xe92d4030\n.inst 0xe24dd014\n.inst 0xe1a0000d\n.inst 0xeb016849\n.inst 0xe1cd00d0\n.inst 0xe1cd00f8\n.inst 0xe28d0008\n.inst 0xebffa3b1\n.inst 0xe1a05000\n.inst 0xe28d0008\n.inst 0xebffa398\n.inst 0xe1a04000\n.inst 0xe28d0008\n.inst 0xebffa37f\n.inst 0xe1a02005\n.inst 0xe1a01004\n.inst 0xeb00f3ed\n.inst 0xe0800080\n.inst 0xe1a04180\n.inst 0xe28d0008\n.inst 0xeb05d5c8\n.inst 0xe0800004\n.inst 0xe0600200\n.inst 0xe1a04100\n.inst 0xe28d0008\n.inst 0xeb05d5dd\n.inst 0xe0800004\n.inst 0xe0600200\n.inst 0xe1a04100\n.inst 0xe28d0008\n.inst 0xeb05d5f3\n.inst 0xe59f1010\n.inst 0xe0800004\n.inst 0xe591100c\n.inst 0xe5810004\n.inst 0xe28dd014\n.inst 0xe8bd8030\n.word 0x0043e2a8\n");
}

// DECOMP_FUNC(0x0026ea7c, 152)
extern "C" __attribute__((naked)) void engine_func_0026ea7c() {
    asm volatile(".arm\n.inst 0xee700a82\n.inst 0xee311a22\n.inst 0xee332a85\n.inst 0xee742a25\n.inst 0xed2d8b02\n.inst 0xe3500000\n.inst 0xed9f8a1c\n.inst 0xeddf7a1c\n.inst 0xee700a82\n.inst 0xee311a22\n.inst 0xee600a88\n.inst 0xee211a08\n.inst 0x0a000009\n.inst 0xee300a21\n.inst 0xee731a24\n.inst 0xed9f2a13\n.inst 0xe3500001\n.inst 0xee300a21\n.inst 0xee200a02\n.inst 0x0a000006\n.inst 0xe3500002\n.inst 0x0a000008\n.inst 0xea000009\n.inst 0xeef06a60\n.inst 0xeeb07a41\n.inst 0xeeb06a67\n.inst 0xea000005\n.inst 0xeeb06a40\n.inst 0xeeb07a41\n.inst 0xeef06a67\n.inst 0xea000001\n.inst 0xeeb06b40\n.inst 0xeeb07a67\n.inst 0xec816a03\n.inst 0xecbd8b02\n.inst 0xe12fff1e\n.word 0x3e800000\n.word 0x00000000\n");
}

// DECOMP_FUNC(0x0026f370, 136)
extern "C" __attribute__((naked)) void func_0026f370() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe1a05000\n.inst 0xe1a07001\n.inst 0xe1a06002\n.inst 0xed2d8b02\n.inst 0xeef08a40\n.inst 0xeeb08a60\n.inst 0xe3a04000\n.inst 0xe1a01002\n.inst 0xe1a00007\n.inst 0xeb015891\n.inst 0xee381a68\n.inst 0xeddf0a13\n.inst 0xe1560007\n.inst 0x03a04001\n.inst 0xed850a00\n.inst 0xeeb41ae0\n.inst 0xeef1fa10\n.inst 0xda000003\n.inst 0xeeb40ac8\n.inst 0xeef1fa10\n.inst 0xaa000006\n.inst 0xea000002\n.inst 0xeeb40ac8\n.inst 0xeef1fa10\n.inst 0x9a000002\n.inst 0xe3540000\n.inst 0x03a00000\n.inst 0x0a000001\n.inst 0xed858a00\n.inst 0xe3a00001\n.inst 0xecbd8b02\n.inst 0xe8bd81f0\n.word 0x00000000\n");
}

// DECOMP_FUNC(0x002701c4, 140)
extern "C" __attribute__((naked)) void script_vm_func_002701c4() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe59f4074\n.inst 0xe5940010\n.inst 0xe3500000\n.inst 0x0a000019\n.inst 0xebffed99\n.inst 0xe5941010\n.inst 0xe3a02080\n.inst 0xeb01335b\n.inst 0xebffed90\n.inst 0xe5941014\n.inst 0xeb00f652\n.inst 0xeb014266\n.inst 0xe59f2048\n.inst 0xe5941018\n.inst 0xeb013354\n.inst 0xeb01c251\n.inst 0xeb015617\n.inst 0xe59f0038\n.inst 0xe5900000\n.inst 0xebfff8de\n.inst 0xe5940010\n.inst 0xeb01504f\n.inst 0xe5940014\n.inst 0xeb01504d\n.inst 0xe5940018\n.inst 0xeb01504b\n.inst 0xe3a00000\n.inst 0xe5840010\n.inst 0xe5840014\n.inst 0xe5840018\n.inst 0xe8bd8010\n.word 0x0044de28\n.word 0x00024d28\n.word 0x00433158\n");
}

// DECOMP_FUNC(0x002706e4, 140)
extern "C" __attribute__((naked)) void script_vm_func_002706e4() {
    asm volatile(".arm\n.inst 0xe59f0080\n.inst 0xe92d4070\n.inst 0xe59f5074\n.inst 0xe5904000\n.inst 0xe2850094\n.inst 0xeb0002b8\n.inst 0xe3a00001\n.inst 0xe5c502f8\n.inst 0xe594002c\n.inst 0xe2852fc3\n.inst 0xe58502fc\n.inst 0xe5940030\n.inst 0xe5850300\n.inst 0xe5950008\n.inst 0xe5850304\n.inst 0xed950a25\n.inst 0xe1c509d8\n.inst 0xed850ac2\n.inst 0xe8820003\n.inst 0xedd50a28\n.inst 0xedc50ac5\n.inst 0xedc50ac6\n.inst 0xe594202c\n.inst 0xe585231c\n.inst 0xe5942030\n.inst 0xe5852320\n.inst 0xe2852fca\n.inst 0xed850ac9\n.inst 0xe8820003\n.inst 0xe5950090\n.inst 0xe5850330\n.inst 0xe5850334\n.inst 0xe8bd8070\n.word 0x0049f91c\n.word 0x00447e28\n");
}

// DECOMP_FUNC(0x00275984, 148)
extern "C" __attribute__((naked)) void script_vm_func_00275984() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe59f6084\n.inst 0xe5960000\n.inst 0xe5d01009\n.inst 0xe3510000\n.inst 0x15d01008\n.inst 0x13510000\n.inst 0x0a00001a\n.inst 0xe5902004\n.inst 0xe3a01000\n.inst 0xe1a04001\n.inst 0xe3520000\n.inst 0xe5c01008\n.inst 0xda000014\n.inst 0xe5960000\n.inst 0xe0805284\n.inst 0xe5f5000c\n.inst 0xe3500000\n.inst 0x0a00000a\n.inst 0xe1d501b0\n.inst 0xe3500000\n.inst 0x1a000007\n.inst 0xe5950008\n.inst 0xe3500000\n.inst 0x1a000004\n.inst 0xe2851014\n.inst 0xe5950004\n.inst 0xec910a03\n.inst 0xeb0071ba\n.inst 0xe5850008\n.inst 0xe5960000\n.inst 0xe2844001\n.inst 0xe5900004\n.inst 0xe1500004\n.inst 0xcaffffea\n.inst 0xe8bd8070\n.word 0x00448c20\n");
}

// DECOMP_FUNC(0x002762e8, 132)
extern "C" void* engine_func_002c2b1c();
extern "C" void script_vm_func_002899c4(s32 val, s32 p1, s32 p2);

extern "C" void script_vm_func_002762e8(s32 target_id) {
    auto* const ctx = static_cast<u8*>(engine_func_002c2b1c());
    const s32 count = *reinterpret_cast<const s8*>(ctx + 0xDE3);
    if (count <= 0) {
        return;
    }

    for (s32 i = 0; i < *reinterpret_cast<const s8*>(ctx + 0xDE3); ++i) {
        auto* const active_ptr = ctx + 0xDE4 + i;
        if (*active_ptr == 0) {
            continue;
        }

        const s16 id = *reinterpret_cast<const s16*>(ctx + 0xE04 + i * 2);
        if (id != target_id) {
            continue;
        }

        *active_ptr = 0;
        const s16 val = *reinterpret_cast<const s16*>(ctx + 0xDF4 + i * 2);
        if (val != 0) {
            script_vm_func_002899c4(val, 1, 1);
        }
    }
}

// DECOMP_FUNC(0x00276c24, 136)
extern "C" __attribute__((naked)) void script_vm_func_00276c24() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3720001\n.inst 0xe1a05000\n.inst 0xe59f8070\n.inst 0xe1a06001\n.inst 0xe1a07002\n.inst 0xe8880007\n.inst 0x0a000015\n.inst 0xe3a04000\n.inst 0xebff563a\n.inst 0xe3500000\n.inst 0xda000011\n.inst 0xe1a00004\n.inst 0xeb001b56\n.inst 0xe1d010d0\n.inst 0xe1510005\n.inst 0x01d010d1\n.inst 0x01510006\n.inst 0x05d01002\n.inst 0x01510007\n.inst 0x1a000003\n.inst 0xe5d00003\n.inst 0xe35000ff\n.inst 0x1a000006\n.inst 0xea000004\n.inst 0xe2844001\n.inst 0xebff5629\n.inst 0xe1500004\n.inst 0xe320f000\n.inst 0xcaffffed\n.inst 0xe3e00000\n.inst 0xe588000c\n.inst 0xe8bd81f0\n.word 0x0049fd14\n");
}

// DECOMP_FUNC(0x00277dcc, 128)
extern "C" u32 script_vm_func_002857e4();
extern "C" s32 script_vm_func_00255050(u32 code);

extern "C" __attribute__((minsize)) void script_vm_func_00277dcc(u16 code, u16 param) {
    if (code == 0x24) {
        return;
    }

    if (script_vm_func_002857e4() == 1) {
        if (script_vm_func_00255050(0x29) == 1) {
            return;
        }
    }

    if (code != 0x18 && code < 0x64) {
        if (script_vm_func_00255050(code) == 1) {
            return;
        }
    }

    auto* const global_ptr = *reinterpret_cast<u8**>(0x00447A78u);
    auto* const target = reinterpret_cast<u32*>(global_ptr + 0xCCB8u);
    target[0] = 1;
    target[1] = (static_cast<u32>(param) << 16) | code;
}

// DECOMP_FUNC(0x00289044, 140)
extern "C" __attribute__((naked)) void camp_func_00289044() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe2516000\n.inst 0xe1a07000\n.inst 0xaa000004\n.inst 0xeb00b5a4\n.inst 0xe1d001fc\n.inst 0xe1500007\n.inst 0xba000013\n.inst 0xea000017\n.inst 0xe320f000\n.inst 0xeb007e65\n.inst 0xe1a05000\n.inst 0xe3a04000\n.inst 0xe0850004\n.inst 0xe2800a09\n.inst 0xe1d00fd0\n.inst 0xe3500000\n.inst 0xba00000b\n.inst 0xeb007e54\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000007\n.inst 0xe1d014b6\n.inst 0xe1510006\n.inst 0x1a000004\n.inst 0xe1d000fe\n.inst 0xe1500007\n.inst 0xaa000001\n.inst 0xe3a00001\n.inst 0xe8bd81f0\n.inst 0xe2844001\n.inst 0xe3540018\n.inst 0xbaffffeb\n.inst 0xe3a00000\n.inst 0xe8bd81f0\n");
}

// DECOMP_FUNC(0x0028de84, 136)
extern "C" __attribute__((naked)) void script_vm_func_0028de84() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe5d00023\n.inst 0xe3e05000\n.inst 0xe3500000\n.inst 0x1a000019\n.inst 0xe5940034\n.inst 0xe3500000\n.inst 0xaa000002\n.inst 0xeb00a20f\n.inst 0xe1d027b2\n.inst 0xea000002\n.inst 0xe320f000\n.inst 0xeb006ac9\n.inst 0xe1d024b4\n.inst 0xe3a00001\n.inst 0xe3a01000\n.inst 0xe1a03000\n.inst 0xe1120013\n.inst 0x0a000008\n.inst 0xe594c01c\n.inst 0xe15c0001\n.inst 0x12811001\n.inst 0x1a000004\n.inst 0xe6bf0070\n.inst 0xeb008a26\n.inst 0xe1a05000\n.inst 0xe320f000\n.inst 0xea000002\n.inst 0xe2800001\n.inst 0xe350000b\n.inst 0xbafffff1\n.inst 0xe1a00005\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002918c4, 140)
extern "C" __attribute__((naked)) void ui_func_002918c4() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3500000\n.inst 0xed9f0a1e\n.inst 0xe1a05001\n.inst 0xe1a04002\n.inst 0x0a00000a\n.inst 0xe3500001\n.inst 0x0a000010\n.inst 0xe3500002\n.inst 0x1a00000d\n.inst 0xe3a01001\n.inst 0xe3a00000\n.inst 0xeb0015c2\n.inst 0xe6af0070\n.inst 0xe3500000\n.inst 0xe1a01005\n.inst 0x0a000007\n.inst 0xe3a00000\n.inst 0xeb0015bc\n.inst 0xee000a10\n.inst 0xee004a90\n.inst 0xeeb81ac0\n.inst 0xeef80a60\n.inst 0xee810a20\n.inst 0xe8bd8070\n.inst 0xe3a00000\n.inst 0xeb0015b4\n.inst 0xee000a10\n.inst 0xee004a90\n.inst 0xeeb80ac0\n.inst 0xeef80a60\n.inst 0xee801a20\n.inst 0xeeb10a41\n.inst 0xe8bd8070\n.word 0x00000000\n");
}

// DECOMP_FUNC(0x00295300, 140)
extern "C" __attribute__((naked)) void ui_func_00295300() {
    asm volatile(".arm\n.inst 0xe5901028\n.inst 0xe3510000\n.inst 0x03a00000\n.inst 0x0a00001c\n.inst 0xe5d0203c\n.inst 0xe3520000\n.inst 0x1a000018\n.inst 0xe3a02001\n.inst 0xe5c0203c\n.inst 0xe5801010\n.inst 0xe59f2058\n.inst 0xe5913000\n.inst 0xe1530002\n.inst 0x13a01000\n.inst 0x15801010\n.inst 0x1a00000f\n.inst 0xe2812028\n.inst 0xe5802014\n.inst 0xe1d130b4\n.inst 0xe0822283\n.inst 0xe5802018\n.inst 0xe5913008\n.inst 0xe0833103\n.inst 0xe0822183\n.inst 0xe580201c\n.inst 0xe1d130b6\n.inst 0xe0822103\n.inst 0xe5802020\n.inst 0xe1d110bc\n.inst 0xe0811081\n.inst 0xe0821181\n.inst 0xe5801024\n.inst 0xe3a00001\n.inst 0xe12fff1e\n.word 0x57444b4e\n");
}

// DECOMP_FUNC(0x00295f04, 140)
extern "C" __attribute__((naked)) void script_vm_func_00295f04() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3510063\n.inst 0xe1a06000\n.inst 0xe1a04001\n.inst 0xa3a00000\n.inst 0xaa00001a\n.inst 0xe1a05004\n.inst 0xe3a01001\n.inst 0xe3a00009\n.inst 0xeb00abe5\n.inst 0xeb00abda\n.inst 0xe0800105\n.inst 0xe5105004\n.inst 0xe1a00006\n.inst 0xeb008d08\n.inst 0xe5d00003\n.inst 0xe0440000\n.inst 0xe2804001\n.inst 0xe3540000\n.inst 0xd3a00064\n.inst 0xda000007\n.inst 0xe354000a\n.inst 0xc3a0400a\n.inst 0xe3a01002\n.inst 0xe3a00009\n.inst 0xeb00abd5\n.inst 0xeb00abca\n.inst 0xe0800084\n.inst 0xe15000b2\n.inst 0xe59f100c\n.inst 0xe0000095\n.inst 0xe0801091\n.inst 0xe1a002a0\n.inst 0xe8bd8070\n.word 0x51eb851f\n");
}

// DECOMP_FUNC(0x002960d4, 128)
extern "C" const void* Tbb_GetGlobalSubTable(u32 table_id, u32 sub_id);
extern "C" const void* Tbb_GetPayloadData(const void* subtable);
extern "C" const u8* camp_func_002b9364(u16 key);

extern "C" __attribute__((minsize)) u32 camp_func_002960d4(u16 key, u32 index, s32 stat_val) {
    const void* const sub1 = Tbb_GetGlobalSubTable(9, 1);
    const auto* const table1 = reinterpret_cast<const u32*>(Tbb_GetPayloadData(sub1));
    const u32 base_val = table1[index - 1];

    const u8* const rec = camp_func_002b9364(key);
    s32 diff = stat_val - static_cast<s32>(rec[3]) + 1;

    u32 scale;
    if (diff <= 0) {
        scale = 100;
    } else {
        if (diff > 10) {
            diff = 10;
        }
        const void* const sub2 = Tbb_GetGlobalSubTable(9, 2);
        const auto* const table2 = reinterpret_cast<const u16*>(Tbb_GetPayloadData(sub2));
        scale = table2[diff - 1];
    }

    const u32 prod = base_val * scale;
    u32 hi, lo;
    __asm__("umull %0, %1, %2, %3" : "=&r"(lo), "=&r"(hi) : "r"(0x51EB851Fu), "r"(prod));
    return hi >> 5;
}

// DECOMP_FUNC(0x0029933c, 152)
extern "C" __attribute__((naked)) void camp_func_0029933c() {
    asm volatile(".arm\n.inst 0xe59f0088\n.inst 0xe92d4038\n.inst 0xe5904008\n.inst 0xeb009e11\n.inst 0xe2800b7d\n.inst 0xe2800054\n.inst 0xe5900000\n.inst 0xe3500000\n.inst 0x03a00001\n.inst 0x0a000018\n.inst 0xeb009e0a\n.inst 0xe2800b7d\n.inst 0xe2800054\n.inst 0xe3a01001\n.inst 0xe5900000\n.inst 0xe3a0200b\n.inst 0xe28430a4\n.inst 0xe584009c\n.inst 0xe5c410a1\n.inst 0xe5c410a0\n.inst 0xe2840b02\n.inst 0xe280006c\n.inst 0xe58d2000\n.inst 0xed9f0a0c\n.inst 0xe3e02000\n.inst 0xe3a0100e\n.inst 0xe1a04000\n.inst 0xeb0091df\n.inst 0xe3a01016\n.inst 0xe1a00004\n.inst 0xeb007f49\n.inst 0xe3a01006\n.inst 0xe1a00004\n.inst 0xeb00971a\n.inst 0xe3a00001\n.inst 0xe8bd8038\n.word 0x0043e188\n.word 0x3f800000\n");
}

// DECOMP_FUNC(0x0029957c, 144)
extern "C" __attribute__((naked)) void engine_func_0029957c() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe59f407c\n.inst 0xe3500000\n.inst 0xe2841000\n.inst 0xe5942004\n.inst 0xe5911004\n.inst 0xe2811d7a\n.inst 0x0a000004\n.inst 0xe3500001\n.inst 0x0a000006\n.inst 0xe3500002\n.inst 0x0a000009\n.inst 0xea00000d\n.inst 0xe5910000\n.inst 0xe3a02007\n.inst 0xe3a01000\n.inst 0xea000002\n.inst 0xe5910000\n.inst 0xe3a02007\n.inst 0xe3a01001\n.inst 0xebffec48\n.inst 0xea000004\n.inst 0xe2822d7a\n.inst 0xe3a01002\n.inst 0xe5920000\n.inst 0xe3a02007\n.inst 0xebffec42\n.inst 0xe5940004\n.inst 0xe59f3014\n.inst 0xe3a02000\n.inst 0xe3a01006\n.inst 0xe5802010\n.inst 0xe7831000\n.inst 0xe8bd8010\n.word 0x0044e140\n.word 0x000012dc\n");
}

// DECOMP_FUNC(0x0029bddc, 140)
extern "C" __attribute__((naked)) void engine_func_0029bddc() {
    asm volatile(".arm\n.inst 0xe92d40f8\n.inst 0xe1a05001\n.inst 0xe1a06000\n.inst 0xeb00155b\n.inst 0xe1a04000\n.inst 0xe5900008\n.inst 0xe3a01000\n.inst 0xe5805008\n.inst 0xe1a00006\n.inst 0xeb00518b\n.inst 0xe3a01001\n.inst 0xe5840004\n.inst 0xeb005181\n.inst 0xe5940004\n.inst 0xebf9f0e5\n.inst 0xe5940004\n.inst 0xe1a0100d\n.inst 0xebfa7142\n.inst 0xe59d1000\n.inst 0xeb005b52\n.inst 0xe1a01000\n.inst 0xe5940008\n.inst 0xe5801004\n.inst 0xe5940008\n.inst 0xe1a01005\n.inst 0xeb003594\n.inst 0xe1a00004\n.inst 0xeb005ab6\n.inst 0xe59f0010\n.inst 0xe3a02000\n.inst 0xe1a01004\n.inst 0xeb005a6d\n.inst 0xe1a00004\n.inst 0xe8bd80f8\n.word 0x004dad60\n");
}

// DECOMP_FUNC(0x002a140c, 148)
extern "C" __attribute__((naked)) void engine_func_002a140c() {
    asm volatile(".arm\n.inst 0xe52de004\n.inst 0xeb000058\n.inst 0xe2001bff\n.inst 0xe3510b4e\n.inst 0x1a00001a\n.inst 0xe59f106c\n.inst 0xe1500001\n.inst 0xe0402001\n.inst 0x0a00000e\n.inst 0xca00000f\n.inst 0xe282160a\n.inst 0xe2911007\n.inst 0x0a00000a\n.inst 0xe59f2050\n.inst 0xe0911002\n.inst 0x12411502\n.inst 0x12511088\n.inst 0x0a000005\n.inst 0xe1a00b00\n.inst 0xe1a00b20\n.inst 0xe3500060\n.inst 0xba000009\n.inst 0xe3500080\n.inst 0xaa000007\n.inst 0xe3a00001\n.inst 0xe49df004\n.inst 0xe59f1020\n.inst 0xe0911000\n.inst 0x12411602\n.inst 0x12511008\n.inst 0x0afffff8\n.inst 0xeafffff1\n.inst 0xe3a00000\n.inst 0xe49df004\n.word 0xc9413910\n.word 0xffe00084\n.word 0x36bec6ee\n");
}

// DECOMP_FUNC(0x002a515c, 128)
extern "C" u32 engine_func_002ae16c(const void* sub);
extern "C" u32 engine_func_002ae074(const void* field8, u32 entry, void* target);

extern "C" u32 engine_func_002a515c(void* target, u32 slot_index) {
    auto* const ctx = *reinterpret_cast<u8* const*>(0x0043DFC0u);
    if (!ctx) {
        return 0;
    }

    auto* const sub = *reinterpret_cast<u8* const*>(ctx + 0x5E4);
    if (!sub || !engine_func_002ae16c(sub)) {
        return 1;
    }

    const auto* const sub_field8 = *reinterpret_cast<const void* const*>(sub + 8);
    const auto* const table = reinterpret_cast<const u32*>(0x0043E048u);
    const u32 ret = engine_func_002ae074(sub_field8, table[slot_index], target);

    if (slot_index == 0) {
        auto* const target_y = reinterpret_cast<float*>(static_cast<u8*>(target) + 8);
        const float offset = *reinterpret_cast<const float*>(ctx + 0x640);
        *target_y += offset;
    }

    return ret;
}

// DECOMP_FUNC(0x002a9414, 132)
extern "C" void battle_func_002ade34(void* buf, u32 size, u32 mode);

extern "C" void func_002a9414(const u32* a, const u32* b, const u32* c) {
    u32 buf[12];
    auto* const src1 = reinterpret_cast<const u32*>(0x00409780u + 0x130u);
    auto* const src2 = reinterpret_cast<const u32*>(0x00409780u + 0x150u);

    for (int i = 0; i < 8; ++i) {
        buf[i] = src1[i];
    }
    for (int i = 0; i < 4; ++i) {
        buf[8 + i] = src2[i];
    }

    buf[0] = a[2];
    buf[2] = a[1];
    buf[3] = a[0];

    buf[4] = b[2];
    buf[6] = b[1];
    buf[7] = b[0];

    buf[10] = c[1];
    buf[11] = c[0];

    battle_func_002ade34(buf, 0x30, 1);
}

// DECOMP_FUNC(0x002b0614, 140)
extern "C" __attribute__((naked)) void engine_func_002b0614() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xeb004b1b\n.inst 0xe3500008\n.inst 0xc3a00008\n.inst 0xca000002\n.inst 0xe3500000\n.inst 0xd3a01000\n.inst 0xda000009\n.inst 0xe2001001\n.inst 0xe3510000\n.inst 0xe3a02000\n.inst 0xda000005\n.inst 0xe7d43002\n.inst 0xe353003a\n.inst 0x0a000010\n.inst 0xe2822001\n.inst 0xe1510002\n.inst 0xcafffff9\n.inst 0xe1510000\n.inst 0xaa000009\n.inst 0xe7d42001\n.inst 0xe352003a\n.inst 0x0a000008\n.inst 0xe0842001\n.inst 0xe5d22001\n.inst 0xe352003a\n.inst 0x0a000004\n.inst 0xe2811002\n.inst 0xe1500001\n.inst 0xcafffff5\n.inst 0xe3a00000\n.inst 0xe8bd8010\n.inst 0xe3a00001\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x002b32e0, 144)
extern "C" __attribute__((naked)) void func_002b32e0() {
    asm volatile(".arm\n.inst 0xe59f1084\n.inst 0xe92d0030\n.inst 0xe281201c\n.inst 0xe5914028\n.inst 0xe892100c\n.inst 0xe1520000\n.inst 0x8a000003\n.inst 0xe591502c\n.inst 0xe0822005\n.inst 0xe1500002\n.inst 0x9a000014\n.inst 0xe1530000\n.inst 0x8a000004\n.inst 0xe5912030\n.inst 0xe0822003\n.inst 0xe1500002\n.inst 0x93a00001\n.inst 0x9a00000e\n.inst 0xe15c0000\n.inst 0x8a000004\n.inst 0xe5912034\n.inst 0xe082200c\n.inst 0xe1500002\n.inst 0x93a00002\n.inst 0x9a000007\n.inst 0xe1540000\n.inst 0x8a000004\n.inst 0xe5911038\n.inst 0xe0811004\n.inst 0xe1510000\n.inst 0x23a00003\n.inst 0x2a000000\n.inst 0xe3a00000\n.inst 0xe8bd0030\n.inst 0xe12fff1e\n.word 0x00465120\n");
}

// DECOMP_FUNC(0x002b7584, 152)
extern "C" __attribute__((naked)) void func_002b7584() {
    asm volatile(".arm\n.inst 0xe2812028\n.inst 0xed9f0a22\n.inst 0xec921a02\n.inst 0xeec10a81\n.inst 0xedc00a04\n.inst 0xed911a0a\n.inst 0xedd10a0b\n.inst 0xee311a40\n.inst 0xeec01a81\n.inst 0xedc01a05\n.inst 0xedd11a00\n.inst 0xed912a0a\n.inst 0xedd10a02\n.inst 0xed911a0b\n.inst 0xee611a82\n.inst 0xee302ac0\n.inst 0xeec10a21\n.inst 0xee221a20\n.inst 0xed801a00\n.inst 0xed911a02\n.inst 0xee311a00\n.inst 0xee610a20\n.inst 0xedc00a01\n.inst 0xedd11a05\n.inst 0xed912a0a\n.inst 0xedd10a06\n.inst 0xed911a0b\n.inst 0xee611a82\n.inst 0xee302a80\n.inst 0xeec10a21\n.inst 0xee221a20\n.inst 0xed801a03\n.inst 0xed911a06\n.inst 0xee310a40\n.inst 0xee200a20\n.inst 0xed800a02\n.inst 0xe12fff1e\n.word 0x3f800000\n");
}

// DECOMP_FUNC(0x002b8070, 148)
extern "C" __attribute__((naked)) void ui_func_002b8070() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xed2d8b0a\n.inst 0xeeb08b40\n.inst 0xeeb09b41\n.inst 0xeeb0ab42\n.inst 0xeeb0bb43\n.inst 0xeeb0ca44\n.inst 0xeb000124\n.inst 0xe3e03000\n.inst 0xeeb04a4c\n.inst 0xeef03a6b\n.inst 0xeeb03a4b\n.inst 0xeef02a6a\n.inst 0xeeb02a4a\n.inst 0xeef01a69\n.inst 0xeeb01a49\n.inst 0xeef00a68\n.inst 0xeeb00a48\n.inst 0xe1a02003\n.inst 0xe1a01003\n.inst 0xe1a00003\n.inst 0xeb00000e\n.inst 0xecbd8b0a\n.inst 0xe8bd4010\n.inst 0xe1a00000\n.inst 0xe59f0024\n.inst 0xe52de004\n.inst 0xe24dd01c\n.inst 0xe3a02001\n.inst 0xec900a06\n.inst 0xe3a01018\n.inst 0xe1a0000d\n.inst 0xec8d0a06\n.inst 0xebffd74e\n.inst 0xe28dd01c\n.inst 0xe49df004\n.word 0x00409898\n");
}

// DECOMP_FUNC(0x002b89fc, 132)
extern "C" u32 ui_func_002b2530(void* handle);
extern "C" void script_vm_func_002a72fc(void* sub);
extern "C" void engine_func_002b2520(void* sub);
extern "C" void engine_func_002c4360(void* main);

extern "C" u32 battle_func_002b89fc() {
    auto** const p_main = reinterpret_cast<u8**>(0x0044DB8Cu);
    auto* main = *p_main;
    if (!main) {
        return 0;
    }

    void* const handle = *reinterpret_cast<void**>(main);
    if (ui_func_002b2530(handle) != 0) {
        return 1;
    }

    if (main[0x18] == 0) {
        return 1;
    }

    main = *p_main;
    if (!main) {
        return 0;
    }

    main[0x18] = 1;

    void* sub = *reinterpret_cast<void**>(main + 0x1C);
    if (sub != nullptr) {
        script_vm_func_002a72fc(sub);
        sub = *reinterpret_cast<void**>(main + 0x1C);
        engine_func_002b2520(sub);
        *reinterpret_cast<void**>(main + 0x1C) = nullptr;
    }

    engine_func_002c4360(*p_main);
    *p_main = nullptr;

    return 0;
}

// DECOMP_FUNC(0x002baacc, 144)
extern "C" __attribute__((naked)) void engine_func_002baacc() {
    asm volatile(".arm\n.inst 0xe92d4030\n.inst 0xe24dd01c\n.inst 0xe3a05000\n.inst 0xe1a04000\n.inst 0xe5805000\n.inst 0xe5845004\n.inst 0xe5845008\n.inst 0xe584500c\n.inst 0xe3a00001\n.inst 0xe5845010\n.inst 0xe5c40414\n.inst 0xe5c40415\n.inst 0xe584541c\n.inst 0xe2840e42\n.inst 0xe5845418\n.inst 0xeb00220d\n.inst 0xe59f1044\n.inst 0xe3a00e31\n.inst 0xe3a02054\n.inst 0xe2413054\n.inst 0xe58d3004\n.inst 0xe58d1014\n.inst 0xe3a0c048\n.inst 0xe2433048\n.inst 0xe58d2008\n.inst 0xe58d0018\n.inst 0xe3a02078\n.inst 0xe2431078\n.inst 0xe2840e42\n.inst 0xe58d500c\n.inst 0xe58d5010\n.inst 0xe58dc000\n.inst 0xeb0021e9\n.inst 0xe28dd01c\n.inst 0xe8bd8030\n.word 0x003ff3f4\n");
}

// DECOMP_FUNC(0x002bc170, 144)
extern "C" __attribute__((naked)) void engine_func_002bc170() {
    asm volatile(".arm\n.inst 0xed9f3a1f\n.inst 0xee306ac0\n.inst 0xee304a80\n.inst 0xee715ac1\n.inst 0xee724ac2\n.inst 0xeddf2a1c\n.inst 0xee315a81\n.inst 0xedc02a01\n.inst 0xedc02a02\n.inst 0xedc02a04\n.inst 0xedc02a06\n.inst 0xeec30a06\n.inst 0xedc02a08\n.inst 0xedc02a09\n.inst 0xedc02a0c\n.inst 0xeddf3a11\n.inst 0xedc02a0d\n.inst 0xe2801038\n.inst 0xecc12a02\n.inst 0xee831a25\n.inst 0xee612a23\n.inst 0xee251a41\n.inst 0xee830a24\n.inst 0xee203aa3\n.inst 0xee640a60\n.inst 0xed800a0a\n.inst 0xee621a00\n.inst 0xed803a00\n.inst 0xedc00a03\n.inst 0xedc02a05\n.inst 0xed801a07\n.inst 0xedc01a0b\n.inst 0xe12fff1e\n.word 0x3f800000\n.word 0x40000000\n.word 0x00000000\n");
}

// DECOMP_FUNC(0x002bdb2c, 152)
extern "C" void engine_func_002c4b30(volatile u8* destination, u32 size);

extern "C" __attribute__((minsize)) u32 camp_func_002bdb2c(
    u8* __restrict sprite, u32 type, u32 index,
    const u8* __restrict group,
    u32 panel, f32 scale) {
    engine_func_002c4b30(sprite, 0x8C);

    *reinterpret_cast<u32*>(sprite + 0x00) = type;
    *reinterpret_cast<u32*>(sprite + 0x04) = index;
    *reinterpret_cast<u32*>(sprite + 0x08) = 0xFFFFFFFFu;
    *reinterpret_cast<f32*>(sprite + 0x20) = scale;
    *reinterpret_cast<u16*>(sprite + 0x38) = static_cast<u16>(panel);
    *reinterpret_cast<f32*>(sprite + 0x24) = 1.0f;
    *reinterpret_cast<f32*>(sprite + 0x28) = 1.0f;
    *reinterpret_cast<f32*>(sprite + 0x2C) = 1.0f;

    *reinterpret_cast<u32*>(sprite + 0x48) = reinterpret_cast<u32>(group);
    const u32* const group_words = reinterpret_cast<const u32*>(group);
    *reinterpret_cast<u32*>(sprite + 0x4C) = group_words[3];
    *reinterpret_cast<u32*>(sprite + 0x58) = group_words[4];
    *reinterpret_cast<u32*>(sprite + 0x64) = group_words[5];
    *reinterpret_cast<u32*>(sprite + 0x70) = group_words[6];
    *reinterpret_cast<u32*>(sprite + 0x78) = group_words[7];

    sprite[0x86] = 1;
    sprite[0x87] = 1;
    sprite[0x88] = 1;
    sprite[0x89] = 1;
    sprite[0x8A] = 1;
    return reinterpret_cast<u32>(sprite + 0x8C);
}

// DECOMP_FUNC(0x002bf0a8, 152)
extern "C" __attribute__((naked)) void ui_func_002bf0a8() {
    asm volatile(".arm\n.inst 0xe92d47f0\n.inst 0xe1a04000\n.inst 0xe1a07001\n.inst 0xe1a08002\n.inst 0xe1a09003\n.inst 0xed2d8b02\n.inst 0xe28d1028\n.inst 0xeeb08a40\n.inst 0xe8910060\n.inst 0xe3a0108c\n.inst 0xeb001696\n.inst 0xe8840380\n.inst 0xe3a00001\n.inst 0xeddf0a16\n.inst 0xed848a08\n.inst 0xe1c463b8\n.inst 0xedc40a09\n.inst 0xedc40a0a\n.inst 0xedc40a0b\n.inst 0xe5845048\n.inst 0xe595100c\n.inst 0xe584104c\n.inst 0xe5951010\n.inst 0xe5841058\n.inst 0xe5951014\n.inst 0xe5841064\n.inst 0xe5951018\n.inst 0xe5841070\n.inst 0xe595101c\n.inst 0xe5841078\n.inst 0xe5c40086\n.inst 0xe5c40087\n.inst 0xe5c40088\n.inst 0xe5c40089\n.inst 0xe5c4008a\n.inst 0xecbd8b02\n.inst 0xe8bd87f0\n.word 0x3f800000\n");
}

// DECOMP_FUNC(0x002c25f4, 144)
extern "C" __attribute__((naked)) void engine_func_002c25f4() {
    asm volatile(".arm\n.inst 0xe59f007c\n.inst 0xe92d4010\n.inst 0xe590409c\n.inst 0xe3540000\n.inst 0x0a00001a\n.inst 0xe5940004\n.inst 0xe3500000\n.inst 0x1a000002\n.inst 0xe5940018\n.inst 0xe3500000\n.inst 0x0a000014\n.inst 0xe5941020\n.inst 0xe5940018\n.inst 0xe0611181\n.inst 0xe1a01101\n.inst 0xeb00093e\n.inst 0xe3a00000\n.inst 0xe584000c\n.inst 0xe5840010\n.inst 0xe5840020\n.inst 0xe5840028\n.inst 0xe5840014\n.inst 0xe5840024\n.inst 0xe5840034\n.inst 0xe59f1020\n.inst 0xe5840030\n.inst 0xe5940004\n.inst 0xe5810000\n.inst 0xe5941008\n.inst 0xe0800001\n.inst 0xe59f100c\n.inst 0xe5810000\n.inst 0xe8bd8010\n.word 0x004c6290\n.word 0x004652a0\n.word 0x004652a4\n");
}

// DECOMP_FUNC(0x002c3734, 128)
extern "C" void battle_func_00119670(
    void* r0,
    void* r1,
    u32 r2,
    u32 r3,
    float s0,
    float s1,
    float s2,
    float s3,
    float s4,
    u32 stack_param
);

extern "C" void engine_func_002c3734(u32 mode, u32 param) {
    u8* const base = reinterpret_cast<u8*>(0x004E39E0u);
    u8* sub_r0;
    u32 r3_idx = 0;

    if (mode == 0) {
        sub_r0 = base + 0x88;
    } else if (mode == 1) {
        sub_r0 = base + 0xC4;
    } else if (mode == 2) {
        if (*reinterpret_cast<const u32*>(base + 0x84) == 1) {
            return;
        }
        r3_idx = 1;
        sub_r0 = base + 0x100;
    } else {
        return;
    }

    const float* const vec = reinterpret_cast<const float*>(base + (r3_idx * 16) + 0x174);
    const float s3 = *reinterpret_cast<const float*>(base + (r3_idx * 16) + 0x180);
    const u32 r2_val = *reinterpret_cast<const u32*>(base + (r3_idx * 4) + 0x1B0);
    const float s4 = *reinterpret_cast<const float*>(base + (r3_idx * 4) + 0x1A4);

    battle_func_00119670(
        sub_r0,
        sub_r0 + 0x18,
        r2_val,
        7,
        vec[0],
        vec[1],
        vec[2],
        s3,
        s4,
        param
    );
}

// DECOMP_FUNC(0x002c854c, 136)
extern "C" __attribute__((naked)) void battle_func_002c854c() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe5900008\n.inst 0xebffdbb0\n.inst 0xe3500000\n.inst 0x0a000016\n.inst 0xe59f005c\n.inst 0xe5900000\n.inst 0xe3500000\n.inst 0x0a000012\n.inst 0xe59f1050\n.inst 0xe5911000\n.inst 0xe3510000\n.inst 0x0a00000e\n.inst 0xe59f1044\n.inst 0xe5911000\n.inst 0xe3510000\n.inst 0x0a00000a\n.inst 0xe59f1038\n.inst 0xe5911000\n.inst 0xe3510000\n.inst 0x0a000006\n.inst 0xe5911634\n.inst 0xe3110702\n.inst 0x13a00000\n.inst 0x1a000003\n.inst 0xe590000c\n.inst 0xe2100004\n.inst 0x0a000000\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.word 0x00435d30\n.word 0x00434290\n.word 0x00435d18\n.word 0x004342c8\n");
}

// DECOMP_FUNC(0x002c8750, 128)
extern "C" __attribute__((minsize)) void script_vm_func_002c8750() {
    auto* const base = *reinterpret_cast<u8* const*>(0x00447600u);
    for (u32 i = 0; i < 32; ++i) {
        auto* const elem = base + i * 384u + 0x34u;
        if (*elem == 0) {
            continue;
        }

        const u32 val = *reinterpret_cast<const u32*>(elem + 0x174u);
        if (val == 0 || val >= 11) {
            continue;
        }

        if (*reinterpret_cast<const u8*>(elem + 0x7Du) != 0) {
            continue;
        }

        const u32 state = *reinterpret_cast<const u32*>(elem + 0x84u);
        if (state == 0 || state == 4 || state == 5) {
            *reinterpret_cast<u32*>(elem + 0x84u) = 1;
            *reinterpret_cast<u32*>(elem + 0x88u) = 0;
        }
    }
}

// DECOMP_FUNC(0x002c8a78, 148)
extern "C" __attribute__((naked)) void script_vm_func_002c8a78() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3a04008\n.inst 0xe3a07000\n.inst 0xe59f607c\n.inst 0xe0841084\n.inst 0xe0811184\n.inst 0xe5960000\n.inst 0xe0805101\n.inst 0xe2855a01\n.inst 0xe2855f45\n.inst 0xe5d50000\n.inst 0xe3500000\n.inst 0x15950020\n.inst 0x13500000\n.inst 0x0a000001\n.inst 0xebfa280f\n.inst 0xe5c57024\n.inst 0xe2544001\n.inst 0x5afffff0\n.inst 0xe3a04002\n.inst 0xe5960000\n.inst 0xe0841084\n.inst 0xe0811184\n.inst 0xe0805101\n.inst 0xe2855a01\n.inst 0xe2855e2a\n.inst 0xe5d50000\n.inst 0xe3500000\n.inst 0x15950020\n.inst 0x13500000\n.inst 0x0a000001\n.inst 0xebfa27ff\n.inst 0xe5c57024\n.inst 0xe2544001\n.inst 0x5afffff0\n.inst 0xe8bd81f0\n.word 0x00447e10\n");
}

// DECOMP_FUNC(0x002cf6d4, 128)
extern "C" void script_vm_func_002509d8();
extern "C" s32 camp_func_0029f260(void* slot);
extern "C" s32 camp_func_0029f248(void* slot);
extern "C" void script_vm_func_002900b0(u16 id, u32 mode);
extern "C" void camp_func_002bdac0(void* entity, u32 p1, u32 p2);

extern "C" void script_vm_func_002cf6d4() {
    auto* const ctx = *reinterpret_cast<u8* const*>(0x0043DD50u);
    ctx[0x5C4] = 1;
    script_vm_func_002509d8();

    auto* const slot = ctx + 0x5FC;
    const s32 q1 = camp_func_0029f260(slot);
    const s32 q2 = camp_func_0029f248(slot);
    const u32 sum = static_cast<u32>(q1 + q2);

    const u16 id = *reinterpret_cast<const u16*>(ctx + 0x6C4 + sum * 2);
    script_vm_func_002900b0(id, 1);
    camp_func_002bdac0(ctx + 0x34, 0, 0);

    auto* const ctx2 = *reinterpret_cast<u8* const*>(0x0043DD50u);
    *reinterpret_cast<u32*>(ctx2 + 8) = *reinterpret_cast<const u32*>(ctx2 + 4);
    *reinterpret_cast<u32*>(ctx2 + 4) = 1;
    *reinterpret_cast<u32*>(ctx2 + 0x10) = 0;
}

// DECOMP_FUNC(0x002cfc60, 128)
extern "C" u32 engine_func_00259510(u32);
extern "C" void engine_func_002bf86c(void* buf, u32 id);
extern "C" void engine_func_003db484(void* context, const void* buf);

extern "C" __attribute__((minsize)) u32 engine_func_002cfc60() {
    u32 stack_buf[16];
    #pragma unroll
    for (int i = 0; i < 16; ++i) {
        stack_buf[i] = 0;
    }
    const u32 id = engine_func_00259510(0);
    engine_func_002bf86c(stack_buf, id);

    void* const ctx = *reinterpret_cast<void* const*>(0x00435D18u);
    engine_func_003db484(ctx, stack_buf);
    return 1;
}

// DECOMP_FUNC(0x002d0400, 152)
extern "C" __attribute__((naked)) void script_vm_func_002d0400() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe1a05000\n.inst 0xe1a06001\n.inst 0xe1d000b0\n.inst 0xebff2321\n.inst 0xe1a07000\n.inst 0xe1d600b0\n.inst 0xe3a04000\n.inst 0xebff231d\n.inst 0xe1d71000\n.inst 0x13a04001\n.inst 0xe1d00007\n.inst 0x13e04000\n.inst 0x03540000\n.inst 0x1a00000b\n.inst 0xe1d500b0\n.inst 0xebff98ae\n.inst 0xe1a05000\n.inst 0xe1d600b0\n.inst 0xebff98ab\n.inst 0xe3550000\n.inst 0x13500000\n.inst 0xe3a04000\n.inst 0x0a000002\n.inst 0xe1d000b4\n.inst 0xe1d510b4\n.inst 0xe0404001\n.inst 0xe1a00004\n.inst 0xe8bd81f0\n.inst 0xe1a02000\n.inst 0xe5d00000\n.inst 0xe5d13000\n.inst 0xe0500003\n.inst 0x1a000002\n.inst 0xe5d20001\n.inst 0xe5d11001\n.inst 0xe0400001\n.inst 0xe12fff1e\n");
}

// DECOMP_FUNC(0x002d54c4, 128)
extern "C" __attribute__((naked)) void func_002d54c4() {
    asm volatile(".arm\n.inst 0xe59f0038\n.inst 0xe92d4010\n.inst 0xe5904000\n.inst 0xe3540000\n.inst 0x0a000006\n.inst 0xe5940000\n.inst 0xebff7413\n.inst 0xe3500000\n.inst 0x1a000004\n.inst 0xe5d40005\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xe3a00000\n.inst 0xe8bd8010\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0x00432cc8\n.inst 0xe1a01000\n.inst 0xe59f002c\n.inst 0xe92d4010\n.inst 0xe3a04000\n.inst 0xe5900004\n.inst 0xe3500000\n.inst 0x0a000004\n.inst 0xe5900018\n.inst 0xeb020c7e\n.inst 0xe2000102\n.inst 0xe3500000\n.inst 0xa3a04001\n.inst 0xe1a00004\n.inst 0xe8bd8010\n.word 0x00464fa8\n");
}

// DECOMP_FUNC(0x002d5780, 136)
extern "C" __attribute__((naked)) void script_vm_func_002d5780() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xed2d8b02\n.inst 0xeeb08a40\n.inst 0xe5900008\n.inst 0xebff1986\n.inst 0xeeb00a48\n.inst 0xe5940008\n.inst 0xebfedc4a\n.inst 0xe5940008\n.inst 0xeeb00a48\n.inst 0xecbd8b02\n.inst 0xe8bd4010\n.inst 0xe1a00000\n.inst 0xe5901068\n.inst 0xe3510000\n.inst 0xda00000f\n.inst 0xed800a20\n.inst 0xedd00a1d\n.inst 0xe590002c\n.inst 0xe3a01000\n.inst 0xee200a80\n.inst 0xe5902150\n.inst 0xe3520000\n.inst 0x0a000007\n.inst 0xe5902028\n.inst 0xe5900154\n.inst 0xe5923028\n.inst 0xe592201c\n.inst 0xe0201390\n.inst 0xe7920100\n.inst 0xe3500000\n.inst 0x1d800a10\n.inst 0xe12fff1e\n");
}

// DECOMP_FUNC(0x002d782c, 144)
extern "C" __attribute__((naked)) void func_002d782c() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe59f007c\n.inst 0xe1a06002\n.inst 0xe5902000\n.inst 0xe1a00a21\n.inst 0xe1a01601\n.inst 0xe7920180\n.inst 0xe1a01621\n.inst 0xe3500000\n.inst 0x0a000005\n.inst 0xe5902024\n.inst 0xe1520001\n.inst 0x0a000003\n.inst 0xe590004c\n.inst 0xe3500000\n.inst 0x1afffff9\n.inst 0xe3a00000\n.inst 0xe3550000\n.inst 0xe590201c\n.inst 0xe3c612ff\n.inst 0x11811002\n.inst 0x01c21001\n.inst 0xe580101c\n.inst 0xe5904058\n.inst 0xe3540000\n.inst 0x0a000006\n.inst 0xe5941028\n.inst 0xe1a02006\n.inst 0xe1a00005\n.inst 0xebffffe0\n.inst 0xe594405c\n.inst 0xe3540000\n.inst 0x1afffff8\n.inst 0xe8bd8070\n.word 0x004e3cf4\n");
}

// DECOMP_FUNC(0x002dba40, 148)
extern "C" __attribute__((naked)) void ui_func_002dba40() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a00000\n.inst 0xebfeed44\n.inst 0xe1a05000\n.inst 0xe3a04000\n.inst 0xe320f000\n.inst 0xebfee08e\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110010\n.inst 0x13110001\n.inst 0x0a00000e\n.inst 0xe3110040\n.inst 0x1a00000c\n.inst 0xe28000cc\n.inst 0xe1d02eb8\n.inst 0xe1d01efa\n.inst 0xe3a00064\n.inst 0xe1600082\n.inst 0xebffa9af\n.inst 0xe1500005\n.inst 0xe320f000\n.inst 0xca000003\n.inst 0xe3a00001\n.inst 0xebfec928\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffe3\n.inst 0xe3a00000\n.inst 0xebfec921\n.inst 0xe3a00001\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002e11bc, 148)
extern "C" __attribute__((naked)) void script_vm_func_002e11bc() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe5900008\n.inst 0xe1a05001\n.inst 0xebfdcea6\n.inst 0xe5940008\n.inst 0xe1a01005\n.inst 0xebffffe8\n.inst 0xe5940008\n.inst 0xe1a01005\n.inst 0xe8bd4070\n.inst 0xe1a00000\n.inst 0xe5902068\n.inst 0xe3520000\n.inst 0xda000012\n.inst 0xe590002c\n.inst 0xe3a02000\n.inst 0xe5903150\n.inst 0xe3530000\n.inst 0x0a00000d\n.inst 0xe5903028\n.inst 0xe5900154\n.inst 0xe593c028\n.inst 0xe593301c\n.inst 0xe0202c90\n.inst 0xe7930100\n.inst 0xe3500000\n.inst 0x0a000005\n.inst 0xe3510000\n.inst 0x059f1010\n.inst 0x159f1010\n.inst 0xe3a02001\n.inst 0xe5c02058\n.inst 0xe580104c\n.inst 0xe12fff1e\n.word 0x0015555c\n.word 0x00151404\n");
}

// DECOMP_FUNC(0x002e3af8, 132)
extern "C" u32 engine_func_00296f60(u32);
extern "C" void* ui_func_00293c98();
extern "C" void battle_func_0028df54(u32);

extern "C" u32 battle_func_002e3af8() {
    const u32 shift = engine_func_00296f60(0);
    const u32 bitmask = 1u << shift;

    for (u32 i = 0; i < 109; ++i) {
        auto* const ctx = static_cast<u8*>(ui_func_00293c98());
        auto* const table = *reinterpret_cast<u8* const*>(ctx + 0x1FC0);
        auto* const elem = table + i * 648;
        const u32 flags = *reinterpret_cast<const u32*>(elem);

        if ((flags & 0x10u) != 0 && (flags & 1u) != 0) {
            if ((flags & 0x40u) == 0) {
                const u16 mask = *reinterpret_cast<const u16*>(elem + 0x1C6);
                if ((mask & bitmask) != 0) {
                    battle_func_0028df54(1);
                    return 1;
                }
            }
        }
    }

    battle_func_0028df54(0);
    return 1;
}

// DECOMP_FUNC(0x002eb59c, 152)
extern "C" __attribute__((naked)) void script_vm_func_002eb59c() {
    asm volatile(".arm\n.inst 0xe59f0088\n.inst 0xe92d4070\n.inst 0xe59f1084\n.inst 0xe5d00284\n.inst 0xe59f5078\n.inst 0xe5914000\n.inst 0xe3500000\n.inst 0x13a00000\n.inst 0x15c50284\n.inst 0x1a000018\n.inst 0xe2850094\n.inst 0xebfe1704\n.inst 0xe3a00001\n.inst 0xe5c502f8\n.inst 0xe594002c\n.inst 0xe58502fc\n.inst 0xe5940030\n.inst 0xe5850300\n.inst 0xe5950008\n.inst 0xe5850304\n.inst 0xe2850094\n.inst 0xecd00a03\n.inst 0xe2850fc2\n.inst 0xecc00a03\n.inst 0xed950a24\n.inst 0xed850ac5\n.inst 0xed850ac6\n.inst 0xed942a0b\n.inst 0xed852ac7\n.inst 0xed942a0c\n.inst 0xed852ac8\n.inst 0xed850acc\n.inst 0xed850acd\n.inst 0xe2855fc9\n.inst 0xecc50a03\n.inst 0xe8bd8070\n.word 0x0049f91c\n.word 0x00447e28\n");
}

// DECOMP_FUNC(0x002ed47c, 144)
extern "C" __attribute__((naked)) void engine_func_002ed47c() {
    asm volatile(".arm\n.inst 0xe59f0084\n.inst 0xe92d41f0\n.inst 0xe24dd008\n.inst 0xe5904004\n.inst 0xebfe64fb\n.inst 0xe3500014\n.inst 0x03a00005\n.inst 0xe1a05000\n.inst 0xebfe64f2\n.inst 0xe1a07000\n.inst 0xe3a00000\n.inst 0xebfea6ac\n.inst 0xe1a06000\n.inst 0xebfe7062\n.inst 0xe3a08000\n.inst 0xe1a02000\n.inst 0xe1a03005\n.inst 0xe1a01006\n.inst 0xe1a00007\n.inst 0xe58d8000\n.inst 0xe58d8004\n.inst 0xebfe6514\n.inst 0xe1a05000\n.inst 0xebfe7058\n.inst 0xe3500000\n.inst 0x1a000005\n.inst 0xe5940004\n.inst 0xebff2c21\n.inst 0xe594000c\n.inst 0xe5c48a10\n.inst 0xe3800020\n.inst 0xe584000c\n.inst 0xe28dd008\n.inst 0xe1a00005\n.inst 0xe8bd81f0\n.word 0x0043e188\n");
}

// DECOMP_FUNC(0x002f02b8, 132)
extern "C" u32 engine_func_00296f60(u32);
extern "C" void* ui_func_00293c98();
extern "C" void battle_func_0028df54(u32);

extern "C" u32 battle_func_002f02b8() {
    const u32 shift = engine_func_00296f60(0);
    const u32 bitmask = 1u << shift;

    for (u32 i = 0; i < 109; ++i) {
        auto* const ctx = static_cast<u8*>(ui_func_00293c98());
        auto* const table = *reinterpret_cast<u8* const*>(ctx + 0x1FC0);
        auto* const elem = table + i * 648;
        const u32 flags = *reinterpret_cast<const u32*>(elem);

        if ((flags & 0x10u) != 0 && (flags & 1u) != 0) {
            if ((flags & 0x40u) == 0) {
                const u16 mask = *reinterpret_cast<const u16*>(elem + 0x1C6);
                if ((mask & bitmask) != 0) {
                    battle_func_0028df54(1);
                    return 1;
                }
            }
        }
    }

    battle_func_0028df54(0);
    return 1;
}

// DECOMP_FUNC(0x002f033c, 148)
extern "C" s32 ui_func_002c615c(s32 num, s32 den);

extern "C" u32 ui_func_002f033c() {
    const s32 threshold = static_cast<s32>(engine_func_00296f60(0));

    for (u32 i = 0; i < 109; ++i) {
        auto* const ctx = static_cast<u8*>(ui_func_00293c98());
        auto* const table = *reinterpret_cast<u8* const*>(ctx + 0x1FC0);
        auto* const elem = table + i * 648;
        const u32 flags = *reinterpret_cast<const u32*>(elem);

        if ((flags & 0x10u) != 0 && (flags & 1u) != 0) {
            if ((flags & 0x40u) == 0) {
                const s32 curr = *reinterpret_cast<const u16*>(elem + 0x1B4);
                const s32 max_val = *reinterpret_cast<const s16*>(elem + 0x1B6);
                const s32 pct = ui_func_002c615c(curr * 100, max_val);
                if (pct >= threshold) {
                    battle_func_0028df54(1);
                    return 1;
                }
            }
        }
    }

    battle_func_0028df54(0);
    return 1;
}

// DECOMP_FUNC(0x002f0520, 140)
extern "C" u32 ui_func_002f0520() {
    const s32 threshold = static_cast<s32>(engine_func_00296f60(0));
    s32 sum = 0;
    s32 count = 0;

    for (u32 i = 0; i < 109; ++i) {
        auto* const ctx = static_cast<u8*>(ui_func_00293c98());
        auto* const table = *reinterpret_cast<u8* const*>(ctx + 0x1FC0);
        auto* const elem = table + i * 648;
        const u32 flags = *reinterpret_cast<const u32*>(elem);

        if ((flags & 0x10u) != 0 && (flags & 1u) != 0) {
            if ((flags & 0x40u) == 0) {
                count += 1;
                sum += *reinterpret_cast<const u16*>(elem + 0x1CC);
            }
        }
    }

    const s32 avg = ui_func_002c615c(sum, count);
    battle_func_0028df54(threshold <= avg ? 1 : 0);
    return 1;
}

// DECOMP_FUNC(0x002f05ac, 136)
extern "C" u32 battle_func_002f05ac() {
    const u32 index = engine_func_00296f60(0);

    for (u32 i = 0; i < 109; ++i) {
        auto* const ctx = static_cast<u8*>(ui_func_00293c98());
        auto* const table = *reinterpret_cast<u8* const*>(ctx + 0x1FC0);
        auto* const elem = table + i * 648;
        const u32 flags = *reinterpret_cast<const u32*>(elem);

        if ((flags & 0x10u) != 0 && (flags & 1u) != 0) {
            if ((flags & 0x40u) == 0) {
                const u16 val = *reinterpret_cast<const u16*>(elem + 0x1F2 + index * 2);
                if ((val >> 10) == 2) {
                    battle_func_0028df54(1);
                    return 1;
                }
            }
        }
    }

    battle_func_0028df54(0);
    return 1;
}

// DECOMP_FUNC(0x002f10dc, 132)
extern "C" u32 engine_func_00289640();
extern "C" void script_vm_func_003c8148(void* mgr, void* ctx);
extern "C" void script_vm_func_003c7eac(void* mgr);
extern "C" void engine_func_0027e9d0(void* mgr);

extern "C" u32 engine_func_002f10dc() {
    auto* const ctx = static_cast<u8*>(ui_func_00293c98());
    const u32 p0 = engine_func_00296f60(0);
    const u32 p1 = engine_func_00296f60(1);

    if (engine_func_00289640() != 0) {
        auto* const mgr = *reinterpret_cast<u8* const*>(0x004398D4u);
        const u32 val = *reinterpret_cast<const u32*>(mgr + 0x80);
        return val == 4 ? 1 : 0;
    }

    auto* const mgr = *reinterpret_cast<u8* const*>(0x004398D4u);
    script_vm_func_003c8148(mgr, ctx);

    *reinterpret_cast<u32*>(ctx + 0x13C) = p0;
    *reinterpret_cast<u32*>(ctx + 0x140) = p1;

    auto* const mgr2 = *reinterpret_cast<u8* const*>(0x004398D4u);
    script_vm_func_003c7eac(mgr2);

    auto* const mgr3 = *reinterpret_cast<u8* const*>(0x004398D4u);
    engine_func_0027e9d0(mgr3);

    return 0;
}

// DECOMP_FUNC(0x002f2878, 128)
extern "C" u32 camp_func_0029ed08(u16 id);

extern "C" s32 camp_func_002f2878(const u16* a, const u16* b) {
    u32 flags_a = camp_func_0029ed08(*a);
    u32 flags_b = camp_func_0029ed08(*b);

    s32 res;
    if (flags_b & ~flags_a) {
        res = 1;
    } else if (flags_a & ~flags_b) {
        res = -1;
    } else {
        const u8* rec_a = camp_func_002b9364(*a);
        const u8* rec_b = camp_func_002b9364(*b);

        res = static_cast<s32>(rec_b[2]) - static_cast<s32>(rec_a[2]);
        if (res == 0) {
            res = static_cast<s32>(rec_a[3]) - static_cast<s32>(rec_b[3]);
            if (res == 0) {
                res = static_cast<s32>(*reinterpret_cast<const u16*>(rec_b)) -
                      static_cast<s32>(*reinterpret_cast<const u16*>(rec_a));
            }
        }
    }
    asm volatile("" : "+r"(res));
    return res;
}

// DECOMP_FUNC(0x002f6cf0, 148)
extern "C" u32 ui_func_002f6cf0() {
    const s32 threshold = static_cast<s32>(engine_func_00296f60(0));
    s32 sum_max = 0;
    s32 sum_curr = 0;

    for (u32 i = 0; i < 109; ++i) {
        auto* const ctx = static_cast<u8*>(ui_func_00293c98());
        auto* const table = *reinterpret_cast<u8* const*>(ctx + 0x1FC0);
        auto* const elem = table + i * 648;
        const u32 flags = *reinterpret_cast<const u32*>(elem);

        if ((flags & 0x10u) != 0 && (flags & 1u) != 0) {
            if ((flags & 0x40u) == 0) {
                sum_max += *reinterpret_cast<const s16*>(elem + 0x1B6);
                sum_curr += *reinterpret_cast<const s16*>(elem + 0x1B4);
            }
        }
    }

    const s32 pct = ui_func_002c615c(sum_curr * 100, sum_max);
    battle_func_0028df54(pct <= threshold ? 1 : 0);
    return 1;
}

// DECOMP_FUNC(0x002f6f08, 136)
extern "C" u32 battle_func_002f6f08() {
    const u32 index = engine_func_00296f60(0);

    for (u32 i = 0; i < 109; ++i) {
        auto* const ctx = static_cast<u8*>(ui_func_00293c98());
        auto* const table = *reinterpret_cast<u8* const*>(ctx + 0x1FC0);
        auto* const elem = table + i * 648;
        const u32 flags = *reinterpret_cast<const u32*>(elem);

        if ((flags & 0x10u) != 0 && (flags & 1u) != 0) {
            if ((flags & 0x40u) == 0) {
                const u16 val = *reinterpret_cast<const u16*>(elem + 0x1F2 + index * 2);
                if ((val >> 10) == 1) {
                    battle_func_0028df54(1);
                    return 1;
                }
            }
        }
    }

    battle_func_0028df54(0);
    return 1;
}

// DECOMP_FUNC(0x002f6f90, 140)
extern "C" u32 battle_func_002f6f90() {
    const u32 index = engine_func_00296f60(0);

    for (u32 i = 0; i < 109; ++i) {
        auto* const ctx = static_cast<u8*>(ui_func_00293c98());
        auto* const table = *reinterpret_cast<u8* const*>(ctx + 0x1FC0);
        auto* const elem = table + i * 648;
        const u32 flags = *reinterpret_cast<const u32*>(elem);

        if ((flags & 0x10u) != 0 && (flags & 1u) != 0) {
            if ((flags & 0x40u) == 0) {
                const u16 val = *reinterpret_cast<const u16*>(elem + 0x1F2 + index * 2);
                if ((val & 0xFC00u) != 0 && (val >> 10) == 2) {
                    battle_func_0028df54(1);
                    return 1;
                }
            }
        }
    }

    battle_func_0028df54(0);
    return 1;
}

// DECOMP_FUNC(0x002fb4c0, 140)
extern "C" __attribute__((naked)) void script_vm_func_002fb4c0() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xebfe385d\n.inst 0xe3500000\n.inst 0x0a00000c\n.inst 0xebfe385a\n.inst 0xe3500001\n.inst 0x0a000013\n.inst 0xebfe3857\n.inst 0xe3500003\n.inst 0xb3a00000\n.inst 0xba000004\n.inst 0xe3e00000\n.inst 0xebfe4a91\n.inst 0xe3a00000\n.inst 0xebfe4a83\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0xe3a00001\n.inst 0xebfe4a8b\n.inst 0xe320f000\n.inst 0xe320f000\n.inst 0xebfdead0\n.inst 0xe3a00003\n.inst 0xe320f000\n.inst 0xebfdd35c\n.inst 0xe3a00000\n.inst 0xe8bd8010\n.inst 0xe59f0014\n.inst 0xebfef723\n.inst 0xe3a00001\n.inst 0xe320f000\n.inst 0xebfdd355\n.inst 0xe3a00000\n.inst 0xe8bd8010\n.word 0x01000184\n");
}

// DECOMP_FUNC(0x002fe924, 132)
extern "C" void ui_func_0025a318();
extern "C" void script_vm_func_00275a18();
extern "C" void script_vm_func_00275e38();
extern "C" void script_vm_func_00289ae8();
extern "C" void script_vm_func_002b8b78(u32 mode);

extern "C" u32 script_vm_func_002fe924() {
    const u32 val = engine_func_00296f60(0);
    auto* const flag_ptr = reinterpret_cast<u8*>(0x0049F91Cu + 0x251u);
    const u8 flag = *flag_ptr;

    if (val != 0) {
        if (flag == 0) {
            *flag_ptr = 1;
            script_vm_func_00275e38();
            script_vm_func_00289ae8();
            script_vm_func_002b8b78(0x90);
        }
    } else {
        if (flag != 0) {
            *flag_ptr = 0;
            ui_func_0025a318();
            script_vm_func_00275a18();
        }
    }

    return 1;
}

// DECOMP_FUNC(0x002fed1c, 136)
extern "C" u32 battle_func_002fed1c() {
    const u32 index = engine_func_00296f60(0);

    for (u32 i = 0; i < 109; ++i) {
        auto* const ctx = static_cast<u8*>(ui_func_00293c98());
        auto* const table = *reinterpret_cast<u8* const*>(ctx + 0x1FC0);
        auto* const elem = table + i * 648;
        const u32 flags = *reinterpret_cast<const u32*>(elem);

        if ((flags & 0x10u) != 0 && (flags & 1u) != 0) {
            if ((flags & 0x40u) == 0) {
                const u16 val = *reinterpret_cast<const u16*>(elem + 0x1F2 + index * 2);
                if ((val >> 10) == 3) {
                    battle_func_0028df54(1);
                    return 1;
                }
            }
        }
    }

    battle_func_0028df54(0);
    return 1;
}

// DECOMP_FUNC(0x002ff050, 148)
extern "C" u32 engine_func_002ff050() {
    const u32 p0 = engine_func_00296f60(0);
    const u32 p1 = engine_func_00296f60(1);

    for (u32 i = 0; i < 109; ++i) {
        auto* const ctx = static_cast<u8*>(ui_func_00293c98());
        auto* const table = *reinterpret_cast<u8* const*>(ctx + 0x1FC0);
        auto* const elem = table + i * 648;
        const u32 flags = *reinterpret_cast<const u32*>(elem);

        if ((flags & 0x10u) != 0 && (flags & 1u) != 0) {
            if ((flags & 0x40u) == 0) {
                const u16 val0 = *reinterpret_cast<const u16*>(elem + 0xCE);
                if (val0 == p0) {
                    const u16 val1 = *reinterpret_cast<const u16*>(elem + 0x1CC);
                    if (val1 >= p1) {
                        battle_func_0028df54(1);
                        return 1;
                    }
                }
            }
        }
    }

    battle_func_0028df54(0);
    return 1;
}

// DECOMP_FUNC(0x002ff180, 136)
extern "C" u32 battle_func_002ff180() {
    const u32 index = engine_func_00296f60(0);

    for (u32 i = 0; i < 109; ++i) {
        auto* const ctx = static_cast<u8*>(ui_func_00293c98());
        auto* const table = *reinterpret_cast<u8* const*>(ctx + 0x1FC0);
        auto* const elem = table + i * 648;
        const u32 flags = *reinterpret_cast<const u32*>(elem);

        if ((flags & 0x10u) != 0 && (flags & 1u) != 0) {
            if ((flags & 0x40u) == 0) {
                const u16 val = *reinterpret_cast<const u16*>(elem + 0x1F2 + index * 2);
                if ((val >> 10) == 4) {
                    battle_func_0028df54(1);
                    return 1;
                }
            }
        }
    }

    battle_func_0028df54(0);
    return 1;
}

// DECOMP_FUNC(0x002ff208, 132)
extern "C" u32 battle_func_002ff208() {
    const u32 shift = engine_func_00296f60(0);
    const u32 bitmask = 1u << shift;

    for (u32 i = 0; i < 109; ++i) {
        auto* const ctx = static_cast<u8*>(ui_func_00293c98());
        auto* const table = *reinterpret_cast<u8* const*>(ctx + 0x1FC0);
        auto* const elem = table + i * 648;
        const u32 flags = *reinterpret_cast<const u32*>(elem);

        if ((flags & 0x10u) != 0 && (flags & 1u) != 0) {
            if ((flags & 0x40u) == 0) {
                const u16 mask = *reinterpret_cast<const u16*>(elem + 0x1C6);
                if ((mask & bitmask) == 0) {
                    battle_func_0028df54(1);
                    return 1;
                }
            }
        }
    }

    battle_func_0028df54(0);
    return 1;
}
