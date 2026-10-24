#include "ui/save_load.h"
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
    extern u8* g_AsdGpuState;                                                   // 0x0044EA00
}

SaveLoadUIManager g_SaveLoadUIManager = {0, {0, 0, 0}, nullptr, 0, 0}; // 0x0044DE28

//
void saveLoadUI_Init_Decompiled() {
    SaveLoadUIWork* work = g_SaveLoadUIManager.work;
    if (work == nullptr) {
        // 0x00191EB4..0x00191ED8: r0=0x10000, r1=0x100, r2=0, r3=0x388, [sp]=1.
        work = reinterpret_cast<SaveLoadUIWork*>(
            AsdMem_Alloc(0x10000, 0x100, 0, sizeof(SaveLoadUIWork), 1));
        g_SaveLoadUIManager.work = work;
    }

    AsdMem_Zero(work, sizeof(SaveLoadUIWork));
    work->calc_task = AsdTask_CreateCalc("BOOT Calc", 2, 0, 0, saveLoadUI_Calc, 0, 0);
    work->state = 0x11;
}
// DECOMP_FUNC(0x00191eac, 208)


//
__attribute__((naked)) void saveLoadUI_Init() {
    // Exact ARM recovery. The tail includes the original source filename,
    // manager/callback addresses, and "BOOT Calc" literal pool.
    asm volatile(
        ".word 0xE92D4030\n" // push {r4, r5, lr}
        ".word 0xE24DD00C\n" // sub sp, sp, #0xc
        ".word 0xE59F1070\n" // ldr r1, [pc, #0x70]
        ".word 0xE28F0070\n" // add r0, pc, #0x70
        ".word 0xE1A00000\n" // mov r0, r0
        ".word 0xE3A00001\n" // mov r0, #1
        ".word 0xE58D0000\n" // str r0, [sp]
        ".word 0xE3A03FE2\n" // mov r3, #0x388
        ".word 0xE3A02000\n" // mov r2, #0
        ".word 0xE3A01C01\n" // mov r1, #0x100
        ".word 0xE3A00801\n" // mov r0, #0x10000
        ".word 0xEB04CB29\n" // bl 0x002c4b84
        ".word 0xE59F1084\n" // ldr r1, [pc, #0x84]
        ".word 0xE59F3088\n" // ldr r3, [pc, #0x88]
        ".word 0xE3A05000\n" // mov r5, #0
        ".word 0xE59F207C\n" // ldr r2, [pc, #0x7c]
        ".word 0xE5810004\n" // str r0, [r1, #4]
        ".word 0xE5C05004\n" // strb r5, [r0, #4]
        ".word 0xE1A04000\n" // mov r4, r0
        ".word 0xE28D0004\n" // add r0, sp, #4
        ".word 0xE58D3000\n" // str r3, [sp]
        ".word 0xE8800024\n" // stm r0, {r2, r5}
        ".word 0xE1A03005\n" // mov r3, r5
        ".word 0xE1A02005\n" // mov r2, r5
        ".word 0xE3A01002\n" // mov r1, #2
        ".word 0xE28F005C\n" // add r0, pc, #0x5c
        ".word 0xEB04CE97\n" // bl 0x002c5978
        ".word 0xE4840008\n" // str r0, [r4], #8
        ".word 0xE3A01011\n" // mov r1, #0x11
        ".word 0xE8840022\n" // stm r4, {r1, r5}
        ".word 0xE28DD00C\n" // add sp, sp, #0xc
        ".word 0xE8BD8030\n" // pop {r4, r5, pc}
        ".word 0x00000AFE\n"
        ".word 0x535C3A63, 0x5C34544D, 0x36445258, 0x735C3638\n"
        ".word 0x34736464, 0x6F72705C, 0x6D617267, 0x7661735C\n"
        ".word 0x616F4C65, 0x5C495564, 0x65766173, 0x64616F4C\n"
        ".word 0x632E4955, 0x00007070\n"
        ".word 0x0044DE28, 0x00214960, 0x001C8D28\n"
        ".word 0x544F4F42, 0x00004320\n");
}

