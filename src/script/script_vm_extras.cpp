#include "script/script_vm_extras.h"
#include "engine/asd_symbols.h"
#include "engine/map_runtime.h"

#include <cstdint>
#include <cstring>
#include <cmath>

namespace smt4::script {

// ---------------------------------------------------------------------------
// Globals reproduced from .data / referenced .bss
// ---------------------------------------------------------------------------

// 0x004474F0 (.data): {null, 0x0049F130}.  The second word is the script
// camera work object; `ldr r1,[r8,#4]` (0x00276CBC) is the only access here.
ScriptCameraWork* g_ScriptCameraWork =
    reinterpret_cast<ScriptCameraWork*>(static_cast<std::uintptr_t>(0x0049F130));

// 0x00447E88 / 0x0044CDF0 / 0x0049F91C are owned by src/engine/map_runtime.cpp:
//   g_MapSceneView     (0x00447E88 -> 0x004BCCD0)
//   g_NaviMainWork      (0x0044CDF0)
//   g_MapRuntimeState   (0x0049F91C)
// They are reused here rather than redeclared.

// 0x0049FA1C (.bss): world-map transition state.  This is the object at
// g_MapRuntimeState+0x100, not a pointer stored at that address.
MapEventState& g_MapEventState = *reinterpret_cast<MapEventState*>(
    smt4::engine::g_MapRuntimeState + 0x100);

// 0x0049F3F0 (.bss): camera projection object consumed by 0x00298FEC,
// 0x002C1774 and 0x002C1FFC.  The object is 0x508 bytes (0x002C1774 stores
// through +0x504); internal layout belongs to the AsdCamera translation unit.
u8 g_AsdProjection[0x508] = {};

// 0x0044CDC8 (.data): world-map transition/palette block.
WorldMapUiState g_WorldMapUiState = {0.5f, 4, 0xF49800FFu, 0xDC0F14FFu, 0x0B};

// 0x0040449C (.rodata): the three 0.6f damping factors used by the camera
// shake loop (`vldr s0,[pc,#0x274]` .. 0x00276D58, values verified in code.bin).
const f32 g_MapRouteDamping[3] = {0.6f, 0.6f, 0.6f};

// 0x004045AC, 0x0040464C, 0x004046EC, 0x0040478C (.rodata): the four
// 20-frame route banks copied onto the stack at 0x002C8CAC..0x002C8CDC.
const MapRouteFrame g_MapRouteBanks[4][20] = {
    {   // 0x004045AC
        {6, 0, 0, 0}, {7, 0, 0, 0}, {8, 0, 0, 0}, {9, 1, 50, 10},
        {10, 0, 0, 0}, {10, 0, 0, 0}, {5, 1, -10, 100}, {2, 0, 0, 0},
        {0, 0, 0, 0}, {0, 0, 0, 0}, {0, 0, 0, 0}, {0, 0, 0, 0},
        {0, 0, 0, 0}, {0, 0, 0, 0}, {0, 0, 0, 0}, {0, 0, 0, 0},
        {0, 0, 0, 0}, {0, 0, 0, 0}, {0, 0, 0, 0}, {0, 0, 0, 0},
    },
    {   // 0x0040464C
        {6, 0, 0, 0}, {6, 0, 0, 0}, {6, 0, 0, 0}, {6, 1, 50, 10},
        {8, 0, 0, 0}, {10, 1, -10, 100}, {5, 0, 0, 0}, {5, 0, 0, 0},
        {0, 0, 0, 0}, {0, 0, 0, 0}, {0, 0, 0, 0}, {0, 0, 0, 0},
        {0, 0, 0, 0}, {0, 0, 0, 0}, {0, 0, 0, 0}, {0, 0, 0, 0},
        {0, 0, 0, 0}, {0, 0, 0, 0}, {0, 0, 0, 0}, {0, 0, 0, 0},
    },
    {   // 0x004046EC
        {5, 0, 0, 0}, {8, 0, -160, 30}, {13, 0, 0, 0}, {14, 0, 0, 0},
        {13, 1, 10, 120}, {12, 0, 0, 0}, {11, 0, 0, 0}, {10, 1, -20, 20},
        {9, 0, 0, 0}, {8, 0, 0, 0}, {7, 0, 0, 0}, {5, 0, 0, 0},
        {2, 0, 0, 0}, {0, 0, 0, 0}, {0, 0, 0, 0}, {0, 0, 0, 0},
        {0, 0, 0, 0}, {0, 0, 0, 0}, {0, 0, 0, 0}, {0, 0, 0, 0},
    },
    {   // 0x0040478C
        {0, 0, 0, 0}, {0, 0, 0, 0}, {0, 0, 0, 0}, {0, 1, 50, 10},
        {0, 0, 0, 0}, {0, 0, 0, 0}, {0, 1, -10, 100}, {0, 1, 0, 180},
        {0, 0, 0, 0}, {0, 0, 0, 0}, {0, 0, 0, 0}, {0, 0, 0, 0},
        {0, 0, 0, 0}, {0, 0, 0, 0}, {0, 0, 0, 0}, {0, 0, 0, 0},
        {0, 0, 0, 0}, {0, 0, 0, 0}, {0, 0, 0, 0}, {0, 0, 0, 0},
    },
};

// ---------------------------------------------------------------------------
// Observed call targets
// ---------------------------------------------------------------------------

extern "C" {
    // 0x002C2B1C (24 B, UI engine context): already declared as
    // UiEngine_GetContext in src/ui/window.cpp.
    void* UiEngine_GetContext();

    // 0x002AE18C (296 B): writes a model's world position to `out`.
    void  ui_func_002ae18c(f32* out, void* model);
    // 0x002820A4 (624 B): full-quadrant atan2(s0,s1) in radians.
    f32   ui_func_002820a4(f32 y, f32 x);
    // 0x0028277C (456 B) / 0x00282600 (380 B): inlined sin/cos.
    f32   script_vm_func_0028277c(f32 radians);
    f32   script_vm_func_00282600(f32 radians);
    // 0x00287D54 (32 B): sqrt((s3-s0)^2 + (s4-s1)^2 + (s5-s2)^2).
    f32   engine_func_00287d54(f32 ax, f32 ay, f32 az,
                               f32 bx, f32 by, f32 bz);
    // 0x0027DC18 (64 B): LCG float in [0,1).
    f32   ui_func_0027dc18();
    // 0x002C615C (556 B): unsigned division (r0 / r1).
    u32   ui_func_002c615c(u32 numerator, u32 denominator);

    // 0x0025C470 (96 B): look-at from two vectors, adding the work shake
    // offset (+0x294..+0x29C) to the second vector.
    void  script_vm_func_0025c470(const f32* eye, const f32* target);
    // 0x0025C4D0 (56 B): camera rotation/roll (s0..s2 position, s3 degrees).
    void  script_vm_func_0025c4d0(f32 x, f32 y, f32 z, f32 degrees);

    // Camera projection helpers (canonical spellings in engine/asd_symbols.h
    // and src/engine/asd_scene.cpp).
    void  AsdCamera_SetClipRange(void* projection, f32 near_plane, f32 far_plane);
    void  AsdCamera_SetPerspective(void* projection, u32 mode, f32 fov,
                                   f32 near_plane, f32 far_plane, f32 aspect);
    void  AsdCamera_LookAt(void* projection, const f32* eye,
                           const f32* target, const f32* up);
    void  AsdCamera_BindProjection(void* projection);

    // 0x00266E88 (724 B): resolves the visible camera point for a look-at.
    void  script_vm_func_00266e88(const f32* eye, const f32* target, f32* out);
    // 0x001F82AC (1,156 B): camera shake / room effect update.
    void  script_vm_func_001f82ac();

    // World-map route camera helpers.
    void  ui_func_002bcf58(void* dst, const void* src, u32 size);       // 0x002BCF58
    void  script_vm_func_0025bffc(f32 angle_offset, f32 distance);      // 0x0025BFFC
    void  script_vm_func_0027fab8(f32* out, f32 x, f32 y, f32 z);       // 0x0027FAB8
    s32   script_vm_func_0027f6fc(const f32* from, const f32* to);      // 0x0027F6FC
    void  script_vm_func_0027ff10(s32 mode);                            // 0x0027FF10
    s32   script_vm_func_0027fbc8(f32* out_x, f32* out_y, s32 mode);    // 0x0027FBC8
    void  script_vm_func_0027fd08(s32 state);                           // 0x0027FD08
    s32   script_vm_func_0028075c(f32* position);                       // 0x0028075C
    // 0x002805D4 ignores its first argument (it executes `mvn r0,#-1` at
    // entry); the camera pointer is still passed by both call sites.
    void  script_vm_func_002805d4(const void* cam, f32 x, f32 z);       // 0x002805D4
    void  script_vm_func_00280bf8();                                    // 0x00280BF8
    void  script_vm_func_00287c44(s32 a, s32 b, s32 c);                 // 0x00287C44
    u32   script_vm_func_002920e4(u32 id, f32 x, f32 y, f32 z);         // 0x002920E4
    bool  camp_func_0025a378(s32 type, s32 bit);                        // 0x0025A378
    void  func_002565b0(s32 a, s32 b, s32 c);                           // 0x002565B0
    void  func_00256524(s32 a, s32 b);                                  // 0x00256524
    bool  shop_func_00256750();                                         // 0x00256750
    void  ui_func_0025beb8();                                           // 0x0025BEB8
    s32   ui_func_00297004(s32 min, s32 max);                           // 0x00297004

    // World-map grid helpers.  The 0x231Fxx/0x2327xx accessors take the
    // work+0x162 handle in r0 and ignore it (each one reloads the global at
    // 0x0044CDF0 / 0x00447E88); 0x231E38 receives the work pointer.
    s32   func_00231f6c(void* handle);                                  // 0x00231F6C
    s32   func_002327c4(void* handle);                                  // 0x002327C4
    const f32* func_002327ec(void* handle);                             // 0x002327EC
    const f32* func_00231f58(void* handle);                             // 0x00231F58
    void  func_00231d4c(const void* src, f32* out);                     // 0x00231D4C
    s32   engine_func_002891e0(s32 id);                                 // 0x002891E0
    void  func_002326e8(WorldMapWork* work, s32 enable);                // 0x002326E8
    bool  script_vm_func_002b89d4();                                    // 0x002B89D4
    void  engine_func_00231c68(s32 mode, s32 cell_x, s32 cell_y);       // 0x00231C68
    bool  engine_func_00231b74(s32 mode, s32 cell_x, s32 cell_y);       // 0x00231B74
    f32   func_00231ec0(void* handle);                                  // 0x00231EC0
    s32   func_00231e38(WorldMapWork* work);                            // 0x00231E38
    f32   func_00231f44(void* handle);                                  // 0x00231F44
    // `vldmia [sp,#0x38]` reads the two trailing arguments as floats, so the
    // listing's integer 0x0B/1 stack words are reproduced as bit patterns.
    void  camp_func_00231d60(void* map_state, s32 id, s32 x, s32 y,
                             f32 a, f32 b);                             // 0x00231D60
    void  ui_func_00231f80(WorldMapWork* work);                         // 0x00231F80
    // The fifth (y) stack word is produced by `vcvt.s32.f32` + `vstr` and is
    // read back by the callee via `vldmia r1,{s16,s17}`; callers must pass the
    // integer bit pattern, not a float value.
    void  func_002b06a0(s32 mode, s32 sprite_type, s32 depth, s32 x,
                        f32 y, f32 alpha, const void* extra);           // 0x002B06A0

    // Marker builder helpers.  The TBB row accessors take a scratch context
    // pointer in r0 (ignored by the callee) and the row index in r1.
    s32   camp_func_00231664(void* ctx);                                // 0x00231664
    CampMapLayerRow* camp_func_00231628(void* ctx, s32 index);          // 0x00231628
    void  engine_func_0024c3f8(u32 category, u32 index,
                               s32* out0, s32* out1);                   // 0x0024C3F8
    s32   camp_func_00248418();                                         // 0x00248418
    CampMapSpawnRow* camp_func_002483b8(s32 index);                     // 0x002483B8
    s32   script_vm_func_002765b8(u32 id);                              // 0x002765B8
    s32   camp_func_00321ad0(u32 id);                                   // 0x00321AD0
    s32   camp_func_0039fec4(void* ctx);                                // 0x0039FEC4
    CampMapCommandRow* camp_func_0039fe50(void* ctx, s32 index);        // 0x0039FE50
    s32   engine_func_00247414(void* ctx);                              // 0x00247414
    CampMapLandmarkRow* camp_func_002473d8(void* ctx, s32 index);       // 0x002473D8

    // 0x0039ED68 (676 B) / 0x0039EAD4 (276 B): map marker submission and
    // command-list flush invoked by the grid renderer.
    void  script_vm_func_0039ed68(WorldMapWork* work);
    void  ui_func_0039ead4(WorldMapWork* work);

    // (g_MapSpriteAtlas is declared once in script_vm_extras.h.)
}

namespace {

constexpr f32 kDegToRad = 0.01745329238474369f;   // 0x3C8EFA35
constexpr f32 kRadToDeg = 57.3248405456543f;      // 0x42654CA3

// Reinterprets a word as a float.  The map renderer passes the phase word
// (0x0B/0x0F1) through `vldr s0,[0x44CDC8+0x10]` / `vstr s0,[sp]` to callees
// that read their stack arguments as floats, so the bit pattern is preserved.
inline f32 BitCastF32(u32 value) {
    union {
        u32 u;
        f32 f;
    } bits;
    bits.u = value;
    return bits.f;
}

inline void Copy3(f32* dst, const f32* src) {
    dst[0] = src[0];
    dst[1] = src[1];
    dst[2] = src[2];
}

inline void Copy3(f32* dst, f32 x, f32 y, f32 z) {
    dst[0] = x;
    dst[1] = y;
    dst[2] = z;
}

inline f32 Distance3(const f32* a, const f32* b) {
    return engine_func_00287d54(a[0], a[1], a[2], b[0], b[1], b[2]);
}

// The listing passes a scratch vector inside the work object as the look-at
// "up" argument: `add r3,r0,#0x1c` at 0x002770CC/0x002771F8 and
// `add r3,r0,#0x28` at 0x00277DB0.  Both slots overlap other fields, so they
// are reached by byte offset rather than by a named member.
inline const f32* CameraUp1c(const ScriptCameraWork* w) {
    return reinterpret_cast<const f32*>(
        reinterpret_cast<const u8*>(w) + 0x1C);
}

inline const f32* CameraUp28(const ScriptCameraWork* w) {
    return reinterpret_cast<const f32*>(
        reinterpret_cast<const u8*>(w) + 0x28);
}

// `ldr r1,[r0,#0xac]` at 0x002778B4: the cut-animation mode word.
inline s32 CutAnimation(const ScriptCameraWork* w) {
    return w->cut_animation;
}

// `vsub.f32 s0,s0,s3; vsub.f32 s1,s1,s2; bl 0x2820a4; vmul.f32 s3,s0,#57.29578`
// -- the angle used by 0x00276CAC's projection tail.
inline f32 YawBetween(const f32* a, const f32* b) {
    return ui_func_002820a4(a[0] - b[0], a[2] - b[2]) * kRadToDeg;
}

} // namespace

// ---------------------------------------------------------------------------
// 0x00276CAC: script/event camera cut evaluator
//
// Called once per frame from the FlowScript camera commands.  It maintains
// two camera modes:
//   * a "cut" camera built from the 16-entry preset tables at work+0xC8..
//     +0x208 (the default path), and
//   * two fixed camera rigs (work+0x64 and work+0x80) selected by mode 3/4.
// The tail always binds the projection at 0x0049F3F0 and emits the camera
// rotation through 0x0025C4D0.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00276cac, 4384)
void script_vm_func_00276cac() {
    UiEngine_GetContext();                                  // 0x00276CB8
    ScriptCameraWork* w = g_ScriptCameraWork;               // 0x00276CBC
    ScriptCamera* cam = reinterpret_cast<ScriptCamera*>(
        smt4::engine::g_MapSceneView);
    ScriptEventState* const ev_state = reinterpret_cast<ScriptEventState*>(
        smt4::engine::g_MapRuntimeState);

    // ---- 0x00276CC4..0x00276D4C: "snap from model" fast path -------------
    if (w->snap_positions != 0) {
        // 0x00276CE0 writes two vectors: the model position at out+0x00 and
        // the model target at out+0x0C (`ldm r0,{r1,r5,ip}` from sp+0x18).
        f32 model_out[0x44 / sizeof(f32)] = {};
        ui_func_002ae18c(model_out, w->model);              // 0x00276CE0
        const f32* model_pos = model_out;
        const f32* model_target = model_out + 3;

        Copy3(w->target, model_target);                     // 0x00276CF4..0x00276D08
        Copy3(w->eye, model_pos);                           // 0x00276D00..0x00276D14
        Copy3(w->blend_target, model_target);               // 0x00276D10
        Copy3(w->blend_eye, model_pos);                     // 0x00276D14

        const f32 yaw = YawBetween(model_pos, model_target); // 0x00276D18..0x00276D38
        script_vm_func_0025c4d0(model_pos[0], model_pos[1], model_pos[2], yaw);
        return;
    }

    // ---- 0x00276D50..0x00276F1C: shake and angle decay -------------------
    // `stm r4` copies the .rodata {0.6,0.6,0.6} damping triplet at 0x0040449C.
    f32 damp[3];
    Copy3(damp, g_MapRouteDamping);
    const f32 kShakeScale = 0.01f;                          // 0x3C23D70A
    const f32 kHalf = 0.5f;                                 // 0x3F000000

    if (w->shake_active == 0) {                             // 0x00276D70
        // 0x00276E44: clear the three shake offsets.
        w->shake_offset[0] = 0.0f;
        w->shake_offset[1] = 0.0f;
        w->shake_offset[2] = 0.0f;
    } else if (w->shake_timer == 0) {                       // 0x00276D7C
        w->shake_active = 0;                                // 0x00276D84
    } else {
        // 0x00276D8C..0x00276EAC: the three 16-bit amplitudes are converted
        // to float * 0.01 and integrated into the offsets.
        f32 amp[3];
        amp[0] = static_cast<f32>(w->shake_angle_x) * kShakeScale;
        amp[1] = static_cast<f32>(w->shake_angle_y) * kShakeScale;
        amp[2] = static_cast<f32>(w->shake_angle_z) * kShakeScale;

        for (s32 i = 0; i < 3; ++i) {
            const f32 v = amp[i];
            if (v == 0.0f) {
                continue;                                   // 0x00276DE8
            }
            const f32 rnd = ui_func_0027dc18();             // 0x00276DEC
            const f32 scaled = v * damp[i];
            f32 off = w->shake_offset[i];
            // 0x00276E0C..0x00276E20: `vmla s17,s1,s22` adds the 0.5 bias.
            const f32 step = (rnd * kHalf + kHalf) * v;
            if (scaled > fabsf(off)) {
                // 0x00276E54: kick the offset away from zero.
                const f32 delta = (ui_func_0027dc18() - kHalf) * step;
                off += delta * 2.0f;
            } else if (off <= 0.0f) {
                off += step;                                // 0x00276E30
            } else {
                off -= step;                                // 0x00276E38
            }
            if (off < -v) {                                 // 0x00276E8C
                off = -v;
            }
            if (off > v) {                                  // 0x00276EA0
                off = v;
            }
            w->shake_offset[i] = off;
        }
    }

    // 0x00276EBC..0x00276F1C: decay the three amplitudes by
    // amplitude/(shake_timer+5) using the unsigned divide at 0x002C615C.
    if (w->shake_timer > 0) {
        const u32 divisor = static_cast<u32>(w->shake_timer) + 5u;
        w->shake_angle_x = static_cast<u16>(
            w->shake_angle_x - ui_func_002c615c(w->shake_angle_x, divisor));
        w->shake_angle_y = static_cast<u16>(
            w->shake_angle_y - ui_func_002c615c(w->shake_angle_y, divisor));
        w->shake_angle_z = static_cast<u16>(
            w->shake_angle_z - ui_func_002c615c(w->shake_angle_z, divisor));
        w->shake_timer -= 1;                                // 0x00276F18
    }

    // ---- 0x00276F20: mode dispatch --------------------------------------
    const f32 kFar = 205000.0f;                             // 0x48483200
    const f32 kFovA = 45.0f;                                // 0x42340000
    const f32 kNearA = 20.0f;                               // 0x41A00000
    const f32 kAspect = 1.6666666f;                         // 0x3FD55555
    const f32 kNearFloor = 20.0f;
    const f32 kNearLow = 140.0f;                            // 0x430C0000
    const f32 kCutDistance = 180.0f;                        // 0x43340000

    if (w->mode == 3) {                                     // 0x00276F40
        // 0x00277014: fixed rig A (work+0x64/+0x70); the listing passes the
        // literal clip pair (100.0f, 1.0f).
        AsdCamera_SetClipRange(g_AsdProjection, 100.0f, 1.0f);
        AsdCamera_SetPerspective(g_AsdProjection, 1, w->alt_fov_a,
                                 kNearA, kFar, kAspect);
        script_vm_func_0025c470(w->alt_eye_a, w->alt_target_a);
        AsdCamera_BindProjection(g_AsdProjection);
        const f32 yaw = YawBetween(w->alt_eye_a, w->alt_target_a);
        script_vm_func_0025c4d0(w->alt_eye_a[0], w->alt_eye_a[1],
                                w->alt_eye_a[2], yaw);
        return;
    }
    if (w->mode == 4) {                                     // 0x00276F4C
        // 0x0027709C: fixed rig B (work+0x80/+0x8C) including an up vector.
        AsdCamera_SetClipRange(g_AsdProjection, 100.0f, 1.0f);
        AsdCamera_SetPerspective(g_AsdProjection, 1, kFovA,
                                 kNearA, kFar, kAspect);
        AsdCamera_LookAt(g_AsdProjection, w->alt_eye_b, w->alt_target_b,
                         CameraUp1c(w));        // `add r3,r0,#0x1c`
        script_vm_func_0025c470(w->alt_eye_b, w->alt_target_b);
        AsdCamera_BindProjection(g_AsdProjection);
        const f32 yaw = YawBetween(w->alt_eye_b, w->alt_target_b);
        script_vm_func_0025c4d0(w->alt_eye_b[0], w->alt_eye_b[1],
                                w->alt_eye_b[2], yaw);
        return;
    }

    if (w->snap_from_model != 0) {                          // 0x00276F68
        // 0x00276F70..0x002771C4: consume the cut block built by an earlier
        // snap frame.  The near plane follows the distance between the
        // blended eye and the live camera (0x00276F90 call to 0x00287D54).
        f32 blend_eye[3] = {w->blend_eye[0], 0.0f, w->blend_eye[2]};
        f32 camera_pos[3] = {cam->position[0], 0.0f, cam->position[2]};
        const f32 eye_distance = Distance3(blend_eye, camera_pos);

        f32 near_plane;
        if (kCutDistance <= eye_distance) {
            near_plane = kNearLow;                          // 0x00277138
        } else {
            near_plane = eye_distance - 40.0f;              // 0x00276FA0
            if (near_plane < kNearFloor) {
                near_plane = kNearFloor;
            }
        }
        AsdCamera_SetClipRange(g_AsdProjection, near_plane, w->far_clip);

        script_vm_func_0025c470(w->cut.eye, w->cut.target); // 0x0027714C
        AsdCamera_BindProjection(g_AsdProjection);
        const f32 yaw = YawBetween(w->cut.eye, w->cut.target);
        script_vm_func_0025c4d0(w->cut.eye[0], w->cut.eye[1],
                                w->cut.eye[2], yaw);

        // 0x002771A0..0x002771B8: publish the cut into the blend pair.
        Copy3(w->blend_eye, w->cut.eye);
        Copy3(w->blend_target, w->cut.target);
        return;
    }

    if (w->mode == 6 || w->mode == 0xF) {                   // 0x002771C8
        // 0x002771F4: direct application of the blend pair.
        AsdCamera_LookAt(g_AsdProjection, w->blend_eye, w->blend_target,
                         CameraUp1c(w));        // `add r3,r0,#0x1c`
        script_vm_func_0025c470(w->blend_eye, w->blend_target);
        AsdCamera_BindProjection(g_AsdProjection);
        const f32 yaw = YawBetween(w->blend_eye, w->blend_target);
        script_vm_func_0025c4d0(w->blend_eye[0], w->blend_eye[1],
                                w->blend_eye[2], yaw);
        return;
    }

    // ---- 0x002771D4..0x0027728C: choose the preset index -----------------
    UiEngine_GetContext();                                  // 0x002771D4
    s32 preset = static_cast<s32>(w->saved_camera_id);
    if (w->camera_id != -1) {
        preset = w->camera_id;
    } else {
        // 0x00277230 jump table indexed by (cut_animation + 3); six entries
        // read from the raw words at 0x00277244.
        switch (CutAnimation(w) + 3) {
            case 0: preset = 5; break;                       // 0x0027725C
            case 1: preset = 9; break;                       // 0x0027726C
            case 2: preset = 8; break;                       // 0x00277264
            case 3: preset = 5 + w->preset_bias; break;      // 0x00277274
            case 4: preset = 6; break;                       // 0x00277280
            case 5: preset = 10; break;                      // 0x00277288
            default: break;
        }
    }

    // ---- 0x0027728C..0x00277510: build the cut eye/target ----------------
    w->target[0] = cam->position[0];
    w->target[2] = cam->position[2];

    f32 angle = w->angle * kDegToRad;
    f32 sin_a = script_vm_func_0028277c(angle);             // 0x002772AC
    f32 cos_a = script_vm_func_00282600(angle);             // 0x002772D4

    w->eye[0] = cam->position[0] - sin_a * w->preset_distance[preset];
    w->eye[2] = cam->position[2] - cos_a * w->preset_distance[preset];
    w->target[1] = cam->position[1] + w->preset_offset_y[preset];
    w->eye[1] = cam->position[1] + w->preset_eye_y[preset];

    // 0x00277318..0x002773B8: the second (90 degrees later) tangent shifts
    // both endpoints sideways by preset_side[preset].
    angle = (w->angle - 90.0f) * kDegToRad;
    sin_a = script_vm_func_0028277c(angle);
    w->target[0] += sin_a * w->preset_side[preset];
    cos_a = script_vm_func_00282600(angle);
    w->target[2] += cos_a * w->preset_side[preset];
    sin_a = script_vm_func_0028277c(angle);
    w->eye[0] += sin_a * w->preset_side[preset];
    cos_a = script_vm_func_00282600(angle);
    w->eye[2] += cos_a * w->preset_side[preset];

    // 0x002773C0..0x00277410: distance and height delta.
    f32 distance = Distance3(w->eye, w->target);
    if (distance < 0.01f) {                                 // 0x002773FC
        distance = 0.01f;
    }

    f32 delta = w->desired_height - w->current_height;
    if (w->hold_flag == 0) {
        if (delta > kNearFloor) {                           // +20
            delta = kNearFloor;
        } else if (delta < -kNearFloor) {                   // -20
            delta = -kNearFloor;
        }
    }
    // 0x00277438..0x00277450: eye Y is shifted by both the old offset and the
    // new delta; the accumulated offset is stored back.
    w->eye[1] = w->eye[1] + w->current_height + delta;
    w->current_height = w->current_height + delta;

    // 0x00277454..0x00277498: floor/ceiling clamp unless the cut tracks a
    // target.
    if (w->track_target == 0) {
        const f32 base_y = cam->position[1];
        if (w->eye[1] < base_y + 5.0f) {
            w->eye[1] = base_y + 5.0f;
        }
        if (w->eye[1] > base_y + 350.0f) {
            w->eye[1] = base_y + 350.0f;
        }
    }

    // 0x0027749C..0x00277510: renormalize the eye around the target at the
    // requested distance.  The listing stores the direction in s17..s19.
    f32 dir[3];
    {
        f32 v[3] = {w->eye[0] - w->target[0],
                    w->eye[1] - w->target[1],
                    w->eye[2] - w->target[2]};
        const f32 length = sqrtf(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]);
        const f32 inv = 1.0f / length;
        dir[0] = v[0] * inv;
        dir[1] = v[1] * inv;
        dir[2] = v[2] * inv;
    }
    w->eye[0] = w->target[0] + dir[0] * distance;
    w->eye[1] = w->target[1] + dir[1] * distance;
    w->eye[2] = w->target[2] + dir[2] * distance;

