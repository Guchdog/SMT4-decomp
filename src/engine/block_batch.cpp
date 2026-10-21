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

// ---------------------------------------------------------------------------
// 0x00267420: General 4-face bounding box / billboard column submitter
// ---------------------------------------------------------------------------
// DECOMP_FUNC(0x00267420, 2888)
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

// ---------------------------------------------------------------------------
// 0x0034A4E4: Three-pass particle emitter command buffer evaluator
// ---------------------------------------------------------------------------
// DECOMP_FUNC(0x0034a4e4, 2816)
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

// ---------------------------------------------------------------------------
// 0x001FB520: Screen transition / distortion grid renderer
// ---------------------------------------------------------------------------
// DECOMP_FUNC(0x001fb520, 2788)
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
            s32 r = static_cast<s32>(grid->param_14 + 0xFF + grid->param_14);
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

// ---------------------------------------------------------------------------
// 0x001AAC60: Battle unit 3D sprite perspective projection & drawing
// ---------------------------------------------------------------------------
// DECOMP_FUNC(0x001aac60, 2448)
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

    if (unit->extra && (unit->extra->field_04[0] != 0.0f || unit->extra->field_04[1] != 0.0f)) {
        f32 anim_mat[16];
        f32 anim_vec[3] = {
            unit->extra->field_04[0] * 0.03125f,
            unit->extra->field_04[1] * -0.03125f,
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

// ---------------------------------------------------------------------------
// 0x0020DC34: Concentric billboard layer renderer with sine fade
// ---------------------------------------------------------------------------
// DECOMP_FUNC(0x0020dc34, 2416)
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

    f32 rot_mat[12] = {
        1.0f, 0.0f, 0.0f, 0.0f,
        0.0f, 1.0f, 0.0f, 0.0f,
        0.0f, 0.0f, 1.0f, 0.0f
    };

    f32 base_corners[4][3] = {
        { -scale_val, -scale_val, 0.0f },
        {  scale_val, -scale_val, 0.0f },
        {  scale_val,  scale_val, 0.0f },
        { -scale_val,  scale_val, 0.0f }
    };

    if (screen_mode >= 100) {
        const f32 step_scale = 4.0f;
        const f32 base_step = 50.0f;

        for (s32 i = 0; i < 4; ++i) {
            f32 step = base_step + static_cast<f32>(state->timer * i) * step_scale;
            f32 trans[4][3];

            for (s32 c = 0; c < 4; ++c) {
                battle_func_002ad6d8(trans[c], rot_mat, base_corners[c]);
                trans[c][0] += state->offset[0];
                trans[c][1] += state->offset[1] + step;
                trans[c][2] += state->offset[2];
            }

            func_002ba520(packed_color, packed_color, packed_color, packed_color);
        }
    } else {
        const f32 step_scale = 1.5f;
        const f32 base_step = 6.0f;

        for (s32 i = 0; i < 4; ++i) {
            f32 step = base_step + static_cast<f32>(state->timer * i) * step_scale;
            f32 trans[4][3];

            for (s32 c = 0; c < 4; ++c) {
                battle_func_002ad6d8(trans[c], rot_mat, base_corners[c]);
                trans[c][0] += state->offset[0];
                trans[c][1] += state->offset[1] + step;
                trans[c][2] += state->offset[2];
            }

            func_002ba520(packed_color, packed_color, packed_color, packed_color);
        }
    }

    smt4::battle::SetRenderModeWithStack(6, 1, 0);
    smt4::battle::PopRenderViewport();
}

} // extern "C"