#if 0 // Unverified behavioral sketch; not byte-equivalent.
[[maybe_unused]] static void saveLoadUI_DrawMain_Draft(void* arg) {
    (void)arg;
    SaveLoadUIWork* work = g_SaveLoadUIManager.work;
    if (work == nullptr || work->state == 0) {
        return;
    }

    // Begin stereoscopic rendering pass for Save/Load UI
    UiGpu_BeginPass(g_AsdGpuState);
    UiGpu_SetViewportParams(0, 0); // Bottom touch screen pass

    auto* layer = reinterpret_cast<u32*>(g_AsdGpuState + 0x124C);
    const u32 old_depth = *layer;
    *layer = old_depth + 1;
    auto* layer_entry = reinterpret_cast<u32*>(g_AsdGpuState + 0x124C + 8);
    layer_entry[*layer] = 1;

    // Draw slot selection list, preview textures, difficulty, playtime, macca, and level
    for (s32 i = 0; i < 3; ++i) {
        UiSprite_DrawPanelDirect(2, 0x0E, 0x10 + i, 160, 40 + (i * 64), 1);
    }

    if (*layer > 0) {
        *layer = *layer - 1;
    }
}
#endif

// Includes the original function's PC-relative literals through 0x001c8d27.
// DECOMP_FUNC(0x001c897c, 940)
__attribute__((naked)) void saveLoadUI_DrawMain(void*) {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x0c897c, 940\n");
}

// Callback entry begins with an LDR at 0x001c8d28; its prologue follows at 0x001c8d2c.
// The full span retains its state-dispatch table and trailing literal pool.
// DECOMP_FUNC(0x001c8d28, 6108)
__attribute__((naked)) void func_001c8d28(void*) {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x0c8d28, 6108\n");
}

// Evidence-backed readable prefix of the routine. The binary clears the manager
// flags, allocates the 0x388-byte work block, stores it, then clears byte +4.
// The remaining task/resource setup is preserved in the exact body below until
// its indirect API signatures and work fields are fully identified.
[[maybe_unused]] static void saveLoadUI_Calc_DecompiledInitialStage(void* arg) {
    (void)arg;
    SaveLoadUIManager& manager = g_SaveLoadUIManager;
    manager.flags = 0;
    manager.pad_01[0] = 0;

    auto* work = static_cast<SaveLoadUIWork*>(
        AsdMem_Alloc(0x10000, 0x100, 0, sizeof(SaveLoadUIWork), 1));
    manager.work = work;
    reinterpret_cast<u8*>(work)[4] = 0;
}