    if (w->track_target != 0 && CutAnimation(w) <= 0) {
        script_vm_func_001f82ac();                          // 0x00277520..0x00277528
    }

    // ---- 0x0027752C..0x00277664: visible point and its distance ----------
    f32 source[3];
    if (w->mode == 0 &&
        ev_state->field_3cc == 0 &&
        ev_state->field_370 != 1 &&
        w->track_target == 0) {
        script_vm_func_00266e88(w->eye, w->target, source); // 0x002775AC
    } else {
        Copy3(source, w->eye);                              // 0x00277568
    }

    f32 aim[3] = {w->target[0] - source[0],
                  w->target[1] - source[1],
                  w->target[2] - source[2]};
    f32 aim_length = sqrtf(aim[0] * aim[0] + aim[1] * aim[1] + aim[2] * aim[2]);
    f32 inv_aim;
    if (aim_length <= 1.0e-4f) {                            // 0x002775E8 (0x38D1B717)
        // 0x00277620..0x00277660: the fallback re-normalizes target-eye but
        // keeps the tiny s16 length for the later clamp comparisons.
        aim[0] = w->target[0] - w->eye[0];
        aim[1] = w->target[1] - w->eye[1];
        aim[2] = w->target[2] - w->eye[2];
        const f32 fallback_length =
            sqrtf(aim[0] * aim[0] + aim[1] * aim[1] + aim[2] * aim[2]);
        inv_aim = 1.0f / fallback_length;
    } else {
        inv_aim = 1.0f / aim_length;
    }
    dir[0] = aim[0] * inv_aim;
    dir[1] = aim[1] * inv_aim;
    dir[2] = aim[2] * inv_aim;

