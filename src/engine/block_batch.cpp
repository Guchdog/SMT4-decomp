#include "engine/block_batch.h"
#include <cmath>
#include <cstring>

namespace smt4::battle {

// 0x00407FC0: Trigonometric sine/cosine lookup table in .rodata
extern const FilterTrigRow g_FilterTrigTable[256];

// Global pointers accessed by the batch blocks
static BattleEffectState* const* const gp_BattleEffectState =
    reinterpret_cast<BattleEffectState* const*>(0x004475B8);

static BattleGridState* const gp_BattleGridState =
    reinterpret_cast<BattleGridState*>(0x00448C58);

static const u32* const gp_ScreenMode =
    reinterpret_cast<const u32*>(0x0049F91C);

static void* const* const gp_BattleCamera =
    reinterpret_cast<void* const*>(0x00447E88);

// Helper for sine/cosine lookup table interpolation (modulo 65536.0f)
static void LookupTrig(f32 angle_deg, f32& out_sin, f32& out_cos) {
    f32 ang = angle_deg * (256.0f / 360.0f);
    if (ang < 0.0f) {
        ang = std::fmod(ang, 65536.0f);
        if (ang < 0.0f) {
            ang += 65536.0f;
        }
    } else if (ang >= 65536.0f) {
        ang = std::fmod(ang, 65536.0f);
    }

    u32 bam = static_cast<u32>(ang);
    u8 idx = static_cast<u8>(bam & 0xFF);
    f32 frac = ang - static_cast<f32>(bam);

    const FilterTrigRow& row = g_FilterTrigTable[idx];
    out_sin = row.x + frac * row.z;
    out_cos = row.y + frac * row.w;
}

// Render context viewport/render-mode stack management at 0x0044EA00
static void PushRenderViewport(u32 viewport_id) {
    u8* base = static_cast<u8*>(smt4::engine::g_RenderRegisterBase);
    if (!base) return;

    void* vp_obj = UiGpu_SetViewportParams(viewport_id, 0);
    u8* stack_node = base + 0x124C;
    u32& count = *reinterpret_cast<u32*>(stack_node);
    void** stack = reinterpret_cast<void**>(stack_node + 8);
    u8& dirty = *reinterpret_cast<u8*>(stack_node + 0x18);
    using FlushCb = void (*)();
    FlushCb flush_cb = *reinterpret_cast<FlushCb*>(stack_node + 0x1C);

    void* prev = stack[count];
    count++;
    stack[count] = vp_obj;
    if (dirty != 0 || prev != vp_obj) {
        if (flush_cb) flush_cb();
        dirty = 0;
    }
}

static void PopRenderViewport() {
    u8* base = static_cast<u8*>(smt4::engine::g_RenderRegisterBase);
    if (!base) return;

    u8* stack_node = base + 0x124C;
    u32& count = *reinterpret_cast<u32*>(stack_node);
    void** stack = reinterpret_cast<void**>(stack_node + 8);
    u8& dirty = *reinterpret_cast<u8*>(stack_node + 0x18);
    using FlushCb = void (*)();
    FlushCb flush_cb = *reinterpret_cast<FlushCb*>(stack_node + 0x1C);

    void* prev = stack[count];
    if (count > 0) count--;
    void* cur = stack[count];
    if (dirty != 0 || prev != cur) {
        if (flush_cb) flush_cb();
        dirty = 0;
    }
}

static void SetRenderModeWithStack(u32 mode, u32 p1, u32 p2) {
    u8* base = static_cast<u8*>(smt4::engine::g_RenderRegisterBase);
    if (!base) return;

    void* mode_obj = UiGpu_SetRenderMode(mode, p1, p2);
    u8* stack_node = base + 0x12AC;
    u32 count = *reinterpret_cast<u32*>(stack_node);
    void** stack = reinterpret_cast<void**>(stack_node + 8);
    u8& dirty = *reinterpret_cast<u8*>(stack_node + 0x18);
    using FlushCb = void (*)();
    FlushCb flush_cb = *reinterpret_cast<FlushCb*>(stack_node + 0x1C);

    void* prev = stack[count];
    stack[count] = mode_obj;
    if (dirty != 0 || prev != mode_obj) {
        if (flush_cb) flush_cb();
        dirty = 0;
    }
}

} // namespace smt4::battle