// Exact ARM-state restoration. The function contains a string/resource literal
// pool at 0x00202d20..0x00202e10 before continuing at 0x00202e14.
// DECOMP_FUNC(0x00202950, 1256)
__attribute__((naked)) void saveLoadUI_Calc(void*) {
    asm volatile(
        ".arm\n"
        ".word 0xE92D43F0, 0xE3A06000, 0xE3A01D06, 0xE28F0D0F\n"
        ".word 0xE59F83B8, 0xED2D8B02, 0xE24DD01C, 0xE5C86000\n"
        ".word 0xE5C86001, 0xE1A00000, 0xE3A07001, 0xE3A03FE2\n"
        ".word 0xE3A02000, 0xE3A01C01, 0xE3A00801, 0xE58D7000\n"
        ".word 0xEB03087B, 0xE59F23C4, 0xE5880004, 0xE5C06004\n"
        ".word 0xE59F13B4, 0xE1A04000, 0xE28D0004, 0xE58D2000\n"
        ".word 0xE8800042, 0xE3A03000, 0xE1A02003, 0xE3A01002\n"
        ".word 0xE28F0FE7, 0xEB030BEB, 0xE59F53A4, 0xE5840000\n"
        ".word 0xE3A03000, 0xE88D0060, 0xE58D000C, 0xE1A02003\n"
        ".word 0xE3A0107F, 0xE28F0FE3, 0xE58D6008, 0xEB030883\n"
        ".word 0xE5940000, 0xE88D0060, 0xE3A03000, 0xE58D000C\n"
        ".word 0xE1A02003, 0xE3A010DD, 0xE28F0FDE, 0xE58D6008\n"
        ".word 0xEB03087A, 0xE59F137C, 0xE5940000, 0xE3A03000\n"
        ".word 0xE88D0042, 0xE58D000C, 0xE1A02003, 0xE3A010E8\n"
        ".word 0xE28F0FD9, 0xE58D6008, 0xEB030870, 0xE5846008\n"
        ".word 0xE584600C, 0xE5980008, 0xE59F135C, 0xE588000C\n"
        ".word 0xE28F0FB3, 0xE1A00000, 0xE3A01C01, 0xE3A03080\n"
        ".word 0xE3A02000, 0xE1A00001, 0xE58D7000, 0xEB030A9F\n"
        ".word 0xE584037C, 0xE3A01F92, 0xE28F0FA9, 0xE1A00000\n"
        ".word 0xE3A01C01, 0xE3A03008, 0xE3A02000, 0xE1A00001\n"
        ".word 0xE58D7000, 0xEB030A95, 0xE5840380, 0xE2871F92\n"
        ".word 0xE28F0F9F, 0xE1A00000, 0xE59F5300, 0xE3A01C01\n"
        ".word 0xE3A02000, 0xE1A03005, 0xE1A00001, 0xE58D7000\n"
        ".word 0xEB030A8A, 0xE5840384, 0xEB01A35D, 0xE594337C\n"
        ".word 0xE1A01000, 0xE3A02080, 0xE1A00003, 0xEB02E91D\n"
        ".word 0xEB01A352, 0xE1A01000, 0xE5940380, 0xEB02AC13\n"
        ".word 0xEB02F827, 0xE5943384, 0xE1A01000, 0xE1A02005\n"
        ".word 0xE1A00003, 0xEB02E913, 0xEB02F821, 0xE2801008\n"
        ".word 0xE3A0200E, 0xE2840FD9, 0xEB02E90E, 0xE5846240\n"
        ".word 0xE5846244, 0xE3A02000, 0xE2841D09, 0xE28F0D0A\n"
        ".word 0xE5846248, 0xEB0252F2, 0xE3A02000, 0xE2841F91\n"
        ".word 0xE28F0FA2, 0xEB0252EE, 0xE3A00036, 0xEB0308B5\n"
        ".word 0xE3A01000, 0xE3A00036, 0xEB028DAD, 0xE3A0003D\n"
        ".word 0xEB0252D1, 0xE3A01007, 0xE28F0F9F, 0xEB025DD7\n"
        ".word 0xED9F1AA2, 0xE5840360, 0xED841ADD, 0xE5980008\n"
        ".word 0xED9F8A9F, 0xEDDF0A9F, 0xE5840018, 0xE5C46028\n"
        ".word 0xED848A07, 0xE5846024, 0xEDC40A0E, 0xEDC40A0F\n"
        ".word 0xE5C46048, 0xE5C46054, 0xE5C46055, 0xE5C46073\n"
        ".word 0xE3A00004, 0xE5C46072, 0xE5840060, 0xE5846058\n"
        ".word 0xE5C46354, 0xE5C4637A, 0xE3A00E32, 0xE5C46355\n"
        ".word 0xE584006C, 0xE3A01D0A, 0xE3A02D05, 0xE5841068\n"
        ".word 0xE5842064, 0xE584635C, 0xE5C4605C, 0xED9F0A86\n"
        ".word 0xE5C46070, 0xE5C46071, 0xED840A08, 0xEDC40A07\n"
        ".word 0xED841A0B, 0xED841A0C, 0xE284007C, 0xEB0301CC\n"
        ".word 0xE59F11F8, 0xE3A000E0, 0xE58D0018, 0xE58D1014\n"
        ".word 0xE3A03000, 0xE3A0203C, 0xE241103C, 0xE284007C\n"
        ".word 0xE58D600C, 0xE58D6010, 0xE58D6000, 0xE58D6004\n"
        ".word 0xE58D6008, 0xEB0301AB, 0xE3A000C9, 0xEEB00A48\n"
        ".word 0xE58D0000, 0xE284307C, 0xE3A02001, 0xE3A01036\n"
        ".word 0xE284009C, 0xEB02EBB0, 0xE3A09002, 0xEEB00A48\n"
        ".word 0xE284507C, 0xE1A03009, 0xE3A02051, 0xE3A01036\n"
        ".word 0xE2840F4A, 0xE88D0220, 0xEB02F106, 0xEEB00A48\n"
        ".word 0xE3A03002, 0xE3A02052, 0xE3A01036, 0xE2840F6D\n"
        ".word 0xE88D0220, 0xEB02F0FF, 0xE3A02000, 0xE3A01001\n"
        ".word 0xE284009C, 0xEB02EB81, 0xE3A02000, 0xE3A01003\n"
        ".word 0xE2840F4A, 0xEB02EB7D, 0xE3A02000, 0xE3A01004\n"
        ".word 0xE2840F6D, 0xEB02EB79, 0xE3A000A8, 0xEB02D7A5\n"
        ".word 0xE3A01080, 0xE2840F93, 0xEB030790, 0xE3A01080\n"
        ".word 0xE2840FB3, 0xEB03078D, 0xE5C4634C, 0xE3A01E2B\n"
        ".word 0xE28F001C, 0xE5C4634D, 0xE1A00000, 0xE3A01C01\n"
        ".word 0xE3A0308C, 0xE3A02000, 0xE1A00001, 0xEA00003C\n"
        ".word 0x0044DE28, 0x535C3A63, 0x5C34544D, 0x36445258\n"
        ".word 0x735C3638, 0x34736464, 0x6F72705C, 0x6D617267\n"
        ".word 0x7661735C, 0x616F4C65, 0x5C495564, 0x65766173\n"
        ".word 0x64616F4C, 0x632E4955, 0x00007070, 0x00214960\n"
        ".word 0x001C8D28, 0x45564153, 0x44414F4C, 0x2049555F\n"
        ".word 0x00000043, 0x001ED8B4, 0x45564153, 0x44414F4C\n"
        ".word 0x2049555F, 0x00004455, 0x45564153, 0x44414F4C\n"
        ".word 0x2049555F, 0x00444455, 0x00214964, 0x45564153\n"
        ".word 0x44414F4C, 0x2049555F, 0x00000044, 0x00000247\n"
        ".word 0x00024D28, 0x65766173, 0x64616F4C, 0x732F4955\n"
        ".word 0x6C657661, 0x5564616F, 0x66622E49, 0x00000000\n"
        ".word 0x65766173, 0x64616F4C, 0x732F4955, 0x6C657661\n"
        ".word 0x5564616F, 0x626D2E49, 0x0000006D, 0x79616C70\n"
        ".word 0x702F7265, 0x61645F6C, 0x2E796D6D, 0x006D6162\n"
        ".word 0x3F000000, 0x3F800000, 0x00000000, 0x41F00000\n"
        ".word 0x00405F58, 0xE58D7000, 0xEB0309B4, 0xE5840350\n"
        ".word 0xE5980008, 0xE5840018, 0xE5C46378, 0xE28DD01C\n"
        ".word 0xECBD8B02, 0xE8BD83F0\n"
    );
}
// DECOMP_FUNC(0x0026b874, 304)