    if (w->track_target == 0) {
        // 0x00277670..0x002776FC: reject distances shorter than the preset
        // rig diagonal (0x00287D54 with preset_height offsets).
        const f32 rig_a[3] = {0.0f, w->preset_offset_y[preset], 0.0f};
        const f32 rig_b[3] = {0.0f, w->preset_eye_y[preset],
                              w->preset_distance[preset]};
        const f32 rig_distance = Distance3(rig_a, rig_b);
        if (aim_length > rig_distance) {
            aim_length = rig_distance;
            f32 v[3] = {w->target[0] - w->eye[0],
                        w->target[1] - w->eye[1],
                        w->target[2] - w->eye[2]};
            const f32 len = sqrtf(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]);
            const f32 inv = 1.0f / len;
            dir[0] = v[0] * inv;
            dir[1] = v[1] * inv;
            dir[2] = v[2] * inv;
        }
        if (aim_length < kFovA) {                           // 45.0, 0x002776F0
            aim_length = kFovA;
            // 0x00277700..0x00277748 re-normalises using target - eye
            // (`s3=[r0+0x40]`, `s5=[r0+0x34]` with r0 = work).
            f32 v[3] = {w->target[0] - w->eye[0],
                        w->target[1] - w->eye[1],
                        w->target[2] - w->eye[2]};
            const f32 len = sqrtf(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]);
            const f32 inv = 1.0f / len;
            dir[0] = v[0] * inv;
            dir[1] = v[1] * inv;
            dir[2] = v[2] * inv;
        }
    }

    // ---- 0x0027774C..0x002777C8: blend distance / speed ------------------
    if (w->hold_flag == 0 && w->track_target == 0 && w->hold_timer <= 0) {
        // 0x0027777C..0x00277780: bgt/bhs both target the equal/zero-speed
        // path, so equality is included.
        if (w->blend_distance >= aim_length) {
            w->blend_distance = aim_length;
            w->blend_speed = 0.0f;
        } else {
            w->blend_speed += 8.0f;                          // 0x00277788 (0x41000000)
            if (w->blend_speed > 40.0f) {
                w->blend_speed = 40.0f;
            }
            w->blend_distance += w->blend_speed;
            if (w->blend_distance > aim_length) {
                w->blend_distance = aim_length;
            }
        }
    } else {
        w->blend_distance = aim_length;                      // 0x002777C8
        w->blend_speed = 0.0f;
    }

    // 0x002777D0..0x002777F8: eye = target - dir * blended distance.
    f32 eye_out[3];
    eye_out[0] = w->target[0] - dir[0] * w->blend_distance;
    eye_out[1] = w->target[1] - dir[1] * w->blend_distance;
    eye_out[2] = w->target[2] - dir[2] * w->blend_distance;

    // ---- 0x002777FC..0x0027782C: hold frame ------------------------------
    if (w->hold_flag != 0) {
        Copy3(w->blend_target, w->target);
        w->hold_timer = 0;
        w->hold_flag = 0;
        Copy3(w->blend_eye, eye_out);
        goto camera_tail;
    }

    // ---- 0x00277830..0x002778B0: explicit camera id => 0.125 blend -------
    if (w->camera_id != -1) {
        const f32 t = 0.125f;                                // 0x3E000000
        w->blend_eye[0] += (eye_out[0] - w->blend_eye[0]) * t;
        w->blend_eye[1] += (eye_out[1] - w->blend_eye[1]) * t;
        w->blend_eye[2] += (eye_out[2] - w->blend_eye[2]) * t;
        w->blend_target[0] += (w->target[0] - w->blend_target[0]) * t;
        w->blend_target[1] += (w->target[1] - w->blend_target[1]) * t;
        w->blend_target[2] += (w->target[2] - w->blend_target[2]) * t;
        goto camera_tail;
    }

    // ---- 0x002778B4: animation-mode switch (jump table at 0x002778CC) ----
    // Raw entries: {0x277AC4, 0x277AC4, 0x277AC4, 0x2778E4, 0x277AC4,
    // 0x277BBC} for (work+0xAC)+3 == 0..5.
    switch (CutAnimation(w) + 3) {
        case 0:
        case 1:
        case 2:
        case 4: {
            // 0x00277AC4: tracking snaps both endpoints; otherwise the eye
            // uses a 1/3 blend (`vldr s3,=0x3EAAAAAB`) and the target a 1/2
            // blend (`vldr s22,=0x3F000000`, 0x00277B68..0x00277BB4).
            if (w->track_target != 0) {
                Copy3(w->blend_eye, eye_out);
                Copy3(w->blend_target, w->target);
            } else {
                const f32 t_eye = 0.33333334f;               // 0x3EAAAAAB
                const f32 t_target = 0.5f;                   // 0x3F000000
                w->blend_eye[0] += (eye_out[0] - w->blend_eye[0]) * t_eye;
                w->blend_eye[1] += (eye_out[1] - w->blend_eye[1]) * t_eye;
                w->blend_eye[2] += (eye_out[2] - w->blend_eye[2]) * t_eye;
                w->blend_target[0] +=
                    (w->target[0] - w->blend_target[0]) * t_target;
                w->blend_target[1] +=
                    (w->target[1] - w->blend_target[1]) * t_target;
                w->blend_target[2] +=
                    (w->target[2] - w->blend_target[2]) * t_target;
            }
            break;
        }
        case 3: {
            // 0x002778E4: hold timer first, then two different blend paths.
            if (w->hold_timer > 0) {
                w->hold_timer -= 1;                          // 0x002778F0
                if (w->track_target != 0) {
                    // 0x00277904..0x00277970: snap both endpoints.
                    Copy3(w->blend_eye, eye_out);
                    Copy3(w->blend_target, w->target);
                    w->hold_timer = 0;                       // 0x00277964
                } else {
                    // 0x00277974..0x002779E0: 1/2 blend on both endpoints.
                    const f32 t = 0.5f;                      // 0x3F000000
                    w->blend_eye[0] += (eye_out[0] - w->blend_eye[0]) * t;
                    w->blend_eye[1] += (eye_out[1] - w->blend_eye[1]) * t;
                    w->blend_eye[2] += (eye_out[2] - w->blend_eye[2]) * t;
                    w->blend_target[0] +=
                        (w->target[0] - w->blend_target[0]) * t;
                    w->blend_target[1] +=
                        (w->target[1] - w->blend_target[1]) * t;
                    w->blend_target[2] +=
                        (w->target[2] - w->blend_target[2]) * t;
                }
            } else {
                // 0x002779E4..0x00277A20: target snaps in every case.
                Copy3(w->blend_target, w->target);
                if (w->track_target != 0) {
                    // 0x00277A30..0x00277A68: eye 2/3 on all three axes.
                    const f32 t = 0.6666667f;                // 0x3F2AAAAB
                    w->blend_eye[0] += (eye_out[0] - w->blend_eye[0]) * t;
                    w->blend_eye[1] += (eye_out[1] - w->blend_eye[1]) * t;
                    w->blend_eye[2] += (eye_out[2] - w->blend_eye[2]) * t;
                } else {
                    // 0x00277A88..0x00277ABC: x/z 2/3, y 1/3.
                    const f32 t_xz = 0.6666667f;             // 0x3F2AAAAB
                    const f32 t_y = 0.33333334f;             // 0x3EAAAAAB
                    w->blend_eye[0] += (eye_out[0] - w->blend_eye[0]) * t_xz;
                    w->blend_eye[1] += (eye_out[1] - w->blend_eye[1]) * t_y;
                    w->blend_eye[2] += (eye_out[2] - w->blend_eye[2]) * t_xz;
                }
            }
            break;
        }
        case 5: {
            // 0x00277BBC: tracking snaps both endpoints; otherwise both use a
            // 1/2 blend (0x00277C38..0x00277C38).
            if (w->track_target != 0) {
                Copy3(w->blend_eye, eye_out);
                Copy3(w->blend_target, w->target);
            } else {
                const f32 t = 0.5f;
                w->blend_eye[0] += (eye_out[0] - w->blend_eye[0]) * t;
                w->blend_eye[1] += (eye_out[1] - w->blend_eye[1]) * t;
                w->blend_eye[2] += (eye_out[2] - w->blend_eye[2]) * t;
                w->blend_target[0] +=
                    (w->target[0] - w->blend_target[0]) * t;
                w->blend_target[1] +=
                    (w->target[1] - w->blend_target[1]) * t;
                w->blend_target[2] +=
                    (w->target[2] - w->blend_target[2]) * t;
            }
            break;
        }
        default:
            // 0x002778C8 `b 0x277CA8`.
            break;
    }

