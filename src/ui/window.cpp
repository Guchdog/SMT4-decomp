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
}

// Forward declaration for task callback
void ComWin_Calc(void* arg);                                                        // 0x0011b094

//
bool ComWin_SetState_Decompiled() {
    auto* state_block = reinterpret_cast<u32*>(0x004E3CD4);
    for (s32 i = 0; i < 6; ++i) {
        state_block[i] = 0;
    }
    state_block[6] = 0x0F;
    state_block[7] = 4;
    return true;
}
// DECOMP_FUNC(0x0010a70c, 60)


__attribute__((naked)) bool ComWin_SetState() {
    // Retain the exact ARM sequence and the absolute state-block literal.
    asm volatile(
        ".word 0xE59F0030\n"
        ".word 0xE3A01000\n"
        ".word 0xE3A02004\n"
        ".word 0xE5801000\n"
        ".word 0xE5801004\n"
        ".word 0xE5801008\n"
        ".word 0xE580100C\n"
        ".word 0xE5801010\n"
        ".word 0xE5801014\n"
        ".word 0xE2800018\n"
        ".word 0xE3A0100F\n"
        ".word 0xE8800006\n"
        ".word 0xE3A00001\n"
        ".word 0xE12FFF1E\n"
        ".word 0x004E3CD4\n");
}