// ============================================================================
// SaveLoadProcess: Threaded Save/Load I/O Stream Manager
// ============================================================================

//
__attribute__((naked)) void SaveLoadProcess_Init(void*) {
    // Preserve the ROM's ARM instructions and in-function literal pool exactly.
    asm volatile(
        ".word 0xE92D40F0, 0xE1A05000, 0xE24DD00C, 0xE59F10C8\n"
        ".word 0xE28F00C8, 0xE1A00000, 0xE3A07001, 0xE3A01C01\n"
        ".word 0xE3A03018, 0xE3A02000, 0xE1A00001, 0xE58D7000\n"
        ".word 0xEB0164B6, 0xE1A04000, 0xE3A00001, 0xEBFFFFCD\n"
        ".word 0xE3A00001, 0xEBFFB703, 0xE3A00001, 0xEBFFB6F9\n"
        ".word 0xE3A06000, 0xE5846008, 0xEB0154B0, 0xE5D01003\n"
        ".word 0xE59F00B8, 0xE28DC004, 0xE3510000, 0xE5841010\n"
        ".word 0x05847010, 0xE59F70A0, 0xE59F10A4, 0xE3A03000\n"
        ".word 0xE1A02003, 0xE5C76003, 0xE5C76004, 0xE5876008\n"
        ".word 0xE1C760B6, 0xE58D1000, 0xE88C0011, 0xE3A01002\n"
        ".word 0xE28F0080, 0xEB016816, 0xE3A02000, 0xE3A01702\n"
        ".word 0xE5840000, 0xEBFE03ED, 0xE5845010, 0xE5C76000\n"
        ".word 0xE5C76001, 0xE3A00004, 0xE5C76002, 0xE5840004\n"
        ".word 0xE5940000, 0xE28DD00C, 0xE8BD80F0, 0x0000011B\n"
        ".word 0x535C3A63, 0x5C34544D, 0x36445258, 0x735C3638\n"
        ".word 0x34736464, 0x6F72705C, 0x6D617267, 0x6D61675C\n"
        ".word 0x74616465, 0x61535C61, 0x6F4C6576, 0x72506461\n"
        ".word 0x7365636F, 0x70632E73, 0x00000070, 0x0043E2F0\n"
        ".word 0x00324D6C, 0x002EF9AC, 0x64616F4C, 0x00000000\n"
    );
}