camera_tail:
    // ---- 0x00277CA8..0x00277D64: projection + rotation -------------------
    AsdCamera_BindProjection(g_AsdProjection);              // 0x00277CAC

    f32 camera_flat[3] = {w->blend_eye[0], 0.0f, w->blend_eye[2]};
    f32 camera_pos[3] = {cam->position[0], 0.0f, cam->position[2]};
    const f32 eye_distance = Distance3(camera_flat, camera_pos);

    f32 near_plane;
    if (eye_distance >= kCutDistance) {
        near_plane = kNearLow;                              // 0x00277D0C
    } else {
        near_plane = eye_distance - 40.0f;
        if (near_plane < kNearFloor) {
            near_plane = kNearFloor;
        }
    }
    AsdCamera_SetClipRange(g_AsdProjection, near_plane, w->far_clip);

    const f32 kNearCut = 10.0f;                             // 0x41200000 (0x00277D3C)
    AsdCamera_SetPerspective(g_AsdProjection, 1, w->preset_fov[preset],
                             kNearCut, kFar, kAspect);

    if (w->mode != 7 && w->mode != 8 && w->mode != 9) {
        script_vm_func_0025c470(w->blend_eye, w->blend_target);
    } else {
        // 0x00277DA8: explicit up vector at work+0x28.
        AsdCamera_LookAt(g_AsdProjection, w->blend_eye, w->blend_target,
                         CameraUp28(w));
    }

    const f32 yaw = YawBetween(w->blend_eye, w->blend_target);
    script_vm_func_0025c4d0(w->blend_eye[0], w->blend_eye[1],
                            w->blend_eye[2], yaw);
}

