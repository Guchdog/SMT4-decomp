#include "ui/save_load.h"
#include "ui/window.h"
#include "engine/asd_symbols.h"

namespace smt4::ui {

// Helpers referenced by saveLoadUI_Init / saveLoadUI_DrawMain.  The canonical
// UiGpu_SetViewportParams / AsdTask_CreateCalc declarations come from
// engine/asd_symbols.h; the remaining spellings match src/ui/status.cpp.
extern "C" {
    void* AsdMem_Alloc(u32 align, u32 line, u32 zero_flag, u32 size, u32 flag); // 0x002C4B84
    void  AsdMem_Zero(void* ptr, u32 size);                                     // 0x002C4B30
    void  UiGpu_BeginPass(void* gpu_state);                                     // 0x002C3BA8
    void  UiSprite_DrawPanelDirect(s32 type, s32 id, s32 sub_id,
                                   s32 x, s32 y, s32 flag);                     // 0x002BF460
    void  func_00214960(void*);                                                 // 0x00214960
    u8*   ui_func_002c0ac8();                                                   // 0x002c0ac8
    void* engine_func_002c54f0(u32, u32, u32, u32, u32);                        // 0x002c54f0
    void  SaveLoad_Thread_func_00247c64(u32, u32, u32, void*, u32);             // 0x00247c64
    s32   script_vm_func_001a1bf8();                                            // 0x001a1bf8
    void* ui_func_0026b844();                                                   // 0x0026b844
    void  ui_func_002bcf58(void*, const void*, u32);                            // 0x002bcf58
    void* ui_func_0026b830();                                                   // 0x0026b830
    void  ui_func_002adb40(void*, const void*);                                 // 0x002adb40
    u8*   ui_func_002c0b94();                                                   // 0x002c0b94
    void  ui_func_0026b734();                                                   // 0x0026b734
    void  ui_func_002e0c54();                                                   // 0x002e0c54
    void  engine_func_002c5ff4(void*, const void*, u32);                        // 0x002c5ff4
    void  engine_func_002c4360(void*);                                          // 0x002c4360
    void  ui_func_0026b7ec(s32);                                                // 0x0026b7ec
    void  camp_func_002594cc(s32);                                              // 0x002594cc
    void  ui_func_002594ac(s32);                                                // 0x002594ac
    void  ui_func_001ec8e4(void*, u32, u32);                                    // 0x001ec8e4
    void  camp_func_002ef890(void*);                                            // 0x002ef890
    void  ui_func_00324d6c(void*);                                              // 0x00324d6c
    void  ui_func_00311350(void*);                                              // 0x00311350
    extern u8* g_AsdGpuState;                                                   // 0x0044EA00
}

SaveLoadUIManager g_SaveLoadUIManager = {0, {0, 0, 0}, nullptr, 0, 0}; // 0x0044DE28

// DECOMP_FUNC(0x00191eac, 208)
void saveLoadUI_Init() {
    auto* const work = static_cast<SaveLoadUIWork*>(
        AsdMem_Alloc(0x10000, 0x100, 0, sizeof(SaveLoadUIWork), 1));
    g_SaveLoadUIManager.work = work;
    work->pad_04[0] = 0;
    work->calc_task = AsdTask_CreateCalc(
        "BOOT C", 2, 0, 0, func_001c8d28, reinterpret_cast<void*>(&func_00214960), 0);
    work->state = 0x11;
    work->sub_state = 0;
}

extern "C" {
    void func_002b7f0a(void* base, s32 count, s32 size, u32 comparator);        // 0x002b7f0a
    u32  ui_func_0026b9ec(u32 record, u32 id);                                  // 0x0026b9ec
    u32  ui_func_0026b9a4(u32 id);                                              // 0x0026b9a4
}

// DECOMP_FUNC(0x001c897c, 940)
void saveLoadUI_DrawMain(void* work_arg, u32 record_arg, void* src_arg, s32 skip_idx) {
    static constexpr u32 kComparatorAddr = 0x002C6DD8;

    auto* const work = static_cast<u8*>(work_arg);
    auto* const src = static_cast<u8*>(src_arg);
    auto* const slots = reinterpret_cast<u16*>(work + 0xD134);
    auto* const ids = reinterpret_cast<u16*>(work + 0xD114);
    auto* const flags = reinterpret_cast<u16*>(work + 0xD124);
    auto* const src_ids = reinterpret_cast<const u16*>(src + 0x34);
    auto* const count_a = reinterpret_cast<s32*>(work + 0xD2C4);
    auto* const count_b = reinterpret_cast<s32*>(work + 0xD2C8);

    for (s32 i = 0; i < 8; ++i) {
        const u16 cur_id = ids[i];
        if (cur_id == 0 || skip_idx == -1 || i == skip_idx || cur_id != src_ids[skip_idx]) {
            continue;
        }

        const u16 old_id = cur_id;
        const u16 new_id = src_ids[i];
        ids[i] = new_id;
        work[0xD2D0 + i] = 1;

        for (s32 j = 0; j < 7; ++j) {
            if (slots[j + 1] == slots[0]) {
                slots[j + 1] = 0;
                func_002b7f0a(slots, 8, 2, kComparatorAddr);
            }
        }

        const s32 count = *count_a;
        for (s32 k = count; k > 0; --k) {
            slots[k] = slots[k - 1];
        }
        for (s32 k = count; k < 8; ++k) {
            slots[k] = 0;
        }

        if (ui_func_0026b9ec(record_arg, new_id) != 0) {
            if (slots[1] == new_id) {
                slots[0] = 0;
            } else {
                slots[0] = new_id;
                for (s32 j = 0; j < 7; ++j) {
                    if (slots[j + 1] == slots[0]) {
                        slots[j + 1] = 0;
                        func_002b7f0a(slots, 8, 2, kComparatorAddr);
                    }
                }
            }
        } else {
            slots[0] = 0;
            func_002b7f0a(slots, 8, 2, kComparatorAddr);
        }

        const u32 old_flag = ui_func_0026b9a4(old_id);
        const u32 new_flag = ui_func_0026b9ec(record_arg, new_id);
        if (old_flag != 0 && new_flag == 0) {
            if (new_id != 0) {
                --(*count_b);
            }
            --(*count_a);
            flags[i] = 0;
        } else if (old_flag == 0 && new_flag != 0) {
            ++(*count_b);
            flags[i] = 1;
        } else if ((old_flag == 0 && new_flag == 0) || new_id == 0) {
            --(*count_a);
        }

        saveLoadUI_DrawMain(work, record_arg, src, i);
        return;
    }
}

// Callback entry begins with an LDR at 0x001c8d28; its prologue follows at 0x001c8d2c.
// The full span retains its state-dispatch table and trailing literal pool.
// DECOMP_FUNC(0x001c8d28, 6108)
__attribute__((naked)) void func_001c8d28(void*) {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x0c8d28, 6108\n");
}

extern "C" {
    void func_00297704(const char* path, void* out, u32 a2);                  // 0x00297704
    void func_002c4e28(s32 id);                                                 // 0x002c4e28
    void func_002a6214(s32 id, s32 a1);                                         // 0x002a6214
    void func_002976ac(s32 id);                                                 // 0x002976ac
    u32  func_0029a2d0(const char* path, s32 a1);                               // 0x0029a2d0
    void func_002c3344(void* slot);                                             // 0x002c3344
    void func_002c32f8(void* slot, u32 w, u32 h, u32 a3, u32 a4, u32 a5,
                       u32 a6, u32 a7, u32 a8, u32 a9, u32 a10);                // 0x002c32f8
    void func_002bdb2c(void* obj, s32 a1, s32 a2, void* slot, s32 a4, f32 f);   // 0x002bdb2c
    void func_002bf0a8(void* obj, s32 a1, s32 a2, s32 a3, void* slot,
                       s32 a5, f32 f);                                          // 0x002bf0a8
    void func_002bdac0(void* obj, s32 a1, s32 a2);                              // 0x002bdac0
    void func_002b8b78(s32 a0);                                                 // 0x002b8b78
}

// DECOMP_FUNC(0x00202950, 1256)
void saveLoadUI_Calc(void*) {
    static constexpr u32 kSlotSize = 0x24D28;
    static constexpr u32 kTargetW = 0x00405F58;

    auto* const mgr_bytes = reinterpret_cast<u8*>(&g_SaveLoadUIManager);
    mgr_bytes[0] = 0;
    mgr_bytes[1] = 0;

    auto* const work = static_cast<SaveLoadUIWork*>(
        AsdMem_Alloc(0x10000, 0x100, 0, sizeof(SaveLoadUIWork), 1));
    g_SaveLoadUIManager.work = work;
    auto* const raw = reinterpret_cast<u8*>(work);
    raw[0x04] = 0;

    void* const calc_task = AsdTask_CreateCalc(
        "SAVELOAD_UI C",
        2,
        0,
        0,
        func_001c8d28,
        reinterpret_cast<void*>(&func_00214960),
        0);
    work->calc_task = calc_task;

    AsdTask_CreateDraw(
        "SAVELOAD_UI UD",
        0x7F,
        0,
        0,
        reinterpret_cast<void (*)(void*)>(0x001ED8B4),
        0,
        0,
        calc_task);
    AsdTask_CreateDraw(
        "SAVELOAD_UI UDD",
        0xDD,
        0,
        0,
        reinterpret_cast<void (*)(void*)>(0x001ED8B4),
        0,
        0,
        calc_task);
    AsdTask_CreateDraw(
        "SAVELOAD_UI D",
        0xE8,
        0,
        0,
        reinterpret_cast<void (*)(void*)>(0x00214964),
        0,
        0,
        calc_task);

    *reinterpret_cast<u32*>(raw + 0x08) = 0;
    *reinterpret_cast<u32*>(raw + 0x0C) = 0;
    *reinterpret_cast<u32*>(mgr_bytes + 0x0C) = *reinterpret_cast<const u32*>(mgr_bytes + 0x08);

    void* const buf_a = engine_func_002c54f0(0x100, 0x100, 0, 0x80, 1);
    *reinterpret_cast<void**>(raw + 0x37C) = buf_a;
    void* const buf_b = engine_func_002c54f0(0x100, 0x100, 0, 8, 1);
    *reinterpret_cast<void**>(raw + 0x380) = buf_b;
    void* const buf_c = engine_func_002c54f0(0x100, 0x100, 0, kSlotSize, 1);
    *reinterpret_cast<void**>(raw + 0x384) = buf_c;

    ui_func_002bcf58(buf_a, ui_func_0026b844(), 0x80);
    ui_func_002adb40(buf_b, ui_func_0026b830());
    ui_func_002bcf58(buf_c, ui_func_002c0b94(), kSlotSize);
    ui_func_002bcf58(raw + 0x364, ui_func_002c0b94() + 8, 0x0E);

    *reinterpret_cast<u32*>(raw + 0x240) = 0;
    *reinterpret_cast<u32*>(raw + 0x244) = 0;
    *reinterpret_cast<u32*>(raw + 0x248) = 0;
    func_00297704("saveLoadUI/saveloadUI.bf", raw + 0x240, 0);
    func_00297704("saveLoadUI/saveloadUI.mbm", raw + 0x244, 0);

    func_002c4e28(0x36);
    func_002a6214(0x36, 0);
    func_002976ac(0x3D);
    *reinterpret_cast<u32*>(raw + 0x360) = func_0029a2d0("player/pl_dammy.bam", 7);

    *reinterpret_cast<f32*>(raw + 0x374) = 0.5f;
    *reinterpret_cast<u32*>(raw + 0x18) = *reinterpret_cast<const u32*>(mgr_bytes + 0x08);
    raw[0x28] = 0;
    *reinterpret_cast<f32*>(raw + 0x1C) = 1.0f;
    *reinterpret_cast<u32*>(raw + 0x24) = 0;
    *reinterpret_cast<f32*>(raw + 0x38) = 0.0f;
    *reinterpret_cast<f32*>(raw + 0x3C) = 0.0f;
    raw[0x48] = 0;
    raw[0x54] = 0;
    raw[0x55] = 0;
    raw[0x73] = 0;
    raw[0x72] = 0;
    *reinterpret_cast<u32*>(raw + 0x60) = 4;
    *reinterpret_cast<u32*>(raw + 0x58) = 0;
    raw[0x354] = 0;
    raw[0x37A] = 0;
    raw[0x355] = 0;
    *reinterpret_cast<u32*>(raw + 0x6C) = 0x320;
    *reinterpret_cast<u32*>(raw + 0x68) = 0x280;
    *reinterpret_cast<u32*>(raw + 0x64) = 0x140;
    *reinterpret_cast<u32*>(raw + 0x35C) = 0;
    raw[0x5C] = 0;
    raw[0x70] = 0;
    raw[0x71] = 0;
    *reinterpret_cast<f32*>(raw + 0x20) = 30.0f;
    *reinterpret_cast<f32*>(raw + 0x1C) = 0.0f;
    *reinterpret_cast<f32*>(raw + 0x2C) = 0.5f;
    *reinterpret_cast<f32*>(raw + 0x30) = 0.5f;

    func_002c3344(raw + 0x7C);
    func_002c32f8(raw + 0x7C, kTargetW - 0x3C, 0x3C, 0, 0, 0, 0, 0, 0, kTargetW, 0xE0);
    func_002bdb2c(raw + 0x9C, 0x36, 1, raw + 0x7C, 0xC9, 1.0f);
    func_002bf0a8(raw + 0x128, 0x36, 0x51, 2, raw + 0x7C, 2, 1.0f);
    func_002bf0a8(raw + 0x1B4, 0x36, 0x52, 2, raw + 0x7C, 2, 1.0f);
    func_002bdac0(raw + 0x9C, 1, 0);
    func_002bdac0(raw + 0x128, 3, 0);
    func_002bdac0(raw + 0x1B4, 4, 0);
    func_002b8b78(0xA8);
    AsdMem_Zero(raw + 0x24C, 0x80);
    AsdMem_Zero(raw + 0x2CC, 0x80);
    raw[0x34C] = 0;
    raw[0x34D] = 0;
    *reinterpret_cast<void**>(raw + 0x350) = engine_func_002c54f0(0x100, 0x100, 0, 0x8C, 1);
    *reinterpret_cast<u32*>(raw + 0x18) = *reinterpret_cast<const u32*>(mgr_bytes + 0x08);
    raw[0x378] = 0;
}

// DECOMP_FUNC(0x0026b874, 304)


// ============================================================================
// SaveLoadProcess: Threaded Save/Load I/O Stream Manager
// ============================================================================

void* SaveLoadProcess_Init(void* arg) {
    u8* const proc = static_cast<u8*>(AsdMem_Alloc(0x100, 0x100, 0, 0x18, 1));
    ui_func_0026b7ec(1);
    camp_func_002594cc(1);
    ui_func_002594ac(1);
    *reinterpret_cast<u32*>(proc + 0x08) = 0;

    const u8* const sys_work = ui_func_002c0b94();
    const u8 sys_flag = sys_work[0x03];
    *reinterpret_cast<u32*>(proc + 0x10) = (sys_flag == 0) ? 1u : static_cast<u32>(sys_flag);

    auto* const mgr = reinterpret_cast<u8*>(0x0043E2F0);
    mgr[0x03] = 0;
    mgr[0x04] = 0;
    *reinterpret_cast<u32*>(mgr + 0x08) = 0;
    *reinterpret_cast<u16*>(mgr + 0x06) = 0;

    void* const task = AsdTask_CreateCalc(
        "Load",
        2,
        0,
        0,
        reinterpret_cast<void (*)(void*)>(&SaveLoadProcess_Step),
        reinterpret_cast<void*>(&ui_func_00324d6c),
        static_cast<u32>(reinterpret_cast<uintptr_t>(proc)));
    *reinterpret_cast<void**>(proc + 0x00) = task;
    ui_func_001ec8e4(task, 0x80000, 0);

    *reinterpret_cast<u32*>(proc + 0x10) = static_cast<u32>(reinterpret_cast<uintptr_t>(arg));
    mgr[0x00] = 0;
    mgr[0x01] = 0;
    mgr[0x02] = 0;
    *reinterpret_cast<s32*>(proc + 0x04) = 4;
    return *reinterpret_cast<void**>(proc + 0x00);
}
// DECOMP_FUNC(0x002ef9ac, 420)


// DECOMP_FUNC(0x002ef9ac, 420)
s32 SaveLoadProcess_Step(void*) {
    static constexpr u32 kBufferSize = 0x24DB0;
    static constexpr u32 kHeaderSize = 0x80;
    static constexpr u32 kMidSize = 0x08;
    static constexpr u32 kPayloadSize = 0x24D28;

    u8* const proc = ui_func_002c0ac8();
    auto* const state = reinterpret_cast<s32*>(proc + 0x04);
    auto* const mgr = reinterpret_cast<u8*>(0x0043E2F0);

    switch (*state) {
    case 4: {
        *reinterpret_cast<u32*>(proc + 0x0C) = kBufferSize;
        void* const buf = engine_func_002c54f0(0x100, 0x100, 0, kBufferSize, 1);
        *reinterpret_cast<void**>(proc + 0x08) = buf;
        SaveLoad_Thread_func_00247c64(
            3, 0, *reinterpret_cast<const u32*>(proc + 0x10), buf,
            *reinterpret_cast<const u32*>(proc + 0x0C));
        *state = 5;
        return 0;
    }
    case 5: {
        if (script_vm_func_001a1bf8() == 1) {
            if (SearchWin_Dismiss()) {
                *state = 7;
                return 0;
            }
            const auto* const buf = *reinterpret_cast<const u8* const*>(proc + 0x08);
            ui_func_002bcf58(ui_func_0026b844(), buf, kHeaderSize);
            ui_func_002adb40(ui_func_0026b830(), buf + kHeaderSize);
            ui_func_002bcf58(ui_func_002c0b94(), buf + kHeaderSize + kMidSize, kPayloadSize);
            ui_func_002c0b94()[3] = static_cast<u8>(*reinterpret_cast<const u32*>(proc + 0x10));
            ui_func_0026b734();
            *state = 6;
        }
        return 0;
    }
    case 6:
        mgr[3] = 1;
        mgr[0] = 1;
        return -1;
    case 7:
        mgr[3] = 0;
        mgr[0] = 1;
        return -1;
    default:
        return 0;
    }
}
// DECOMP_FUNC(0x002efb50, 456)
s32 SaveLoadProcess_Write(void*) {
    static constexpr u32 kBufferSize = 0x24DB0;
    static constexpr u32 kHeaderSize = 0x80;
    static constexpr u32 kMidSize = 0x08;
    static constexpr u32 kPayloadSize = 0x24D28;

    u8* const proc = ui_func_002c0ac8();
    auto* const state = reinterpret_cast<s32*>(proc + 0x04);
    auto* const mgr = reinterpret_cast<u8*>(0x0043E2F0);

    switch (*state) {
    case 0: {
        *reinterpret_cast<u32*>(proc + 0x0C) = kBufferSize;
        auto* const buf = static_cast<u8*>(
            AsdMem_Alloc(0x100, 0x100, 0, kBufferSize, 1));
        *reinterpret_cast<u8**>(proc + 0x08) = buf;
        ui_func_002e0c54();
        ui_func_002c0b94()[3] = static_cast<u8>(*reinterpret_cast<const u32*>(proc + 0x10));
        engine_func_002c5ff4(buf, ui_func_0026b844(), kHeaderSize);
        ui_func_002adb40(buf + kHeaderSize, ui_func_0026b830());
        u8* const payload = buf + kHeaderSize + kMidSize;
        ui_func_002bcf58(payload, ui_func_002c0b94(), kPayloadSize);
        *reinterpret_cast<u16*>(payload) = 3;
        payload[2] = proc[0x14];
        ui_func_0026b734();
        SaveLoad_Thread_func_00247c64(
            2, 0, *reinterpret_cast<const u32*>(proc + 0x10), buf,
            *reinterpret_cast<const u32*>(proc + 0x0C));
        *state = 1;
        return 0;
    }
    case 1: {
        if (script_vm_func_001a1bf8() == 1) {
            const bool dismissed = SearchWin_Dismiss();
            engine_func_002c4360(*reinterpret_cast<void**>(proc + 0x08));
            *reinterpret_cast<void**>(proc + 0x08) = nullptr;
            *state = dismissed ? 3 : 2;
        }
        return 0;
    }
    case 2:
        mgr[1] = 1;
        mgr[4] = 1;
        return -1;
    case 3:
        mgr[1] = 1;
        mgr[4] = 0;
        return -1;
    default:
        return 0;
    }
}
// DECOMP_FUNC(0x00322d70, 412)
void* SaveLoadProcess_Read(void*) {
    auto* const proc = static_cast<u8*>(
        AsdMem_Alloc(0x100, 0x100, 0, sizeof(SaveLoadProcess), 1));
    ui_func_0026b7ec(1);
    camp_func_002594cc(1);
    ui_func_002594ac(1);
    *reinterpret_cast<void**>(proc + 0x08) = nullptr;

    const u32 slot = ui_func_002c0b94()[3];
    *reinterpret_cast<u32*>(proc + 0x10) = (slot == 0) ? 1u : slot;

    auto* const mgr = reinterpret_cast<u8*>(0x0043E2F0);
    mgr[3] = 0;
    mgr[4] = 0;
    *reinterpret_cast<u32*>(mgr + 8) = 0;
    *reinterpret_cast<u16*>(mgr + 6) = 0;
    mgr[0] = 0;
    mgr[1] = 0;
    mgr[2] = 0;

    void* const task = AsdTask_CreateCalc(
        "Boot", 2, 0, 0, camp_func_002ef890,
        reinterpret_cast<void*>(&ui_func_00324d6c),
        static_cast<u32>(reinterpret_cast<std::uintptr_t>(proc)));
    *reinterpret_cast<void**>(proc + 0x00) = task;
    ui_func_001ec8e4(task, 0x80000, 0);

    AsdTask_CreateDraw(
        "Boot UpDraw", 0x81, 0, 0, ui_func_00311350, 0, 0,
        *reinterpret_cast<void**>(proc + 0x00));
    AsdTask_CreateDraw(
        "Boot UpDraw_R", 0xDF, 0, 0, ui_func_00311350, 0, 0,
        *reinterpret_cast<void**>(proc + 0x00));

    *reinterpret_cast<u32*>(proc + 0x04) = 8;
    return *reinterpret_cast<void**>(proc + 0x00);
}
// DECOMP_FUNC(0x00322f0c, 304)
void* SaveLoadProcess_Close(u32 slot, u8 flag) {
    auto* const proc = static_cast<u8*>(
        AsdMem_Alloc(0x100, 0x100, 0, sizeof(SaveLoadProcess), 1));
    ui_func_0026b7ec(1);
    camp_func_002594cc(1);
    ui_func_002594ac(1);
    *reinterpret_cast<void**>(proc + 0x08) = nullptr;

    const u32 cur_slot = ui_func_002c0b94()[3];
    *reinterpret_cast<u32*>(proc + 0x10) = (cur_slot == 0) ? 1u : cur_slot;

    auto* const mgr = reinterpret_cast<u8*>(0x0043E2F0);
    mgr[3] = 0;
    mgr[4] = 0;
    *reinterpret_cast<u32*>(mgr + 8) = 0;
    *reinterpret_cast<u16*>(mgr + 6) = 0;
    mgr[0] = 0;
    mgr[1] = 0;
    mgr[2] = 0;

    *reinterpret_cast<u32*>(proc + 0x10) = slot;
    void* const task = AsdTask_CreateCalc(
        "Save", 2, 0, 0,
        reinterpret_cast<void (*)(void*)>(SaveLoadProcess_Write),
        reinterpret_cast<void*>(&ui_func_00324d6c),
        static_cast<u32>(reinterpret_cast<std::uintptr_t>(proc)));
    *reinterpret_cast<void**>(proc + 0x00) = task;
    ui_func_001ec8e4(task, 0x80000, 0);

    *reinterpret_cast<u32*>(proc + 0x04) = 0;
    proc[0x14] = flag;
    return *reinterpret_cast<void**>(proc + 0x00);
}

} // namespace smt4::ui