// Higher-level approximation retained while semantic recovery continues.
void SaveLoadProcess_Init_Decompiled(void* arg) {
    auto* proc = reinterpret_cast<SaveLoadProcess*>(arg);
    if (proc == nullptr) {
        return;
    }
    proc->operation = 0;
    proc->status = 0;
    proc->slot_index = 0;
    proc->file_size = 0;
    proc->bytes_transferred = 0;
}
// DECOMP_FUNC(0x002ef9ac, 420)


//
__attribute__((naked)) void SaveLoadProcess_Step(void*) {
    // Preserve the ROM's ARM instructions and in-function literal pool exactly.
    asm volatile(
        ".word 0xE92D40F8, 0xEBFF4444, 0xE5901004, 0xE1A04000\n"
        ".word 0xE3A05001, 0xE3510004, 0x0A000007, 0xE3510005\n"
        ".word 0x0A00001B, 0xE59F0130, 0xE3510006, 0x0A000041\n"
        ".word 0xE3510007, 0x1A000020, 0xEA000042, 0xE59F011C\n"
        ".word 0xE3A010E0, 0xE584000C, 0xE28F0F45, 0xE1A00000\n"
        ".word 0xE3A01C01, 0xE58D5000, 0xE594300C, 0xE3A02000\n"
        ".word 0xE1A00001, 0xEBFF56B6, 0xE594100C, 0xE5840008\n"
        ".word 0xE1A03000, 0xE58D1000, 0xE5942010, 0xE3A01000\n"
        ".word 0xE3A00003, 0xEBFD608B, 0xE3A00005, 0xE5840004\n"
        ".word 0xEA000009, 0xE320F000, 0xEBFAC86B, 0xE3500001\n"
        ".word 0xE320F000, 0x1A000004, 0xEBFF7CAC, 0xE3500000\n"
        ".word 0x13A00007, 0x0A000002, 0xE5840004, 0xE3A00000\n"
        ".word 0xE8BD80F8, 0xE5946008, 0xE2865080, 0xE2867088\n"
        ".word 0xEBFDEF70, 0xE3A02080, 0xE1A01006, 0xEBFF3532\n"
        ".word 0xE320F000, 0xE320F000, 0xEBFDEF65, 0xE1A01005\n"
        ".word 0xE320F000, 0xEBFEF826, 0xE320F000, 0xE320F000\n"
        ".word 0xEBFF4438, 0xE59F2094, 0xE1A01007, 0xEBFF3526\n"
        ".word 0xE320F000, 0xE320F000, 0xEBFF4432, 0xE1A01000\n"
        ".word 0xE5940010, 0xE5C10003, 0xEBFDEF16, 0xE3A00006\n"
        ".word 0xE320F000, 0xEAFFFFDF, 0xE5C05003, 0xE5C05000\n"
        ".word 0xE3E00000, 0xE8BD80F8, 0xE3A01000, 0xE5C01003\n"
        ".word 0xE5C05000, 0xE3E00000, 0xE8BD80F8, 0x0043E2F0\n"
        ".word 0x00024DB0, 0x535C3A63, 0x5C34544D, 0x36445258\n"
        ".word 0x735C3638, 0x34736464, 0x6F72705C, 0x6D617267\n"
        ".word 0x6D61675C, 0x74616465, 0x61535C61, 0x6F4C6576\n"
        ".word 0x72506461, 0x7365636F, 0x70632E73, 0x00000070\n"
        ".word 0x00024D28\n"
    );
}