// ---------------------------------------------------------------------------
// 0x002C8C90: world-map route camera
//
// States: 0 = arm the route, 1 = follow the 20-frame route bank selected by
// the current map section (event state +0x218), 2 = post-route/free camera.
// Every marker path is drawn through 0x0025BFFC and every map icon through
// 0x002920E4; the routine finishes by easing camera position toward the route
// position and mirroring it into the previous-position slot.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x002c8c90, 3656)
void script_vm_func_002c8c90() {
    // 0x002C8C94..0x002C8CDC: four 0xA0-byte route banks copied to the
    // stack in the order 0x004045AC, 0x0040464C, 0x004046EC, 0x0040478C.
    MapRouteFrame banks[4][20];
    ui_func_002bcf58(&banks[0][0], &g_MapRouteBanks[0][0], 0xA0);
    ui_func_002bcf58(&banks[1][0], &g_MapRouteBanks[1][0], 0xA0);
    ui_func_002bcf58(&banks[2][0], &g_MapRouteBanks[2][0], 0xA0);
    ui_func_002bcf58(&banks[3][0], &g_MapRouteBanks[3][0], 0xA0);

    ScriptCamera* cam = reinterpret_cast<ScriptCamera*>(
        smt4::engine::g_MapSceneView);
    ScriptEventState* ev = reinterpret_cast<ScriptEventState*>(
        smt4::engine::g_MapRuntimeState);

    const f32 start_x = cam->route_position[0];             // s18, 0x002C8D00
    const f32 start_y = cam->route_position[1];             // s17
    const f32 start_z = cam->route_position[2];             // s16

    const bool not_in_progress = ev->field_3cc == 0 && ev->field_021 != 0;

    if (cam->state == 0) {
        // 0x002C8D30: arm the route; the +0x54 slot selects the destination
        // (4 for the first section, 0x16..0x18 for the later ones).
        cam->field_06c = 0;
        switch (ev->field_218) {
            case 0: cam->field_054 = 4; break;              // 0x002C8D3C
            case 1: cam->field_054 = 0x16; break;           // 0x002C8D48
            case 2: cam->field_054 = 0x17; break;           // 0x002C8D54
            case 3: cam->field_054 = 0x18; break;           // 0x002C8D60
            default: break;
        }
        cam->field_058 = 3.0f;                              // 0x40400000
        cam->field_05c = 1;
        cam->state = 1;                                     // 0x002C8D7C
        cam->frame = 0;                                     // 0x002C8D80
        goto tail_calc;                                     // 0x002C8D84
    } else if (cam->state == 1) {
        // 0x002C8D88: advance one 20-frame route entry.
        cam->frame += 1;
        if (cam->frame < 20) {
            const s32 section = ev->field_218;
            MapRouteFrame* frame = &banks[section][cam->frame];

            if (frame->has_segment != 0) {                  // 0x002C8EB4
                script_vm_func_0025bffc(static_cast<f32>(frame->segment_x),
                                        static_cast<f32>(frame->segment_y));
            }

            const f32 amount = static_cast<f32>(frame->distance);
            const f32 angle = cam->route_angle * kDegToRad;
            const f32 sin_a = script_vm_func_0028277c(angle);
            cam->route_position[0] += sin_a * amount;       // 0x002C8F00
            const f32 cos_a = script_vm_func_00282600(angle);
            cam->route_position[2] += cos_a * amount;       // 0x002C8F20

            // 0x002C8F24..0x002C8F44: keep the route point inside the map
            // geometry (helper at 0x0027FAB8).
            f32 projected[3];
            script_vm_func_0027fab8(projected, cam->route_position[0],
                                    cam->route_position[1],
                                    cam->route_position[2]);
            Copy3(cam->route_position, projected);

            // 0x002C8F48..0x002C8F50: remember where the route started.
            cam->saved_position[0] = start_x;
            cam->saved_position[1] = start_y;
            cam->saved_position[2] = start_z;

            if (not_in_progress) {
                // 0x002C8F74: collision with map geometry resets the
                // accumulated distance, otherwise it eases up to 20.
                if (script_vm_func_0027f6fc(cam->route_position,
                                            cam->saved_position) != 0) {
                    cam->field_068 = 0.0f;
                } else {
                    const f32 grown = cam->field_068 + 2.0f;
                    cam->field_068 = grown <= 20.0f ? grown : 20.0f;
                }
            }

            // 0x002C8FB8: `ldr r0,[sb]` compares the first event word with
            // 0x24 and asks 0x0025A378(2,5) for a valid transfer.
            if (*reinterpret_cast<const s32*>(ev) != 0x24 &&
                camp_func_0025a378(2, 5)) {
                const f32 travelled = Distance3(cam->saved_position,
                                                cam->route_position);
                cam->field_160 -= travelled;                // 0x002C9004
            }

            // 0x002C9008: the collision mask from 0x0028075C.
            const s32 mask = script_vm_func_0028075c(cam->route_position);
            if ((mask & 2) != 0) {
                const f32 travelled = Distance3(cam->saved_position,
                                                cam->route_position);
                cam->field_15c -= travelled;                // 0x002C9044
                ev->field_033 = 4;                          // 0x002C9048
            } else {
                if (cam->field_15c > 0.0f) {
                    const f32 travelled = Distance3(cam->saved_position,
                                                    cam->route_position);
                    cam->field_15c -= travelled;            // 0x002C90B8
                }
                if (cam->field_15c < 0.0f) {
                    cam->field_15c = 0.0f;                  // 0x002C90D0
                }
                ev->field_033 = 0xFF;                       // 0x002C90D8
            }

            // 0x002C90DC..0x002C9138: ease position toward the route point
            // by 1/3 and mirror the result into previous/saved slots.
            const f32 t = 0.33333334f;                      // 0x3EAAAAAB
            cam->position[0] += (cam->route_position[0] - cam->position[0]) * t;
            cam->position[1] += (cam->route_position[1] - cam->position[1]) * t;
            cam->position[2] += (cam->route_position[2] - cam->position[2]) * t;
            cam->previous_position[0] = cam->position[0];
            cam->previous_position[1] = cam->position[1];
            cam->previous_position[2] = cam->position[2];
            cam->saved_position[0] = start_x;
            cam->saved_position[1] = start_y;
            cam->saved_position[2] = start_z;
        }

        // ---- 0x002C913C..0x002C9538: per-section icon pass ----------------
        // s22 = 130, s23 = 60, s21 = 150; `emit_icon` reproduces the
        // yaw-based `pos + (sin*step, rise, cos*step)` placement used by all
        // eight 0x002920E4 calls.
        const f32 kIconRise = 130.0f;                       // 0x43020000
        const f32 kIconNearStep = 60.0f;                    // 0x42700000
        const f32 kIconFarStep = 150.0f;                    // 0x43160000
        auto emit_icon = [&](u32 id, f32 step, f32 rise) {
            const f32 angle = cam->yaw * kDegToRad;
            const f32 sin_yaw = script_vm_func_0028277c(angle);
            const f32 cos_yaw = script_vm_func_00282600(angle);
            script_vm_func_002920e4(id,
                                    cam->position[0] + sin_yaw * step,
                                    cam->position[1] + rise,
                                    cam->position[2] + cos_yaw * step);
        };

        switch (ev->field_218) {
            case 0:                                         // 0x002C9174
                if (cam->frame == 3) {
                    emit_icon(0x010001F0, kIconFarStep, kIconRise);
                    emit_icon(0x0100022C + static_cast<u32>(
                                   ui_func_00297004(0, 2)),
                              kIconNearStep, kIconFarStep);
                    script_vm_func_0027ff10(-1);            // 0x002C922C
                }
                if (cam->frame == 6) {                      // 0x002C9230
                    ui_func_0025beb8();
                    if (cam->frame == 6) {
                        script_vm_func_00287c44(4, 8, 0);   // 0x002C9260
                    }
                }
                break;
            case 1:                                         // 0x002C9264
                if (cam->frame == 3) {
                    emit_icon(0x010001F1, kIconFarStep, kIconRise);
                    emit_icon(0x0100022F + static_cast<u32>(
                                   ui_func_00297004(0, 2)),
                              kIconNearStep, kIconFarStep);
                    script_vm_func_0027ff10(-1);            // 0x002C931C
                }
                if (cam->frame == 6) {                      // 0x002C9320
                    ui_func_0025beb8();                     // 0x002C9410
                }
                break;
            case 2:                                         // 0x002C9334
                if (cam->frame == 2) {
                    emit_icon(0x01000232 + static_cast<u32>(
                                   ui_func_00297004(0, 2)),
                              kIconNearStep, kIconFarStep);
                }
                if (cam->frame == 3) {
                    emit_icon(0x010001F2, kIconFarStep, kIconRise);
                    script_vm_func_0027ff10(-1);            // 0x002C93F8
                }
                if (cam->frame == 4) {                      // 0x002C93FC
                    ui_func_0025beb8();                     // 0x002C9410
                }
                break;
            case 3:                                         // 0x002C9440
                if (cam->frame == 2) {
                    emit_icon(0x01000235 + static_cast<u32>(
                                   ui_func_00297004(0, 2)),
                              kIconNearStep, kIconFarStep);
                }
                if (cam->frame == 3) {
                    emit_icon(0x010001F3, kIconFarStep, kIconRise);
                    script_vm_func_0027ff10(-1);            // 0x002C9504
                }
                if (cam->frame == 6) {                      // 0x002C9508
                    ui_func_0025beb8();
                    if (cam->frame == 6) {
                        script_vm_func_00287c44(6, 0x14, 0); // 0x002C9538
                    }
                }
                break;
            default:
                break;
        }

        // 0x002C953C..0x002C966C: frame-3 arrival bookkeeping and the
        // frame-15 transfer completion.  These reads/writes use the event
        // state (sb), not the camera.
        if (cam->frame == 3) {
            cam->field_16c = -1;                            // 0x002C9554
            cam->field_168 = 0;                             // 0x002C955C
            ev->field_17c = 1;                              // 0x002C9560
            ev->arrival_x = cam->position[0];               // 0x002C9568
            ev->arrival_y = cam->position[1];
            ev->arrival_z = cam->position[2];
            ev->arrival_yaw = cam->yaw;                     // 0x002C9574
            g_MapEventState.field_090 = 0;                 // 0x002C9578
            g_MapEventState.field_092 = 0;
        }

        if (g_MapEventState.field_07c != 0) {
            // 0x002C958C..0x002C961C: arrival counter and section window.
            ev->arrival_x = cam->position[0];
            ev->arrival_y = cam->position[1];
            ev->arrival_z = cam->position[2];
            ev->arrival_yaw = cam->yaw;

            s32 arrival = static_cast<s16>(g_MapEventState.field_090 + 1);
            g_MapEventState.field_090 = static_cast<s16>(arrival);
            g_MapEventState.field_092 = 0;

            switch (ev->field_218) {
                case 0:
                    if (static_cast<u32>(arrival - 5) <= 3) {
                        g_MapEventState.field_092 = 1;
                    }
                    break;
                case 1:
                    if (static_cast<u32>(arrival - 3) <= 3) {
                        g_MapEventState.field_092 = 1;
                    }
                    break;
                case 2:
                    if (static_cast<u32>(arrival - 6) <= 5) {
                        g_MapEventState.field_092 = 1;
                    }
                    break;
                case 3:
                    if (static_cast<u32>(arrival - 5) <= 4) {
                        g_MapEventState.field_092 = 1;
                    }
                    break;
                default:
                    break;
            }
        }

        if (g_MapEventState.field_0a0 == 0 &&
            g_MapEventState.field_094 > 0) {
            ev->field_1a0 = 1;                              // 0x002C9634
            ev->field_1a4 = 0;
            goto after_state2;
        }

        if (g_MapEventState.field_094 == 0 && cam->frame > 0xE) {
            // 0x002C9658: route complete; next frame runs state 2.
            ev->field_17c = 0;
            cam->field_168 = 0;
            cam->state += 1;                                // 0x002C9660
            cam->frame = 0;
        }

        goto after_state2;
    } else if (cam->state == 2) {
        // 0x002C9670: post-route / map transfer state.
        cam->frame += 1;

        // State 2 arrives with s21 = 0.0f (0x002C8D18); only state 1 reloads
        // s21 with 150.0f (0x002C9148).
        const f32 kIconDistance = 0.0f;                     // 0x00000000
        if (*reinterpret_cast<const s32*>(ev) != 0x24 &&
            camp_func_0025a378(2, 5) &&
            cam->field_160 < kIconDistance) {
            func_002565b0(2, 5, 5);                         // 0x002C96C4
            cam->field_160 = 1000.0f;                       // 0x447A0000
            func_00256524(0xF, 0x50);                       // 0x002C96DC
            const u32 icon = script_vm_func_002920e4(
                0x01000186, cam->position[0], cam->position[1],
                cam->position[2]);                          // 0x002C96F0
            cam->field_18c = icon;                          // 0x002C96FC
            cam->field_190 = 0x14;
        }

        if (cam->field_15c < kIconDistance) {
            // 0x002C9718: choose 1500 for the transfer from section 5/9,
            // otherwise 500, then request state 0x20.
            cam->field_15c =
                (*reinterpret_cast<const s32*>(ev) == 5 &&
                 *(reinterpret_cast<const s32*>(ev) + 1) == 9)
                    ? 1500.0f                               // 0x44BB8000
                    : 500.0f;                               // 0x43FA0000
            script_vm_func_0027fd08(0x20);
        } else {
            // 0x002C973C: route-to-map projection and the second icon pass.
            f32 out_x = 0.0f;
            f32 out_y = 0.0f;
            script_vm_func_0027fbc8(&out_x, &out_y, 0);

            const f32 left = -130.0f;                       // 0xC3020000
            const f32 right = 30.0f;                        // 0x41F00000
            const f32 forward = 20.0f;                      // 0x41A00000 (s22)

            switch (ev->field_218) {
                case 0:
                    if (cam->frame == 5) {
                        script_vm_func_0027ff10(-1);        // 0x002C978C
                        ui_func_0025beb8();
                        script_vm_func_0025bffc(left, forward);
                    }
                    if (cam->frame == 6) {
                        script_vm_func_0025bffc(right, forward); // 0x002C98A4
                        ui_func_0025beb8();
                    }
                    break;
                case 1:
                    if (cam->frame == 5) {
                        script_vm_func_0027ff10(-1);        // 0x002C97D0
                        ui_func_0025beb8();
                        script_vm_func_0025bffc(right, forward);
                    }
                    if (cam->frame == 6) {
                        ui_func_0025beb8();                 // 0x002C9844
                        script_vm_func_0025bffc(left, forward);
                    }
                    break;
                case 2:
                    if (cam->frame == 5) {
                        script_vm_func_0027ff10(-1);        // 0x002C9814
                        ui_func_0025beb8();
                        script_vm_func_0025bffc(right, forward);
                    }
                    if (cam->frame == 6) {
                        ui_func_0025beb8();                 // 0x002C9844
                        script_vm_func_0025bffc(left, forward);
                    }
                    break;
                case 3:
                    if (cam->frame == 5) {
                        script_vm_func_0027ff10(-1);        // 0x002C9874
                        ui_func_0025beb8();
                        script_vm_func_0025bffc(left, forward);
                    }
                    if (cam->frame == 6) {
                        script_vm_func_0025bffc(right, forward); // 0x002C98A4
                        ui_func_0025beb8();
                    }
                    break;
                default:
                    break;
            }

            // 0x002C98BC: leave the state when the transfer finished and the
            // shop/map input helper accepts the section-specific threshold.
            s32 frame_threshold = -1;
            switch (ev->field_218) {
                case 0: frame_threshold = 6; break;         // 0x002C98E4
                case 1: frame_threshold = 3; break;         // 0x002C9914
                case 2:                                     // 0x002C9938
                case 3: frame_threshold = 8; break;         // 0x002C995C
                default: break;                             // 0x002C98E0
            }
            if (frame_threshold >= 0 && cam->frame > frame_threshold) {
                if (shop_func_00256750()) {
                    cam->state = 0;                        // 0x002C9908
                    cam->frame = 0;
                    goto after_state2;
                }
            }

            // 0x002C997C: once the projected cursor leaves the centre box (or
            // the transfer runs past frame 10), commit the settled camera.
            const bool centred =
                out_x >= -0.5f && out_x <= 0.5f &&
                out_y >= -0.5f && out_y <= 0.5f;
            if (!centred || cam->frame > 10) {
                if (cam->frame > 10) {
                    cam->field_188 = 1;                    // 0x002C99CC
                } else if (ev->field_218 == 0 || ev->field_218 == 1) {
                    cam->field_188 = 2;                    // 0x002C99E4
                } else if (ev->field_218 == 2 || ev->field_218 == 3) {
                    cam->field_188 = 4;                    // 0x002C99F4
                }
                cam->field_068 = 0.0f;                     // 0x002C99BC
                cam->field_058 = 5.0f;                     // 0x002C99C0
                script_vm_func_0027fd08(1);                // 0x002C99FC
            }
        }
    }

after_state2:
    if (cam->state != 1) {
        script_vm_func_0028075c(cam->route_position);      // 0x002C9A18
    }

tail_calc:
    // 0x002C9A1C..0x002C9A34: final collision/angle pass.  0x002805D4
    // ignores the camera pointer it receives in r0.
    script_vm_func_002805d4(cam, cam->position[0], cam->position[2]);
    script_vm_func_00280bf8();

    // 0x002C9A38..0x002C9A80: ease position toward route_position (1/3 for
    // X/Z, 1/6 for Y) and mirror it into the previous-position slot.
    const f32 t_xz = 0.33333334f;                           // 0x3EAAAAAB
    const f32 t_y = 0.16666667f;                            // 0x3E2AAAAB
    cam->position[0] += (cam->route_position[0] - cam->position[0]) * t_xz;
    cam->position[1] += (cam->route_position[1] - cam->position[1]) * t_y;
    cam->position[2] += (cam->route_position[2] - cam->position[2]) * t_xz;
    cam->previous_position[0] = cam->position[0];
    cam->previous_position[1] = cam->position[1];
    cam->previous_position[2] = cam->position[2];

    // 0x002C9A8C..0x002C9AC8
    cam->saved_position[0] = start_x;
    cam->saved_position[1] = start_y;
    cam->saved_position[2] = start_z;
}

