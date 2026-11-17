#include "ui/window.h"
#include "engine/asd_symbols.h"
#include <cstring>

namespace smt4::ui {

// 0x002C32F8 copies its ten trailing arguments verbatim; table pointers are
// passed as their 32-bit address words.
static inline u32 SpriteTableWord(const void* pointer) {
    return static_cast<u32>(reinterpret_cast<std::uintptr_t>(pointer));
}

ComWinWork* g_ComWinWork = nullptr; // 0x0043E0F8

// External engine and UI helpers referenced by ComWin
extern "C" {
    void* AsdMem_Alloc(u32 align, u32 line, u32 zero_flag, u32 size, u32 flag);     // 0x002c4b84
    void* engine_func_002c2be8(const f32* values);                                  // 0x002c2be8
    s32   script_vm_func_0025a274(s32 value);                                       // 0x0025a274
    s32   ui_func_002d569c(s32 value);                                              // 0x002d569c
    s32   ui_func_002d56fc(s32 value);                                              // 0x002d56fc
    void  func_0011b558(void* value);                                               // 0x0011b558
    void  engine_func_0011b5e8(void* value);                                       // 0x0011b5e8
    void  AsdMem_Zero(void* ptr, u32 size);                                         // 0x002c4b30
    void  AsdMem_Copy(void* dst, const void* src, u32 size);                        // 0x002c5ff4
    u32   battle_func_002bf148(u32 value);                                           // 0x002bf148
    void  engine_func_002c25f4(u32 value);                                          // 0x002c25f4
    void* AsdTask_CreateCalc(const char* name, u32 prio, u32 a2, u32 a3,
                             void (*cb)(void*), u32 a5, u32 a6);                    // 0x002c5978
    void* AsdTask_CreateDraw(const char* name, u32 prio, u32 a2, u32 a3,
                             void (*cb)(void*), u32 a5, u32 a6, void* parent);      // 0x002c4c00
    // UiSpriteGroup_Init / UiSpriteGroup_BindTable are declared canonically in
    // engine/asd_symbols.h (0x002C3344 / 0x002C32F8).
    void  UiAnimSprite_Setup(UiAnimSprite* sprite, s32 type, s32 id,
                             UiSpriteGroup* group, u32 flag, f32 scale);            // 0x002bf0a8
    void  UiAnimSprite_SetAnim(UiAnimSprite* sprite, s32 anim, s32 frame);          // 0x002bf030
    void  UiGpu_BeginPass(void* gpu_state);                                         // 0x002c3ba8
    void* UiGpu_SetViewportParams(s32 a0, s32 a1);                                 // 0x002c5f7c
    void  UiGpu_SetAlphaBlend(f32 alpha);                                           // 0x002bf710
    f32   UiGpu_TransformCoord(void* gpu_state, f32 scale);                         // 0x002ba46c
    void  UiSprite_DrawPanelDirect(s32 type, s32 id, s32 sub_id, s32 x, s32 y, s32 flag); // 0x002bf460
    void  UiWindow_PushContext(void* ptr, s32 mode);                                // 0x002befdc
    void  UiWindow_PopContext(void* ptr, s32 mode);                                 // 0x002bef88
    void  UiWindow_SetResult(const s32* value);                                     // 0x002c4244
    void  func_00115b74();                                                          // 0x00115b74
    void* engine_func_002c54f0(u32 a0, u32 a1, u32 a2, u32 a3, u32 a4);        // 0x002c54f0
    u32   engine_func_002bdc08(void* voice, u32 release);                       // 0x002bdc08
    void  engine_func_002bdbcc(void* ptr);                                      // 0x002bdbcc
    u32   camp_func_002bf030(void* object, u32 selector);                       // 0x002bf030
    void* AsdText_CreateDefault(s32 a0);                                            // 0x002bda1c
    void  AsdText_SetAlpha(void* handle, u32 alpha);                                // 0x002bda10
    void  AsdText_SetColorAndScale(void* handle, s32 a0, u32 color, f32 scale);    // 0x002bda00
    void  UiAnimSprite_SetupEx(UiAnimSprite* sprite, s32 type, s32 id, s32 a3,
                               UiSpriteGroup* group, u32 flag, f32 scale);          // 0x002bdb2c
    void  UiAnimSprite_SetMode(UiAnimSprite* sprite, s32 m0, s32 m1);               // 0x002bdac0
    extern u8* g_AsdGpuState;                                                       // 0x0044ea00
    extern u8  g_ComWinSpriteTable[];                                               // 0x004038F0
    extern u8  g_InfoWinSpriteTable[];                                              // 0x00403AA8
    extern u8  g_GuestWinSpriteTable[];                                             // 0x00403A38
    void* UiEngine_GetContext();                                                    // 0x002c2b1c
    void* ui_func_002c0ac8();                                                       // 0x002c0ac8
    u32   func_002c00e8(u32);                                                       // 0x002c00e8
    u32   func_002bfcb4(u32, void*);                                                // 0x002bfcb4
    void  func_002bfc88(void*, void*);                                              // 0x002bfc88
    void* battle_func_002b6e60();                                                   // 0x002b6e60
    u32   ui_func_002bf9f0(void*);                                                  // 0x002bf9f0
}

// Forward declaration for task callback
void ComWin_Calc(void* arg);                                                        // 0x0011b094

// DECOMP_FUNC(0x0010a70c, 60)
bool ComWin_SetState() {
    auto* const state_block = reinterpret_cast<u32*>(0x004E3CD4);
    for (s32 i = 0; i < 6; ++i) {
        state_block[i] = 0;
    }
    state_block[6] = 0x0F;
    state_block[7] = 4;
    return true;
}

extern "C" {
    extern const u8 g_ComWinSpriteTable_00403890;                                          // 0x00403890
    extern const u8 g_ComWinSpriteTable_004038c0;                                          // 0x004038c0
}

// DECOMP_FUNC(0x0010a748, 504)
void ComWin_Init() {
    static constexpr u32 kWorkSize = 0x188;
    static constexpr u32 kCalcTag = 1;
    static constexpr u32 kDrawUpLeftTag = 0x81;
    static constexpr u32 kDrawUpRightTag = 0xDF;
    static constexpr s32 kSpriteType = 0x0E;

    u8* work = reinterpret_cast<u8*>(g_ComWinWork);
    if (work == nullptr) {
        work = static_cast<u8*>(AsdMem_Alloc(0x100, 0x100, 0, kWorkSize, 1));
        g_ComWinWork = reinterpret_cast<ComWinWork*>(work);
    }

    AsdMem_Zero(work, kWorkSize);

    void* const calc_task = AsdTask_CreateCalc(
        "ComWin Calc",
        kCalcTag,
        0,
        0,
        ComWin_Calc,
        0,
        0);
    *reinterpret_cast<void**>(work) = calc_task;

    AsdTask_CreateDraw(
        "ComWin DrawUpLeft",
        kDrawUpLeftTag,
        0,
        0,
        ComWin_DrawUp,
        0,
        0,
        calc_task);

    AsdTask_CreateDraw(
        "ComWin DrawUpRight",
        kDrawUpRightTag,
        0,
        0,
        ComWin_DrawUp,
        0,
        0,
        calc_task);

    u8* const bound_work = reinterpret_cast<u8*>(g_ComWinWork);
    UiSpriteGroup* const sprite_group = reinterpret_cast<UiSpriteGroup*>(bound_work + 0x1C);
    UiAnimSprite* const panel_sprite = reinterpret_cast<UiAnimSprite*>(bound_work + 0x3C);
    UiAnimSprite* const cursor_sprite = reinterpret_cast<UiAnimSprite*>(bound_work + 0xC8);

    UiSpriteGroup_Init(sprite_group);
    UiSpriteGroup_BindTable(
        sprite_group,
        0,
        0,
        SpriteTableWord(&g_ComWinSpriteTable_00403890),
        0x30,
        SpriteTableWord(&g_ComWinSpriteTable_004038c0),
        0x30,
        0,
        0,
        SpriteTableWord(g_ComWinSpriteTable),
        0x118);

    using ComWinSetup = void (*)(UiAnimSprite*, s32, s32, s32, UiSpriteGroup*, u32, f32);
    using ComWinSetAnim = void (*)(UiAnimSprite*, s32);

    reinterpret_cast<ComWinSetup>(UiAnimSprite_Setup)(
        panel_sprite,
        kSpriteType,
        -1,
        2,
        sprite_group,
        1,
        1.0f);
    reinterpret_cast<ComWinSetAnim>(UiAnimSprite_SetAnim)(panel_sprite, 0);

    reinterpret_cast<ComWinSetup>(UiAnimSprite_Setup)(
        cursor_sprite,
        kSpriteType,
        -1,
        3,
        sprite_group,
        1,
        1.0f);
    reinterpret_cast<ComWinSetAnim>(UiAnimSprite_SetAnim)(cursor_sprite, 2);
}
#if 0
// Partial semantic draft retained for reconstruction; not compiled.
[[maybe_unused]] static void ComWin_Init_Draft() {
    ComWinWork* work = g_ComWinWork;
    if (work == nullptr) {
        work = static_cast<ComWinWork*>(
            AsdMem_Alloc(0x100, 0x122, 0, sizeof(ComWinWork), 1));
        g_ComWinWork = work;
    }

    AsdMem_Zero(work, sizeof(ComWinWork));

    work->calc_task = AsdTask_CreateCalc("ComWin Calc", 1, 0, 0,
                                         ComWin_Calc, 0, 0);
    work->draw_up_left = AsdTask_CreateDraw("ComWin DrawUpLeft", 0x81, 0, 0,
                                            ComWin_DrawUp, 0, 0, work->calc_task);
    work->draw_up_right = AsdTask_CreateDraw("ComWin DrawUpRight", 0xDF, 0, 0,
                                             ComWin_DrawUp, 0, 0, work->calc_task);

    UiSpriteGroup_Init(&work->sprite_group);
    UiSpriteGroup_BindTable(&work->sprite_group,
                            0, 0,
                            SpriteTableWord(g_ComWinSpriteTable - 0x60), 0x30,
                            SpriteTableWord(g_ComWinSpriteTable - 0x30),
                            0x30, 0, 0,
                            SpriteTableWord(g_ComWinSpriteTable), 0x118);

    UiAnimSprite_Setup(&work->panel_sprites[0], 0x0E, -1, &work->sprite_group, 1, 1.0f);
    UiAnimSprite_SetAnim(&work->panel_sprites[0], 0, 0);

    UiAnimSprite_Setup(&work->panel_sprites[1], 0x0E, -1, &work->sprite_group, 1, 1.0f);
    UiAnimSprite_SetAnim(&work->panel_sprites[1], 2, 0);
}
#endif

// DECOMP_FUNC(0x0010a940, 20)
void* ComWin_GetState(u32 a0, u32 a1, u32 a2, u32 a3) {
    return engine_func_002c54f0(a0, a1, a2, a3, 1);
}

// DECOMP_FUNC(0x0010a954, 1352)
// Boundary-verified ARM-state span; includes its PC-relative literal pool.
__attribute__((naked)) void ComWin_ProcessDialog() {
    asm volatile(
        ".word 0xe92d4ff0\n"
        ".word 0xe59fa3cc\n"
        ".word 0xed2d8b02\n"
        ".word 0xe24dd054\n"
        ".word 0xe59a4008\n"
        ".word 0xe5d40083\n"
        ".word 0xe3500000\n"
        ".word 0x1a000143\n"
        ".word 0xe5d40009\n"
        ".word 0xe59f83b4\n"
        ".word 0xed9f8aeb\n"
        ".word 0xe350000b\n"
        ".word 0xe3a05006\n"
        ".word 0xe3a07000\n"
        ".word 0x0a000002\n"
        ".word 0xe3500013\n"
        ".word 0x0a00001f\n"
        ".word 0xea00003f\n"
        ".word 0xe5d40008\n"
        ".word 0xe3500000\n"
        ".word 0x0a000037\n"
        ".word 0xe28400c4\n"
        ".word 0xed900a08\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb06d354\n"
        ".word 0xe3a01000\n"
        ".word 0xe3a00001\n"
        ".word 0xeb06ed6c\n"
        ".word 0xe1a02000\n"
        ".word 0xe5980000\n"
        ".word 0xe3a01003\n"
        ".word 0xeb06d180\n"
        ".word 0xe59f2358\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a0100e\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d5004\n"
        ".word 0xe58d7000\n"
        ".word 0xeb06d29a\n"
        ".word 0xe5980000\n"
        ".word 0xe3a01003\n"
        ".word 0xeb06d161\n"
        ".word 0xeeb00a48\n"
        ".word 0xe320f000\n"
        ".word 0xeb06d340\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea00001b\n"
        ".word 0xe5d40008\n"
        ".word 0xe3500000\n"
        ".word 0x0a000018\n"
        ".word 0xe28400c4\n"
        ".word 0xed900a08\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb06d335\n"
        ".word 0xe3a01000\n"
        ".word 0xe3a00001\n"
        ".word 0xeb06ed4d\n"
        ".word 0xe1a02000\n"
        ".word 0xe5980000\n"
        ".word 0xe3a01003\n"
        ".word 0xeb06d161\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a0208d\n"
        ".word 0xe3a0103a\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d5004\n"
        ".word 0xe58d7000\n"
        ".word 0xeb06d27b\n"
        ".word 0xe5980000\n"
        ".word 0xe3a01003\n"
        ".word 0xeb06d142\n"
        ".word 0xeeb00a48\n"
        ".word 0xe320f000\n"
        ".word 0xeb06d321\n"
        ".word 0xe1a00004\n"
        ".word 0xeb006d89\n"
        ".word 0xe59a0008\n"
        ".word 0xe320f000\n"
        ".word 0xeb00378c\n"
        ".word 0xe59a0008\n"
        ".word 0xe5d0107d\n"
        ".word 0xe3510000\n"
        ".word 0x0a000003\n"
        ".word 0xe5d0007f\n"
        ".word 0xe3500000\n"
        ".word 0x03a00000\n"
        ".word 0x0b006862\n"
        ".word 0xe59a0008\n"
        ".word 0xe3a0b00b\n"
        ".word 0xe3a09010\n"
        ".word 0xe5d0107e\n"
        ".word 0xe3510000\n"
        ".word 0x0a000083\n"
        ".word 0xe2800b01\n"
        ".word 0xe2800fd5\n"
        ".word 0xeb06d126\n"
        ".word 0xe1a05000\n"
        ".word 0xe59a0008\n"
        ".word 0xe2800b01\n"
        ".word 0xe2800fd5\n"
        ".word 0xeb06d11e\n"
        ".word 0xe1a06000\n"
        ".word 0xe3a01000\n"
        ".word 0xe3a00001\n"
        ".word 0xeb06ed1d\n"
        ".word 0xe1a02000\n"
        ".word 0xe5980000\n"
        ".word 0xe3a01003\n"
        ".word 0xeb06d131\n"
        ".word 0xeeb00a48\n"
        ".word 0xe320f000\n"
        ".word 0xeb06d2fb\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb06d0f9\n"
        ".word 0xe3a010c8\n"
        ".word 0xe3a0000e\n"
        ".word 0xeb06d2e5\n"
        ".word 0xe1d010fa\n"
        ".word 0xe1a04000\n"
        ".word 0xe3a0200a\n"
        ".word 0xe0810006\n"
        ".word 0xe88d0801\n"
        ".word 0xe1d400f8\n"
        ".word 0xe3a0100e\n"
        ".word 0xe0803005\n"
        ".word 0xe3a00002\n"
        ".word 0xeb06d27d\n"
        ".word 0xe59a0008\n"
        ".word 0xe3a01000\n"
        ".word 0xe5900068\n"
        ".word 0xeb06cf2d\n"
        ".word 0xe1a02000\n"
        ".word 0xe28f1d07\n"
        ".word 0xe28d0010\n"
        ".word 0xfa06cf1e\n"
        ".word 0xe3a010c2\n"
        ".word 0xe3a0000e\n"
        ".word 0xeb06d2d0\n"
        ".word 0xe1d030fa\n"
        ".word 0xe1d420fa\n"
        ".word 0xe1d4c0f8\n"
        ".word 0xe1d000f8\n"
        ".word 0xe0821003\n"
        ".word 0xe0811006\n"
        ".word 0xe080000c\n"
        ".word 0xe0800005\n"
        ".word 0xee001a90\n"
        ".word 0xee000a10\n"
        ".word 0xed9f1a61\n"
        ".word 0xeeb02a48\n"
        ".word 0xe28d2010\n"
        ".word 0xeef01a41\n"
        ".word 0xeef80ae0\n"
        ".word 0xeeb80ac0\n"
        ".word 0xe3a010ff\n"
        ".word 0xe3a00002\n"
        ".word 0xeb06cee8\n"
        ".word 0xe3a010c1\n"
        ".word 0xe3a0000e\n"
        ".word 0xeb06d2ba\n"
        ".word 0xe58d7000\n"
        ".word 0xe59ac008\n"
        ".word 0xe1d420fa\n"
        ".word 0xe1d030fa\n"
        ".word 0xe1d470f8\n"
        ".word 0xe1d000f8\n"
        ".word 0xe59c1068\n"
        ".word 0xe0822003\n"
        ".word 0xe0873000\n"
        ".word 0xe0822006\n"
        ".word 0xe6bf0071\n"
        ".word 0xe0831005\n"
        ".word 0xe3a03010\n"
        ".word 0xeb06ce4a\n"
        ".word 0xe3a000ff\n"
        ".word 0xe320f000\n"
        ".word 0xeb06ce2c\n"
        ".word 0xe3a010c6\n"
        ".word 0xe3a0000e\n"
        ".word 0xeb06d2a6\n"
        ".word 0xe1a01000\n"
        ".word 0xe59a0008\n"
        ".word 0xe28f2c01\n"
        ".word 0xe3a03004\n"
        ".word 0xe590006c\n"
        ".word 0xe58d2008\n"
        ".word 0xe58d000c\n"
        ".word 0xe88d0208\n"
        ".word 0xe1d120fa\n"
        ".word 0xe1d400fa\n"
        ".word 0xe1d430f8\n"
        ".word 0xe1d110f8\n"
        ".word 0xe0822000\n"
        ".word 0xe0822006\n"
        ".word 0xe0811003\n"
        ".word 0xe0811005\n"
        ".word 0xe3a03001\n"
        ".word 0xe3a00000\n"
        ".word 0xeb06cd3a\n"
        ".word 0xe3a010c7\n"
        ".word 0xe3a0000e\n"
        ".word 0xeb06d290\n"
        ".word 0xe1a01000\n"
        ".word 0xe28f00b0\n"
        ".word 0xe3a02001\n"
        ".word 0xe58d0008\n"
        ".word 0xe88d0204\n"
        ".word 0xe1d100fa\n"
        ".word 0xe1d430f8\n"
        ".word 0xe1d110f8\n"
        ".word 0xe1d420fa\n"
        ".word 0xe0811003\n"
        ".word 0xe0822000\n"
        ".word 0xe3a03000\n"
        ".word 0xe0822006\n"
        ".word 0xe0811005\n"
        ".word 0xe1a00003\n"
        ".word 0xeb06cd27\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb06d08e\n"
        ".word 0xe5980000\n"
        ".word 0xe3a01003\n"
        ".word 0xeb06d0a8\n"
        ".word 0xe59a5008\n"
        ".word 0xe595008c\n"
        ".word 0xe3500000\n"
        ".word 0x0a000063\n"
        ".word 0xe2850b02\n"
        ".word 0xe2800f61\n"
        ".word 0xe1a04000\n"
        ".word 0xeb06d09d\n"
        ".word 0xe1a06000\n"
        ".word 0xe1a00004\n"
        ".word 0xeb06d097\n"
        ".word 0xe1a07000\n"
        ".word 0xe3a01000\n"
        ".word 0xe3a00001\n"
        ".word 0xeb06ec96\n"
        ".word 0xe1a02000\n"
        ".word 0xe3a01003\n"
        ".word 0xea000007\n"
        ".word 0x0043e188\n"
        ".word 0x3f800000\n"
        ".word 0x0044ea00\n"
        ".word 0x00000101\n"
        ".word 0x00007325\n"
        ".word 0x00000000\n"
        ".word 0x00006425\n"
        ".word 0x0000002a\n"
        ".word 0xe5980000\n"
        ".word 0xeb06d0a1\n"
        ".word 0xeeb00a48\n"
        ".word 0xe320f000\n"
        ".word 0xeb06d26b\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb06d069\n"
        ".word 0xe3a010c0\n"
        ".word 0xe3a0000e\n"
        ".word 0xeb06d255\n"
        ".word 0xe1a04000\n"
        ".word 0xe1d000fa\n"
        ".word 0xe3a02011\n"
        ".word 0xe3a0100e\n"
        ".word 0xe0800007\n"
        ".word 0xe88d0801\n"
        ".word 0xe1d400f8\n"
        ".word 0xe0803006\n"
        ".word 0xe3a00002\n"
        ".word 0xeb06d1ed\n"
        ".word 0xe1d400fa\n"
        ".word 0xe1d410f8\n"
        ".word 0xe1d5c9b0\n"
        ".word 0xe0802007\n"
        ".word 0xe0811006\n"
        ".word 0xe3a03000\n"
        ".word 0xe1a0000c\n"
        ".word 0xeb06cc3d\n"
        ".word 0xe59f10cc\n"
        ".word 0xe59fc0cc\n"
        ".word 0xe1d539b0\n"
        ".word 0xe3e02000\n"
        ".word 0xe3a00000\n"
        ".word 0xe1510003\n"
        ".word 0xe0c1519c\n"
        ".word 0xd3520000\n"
        ".word 0xb1a02000\n"
        ".word 0xe2800001\n"
        ".word 0xe1a05141\n"
        ".word 0xe0451fc1\n"
        ".word 0xe3510000\n"
        ".word 0xcafffff6\n"
        ".word 0xe3520000\n"
        ".word 0xba000005\n"
        ".word 0xe2621065\n"
        ".word 0xe3a0000e\n"
        ".word 0xeb06d230\n"
        ".word 0xe1a05000\n"
        ".word 0xe320f000\n"
        ".word 0xea000003\n"
        ".word 0xe3a0105d\n"
        ".word 0xe3a0000e\n"
        ".word 0xeb06d22a\n"
        ".word 0xe1a05000\n"
        ".word 0xe3a000ff\n"
        ".word 0xeb06cdaa\n"
        ".word 0xe24f00f0\n"
        ".word 0xe3a0100f\n"
        ".word 0xe58d0008\n"
        ".word 0xe88d0202\n"
        ".word 0xe1d400fa\n"
        ".word 0xe1d510fa\n"
        ".word 0xe1d420f8\n"
        ".word 0xe1d530f8\n"
        ".word 0xe0811000\n"
        ".word 0xe0820003\n"
        ".word 0xe0812007\n"
        ".word 0xe0801006\n"
        ".word 0xe3a03000\n"
        ".word 0xe1a00003\n"
        ".word 0xeb06ccbf\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb06d026\n"
        ".word 0xe5980000\n"
        ".word 0xe3a01003\n"
        ".word 0xeb06d040\n"
        ".word 0xe28dd054\n"
        ".word 0xe3a00000\n"
        ".word 0xecbd8b02\n"
        ".word 0xe8bd8ff0\n"
        ".word 0x05f5e100\n"
        ".word 0x66666667\n"
    );
}
#if 0
// Partial semantic draft retained for reconstruction; not compiled.
[[maybe_unused]] static void ComWin_ProcessDialog_Draft() {
    auto* ctx = *reinterpret_cast<u8**>(0x0043E188 + 8);
    if (ctx == nullptr || ctx[0x83] != 0) {
        return;
    }

    const u8 type = ctx[9];
    if (type == 0x0B) {
        if (ctx[8] != 0) {
            const f32 alpha = *reinterpret_cast<const f32*>(&ctx[0xC4 + 0x20]);
            UiGpu_SetAlphaBlend(alpha);
            UiGpu_SetViewportParams(1, 0);
            UiWindow_PushContext(g_AsdGpuState, 3);
            UiSprite_DrawPanelDirect(2, 0x0E, 0x101, 0, 6, 0);
            UiWindow_PopContext(g_AsdGpuState, 3);
            UiGpu_SetAlphaBlend(1.0f);
        }
    } else if (type == 0x13) {
        // Mode 0x13 dialog processing
        UiGpu_SetAlphaBlend(1.0f);
        UiSprite_DrawPanelDirect(2, 0x0E, 0x102, 0, 6, 0);
    }
}
#endif

// DECOMP_FUNC(0x0010ae9c, 44)
void ComWin_CheckFlag() {
    const u32 flag = *reinterpret_cast<const u32*>(0x00465058) ^ 1;
    const u32 selected = reinterpret_cast<const u32*>(0x00465064)[flag];
    engine_func_002c25f4(battle_func_002bf148(selected));
}

// DECOMP_FUNC(0x0010aec8, 12)
void ComWin_GetResult() {
    UiWindow_SetResult(reinterpret_cast<const s32*>(0x00465024));
}

// DECOMP_FUNC(0x0010aed4, 16)
s32 func_0010aed4() {
    func_00115b74();
    return 0;
}

// DECOMP_FUNC(0x0010aee4, 84)
void ComWin_Reset() {
    auto* const context = *reinterpret_cast<u8**>(0x004E2F68 + 0x204);
    if (context == nullptr) {
        return;
    }
    for (u32 i = 0; i < 8; ++i) {
        auto* const slot = context + (i << 2);
        void* const entry = *reinterpret_cast<void**>(slot + 0x20);
        if (entry != nullptr) {
            engine_func_002bdc08(entry, 0);
            engine_func_002bdbcc(slot + 0x20);
        }
    }
}

// DECOMP_FUNC(0x0011a354, 1632)
// Boundary-verified ARM-state span; includes its PC-relative literal pool.
__attribute__((naked)) void ComWin_DrawUp(void* arg) {
    asm volatile(
        ".word 0xe92d43f0\n"
        ".word 0xe59f0418\n"
        ".word 0xed2d8b04\n"
        ".word 0xe24dd08c\n"
        ".word 0xe5904000\n"
        ".word 0xe5940008\n"
        ".word 0xe3500000\n"
        ".word 0x0a00018a\n"
        ".word 0xe59f8400\n"
        ".word 0xe5980000\n"
        ".word 0xeb06a609\n"
        ".word 0xe5985000\n"
        ".word 0xe3a01000\n"
        ".word 0xe3a00001\n"
        ".word 0xeb06aefa\n"
        ".word 0xe2855a01\n"
        ".word 0xe2855f93\n"
        ".word 0xe3a07000\n"
        ".word 0xe5951000\n"
        ".word 0xe2812001\n"
        ".word 0xe0853101\n"
        ".word 0xe5931008\n"
        ".word 0xe0853102\n"
        ".word 0xe5852000\n"
        ".word 0xe5830008\n"
        ".word 0xe5d52018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000002\n"
        ".word 0xe595101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe5c57018\n"
        ".word 0xe5980000\n"
        ".word 0xed9f0ae8\n"
        ".word 0xeb068022\n"
        ".word 0xeebd0ac0\n"
        ".word 0xe284003c\n"
        ".word 0xee105a10\n"
        ".word 0xed900a08\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb0694c4\n"
        ".word 0xe59f9380\n"
        ".word 0xed949a18\n"
        ".word 0xeddf8adf\n"
        ".word 0xed9f8adf\n"
        ".word 0xe5990000\n"
        ".word 0xe3100001\n"
        ".word 0x1a000017\n"
        ".word 0xe2890000\n"
        ".word 0xfa06972c\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000012\n"
        ".word 0xe59f035c\n"
        ".word 0xe2801010\n"
        ".word 0xedc08a00\n"
        ".word 0xed808a01\n"
        ".word 0xed808a02\n"
        ".word 0xed808a03\n"
        ".word 0xec818a02\n"
        ".word 0xe2801024\n"
        ".word 0xed808a06\n"
        ".word 0xed808a07\n"
        ".word 0xed808a08\n"
        ".word 0xec818a02\n"
        ".word 0xed808a0b\n"
        ".word 0xed808a0c\n"
        ".word 0xed808a0d\n"
        ".word 0xe2800038\n"
        ".word 0xec808a02\n"
        ".word 0xe2890000\n"
        ".word 0xe1a00000\n"
        ".word 0xe59f1310\n"
        ".word 0xe28d0048\n"
        ".word 0xeb0696de\n"
        ".word 0xe5990000\n"
        ".word 0xe3100001\n"
        ".word 0x1a000017\n"
        ".word 0xe59f02ec\n"
        ".word 0xfa06970e\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000012\n"
        ".word 0xe59f02e4\n"
        ".word 0xe2801010\n"
        ".word 0xedc08a00\n"
        ".word 0xed808a01\n"
        ".word 0xed808a02\n"
        ".word 0xed808a03\n"
        ".word 0xec818a02\n"
        ".word 0xe2801024\n"
        ".word 0xed808a06\n"
        ".word 0xed808a07\n"
        ".word 0xed808a08\n"
        ".word 0xec818a02\n"
        ".word 0xed808a0b\n"
        ".word 0xed808a0c\n"
        ".word 0xed808a0d\n"
        ".word 0xe2800038\n"
        ".word 0xec808a02\n"
        ".word 0xe59f0294\n"
        ".word 0xe1a00000\n"
        ".word 0xe59f1298\n"
        ".word 0xe28d0008\n"
        ".word 0xeb0696c0\n"
        ".word 0xe5d40012\n"
        ".word 0xe3500000\n"
        ".word 0x1a000003\n"
        ".word 0xe3a010dc\n"
        ".word 0xe3a0000e\n"
        ".word 0xeb06946e\n"
        ".word 0xe1a06000\n"
        ".word 0xe5d40012\n"
        ".word 0xe3500001\n"
        ".word 0x1a000003\n"
        ".word 0xe3a010dd\n"
        ".word 0xe3a0000e\n"
        ".word 0xeb069467\n"
        ".word 0xe1a06000\n"
        ".word 0xe596100c\n"
        ".word 0xe1d630fa\n"
        ".word 0xe1d620f8\n"
        ".word 0xe1d100f0\n"
        ".word 0xe1d110f2\n"
        ".word 0xe0800fa0\n"
        ".word 0xe0811fa1\n"
        ".word 0xe085c0c0\n"
        ".word 0xe08300c1\n"
        ".word 0xe082100c\n"
        ".word 0xee001a10\n"
        ".word 0xee000a90\n"
        ".word 0xe3a00000\n"
        ".word 0xe3a015fe\n"
        ".word 0xe58d000c\n"
        ".word 0xe58d1008\n"
        ".word 0xeeb80ac0\n"
        ".word 0xeef80ae0\n"
        ".word 0xe58d0010\n"
        ".word 0xe28d2008\n"
        ".word 0xed8d0a05\n"
        ".word 0xe1cd01f8\n"
        ".word 0xe58d0020\n"
        ".word 0xedcd0a09\n"
        ".word 0xe58d0028\n"
        ".word 0xe1cd02fc\n"
        ".word 0xed8d8a0d\n"
        ".word 0xe1cd04f0\n"
        ".word 0xe28d1048\n"
        ".word 0xe58d0038\n"
        ".word 0xe58d003c\n"
        ".word 0xe1a00001\n"
        ".word 0xeb06730f\n"
        ".word 0xeeb00a49\n"
        ".word 0xe3a00000\n"
        ".word 0xe3a015fe\n"
        ".word 0xe28d2008\n"
        ".word 0xed8d0a02\n"
        ".word 0xe58d000c\n"
        ".word 0xe58d0010\n"
        ".word 0xe58d0014\n"
        ".word 0xe58d0018\n"
        ".word 0xed8d0a07\n"
        ".word 0xe58d0020\n"
        ".word 0xe58d0024\n"
        ".word 0xe58d0028\n"
        ".word 0xe58d002c\n"
        ".word 0xed8d9a0c\n"
        ".word 0xe1cd04f0\n"
        ".word 0xe28d1048\n"
        ".word 0xe58d0034\n"
        ".word 0xe58d0038\n"
        ".word 0xe58d003c\n"
        ".word 0xe1a00001\n"
        ".word 0xeb0672f9\n"
        ".word 0xe3a01015\n"
        ".word 0xe3a0000e\n"
        ".word 0xeb06942c\n"
        ".word 0xe1a06000\n"
        ".word 0xe590000c\n"
        ".word 0xe3a02004\n"
        ".word 0xe1d010f0\n"
        ".word 0xe1d000f2\n"
        ".word 0xe0811fa1\n"
        ".word 0xe0800fa0\n"
        ".word 0xe08210c1\n"
        ".word 0xe08220c0\n"
        ".word 0xe2610000\n"
        ".word 0xee000a90\n"
        ".word 0xe2621000\n"
        ".word 0xee001a10\n"
        ".word 0xe3a00000\n"
        ".word 0xe3a015fe\n"
        ".word 0xe58d000c\n"
        ".word 0xeef80ae0\n"
        ".word 0xe58d1008\n"
        ".word 0xeeb80ac0\n"
        ".word 0xe58d0010\n"
        ".word 0xe28d2008\n"
        ".word 0xedcd0a05\n"
        ".word 0xe1cd01f8\n"
        ".word 0xe58d0020\n"
        ".word 0xed8d0a09\n"
        ".word 0xe58d0028\n"
        ".word 0xe1cd02fc\n"
        ".word 0xed8d8a0d\n"
        ".word 0xe1cd04f0\n"
        ".word 0xe28d1048\n"
        ".word 0xe58d0038\n"
        ".word 0xe58d003c\n"
        ".word 0xe1a00001\n"
        ".word 0xeb0672d4\n"
        ".word 0xe5980000\n"
        ".word 0xe28d1048\n"
        ".word 0xeb067b61\n"
        ".word 0xe5940008\n"
        ".word 0xe3500002\n"
        ".word 0x1a000004\n"
        ".word 0xe28400c8\n"
        ".word 0xed900a08\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb06940f\n"
        ".word 0xe5985000\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01001\n"
        ".word 0xe3a00006\n"
        ".word 0xeb06ae2f\n"
        ".word 0xe2855a01\n"
        ".word 0xe2855fab\n"
        ".word 0xe5951000\n"
        ".word 0xe0852101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d52018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000002\n"
        ".word 0xe595101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe5c57018\n"
        ".word 0xe3a00065\n"
        ".word 0xe58d0004\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a02003\n"
        ".word 0xe3a0100e\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d7000\n"
        ".word 0xeb069387\n"
        ".word 0xe5985000\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01007\n"
        ".word 0xe3a00006\n"
        ".word 0xeb06ae15\n"
        ".word 0xe2855a01\n"
        ".word 0xe2855fab\n"
        ".word 0xe5951000\n"
        ".word 0xe0852101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d52018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a00000a\n"
        ".word 0xea000006\n"
        ".word 0x0043e0f8\n"
        ".word 0x0044ea00\n"
        ".word 0x3e947ae1\n"
        ".word 0x00476638\n"
        ".word 0x3f800000\n"
        ".word 0x00000000\n"
        ".word 0x004efd9c\n"
        ".word 0xe595101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe5c57018\n"
        ".word 0xe284003c\n"
        ".word 0xed900a08\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb0693d6\n"
        ".word 0xe3a0006a\n"
        ".word 0xe3a02002\n"
        ".word 0xe58d0004\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a0100e\n"
        ".word 0xe1a00002\n"
        ".word 0xe58d7000\n"
        ".word 0xeb069360\n"
        ".word 0xe5d40010\n"
        ".word 0xe3500000\n"
        ".word 0x0a000058\n"
        ".word 0xe5d40012\n"
        ".word 0xe3500000\n"
        ".word 0x1a000003\n"
        ".word 0xe3a010dc\n"
        ".word 0xe3a0000e\n"
        ".word 0xeb0693b5\n"
        ".word 0xe1a06000\n"
        ".word 0xe5d40012\n"
        ".word 0xe3500001\n"
        ".word 0x1a000003\n"
        ".word 0xe3a010dd\n"
        ".word 0xe3a0000e\n"
        ".word 0xeb0693ae\n"
        ".word 0xe1a06000\n"
        ".word 0xe3a01004\n"
        ".word 0xe2840f55\n"
        ".word 0xeb06723c\n"
        ".word 0xe596100c\n"
        ".word 0xe1d110f0\n"
        ".word 0xe0410000\n"
        ".word 0xe0800fa0\n"
        ".word 0xe1a050c0\n"
        ".word 0xe284003c\n"
        ".word 0xed900a08\n"
        ".word 0xeeb02a40\n"
        ".word 0xee005a10\n"
        ".word 0xeef01a48\n"
        ".word 0xe2842f55\n"
        ".word 0xe3a010ff\n"
        ".word 0xe3a00004\n"
        ".word 0xed9f1a53\n"
        ".word 0xeeb80ac0\n"
        ".word 0xeddf0a52\n"
        ".word 0xeb068fc4\n"
        ".word 0xe5940014\n"
        ".word 0xe3500001\n"
        ".word 0x1a000010\n"
        ".word 0xe3a0006f\n"
        ".word 0xe3a06007\n"
        ".word 0xe58d0004\n"
        ".word 0xe245300d\n"
        ".word 0xe3a020df\n"
        ".word 0xe3a0100e\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d6000\n"
        ".word 0xeb0692f1\n"
        ".word 0xe3a00074\n"
        ".word 0xe58d0004\n"
        ".word 0xe245300d\n"
        ".word 0xe3a020de\n"
        ".word 0xe3a0100e\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d6000\n"
        ".word 0xeb0692e9\n"
        ".word 0xe5940014\n"
        ".word 0xe3500004\n"
        ".word 0x1a000004\n"
        ".word 0xe1d401f8\n"
        ".word 0xe3a03079\n"
        ".word 0xe3a02008\n"
        ".word 0xe245100d\n"
        ".word 0xeb067205\n"
        ".word 0xe5940014\n"
        ".word 0xe3500002\n"
        ".word 0x1a000006\n"
        ".word 0xe1d401d1\n"
        ".word 0xe3a03079\n"
        ".word 0xe3a02008\n"
        ".word 0xe88d0081\n"
        ".word 0xe1d401f8\n"
        ".word 0xe245100d\n"
        ".word 0xeb06719c\n"
        ".word 0xe5940014\n"
        ".word 0xe3500003\n"
        ".word 0x1a000005\n"
        ".word 0xe58d7000\n"
        ".word 0xe1d401f8\n"
        ".word 0xe3a03079\n"
        ".word 0xe3a02008\n"
        ".word 0xe245100d\n"
        ".word 0xeb068f08\n"
        ".word 0xe5940014\n"
        ".word 0xe3500005\n"
        ".word 0x1a000004\n"
        ".word 0xe1d401b8\n"
        ".word 0xe3a03079\n"
        ".word 0xe3a02008\n"
        ".word 0xe245100d\n"
        ".word 0xeb067161\n"
        ".word 0xe5980000\n"
        ".word 0xeb069c85\n"
        ".word 0xeeb00a68\n"
        ".word 0xe320f000\n"
        ".word 0xeb06936d\n"
        ".word 0xe5980000\n"
        ".word 0xe2804a01\n"
        ".word 0xe2844f93\n"
        ".word 0xe5940000\n"
        ".word 0xe0841100\n"
        ".word 0xe2400001\n"
        ".word 0xe5911008\n"
        ".word 0xe5840000\n"
        ".word 0xe0840100\n"
        ".word 0xe5d42018\n"
        ".word 0xe5900008\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000002\n"
        ".word 0xe594101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe5c47018\n"
        ".word 0xe3a00000\n"
        ".word 0xe28dd08c\n"
        ".word 0xecbd8b04\n"
        ".word 0xe8bd83f0\n"
        ".word 0x3f11eb85\n"
        ".word 0x40c00000\n"
    );
}
#if 0
// Partial semantic draft retained for reconstruction; not compiled.
[[maybe_unused]] static void ComWin_DrawUp_Draft(void* arg) {
    (void)arg;
    ComWinWork* work = g_ComWinWork;
    if (work == nullptr || work->draw_up_right == nullptr) {
        return;
    }

    UiGpu_BeginPass(g_AsdGpuState);
    UiGpu_SetViewportParams(1, 0);

    auto* layer = reinterpret_cast<u32*>(g_AsdGpuState + 0x124C);
    const u32 old_depth = *layer;
    *layer = old_depth + 1;
    auto* layer_entry = reinterpret_cast<u32*>(g_AsdGpuState + 0x124C + 8);
    layer_entry[*layer] = 1;

    // Stereoscopic parallax shift (0.29f scale)
    const f32 shift = UiGpu_TransformCoord(g_AsdGpuState, 0.29f);
    const s32 base_x = static_cast<s32>(shift);

    // Apply alpha from message panel sprite
    const f32 alpha = *reinterpret_cast<const f32*>(&work->panel_sprites[0].raw[0x20]);
    UiGpu_SetAlphaBlend(alpha);

    // Draw message dialog frame panel
    UiSprite_DrawPanelDirect(2, 0x0E, 0x01, base_x, 0, 1);

    // Draw dialog text background
    UiSprite_DrawPanelDirect(2, 0x0E, 0x02, base_x, 0, 1);

    // Restore layer matrix
    if (*layer > 0) {
        *layer = *layer - 1;
    }
}
#endif

void ComWin_Calc(void* arg) {
    (void)arg;
}

InfoWinWork* g_InfoWinWork = nullptr; // 0x0043E128

// DECOMP_FUNC(0x0010af48, 60)
void InfoWin_SetState(u32 state) {
    auto* context = reinterpret_cast<u8*>(0x004C3B20);
    func_0011b558(*reinterpret_cast<void**>(context + 0x1C0));
    engine_func_0011b5e8(context);
    if (state == 3) {
        *reinterpret_cast<volatile u8*>(0x0044D020) = 1;
    }
}

// DECOMP_FUNC(0x0010af84, 560)
void InfoWin_Init() {
    static constexpr u32 kWorkSize = 0x1BC;
    static constexpr u32 kCalcTag = 1;
    static constexpr u32 kDrawUpLeftTag = 0x81;
    static constexpr u32 kDrawUpRightTag = 0xDF;
    static constexpr s32 kSpriteType = 0x0E;
    static constexpr s32 kSpriteId = 0x87;
    static constexpr u32 kTextColor = 0x646464FFu;
    static constexpr u32 kInitialTimer = 0x1E;

    u8* work = reinterpret_cast<u8*>(g_InfoWinWork);
    if (work == nullptr) {
        work = static_cast<u8*>(AsdMem_Alloc(0x100, 0x100, 0, kWorkSize, 1));
        g_InfoWinWork = reinterpret_cast<InfoWinWork*>(work);
    }

    AsdMem_Zero(work, kWorkSize);

    void* const calc_task = AsdTask_CreateCalc(
        "InfoWin Calc",
        kCalcTag,
        0,
        0,
        InfoWin_Calc,
        0,
        0);
    *reinterpret_cast<void**>(work) = calc_task;

    AsdTask_CreateDraw(
        "InfoWin DrawUpLeft",
        kDrawUpLeftTag,
        0,
        0,
        InfoWin_DrawUp,
        0,
        0,
        calc_task);

    AsdTask_CreateDraw(
        "InfoWin DrawUpRight",
        kDrawUpRightTag,
        0,
        0,
        InfoWin_DrawUp,
        0,
        0,
        calc_task);

    u8* const bound_work = reinterpret_cast<u8*>(g_InfoWinWork);
    UiSpriteGroup* const sprite_group = reinterpret_cast<UiSpriteGroup*>(bound_work + 0x24);
    UiAnimSprite* const panel_sprite = reinterpret_cast<UiAnimSprite*>(bound_work + 0x44);
    UiAnimSprite* const arrow_sprite = reinterpret_cast<UiAnimSprite*>(bound_work + 0xD0);

    UiSpriteGroup_Init(sprite_group);
    UiSpriteGroup_BindTable(
        sprite_group,
        SpriteTableWord(g_InfoWinSpriteTable),
        0x24,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0);

    using InfoWinSetupEx = void (*)(UiAnimSprite*, s32, s32, UiSpriteGroup*, u32, f32);
    reinterpret_cast<InfoWinSetupEx>(UiAnimSprite_SetupEx)(
        panel_sprite,
        kSpriteType,
        kSpriteId,
        sprite_group,
        1,
        1.0f);
    UiAnimSprite_SetMode(panel_sprite, 0, 0);

    reinterpret_cast<InfoWinSetupEx>(UiAnimSprite_SetupEx)(
        arrow_sprite,
        kSpriteType,
        kSpriteId,
        sprite_group,
        1,
        1.0f);
    UiAnimSprite_SetMode(arrow_sprite, 2, 0);

    void* const text_handle = AsdText_CreateDefault(0);
    *reinterpret_cast<void**>(bound_work + 0x1B8) = text_handle;
    AsdText_SetAlpha(text_handle, 0xFFFFFFFFu);
    AsdText_SetColorAndScale(
        *reinterpret_cast<void**>(bound_work + 0x1B8),
        0,
        kTextColor,
        0.0f);

    *reinterpret_cast<u32*>(bound_work + 0x10) = kInitialTimer;
}
#if 0
// Partial semantic draft retained for reconstruction; not compiled.
[[maybe_unused]] static void InfoWin_Init_Draft() {
    InfoWinWork* work = g_InfoWinWork;
    if (work == nullptr) {
        work = static_cast<InfoWinWork*>(
            AsdMem_Alloc(0x100, 0xFF, 0, sizeof(InfoWinWork), 1));
        g_InfoWinWork = work;
    }

    AsdMem_Zero(work, sizeof(InfoWinWork));

    work->calc_task = AsdTask_CreateCalc("InfoWin Calc", 1, 0, 0,
                                         InfoWin_Calc, 0, 0);
    work->draw_up_left = AsdTask_CreateDraw("InfoWin DrawUpLeft", 0x81, 0, 0,
                                            InfoWin_DrawUp, 0, 0, work->calc_task);
    work->draw_up_right = AsdTask_CreateDraw("InfoWin DrawUpRight", 0xDF, 0, 0,
                                             InfoWin_DrawUp, 0, 0, work->calc_task);

    UiSpriteGroup_Init(&work->sprite_group);
    UiSpriteGroup_BindTable(&work->sprite_group,
                            SpriteTableWord(g_InfoWinSpriteTable), 0x24,
                            0, 0, 0, 0, 0, 0, 0, 0);

    UiAnimSprite_SetupEx(&work->panel_sprites[0], 0x0E, 0x87, 0, &work->sprite_group, 1, 1.0f);
    UiAnimSprite_SetMode(&work->panel_sprites[0], 0, 0);

    UiAnimSprite_SetupEx(&work->panel_sprites[1], 0x0E, 0x87, 0, &work->sprite_group, 1, 1.0f);
    UiAnimSprite_SetMode(&work->panel_sprites[1], 2, 0);

    work->text_handle = AsdText_CreateDefault(0);
    AsdText_SetAlpha(work->text_handle, 0xFF);
    AsdText_SetColorAndScale(work->text_handle, 0, 0x646464FFu, 0.0f);

    work->timer = 0x1E;
}
#endif

// Incomplete first-pass C++ sketch. The extracted body also dereferences the
// input through AsdRef_Get, checks several flags at +0xF60/+0xF63/+0xF99,
// initializes the referenced render object, and updates bytes at +0xF62/+0xF63.
[[maybe_unused]] static void InfoWin_ShowMessage_Draft(const char* msg) {
    (void)msg;
    InfoWinWork* work = g_InfoWinWork;
    if (work == nullptr) {
        return;
    }
    work->state = 1;
    work->timer = 0x1E;
}

// The complete ARM body includes a literal pool word at 0x0010B25C.
// DECOMP_FUNC(0x0010b1b4, 172)
void InfoWin_ShowMessage(const char*) {
    auto* const work = reinterpret_cast<u8*>(ui_func_002c0ac8());
    auto* const f00 = work + 0xF00;

    const u8 b60 = f00[0x60];
    if (b60 == 0) {
        return;
    }
    const u8 b63 = f00[0x63];
    if (b63 != 0) {
        return;
    }

    const u8 b99 = f00[0x99];
    if (b99 == 0) {
        return;
    }
    void* const sound_obj = *reinterpret_cast<void**>(0x0044EA00);
    UiGpu_BeginPass(sound_obj);

    auto* const obj = *reinterpret_cast<u8**>(work + 4);
    *reinterpret_cast<u32*>(obj + 0x14) = 0x200;
    *reinterpret_cast<u32*>(obj + 0x18) = 0x200;

    work[0xF62] = static_cast<u8>(func_002bfcb4(0, obj));
    func_002bfc88(obj, obj);

    *reinterpret_cast<s32*>(obj + 0x14) >>= 1;
    *reinterpret_cast<s32*>(obj + 0x18) >>= 1;

    work[0xF63] = 1;
}

// Incomplete first-pass C++ sketch; the exact body also obtains an object via
// AsdRef_Get and runs its render/state setup path when its control flags allow.
[[maybe_unused]] static void InfoWin_UpdateTimer_Draft() {
    InfoWinWork* work = g_InfoWinWork;
    if (work == nullptr || work->state == 0) {
        return;
    }
    if (work->timer > 0) {
        work->timer--;
    } else {
        work->state = 0;
    }
}

// The complete ARM body includes its literal pool word at 0x0010B31C.
// DECOMP_FUNC(0x0010b260, 192)
void InfoWin_UpdateTimer() {
    auto* const work = reinterpret_cast<u8*>(ui_func_002c0ac8());
    if (func_002c00e8(0) != 0) {
        work[0xF65] = 1;
        return;
    }

    const u8 b60 = work[0xF60];
    if (b60 == 0) {
        return;
    }

    auto* const f00 = work + 0xF00;
    if (f00[0x64] != 0 || f00[0x65] != 0) {
        return;
    }

    const u8 b99 = f00[0x99];
    if (b99 == 0) {
        return;
    }
    void* const sound_obj = *reinterpret_cast<void**>(0x0044EA00);
    UiGpu_BeginPass(sound_obj);

    auto* const obj = *reinterpret_cast<u8**>(work + 8);
    *reinterpret_cast<u32*>(obj + 0x14) = 0x200;
    *reinterpret_cast<u32*>(obj + 0x18) = 0x200;

    work[0xF62] = static_cast<u8>(func_002bfcb4(0, obj));
    func_002bfc88(obj, obj);

    *reinterpret_cast<s32*>(obj + 0x14) >>= 1;
    *reinterpret_cast<s32*>(obj + 0x18) >>= 1;

    work[0xF64] = 1;
}

// DECOMP_FUNC(0x0010b320, 32)
bool InfoWin_Dismiss(u32 value) {
    u32* context = reinterpret_cast<u32*>(0x00464A70);
    const u32 limit = context[1];
    if (value < limit) {
        context[3] = value;
        return true;
    }
    return false;
}

extern "C" {
    void engine_func_002b9220(void* sprite, u32 a1);                                        // 0x002b9220
    s32  ui_func_002bef7c(void* sprite);                                                    // 0x002bef7c
    s32  ui_func_002bef70(void* sprite);                                                    // 0x002bef70
    const u8* camp_func_002bf6d0(s32 type, s32 id);                                         // 0x002bf6d0
    void func_002b68dc(s32 x, s32 y, s32 w, s32 h);                                         // 0x002b68dc
    void func_002b792c(void* text, s32 x, s32 y, s32 a3, s32 a4, s32 a5, f32 scale);        // 0x002b792c
    void func_002b67f8();                                                                   // 0x002b67f8
}

// DECOMP_FUNC(0x0011ae10, 792)
void InfoWin_DrawUp(void*) {
    static constexpr f32 kParallaxScale = 0.27f;

    auto* const work = reinterpret_cast<u8*>(g_InfoWinWork);
    if (*reinterpret_cast<const u32*>(work + 0x08) == 0 || work[0x20] == 0) {
        return;
    }

    auto sync_viewport = [](u8* vp_stack, void* old_vp, void* target_vp) {
        if (vp_stack[0x18] != 0 || old_vp != target_vp) {
            using ViewportCb = void (*)(void*);
            (*reinterpret_cast<const ViewportCb*>(vp_stack + 0x1C))(target_vp);
            vp_stack[0x18] = 0;
        }
    };

    UiGpu_BeginPass(g_AsdGpuState);

    void* const new_vp = UiGpu_SetViewportParams(1, 0);
    auto* const vp_stack = g_AsdGpuState + 0x124C;
    auto* const vp_idx = reinterpret_cast<s32*>(vp_stack);
    auto* const vp_slots = reinterpret_cast<void**>(vp_stack + 0x08);
    const s32 push_idx = *vp_idx;
    void* const prev_vp = vp_slots[push_idx];
    *vp_idx = push_idx + 1;
    vp_slots[push_idx + 1] = new_vp;
    sync_viewport(vp_stack, prev_vp, new_vp);

    const s32 base_x = ui_func_002bef7c(work + 0x44) +
                       static_cast<s32>(UiGpu_TransformCoord(g_AsdGpuState, kParallaxScale));
    const s32 base_y = ui_func_002bef70(work + 0x44);

    UiSprite_DrawPanelDirect(2, 0x0E, 0x87, base_x, base_y, 0x15);
    UiSprite_DrawPanelDirect(2, 0x0E, 0x88, base_x, base_y, 0x15);

    if (work[0x21] != 0) {
        const u8* const clip_layout = camp_func_002bf6d0(0x0E, 0x87);
        const s16* const rect = *reinterpret_cast<const s16* const*>(clip_layout + 0x0C);
        func_002b68dc(
            base_x + *reinterpret_cast<const s16*>(clip_layout + 0x08),
            base_y + *reinterpret_cast<const s16*>(clip_layout + 0x0A),
            rect[0], rect[1]);

        const u8* const text_layout = camp_func_002bf6d0(0x0E, 0x89);
        const s32 tx = base_x + *reinterpret_cast<const s16*>(text_layout + 0x08);
        const s32 ty = base_y + *reinterpret_cast<const s16*>(text_layout + 0x0A);
        void* const text_obj = *reinterpret_cast<void* const*>(work + 0x1B8);

        if (work[0x23] != 0) {
            func_002b792c(text_obj, tx, ty, 0xC9, 6, 0, 1.0f);
        } else {
            func_002b792c(
                text_obj, tx + *reinterpret_cast<const s32*>(work + 0x18), ty, 0xC9, 6, 0, 1.0f);
            if (work[0x22] != 0) {
                func_002b792c(
                    text_obj, tx + *reinterpret_cast<const s32*>(work + 0x1C), ty, 0xC9, 6, 0, 1.0f);
            }
        }
        func_002b67f8();
    }

    UiSprite_DrawPanelDirect(2, 0x0E, 0x86, base_x, base_y, 0x1F);
    UiSprite_DrawPanelDirect(2, 0x0E, 0x102, base_x, base_y, 0x1F);

    auto* const pop_stack = g_AsdGpuState + 0x124C;
    auto* const pop_idx = reinterpret_cast<s32*>(pop_stack);
    auto* const pop_slots = reinterpret_cast<void**>(pop_stack + 0x08);
    const s32 cur_idx = *pop_idx;
    void* const popped_vp = pop_slots[cur_idx];
    *pop_idx = cur_idx - 1;
    void* const restored_vp = pop_slots[cur_idx - 1];
    sync_viewport(pop_stack, popped_vp, restored_vp);
}

// DECOMP_FUNC(0x0011b1bc, 440)
void InfoWin_Calc(void*) {
    static constexpr s32 kScrollGap = 0x2A;
    static constexpr s32 kScrollDelayFrames = 0x1E;
    static constexpr s32 kCloseTimer = 0x1E;

    u8* const work = reinterpret_cast<u8*>(g_InfoWinWork);
    const u32 state = *reinterpret_cast<const u32*>(work + 0x08);

    switch (state) {
    case 1:
        if (ui_func_002bf9f0(work + 0x44) != 0) {
            if (work[0x23] != 0) {
                *reinterpret_cast<u32*>(work + 0x08) = 4;
            } else {
                *reinterpret_cast<u32*>(work + 0x08) = 2;
                UiAnimSprite_SetMode(reinterpret_cast<UiAnimSprite*>(work + 0xD0), 2, 0);
            }
            *reinterpret_cast<u32*>(work + 0x0C) = 0;
        }
        break;
    case 2: {
        engine_func_002b9220(work + 0xD0, 0);
        const s32 width = ui_func_002bef7c(work + 0xD0);
        *reinterpret_cast<s32*>(work + 0x18) = width;
        if (width <= 0) {
            *reinterpret_cast<s32*>(work + 0x18) = 0;
            *reinterpret_cast<u32*>(work + 0x08) = 3;
            *reinterpret_cast<u32*>(work + 0x0C) = 0;
        }
        *reinterpret_cast<s32*>(work + 0x1C) =
            *reinterpret_cast<const s32*>(work + 0x18) +
            *reinterpret_cast<const s32*>(work + 0x14) +
            kScrollGap;
        break;
    }
    case 3:
        if (*reinterpret_cast<const s32*>(work + 0x0C) > kScrollDelayFrames && work[0x22] != 0) {
            const s32 span = *reinterpret_cast<const s32*>(work + 0x14);
            const s32 x0 = *reinterpret_cast<const s32*>(work + 0x18) - 1;
            *reinterpret_cast<s32*>(work + 0x18) = x0;
            if (x0 < -span) {
                *reinterpret_cast<s32*>(work + 0x18) =
                    *reinterpret_cast<const s32*>(work + 0x1C) + span + kScrollGap;
            }
            const s32 span2 = *reinterpret_cast<const s32*>(work + 0x14);
            const s32 x1 = *reinterpret_cast<const s32*>(work + 0x1C) - 1;
            *reinterpret_cast<s32*>(work + 0x1C) = x1;
            if (x1 < -span2) {
                *reinterpret_cast<s32*>(work + 0x1C) =
                    *reinterpret_cast<const s32*>(work + 0x18) + span2 + kScrollGap;
            }
        }
        break;
    case 4: {
        const s32 timer = *reinterpret_cast<const s32*>(work + 0x10);
        if (timer >= 0 && *reinterpret_cast<const s32*>(work + 0x0C) > timer) {
            *reinterpret_cast<u32*>(work + 0x08) = 5;
            *reinterpret_cast<s32*>(work + 0x10) = kCloseTimer;
            UiAnimSprite_SetMode(reinterpret_cast<UiAnimSprite*>(work + 0x44), 1, 0);
        }
        break;
    }
    case 5:
        if (ui_func_002bf9f0(work + 0x44) != 0) {
            work[0x23] = 0;
            *reinterpret_cast<u32*>(work + 0x08) = 0;
            *reinterpret_cast<u32*>(work + 0x0C) = 0;
        }
        break;
    default:
        break;
    }

    *reinterpret_cast<s32*>(work + 0x0C) += 1;
}
#if 0
// Partial semantic draft retained for reconstruction; not compiled.
[[maybe_unused]] static void InfoWin_Calc_Draft(void* arg) {
    (void)arg;
    InfoWinWork* work = g_InfoWinWork;
    if (work == nullptr || work->state == 0) {
        return;
    }
    InfoWin_UpdateTimer();
}
#endif

GuestWinWork* g_GuestWinWork = nullptr; // 0x0043E110

void GuestWin_Calc(void* arg);                                                      // 0x0011b128

extern "C" {
    void GuestWin_Calc_0011b128(void*);                                                     // 0x0011b128
    extern const u8 g_GuestWinSpriteTable_00403a08;                                         // 0x00403a08
    extern const u8 g_GuestWinSpriteTable_00403a20;                                         // 0x00403a20
}

// DECOMP_FUNC(0x0010b350, 448)
void GuestWin_Init() {
    static constexpr u32 kWorkSize = 0xBC;
    static constexpr u32 kCalcTag = 1;
    static constexpr u32 kDrawUpLeftTag = 0x81;
    static constexpr u32 kDrawUpRightTag = 0xDF;
    static constexpr s32 kSpriteType = 0x0E;
    static constexpr s32 kSpriteId = 0x87;

    u8* work = reinterpret_cast<u8*>(g_GuestWinWork);
    if (work == nullptr) {
        work = static_cast<u8*>(AsdMem_Alloc(0x100, 0x100, 0, kWorkSize, 1));
        g_GuestWinWork = reinterpret_cast<GuestWinWork*>(work);
    }

    AsdMem_Zero(work, kWorkSize);

    void* const calc_task = AsdTask_CreateCalc(
        "GuestWin Calc",
        kCalcTag,
        0,
        0,
        GuestWin_Calc_0011b128,
        0,
        0);
    *reinterpret_cast<void**>(work) = calc_task;

    AsdTask_CreateDraw(
        "GuestWin DrawUpLeft",
        kDrawUpLeftTag,
        0,
        0,
        GuestWin_DrawUp,
        0,
        0,
        calc_task);

    AsdTask_CreateDraw(
        "GuestWin DrawUpRight",
        kDrawUpRightTag,
        0,
        0,
        GuestWin_DrawUp,
        0,
        0,
        calc_task);

    u8* const bound_work = reinterpret_cast<u8*>(g_GuestWinWork);
    UiSpriteGroup* const sprite_group = reinterpret_cast<UiSpriteGroup*>(bound_work + 0x10);
    UiAnimSprite* const panel_sprite = reinterpret_cast<UiAnimSprite*>(bound_work + 0x30);

    UiSpriteGroup_Init(sprite_group);
    UiSpriteGroup_BindTable(
        sprite_group,
        SpriteTableWord(&g_GuestWinSpriteTable_00403a08),
        0x18,
        SpriteTableWord(&g_GuestWinSpriteTable_00403a20),
        0x18,
        0,
        0,
        0,
        0,
        SpriteTableWord(g_GuestWinSpriteTable),
        0x70);

    using GuestWinSetupEx = void (*)(UiAnimSprite*, s32, s32, UiSpriteGroup*, u32, f32);
    reinterpret_cast<GuestWinSetupEx>(UiAnimSprite_SetupEx)(
        panel_sprite,
        kSpriteType,
        kSpriteId,
        sprite_group,
        1,
        1.0f);

    using GuestWinSetAnim = void (*)(UiAnimSprite*, s32);
    reinterpret_cast<GuestWinSetAnim>(UiAnimSprite_SetAnim)(
        panel_sprite,
        0);
}
#if 0
// Partial semantic draft retained for reconstruction; not compiled.
[[maybe_unused]] static void GuestWin_Init_Draft() {
    GuestWinWork* work = g_GuestWinWork;
    if (work == nullptr) {
        work = static_cast<GuestWinWork*>(
            AsdMem_Alloc(0x100, 0xF5, 0, sizeof(GuestWinWork), 1));
        g_GuestWinWork = work;
    }

    AsdMem_Zero(work, sizeof(GuestWinWork));

    work->calc_task = AsdTask_CreateCalc("GuestWin Calc", 1, 0, 0,
                                         GuestWin_Calc, 0, 0);
    work->draw_up_left = AsdTask_CreateDraw("GuestWin DrawUpLeft", 0x81, 0, 0,
                                            GuestWin_DrawUp, 0, 0, work->calc_task);
    work->draw_up_right = AsdTask_CreateDraw("GuestWin DrawUpRight", 0xDF, 0, 0,
                                             GuestWin_DrawUp, 0, 0, work->calc_task);

    UiSpriteGroup_Init(&work->sprite_group);
    UiSpriteGroup_BindTable(&work->sprite_group,
                            SpriteTableWord(g_GuestWinSpriteTable - 0x30), 0x18,
                            SpriteTableWord(g_GuestWinSpriteTable - 0x18), 0x18,
                            0, 0, 0, 0,
                            SpriteTableWord(g_GuestWinSpriteTable), 0x70);

    UiAnimSprite_SetupEx(&work->panel_sprite, 0x0E, 0x87, 0, &work->sprite_group, 1, 1.0f);
    UiAnimSprite_SetAnim(&work->panel_sprite, 0, 0);
}
#endif

//
void GuestWin_HandlePrompt_Decompiled() {
    auto* ctx = reinterpret_cast<u8*>(UiEngine_GetContext());
    if (ctx == nullptr) {
        return;
    }

    auto* timer_block = reinterpret_cast<s16*>(ctx + 0xF28);
    auto* flag_block = ctx + 0xF20;

    for (s32 i = 0; i < 16; ++i) {
        u8 flags = flag_block[i * 0x14];
        if ((flags & 7) == 7 && !(flags & 8)) {
            s16 timer = timer_block[i * (0x14 / 2)];
            if (timer > 0) {
                timer--;
                timer_block[i * (0x14 / 2)] = timer;
            }
            if (timer == 0) {
                flag_block[i * 0x14] |= 8;
            }
        }
    }
}
// DECOMP_FUNC(0x0010b510, 104)
void GuestWin_HandlePrompt() {
    auto* const ctx = reinterpret_cast<u8*>(UiEngine_GetContext());

    for (s32 i = 0; i < 16; ++i) {
        auto* const flag_ptr = ctx + 0x3C80 + i * 0x14;
        const u8 flags = *flag_ptr;
        if ((flags & 7) == 7 && !(flags & 8)) {
            auto* const timer_ptr = reinterpret_cast<s16*>(ctx + 0xF28 + i * 0x14);
            s16 timer = *timer_ptr;
            if (timer > 0) {
                timer--;
                *timer_ptr = timer;
            }
            if (timer == 0) {
                *flag_ptr = flags | 8;
            }
        }
    }
}

// DECOMP_FUNC(0x0011a9b4, 1116)
// Boundary-verified ARM-state span; includes its PC-relative literal pool.
__attribute__((naked)) void GuestWin_DrawUp(void* arg) {
    asm volatile(
        ".word 0xe92d47f0\n"
        ".word 0xe59f0438\n"
        ".word 0xed2d8b02\n"
        ".word 0xe24dd048\n"
        ".word 0xe5905000\n"
        ".word 0xe5950008\n"
        ".word 0xe3500000\n"
        ".word 0x0a000105\n"
        ".word 0xeb067127\n"
        ".word 0xe3500000\n"
        ".word 0x0a000102\n"
        ".word 0xe3500001\n"
        ".word 0x0a0000ff\n"
        ".word 0xeb06711c\n"
        ".word 0xe1a06000\n"
        ".word 0xe1d004b6\n"
        ".word 0xe3500000\n"
        ".word 0x0a0000fb\n"
        ".word 0xe59f93f8\n"
        ".word 0xe5990000\n"
        ".word 0xeb06a467\n"
        ".word 0xe5994000\n"
        ".word 0xe3a01000\n"
        ".word 0xe3a00001\n"
        ".word 0xeb06ad58\n"
        ".word 0xe2844a01\n"
        ".word 0xe2844f93\n"
        ".word 0xe3a08000\n"
        ".word 0xe5941000\n"
        ".word 0xe2812001\n"
        ".word 0xe0843101\n"
        ".word 0xe5931008\n"
        ".word 0xe0843102\n"
        ".word 0xe5842000\n"
        ".word 0xe5830008\n"
        ".word 0xe5d42018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000002\n"
        ".word 0xe594101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe5c48018\n"
        ".word 0xe2850030\n"
        ".word 0xeb069145\n"
        ".word 0xe1a04000\n"
        ".word 0xe5990000\n"
        ".word 0xed9f0ae3\n"
        ".word 0xeb067e7d\n"
        ".word 0xeebd0ac0\n"
        ".word 0xee100a10\n"
        ".word 0xe0847000\n"
        ".word 0xe2850030\n"
        ".word 0xeb069139\n"
        ".word 0xe1a0a000\n"
        ".word 0xe2850030\n"
        ".word 0xed900a08\n"
        ".word 0xeeb08a40\n"
        ".word 0xe320f000\n"
        ".word 0xeb06931b\n"
        ".word 0xe3a010da\n"
        ".word 0xe3a0000e\n"
        ".word 0xeb069308\n"
        ".word 0xe1a04000\n"
        ".word 0xe320f000\n"
        ".word 0xeb0670e2\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000003\n"
        ".word 0xe3a010db\n"
        ".word 0xe3a0000e\n"
        ".word 0xeb0692ff\n"
        ".word 0xe1a04000\n"
        ".word 0xe5995000\n"
        ".word 0xe1d410f8\n"
        ".word 0xe1d400fa\n"
        ".word 0xe3a02000\n"
        ".word 0xe0877001\n"
        ".word 0xe080400a\n"
        ".word 0xe3a01001\n"
        ".word 0xe3a00006\n"
        ".word 0xeb06ad2a\n"
        ".word 0xe2855a01\n"
        ".word 0xe2855fab\n"
        ".word 0xe5951000\n"
        ".word 0xe0852101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d52018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000002\n"
        ".word 0xe595101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe5c58018\n"
        ".word 0xe3a00015\n"
        ".word 0xe58d0004\n"
        ".word 0xe1a03007\n"
        ".word 0xe3a020c9\n"
        ".word 0xe3a0100e\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d4000\n"
        ".word 0xeb069244\n"
        ".word 0xe5995000\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01007\n"
        ".word 0xe3a00006\n"
        ".word 0xeb06ad10\n"
        ".word 0xe2855a01\n"
        ".word 0xe2855fab\n"
        ".word 0xe5951000\n"
        ".word 0xe0852101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d52018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000002\n"
        ".word 0xe595101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe5c58018\n"
        ".word 0xe3a0501a\n"
        ".word 0xe1a03007\n"
        ".word 0xe3a020ca\n"
        ".word 0xe3a0100e\n"
        ".word 0xe3a00002\n"
        ".word 0xe1cd40f0\n"
        ".word 0xeb06922b\n"
        ".word 0xe1a03007\n"
        ".word 0xe3a020cb\n"
        ".word 0xe3a0100e\n"
        ".word 0xe3a00002\n"
        ".word 0xe1cd40f0\n"
        ".word 0xeb069225\n"
        ".word 0xe1a03007\n"
        ".word 0xe3a020cc\n"
        ".word 0xe3a0100e\n"
        ".word 0xe3a00002\n"
        ".word 0xe1cd40f0\n"
        ".word 0xeb06921f\n"
        ".word 0xe1a03007\n"
        ".word 0xe3a020cd\n"
        ".word 0xe3a0100e\n"
        ".word 0xe3a00002\n"
        ".word 0xe1cd40f0\n"
        ".word 0xeb069219\n"
        ".word 0xe3a0501f\n"
        ".word 0xe1a03007\n"
        ".word 0xe3a020ce\n"
        ".word 0xe3a0100e\n"
        ".word 0xe3a00002\n"
        ".word 0xe1cd40f0\n"
        ".word 0xeb069212\n"
        ".word 0xe1a03007\n"
        ".word 0xe3a020cf\n"
        ".word 0xe3a0100e\n"
        ".word 0xe3a00002\n"
        ".word 0xe1cd40f0\n"
        ".word 0xeb06920c\n"
        ".word 0xe28d101c\n"
        ".word 0xe3a00024\n"
        ".word 0xe58d4018\n"
        ".word 0xe8810101\n"
        ".word 0xe3a010d2\n"
        ".word 0xe3a030d0\n"
        ".word 0xe58d100c\n"
        ".word 0xe58d3004\n"
        ".word 0xe3a020d3\n"
        ".word 0xe3a0c00e\n"
        ".word 0xe28d1010\n"
        ".word 0xe58d2008\n"
        ".word 0xe3a000d1\n"
        ".word 0xe58dc000\n"
        ".word 0xe8810081\n"
        ".word 0xe3a03000\n"
        ".word 0xe1d610fe\n"
        ".word 0xe1d602fa\n"
        ".word 0xe1a02003\n"
        ".word 0xeb068f99\n"
        ".word 0xe3a010d9\n"
        ".word 0xe3a0000e\n"
        ".word 0xeb069291\n"
        ".word 0xe1a05000\n"
        ".word 0xe320f000\n"
        ".word 0xeb06705e\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a00001a\n"
        ".word 0xeb06706e\n"
        ".word 0xe2800c06\n"
        ".word 0xe1d060b6\n"
        ".word 0xeb06706b\n"
        ".word 0xe2800c06\n"
        ".word 0xe1a01006\n"
        ".word 0xe1d000f4\n"
        ".word 0xeb067034\n"
        ".word 0xe1d520fa\n"
        ".word 0xe1d510f8\n"
        ".word 0xe1d005ba\n"
        ".word 0xe0822004\n"
        ".word 0xe0811007\n"
        ".word 0xe3a03024\n"
        ".word 0xeb066fe8\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb06705d\n"
        ".word 0xe2800c06\n"
        ".word 0xe1d000b4\n"
        ".word 0xeb068911\n"
        ".word 0xe1a01000\n"
        ".word 0xe28d0028\n"
        ".word 0xfa068ebe\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea00000d\n"
        ".word 0xe58d8000\n"
        ".word 0xe1d520fa\n"
        ".word 0xe1d510f8\n"
        ".word 0xe1d604f6\n"
        ".word 0xe0822004\n"
        ".word 0xe0811007\n"
        ".word 0xe3a03024\n"
        ".word 0xeb066f5a\n"
        ".word 0xe1d604b6\n"
        ".word 0xe320f000\n"
        ".word 0xeb068947\n"
        ".word 0xe1a01000\n"
        ".word 0xe28d0028\n"
        ".word 0xfa068ead\n"
        ".word 0xe3a010d8\n"
        ".word 0xe3a0000e\n"
        ".word 0xeb06925f\n"
        ".word 0xe1d010fa\n"
        ".word 0xe1d020f8\n"
        ".word 0xeeb02a48\n"
        ".word 0xe0810004\n"
        ".word 0xe0821007\n"
        ".word 0xee000a90\n"
        ".word 0xee001a10\n"
        ".word 0xe28d2028\n"
        ".word 0xe3a010ff\n"
        ".word 0xeddf1a22\n"
        ".word 0xe3a00002\n"
        ".word 0xeef80ae0\n"
        ".word 0xeeb80ac0\n"
        ".word 0xed9f1a1f\n"
        ".word 0xeb068e7b\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb06905e\n"
        ".word 0xed9f0a1b\n"
        ".word 0xe320f000\n"
        ".word 0xeb06925a\n"
        ".word 0xe5990000\n"
        ".word 0xe2804a01\n"
        ".word 0xe2844f93\n"
        ".word 0xe5940000\n"
        ".word 0xe0841100\n"
        ".word 0xe2400001\n"
        ".word 0xe5911008\n"
        ".word 0xe5840000\n"
        ".word 0xe0840100\n"
        ".word 0xe5d42018\n"
        ".word 0xe5900008\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000002\n"
        ".word 0xe594101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe5c48018\n"
        ".word 0xe3a00000\n"
        ".word 0xe28dd048\n"
        ".word 0xecbd8b02\n"
        ".word 0xe8bd87f0\n"
        ".word 0x0043e110\n"
        ".word 0x0044ea00\n"
        ".word 0x3e8a3d71\n"
        ".word 0x00000000\n"
        ".word 0x3f59999a\n"
        ".word 0x3f800000\n"
    );
}
#if 0
// Partial semantic draft retained for reconstruction; not compiled.
[[maybe_unused]] static void GuestWin_DrawUp_Draft(void* arg) {
    (void)arg;
    GuestWinWork* work = g_GuestWinWork;
    if (work == nullptr || work->draw_up_right == nullptr || work->state == 0) {
        return;
    }

    UiGpu_BeginPass(g_AsdGpuState);
    UiGpu_SetViewportParams(1, 0);

    auto* layer = reinterpret_cast<u32*>(g_AsdGpuState + 0x124C);
    const u32 old_depth = *layer;
    *layer = old_depth + 1;
    auto* layer_entry = reinterpret_cast<u32*>(g_AsdGpuState + 0x124C + 8);
    layer_entry[*layer] = 1;

    // Stereoscopic parallax shift (0.35f scale)
    const f32 shift = UiGpu_TransformCoord(g_AsdGpuState, 0.35f);
    const s32 base_x = static_cast<s32>(shift);

    const f32 alpha = *reinterpret_cast<const f32*>(&work->panel_sprite.raw[0x20]);
    UiGpu_SetAlphaBlend(alpha);

    // Draw partner prompt banner backdrop & Demonica prompt icon
    UiSprite_DrawPanelDirect(2, 0x0E, 0x03, base_x, 0, 1);
    UiSprite_DrawPanelDirect(2, 0x0E, 0x04, base_x, 0, 1);

    if (*layer > 0) {
        *layer = *layer - 1;
    }
}
#endif

// DECOMP_FUNC(0x0011b128, 148)
void GuestWin_Calc(void*) {
    auto* const btl = reinterpret_cast<u8*>(battle_func_002b6e60());
    const u16 active = *reinterpret_cast<const u16*>(btl + 0x46);
    if (active == 0) {
        return;
    }

    auto* const work = *reinterpret_cast<u8**>(0x0043E110);
    const u32 state = *reinterpret_cast<const u32*>(work + 8);
    if (state == 1) {
        if (ui_func_002bf9f0(work + 0x30) != 0) {
            *reinterpret_cast<u32*>(work + 8) = 2;
            *reinterpret_cast<u32*>(work + 0xC) = 0;
        }
    } else if (state == 3) {
        if (ui_func_002bf9f0(work + 0x30) != 0) {
            *reinterpret_cast<u32*>(work + 8) = 0;
        }
    }

    *reinterpret_cast<u32*>(work + 0xC) += 1;
}

// ============================================================================
// PlaceWin: Location & Area Banner HUD Window (c:\SMT4\XRD686\sdds4\program\font\PlaceWin\PlaceWin.cpp)
// ============================================================================

PlaceWinWork* g_PlaceWinWork = nullptr; // 0x0043E140
static const u8 g_PlaceWinSpriteTable[0x20] = {0};

// DECOMP_FUNC(0x0026385c, 64)
void PlaceWin_SetPos(s32 index, s32 layer, f32 x, f32 y, f32 z) {
    const s32 layer_index = layer + (layer << 5) + (layer << 7);
    const u32 slot_address = 0x004D9880 + 0x264 +
                             static_cast<u32>((layer_index + index) * 4);
    auto* const slot = *reinterpret_cast<u8* const*>(slot_address);
    auto* const target = *reinterpret_cast<u8* const*>(slot + 8);
    auto* const floats = reinterpret_cast<f32*>(target + 0xB8);
    floats[0] = x;
    floats[1] = y;
    floats[2] = z;
    floats[3] = 1.0f;
    *reinterpret_cast<void**>(target + 0xC8) = engine_func_002c2be8(floats);
}

// DECOMP_FUNC(0x0026389c, 64)
void PlaceWin_SetScale(s32 idx, s32 layer, f32 sx, f32 sy, f32 sz, f32 sw) {
    if (idx < 0) {
        return;
    }
    const s32 layer_index = layer + (layer << 5) + (layer << 7);
    const u32 slot_address = 0x004D9D88 + 0x264 +
                             static_cast<u32>((layer_index + idx) * 4);
    auto* const slot = *reinterpret_cast<u8* const*>(slot_address);
    auto* const target = *reinterpret_cast<u8* const*>(slot + 8);
    auto* const floats = reinterpret_cast<f32*>(target + 0xCC);
    floats[0] = sx;
    floats[1] = sy;
    floats[2] = sz;
    floats[3] = sw;
    *reinterpret_cast<void**>(target + 0x100) = engine_func_002c2be8(floats);
}
// DECOMP_FUNC(0x002638dc, 32)
void PlaceWin_Dismiss() {
    auto* const work = *reinterpret_cast<u8**>(0x0043E140);
    *reinterpret_cast<u32*>(work + 8) = 3;
    camp_func_002bf030(work + 0x34, 1);
}

// DECOMP_FUNC(0x002638fc, 20)
void PlaceWin_SetVisible(u8 visible) {
    // The ROM context at 0x0043DA28 holds the object pointer at +4; its
    // visibility byte is at +0x4C5. The ROM performs no null check.
    register u8** context_slot asm("r1") =
        reinterpret_cast<u8**>(0x0043DA28);
    asm volatile("" : "+r"(context_slot));
    auto* context = context_slot[1];
    context[0x4C5] = visible;
}

// DECOMP_FUNC(0x00263910, 60)
bool PlaceWin_CheckState(const void* context) {
    const auto* bytes = static_cast<const u8*>(context);
    if (script_vm_func_0025a274(
            *reinterpret_cast<const s32*>(bytes + 8)) == 0) {
        return false;
    }
    if (ui_func_002d569c(*reinterpret_cast<const s32*>(bytes + 8)) == 0) {
        return false;
    }
    return ui_func_002d56fc(*reinterpret_cast<const s32*>(bytes + 8)) != 0;
}

// DECOMP_FUNC(0x0026394c, 44)
bool PlaceWin_IsActive(const void* context) {
    auto* object = *reinterpret_cast<const u8* const*>(
        static_cast<const u8*>(context) + 4);
    if (object == nullptr) {
        return true;
    }
    const f32 first = *reinterpret_cast<const f32*>(object + 0x38);
    const f32 second = *reinterpret_cast<const f32*>(object + 0x48);
    return !(second > first);
}

// DECOMP_FUNC(0x00263978, 124)
void PlaceWin_ShowMessage(const char* msg) {
    PlaceWinWork* work = g_PlaceWinWork;
    work->state = 1;
    work->flags = 1;
    UiAnimSprite_SetAnim(&work->panel_sprite, 0, 0);
    AsdMem_Zero(work->message, 0x80);
    u32 length = 0;
    while (length < 0x80 && msg[length] != 0) {
        if (msg[length + 1] == 0) {
            length += 1;
            break;
        }
        length += 2;
    }
    AsdString_Strcpy(work->message, msg);
}

extern "C" {
    void PlaceWin_Calc_0032ac30(void*);                                                     // 0x0032ac30
    void PlaceWin_Draw_0032aa84(void*);                                                     // 0x0032aa84
    void camp_func_0029c56c(void*, s32);                                                    // 0x0029c56c
    void camp_func_002a06dc(void*, s32);                                                    // 0x002a06dc
    void engine_func_002a58ec(void*, s32, f32, f32);                                        // 0x002a58ec
    void script_vm_func_002d5780(void*, f32);                                               // 0x002d5780
    void script_vm_func_002e11bc(void*, s32);                                               // 0x002e11bc
    void func_00151404();                                                                   // 0x00151404
    void func_0015555c();                                                                   // 0x0015555c
    extern const u8 g_PlaceWinSpriteTable_00403acc;                                         // 0x00403acc
    extern const u8 g_PlaceWinSpriteTable_00403ae4;                                         // 0x00403ae4
    extern const u8 g_PlaceWinSpriteTable_00403afc;                                         // 0x00403afc
}

// DECOMP_FUNC(0x002639f4, 448)
void PlaceWin_Init() {
    static constexpr u32 kWorkSize = 0x140;
    static constexpr u32 kCalcTag = 1;
    static constexpr u32 kDrawUpLeftTag = 0x81;
    static constexpr u32 kDrawUpRightTag = 0xDF;
    static constexpr s32 kSpriteType = 0x0E;
    static constexpr s32 kSpriteId = 0x87;

    u8* work = reinterpret_cast<u8*>(g_PlaceWinWork);
    if (work == nullptr) {
        work = static_cast<u8*>(AsdMem_Alloc(0x100, 0x100, 0, kWorkSize, 1));
        g_PlaceWinWork = reinterpret_cast<PlaceWinWork*>(work);
    }

    AsdMem_Zero(work, kWorkSize);

    void* const calc_task = AsdTask_CreateCalc(
        "PlaceWin Calc",
        kCalcTag,
        0,
        0,
        PlaceWin_Calc_0032ac30,
        0,
        0);
    *reinterpret_cast<void**>(work) = calc_task;

    AsdTask_CreateDraw(
        "PlaceWin DrawUpLeft",
        kDrawUpLeftTag,
        0,
        0,
        PlaceWin_Draw_0032aa84,
        0,
        0,
        calc_task);

    AsdTask_CreateDraw(
        "PlaceWin DrawUpRight",
        kDrawUpRightTag,
        0,
        0,
        PlaceWin_Draw_0032aa84,
        0,
        0,
        calc_task);

    u8* const bound_work = reinterpret_cast<u8*>(g_PlaceWinWork);
    UiSpriteGroup* const sprite_group = reinterpret_cast<UiSpriteGroup*>(bound_work + 0x14);
    UiAnimSprite* const panel_sprite = reinterpret_cast<UiAnimSprite*>(bound_work + 0x34);

    UiSpriteGroup_Init(sprite_group);
    UiSpriteGroup_BindTable(
        sprite_group,
        SpriteTableWord(&g_PlaceWinSpriteTable_00403acc),
        0x18,
        SpriteTableWord(&g_PlaceWinSpriteTable_00403ae4),
        0x18,
        0,
        0,
        0,
        0,
        SpriteTableWord(&g_PlaceWinSpriteTable_00403afc),
        0x70);

    using PlaceWinSetupEx = void (*)(UiAnimSprite*, s32, s32, UiSpriteGroup*, u32, f32);
    reinterpret_cast<PlaceWinSetupEx>(UiAnimSprite_SetupEx)(
        panel_sprite,
        kSpriteType,
        kSpriteId,
        sprite_group,
        1,
        1.0f);

    using PlaceWinSetAnim = void (*)(UiAnimSprite*, s32);
    reinterpret_cast<PlaceWinSetAnim>(UiAnimSprite_SetAnim)(
        panel_sprite,
        0);
}
#if 0
// Partial semantic draft retained for reconstruction; not compiled.
[[maybe_unused]] static void PlaceWin_Init_Draft() {
    PlaceWinWork* work = g_PlaceWinWork;
    if (work == nullptr) {
        work = static_cast<PlaceWinWork*>(
            AsdMem_Alloc(0x100, 0x100, 0, sizeof(PlaceWinWork), 1));
        g_PlaceWinWork = work;
    }

    AsdMem_Zero(work, sizeof(PlaceWinWork));

    work->calc_task = AsdTask_CreateCalc("PlaceWin Calc", 1, 0, 0,
                                         PlaceWin_Calc, 0, 0);
    work->draw_up_left = AsdTask_CreateDraw("PlaceWin DrawUpLeft", 0x81, 0, 0,
                                            nullptr, 0, 0, work->calc_task);
    work->draw_up_right = AsdTask_CreateDraw("PlaceWin DrawUpRight", 0xDF, 0, 0,
                                             nullptr, 0, 0, work->calc_task);

    UiSpriteGroup_Init(&work->sprite_group);
    UiSpriteGroup_BindTable(&work->sprite_group,
                            SpriteTableWord(g_PlaceWinSpriteTable - 0x30), 0x18,
                            SpriteTableWord(g_PlaceWinSpriteTable - 0x18), 0x18,
                            0, 0, 0, 0,
                            SpriteTableWord(g_PlaceWinSpriteTable), 0x70);

    UiAnimSprite_SetupEx(&work->panel_sprite, 0x0E, 0x87, 0, &work->sprite_group, 1, 1.0f);
    UiAnimSprite_SetAnim(&work->panel_sprite, 0, 0);
}
#endif

// DECOMP_FUNC(0x00263bb4, 660)
void PlaceWin_Calc(void* arg, s32 mode) {
    static constexpr f32 kDefaultFade = 0.3f;
    static constexpr f32 kFocusScale = 0.6f;
    static constexpr f32 kFocusPos = 0.1f;

    auto* const work = static_cast<u8*>(arg);
    const s32 prev_mode = *reinterpret_cast<const s32*>(work + 0x550);
    if (prev_mode == mode) {
        return;
    }

    auto get_slot_34 = [work](s32 idx) -> void* {
        return *reinterpret_cast<void**>(work + idx * 4 + 0x34);
    };
    auto get_slot_3c = [work](s32 idx) -> u8* {
        return *reinterpret_cast<u8**>(work + idx * 4 + 0x3C);
    };
    auto get_sub = [&](s32 idx) -> u8* {
        return *reinterpret_cast<u8**>(get_slot_3c(idx) + 0x04);
    };

    if (prev_mode != -1) {
        camp_func_0029c56c(get_slot_3c(prev_mode), 0);
        script_vm_func_002d5780(
            get_slot_34(*reinterpret_cast<const s32*>(work + 0x560)), 0.0f);
        u8* const prev_sub = get_sub(*reinterpret_cast<const s32*>(work + 0x550));
        *reinterpret_cast<f32*>(prev_sub + 0x40) = 0.0f;
        prev_sub[0x58] = 1;
        using VtableFn = void (*)(void*);
        auto* const vtable = *reinterpret_cast<VtableFn* const*>(prev_sub);
        vtable[0x20 / 4](prev_sub);
    }

    *reinterpret_cast<s32*>(work + 0x550) = mode;
    camp_func_002a06dc(get_slot_3c(mode), 0);
    engine_func_002a58ec(
        get_slot_34(*reinterpret_cast<const s32*>(work + 0x560)), mode, 0.0f, 0.0f);
    script_vm_func_002d5780(
        get_slot_34(*reinterpret_cast<const s32*>(work + 0x560)), 1.0f);

    u8* const cur_sub = get_sub(*reinterpret_cast<const s32*>(work + 0x550));
    using BlendFn = f32 (*)(void*, f32, f32);
    const auto blend_fn =
        *reinterpret_cast<const BlendFn*>(cur_sub + 0x4C);
    const f32 blend_res = blend_fn(
        *reinterpret_cast<void* const*>(cur_sub + 0x50),
        *reinterpret_cast<const f32*>(cur_sub + 0x44),
        *reinterpret_cast<const f32*>(cur_sub + 0x48));
    *reinterpret_cast<u32*>(cur_sub + 0x3C) =
        *reinterpret_cast<const u32*>(cur_sub + 0x38);
    *reinterpret_cast<f32*>(cur_sub + 0x38) = blend_res;
    cur_sub[0x58] = 1;

    u8* const sub_after = get_sub(*reinterpret_cast<const s32*>(work + 0x550));
    *reinterpret_cast<f32*>(sub_after + 0x40) = 1.0f;

    if (mode == 0 || mode == 2) {
        script_vm_func_002e11bc(
            get_slot_34(*reinterpret_cast<const s32*>(work + 0x560)),
            mode == 2 ? 1 : 0);
        u8* const mode_sub = get_sub(*reinterpret_cast<const s32*>(work + 0x550));
        *reinterpret_cast<void**>(mode_sub + 0x4C) = reinterpret_cast<void*>(
            mode == 2 ? &func_00151404 : &func_0015555c);
        mode_sub[0x58] = 1;
        PlaceWin_SetScale(0, 0, 1.0f, 1.0f, 1.0f, 1.0f);
        PlaceWin_SetPos(0, 0, kDefaultFade, kDefaultFade, kDefaultFade);
    } else if (mode == 1) {
        script_vm_func_002e11bc(
            get_slot_34(*reinterpret_cast<const s32*>(work + 0x560)), 0);
        u8* const mode_sub = get_sub(*reinterpret_cast<const s32*>(work + 0x550));
        *reinterpret_cast<void**>(mode_sub + 0x4C) =
            reinterpret_cast<void*>(&func_0015555c);
        mode_sub[0x58] = 1;
        PlaceWin_SetScale(0, 0, kFocusScale, kFocusScale, kFocusScale, 1.0f);
        PlaceWin_SetPos(0, 0, kFocusPos, kFocusPos, kFocusPos);
    }
}
#if 0
// Partial semantic draft retained for reconstruction; not compiled.
[[maybe_unused]] static void PlaceWin_Calc_Draft(void* arg) {
    (void)arg;
    PlaceWinWork* work = g_PlaceWinWork;
    if (work == nullptr || work->state == 0) {
        return;
    }

    switch (work->state) {
        case 1: // Appearing / Slide-in
            work->state = 2;
            break;
        case 2: // Displaying area banner
            break;
        case 3: // Fade-out / Dismiss
            work->state = 0;
            break;
        default:
            break;
    }
}
#endif

// ============================================================================
// RunWin: Running / Escape Prompt Window (c:\SMT4\XRD686\sdds4\program\font\SearchWin\RunWin.cpp)
// ============================================================================

RunWinWork* g_RunWinWork = nullptr; // 0x0043E158
static const u8 g_RunWinSpriteTable[0x20] = {0};

extern "C" {
    void RunWin_Calc_0018f4ac(void*);                                                       // 0x0018f4ac
    extern const u8 g_RunWinSpriteTable_00403b6c;                                           // 0x00403b6c
    extern const u8 g_RunWinSpriteTable_00403b90;                                           // 0x00403b90
    extern const u8 g_RunWinSpriteTable_00403bb4;                                           // 0x00403bb4
}

// DECOMP_FUNC(0x002027dc, 372)
void RunWin_Init() {
    static constexpr u32 kWorkSize = sizeof(RunWinWork);
    static constexpr u32 kCalcTag = 1;
    static constexpr u32 kDrawDownTag = 0xE9;
    static constexpr s32 kSpriteType = 0x0E;
    static constexpr s32 kSpriteId = 0x87;

    RunWinWork* work = g_RunWinWork;
    if (work == nullptr) {
        work = static_cast<RunWinWork*>(
            AsdMem_Alloc(0x100, 0x100, 0, kWorkSize, 1));
        g_RunWinWork = work;
    }

    AsdMem_Zero(work, kWorkSize);

    work->calc_task = AsdTask_CreateCalc(
        "RunWin Calc",
        kCalcTag,
        0,
        0,
        RunWin_Calc_0018f4ac,
        0,
        0);

    AsdTask_CreateDraw(
        "RunWin DrawDown",
        kDrawDownTag,
        0,
        0,
        RunWin_DrawDownAndCalc,
        0,
        0,
        work->calc_task);

    UiSpriteGroup_Init(&work->sprite_group);
    UiSpriteGroup_BindTable(
        &work->sprite_group,
        SpriteTableWord(&g_RunWinSpriteTable_00403b6c),
        0x24,
        SpriteTableWord(&g_RunWinSpriteTable_00403b90),
        0x24,
        0,
        0,
        0,
        0,
        SpriteTableWord(&g_RunWinSpriteTable_00403bb4),
        0x70);

    using RunWinSetupEx = void (*)(UiAnimSprite*, s32, s32, UiSpriteGroup*, u32, f32);
    reinterpret_cast<RunWinSetupEx>(UiAnimSprite_SetupEx)(
        &work->panel_sprite,
        kSpriteType,
        kSpriteId,
        &work->sprite_group,
        1,
        1.0f);

    using RunWinSetAnim = void (*)(UiAnimSprite*, s32);
    reinterpret_cast<RunWinSetAnim>(UiAnimSprite_SetAnim)(
        &work->panel_sprite,
        0);
}
#if 0
// Partial semantic draft retained for reconstruction; not compiled.
[[maybe_unused]] static void RunWin_Init_Draft() {
    RunWinWork* work = g_RunWinWork;
    if (work == nullptr) {
        work = static_cast<RunWinWork*>(
            AsdMem_Alloc(0x100, 0x100, 0, sizeof(RunWinWork), 1));
        g_RunWinWork = work;
    }

    AsdMem_Zero(work, sizeof(RunWinWork));

    work->calc_task = AsdTask_CreateCalc("RunWin Calc", 1, 0, 0,
                                         RunWin_DrawDownAndCalc, 0, 0);
    work->draw_down = AsdTask_CreateDraw("RunWin DrawDown", 0xE9, 0, 0,
                                         RunWin_DrawDownAndCalc, 0, 0, work->calc_task);

    UiSpriteGroup_Init(&work->sprite_group);
    UiSpriteGroup_BindTable(&work->sprite_group,
                            SpriteTableWord(g_RunWinSpriteTable - 0x48), 0x24,
                            SpriteTableWord(g_RunWinSpriteTable - 0x24), 0x24,
                            0, 0, 0, 0,
                            SpriteTableWord(g_RunWinSpriteTable), 0x70);

    UiAnimSprite_SetupEx(&work->panel_sprite, 0x0E, 0x87, 0, &work->sprite_group, 1, 1.0f);
    UiAnimSprite_SetAnim(&work->panel_sprite, 0, 0);
}
#endif

extern "C" {
    void  UiGpu_SetAlphaBlend(f32 alpha);                                                   // 0x002bf710
    void  func_002bf558(s32 type, s32 id, s32 sub_id, s32 x, s32 y, s32 flag);              // 0x002bf558
    void* battle_func_002c5fa4(s32 a0, s32 a1, s32 a2);                                     // 0x002c5fa4
    void  ui_func_002be77c(s32 align, u32 color, const char* text,
                           f32 x, f32 y, f32 scale, f32 z, f32 alpha);                      // 0x002be77c
    void  script_vm_func_002bef14();                                                        // 0x002bef14
}

// DECOMP_FUNC(0x0018f178, 988)
void RunWin_DrawDownAndCalc(void*) {
    static constexpr f32 kParallaxScale = 0.27f;
    static constexpr f32 kTextScale = 0.56640625f;
    static constexpr u32 kTextColor = 0xF49800FFu;

    auto* const work = reinterpret_cast<u8*>(g_RunWinWork);
    if (*reinterpret_cast<const u32*>(work + 0x08) == 0 || work[0x14] == 0) {
        return;
    }

    auto sync_render_mode = [](u8* mode_stack, void* old_mode, void* target_mode) {
        if (mode_stack[0x18] != 0 || old_mode != target_mode) {
            using ModeCb = void (*)(void*);
            (*reinterpret_cast<const ModeCb*>(mode_stack + 0x1C))(target_mode);
            mode_stack[0x18] = 0;
        }
    };

    UiGpu_BeginPass(g_AsdGpuState);
    UiSprite_DrawPanelDirect(2, 0x0E, 0x14F, 0, 0, 0x6D);

    const s32 base_x = ui_func_002bef7c(work + 0x38) +
                       static_cast<s32>(UiGpu_TransformCoord(g_AsdGpuState, kParallaxScale));
    const s32 base_y = ui_func_002bef70(work + 0x38);

    UiGpu_SetAlphaBlend(*reinterpret_cast<const f32*>(work + 0x58));
    func_002bf558(2, 0x0E, 0x13, base_x, base_y, 0x6E);

    void* const new_mode = battle_func_002c5fa4(6, 1, 0);
    auto* const mode_stack = g_AsdGpuState + 0x12AC;
    auto* const mode_idx = reinterpret_cast<s32*>(mode_stack);
    auto* const mode_slots = reinterpret_cast<void**>(mode_stack + 0x08);
    const s32 push_idx = *mode_idx;
    void* const prev_mode = mode_slots[push_idx];
    *mode_idx = push_idx + 1;
    mode_slots[push_idx + 1] = new_mode;
    sync_render_mode(mode_stack, prev_mode, new_mode);

    UiSprite_DrawPanelDirect(2, 0x0E, 0x150, base_x, 0, 0x6F);
    UiSprite_DrawPanelDirect(2, 0x0E, 0x151, base_x, 0, 0x6F);

    auto* const pop_stack = g_AsdGpuState + 0x12AC;
    auto* const pop_idx = reinterpret_cast<s32*>(pop_stack);
    auto* const pop_slots = reinterpret_cast<void**>(pop_stack + 0x08);
    const s32 cur_idx = *pop_idx;
    void* const popped_mode = pop_slots[cur_idx];
    *pop_idx = cur_idx - 1;
    void* const restored_mode = pop_slots[cur_idx - 1];
    sync_render_mode(pop_stack, popped_mode, restored_mode);

    const u8* const text_layout = camp_func_002bf6d0(0x0E, 0x153);
    const f32 tx = static_cast<f32>(base_x - 0x0E + *reinterpret_cast<const s16*>(text_layout + 0x08));
    const f32 ty = static_cast<f32>(base_y + *reinterpret_cast<const s16*>(text_layout + 0x0A));
    ui_func_002be77c(
        4, kTextColor, reinterpret_cast<const char*>(work + 0xC4),
        tx, ty, kTextScale, 0.0f, *reinterpret_cast<const f32*>(work + 0x58));

    const s32 phase = *reinterpret_cast<const s32*>(work + 0x10) / 5;
    const s32 a = phase % 8;
    const s32 b = (a + 7) % 8;
    const s32 c = (phase + 4) % 8;
    const s32 d = (c + 7) % 8;

    for (s32 row = 0; row < 3; ++row) {
        for (s32 col = 0; col < 3; ++col) {
            const s32 idx = row * 3 + col;
            const u8* const cell_layout = camp_func_002bf6d0(0x0E, 0x157 + idx);
            s32 sub_id = 0x154;
            if (idx == a || idx == c) {
                sub_id = 0x155;
            } else if (idx == b || idx == d) {
                sub_id = 0x156;
            }
            UiSprite_DrawPanelDirect(
                2, 0x0E, sub_id,
                base_x + *reinterpret_cast<const s16*>(cell_layout + 0x08),
                *reinterpret_cast<const s16*>(cell_layout + 0x0A),
                0x6F);
        }
    }

    script_vm_func_002bef14();
    UiGpu_SetAlphaBlend(1.0f);
}

// ============================================================================
// SearchWin: Demonica Radar & Relic Search Window (c:\SMT4\XRD686\sdds4\program\font\SearchWin\SearchWin.cpp)
// ============================================================================

SearchWinWork* g_SearchWinWork = nullptr; // 0x0043E170

// DECOMP_FUNC(0x002cecd8, 52)
void SearchWin_IsActive() {
    auto* context = *reinterpret_cast<u8**>(0x0043E2AC);
    auto* counter = reinterpret_cast<u16*>(context + 0x66);
    u16 value = *counter;
    if (value < 0x270E) {
        value = static_cast<u16>(value + 1);
        *counter = value;
    }
    if (value >= 0x270E) {
        *counter = 0x270E;
    }
}

// DECOMP_FUNC(0x002ced0c, 28)
bool SearchWin_Dismiss() {
    return *reinterpret_cast<const u8*>(0x0043E311) == 0;
}

extern "C" {
    void SearchWin_Calc_001ad07c(void*);                                                    // 0x001ad07c
    extern const u8 g_SearchWinSpriteTable_00403c24;                                        // 0x00403c24
    extern const u8 g_SearchWinSpriteTable_00403c48;                                        // 0x00403c48
    extern const u8 g_SearchWinSpriteTable_00403c6c;                                        // 0x00403c6c
}

// DECOMP_FUNC(0x002ced28, 348)
void SearchWin_Init() {
    static constexpr u32 kWorkSize = sizeof(SearchWinWork);
    static constexpr u32 kCalcTag = 1;
    static constexpr u32 kDrawUpLeftTag = 0x81;
    static constexpr u32 kDrawUpRightTag = 0xDF;
    static constexpr s32 kSpriteType = 0x0E;
    static constexpr s32 kSpriteId = 0x87;

    SearchWinWork* work = g_SearchWinWork;
    if (work == nullptr) {
        work = static_cast<SearchWinWork*>(
            AsdMem_Alloc(0x100, 0x100, 0, kWorkSize, 1));
        g_SearchWinWork = work;
    }

    AsdMem_Zero(work, kWorkSize);

    work->calc_task = AsdTask_CreateCalc(
        "SearchWin Calc",
        kCalcTag,
        0,
        0,
        SearchWin_Calc_001ad07c,
        0,
        0);

    AsdTask_CreateDraw(
        "SearchWin DrawUpLeft",
        kDrawUpLeftTag,
        0,
        0,
        SearchWin_DrawUpAndCalc,
        0,
        0,
        work->calc_task);

    AsdTask_CreateDraw(
        "SearchWin DrawUpRight",
        kDrawUpRightTag,
        0,
        0,
        SearchWin_DrawUpAndCalc,
        0,
        0,
        work->calc_task);

    UiSpriteGroup_Init(&work->sprite_group);
    UiSpriteGroup_BindTable(
        &work->sprite_group,
        SpriteTableWord(&g_SearchWinSpriteTable_00403c24),
        0x24,
        SpriteTableWord(&g_SearchWinSpriteTable_00403c48),
        0x24,
        0,
        0,
        0,
        0,
        SpriteTableWord(&g_SearchWinSpriteTable_00403c6c),
        0x70);

    using SearchWinSetupEx = void (*)(UiAnimSprite*, s32, s32, UiSpriteGroup*, u32, f32);
    reinterpret_cast<SearchWinSetupEx>(UiAnimSprite_SetupEx)(
        &work->panel_sprite,
        kSpriteType,
        kSpriteId,
        &work->sprite_group,
        1,
        1.0f);

    using SearchWinSetAnim = void (*)(UiAnimSprite*, s32);
    reinterpret_cast<SearchWinSetAnim>(UiAnimSprite_SetAnim)(
        &work->panel_sprite,
        0);
}
#if 0
// Partial semantic draft retained for reconstruction; not compiled.
[[maybe_unused]] static void SearchWin_Init_Draft() {
    SearchWinWork* work = g_SearchWinWork;
    if (work == nullptr) {
        work = static_cast<SearchWinWork*>(
            AsdMem_Alloc(0x100, 0x100, 0, sizeof(SearchWinWork), 1));
        g_SearchWinWork = work;
    }

    AsdMem_Zero(work, sizeof(SearchWinWork));

    work->calc_task = AsdTask_CreateCalc("SearchWin Calc", 1, 0, 0,
                                         SearchWin_DrawUpAndCalc, 0, 0);
    AsdTask_CreateDraw("SearchWin DrawUpLeft", 0x81, 0, 0,
                       SearchWin_DrawUpAndCalc, 0, 0, work->calc_task);
    AsdTask_CreateDraw("SearchWin DrawUpRight", 0xDF, 0, 0,
                       SearchWin_DrawUpAndCalc, 0, 0, work->calc_task);

    UiSpriteGroup_Init(&work->sprite_group);
    UiSpriteGroup_BindTable(&work->sprite_group,
                            0x00403C24u, 0x24,
                            0x00403C48u, 0x24,
                            0, 0, 0, 0,
                            0x00403C6Cu, 0x70);

    // The ROM ABI for 0x002BDB2C takes the sprite group in r3; there is no
    // separate fourth integer argument before it. Keep this corrected
    // six-argument view local because other reconstructed call sites still
    // use their current signatures.
    using SearchWinSetupEx = void (*)(UiAnimSprite*, s32, s32,
                                     UiSpriteGroup*, u32, f32);
    reinterpret_cast<SearchWinSetupEx>(UiAnimSprite_SetupEx)(
        &work->panel_sprite, 0x0E, 0x87, &work->sprite_group, 1, 1.0f);
    // 0x002BF030 consumes (sprite, animation); it initializes its two
    // internal search indices itself, so the source frame argument is not
    // present in the ROM ABI.
    using SearchWinSetAnim = void (*)(UiAnimSprite*, s32);
    reinterpret_cast<SearchWinSetAnim>(UiAnimSprite_SetAnim)(
        &work->panel_sprite, 0);
}
#endif

// DECOMP_FUNC(0x001accd4, 1104)
// Boundary-verified ARM-state span; includes its PC-relative literal pool.
__attribute__((naked)) void SearchWin_DrawUpAndCalc(void* arg) {
    asm volatile(
        ".word 0xe92d4ff0\n"
        ".word 0xe24dd014\n"
        ".word 0xe59f036c\n"
        ".word 0xe5904000\n"
        ".word 0xe5940008\n"
        ".word 0xe3500000\n"
        ".word 0x15d40014\n"
        ".word 0x13500000\n"
        ".word 0x0a0000d3\n"
        ".word 0xe59f8354\n"
        ".word 0xe5980000\n"
        ".word 0xeb045ba8\n"
        ".word 0xe5985000\n"
        ".word 0xe3a01000\n"
        ".word 0xe3a00001\n"
        ".word 0xeb046499\n"
        ".word 0xe2855a01\n"
        ".word 0xe2855f93\n"
        ".word 0xe5951000\n"
        ".word 0xe2812001\n"
        ".word 0xe0853101\n"
        ".word 0xe5931008\n"
        ".word 0xe0853102\n"
        ".word 0xe5852000\n"
        ".word 0xe5830008\n"
        ".word 0xe5d52018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000003\n"
        ".word 0xe595101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c50018\n"
        ".word 0xe2840038\n"
        ".word 0xeb044886\n"
        ".word 0xe1a05000\n"
        ".word 0xe5980000\n"
        ".word 0xed9f0aba\n"
        ".word 0xeb0435be\n"
        ".word 0xeebd0ac0\n"
        ".word 0xee100a10\n"
        ".word 0xe0857000\n"
        ".word 0xe2840038\n"
        ".word 0xeb04487a\n"
        ".word 0xe1a06000\n"
        ".word 0xed940a16\n"
        ".word 0xeb044a5f\n"
        ".word 0xe3a00065\n"
        ".word 0xe58d0004\n"
        ".word 0xe1a03007\n"
        ".word 0xe3a02014\n"
        ".word 0xe3a0100e\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d6000\n"
        ".word 0xeb0449e9\n"
        ".word 0xe5985000\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01001\n"
        ".word 0xe3a00006\n"
        ".word 0xeb046477\n"
        ".word 0xe2855a01\n"
        ".word 0xe2855fab\n"
        ".word 0xe5951000\n"
        ".word 0xe2812001\n"
        ".word 0xe0853101\n"
        ".word 0xe5931008\n"
        ".word 0xe0853102\n"
        ".word 0xe5852000\n"
        ".word 0xe5830008\n"
        ".word 0xe5d52018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000003\n"
        ".word 0xe595101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c50018\n"
        ".word 0xe3a00066\n"
        ".word 0xe58d0004\n"
        ".word 0xe1a03007\n"
        ".word 0xe3a02015\n"
        ".word 0xe3a0100e\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d6000\n"
        ".word 0xeb0449cb\n"
        ".word 0xe59f0224\n"
        ".word 0xe5900000\n"
        ".word 0xe2805a01\n"
        ".word 0xe2855fab\n"
        ".word 0xe5950000\n"
        ".word 0xe2401001\n"
        ".word 0xe0852100\n"
        ".word 0xe5920008\n"
        ".word 0xe5851000\n"
        ".word 0xe0851101\n"
        ".word 0xe5d52018\n"
        ".word 0xe5911008\n"
        ".word 0xe3520000\n"
        ".word 0x01500001\n"
        ".word 0x0a000004\n"
        ".word 0xe595201c\n"
        ".word 0xe1a00001\n"
        ".word 0xe12fff32\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c50018\n"
        ".word 0xe59f11dc\n"
        ".word 0xe3a0000e\n"
        ".word 0xeb044a12\n"
        ".word 0xe1d010fa\n"
        ".word 0xe1d000f8\n"
        ".word 0xed942a16\n"
        ".word 0xe0811006\n"
        ".word 0xe0800007\n"
        ".word 0xee001a90\n"
        ".word 0xee000a10\n"
        ".word 0xe59f11b8\n"
        ".word 0xe28420c4\n"
        ".word 0xeddf1a6d\n"
        ".word 0xe3a00004\n"
        ".word 0xeef80ae0\n"
        ".word 0xeeb80ac0\n"
        ".word 0xed9f1a6a\n"
        ".word 0xeb04462e\n"
        ".word 0xe5941010\n"
        ".word 0xe59f01a0\n"
        ".word 0xe3a0a000\n"
        ".word 0xe3a0b06f\n"
        ".word 0xe0c01190\n"
        ".word 0xe1a010c0\n"
        ".word 0xe0410fc0\n"
        ".word 0xe1a01fc0\n"
        ".word 0xe0801ea1\n"
        ".word 0xe3c11007\n"
        ".word 0xe0408001\n"
        ".word 0xe2881007\n"
        ".word 0xe2800004\n"
        ".word 0xe1a02fc1\n"
        ".word 0xe0812ea2\n"
        ".word 0xe3c22007\n"
        ".word 0xe0411002\n"
        ".word 0xe58d1008\n"
        ".word 0xe1a01fc0\n"
        ".word 0xe0801ea1\n"
        ".word 0xe3c11007\n"
        ".word 0xe0409001\n"
        ".word 0xe2890007\n"
        ".word 0xe1a01fc0\n"
        ".word 0xe0801ea1\n"
        ".word 0xe3c11007\n"
        ".word 0xe0400001\n"
        ".word 0xe58d000c\n"
        ".word 0xe3a04000\n"
        ".word 0xe08a608a\n"
        ".word 0xe0865004\n"
        ".word 0xe2851e17\n"
        ".word 0xe3a0000e\n"
        ".word 0xeb0449e1\n"
        ".word 0xe1580005\n"
        ".word 0x11590005\n"
        ".word 0x1a00000a\n"
        ".word 0xe1d010fa\n"
        ".word 0xe59f2110\n"
        ".word 0xe88d0802\n"
        ".word 0xe1d000f8\n"
        ".word 0xe3a0100e\n"
        ".word 0xe0803007\n"
        ".word 0xe3a00002\n"
        ".word 0xeb04493a\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000013\n"
        ".word 0xe59d1008\n"
        ".word 0xe1510005\n"
        ".word 0x159d100c\n"
        ".word 0x11510005\n"
        ".word 0xe1d010fa\n"
        ".word 0xe88d0802\n"
        ".word 0xe1d000f8\n"
        ".word 0xe0803007\n"
        ".word 0x1a000006\n"
        ".word 0xe59f20c8\n"
        ".word 0xe3a0100e\n"
        ".word 0xe3a00002\n"
        ".word 0xeb04492a\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000003\n"
        ".word 0xe3a02f55\n"
        ".word 0xe3a0100e\n"
        ".word 0xe3a00002\n"
        ".word 0xeb044923\n"
        ".word 0xe2844001\n"
        ".word 0xe3540003\n"
        ".word 0xbaffffd6\n"
        ".word 0xe28aa001\n"
        ".word 0xe35a0003\n"
        ".word 0xbaffffd1\n"
        ".word 0xeb0447c9\n"
        ".word 0xed9f0a21\n"
        ".word 0xe320f000\n"
        ".word 0xeb0449c5\n"
        ".word 0xe59f0054\n"
        ".word 0xe5900000\n"
        ".word 0xe2804a01\n"
        ".word 0xe2844f93\n"
        ".word 0xe5940000\n"
        ".word 0xe0841100\n"
        ".word 0xe2400001\n"
        ".word 0xe5911008\n"
        ".word 0xe5840000\n"
        ".word 0xe0840100\n"
        ".word 0xe5d42018\n"
        ".word 0xe5900008\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000003\n"
        ".word 0xe594101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c40018\n"
        ".word 0xe3a00000\n"
        ".word 0xe28dd014\n"
        ".word 0xe8bd8ff0\n"
        ".word 0x0043e170\n"
        ".word 0x0044ea00\n"
        ".word 0x3e8a3d71\n"
        ".word 0x0000016f\n"
        ".word 0xf49800ff\n"
        ".word 0x00000000\n"
        ".word 0x3f110000\n"
        ".word 0x66666667\n"
        ".word 0x00000155\n"
        ".word 0x00000156\n"
        ".word 0x3f800000\n"
        ".word 0xe59f009c\n"
        ".word 0xe92d4070\n"
        ".word 0xe3a05000\n"
        ".word 0xe3a06004\n"
        ".word 0xe5904000\n"
        ".word 0xe5940008\n"
        ".word 0xe3500004\n"
        ".word 0x379ff100\n"
        ".word 0xea000016\n"
        ".word 0x001ad0fc\n"
        ".word 0x001ad0b0\n"
        ".word 0x001ad0d8\n"
        ".word 0x001ad0e8\n"
        ".word 0xe3a01000\n"
        ".word 0xe2840038\n"
        ".word 0xeb043058\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a00000c\n"
        ".word 0xe3a00002\n"
        ".word 0xe5840008\n"
        ".word 0xe5845010\n"
        ".word 0xea000008\n"
        ".word 0xe594000c\n"
        ".word 0xe3500003\n"
        ".word 0x05840008\n"
        ".word 0xea000004\n"
        ".word 0xe2840038\n"
        ".word 0xeb044a3f\n"
        ".word 0xe3500000\n"
        ".word 0x15c45014\n"
        ".word 0x15846008\n"
        ".word 0xe5940010\n"
        ".word 0xe2800001\n"
        ".word 0xe5840010\n"
        ".word 0xeb045386\n"
        ".word 0xe3500000\n"
        ".word 0x15c45014\n"
        ".word 0xe3a00000\n"
        ".word 0x15846008\n"
        ".word 0xe8bd8070\n"
        ".word 0x0043e170\n"
    );
}
#if 0
// Partial semantic draft retained for reconstruction; not compiled.
[[maybe_unused]] static void SearchWin_DrawUpAndCalc_Draft(void* arg) {
    (void)arg;
    SearchWinWork* work = g_SearchWinWork;
    if (work == nullptr || work->state == 0 || !work->visible) {
        return;
    }

    // State machine logic (SearchWin_Calc slice)
    switch (work->state) {
        case 1: // Scanning radar sweep
            if (work->timer > 0) {
                work->timer--;
            } else {
                work->state = 2;
            }
            break;
        case 2: // Target locked / prompt active
            break;
        case 3: // Fade out
            work->state = 0;
            break;
        default:
            break;
    }

    // Upper stereoscopic pass (3D radar prompt)
    UiGpu_BeginPass(g_AsdGpuState);
    UiGpu_SetViewportParams(1, 0);

    auto* layer = reinterpret_cast<u32*>(g_AsdGpuState + 0x124C);
    const u32 old_depth = *layer;
    *layer = old_depth + 1;
    auto* layer_entry = reinterpret_cast<u32*>(g_AsdGpuState + 0x124C + 8);
    layer_entry[*layer] = 1;

    // Stereoscopic parallax shift (0.45f scale for radar reticle)
    const f32 shift = UiGpu_TransformCoord(g_AsdGpuState, 0.45f);
    const s32 base_x = static_cast<s32>(shift);

    UiSprite_DrawPanelDirect(2, 0x0E, 0x06, 200 + base_x, 120, 1);

    if (*layer > 0) {
        *layer = *layer - 1;
    }
}
#endif

} // namespace smt4::ui
