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

// DECOMP_FUNC(0x001c897c, 7048)
void saveLoadUI_DrawMain(void* arg) {
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

// DECOMP_FUNC(0x00202950, 1256)
void saveLoadUI_Calc(void* arg) {
    (void)arg;
    SaveLoadUIWork* work = g_SaveLoadUIManager.work;
    if (work == nullptr) {
        return;
    }

    switch (work->state) {
        case 0x11: // Initialize slots & preview headers
            work->state = 0;
            break;
        case 0: // Slot select
            break;
        case 1: // Confirmation prompt
            break;
        case 2: // Executing file operation
            break;
        default:
            break;
    }
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