// ---------------------------------------------------------------------------
// 0x00399F28: bottom-screen map cell grid renderer
//
// Draws the 5x7 cell map (0x40-pixel cells over the 320x400 bottom screen),
// marks the cells covered by the player-centred plus, and submits one
// 0x002B06A0 tile per visible cell.  The three modes are the three map zoom
// levels 0x65/0x66/0x67; each has its own world->screen alignment constants.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00399f28, 3928)
void script_vm_func_00399f28(WorldMapWork* work) {
    UiEngine_GetContext();                                  // 0x00399F34

    // `add r0,r0,#0x100; add r0,r0,#0x62` (0x00399F44) forms work+0x162 and
    // passes it to the four accessors, which ignore r0.
    u8* const handle = reinterpret_cast<u8*>(work) + 0x162;
    ScriptEventState* const ev_state = reinterpret_cast<ScriptEventState*>(
        smt4::engine::g_MapRuntimeState);
    const s32 mode = func_00231f6c(handle);                 // 0x00399F48
    const s32 map_center = func_002327c4(handle);           // 0x00399F54
    (void)map_center;
    const f32* camera = func_002327ec(handle);              // 0x00399F58
    const f32 cam_x = camera[0];
    const f32 cam_z = camera[2];
    const f32* pair = func_00231f58(handle);                // 0x00399F6C
    const f32 pair_a = pair[0];
    const f32 pair_b = pair[1];

    f32 origin[2] = {0.0f, 0.0f};
    func_00231d4c(&work->origin_x, origin);                 // 0x00399F80

    g_WorldMapUiState.phase = 0x0B;                         // 0x00399F90

    if ((work->flags & 2) != 0) {                           // 0x00399F9C
        return;
    }
    if (!Flag_CheckEventBit(0x529)) {                       // 0x00399FA4
        return;
    }

    const s32 area = engine_func_002891e0(mode);            // 0x00399FB4
    const bool free_move = area == 2 || area == 3;
    func_002326e8(work, 1);                                 // 0x00399FD0

    const f32 kCellHalf = 8.0f;                             // 0x41000000 (0x00399FF8)

    if (ev_state->field_025 != 0 ||                          // 0x00399FDC
        script_vm_func_002b89d4()) {                        // 0x00399FE8
        goto final_compass;
    }

    switch (mode) {
        case 0x65: {                                        // 0x0039A020
            // 0x39A020..0x39A074: world->screen alignment.
            const f32 scale_x = 0.010745762847363949f;       // 0x3C300EFF
            const f32 scale_y = 0.010526316240429878f;       // 0x3C2C7692
            const f32 center_x = pair_a + 160.0f;            // s16
            const f32 center_y = pair_b + 120.0f;            // s17
            const f32 left_x = center_x - kCellHalf;         // s18
            const f32 right_x = center_x + kCellHalf;        // s19
            const f32 upper_y = center_y - kCellHalf;        // s20
            const f32 lower_y = center_y + kCellHalf;        // s21

            const s32 align_x = static_cast<s32>(
                pair_a - (scale_x * (cam_x + 25500.0f) - 160.0f)); // r6
            const s32 align_y = static_cast<s32>(
                pair_b - (scale_y * (cam_z + 18500.0f) - 120.0f)); // r8

            auto inside = [](f32 cx, f32 cy, s32 left, s32 right,
                             s32 bottom, s32 top) {
                return static_cast<f32>(right) >= cx &&
                       static_cast<f32>(left) <= cx &&
                       static_cast<f32>(top) >= cy &&
                       static_cast<f32>(bottom) <= cy;
            };

            for (s32 y = 0; y < 0x190; y += 0x40) {
                for (s32 x = 0; x < 0x140; x += 0x40) {
                    const s32 left = x + align_x;
                    const s32 right = x + 0x40 + align_x;
                    const s32 bottom = y + align_y;
                    const s32 top = y + 0x40 + align_y;
                    if (right < 0 || left > 0x140 ||
                        top < 8 || bottom > 0xE8) {
                        continue;
                    }

                    const s32 cell_x = x >> 6;
                    const s32 cell_y = y >> 6;

                    // 0x39A0E0..0x39A26C: five player-centred boxes, first
                    // hit marks the cell as visited.
                    if (inside(center_x, center_y, left, right, bottom, top) ||
                        inside(left_x, center_y, left, right, bottom, top) ||
                        inside(right_x, center_y, left, right, bottom, top) ||
                        inside(center_x, upper_y, left, right, bottom, top) ||
                        inside(center_x, lower_y, left, right, bottom, top)) {
                        engine_func_00231c68(mode, cell_x, cell_y); // 0x39A288
                    }

                    // 0x39A28C..0x39A318: draw the cell when it is the
                    // current cell (or the debug event forces every cell).
                    const u32 visited =
                        engine_func_00231b74(mode, cell_x, cell_y) ? 1u : 0u;
                    const bool forced =
                        ev_state->field_3e0 != 0;
                    if (free_move ? forced : (visited != 0 || forced)) {
                        s32 rect[4] = {y, y + 0x40, x, x + 0x40};
                        const f32 px = static_cast<f32>(left) + origin[0];
                        const f32 py = static_cast<f32>(bottom) + origin[1];
                        func_002b06a0(2, 0x1C, 0x1770,
                                      static_cast<s32>(px),
                                      BitCastF32(static_cast<u32>(
                                          static_cast<s32>(py))),
                                      BitCastF32(g_WorldMapUiState.phase),
                                      rect);                // 0x0039A318
                    }
                }
            }

            if (!free_move) {
                script_vm_func_0039ed68(work);              // 0x0039ADAC
                ui_func_0039ead4(work);                     // 0x0039ADBC
            }
            break;
        }
        case 0x66: {                                        // 0x0039A374
            const f32 scale_x = 0.010225806385278702f;       // 0x3C278A24
            const f32 scale_y = 0.010810811072587967f;       // 0x3C311FD4
            const f32 center_x = pair_a + 160.0f;            // s16
            const f32 center_y = pair_b + 120.0f;            // s18
            const f32 outer_r = center_x + 24.0f;            // s28
            const f32 outer_l = center_x - 28.0f;            // s27, 0x41E00000
            const f32 outer_d = center_y - 32.0f;            // s26
            const f32 near_d = center_y - 14.0f;             // s4
            const f32 near_l = center_x - 14.0f;             // s17
            const f32 near_u = center_y + 14.0f;             // s22
            const f32 near_r = center_x + 14.0f;             // s21
            const f32 far_r = center_x + 32.0f;              // s20
            const f32 far_u = center_y + 32.0f;              // s30

            const s32 align_x = static_cast<s32>(
                pair_a - (scale_x * (cam_x + 17000.0f) - 160.0f));
            const s32 align_y = static_cast<s32>(
                pair_b - (scale_y * (cam_z + 18000.0f) - 120.0f));

            auto inside = [](f32 cx, f32 cy, s32 left, s32 right,
                             s32 bottom, s32 top) {
                return static_cast<f32>(right) >= cx &&
                       static_cast<f32>(left) <= cx &&
                       static_cast<f32>(top) >= cy &&
                       static_cast<f32>(bottom) <= cy;
            };

            for (s32 y = 0; y < 0x190; y += 0x40) {
                for (s32 x = 0; x < 0x140; x += 0x40) {
                    const s32 left = x + align_x;
                    const s32 right = x + 0x40 + align_x;
                    const s32 bottom = y + align_y;
                    const s32 top = y + 0x40 + align_y;
                    if (right < 0 || left > 0x140 ||
                        top < 8 || bottom > 0xE8) {
                        continue;
                    }
                    const s32 cell_x = x >> 6;
                    const s32 cell_y = y >> 6;

                    // 0x39A45C..0x39A640: the same five centre boxes.
                    if (inside(center_x, center_y, left, right, bottom, top) ||
                        inside(near_l, center_y, left, right, bottom, top) ||
                        inside(near_r, center_y, left, right, bottom, top) ||
                        inside(center_x, near_d, left, right, bottom, top) ||
                        inside(center_x, near_u, left, right, bottom, top)) {
                        engine_func_00231c68(mode, cell_x, cell_y);
                    }

                    // 0x39A65C..0x39A778: far-east strip.
                    if (cam_x > 5000.0f) {                // 0x459C4000
                        if (inside(far_r, outer_d, left, right, bottom, top)) {
                            engine_func_00231c68(mode, cell_x, cell_y);
                        } else if (inside(far_r, near_u, left, right, bottom, top)) {
                            engine_func_00231c68(mode, cell_x, cell_y);
                        }
                    }

                    // 0x39A77C..0x39A878: south strip.
                    if (cam_z > -5000.0f) {               // 0xC59C4000
                        if (inside(outer_l, outer_d, left, right, bottom, top)) {
                            engine_func_00231c68(mode, cell_x, cell_y);
                        } else if (inside(outer_r, outer_d, left, right, bottom, top)) {
                            engine_func_00231c68(mode, cell_x, cell_y);
                        }
                    }

                    // 0x39A87C..0x39A918: north strip.
                    if (cam_z > 8000.0f) {                // 0x45FA0000
                        if (inside(center_x, far_u, left, right, bottom, top)) {
                            engine_func_00231c68(mode, cell_x, cell_y);
                        }
                    }

                    // 0x39A91C..0x39A930: the cell under the cursor is
                    // always marked in this mode.
                    engine_func_00231c68(mode, cell_x, cell_y);

                    const u32 visited =
                        engine_func_00231b74(mode, cell_x, cell_y) ? 1u : 0u;
                    const bool forced =
                        ev_state->field_3e0 != 0;
                    if (free_move ? forced : (visited != 0 || forced)) {
                        s32 rect[4] = {y, y + 0x40, x, x + 0x40};
                        const f32 px = static_cast<f32>(left) + origin[0];
                        const f32 py = static_cast<f32>(bottom) + origin[1];
                        func_002b06a0(2, 0x1C, 0x1B58,
                                      static_cast<s32>(px),
                                      BitCastF32(static_cast<u32>(
                                          static_cast<s32>(py))),
                                      BitCastF32(g_WorldMapUiState.phase),
                                      rect);                // 0x0039A9A0
                    }
                }
            }

            if (!free_move) {
                script_vm_func_0039ed68(work);
                ui_func_0039ead4(work);
            }
            break;
        }
        case 0x67: {                                        // 0x0039A9C8
            const f32 scale_x = 0.010566666722297668f;       // 0x3C2D1FD0
            const f32 scale_y = 0.010810811072587967f;       // 0x3C311FD4
            const f32 center_x = pair_a + 160.0f;            // s16
            const f32 center_y = pair_b + 120.0f;            // s17
            const f32 left_x = center_x - kCellHalf;         // s18
            const f32 right_x = center_x + kCellHalf;        // s19
            const f32 upper_y = center_y - kCellHalf;        // s21
            const f32 lower_y = center_y + kCellHalf;        // s22
            const f32 north_y = center_y + 16.0f;            // s25

            const s32 align_x = static_cast<s32>(
                pair_a - (scale_x * (cam_x + 17000.0f) - 160.0f));
            const s32 align_y = static_cast<s32>(
                pair_b - (scale_y * (cam_z + 19000.0f) - 120.0f));

            auto inside = [](f32 cx, f32 cy, s32 left, s32 right,
                             s32 bottom, s32 top) {
                return static_cast<f32>(right) >= cx &&
                       static_cast<f32>(left) <= cx &&
                       static_cast<f32>(top) >= cy &&
                       static_cast<f32>(bottom) <= cy;
            };

            for (s32 y = 0; y < 0x190; y += 0x40) {
                for (s32 x = 0; x < 0x140; x += 0x40) {
                    const s32 left = x + align_x;
                    const s32 right = x + 0x40 + align_x;
                    const s32 bottom = y + align_y;
                    const s32 top = y + 0x40 + align_y;
                    if (right < 0 || left > 0x140 ||
                        top < 8 || bottom > 0xE8) {
                        continue;
                    }
                    const s32 cell_x = x >> 6;
                    const s32 cell_y = y >> 6;

                    if (inside(center_x, center_y, left, right, bottom, top) ||
                        inside(left_x, center_y, left, right, bottom, top) ||
                        inside(right_x, center_y, left, right, bottom, top) ||
                        inside(center_x, upper_y, left, right, bottom, top) ||
                        inside(center_x, lower_y, left, right, bottom, top)) {
                        engine_func_00231c68(mode, cell_x, cell_y);
                    }

                    // 0x39AC38..0x39ACD4: north strip.
                    if (cam_z > 3000.0f) {                // 0x453B8000
                        if (inside(center_x, north_y, left, right, bottom, top)) {
                            engine_func_00231c68(mode, cell_x, cell_y);
                        }
                    }

                    const u32 visited =
                        engine_func_00231b74(mode, cell_x, cell_y) ? 1u : 0u;
                    const bool forced =
                        ev_state->field_3e0 != 0;
                    if (free_move ? forced : (visited != 0 || forced)) {
                        s32 rect[4] = {y, y + 0x40, x, x + 0x40};
                        const f32 px = static_cast<f32>(left) + origin[0];
                        const f32 py = static_cast<f32>(bottom) + origin[1];
                        func_002b06a0(2, 0x1C, 0x1F40,
                                      static_cast<s32>(px),
                                      BitCastF32(static_cast<u32>(
                                          static_cast<s32>(py))),
                                      BitCastF32(g_WorldMapUiState.phase),
                                      rect);                // 0x0039AD60
                    }
                }
            }

            if (!free_move) {
                script_vm_func_0039ed68(work);
                ui_func_0039ead4(work);
            }
            break;
        }
        default:
            break;
    }

final_compass:
    // 0x0039ADC0..0x0039AE58: compass direction icons (only when the player
    // is not in free-move mode).
    {
        const f32 cx = pair_a + 160.0f;
        const f32 cy = pair_b + 120.0f;
        if (!free_move) {
            (void)func_00231ec0(handle);                     // 0x0039ADDC
            const s32 dir1 = func_00231e38(work);            // 0x0039ADEC
            camp_func_00231d60(&work->origin_x, dir1 + 0xBC1,
                               static_cast<s32>(cx), static_cast<s32>(cy),
                               BitCastF32(0x0B), BitCastF32(1));
            (void)func_00231f44(handle);                     // 0x0039AE28
            const s32 dir2 = func_00231e38(work);            // 0x0039AE34
            camp_func_00231d60(&work->origin_x, dir2 + 0xBB9,
                               static_cast<s32>(cx), static_cast<s32>(cy),
                               BitCastF32(0x0B), BitCastF32(1));
        }
        func_002326e8(work, 0);                              // 0x0039AE60
        g_WorldMapUiState.phase = 0xF1;                      // 0x0039AE68
        ui_func_00231f80(work);                              // 0x0039AE70
    }
}