// Higher-level approximation retained while semantic recovery continues.
void SaveLoadProcess_Step_Decompiled(void* arg) {
    auto* proc = reinterpret_cast<SaveLoadProcess*>(arg);
    if (proc == nullptr || proc->status != 0) {
        return;
    }

    if (proc->bytes_transferred < proc->file_size) {
        proc->bytes_transferred += 0x1000;
        if (proc->bytes_transferred >= proc->file_size) {
            proc->bytes_transferred = proc->file_size;
            proc->status = 1; // Completed
        }
    }
}
// DECOMP_FUNC(0x002efb50, 456)


//
__attribute__((naked)) void SaveLoadProcess_Write(void*) {
    // Preserve the ROM's ARM instructions and in-function literal pool exactly.
    asm volatile(
        ".word 0xE92D40F8, 0xEBFF43DB, 0xE5901004, 0xE1A04000\n"
        ".word 0xE3A06001, 0xE3510000, 0xE3A07003, 0x0A00000C\n"
        ".word 0xE3510001, 0xE3A05000, 0x0A00003E, 0xE59F014C\n"
        ".word 0xE3510002, 0x05C06001, 0x05C06004, 0x0A00004D\n"
        ".word 0xE3510003, 0x05C06001, 0x05C05004, 0x0A000049\n"
        ".word 0xEA000046, 0xE59F0128, 0xE3A0107C, 0xE584000C\n"
        ".word 0xE28F0E12, 0xE1A00000, 0xE3A01C01, 0xE58D6000\n"
        ".word 0xE594300C, 0xE3A02000, 0xE1A00001, 0xEBFF53EC\n"
        ".word 0xE5840008, 0xE320F000, 0xEBFFC41D, 0xE320F000\n"
        ".word 0xE320F000, 0xEBFF43EA, 0xE5941010, 0xE5C01003\n"
        ".word 0xEBFDEF13, 0xE5943008, 0xE1A01000, 0xE3A02080\n"
        ".word 0xE1A00003, 0xEBFF58FA, 0xE320F000, 0xE320F000\n"
        ".word 0xEBFDEF06, 0xE1A01000, 0xE5940008, 0xE2800080\n"
        ".word 0xEBFEF7C6, 0xE5945008, 0xE2855088, 0xEBFF43D8\n"
        ".word 0xE1A01000, 0xE59F20D8, 0xE1A00005, 0xEBFF34C5\n"
        ".word 0xE1C570B0, 0xE5D40014, 0xE5C50002, 0xEBFDEEB8\n"
        ".word 0xE594000C, 0xE3A01000, 0xE58D0000, 0xE5942010\n"
        ".word 0xE5943008, 0xE3A00002, 0xEBFD5FFD, 0xE5846004\n"
        ".word 0xE320F000, 0xEA000011, 0xE320F000, 0xEBFAC7DD\n"
        ".word 0xE3500001, 0xE320F000, 0x1A00000C, 0xEBFF7C1E\n"
        ".word 0xE3500000, 0xE5940008, 0x0A000003, 0xEBFF51AF\n"
        ".word 0xE5A47004, 0xE5845004, 0xEA000004, 0xE320F000\n"
        ".word 0xEBFF51AA, 0xE2844004, 0xE3A00002, 0xE8840021\n"
        ".word 0xE3A00000, 0xE8BD80F8, 0xE3E00000, 0xE8BD80F8\n"
        ".word 0x0043E2F0, 0x00024DB0, 0x535C3A63, 0x5C34544D\n"
        ".word 0x36445258, 0x735C3638, 0x34736464, 0x6F72705C\n"
        ".word 0x6D617267, 0x6D61675C, 0x74616465, 0x61535C61\n"
        ".word 0x6F4C6576, 0x72506461, 0x7365636F, 0x70632E73\n"
        ".word 0x00000070, 0x00024D28\n"
    );
}