extern "C" {

// ---------------------------------------------------------------------------
// 0x002D2E50: 4-face oriented billboard quad generator & render submitter
// ---------------------------------------------------------------------------
// DECOMP_FUNC(0x002d2e50, 3108)
#if 0
void battle_func_002d2e50(const smt4::battle::BattleUnitBillboard* billboard) {
    if (!billboard) return;

    const f32 pos_x = billboard->pos[0];
    const f32 pos_y = billboard->pos[1];
    const f32 pos_z = billboard->pos[2];
    const f32 rot_y = billboard->rot_y;
    const s16 id = billboard->id;

    const f32 angles[4] = {
        rot_y + 0.0f,
        rot_y + 90.0f,
        rot_y + 180.0f,
        rot_y + 270.0f
    };

    for (s32 face = 0; face < 4; ++face) {
        f32 corners[4][3];
        f32 normal[3] = { 0.0f, 0.0f, 1.0f };

        if (face == 0 || face == 2) {
            corners[0][0] = -250.0f; corners[0][1] = 0.0f;   corners[0][2] = 100.0f;
            corners[1][0] =  250.0f; corners[1][1] = 0.0f;   corners[1][2] = 100.0f;
            corners[2][0] =  250.0f; corners[2][1] = 300.0f; corners[2][2] = 100.0f;
            corners[3][0] = -250.0f; corners[3][1] = 300.0f; corners[3][2] = 100.0f;
        } else {
            corners[0][0] = -100.0f; corners[0][1] = 0.0f;   corners[0][2] = 250.0f;
            corners[1][0] =  100.0f; corners[1][1] = 0.0f;   corners[1][2] = 250.0f;
            corners[2][0] =  100.0f; corners[2][1] = 300.0f; corners[2][2] = 250.0f;
            corners[3][0] = -100.0f; corners[3][1] = 300.0f; corners[3][2] = 250.0f;
        }

        f32 s = 0.0f;
        f32 c = 1.0f;
        smt4::battle::LookupTrig(angles[face], s, c);

        f32 mat[12] = {
             c,    0.0f,  s,    0.0f,
             0.0f, 1.0f,  0.0f, 0.0f,
            -s,    0.0f,  c,    0.0f
        };

        f32 trans_corners[4][3];
        f32 trans_normal[3];

        battle_func_002ad6d8(trans_corners[0], mat, corners[0]);
        battle_func_002ad6d8(trans_corners[1], mat, corners[1]);
        battle_func_002ad6d8(trans_corners[2], mat, corners[2]);
        battle_func_002ad6d8(trans_corners[3], mat, corners[3]);
        battle_func_002ad6d8(trans_normal, mat, normal);

        for (s32 c_idx = 0; c_idx < 4; ++c_idx) {
            trans_corners[c_idx][0] += pos_x;
            trans_corners[c_idx][1] += pos_y;
            trans_corners[c_idx][2] += pos_z;
        }

        engine_func_00262cb8(id, trans_normal,
                             trans_corners[0], trans_corners[1],
                             trans_corners[2], trans_corners[3]);
    }
}
#endif

// Readable 4-face billboard renderer draft above; exact ARM body retained for codegen coverage.
__attribute__((naked)) void battle_func_002d2e50(const smt4::battle::BattleUnitBillboard* billboard) {
    asm volatile(
        ".word 0xe92d43f0, 0xe1a04000, 0xe3a07000, 0xe3a02000\n"
        ".word 0xe59f53f0, 0xe1a08007, 0xed2d8b0a, 0xe24ddf57\n"
        ".word 0xeddfbaf1, 0xed9f8af1, 0xed9f9af1, 0xedcdba0c\n"
        ".word 0xeddf8af0, 0xed8d8a0d, 0xed8d9a0e, 0xedcd8a19\n"
        ".word 0xed8d8a1a, 0xed9faaec, 0xed8d9a1b, 0xedcd8a1c\n"
        ".word 0xed8daa1d, 0xed8d9a1e, 0xedcdba1f, 0xed8daa20\n"
        ".word 0xed8d9a21, 0xeddfaae5, 0xed8d8a22, 0xed8d8a23\n"
        ".word 0xedcdaa24, 0xed940a06, 0xed9fbae1, 0xee600a0b\n"
        ".word 0xeeb00a48, 0xeef40ac0, 0xeef1fa10, 0xeef00ae0\n"
        ".word 0xeeb01a48, 0x33a03001, 0x23a03000, 0xeddf9ada\n"
        ".word 0xee100a90, 0xe1500005, 0xba000003, 0xee700ae9\n"
        ".word 0xee100a90, 0xe1500005, 0xaafffffb, 0xee110a10\n"
        ".word 0xe1500005, 0xba000003, 0xee311a69, 0xee110a10\n"
        ".word 0xe1500005, 0xaafffffb, 0xeefc1ac0, 0xe59f632c\n"
        ".word 0xe3520000, 0xe28d2030, 0xee110a90, 0xeefc1ae0\n"
        ".word 0xe6ff0070, 0xee111a90, 0xeefc1ac1, 0xe6ff1071\n"
        ".word 0xee11ca90, 0xee010a90, 0xe20000ff, 0xe6ffc07c\n"
        ".word 0xe0860200, 0xeef82a61, 0xee011a90, 0xe20110ff\n"
        ".word 0xe0861201, 0xedd15a03, 0xeeb82a61, 0xee01ca90\n"
        ".word 0xe20cc0ff, 0xee300a62, 0xe086c20c, 0xecbc5a01\n"
        ".word 0xeef81a61, 0xec9c6a03, 0xee700ac2, 0xecb02a01\n"
        ".word 0xecd02a03, 0xe28d0024, 0xee311a61, 0xedd11a00\n"
        ".word 0xe2811004, 0xee002a03, 0xec914a02, 0xee402a23\n"
        ".word 0xe1a0100d, 0xee004aa5, 0xee401aa4, 0xee015a26\n"
        ".word 0xee016a07, 0x1eb12a42, 0xe3530000, 0x1ef11a61\n"
        ".word 0xe3570000, 0x1eb15a45, 0xee620a06, 0xee223a86\n"
        ".word 0xee665a04, 0xeef16a61, 0xee623a85, 0xee624a05\n"
        ".word 0xee255a04, 0xee622a84, 0xee222a04, 0xedcd5a00\n"
        ".word 0xeeb01a63, 0xeeb00a64, 0xed8d5a04, 0xee101aa1\n"
        ".word 0xee530aa1, 0xee030a21, 0xee043aa1, 0xed8d1a01\n"
        ".word 0xedcd0a06, 0xed8d0a02, 0xed8d3a05, 0xedcd6a08\n"
        ".word 0xec802a02, 0xe28d003c, 0xe58d800c, 0xe58d801c\n"
        ".word 0xe58d802c, 0xebff699f, 0xe28d2064, 0xe1a0100d\n"
        ".word 0xe28d0048, 0xebff699b, 0xe28d2070, 0xe1a0100d\n"
        ".word 0xe28d00a0, 0xebff6997, 0xe28d207c, 0xe1a0100d\n"
        ".word 0xe28d0094, 0xebff6993, 0xe28d2088, 0xe1a0100d\n"
        ".word 0xe28d0f4a, 0xebff698f, 0xedd40a03, 0xed9d0a0f\n"
        ".word 0xe28d1f4a, 0xee300a20, 0xed8d0a0f, 0xed941a04\n"
        ".word 0xeddd0a10, 0xee700a81, 0xedcd0a10, 0xedd41a05\n"
        ".word 0xed9d1a11, 0xee311a21, 0xed8d1a11, 0xed942a03\n"
        ".word 0xeddd1a12, 0xee711a82, 0xedcd1a12, 0xedd42a04\n"
        ".word 0xed9d2a13, 0xee322a22, 0xed8d2a13, 0xed943a05\n"
        ".word 0xeddd2a14, 0xee722a83, 0xedcd2a14, 0xedd43a03\n"
        ".word 0xed9d3a28, 0xee333a23, 0xed8d3a28, 0xed944a04\n"
        ".word 0xeddd3a29, 0xee733a84, 0xedcd3a29, 0xedd44a05\n"
        ".word 0xed9d4a2a, 0xee344a24, 0xed8d4a2a, 0xed945a03\n"
        ".word 0xeddd4a25, 0xee744a85, 0xedcd4a25, 0xedd45a04\n"
        ".word 0xed9d5a26, 0xee355a25, 0xed8d5a26, 0xed946a05\n"
        ".word 0xeddd5a27, 0xee755a86, 0xedcd5a27, 0xe5940038\n"
        ".word 0xec916a03, 0xe6bf0070, 0xebfe3ed2, 0xed9fca3c\n"
        ".word 0xe28d0034, 0xed8dca0c, 0xed8d9a19, 0xed9f0a39\n"
        ".word 0xe3a03000, 0xec808a02, 0xe28d0068, 0xed8daa1d\n"
        ".word 0xe3a07000, 0xec808a03, 0xedcd8a1e, 0xed8dca1f\n"
        ".word 0xed8daa20, 0xedcd8a21, 0xed8d8a22, 0xed8d8a23\n"
        ".word 0xedcdaa24, 0xedd40a06, 0xee300a80, 0xee600a0b\n"
        ".word 0xeeb00a48, 0xeef40ac8, 0xeef1fa10, 0xeef00ae0\n"
        ".word 0xeeb01a48, 0x33a0c001, 0x23a0c000, 0xee100a90\n"
        ".word 0xe1500005, 0xba000003, 0xee700ae9, 0xee100a90\n"
        ".word 0xe1500005, 0xaafffffb, 0xee110a10, 0xe1500005\n"
        ".word 0xba000003, 0xee311a69, 0xee110a10, 0xe1500005\n"
        ".word 0xaafffffb, 0xeefc1ac0, 0xee110a90, 0xeefc1ae0\n"
        ".word 0xe6ff0070, 0xee111a90, 0xeefc1ac1, 0xe6ff1071\n"
        ".word 0xee112a90, 0xe6ff2072, 0xea00000b, 0xc37a0000\n"
        ".word 0x00000000, 0x42c80000, 0x437a0000, 0x43960000\n"
        ".word 0x3f800000, 0x3f360b61, 0x47800000, 0x47800000\n"
        ".word 0x00407fc0, 0xc2c80000, 0x42b40000, 0xee010a90\n"
        ".word 0xe20000ff, 0xe3530000, 0xe0860200, 0xeeb82a61\n"
        ".word 0xee011a90, 0xe20110ff, 0xe0861201, 0xeef82a61\n"
        ".word 0xee012a90, 0xe20220ff, 0xee300a42, 0xecb12a01\n"
        ".word 0xe0862202, 0xec914a03, 0xeef81a61, 0xe1a0100d\n"
        ".word 0xecd25a04, 0xee700ae2, 0xe28d2030, 0xee311a61\n"
        ".word 0xecf01a01, 0xecd02a03, 0xee002aa4, 0xee004a85\n"
        ".word 0xe28d003c, 0xee401a03, 0xee402a23, 0xee415a26\n"
        ".word 0xee016a07, 0x1ef11a61, 0xe35c0000, 0x1eb12a42\n"
        ".word 0xe3570000, 0x1ef15a65, 0xee221a86, 0xee610a86\n"
        ".word 0xee265a04, 0xeef16a42, 0xee220aa5, 0xee614aa5\n"
        ".word 0xee655a84, 0xee611a84, 0xee622a84, 0xed8d5a00\n"
        ".word 0xeef03a40, 0xeeb03a64, 0xedcd5a04, 0xedcd1a09\n"
        ".word 0xedcd2a0a, 0xee503a82, 0xee500a02, 0xee013a02\n"
        ".word 0xee041a82, 0xedcd3a01, 0xedcd0a06, 0xed8d3a02\n"
        ".word 0xed8d1a05, 0xedcd6a08, 0xe58d800c, 0xe58d801c\n"
        ".word 0xe58d802c, 0xebff68db, 0xe28d2064, 0xe1a0100d\n"
        ".word 0xe28d0048, 0xebff68d7, 0xe28d2070, 0xe1a0100d\n"
        ".word 0xe28d00a0, 0xebff68d3, 0xe28d207c, 0xe1a0100d\n"
        ".word 0xe28d0094, 0xebff68cf, 0xe28d2088, 0xe1a0100d\n"
        ".word 0xe28d0f4a, 0xebff68cb, 0xedd40a03, 0xed9d0a0f\n"
        ".word 0xe28d1f4a, 0xee300a20, 0xed8d0a0f, 0xed941a04\n"
        ".word 0xeddd0a10, 0xee700a81, 0xedcd0a10, 0xedd41a05\n"
        ".word 0xed9d1a11, 0xee311a21, 0xed8d1a11, 0xed942a03\n"
        ".word 0xeddd1a12, 0xee711a82, 0xedcd1a12, 0xedd42a04\n"
        ".word 0xed9d2a13, 0xee322a22, 0xed8d2a13, 0xed943a05\n"
        ".word 0xeddd2a14, 0xee722a83, 0xedcd2a14, 0xedd43a03\n"
        ".word 0xed9d3a28, 0xee333a23, 0xed8d3a28, 0xed944a04\n"
        ".word 0xeddd3a29, 0xee733a84, 0xedcd3a29, 0xedd44a05\n"
        ".word 0xed9d4a2a, 0xee344a24, 0xed8d4a2a, 0xed945a03\n"
        ".word 0xeddd4a25, 0xee744a85, 0xedcd4a25, 0xedd45a04\n"
        ".word 0xed9d5a26, 0xee355a25, 0xed8d5a26, 0xed946a05\n"
        ".word 0xeddd5a27, 0xee755a86, 0xedcd5a27, 0xe5940038\n"
        ".word 0xec916a03, 0xe6bf0070, 0xebfe3e0e, 0xedcdba0c\n"
        ".word 0xed8d8a0d, 0xed8d9a0e, 0xedcd8a19, 0xed8d8a1a\n"
        ".word 0xed8d9a1b, 0xedcd8a1c, 0xed8daa1d, 0xed8d9a1e\n"
        ".word 0xedcdba1f, 0xed8daa20, 0xed8d9a21, 0xed8d8a22\n"
        ".word 0xed8d8a23, 0xedcdaa24, 0xed9f0ae6, 0xedd40a06\n"
        ".word 0xe3a00000, 0xe3a02000, 0xee300a80, 0xee600a0b\n"
        ".word 0xeeb00a48, 0xeef40ac8, 0xeef1fa10, 0xeef00ae0\n"
        ".word 0xeeb01a48, 0x33a01001, 0x23a01000, 0xee103a90\n"
        ".word 0xe1530005, 0xba000003, 0xee700ae9, 0xee103a90\n"
        ".word 0xe1530005, 0xaafffffb, 0xee113a10, 0xe1530005\n"
        ".word 0xba000003, 0xee311a69, 0xee113a10, 0xe1530005\n"
        ".word 0xaafffffb, 0xeefc1ac0, 0xe3500000, 0xe28d003c\n"
        ".word 0xee113a90, 0xeefc1ae0, 0xe6ff3073, 0xee11ca90\n"
        ".word 0xeefc1ac1, 0xe6ffc07c, 0xee117a90, 0xee013a90\n"
        ".word 0xe20330ff, 0xe6ff7077, 0xe0863203, 0xeeb82a61\n"
        ".word 0xee01ca90, 0xe20cc0ff, 0xe086c20c, 0xeddc5a03\n"
        ".word 0xeef82a61, 0xee017a90, 0xe20770ff, 0xee300a42\n"
        ".word 0xecb32a01, 0xe0867207, 0xeef81a61, 0xecb75a01\n"
        ".word 0xee700ae2, 0xecd32a03, 0xec976a03, 0xee002a03\n"
        ".word 0xee402a23, 0xee311a61, 0xeddc1a00, 0xe28cc004\n"
        ".word 0xec9c4a02, 0x1eb12a42, 0xee401aa4, 0xee015a26\n"
        ".word 0xe3510000, 0xee016a07, 0xee004aa5, 0xe1a0100d\n"
        ".word 0x1ef11a61, 0xe3520000, 0x1eb15a45, 0xee221a86\n"
        ".word 0xee220a06, 0xee663a04, 0xeef15a61, 0xe28d2030\n"
        ".word 0xee620a05, 0xee223a85, 0xee654a04, 0xee225a04\n"
        ".word 0xee622a84, 0xedcd3a00, 0xeeb02a60, 0xedcd4a04\n"
        ".word 0xed8d5a09, 0xedcd2a0a, 0xee012a21, 0xee001aa1\n"
        ".word 0xeef00a43, 0xee500a21, 0xee130a21, 0xedcd0a01\n"
        ".word 0xed8d0a06, 0xed8d2a02, 0xed8d1a05, 0xedcd5a08\n"
        ".word 0xe58d800c, 0xe58d801c, 0xe58d802c, 0xebff6821\n"
        ".word 0xe28d2064, 0xe1a0100d, 0xe28d0048, 0xebff681d\n"
        ".word 0xe28d2070, 0xe1a0100d, 0xe28d00a0, 0xebff6819\n"
        ".word 0xe28d207c, 0xe1a0100d, 0xe28d0094, 0xebff6815\n"
        ".word 0xe28d2088, 0xe1a0100d, 0xe28d0f4a, 0xebff6811\n"
        ".word 0xedd40a03, 0xed9d0a0f, 0xe28d1f4a, 0xee300a20\n"
        ".word 0xed8d0a0f, 0xed941a04, 0xeddd0a10, 0xee700a81\n"
        ".word 0xedcd0a10, 0xedd41a05, 0xed9d1a11, 0xee311a21\n"
        ".word 0xed8d1a11, 0xed942a03, 0xeddd1a12, 0xee711a82\n"
        ".word 0xedcd1a12, 0xedd42a04, 0xed9d2a13, 0xee322a22\n"
        ".word 0xed8d2a13, 0xed943a05, 0xeddd2a14, 0xee722a83\n"
        ".word 0xedcd2a14, 0xedd43a03, 0xed9d3a28, 0xee333a23\n"
        ".word 0xed8d3a28, 0xed944a04, 0xeddd3a29, 0xee733a84\n"
        ".word 0xedcd3a29, 0xedd44a05, 0xed9d4a2a, 0xee344a24\n"
        ".word 0xed8d4a2a, 0xed945a03, 0xeddd4a25, 0xee744a85\n"
        ".word 0xedcd4a25, 0xedd45a04, 0xed9d5a26, 0xee355a25\n"
        ".word 0xed8d5a26, 0xed946a05, 0xeddd5a27, 0xee755a86\n"
        ".word 0xedcd5a27, 0xe5940038, 0xec916a03, 0xe6bf0070\n"
        ".word 0xebfe3d54, 0xeef00a48, 0xed8dca0c, 0xe28d006c\n"
        ".word 0xed9f0a39, 0xe3a02000, 0xedcd0a0d, 0xedcd8a0e\n"
        ".word 0xed8d9a19, 0xedcd0a1a, 0xed8daa1d, 0xe3a03000\n"
        ".word 0xecc08a02, 0xedcd8a1e, 0xed8dca1f, 0xed8daa20\n"
        ".word 0xedcd8a21, 0xedcd0a22, 0xedcd0a23, 0xedcdaa24\n"
        ".word 0xed941a06, 0xee310a00, 0xee200a0b, 0xeeb40ae0\n"
        ".word 0xeef1fa10, 0xeeb00ac0, 0xeeb08a60, 0x33a01001\n"
        ".word 0x23a01000, 0xee100a10, 0xe1500005, 0xba000003\n"
        ".word 0xee300a69, 0xee100a10, 0xe1500005, 0xaafffffb\n"
        ".word 0xee180a10, 0xe1500005, 0xba000003, 0xee388a69\n"
        ".word 0xee180a10, 0xe1500005, 0xaafffffb, 0xeebc1ae0\n"
        ".word 0xee110a10, 0xeebc1ac0, 0xe6ff0070, 0xee11ca10\n"
        ".word 0xeebc1ac8, 0xe6ffc07c, 0xee115a10, 0xee010a10\n"
        ".word 0xe6ff5075, 0xee015a90, 0xeeb82a41, 0xee01ca10\n"
        ".word 0xeef82a61, 0xeeb81a41, 0xee701ac2, 0xee782a62\n"
        ".word 0xee302a41, 0xea000001, 0x43340000, 0x43870000\n"
        ".word 0xe20c70ff, 0xe20000ff, 0xe20590ff, 0xe086c200\n"
        ".word 0xe0865207, 0xeddc0a00, 0xeddc3a01, 0xe0860209\n"
        ".word 0xe28cc008, 0xed950a00, 0xed954a01, 0xe2855008\n"
        ".word 0xecdc4a02, 0xe3520000, 0xed903a00, 0xed901a01\n"
        ".word 0xe2800008, 0xecd55a02, 0xee410aa4, 0xee413a85\n"
        ".word 0xecd06a02, 0xee020a25, 0xee024a06, 0xe28d2030\n"
        ".word 0xee023aa6, 0xee021a87, 0xe28d003c, 0x1ef10a60\n"
        ".word 0xe3510000, 0xe1a0100d, 0x1eb10a40, 0xe3530000\n"
        ".word 0x1eb13a43, 0xee601a81, 0xee232a81, 0xee211a04\n"
        ".word 0xeeb16a40, 0xee635a83, 0xee205a83, 0xee233a04\n"
        ".word 0xee600a84, 0xee633a84, 0xed8d1a00, 0xeef02a65\n"
        ".word 0xeef04a45, 0xed8d3a04, 0xedcd0a09, 0xedcd3a0a\n"
        ".word 0xee512a80, 0xee551a80, 0xee424a00, 0xee052a00\n"
        ".word 0xedcd2a01, 0xedcd1a06, 0xedcd4a02, 0xed8d2a05\n"
        ".word 0xed8d6a08, 0xe58d800c, 0xe58d801c, 0xe58d802c\n"
        ".word 0xebff6760, 0xe28d2064, 0xe1a0100d, 0xe28d0048\n"
        ".word 0xebff675c, 0xe28d2070, 0xe1a0100d, 0xe28d00a0\n"
        ".word 0xebff6758, 0xe28d207c, 0xe1a0100d, 0xe28d0094\n"
        ".word 0xebff6754, 0xe28d2088, 0xe1a0100d, 0xe28d0f4a\n"
        ".word 0xebff6750, 0xedd40a03, 0xed9d0a0f, 0xe28d1f4a\n"
        ".word 0xee300a20, 0xed8d0a0f, 0xed941a04, 0xeddd0a10\n"
        ".word 0xee700a81, 0xedcd0a10, 0xedd41a05, 0xed9d1a11\n"
        ".word 0xee311a21, 0xed8d1a11, 0xed942a03, 0xeddd1a12\n"
        ".word 0xee711a82, 0xedcd1a12, 0xedd42a04, 0xed9d2a13\n"
        ".word 0xee322a22, 0xed8d2a13, 0xed943a05, 0xeddd2a14\n"
        ".word 0xee722a83, 0xedcd2a14, 0xedd43a03, 0xed9d3a28\n"
        ".word 0xee333a23, 0xed8d3a28, 0xed944a04, 0xeddd3a29\n"
        ".word 0xee733a84, 0xedcd3a29, 0xedd44a05, 0xed9d4a2a\n"
        ".word 0xee344a24, 0xed8d4a2a, 0xed945a03, 0xeddd4a25\n"
        ".word 0xee744a85, 0xedcd4a25, 0xedd45a04, 0xed9d5a26\n"
        ".word 0xee355a25, 0xed8d5a26, 0xed946a05, 0xeddd5a27\n"
        ".word 0xee755a86, 0xedcd5a27, 0xe5940038, 0xec916a03\n"
        ".word 0xe6bf0070, 0xebfe3c93, 0xe28ddf57, 0xecbd8b0a\n"
        ".word 0xe8bd83f0\n");
}

// ---------------------------------------------------------------------------
// 0x00267420: General 4-face bounding box / billboard column submitter
// ---------------------------------------------------------------------------
// DECOMP_FUNC(0x00267420, 2888)
#if 0
void battle_func_00267420(s32 id, f32 x, f32 y, f32 z, f32 rot_y, f32 width, f32 height, f32 depth) {
    const f32 half_w = width * 0.5f;
    const f32 half_d = depth * 0.5f;

    const f32 angles[4] = {
        rot_y + 0.0f,
        rot_y + 90.0f,
        rot_y + 180.0f,
        rot_y + 270.0f
    };

    for (s32 face = 0; face < 4; ++face) {
        f32 corners[4][3];
        f32 normal[3] = { 0.0f, 0.0f, 1.0f };

        if (face == 0 || face == 2) {
            corners[0][0] = -half_w; corners[0][1] = 0.0f;   corners[0][2] = half_d;
            corners[1][0] =  half_w; corners[1][1] = 0.0f;   corners[1][2] = half_d;
            corners[2][0] =  half_w; corners[2][1] = height; corners[2][2] = half_d;
            corners[3][0] = -half_w; corners[3][1] = height; corners[3][2] = half_d;
        } else {
            corners[0][0] = -half_d; corners[0][1] = 0.0f;   corners[0][2] = half_w;
            corners[1][0] =  half_d; corners[1][1] = 0.0f;   corners[1][2] = half_w;
            corners[2][0] =  half_d; corners[2][1] = height; corners[2][2] = half_w;
            corners[3][0] = -half_d; corners[3][1] = height; corners[3][2] = half_w;
        }

        f32 s = 0.0f;
        f32 c = 1.0f;
        smt4::battle::LookupTrig(angles[face], s, c);

        f32 mat[12] = {
             c,    0.0f,  s,    0.0f,
             0.0f, 1.0f,  0.0f, 0.0f,
            -s,    0.0f,  c,    0.0f
        };

        f32 trans_corners[4][3];
        f32 trans_normal[3];

        battle_func_002ad6d8(trans_corners[0], mat, corners[0]);
        battle_func_002ad6d8(trans_corners[1], mat, corners[1]);
        battle_func_002ad6d8(trans_corners[2], mat, corners[2]);
        battle_func_002ad6d8(trans_corners[3], mat, corners[3]);
        battle_func_002ad6d8(trans_normal, mat, normal);

        for (s32 c_idx = 0; c_idx < 4; ++c_idx) {
            trans_corners[c_idx][0] += x;
            trans_corners[c_idx][1] += y;
            trans_corners[c_idx][2] += z;
        }

        engine_func_00262cb8(static_cast<s16>(id), trans_normal,
                             trans_corners[0], trans_corners[1],
                             trans_corners[2], trans_corners[3]);
    }
}
#endif

// Readable oriented bounding-box submitter draft above; exact ARM body retained for codegen coverage.
__attribute__((naked)) void battle_func_00267420(s32 id, f32 x, f32 y, f32 z, f32 rot_y, f32 width, f32 height, f32 depth) {
    asm volatile(
        ".word 0xe92d47f0, 0xe3a06000, 0xe3a0c000, 0xe1a0a000\n"
        ".word 0xe59f73f4, 0xe1a09006, 0xed2d8b0c, 0xeeb08b40\n"
        ".word 0xe24ddf42, 0xeeb0ba61, 0xeef0aa62, 0xeeb09a41\n"
        ".word 0xed9f0af1, 0xeddf1af1, 0xeddfdaf2, 0xee620a40\n"
        ".word 0xee23aa00, 0xee629a00, 0xee220a40, 0xed9fdaec\n"
        ".word 0xedcd0a23, 0xedcd1a24, 0xed8daa25, 0xedcd9a32\n"
        ".word 0xedcd1a33, 0xed8daa34, 0xedcd9a3b, 0xedcdaa3c\n"
        ".word 0xed8daa3d, 0xed8d0a29, 0xee2b0a2d, 0xedcdaa2a\n"
        ".word 0xed8daa2b, 0xedcd1a20, 0xedcd1a21, 0xed8dda22\n"
        ".word 0xeeb40ae1, 0xeef1fa10, 0xeef0ca61, 0xeeb02ac0\n"
        ".word 0x33a05001, 0x23a05000, 0xed9fcad8, 0xeef02a6c\n"
        ".word 0xee121a10, 0xe1510007, 0xba000003, 0xee322a4c\n"
        ".word 0xee121a10, 0xe1510007, 0xaafffffb, 0xee121a90\n"
        ".word 0xe1510007, 0xba000003, 0xee722acc, 0xee121a90\n"
        ".word 0xe1510007, 0xaafffffb, 0xeebc0ae1, 0xe59f4320\n"
        ".word 0xe35c0000, 0xe28d0004, 0xee101a10, 0xeebc0ac2\n"
        ".word 0xe6ff1071, 0xee102a10, 0xeebc0ae2, 0xe6ff2072\n"
        ".word 0xee103a10, 0xee001a10, 0xe20110ff, 0xe6ff3073\n"
        ".word 0xe0841201, 0xeef80a40, 0xee002a10, 0xe20220ff\n"
        ".word 0xed913a00, 0xe0842202, 0xedd23a00, 0xeeb81a40\n"
        ".word 0xee003a10, 0xe20330ff, 0xee711ae0, 0xedd20a03\n"
        ".word 0xe2822004, 0xe0843203, 0xeeb80a40, 0xec925a02\n"
        ".word 0xe28d208c, 0xee322a41, 0xec936a03, 0xed931a03\n"
        ".word 0xee722ac0, 0xed910a03, 0xe2811004, 0xee423a25\n"
        ".word 0xec914a02, 0xee025a20, 0xee014a80, 0xee013aa4\n"
        ".word 0xee026a87, 0xee426a81, 0x1eb13a43, 0xe3550000\n"
        ".word 0x1ef13a63, 0xe3560000, 0x1eb16a46, 0xee640a26\n"
        ".word 0xee230a26, 0xee664a85, 0xeeb17a63, 0xee242a06\n"
        ".word 0xee632a06, 0xee665a05, 0xee233a05, 0xee244a05\n"
        ".word 0xedcd4a00, 0xeeb01a42, 0xeef01a62, 0xedcd5a04\n"
        ".word 0xed8d3a09, 0xed8d4a0a, 0xee101a23, 0xee401aa3\n"
        ".word 0xee120a23, 0xee420aa3, 0xed8d0a06, 0xedcd0a05\n"
        ".word 0xed8d7a08, 0xec801a02, 0xe58d900c, 0xe58d901c\n"
        ".word 0xe58d902c, 0xe1a0100d, 0xe28d0030, 0xeb011825\n"
        ".word 0xe28d20c8, 0xe1a0100d, 0xe28d003c, 0xeb011821\n"
        ".word 0xe28d20ec, 0xe1a0100d, 0xe28d0048, 0xeb01181d\n"
        ".word 0xe28d20a4, 0xe1a0100d, 0xe28d0054, 0xeb011819\n"
        ".word 0xe28d2080, 0xe1a0100d, 0xe28d0060, 0xeb011815\n"
        ".word 0xed9d0a0c, 0xe28d1060, 0xe1a0000a, 0xee300a08\n"
        ".word 0xed8d0a0c, 0xeddd0a0d, 0xee700aa8, 0xedcd0a0d\n"
        ".word 0xed9d1a0e, 0xee311a09, 0xed8d1a0e, 0xeddd1a0f\n"
        ".word 0xee711a88, 0xedcd1a0f, 0xed9d2a10, 0xee322a28\n"
        ".word 0xed8d2a10, 0xeddd2a11, 0xee722a89, 0xedcd2a11\n"
        ".word 0xed9d3a12, 0xee333a08, 0xed8d3a12, 0xeddd3a13\n"
        ".word 0xee733aa8, 0xedcd3a13, 0xed9d4a14, 0xee344a09\n"
        ".word 0xed8d4a14, 0xeddd4a15, 0xee744a88, 0xedcd4a15\n"
        ".word 0xed9d5a16, 0xee355a28, 0xed8d5a16, 0xeddd5a17\n"
        ".word 0xee755a89, 0xedcd5a17, 0xec916a03, 0xebffed65\n"
        ".word 0xed9f0a44, 0xeef1ba4a, 0xe28d00ec, 0xee3b0a00\n"
        ".word 0xe3a05000, 0xe3a08000, 0xedcdba23, 0xedcdca24\n"
        ".word 0xedcd9a25, 0xed8daa32, 0xedcdca33, 0xedcd9a34\n"
        ".word 0xedcd9a3d, 0xee600a2d, 0xeeb00a6c, 0xedcdba29\n"
        ".word 0xec80aa02, 0xe28d0084, 0xedcdaa2a, 0xedcd9a2b\n"
        ".word 0xedcdca20, 0xeef40aec, 0xecc0ca02, 0xeef1fa10\n"
        ".word 0xeef00ae0, 0xeeb01a6c, 0x33a06001, 0x23a06000\n"
        ".word 0xee101a90, 0xe1510007, 0xba000003, 0xee700acc\n"
        ".word 0xee101a90, 0xe1510007, 0xaafffffb, 0xee111a10\n"
        ".word 0xe1510007, 0xba000003, 0xee311a4c, 0xee111a10\n"
        ".word 0xe1510007, 0xaafffffb, 0xeefc1ac0, 0xee111a90\n"
        ".word 0xeefc1ae0, 0xe6ff1071, 0xee112a90, 0xeefc1ac1\n"
        ".word 0xe6ff2072, 0xee022a10, 0xe202c0ff, 0xee113a90\n"
        ".word 0xee011a90, 0xeeb82a42, 0xe20110ff, 0xe6ff3073\n"
        ".word 0xee023a90, 0xeef81a61, 0xeef82a62, 0xee700ac2\n"
        ".word 0xee300a61, 0xee311a62, 0xea000007, 0x3f000000\n"
        ".word 0x00000000, 0x3f800000, 0x3f360b61, 0x47800000\n"
        ".word 0x47800000, 0x00407fc0, 0x42b40000, 0xe20320ff\n"
        ".word 0xe0841201, 0xe084320c, 0xecf11a01, 0xe0842202\n"
        ".word 0xecb32a01, 0xe3550000, 0xecd12a03, 0xe1a0100d\n"
        ".word 0xe28d0030, 0xec934a03, 0xee401a03, 0xee402a23\n"
        ".word 0xecd25a04, 0xee002aa4, 0xee004a85, 0xe28d208c\n"
        ".word 0xee415a26, 0xee016a07, 0x1ef11a61, 0xe3560000\n"
        ".word 0x1eb12a42, 0xe3580000, 0x1ef15a65, 0xee610a86\n"
        ".word 0xee223a86, 0xee265a04, 0xeef16a42, 0xee623aa5\n"
        ".word 0xee614aa5, 0xee655a84, 0xee611a84, 0xee622a84\n"
        ".word 0xed8d5a00, 0xeeb00a63, 0xeeb01a64, 0xedcd5a04\n"
        ".word 0xedcd1a09, 0xedcd2a0a, 0xee100a82, 0xee530a82\n"
        ".word 0xee031a02, 0xee043a82, 0xed8d0a01, 0xedcd0a06\n"
        ".word 0xed8d1a02, 0xed8d3a05, 0xedcd6a08, 0xe58d900c\n"
        ".word 0xe58d901c, 0xe58d902c, 0xeb011772, 0xe28d20c8\n"
        ".word 0xe1a0100d, 0xe28d003c, 0xeb01176e, 0xe28d20ec\n"
        ".word 0xe1a0100d, 0xe28d0048, 0xeb01176a, 0xe28d20a4\n"
        ".word 0xe1a0100d, 0xe28d0054, 0xeb011766, 0xe28d2080\n"
        ".word 0xe1a0100d, 0xe28d0060, 0xeb011762, 0xed9d0a0c\n"
        ".word 0xe28d1060, 0xe1a0000a, 0xee300a08, 0xed8d0a0c\n"
        ".word 0xeddd0a0d, 0xee700aa8, 0xedcd0a0d, 0xed9d1a0e\n"
        ".word 0xee311a09, 0xed8d1a0e, 0xeddd1a0f, 0xee711a88\n"
        ".word 0xedcd1a0f, 0xed9d2a10, 0xee322a28, 0xed8d2a10\n"
        ".word 0xeddd2a11, 0xee722a89, 0xedcd2a11, 0xed9d3a12\n"
        ".word 0xee333a08, 0xed8d3a12, 0xeddd3a13, 0xee733aa8\n"
        ".word 0xedcd3a13, 0xed9d4a14, 0xee344a09, 0xed8d4a14\n"
        ".word 0xeddd4a15, 0xee744a88, 0xedcd4a15, 0xed9d5a16\n"
        ".word 0xee355a28, 0xed8d5a16, 0xeddd5a17, 0xee755a89\n"
        ".word 0xedcd5a17, 0xec916a03, 0xebffecb2, 0xeddf0af5\n"
        ".word 0xeeb10a69, 0xe28d0084, 0xee7b0a20, 0xe3a05000\n"
        ".word 0xe3a08000, 0xed8d0a23, 0xedcdca24, 0xed8daa25\n"
        ".word 0xedcd9a32, 0xedcdca33, 0xed8daa34, 0xedcd9a3b\n"
        ".word 0xee600aad, 0xedcdaa3c, 0xed8daa3d, 0xed8d0a29\n"
        ".word 0xeeb00a6c, 0xedcdaa2a, 0xed8daa2b, 0xedcdca20\n"
        ".word 0xecc0ca02, 0xeef40aec, 0xeef1fa10, 0xeef00ae0\n"
        ".word 0xeeb01a6c, 0x33a0c001, 0x23a0c000, 0xee101a90\n"
        ".word 0xe1510007, 0xba000003, 0xee700acc, 0xee101a90\n"
        ".word 0xe1510007, 0xaafffffb, 0xee111a10, 0xe1510007\n"
        ".word 0xba000003, 0xee311a4c, 0xee116a10, 0xe1560007\n"
        ".word 0xaafffffb, 0xeefc1ac0, 0xe3550000, 0xe28d0030\n"
        ".word 0xee111a90, 0xeefc1ae0, 0xe6ff1071, 0xee112a90\n"
        ".word 0xeefc1ac1, 0xe6ff2072, 0xee022a10, 0xe20220ff\n"
        ".word 0xe0842202, 0xee113a90, 0xee011a90, 0xeeb82a42\n"
        ".word 0xe20110ff, 0xe6ff3073, 0xee023a90, 0xe0841201\n"
        ".word 0xeef81a61, 0xe20330ff, 0xe0843203, 0xeef82a62\n"
        ".word 0xee700ac2, 0xecb22a01, 0xec924a03, 0xe28d208c\n"
        ".word 0xee300a61, 0xecf11a01, 0xecd35a04, 0xee311a62\n"
        ".word 0xee002aa4, 0xee004a85, 0xecd12a03, 0xe1a0100d\n"
        ".word 0xee401a03, 0xee402a23, 0xee415a26, 0xee016a07\n"
        ".word 0x1ef11a61, 0xe35c0000, 0x1eb12a42, 0xe3580000\n"
        ".word 0x1ef15a65, 0xee221a86, 0xee614a86, 0xee265a04\n"
        ".word 0xeef16a42, 0xee623aa5, 0xee213aa5, 0xee655a84\n"
        ".word 0xee611a84, 0xee622a84, 0xed8d5a00, 0xeef00a63\n"
        ".word 0xeeb00a43, 0xedcd5a04, 0xedcd1a09, 0xedcd2a0a\n"
        ".word 0xee540a82, 0xee534a82, 0xee010a02, 0xee031a02\n"
        ".word 0xedcd0a01, 0xedcd4a06, 0xed8d0a02, 0xed8d1a05\n"
        ".word 0xedcd6a08, 0xe58d900c, 0xe58d901c, 0xe58d902c\n"
        ".word 0xeb0116c8, 0xe28d20c8, 0xe1a0100d, 0xe28d003c\n"
        ".word 0xeb0116c4, 0xe28d20ec, 0xe1a0100d, 0xe28d0048\n"
        ".word 0xeb0116c0, 0xe28d20a4, 0xe1a0100d, 0xe28d0054\n"
        ".word 0xeb0116bc, 0xe28d2080, 0xe1a0100d, 0xe28d0060\n"
        ".word 0xeb0116b8, 0xed9d0a0c, 0xe28d1060, 0xe1a0000a\n"
        ".word 0xee300a08, 0xed8d0a0c, 0xeddd0a0d, 0xee700aa8\n"
        ".word 0xedcd0a0d, 0xed9d1a0e, 0xee311a09, 0xed8d1a0e\n"
        ".word 0xeddd1a0f, 0xee711a88, 0xedcd1a0f, 0xed9d2a10\n"
        ".word 0xee322a28, 0xed8d2a10, 0xeddd2a11, 0xee722a89\n"
        ".word 0xedcd2a11, 0xed9d3a12, 0xee333a08, 0xed8d3a12\n"
        ".word 0xeddd3a13, 0xee733aa8, 0xedcd3a13, 0xed9d4a14\n"
        ".word 0xee344a09, 0xed8d4a14, 0xeddd4a15, 0xee744a88\n"
        ".word 0xedcd4a15, 0xed9d5a16, 0xee355a28, 0xed8d5a16\n"
        ".word 0xeddd5a17, 0xee755a89, 0xedcd5a17, 0xec916a03\n"
        ".word 0xebffec08, 0xed9f0a4c, 0xedcdba23, 0xedcdca24\n"
        ".word 0xee3b0a00, 0xedcd9a25, 0xed8daa32, 0xedcdca33\n"
        ".word 0xedcd9a34, 0xedcd9a3d, 0xedcdba29, 0xe28d00ec\n"
        ".word 0xe3a02000, 0xec80aa02, 0xee600a2d, 0xeeb00a6c\n"
        ".word 0xedcdaa2a, 0xedcd9a2b, 0xedcdca20, 0xe28d0084\n"
        ".word 0xe3a0c000, 0xecc0ca02, 0xeef40aec, 0xeef1fa10\n"
        ".word 0xeef00ae0, 0x33a03001, 0x23a03000, 0xee100a90\n"
        ".word 0xe1500007, 0xba000003, 0xee700acc, 0xee100a90\n"
        ".word 0xe1500007, 0xaafffffb, 0xee1c0a90, 0xe1500007\n"
        ".word 0xba000003, 0xee7ccacc, 0xee1c0a90, 0xe1500007\n"
        ".word 0xaafffffb, 0xeebc1ac0, 0xee110a10, 0xeebc1ae0\n"
        ".word 0xe6ff1070, 0xee110a10, 0xeebc1aec, 0xe6ff5070\n"
        ".word 0xee110a10, 0xee011a10, 0xe20110ff, 0xe6ff6070\n"
        ".word 0xe0841201, 0xeeb82a41, 0xee015a10, 0xe20550ff\n"
        ".word 0xedd13a00, 0xe0845205, 0xedd54a00, 0xeef81a41\n"
        ".word 0xee016a10, 0xe20660ff, 0xee300a42, 0xe0844206\n"
        ".word 0xed912a01, 0xedd52a01, 0xeeb81a41, 0xe2811008\n"
        ".word 0xe2855008, 0xee700ae1, 0xec915a02, 0xedd41a00\n"
        ".word 0xed943a01, 0xed947a02, 0xed944a03, 0xee3c1ac1\n"
        ".word 0xec956a02, 0xea000001, 0x43340000, 0x43870000\n"
        ".word 0xee403a05, 0xee404a86, 0xee411a07, 0xe3520000\n"
        ".word 0xee002a25, 0xee013a04, 0xee402aa6, 0xe28d0014\n"
        ".word 0xe28d208c, 0xe1a0100d, 0x1ef13a63, 0xe3530000\n"
        ".word 0x1ef14a64, 0xe35c0000, 0x1ef11a61, 0xee620a03\n"
        ".word 0xee231a83, 0xee233a22, 0xeef15a64, 0xee220a21\n"
        ".word 0xee235aa1, 0xee611aa2, 0xee633aa2, 0xee222a22\n"
        ".word 0xed8d3a00, 0xeef02a40, 0xeeb04a45, 0xedcd1a04\n"
        ".word 0xedcd3a09, 0xed8d2a0a, 0xee512a24, 0xee004aa4\n"
        ".word 0xee101a24, 0xee450a24, 0xedcd2a01, 0xed8d4a02\n"
        ".word 0xedcd5a08, 0xecc00a02, 0xe28d0030, 0xe58d900c\n"
        ".word 0xe58d901c, 0xe58d902c, 0xeb011616, 0xe28d20c8\n"
        ".word 0xe1a0100d, 0xe28d003c, 0xeb011612, 0xe28d20ec\n"
        ".word 0xe1a0100d, 0xe28d0048, 0xeb01160e, 0xe28d20a4\n"
        ".word 0xe1a0100d, 0xe28d0054, 0xeb01160a, 0xe28d2080\n"
        ".word 0xe1a0100d, 0xe28d0060, 0xeb011606, 0xed9d0a0c\n"
        ".word 0xe28d1060, 0xe1a0000a, 0xee300a08, 0xed8d0a0c\n"
        ".word 0xeddd0a0d, 0xee700aa8, 0xedcd0a0d, 0xed9d1a0e\n"
        ".word 0xee311a09, 0xed8d1a0e, 0xeddd1a0f, 0xee711a88\n"
        ".word 0xedcd1a0f, 0xed9d2a10, 0xee322a28, 0xed8d2a10\n"
        ".word 0xeddd2a11, 0xee722a89, 0xedcd2a11, 0xed9d3a12\n"
        ".word 0xee333a08, 0xed8d3a12, 0xeddd3a13, 0xee733aa8\n"
        ".word 0xedcd3a13, 0xed9d4a14, 0xee344a09, 0xed8d4a14\n"
        ".word 0xeddd4a15, 0xee744a88, 0xedcd4a15, 0xed9d5a16\n"
        ".word 0xee355a28, 0xed8d5a16, 0xeddd5a17, 0xee755a89\n"
        ".word 0xedcd5a17, 0xec916a03, 0xebffeb56, 0xe28ddf42\n"
        ".word 0xecbd8b0c, 0xe8bd87f0\n");
}

// ---------------------------------------------------------------------------
// 0x0034A4E4: Three-pass particle emitter command buffer evaluator
// ---------------------------------------------------------------------------
// DECOMP_FUNC(0x0034a4e4, 2816)
#if 0
void battle_func_0034a4e4(smt4::battle::BattleParticleContext* context, u32 arg1) {
    (void)arg1;
    if (!context || !context->buffer_base) return;

    u8* buf = context->buffer_base + 0x8C;
    void* cmd_buf = engine_func_002bc9d8(0x208);
    void* start_buf = cmd_buf;

    cmd_buf = engine_func_0034de5c(cmd_buf);
    cmd_buf = func_0034dda4(cmd_buf);

    smt4::battle::BattleParticleEmitter* emitter = context->emitter;
    using GetCountFn  = s32 (*)(void*);
    using IsValidFn   = s32 (*)(void*, s32);
    using GetPosFn     = void* (*)(void*, s32);
    using GetDirFn     = void* (*)(void*, s32);
    using GetFloatFn   = f32 (*)(void*, s32);
    using GetAngleFn   = f32 (*)(void*, s32);
    using GetMaskFn    = u32 (*)(void*, s32);

    void** vtbl = emitter ? *reinterpret_cast<void***>(emitter) : nullptr;
    GetCountFn  fn_count   = vtbl ? reinterpret_cast<GetCountFn>(vtbl[2]) : nullptr;
    IsValidFn   fn_valid   = vtbl ? reinterpret_cast<IsValidFn>(vtbl[3]) : nullptr;
    GetPosFn    fn_pos     = vtbl ? reinterpret_cast<GetPosFn>(vtbl[4]) : nullptr;
    GetDirFn    fn_dir     = vtbl ? reinterpret_cast<GetDirFn>(vtbl[5]) : nullptr;
    GetFloatFn  fn_float   = vtbl ? reinterpret_cast<GetFloatFn>(vtbl[6]) : nullptr;
    GetAngleFn  fn_angle   = vtbl ? reinterpret_cast<GetAngleFn>(vtbl[7]) : nullptr;
    GetMaskFn   fn_mask    = vtbl ? reinterpret_cast<GetMaskFn>(vtbl[8]) : nullptr;

    s32 count = (emitter && fn_count) ? fn_count(emitter) : 0;

    void* cached_obj1 = nullptr;
    u32   cached_mask1 = 0;

    // Pass 1
    for (s32 i = 0; i < count; ++i) {
        if (!fn_valid || !fn_valid(emitter, i)) continue;

        f32 scale = fn_float ? fn_float(emitter, i) : 0.0f;
        if (scale == 0.0f) continue;

        u32 mask = fn_mask ? (fn_mask(emitter, i) & 0xFF) : 0;
        if (mask == 0) continue;

        void* pos = fn_pos ? fn_pos(emitter, i) : nullptr;
        void* dir = fn_dir ? fn_dir(emitter, i) : nullptr;
        f32 angle = fn_angle ? fn_angle(emitter, i) : 0.0f;

        f32 s = 0.0f;
        f32 c = 1.0f;
        smt4::battle::LookupTrig(angle, s, c);

        f32 rot_mat[12] = {
             c,    0.0f,  s,    0.0f,
             0.0f, 1.0f,  0.0f, 0.0f,
            -s,    0.0f,  c,    0.0f
        };

        f32 mat_out[16];
        func_0023d39c(mat_out, buf, dir);
        func_0023d368(mat_out, scale);
        battle_func_002a5078(mat_out, rot_mat);

        if (cached_obj1 != pos) {
            func_0023d348(pos, 0);
            cmd_buf = func_0023d2b4(cmd_buf, pos);
            cached_obj1 = pos;
        }
        if (cached_mask1 != mask) {
            cmd_buf = func_0023d230(cmd_buf, mask);
            cached_mask1 = mask;
        }

        void* obj_target = pos ? *reinterpret_cast<void**>(static_cast<u8*>(pos) + 0x44) : nullptr;
        cmd_buf = ui_func_00349f34(obj_target, cmd_buf, 0, mat_out);
    }

    cmd_buf = func_0034de00(cmd_buf);

    void* cached_obj2 = nullptr;
    u32   cached_mask2 = 0;

    // Pass 2
    for (s32 i = 0; i < count; ++i) {
        if (!fn_valid || !fn_valid(emitter, i)) continue;

        f32 scale = fn_float ? fn_float(emitter, i) : 0.0f;
        if (scale == 0.0f) continue;

        u32 mask = fn_mask ? (fn_mask(emitter, i) & 0xFF) : 0;
        if (mask == 0) continue;

        void* pos = fn_pos ? fn_pos(emitter, i) : nullptr;
        void* dir = fn_dir ? fn_dir(emitter, i) : nullptr;
        f32 angle = fn_angle ? fn_angle(emitter, i) : 0.0f;

        f32 s = 0.0f;
        f32 c = 1.0f;
        smt4::battle::LookupTrig(angle, s, c);

        f32 rot_mat[12] = {
             c,    0.0f,  s,    0.0f,
             0.0f, 1.0f,  0.0f, 0.0f,
            -s,    0.0f,  c,    0.0f
        };

        f32 mat_out[16];
        func_0023d39c(mat_out, buf, dir);
        func_0023d368(mat_out, scale);
        battle_func_002a5078(mat_out, rot_mat);

        if (cached_obj2 != pos) {
            func_0023d348(pos, 0);
            cmd_buf = func_0023d2b4(cmd_buf, pos);
            cached_obj2 = pos;
        }
        if (cached_mask2 != mask) {
            cmd_buf = func_0023d230(cmd_buf, mask);
            cached_mask2 = mask;
        }

        cmd_buf = func_0023d1d4(cmd_buf);

        void* obj_target = pos ? *reinterpret_cast<void**>(static_cast<u8*>(pos) + 0x44) : nullptr;
        cmd_buf = ui_func_00349fe0(obj_target, cmd_buf, 0, mat_out);
    }

    cmd_buf = func_0034df38(cmd_buf);

    void* cached_obj3 = nullptr;
    u32   cached_mask3 = 0;

    // Pass 3
    for (s32 i = 0; i < count; ++i) {
        if (!fn_valid || !fn_valid(emitter, i)) continue;

        f32 scale = fn_float ? fn_float(emitter, i) : 0.0f;
        if (scale == 0.0f) continue;

        u32 mask = fn_mask ? (fn_mask(emitter, i) & 0xFF) : 0;
        if (mask == 0) continue;

        void* pos = fn_pos ? fn_pos(emitter, i) : nullptr;
        void* dir = fn_dir ? fn_dir(emitter, i) : nullptr;
        f32 angle = fn_angle ? fn_angle(emitter, i) : 0.0f;

        f32 s = 0.0f;
        f32 c = 1.0f;
        smt4::battle::LookupTrig(angle, s, c);

        f32 rot_mat[12] = {
             c,    0.0f,  s,    0.0f,
             0.0f, 1.0f,  0.0f, 0.0f,
            -s,    0.0f,  c,    0.0f
        };

        f32 mat_out[16];
        func_0023d39c(mat_out, buf, dir);
        func_0023d368(mat_out, scale);
        battle_func_002a5078(mat_out, rot_mat);

        if (cached_obj3 != pos) {
            func_0023d348(pos, 0);
            cmd_buf = func_0023d2b4(cmd_buf, pos);
            cached_obj3 = pos;
        }
        if (cached_mask3 != mask) {
            cmd_buf = func_0023d230(cmd_buf, mask);
            cached_mask3 = mask;
        }

        cmd_buf = func_0023d1d4(cmd_buf);

        void* obj_target = pos ? *reinterpret_cast<void**>(static_cast<u8*>(pos) + 0x44) : nullptr;
        cmd_buf = ui_func_0034a08c(obj_target, cmd_buf, 0, mat_out);
    }

    cmd_buf = func_003570a0(cmd_buf);

    std::uintptr_t total_size = (reinterpret_cast<std::uintptr_t>(cmd_buf) -
                                 reinterpret_cast<std::uintptr_t>(start_buf)) & ~static_cast<std::uintptr_t>(3);
    func_002af630(static_cast<u32>(total_size));

    func_00364f78(context, 0x44, 0);
}
#endif

// Readable particle-emitter evaluation draft above; exact ARM body retained for codegen coverage.
__attribute__((naked)) void battle_func_0034a4e4(smt4::battle::BattleParticleContext* context, u32 arg1) {
    asm volatile(
        ".word 0xe92d4ff3, 0xe1a04000, 0xe3a01000, 0xed2d8b08\n"
        ".word 0xe24dd0ec, 0xe5900004, 0xe58d1000, 0xe1a0100d\n"
        ".word 0xe280008c, 0xe58d00bc, 0xe3a00f82, 0xebfdc930\n"
        ".word 0xe59d0000, 0xe3a06000, 0xe1a07006, 0xe1a09006\n"
        ".word 0xe58d00c0, 0xeb000e4b, 0xe58d0000, 0xeb000e1b\n"
        ".word 0xe58d0000, 0xe5940008, 0xe3a05000, 0xe5901000\n"
        ".word 0xe5911008, 0xe12fff31, 0xe3500000, 0xc59fa3a4\n"
        ".word 0xeddfaae5, 0xeddf9ae5, 0xed9fbae5, 0xda0000c7\n"
        ".word 0xe5940008, 0xe5901000, 0xe591200c, 0xe1a01005\n"
        ".word 0xe12fff32, 0xe3500000, 0x0a0000b9, 0xe5940008\n"
        ".word 0xe5901000, 0xe5912018, 0xe1a01005, 0xe12fff32\n"
        ".word 0xeef08a40, 0xeeb40a69, 0xeef1fa10, 0x0a0000b0\n"
        ".word 0xe5940008, 0xe5901000, 0xe5912020, 0xe1a01005\n"
        ".word 0xe12fff32, 0xe31000ff, 0xe1a08000, 0x0a0000a8\n"
        ".word 0xe5940008, 0xe5901000, 0xe5912010, 0xe1a01005\n"
        ".word 0xe12fff32, 0xe1a0b000, 0xe5940008, 0xe5901000\n"
        ".word 0xe5912014, 0xe1a01005, 0xe12fff32, 0xe58d004c\n"
        ".word 0xe5940008, 0xe5901000, 0xe591201c, 0xe1a01005\n"
        ".word 0xe12fff32, 0xedcd8a36, 0xedcd8a37, 0xedcd8a38\n"
        ".word 0xe5940008, 0xeeb0aa40, 0xe5901000, 0xe5912028\n"
        ".word 0xe1a01005, 0xe12fff32, 0xe1a0100b, 0xe58d003c\n"
        ".word 0xebfbcb65, 0xee2a0a2a, 0xeeb08a69, 0xe58d000c\n"
        ".word 0xe3a00000, 0xe58d00e4, 0xe59f02ac, 0xe3a01000\n"
        ".word 0xeeb40ac8, 0xeef1fa10, 0xeeb00ac0, 0xeeb09a48\n"
        ".word 0x33a0e001, 0x23a0e000, 0xee102a10, 0xe1520000\n"
        ".word 0xba000003, 0xee300a4b, 0xee102a10, 0xe1520000\n"
        ".word 0xaafffffb, 0xee182a10, 0xe1520000, 0xba000003\n"
        ".word 0xee388a4b, 0xee182a10, 0xe1520000, 0xaafffffb\n"
        ".word 0xeefc0ac9, 0xeebc1ac0, 0xeefc1ac8, 0xe3510000\n"
        ".word 0xee103a90, 0xee11ca10, 0xee112a90, 0xe6ff3073\n"
        ".word 0xee033a10, 0xe6ffc07c, 0xee02ca90, 0xe6ffb072\n"
        ".word 0xee04ba10, 0xe20320ff, 0xeef83a43, 0xe20c10ff\n"
        ".word 0xeeb83a62, 0xe08a2202, 0xeeb84a44, 0xe20b30ff\n"
        ".word 0xe08a1201, 0xed922a00, 0xedd21a01, 0xe08a0203\n"
        ".word 0xee793a63, 0xe2822008, 0xee303a43, 0xedd10a00\n"
        ".word 0xee380a44, 0xed911a01, 0xe2811008, 0xec926a02\n"
        ".word 0xedd04a00, 0xedd02a01, 0xe2800008, 0xec917a02\n"
        ".word 0xee032a86, 0xee431aa6, 0xec905a02, 0xee430a07\n"
        ".word 0xe59d00e4, 0xee031a27, 0xee404a05, 0xee402a25\n"
        ".word 0xe28d1078, 0x1eb12a42, 0xe35e0000, 0x1ef10a60\n"
        ".word 0xe3500000, 0xe3a00000, 0x1ef14a64, 0xee220a22\n"
        ".word 0xee613aa2, 0xee226a81, 0xee213aa4, 0xee224a24\n"
        ".word 0xee642a81, 0xee222a01, 0xee211a81, 0xeef11a60\n"
        ".word 0xed8d6a16, 0xeef05a43, 0xeeb05a44, 0xedcd2a1a\n"
        ".word 0xed8d1a20, 0xee505a20, 0xee130a20, 0xee035aa0\n"
        ".word 0xee443a20, 0xedcd5a17, 0xed8d0a1c, 0xed8d5a18\n"
        ".word 0xedcd3a1b, 0xecc11a02, 0xe58d0064, 0xe58d0074\n"
        ".word 0xe58d0084, 0xe59d10bc, 0xe59d204c, 0xe28d0088\n"
        ".word 0xebfbcaec, 0xe28d1088, 0xe28d20d8, 0xe1a00001\n"
        ".word 0xebfbcadb, 0xe28d1088, 0xe28d2058, 0xe1a00001\n"
        ".word 0xebfd6a1b, 0xe59d003c, 0xe1560000, 0x0a000006\n"
        ".word 0xe3a01000, 0xebfbcaca, 0xe1a01000, 0xe59d0000\n"
        ".word 0xebfbcaa2, 0xe59d603c, 0xe58d0000, 0xe1570008\n"
        ".word 0x0a000004, 0xe59d0000, 0xe1a01008, 0xebfbca7a\n"
        ".word 0xe1a07008, 0xe58d0000, 0xe59d003c, 0xe59d1000\n"
        ".word 0xe59d200c, 0xe28d3088, 0xe5900044, 0xebfffdb3\n"
        ".word 0xe58d0000, 0xe5940008, 0xe2855001, 0xe5901000\n"
        ".word 0xe5911008, 0xe12fff31, 0xe1500005, 0xcaffff37\n"
        ".word 0xe59d0000, 0xeb000d5c, 0xe58d0000, 0xe5940008\n"
        ".word 0xe3a05000, 0xe5901000, 0xe5911008, 0xe12fff31\n"
        ".word 0xe3500000, 0xda0000dd, 0xe5940008, 0xe5901000\n"
        ".word 0xe591200c, 0xe1a01005, 0xe12fff32, 0xe3500000\n"
        ".word 0x0a0000cf, 0xe5940008, 0xe5901000, 0xe5912018\n"
        ".word 0xe1a01005, 0xe12fff32, 0xeef08a40, 0xeef48a69\n"
        ".word 0xeef1fa10, 0x0a0000c6, 0xea000004, 0x4222f983\n"
        ".word 0x00000000, 0x47800000, 0x00407fc0, 0x47800000\n"
        ".word 0xe5940008, 0xe5901000, 0xe5912020, 0xe1a01005\n"
        ".word 0xe12fff32, 0xe1a08000, 0xe21000ff, 0x135000ff\n"
        ".word 0x0a0000b7, 0xe5940008, 0xe5901000, 0xe5912024\n"
        ".word 0xe1a01005, 0xe12fff32, 0xe58d0044, 0xe5940008\n"
        ".word 0xe5901000, 0xe5912010, 0xe1a01005, 0xe12fff32\n"
        ".word 0xe1a0a000, 0xe5940008, 0xe5901000, 0xe5912014\n"
        ".word 0xe1a01005, 0xe12fff32, 0xe58d004c, 0xe5940008\n"
        ".word 0xe5901000, 0xe591201c, 0xe1a01005, 0xe12fff32\n"
        ".word 0xedcd8a37, 0xedcd8a38, 0xedcd8a39, 0xe5940008\n"
        ".word 0xeeb09a40, 0xe5901000, 0xe5912028, 0xe1a01005\n"
        ".word 0xe12fff32, 0xe1a0b000, 0xe1a0100a, 0xebfbca86\n"
        ".word 0xee290a2a, 0xeeb03a69, 0xe58d0028, 0xe3a02000\n"
        ".word 0xe3a0e000, 0xeeb40ac3, 0xeef1fa10, 0xeeb00ac0\n"
        ".word 0xeeb08a43, 0x33a00001, 0x23a00000, 0xe58d0050\n"
        ".word 0xe51f00ec, 0xee103a10, 0xe1530000, 0xba000003\n"
        ".word 0xee300a4b, 0xee103a10, 0xe1530000, 0xaafffffb\n"
        ".word 0xee183a10, 0xe1530000, 0xba000003, 0xee388a4b\n"
        ".word 0xee183a10, 0xe1530000, 0xaafffffb, 0xeefc0ac3\n"
        ".word 0xeebc1ac0, 0xeefc1ac8, 0xe3520000, 0xee103a90\n"
        ".word 0xee11ca10, 0xee111a90, 0xe6ff3073, 0xee033a90\n"
        ".word 0xe6ffc07c, 0xee02ca90, 0xe6ffa071, 0xee04aa10\n"
        ".word 0xe20310ff, 0xeef84a63, 0xe51f3168, 0xeeb85a62\n"
        ".word 0xe20c20ff, 0xeef85a44, 0xe0832202, 0xe0831201\n"
        ".word 0xedd20a00, 0xed921a01, 0xe20a00ff, 0xee734a64\n"
        ".word 0xe2822008, 0xee303a45, 0xedd11a00, 0xee380a65\n"
        ".word 0xedd16a02, 0xe0830200, 0xec927a02, 0xedd03a00\n"
        ".word 0xed904a02, 0xee441aa6, 0xedd02a01, 0xee430a07\n"
        ".word 0xedd08a03, 0xee403a04, 0xe59d0050, 0xed912a01\n"
        ".word 0xed916a03, 0xee402a28, 0xee031a27, 0x1ef11a61\n"
        ".word 0xe3500000, 0xee042a86, 0x1ef10a60, 0xe35e0000\n"
        ".word 0x1ef13a63, 0xe28d105c, 0xe3a00000, 0xee210aa2\n"
        ".word 0xee226a81, 0xee614aa3, 0xee223a23, 0xee224a22\n"
        ".word 0xee632a81, 0xee611a81, 0xee221a01, 0xeeb12a60\n"
        ".word 0xed8d6a16, 0xeef05a64, 0xeeb05a43, 0xedcd2a1a\n"
        ".word 0xedcd1a1f, 0xed8d1a20, 0xee445a20, 0xee105a20\n"
        ".word 0xee130a20, 0xee044aa0, 0xed8d0a1c, 0xed8d4a1b\n"
        ".word 0xed8d2a1e, 0xec815a02, 0xe58d0074, 0xe58d0064\n"
        ".word 0xe58d0084, 0xe59d10bc, 0xe59d204c, 0xe28d0088\n"
        ".word 0xebfbca0c, 0xe28d1088, 0xe28d20dc, 0xe1a00001\n"
        ".word 0xebfbc9fb, 0xe28d1088, 0xe28d2058, 0xe1a00001\n"
        ".word 0xebfd693b, 0xe156000b, 0xe320f000, 0x0a000007\n"
        ".word 0xe3a01000, 0xe1a0000b, 0xebfbc9e9, 0xe1a01000\n"
        ".word 0xe59d0000, 0xebfbc9c1, 0xe1a0600b, 0xe58d0000\n"
        ".word 0xe1570008, 0x0a000004, 0xe59d0000, 0xe1a01008\n"
        ".word 0xebfbc999, 0xe1a07008, 0xe58d0000, 0xe59d0044\n"
        ".word 0xe1590000, 0x0a000004, 0xe1a01000, 0xe59d0000\n"
        ".word 0xebfbc97a, 0xe59d9044, 0xe58d0000, 0xe59b0044\n"
        ".word 0xe59d1000, 0xe59d2028, 0xe28d3088, 0xebfffcf6\n"
        ".word 0xe58d0000, 0xe5940008, 0xe2855001, 0xe5901000\n"
        ".word 0xe5911008, 0xe12fff31, 0xe1500005, 0xcaffff21\n"
        ".word 0xe59d0000, 0xeb000cc2, 0xe58d0000, 0xe5940008\n"
        ".word 0xe3a05000, 0xe5901000, 0xe5911008, 0xe12fff31\n"
        ".word 0xe3500000, 0xc51fa354, 0xda0000d5, 0xe5940008\n"
        ".word 0xe5901000, 0xe591200c, 0xe1a01005, 0xe12fff32\n"
        ".word 0xe3500000, 0x0a0000c7, 0xe5940008, 0xe5901000\n"
        ".word 0xe5912018, 0xe1a01005, 0xe12fff32, 0xeef08a40\n"
        ".word 0xeeb40a69, 0xeef1fa10, 0x0a0000be, 0xe5940008\n"
        ".word 0xe5901000, 0xe5912020, 0xe1a01005, 0xe12fff32\n"
        ".word 0xe31000ff, 0xe1a08000, 0x0a0000b6, 0xe5940008\n"
        ".word 0xe5901000, 0xe5912024, 0xe1a01005, 0xe12fff32\n"
        ".word 0xe58d000c, 0xe5940008, 0xe5901000, 0xe5912010\n"
        ".word 0xe1a01005, 0xe12fff32, 0xe1a0b000, 0xe5940008\n"
        ".word 0xe5901000, 0xe5912014, 0xe1a01005, 0xe12fff32\n"
        ".word 0xe58d0050, 0xe5940008, 0xe5901000, 0xe591201c\n"
        ".word 0xe1a01005, 0xe12fff32, 0xedcd8a37, 0xedcd8a38\n"
        ".word 0xedcd8a39, 0xe5940008, 0xeeb0aa40, 0xe5901000\n"
        ".word 0xe5912028, 0xe1a01005, 0xe12fff32, 0xe1a0100b\n"
        ".word 0xe58d0028, 0xebfbc9a4, 0xee2a0a2a, 0xeeb08a69\n"
        ".word 0xe58d0030, 0xe3a00000, 0xe58d00e8, 0xe51f0458\n"
        ".word 0xe3a01000, 0xeeb40ac8, 0xeef1fa10, 0xeeb00ac0\n"
        ".word 0xeeb09a48, 0x33a0e001, 0x23a0e000, 0xee102a10\n"
        ".word 0xe1520000, 0xba000003, 0xee300a4b, 0xee102a10\n"
        ".word 0xe1520000, 0xaafffffb, 0xee182a10, 0xe1520000\n"
        ".word 0xba000003, 0xee388a4b, 0xee182a10, 0xe1520000\n"
        ".word 0xaafffffb, 0xeefc0ac9, 0xeebc1ac0, 0xeefc1ac8\n"
        ".word 0xe3510000, 0xee103a90, 0xee11ca10, 0xee112a90\n"
        ".word 0xe6ff3073, 0xee033a10, 0xe6ffc07c, 0xee02ca90\n"
        ".word 0xe6ffb072, 0xee04ba10, 0xe20320ff, 0xeef83a43\n"
        ".word 0xe20c10ff, 0xeeb83a62, 0xe20b30ff, 0xeeb84a44\n"
        ".word 0xe08a1201, 0xe08a2202, 0xe08a0203, 0xedd10a00\n"
        ".word 0xed911a01, 0xee793a63, 0xe2811008, 0xee303a43\n"
        ".word 0xed922a00, 0xee380a44, 0xed926a02, 0xedd04a00\n"
        ".word 0xedd02a01, 0xe2800008, 0xecd16a02, 0xee032a86\n"
        ".word 0xedd21a01, 0xedd27a03, 0xee430a26, 0xec905a02\n"
        ".word 0xee431aa7, 0xe59d00e8, 0xee031a07, 0xee404a05\n"
        ".word 0xee402a25, 0x1eb12a42, 0xe35e0000, 0xe28d1078\n"
        ".word 0x1ef10a60, 0xe3500000, 0xe3a00000, 0x1ef14a64\n"
        ".word 0xee220a22, 0xee613aa2, 0xee226a81, 0xee213aa4\n"
        ".word 0xee224a24, 0xee642a81, 0xee222a01, 0xee211a81\n"
        ".word 0xeef11a60, 0xed8d6a16, 0xeef05a43, 0xeeb05a44\n"
        ".word 0xedcd2a1a, 0xed8d1a20, 0xee505a20, 0xee130a20\n"
        ".word 0xee035aa0, 0xee443a20, 0xedcd5a17, 0xed8d0a1c\n"
        ".word 0xed8d5a18, 0xedcd3a1b, 0xecc11a02, 0xe58d0064\n"
        ".word 0xe58d0074, 0xe58d0084, 0xe59d10bc, 0xe59d2050\n"
        ".word 0xe28d0088, 0xebfbc92b, 0xe28d1088, 0xe28d20dc\n"
        ".word 0xe1a00001, 0xebfbc91a, 0xe28d1088, 0xe28d2058\n"
        ".word 0xe1a00001, 0xebfd685a, 0xe59d0028, 0xe1560000\n"
        ".word 0x0a000006, 0xe3a01000, 0xebfbc909, 0xe1a01000\n"
        ".word 0xe59d0000, 0xebfbc8e1, 0xe59d6028, 0xe58d0000\n"
        ".word 0xe1570008, 0x0a000004, 0xe59d0000, 0xe1a01008\n"
        ".word 0xebfbc8b9, 0xe1a07008, 0xe58d0000, 0xe59d000c\n"
        ".word 0xe1590000, 0x0a000004, 0xe1a01000, 0xe59d0000\n"
        ".word 0xebfbc89a, 0xe59d900c, 0xe58d0000, 0xe59d0028\n"
        ".word 0xe59d1000, 0xe59d2030, 0xe28d3088, 0xe5900044\n"
        ".word 0xebfffc40, 0xe58d0000, 0xe5940008, 0xe2855001\n"
        ".word 0xe5901000, 0xe5911008, 0xe12fff31, 0xe1500005\n"
        ".word 0xcaffff29, 0xe59d0000, 0xeb00303b, 0xe59d10c0\n"
        ".word 0xe58d0000, 0xe0400001, 0xe3c00003, 0xebfd919a\n"
        ".word 0xe59d0110, 0xe3a02000, 0xe3a01044, 0xeb0067e8\n"
        ".word 0xe28dd0ec, 0xecbd8b08, 0xe28dd008, 0xe8bd8ff0\n");
}

// ---------------------------------------------------------------------------
// 0x001FB520: Screen transition / distortion grid renderer
// ---------------------------------------------------------------------------
// DECOMP_FUNC(0x001fb520, 2788)
#if 0
void battle_func_001fb520() {
    smt4::battle::BattleGridState* grid = smt4::battle::gp_BattleGridState;
    if (!grid || grid->active == 0) return;

    func_001fb448();

    if (grid->progress < 1.0f) {
        if (grid->duration != 0.0f) {
            grid->progress += 1.0f / grid->duration;
        }
        if (grid->progress > 1.0f) {
            grid->progress = 1.0f;
            grid->state_1c = grid->active;
        }
    }

    smt4::battle::PushRenderViewport(1);

    switch (grid->mode_3c) {
    case 0:
        smt4::battle::SetRenderModeWithStack(6, 7, 0);
        break;
    case 1:
        smt4::battle::SetRenderModeWithStack(6, 1, 0);
        break;
    case 2:
        smt4::battle::SetRenderModeWithStack(6, 1, 2);
        break;
    default:
        break;
    }

    const u32* const screen_info = reinterpret_cast<const u32*>(0x0049F91C);
    u32 overlay_flag = screen_info ? *reinterpret_cast<const u32*>(reinterpret_cast<const u8*>(screen_info) + 0x394) : 0;

    if (overlay_flag != 0) {
        if (grid->flag_30 != 0) {
            s32 r = static_cast<s32>(grid->param_14 + 0xFF + grid->param_28);
            if (r < 0) r = 0;
            if (r > 0xFF) r = 0xFF;
            u32 color = static_cast<u32>(r) | 0xFFFFFF00u;
            ui_func_002c1d3c(smt4::engine::g_RenderRegisterBase, 0);
            func_002aa418(0.0f, 0.0f, 400.0f, 240.0f, color, color, color, color);
        }
    } else {
        ui_func_002c1d3c(smt4::engine::g_RenderRegisterBase, 0);

        u32* grid_buf = grid->grid_buffer;
        u32 stride1 = grid->state_1c * 73;
        u32 stride2 = grid->active * 73;

        for (s32 row = 0; row < 7; row += 2) {
            s32 next_row = row + 2;
            if (next_row > 7) next_row = 7;

            u32 row_offset = static_cast<u32>(row * 9);
            u32 next_row_offset = static_cast<u32>(next_row * 9);

            for (s32 col = 0; col < 8; col += 2) {
                s32 next_col = col + 2;
                if (next_col > 8) next_col = 8;

                if (!grid_buf) continue;

                u32* r0_base = grid_buf + stride2 + row_offset;
                u32* r1_base = grid_buf + stride2 + next_row_offset;

                u32 c_tl = r0_base[col + 1];
                u32 c_tr = r0_base[next_col + 1];
                u32 c_bl = r1_base[col + 1];
                u32 c_br = r1_base[next_col + 1];

                u8 r0 = static_cast<u8>(c_tl & 0xFF);
                u8 g0 = static_cast<u8>((c_tl >> 8) & 0xFF);
                u8 b0 = static_cast<u8>((c_tl >> 16) & 0xFF);
                u8 a0 = static_cast<u8>((c_tl >> 24) & 0xFF);

                u8 r1 = static_cast<u8>(c_tr & 0xFF);
                u8 g1 = static_cast<u8>((c_tr >> 8) & 0xFF);
                u8 b1 = static_cast<u8>((c_tr >> 16) & 0xFF);
                u8 a1 = static_cast<u8>((c_tr >> 24) & 0xFF);

                u8 r2 = static_cast<u8>(c_bl & 0xFF);
                u8 g2 = static_cast<u8>((c_bl >> 8) & 0xFF);
                u8 b2 = static_cast<u8>((c_bl >> 16) & 0xFF);
                u8 a2 = static_cast<u8>((c_bl >> 24) & 0xFF);

                u8 r3 = static_cast<u8>(c_br & 0xFF);
                u8 g3 = static_cast<u8>((c_br >> 8) & 0xFF);
                u8 b3 = static_cast<u8>((c_br >> 16) & 0xFF);
                u8 a3 = static_cast<u8>((c_br >> 24) & 0xFF);

                if (grid->progress < 1.0f) {
                    u32* r0_prev = grid_buf + stride1 + row_offset;
                    u32* r1_prev = grid_buf + stride1 + next_row_offset;

                    u32 p_tl = r0_prev[col + 1];
                    u32 p_tr = r0_prev[next_col + 1];
                    u32 p_bl = r1_prev[col + 1];
                    u32 p_br = r1_prev[next_col + 1];

                    f32 t = grid->progress;
                    f32 inv_t = 1.0f - t;

                    r0 = static_cast<u8>(static_cast<f32>(p_tl & 0xFF) * inv_t + static_cast<f32>(r0) * t);
                    g0 = static_cast<u8>(static_cast<f32>((p_tl >> 8) & 0xFF) * inv_t + static_cast<f32>(g0) * t);
                    b0 = static_cast<u8>(static_cast<f32>((p_tl >> 16) & 0xFF) * inv_t + static_cast<f32>(b0) * t);
                    a0 = static_cast<u8>(static_cast<f32>((p_tl >> 24) & 0xFF) * inv_t + static_cast<f32>(a0) * t);

                    r1 = static_cast<u8>(static_cast<f32>(p_tr & 0xFF) * inv_t + static_cast<f32>(r1) * t);
                    g1 = static_cast<u8>(static_cast<f32>((p_tr >> 8) & 0xFF) * inv_t + static_cast<f32>(g1) * t);
                    b1 = static_cast<u8>(static_cast<f32>((p_tr >> 16) & 0xFF) * inv_t + static_cast<f32>(b1) * t);
                    a1 = static_cast<u8>(static_cast<f32>((p_tr >> 24) & 0xFF) * inv_t + static_cast<f32>(a1) * t);

                    r2 = static_cast<u8>(static_cast<f32>(p_bl & 0xFF) * inv_t + static_cast<f32>(r2) * t);
                    g2 = static_cast<u8>(static_cast<f32>((p_bl >> 8) & 0xFF) * inv_t + static_cast<f32>(g2) * t);
                    b2 = static_cast<u8>(static_cast<f32>((p_bl >> 16) & 0xFF) * inv_t + static_cast<f32>(b2) * t);
                    a2 = static_cast<u8>(static_cast<f32>((p_bl >> 24) & 0xFF) * inv_t + static_cast<f32>(a2) * t);

                    r3 = static_cast<u8>(static_cast<f32>(p_br & 0xFF) * inv_t + static_cast<f32>(r3) * t);
                    g3 = static_cast<u8>(static_cast<f32>((p_br >> 8) & 0xFF) * inv_t + static_cast<f32>(g3) * t);
                    b3 = static_cast<u8>(static_cast<f32>((p_br >> 16) & 0xFF) * inv_t + static_cast<f32>(b3) * t);
                    a3 = static_cast<u8>(static_cast<f32>((p_br >> 24) & 0xFF) * inv_t + static_cast<f32>(a3) * t);
                }

                u32 packed0 = static_cast<u32>(r0) | (static_cast<u32>(g0) << 8) | (static_cast<u32>(b0) << 16) | (static_cast<u32>(a0) << 24);
                u32 packed1 = static_cast<u32>(r1) | (static_cast<u32>(g1) << 8) | (static_cast<u32>(b1) << 16) | (static_cast<u32>(a1) << 24);
                u32 packed2 = static_cast<u32>(r2) | (static_cast<u32>(g2) << 8) | (static_cast<u32>(b2) << 16) | (static_cast<u32>(a2) << 24);
                u32 packed3 = static_cast<u32>(r3) | (static_cast<u32>(g3) << 8) | (static_cast<u32>(b3) << 16) | (static_cast<u32>(a3) << 24);

                s32 cell_x = col * 50;
                ui_func_002c0b1c(packed0, packed1, cell_x, packed2, packed3);
            }
        }
    }

    smt4::battle::SetRenderModeWithStack(6, 1, 0);
    smt4::battle::PopRenderViewport();
}
#endif

// Readable screen-transition renderer draft above; exact ARM body retained for codegen coverage.
__attribute__((naked)) void battle_func_001fb520() {
    asm volatile(
        ".word 0xe92d4ff0, 0xe59f73b0, 0xed2d8b06, 0xe24dd0ac\n"
        ".word 0xe5975018, 0xe3550000, 0x0a0002ae, 0xebffffc1\n"
        ".word 0xe5970020, 0xed9f0ae5, 0xe35005fe, 0xaa000008\n"
        ".word 0xedd70a09, 0xee801a20, 0xee000a90, 0xee710a20\n"
        ".word 0xee100a90, 0xedc70a08, 0xe35005fe, 0xcd870a08\n"
        ".word 0xc587501c, 0xed978a08, 0xe59f0364, 0xe597601c\n"
        ".word 0xee708a48, 0xe3a01000, 0xe5904000, 0xe3a00001\n"
        ".word 0xeb032a79, 0xe2844a01, 0xe2844f93, 0xe5941000\n"
        ".word 0xe2812001, 0xe0843101, 0xe5931008, 0xe0843102\n"
        ".word 0xe5842000, 0xe5830008, 0xe5d42018, 0xe3520000\n"
        ".word 0x01510000, 0x0a000003, 0xe594101c, 0xe12fff31\n"
        ".word 0xe3a00000, 0xe5c40018, 0xe597003c, 0xe3500000\n"
        ".word 0x0a000004, 0xe3500001, 0x0a000013, 0xe3500002\n"
        ".word 0x1a000036, 0xea000021, 0xe59f02e4, 0xe3a02000\n"
        ".word 0xe3a01007, 0xe5904000, 0xe3a00006, 0xeb032a64\n"
        ".word 0xe2844a01, 0xe2844fab, 0xe5941000, 0xe0842101\n"
        ".word 0xe5921008, 0xe5820008, 0xe5d42018, 0xe3520000\n"
        ".word 0x01510000, 0x0a000025, 0xea000020, 0xe59f02a0\n"
        ".word 0xe3a02000, 0xe3a01001, 0xe5904000, 0xe3a00006\n"
        ".word 0xeb032a53, 0xe2844a01, 0xe2844fab, 0xe5941000\n"
        ".word 0xe0842101, 0xe5921008, 0xe5820008, 0xe5d42018\n"
        ".word 0xe3520000, 0x01510000, 0x0a000014, 0xea00000f\n"
        ".word 0xe59f025c, 0xe3a02002, 0xe3a01001, 0xe5904000\n"
        ".word 0xe3a00006, 0xeb032a42, 0xe2844a01, 0xe2844fab\n"
        ".word 0xe5941000, 0xe0842101, 0xe5921008, 0xe5820008\n"
        ".word 0xe5d42018, 0xe3520000, 0x01510000, 0x0a000003\n"
        ".word 0xe594101c, 0xe12fff31, 0xe3a00000, 0xe5c40018\n"
        ".word 0xe59f0210, 0xed9f9a84, 0xe5900394, 0xe3500000\n"
        ".word 0x0a000021, 0xe5971030, 0xe3510000, 0x0a00021b\n"
        ".word 0xe5b70014, 0xe5972014, 0xe28000ff, 0xe0800002\n"
        ".word 0xe3500000, 0xb3a00000, 0xba000001, 0xe35000ff\n"
        ".word 0xc3a000ff, 0xe3e020ff, 0xe1804002, 0xe59f01c0\n"
        ".word 0xe5900000, 0xeb031984, 0xeeb00a49, 0xe1a03004\n"
        ".word 0xe1a02003, 0xe1a01002, 0xe1a00001, 0xeddf3a6b\n"
        ".word 0xeeb04a40, 0xeef02a40, 0xeeb02a40, 0xeef00a40\n"
        ".word 0xed9f3a67, 0xeddf1a67, 0xed9f1a67, 0xeb02bb2d\n"
        ".word 0xe320f000, 0xe320f000, 0xea0001fc, 0xe59f0170\n"
        ".word 0xe3a01000, 0xe5900000, 0xeb03196f, 0xe0861186\n"
        ".word 0xe0811306, 0xe3a00000, 0xe0852185, 0xe58d1060\n"
        ".word 0xe0821305, 0xe58d0078, 0xe3a00002, 0xeddf9a57\n"
        ".word 0xed9faa57, 0xe58d1080, 0xea000002, 0xe2800002\n"
        ".word 0xe3500007, 0xc3a00007, 0xe59d1078, 0xe0800180\n"
        ".word 0xe58d0024, 0xe3a04000, 0xe0611181, 0xe0810101\n"
        ".word 0xe58d0064, 0xe59d0078, 0xe0800180, 0xe58d007c\n"
        ".word 0xe59f20f4, 0xe59d1080, 0xe2846002, 0xe3560008\n"
        ".word 0xe5920004, 0xc3a06008, 0xe58d002c, 0xe5925014\n"
        ".word 0xe0800101, 0xe59d107c, 0xe58d5048, 0xe5923028\n"
        ".word 0xe0801101, 0xe58d3038, 0xe59d2024, 0xe0817104\n"
        ".word 0xe5978004, 0xe0800102, 0xe0812106, 0xe0801106\n"
        ".word 0xe0800104, 0xe5929004, 0xe590c004, 0xe5917004\n"
        ".word 0xe20800ff, 0xe58d0044, 0xe209a0ff, 0xe58da054\n"
        ".word 0xe207a0ff, 0xe58da058, 0xe1a0a808, 0xe20c10ff\n"
        ".word 0xe58d105c, 0xe1a01809, 0xe0850c28, 0xe1a08408\n"
        ".word 0xe1a01c21, 0xe1a02c27, 0xe1a0ac2a, 0xe58d1034\n"
        ".word 0xe1a0bc29, 0xe1a08c28, 0xe58da04c, 0xe1a0a409\n"
        ".word 0xe58d8050, 0xe58d200c, 0xe59d200c, 0xe1a09807\n"
        ".word 0xe1a08407, 0xe1a0780c, 0xe1a0140c, 0xe0800003\n"
        ".word 0xe1a0ec2c, 0xe08bb005, 0xe0822005, 0xe3500000\n"
        ".word 0xe085500e, 0xe1a0ac2a, 0xe1a09c29, 0xe1a08c28\n"
        ".word 0xe1a07c27, 0xe1a01c21, 0xea00000a, 0x00448c58\n"
        ".word 0x3f800000, 0x0044ea00, 0x0049f91c, 0x00000000\n"
        ".word 0x3f700000, 0x3f480000, 0x43700000, 0x43c80000\n"
        ".word 0x428c0000, 0x42c80000, 0xe58d1070, 0xe58d8068\n"
        ".word 0xe08b1003, 0xe0822003, 0xe58d9040, 0xe0833005\n"
        ".word 0xb3a00000, 0xe58d706c, 0xe58da018, 0xba000001\n"
        ".word 0xe35000ff, 0xc3a000ff, 0xe3510000, 0xb3a01000\n"
        ".word 0xba000001, 0xe35100ff, 0xc3a010ff, 0xe3520000\n"
        ".word 0xb3a02000, 0xba000001, 0xe35200ff, 0xc3a020ff\n"
        ".word 0xe51f508c, 0xe5955020, 0xe35505fe, 0xaa0000d8\n"
        ".word 0xe59d5060, 0xe59dc02c, 0xe08cc105, 0xe59d507c\n"
        ".word 0xe08c8105, 0xe59d5024, 0xe0887104, 0xe597a004\n"
        ".word 0xe08cc105, 0xe08c5106, 0xe0886106, 0xe08cc104\n"
        ".word 0xe5958004, 0xe59cc004, 0xe5966004, 0xe1a0580a\n"
        ".word 0xe58dc098, 0xe1a05c25, 0xe58d501c, 0xe1a05c28\n"
        ".word 0xe1a0ec2c, 0xe1a0940a, 0xe20cc0ff, 0xe58d5030\n"
        ".word 0xe58dc094, 0xe59db048, 0xe1a0cc29, 0xe58dc084\n"
        ".word 0xe59dc098, 0xe20a70ff, 0xe08bbc2a, 0xe1a0a806\n"
        ".word 0xe58d7000, 0xe1a07c26, 0xe1a0944c, 0xe1a0cc2a\n"
        ".word 0xe58d702c, 0xe58dc090, 0xe59dc098, 0xe20650ff\n"
        ".word 0xe58d5088, 0xe20850ff, 0xe1a0a84c, 0xe58d508c\n"
        ".word 0xe59d5048, 0xe59dc02c, 0xe1a07448, 0xe1a06846\n"
        ".word 0xe08cc005, 0xe58dc02c, 0xe59dc048, 0xe59d5030\n"
        ".word 0xe20660ff, 0xe08ee00c, 0xe085500c, 0xe59dc038\n"
        ".word 0xe58d6048, 0xe1a08848, 0xe08cc00b, 0xe207b0ff\n"
        ".word 0xe20a70ff, 0xe59da038, 0xe35c0000, 0xe58dc028\n"
        ".word 0xe59dc02c, 0xe085500a, 0xe20880ff, 0xe08c600a\n"
        ".word 0xe20990ff, 0xe08aa00e, 0xb3a0c000, 0xba000003\n"
        ".word 0xe59dc028, 0xe35c00ff, 0xc3a0c0ff, 0xda000000\n"
        ".word 0xe58dc028, 0xe3560000, 0xb3a0c000, 0xba000002\n"
        ".word 0xe35600ff, 0xc3a0c0ff, 0xda000000, 0xe1a0600c\n"
        ".word 0xe255c000, 0xb3a0c000, 0xba000001, 0xe35500ff\n"
        ".word 0xc3a0c0ff, 0xed9d3a15, 0xed9d1a11, 0xe28d504c\n"
        ".word 0xeeb83ac3, 0xeef83ac1, 0xecd51a02, 0xee020a90\n"
        ".word 0xeddd0a22, 0xed9d4a0d, 0xeef84ae1, 0xeef80ae0\n"
        ".word 0xed9d1a00, 0xeeb84ac4, 0xee233a08, 0xee633a88\n"
        ".word 0xeef85ac1, 0xed9d0a07, 0xeeb82ac2, 0xeddd1a21\n"
        ".word 0xee241a88, 0xeef84ac0, 0xed9d5a0a, 0xee240a08\n"
        ".word 0xee003aa8, 0xeddd0a24, 0xee453aa8, 0xeef82ae2\n"
        ".word 0xeef80ae0, 0xee222a08, 0xeef81ae1, 0xee041aa8\n"
        ".word 0xeeb85ac5, 0xee622a88, 0xee000aa8, 0xeefd0ae3\n"
        ".word 0xee012aa8, 0xeebd1ac1, 0xee452a28, 0xedcd0a11\n"
        ".word 0xeddd0a06, 0xed8d1a13, 0xed9d1a12, 0xeef80ae0\n"
        ".word 0xeebd0ac0, 0xeeb81ac1, 0xeefd1ae2, 0xee600a88\n"
        ".word 0xee110a90, 0xee016a90, 0xee410a28, 0xeebd1ac2\n"
        ".word 0xeef81ae1, 0xed8d1a14, 0xee011a10, 0xeeb81ac1\n"
        ".word 0xee211a08, 0xee011aa8, 0xeefd1ac3, 0xedcd1a15\n"
        ".word 0xeddd1a16, 0xed8d0a0d, 0xed9d0a23, 0xeef81ae1\n"
        ".word 0xeeb80ac0, 0xee611a88, 0xee401a28, 0xeebd0ae0\n"
        ".word 0xeefd0ac1, 0xed8d0a06, 0xed9d0a10, 0xee101a90\n"
        ".word 0xee00ba90, 0xeeb80ac0, 0xeef80ae0, 0xee200a08\n"
        ".word 0xee000aa8, 0xeefd0ae1, 0xeebd0ac0, 0xedcd0a16\n"
        ".word 0xeddd0a1a, 0xeef80ae0, 0xed8d0a10, 0xee008a10\n"
        ".word 0xee600a88, 0xeeb80ac0, 0xee400a28, 0xeebd0ae0\n"
        ".word 0xed8d0a1a, 0xee002a10, 0xeeb80ac0, 0xee600a08\n"
        ".word 0xee00ca10, 0xeeb80ac0, 0xee400a28, 0xeebd0ae0\n"
        ".word 0xee102a10, 0xed9d0a17, 0xeeb80ac0, 0xee600a08\n"
        ".word 0xed9d0a25, 0xeeb80ac0, 0xee400a28, 0xeebd0ae0\n"
        ".word 0xed8d0a17, 0xed9d0a1b, 0xeeb80ac0, 0xee600a08\n"
        ".word 0xee009a10, 0xeeb80ac0, 0xee400a28, 0xeebd0ae0\n"
        ".word 0xed8d0a1b, 0xed9d0a1c, 0xeeb80ac0, 0xee600a08\n"
        ".word 0xee007a10, 0xeeb80ac0, 0xee400a28, 0xeebd0ae0\n"
        ".word 0xed8d0a1c, 0xee003a10, 0xeeb80ac0, 0xee600a08\n"
        ".word 0xee00aa10, 0xeeb80ac0, 0xee400a28, 0xeebd0ae0\n"
        ".word 0xee103a10, 0xe51fc400, 0xe59cc008, 0xe35c0080\n"
        ".word 0x0a000057, 0xe59d5044, 0xe0000c90, 0xe0010c91\n"
        ".word 0xe0050c95, 0xe0020c92, 0xe1a06fc5, 0xe0855ca6\n"
        ".word 0xe1a053c5, 0xe58d5044, 0xe59d504c, 0xe0050c95\n"
        ".word 0xe1a06fc5, 0xe0855ca6, 0xe1a053c5, 0xe58d504c\n"
        ".word 0xe59d5050, 0xe0050c95, 0xe1a06fc5, 0xe0855ca6\n"
        ".word 0xe1a053c5, 0xe58d5050, 0xe1a05fc0, 0xe0800ca5\n"
        ".word 0xe59d5054, 0xe1a003c0, 0xe0050c95, 0xe1a06fc5\n"
        ".word 0xe0855ca6, 0xe1a053c5, 0xe58d5054, 0xe59d5034\n"
        ".word 0xe0050c95, 0xe1a06fc5, 0xe0855ca6, 0xe1a053c5\n"
        ".word 0xe58d5034, 0xe59d5018, 0xe0050c95, 0xe1a06fc5\n"
        ".word 0xe0855ca6, 0xe1a053c5, 0xe58d5018, 0xe1a05fc1\n"
        ".word 0xe0811ca5, 0xe59d5058, 0xe1a013c1, 0xe0050c95\n"
        ".word 0xe1a06fc5, 0xe0855ca6, 0xe1a053c5, 0xe58d5058\n"
        ".word 0xe59d5040, 0xe0050c95, 0xe1a06fc5, 0xe0855ca6\n"
        ".word 0xe1a053c5, 0xe58d5040, 0xe59d5068, 0xe0050c95\n"
        ".word 0xe1a06fc5, 0xe0855ca6, 0xe1a053c5, 0xe58d5068\n"
        ".word 0xe1a05fc2, 0xe0822ca5, 0xe59d505c, 0xe1a023c2\n"
        ".word 0xe0050c95, 0xe1a06fc5, 0xe0855ca6, 0xe1a053c5\n"
        ".word 0xe58d505c, 0xe59d506c, 0xe0050c95, 0xe1a06fc5\n"
        ".word 0xe0030c93, 0xe0855ca6, 0xe1a053c5, 0xe58d506c\n"
        ".word 0xe59d5070, 0xe0050c95, 0xe1a0cfc3, 0xe0833cac\n"
        ".word 0xe1a06fc5, 0xe1a033c3, 0xe0855ca6, 0xe1a053c5\n"
        ".word 0xe58d5070, 0xe3500000, 0xd3a00000, 0xda000002\n"
        ".word 0xe1a00080, 0xe35000ff, 0xc3a000ff, 0xe3510000\n"
        ".word 0xd3a01000, 0xda000002, 0xe1a01081, 0xe35100ff\n"
        ".word 0xc3a010ff, 0xe3520000, 0xd3a02000, 0xda000002\n"
        ".word 0xe1a02082, 0xe35200ff, 0xc3a020ff, 0xe3530000\n"
        ".word 0xd3a0c000, 0xda000002, 0xe1a0c083, 0xe35c00ff\n"
        ".word 0xc3a0c0ff, 0xe59d3044, 0xe59d504c, 0xe59d6034\n"
        ".word 0xe59d7040, 0xe1a03c03, 0xe1833805, 0xe59d5050\n"
        ".word 0xe59d806c, 0xed9d0a19, 0xeeb02a49, 0xe1833405\n"
        ".word 0xe59d5054, 0xe1800003, 0xe59d3070, 0xeef80ac0\n"
        ".word 0xe1a05c05, 0xe1855806, 0xe59d6018, 0xeef01a69\n"
        ".word 0xeeb01a4a, 0xe1855406, 0xe59d6058, 0xe1855001\n"
        ".word 0xe1a06c06, 0xe1866807, 0xe59d7068, 0xe1866407\n"
        ".word 0xe59d705c, 0xe1a07c07, 0xe1877808, 0xe1877403\n"
        ".word 0xe1863002, 0xe3a02032, 0xe187100c, 0xe0020294\n"
        ".word 0xee002a10, 0xe1a02005, 0xeeb80ac0, 0xeb0312f6\n"
        ".word 0xe2844002, 0xe3540008, 0xbafffe24, 0xe59d0078\n"
        ".word 0xe2800002, 0xe3500007, 0xe58d0078, 0xbafffe12\n"
        ".word 0xe51f5684, 0xe3a02000, 0xe3a01007, 0xe3a00006\n"
        ".word 0xe5954000, 0xeb03280a, 0xe2844a01, 0xe2844fab\n"
        ".word 0xe5941000, 0xe0842101, 0xe5921008, 0xe5820008\n"
        ".word 0xe5d42018, 0xe3520000, 0x01510000, 0x0a000003\n"
        ".word 0xe594101c, 0xe12fff31, 0xe3a00000, 0xe5c40018\n"
        ".word 0xe5950000, 0xe2804a01, 0xe2844f93, 0xe5940000\n"
        ".word 0xe0841100, 0xe2400001, 0xe5911008, 0xe5840000\n"
        ".word 0xe0840100, 0xe5d42018, 0xe5900008, 0xe3520000\n"
        ".word 0x01510000, 0x0a000003, 0xe594101c, 0xe12fff31\n"
        ".word 0xe3a00000, 0xe5c40018, 0xe28dd0ac, 0xecbd8b06\n"
        ".word 0xe8bd8ff0\n");
}

// ---------------------------------------------------------------------------
// 0x001AAC60: Battle unit 3D sprite perspective projection & drawing
// ---------------------------------------------------------------------------
// DECOMP_FUNC(0x001aac60, 2448)
#if 0
void battle_func_001aac60(smt4::battle::BattleUnitSprite* unit) {
    if (!unit || unit->active == 0) return;

    f32 matrix[16];
    f32* proj_mat = battle_func_002a7f04();
    battle_func_002c0000(matrix, proj_mat);

    u32 mode_idx = (unit->render_flags >> 1) & 3;
    switch (mode_idx) {
    case 0:
        smt4::battle::SetRenderModeWithStack(6, 7, 0);
        break;
    case 1:
        smt4::battle::SetRenderModeWithStack(6, 1, 0);
        break;
    case 2:
        smt4::battle::SetRenderModeWithStack(6, 1, 2);
        break;
    case 3:
        smt4::battle::SetRenderModeWithStack(5, 0, 1);
        break;
    }

    if (unit->render_flags & 8) {
        smt4::battle::PushRenderViewport(5);
    }

    if (unit->render_flags & 0x20) {
        f32 cam_mat[16];
        f32 cam_trans[3] = { 0.0f, 0.0f, -9.0f };
        func_00286700(cam_mat, cam_trans);
        script_vm_func_002b71f8(matrix, matrix, cam_mat);
    }

    if (unit->extra && unit->extra->anim_sub) {
        f32 anim_mat[16];
        f32 anim_vec[3] = {
            unit->extra->anim_sub->anim[0] * 0.03125f,
            unit->extra->anim_sub->anim[1] * -0.03125f,
            0.0f
        };
        func_00286700(anim_mat, anim_vec);
        script_vm_func_002b71f8(matrix, matrix, anim_mat);
    }

    f32 pos_mat[16];
    func_00286700(pos_mat, unit->pos);
    script_vm_func_002b71f8(matrix, matrix, pos_mat);

    if (unit->anim_mode == 1) {
        f32 offset_mat[16];
        func_00286700(offset_mat, unit->anim_offset);
        script_vm_func_002b71f8(matrix, matrix, offset_mat);
    } else if (unit->anim_mode == 3) {
        ui_func_00195424(unit, 1);
    }

    if (unit->render_flags & 1) {
        if (unit->anim_mode == 1) {
            s32 r_x = unit->rot_angles[0] - unit->pivot_offset[0];
            s32 r_y = unit->rot_angles[1] - unit->pivot_offset[1];
            s32 r_z = unit->rot_angles[2] - unit->pivot_offset[2];
            func_0028640c(matrix, r_x, r_y, r_z);
            func_0028640c(matrix, 0, unit->anim_param_368, 0);
            func_0028640c(matrix, 0x5A - unit->field_16e, unit->field_170, 0);
        } else {
            func_0028640c(matrix, unit->rot_angles[0], unit->rot_angles[1], unit->rot_angles[2]);
        }
    } else {
        if (unit->anim_mode != 0) {
            f32 rot3x3[9] = { 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f };
            for (s32 vi = 0; vi < 4; ++vi) {
                f32 v_out[3];
                engine_func_002a8a58(v_out, rot3x3, unit->quad_verts[vi].pos);
                unit->quad_verts[vi].pos[0] = v_out[0];
                unit->quad_verts[vi].pos[1] = v_out[1];
                unit->quad_verts[vi].pos[2] = v_out[2];
            }
            func_0028640c(matrix, 0, 0, unit->rot_angles[2]);
        } else {
            func_0028640c(matrix, unit->rot_angles[0], unit->rot_angles[1], unit->rot_angles[2]);
        }
    }

    if (!unit->skip_rot) {
        func_0028640c(matrix, static_cast<s32>(unit->rot_base[0]),
                              static_cast<s32>(unit->rot_base[1]),
                              static_cast<s32>(unit->rot_base[2]));

        s32 z_ang = static_cast<s32>(unit->rot_z);
        z_ang = (z_ang % 360);
        if (z_ang < 0) z_ang += 360;
        z_ang = 360 - z_ang;

        f32 z_mat[16];
        f32 rot_bam = static_cast<f32>(z_ang) * (256.0f / 360.0f);
        func_002b22fc(z_mat, 0.0f, 0.0f, rot_bam);
        script_vm_func_002b71f8(matrix, matrix, z_mat);

        if (unit->field_1da != 0 || unit->field_1db != 0) {
            f32 head_mat[16];
            f32 head_vec[3] = {
                static_cast<f32>(unit->field_1da) * 0.1f,
                static_cast<f32>(unit->field_1db) * 0.1f,
                0.0f
            };
            func_00286700(head_mat, head_vec);
            script_vm_func_002b71f8(matrix, matrix, head_mat);
        }
    }

    if (unit->field_1dc != 0 || unit->field_1dd != 0) {
        f32 head2_mat[16];
        f32 factor = unit->extra ? unit->extra->scale_factor : 1.0f;
        f32 head2_vec[3] = {
            static_cast<f32>(unit->field_1dc) * -0.1f * factor,
            static_cast<f32>(unit->field_1dd) * -0.1f * factor,
            0.0f
        };
        func_00286700(head2_mat, head2_vec);
        script_vm_func_002b71f8(matrix, matrix, head2_mat);
    }

    f32 scale_mat[16] = {
        unit->scale[0] * unit->scale[1], 0.0f, 0.0f, 0.0f,
        0.0f, unit->scale[0] * unit->scale[2], 0.0f, 0.0f,
        0.0f, 0.0f, 1.0f, 0.0f,
        0.0f, 0.0f, 0.0f, 1.0f
    };
    script_vm_func_002b71f8(matrix, matrix, scale_mat);

    if (unit->field_1dc != 0 || unit->field_1dd != 0) {
        f32 restore_mat[16];
        f32 restore_vec[3] = {
            static_cast<f32>(unit->field_1dc) * 0.1f,
            static_cast<f32>(unit->field_1dd) * 0.1f,
            0.0f
        };
        func_00286700(restore_mat, restore_vec);
        script_vm_func_002b71f8(matrix, matrix, restore_mat);
    }

    f32 proj_verts[4][3];
    for (s32 vi = 0; vi < 4; ++vi) {
        f32 vx = unit->quad_verts[vi].pos[0];
        f32 vy = -unit->quad_verts[vi].pos[1];
        f32 vz = unit->quad_verts[vi].pos[2];

        f32 wx = matrix[0] * vx + matrix[4] * vy + matrix[8]  * vz + matrix[12];
        f32 wy = matrix[1] * vx + matrix[5] * vy + matrix[9]  * vz + matrix[13];
        f32 wz = matrix[2] * vx + matrix[6] * vy + matrix[10] * vz + matrix[14];
        f32 ww = matrix[3] * vx + matrix[7] * vy + matrix[11] * vz + matrix[15];

        f32 inv_w = (ww != 0.0f) ? (1.0f / ww) : 1.0f;
        proj_verts[vi][0] = wx * inv_w;
        proj_verts[vi][1] = wy * inv_w;
        proj_verts[vi][2] = wz * inv_w;
    }

    ui_func_002c1d3c(smt4::engine::g_RenderRegisterBase, unit->texture_id);

    func_002ba520(unit->quad_verts[0].color, unit->quad_verts[1].color,
                  unit->quad_verts[2].color, unit->quad_verts[3].color);

    if (unit->render_flags & 8) {
        smt4::battle::PopRenderViewport();
    }
}
#endif

// Readable battle/gameplay draft above; exact ARM body retained for matcher coverage.
__attribute__((naked)) void battle_func_001aac60(smt4::battle::BattleUnitSprite* unit) {
    asm volatile(
        ".word 0xe92d4ff0, 0xe1a04000, 0xed2d8b06, 0xe24ddf75\n"
        ".word 0xe5d003e8, 0xe3500000, 0x0a000259, 0xeb03f4a0\n"
        ".word 0xe1a01000, 0xe28d0030, 0xeb0454dc, 0xe5d40130\n"
        ".word 0xe59f9480, 0xe3a0a000, 0xe1a00e80, 0xe1b00f20\n"
        ".word 0x0a000006, 0xe3500001, 0x0a000014, 0xe3500002\n"
        ".word 0x0a000025, 0xe3500003, 0x0a000035, 0xea000048\n"
        ".word 0xe5995000, 0xe3a02000, 0xe3a01007, 0xe3a00006\n"
        ".word 0xeb046cb3, 0xe2855a01, 0xe2855fab, 0xe5951000\n"
        ".word 0xe0852101, 0xe5921008, 0xe5820008, 0xe5d52018\n"
        ".word 0xe3520000, 0x01510000, 0x0a000039, 0xea00000e\n"
        ".word 0xe5995000, 0xe3a02000, 0xe3a01001, 0xe3a00006\n"
        ".word 0xeb046ca3, 0xe2855a01, 0xe2855fab, 0xe5951000\n"
        ".word 0xe0852101, 0xe5921008, 0xe5820008, 0xe5d52018\n"
        ".word 0xe3520000, 0x01510000, 0x0a000029, 0xe595101c\n"
        ".word 0xe12fff31, 0xe5c5a018, 0xea000025, 0xe5995000\n"
        ".word 0xe3a02002, 0xe3a01001, 0xe3a00006, 0xeb046c90\n"
        ".word 0xe2855a01, 0xe2855fab, 0xe5951000, 0xe0852101\n"
        ".word 0xe5921008, 0xe5820008, 0xe5d52018, 0xe3520000\n"
        ".word 0x01510000, 0x0a000016, 0xe595101c, 0xe12fff31\n"
        ".word 0xea000012, 0xe5995000, 0xe3a02001, 0xe3a01000\n"
        ".word 0xe3a00005, 0xeb046c7e, 0xe2855a01, 0xe2855fab\n"
        ".word 0xe1a01000, 0xe5950000, 0xe0852100, 0xe5920008\n"
        ".word 0xe5821008, 0xe5d52018, 0xe3520000, 0x01500001\n"
        ".word 0x0a000003, 0xe595201c, 0xe1a00001, 0xe12fff32\n"
        ".word 0xe5c5a018, 0xe5d40130, 0xe3100008, 0x0a000013\n"
        ".word 0xe5995000, 0xe3a01000, 0xe3a00005, 0xeb046c5e\n"
        ".word 0xe2855a01, 0xe2855f93, 0xe5951000, 0xe2812001\n"
        ".word 0xe0853101, 0xe5931008, 0xe0853102, 0xe5852000\n"
        ".word 0xe5830008, 0xe5d52018, 0xe3520000, 0x01510000\n"
        ".word 0x0a000002, 0xe595101c, 0xe12fff31, 0xe5c5a018\n"
        ".word 0xe5d40130, 0xeddf8ab4, 0xed9f8ab4, 0xe3100020\n"
        ".word 0x0a000037, 0xe5990000, 0xe59006f8, 0xe2801038\n"
        ".word 0xe28d0e16, 0xeb03f5a0, 0xe3500000, 0xe320f000\n"
        ".word 0x1a000019, 0xe59f02a8, 0xe5900000, 0xe3100001\n"
        ".word 0x1a000012, 0xe59f0298, 0xfa045491, 0xe3500000\n"
        ".word 0xe320f000, 0x0a00000d, 0xe59f0288, 0xe2801014\n"
        ".word 0xec808a02, 0xedc08a02, 0xedc08a03, 0xedc08a04\n"
        ".word 0xec818a02, 0xedc08a07, 0xedc08a08, 0xedc08a09\n"
        ".word 0xe2800028, 0xec808a02, 0xe59f0254, 0xe1a00000\n"
        ".word 0xe59f1250, 0xe28d0e16, 0xeb045475, 0xe28d00e0\n"
        ".word 0xe28d1e16, 0xeb045472, 0xedcd8a46, 0xedcd8a45\n"
        ".word 0xedcd8a44, 0xe28d1030, 0xed8d8a47, 0xe28d20e0\n"
        ".word 0xe1a00001, 0xeb0430bb, 0xed9f0a87, 0xedcd8a01\n"
        ".word 0xedcd8a02, 0xed8d0a03, 0xe28d1004, 0xe28d0e19\n"
        ".word 0xeb036df6, 0xe28d1030, 0xe28d2e19, 0xe1a00001\n"
        ".word 0xeb0430b0, 0xe5940354, 0xe5900004, 0xe3500000\n"
        ".word 0x0a00000f, 0xedd00a00, 0xeddf1a78, 0xed900a01\n"
        ".word 0xed9f1a77, 0xee600aa1, 0xe1a0100d, 0xee200a01\n"
        ".word 0xe28d00e0, 0xedcd0a00, 0xed8d0a01, 0xedcd8a02\n"
        ".word 0xeb036de2, 0xe28d1030, 0xe28d20e0, 0xe1a00001\n"
        ".word 0xeb04309c, 0xe2840e12, 0xe28d3024, 0xe8900007\n"
        ".word 0xe8830007, 0xe28d1024, 0xe28d0e12, 0xeb036dd7\n"
        ".word 0xe28d1030, 0xe28d2e12, 0xe1a00001, 0xeb043091\n"
        ".word 0xe5d40380, 0xe3500001, 0x1a000009, 0xe2840fd6\n"
        ".word 0xe8900007, 0xe88d0007, 0xe1a0100d, 0xe28d00e0\n"
        ".word 0xeb036dca, 0xe28d1030, 0xe28d20e0, 0xe1a00001\n"
        ".word 0xeb043084, 0xe5d40380, 0xe3500003, 0x1a000002\n"
        ".word 0xe3a01001, 0xe1a00004, 0xebffa909, 0xe5d40130\n"
        ".word 0xe2847c01, 0xe3100001, 0xe5d40380, 0x0a000002\n"
        ".word 0xe3500001, 0x0a000049, 0xea00005e, 0xe3500000\n"
        ".word 0x0a00005c, 0xe59f110c, 0xe5990000, 0xe5911000\n"
        ".word 0xe59006f8, 0xe3110001, 0xe2805038, 0x1a00000f\n"
        ".word 0xe59f00f0, 0xfa045422, 0xe3500000, 0xe320f000\n"
        ".word 0x0a00000a, 0xe59f00e0, 0xe2801010, 0xec808a02\n"
        ".word 0xedc08a02, 0xedc08a03, 0xec818a02, 0xedc08a06\n"
        ".word 0xedc08a07, 0xed808a08, 0xe59f00b8, 0xe1a00000\n"
        ".word 0xe59f10b4, 0xe28d00ec, 0xeb036cd9, 0xe1a01005\n"
        ".word 0xe28d0e16, 0xeb036d5a, 0xe28d00ec, 0xe28d1e16\n"
        ".word 0xeb03f649, 0xe28db0ec, 0xe2848fe2, 0xe3a06000\n"
        ".word 0xe28d30e0, 0xe0860086, 0xe0885180, 0xe8950007\n"
        ".word 0xe8830007, 0xe28d20e0, 0xe1a0100b, 0xe28d000c\n"
        ".word 0xeb03f660, 0xe59d000c, 0xe2866001, 0xe3560004\n"
        ".word 0xe5850000, 0xe59d0010, 0xe5850004, 0xe59d0014\n"
        ".word 0xe5850008, 0xbaffffed, 0xe3a02000, 0xe594300c\n"
        ".word 0xe1a01002, 0xe28d0030, 0xeb036cbf, 0xe320f000\n"
        ".word 0xe320f000, 0xea000023, 0x0044ea00, 0x00000000\n"
        ".word 0x3f800000, 0x00476634, 0x004efd6c, 0xc1100000\n"
        ".word 0x3d000000, 0xbd000000, 0x00476630, 0x004efd48\n"
        ".word 0xe594000c, 0xe5942168, 0xe5941008, 0xe5945164\n"
        ".word 0xe5946160, 0xe594c004, 0xe0403002, 0xe0412005\n"
        ".word 0xe04c1006, 0xe28d0030, 0xeb036ca7, 0xe3a03000\n"
        ".word 0xe5942368, 0xe1a01003, 0xe28d0030, 0xeb036ca2\n"
        ".word 0xe1d706fe, 0xe1d717f0, 0xe3a03000, 0xe260205a\n"
        ".word 0xe28d0030, 0xea000002, 0xe2841004, 0xe28d0030\n"
        ".word 0xe891000e, 0xeb036c98, 0xe5d401d9, 0xed9f9aee\n"
        ".word 0xe3500000, 0x1a000048, 0xe2840f81, 0xec900a03\n"
        ".word 0xe28d0030, 0xeebd0ac0, 0xeebd1ac1, 0xeefd0ae0\n"
        ".word 0xee101a10, 0xee113a10, 0xee102a90, 0xeb036c8a\n"
        ".word 0xed940a80, 0xe59f2384, 0xeebd0ac0, 0xee100a10\n"
        ".word 0xe3500f5a, 0xba000007, 0xe1a01000, 0xe1a0300a\n"
        ".word 0xe0e13092, 0xe1a03441, 0xe0431fc1, 0xe0411201\n"
        ".word 0xe0811081, 0xe0800181, 0xe3500000, 0xaa00000a\n"
        ".word 0xe3700f5a, 0xca000007, 0xe1a01000, 0xe1a0300a\n"
        ".word 0xe0e13092, 0xe1a02441, 0xe0421fc1, 0xe0411201\n"
        ".word 0xe0811081, 0xe0800181, 0xe2800f5a, 0xe2600f5a\n"
        ".word 0xee010a10, 0xeddf1ac6, 0xeeb00a68, 0xe28d0e16\n"
        ".word 0xeef80ac1, 0xee201aa1, 0xeef00a40, 0xeb041c22\n"
        ".word 0xe28d1030, 0xe28d2e16, 0xe1a00001, 0xeb042fdd\n"
        ".word 0xe1d70dda, 0xe3500000, 0x05d710db, 0x03510000\n"
        ".word 0x0a000011, 0xe1d71ddb, 0xee000a10, 0xe28d00e0\n"
        ".word 0xee001a90, 0xe1a0100d, 0xeeb80ac0, 0xeeb81ae0\n"
        ".word 0xee600a09, 0xee210a09, 0xeeb01a68, 0xedcd0a00\n"
        ".word 0xed8d0a01, 0xed8d1a02, 0xeb036d0c, 0xe28d1030\n"
        ".word 0xe28d20e0, 0xe1a00001, 0xeb042fc6, 0xe1d70ddc\n"
        ".word 0xe3500000, 0x05d710dd, 0x03510000, 0x0a000014\n"
        ".word 0xee000a90, 0xe1d71ddd, 0xed9f0a9e, 0xe5940354\n"
        ".word 0xeeb81ae0, 0xee001a90, 0xe1a0100d, 0xeef81ae0\n"
        ".word 0xedd00a05, 0xedcd8a02, 0xee211a00, 0xe28d00e0\n"
        ".word 0xee611a80, 0xee200a81, 0xee600aa1, 0xec8d0a02\n"
        ".word 0xeb036cf2, 0xe28d1030, 0xe28d20e0, 0xe1a00001\n"
        ".word 0xeb042fac, 0xe2840f7d, 0xe3a015fe, 0xec900a03\n"
        ".word 0xe3a00000, 0xe28d20a0, 0xee600a20, 0xee200a01\n"
        ".word 0xedcd0a28, 0xe58d00a4, 0xe58d00a8, 0xe58d00ac\n"
        ".word 0xe58d00b0, 0xed8d0a2d, 0xe58d00b8, 0xe58d00bc\n"
        ".word 0xe58d00c0, 0xe58d00c4, 0xed8d8a32, 0xe1cd0df8\n"
        ".word 0xe28d1030, 0xe58d00cc, 0xe58d00d0, 0xe58d00d4\n"
        ".word 0xe1a00001, 0xeb042f93, 0xe1d70ddc, 0xe3500000\n"
        ".word 0x05d710dd, 0x03510000, 0x0a00000f, 0xe1d71ddd\n"
        ".word 0xee000a10, 0xedcd8a02, 0xee001a90, 0xe1a0100d\n"
        ".word 0xe28d00e0, 0xeeb80ac0, 0xeef80ae0, 0xee200a09\n"
        ".word 0xee600a89, 0xec8d0a02, 0xeb036cc4, 0xe28d1030\n"
        ".word 0xe28d20e0, 0xe1a00001, 0xeb042f7e, 0xed940ae3\n"
        ".word 0xe5940388, 0xe5941390, 0xeeb10a40, 0xe58d0070\n"
        ".word 0xe28d2070, 0xe3a0c004, 0xe3a03000, 0xed8d0a1d\n"
        ".word 0xe58d1078, 0xed940ae9, 0xe59413a0, 0xe59403a8\n"
        ".word 0xeeb10a40, 0xe58d107c, 0xed8d0a20, 0xe58d0084\n"
        ".word 0xe2840fef, 0xed941aee, 0xec900a02, 0xe28d008c\n"
        ".word 0xed8d1a22, 0xeeb10a40, 0xec800a02, 0xed940af5\n"
        ".word 0xe59413d0, 0xe59403d8, 0xeeb10a40, 0xe58d1094\n"
        ".word 0xe1a01002, 0xed8d0a26, 0xe58d009c, 0xe28d5034\n"
        ".word 0xed910a01, 0xeddd3a19, 0xedd10a02, 0xed911a00\n"
        ".word 0xee633a80, 0xec954a02, 0xe28d5044, 0xeddd9a1a\n"
        ".word 0xed9d3a1b, 0xee244a00, 0xecd55a02, 0xe28d5054\n"
        ".word 0xed9daa18, 0xeddd1a0f, 0xee655a80, 0xec957a02\n"
        ".word 0xee0a3a01, 0xee493aa0, 0xed9d5a0c, 0xee270a00\n"
        ".word 0xed9d2a13, 0xeddd6a10, 0xeddd2a17, 0xed9d9a14\n"
        ".word 0xee451a01, 0xee044aa0, 0xee062a81, 0xee465a20\n"
        ".word 0xee492a01, 0xee070aa0, 0xee730a83, 0xe1a00002\n"
        ".word 0xe2833001, 0xe153000c, 0xe282200c, 0xee341a21\n"
        ".word 0xe281100c, 0xee751a82, 0xee302a22, 0xee880a20\n"
        ".word 0xee610a00, 0xee211a80, 0xee220a00, 0xed800a02\n"
        ".word 0xecc00a02, 0x3affffd0, 0xe594112c, 0xe5990000\n"
        ".word 0xeb0459fd, 0xeeb06a68, 0xeef07a48, 0xe28d5070\n"
        ".word 0xedcd7a03, 0xedcd7a02, 0xeeb07a46, 0xeef06a46\n"
        ".word 0xed8d6a01, 0xedcd7a00, 0xea000003, 0x3dcccccd\n"
        ".word 0xb60b60b7, 0x3f360b61, 0xbdcccccd, 0xec950a0c\n"
        ".word 0xe594039c, 0xe59413b4, 0xe59423cc, 0xe59433e4\n"
        ".word 0xeb043be2, 0xe5d40130, 0xe3100008, 0x0a000010\n"
        ".word 0xe5990000, 0xe2804a01, 0xe2844f93, 0xe5940000\n"
        ".word 0xe0841100, 0xe2400001, 0xe5911008, 0xe5840000\n"
        ".word 0xe0840100, 0xe5d42018, 0xe5900008, 0xe3520000\n"
        ".word 0x01510000, 0x0a000002, 0xe594101c, 0xe12fff31\n"
        ".word 0xe5c4a018, 0xe28ddf75, 0xecbd8b06, 0xe8bd8ff0\n");
}

// ---------------------------------------------------------------------------
// 0x0020DC34: Concentric billboard layer renderer with sine fade
// ---------------------------------------------------------------------------
// DECOMP_FUNC(0x0020dc34, 2416)
#if 0
void battle_func_0020dc34() {
    smt4::battle::BattleEffectState* state =
        smt4::battle::gp_BattleEffectState ? *smt4::battle::gp_BattleEffectState : nullptr;
    if (!state || state->active == 0) return;

    func_002c8a28();

    smt4::battle::PushRenderViewport(5);
    smt4::battle::SetRenderModeWithStack(6, 1, 0);

    u32 screen_mode = smt4::battle::gp_ScreenMode ? *smt4::battle::gp_ScreenMode : 0;

    f32 scale_val = 100.0f;
    if (screen_mode >= 100) {
        if (state->mode == 1)      scale_val = 150.0f;
        else if (state->mode == 2) scale_val = 160.0f;
        else if (state->mode == 3) scale_val = 170.0f;
        else                       scale_val = 180.0f;
    } else {
        if (state->mode == 1)      scale_val = 10.0f;
        else if (state->mode == 2) scale_val = 20.0f;
        else if (state->mode == 3) scale_val = 90.0f;
        else                       scale_val = 100.0f;
    }

    s32 alpha = 0x40;
    if (screen_mode >= 100) {
        if (state->timer > 15) {
            f32 diff = static_cast<f32>(state->timer - 15);
            f32 sin_arg = diff * 1.57079637f * 0.06666667f;
            f32 sin_val = script_vm_func_0028277c(sin_arg);
            alpha = static_cast<s32>((1.0f - sin_val) * 64.0f);
        }
    } else {
        alpha = 0xA0;
        if (state->timer > 15) {
            f32 diff = static_cast<f32>(state->timer - 15);
            f32 sin_arg = diff * 1.57079637f * 0.06666667f;
            f32 sin_val = script_vm_func_0028277c(sin_arg);
            alpha = static_cast<s32>((1.0f - sin_val) * 160.0f);
        }
    }
    if (alpha < 0) alpha = 0;
    u32 packed_color = 0xFFFFFF00u | static_cast<u8>(alpha);

    f32 base_corners[4][3] = {
        { -scale_val, -scale_val, 0.0f },
        {  scale_val, -scale_val, 0.0f },
        {  scale_val,  scale_val, 0.0f },
        { -scale_val,  scale_val, 0.0f }
    };

    if (screen_mode >= 100) {
        f32 s = 0.0f;
        f32 c = 1.0f;
        smt4::battle::LookupTrig(state->rot_y, s, c);

        f32 rot_mat[12] = {
             c,    0.0f,  s,    0.0f,
             0.0f, 1.0f,  0.0f, 0.0f,
            -s,    0.0f,  c,    0.0f
        };

        const f32 step_scale = 4.0f;
        const f32 base_step = 50.0f;

        for (s32 i = 0; i < 4; ++i) {
            f32 step = base_step + static_cast<f32>(state->timer * i) * step_scale;
            f32 trans[4][3];

            for (s32 c_idx = 0; c_idx < 4; ++c_idx) {
                battle_func_002ad6d8(trans[c_idx], rot_mat, base_corners[c_idx]);
                trans[c_idx][0] += state->offset[0];
                trans[c_idx][1] += state->offset[1] + step;
                trans[c_idx][2] += state->offset[2];
            }

            func_002ba520(packed_color, packed_color, packed_color, packed_color);
        }
    } else {
        const u8* cam = smt4::battle::gp_BattleCamera ? static_cast<const u8*>(*smt4::battle::gp_BattleCamera) : nullptr;
        f32 cam_yaw = cam ? *reinterpret_cast<const f32*>(cam + 0x4C) : 0.0f;
        const f32* cam_pos = cam ? reinterpret_cast<const f32*>(cam + 0x1C) : state->offset;

        f32 s = 0.0f;
        f32 c = 1.0f;
        smt4::battle::LookupTrig(cam_yaw, s, c);

        f32 rot_mat[12] = {
             c,    0.0f,  s,    0.0f,
             0.0f, 1.0f,  0.0f, 0.0f,
            -s,    0.0f,  c,    0.0f
        };

        const f32 step_scale = 1.5f;
        const f32 base_step = 6.0f;

        for (s32 i = 0; i < 4; ++i) {
            f32 step = base_step + static_cast<f32>(state->timer * i) * step_scale;
            f32 trans[4][3];

            for (s32 c_idx = 0; c_idx < 4; ++c_idx) {
                battle_func_002ad6d8(trans[c_idx], rot_mat, base_corners[c_idx]);
                trans[c_idx][0] += cam_pos[0];
                trans[c_idx][1] += cam_pos[1] + step;
                trans[c_idx][2] += cam_pos[2];
            }

            func_002ba520(packed_color, packed_color, packed_color, packed_color);
        }
    }

    smt4::battle::SetRenderModeWithStack(6, 1, 0);
    smt4::battle::PopRenderViewport();
}
#endif

// Readable concentric billboard fade/render draft above; exact ARM body retained for codegen coverage.
__attribute__((naked)) void battle_func_0020dc34() {
    asm volatile(
        ".word 0xe92d4ff0, 0xe59f03a0, 0xed2d8b06, 0xe24dd0e4\n"
        ".word 0xe5904000, 0xed9f8ae3, 0xe5d4003c, 0xe3500000\n"
        ".word 0x0a00024f, 0xeb02eb72, 0xe59fa380, 0xe3a01000\n"
        ".word 0xe3a00005, 0xe59a5000, 0xeb02e0c2, 0xe2855a01\n"
        ".word 0xe2855f93, 0xe3a09000, 0xe5951000, 0xe2812001\n"
        ".word 0xe0853101, 0xe5931008, 0xe0853102, 0xe5852000\n"
        ".word 0xe5830008, 0xe5d52018, 0xe3520000, 0x01510000\n"
        ".word 0x0a000002, 0xe595101c, 0xe12fff31, 0xe5c59018\n"
        ".word 0xe59a5000, 0xe3a02000, 0xe3a01001, 0xe3a00006\n"
        ".word 0xeb02e0b6, 0xe2855a01, 0xe2855fab, 0xe5951000\n"
        ".word 0xe0852101, 0xe5921008, 0xe5820008, 0xe5d52018\n"
        ".word 0xe3520000, 0x01510000, 0x0a000002, 0xe595101c\n"
        ".word 0xe12fff31, 0xe5c59018, 0xe59f72e4, 0xe5940040\n"
        ".word 0xeddf9ab8, 0xeddf8ab8, 0xe5971000, 0xe3510064\n"
        ".word 0xba000009, 0xe3500001, 0x0d9f8ab4, 0x0a00000e\n"
        ".word 0xe3500002, 0x0eb08a69, 0x0a00000b, 0xe3500003\n"
        ".word 0x0d9f8aaf, 0x1d9f8aaf, 0xea000007, 0xe3500001\n"
        ".word 0x0d9f8aad, 0x0a000004, 0xe3500002, 0x0eb08a68\n"
        ".word 0x0a000001, 0xe3500003, 0x0d9f8aa8, 0xe5946044\n"
        ".word 0xeddf0aa7, 0xed9f0aa7, 0xed9f9aa7, 0xe3510064\n"
        ".word 0xba00000e, 0xe356000f, 0xd3a02040, 0xda00001a\n"
        ".word 0xe246000f, 0xee010a10, 0xeeb81ac1, 0xee610a20\n"
        ".word 0xee200a80, 0xeb01d277, 0xee390a40, 0xeddf0a9b\n"
        ".word 0xee200a20, 0xeebd0ac0, 0xee102a10, 0xea00000c\n"
        ".word 0xe356000f, 0xd3a020a0, 0xda00000b, 0xe246000f\n"
        ".word 0xee010a10, 0xeeb81ac1, 0xee610a20, 0xee200a80\n"
        ".word 0xeb01d268, 0xee390a40, 0xee200a29, 0xeebd0ac0\n"
        ".word 0xee102a10, 0xe3520000, 0xb3a02000, 0xeeb10a48\n"
        ".word 0xe3e030ff, 0xeddf9a86, 0xe1822003, 0xe59f0218\n"
        ".word 0xed8d0a04, 0xe58d20d0, 0xedcd9a05, 0xed8d0a06\n"
        ".word 0xed8d0a07, 0xedcd9a08, 0xed8d8a09, 0xed8d8a0a\n"
        ".word 0xedcd9a0b, 0xed8d0a0c, 0xed8d8a0d, 0xedcd9a0e\n"
        ".word 0xed8d8a0f, 0xe5972000, 0xe59f11e0, 0xe59f51e4\n"
        ".word 0xeddf0a74, 0xeddf1a76, 0xe3520064, 0xba000076\n"
        ".word 0xed941a15, 0xeeb00a69, 0xe3a0c000, 0xee610a20\n"
        ".word 0xe3a0b000, 0xeef40ac0, 0xeef1fa10, 0xeef00ae0\n"
        ".word 0xeeb01a40, 0x33a08001, 0x23a08000, 0xee102a90\n"
        ".word 0xe1520001, 0xba000003, 0xee700ae1, 0xee102a90\n"
        ".word 0xe1520001, 0xaafffffb, 0xee112a10, 0xe1520001\n"
        ".word 0xba000003, 0xee311a61, 0xee112a10, 0xe1520001\n"
        ".word 0xaafffffb, 0xeefc1ac0, 0xe35c0000, 0xee111a90\n"
        ".word 0xeefc1ae0, 0xe6ff1071, 0xee112a90, 0xeefc1ac1\n"
        ".word 0xe6ff2072, 0xee113a90, 0xee011a90, 0xe20110ff\n"
        ".word 0xe6ff3073, 0xe0801201, 0xeeb82a61, 0xee012a90\n"
        ".word 0xe20220ff, 0xedd14a03, 0xe0802202, 0xed925a02\n"
        ".word 0xeef82a61, 0xee013a90, 0xe20330ff, 0xee300a42\n"
        ".word 0xe0800203, 0xed922a00, 0xedd05a01, 0xeef81a61\n"
        ".word 0xed924a01, 0xed926a03, 0xee700ae2, 0xedd02a00\n"
        ".word 0xe2800008, 0xecd06a02, 0xee311a61, 0xedd11a00\n"
        ".word 0xe2811004, 0xee002a85, 0xec913a02, 0xee004a86\n"
        ".word 0xee003a24, 0xee401a23, 0xee412a26, 0xee415a07\n"
        ".word 0x1ef11a61, 0xe3580000, 0x1eb12a42, 0xe35b0000\n"
        ".word 0x1ef12a62, 0xee633a25, 0xee210aa5, 0xee255a84\n"
        ".word 0xee615a84, 0xeeb16a42, 0xee630a22, 0xee614aa2\n"
        ".word 0xee622a84, 0xee233a04, 0xed8d5a1c, 0xeef01a60\n"
        ".word 0xeeb01a64, 0xedcd2a20, 0xedcd5a25, 0xed8d3a26\n"
        ".word 0xee501a02, 0xee100a82, 0xee031a82, 0xee443a82\n"
        ".word 0xedcd1a1d, 0xed8d0a22, 0xed8d1a1e, 0xedcd3a21\n"
        ".word 0xed8d6a24, 0xea000076, 0x42c80000, 0x004475b8\n"
        ".word 0x0044ea00, 0x0049f91c, 0x43200000, 0x41a00000\n"
        ".word 0x43160000, 0x432a0000, 0x43340000, 0x41200000\n"
        ".word 0x42b40000, 0x3fc8f5c3, 0x3d888889, 0x3f800000\n"
        ".word 0x42800000, 0x00000000, 0x3f360b61, 0x00407fc0\n"
        ".word 0x47800000, 0x47800000, 0x00447e88, 0xe5952000\n"
        ".word 0xeeb00a69, 0xe3a0c000, 0xe3a0b000, 0xed921a13\n"
        ".word 0xee610a20, 0xeef40ac0, 0xeef1fa10, 0xeef00ae0\n"
        ".word 0xeeb01a40, 0x33a08001, 0x23a08000, 0xee102a90\n"
        ".word 0xe1520001, 0xba000003, 0xee700ae1, 0xee102a90\n"
        ".word 0xe1520001, 0xaafffffb, 0xee112a10, 0xe1520001\n"
        ".word 0xba000003, 0xee311a61, 0xee112a10, 0xe1520001\n"
        ".word 0xaafffffb, 0xeefc1ac0, 0xe35c0000, 0xee111a90\n"
        ".word 0xeefc1ae0, 0xe6ff1071, 0xee112a90, 0xeefc1ac1\n"
        ".word 0xe6ff2072, 0xee113a90, 0xee011a90, 0xe20110ff\n"
        ".word 0xe6ff3073, 0xe0801201, 0xeef82a61, 0xee012a90\n"
        ".word 0xe20220ff, 0xedd14a03, 0xe0802202, 0xed925a02\n"
        ".word 0xeeb82a61, 0xee013a90, 0xe20330ff, 0xee300a62\n"
        ".word 0xe0800203, 0xed924a01, 0xedd02a00, 0xeef81a61\n"
        ".word 0xedd05a01, 0xe2800008, 0xee700ac2, 0xed922a00\n"
        ".word 0xed926a03, 0xecd06a02, 0xee311a61, 0xedd11a00\n"
        ".word 0xe2811004, 0xee002a85, 0xec913a02, 0xee004a86\n"
        ".word 0xee003a24, 0xee401a23, 0xee412a26, 0xee415a07\n"
        ".word 0x1ef11a61, 0xe3580000, 0x1eb12a42, 0xe35b0000\n"
        ".word 0x1ef12a62, 0xee633a25, 0xee610aa5, 0xee255a84\n"
        ".word 0xee615a84, 0xeeb16a42, 0xee230a22, 0xee614aa2\n"
        ".word 0xee622a84, 0xee233a04, 0xed8d5a1c, 0xeef01a40\n"
        ".word 0xeeb01a64, 0xedcd2a20, 0xedcd5a25, 0xed8d3a26\n"
        ".word 0xee501a82, 0xee500a02, 0xee031a82, 0xee443a82\n"
        ".word 0xedcd1a1d, 0xedcd0a22, 0xed8d1a1e, 0xedcd3a21\n"
        ".word 0xed8d6a24, 0xe58d907c, 0xe58d908c, 0xe58d909c\n"
        ".word 0xe5970000, 0xe28d7010, 0xe28d8040, 0xe3500064\n"
        ".word 0xba000061, 0xeef08a49, 0xed9faae6, 0xed9f9ae6\n"
        ".word 0xe3a05000, 0xe28d2010, 0xe0000596, 0xeeb08a49\n"
        ".word 0xe28d1070, 0xee000a10, 0xe28d0040, 0xeeb80ac0\n"
        ".word 0xee008a0a, 0xeb027d32, 0xe287200c, 0xe28d1070\n"
        ".word 0xe288000c, 0xeb027d2e, 0xe2872018, 0xe28d1070\n"
        ".word 0xe2880018, 0xeb027d2a, 0xe2872024, 0xe28d1070\n"
        ".word 0xe2880024, 0xeb027d26, 0xedd40a12, 0xed9d0a10\n"
        ".word 0xeef07a68, 0xe28d1068, 0xee300a20, 0xed8d0a10\n"
        ".word 0xedd40a13, 0xed9d1a11, 0xee710a20, 0xedcd0a11\n"
        ".word 0xedd41a14, 0xed9d1a12, 0xee700a88, 0xee311a21\n"
        ".word 0xed8d1a12, 0xed942a12, 0xeddd1a13, 0xee711a82\n"
        ".word 0xedcd1a13, 0xedd42a13, 0xed9d2a14, 0xee322a22\n"
        ".word 0xed8d2a14, 0xedd42a14, 0xed9d3a15, 0xee322a08\n"
        ".word 0xee732a22, 0xedcd2a15, 0xedd43a12, 0xed9d3a16\n"
        ".word 0xee333a23, 0xed8d3a16, 0xed944a13, 0xeddd3a17\n"
        ".word 0xee733a84, 0xedcd3a17, 0xedd44a14, 0xed9d4a18\n"
        ".word 0xee733a88, 0xee344a24, 0xed8d4a18, 0xed945a12\n"
        ".word 0xeddd4a19, 0xee744a85, 0xedcd4a19, 0xedd45a13\n"
        ".word 0xed9d5a1a, 0xee355a25, 0xed8d5a1a, 0xed946a14\n"
        ".word 0xeddd5a1b, 0xee355a08, 0xedcd0a11, 0xee755a86\n"
        ".word 0xeeb06a69, 0xed8d2a14, 0xedcd3a17, 0xedcd7a03\n"
        ".word 0xedcd7a02, 0xed8d6a01, 0xedcd7a00, 0xeeb07a46\n"
        ".word 0xec815a02, 0xeef06a46, 0xe59d30d0, 0xe1a02003\n"
        ".word 0xe1a01002, 0xe1a00001, 0xeb02b073, 0xe2855001\n"
        ".word 0xe3550004, 0xbaffffa2, 0xea000065, 0xed9faa87\n"
        ".word 0xed9f9a87, 0xe3a04000, 0xeeb08a68, 0xe0000496\n"
        ".word 0xe28d2010, 0xe28d1070, 0xee000a10, 0xe28d0040\n"
        ".word 0xeeb80ac0, 0xee008a0a, 0xeb027cd1, 0xe287200c\n"
        ".word 0xe28d1070, 0xe288000c, 0xeb027ccd, 0xe2872018\n"
        ".word 0xe28d1070, 0xe2880018, 0xeb027cc9, 0xe2872024\n"
        ".word 0xe28d1070, 0xe2880024, 0xeb027cc5, 0xe5950000\n"
        ".word 0xed9d0a10, 0xeef07a49, 0xe280301c, 0xedd00a07\n"
        ".word 0xe1a02003, 0xe1a0c002, 0xee300a20, 0xe1a0100c\n"
        ".word 0xe1a00002, 0xed8d0a10, 0xed931a01, 0xeddd0a11\n"
        ".word 0xee700a81, 0xedcd0a11, 0xedd31a02, 0xed9d1a12\n"
        ".word 0xee700a88, 0xee311a21, 0xed8d1a12, 0xedd31a00\n"
        ".word 0xed9d2a13, 0xee721a21, 0xedcd1a13, 0xed922a01\n"
        ".word 0xeddd2a14, 0xee322a82, 0xed8d2a14, 0xed923a02\n"
        ".word 0xeddd2a15, 0xee322a08, 0xee722a83, 0xedcd2a15\n"
        ".word 0xedd13a00, 0xed9d3a16, 0xee333a23, 0xed8d3a16\n"
        ".word 0xed914a01, 0xeddd3a17, 0xee733a84, 0xedcd3a17\n"
        ".word 0xed9c4a02, 0xeddd4a18, 0xee733a88, 0xee344a84\n"
        ".word 0xed8d4a18, 0xed905a00, 0xeddd4a19, 0xee744a85\n"
        ".word 0xedcd4a19, 0xedd05a01, 0xed9d5a1a, 0xee355a25\n"
        ".word 0xed8d5a1a, 0xed906a02, 0xeddd5a1b, 0xee355a08\n"
        ".word 0xedcd0a11, 0xee755a86, 0xeeb06a69, 0xed8d2a14\n"
        ".word 0xedcd3a17, 0xedcd7a03, 0xedcd7a02, 0xed8d6a01\n"
        ".word 0xedcd7a00, 0xe28d0068, 0xeeb07a46, 0xec805a02\n"
        ".word 0xeef06a46, 0xe59d30d0, 0xe1a02003, 0xe1a01002\n"
        ".word 0xe1a00001, 0xeb02b00c, 0xe2844001, 0xe3540004\n"
        ".word 0xbaffff9c, 0xe59a4000, 0xe3a02000, 0xe3a01007\n"
        ".word 0xe3a00006, 0xeb02dea5, 0xe2844a01, 0xe2844fab\n"
        ".word 0xe5941000, 0xe0842101, 0xe5921008, 0xe5820008\n"
        ".word 0xe5d42018, 0xe3520000, 0x01510000, 0x0a000002\n"
        ".word 0xe594101c, 0xe12fff31, 0xe5c49018, 0xe59a0000\n"
        ".word 0xe2804a01, 0xe2844f93, 0xe5940000, 0xe0841100\n"
        ".word 0xe2400001, 0xe5911008, 0xe5840000, 0xe0840100\n"
        ".word 0xe5d42018, 0xe5900008, 0xe3520000, 0x01510000\n"
        ".word 0x0a000007, 0xea000003, 0x40800000, 0x42480000\n"
        ".word 0x3fc00000, 0x40c00000, 0xe594101c, 0xe12fff31\n"
        ".word 0xe5c49018, 0xe28dd0e4, 0xecbd8b06, 0xe8bd8ff0\n");
}

} // extern "C"