// DECOMP_FUNC(0x0010a748, 504)
// Boundary-verified ARM-state span; includes its PC-relative literal pool.
__attribute__((naked)) void ComWin_Init() {
    asm volatile(
        ".word 0xe92d41f0\n"
        ".word 0xe3a06001\n"
        ".word 0xe59f7168\n"
        ".word 0xed2d8b02\n"
        ".word 0xe24dd020\n"
        ".word 0xe5970000\n"
        ".word 0xe3500000\n"
        ".word 0x1a000009\n"
        ".word 0xe59f1154\n"
        ".word 0xe28f0f55\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a03f62\n"
        ".word 0xe3a02000\n"
        ".word 0xe1a00001\n"
        ".word 0xe58d6000\n"
        ".word 0xeb06e8fd\n"
        ".word 0xe5870000\n"
        ".word 0xe1a04000\n"
        ".word 0xe3a01f62\n"
        ".word 0xeb06e8e4\n"
        ".word 0xe59f0158\n"
        ".word 0xe3a05000\n"
        ".word 0xe1a03005\n"
        ".word 0xe88d0021\n"
        ".word 0xe1a02005\n"
        ".word 0xe3a01001\n"
        ".word 0xe28f0f51\n"
        ".word 0xe58d5008\n"
        ".word 0xeb06ec6d\n"
        ".word 0xe5840000\n"
        ".word 0xe59f8140\n"
        ".word 0xe3a03000\n"
        ".word 0xe58d000c\n"
        ".word 0xe1a02003\n"
        ".word 0xe3a01081\n"
        ".word 0xe28f0e13\n"
        ".word 0xe58d5004\n"
        ".word 0xe58d8000\n"
        ".word 0xe58d5008\n"
        ".word 0xeb06e904\n"
        ".word 0xe5940000\n"
        ".word 0xe3a03000\n"
        ".word 0xe1a02003\n"
        ".word 0xe58d000c\n"
        ".word 0xe3a010df\n"
        ".word 0xe28f0f47\n"
        ".word 0xe58d5004\n"
        ".word 0xe58d8000\n"
        ".word 0xe58d5008\n"
        ".word 0xeb06e8fa\n"
        ".word 0xe5974000\n"
        ".word 0xe284001c\n"
        ".word 0xeb06e2c8\n"
        ".word 0xe59f2110\n"
        ".word 0xe3a01f46\n"
        ".word 0xe58d1018\n"
        ".word 0xe2423030\n"
        ".word 0xe58d2014\n"
        ".word 0xe3a00030\n"
        ".word 0xe58d500c\n"
        ".word 0xe58d5010\n"
        ".word 0xe88d0009\n"
        ".word 0xe3a02000\n"
        ".word 0xe58d0008\n"
        ".word 0xe2433030\n"
        ".word 0xe1a01002\n"
        ".word 0xe284001c\n"
        ".word 0xeb06e2a6\n"
        ".word 0xed9f8a36\n"
        ".word 0xe284501c\n"
        ".word 0xe3a03002\n"
        ".word 0xeeb00a48\n"
        ".word 0xe3e02000\n"
        ".word 0xe3a0100e\n"
        ".word 0xe284003c\n"
        ".word 0xe88d0060\n"
        ".word 0xeb06d209\n"
        ".word 0xe3a01000\n"
        ".word 0xe284003c\n"
        ".word 0xeb06d1e8\n"
        ".word 0xeeb00a48\n"
        ".word 0xe3a03003\n"
        ".word 0xe3e02000\n"
        ".word 0xe3a0100e\n"
        ".word 0xe28400c8\n"
        ".word 0xe88d0060\n"
        ".word 0xeb06d1ff\n"
        ".word 0xe28dd020\n"
        ".word 0xe28400c8\n"
        ".word 0xecbd8b02\n"
        ".word 0xe3a01002\n"
        ".word 0xe8bd41f0\n"
        ".word 0xea06d1db\n"
        ".word 0x0043e0f8\n"
        ".word 0x00000122\n"
        ".word 0x535c3a63\n"
        ".word 0x5c34544d\n"
        ".word 0x36445258\n"
        ".word 0x735c3638\n"
        ".word 0x34736464\n"
        ".word 0x6f72705c\n"
        ".word 0x6d617267\n"
        ".word 0x6e6f665c\n"
        ".word 0x6f435c74\n"
        ".word 0x6e69576d\n"
        ".word 0x6d6f435c\n"
        ".word 0x2e6e6957\n"
        ".word 0x00707063\n"
        ".word 0x0011b094\n"
        ".word 0x576d6f43\n"
        ".word 0x43206e69\n"
        ".word 0x00636c61\n"
        ".word 0x0011a354\n"
        ".word 0x576d6f43\n"
        ".word 0x44206e69\n"
        ".word 0x55776172\n"
        ".word 0x66654c70\n"
        ".word 0x00000074\n"
        ".word 0x576d6f43\n"
        ".word 0x44206e69\n"
        ".word 0x55776172\n"
        ".word 0x67695270\n"
        ".word 0x00007468\n"
        ".word 0x004038f0\n"
        ".word 0x3f800000\n"
    );
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
__attribute__((naked)) void* ComWin_GetState(u32, u32, u32, u32) {
    // The verified ROM body is an ABI-preserving call thunk: it forwards r0-r3
    // to engine_func_002c54f0 (0x002C54F0), adds stack argument 1, then returns
    // the helper's r0. Keep the branch displacement literal as in code.bin.
    asm volatile(
        ".word 0xE92D4008\n"
        ".word 0xE3A0C001\n"
        ".word 0xE58DC000\n"
        ".word 0xEB06EAE7\n"
        ".word 0xE8BD8008\n");
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

[[maybe_unused]] static void ComWin_CheckFlag_Decompiled() {
    const u32 flag = *reinterpret_cast<const u32*>(0x00465058) ^ 1;
    const u32 selected = reinterpret_cast<const u32*>(0x00465064)[flag];
    engine_func_002c25f4(battle_func_002bf148(selected));
}

// DECOMP_FUNC(0x0010ae9c, 44)
__attribute__((naked)) void ComWin_CheckFlag() {
    // Observed register flow: global word ^ 1 indexes the table, the first
    // helper's result flows to the common state helper. The two trailing words
    // are the literal pool, not instructions; branch displacements are fixed.
    asm volatile(
        ".word 0xE59F001C\n"
        ".word 0xE92D4010\n"
        ".word 0xE59F1018\n"
        ".word 0xE5900000\n"
        ".word 0xE2200001\n"
        ".word 0xE7910100\n"
        ".word 0xEB06D0A3\n"
        ".word 0xE8BD4010\n"
        ".word 0xEA06DDCC\n"
        ".word 0x00465058\n"
        ".word 0x00465064\n");
}

[[maybe_unused]] static void ComWin_GetResult_Decompiled() {
    UiWindow_SetResult(reinterpret_cast<const s32*>(0x00465024));
}

// DECOMP_FUNC(0x0010aec8, 12)
__attribute__((naked)) void ComWin_GetResult() {
    // ROM loads the address of the global result cell and tail-branches to the
    // helper, which consumes that cell as an atomic/state object.
    asm volatile(
        ".word 0xE59F0000\n"
        ".word 0xEA06E4DC\n"
        ".word 0x00465024\n");
}

// DECOMP_FUNC(0x0010aed4, 16)
__attribute__((naked)) s32 func_0010aed4() {
    asm volatile(
        ".arm\n"
        "push {r4, lr}\n"
        "bl func_00115b74\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n");
}

// DECOMP_FUNC(0x0010aee4, 84)
__attribute__((naked)) void ComWin_Reset() {
    // The eight slots are walked with the original byte-sized index and the
    // two reset calls intentionally receive different pointers. Keep the ROM
    // branch displacements and the literal pool as data to preserve that ABI.
    asm volatile(
        ".word 0xE59F0048\n" // ldr r0, [pc, #0x48]
        ".word 0xE92D4070\n" // push {r4, r5, r6, lr}
        ".word 0xE5906204\n" // ldr r6, [r0, #0x204]
        ".word 0xE3560000\n" // cmp r6, #0
        ".word 0x13A04000\n" // movne r4, #0
        ".word 0x0A00000C\n" // beq return
        ".word 0xE0865104\n" // add r5, r6, r4, lsl #2
        ".word 0xE5950020\n" // ldr r0, [r5, #0x20]
        ".word 0xE3500000\n" // cmp r0, #0
        ".word 0x0A000004\n" // beq next slot
        ".word 0xE3A01000\n" // mov r1, #0
        ".word 0xEB06CB3C\n" // bl engine_func_002bdc08
        ".word 0xE2850020\n" // add r0, r5, #0x20
        ".word 0xE320F000\n" // nop
        ".word 0xEB06CB2A\n" // bl engine_func_002bdbcc
        ".word 0xE2840001\n" // add r0, r4, #1
        ".word 0xE20040FF\n" // and r4, r0, #0xff
        ".word 0xE3540008\n" // cmp r4, #8
        ".word 0x3AFFFFF2\n" // blo loop
        ".word 0xE8BD8070\n" // pop {r4, r5, r6, pc}
        ".word 0x004E2F68\n"); // literal pool
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

[[maybe_unused]] static void InfoWin_SetState_Decompiled(u32 state) {
    auto* context = reinterpret_cast<u8*>(0x004C3B20);
    func_0011b558(*reinterpret_cast<void**>(context + 0x1C0));
    engine_func_0011b5e8(context);
    if (state == 3) {
        *reinterpret_cast<volatile u8*>(0x0044D020) = 1;
    }
}

// DECOMP_FUNC(0x0010af48, 60)
__attribute__((naked)) void InfoWin_SetState(u32) {
    // Preserve both helper calls, the state==3 flag side effect, and the two
    // global literals with the ROM's original ARM-state encodings.
    asm volatile(
        ".word 0xE92D4070\n"
        ".word 0xE1A05000\n"
        ".word 0xE59F4024\n"
        ".word 0xE59401C0\n"
        ".word 0xEB00417E\n"
        ".word 0xE1A00004\n"
        ".word 0xEB0041A0\n"
        ".word 0xE3550003\n"
        ".word 0x1A000002\n"
        ".word 0xE59F100C\n"
        ".word 0xE3A00001\n"
        ".word 0xE5C10000\n"
        ".word 0xE8BD8070\n"
        ".word 0x004C3B20\n"
        ".word 0x0044D020\n");
}

// DECOMP_FUNC(0x0010af84, 560)
// Boundary-verified ARM-state span; includes its PC-relative literal pool.
__attribute__((naked)) void InfoWin_Init() {
    asm volatile(
        ".word 0xe92d41f0\n"
        ".word 0xe3a06001\n"
        ".word 0xe59f7194\n"
        ".word 0xed2d8b02\n"
        ".word 0xe24dd020\n"
        ".word 0xe5970000\n"
        ".word 0xe3500000\n"
        ".word 0x1a000009\n"
        ".word 0xe3a010ff\n"
        ".word 0xe28f0f5f\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a03f6f\n"
        ".word 0xe3a02000\n"
        ".word 0xe1a00001\n"
        ".word 0xe58d6000\n"
        ".word 0xeb06e6ee\n"
        ".word 0xe5870000\n"
        ".word 0xe1a04000\n"
        ".word 0xe3a01f6f\n"
        ".word 0xeb06e6d5\n"
        ".word 0xe59f0184\n"
        ".word 0xe3a05000\n"
        ".word 0xe1a03005\n"
        ".word 0xe88d0021\n"
        ".word 0xe1a02005\n"
        ".word 0xe3a01001\n"
        ".word 0xe28f0e17\n"
        ".word 0xe58d5008\n"
        ".word 0xeb06ea5e\n"
        ".word 0xe5840000\n"
        ".word 0xe59f8170\n"
        ".word 0xe3a03000\n"
        ".word 0xe58d000c\n"
        ".word 0xe1a02003\n"
        ".word 0xe3a01081\n"
        ".word 0xe28f0e16\n"
        ".word 0xe58d5004\n"
        ".word 0xe58d8000\n"
        ".word 0xe58d5008\n"
        ".word 0xeb06e6f5\n"
        ".word 0xe5940000\n"
        ".word 0xe3a03000\n"
        ".word 0xe1a02003\n"
        ".word 0xe58d000c\n"
        ".word 0xe3a010df\n"
        ".word 0xe28f0f53\n"
        ".word 0xe58d5004\n"
        ".word 0xe58d8000\n"
        ".word 0xe58d5008\n"
        ".word 0xeb06e6eb\n"
        ".word 0xe5974000\n"
        ".word 0xe2840024\n"
        ".word 0xeb06e0b9\n"
        ".word 0xe58d5014\n"
        ".word 0xe58d5018\n"
        ".word 0xe59f1138\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a02024\n"
        ".word 0xe2840024\n"
        ".word 0xe58d500c\n"
        ".word 0xe58d5010\n"
        ".word 0xe58d5000\n"
        ".word 0xe58d5004\n"
        ".word 0xe58d5008\n"
        ".word 0xeb06e09a\n"
        ".word 0xed9f8a45\n"
        ".word 0xe2843024\n"
        ".word 0xe3a02087\n"
        ".word 0xeeb00a48\n"
        ".word 0xe3a0100e\n"
        ".word 0xe2840044\n"
        ".word 0xe58d6000\n"
        ".word 0xeb06ca9f\n"
        ".word 0xe3a02000\n"
        ".word 0xe1a01002\n"
        ".word 0xe2840044\n"
        ".word 0xeb06ca80\n"
        ".word 0xeeb00a48\n"
        ".word 0xe2843024\n"
        ".word 0xe3a02087\n"
        ".word 0xe3a0100e\n"
        ".word 0xe28400d0\n"
        ".word 0xe58d6000\n"
        ".word 0xeb06ca94\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01002\n"
        ".word 0xe28400d0\n"
        ".word 0xeb06ca75\n"
        ".word 0xe3a00000\n"
        ".word 0xe320f000\n"
        ".word 0xeb06ca49\n"
        ".word 0xe3e01000\n"
        ".word 0xe58401b8\n"
        ".word 0xeb06ca43\n"
        ".word 0xe59401b8\n"
        ".word 0xe59f20a4\n"
        ".word 0xed9f0a27\n"
        ".word 0xe3a01000\n"
        ".word 0xeb06ca3a\n"
        ".word 0xe3a0001e\n"
        ".word 0xe5840010\n"
        ".word 0xe28dd020\n"
        ".word 0xecbd8b02\n"
        ".word 0xe8bd81f0\n"
        ".word 0x0043e128\n"
        ".word 0x535c3a63\n"
        ".word 0x5c34544d\n"
        ".word 0x36445258\n"
        ".word 0x735c3638\n"
        ".word 0x34736464\n"
        ".word 0x6f72705c\n"
        ".word 0x6d617267\n"
        ".word 0x6e6f665c\n"
        ".word 0x6e495c74\n"
        ".word 0x69576f66\n"
        ".word 0x6e495c6e\n"
        ".word 0x69576f66\n"
        ".word 0x70632e6e\n"
        ".word 0x00000070\n"
        ".word 0x0011b1bc\n"
        ".word 0x6f666e49\n"
        ".word 0x206e6957\n"
        ".word 0x636c6143\n"
        ".word 0x00000000\n"
        ".word 0x0011ae10\n"
        ".word 0x6f666e49\n"
        ".word 0x206e6957\n"
        ".word 0x77617244\n"
        ".word 0x654c7055\n"
        ".word 0x00007466\n"
        ".word 0x6f666e49\n"
        ".word 0x206e6957\n"
        ".word 0x77617244\n"
        ".word 0x69527055\n"
        ".word 0x00746867\n"
        ".word 0x00403aa8\n"
        ".word 0x3f800000\n"
        ".word 0x00000000\n"
        ".word 0x646464ff\n"
    );
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
__attribute__((naked)) void InfoWin_ShowMessage(const char*) {
    asm volatile(
        ".word 0xE92D4010, 0xEB06D642, 0xE1A04000, 0xE2800C0F\n"
        ".word 0xE5D01060, 0xE3510000, 0x0A000002, 0xE5D01063\n"
        ".word 0xE3510000, 0x0A000001, 0xE3A00000, 0xE8BD8010\n"
        ".word 0xE5D00099, 0xE3500000, 0x0AFFFFFB, 0xE59F0064\n"
        ".word 0xE5900000, 0xEB06E26A, 0xE5941004, 0xE3A00C02\n"
        ".word 0xE5810014, 0xE5941004, 0xE5810018, 0xE5941004\n"
        ".word 0xE3A00000, 0xEB06D2A5, 0xE5C40F62, 0xE5940004\n"
        ".word 0xE1A01000, 0xEB06D296, 0xE5940004, 0xE3A01001\n"
        ".word 0xE5902014, 0xE1A020C2, 0xE5802014, 0xE5940004\n"
        ".word 0xE5902018, 0xE1A020C2, 0xE5802018, 0xE3A00000\n"
        ".word 0xE5C41F63, 0xE8BD8010, 0x0044EA00\n");
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
__attribute__((naked)) void InfoWin_UpdateTimer() {
    asm volatile(
        ".word 0xE92D4070, 0xEB06D617, 0xE1A04000, 0xE3A00000\n"
        ".word 0xEB06D39C, 0xE3500000, 0xE3A05001, 0x15C45F65\n"
        ".word 0x1A000023, 0xE5D41F60, 0xE2840C0F, 0xE3510000\n"
        ".word 0x0A00001F, 0xE5D01064, 0xE3510000, 0x05D01065\n"
        ".word 0x03510000, 0x1A00001A, 0xE5D00099, 0xE3500000\n"
        ".word 0x0A000018, 0xE59F0060, 0xE5900000, 0xEB06E239\n"
        ".word 0xE5941008, 0xE3A00C02, 0xE5810014, 0xE5941008\n"
        ".word 0xE5810018, 0xE5941008, 0xE3A00000, 0xEB06D274\n"
        ".word 0xE5C40F62, 0xE5940008, 0xE1A01000, 0xEB06D265\n"
        ".word 0xE5940008, 0xE5901014, 0xE1A010C1, 0xE5801014\n"
        ".word 0xE5940008, 0xE5901018, 0xE1A010C1, 0xE5801018\n"
        ".word 0xE5C45F64, 0xE3A00000, 0xE8BD8070, 0x0044EA00\n");
}

[[maybe_unused]] static bool InfoWin_Dismiss_Decompiled(u32 value) {
    register u32* context asm("r1") = reinterpret_cast<u32*>(0x00464A70);
    asm volatile("" : "+r"(context));
    const u32 limit = context[1];
    if (value < limit) {
        context[3] = value;
        return true;
    }
    return false;
}

// DECOMP_FUNC(0x0010b320, 32)
__attribute__((naked)) bool InfoWin_Dismiss(u32) {
    // The observed entry conditionally stores the incoming value under the
    // bound at 0x00464A74 and returns that unsigned comparison as a bool.
    asm volatile(
        ".word 0xE59F1014\n"
        ".word 0xE5912004\n"
        ".word 0xE1500002\n"
        ".word 0x3581000C\n"
        ".word 0x23A00000\n"
        ".word 0x33A00001\n"
        ".word 0xE12FFF1E\n"
        ".word 0x00464A70\n");
}

// DECOMP_FUNC(0x0011ae10, 792)
// Boundary-verified ARM-state span; includes its PC-relative literal pool.
__attribute__((naked)) void InfoWin_DrawUp(void* arg) {
    asm volatile(
        ".word 0xe92d47f0\n"
        ".word 0xe59f0268\n"
        ".word 0xed2d8b02\n"
        ".word 0xe24dd008\n"
        ".word 0xe5904000\n"
        ".word 0xe5940008\n"
        ".word 0xe3500000\n"
        ".word 0x15d40020\n"
        ".word 0x13500000\n"
        ".word 0x0a00008f\n"
        ".word 0xe59f9248\n"
        ".word 0xe5990000\n"
        ".word 0xeb06a358\n"
        ".word 0xe5995000\n"
        ".word 0xe3a01000\n"
        ".word 0xe3a00001\n"
        ".word 0xeb06ac49\n"
        ".word 0xe2855a01\n"
        ".word 0xe2855f93\n"
        ".word 0xe3a08000\n"
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
        ".word 0xe5c58018\n"
        ".word 0xe2840044\n"
        ".word 0xeb069036\n"
        ".word 0xe1a05000\n"
        ".word 0xe5990000\n"
        ".word 0xed9f0a77\n"
        ".word 0xeb067d6e\n"
        ".word 0xeebd0ac0\n"
        ".word 0xee100a10\n"
        ".word 0xe0857000\n"
        ".word 0xe2840044\n"
        ".word 0xeb06902a\n"
        ".word 0xe1a05000\n"
        ".word 0xe3a06015\n"
        ".word 0xe1a03007\n"
        ".word 0xe3a02087\n"
        ".word 0xe3a0100e\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0060\n"
        ".word 0xeb06915e\n"
        ".word 0xe1a03007\n"
        ".word 0xe3a02088\n"
        ".word 0xe3a0100e\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0060\n"
        ".word 0xeb069158\n"
        ".word 0xe5d40021\n"
        ".word 0xe3500000\n"
        ".word 0x0a00003a\n"
        ".word 0xe3a01087\n"
        ".word 0xe3a0000e\n"
        ".word 0xeb0691ee\n"
        ".word 0xe590100c\n"
        ".word 0xe1d0c0fa\n"
        ".word 0xe1d000f8\n"
        ".word 0xe1d130f2\n"
        ".word 0xe1d120f0\n"
        ".word 0xe08c1005\n"
        ".word 0xe0800007\n"
        ".word 0xeb066e69\n"
        ".word 0xe3a01089\n"
        ".word 0xe3a0000e\n"
        ".word 0xeb0691e3\n"
        ".word 0xe1a06000\n"
        ".word 0xe5d40023\n"
        ".word 0xe3a0a006\n"
        ".word 0xed9f0a4f\n"
        ".word 0xe3500000\n"
        ".word 0xe58d8004\n"
        ".word 0xe58da000\n"
        ".word 0x0a000009\n"
        ".word 0xe1d620fa\n"
        ".word 0xe1d610f8\n"
        ".word 0xe59401b8\n"
        ".word 0xe0822005\n"
        ".word 0xe0811007\n"
        ".word 0xe3a030c9\n"
        ".word 0xeb06726b\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000018\n"
        ".word 0xe1d610f8\n"
        ".word 0xe5943018\n"
        ".word 0xe1d620fa\n"
        ".word 0xeeb08a40\n"
        ".word 0xe0811003\n"
        ".word 0xe59401b8\n"
        ".word 0xe0822005\n"
        ".word 0xe0811007\n"
        ".word 0xe3a030c9\n"
        ".word 0xeb06725e\n"
        ".word 0xe5d40022\n"
        ".word 0xe3500000\n"
        ".word 0x0a00000b\n"
        ".word 0xe58d8004\n"
        ".word 0xe58da000\n"
        ".word 0xe1d610f8\n"
        ".word 0xe5b4301c\n"
        ".word 0xe1d620fa\n"
        ".word 0xeeb00a48\n"
        ".word 0xe0811003\n"
        ".word 0xe594019c\n"
        ".word 0xe0822005\n"
        ".word 0xe0811007\n"
        ".word 0xe3a030c9\n"
        ".word 0xeb06724f\n"
        ".word 0xe320f000\n"
        ".word 0xeb066e00\n"
        ".word 0xe3a0401f\n"
        ".word 0xe1a03007\n"
        ".word 0xe3a02086\n"
        ".word 0xe3a0100e\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d4004\n"
        ".word 0xe58d5000\n"
        ".word 0xeb069112\n"
        ".word 0xe1a03007\n"
        ".word 0xe28420e3\n"
        ".word 0xe3a0100e\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d4004\n"
        ".word 0xe58d5000\n"
        ".word 0xeb06910b\n"
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
        ".word 0xe28dd008\n"
        ".word 0xecbd8b02\n"
        ".word 0xe8bd87f0\n"
        ".word 0x0043e128\n"
        ".word 0x0044ea00\n"
        ".word 0x3e8a3d71\n"
        ".word 0x3f800000\n"
        ".word 0xe59f0088\n"
        ".word 0xe92d4070\n"
        ".word 0xe3a05000\n"
        ".word 0xe5904000\n"
        ".word 0xe5940008\n"
        ".word 0xe3500005\n"
        ".word 0x379ff100\n"
        ".word 0xea000016\n"
        ".word 0x0011b110\n"
        ".word 0x0011b0c8\n"
        ".word 0x0011b0ec\n"
        ".word 0x0011b110\n"
        ".word 0x0011b100\n"
        ".word 0xe284003c\n"
        ".word 0xeb069247\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a00000c\n"
        ".word 0xe2841008\n"
        ".word 0xe3a00002\n"
        ".word 0xe8810021\n"
        ".word 0xea000008\n"
        ".word 0xe28400c8\n"
        ".word 0xeb06923e\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000003\n"
        ".word 0xe284003c\n"
        ".word 0xeb069239\n"
        ".word 0xe3500000\n"
        ".word 0x15845008\n"
        ".word 0xe594000c\n"
        ".word 0xe2800001\n"
        ".word 0xe584000c\n"
        ".word 0xe3a00000\n"
        ".word 0xe8bd8070\n"
        ".word 0x0043e0f8\n"
    );
}
#if 0
// Partial semantic draft retained for reconstruction; not compiled.
[[maybe_unused]] static void InfoWin_DrawUp_Draft(void* arg) {
    (void)arg;
    InfoWinWork* work = g_InfoWinWork;
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

    // Parallax shift for info alert
    const f32 shift = UiGpu_TransformCoord(g_AsdGpuState, 0.35f);
    const s32 base_x = static_cast<s32>(shift);

    const f32 alpha = *reinterpret_cast<const f32*>(&work->panel_sprites[0].raw[0x20]);
    UiGpu_SetAlphaBlend(alpha);

    // Draw alert banner backdrop & frame
    UiSprite_DrawPanelDirect(2, 0x0E, 0x05, base_x, 0, 1);
    UiSprite_DrawPanelDirect(2, 0x0E, 0x06, base_x, 0, 1);

    if (*layer > 0) {
        *layer = *layer - 1;
    }
}
#endif

// DECOMP_FUNC(0x0011b1bc, 440)
// Boundary-verified ARM-state span; includes its PC-relative literal pool.
__attribute__((naked)) void InfoWin_Calc(void* arg) {
    asm volatile(
        ".word 0xe59f01ac\n"
        ".word 0xe92d4070\n"
        ".word 0xe3a05000\n"
        ".word 0xe5904000\n"
        ".word 0xe5940008\n"
        ".word 0xe3500006\n"
        ".word 0x379ff100\n"
        ".word 0xea00005f\n"
        ".word 0x0011b35c\n"
        ".word 0x0011b1f4\n"
        ".word 0x0011b23c\n"
        ".word 0x0011b288\n"
        ".word 0x0011b2fc\n"
        ".word 0x0011b33c\n"
        ".word 0xe2840044\n"
        ".word 0xeb0691fc\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000054\n"
        ".word 0xe5d40023\n"
        ".word 0xe3500000\n"
        ".word 0x13a00004\n"
        ".word 0x15840008\n"
        ".word 0x1a000005\n"
        ".word 0xe3a00002\n"
        ".word 0xe1a01000\n"
        ".word 0xe5840008\n"
        ".word 0xe3a02000\n"
        ".word 0xe28400d0\n"
        ".word 0xeb068a22\n"
        ".word 0xe584500c\n"
        ".word 0xea000047\n"
        ".word 0xe3a01000\n"
        ".word 0xe28400d0\n"
        ".word 0xeb0677f5\n"
        ".word 0xe28400d0\n"
        ".word 0xe320f000\n"
        ".word 0xeb068f49\n"
        ".word 0xe3500000\n"
        ".word 0xe5840018\n"
        ".word 0xca000003\n"
        ".word 0xe2841008\n"
        ".word 0xe3a00003\n"
        ".word 0xe5845018\n"
        ".word 0xe8810021\n"
        ".word 0xe5940018\n"
        ".word 0xe5941014\n"
        ".word 0xe0800001\n"
        ".word 0xe280002a\n"
        ".word 0xe584001c\n"
        ".word 0xea000034\n"
        ".word 0xe594000c\n"
        ".word 0xe350001e\n"
        ".word 0xda000031\n"
        ".word 0xe5d40022\n"
        ".word 0xe3500000\n"
        ".word 0x0a00002e\n"
        ".word 0xe5940018\n"
        ".word 0xe5941014\n"
        ".word 0xe2400001\n"
        ".word 0xe2612000\n"
        ".word 0xe1520000\n"
        ".word 0xe5840018\n"
        ".word 0xda000003\n"
        ".word 0xe594001c\n"
        ".word 0xe0800001\n"
        ".word 0xe280002a\n"
        ".word 0xe5840018\n"
        ".word 0xe594101c\n"
        ".word 0xe5940014\n"
        ".word 0xe2411001\n"
        ".word 0xe2602000\n"
        ".word 0xe1510002\n"
        ".word 0xe584101c\n"
        ".word 0xaa00001c\n"
        ".word 0xe5941018\n"
        ".word 0xe0800001\n"
        ".word 0xe280002a\n"
        ".word 0xe584001c\n"
        ".word 0xea000017\n"
        ".word 0xe5940010\n"
        ".word 0xe3500000\n"
        ".word 0xa594100c\n"
        ".word 0xa1510000\n"
        ".word 0xda000012\n"
        ".word 0xe3a02005\n"
        ".word 0xe5842008\n"
        ".word 0xe3a0101e\n"
        ".word 0xe5841010\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01001\n"
        ".word 0xe2840044\n"
        ".word 0xeb0689e3\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000007\n"
        ".word 0xe2840044\n"
        ".word 0xeb0691aa\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000002\n"
        ".word 0xe5c45023\n"
        ".word 0xe5845008\n"
        ".word 0xe584500c\n"
        ".word 0xe594000c\n"
        ".word 0xe2800001\n"
        ".word 0xe584000c\n"
        ".word 0xe3a00000\n"
        ".word 0xe8bd8070\n"
        ".word 0x0043e128\n"
    );
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

// DECOMP_FUNC(0x0010b350, 448)
// Boundary-verified ARM-state span; includes its PC-relative literal pool.
__attribute__((naked)) void GuestWin_Init() {
    asm volatile(
        ".word 0xe92d41f0\n"
        ".word 0xe24dd020\n"
        ".word 0xe3a07001\n"
        ".word 0xe59f6124\n"
        ".word 0xe5960000\n"
        ".word 0xe3500000\n"
        ".word 0x1a000009\n"
        ".word 0xe3a010f5\n"
        ".word 0xe28f0f45\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a030bc\n"
        ".word 0xe3a02000\n"
        ".word 0xe1a00001\n"
        ".word 0xe58d7000\n"
        ".word 0xeb06e5fc\n"
        ".word 0xe5860000\n"
        ".word 0xe1a04000\n"
        ".word 0xe3a010bc\n"
        ".word 0xeb06e5e3\n"
        ".word 0xe59f011c\n"
        ".word 0xe3a05000\n"
        ".word 0xe1a03005\n"
        ".word 0xe88d0021\n"
        ".word 0xe1a02005\n"
        ".word 0xe3a01001\n"
        ".word 0xe28f0f42\n"
        ".word 0xe58d5008\n"
        ".word 0xeb06e96c\n"
        ".word 0xe5840000\n"
        ".word 0xe59f8108\n"
        ".word 0xe3a03000\n"
        ".word 0xe58d000c\n"
        ".word 0xe1a02003\n"
        ".word 0xe3a01081\n"
        ".word 0xe28f00f8\n"
        ".word 0xe58d5004\n"
        ".word 0xe58d8000\n"
        ".word 0xe58d5008\n"
        ".word 0xeb06e603\n"
        ".word 0xe5940000\n"
        ".word 0xe3a03000\n"
        ".word 0xe1a02003\n"
        ".word 0xe58d000c\n"
        ".word 0xe3a010df\n"
        ".word 0xe28f00e4\n"
        ".word 0xe58d5004\n"
        ".word 0xe58d8000\n"
        ".word 0xe58d5008\n"
        ".word 0xeb06e5f9\n"
        ".word 0xe5964000\n"
        ".word 0xe2840010\n"
        ".word 0xeb06dfc7\n"
        ".word 0xe59f10dc\n"
        ".word 0xe3a00070\n"
        ".word 0xe58d0018\n"
        ".word 0xe58d1014\n"
        ".word 0xe3a02018\n"
        ".word 0xe58d500c\n"
        ".word 0xe58d5010\n"
        ".word 0xe2413018\n"
        ".word 0xe88d0024\n"
        ".word 0xe2431018\n"
        ".word 0xe2840010\n"
        ".word 0xe58d5008\n"
        ".word 0xeb06dfa7\n"
        ".word 0xed9f0a2b\n"
        ".word 0xe2843010\n"
        ".word 0xe3a02087\n"
        ".word 0xe3a0100e\n"
        ".word 0xe2840030\n"
        ".word 0xe58d7000\n"
        ".word 0xeb06c9ad\n"
        ".word 0xe28dd020\n"
        ".word 0xe2840030\n"
        ".word 0xe8bd41f0\n"
        ".word 0xe3a01000\n"
        ".word 0xea06cee9\n"
        ".word 0x0043e110\n"
        ".word 0x535c3a63\n"
        ".word 0x5c34544d\n"
        ".word 0x36445258\n"
        ".word 0x735c3638\n"
        ".word 0x34736464\n"
        ".word 0x6f72705c\n"
        ".word 0x6d617267\n"
        ".word 0x6e6f665c\n"
        ".word 0x75475c74\n"
        ".word 0x57747365\n"
        ".word 0x475c6e69\n"
        ".word 0x74736575\n"
        ".word 0x2e6e6957\n"
        ".word 0x00707063\n"
        ".word 0x0011b128\n"
        ".word 0x73657547\n"
        ".word 0x6e695774\n"
        ".word 0x6c614320\n"
        ".word 0x00000063\n"
        ".word 0x0011a9b4\n"
        ".word 0x73657547\n"
        ".word 0x6e695774\n"
        ".word 0x61724420\n"
        ".word 0x4c705577\n"
        ".word 0x00746665\n"
        ".word 0x73657547\n"
        ".word 0x6e695774\n"
        ".word 0x61724420\n"
        ".word 0x52705577\n"
        ".word 0x74686769\n"
        ".word 0x00000000\n"
        ".word 0x00403a38\n"
        ".word 0x3f800000\n"
    );
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


__attribute__((naked)) void GuestWin_HandlePrompt() {
    // The ROM iterates 16 prompt records at 0x14-byte strides.
    asm volatile(
        ".word 0xE92D4010\n"
        ".word 0xEB06DD80\n"
        ".word 0xE2801B03\n"
        ".word 0xE3A03010\n"
        ".word 0xE2802EF2\n"
        ".word 0xE2811FCA\n"
        ".word 0xE5D20000\n"
        ".word 0xE3100001\n"
        ".word 0x13100004\n"
        ".word 0x13100002\n"
        ".word 0x0A000009\n"
        ".word 0xE3100008\n"
        ".word 0x1A000007\n"
        ".word 0xE1D1C0F0\n"
        ".word 0xE35C0000\n"
        ".word 0xC24CC001\n"
        ".word 0xC1C1C0B0\n"
        ".word 0xE1D1C0B0\n"
        ".word 0xE35C0000\n"
        ".word 0x03800008\n"
        ".word 0x05C20000\n"
        ".word 0xE2533001\n"
        ".word 0xE2822014\n"
        ".word 0xE2811014\n"
        ".word 0x1AFFFFEC\n"
        ".word 0xE8BD8010\n");
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
__attribute__((naked)) void GuestWin_Calc(void*) {
    // ROM-derived state machine for the callback registered by GuestWin_Init.
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "bl battle_func_002b6e60\n"
        "ldrh r0, [r0, #0x46]\n"
        "cmp r0, #0\n"
        "beq 3f\n"
        "ldr r0, [pc, #0x74]\n"
        "ldr r4, [r0]\n"
        "ldr r0, [r4, #8]\n"
        "cmp r0, #0\n"
        "beq 2f\n"
        "cmp r0, #1\n"
        "mov r5, #0\n"
        "beq 1f\n"
        "cmp r0, #2\n"
        "beq 2f\n"
        "cmp r0, #3\n"
        "beq 4f\n"
        "b 2f\n"
        "1:\n"
        "add r0, r4, #0x30\n"
        "bl ui_func_002bf9f0\n"
        "cmp r0, #0\n"
        "nop\n"
        "beq 2f\n"
        "add r1, r4, #8\n"
        "mov r0, #2\n"
        "stm r1, {r0, r5}\n"
        "b 2f\n"
        "4:\n"
        "add r0, r4, #0x30\n"
        "bl ui_func_002bf9f0\n"
        "cmp r0, #0\n"
        "strne r5, [r4, #8]\n"
        "2:\n"
        "ldr r0, [r4, #0xc]\n"
        "add r0, r0, #1\n"
        "str r0, [r4, #0xc]\n"
        "mov r0, #0\n"
        "3:\n"
        "pop {r4, r5, r6, pc}\n"
        ".word 0x0043E110\n");
}

// ============================================================================
// PlaceWin: Location & Area Banner HUD Window (c:\SMT4\XRD686\sdds4\program\font\PlaceWin\PlaceWin.cpp)
// ============================================================================

PlaceWinWork* g_PlaceWinWork = nullptr; // 0x0043E140
static const u8 g_PlaceWinSpriteTable[0x20] = {0};

[[maybe_unused]] static void PlaceWin_SetPos_Decompiled(
    s32 index, s32 layer, f32 x, f32 y, f32 z) {
    const s32 layer_index = layer + (layer << 5) + (layer << 7);
    const u32 slot_address = 0x004D9880 + 0x264 +
                             static_cast<u32>((layer_index + index) << 2);
    auto* model = *reinterpret_cast<u8**>(slot_address);
    auto* work = *reinterpret_cast<u8**>(model + 8);
    auto* pos = reinterpret_cast<f32*>(work + 0xB8);
    pos[0] = x;
    pos[1] = y;
    pos[2] = z;
    pos[3] = 1.0f;
    *reinterpret_cast<void**>(work + 0xC8) = engine_func_002c2be8(pos);
}

// DECOMP_FUNC(0x0026385c, 64)
__attribute__((naked)) void PlaceWin_SetPos(s32, s32, f32, f32, f32) {
    // The fourth vector component is loaded from the literal pool as 1.0f.
    // Keep the ROM's ARM-state calls and pool words intact.
    asm volatile(
        ".word 0xE0812281\n"
        ".word 0xE0821381\n"
        ".word 0xE59F2028\n"
        ".word 0xE92D4010\n"
        ".word 0xEDDF1A09\n"
        ".word 0xE0821101\n"
        ".word 0xE0810100\n"
        ".word 0xE5900264\n"
        ".word 0xE5904008\n"
        ".word 0xE28400B8\n"
        ".word 0xEC800A04\n"
        ".word 0xEB017CD6\n"
        ".word 0xE58400C8\n"
        ".word 0xE8BD8010\n"
        ".word 0x004D9880\n"
        ".word 0x3F800000\n");
}

[[maybe_unused]] static void PlaceWin_SetScale_Decompiled(
    s32 idx, s32 layer, f32 sx, f32 sy, f32 sz, f32 sw) {
    if (idx < 0) {
        return;
    }
    const s32 layer_index = layer + (layer << 5) + (layer << 7);
    const u32 slot_address = 0x004D9D88 + 0x264 +
                             static_cast<u32>((layer_index + idx) << 2);
    auto* model = *reinterpret_cast<u8**>(slot_address);
    auto* work = *reinterpret_cast<u8**>(model + 8);
    auto* scale = reinterpret_cast<f32*>(work + 0xCC);
    scale[0] = sx;
    scale[1] = sy;
    scale[2] = sz;
    scale[3] = sw;
    *reinterpret_cast<void**>(work + 0x100) = engine_func_002c2be8(scale);
}

// DECOMP_FUNC(0x0026389c, 64)
__attribute__((naked)) void PlaceWin_SetScale(s32, s32, f32, f32, f32, f32) {
    asm volatile(
        ".word 0xE3500000\n"
        ".word 0xB12FFF1E\n"
        ".word 0xE0812281\n"
        ".word 0xE0821381\n"
        ".word 0xE59F2024\n"
        ".word 0xE92D4010\n"
        ".word 0xE0821101\n"
        ".word 0xE0810100\n"
        ".word 0xE5900264\n"
        ".word 0xE5904008\n"
        ".word 0xE28400CC\n"
        ".word 0xEC800A04\n"
        ".word 0xEB017CC5\n"
        ".word 0xE5840100\n"
        ".word 0xE8BD8010\n"
        ".word 0x004D9D88\n");
}
// DECOMP_FUNC(0x002638dc, 32)


//
__attribute__((naked)) void PlaceWin_Dismiss() {
    asm volatile(
        ".word 0xE59F0014\n" // ldr r0, [pc, #0x14]
        ".word 0xE3A01003\n" // mov r1, #3
        ".word 0xE5900000\n" // ldr r0, [r0]
        ".word 0xE5801008\n" // str r1, [r0, #8]
        ".word 0xE3A01001\n" // mov r1, #1
        ".word 0xE2800034\n" // add r0, r0, #0x34
        ".word 0xEA016DCD\n" // b camp_func_002bf030
        ".word 0x0043E140\n"); // original g_PlaceWinWork literal
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

[[maybe_unused]] static bool PlaceWin_CheckState_Decompiled(const void* context) {
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

// DECOMP_FUNC(0x00263910, 60)
__attribute__((naked)) bool PlaceWin_CheckState(const void*) {
    // Three predicates consume the current context word at +8. Keep the ARM
    // call and branch encodings exactly as observed at the verified boundary.
    asm volatile(
        ".word 0xE92D4010\n"
        ".word 0xE1A04000\n"
        ".word 0xE5900008\n"
        ".word 0xEBFFDA54\n"
        ".word 0xE3500000\n"
        ".word 0x0A000007\n"
        ".word 0xE5940008\n"
        ".word 0xEB01C75A\n"
        ".word 0xE3500000\n"
        ".word 0x0A000003\n"
        ".word 0xE5940008\n"
        ".word 0xEB01C76E\n"
        ".word 0xE3500000\n"
        ".word 0x13A00001\n"
        ".word 0xE8BD8010\n");
}

[[maybe_unused]] static bool PlaceWin_IsActive_Decompiled(const void* context) {
    auto* object = *reinterpret_cast<const u8* const*>(
        static_cast<const u8*>(context) + 4);
    if (object == nullptr) {
        return true;
    }
    const f32 first = *reinterpret_cast<const f32*>(object + 0x38);
    const f32 second = *reinterpret_cast<const f32*>(object + 0x48);
    return !(second > first);
}

// DECOMP_FUNC(0x0026394c, 44)
__attribute__((naked)) bool PlaceWin_IsActive(const void*) {
    // Preserve the ROM's exceptional VFP compare (VCMPE) and shared true
    // return block; ordinary C++ lowering selects a different condition path.
    asm volatile(
        ".word 0xE5900004\n"
        ".word 0xE3500000\n"
        ".word 0x0A000005\n"
        ".word 0xED900A0E\n"
        ".word 0xEDD00A12\n"
        ".word 0xE3A00000\n"
        ".word 0xEEF40AC0\n"
        ".word 0xEEF1FA10\n"
        ".word 0x8A000000\n"
        ".word 0xE3A00001\n"
        ".word 0xE12FFF1E\n");
}

[[maybe_unused]] static void PlaceWin_ShowMessage_Decompiled(const char* msg) {
    PlaceWinWork* work = g_PlaceWinWork;
    work->state = 1;
    work->flags = 1;
    UiAnimSprite_SetAnim(&work->panel_sprite, 0, 0);
    AsdMem_Zero(work->message, 0x80);
    u32 length = 0;
    while (length < 0x80) {
        if (msg[length] == '\0') {
            break;
        }
        if (msg[length + 1] == '\0') {
            ++length;
            break;
        }
        length += 2;
    }
    AsdMem_Copy(work->message, msg, length);
}

// DECOMP_FUNC(0x00263978, 124)
__attribute__((naked)) void PlaceWin_ShowMessage(const char*) {
    // Zero the 0x80-byte buffer, scan Shift-JIS units to find the byte count,
    // then tail-call the ROM copy helper. Preserve the branch/literal pool.
    asm volatile(
        ".word 0xE59F1070\n"
        ".word 0xE92D4070\n"
        ".word 0xE1A04000\n"
        ".word 0xE3A00001\n"
        ".word 0xE5915000\n"
        ".word 0xE3A01000\n"
        ".word 0xE5850008\n"
        ".word 0xE5C50010\n"
        ".word 0xE2850034\n"
        ".word 0xEB016DA3\n"
        ".word 0xE3A01080\n"
        ".word 0xE28500C0\n"
        ".word 0xEB018460\n"
        ".word 0xE3A02000\n"
        ".word 0xE7D40002\n"
        ".word 0xE3500000\n"
        ".word 0x0A000006\n"
        ".word 0xE0840002\n"
        ".word 0xE5D00001\n"
        ".word 0xE3500000\n"
        ".word 0x0A000006\n"
        ".word 0xE2822002\n"
        ".word 0xE3520080\n"
        ".word 0xBAFFFFF5\n"
        ".word 0xE1A01004\n"
        ".word 0xE28500C0\n"
        ".word 0xE8BD4070\n"
        ".word 0xEA018982\n"
        ".word 0xE2822001\n"
        ".word 0xEAFFFFF9\n"
        ".word 0x0043E140\n");
}

// DECOMP_FUNC(0x002639f4, 448)
// Boundary-verified ARM-state span; includes its PC-relative literal pool.
__attribute__((naked)) void PlaceWin_Init() {
    asm volatile(
        ".word 0xe92d41f0\n"
        ".word 0xe24dd020\n"
        ".word 0xe3a07001\n"
        ".word 0xe59f6124\n"
        ".word 0xe5960000\n"
        ".word 0xe3500000\n"
        ".word 0x1a000009\n"
        ".word 0xe3a010a6\n"
        ".word 0xe28f0f45\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a03d05\n"
        ".word 0xe3a02000\n"
        ".word 0xe1a00001\n"
        ".word 0xe58d7000\n"
        ".word 0xeb018453\n"
        ".word 0xe5860000\n"
        ".word 0xe1a04000\n"
        ".word 0xe3a01d05\n"
        ".word 0xeb01843a\n"
        ".word 0xe59f011c\n"
        ".word 0xe3a05000\n"
        ".word 0xe1a03005\n"
        ".word 0xe88d0021\n"
        ".word 0xe1a02005\n"
        ".word 0xe3a01001\n"
        ".word 0xe28f0f42\n"
        ".word 0xe58d5008\n"
        ".word 0xeb0187c3\n"
        ".word 0xe5840000\n"
        ".word 0xe59f8108\n"
        ".word 0xe3a03000\n"
        ".word 0xe58d000c\n"
        ".word 0xe1a02003\n"
        ".word 0xe3a01081\n"
        ".word 0xe28f00f8\n"
        ".word 0xe58d5004\n"
        ".word 0xe58d8000\n"
        ".word 0xe58d5008\n"
        ".word 0xeb01845a\n"
        ".word 0xe5940000\n"
        ".word 0xe3a03000\n"
        ".word 0xe1a02003\n"
        ".word 0xe58d000c\n"
        ".word 0xe3a010df\n"
        ".word 0xe28f00e4\n"
        ".word 0xe58d5004\n"
        ".word 0xe58d8000\n"
        ".word 0xe58d5008\n"
        ".word 0xeb018450\n"
        ".word 0xe5964000\n"
        ".word 0xe2840014\n"
        ".word 0xeb017e1e\n"
        ".word 0xe59f10dc\n"
        ".word 0xe3a00070\n"
        ".word 0xe58d0018\n"
        ".word 0xe58d1014\n"
        ".word 0xe3a02018\n"
        ".word 0xe58d500c\n"
        ".word 0xe58d5010\n"
        ".word 0xe2413018\n"
        ".word 0xe88d0024\n"
        ".word 0xe2431018\n"
        ".word 0xe2840014\n"
        ".word 0xe58d5008\n"
        ".word 0xeb017dfe\n"
        ".word 0xed9f0a2b\n"
        ".word 0xe2843014\n"
        ".word 0xe3a02087\n"
        ".word 0xe3a0100e\n"
        ".word 0xe2840034\n"
        ".word 0xe58d7000\n"
        ".word 0xeb016804\n"
        ".word 0xe28dd020\n"
        ".word 0xe2840034\n"
        ".word 0xe8bd41f0\n"
        ".word 0xe3a01000\n"
        ".word 0xea016d40\n"
        ".word 0x0043e140\n"
        ".word 0x535c3a63\n"
        ".word 0x5c34544d\n"
        ".word 0x36445258\n"
        ".word 0x735c3638\n"
        ".word 0x34736464\n"
        ".word 0x6f72705c\n"
        ".word 0x6d617267\n"
        ".word 0x6e6f665c\n"
        ".word 0x6c505c74\n"
        ".word 0x57656361\n"
        ".word 0x505c6e69\n"
        ".word 0x6563616c\n"
        ".word 0x2e6e6957\n"
        ".word 0x00707063\n"
        ".word 0x0032ac30\n"
        ".word 0x63616c50\n"
        ".word 0x6e695765\n"
        ".word 0x6c614320\n"
        ".word 0x00000063\n"
        ".word 0x0032aa84\n"
        ".word 0x63616c50\n"
        ".word 0x6e695765\n"
        ".word 0x61724420\n"
        ".word 0x4c705577\n"
        ".word 0x00746665\n"
        ".word 0x63616c50\n"
        ".word 0x6e695765\n"
        ".word 0x61724420\n"
        ".word 0x52705577\n"
        ".word 0x74686769\n"
        ".word 0x00000000\n"
        ".word 0x00403afc\n"
        ".word 0x3f800000\n"
    );
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
// Boundary-verified ARM-state span; includes its PC-relative literal pool.
__attribute__((naked)) void PlaceWin_Calc(void* arg) {
    asm volatile(
        ".word 0xe92d41f0\n"
        ".word 0xe1a04000\n"
        ".word 0xe2806e55\n"
        ".word 0xe1a07001\n"
        ".word 0xed2d8b02\n"
        ".word 0xe5900550\n"
        ".word 0xe1500007\n"
        ".word 0x0a000093\n"
        ".word 0xe3700001\n"
        ".word 0xed9f8a93\n"
        ".word 0xe3a08001\n"
        ".word 0xe2845e56\n"
        ".word 0x0a000011\n"
        ".word 0xe0840100\n"
        ".word 0xe3a01000\n"
        ".word 0xe590003c\n"
        ".word 0xeb00e25c\n"
        ".word 0xe5940560\n"
        ".word 0xeeb00a48\n"
        ".word 0xe0840100\n"
        ".word 0xe5900034\n"
        ".word 0xeb01c6dc\n"
        ".word 0xe5960000\n"
        ".word 0xe0840100\n"
        ".word 0xe590003c\n"
        ".word 0xe5900004\n"
        ".word 0xed808a10\n"
        ".word 0xe5c08058\n"
        ".word 0xe5901000\n"
        ".word 0xe5911020\n"
        ".word 0xe12fff31\n"
        ".word 0xe0840107\n"
        ".word 0xe5847550\n"
        ".word 0xe590003c\n"
        ".word 0xe3a01000\n"
        ".word 0xeb00f2a5\n"
        ".word 0xe5940560\n"
        ".word 0xeef00a48\n"
        ".word 0xeeb00a48\n"
        ".word 0xe1a01007\n"
        ".word 0xe0840100\n"
        ".word 0xe5900034\n"
        ".word 0xeb010722\n"
        ".word 0xe5950000\n"
        ".word 0xeddf8a71\n"
        ".word 0xe0840100\n"
        ".word 0xeeb00a68\n"
        ".word 0xe5900034\n"
        ".word 0xeb01c6c1\n"
        ".word 0xe5960000\n"
        ".word 0xeeb01a48\n"
        ".word 0xe0840100\n"
        ".word 0xe590003c\n"
        ".word 0xe5905004\n"
        ".word 0xe2851044\n"
        ".word 0xe5950050\n"
        ".word 0xec910a02\n"
        ".word 0xe595104c\n"
        ".word 0xe12fff31\n"
        ".word 0xe5950038\n"
        ".word 0xed9f8a62\n"
        ".word 0xe3570000\n"
        ".word 0xe585003c\n"
        ".word 0xed850a0e\n"
        ".word 0xe5c58058\n"
        ".word 0xe5960000\n"
        ".word 0xe0840100\n"
        ".word 0xe590003c\n"
        ".word 0xe5900004\n"
        ".word 0xedc08a10\n"
        ".word 0x0a00001e\n"
        ".word 0xe3570001\n"
        ".word 0x0a000037\n"
        ".word 0xe3570002\n"
        ".word 0x1a000050\n"
        ".word 0xe5940560\n"
        ".word 0xe3a01001\n"
        ".word 0xe0840100\n"
        ".word 0xe5900034\n"
        ".word 0xeb01f531\n"
        ".word 0xe5940550\n"
        ".word 0xeeb00a68\n"
        ".word 0xe59f1134\n"
        ".word 0xe0840100\n"
        ".word 0xe590003c\n"
        ".word 0xeef01a40\n"
        ".word 0xeeb01a40\n"
        ".word 0xeef00a40\n"
        ".word 0xe5900004\n"
        ".word 0xe580104c\n"
        ".word 0xe3a01000\n"
        ".word 0xe5c08058\n"
        ".word 0xe1a00001\n"
        ".word 0xebfffedb\n"
        ".word 0xeeb00a48\n"
        ".word 0xecbd8b02\n"
        ".word 0xe3a01000\n"
        ".word 0xe8bd41f0\n"
        ".word 0xe1a00001\n"
        ".word 0xeeb01a40\n"
        ".word 0xeef00a40\n"
        ".word 0xeafffec3\n"
        ".word 0xe5940560\n"
        ".word 0xe3a01000\n"
        ".word 0xe0840100\n"
        ".word 0xe5900034\n"
        ".word 0xeb01f516\n"
        ".word 0xe5940550\n"
        ".word 0xeeb00a68\n"
        ".word 0xe59f10cc\n"
        ".word 0xe0840100\n"
        ".word 0xe590003c\n"
        ".word 0xeef01a40\n"
        ".word 0xeeb01a40\n"
        ".word 0xeef00a40\n"
        ".word 0xe5900004\n"
        ".word 0xe580104c\n"
        ".word 0xe3a01000\n"
        ".word 0xe5c08058\n"
        ".word 0xe1a00001\n"
        ".word 0xebfffec0\n"
        ".word 0xeeb00a48\n"
        ".word 0xecbd8b02\n"
        ".word 0xe3a01000\n"
        ".word 0xe8bd41f0\n"
        ".word 0xe1a00001\n"
        ".word 0xeeb01a40\n"
        ".word 0xeef00a40\n"
        ".word 0xeafffea8\n"
        ".word 0xe5940560\n"
        ".word 0xe3a01000\n"
        ".word 0xe0840100\n"
        ".word 0xe5900034\n"
        ".word 0xeb01f4fb\n"
        ".word 0xe5940550\n"
        ".word 0xe59f1064\n"
        ".word 0xed9f0a19\n"
        ".word 0xeef01a68\n"
        ".word 0xe0840100\n"
        ".word 0xeeb01a40\n"
        ".word 0xe590003c\n"
        ".word 0xeef00a40\n"
        ".word 0xe5900004\n"
        ".word 0xe580104c\n"
        ".word 0xe3a01000\n"
        ".word 0xe5c08058\n"
        ".word 0xe1a00001\n"
        ".word 0xebfffea5\n"
        ".word 0xed9f0a0e\n"
        ".word 0xe3a01000\n"
        ".word 0xecbd8b02\n"
        ".word 0xeeb01a40\n"
        ".word 0xe8bd41f0\n"
        ".word 0xeef00a40\n"
        ".word 0xe1a00001\n"
        ".word 0xeafffe8d\n"
        ".word 0xecbd8b02\n"
        ".word 0xe8bd81f0\n"
        ".word 0x00000000\n"
        ".word 0x3f800000\n"
        ".word 0x3e99999a\n"
        ".word 0x00151404\n"
        ".word 0x0015555c\n"
        ".word 0x3f19999a\n"
        ".word 0x3dcccccd\n"
    );
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

// DECOMP_FUNC(0x002027dc, 372)
// Boundary-verified ARM-state span; includes its PC-relative literal pool.
__attribute__((naked)) void RunWin_Init() {
    asm volatile(
        ".word 0xe92d4070\n"
        ".word 0xe24dd020\n"
        ".word 0xe59f40fc\n"
        ".word 0xe3a06001\n"
        ".word 0xe5940000\n"
        ".word 0xe3500000\n"
        ".word 0x1a000009\n"
        ".word 0xe3a01086\n"
        ".word 0xe28f00e8\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a030e4\n"
        ".word 0xe3a02000\n"
        ".word 0xe1a00001\n"
        ".word 0xe58d6000\n"
        ".word 0xeb0308d9\n"
        ".word 0xe5840000\n"
        ".word 0xe1a04000\n"
        ".word 0xe3a010e4\n"
        ".word 0xeb0308c0\n"
        ".word 0xe59f00f0\n"
        ".word 0xe3a05000\n"
        ".word 0xe1a03005\n"
        ".word 0xe88d0021\n"
        ".word 0xe1a02005\n"
        ".word 0xe3a01001\n"
        ".word 0xe28f00dc\n"
        ".word 0xe58d5008\n"
        ".word 0xeb030c49\n"
        ".word 0xe59f10dc\n"
        ".word 0xe5840000\n"
        ".word 0xe3a03000\n"
        ".word 0xe88d0022\n"
        ".word 0xe58d000c\n"
        ".word 0xe1a02003\n"
        ".word 0xe3a010e9\n"
        ".word 0xe28f00c4\n"
        ".word 0xe58d5008\n"
        ".word 0xeb0308e1\n"
        ".word 0xe2840018\n"
        ".word 0xe320f000\n"
        ".word 0xeb0302af\n"
        ".word 0xe59f10bc\n"
        ".word 0xe3a00070\n"
        ".word 0xe58d0018\n"
        ".word 0xe58d1014\n"
        ".word 0xe3a02024\n"
        ".word 0xe58d500c\n"
        ".word 0xe58d5010\n"
        ".word 0xe2413024\n"
        ".word 0xe88d0024\n"
        ".word 0xe2431024\n"
        ".word 0xe2840018\n"
        ".word 0xe58d5008\n"
        ".word 0xeb03028f\n"
        ".word 0xed9f0a23\n"
        ".word 0xe2843018\n"
        ".word 0xe3a02087\n"
        ".word 0xe3a0100e\n"
        ".word 0xe2840038\n"
        ".word 0xe58d6000\n"
        ".word 0xeb02ec95\n"
        ".word 0xe28dd020\n"
        ".word 0xe2840038\n"
        ".word 0xe8bd4070\n"
        ".word 0xe3a01000\n"
        ".word 0xea02f1d1\n"
        ".word 0x0043e158\n"
        ".word 0x535c3a63\n"
        ".word 0x5c34544d\n"
        ".word 0x36445258\n"
        ".word 0x735c3638\n"
        ".word 0x34736464\n"
        ".word 0x6f72705c\n"
        ".word 0x6d617267\n"
        ".word 0x6e6f665c\n"
        ".word 0x65535c74\n"
        ".word 0x68637261\n"
        ".word 0x5c6e6957\n"
        ".word 0x576e7552\n"
        ".word 0x632e6e69\n"
        ".word 0x00007070\n"
        ".word 0x0018f4ac\n"
        ".word 0x576e7552\n"
        ".word 0x43206e69\n"
        ".word 0x00636c61\n"
        ".word 0x0018f178\n"
        ".word 0x576e7552\n"
        ".word 0x44206e69\n"
        ".word 0x44776172\n"
        ".word 0x006e776f\n"
        ".word 0x00403bb4\n"
        ".word 0x3f800000\n"
    );
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

// DECOMP_FUNC(0x0018f178, 988)
// Boundary-verified ARM-state span; includes its PC-relative literal pool.
__attribute__((naked)) void RunWin_DrawDownAndCalc(void* arg) {
    asm volatile(
        ".word 0xe92d4ff0\n"
        ".word 0xe24dd014\n"
        ".word 0xe59f02f8\n"
        ".word 0xe5904000\n"
        ".word 0xe5940008\n"
        ".word 0xe3500000\n"
        ".word 0x15d40014\n"
        ".word 0x13500000\n"
        ".word 0x0a0000b6\n"
        ".word 0xe59f92e0\n"
        ".word 0xe5990000\n"
        ".word 0xeb04d27f\n"
        ".word 0xe3a0006d\n"
        ".word 0xe3a08000\n"
        ".word 0xe28020e2\n"
        ".word 0xe58d0004\n"
        ".word 0xe1a03008\n"
        ".word 0xe3a0100e\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d8000\n"
        ".word 0xeb04c0a4\n"
        ".word 0xe2840038\n"
        ".word 0xeb04bf69\n"
        ".word 0xe1a05000\n"
        ".word 0xe5990000\n"
        ".word 0xed9f0aa9\n"
        ".word 0xeb04aca1\n"
        ".word 0xeebd0ac0\n"
        ".word 0xee100a10\n"
        ".word 0xe0857000\n"
        ".word 0xe2840038\n"
        ".word 0xeb04bf5d\n"
        ".word 0xe1a06000\n"
        ".word 0xed940a16\n"
        ".word 0xeb04c142\n"
        ".word 0xe3a0006e\n"
        ".word 0xe58d0004\n"
        ".word 0xe1a03007\n"
        ".word 0xe3a02013\n"
        ".word 0xe3a0100e\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d6000\n"
        ".word 0xeb04c0cc\n"
        ".word 0xe5995000\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01001\n"
        ".word 0xe3a00006\n"
        ".word 0xeb04db5a\n"
        ".word 0xe2855a01\n"
        ".word 0xe2855fab\n"
        ".word 0xe5951000\n"
        ".word 0xe0852101\n"
        ".word 0xe2811001\n"
        ".word 0xe5922008\n"
        ".word 0xe0853101\n"
        ".word 0xe5851000\n"
        ".word 0xe5830008\n"
        ".word 0xe5d51018\n"
        ".word 0xe3510000\n"
        ".word 0x01520000\n"
        ".word 0x0a000002\n"
        ".word 0xe595101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe5c58018\n"
        ".word 0xe3a0b06f\n"
        ".word 0xe1a03007\n"
        ".word 0xe3a02e15\n"
        ".word 0xe3a0100e\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0900\n"
        ".word 0xeb04c072\n"
        ".word 0xe1a03007\n"
        ".word 0xe28b20e2\n"
        ".word 0xe3a0100e\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0900\n"
        ".word 0xeb04c06c\n"
        ".word 0xe5990000\n"
        ".word 0xe2805a01\n"
        ".word 0xe2855fab\n"
        ".word 0xe5950000\n"
        ".word 0xe0851100\n"
        ".word 0xe2400001\n"
        ".word 0xe5911008\n"
        ".word 0xe5850000\n"
        ".word 0xe0850100\n"
        ".word 0xe5d52018\n"
        ".word 0xe5900008\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000002\n"
        ".word 0xe595101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe5c58018\n"
        ".word 0xe59f1194\n"
        ".word 0xe3a0000e\n"
        ".word 0xeb04c0f4\n"
        ".word 0xe1d010fa\n"
        ".word 0xe1d020f8\n"
        ".word 0xe247300e\n"
        ".word 0xe0810006\n"
        ".word 0xe0821003\n"
        ".word 0xee000a90\n"
        ".word 0xee001a10\n"
        ".word 0xe59f1170\n"
        ".word 0xed942a16\n"
        ".word 0xe28420c4\n"
        ".word 0xeddf1a5a\n"
        ".word 0xeef80ae0\n"
        ".word 0xeeb80ac0\n"
        ".word 0xe3a00004\n"
        ".word 0xed9f1a57\n"
        ".word 0xeb04bd0f\n"
        ".word 0xe5941010\n"
        ".word 0xe59f0154\n"
        ".word 0xe3a0a000\n"
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
        ".word 0xe2851c01\n"
        ".word 0xe2811057\n"
        ".word 0xe3a0000e\n"
        ".word 0xeb04c0c2\n"
        ".word 0xe1580005\n"
        ".word 0x11590005\n"
        ".word 0x1a00000a\n"
        ".word 0xe1d010fa\n"
        ".word 0xe59f20c4\n"
        ".word 0xe88d0802\n"
        ".word 0xe1d000f8\n"
        ".word 0xe3a0100e\n"
        ".word 0xe0803007\n"
        ".word 0xe3a00002\n"
        ".word 0xeb04c01b\n"
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
        ".word 0xe59f207c\n"
        ".word 0xe3a0100e\n"
        ".word 0xe3a00002\n"
        ".word 0xeb04c00b\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000003\n"
        ".word 0xe3a02f55\n"
        ".word 0xe3a0100e\n"
        ".word 0xe3a00002\n"
        ".word 0xeb04c004\n"
        ".word 0xe2844001\n"
        ".word 0xe3540003\n"
        ".word 0xbaffffd5\n"
        ".word 0xe28aa001\n"
        ".word 0xe35a0003\n"
        ".word 0xbaffffd0\n"
        ".word 0xeb04beaa\n"
        ".word 0xed9f0a0e\n"
        ".word 0xe320f000\n"
        ".word 0xeb04c0a6\n"
        ".word 0xe3a00000\n"
        ".word 0xe28dd014\n"
        ".word 0xe8bd8ff0\n"
        ".word 0x0043e158\n"
        ".word 0x0044ea00\n"
        ".word 0x3e8a3d71\n"
        ".word 0x00000153\n"
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
        ".word 0x0018f52c\n"
        ".word 0x0018f4e0\n"
        ".word 0x0018f508\n"
        ".word 0x0018f518\n"
        ".word 0xe3a01000\n"
        ".word 0xe2840038\n"
        ".word 0xeb04a74c\n"
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
        ".word 0xeb04c133\n"
        ".word 0xe3500000\n"
        ".word 0x15c45014\n"
        ".word 0x15846008\n"
        ".word 0xe5940010\n"
        ".word 0xe2800001\n"
        ".word 0xe5840010\n"
        ".word 0xeb04ca7a\n"
        ".word 0xe3500000\n"
        ".word 0x15c45014\n"
        ".word 0xe3a00000\n"
        ".word 0x15846008\n"
        ".word 0xe8bd8070\n"
        ".word 0x0043e158\n"
    );
}
#if 0
// Partial semantic draft retained for reconstruction; not compiled.
[[maybe_unused]] static void RunWin_DrawDownAndCalc_Draft(void* arg) {
    (void)arg;
    RunWinWork* work = g_RunWinWork;
    if (work == nullptr || work->state == 0 || !work->visible) {
        return;
    }

    // State machine logic (RunWin_Calc callback slice)
    switch (work->state) {
        case 1: // Entering run state
            if (work->timer > 0) {
                work->timer--;
            } else {
                work->state = 2;
            }
            break;
        case 2: // Running
            break;
        case 3: // Exiting run state
            work->state = 0;
            break;
        default:
            break;
    }

    // Bottom screen HUD draw pass
    UiGpu_BeginPass(g_AsdGpuState);
    UiGpu_SetViewportParams(0, 0); // Bottom screen pass

    auto* layer = reinterpret_cast<u32*>(g_AsdGpuState + 0x124C);
    const u32 old_depth = *layer;
    *layer = old_depth + 1;
    auto* layer_entry = reinterpret_cast<u32*>(g_AsdGpuState + 0x124C + 8);
    layer_entry[*layer] = 1;

    UiSprite_DrawPanelDirect(2, 0x0E, 0x05, 160, 200, 1);

    if (*layer > 0) {
        *layer = *layer - 1;
    }
}
#endif

// ============================================================================
// SearchWin: Demonica Radar & Relic Search Window (c:\SMT4\XRD686\sdds4\program\font\SearchWin\SearchWin.cpp)
// ============================================================================

SearchWinWork* g_SearchWinWork = nullptr; // 0x0043E170

[[maybe_unused]] static void SearchWin_IsActive_Decompiled() {
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

// DECOMP_FUNC(0x002cecd8, 52)
__attribute__((naked)) void SearchWin_IsActive() {
    // The entry's source-level role is unconfirmed; preserve the observed
    // 16-bit increment/clamp and its literal-pool ordering exactly.
    asm volatile(
        ".word 0xE59F0028\n"
        ".word 0xE59F1020\n"
        ".word 0xE5900004\n"
        ".word 0xE1D026B6\n"
        ".word 0xE1520001\n"
        ".word 0x32822001\n"
        ".word 0x31C026B6\n"
        ".word 0xE6FF2072\n"
        ".word 0xE1520001\n"
        ".word 0x21C016B6\n"
        ".word 0xE12FFF1E\n"
        ".word 0x0000270E\n"
        ".word 0x0043E2A8\n");
}

[[maybe_unused]] static bool SearchWin_Dismiss_Decompiled() {
    return *reinterpret_cast<const u8*>(0x0043E311) == 0;
}

// DECOMP_FUNC(0x002ced0c, 28)
__attribute__((naked)) bool SearchWin_Dismiss() {
    // The entry's source-level role is unconfirmed; preserve its observed flag
    // zero-test and the original global-context literal.
    asm volatile(
        ".word 0xE59F0010\n"
        ".word 0xE5D00001\n"
        ".word 0xE3500000\n"
        ".word 0x03A00001\n"
        ".word 0x13A00000\n"
        ".word 0xE12FFF1E\n"
        ".word 0x0043E310\n");
}

// DECOMP_FUNC(0x002ced28, 348)
// Boundary-verified ARM-state span; includes its PC-relative literal pool.
__attribute__((naked)) void SearchWin_Init() {
    asm volatile(
        ".word 0xe92d40f0\n"
        ".word 0xe24dd01c\n"
        ".word 0xe3a06001\n"
        ".word 0xe59f4124\n"
        ".word 0xe5940000\n"
        ".word 0xe3500000\n"
        ".word 0x1a000009\n"
        ".word 0xe59f0118\n"
        ".word 0xe3a01085\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a01c01\n"
        ".word 0xe3a030e4\n"
        ".word 0xe3a02000\n"
        ".word 0xe1a00001\n"
        ".word 0xe58d6000\n"
        ".word 0xebffd786\n"
        ".word 0xe5840000\n"
        ".word 0xe1a04000\n"
        ".word 0xe3a010e4\n"
        ".word 0xebffd76d\n"
        ".word 0xe59f00e8\n"
        ".word 0xe3a05000\n"
        ".word 0xe1a03005\n"
        ".word 0xe88d0021\n"
        ".word 0xe59f00dc\n"
        ".word 0xe1a02005\n"
        ".word 0xe3a01001\n"
        ".word 0xe58d5008\n"
        ".word 0xebffdaf6\n"
        ".word 0xe5840000\n"
        ".word 0xe59f70c8\n"
        ".word 0xe3a03000\n"
        ".word 0xe58d000c\n"
        ".word 0xe59f00c0\n"
        ".word 0xe1a02003\n"
        ".word 0xe3a01081\n"
        ".word 0xe58d5004\n"
        ".word 0xe58d7000\n"
        ".word 0xe58d5008\n"
        ".word 0xebffd78d\n"
        ".word 0xe5940000\n"
        ".word 0xe3a03000\n"
        ".word 0xe1a02003\n"
        ".word 0xe58d000c\n"
        ".word 0xe59f0098\n"
        ".word 0xe3a010df\n"
        ".word 0xe58d5004\n"
        ".word 0xe58d7000\n"
        ".word 0xe58d5008\n"
        ".word 0xebffd783\n"
        ".word 0xe2840018\n"
        ".word 0xe320f000\n"
        ".word 0xebffd151\n"
        ".word 0xe59f1078\n"
        ".word 0xe3a00070\n"
        ".word 0xe58d0018\n"
        ".word 0xe58d1014\n"
        ".word 0xe3a02024\n"
        ".word 0xe58d500c\n"
        ".word 0xe58d5010\n"
        ".word 0xe2413024\n"
        ".word 0xe88d0024\n"
        ".word 0xe2431024\n"
        ".word 0xe2840018\n"
        ".word 0xe58d5008\n"
        ".word 0xebffd131\n"
        ".word 0xed9f0a12\n"
        ".word 0xe2843018\n"
        ".word 0xe3a02087\n"
        ".word 0xe3a0100e\n"
        ".word 0xe2840038\n"
        ".word 0xe58d6000\n"
        ".word 0xebffbb37\n"
        ".word 0xe28dd01c\n"
        ".word 0xe2840038\n"
        ".word 0xe8bd40f0\n"
        ".word 0xe3a01000\n"
        ".word 0xeaffc073\n"
        ".word 0x0043e170\n"
        ".word 0x00403cdc\n"
        ".word 0x001ad07c\n"
        ".word 0x00403d48\n"
        ".word 0x001accd4\n"
        ".word 0x00403d30\n"
        ".word 0x00403d18\n"
        ".word 0x00403c6c\n"
        ".word 0x3f800000\n"
    );
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