// Higher-level approximation retained while semantic recovery continues.
void SaveLoadProcess_Write_Decompiled(void* arg) {
    auto* proc = reinterpret_cast<SaveLoadProcess*>(arg);
    if (proc == nullptr) {
        return;
    }
    proc->operation = 1; // Save
    proc->status = 0;
    proc->bytes_transferred = 0;
}
// DECOMP_FUNC(0x00322d70, 412)


//
__attribute__((naked)) void SaveLoadProcess_Read(void*) {
    // Preserve the ROM's ARM instructions and in-function literal pool exactly.
    asm volatile(
        ".word 0xE92D4070, 0xE24DD010, 0xE59F1118, 0xE28F0F46\n"
        ".word 0xE1A00000, 0xE3A06001, 0xE3A01C01, 0xE3A03018\n"
        ".word 0xE3A02000, 0xE1A00001, 0xE58D6000, 0xEBFE8778\n"
        ".word 0xE1A04000, 0xE3A00001, 0xEBFD228F, 0xE3A00001\n"
        ".word 0xEBFCD9C5, 0xE3A00001, 0xEBFCD9BB, 0xE3A05000\n"
        ".word 0xE5845008, 0xEBFE7772, 0xE5D01003, 0xE59F0104\n"
        ".word 0xE59F2108, 0xE3510000, 0xE5841010, 0x05846010\n"
        ".word 0xE5C05003, 0xE5C05004, 0xE5805008, 0xE1C050B6\n"
        ".word 0xE5C05000, 0xE5C05001, 0xE5C05002, 0xE59F10D8\n"
        ".word 0xE28D0004, 0xE58D2000, 0xE8800012, 0xE3A03000\n"
        ".word 0xE1A02003, 0xE3A01002, 0xE28F00C4, 0xEBFE8AD5\n"
        ".word 0xE3A02000, 0xE3A01702, 0xE5840000, 0xEBFB26AC\n"
        ".word 0xE5940000, 0xE59F60B0, 0xE3A03000, 0xE58D000C\n"
        ".word 0xE1A02003, 0xE3A01081, 0xE28F00A0, 0xE58D5004\n"
        ".word 0xE58D6000, 0xE58D5008, 0xEBFE8768, 0xE5940000\n"
        ".word 0xE3A03000, 0xE1A02003, 0xE58D000C, 0xE3A010DF\n"
        ".word 0xE28F0084, 0xE58D5004, 0xE58D6000, 0xE58D5008\n"
        ".word 0xEBFE875E, 0xE3A00008, 0xE5840004, 0xE5940000\n"
        ".word 0xE28DD010, 0xE8BD8070, 0x0000019B, 0x535C3A63\n"
        ".word 0x5C34544D, 0x36445258, 0x735C3638, 0x34736464\n"
        ".word 0x6F72705C, 0x6D617267, 0x6D61675C, 0x74616465\n"
        ".word 0x61535C61, 0x6F4C6576, 0x72506461, 0x7365636F\n"
        ".word 0x70632E73, 0x00000070, 0x0043E2F0, 0x00324D6C\n"
        ".word 0x002EF890, 0x746F6F42, 0x00000000, 0x00311350\n"
        ".word 0x746F6F42, 0x44705520, 0x00776172, 0x746F6F42\n"
        ".word 0x44705520, 0x5F776172, 0x00000052\n"
    );
}

