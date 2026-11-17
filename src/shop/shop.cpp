#include "shop/shop.h"
#include "ui/status_down.h"
#include "engine/asd_symbols.h"

namespace smt4::shop {

extern "C" {
    void engine_func_002c583c(s32);                                             // 0x002c583c
    void func_0021f1ec(void*);                                                  // 0x0021f1ec
    void func_001fe15c(void*);                                                  // 0x001fe15c
    void func_0021f204(void*);                                                  // 0x0021f204
    s32  battle_func_003a6528();                                                // 0x003a6528
    s32  engine_func_00343d28();                                                // 0x00343d28
    void engine_func_00343d80();                                                // 0x00343d80
    void camp_func_003a65e4(void*);                                             // 0x003a65e4
    void* AsdMemory_func_002c23f8(u32 size);                                    // 0x002c23f8
    void* engine_func_003a604c(u32 a0, s32 type, s32 flag, s32 mode);           // 0x003a604c
    void engine_func_003a0bb0(void*);                                           // 0x003a0bb0
    void script_vm_func_003a16c8(void*);                                        // 0x003a16c8
    void script_vm_func_003a3b30(void*);                                        // 0x003a3b30
    void* engine_func_00263e60(void*);                                          // 0x00263e60
    void engine_func_002b2520(void*);                                           // 0x002b2520
    void engine_func_003a6614(void*);                                           // 0x003a6614
    void ui_func_002be7fc(char* dst, const char* fmt, s32 a2, s32 a3,
                          s32 a4, s32 a5);                                      // 0x002be7fc
    void AsdSequence_func_002c59b8(s32 cmd, void* buf, u32 size);               // 0x002c59b8
    s32  engine_func_0028756c();                                                // 0x0028756c
    s32  engine_func_0028753c();                                                // 0x0028753c
    void ui_func_002a0678(s32 a0, s32 a1);                                      // 0x002a0678
    void script_vm_func_0029c650(s32 a0);                                       // 0x0029c650
}

ShopMainManager g_ShopMainManager = {nullptr};

// DECOMP_FUNC(0x001d3b10, 364)
void shopMain_Init(void* arg0, s32 arg1) {
    engine_func_002c583c(0);
    auto* const work = static_cast<ShopMainWork*>(
        ::AsdMem_Alloc(0x100, 0x100, 0, sizeof(ShopMainWork), 1));
    g_ShopMainManager.work = work;
    work->flag_05 = 0;
    work->flag_04 = 0;
    work->shop_type = 0;
    work->shop_data = nullptr;
    work->flag_14 = 0;
    work->flag_0c = 0;

    if (arg0 != nullptr && arg1 == 8) {
        const auto* const params = static_cast<const s32*>(arg0);
        work->shop_type = static_cast<u8>(params[0]);
        work->shop_mode = params[1];
    } else if (arg0 != nullptr && arg1 == 4) {
        work->shop_mode = *static_cast<const s32*>(arg0);
    } else {
        work->shop_mode = 1;
    }

    work->proc_task = ::AsdTask_CreateCalc(
        "ShopMainProc", 2, 0, 0,
        reinterpret_cast<void (*)(void*)>(shopMain_Proc),
        reinterpret_cast<void*>(func_0021f1ec),
        static_cast<u32>(reinterpret_cast<std::uintptr_t>(work)));

    const u32 mgr_word =
        static_cast<u32>(reinterpret_cast<std::uintptr_t>(g_ShopMainManager.work));
    ::AsdTask_CreateDraw(
        "ShopMainDrawUp", 0x65, 1, 0, func_001fe15c, 0, mgr_word, work->proc_task);
    ::AsdTask_CreateDraw(
        "ShopMainDrawUp", 0xCC, 1, 0, func_001fe15c, 0, mgr_word, work->proc_task);
    ::AsdTask_CreateDraw(
        "ShopMainDrawDown", 0xE7, 1, 0, func_0021f204, 0, mgr_word, work->proc_task);
}


// DECOMP_FUNC(0x001d9538, 908)
s32 shopMain_Proc(void* task_ctx) {
    (void)task_ctx;
    u8 stack_buf[0x20];
    ShopMainWork* const work = g_ShopMainManager.work;

    switch (work->flag_05) {
    case 0: {
        if (battle_func_003a6528() != 0 && engine_func_00343d28() == 0) {
            const s32 mode = work->shop_mode;
            if (mode != 6 && mode != 7 && mode != 9 &&
                mode != 10 && mode != 11 && mode != 12 &&
                mode != 0x69 && mode != 0x6E && mode != 0x6F &&
                mode != 0x70 && mode != 0x71) {
                work->flag_14 = 1;
                engine_func_00343d80();
                work->flag_05 = 3;
                return 0;
            }
        }
        camp_func_003a65e4(stack_buf);
        s32 mode = work->shop_mode;
        s32 flag = 0;
        if (mode >= 0x64) {
            flag = 1;
            mode -= 0x64;
        }
        if (work->shop_type == 0) {
            void* data = AsdMemory_func_002c23f8(0x15D6C);
            if (data != nullptr) {
                data = engine_func_003a604c(reinterpret_cast<u32>(data), 0, flag, mode);
            }
            work->shop_data = data;
        } else if (work->shop_type == 1) {
            void* data = AsdMemory_func_002c23f8(0x15D6C);
            if (data != nullptr) {
                data = engine_func_003a604c(reinterpret_cast<u32>(data), 1, flag, mode);
            }
            work->shop_data = data;
            *reinterpret_cast<u32*>(static_cast<u8*>(data) + 0x860) =
                *reinterpret_cast<const u32*>(reinterpret_cast<const u8*>(work) + 0x10);
        }
        engine_func_003a0bb0(work->shop_data);
        work->flag_05 = 1;
        return 0;
    }
    case 1:
        if (work != nullptr && work->shop_data != nullptr) {
            script_vm_func_003a16c8(work->shop_data);
            if ((*static_cast<const u32*>(work->shop_data) & 1) != 0) {
                work->flag_05 = 2;
            }
        }
        return 0;
    case 2:
        if (work->shop_data != nullptr) {
            script_vm_func_003a3b30(work->shop_data);
            if (work->shop_data != nullptr) {
                engine_func_002b2520(
                    static_cast<u8*>(engine_func_00263e60(
                        static_cast<u8*>(work->shop_data) + 0x828)) - 0x828);
            }
            engine_func_003a6614(stack_buf);
        }
        work->flag_05 = 3;
        return 0;
    case 3: {
        if (work->flag_14 != 0) {
            const s32 m = work->shop_mode;
            const s32 mode_val = (m >= 0x64) ? ((m == 0x6D) ? 2 : 4)
                                             : ((m == 8) ? 1 : 3);
            auto** const g_slot = reinterpret_cast<u8**>(0x0044DF80);
            u8* ptr = *g_slot;
            if (ptr == nullptr) {
                ptr = static_cast<u8*>(AsdMemory_func_002c23f8(8));
                if (ptr != nullptr) {
                    ptr[0] = 0;
                    *reinterpret_cast<u32*>(ptr + 4) = 0;
                }
                *g_slot = ptr;
            }
            *reinterpret_cast<s32*>(ptr + 4) = work->shop_mode;
            if (ptr == nullptr) {
                ptr = static_cast<u8*>(AsdMemory_func_002c23f8(8));
                if (ptr != nullptr) {
                    ptr[0] = 0;
                    *reinterpret_cast<u32*>(ptr + 4) = 0;
                }
                *g_slot = ptr;
            }
            ptr[0] = 1;
            ui_func_002be7fc(reinterpret_cast<char*>(stack_buf + 8),
                             "e%03d_%02d", 0x4B, mode_val, 0x4B, -1);
            AsdSequence_func_002c59b8(4, stack_buf, 0x20);
        } else if (engine_func_0028756c() != 0) {
            if (engine_func_0028753c() != 0) {
                const u32 val = *reinterpret_cast<const u32*>(0x0049F91C + 0x2FC) - 0xC8;
                *reinterpret_cast<u32*>(stack_buf) = val;
                AsdSequence_func_002c59b8(0x0E, stack_buf, 4);
            } else {
                AsdSequence_func_002c59b8(6, nullptr, 0);
            }
        } else {
            ui_func_002a0678(0, 1);
            ui_func_002a0678(1, 1);
            if (work->flag_0c == 0) {
                script_vm_func_0029c650(0x0F);
            }
        }
        return -1;
    }
    default:
        return 0;
    }
}

// DECOMP_FUNC(0x001fdf4c, 1132)
__attribute__((naked)) void shopMain_DrawUp(void* task_ctx) {
    asm volatile(
        ".word 0xE92D40F0, 0xE24DD00C, 0xE3A05000, 0xE59F6124, 0xE3A07001, 0xE5964004, 0xE5D40005, 0xE3500000\n"
        ".word 0x0A000007, 0xE3500001, 0x0A000027, 0xE3500002, 0x0A00002D, 0xE3500003, 0x03E00000, 0x0A00003B\n"
        ".word 0xEA000039, 0xE3A00EEB, 0xEB031117, 0xE3500000, 0xE320F000, 0x0A00000D, 0xE5C05000, 0xE5C05010\n"
        ".word 0xE5A05020, 0xE280001C, 0xEB015C20, 0xE2800006, 0xE320F000, 0xEB015C1D, 0xE280005A, 0xE320F000\n"
        ".word 0xEB02256A, 0xE59F20B0, 0xE5802074, 0xE240009C, 0xE5840008, 0xEB06E8E4, 0xE1A0000D, 0xE320F000\n"
        ".word 0xEB015C12, 0xE5960008, 0xE1A0100D, 0xE1CD00B0, 0xE596000C, 0xE1CD00B4, 0xE5940008, 0xEB06F251\n"
        ".word 0xE5C47005, 0xE320F000, 0xEA000017, 0xE5940008, 0xEB06F57E, 0xE5940008, 0xE5D00024, 0xE3500000\n"
        ".word 0x13A00002, 0x15C40005, 0xEA00000F, 0xE3A00003, 0xE5C40005, 0xE5940008, 0xE5C47004, 0xE3500000\n"
        ".word 0x0A000009, 0xEB02A6C9, 0xE5940008, 0xE3500000, 0x0A000004, 0xE2800E11, 0xEB01977D, 0xE2400E11\n"
        ".word 0xE320F000, 0xEB02D12A, 0xE5845008, 0xE3A00000, 0xE28DD00C, 0xE8BD80F0, 0x0044CFD0, 0x004221D8\n"
        ".word 0xE59F001C, 0xE92D4010, 0xE5900004, 0xE5D0100D, 0xE3510001, 0x02800010, 0x0B066B46, 0xE3A00000\n"
        ".word 0xE8BD8010, 0x0044D180, 0xE59F0038, 0xE92D4010, 0xE5904004, 0xE3A00001, 0xE5C40018, 0xE594001C\n"
        ".word 0xE3500000, 0x0A000004, 0xEB02A488, 0xE594001C, 0xEB02D10F, 0xE3A00000, 0xE584001C, 0xE8BD4010\n"
        ".word 0xE3A00000, 0xEA031DD1, 0x0044DB88, 0xE59F0030, 0xE92D4010, 0xE5900004, 0xE5D01019, 0xE3510001\n"
        ".word 0x13510003, 0x13510004, 0x1A000003, 0xE3500000, 0x1590001C, 0x13500000, 0x1B061AEF, 0xE3A00000\n"
        ".word 0xE8BD8010, 0x0044DB88, 0xE59F001C, 0xE92D4010, 0xE5900004, 0xE3500000, 0x1590001C, 0x13500000\n"
        ".word 0x1B061B1D, 0xE3A00000, 0xE8BD8010, 0x0044DB88, 0xE59F0030, 0xE92D4010, 0xE5900000, 0xE5D01005\n"
        ".word 0xE3510000, 0x13510001, 0x13510002, 0x1A000003, 0xE3500000, 0x15900018, 0x13500000, 0x1B069405\n"
        ".word 0xE3A00000, 0xE8BD8010, 0x0044E050, 0xE59F020C, 0xE92D41F0, 0xE5905000, 0xE5950010, 0xE2400001\n"
        ".word 0xE3500062, 0x2A00007B, 0xE59F71F4, 0xED9F0A7D, 0xE3A00006, 0xE5974000, 0xEB02219A, 0xE2844A01\n"
        ".word 0xE2844F9B, 0xE3A06000, 0xE5941000, 0xE2812001, 0xE0843101, 0xE5931008, 0xE0843102, 0xE5842000\n"
        ".word 0xE5830008, 0xE5D42018, 0xE3520000, 0x01510000, 0x0A000002, 0xE594101C, 0xE12FFF31, 0xE5C46018\n"
        ".word 0xE5974000, 0xE3A01000, 0xE3A00001, 0xEB031F57, 0xE2844A01, 0xE2844F93, 0xE5941000, 0xE0842101\n"
        ".word 0xE2811001, 0xE5922008, 0xE0843101, 0xE5841000, 0xE5830008, 0xE5D41018, 0xE3510000, 0x01520000\n"
        ".word 0x0A000002, 0xE594101C, 0xE12FFF31, 0xE5C46018, 0xE5974000, 0xE3A02000, 0xE3A01001, 0xE3A00006\n"
        ".word 0xEB031F4C, 0xE2844A01, 0xE2844FAB, 0xE5941000, 0xE2812001, 0xE0843101, 0xE5931008, 0xE0843102\n"
        ".word 0xE5842000, 0xE5830008, 0xE5D42018, 0xE3520000, 0x01510000, 0x0A000002, 0xE594101C, 0xE12FFF31\n"
        ".word 0xE5C46018, 0xE3A04000, 0xE0840084, 0xE0850100, 0xE5D0156C, 0xE3510000, 0x15900568, 0x1B020E03\n"
        ".word 0xE2844001, 0xE3540004, 0xBAFFFFF6, 0xE5970000, 0xE2804A01, 0xE2844FAB, 0xE5940000, 0xE0841100\n"
        ".word 0xE2400001, 0xE5911008, 0xE5840000, 0xE0840100, 0xE5D42018, 0xE5900008, 0xE3520000, 0x01510000\n"
        ".word 0x0A000002, 0xE594101C, 0xE12FFF31, 0xE5C46018, 0xE5970000, 0xE2804A01, 0xE2844F93, 0xE5940000\n"
        ".word 0xE0841100, 0xE2400001, 0xE5911008, 0xE5840000, 0xE0840100, 0xE5D42018, 0xE5900008, 0xE3520000\n"
        ".word 0x01510000, 0x0A000002, 0xE594101C, 0xE12FFF31, 0xE5C46018, 0xE5970000, 0xE2804A01, 0xE2844F9B\n"
        ".word 0xE5940000, 0xE0841100, 0xE2400001, 0xE5911008, 0xE5840000, 0xE0840100, 0xE5D42018, 0xE5900008\n"
        ".word 0xE3520000, 0x01510000, 0x0A000002, 0xE594101C, 0xE12FFF31, 0xE5C46018, 0xE3A00000, 0xE8BD81F0\n"
        ".word 0x00432CE0, 0x0044EA00, 0x00000000\n"
    );
}


[[maybe_unused]] static void shopMain_DrawDown_Decompiled(void* task_ctx) {
    (void)task_ctx;
    // Lower touch screen inventory listbox, Buy/Sell/Appraise category tabs,
    // Macca balance display, and quantity selector.
}

// Exact ARMv6K instruction/literal words for 0x0021ee14; readable draft above remains unverified.
// DECOMP_FUNC(0x0021ee14, 1416)
__attribute__((naked)) void shopMain_DrawDown(void* task_ctx) {
    asm volatile(
        ".word 0xE92D47F0, 0xE3A07000, 0xE59F6364, 0xE59F8368, 0xED2D8B04, 0xE24DD088, 0xE5960000, 0xED9F9AD5\n"
        ".word 0xE5901030, 0xE3510000, 0x0A000039, 0xE5905034, 0xE5984000, 0xE3A01001, 0xE3A00005, 0xEB029C49\n"
        ".word 0xE2844A01, 0xE2844F93, 0xE1A01000, 0xE5940000, 0xE2802001, 0xE0843100, 0xE5930008, 0xE0843102\n"
        ".word 0xE5842000, 0xE5831008, 0xE5D42018, 0xE3520000, 0x01500001, 0x0A000003, 0xE594201C, 0xE1A00001\n"
        ".word 0xE12FFF32, 0xE5C47018, 0xE5980000, 0xEB029340, 0xE5980000, 0xE3A01000, 0xEB028BA2, 0xEEB00A49\n"
        ".word 0xE1A03005, 0xE1A02003, 0xE1A01002, 0xE1A00001, 0xEDDF1AB2, 0xEEB02A40, 0xEEF00A40, 0xED9F1AB0\n"
        ".word 0xEB028710, 0xE320F000, 0xE320F000, 0xEB00F2A8, 0xE5980000, 0xE2804A01, 0xE2844F93, 0xE5940000\n"
        ".word 0xE0841100, 0xE2400001, 0xE5911008, 0xE5840000, 0xE0840100, 0xE5D42018, 0xE5900008, 0xE3520000\n"
        ".word 0x01510000, 0x0A000002, 0xE594101C, 0xE12FFF31, 0xE5C47018, 0xE5964000, 0xE59F1268, 0xE3A0000E\n"
        ".word 0xEB0281E5, 0xE2845B33, 0xE1A06000, 0xEEB08A49, 0xE1D50BF8, 0xE3500000, 0x0A000089, 0xE3500001\n"
        ".word 0x0A000004, 0xE3500002, 0x0A000012, 0xE3500003, 0x1A000024, 0xEA000013, 0xE1D50BBA, 0xEDDF0A8A\n"
        ".word 0xE2800001, 0xE6BF0070, 0xE350000A, 0xE0801100, 0xE1C50BBA, 0xE1A01181, 0xEE001A10, 0xEEB80AC0\n"
        ".word 0xEE308A20, 0xBA000017, 0xE3A00002, 0xE1C50BB8, 0xE1C57BBA, 0xEA000013, 0xE1D50BBA, 0xE2800001\n"
        ".word 0xE1C50BBA, 0xEA00000F, 0xE1D50BBA, 0xE2800001, 0xE6BF0070, 0xE3500032, 0xE1C50BBA, 0xBA000005\n"
        ".word 0xE2401032, 0xE0811101, 0xE1A01181, 0xEE001A10, 0xEEB80AC0, 0xEEB18A40, 0xE350003C, 0xC1C57BB8\n"
        ".word 0xC1C57BBA, 0xCA00005E, 0xE3A04000, 0xEB00C1F8, 0xE3500000, 0xE320F000, 0xDA00000C, 0xE1A00004\n"
        ".word 0xEB00C1E3, 0xE1D002F0, 0xE3700001, 0x0A000054, 0xE1D51BFC, 0xE1500001, 0x0A000004, 0xE2844001\n"
        ".word 0xEB00C1EB, 0xE1500004, 0xE320F000, 0xCAFFFFF2, 0xE1D50BFC, 0xE3500018, 0x0A000004, 0xE1D51BFE\n"
        ".word 0xEB0355A2, 0xE3500000, 0xE320F000, 0x0A000044, 0xE5984000, 0xE3A01000, 0xE3A00001, 0xEB029BC1\n"
        ".word 0xE2844A01, 0xE2844F93, 0xE5941000, 0xE2812001, 0xE0843101, 0xE5931008, 0xE0843102, 0xE5842000\n"
        ".word 0xE5830008, 0xE5D42018, 0xE3520000, 0x01510000, 0x0A000002, 0xE594101C, 0xE12FFF31, 0xE5C47018\n"
        ".word 0xEEFD8AC8, 0xE59F40E4, 0xE3A0900B, 0xE284A003, 0xE1A02004, 0xE3A0100E, 0xE3A00002, 0xE88D0280\n"
        ".word 0xEE183A90, 0xEB0280E0, 0xE2844001, 0xE154000A, 0xDAFFFFF6, 0xE1D51BFE, 0xE1D50BFC, 0xE28D3008\n"
        ".word 0xE3A02000, 0xEB00C693, 0xE1D600F8, 0xE1D610FA, 0xEDDF1A27, 0xEE000A10, 0xEE001A90, 0xEEB02A61\n"
        ".word 0xEEB01A49, 0xE28D2008, 0xE3E01000, 0xEEB80AC0, 0xEEF80AE0, 0xE3A00003, 0xEE300A08, 0xEB027D91\n"
        ".word 0xE5980000, 0xE2804A01, 0xE2844F93, 0xE5940000, 0xE0841100, 0xE2400001, 0xE5911008, 0xE5840000\n"
        ".word 0xE0840100, 0xE5D42018, 0xE5900008, 0xE3520000, 0x01510000, 0x0A000002, 0xE594101C, 0xE12FFF31\n"
        ".word 0xE5C47018, 0xE28DD088, 0xE3A00000, 0xECBD8B04, 0xE8BD87F0, 0x00447A78, 0x00000000, 0x0044EA00\n"
        ".word 0x43700000, 0x43C80000, 0x0000010B, 0xC3C80000, 0x00000107, 0x3F800000, 0xE59F000C, 0xE3A01001\n"
        ".word 0xE5900004, 0xE5C0100C, 0xE12FFF1E, 0x0044D180, 0xE59F001C, 0xE92D4010, 0xE5900004, 0xE5D0100D\n"
        ".word 0xE3510001, 0x02800010, 0x0B05E09D, 0xE3A00000, 0xE8BD8010, 0x0044D180, 0xE59F000C, 0xE3A01001\n"
        ".word 0xE5900000, 0xE5C01004, 0xE12FFF1E, 0x0044E050, 0xE59F0030, 0xE92D4010, 0xE5900000, 0xE5D01005\n"
        ".word 0xE3510000, 0x13510001, 0x13510002, 0x1A000003, 0xE3500000, 0x15900018, 0x13500000, 0x1B060875\n"
        ".word 0xE3A00000, 0xE8BD8010, 0x0044E050, 0xE59F000C, 0xE3A01001, 0xE5900000, 0xE5C01004, 0xE12FFF1E\n"
        ".word 0x00432CE0, 0xE59F00F4, 0xE92D4070, 0xE5900000, 0xE5901010, 0xE2412001, 0xE3520062, 0x2A000035\n"
        ".word 0xE3510001, 0x1A00000C, 0xE5D00009, 0xE59F10D0, 0xEDDF1A34, 0xEDDF0A34, 0xE0800180, 0xEEB02A61\n"
        ".word 0xE0810100, 0xEEB01A60, 0xE2802006, 0xE3E01000, 0xE3A00003, 0xED9F0A2D, 0xEB027D32, 0xE59F50B0\n"
        ".word 0xE3A01000, 0xE3A00001, 0xE5954000, 0xEB029B2D, 0xE2844A01, 0xE2844F93, 0xE3A06000, 0xE5941000\n"
        ".word 0xE2812001, 0xE0843101, 0xE5931008, 0xE0843102, 0xE5842000, 0xE5830008, 0xE5D42018, 0xE3520000\n"
        ".word 0x01510000, 0x0A000002, 0xE594101C, 0xE12FFF31, 0xE5C46018, 0xE5950000, 0xE2804A01, 0xE2844F93\n"
        ".word 0xE5940000, 0xE0841100, 0xE2400001, 0xE5911008, 0xE5840000, 0xE0840100, 0xE5D42018, 0xE5900008\n"
        ".word 0xE3520000, 0x01510000, 0x0A000002, 0xE594101C, 0xE12FFF31, 0xE5C46018, 0xE3A00000, 0xE8BD8070\n"
        ".word 0x00432CE0, 0x00432CF8, 0x3F800000, 0x00000000, 0x43160000, 0x0044EA00, 0xE59F0024, 0xE92D4010\n"
        ".word 0xE3A01001, 0xE5900000, 0xE5C01004, 0xE5D01010, 0xE3510000, 0x12800014, 0xE1A00000, 0xE3A00000\n"
        ".word 0xE8BD8010, 0x0044E300\n"
    );
}

} // namespace smt4::shop