// ---------------------------------------------------------------------------
// 0x0039D8B8: world-map marker / command list builder
//
// Four sweeps feed two marker banks and one command bank inside the map work
// buffer:
//   * TBB 0x2B/1 layer rows filtered by the four layer types 0..3,
//   * TBB 0x2B/1 rows referenced by TBB 0x23 rows of type 0x18..0x1A,
//   * the same rows with type 0x2B (sprite-table aligned blocks),
//   * TBB 0x2B/0 landmark rows and TBB 0x2B/3 command rows (tile grids).
// The counts are committed to work+0x5A88, work+0x61B0 and work+0x121B4.
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0039d8b8, 3792)
void script_vm_func_0039d8b8(WorldMapWork* work, s32 map_id) {
    s32 marker_a_count = 0;                                 // sl
    s32 marker_b_count = 0;                                 // sp+0x54
    s32 layer_index = 0;                                    // sp+0x30
    s32 command_count = 0;                                  // r4

    auto write_marker = [](MapMarker* m, u32 object, u8 kind, u16 sprite,
                           u8 palette, u16 f006, u16 f030, u16 f032,
                           u16 f008, f32 x, f32 y, f32 z, f32 f018,
                           u16 f00a, f32 f01c, f32 f020, f32 f024,
                           f32 f028) {
        m->object = object;
        m->kind = kind;
        m->palette = palette;
        m->field_006 = f006;
        m->field_008 = f008;
        m->field_00A = f00a;
        m->x = x;
        m->y = y;
        m->z = z;
        m->field_018 = f018;
        m->field_01C = f01c;
        m->field_020 = f020;
        m->field_024 = f024;
        m->field_028 = f028;
        m->sprite = sprite;
        m->field_030 = f030;
        m->field_032 = f032;
        m->visible = 0;
        m->field_048 = -1;
    };

    // Stack scratch at sp+0x2c passed to the TBB row accessors.  Every callee
    // ignores r0 and takes the row index in r1.
    u32 tbb_ctx = 0;

    // ---- 0x0039D8E0..0x0039DB48: four-layer marker sweep -----------------
    // r7 selects the allowed row type: 0 => 1, 1 => 0, 2 => 4, 3 => 2.
    for (s32 layer = 0; layer < 4; ++layer) {
        for (s32 i = 0; i < camp_func_00231664(&tbb_ctx); ++i) { // 0x0039D8EC
            CampMapLayerRow* row =
                camp_func_00231628(&tbb_ctx, i);             // 0x0039D900
            if (static_cast<s8>(row->field_000) != map_id) {
                continue;                                    // 0x0039D910
            }

            bool type_ok = false;                            // 0x0039D918..0x0039D98C
            switch (layer) {
                case 0: type_ok = row->type == 1; break;
                case 1: type_ok = row->type == 0; break;
                case 2: type_ok = row->type == 4; break;
                case 3: type_ok = row->type == 2; break;
                default: type_ok = row->type == 3; break;    // unreachable (layer < 4)
            }
            if (!type_ok) {
                continue;
            }

            // 0x0039D990..0x0039D9C4: two optional event-bit filters.
            if (row->field_004 != 0 &&
                !Flag_CheckEventBit(row->field_004)) {
                continue;
            }
            if (row->field_006 != 0 &&
                Flag_CheckEventBit(row->field_006)) {
                continue;
            }

            const u16 flag_a = row->field_00A;               // sb
            const u16 flag_b = row->field_00C;               // fp
            if ((flag_a | flag_b) == 0) {
                continue;                                    // 0x0039D9D4
            }

            const u32 object =
                (row->type == 2 || row->type == 4) ? 0x13u : 0x33u;
            const s32 sx = row->field_00E;
            const s32 sy = row->field_010;

            // 0x0039DA00..0x0039DA30: marker centre = layer offset + size/2.
            s32 centre_x = sx + (sx < 0 ? 1 : 0);
            centre_x = row->field_012 + (centre_x >> 1);
            s32 centre_y = sy + (sy < 0 ? 1 : 0);
            centre_y = row->field_013 + (centre_y >> 1);

            s32 out0 = 0;
            s32 out1 = 0;
            s32 out2 = 0;
            s32 out3 = 0;
            engine_func_0024c3f8(object, flag_a, &out0, &out1); // 0x0039DA38
            engine_func_0024c3f8(object, flag_b, &out2, &out3); // 0x0039DA4C

            MapMarker* marker;
            if (row->type != 0) {
                marker = &work->markers_a[marker_a_count++]; // 0x0039DA50
            } else {
                marker = &work->markers_b[marker_b_count++]; // 0x0039DBF8
            }
            write_marker(marker, object, row->field_001, row->type,
                         row->field_002,
                         static_cast<u16>(static_cast<s16>(row->field_003)),
                         row->field_004, row->field_006, row->field_00A,
                         static_cast<f32>(sx), static_cast<f32>(sy),
                         static_cast<f32>(out0), static_cast<f32>(out1),
                         row->field_00C,
                         static_cast<f32>(centre_x), static_cast<f32>(centre_y),
                         static_cast<f32>(out2), static_cast<f32>(out3));
        }
    }

    // ---- 0x0039DB4C..0x0039DB94: shared landmark-group ids --------------
    // 0x1B67/0x1B8F are resolved into two 24-bit positions used by both
    // TBB 0x23 sweeps.
    const f32 kSpriteScaleX = 0.024000000208616257f;         // 0x3CC49BA6
    const f32 kSpriteScaleY = 0.012000000104308128f;         // 0x3C449BA6
    s32 group0_x = 0;
    s32 group0_y = 0;
    s32 group1_x = 0;
    s32 group1_y = 0;
    engine_func_0024c3f8(0x13, 0x1B67, &group0_x, &group0_y); // 0x0039DB80
    engine_func_0024c3f8(0x13, 0x1B8F, &group1_x, &group1_y); // 0x0039DB94

    // ---- 0x0039DBB4..0x0039DED0: TBB 0x23 rows of type 0x18..0x1A --------
    for (s32 i = 0; i < camp_func_00248418(); ++i) {         // 0x0039DBA0
        CampMapSpawnRow* row = camp_func_002483b8(i);        // 0x0039DBC8
        if (row->map_id != map_id) {
            continue;                                        // 0x0039DBD8
        }
        if (row->type != 0x18 && row->type != 0x19 &&
            row->type != 0x1A) {
            continue;                                        // 0x0039DBEC
        }

        // 0x0039DC1C..0x0039DC88: find the layer row whose link id matches.
        layer_index = 1;
        CampMapLayerRow* layer_row = nullptr;
        for (s32 k = 0; k < camp_func_00231664(&tbb_ctx); ++k) {
            layer_row = camp_func_00231628(&tbb_ctx, k);     // 0x0039DC44
            if (layer_row->type == 0 &&
                layer_row->field_001 == row->link_id) {
                layer_index = layer_row->field_003;          // 0x0039DC68
                break;
            }
        }

        const s32 table0 = work->sprite_table[row->sprite_index][0];
        const s32 table1 = work->sprite_table[row->sprite_index][1];
        const s32 half0 = static_cast<s16>(
            static_cast<s32>(static_cast<f32>(table0) * 0.5f));
        const s32 half1 = static_cast<s16>(
            static_cast<s32>(static_cast<f32>(table1) * 0.5f));

        // 0x0039DC8C..0x0039DE10: sprite-atlas aligned centres.  The first
        // centre uses offset_x for both terms; the second uses offset_y.
        s32 centre_x = static_cast<s16>(
            static_cast<f32>(static_cast<s16>(table0)) +
            static_cast<f32>(row->offset_x) * kSpriteScaleX);
        s32 centre_y = static_cast<s16>(
            static_cast<f32>(half0) +
            static_cast<f32>(row->offset_x) * kSpriteScaleY);
        s32 centre2_x = static_cast<s16>(
            static_cast<f32>(static_cast<s16>(table1)) +
            static_cast<f32>(row->offset_y) * kSpriteScaleX);
        s32 centre2_y = static_cast<s16>(
            static_cast<f32>(half1) +
            static_cast<f32>(row->offset_y) * kSpriteScaleY);

        // 0x0039DE14: `sub` of 7 / 3 centres the atlas sprite.
        centre_x -= 7;
        centre_y -= 3;
        centre2_x -= 7;
        centre2_y -= 3;

        MapMarker* marker = &work->markers_a[marker_a_count++]; // 0x0039DD18
        marker->object = 0x13;                               // 0x0039DE18
        marker->kind = layer_row != nullptr ? layer_row->field_001 : 0;
        marker->sprite = 2;                                  // 0x0039DE24
        marker->palette = 0xFF;                              // 0x0039DE28
        marker->field_02E = static_cast<u16>(
            script_vm_func_002765b8(row->field_000));        // 0x0039DE30
        marker->field_006 = static_cast<u16>(layer_index);   // 0x0039DE4C
        marker->field_030 = 0;                               // 0x0039DE58
        marker->field_032 = 0;                               // 0x0039DE5C
        marker->field_008 = static_cast<u16>(0x1B67);        // 0x0039DE6C
        marker->x = static_cast<f32>(centre_x);              // 0x0039DE70
        marker->y = static_cast<f32>(centre2_x);             // 0x0039DE74
        marker->z = static_cast<f32>(group0_x);              // 0x0039DE90
        marker->field_018 = static_cast<f32>(group0_y);      // 0x0039DE9C
        marker->field_00A = static_cast<u16>(0x1B8F);        // 0x0039DEA0
        marker->field_01C = static_cast<f32>(centre_y);      // 0x0039DECC
        marker->field_020 = static_cast<f32>(centre2_y);     // 0x0039DEB0
        marker->field_024 = static_cast<f32>(group1_x);      // 0x0039DEB8
        marker->field_028 = static_cast<f32>(group1_y);      // 0x0039DEC4
        marker->visible = 0;
        marker->field_048 = -1;
    }

    // ---- 0x0039DF14..0x0039E25C: TBB 0x23 rows of type 0x2B -------------
    for (s32 i = 0; i < camp_func_00248418(); ++i) {        // 0x0039DF40
        CampMapSpawnRow* row = camp_func_002483b8(i);        // 0x0039DF64
        if (row->map_id != map_id) {
            continue;                                        // 0x0039DF74
        }
        if (row->type != 0x2B) {                             // 0x0039DF7C
            continue;
        }
        if (row->field_000 == 0x00103001 &&
            Flag_CheckEventBit(0xEF)) {                      // 0x0039DF94
            continue;
        }

        layer_index = 1;
        CampMapLayerRow* layer_row = nullptr;
        for (s32 k = 0; k < camp_func_00231664(&tbb_ctx); ++k) {
            layer_row = camp_func_00231628(&tbb_ctx, k);     // 0x0039DFD0
            if (layer_row->type == 0 &&
                layer_row->field_001 == row->link_id) {
                layer_index = layer_row->field_003;          // 0x0039DFF8
                break;
            }
        }

        const s32 table0 = work->sprite_table[row->sprite_index][0];
        const s32 table1 = work->sprite_table[row->sprite_index][1];
        const s32 half0 = static_cast<s16>(
            static_cast<s32>(static_cast<f32>(table0) * 0.5f));
        const s32 half1 = static_cast<s16>(
            static_cast<s32>(static_cast<f32>(table1) * 0.5f));

        // Same atlas-alignment chain as above (0x0039E0F8..0x0039E18C).
        s32 centre_x = static_cast<s16>(
            static_cast<f32>(static_cast<s16>(table0)) +
            static_cast<f32>(row->offset_x) * kSpriteScaleX);
        s32 centre_y = static_cast<s16>(
            static_cast<f32>(half0) +
            static_cast<f32>(row->offset_x) * kSpriteScaleY);
        s32 centre2_x = static_cast<s16>(
            static_cast<f32>(static_cast<s16>(table1)) +
            static_cast<f32>(row->offset_y) * kSpriteScaleX);
        s32 centre2_y = static_cast<s16>(
            static_cast<f32>(half1) +
            static_cast<f32>(row->offset_y) * kSpriteScaleY);
        centre_x -= 7;
        centre_y -= 3;
        centre2_x -= 7;
        centre2_y -= 3;

        MapMarker* marker = &work->markers_a[marker_a_count++]; // 0x0039E0A4
        marker->object = 0x13;
        marker->kind = layer_row != nullptr ? layer_row->field_001 : 0;
        marker->sprite = 2;
        marker->palette = 0xFE;                              // 0x0039E028
        marker->field_02E = static_cast<u16>(
            camp_func_00321ad0(row->field_000));             // 0x0039E1AC
        marker->field_006 = static_cast<u16>(layer_index);
        marker->field_030 = 0;
        marker->field_032 = 0;
        marker->field_008 = static_cast<u16>(0x1B67);
        marker->x = static_cast<f32>(centre_x);
        marker->y = static_cast<f32>(centre2_x);
        marker->z = static_cast<f32>(group0_x);
        marker->field_018 = static_cast<f32>(group0_y);
        marker->field_00A = static_cast<u16>(0x1B8F);
        marker->field_01C = static_cast<f32>(centre_y);
        marker->field_020 = static_cast<f32>(centre2_y);
        marker->field_024 = static_cast<f32>(group1_x);
        marker->field_028 = static_cast<f32>(group1_y);
        marker->visible = 0;
        marker->field_048 = -1;
    }

    // ---- 0x0039E260..0x0039E2A4: commit counts and clear command kinds ---
    work->marker_count = static_cast<u32>(marker_a_count);
    work->line_count = static_cast<u32>(marker_b_count);
    for (s32 i = 0; i < 0x400; i += 2) {
        work->commands[i].kind = 0;
        work->commands[i + 1].kind = 0;
    }

    // ---- 0x0039E2AC..0x0039E580: TBB 0x2B/0 landmark rows ---------------
    const f32 kTileHalf = 0.00390625f;                       // 0x3B800000
    for (s32 i = 0; i < engine_func_00247414(&tbb_ctx); ++i) { // 0x0039E2B0
        CampMapLandmarkRow* landmark =
            camp_func_002473d8(&tbb_ctx, i);                 // 0x0039E2CC
        if (landmark->map_id != map_id) {
            continue;                                        // 0x0039E2DC
        }

        // 0x0039E2E4..0x0039E314: half the tile footprint.
        const s32 width = (static_cast<s32>(landmark->field_008) -
                           static_cast<s32>(landmark->field_006) + 1) >> 1;
        const s32 height = (static_cast<s32>(landmark->field_009) -
                            static_cast<s32>(landmark->field_007) + 1) >> 1;

        // 0x0039E31C..0x0039E38C: find the marker-bank entry that owns this
        // landmark; the entry index also gives the fade scale.
        s32 current = -0x63;
        f32 scale = 0.0f;
        const s32 line_count = static_cast<s32>(work->line_count);
        for (s32 k = 0; k < line_count; ++k) {
            MapMarker* marker = &work->markers_b[k];
            if (marker->kind == landmark->field_004) {
                current = marker->field_006;
                scale = static_cast<f32>(0xF5 - k * 2) * kTileHalf;
                if (current == 0x63) {
                    break;
                }
                break;
            }
        }
        if (current == 0x63) {
            continue;
        }

        // 0x0039E390..0x0039E3E4: find the layer row for the link id.  The
        // loop stops on the first row whose type is 0.
        CampMapLayerRow* layer_row = nullptr;
        for (s32 k = 0; k < camp_func_00231664(&tbb_ctx); ++k) {
            layer_row = camp_func_00231628(&tbb_ctx, k);     // 0x0039E3B0
            if (layer_row->field_001 == landmark->field_004 &&
                layer_row->type == 0) {
                break;
            }
        }
        if (layer_row == nullptr) {
            continue;
        }

        // 0x0039E3E8..0x0039E434: layer-row centre offsets.
        const s32 sx = layer_row->field_00E;
        const s32 sy = layer_row->field_010;
        s32 centre_x = sx + (sx < 0 ? 1 : 0);
        centre_x = layer_row->field_012 + (centre_x >> 1);
        s32 centre_y = sy + (sy < 0 ? 1 : 0);
        centre_y = layer_row->field_013 + (centre_y >> 1);

        if (height <= 0) {
            continue;
        }
        if (width <= 0) {
            continue;
        }

        const s32 kind = landmark->field_004;
        for (s32 dy = 0; dy < height; ++dy) {
            for (s32 dx = 0; dx < width; ++dx) {
                // 0x39E454..0x39E488: the 0x8E landmark omits the notch.
                if (kind == 0x8E &&
                    (dx == 3 || dx == 4) &&
                    (dy <= 2 || (dy >= 5 && dy <= 6))) {
                    continue;
                }
                if (command_count >= 0x400) {               // 0x0039E48C
                    continue;
                }

                MapCommand* cmd = &work->commands[command_count++];
                cmd->kind = 0;                              // 0x0039E4AC
                cmd->field_001 = 1;                         // 0x0039E4B0
                cmd->field_002 = static_cast<u8>(kind);     // 0x0039E4C0
                cmd->field_003 = layer_row->field_002;      // 0x0039E4D4
                cmd->field_006 = static_cast<u16>(current); // 0x0039E4C8

                // 0x39E4D8..0x39E510: atlas tile index.
                const MapSpriteAtlasEntry& atlas =
                    g_MapSpriteAtlas[static_cast<u8>(kind)];
                cmd->field_008 = atlas.base +
                                 atlas.stride * dy + dx;

                // 0x39E4FC..0x39E560: raw layer offsets for +0x0C/+0x10 and
                // the centre-derived 12-pixel positions for +0x14/+0x18.
                cmd->field_00C = static_cast<f32>(layer_row->field_00E) +
                                 static_cast<f32>(dx * 24);
                cmd->field_010 = static_cast<f32>(layer_row->field_010) +
                                 static_cast<f32>(dy * 24);
                cmd->field_014 = static_cast<f32>(centre_x) +
                                 static_cast<f32>(dx * 12);
                cmd->field_018 = static_cast<f32>(centre_y) +
                                 static_cast<f32>(dy * 12);
                cmd->field_02C = scale;
            }
        }
    }

    // ---- 0x0039E5A4..0x0039E76C: TBB 0x2B/3 command rows ----------------
    for (s32 i = 0; i < camp_func_0039fec4(&tbb_ctx); ++i) { // 0x0039E5A8
        CampMapCommandRow* row =
            camp_func_0039fe50(&tbb_ctx, i);                 // 0x0039E5CC
        if (row->map_id == -1) {
            break;                                           // 0x0039E5DC sentinel
        }
        if (row->map_id != map_id) {
            continue;                                        // 0x0039E5E8
        }

        s32 current = -0x63;
        f32 scale = 0.0f;
        const s32 line_count = static_cast<s32>(work->line_count);
        for (s32 k = 0; k < line_count; ++k) {
            MapMarker* marker = &work->markers_b[k];
            if (marker->kind == row->field_002) {
                current = marker->field_006;
                scale = static_cast<f32>(0xF5 - k * 2) * kTileHalf;
                break;
            }
        }
        // No 0x63 filter here: 0x0039E628..0x0039E644 branches straight to
        // the layer scan (unlike the landmark sweep at 0x0039E36C).

        // 0x39E66C..0x39E6BC: the layer row only validates the command; the
        // scan stops on the first row whose type is 0.
        CampMapLayerRow* layer_row = nullptr;
        for (s32 k = 0; k < camp_func_00231664(&tbb_ctx); ++k) {
            layer_row = camp_func_00231628(&tbb_ctx, k);     // 0x0039E68C
            if (layer_row->field_001 == row->field_002 &&
                layer_row->type == 0) {
                break;
            }
        }
        if (layer_row == nullptr) {
            continue;
        }
        if (command_count >= 0x400) {                       // 0x0039E6C0
            continue;
        }

        MapCommand* cmd = &work->commands[command_count++];
        cmd->kind = 0;                                      // 0x0039E6DC
        cmd->field_001 = 1;                                 // 0x0039E6E0
        cmd->field_002 = row->field_002;                    // 0x0039E6EC
        cmd->field_006 = static_cast<u16>(current);         // 0x0039E6F0
        cmd->field_003 = row->field_003;                    // 0x0039E6F4
        cmd->field_004 = row->field_004;                    // 0x0039E6FC
        cmd->field_005 = row->field_005;                    // 0x0039E704
        cmd->field_008 = -1;                                // 0x0039E70C
        cmd->field_00C = static_cast<f32>(row->field_006);  // 0x0039E71C
        cmd->field_010 = static_cast<f32>(row->field_008);  // 0x0039E72C
        cmd->field_014 = static_cast<f32>(row->field_00A);  // 0x0039E73C
        cmd->field_018 = static_cast<f32>(row->field_00B);  // 0x0039E74C
        cmd->field_02C = scale;                             // 0x0039E750
    }

    work->command_count = static_cast<u32>(command_count);  // 0x0039E770
}

} // namespace smt4::script