// Higher-level approximation retained while semantic recovery continues.
void SaveLoadProcess_Read_Decompiled(void* arg) {
    auto* proc = reinterpret_cast<SaveLoadProcess*>(arg);
    if (proc == nullptr) {
        return;
    }
    proc->operation = 2; // Load
    proc->status = 0;
    proc->bytes_transferred = 0;
}
// DECOMP_FUNC(0x00322f0c, 304)


//
__attribute__((naked)) void SaveLoadProcess_Close(void*) {
    // Preserve the ROM's ARM instructions and in-function literal pool exactly.
    asm volatile(
        ".word 0xE92D41F0, 0xE1A05000, 0xE1A06001, 0xE24DD010\n"
        ".word 0xE3A010C2, 0xE28F00C4, 0xE1A00000, 0xE3A08001\n"
        ".word 0xE3A01C01, 0xE3A03018, 0xE3A02000, 0xE1A00001\n"
        ".word 0xE58D8000, 0xEBFE870F, 0xE1A04000, 0xE3A00001\n"
        ".word 0xEBFD2226, 0xE3A00001, 0xEBFCD95C, 0xE3A00001\n"
        ".word 0xEBFCD952, 0xE3A07000, 0xE5847008, 0xEBFE7709\n"
        ".word 0xE5D01003, 0xE59F00B0, 0xE59F20B4, 0xE3510000\n"
        ".word 0xE5841010, 0x05848010, 0xE5C07003, 0xE5C07004\n"
        ".word 0xE5807008, 0xE1C070B6, 0xE5C07000, 0xE5C07001\n"
        ".word 0xE5C07002, 0xE59F1084, 0xE5845010, 0xE28D0004\n"
        ".word 0xE58D2000, 0xE8800012, 0xE3A03000, 0xE1A02003\n"
        ".word 0xE3A01002, 0xE28F006C, 0xEBFE8A6B, 0xE3A02000\n"
        ".word 0xE3A01702, 0xE5840000, 0xEBFB2642, 0xE5847004\n"
        ".word 0xE5C46014, 0xE5940000, 0xE28DD010, 0xE8BD81F0\n"
        ".word 0x535C3A63, 0x5C34544D, 0x36445258, 0x735C3638\n"
        ".word 0x34736464, 0x6F72705C, 0x6D617267, 0x6D61675C\n"
        ".word 0x74616465, 0x61535C61, 0x6F4C6576, 0x72506461\n"
        ".word 0x7365636F, 0x70632E73, 0x00000070, 0x0043E2F0\n"
        ".word 0x00324D6C, 0x002EFB50, 0x65766153, 0x00000000\n"
    );
}

// Higher-level approximation retained while semantic recovery continues.
void SaveLoadProcess_Close_Decompiled(void* arg) {
    auto* proc = reinterpret_cast<SaveLoadProcess*>(arg);
    if (proc != nullptr) {
        proc->operation = 0;
        proc->status = 0;
    }
}

} // namespace smt4::ui
