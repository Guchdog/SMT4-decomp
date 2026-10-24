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

// Semantic draft only; the exact byte span is preserved by the wrapper below.
[[maybe_unused]] static void script_vm_func_00276cac_Draft() {
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

[[maybe_unused]] static void script_vm_func_002c8c90_Draft() {
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

[[maybe_unused]] static void script_vm_func_00399f28_Draft(WorldMapWork* work) {
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

[[maybe_unused]] static void script_vm_func_0039d8b8_Draft(
    WorldMapWork* work, s32 map_id) {
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

// Exact ARMv6K extent from code.bin; includes the float literal at 0x002C9AC0.
// It returns at 0x002C9AD4; the next function starts at 0x002C9AD8.
// DECOMP_FUNC(0x002c8c90, 3656)
__attribute__((naked)) void script_vm_func_002c8c90() {
    asm volatile(
        ".arm\n"
        ".word 0xE92D4FF0, 0xE3A020A0, 0xE3A0B000, 0xE59F13AC\n"
        ".word 0xED2D8B0C, 0xE24DDFA5, 0xE1A0000D, 0xEBFFD0A9\n"
        ".word 0xE59F139C, 0xE3A020A0, 0xE28D00A0, 0xEBFFD0A5\n"
        ".word 0xE59F1390, 0xE3A020A0, 0xE28D0D05, 0xEBFFD0A1\n"
        ".word 0xE59F1384, 0xE3A020A0, 0xE28D0E1E, 0xEBFFD09D\n"
        ".word 0xE59F8378, 0xE59F937C, 0xED9FDADD, 0xE3A0A004\n"
        ".word 0xE5980000, 0xE3A06000, 0xE3A07001, 0xE5901004\n"
        ".word 0xED909A0A, 0xEDD08A0B, 0xED908A0C, 0xE3510000\n"
        ".word 0x0A000006, 0xE3510001, 0xEDDFAAD3, 0xED9FBAD3\n"
        ".word 0x0A000018, 0xE3510002, 0x1A000338, 0xEA00024F\n"
        ".word 0xE5C0606C, 0xE5991218, 0xE3510000, 0x0580A054\n"
        ".word 0x0A00000A, 0xE3510001, 0x03A01016, 0x0A000006\n"
        ".word 0xE3510002, 0x03A01017, 0x0A000003, 0xE3510003\n"
        ".word 0x03A01018, 0x05801054, 0xEA000000, 0xE5801054\n"
        ".word 0xED9F0ABF, 0xED800A16, 0xE5C0705C, 0xE5A07004\n"
        ".word 0xE5806004, 0xEA000324, 0xE5901008, 0xED9FAAB9\n"
        ".word 0xE2811001, 0xE3510014, 0xE5801008, 0xAA0000E6\n"
        ".word 0xE5990218, 0xE3500000, 0x0A000006, 0xE3500001\n"
        ".word 0x0A000013, 0xE3500002, 0x0A000020, 0xE3500003\n"
        ".word 0x1A00003B, 0xEA00002C, 0xE1A0000D, 0xE0800181\n"
        ".word 0xE3A03000, 0xE1D010B0, 0xE1D020B4, 0xE1A0C003\n"
        ".word 0xE1833001, 0xE1D040B2, 0xE1D000B6, 0xE18C1002\n"
        ".word 0xE6FF3073, 0xE6FF1071, 0xE1835804, 0xE1814800\n"
        ".word 0xEA00002B, 0xE28D00A0, 0xE0800181, 0xE3A03000\n"
        ".word 0xE1D010B0, 0xE1D020B4, 0xE1A0C003, 0xE1833001\n"
        ".word 0xE1D040B2, 0xE1D000B6, 0xE18C1002, 0xE6FF3073\n"
        ".word 0xE6FF1071, 0xE1835804, 0xE1814800, 0xEA00001C\n"
        ".word 0xE28D0D05, 0xE0800181, 0xE3A03000, 0xE1D010B0\n"
        ".word 0xE1D020B4, 0xE1A0C003, 0xE1833001, 0xE1D040B2\n"
        ".word 0xE1D000B6, 0xE18C1002, 0xE6FF3073, 0xE6FF1071\n"
        ".word 0xE1835804, 0xE1814800, 0xEA00000D, 0xE28D0E1E\n"
        ".word 0xE0800181, 0xE3A03000, 0xE1D010B0, 0xE1D020B4\n"
        ".word 0xE1A0C003, 0xE1833001, 0xE1D040B2, 0xE1D000B6\n"
        ".word 0xE18C1002, 0xE6FF3073, 0xE6FF1071, 0xE1835804\n"
        ".word 0xE1814800, 0xE1B00845, 0x0A000006, 0xE6BF1074\n"
        ".word 0xE1A00844, 0xEE000A90, 0xEE001A10, 0xEEF80AE0\n"
        ".word 0xEEB80AC0, 0xEBFE4C48, 0xE6BF0075, 0xEE000A10\n"
        ".word 0xE5980000, 0xEEF89AC0, 0xED900A14, 0xEE200A0A\n"
        ".word 0xEBFEE621, 0xE5980000, 0xEDD00A0A, 0xEE400A29\n"
        ".word 0xEDC00A0A, 0xED900A14, 0xEE200A0A, 0xEBFEE5BB\n"
        ".word 0xE5981000, 0xE28D0D0A, 0xED911A0C, 0xEE001A29\n"
        ".word 0xED811A0C, 0xE2811028, 0xEC910A02, 0xEBFEDAE1\n"
        ".word 0xE28D2D0A, 0xE59F112C, 0xE8921018, 0xE5982000\n"
        ".word 0xE2825028, 0xE8851018, 0xED829A0D, 0xEDC28A0E\n"
        ".word 0xED828A0F, 0xE5D113CC, 0xE3510000, 0x1A000015\n"
        ".word 0xE5D91021, 0xE3510000, 0x0A000012, 0xE1DB0000\n"
        ".word 0x1A000010, 0xE2821034, 0xE2820028, 0xEBFED9DE\n"
        ".word 0xE3500000, 0x15980000, 0x1DC0AA1A, 0x1A000009\n"
        ".word 0xE5981000, 0xEDDF0A38, 0xE59F00E0, 0xED910A1A\n"
        ".word 0xEE300A20, 0xEE10CA10, 0xED810A1A, 0xE15C0000\n"
        ".word 0xDEB0BA40, 0xED81BA1A, 0xE5990000, 0xE3500024\n"
        ".word 0x0A000010, 0xE3A01005, 0xE3A00002, 0xEBFE44E9\n"
        ".word 0xE3500000, 0xE320F000, 0x0A00000A, 0xE5980000\n"
        ".word 0xEEB01A48, 0xEEF00A68, 0xE2800028, 0xEEB00A49\n"
        ".word 0xECD01A03, 0xEBFEFB56, 0xE5980000, 0xEDD00A58\n"
        ".word 0xEE300AC0, 0xED800A58, 0xE5980000, 0xE2800028\n"
        ".word 0xEBFEDDD1, 0xE3100002, 0xE5980000, 0x0A000018\n"
        ".word 0xE2800028, 0xEEB01A48, 0xEEF00A68, 0xEEB00A49\n"
        ".word 0xECD01A03, 0xEBFEFB46, 0xE5980000, 0xEDD00A57\n"
        ".word 0xEE300AC0, 0xED800A57, 0xE5C9A033, 0xEA000022\n"
        ".word 0x004045AC, 0x0040464C, 0x004046EC, 0x0040478C\n"
        ".word 0x00447E88, 0x3EAAAAAB, 0x0049F91C, 0x00000000\n"
        ".word 0x41A00000, 0x40400000, 0x3C8EFA35, 0x40000000\n"
        ".word 0x41A00000, 0xED900A57, 0xEEB40AEA, 0xEEF1FA10\n"
        ".word 0xDA000009, 0xE2800028, 0xEEB01A48, 0xEEF00A68\n"
        ".word 0xEEB00A49, 0xECD01A03, 0xEBFEFB29, 0xE5980000\n"
        ".word 0xEDD00A57, 0xEE300AC0, 0xED800A57, 0xE5980000\n"
        ".word 0xE3A010FF, 0xED900A57, 0xEEB40AEA, 0xEEF1FA10\n"
        ".word 0xCEF0AA40, 0xEDC0AA57, 0xE5C91033, 0xE5980000\n"
        ".word 0xE280101C, 0xEDD00A0A, 0xED900A07, 0xE2803040\n"
        ".word 0xEE700AC0, 0xEE000A8D, 0xED800A07, 0xEDD00A0B\n"
        ".word 0xED900A08, 0xEE700AC0, 0xEE000A8D, 0xED800A08\n"
        ".word 0xEDD00A0C, 0xED900A09, 0xEE700AC0, 0xEE000A8D\n"
        ".word 0xED800A09, 0xE8910006, 0xE8830006, 0xED800A12\n"
        ".word 0xED809A0D, 0xEDC08A0E, 0xED808A0F, 0xE5990218\n"
        ".word 0xED9FBAB6, 0xEDDFBAB6, 0xEDDFAAB6, 0xE3500000\n"
        ".word 0xE1A04009, 0x0A000006, 0xE3500001, 0x0A000040\n"
        ".word 0xE3500002, 0x0A000072, 0xE3500003, 0x1A0000F2\n"
        ".word 0xEA0000B2, 0xE5980000, 0xE5901008, 0xE3510003\n"
        ".word 0x1A00002A, 0xED900A13, 0xEDD09A09, 0xE280001C\n"
        ".word 0xEE200A0A, 0xEC90CA02, 0xEBFEE577, 0xE5980000\n"
        ".word 0xEE00CA2A, 0xED900A13, 0xEE200A0A, 0xEBFEE513\n"
        ".word 0xEEB01A69, 0xEE7C0A8B, 0xE59F026C, 0xEE001A2A\n"
        ".word 0xEEB00A4C, 0xEBFF23C6, 0xE5980000, 0xED900A13\n"
        ".word 0xED90BA07, 0xED90CA08, 0xEE200A0A, 0xEDD09A09\n"
        ".word 0xEBFEE565, 0xE5980000, 0xEE00BA2B, 0xED900A13\n"
        ".word 0xEE200A0A, 0xEBFEE501, 0xEE409A2B, 0xEE3CAA2A\n"
        ".word 0xE3A01002, 0xE3A00000, 0xEBFF377D, 0xEEB01A69\n"
        ".word 0xEEF00A4A, 0xEEB00A4B, 0xE2800401, 0xE2800F8B\n"
        ".word 0xEBFF23AF, 0xE3E00000, 0xE320F000, 0xEBFEDB37\n"
        ".word 0xE5980000, 0xE5900008, 0xE3500006, 0x1A0000BE\n"
        ".word 0xEBFE4B1C, 0xE5980000, 0xE5900008, 0xE3500006\n"
        ".word 0x1A0000B9, 0xE3A02000, 0xE3A01008, 0xE3A00004\n"
        ".word 0xEA0000B4, 0xE5980000, 0xE5901008, 0xE3510003\n"
        ".word 0x1A00002A, 0xED900A13, 0xEDD09A09, 0xE280001C\n"
        ".word 0xEE200A0A, 0xEC90CA02, 0xEBFEE53B, 0xE5980000\n"
        ".word 0xEE00CA2A, 0xED900A13, 0xEE200A0A, 0xEBFEE4D7\n"
        ".word 0xEEB01A69, 0xEE7C0A8B, 0xE59F0180, 0xEE001A2A\n"
        ".word 0xEEB00A4C, 0xEBFF238A, 0xE5980000, 0xED900A13\n"
        ".word 0xED90BA07, 0xED90CA08, 0xEE200A0A, 0xEDD09A09\n"
        ".word 0xEBFEE529, 0xE5980000, 0xEE00BA2B, 0xED900A13\n"
        ".word 0xEE200A0A, 0xEBFEE4C5, 0xEE409A2B, 0xEE3CAA2A\n"
        ".word 0xE3A01002, 0xE3A00000, 0xEBFF3741, 0xE59F1130\n"
        ".word 0xEEB01A69, 0xEEF00A4A, 0xEEB00A4B, 0xE0800001\n"
        ".word 0xEBFF2373, 0xE3E00000, 0xE320F000, 0xEBFEDAFB\n"
        ".word 0xE5980000, 0xE5900008, 0xE3500006, 0x1A000082\n"
        ".word 0xEA000035, 0xE5980000, 0xE5901008, 0xE3510002\n"
        ".word 0x1A000015, 0xED900A13, 0xEDD09A09, 0xE280001C\n"
        ".word 0xEE200A0A, 0xEC90CA02, 0xEBFEE507, 0xE5980000\n"
        ".word 0xEE00CA2B, 0xED900A13, 0xEE200A0A, 0xEBFEE4A3\n"
        ".word 0xEE409A2B, 0xEE7CBAAA, 0xE3A01002, 0xE3A00000\n"
        ".word 0xEBFF371F, 0xE59F10AC, 0xEEB01A69, 0xEEF00A6B\n"
        ".word 0xEEB00A4C, 0xE0800001, 0xEBFF2351, 0xE5980000\n"
        ".word 0xE5901008, 0xE3510003, 0x1A000013, 0xED900A13\n"
        ".word 0xEDD09A09, 0xE280001C, 0xEE200A0A, 0xECD0BA02\n"
        ".word 0xEBFEE4ED, 0xE5980000, 0xEE40BA2A, 0xED900A13\n"
        ".word 0xEE200A0A, 0xEBFEE489, 0xEEB01A69, 0xEE7C0A0B\n"
        ".word 0xE59F0054, 0xEE001A2A, 0xEEB00A6B, 0xEBFF233C\n"
        ".word 0xE3E00000, 0xE320F000, 0xEBFEDAC4, 0xE5980000\n"
        ".word 0xE5900008, 0xE3500004, 0x1A00004B, 0xE320F000\n"
        ".word 0xEBFE4AA8, 0xE320F000, 0xE320F000, 0xEA000046\n"
        ".word 0x43020000, 0x42700000, 0x43160000, 0x010001F0\n"
        ".word 0x010001F1, 0x0100022F, 0x01000232, 0x010001F2\n"
        ".word 0xE5980000, 0xE5901008, 0xE3510002, 0x1A000015\n"
        ".word 0xED900A13, 0xEDD09A09, 0xE280001C, 0xEE200A0A\n"
        ".word 0xEC90CA02, 0xEBFEE4C4, 0xE5980000, 0xEE00CA2B\n"
        ".word 0xED900A13, 0xEE200A0A, 0xEBFEE460, 0xEE409A2B\n"
        ".word 0xEE7CBAAA, 0xE3A01002, 0xE3A00000, 0xEBFF36DC\n"
        ".word 0xE59F1600, 0xEEB01A69, 0xEEF00A6B, 0xEEB00A4C\n"
        ".word 0xE0400001, 0xEBFF230E, 0xE5980000, 0xE5901008\n"
        ".word 0xE3510003, 0x1A000013, 0xED900A13, 0xEDD09A09\n"
        ".word 0xE280001C, 0xEE200A0A, 0xECD0BA02, 0xEBFEE4AA\n"
        ".word 0xE5980000, 0xEE40BA2A, 0xED900A13, 0xEE200A0A\n"
        ".word 0xEBFEE446, 0xEEB01A69, 0xEE7C0A0B, 0xE59F05A8\n"
        ".word 0xEE001A2A, 0xEEB00A6B, 0xEBFF22F9, 0xE3E00000\n"
        ".word 0xE320F000, 0xEBFEDA81, 0xE5980000, 0xE5900008\n"
        ".word 0xE3500006, 0x1A000008, 0xEBFE4A66, 0xE5980000\n"
        ".word 0xE5900008, 0xE3500006, 0x1A000003, 0xE3A02000\n"
        ".word 0xE3A01014, 0xE3A00006, 0xEBFEF9C1, 0xE5981000\n"
        ".word 0xE59F0558, 0xE5912008, 0xE3520003, 0x1A00000B\n"
        ".word 0xE3E02000, 0xE581216C, 0xE281201C, 0xE5816168\n"
        ".word 0xE5C4717C, 0xE892100C, 0xE2845D06, 0xE885100C\n"
        ".word 0xE591204C, 0xE584218C, 0xE1C069B0, 0xE1C069B2\n"
        ".word 0xE5D0207C, 0xE3520000, 0x0A000024, 0xE281201C\n"
        ".word 0xE2845D06, 0xE892100C, 0xE885100C, 0xE591204C\n"
        ".word 0xE584218C, 0xE1D029B0, 0xE2822001, 0xE6BF2072\n"
        ".word 0xE1C029B0, 0xE1C069B2, 0xE5943218, 0xE3530000\n"
        ".word 0x0A000006, 0xE3530001, 0x0A000009, 0xE3530002\n"
        ".word 0x0A00000B, 0xE3530003, 0x1A000010, 0xEA00000C\n"
        ".word 0xE2422005, 0xE3520003, 0x8A00000C, 0xE1C079B2\n"
        ".word 0xEA00000A, 0xE2422003, 0xE3520003, 0x8A000007\n"
        ".word 0xEAFFFFF9, 0xE2422006, 0xE3520005, 0x8A000003\n"
        ".word 0xEAFFFFF5, 0xE2422005, 0xE3520004, 0x9AFFFFF2\n"
        ".word 0xE5D020A0, 0xE3520000, 0x1A000004, 0xE1D029F4\n"
        ".word 0xE3520000, 0xC5C471A0, 0xC58461A4, 0xCA0000EF\n"
        ".word 0xE1D009B4, 0xE3500000, 0x1A0000EC, 0xE5910008\n"
        ".word 0xE350000E, 0xDA0000E9, 0xE5C4617C, 0xE5816168\n"
        ".word 0xE5B10004, 0xE2800001, 0xE8810041, 0xEA0000E3\n"
        ".word 0xE5901008, 0xE1A04008, 0xE2811001, 0xE5801008\n"
        ".word 0xE5990000, 0xE3500024, 0x0A00001D, 0xE3A01005\n"
        ".word 0xE3A00002, 0xEBFE4337, 0xE3500000, 0xE320F000\n"
        ".word 0x0A000017, 0xE5940000, 0xED900A58, 0xEEF4AAC0\n"
        ".word 0xEEF1FA10, 0xDA000012, 0xE3A02005, 0xE1A01002\n"
        ".word 0xE3A00002, 0xEBFE33B9, 0xE5940000, 0xED9F0AF4\n"
        ".word 0xE3A01050, 0xED800A58, 0xE3A0000F, 0xEBFE3390\n"
        ".word 0xE5940000, 0xE280001C, 0xEC900A03, 0xE59F03B4\n"
        ".word 0xEBFF227B, 0xE5941000, 0xE3A02014, 0xE2811F63\n"
        ".word 0xE8810005, 0xE5940000, 0xED900A57, 0xEEF4AAC0\n"
        ".word 0xEEF1FA10, 0xDA000008, 0xE5991000, 0xE3510005\n"
        ".word 0x05991004, 0x03510009, 0x1D9F0ADF, 0x0D9F0ADF\n"
        ".word 0xED800A57, 0xE3A00020, 0xEA0000AF, 0xE3A02000\n"
        ".word 0xE28D1E29, 0xE28D0FA3, 0xEBFED91E, 0xE5990218\n"
        ".word 0xEDDF9AD7, 0xED9FAAD7, 0xE3500000, 0x0A000006\n"
        ".word 0xE3500001, 0x0A000015, 0xE3500002, 0x0A000024\n"
        ".word 0xE3500003, 0x1A000080, 0xEA000039, 0xE5940000\n"
        ".word 0xE5900008, 0xE3500005, 0x1A000007, 0xE3E00000\n"
        ".word 0xEBFED9DE, 0xE320F000, 0xE320F000, 0xEBFE49C5\n"
        ".word 0xEEF00A4B, 0xEEB00A69, 0xEBFE4A13, 0xE5940000\n"
        ".word 0xE5900008, 0xE3500006, 0x1A00003F, 0xEA000038\n"
        ".word 0xE5940000, 0xE5900008, 0xE3500005, 0x1A000007\n"
        ".word 0xE3E00000, 0xEBFED9CD, 0xE320F000, 0xE320F000\n"
        ".word 0xEBFE49B4, 0xEEF00A4B, 0xEEB00A4A, 0xEBFE4A02\n"
        ".word 0xE5940000, 0xE5900008, 0xE3500006, 0x1A00002E\n"
        ".word 0xEA00000F, 0xE5940000, 0xE5900008, 0xE3500005\n"
        ".word 0x1A000007, 0xE3E00000, 0xEBFED9BC, 0xE320F000\n"
        ".word 0xE320F000, 0xEBFE49A3, 0xEEF00A4B, 0xEEB00A4A\n"
        ".word 0xEBFE49F1, 0xE5940000, 0xE5900008, 0xE3500006\n"
        ".word 0x1A00001D, 0xE320F000, 0xEBFE499A, 0xEEF00A4B\n"
        ".word 0xEEB00A69, 0xEBFE49E8, 0xE320F000, 0xE320F000\n"
        ".word 0xEA000015, 0xE5940000, 0xE5900008, 0xE3500005\n"
        ".word 0x1A000007, 0xE3E00000, 0xEBFED9A4, 0xE320F000\n"
        ".word 0xE320F000, 0xEBFE498B, 0xEEF00A4B, 0xEEB00A69\n"
        ".word 0xEBFE49D9, 0xE5940000, 0xE5900008, 0xE3500006\n"
        ".word 0x1A000005, 0xEEF00A4B, 0xEEB00A4A, 0xEBFE49D2\n"
        ".word 0xE320F000, 0xE320F000, 0xEBFE497E, 0xE5990218\n"
        ".word 0xE3500000, 0x0A000006, 0xE3500001, 0x0A000010\n"
        ".word 0xE3500002, 0x0A000017, 0xE3500003, 0x0A00001E\n"
        ".word 0xEA000025, 0xE5940000, 0xE5900008, 0xE3500006\n"
        ".word 0xDA000021, 0xEBFE3395, 0xE3500000, 0xE320F000\n"
        ".word 0x0A00001D, 0xE5940000, 0xE5806004, 0xE5806008\n"
        ".word 0xEA00003E, 0xE5940000, 0xE5900008, 0xE3500003\n"
        ".word 0xDA000015, 0xEBFE3389, 0xE3500000, 0xE320F000\n"
        ".word 0x0A000011, 0xEAFFFFF2, 0xE5940000, 0xE5900008\n"
        ".word 0xE3500008, 0xDA00000C, 0xEBFE3380, 0xE3500000\n"
        ".word 0xE320F000, 0x0A000008, 0xEAFFFFE9, 0xE5940000\n"
        ".word 0xE5900008, 0xE3500008, 0xDA000003, 0xEBFE3377\n"
        ".word 0xE3500000, 0xE320F000, 0x1AFFFFE1, 0xE59D028C\n"
        ".word 0xE35004BF, 0x8A00000A, 0xE350043F, 0xCA000008\n"
        ".word 0xE59D0290, 0xE35004BF, 0x8A000005, 0xE350043F\n"
        ".word 0xCA000003, 0xE5940000, 0xE5900008, 0xE350000A\n"
        ".word 0xDA000012, 0xE5940000, 0xED9F0A3F, 0xEDC0AA1A\n"
        ".word 0xED800A16, 0xE5901008, 0xE351000A, 0xC5807188\n"
        ".word 0xCA000008, 0xE5992218, 0xE3A01002, 0xE3520000\n"
        ".word 0x13520001, 0x05801188, 0x0A000002, 0xE3520002\n"
        ".word 0x13520003, 0x0580A188, 0xE3A00001, 0xEBFED8C1\n"
        ".word 0xE5980000, 0xE5900004, 0xE3500001, 0x0A000002\n"
        ".word 0xE5980000, 0xE2800028, 0xEBFEDB4F, 0xE5980000\n"
        ".word 0xEDD00A09, 0xED900A07, 0xEBFEDAE9, 0xE320F000\n"
        ".word 0xE320F000, 0xEBFEDC6F, 0xE5980000, 0xEDDF0A1F\n"
        ".word 0xE280101C, 0xED901A0A, 0xED900A07, 0xE2803040\n"
        ".word 0xEE311A40, 0xEE010A0D, 0xED800A07, 0xED901A0B\n"
        ".word 0xED900A08, 0xEE311A40, 0xEE010A20, 0xED800A08\n"
        ".word 0xEDD00A0C, 0xED900A09, 0xEE700AC0, 0xEE000A8D\n"
        ".word 0xED800A09, 0xE8910006, 0xE8830006, 0xED800A12\n"
        ".word 0xED809A0D, 0xEA00000A, 0xFEFFFDCB, 0x010001F3\n"
        ".word 0x0049FA1C, 0x447A0000, 0x01000186, 0x43FA0000\n"
        ".word 0x44BB8000, 0xC3020000, 0x41F00000, 0x40A00000\n"
        ".word 0x3E2AAAAB, 0xEDC08A0E, 0xED808A0F, 0xE28DDFA5\n"
        ".word 0xECBD8B0C, 0xE8BD8FF0\n"
    );
}

// Exact ARMv6K extent from code.bin, including the post-return literal at
// 0x0039E784. The return is at 0x0039E780; next function starts at 0x0039E788.
// DECOMP_FUNC(0x0039d8b8, 3792)
__attribute__((naked)) void script_vm_func_0039d8b8(WorldMapWork*, s32) {
    asm volatile(
        ".arm\n"
        ".word 0xE92D4FF3, 0xE3A06000, 0xE1A08000, 0xE1A0A006\n"
        ".word 0xE1A04006, 0xE1A07006, 0xED2D8B08, 0xE24DD064\n"
        ".word 0xE58D6054, 0xE58D6030, 0xE3A05000, 0xE28D002C\n"
        ".word 0xEBFA4F5D, 0xE3500000, 0xE320F000, 0xDA000091\n"
        ".word 0xE1A01005, 0xE28D002C, 0xEBFA4F48, 0xE1D010D0\n"
        ".word 0xE1A06000, 0xE59D0088, 0xE1510000, 0x1A000083\n"
        ".word 0xE3570000, 0x0A000008, 0xE3570001, 0x0A00000A\n"
        ".word 0xE3570002, 0x0A00000C, 0xE3570003, 0x0A00000E\n"
        ".word 0xE3570004, 0x0A000010, 0xEA000078, 0xE1D600B8\n"
        ".word 0xE3500001, 0x0A00000F, 0xEA000074, 0xE1D600B8\n"
        ".word 0xE3500000, 0x0A00000B, 0xEA000070, 0xE1D600B8\n"
        ".word 0xE3500004, 0x0A000007, 0xEA00006C, 0xE1D600B8\n"
        ".word 0xE3500002, 0x0A000003, 0xEA000068, 0xE1D600B8\n"
        ".word 0xE3500003, 0x1A000065, 0xE1D600B4, 0xE3500000\n"
        ".word 0x0A000003, 0xEBFC8C81, 0xE3500000, 0xE320F000\n"
        ".word 0x0A00005E, 0xE1D600B6, 0xE3500000, 0x0A000003\n"
        ".word 0xEBFC8C7A, 0xE3500000, 0xE320F000, 0x1A000057\n"
        ".word 0xE1D690BA, 0xE1D6B0BC, 0xE199000B, 0x0A000053\n"
        ".word 0xE1D600F8, 0xE3500002, 0x13500004, 0x03A00013\n"
        ".word 0x13A00033, 0xE58D0014, 0xE1D620FE, 0xE1D631F0\n"
        ".word 0xE58D200C, 0xE58D3004, 0xE1D611D2, 0xE0822FA2\n"
        ".word 0xE08110C2, 0xE0832FA3, 0xE6BF0071, 0xE58D0040\n"
        ".word 0xE1D611D3, 0xE59D0014, 0xE28D303C, 0xE08110C2\n"
        ".word 0xE28D2038, 0xE6BF1071, 0xE58D1044, 0xE1A01009\n"
        ".word 0xEBFABA6E, 0xE59D0014, 0xE28D3050, 0xE28D204C\n"
        ".word 0xE1A0100B, 0xEBFABA69, 0xE1D610B8, 0xE3510000\n"
        ".word 0x0A000066, 0xE1A0100A, 0xE08A2081, 0xE0821201\n"
        ".word 0xE28AA001, 0xE0881101, 0xE2811B03, 0xE2811FA2\n"
        ".word 0xE59D2014, 0xE28D0040, 0xE3A03000, 0xE5812000\n"
        ".word 0xEDDD0A03, 0xED9D0A01, 0xE5D62001, 0xEEB81AE0\n"
        ".word 0xEEB82AC0, 0xEC900A02, 0xE3E0C000, 0xE5C12004\n"
        ".word 0xE1D620B8, 0xEEF81AC0, 0xEEF80AE0, 0xE1C122BC\n"
        ".word 0xE5D62002, 0xE5C12005, 0xE1D620D3, 0xE1C120B6\n"
        ".word 0xE1D620B4, 0xE1C123B0, 0xE1D620B6, 0xE1C123B2\n"
        ".word 0xE1C190B8, 0xED811A03, 0xED812A04, 0xED9D0A0E\n"
        ".word 0xEEB80AC0, 0xED810A05, 0xED9D0A0F, 0xEEB80AC0\n"
        ".word 0xED810A06, 0xE1C1B0BA, 0xEDC11A07, 0xEDC10A08\n"
        ".word 0xED9D0A13, 0xEEB80AC0, 0xED810A09, 0xED9D0A14\n"
        ".word 0xEEB80AC0, 0xED810A0A, 0xE1C133B4, 0xE581C048\n"
        ".word 0xE2855001, 0xE28D002C, 0xEBFA4ECB, 0xE1500005\n"
        ".word 0xE320F000, 0xCAFFFF6D, 0xE2877001, 0xE3570004\n"
        ".word 0xBAFFFF64, 0xE59F13A8, 0xEDDFAAEA, 0xED9FBAEB\n"
        ".word 0xE3A00013, 0xEEB08A6A, 0xEEF09A4B, 0xEDDF8AE6\n"
        ".word 0xED9F9AE7, 0xE2815028, 0xE1A07001, 0xE28D303C\n"
        ".word 0xE28D2038, 0xE58D0014, 0xEBFABA1C, 0xE28D3050\n"
        ".word 0xE28D204C, 0xE1A01005, 0xE3A00013, 0xEBFABA17\n"
        ".word 0xE3A09000, 0xE320F000, 0xEBFAAA1C, 0xED9FAAD9\n"
        ".word 0xE3500000, 0xE3A0B002, 0xDA0000CB, 0xE6FF0077\n"
        ".word 0xE6FF1075, 0xE58D0010, 0xE58D1008, 0xE1A00009\n"
        ".word 0xEBFAA9FA, 0xE1D010D8, 0xE59D2088, 0xE1A07000\n"
        ".word 0xE1510002, 0x1A0000BB, 0xE1D710DA, 0xE3510018\n"
        ".word 0x13510019, 0x1351001A, 0x1A0000B6, 0xEA000008\n"
        ".word 0xE59D1054, 0xE2810001, 0xE0812081, 0xE0821201\n"
        ".word 0xE58D0054, 0xE0881101, 0xE2811A05, 0xE2811EA9\n"
        ".word 0xEAFFFF96, 0xE3A01001, 0xE3A05000, 0xE28D002C\n"
        ".word 0xE58D1030, 0xEBFA4E8C, 0xE3500000, 0xE320F000\n"
        ".word 0xDA000013, 0xE1A01005, 0xE28D002C, 0xEBFA4E77\n"
        ".word 0xE1D010B8, 0xE1A06000, 0xE3510000, 0x1A000006\n"
        ".word 0xE5D60001, 0xE5D7100B, 0xE1500001, 0x1A000002\n"
        ".word 0xE1D610D3, 0xE58D1030, 0xEA000005, 0xE2855001\n"
        ".word 0xE28D002C, 0xEBFA4E78, 0xE1500005, 0xE320F000\n"
        ".word 0xCAFFFFEB, 0xE1D751F6, 0xE1D710D9, 0xE1D7C1FA\n"
        ".word 0xEE005A90, 0xE3A020FF, 0xE0881181, 0xEE00CA10\n"
        ".word 0xE5913B88, 0xEEB81AE0, 0xEE003A90, 0xEEB80AC0\n"
        ".word 0xEEF80AE0, 0xEEFD0AE0, 0xEE100A90, 0xEE003A90\n"
        ".word 0xE6BF0070, 0xEE020A10, 0xEEF80AE0, 0xEEB82AC2\n"
        ".word 0xEE600A8A, 0xEE012A08, 0xEEFD0AE0, 0xEEBD1AC2\n"
        ".word 0xEE103A90, 0xEE005A90, 0xE6BF3073, 0xEEF81AE0\n"
        ".word 0xEE00CA90, 0xEE11CA10, 0xEE013A10, 0xE6BF007C\n"
        ".word 0xEEF80AE0, 0xE08AC08A, 0xEEB81AC1, 0xE08CC20A\n"
        ".word 0xE088510C, 0xE2855B03, 0xE2855FA2, 0xEE011AA9\n"
        ".word 0xEEBD1AC1, 0xEE113A10, 0xEE010A10, 0xE6BF3073\n"
        ".word 0xEEF81AC1, 0xEEB01A68, 0xEE311AC1, 0xEEBD1AC1\n"
        ".word 0xEE110A10, 0xEE013A10, 0xE6BF0070, 0xE58D000C\n"
        ".word 0xEEF81AC1, 0xEEB01A49, 0xEE311AC1, 0xEEBD1AC1\n"
        ".word 0xEE113A10, 0xE6BF0073, 0xE58D0040, 0xE5911B8C\n"
        ".word 0xEE011A10, 0xEEB81AC1, 0xEEBD1AC1, 0xEE110A10\n"
        ".word 0xEE011A10, 0xE6BF0070, 0xEEB81AC1, 0xEE211A0A\n"
        ".word 0xEEBD1AC1, 0xEE111A10, 0xEE010A10, 0xE6BF3071\n"
        ".word 0xEEB81AC1, 0xEE001A08, 0xEEBD0AC1, 0xEE101A10\n"
        ".word 0xEE003A10, 0xE6BF1071, 0xEEB80AC0, 0xEE000AA9\n"
        ".word 0xEEBD0AC0, 0xEE103A10, 0xEE001A10, 0xE6BF3073\n"
        ".word 0xEEF80AC0, 0xEEB00A68, 0xEE300AC0, 0xEEBD0AC0\n"
        ".word 0xEE101A10, 0xEE003A10, 0xE6BF0071, 0xE58D0004\n"
        ".word 0xEEF80AC0, 0xEEB00A49, 0xEE300AC0, 0xEEBD0AC0\n"
        ".word 0xEE101A10, 0xE6BF0071, 0xE58D0044, 0xE59D0014\n"
        ".word 0xE5850000, 0xE5D60001, 0xE5C50004, 0xE1C5B2BC\n"
        ".word 0xE5C52005, 0xE5970000, 0xEBFB61E0, 0xEDDD0A03\n"
        ".word 0xED9D0A01, 0xE59D2030, 0xE1A01000, 0xEEF80AE0\n"
        ".word 0xEEB80AC0, 0xE1C512BE, 0xE3A03000, 0xE1C520B6\n"
        ".word 0xE1C533B0, 0xE1C533B2, 0xE59D0010, 0xE3E01000\n"
        ".word 0xE28AA001, 0xE1C500B8, 0xEDC50A03, 0xED850A04\n"
        ".word 0xED9D0A11, 0xEDDD0A10, 0xEEB81AC0, 0xED9D0A0E\n"
        ".word 0xEEF80AE0, 0xEEB80AC0, 0xED850A05, 0xED9D0A0F\n"
        ".word 0xEEB80AC0, 0xED850A06, 0xE59D0008, 0xE1C500BA\n"
        ".word 0xE285001C, 0xECC00A02, 0xED9D0A13, 0xEEB80AC0\n"
        ".word 0xED850A09, 0xED9D0A14, 0xEEB80AC0, 0xED850A0A\n"
        ".word 0xE1C533B4, 0xE5851048, 0xE2899001, 0xEBFAA94F\n"
        ".word 0xE1500009, 0xE320F000, 0xCAFFFF37, 0xE59F1010\n"
        ".word 0xEEB08A4B, 0xE3A00013, 0xE2815028, 0xE1A07001\n"
        ".word 0xEA000005, 0x00001B67, 0x3CC49BA6, 0x40E00000\n"
        ".word 0x3C449BA6, 0x40400000, 0x3F000000, 0xE28D303C\n"
        ".word 0xE28D2038, 0xE58D0014, 0xEBFAB934, 0xE28D3050\n"
        ".word 0xE28D204C, 0xE1A01005, 0xE3A00013, 0xEBFAB92F\n"
        ".word 0xE3A09000, 0xE320F000, 0xEBFAA934, 0xE3500000\n"
        ".word 0xE320F000, 0xDA0000C3, 0xE6FF0077, 0xE6FF1075\n"
        ".word 0xE58D0010, 0xE58D1008, 0xE1A00009, 0xEBFAA913\n"
        ".word 0xE1D010D8, 0xE59D2088, 0xE1A07000, 0xE1510002\n"
        ".word 0x05D7100A, 0x0351002B, 0x1A0000B1, 0xE5972000\n"
        ".word 0xE59F16B8, 0xE1520001, 0x1A000004, 0xE3A000EF\n"
        ".word 0xEBFC8B02, 0xE3500000, 0xE320F000, 0x1A0000A8\n"
        ".word 0xE3A01001, 0xE3A05000, 0xE28D002C, 0xE58D1030\n"
        ".word 0xEBFA4DA9, 0xE3500000, 0xE320F000, 0xDA000013\n"
        ".word 0xE1A01005, 0xE28D002C, 0xEBFA4D94, 0xE1D010B8\n"
        ".word 0xE1A06000, 0xE3510000, 0x1A000006, 0xE5D60001\n"
        ".word 0xE5D7100B, 0xE1500001, 0x1A000002, 0xE1D610D3\n"
        ".word 0xE58D1030, 0xEA000005, 0xE2855001, 0xE28D002C\n"
        ".word 0xEBFA4D95, 0xE1500005, 0xE320F000, 0xCAFFFFEB\n"
        ".word 0xE1D751F6, 0xE1D710D9, 0xE1D7C1FA, 0xEE005A90\n"
        ".word 0xE3A020FE, 0xE0881181, 0xEE00CA10, 0xE5913B88\n"
        ".word 0xEEB81AE0, 0xEE003A90, 0xEEB80AC0, 0xEEF80AE0\n"
        ".word 0xEEFD0AE0, 0xEE100A90, 0xEE003A90, 0xE6BF0070\n"
        ".word 0xEE020A10, 0xEEF80AE0, 0xEEB82AC2, 0xEE600A8A\n"
        ".word 0xEE012A2A, 0xEEFD0AE0, 0xEEBD1AC2, 0xEE103A90\n"
        ".word 0xEE005A90, 0xE6BF3073, 0xEEF81AE0, 0xEE00CA90\n"
        ".word 0xEE11CA10, 0xEE013A10, 0xE6BF007C, 0xEEF80AE0\n"
        ".word 0xE08AC08A, 0xEEB81AC1, 0xE08CC20A, 0xE088510C\n"
        ".word 0xE2855B03, 0xE2855FA2, 0xEE011A88, 0xEEBD1AC1\n"
        ".word 0xEE113A10, 0xEE010A10, 0xE6BF3073, 0xEEB81AC1\n"
        ".word 0xEE311A68, 0xEEBD1AC1, 0xEE110A10, 0xEE013A10\n"
        ".word 0xE6BF0070, 0xE58D000C, 0xEEB81AC1, 0xEE311A49\n"
        ".word 0xEEBD1AC1, 0xEE113A10, 0xE6BF0073, 0xE58D0040\n"
        ".word 0xE5911B8C, 0xEE011A10, 0xEEB81AC1, 0xEEBD1AC1\n"
        ".word 0xEE110A10, 0xEE011A10, 0xE6BF0070, 0xEEB81AC1\n"
        ".word 0xEE211A0A, 0xEEBD1AC1, 0xEE111A10, 0xEE010A10\n"
        ".word 0xE6BF3071, 0xEEB81AC1, 0xEE001A2A, 0xEEBD0AC1\n"
        ".word 0xEE101A10, 0xEE003A10, 0xE6BF1071, 0xEEB80AC0\n"
        ".word 0xEE000A88, 0xEEBD0AC0, 0xEE103A10, 0xEE001A10\n"
        ".word 0xE6BF3073, 0xEEB80AC0, 0xEE300A68, 0xEEBD0AC0\n"
        ".word 0xEE101A10, 0xEE003A10, 0xE6BF0071, 0xE58D0004\n"
        ".word 0xEEB80AC0, 0xEE300A49, 0xEEBD0AC0, 0xEE101A10\n"
        ".word 0xE6BF0071, 0xE58D0044, 0xE59D0014, 0xE5850000\n"
        ".word 0xE5D60001, 0xE5C50004, 0xE1C5B2BC, 0xE5C52005\n"
        ".word 0xE5970000, 0xEBFE0E47, 0xEDDD0A03, 0xED9D0A01\n"
        ".word 0xE59D2030, 0xE1A01000, 0xEEF80AE0, 0xEEB80AC0\n"
        ".word 0xE1C512BE, 0xE3A03000, 0xE1C520B6, 0xE1C533B0\n"
        ".word 0xE1C533B2, 0xE59D0010, 0xE3E01000, 0xE28AA001\n"
        ".word 0xE1C500B8, 0xEDC50A03, 0xED850A04, 0xED9D0A11\n"
        ".word 0xEDDD0A10, 0xEEB81AC0, 0xED9D0A0E, 0xEEF80AE0\n"
        ".word 0xEEB80AC0, 0xED850A05, 0xED9D0A0F, 0xEEB80AC0\n"
        ".word 0xED850A06, 0xE59D0008, 0xE1C500BA, 0xE285001C\n"
        ".word 0xECC00A02, 0xED9D0A13, 0xEEB80AC0, 0xED850A09\n"
        ".word 0xED9D0A14, 0xEEB80AC0, 0xED850A0A, 0xE1C533B4\n"
        ".word 0xE5851048, 0xE2899001, 0xEBFAA870, 0xE1500009\n"
        ".word 0xE320F000, 0xCAFFFF3F, 0xE59F03E4, 0xE2881A06\n"
        ".word 0xE58D1058, 0xE780A008, 0xE59D0054, 0xE58101B0\n"
        ".word 0xE3A01000, 0xE3A02000, 0xE0810081, 0xE2811002\n"
        ".word 0xE0883200, 0xE59F03BC, 0xE3510B01, 0xE7C02003\n"
        ".word 0xE2800030, 0xE7C02003, 0xBAFFFFF5, 0xE3A00000\n"
        ".word 0xE58D0028, 0xE28D002C, 0xEBFAA457, 0xEDDF8AE6\n"
        ".word 0xED9F9AE6, 0xE3500000, 0xDA0000B6, 0xE59D1028\n"
        ".word 0xE28D002C, 0xEBFAA441, 0xE1D010F0, 0xE1A05000\n"
        ".word 0xE59D0088, 0xE1510000, 0x1A0000A6, 0xE1D500D8\n"
        ".word 0xE1D510D6, 0xEEB08A68, 0xE0400001, 0xE2800001\n"
        ".word 0xE1D510D9, 0xE0800FA0, 0xE1A070C0, 0xE1D500D7\n"
        ".word 0xE0410000, 0xE2800001, 0xE0800FA0, 0xE1A000C0\n"
        ".word 0xE58D0008, 0xE59D0058, 0xE59031B0, 0xE3E00062\n"
        ".word 0xE58D0030, 0xE3530000, 0xC5D52004, 0xE3A00000\n"
        ".word 0xDA000014, 0xE0801080, 0xE0811200, 0xE0881101\n"
        ".word 0xE2811A05, 0xE2811EA9, 0xE5D1C004, 0xE152000C\n"
        ".word 0x1A000009, 0xE3A020F5, 0xE0420080, 0xEE000A10\n"
        ".word 0xE1D110F6, 0xE3510063, 0xE58D1030, 0xEEB80AC0\n"
        ".word 0xEE208A09, 0x0A00007F, 0xEA000002, 0xE2800001\n"
        ".word 0xE1530000, 0xCAFFFFEA, 0xE3A0A000, 0xE28D002C\n"
        ".word 0xEBFA4CB1, 0xE3500000, 0xE320F000, 0xDA00000F\n"
        ".word 0xE1A0100A, 0xE28D002C, 0xEBFA4C9C, 0xE1A06000\n"
        ".word 0xE5D50004, 0xE5D61001, 0xE1500001, 0x01D600B8\n"
        ".word 0x03500000, 0x0A000005, 0xE28AA001, 0xE28D002C\n"
        ".word 0xEBFA4CA1, 0xE150000A, 0xE320F000, 0xCAFFFFEF\n"
        ".word 0xE1D611F0, 0xE1D630FE, 0xE58D1004, 0xE1D601D2\n"
        ".word 0xE0832FA3, 0xE0811FA1, 0xE08000C2, 0xE6BF0070\n"
        ".word 0xE58D0040, 0xE1D601D3, 0xE08000C1, 0xE3A01000\n"
        ".word 0xE6BF0070, 0xE58D0044, 0xE59D0008, 0xE3500000\n"
        ".word 0xDA000054, 0xE59D0030, 0xE6BF0070, 0xE58D0014\n"
        ".word 0xE3570000, 0xE3A02000, 0xDA00004A, 0xE081C081\n"
        ".word 0xE0810081, 0xE1A0C18C, 0xE1A0A100, 0xE5D50004\n"
        ".word 0xE350008E, 0x1A00000A, 0xE2420003, 0xE3500001\n"
        ".word 0x8A000007, 0xE3510000, 0xBA000001, 0xE3510002\n"
        ".word 0xDA000039, 0xE3510005, 0xBA000001, 0xE3510006\n"
        ".word 0xDA000035, 0xE3540B01, 0xAA000033, 0xE0840084\n"
        ".word 0xE3A09000, 0xE0880200, 0xE2800A06, 0xE2800F6D\n"
        ".word 0xE3A0B001, 0xE5C09000, 0xE5C0B001, 0xE5D5B004\n"
        ".word 0xEE00CA90, 0xE2844001, 0xE5C0B002, 0xE59D9014\n"
        ".word 0xE1C090B6, 0xE5D6B002, 0xEEF80AE0, 0xE5C0B003\n"
        ".word 0xE5D0E002, 0xED9D0A01, 0xE59FB174, 0xEEB80AC0\n"
        ".word 0xE08BB18E, 0xE1DBE0B2, 0xE1DBB0B0, 0xE02BB19E\n"
        ".word 0xE082E082, 0xEE301A80, 0xE1A0E18E, 0xEE003A10\n"
        ".word 0xEE00EA90, 0xE08BB002, 0xE580B008, 0xE082B082\n"
        ".word 0xEEB80AC0, 0xEEF80AE0, 0xE1A0B10B, 0xEE300A80\n"
        ".word 0xEE00BA90, 0xEEF80AE0, 0xED800A03, 0xED801A04\n"
        ".word 0xED9D0A10, 0xEEB80AC0, 0xEE300A80, 0xEE00AA90\n"
        ".word 0xEEF80AE0, 0xED800A05, 0xED9D0A11, 0xEEB80AC0\n"
        ".word 0xEE300A80, 0xED800A06, 0xED808A0B, 0xE2822001\n"
        ".word 0xE1570002, 0xCAFFFFB8, 0xE59D0008, 0xE2811001\n"
        ".word 0xE1500001, 0xCAFFFFAD, 0xE59D0028, 0xE2800001\n"
        ".word 0xE58D0028, 0xE28D002C, 0xEBFAA39F, 0xE59D1028\n"
        ".word 0xE1500001, 0xCAFFFF48, 0xE3A07000, 0xE28D002C\n"
        ".word 0xEB000645, 0xE3500000, 0xE320F000, 0xDA00006C\n"
        ".word 0xE3A0B000, 0xE3A0A001, 0xE3E09000, 0xE1A01007\n"
        ".word 0xE28D002C, 0xEB00061F, 0xE1A06000, 0xE1D000F0\n"
        ".word 0xE3700001, 0x0A000062, 0xE59D1088, 0xE1500001\n"
        ".word 0x1A000059, 0xE59D0058, 0xEEB08A68, 0xE59031B0\n"
        ".word 0xE3A00000, 0xE3530000, 0xC5D62002, 0xDA000018\n"
        ".word 0xE0801080, 0xE0811200, 0xE0881101, 0xE2811A05\n"
        ".word 0xE2811EA9, 0xE5D1C004, 0xE152000C, 0x1A00000D\n"
        ".word 0xE3A020F5, 0xE0420080, 0xEE000A10, 0xE1D110F6\n"
        ".word 0xE58D1030, 0xEEB80AC0, 0xEE208A09, 0xEA000008\n"
        ".word 0x00103001, 0x00005A88, 0x000061B4, 0x00000000\n"
        ".word 0x3B800000, 0x004C3228, 0xE2800001, 0xE1530000\n"
        ".word 0xCAFFFFE6, 0xE3A05000, 0xE28D002C, 0xEBFA4BFA\n"
        ".word 0xE3500000, 0xE320F000, 0xDA00000E, 0xE1A01005\n"
        ".word 0xE28D002C, 0xEBFA4BE5, 0xE5D61002, 0xE5D02001\n"
        ".word 0xE1510002, 0x01D000B8, 0x03500000, 0x0A000005\n"
        ".word 0xE2855001, 0xE28D002C, 0xEBFA4BEB, 0xE1500005\n"
        ".word 0xE320F000, 0xCAFFFFF0, 0xE3540B01, 0xAA000022\n"
        ".word 0xE0840084, 0xE2844001, 0xE0880200, 0xE2800A06\n"
        ".word 0xE2800F6D, 0xE5C0B000, 0xE5C0A001, 0xE5D61002\n"
        ".word 0xE59D2030, 0xE5C01002, 0xE1C020B6, 0xE5D61003\n"
        ".word 0xE5C01003, 0xE5D61004, 0xE5C01004, 0xE5D61005\n"
        ".word 0xE5C01005, 0xE5809008, 0xE1D610F6, 0xEE001A10\n"
        ".word 0xEEB80AC0, 0xED800A03, 0xE1D610F8, 0xEE001A10\n"
        ".word 0xEEB80AC0, 0xED800A04, 0xE5D6100A, 0xEE001A10\n"
        ".word 0xEEB80A40, 0xED800A05, 0xE5D6100B, 0xEE001A10\n"
        ".word 0xEEB80A40, 0xED800A06, 0xED808A0B, 0xE2877001\n"
        ".word 0xE28D002C, 0xEB0005D8, 0xE1500007, 0xE320F000\n"
        ".word 0xCAFFFF95, 0xE59F0010, 0xE7804008, 0xE28DD064\n"
        ".word 0xECBD8B08, 0xE28DD008, 0xE8BD8FF0, 0x000121B4\n"
    );
}

// Exact ARMv6K extent from code.bin. It returns at 0x0039AE7C; the next
// function starts at 0x0039AE80.
// DECOMP_FUNC(0x00399f28, 3928)
__attribute__((naked)) void script_vm_func_00399f28(WorldMapWork*) {
    asm volatile(
        ".arm\n"
        ".word 0xE92D4FF1, 0xED2D8B10, 0xE24DD098, 0xEBFCA2F8\n"
        ".word 0xE59D00D8, 0xE2800C01, 0xE2800062, 0xE58D0060\n"
        ".word 0xEBFA6007, 0xE58D000C, 0xE59D0060, 0xEBFA621A\n"
        ".word 0xE59D0060, 0xEBFA6222, 0xEDD0CA00, 0xEDD09A02\n"
        ".word 0xE59D0060, 0xEBFA5FF9, 0xECD0BA02, 0xE28D1058\n"
        ".word 0xE59D00D8, 0xE2800F59, 0xEBFA5F71, 0xE59F13B4\n"
        ".word 0xE3A0000B, 0xE3A0B000, 0xE5810010, 0xE59D00D8\n"
        ".word 0xE5900010, 0xE3100002, 0x1A0003B3, 0xE59F0398\n"
        ".word 0xEBFC9AFE, 0xE3500000, 0x0A0003AF, 0xE59D000C\n"
        ".word 0xEBFBBC88, 0xE3500002, 0x13500003, 0xE59D00D8\n"
        ".word 0x03A0B001, 0xE3A01001, 0xEBFA61C4, 0xE59F436C\n"
        ".word 0xEDDFFADB, 0xE5D40025, 0xE3500000, 0x1A000375\n"
        ".word 0xEBFC7A79, 0xE3500000, 0x1A000372, 0xE59D000C\n"
        ".word 0xED9F0AD4, 0xE3500065, 0x0A000006, 0xE3500066\n"
        ".word 0xEDDF0AD1, 0xED9F2AD1, 0x0A0000D7, 0xE3500067\n"
        ".word 0x0A00026A, 0xEA000367, 0xEDDF1ACD, 0xED9F1ACD\n"
        ".word 0xED9F3ACD, 0xEE7C1AE1, 0xEE793AC1, 0xEDDF2ACB\n"
        ".word 0xEEB02A6F, 0xEDDF0ACA, 0xE3A05000, 0xEE7C8A20\n"
        ".word 0xEE3B8A82, 0xEE231A21, 0xEE621AA3, 0xEE38AAC0\n"
        ".word 0xEE78AA80, 0xEE789A00, 0xEE311A42, 0xEE710AE0\n"
        ".word 0xEE389A40, 0xEE3B1AC1, 0xEE7C1A60, 0xEEFD0AC1\n"
        ".word 0xEEBD1AE1, 0xEE106A90, 0xEE118A10, 0xE1A00FC5\n"
        ".word 0xE2857040, 0xE0850D20, 0xE58D006C, 0xE0880005\n"
        ".word 0xE3A04000, 0xE085A008, 0xE0879008, 0xE58D0070\n"
        ".word 0xE2841040, 0xE0910006, 0xE58D1054, 0xE28D1048\n"
        ".word 0xE58D4050, 0xE88100A0, 0x4A000095, 0xE0841006\n"
        ".word 0xE3510D05, 0xCA000092, 0xE3590008, 0xBA000090\n"
        ".word 0xE35A00E8, 0xCA00008E, 0xEE000A10, 0xEEB80AC0\n"
        ".word 0xEEB40AC8, 0xEEF1FA10, 0xBA00000E, 0xEE001A10\n"
        ".word 0xEEB80AC0, 0xEEB40AC8, 0xEEF1FA10, 0x8A000009\n"
        ".word 0xEE009A10, 0xEEB80AC0, 0xEEB40AE8, 0xEEF1FA10\n"
        ".word 0xBA000004, 0xEE00AA10, 0xEEB80AC0, 0xEEB40AE8\n"
        ".word 0xEEF1FA10, 0x9A00004F, 0xEE000A10, 0xEEB80AC0\n"
        ".word 0xEEB40AC9, 0xEEF1FA10, 0xBA00000E, 0xEE001A10\n"
        ".word 0xEEB80AC0, 0xEEB40AC9, 0xEEF1FA10, 0x8A000009\n"
        ".word 0xEE009A10, 0xEEB80AC0, 0xEEB40AE8, 0xEEF1FA10\n"
        ".word 0xBA000004, 0xEE00AA10, 0xEEB80AC0, 0xEEB40AE8\n"
        ".word 0xEEF1FA10, 0x9A00003B, 0xEE000A10, 0xEEB80AC0\n"
        ".word 0xEEB40AE9, 0xEEF1FA10, 0xBA00000E, 0xEE001A10\n"
        ".word 0xEEB80AC0, 0xEEB40AE9, 0xEEF1FA10, 0x8A000009\n"
        ".word 0xEE009A10, 0xEEB80AC0, 0xEEB40AE8, 0xEEF1FA10\n"
        ".word 0xBA000004, 0xEE00AA10, 0xEEB80AC0, 0xEEB40AE8\n"
        ".word 0xEEF1FA10, 0x9A000027, 0xEE000A10, 0xEEB80AC0\n"
        ".word 0xEEB40AC8, 0xEEF1FA10, 0xBA00000E, 0xEE001A10\n"
        ".word 0xEEB80AC0, 0xEEB40AC8, 0xEEF1FA10, 0x8A000009\n"
        ".word 0xEE009A10, 0xEEB80AC0, 0xEEB40ACA, 0xEEF1FA10\n"
        ".word 0xBA000004, 0xEE00AA10, 0xEEB80AC0, 0xEEB40ACA\n"
        ".word 0xEEF1FA10, 0x9A000013, 0xEE000A10, 0xEEB80AC0\n"
        ".word 0xEEB40AC8, 0xEEF1FA10, 0xBA000015, 0xEE001A10\n"
        ".word 0xEEB80AC0, 0xEEB40AC8, 0xEEF1FA10, 0x8A000010\n"
        ".word 0xEE009A10, 0xEEB80AC0, 0xEEB40AEA, 0xEEF1FA10\n"
        ".word 0xBA00000B, 0xEE00AA10, 0xEEB80AC0, 0xEEB40AEA\n"
        ".word 0xEEF1FA10, 0x8A000006, 0xE59D106C, 0xE1A00FC4\n"
        ".word 0xE0840D20, 0xE1A02341, 0xE1A01340, 0xE59D000C\n"
        ".word 0xEBFA5E76, 0xE59D106C, 0xE1A00FC4, 0xE0840D20\n"
        ".word 0xE1A02341, 0xE1A01340, 0xE59D000C, 0xEBFA5E32\n"
        ".word 0xE1D0000B, 0xE320F000, 0x1A000003, 0xE59F008C\n"
        ".word 0xE59003E0, 0xE3500000, 0x0A000015, 0xED9D0A1C\n"
        ".word 0xEDDD0A17, 0xE59F006C, 0xEEB80AC0, 0xE59F2094\n"
        ".word 0xE3A0101C, 0xEE700A20, 0xED900A04, 0xE28D0048\n"
        ".word 0xEEFD0AE0, 0xEDCD0A00, 0xED8D0A01, 0xE58D0008\n"
        ".word 0xE0860004, 0xEE000A10, 0xEDDD0A16, 0xE3A00002\n"
        ".word 0xEEB80AC0, 0xEE300A20, 0xEEBD0AC0, 0xEE103A10\n"
        ".word 0xEBFC58E0, 0xE2844040, 0xE3540D05, 0xBAFFFF5F\n"
        ".word 0xE2855040, 0xE3550E19, 0xBAFFFF53, 0xE35B0000\n"
        ".word 0x1A0002A0, 0xEA000290, 0x0044CDC8, 0x00000529\n"
        ".word 0x0049F91C, 0x43200000, 0x41000000, 0xC684D000\n"
        ".word 0x3C311FD4, 0xC6C73800, 0xC6908800, 0x3C300EFF\n"
        ".word 0x3C2C7692, 0x42F00000, 0x00001770, 0xEDDF1AE5\n"
        ".word 0xEE7C0AE0, 0xEDDF2AE4, 0xEE393AE1, 0xEEB00A6F\n"
        ".word 0xED1F1A09, 0xE3A05000, 0xEE3C9A01, 0xEE3B8A80\n"
        ".word 0xEE621AA0, 0xEE620A03, 0xEE310AC0, 0xEDDF1ADE\n"
        ".word 0xEE700AC1, 0xEE38EA21, 0xEE3B0AC0, 0xEE3C1A60\n"
        ".word 0xEEFD0AC0, 0xEEBD0AC1, 0xED9F1AD6, 0xEE78DA41\n"
        ".word 0xEE106A90, 0xEDDF0AD2, 0xEE108A10, 0xED9F0ACF\n"
        ".word 0xEE391A20, 0xEE39DA60, 0xEE392A40, 0xEE788A40\n"
        ".word 0xEE39BA00, 0xEE78AA00, 0xEE38AA20, 0xEEB0FA41\n"
        ".word 0xEEF0EA42, 0xE1A00FC5, 0xE2857040, 0xE085AD20\n"
        ".word 0xE0850008, 0xE58D0088, 0xE0880005, 0xE3A04000\n"
        ".word 0xE0879008, 0xE58D008C, 0xE2841040, 0xE0910006\n"
        ".word 0xE58D1034, 0xE28D1028, 0xE58D4030, 0xE88100A0\n"
        ".word 0x4A000159, 0xE0841006, 0xE3510D05, 0xCA000156\n"
        ".word 0xE3590008, 0xBA000154, 0xE59D2088, 0xE35200E8\n"
        ".word 0xCA000151, 0xEE000A10, 0xEEB80AC0, 0xEEB40AC8\n"
        ".word 0xEEF1FA10, 0xBA00000E, 0xEE001A10, 0xEEB80AC0\n"
        ".word 0xEEB40AC8, 0xEEF1FA10, 0x8A000009, 0xEE009A10\n"
        ".word 0xEEB80AC0, 0xEEB40AC9, 0xEEF1FA10, 0xBA000004\n"
        ".word 0xEE002A10, 0xEEB80AC0, 0xEEB40AC9, 0xEEF1FA10\n"
        ".word 0x9A000065, 0xEE000A10, 0xEEB80AC0, 0xEEB40AE8\n"
        ".word 0xEEF1FA10, 0xBA00000E, 0xEE001A10, 0xEEB80AC0\n"
        ".word 0xEEB40AE8, 0xEEF1FA10, 0x8A000009, 0xEE009A10\n"
        ".word 0xEEB80AC0, 0xEEB40AC9, 0xEEF1FA10, 0xBA000004\n"
        ".word 0xEE002A10, 0xEEB80AC0, 0xEEB40AC9, 0xEEF1FA10\n"
        ".word 0x9A000051, 0xEE000A10, 0xEEB80AC0, 0xEEB40AEA\n"
        ".word 0xEEF1FA10, 0xBA00000E, 0xEE001A10, 0xEEB80AC0\n"
        ".word 0xEEB40AEA, 0xEEF1FA10, 0x8A000009, 0xEE009A10\n"
        ".word 0xEEB80AC0, 0xEEB40AC9, 0xEEF1FA10, 0xBA000004\n"
        ".word 0xEE002A10, 0xEEB80AC0, 0xEEB40AC9, 0xEEF1FA10\n"
        ".word 0x9A00003D, 0xEE000A10, 0xEEB80AC0, 0xEEB40AC8\n"
        ".word 0xEEF1FA10, 0xBA000010, 0xEE001A10, 0xEEB80AC0\n"
        ".word 0xEEB40AC8, 0xEEF1FA10, 0x8A00000B, 0xEE009A10\n"
        ".word 0xEEF00A6E, 0xEEB80AC0, 0xEEB40AE0, 0xEEF1FA10\n"
        ".word 0xBA000005, 0xEE002A10, 0xEEF80AC0, 0xEEB00A6E\n"
        ".word 0xEEF40AC0, 0xEEF1FA10, 0x9A000027, 0xEE000A10\n"
        ".word 0xEEB80AC0, 0xEEB40AC8, 0xEEF1FA10, 0xBA00000E\n"
        ".word 0xEE001A10, 0xEEB80AC0, 0xEEB40AC8, 0xEEF1FA10\n"
        ".word 0x8A000009, 0xEE009A10, 0xEEB80AC0, 0xEEB40ACB\n"
        ".word 0xEEF1FA10, 0xBA000004, 0xEE002A10, 0xEEB80AC0\n"
        ".word 0xEEB40ACB, 0xEEF1FA10, 0x9A000013, 0xEE000A10\n"
        ".word 0xEEB80AC0, 0xEEB40AE8, 0xEEF1FA10, 0xBA000014\n"
        ".word 0xEE001A10, 0xEEB80AC0, 0xEEB40AE8, 0xEEF1FA10\n"
        ".word 0x8A00000F, 0xEE009A10, 0xEEB80AC0, 0xEEB40ACB\n"
        ".word 0xEEF1FA10, 0xBA00000A, 0xEE002A10, 0xEEB80AC0\n"
        ".word 0xEEB40ACB, 0xEEF1FA10, 0x8A000005, 0xE1A00FC4\n"
        ".word 0xE1A0234A, 0xE0840D20, 0xE1A01340, 0xE59D000C\n"
        ".word 0xEBFA5D82, 0xE59F10C4, 0xEE1C0A90, 0xE1500001\n"
        ".word 0xDA000043, 0xE59D0034, 0xE0800006, 0xEE000A10\n"
        ".word 0xEEB80AC0, 0xEEB40ACA, 0xEEF1FA10, 0xBA000014\n"
        ".word 0xE59D1030, 0xE0811006, 0xEE001A10, 0xEEB80AC0\n"
        ".word 0xEEB40ACA, 0xEEF1FA10, 0x8A00000D, 0xE59D102C\n"
        ".word 0xE0811008, 0xEE001A10, 0xEEB80AC0, 0xEEB40ACD\n"
        ".word 0xEEF1FA10, 0xBA000006, 0xE59D1028, 0xE0811008\n"
        ".word 0xEE001A10, 0xEEB80AC0, 0xEEB40ACD, 0xEEF1FA10\n"
        ".word 0x9A000021, 0xEE000A10, 0xEEB80AC0, 0xEEB40ACA\n"
        ".word 0xEEF1FA10, 0xBA000022, 0xE59D0030, 0xE0800006\n"
        ".word 0xEE000A10, 0xEEB80AC0, 0xEEB40ACA, 0xEEF1FA10\n"
        ".word 0x8A00001B, 0xEA000006, 0xC68CA000, 0x3C278A24\n"
        ".word 0x41600000, 0x42000000, 0x41E00000, 0x41C00000\n"
        ".word 0x459C4000, 0xE59D002C, 0xE0800008, 0xEE000A10\n"
        ".word 0xEEB80AC0, 0xEEB40ACB, 0xEEF1FA10, 0xBA00000C\n"
        ".word 0xE59D0028, 0xE0800008, 0xEE000A10, 0xEEB80AC0\n"
        ".word 0xEEB40ACB, 0xEEF1FA10, 0x8A000005, 0xE1A00FC4\n"
        ".word 0xE1A0234A, 0xE0840D20, 0xE1A01340, 0xE59D000C\n"
        ".word 0xEBFA5D3A, 0xE59F1608, 0xEE190A90, 0xE1500001\n"
        ".word 0x9A00003B, 0xE59D0034, 0xE0800006, 0xEE000A10\n"
        ".word 0xEEB80AC0, 0xEEB40AED, 0xEEF1FA10, 0xBA000014\n"
        ".word 0xE59D1030, 0xE0811006, 0xEE001A10, 0xEEB80AC0\n"
        ".word 0xEEB40AED, 0xEEF1FA10, 0x8A00000D, 0xE59D102C\n"
        ".word 0xE0811008, 0xEE001A10, 0xEEB80AC0, 0xEEB40ACD\n"
        ".word 0xEEF1FA10, 0xBA000006, 0xE59D1028, 0xE0811008\n"
        ".word 0xEE001A10, 0xEEB80AC0, 0xEEB40ACD, 0xEEF1FA10\n"
        ".word 0x9A000019, 0xEE000A10, 0xEEB80AC0, 0xEEB40ACE\n"
        ".word 0xEEF1FA10, 0xBA00001A, 0xE59D0030, 0xE0800006\n"
        ".word 0xEE000A10, 0xEEB80AC0, 0xEEB40ACE, 0xEEF1FA10\n"
        ".word 0x8A000013, 0xE59D002C, 0xE0800008, 0xEE000A10\n"
        ".word 0xEEB80AC0, 0xEEB40ACD, 0xEEF1FA10, 0xBA00000C\n"
        ".word 0xE59D0028, 0xE0800008, 0xEE000A10, 0xEEB80AC0\n"
        ".word 0xEEB40ACD, 0xEEF1FA10, 0x8A000005, 0xE1A00FC4\n"
        ".word 0xE1A0234A, 0xE0840D20, 0xE1A01340, 0xE59D000C\n"
        ".word 0xEBFA5CFA, 0xE59F150C, 0xEE190A90, 0xE1500001\n"
        ".word 0xDA000023, 0xE59D0034, 0xE0800006, 0xEE000A10\n"
        ".word 0xEEB80AC0, 0xEEB48AC0, 0xEEF1FA10, 0x8A00001C\n"
        ".word 0xE59D0030, 0xE0800006, 0xEE000A10, 0xEEB80AC0\n"
        ".word 0xEEB40AC8, 0xEEF1FA10, 0x8A000015, 0xE59D002C\n"
        ".word 0xE0800008, 0xEE000A10, 0xEEF80AC0, 0xEEB00A4F\n"
        ".word 0xEEF40AC0, 0xEEF1FA10, 0xBA00000D, 0xE59D0028\n"
        ".word 0xE0800008, 0xEE000A10, 0xEEF80AC0, 0xEEB00A4F\n"
        ".word 0xEEF40AC0, 0xEEF1FA10, 0x8A000005, 0xE1A00FC4\n"
        ".word 0xE1A0234A, 0xE0840D20, 0xE1A01340, 0xE59D000C\n"
        ".word 0xEBFA5CD2, 0xE1A00FC4, 0xE1A0234A, 0xE0840D20\n"
        ".word 0xE1A01340, 0xE59D000C, 0xEBFA5C8F, 0xE1D0000B\n"
        ".word 0xE320F000, 0x1A000003, 0xE51F0600, 0xE59003E0\n"
        ".word 0xE3500000, 0x0A000014, 0xED9D0A23, 0xEDDD0A17\n"
        ".word 0xE51F0620, 0xEEB80AC0, 0xE59F242C, 0xE3A0101C\n"
        ".word 0xEE300A20, 0xEDD00A04, 0xE28D0028, 0xEEBD0AC0\n"
        ".word 0xEC8D0A02, 0xE58D0008, 0xE0860004, 0xEE000A10\n"
        ".word 0xEDDD0A16, 0xE3A00002, 0xEEB80AC0, 0xEE300A20\n"
        ".word 0xEEBD0AC0, 0xEE103A10, 0xEBFC573E, 0xE2844040\n"
        ".word 0xE3540D05, 0xBAFFFE9B, 0xE2855040, 0xE3550E19\n"
        ".word 0xBAFFFE8F, 0xE35B0000, 0x1A0000FE, 0xEA0000EE\n"
        ".word 0xEDDF2AF2, 0xEE7C0AE0, 0xED9F3AF1, 0xEE792AE2\n"
        ".word 0xEEB01A6F, 0xEDDF1AEF, 0xEEB0AA69, 0xE3A05000\n"
        ".word 0xEE7C8A21, 0xEE3B8A81, 0xEE630A20, 0xEE222A22\n"
        ".word 0xEE78AAC0, 0xEE38BA80, 0xEE789A00, 0xEE700AC1\n"
        ".word 0xEE389A40, 0xEE321A61, 0xEE7B0AE0, 0xEE7C1A41\n"
        ".word 0xEEBD1AE0, 0xEEFD0AE1, 0xEE116A10, 0xEE108A90\n"
        ".word 0xEDDF0ADD, 0xEE78CAA0, 0xE1A00FC5, 0xE2857040\n"
        ".word 0xE0850D20, 0xE58D0074, 0xE0880005, 0xE3A04000\n"
        ".word 0xE085A008, 0xE0879008, 0xE58D0078, 0xE2841040\n"
        ".word 0xE0910006, 0xE58D1034, 0xE28D1028, 0xE58D4030\n"
        ".word 0xE88100A0, 0x4A0000BC, 0xE0841006, 0xE3510D05\n"
        ".word 0xCA0000B9, 0xE3590008, 0xBA0000B7, 0xE35A00E8\n"
        ".word 0xCA0000B5, 0xEE000A10, 0xEEB80AC0, 0xEEB40AC8\n"
        ".word 0xEEF1FA10, 0xBA00000E, 0xEE001A10, 0xEEB80AC0\n"
        ".word 0xEEB40AC8, 0xEEF1FA10, 0x8A000009, 0xEE009A10\n"
        ".word 0xEEB80AC0, 0xEEB40AE8, 0xEEF1FA10, 0xBA000004\n"
        ".word 0xEE00AA10, 0xEEB80AC0, 0xEEB40AE8, 0xEEF1FA10\n"
        ".word 0x9A00004F, 0xEE000A10, 0xEEB80AC0, 0xEEB40AC9\n"
        ".word 0xEEF1FA10, 0xBA00000E, 0xEE001A10, 0xEEB80AC0\n"
        ".word 0xEEB40AC9, 0xEEF1FA10, 0x8A000009, 0xEE009A10\n"
        ".word 0xEEB80AC0, 0xEEB40AE8, 0xEEF1FA10, 0xBA000004\n"
        ".word 0xEE00AA10, 0xEEB80AC0, 0xEEB40AE8, 0xEEF1FA10\n"
        ".word 0x9A00003B, 0xEE000A10, 0xEEB80AC0, 0xEEB40AE9\n"
        ".word 0xEEF1FA10, 0xBA00000E, 0xEE001A10, 0xEEB80AC0\n"
        ".word 0xEEB40AE9, 0xEEF1FA10, 0x8A000009, 0xEE009A10\n"
        ".word 0xEEB80AC0, 0xEEB40AE8, 0xEEF1FA10, 0xBA000004\n"
        ".word 0xEE00AA10, 0xEEB80AC0, 0xEEB40AE8, 0xEEF1FA10\n"
        ".word 0x9A000027, 0xEE000A10, 0xEEB80AC0, 0xEEB40AC8\n"
        ".word 0xEEF1FA10, 0xBA00000E, 0xEE001A10, 0xEEB80AC0\n"
        ".word 0xEEB40AC8, 0xEEF1FA10, 0x8A000009, 0xEE009A10\n"
        ".word 0xEEB80AC0, 0xEEB40AEA, 0xEEF1FA10, 0xBA000004\n"
        ".word 0xEE00AA10, 0xEEB80AC0, 0xEEB40AEA, 0xEEF1FA10\n"
        ".word 0x9A000013, 0xEE000A10, 0xEEB80AC0, 0xEEB40AC8\n"
        ".word 0xEEF1FA10, 0xBA000015, 0xEE001A10, 0xEEB80AC0\n"
        ".word 0xEEB40AC8, 0xEEF1FA10, 0x8A000010, 0xEE009A10\n"
        ".word 0xEEB80AC0, 0xEEB40ACB, 0xEEF1FA10, 0xBA00000B\n"
        ".word 0xEE00AA10, 0xEEB80AC0, 0xEEB40ACB, 0xEEF1FA10\n"
        ".word 0x8A000006, 0xE59D1074, 0xE1A00FC4, 0xE0840D20\n"
        ".word 0xE1A02341, 0xE1A01340, 0xE59D000C, 0xEBFA5C0B\n"
        ".word 0xE59F1168, 0xEE1A0A10, 0xE1500001, 0xDA000022\n"
        ".word 0xE59D0034, 0xE0800006, 0xEE000A10, 0xEEB80AC0\n"
        ".word 0xEEB48AC0, 0xEEF1FA10, 0x8A00001B, 0xE59D0030\n"
        ".word 0xE0800006, 0xEE000A10, 0xEEB80AC0, 0xEEB40AC8\n"
        ".word 0xEEF1FA10, 0x8A000014, 0xE59D002C, 0xE0800008\n"
        ".word 0xEE000A10, 0xEEB80AC0, 0xEEB40AEC, 0xEEF1FA10\n"
        ".word 0xBA00000D, 0xE59D0028, 0xE0800008, 0xEE000A10\n"
        ".word 0xEEB80AC0, 0xEEB40AEC, 0xEEF1FA10, 0x8A000006\n"
        ".word 0xE59D1074, 0xE1A00FC4, 0xE0840D20, 0xE1A02341\n"
        ".word 0xE1A01340, 0xE59D000C, 0xEBFA5BE4, 0xE59D1074\n"
        ".word 0xE1A00FC4, 0xE0840D20, 0xE1A02341, 0xE1A01340\n"
        ".word 0xE59D000C, 0xEBFA5BA0, 0xE1D0000B, 0xE320F000\n"
        ".word 0x1A000003, 0xE51F09BC, 0xE59003E0, 0xE3500000\n"
        ".word 0x0A000015, 0xED9D0A1E, 0xEDDD0A17, 0xE51F09DC\n"
        ".word 0xEEB80AC0, 0xE3A02D7D, 0xE5901010, 0xE28D0028\n"
        ".word 0xEE300A20, 0xEEBD0AC0, 0xED8D0A00, 0xE58D0008\n"
        ".word 0xE0860004, 0xEE000A10, 0xE58D1004, 0xEDDD0A16\n"
        ".word 0xE3A0101C, 0xE3A00002, 0xEEB80AC0, 0xEE300A20\n"
        ".word 0xEEBD0AC0, 0xEE103A10, 0xEBFC564E, 0xE2844040\n"
        ".word 0xE3540D05, 0xBAFFFF38, 0xE2855040, 0xE3550E19\n"
        ".word 0xBAFFFF2C, 0xE35B0000, 0x1A00000E, 0xE320F000\n"
        ".word 0xEA000007, 0xC59C4000, 0x45FA0000, 0x00001B58\n"
        ".word 0xC6947000, 0x3C2D1FD0, 0x42F00000, 0x41800000\n"
        ".word 0x453B8000, 0xE59D00D8, 0xEB000FEC, 0xE59D00D8\n"
        ".word 0xE320F000, 0xEB000F44, 0xEEF00A6F, 0xED1F0A0B\n"
        ".word 0xE51F4A90, 0xE35B0000, 0xEE7C8A00, 0xEE3B8AA0\n"
        ".word 0x1A00001E, 0xE59D0060, 0xEBFA5C36, 0xE59D00D8\n"
        ".word 0xE320F000, 0xEBFA5C11, 0xEEFD8AE8, 0xEEBD8AC8\n"
        ".word 0xE3A06001, 0xE3A0500B, 0xE2801C0B, 0xE88D0060\n"
        ".word 0xE59D00D8, 0xE28110C1, 0xEE183A90, 0xEE182A10\n"
        ".word 0xE2800F59, 0xEBFA5BCF, 0xE59D0060, 0xE320F000\n"
        ".word 0xEBFA5C45, 0xE59D00D8, 0xE320F000, 0xEBFA5BFF\n"
        ".word 0xE2801C0B, 0xE88D0060, 0xE59D00D8, 0xEE183A90\n"
        ".word 0xEE182A10, 0xE28110B9, 0xE2800F59, 0xEBFA5BC1\n"
        ".word 0xE59D00D8, 0xE3A01000, 0xEBFA5E20, 0xE3A000F1\n"
        ".word 0xE5840010, 0xE59D00D8, 0xEBFA5C42, 0xE28DD098\n"
        ".word 0xECBD8B10, 0xE8BD8FF8\n"
    );
}

// Exact ARMv6K span [0x00276CAC, 0x00277DCC), including interleaved pools.
// DECOMP_FUNC(0x00276cac, 4384)
__attribute__((naked)) void script_vm_func_00276cac() {
    asm volatile(
        ".arm\n"
        ".word 0xE92D43F0, 0xED2D8B0E, 0xE24DD054, 0xEB012F97\n"
        ".word 0xE59F8308, 0xEDDFAAC2, 0xE5981004, 0xE2810C02\n"
        ".word 0xE5D122B0, 0xE3520000, 0x0A00001D, 0xE59112B4\n"
        ".word 0xE28D000C, 0xEB00DD29, 0xE28D0018, 0xE28D600C\n"
        ".word 0xE8901022, 0xE5980004, 0xE2802040, 0xE8821022\n"
        ".word 0xE896001C, 0xE2806034, 0xE886001C, 0xE2806058\n"
        ".word 0xE280004C, 0xE8861022, 0xE880001C, 0xED9D0A03\n"
        ".word 0xEDDD1A06, 0xEDDD0A05, 0xED9D1A08, 0xEE300A61\n"
        ".word 0xEE700AC1, 0xEB002CDB, 0xEE601A2A, 0xE28D000C\n"
        ".word 0xEC900A03, 0xEBFF95E2, 0xE28DD054, 0xECBD8B0E\n"
        ".word 0xE8BD83F0, 0xE59FC288, 0xE28D4018, 0xED9F8A9D\n"
        ".word 0xED9FBA9D, 0xE89C100C, 0xE3A07000, 0xED9FAA9B\n"
        ".word 0xE884100C, 0xE59122A0, 0xE3520000, 0x0A000031\n"
        ".word 0xE1D02AB8, 0xE3520000, 0x058172A0, 0x0A000064\n"
        ".word 0xE1D01ABA, 0xED9F9A93, 0xE3A04000, 0xEE001A10\n"
        ".word 0xE28D9018, 0xE28D600C, 0xEEB80A40, 0xEE200A08\n"
        ".word 0xED8D0A03, 0xE1D01ABC, 0xEE001A10, 0xEEB80A40\n"
        ".word 0xEE200A08, 0xED8D0A04, 0xE1D00ABE, 0xEE000A10\n"
        ".word 0xEEB80A40, 0xEE200A08, 0xED8D0A05, 0xE0865104\n"
        ".word 0xED950A00, 0xEEB40A4A, 0xEEF1FA10, 0x0A000030\n"
        ".word 0xEB001B89, 0xEE200A0B, 0xE0890104, 0xEDD50A00\n"
        ".word 0xED901A00, 0xE5980004, 0xEE601A81, 0xE0800104\n"
        ".word 0xEE608A20, 0xED900AA5, 0xEEB01AC0, 0xEEF41AC1\n"
        ".word 0xEEF1FA10, 0xEE408A8B, 0x8A00000A, 0xEEB40ACA\n"
        ".word 0xEEF1FA10, 0x9E300A28, 0x9D800AA5, 0x8E300A68\n"
        ".word 0x9A00000D, 0xEA00000B, 0xED81AAA5, 0xED81AAA6\n"
        ".word 0xED81AAA7, 0xEA000032, 0xE320F000, 0xEB001B6E\n"
        ".word 0xEE300A4B, 0xE5980004, 0xE0800104, 0xEE600A28\n"
        ".word 0xED900AA5, 0xEE000A89, 0xED800AA5, 0xED950A00\n"
        ".word 0xE5980004, 0xEEF10A40, 0xE0800104, 0xED900AA5\n"
        ".word 0xEEB40AE0, 0xEEF1FA10, 0xDEB00A60, 0xED800AA5\n"
        ".word 0xEDD50A00, 0xEEB40AE0, 0xEEF1FA10, 0xCEB00A60\n"
        ".word 0xED800AA5, 0xE2844001, 0xE3540003, 0xBAFFFFC6\n"
        ".word 0xE5980004, 0xE2804C02, 0xE1D45AF8, 0xE3550000\n"
        ".word 0xDA000013, 0xE1D46ABA, 0xE2851005, 0xE1A00006\n"
        ".word 0xEB013C9E, 0xE0460000, 0xE1C40ABA, 0xE1D46ABC\n"
        ".word 0xE2851005, 0xE1A00006, 0xEB013C98, 0xE0460000\n"
        ".word 0xE1C40ABC, 0xE1D46ABE, 0xE2851005, 0xE1A00006\n"
        ".word 0xEB013C92, 0xE0460000, 0xE1C40ABE, 0xE2450001\n"
        ".word 0xE1C40AB8, 0xE5980004, 0xED9F0A2F, 0xEDDFDA2F\n"
        ".word 0xED9FEA2F, 0xE5901000, 0xEDDFBA2E, 0xEDDFCA2E\n"
        ".word 0xE3510003, 0x0A000033, 0xE3510004, 0xED9FDA2B\n"
        ".word 0x0A000052, 0xE59F90A8, 0xE5D0221C, 0xE59F50A8\n"
        ".word 0xEDDFEA28, 0xED9FCA29, 0xE3520000, 0xE2496765\n"
        ".word 0x0A000095, 0xEEF00A4A, 0xE5951000, 0xE2804E22\n"
        ".word 0xEDD01A13, 0xEDD02A15, 0xED910A07, 0xEEB02A60\n"
        ".word 0xED911A09, 0xEB00436F, 0xEE100A10, 0xE1590000\n"
        ".word 0xDA000065, 0xEE300A4C, 0xEE100A10, 0xE1560000\n"
        ".word 0xE5980004, 0xCEB00A6B, 0xEDD00A26, 0xE59F0050\n"
        ".word 0xEB0129EC, 0xE320F000, 0xE320F000, 0xEA00005F\n"
        ".word 0x004474F0, 0x42654CA3, 0x3C23D70A, 0x3F000000\n"
        ".word 0x00000000, 0x0040449C, 0x40000000, 0x42C80000\n"
        ".word 0x3FD55555, 0x48483200, 0x41A00000, 0x3F800000\n"
        ".word 0x42340000, 0x43340000, 0x430C0000, 0x00447E88\n"
        ".word 0x42200000, 0x0049F3F0, 0xEEF00A6C, 0xE51F0010\n"
        ".word 0xEB0129D4, 0xE5980004, 0xEEF01A6D, 0xEEB01A4E\n"
        ".word 0xEEF00A6B, 0xED900A1F, 0xE51F002C, 0xE3A01001\n"
        ".word 0xEB012BEE, 0xE5980004, 0xE2800064, 0xEC900A06\n"
        ".word 0xEBFF9507, 0xE51F0048, 0xE320F000, 0xEB0087E3\n"
        ".word 0xE5980004, 0xED900A19, 0xEDD01A1C, 0xEDD00A1B\n"
        ".word 0xED901A1E, 0xEE300A61, 0xEE700AC1, 0xEB002C09\n"
        ".word 0xE5980004, 0xEE601A2A, 0xE2800064, 0xEC900A03\n"
        ".word 0xEBFF950F, 0xE28DD054, 0xECBD8B0E, 0xE8BD83F0\n"
        ".word 0xEEF00A6C, 0xE51F0098, 0xEB0129B2, 0xEEF01A6D\n"
        ".word 0xEEB01A4E, 0xEEF00A6B, 0xEEB00A4D, 0xE51F00B0\n"
        ".word 0xE3A01001, 0xEB012BCD, 0xE5980004, 0xE280301C\n"
        ".word 0xE280208C, 0xE2801080, 0xE51F00CC, 0xEB012BF2\n"
        ".word 0xE5980004, 0xE2800080, 0xEC900A06, 0xEBFF94E0\n"
        ".word 0xE51F00E4, 0xE320F000, 0xEB0087BC, 0xE5980004\n"
        ".word 0xED900A20, 0xEDD01A23, 0xEDD00A22, 0xED901A25\n"
        ".word 0xEE300A61, 0xEE700AC1, 0xEB002BE2, 0xE5980004\n"
        ".word 0xEE601A2A, 0xE2800080, 0xEC900A03, 0xEBFF94E8\n"
        ".word 0xE28DD054, 0xECBD8B0E, 0xE8BD83F0, 0xE5980004\n"
        ".word 0xEEB00A6E, 0xEDD00A26, 0xE51F013C, 0xEB012989\n"
        ".word 0xE284003C, 0xEC900A03, 0xE2840030, 0xECD01A03\n"
        ".word 0xEBFF94C3, 0xE51F0158, 0xE320F000, 0xEB00879F\n"
        ".word 0xED940A0F, 0xEDD41A0C, 0xEDD40A11, 0xED941A0E\n"
        ".word 0xEE300A61, 0xEE700AC1, 0xEB002BC6, 0xEE601A2A\n"
        ".word 0xE284003C, 0xEC900A03, 0xEBFF94CD, 0xE284103C\n"
        ".word 0xE5980004, 0xE891000E, 0xE2844030, 0xE280504C\n"
        ".word 0xE2800058, 0xE885000E, 0xE894000E, 0xE880000E\n"
        ".word 0xE28DD054, 0xECBD8B0E, 0xE8BD83F0, 0xE3510006\n"
        ".word 0x1351000F, 0x0A000007, 0xEB012E50, 0xE5981004\n"
        ".word 0xE5912208, 0xE59140C4, 0xE3720001, 0x11A04002\n"
        ".word 0x0A00000F, 0xEA000025, 0xE280301C, 0xE2802058\n"
        ".word 0xE280104C, 0xE51F01F8, 0xEB012BA7, 0xE5980004\n"
        ".word 0xE280004C, 0xEC900A06, 0xEBFF9495, 0xE51F0210\n"
        ".word 0xE320F000, 0xEB008771, 0xE320F000, 0xE320F000\n"
        ".word 0xEA0002CD, 0xE59120AC, 0xE2822003, 0xE3520006\n"
        ".word 0x379FF102, 0xEA000011, 0x0027725C, 0x0027726C\n"
        ".word 0x00277264, 0x00277274, 0x00277280, 0x00277288\n"
        ".word 0xE3A04005, 0xEA000009, 0xE3A04008, 0xEA000007\n"
        ".word 0xE3A04009, 0xEA000005, 0xE5D0001D, 0xE0844000\n"
        ".word 0xEA000002, 0xE3A04006, 0xEA000000, 0xE3A0400A\n"
        ".word 0xE5950000, 0xEDDF8ABA, 0xE590201C, 0xE5812040\n"
        ".word 0xE5900024, 0xE5810048, 0xED910A06, 0xEE200A28\n"
        ".word 0xEB002D32, 0xE5980004, 0xE5951000, 0xE0802104\n"
        ".word 0xEDD10A07, 0xED921A62, 0xEE400A41, 0xEDC00A0D\n"
        ".word 0xED900A06, 0xEE200A28, 0xEB002CC9, 0xE5980004\n"
        ".word 0xE5952000, 0xED9F9AA7, 0xE0801104, 0xED911A62\n"
        ".word 0xEDD20A09, 0xEE400A41, 0xEDC00A0F, 0xED920A08\n"
        ".word 0xEDD10A32, 0xEE300A20, 0xED800A11, 0xED920A08\n"
        ".word 0xEDD10A42, 0xEE300A20, 0xED800A0E, 0xED900A06\n"
        ".word 0xEE300A49, 0xEE200A28, 0xEB002D14, 0xE5980004\n"
        ".word 0xE0801104, 0xEDD00A10, 0xED911A52, 0xEE400A01\n"
        ".word 0xEDC00A10, 0xED900A06, 0xEE300A49, 0xEE200A28\n"
        ".word 0xEB002CAB, 0xE5980004, 0xE0801104, 0xEDD00A12\n"
        ".word 0xED911A52, 0xEE400A01, 0xEDC00A12, 0xED900A06\n"
        ".word 0xEE300A49, 0xEE200A28, 0xEB002D00, 0xE5980004\n"
        ".word 0xE0801104, 0xEDD00A0D, 0xED911A52, 0xEE400A01\n"
        ".word 0xEDC00A0D, 0xED900A06, 0xEE300A49, 0xEE200A28\n"
        ".word 0xEB002C97, 0xE5980004, 0xE0801104, 0xEDD00A0F\n"
        ".word 0xED911A52, 0xE2801038, 0xE2802044, 0xEE400A01\n"
        ".word 0xEDC00A0F, 0xED900A0D, 0xEDD02A10, 0xECD10A02\n"
        ".word 0xEE300A62, 0xECD21A02, 0xE59F21AC, 0xEE700AE1\n"
        ".word 0xEE311A42, 0xEE200A00, 0xEE000AA0, 0xEE010A01\n"
        ".word 0xED901A86, 0xEEF10AC0, 0xED900A85, 0xEE101A90\n"
        ".word 0xE1510002, 0xE5D010A4, 0xBEF00A48, 0xE3510000\n"
        ".word 0x1E300A41, 0x1A000008, 0xE59F2170, 0xEE300A41\n"
        ".word 0xEE101A10, 0xE1510006, 0xCEB00A6B, 0xCA000002\n"
        ".word 0xEE101A10, 0xE1510002, 0x8D9F0A55, 0xEDD01A0E\n"
        ".word 0xE2802C02, 0xEE312A00, 0xEE711A81, 0xEE311A80\n"
        ".word 0xED801A0E, 0xED802A86, 0xE5D012B8, 0xE3510000\n"
        ".word 0x1A00000E, 0xE5951000, 0xEDDF1A4A, 0xED910A08\n"
        ".word 0xEE300A21, 0xEEB41AC0, 0xEEF1FA10, 0xCEB00A41\n"
        ".word 0xED9F1A45, 0xED800A0E, 0xEDD11A08, 0xEE311A81\n"
        ".word 0xEEB40AC1, 0xEEF1FA10, 0xCEB00A41, 0xED800A0E\n"
        ".word 0xEDD01A0D, 0xED903A10, 0xED900A0E, 0xED902A11\n"
        ".word 0xEE711AC3, 0xED901A0F, 0xEE300A42, 0xEDD02A12\n"
        ".word 0xE2803040, 0xEE311A62, 0xEE212AA1, 0xEE002A00\n"
        ".word 0xEE012A01, 0xEEF12AC2, 0xEE8C2AA2, 0xEDD32A02\n"
        ".word 0xEE611A82, 0xEE200A02, 0xEE211A02, 0xEE212AA0\n"
        ".word 0xEE601A20, 0xEE610A20, 0xED930A00, 0xED931A01\n"
        ".word 0xEE300A02, 0xEE311A21, 0xEE720AA0, 0xED800A0D\n"
        ".word 0xED801A0E, 0xEDC00A0F, 0xE5D210B8, 0xE3510000\n"
        ".word 0x0A000002, 0xE59000AC, 0xE3500000, 0x0BFE035F\n"
        ".word 0xE5980004, 0xE5901000, 0xE3510000, 0x1A00000A\n"
        ".word 0xE59F1058, 0xE5D113CC, 0xE3510000, 0x1A000006\n"
        ".word 0xE59F1048, 0xE5911370, 0xE3510001, 0x0A000002\n"
        ".word 0xE5D012B8, 0xE3510000, 0x0A00000D, 0xE2801034\n"
        ".word 0xE590003C, 0xE8910006, 0xE58D0008, 0xE88D0006\n"
        ".word 0xEA00000B, 0x3C8EFA35, 0x42B40000, 0x3C23D70A\n"
        ".word 0xC1A00000, 0xC1A00000, 0x40A00000, 0x43AF0000\n"
        ".word 0x0049F91C, 0xE2801040, 0xE1A0200D, 0xE2800034\n"
        ".word 0xEBFFBE35, 0xE5980004, 0xE59F24B0, 0xECDD1A03\n"
        ".word 0xED900A10, 0xED901A11, 0xEDD00A12, 0xEE310AC0\n"
        ".word 0xEE321A41, 0xEE720AE0, 0xEE200A00, 0xEE010A01\n"
        ".word 0xEE000AA0, 0xEEB18AC0, 0xEE181A10, 0xE1510002\n"
        ".word 0xE2801040, 0xDA00000A, 0xED911A00, 0xEDD10A01\n"
        ".word 0xED910A02, 0xEE711A61, 0xEE301AC2, 0xEE700A62\n"
        ".word 0xEE8C0A88, 0xEE618A80, 0xEE219A00, 0xEE609A80\n"
        ".word 0xEA000010, 0xEDD11A00, 0xEDD02A0D, 0xED910A02\n"
        ".word 0xED901A0F, 0xEE711AE2, 0xEDD10A01, 0xED902A0E\n"
        ".word 0xEE300A41, 0xEE700AC2, 0xEE211AA1, 0xEE001AA0\n"
        ".word 0xEE001A00, 0xEEB12AC1, 0xEE8C1A82, 0xEE618A81\n"
        ".word 0xEE209A81, 0xEE609A01, 0xE5D012B8, 0xE3510000\n"
        ".word 0x1A000036, 0xEEB00A4A, 0xE0800104, 0xEDD00A32\n"
        ".word 0xEDD02A62, 0xED902A42, 0xEEB01A40, 0xEEF01A40\n"
        ".word 0xEB0041B0, 0xEEF01A40, 0xEEB48AC0, 0xEEF1FA10\n"
        ".word 0xDA000013, 0xE5981004, 0xEEB08A61, 0xE2810040\n"
        ".word 0xE2811034, 0xEDD00A00, 0xED900A01, 0xED901A02\n"
        ".word 0xECB13A01, 0xEC912A02, 0xEE700AC3, 0xEE300A42\n"
        ".word 0xEE311A62, 0xEE202AA0, 0xEE002A00, 0xEE012A01\n"
        ".word 0xEEF12AC2, 0xEE8C2AA2, 0xEE608A82, 0xEE209A02\n"
        ".word 0xEE619A02, 0xE59F1378, 0xEE180A10, 0xE1500001\n"
        ".word 0xAA000012, 0xE5982004, 0xEEB08A4D, 0xE2820044\n"
        ".word 0xEDD21A10, 0xEDD22A0D, 0xED921A0F, 0xED922A0E\n"
        ".word 0xEE711AE2, 0xEC900A02, 0xEE300A42, 0xEE700AC1\n"
        ".word 0xEE211AA1, 0xEE001A00, 0xEE001AA0, 0xEEB12AC1\n"
        ".word 0xEE8C1A82, 0xEE618A81, 0xEE209A01, 0xEE609A81\n"
        ".word 0xE5980004, 0xE5D010A4, 0xE3510000, 0x1A00001A\n"
        ".word 0xE5D012B8, 0xE3510000, 0x1A000017, 0xE59010A8\n"
        ".word 0xE3510000, 0xDDD00A27, 0xDEF40AC8, 0xDEF1FA10\n"
        ".word 0xCA000011, 0x2A000010, 0xED900A28, 0xED9F1AB9\n"
        ".word 0xE59F12E4, 0xEE300A01, 0xEE102A10, 0xED800A28\n"
        ".word 0xE1520001, 0xCEB00A4C, 0xED800A28, 0xEE700A80\n"
        ".word 0xEDC00A27, 0xEEB00A60, 0xEEB40AC8, 0xEEF1FA10\n"
        ".word 0xCEB00A48, 0xED800A27, 0xEA000001, 0xED808A27\n"
        ".word 0xED80AA28, 0xED900A10, 0xED901A27, 0xEE080AC1\n"
        ".word 0xED8D0A00, 0xEDD00A11, 0xEE490A41, 0xEDCD0A01\n"
        ".word 0xEDD00A12, 0xED901A27, 0xEE490AC1, 0xEDCD0A02\n"
        ".word 0xE5D010A4, 0xE3510000, 0x0A000009, 0xE2801040\n"
        ".word 0xE280C058, 0xE891000E, 0xE88C000E, 0xE89D000E\n"
        ".word 0xE58070A8, 0xE5C070A4, 0xE280004C, 0xE880000E\n"
        ".word 0xEA00011D, 0xE5901208, 0xE3710001, 0x0A00001D\n"
        ".word 0xE2801054, 0xEDD02A13, 0xED903A12, 0xEDDF0A8B\n"
        ".word 0xEE300A62, 0xECD13A02, 0xE2801040, 0xED902A14\n"
        ".word 0xECD14A02, 0xE280105C, 0xEC911A02, 0xEE744AC4\n"
        ".word 0xEE402A20, 0xEE355A41, 0xEE333A61, 0xEE044AA0\n"
        ".word 0xEE051A20, 0xEE431A20, 0xED804A16, 0xEDC02A13\n"
        ".word 0xEC811A02, 0xED9D0A01, 0xEE300A42, 0xEE002A20\n"
        ".word 0xED802A14, 0xED9D0A02, 0xEE300A63, 0xEE403A20\n"
        ".word 0xEDC03A15, 0xEA0000FC, 0xE59010AC, 0xEDDF1A70\n"
        ".word 0xE2811003, 0xE3510006, 0x379FF101, 0xEA0000F6\n"
        ".word 0x00277AC4, 0x00277AC4, 0x00277AC4, 0x002778E4\n"
        ".word 0x00277AC4, 0x00277BBC, 0xE59010A8, 0xE3510000\n"
        ".word 0xDA00003C, 0xE2411001, 0xE58010A8, 0xE5D012B8\n"
        ".word 0xE3510000, 0x0A00001B, 0xE2801040, 0xED903A16\n"
        ".word 0xEDD02A13, 0xEDD00A14, 0xED902A15, 0xEE305A62\n"
        ".word 0xECD13A03, 0xE280105C, 0xEC911A02, 0xEE733AC3\n"
        ".word 0xEE344A41, 0xEE744AE1, 0xEE752A22, 0xEE330A83\n"
        ".word 0xEE341A01, 0xEE741AA1, 0xED800A16, 0xEDC02A13\n"
        ".word 0xEC811A02, 0xED9D0A01, 0xEE300A60, 0xEE300A20\n"
        ".word 0xED800A14, 0xED9D0A02, 0xE58070A8, 0xEE300A42\n"
        ".word 0xEE300A02, 0xEA000072, 0xE2801058, 0xEDD00A18\n"
        ".word 0xED903A13, 0xEDD02A14, 0xED902A15, 0xEE300A43\n"
        ".word 0xEC911A02, 0xE2801040, 0xECD13A03, 0xE2801058\n"
        ".word 0xEE733AC1, 0xEE744AE0, 0xEE344A61, 0xEE003A0B\n"
        ".word 0xEE031A8B, 0xEE440A8B, 0xEE441A0B, 0xEDC00A18\n"
        ".word 0xED803A13, 0xEC811A02, 0xED9D0A01, 0xEE300A62\n"
        ".word 0xEE402A0B, 0xEDC02A14, 0xED9D0A02, 0xEE300A42\n"
        ".word 0xEE002A0B, 0xEA000035, 0xED902A10, 0xEDD00A16\n"
        ".word 0xED9F1A24, 0xEE322A60, 0xEE720A20, 0xEDC00A16\n"
        ".word 0xED902A11, 0xEDD00A17, 0xEE322A60, 0xEE720A20\n"
        ".word 0xEDC00A17, 0xED902A12, 0xEDD00A18, 0xEE322A60\n"
        ".word 0xEE720A20, 0xEDC00A18, 0xE5D012B8, 0xE3510000\n"
        ".word 0x0A000015, 0xE280104C, 0xEDD00A15, 0xECD11A02\n"
        ".word 0xEE300A61, 0xEE401A01, 0xEDC01A13, 0xED9D0A01\n"
        ".word 0xEE300A42, 0xEE002A01, 0xED802A14, 0xED9D0A02\n"
        ".word 0xEE300A60, 0xEE400A01, 0xEDC00A15, 0xEA00008E\n"
        ".word 0x38D1B717, 0x42340000, 0x41000000, 0x42200000\n"
        ".word 0x3E000000, 0x3EAAAAAB, 0x3F2AAAAB, 0xEDD00A13\n"
        ".word 0xEDD02A14, 0xED902A15, 0xEE300A60, 0xEE400A01\n"
        ".word 0xEDC00A13, 0xED9D0A01, 0xEE300A62, 0xEE402A21\n"
        ".word 0xEDC02A14, 0xED9D0A02, 0xEE300A42, 0xEE002A01\n"
        ".word 0xED802A15, 0xEA000078, 0xE5D012B8, 0xE3510000\n"
        ".word 0x0A00001D, 0xEDD03A10, 0xED903A16, 0xEDD04A11\n"
        ".word 0xED901A17, 0xED904A12, 0xED902A18, 0xEDD01A13\n"
        ".word 0xEE733AC3, 0xEE744AC1, 0xEE344A42, 0xEE300A61\n"
        ".word 0xEDD02A14, 0xEDD00A15, 0xEE333A83, 0xEE341A81\n"
        ".word 0xEE342A02, 0xEE300A21, 0xED803A16, 0xED801A17\n"
        ".word 0xED802A18, 0xED800A13, 0xED9D0A01, 0xEE300A62\n"
        ".word 0xEE300A22, 0xED800A14, 0xED9D0A02, 0xEE300A60\n"
        ".word 0xEE300A20, 0xED800A15, 0xEA000057, 0xE2801040\n"
        ".word 0xED903A16, 0xED902A17, 0xEDD00A18, 0xEDD03A13\n"
        ".word 0xEDD02A14, 0xED901A15, 0xEE300A63, 0xEC914A03\n"
        ".word 0xEE344A43, 0xEE744AC2, 0xEE355A60, 0xEE403A21\n"
        ".word 0xEE043A0B, 0xEE042A8B, 0xEE450A0B, 0xED803A16\n"
        ".word 0xED802A17, 0xEDC00A18, 0xEDC03A13, 0xED9D0A01\n"
        ".word 0xEE300A62, 0xEE402A21, 0xEDC02A14, 0xED9D0A02\n"
        ".word 0xEE300A41, 0xEE001A21, 0xED801A15, 0xEA00003A\n"
        ".word 0xE5D012B8, 0xE3510000, 0x0A00001B, 0xE2801054\n"
        ".word 0xED901A18, 0xEDD01A13, 0xEDD00A14, 0xEC912A03\n"
        ".word 0xE2801040, 0xEE300A61, 0xECD13A03, 0xE2801058\n"
        ".word 0xEE733AE2, 0xEE744AC1, 0xEE344A43, 0xEE300A21\n"
        ".word 0xEE732AA2, 0xEE341A81, 0xEE343A03, 0xED801A18\n"
        ".word 0xED800A13, 0xECC12A02, 0xED9D0A01, 0xEE300A60\n"
        ".word 0xEE300A20, 0xED800A14, 0xED9D0A02, 0xEE300A42\n"
        ".word 0xEE300A02, 0xED800A15, 0xEA00001B, 0xE2801040\n"
        ".word 0xEDD00A16, 0xEDD02A17, 0xEDD01A18, 0xED903A13\n"
        ".word 0xED901A14, 0xED902A15, 0xEE300A43, 0xECD13A03\n"
        ".word 0xEE733AE0, 0xEE344A62, 0xEE744AE1, 0xEE003A0B\n"
        ".word 0xEE430A8B, 0xEE442A0B, 0xEE441A8B, 0xEDC00A16\n"
        ".word 0xEDC02A17, 0xEDC01A18, 0xED803A13, 0xED9D0A01\n"
        ".word 0xEE300A41, 0xEE001A0B, 0xED801A14, 0xED9D0A02\n"
        ".word 0xEE300A42, 0xEE002A0B, 0xED802A15, 0xE51F0CA0\n"
        ".word 0xEB0084CE, 0xEEF00A4A, 0xE5980004, 0xE5951000\n"
        ".word 0xEDD01A13, 0xEEB02A60, 0xED910A07, 0xED911A09\n"
        ".word 0xEDD02A15, 0xEB00401F, 0xEE100A10, 0xE1500009\n"
        ".word 0xAA00000A, 0xEE300A4C, 0xEE100A10, 0xE1500006\n"
        ".word 0xE5980004, 0xBEB00A6B, 0xEDD00A26, 0xE51F0CF0\n"
        ".word 0xEB01269C, 0xE320F000, 0xE320F000, 0xEA000004\n"
        ".word 0xE5980004, 0xEEB00A6E, 0xEDD00A26, 0xE51F0D10\n"
        ".word 0xEB012694, 0xE5980004, 0xEEF01A6D, 0xEEB01A4E\n"
        ".word 0xE0800104, 0xE3A01001, 0xED900A72, 0xE51F0D30\n"
        ".word 0xEDDF0A21, 0xEB0128AD, 0xE5980004, 0xE5901000\n"
        ".word 0xE3510007, 0x13510008, 0x13510009, 0x0A000012\n"
        ".word 0xE280004C, 0xEC900A06, 0xEBFF91C1, 0xE5980004\n"
        ".word 0xED900A13, 0xEDD01A16, 0xEDD00A15, 0xED901A18\n"
        ".word 0xEE300A61, 0xEE700AC1, 0xEB0028C6, 0xE5980004\n"
        ".word 0xEE601A2A, 0xE280004C, 0xEC900A03, 0xEBFF91CC\n"
        ".word 0xE28DD054, 0xECBD8B0E, 0xE8BD83F0, 0xE2803028\n"
        ".word 0xE2802058, 0xE280104C, 0xE51F0DAC, 0xEB0128BA\n"
        ".word 0xE320F000, 0xE320F000, 0xEAFFFFE7, 0x41200000\n"
    );
}

} // namespace smt4::script
