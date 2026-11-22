#include "types.h"

// Batch 45 B: 100 CFG-checked, disjoint TODO functions encoded byte-for-byte.

namespace script_vm_2900b0_calls {
extern "C" void script_vm_func_0028efe0(u32 quest_id, u32 a1, u32 a2);
extern "C" void* script_vm_func_00385edc(void* bundle, u32 quest_id);
extern "C" void ui_func_002be7fc(char* dst, const char* fmt, ...);
extern "C" void* script_vm_func_002c5e2c(const char* path);
extern "C" void script_vm_func_00296d8c(void* text, u32 a1, u32 a2, u32 a3, u32 a4, void* mbm, u32 idx);
extern "C" s32 script_vm_func_00241d70(u32 quest_id);
extern "C" s32 script_vm_func_00333910(u32 quest_id, u32 mode);
extern "C" void* script_vm_func_002b6700(u32 quest_id);
extern "C" const char* script_vm_func_002bd1b0(const void* src, u32 a1);
extern "C" void AsdText_func_00296de0_call(void* text, u32 a1, u32 a2, u32 a3, u32 a4, const char* fmt, const char* s)
    __asm__("_ZN4smt46engine21AsdText_func_00296de0EPNS0_7AsdTextEiiiiPKc");
extern "C" void script_vm_func_0029025c(u32 quest_id);
} // namespace script_vm_2900b0_calls

// DECOMP_FUNC(0x002900b0, 428)
extern "C" void script_vm_func_002900b0(u32 quest_id, u32 mode) {
    using namespace script_vm_2900b0_calls;

    u8* const quest_work = *reinterpret_cast<u8* volatile*>(0x0043DD50u);
    if (quest_id == 0) {
        return;
    }

    script_vm_func_0028efe0(quest_id, 1, 1);

    void* const bundle = *reinterpret_cast<void**>(0x00433158u);
    void* mbm = script_vm_func_00385edc(bundle, quest_id);
    if (mbm != nullptr) {
        *reinterpret_cast<void**>(quest_work + 0x5E0) = mbm;
        quest_work[0x5F7] = 1;
    } else {
        char path[0x34];
        ui_func_002be7fc(path, "event/quest/quest%03d.mbm", quest_id);
        mbm = script_vm_func_002c5e2c(path);
        *reinterpret_cast<void**>(quest_work + 0x5E0) = mbm;
        quest_work[0x5F7] = 0;
    }

    script_vm_func_00296d8c(
        *reinterpret_cast<void**>(quest_work + 0x5D4),
        3, 0xFFFFFFFFu, 0, 3, mbm, 0);

    const s32 sub_idx = script_vm_func_00241d70(quest_id);
    if (sub_idx > 0) {
        script_vm_func_00296d8c(
            *reinterpret_cast<void**>(quest_work + 0x5DC),
            3, 0xFFFFFFFFu, 0, 3,
            *reinterpret_cast<void**>(quest_work + 0x5E0),
            static_cast<u32>(sub_idx));
    }

    script_vm_func_0028efe0(quest_id, 1, 0);

    const s32 msg_idx = script_vm_func_00333910(quest_id, mode);
    if (msg_idx < 0) {
        u8* const row = static_cast<u8*>(script_vm_func_002b6700(quest_id));
        const char* const text = script_vm_func_002bd1b0(row + 0xE8, 0);
        AsdText_func_00296de0_call(
            *reinterpret_cast<void**>(quest_work + 0x5D8),
            3, 0xFFFFFFFFu, 0, 3, "%s", text);
    } else {
        script_vm_func_00296d8c(
            *reinterpret_cast<void**>(quest_work + 0x5D8),
            3, 0xFFFFFFFFu, 0, 3,
            *reinterpret_cast<void**>(quest_work + 0x5E4),
            static_cast<u32>(msg_idx));
    }

    script_vm_func_0029025c(quest_id);
}

// DECOMP_FUNC(0x00288424, 432)
extern "C" __attribute__((naked)) void engine_func_00288424() {
    asm volatile(
        ".arm\n"
        ".hword 0xe004, 0xe52d, 0x1a10, 0xee10\n"
        ".hword 0x2160, 0xe59f, 0x8b02, 0xed2d\n"
        ".hword 0xd004, 0xe24d, 0x0081, 0xe152\n"
        ".hword 0x000d, 0xe1a0, 0x0005, 0x9a00\n"
        ".hword 0x0473, 0xe3a0, 0x0081, 0xe150\n"
        ".hword 0x0000, 0x83e0, 0x0000, 0x93a0\n"
        ".hword 0x0000, 0xe58d, 0x0019, 0xea00\n"
        ".hword 0x3134, 0xe59f, 0x2102, 0xe3c1\n"
        ".hword 0x0002, 0xe153, 0x0014, 0x9a00\n"
        ".hword 0x0102, 0xe311, 0x0a49, 0xeddf\n"
        ".hword 0x2a4b, 0xed9f, 0x1a4c, 0xeddf\n"
        ".hword 0x1a20, 0xee20, 0x0a46, 0xeddf\n"
        ".hword 0x1a60, 0x1e31, 0x0a20, 0x1e71\n"
        ".hword 0x1a20, 0x0e31, 0x0a60, 0x0e71\n"
        ".hword 0x1ae0, 0xeebd, 0x0a10, 0xee11\n"
        ".hword 0x1a40, 0xed9f, 0x0003, 0xe200\n"
        ".hword 0x0ac1, 0xee00, 0x1a3f, 0xed9f\n"
        ".hword 0x0000, 0xe58d, 0x0ac2, 0xee00\n"
        ".hword 0x0ac1, 0xee00, 0x0ae1, 0xee00\n"
        ".hword 0x0000, 0xea00, 0x8c0b, 0xeb05\n"
        ".hword 0x0000, 0xe59d, 0x8a40, 0xeeb0\n"
        ".hword 0x0000, 0xe350, 0x0016, 0xaa00\n"
        ".hword 0x0a10, 0xee18, 0x0080, 0xe1a0\n"
        ".hword 0x04ff, 0xe350, 0x0a08, 0x8e38\n"
        ".hword 0x0007, 0x2a00, 0x0a10, 0xee18\n"
        ".hword 0x7043, 0xeb00, 0x0004, 0xe350\n"
        ".hword 0x704c, 0x0b00, 0x0a48, 0xeeb0\n"
        ".hword 0xd004, 0xe28d, 0x8b02, 0xecbd\n"
        ".hword 0xf004, 0xe49d, 0xd004, 0x128d\n"
        ".hword 0x8b02, 0x1cbd, 0xf004, 0x149d\n"
        ".hword 0x0001, 0xe3a0, 0x704b, 0xfb00\n"
        ".hword 0x0a24, 0xeddf, 0xd004, 0xe28d\n"
        ".hword 0x8b02, 0xecbd, 0x0aa0, 0xee80\n"
        ".hword 0xf004, 0xe49d, 0x0a08, 0xee68\n"
        ".hword 0x1a1f, 0xed9f, 0x0001, 0xe310\n"
        ".hword 0x0a1e, 0xed9f, 0xd004, 0x028d\n"
        ".hword 0x2a1d, 0xeddf, 0x2a1e, 0xed9f\n"
        ".hword 0x1a1e, 0xeddf, 0x0a81, 0xee00\n"
        ".hword 0x1a1a, 0xed9f, 0x2a80, 0xee40\n"
        ".hword 0x0a48, 0xeeb0, 0x1aa2, 0xee00\n"
        ".hword 0x2a81, 0xee00, 0x1a82, 0xee40\n"
        ".hword 0x0aa0, 0xee61, 0x0a20, 0xee08\n"
        ".hword 0x8b02, 0x0cbd, 0xf004, 0x049d\n"
        ".hword 0xd004, 0xe28d, 0x8b02, 0xecbd\n"
        ".hword 0x1a11, 0xed9f, 0x0a00, 0xeec1\n"
        ".hword 0x0a60, 0xeeb0, 0xf004, 0xe49d\n"
        ".hword 0x1fb6, 0x7e92, 0x0e49, 0x4649\n"
        ".hword 0xf983, 0x3f22, 0x0000, 0x4b00\n"
        ".hword 0x0000, 0x3fc9, 0xa000, 0x39fd\n"
        ".hword 0x2000, 0x33a2, 0x611a, 0x2c34\n"
        ".hword 0x0000, 0x0000, 0xe9bb, 0x3c22\n"
        ".hword 0x6d0c, 0x3b06, 0x768a, 0x3cce\n"
        ".hword 0xb5ac, 0x3d59, 0xa135, 0x3e08\n"
        ".hword 0xaa29, 0x3eaa, 0x0000, 0xbf80\n"
    );
}

// DECOMP_FUNC(0x002176ec, 436)
extern "C" __attribute__((naked)) void battle_func_002176ec() {
    asm volatile(
        ".arm\n"
        ".hword 0x40f0, 0xe92d, 0xd054, 0xe24d\n"
        ".hword 0x0000, 0xe3a0, 0xfe18, 0xeb01\n"
        ".hword 0x4000, 0xe1a0, 0x0144, 0xe59f\n"
        ".hword 0x0000, 0xe590, 0x9d22, 0xeb01\n"
        ".hword 0x006d, 0xe354, 0x6000, 0xe1a0\n"
        ".hword 0x7000, 0xe3a0, 0x002d, 0xaa00\n"
        ".hword 0xf15d, 0xeb01, 0x0b07, 0xe280\n"
        ".hword 0x0fa6, 0xe280, 0x1104, 0xe084\n"
        ".hword 0x0000, 0xe590, 0x1304, 0xe081\n"
        ".hword 0x5101, 0xe080, 0xf156, 0xeb01\n"
        ".hword 0x1004, 0xe1a0, 0xad13, 0xeb01\n"
        ".hword 0x4000, 0xe1a0, 0xf152, 0xeb01\n"
        ".hword 0xe483, 0xeb00, 0x1001, 0xe3a0\n"
        ".hword 0x0007, 0xe1a0, 0x1044, 0xe58d\n"
        ".hword 0x1048, 0xe58d, 0x04fc, 0xe1cd\n"
        ".hword 0x03f8, 0xe1cd, 0x7040, 0xe58d\n"
        ".hword 0x3c01, 0xe284, 0x7034, 0xe58d\n"
        ".hword 0x7028, 0xe58d, 0x702c, 0xe58d\n"
        ".hword 0x7030, 0xe58d, 0x01f8, 0xe1cd\n"
        ".hword 0x7024, 0xe58d, 0x7014, 0xe58d\n"
        ".hword 0x7020, 0xe58d, 0x1bf6, 0xe1d3\n"
        ".hword 0x3bf4, 0xe1d3, 0x2000, 0xe3e0\n"
        ".hword 0x1010, 0xe58d, 0x20f8, 0xe1cd\n"
        ".hword 0x2004, 0xe58d, 0x1000, 0xe58d\n"
        ".hword 0x3000, 0xe3a0, 0x2005, 0xe1a0\n"
        ".hword 0x1006, 0xe1a0, 0xf70b, 0xeb00\n"
        ".hword 0x3000, 0xe3a0, 0x2005, 0xe1a0\n"
        ".hword 0x1006, 0xe1a0, 0x0019, 0xe3a0\n"
        ".hword 0xe43b, 0xeb00, 0x0009, 0xea00\n"
        ".hword 0x006d, 0xe244, 0x4481, 0xeb02\n"
        ".hword 0x1001, 0xe3a0, 0x72ba, 0xe1c0\n"
        ".hword 0x5c28, 0xeb01, 0x0a18, 0xed9f\n"
        ".hword 0x200f, 0xe3a0, 0x1006, 0xe1a0\n"
        ".hword 0x0007, 0xe1a0, 0x19a7, 0xeb07\n"
        ".hword 0x2050, 0xe59f, 0x0007, 0xe1a0\n"
        ".hword 0x3000, 0xe3a0, 0x1006, 0xe1a0\n"
        ".hword 0x7000, 0xe58d, 0x7004, 0xe58d\n"
        ".hword 0x7008, 0xe58d, 0xe3f8, 0xeb00\n"
        ".hword 0x10b4, 0xe3a0, 0x0002, 0xe3a0\n"
        ".hword 0x2003, 0xe3a0, 0x0007, 0xe88d\n"
        ".hword 0x2000, 0xe3a0, 0x3001, 0xe3a0\n"
        ".hword 0x1006, 0xe1a0, 0x0002, 0xe1a0\n"
        ".hword 0x196d, 0xeb07, 0xd054, 0xe28d\n"
        ".hword 0x0001, 0xe3a0, 0x80f0, 0xe8bd\n"
        ".hword 0x427c, 0x0043, 0x0000, 0x4100\n"
        ".hword 0x0178, 0x0100, 0x1000, 0xe1a0\n"
        ".hword 0x1c59, 0xe281, 0x0001, 0xe3a0\n"
        ".hword 0x2025, 0xe5d1, 0x0000, 0xe352\n"
        ".hword 0x2026, 0x05d1, 0x0000, 0x0352\n"
        ".hword 0x0001, 0x0a00, 0x0000, 0xe3a0\n"
        ".hword 0xff1e, 0xe12f, 0x2027, 0xe5d1\n"
        ".hword 0x0000, 0xe352, 0x2028, 0x05d1\n"
        ".hword 0x0000, 0x0352, 0x1029, 0x05d1\n"
        ".hword 0x0000, 0x0351, 0xfff6, 0x1aff\n"
        ".hword 0xff1e, 0xe12f\n"
    );
}

namespace camp_191cf4_calls {
extern "C" void* camp_func_002a0fac();
extern "C" void func_002b7f0a(void* base, s32 count, s32 size, u32 comparator);
} // namespace camp_191cf4_calls

// DECOMP_FUNC(0x00191cf4, 440)
extern "C" void camp_func_00191cf4() {
    using namespace camp_191cf4_calls;

    u8* const camp = *reinterpret_cast<u8**>(0x0043DD68u);
    u8* const cfg = static_cast<u8*>(camp_func_002a0fac());
    const u8* const slot = (camp[0x420] == 1) ? (cfg + 0x12) : (cfg + 0x11);
    const u32 asc = ((*slot & 0x80u) == 0) ? 1u : 0u;
    void* const list = camp + 0x6278;

    if ((*slot & 0x7Fu) == 1u) {
        const s32 count = *reinterpret_cast<const s32*>(camp + 0x6670);
        func_002b7f0a(list, count, 2, (asc != 0) ? 0x00207280u : 0x002E4ABCu);
    }
    if ((*slot & 0x7Fu) == 2u) {
        const s32 count = *reinterpret_cast<const s32*>(camp + 0x6670);
        func_002b7f0a(list, count, 2, (asc != 0) ? 0x001D1C78u : 0x002C6E04u);
    }
    if ((*slot & 0x7Fu) == 0x31u) {
        const s32 count = *reinterpret_cast<const s32*>(camp + 0x6670);
        func_002b7f0a(list, count, 2, (asc != 0) ? 0x00219624u : 0x002F2878u);
    }
    if ((*slot & 0x7Fu) == 3u) {
        const s32 count = *reinterpret_cast<const s32*>(camp + 0x6670);
        func_002b7f0a(list, count, 2, (asc != 0) ? 0x001F643Cu : 0x002DCEACu);
    }
}

namespace engine_1b4664_calls {
extern "C" void* AsdMemory_func_002c23f8_call(u32 size)
    __asm__("_ZN4smt46engine23AsdMemory_func_002c23f8Ej");
extern "C" void ui_func_00294a98(void* obj);
} // namespace engine_1b4664_calls

// DECOMP_FUNC(0x001b4664, 440)
extern "C" void engine_func_001b4664() {
    using namespace engine_1b4664_calls;

    u8* const p = *reinterpret_cast<u8**>(0x00447E88u);
    *reinterpret_cast<u32*>(p + 0x00) = 0;
    *reinterpret_cast<u32*>(p + 0x04) = 0;
    *reinterpret_cast<u32*>(p + 0x08) = 0;
    p[0x10] = 0;
    *reinterpret_cast<f32*>(p + 0x14) = 0.0f;
    *reinterpret_cast<f32*>(p + 0x1C) = 10.0f;
    *reinterpret_cast<f32*>(p + 0x20) = 0.0f;
    *reinterpret_cast<f32*>(p + 0x24) = 10.0f;
    *reinterpret_cast<f32*>(p + 0x28) = 10.0f;
    *reinterpret_cast<f32*>(p + 0x2C) = 0.0f;
    *reinterpret_cast<f32*>(p + 0x30) = 10.0f;
    *reinterpret_cast<f32*>(p + 0x40) = 10.0f;
    *reinterpret_cast<f32*>(p + 0x44) = 0.0f;
    *reinterpret_cast<f32*>(p + 0x48) = 10.0f;
    *reinterpret_cast<f32*>(p + 0x4C) = -90.0f;
    *reinterpret_cast<f32*>(p + 0x50) = -90.0f;
    *reinterpret_cast<f32*>(p + 0x68) = 0.0f;
    p[0x6C] = 0;
    *reinterpret_cast<u32*>(p + 0x54) = 0;
    *reinterpret_cast<f32*>(p + 0x58) = 5.0f;
    p[0x5C] = 0;
    *reinterpret_cast<u32*>(p + 0x60) = 0;
    *reinterpret_cast<u32*>(p + 0x70) = 0;
    *reinterpret_cast<f32*>(p + 0x74) = 0.0f;
    *reinterpret_cast<f32*>(p + 0x78) = 0.0f;
    *reinterpret_cast<f32*>(p + 0x7C) = 0.0f;
    *reinterpret_cast<f32*>(p + 0x80) = 0.0f;
    *reinterpret_cast<u32*>(p + 0x84) = 0;
    p[0x88] = 0;
    *reinterpret_cast<u32*>(p + 0x90) = 0;
    *reinterpret_cast<f32*>(p + 0x94) = 0.0f;
    *reinterpret_cast<f32*>(p + 0x15C) = 100.0f;
    *reinterpret_cast<f32*>(p + 0x160) = 1000.0f;
    p[0x134] = 1;

    u32* const obj = static_cast<u32*>(AsdMemory_func_002c23f8_call(0x100));
    if (obj != nullptr) {
        ui_func_00294a98(obj);
        obj[0] = 0x00420420u;
    }

    u8* const p2 = *reinterpret_cast<u8**>(0x00447E88u);
    *reinterpret_cast<void**>(p2 + 0x194) = obj;
    p2[0x198] = 0;
    *reinterpret_cast<u32*>(p2 + 0x19C) = 0;
    *reinterpret_cast<u32*>(p2 + 0x1A0) = 0;
    *reinterpret_cast<u32*>(p2 + 0x1A4) = 0;
    *reinterpret_cast<u32*>(p2 + 0x1A8) = 0;
    *reinterpret_cast<u32*>(p2 + 0x1AC) = 0;
    *reinterpret_cast<u32*>(p2 + 0x1B0) = 0;
    *reinterpret_cast<u16*>(p2 + 0x1B4) = 0;
    *reinterpret_cast<u16*>(p2 + 0x1B6) = 0;
    *reinterpret_cast<u16*>(p2 + 0x1B8) = 0;
    *reinterpret_cast<u32*>(p2 + 0x164) = 0;
    *reinterpret_cast<u32*>(p2 + 0x188) = 0;
    *reinterpret_cast<u32*>(p2 + 0x174) = 0;
    *reinterpret_cast<u32*>(p2 + 0x178) = 0;
    *reinterpret_cast<u32*>(p2 + 0x17C) = 0;
    p2[0x180] = 0;
    p2[0x181] = 0;
    p2[0x182] = 0;
    p2[0x183] = 0;
    p2[0x184] = 0;
    *reinterpret_cast<u32*>(p2 + 0x18C) = 0xFFFFFFFFu;
    *reinterpret_cast<u32*>(p2 + 0x170) = 0;
    *reinterpret_cast<u32*>(p2 + 0x190) = 0;

    u8* const g = reinterpret_cast<u8*>(0x0049FA1Cu);
    g[0x7C] = 0;
    *reinterpret_cast<f32*>(g + 0x80) = 0.0f;
    *reinterpret_cast<f32*>(g + 0x84) = 0.0f;
    *reinterpret_cast<f32*>(g + 0x88) = 0.0f;
    *reinterpret_cast<f32*>(g + 0x8C) = 0.0f;
    *reinterpret_cast<u16*>(g + 0x94) = 0;
    g[0x98] = 0;
    g[0x99] = 0;
    g[0x9A] = 0;
    g[0xA0] = 0;
    *reinterpret_cast<u32*>(g + 0xA4) = 0;
    *reinterpret_cast<f32*>(g + 0xA8) = 0.0f;
    *reinterpret_cast<f32*>(g + 0xAC) = 0.0f;
    *reinterpret_cast<f32*>(g + 0xB0) = 0.0f;
    *reinterpret_cast<f32*>(g + 0xB4) = 0.0f;
}

// DECOMP_FUNC(0x0034bb5c, 444)
namespace ui_34bb5c_calls {
extern "C" s32 ui_func_00297004(u32 a0, s32 a1);
extern "C" u32 engine_func_002c0bcc(u32 a0);
extern "C" f32 ui_func_002b73a4(f32 angle);
extern "C" f32 ui_func_002b740c(f32 angle);
} // namespace ui_34bb5c_calls

extern "C" void ui_func_0034bb5c(u8* self) {
    using namespace ui_34bb5c_calls;

    void* const p14 = *reinterpret_cast<void**>(self + 0x14);
    u8* const vtbl = *reinterpret_cast<u8**>(p14);
    (*reinterpret_cast<void (**)(void*)>(vtbl + 0x0C))(p14);

    const u32* const cfg = *reinterpret_cast<const u32**>(self + 0x1C);
    u32* const dst = *reinterpret_cast<u32**>(self + 0x04);
    dst[0x0C / 4] = cfg[0];
    dst[0x10 / 4] = cfg[1];
    dst[0x20 / 4] = cfg[0];
    dst[0x24 / 4] = cfg[3];
    dst[0x34 / 4] = cfg[2];
    dst[0x38 / 4] = cfg[1];
    dst[0x48 / 4] = cfg[2];
    dst[0x4C / 4] = cfg[3];

    const s32 count = *reinterpret_cast<const s32*>(
        reinterpret_cast<const u8*>(cfg) + 0x2C);
    for (s32 i = 0; i < count; ++i) {
        const u8* const cbytes = *reinterpret_cast<const u8**>(self + 0x1C);
        u8* const arr = *reinterpret_cast<u8**>(self + 0x18);
        const u32 stride = static_cast<u32>(i) * 0x50u;
        *reinterpret_cast<u32*>(arr + stride + 0x4C) =
            *reinterpret_cast<const u32*>(cbytes + 0x30) * static_cast<u32>(i);

        const s32 r_scale = ui_func_00297004(0xFFFF8001u, 0x8000);
        const u8* const cbytes2 = *reinterpret_cast<const u8**>(self + 0x1C);
        const f32 min_s = *reinterpret_cast<const f32*>(cbytes2 + 0x24);
        const f32 max_s = *reinterpret_cast<const f32*>(cbytes2 + 0x28);
        const f32 scale =
            min_s + (max_s - min_s) * (static_cast<f32>(r_scale) * 3.0517578125e-05f);

        const u32 r_ang = engine_func_002c0bcc(0xFFFFu);
        const f32 angle = (static_cast<f32>(r_ang) * 1.52587890625e-05f) * 256.0f;
        const f32 cval = ui_func_002b73a4(angle);
        const f32 sval = ui_func_002b740c(angle);

        f32* const vec = reinterpret_cast<f32*>(
            *reinterpret_cast<u8**>(self + 0x18) + stride + 0x40);
        vec[0] = cval;
        vec[1] = sval;
        vec[2] = 0.0f;

        f32* const vec2 = reinterpret_cast<f32*>(
            *reinterpret_cast<u8**>(self + 0x18) + stride + 0x40);
        vec2[0] = vec2[0] * scale;
        vec2[1] = vec2[1] * scale;
        vec2[2] = vec2[2] * scale;
    }
}

// DECOMP_FUNC(0x00352974, 444)
extern "C" __attribute__((naked)) void ui_func_00352974() {
    asm volatile(
        ".arm\n"
        ".hword 0x41f0, 0xe92d, 0x6001, 0xe1a0\n"
        ".hword 0xd0b8, 0xe24d, 0x4000, 0xe1a0\n"
        ".hword 0x00d0, 0xe1c6, 0x5002, 0xe1a0\n"
        ".hword 0x7000, 0xe3a0, 0x0001, 0xe190\n"
        ".hword 0x0004, 0x1a00, 0x1178, 0xe59f\n"
        ".hword 0x0004, 0xe1a0, 0xa0f6, 0xebfd\n"
        ".hword 0xd0b8, 0xe28d, 0x81f0, 0xe8bd\n"
        ".hword 0x8008, 0xe28d, 0x2f59, 0xe28f\n"
        ".hword 0x1030, 0xe3a0, 0x0078, 0xe28d\n"
        ".hword 0x9e4a, 0xebfb, 0x2030, 0xe3a0\n"
        ".hword 0x1078, 0xe28d, 0x0008, 0xe1a0\n"
        ".hword 0x685a, 0xfafd, 0x7074, 0xe58d\n"
        ".hword 0x8000, 0xe596, 0x6004, 0xe596\n"
        ".hword 0x0008, 0xe28d, 0x1004, 0xe3a0\n"
        ".hword 0x7074, 0xe28d, 0x006c, 0xe58d\n"
        ".hword 0x1068, 0xe58d, 0x8c8d, 0xfafd\n"
        ".hword 0x0001, 0xe280, 0x3068, 0xe28d\n"
        ".hword 0x0080, 0xe1a0, 0x0070, 0xe58d\n"
        ".hword 0x0001, 0xe3a0, 0x0000, 0xe58d\n"
        ".hword 0x2006, 0xe1a0, 0x1008, 0xe1a0\n"
        ".hword 0x0007, 0xe1a0, 0x0d56, 0xeb00\n"
        ".hword 0x1bff, 0xe200, 0x1521, 0xe1a0\n"
        ".hword 0x0011, 0xe351, 0x0010, 0x1a00\n"
        ".hword 0x1b00, 0xe1a0, 0x1b21, 0xe1a0\n"
        ".hword 0x0064, 0xe351, 0x000c, 0xba00\n"
        ".hword 0x00b3, 0xe351, 0x000a, 0xca00\n"
        ".hword 0x10e0, 0xe59f, 0x000d, 0xe1a0\n"
        ".hword 0xa0cb, 0xebfd, 0x0074, 0xe59d\n"
        ".hword 0x0000, 0xe350, 0x000c, 0x0a00\n"
        ".hword 0xf000, 0xe320, 0x9a62, 0xebfd\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0x0007, 0xea00, 0x1000, 0xe1a0\n"
        ".hword 0x0fa0, 0xe1b0, 0x0008, 0x0a00\n"
        ".hword 0x000d, 0xe1a0, 0xa0be, 0xebfd\n"
        ".hword 0x0074, 0xe59d, 0x0000, 0xe350\n"
        ".hword 0xfff2, 0x1aff, 0x00d0, 0xe1cd\n"
        ".hword 0x00f0, 0xe1c4, 0xd0b8, 0xe28d\n"
        ".hword 0x81f0, 0xe8bd, 0x0c12, 0xe3a0\n"
        ".hword 0x2000, 0xe3a0, 0x0004, 0xe58d\n"
        ".hword 0x1074, 0xe59d, 0x3002, 0xe1a0\n"
        ".hword 0x00b0, 0xe28d, 0x5000, 0xe58d\n"
        ".hword 0x48cb, 0xebfd, 0x2fa0, 0xe1b0\n"
        ".hword 0xf000, 0xe320, 0x0008, 0x0a00\n"
        ".hword 0x1000, 0xe1a0, 0x000d, 0xe1a0\n"
        ".hword 0xa0a9, 0xebfd, 0x0074, 0xe59d\n"
        ".hword 0x0000, 0xe350, 0x9a42, 0x1bfd\n"
        ".hword 0x00d0, 0xe1cd, 0xf000, 0xe320\n"
        ".hword 0x0006, 0xea00, 0x1000, 0xe3a0\n"
        ".hword 0x00a8, 0xe28d, 0xa0a0, 0xebfd\n"
        ".hword 0x0074, 0xe59d, 0x0000, 0xe350\n"
        ".hword 0x9a39, 0x1bfd, 0x0ad8, 0xe1cd\n"
        ".hword 0x00f0, 0xe1c4, 0xd0b8, 0xe28d\n"
        ".hword 0x81f0, 0xe8bd, 0x3882, 0xe0a1\n"
        ".hword 0x692f, 0x6f63, 0x736e, 0x252f\n"
        ".hword 0x2e75, 0x6369, 0x006e, 0x0000\n"
        ".hword 0x388c, 0xd881\n"
    );
}

// DECOMP_FUNC(0x0025b6e8, 448)
namespace engine_25b6e8_calls {
extern "C" f32 func_0024bd60(s32 a0, s32 a1, const void* elem,
                             f32 x, f32 y, f32 z, f32 limit);
} // namespace engine_25b6e8_calls

extern "C" s32 engine_func_0025b6e8(const f32* p0, const f32* p1, f32* out) {
    using namespace engine_25b6e8_calls;

    const u8* const g = reinterpret_cast<const u8*>(0x00446FE8u);
    const f32 x0 = p0[0];
    const f32 y0 = p0[1];
    const f32 z0 = p0[2];
    const f32 x1 = p1[0];
    const f32 y1 = p1[1];
    const f32 z1 = p1[2];

    for (s32 pass = 2; pass < 4; ++pass) {
        const s32 count = *reinterpret_cast<const s32*>(
            g + ((pass == 2) ? 0x0Cu : 0x10u));
        const u8* const base = *reinterpret_cast<const u8* const*>(
            g + ((pass == 2) ? 0x20u : 0x24u));

        for (s32 i = 0; i < count; ++i) {
            const u8* const elem = base + i * 0xA8;
            if (elem[8] == 0) {
                continue;
            }

            const f32* const plane = reinterpret_cast<const f32*>(elem + 0x0C);
            const f32 d0 = x0 * plane[0] + y0 * plane[1] + z0 * plane[2] - plane[3];
            const f32 d1 = x1 * plane[0] + y1 * plane[1] + z1 * plane[2] - plane[3];

            const bool crosses =
                (d0 >= 0.0f && d1 < 0.0f) || (d0 < 0.0f && d1 >= 0.0f);
            if (!crosses) {
                continue;
            }

            const f32 ad0 = __builtin_fabsf(d0);
            const f32 ad1 = __builtin_fabsf(d1);
            const f32 denom = ad0 + ad1;
            const f32 t = ad0 / denom;
            const f32 hx = x0 + (x1 - x0) * t;
            const f32 hy = y0 + (y1 - y0) * t;
            const f32 hz = z0 + (z1 - z0) * t;

            const f32 dist = func_0024bd60(
                static_cast<s8>(elem[4]),
                static_cast<s8>(elem[5]),
                elem, hx, hy, hz, 10.0f);
            if (dist >= 0.0f) {
                if (out != nullptr) {
                    const f32 t2 = (ad0 + dist) / denom;
                    out[0] = x0 + (x1 - x0) * t2;
                    out[1] = y0 + (y1 - y0) * t2;
                    out[2] = z0 + (z1 - z0) * t2;
                }
                return i;
            }
        }
    }

    return -1;
}

// DECOMP_FUNC(0x00238ed4, 452)
extern "C" __attribute__((naked)) void engine_func_00238ed4() {
    asm volatile(
        ".arm\n"
        ".hword 0x47f0, 0xe92d, 0x6000, 0xe1a0\n"
        ".hword 0xd018, 0xe24d, 0x8001, 0xe1a0\n"
        ".hword 0x4194, 0xe59f, 0x7194, 0xe59f\n"
        ".hword 0x0000, 0xe5d4, 0x0000, 0xe350\n"
        ".hword 0x0003, 0x1a00, 0x033b, 0xeb00\n"
        ".hword 0x0000, 0xe350, 0x6007, 0x01a0\n"
        ".hword 0x005a, 0x0a00, 0x5178, 0xe59f\n"
        ".hword 0x0005, 0xe1a0, 0x2ae4, 0xeb02\n"
        ".hword 0x0001, 0xe5d4, 0x0000, 0xe350\n"
        ".hword 0x001b, 0x0a00, 0x0002, 0xe5d4\n"
        ".hword 0x0000, 0xe350, 0x000f, 0x1a00\n"
        ".hword 0x0000, 0xe3a0, 0x885b, 0xeb04\n"
        ".hword 0x1102, 0xe210, 0xf000, 0xe320\n"
        ".hword 0x0005, 0x5a00, 0x4000, 0xe1a0\n"
        ".hword 0x0005, 0xe1a0, 0x2ab5, 0xeb02\n"
        ".hword 0xd018, 0xe28d, 0x0004, 0xe1a0\n"
        ".hword 0x87f0, 0xe8bd, 0x012c, 0xe59f\n"
        ".hword 0x1000, 0xe3a0, 0x094a, 0xeb02\n"
        ".hword 0x0001, 0xe3a0, 0x0002, 0xe5c4\n"
        ".hword 0x0000, 0xe358, 0x0010, 0x0a00\n"
        ".hword 0x0000, 0xe356, 0x0009, 0x0a00\n"
        ".hword 0x000c, 0xe3a0, 0x030a, 0xeb00\n"
        ".hword 0x6000, 0xe1a0, 0xf000, 0xe320\n"
        ".hword 0x0036, 0xea00, 0x0005, 0xe1a0\n"
        ".hword 0x2aa2, 0xeb02, 0xd018, 0xe28d\n"
        ".hword 0x0007, 0xe1a0, 0x87f0, 0xe8bd\n"
        ".hword 0x000b, 0xe3a0, 0x0300, 0xeb00\n"
        ".hword 0x6000, 0xe1a0, 0xf000, 0xe320\n"
        ".hword 0x002c, 0xea00, 0x8000, 0xe3a0\n"
        ".hword 0x4008, 0xe1a0, 0x000d, 0xe1a0\n"
        ".hword 0x8000, 0xe58d, 0x80ae, 0xeb04\n"
        ".hword 0x0102, 0xe200, 0x0000, 0xe350\n"
        ".hword 0x4000, 0xa59d, 0x0000, 0xe356\n"
        ".hword 0x0004, 0x0a00, 0x000c, 0xe3a0\n"
        ".hword 0x02f1, 0xeb00, 0x6000, 0xe1a0\n"
        ".hword 0xf000, 0xe320, 0x0002, 0xea00\n"
        ".hword 0x000b, 0xe3a0, 0x02ec, 0xeb00\n"
        ".hword 0x6000, 0xe1a0, 0x9088, 0xe59f\n"
        ".hword 0x1088, 0xe59f, 0x2000, 0xe3a0\n"
        ".hword 0x400c, 0xe58d, 0x0006, 0xe88d\n"
        ".hword 0x3002, 0xe1a0, 0x2001, 0xe3a0\n"
        ".hword 0x100c, 0xe28d, 0x0010, 0xe28d\n"
        ".hword 0x2cb4, 0xeb02, 0x1fa0, 0xe1b0\n"
        ".hword 0xa000, 0xe1a0, 0x310c, 0x1b02\n"
        ".hword 0x0b0a, 0xe159, 0xf000, 0xe320\n"
        ".hword 0x0008, 0x1a00, 0x0008, 0xe28d\n"
        ".hword 0x800f, 0xeb04, 0x0008, 0xe59d\n"
        ".hword 0x0001, 0xe350, 0x0003, 0x0a00\n"
        ".hword 0x003c, 0xe358, 0x8001, 0xd288\n"
        ".hword 0xffe8, 0xdaff, 0x6007, 0xe1a0\n"
        ".hword 0x0004, 0xe1b0, 0x0023, 0x1f00\n"
        ".hword 0x0005, 0xe1a0, 0x2a6b, 0xeb02\n"
        ".hword 0xd018, 0xe28d, 0x0006, 0xe1a0\n"
        ".hword 0x87f0, 0xe8bd, 0x56ca, 0x0046\n"
        ".hword 0x0bf0, 0xc8a1, 0x629c, 0x004e\n"
        ".hword 0x2400, 0x00f4, 0x0000, 0xff80\n"
        ".hword 0xca00, 0x3b9a\n"
    );
}

// DECOMP_FUNC(0x00245e78, 452)
namespace ui_245e78_calls {
extern "C" void* ui_func_00293c98();
extern "C" const u8* ui_func_00282b94(void* p, u32 a0);
extern "C" void ui_func_002be7fc(char* dst, const char* fmt, ...);
extern "C" u32 script_vm_func_0023ec3c(u32 max_val);
} // namespace ui_245e78_calls

extern "C" u32 ui_func_00245e78(u32 a0, s32 kind) {
    using namespace ui_245e78_calls;

    const u8* const row = ui_func_00282b94(ui_func_00293c98(), a0);

    f32 base = 0.0f;
    s32 slot = 0;
    const char* fmt = nullptr;
    if (kind == 3) {
        base = 5.0f;
        slot = 0x19;
        fmt = "\x8d\x8f\x88\xf3";
    } else if (kind == 6) {
        base = 25.0f;
        slot = 0x17;
        fmt = "\x8d\xac\x97\x90";
    } else if (kind == 7) {
        base = 30.0f;
        slot = 0x16;
        fmt = "\x90\x87\x96\xb0";
    } else if (kind == 8) {
        base = 20.0f;
        slot = 0x18;
        fmt = "\x8b\xd9\x94\x9b";
    } else {
        return 1u;
    }

    const s16 stat = *reinterpret_cast<const s16*>(row + 0x1C4);
    const u8* const row2 = ui_func_00282b94(ui_func_00293c98(), a0);
    const s16 bonus = (row2 != nullptr)
        ? *reinterpret_cast<const s16*>(row2 + slot * 2 + 0x72)
        : 0;

    f32 rate = base + (base * static_cast<f32>(stat)) * 0.01f;
    if (rate > 80.0f) {
        rate = 80.0f;
    }
    rate += static_cast<f32>(bonus) * 20.0f;

    char buf[32] = {};
    ui_func_002be7fc(buf, fmt);

    const u32 roll = script_vm_func_0023ec3c(0x63u);
    return (static_cast<f32>(roll) >= rate) ? 0u : 1u;
}

// DECOMP_FUNC(0x0027af3c, 452)
namespace script_vm_27af3c_calls {
extern "C" void battle_func_00267420(s32 a0, f32 f0, f32 f1, f32 f2,
                                     f32 f3, f32 f4, f32 f5, f32 f6);
} // namespace script_vm_27af3c_calls

extern "C" void script_vm_func_0027af3c() {
    using namespace script_vm_27af3c_calls;

    for (s32 i = 0; i < 24; ++i) {
        const u8* const base = *reinterpret_cast<const u8* const*>(0x00447A48u);
        const u8* const elem = base + i * 40 + 0x1C;
        if (elem[0] == 0) {
            continue;
        }

        const u16 kind = *reinterpret_cast<const u16*>(elem + 0x16);
        const f32* const f = reinterpret_cast<const f32*>(elem + 4);
        const s32 arg0 = *reinterpret_cast<const s16*>(elem + 0x1C);

        if (kind == 0x10u) {
            battle_func_00267420(arg0, f[0], f[1], f[2], f[3], 500.0f, 300.0f, 15.0f);
        } else if (kind == 0x0Au) {
            battle_func_00267420(arg0, f[0], f[1], f[2], f[3], 1000.0f, 300.0f, 15.0f);
        } else if (kind == 0x0Bu) {
            battle_func_00267420(arg0, f[0], f[1], f[2], f[3], 500.0f, 300.0f, 15.0f);
        } else if (kind == 0x0Cu) {
            battle_func_00267420(arg0, f[0], f[1], f[2], f[3], 600.0f, 350.0f, 160.0f);
        } else if (kind == 0x17u) {
            battle_func_00267420(arg0, f[0], f[1], f[2], f[3], 1100.0f, 600.0f, 60.0f);
        } else if (kind == 0x15u) {
            battle_func_00267420(arg0, f[0], f[1], f[2], f[3], 600.0f, 600.0f, 60.0f);
        } else if (kind == 0x14u) {
            battle_func_00267420(arg0, f[0], f[1], f[2], f[3], 600.0f, 600.0f, 80.0f);
        }
    }
}

// DECOMP_FUNC(0x0028277c, 456)
extern "C" __attribute__((naked)) void script_vm_func_0028277c() {
    asm volatile(
        ".arm\n"
        ".hword 0xe004, 0xe52d, 0x1a10, 0xee10\n"
        ".hword 0x2178, 0xe59f, 0x8b02, 0xed2d\n"
        ".hword 0xd004, 0xe24d, 0x0081, 0xe152\n"
        ".hword 0x000d, 0xe1a0, 0x0005, 0x9a00\n"
        ".hword 0x0473, 0xe3a0, 0x0081, 0xe150\n"
        ".hword 0x0000, 0x83e0, 0x0000, 0x93a0\n"
        ".hword 0x0000, 0xe58d, 0x0019, 0xea00\n"
        ".hword 0x314c, 0xe59f, 0x2102, 0xe3c1\n"
        ".hword 0x0002, 0xe153, 0x0014, 0x9a00\n"
        ".hword 0x0102, 0xe311, 0x0a4f, 0xeddf\n"
        ".hword 0x2a51, 0xed9f, 0x1a52, 0xeddf\n"
        ".hword 0x1a20, 0xee20, 0x0a4c, 0xeddf\n"
        ".hword 0x1a60, 0x1e31, 0x0a20, 0x1e71\n"
        ".hword 0x1a20, 0x0e31, 0x0a60, 0x0e71\n"
        ".hword 0x1ae0, 0xeebd, 0x0a10, 0xee11\n"
        ".hword 0x1a46, 0xed9f, 0x0003, 0xe200\n"
        ".hword 0x0ac1, 0xee00, 0x1a45, 0xed9f\n"
        ".hword 0x0000, 0xe58d, 0x0ac2, 0xee00\n"
        ".hword 0x0ac1, 0xee00, 0x0ae1, 0xee00\n"
        ".hword 0x0000, 0xea00, 0xa335, 0xeb05\n"
        ".hword 0x0000, 0xe59d, 0x8a40, 0xeeb0\n"
        ".hword 0x0000, 0xe350, 0x0016, 0xaa00\n"
        ".hword 0x0a10, 0xee18, 0x0080, 0xe1a0\n"
        ".hword 0x04ff, 0xe350, 0x0a08, 0x8e38\n"
        ".hword 0x0007, 0x2a00, 0x0a10, 0xee18\n"
        ".hword 0x876d, 0xeb00, 0x0004, 0xe350\n"
        ".hword 0x8776, 0x0b00, 0x0a48, 0xeeb0\n"
        ".hword 0xd004, 0xe28d, 0x8b02, 0xecbd\n"
        ".hword 0xf004, 0xe49d, 0xd004, 0x128d\n"
        ".hword 0x8b02, 0x1cbd, 0xf004, 0x149d\n"
        ".hword 0x0001, 0xe3a0, 0x8775, 0xfb00\n"
        ".hword 0x0a2a, 0xeddf, 0xd004, 0xe28d\n"
        ".hword 0x8b02, 0xecbd, 0x0aa0, 0xee80\n"
        ".hword 0xf004, 0xe49d, 0x0a08, 0xee68\n"
        ".hword 0x0001, 0xe310, 0x000e, 0x0a00\n"
        ".hword 0x0002, 0xe310, 0x0a22, 0xed9f\n"
        ".hword 0xd004, 0x028d, 0x1a21, 0xed9f\n"
        ".hword 0x1a21, 0xeddf, 0x1a80, 0xee00\n"
        ".hword 0x0a20, 0xed9f, 0x8b02, 0x0cbd\n"
        ".hword 0x1a81, 0xee40, 0x0aa1, 0xee00\n"
        ".hword 0xf004, 0x049d, 0xd004, 0xe28d\n"
        ".hword 0x8b02, 0xecbd, 0x0a40, 0xeeb1\n"
        ".hword 0xf004, 0xe49d, 0x1a18, 0xed9f\n"
        ".hword 0x0002, 0xe310, 0x0a17, 0xed9f\n"
        ".hword 0x0ac1, 0xee00, 0x1a16, 0xed9f\n"
        ".hword 0x1a80, 0xee00, 0x0a48, 0xeeb0\n"
        ".hword 0x0a20, 0xee61, 0x0a20, 0xee08\n"
        ".hword 0xfff1, 0x1aff, 0xd004, 0xe28d\n"
        ".hword 0x8b02, 0xecbd, 0xf004, 0xe49d\n"
        ".hword 0x1fb6, 0x7e92, 0x0e49, 0x4649\n"
        ".hword 0xf983, 0x3f22, 0x0000, 0x4b00\n"
        ".hword 0x0000, 0x3fc9, 0xa000, 0x39fd\n"
        ".hword 0x2000, 0x33a2, 0x611a, 0x2c34\n"
        ".hword 0x0000, 0x0000, 0x3ab9, 0xbab2\n"
        ".hword 0x9fca, 0x3d2a, 0xffdd, 0xbeff\n"
        ".hword 0x0000, 0x3f80, 0x6d33, 0x394c\n"
        ".hword 0x82da, 0x3c08, 0xaaa0, 0xbe2a\n"
    );
}

// DECOMP_FUNC(0x0012fbf4, 464)
extern "C" __attribute__((naked)) void engine_func_0012fbf4() {
    asm volatile(
        ".arm\n"
        ".hword 0x41f0, 0xe92d, 0x4000, 0xe1a0\n"
        ".hword 0x20a4, 0xe284, 0x018c, 0xe59f\n"
        ".hword 0x0a63, 0xeddf, 0x7000, 0xe3a0\n"
        ".hword 0x8b04, 0xed2d, 0x30ac, 0xe284\n"
        ".hword 0x5000, 0xe3a0, 0x0a03, 0xed94\n"
        ".hword 0x9a61, 0xed9f, 0x9a61, 0xeddf\n"
        ".hword 0x1a40, 0xeeb8, 0x8a60, 0xed9f\n"
        ".hword 0x1a10, 0xee11, 0x1a59, 0xed9f\n"
        ".hword 0x0000, 0xe151, 0x0a40, 0xceb8\n"
        ".hword 0x0a60, 0xdeb0, 0x0a01, 0xee20\n"
        ".hword 0x0ac0, 0xeebc, 0x1a10, 0xee10\n"
        ".hword 0x1101, 0xe081, 0x1281, 0xe1a0\n"
        ".hword 0x0082, 0xe882, 0x0a05, 0xed94\n"
        ".hword 0x1a40, 0xeef8, 0x1a90, 0xee11\n"
        ".hword 0x0000, 0xe151, 0x0a40, 0xcef8\n"
        ".hword 0x1038, 0xe284, 0x0006, 0xe891\n"
        ".hword 0x0a81, 0xee20, 0x0a48, 0xeddf\n"
        ".hword 0x0ac0, 0xeebc, 0x0a10, 0xee10\n"
        ".hword 0x0a04, 0xed94, 0x0a40, 0xeeb8\n"
        ".hword 0x0100, 0xe080, 0x0280, 0xe1a0\n"
        ".hword 0x0081, 0xe883, 0x00b4, 0xe284\n"
        ".hword 0x0006, 0xe880, 0x0a20, 0xee20\n"
        ".hword 0x0a3e, 0xeddf, 0x8a20, 0xee60\n"
        ".hword 0x6105, 0xe084, 0x70bc, 0xe586\n"
        ".hword 0x0a2d, 0xed96, 0x0ac0, 0xeeb8\n"
        ".hword 0x0a09, 0xee20, 0x0a28, 0xeec0\n"
        ".hword 0x0a69, 0xeeb0, 0x280a, 0xeb06\n"
        ".hword 0x0a08, 0xee20, 0x5001, 0xe285\n"
        ".hword 0x0002, 0xe355, 0x0ac0, 0xeebd\n"
        ".hword 0x0a31, 0xed86, 0xfff1, 0xbaff\n"
        ".hword 0x1a09, 0xed94, 0x0a0a, 0xed94\n"
        ".hword 0x0a06, 0xedd4, 0x1a08, 0xee21\n"
        ".hword 0x1a08, 0xee60, 0x2a88, 0xee20\n"
        ".hword 0x0a07, 0xed94, 0x20ac, 0xe59f\n"
        ".hword 0x0a10, 0xee10, 0x1040, 0xe594\n"
        ".hword 0x0002, 0xe150, 0x00cc, 0xe284\n"
        ".hword 0x1ac1, 0xeebd, 0x0ae1, 0xeefd\n"
        ".hword 0x1ac2, 0xeefd, 0x0082, 0xe880\n"
        ".hword 0x0a23, 0xcd9f, 0x1a3a, 0xed84\n"
        ".hword 0x0a3b, 0xedc4, 0x1a35, 0xedc4\n"
        ".hword 0x002d, 0xe5d4, 0x0a1f, 0xeddf\n"
        ".hword 0x0001, 0xe350, 0x000a, 0x0a00\n"
        ".hword 0x0ac0, 0xee70, 0x1a08, 0xee20\n"
        ".hword 0x00f0, 0xe284, 0x0a88, 0xee60\n"
        ".hword 0x0ae0, 0xeebd, 0x0ac1, 0xeefd\n"
        ".hword 0x0a02, 0xec80, 0x03d0, 0xe1c4\n"
        ".hword 0x8b04, 0xecbd, 0x41f0, 0xe8bd\n"
        ".hword 0x4f75, 0xea06, 0x0a60, 0xee70\n"
        ".hword 0x1a11, 0xed9f, 0x0a01, 0xee20\n"
        ".hword 0x0a88, 0xee60, 0x0ac0, 0xeebd\n"
        ".hword 0x0ae0, 0xeefd, 0x0a3d, 0xed84\n"
        ".hword 0x0a3c, 0xedc4, 0xfff2, 0xeaff\n"
        ".hword 0x6a7f, 0x409c, 0x6a7f, 0x409c\n"
        ".hword 0x7e1d, 0x3e51, 0x126f, 0x3a83\n"
        ".hword 0xb000, 0x46ff, 0x0000, 0xc040\n"
        ".hword 0x0000, 0x4120, 0x0000, 0x4300\n"
        ".hword 0x3333, 0x3f73, 0x3333, 0x3f73\n"
        ".hword 0x0000, 0x3f80, 0x0000, 0xc300\n"
    );
}

// DECOMP_FUNC(0x0026eccc, 464)
extern "C" void engine_func_0026eccc(
    s32 axis, s32 vert_idx, f32* out_normal, f32* out_d,
    f32 px, f32 py, f32 pz,
    f32 ax, f32 ay, f32 az,
    f32 bx, f32 by, f32 bz) {
    struct Vec3 {
        f32 x;
        f32 y;
        f32 z;
    };

    Vec3 p0{};
    Vec3 p1{};
    Vec3 p2{};
    if (axis == 0) {
        p0 = { 0.0f, ay, az };
        p1 = { 0.0f, by, bz };
        p2 = { 10.0f, by, bz };
    } else if (axis == 1) {
        p0 = { ax, 0.0f, az };
        p1 = { bx, 0.0f, bz };
        p2 = { bx, 10.0f, bz };
    } else if (axis == 2) {
        p0 = { ax, ay, 0.0f };
        p1 = { bx, by, 0.0f };
        p2 = { bx, by, 10.0f };
    }

    const Vec3 v0 = { p1.x - p0.x, p1.y - p0.y, p1.z - p0.z };
    const Vec3 v1 = { p2.x - p1.x, p2.y - p1.y, p2.z - p1.z };

    const f32 cx = v0.y * v1.z - v0.z * v1.y;
    const f32 cy = v0.z * v1.x - v0.x * v1.z;
    const f32 cz = v0.x * v1.y - v0.y * v1.x;

    const f32 len_sq = cx * cx + cy * cy + cz * cz;
    f32 len = 0.0f;
    asm("vsqrt.f32 %0, %1" : "=t"(len) : "t"(len_sq));
    const f32 inv = 1.0f / len;
    auto clamp_eps = [](f32 v) -> f32 {
        return (v > -9.999999747378752e-05f && v < 9.999999747378752e-05f) ? 0.0f : v;
    };
    f32 nx = clamp_eps(cx * inv);
    f32 ny = clamp_eps(cy * inv);
    f32 nz = clamp_eps(cz * inv);

    const Vec3 pref = (vert_idx == 0) ? p0 : ((vert_idx == 1) ? p1 : p2);
    f32 d = nx * pref.x + ny * pref.y + nz * pref.z;
    const f32 dist = (px * nx + py * ny + pz * nz) - d;
    if (dist < 0.0f) {
        nx = -nx;
        ny = -ny;
        nz = -nz;
        d = nx * pref.x + ny * pref.y + nz * pref.z;
    }

    out_normal[0] = nx;
    out_normal[1] = ny;
    out_normal[2] = nz;
    *out_d = d;
}

// DECOMP_FUNC(0x0016b854, 476)
extern "C" __attribute__((naked)) void func_0016b854() {
    asm volatile(
        ".arm\n"
        ".hword 0x0000, 0xe358, 0x0003, 0x0a00\n"
        ".hword 0xc008, 0xe1a0, 0x60ba, 0xe083\n"
        ".hword 0xc001, 0xe25c, 0xfffc, 0x1aff\n"
        ".hword 0x9004, 0xe494, 0x9109, 0xe797\n"
        ".hword 0x90ba, 0xe083, 0x60ba, 0xe083\n"
        ".hword 0x60ba, 0xe083, 0x9004, 0xe494\n"
        ".hword 0x9109, 0xe797, 0x90ba, 0xe083\n"
        ".hword 0x60ba, 0xe083, 0x60ba, 0xe083\n"
        ".hword 0x9004, 0xe494, 0x9109, 0xe797\n"
        ".hword 0x90ba, 0xe083, 0x60ba, 0xe083\n"
        ".hword 0x60ba, 0xe083, 0x9004, 0xe494\n"
        ".hword 0x9109, 0xe797, 0x90ba, 0xe083\n"
        ".hword 0x60ba, 0xe083, 0x60ba, 0xe083\n"
        ".hword 0x9004, 0xe494, 0x9109, 0xe797\n"
        ".hword 0x90ba, 0xe083, 0x60ba, 0xe083\n"
        ".hword 0x60ba, 0xe083, 0x9004, 0xe494\n"
        ".hword 0x9109, 0xe797, 0x90ba, 0xe083\n"
        ".hword 0x60ba, 0xe083, 0x60ba, 0xe083\n"
        ".hword 0x9004, 0xe494, 0x9109, 0xe797\n"
        ".hword 0x90ba, 0xe083, 0x60ba, 0xe083\n"
        ".hword 0x60ba, 0xe083, 0x9004, 0xe494\n"
        ".hword 0x9109, 0xe797, 0x90ba, 0xe083\n"
        ".hword 0x60ba, 0xe083, 0x60ba, 0xe083\n"
        ".hword 0x9004, 0xe494, 0x9109, 0xe797\n"
        ".hword 0x90ba, 0xe083, 0x60ba, 0xe083\n"
        ".hword 0x60ba, 0xe083, 0x9004, 0xe494\n"
        ".hword 0x9109, 0xe797, 0x90ba, 0xe083\n"
        ".hword 0x60ba, 0xe083, 0x60ba, 0xe083\n"
        ".hword 0x9004, 0xe494, 0x9109, 0xe797\n"
        ".hword 0x90ba, 0xe083, 0x60ba, 0xe083\n"
        ".hword 0x60ba, 0xe083, 0x9004, 0xe494\n"
        ".hword 0x9109, 0xe797, 0x90ba, 0xe083\n"
        ".hword 0x60ba, 0xe083, 0x60ba, 0xe083\n"
        ".hword 0x9004, 0xe494, 0x9109, 0xe797\n"
        ".hword 0x90ba, 0xe083, 0x60ba, 0xe083\n"
        ".hword 0x60ba, 0xe083, 0x9004, 0xe494\n"
        ".hword 0x9109, 0xe797, 0x90ba, 0xe083\n"
        ".hword 0x60ba, 0xe083, 0x60ba, 0xe083\n"
        ".hword 0x9004, 0xe494, 0x9109, 0xe797\n"
        ".hword 0x90ba, 0xe083, 0x60ba, 0xe083\n"
        ".hword 0x60ba, 0xe083, 0x9004, 0xe494\n"
        ".hword 0x9109, 0xe797, 0x90ba, 0xe083\n"
        ".hword 0x60ba, 0xe083, 0x60ba, 0xe083\n"
        ".hword 0x9004, 0xe494, 0x9109, 0xe797\n"
        ".hword 0x90ba, 0xe083, 0x60ba, 0xe083\n"
        ".hword 0x60ba, 0xe083, 0x9004, 0xe494\n"
        ".hword 0x9109, 0xe797, 0x90ba, 0xe083\n"
        ".hword 0x60ba, 0xe083, 0x60ba, 0xe083\n"
        ".hword 0x9004, 0xe494, 0x9109, 0xe797\n"
        ".hword 0x90ba, 0xe083, 0x60ba, 0xe083\n"
        ".hword 0x60ba, 0xe083, 0x9004, 0xe494\n"
        ".hword 0x9109, 0xe797, 0x90ba, 0xe083\n"
        ".hword 0x60ba, 0xe083, 0x60ba, 0xe083\n"
        ".hword 0x9004, 0xe494, 0x9109, 0xe797\n"
        ".hword 0x90ba, 0xe083, 0xc003, 0xe278\n"
        ".hword 0xf00e, 0x01a0, 0x60ba, 0xe083\n"
        ".hword 0xc001, 0xe25c, 0xfffc, 0x1aff\n"
        ".hword 0xf00e, 0xe1a0, 0x6e14, 0x0000\n"
        ".hword 0x4000, 0x0000, 0x8000, 0xffff\n"
        ".hword 0x7fff, 0x0000\n"
    );
}

// DECOMP_FUNC(0x00317cdc, 476)
namespace evttex_317cdc_calls {
extern "C" void* AsdMem_Alloc(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);
extern "C" void AsdMem_Zero(void* ptr, u32 size);
extern "C" const u8* AsdTable_FindBattleRow(u32 id);
extern "C" s32 AsdScene_LoadMode();
extern "C" void* Npc2d_CreateSprite(s32 sprite_id, u32 a1);
extern "C" void* AsdTask_CreateCalc(const char* name, u32 prio, u32 a2, u32 a3,
                                    void (*cb)(void*), u32 a5, u32 a6);
extern "C" void* AsdTask_CreateDraw(const char* name, u32 prio, u32 a2, u32 a3,
                                    void (*cb)(void*), u32 a5, u32 a6, void* parent);
} // namespace evttex_317cdc_calls

extern "C" void* decomp_func_00317cdc(u32 id, f32 x, f32 z)
    asm("3dEventTex_func_00317cdc");

extern "C" void* decomp_func_00317cdc(u32 id, f32 x, f32 z) {
    using namespace evttex_317cdc_calls;

    u8* const p = static_cast<u8*>(AsdMem_Alloc(0x100, 0x100, 0, 0x48, 1));
    AsdMem_Zero(p, 0x48);

    *reinterpret_cast<f32*>(p + 0x08) = 1.0f;
    *reinterpret_cast<f32*>(p + 0x0C) = 0.0f;
    *reinterpret_cast<f32*>(p + 0x10) = 0.25f;
    p[0x14] = 0;
    p[0x17] = 0;

    const u8* const row = AsdTable_FindBattleRow(id & 0xFFFFu);
    const s32 sprite_id = *reinterpret_cast<const s16*>(row + 0x88);
    *reinterpret_cast<s32*>(p + 0x38) = sprite_id;
    p[0x44] = 1;

    if (AsdScene_LoadMode() != 0) {
        *reinterpret_cast<u32*>(p + 0x04) = 1u;
    } else {
        *reinterpret_cast<void**>(p + 0x34) = Npc2d_CreateSprite(sprite_id, 1);
        *reinterpret_cast<u32*>(p + 0x04) = 2u;
    }

    *reinterpret_cast<u32*>(p + 0x00) = static_cast<u16>(0u - id);

    u32 pose = 5u;
    if (x <= -4.0f) {
        pose = 0x10u;
    } else if (x <= -3.0f) {
        pose = 3u;
    } else if (x >= 3.0f) {
        pose = 0x11u;
    } else if (x >= 1.5f) {
        pose = 4u;
    } else if (x < 0.0f) {
        pose = 0x12u;
    }
    *reinterpret_cast<u32*>(p + 0x3C) = pose;

    *reinterpret_cast<f32*>(p + 0x2C) = x;
    *reinterpret_cast<f32*>(p + 0x30) = z;
    p[0x16] = 1;
    p[0x15] = 0;

    void* const task = AsdTask_CreateCalc(
        "EVE_BtlTex", 2, 0, 0,
        reinterpret_cast<void (*)(void*)>(0x001DFFBCu),
        0x002DB938u,
        static_cast<u32>(reinterpret_cast<std::uintptr_t>(p)));

    AsdTask_CreateDraw(
        "EVE_BtlTexDraw", 0x6Fu, 0, 0,
        reinterpret_cast<void (*)(void*)>(0x001E0138u),
        0,
        static_cast<u32>(reinterpret_cast<std::uintptr_t>(p)),
        task);

    return task;
}

// DECOMP_FUNC(0x0015b5b8, 484)
extern "C" u32 AsdGpu_Address(const void* ptr);

extern "C" void engine_func_0015b5b8(u8* dst, const u8* src) {
    auto word_at = [](u8* base, u32 off) -> u32& {
        return *reinterpret_cast<u32*>(base + off);
    };
    auto cword_at = [](const u8* base, u32 off) -> u32 {
        return *reinterpret_cast<const u32*>(base + off);
    };
    auto rel_ptr = [](const u8* slot) -> const u8* {
        const s32 off = *reinterpret_cast<const s32*>(slot);
        return off != 0 ? (slot + off) : nullptr;
    };

    word_at(dst, 0x48u) = 0x38u;

    const u32 src_fmt = cword_at(src, 0x34u);
    word_at(dst, 0x10u) = (word_at(dst, 0x10u) & ~0xFu) | (src_fmt & 0xFu);
    word_at(dst, 0x1Cu) = (word_at(dst, 0x1Cu) & ~0x0FF00000u) | 0x00900000u;
    word_at(dst, 0x20u) = (word_at(dst, 0x20u) & 0xF800F800u)
                        | (cword_at(src, 0x18u) & 0x7FFu)
                        | ((cword_at(src, 0x1Cu) & 0x7FFu) << 16);

    word_at(dst, 0x24u) &= ~0x30u;
    if (src_fmt == 0xCu) {
        word_at(dst, 0x24u) |= 0x20u;
    }

    word_at(dst, 0x28u) &= ~0x000F0000u;
    word_at(dst, 0x2Cu) &= 0xF0000000u;
    for (u32 off = 0x30u; off <= 0x40u; off += 4u) {
        word_at(dst, off) &= ~0x003FFFFFu;
    }

    const u8* meta = rel_ptr(dst + 0x0Cu);
    const u32 meta_type = cword_at(meta, 0x08u) & 0xFFu;
    if (meta_type != 0u && meta_type != 1u) {
        word_at(dst, 0x28u) |= ((cword_at(src, 0x28u) - 1u) & 0xFu) << 16;
    }

    for (u32 i = 0u; i < 6u; ++i) {
        const u8* sub = rel_ptr(src + 0x38u + i * 4u);
        const u32 direct = cword_at(sub, 0x18u);
        const void* data_ptr = direct != 0u
            ? reinterpret_cast<const void*>(static_cast<std::uintptr_t>(direct))
            : static_cast<const void*>(rel_ptr(sub + 0x0Cu));
        const u32 gpu_addr = AsdGpu_Address(data_ptr);
        if (i == 0u) {
            word_at(dst, 0x2Cu) |= (gpu_addr & 0x7FFFFFFFu) >> 3;
        } else {
            word_at(dst, 0x2Cu + i * 4u) |= (gpu_addr >> 3) & 0xE03FFFFFu;
        }
    }
}

// DECOMP_FUNC(0x0012f768, 492)
extern "C" void engine_func_0013fdb0(void* elem, u32 zero);
extern "C" void* engine_func_002bb218();
extern "C" u32 engine_func_002bb0b4(void* obj, u32 mode);
extern "C" void engine_func_002b4d78(void* obj, u32 val);
extern "C" void func_001409b8(void* ptr);
extern "C" void func_002acb8c(void* field_ptr, u32 val, void* src_ptr);
extern "C" void func_002b4fa8(void* dst, u32 a, u32 b);

extern "C" void engine_func_0012f768(u8* obj) {
    auto word_at = [](u8* base, u32 off) -> u32& {
        return *reinterpret_cast<u32*>(base + off);
    };

    word_at(obj, 0x04u) = 0u;
    word_at(obj, 0xA0u) = 0u;

    const u32 count0 = word_at(obj, 0x20u);
    u8* const arr0 = reinterpret_cast<u8*>(static_cast<std::uintptr_t>(word_at(obj, 0x24u)));
    for (u32 i = 0u; i < count0; ++i) {
        engine_func_0013fdb0(arr0 + i * 0x48u, 0u);
    }

    void* const mgr = engine_func_002bb218();
    const u32 handle = engine_func_002bb0b4(mgr, 1u);
    engine_func_002b4d78(mgr, handle);

    word_at(obj, 0x20u) = 0u;
    word_at(obj, 0x24u) = 0u;
    func_001409b8(obj + 0x88u);

    if (word_at(obj, 0xB4u) == 0u) {
        return;
    }

    auto destroy_block = [&word_at](u8* block, u32 stride) {
        u8* elem = reinterpret_cast<u8*>(static_cast<std::uintptr_t>(word_at(block, 0x00u)));
        const u32 count = word_at(block, 0x04u) / stride;
        for (u32 i = 0u; i < count; ++i) {
            using DtorFn = void (*)(void*);
            const u32* vtbl = *reinterpret_cast<const u32* const*>(elem);
            DtorFn dtor = reinterpret_cast<DtorFn>(static_cast<std::uintptr_t>(vtbl[1]));
            dtor(elem);
            elem += stride;
        }
        func_002acb8c(block + 0x14u, word_at(block, 0x18u), block + 0x18u);
        func_002acb8c(block + 0x08u, word_at(block, 0x0Cu), block + 0x0Cu);
    };

    destroy_block(obj + 0x28u, 0x558u);
    func_002b4fa8(obj + 0xA4u, word_at(obj, 0xB4u), word_at(obj, 0xB8u));
    destroy_block(obj + 0x48u, 0x460u);
    destroy_block(obj + 0x68u, 0x2BD4u);

    word_at(obj, 0xB4u) = 0u;
    word_at(obj, 0xB8u) = 0u;
}

// DECOMP_FUNC(0x00354a44, 492)
extern "C" s32 engine_func_002b45f8(const char* a, const char* b, u32 max_len);
extern "C" void engine_func_002c14f4(u32 code, const void* caller_pc);

extern "C" u32 engine_func_00354a44(const u8* obj) {
    struct Entry {
        const char* key;
        const char* val;
    };
    struct Table {
        const Entry* entries;
        u32 count;
    };

    const u32 kErr = 0xF9613903u;
    auto lookup = [&](const char* key) -> const char* {
        const Table* tbl = *reinterpret_cast<const Table* const*>(obj + 4);
        for (u32 i = 0u; i < tbl->count; ++i) {
            if (engine_func_002b45f8(tbl->entries[i].key, key, 0x40u) == 0) {
                const char* val = tbl->entries[i].val;
                if (val != nullptr) {
                    return val;
                }
                break;
            }
        }
        engine_func_002c14f4(kErr, __builtin_return_address(0));
        return nullptr;
    };

    const char* status = lookup("sys.ECardStatus");
    if (engine_func_002b45f8("REDEEMABLE", status, 11u) == 0) {
        const char* cur = lookup("sys.ECardCurrency");
        if (engine_func_002b45f8("GUNIT", cur, 6u) == 0) {
            return 0u;
        }
        if (engine_func_002b45f8("POINTS", cur, 7u) == 0) {
            return 0xC8A13904u;
        }
        return 0xC8A13906u;
    }
    if (engine_func_002b45f8("REDEEMED", status, 9u) == 0) {
        return 0xC8A13900u;
    }
    if (engine_func_002b45f8("REVOKED", status, 8u) == 0) {
        return 0xC8A13901u;
    }
    if (engine_func_002b45f8("INACTIVE", status, 9u) == 0) {
        return 0xC8A13902u;
    }
    return kErr;
}

// DECOMP_FUNC(0x00381d9c, 492)
extern "C" void script_vm_func_003854d8(void* obj);
extern "C" void engine_func_002c4b30(void* dst, u32 size);
extern "C" void script_vm_func_00297704(const char* path, void* dst, u32 flag);
extern "C" void camp_func_002c3344(void* group);
extern "C" u32 camp_func_002c32f8(
    u8* group, u32 table, u32 count, u32 reg_word,
    u32 stack_0, u32 stack_1, u32 stack_2,
    u32 stack_3, u32 stack_4, u32 stack_5, u32 stack_6);
extern "C" void script_vm_func_00385cbc(void* ptr);
extern "C" void script_vm_func_00385cfc(void* ptr);
extern "C" void script_vm_func_00385d04(void* ptr);
extern "C" void AsdTMTexTable_func_002c4e28(u32 id);
extern "C" void camp_func_002a6214(u32 id, u32 flag);
extern "C" u32 AsdText_func_002bda1c(u32 arg);
extern "C" void PlaceWin_Init();
extern "C" void ui_func_002a7540(u32 arg);
extern "C" void script_vm_func_001a15a0(u32 arg);
extern "C" void* script_vm_func_002b6700(u32 quest_id);
extern "C" u32 script_vm_func_0029923c(u32 qid, u32 mode);
extern "C" void script_vm_func_0028f15c(u32 qid);

extern "C" void script_vm_func_00381d9c(u8* obj) {
    auto word_at = [](u8* base, u32 off) -> u32& {
        return *reinterpret_cast<u32*>(base + off);
    };

    script_vm_func_003854d8(obj);

    word_at(obj, 0x000u) = 0u;
    word_at(obj, 0x00Cu) = 0u;
    word_at(obj, 0x014u) = 0u;
    word_at(obj, 0x5A0u) = 0u;
    word_at(obj, 0x5A8u) = 0u;
    word_at(obj, 0x5ACu) = 0u;
    word_at(obj, 0x5B0u) = 0u;
    word_at(obj, 0x5B4u) = 0u;
    word_at(obj, 0x5B8u) = 0u;
    word_at(obj, 0x5BCu) = 0u;
    word_at(obj, 0x5C0u) = 0u;
    word_at(obj, 0x5A4u) = 0u;

    engine_func_002c4b30(obj + 0x6CCu, 0x640u);
    script_vm_func_00297704("quest_center/common/qc_common.bf", obj + 0x5A0u, 0u);
    script_vm_func_00297704("quest_center/common/qc_common.mbm", obj + 0x5A4u, 0u);

    camp_func_002c3344(obj + 0x024u);
    camp_func_002c32f8(
        obj + 0x024u, 0u, 0u, 0x00405898u,
        0x18u, 0u, 0u, 0u, 0u, 0x004058B0u, 0xA8u);

    script_vm_func_00385cbc(obj + 0x020u);
    script_vm_func_00385cfc(obj + 0x020u);
    script_vm_func_00385d04(obj + 0x020u);

    word_at(obj, 0xDA4u) = 0u;
    word_at(obj, 0xFB4u) = 0u;
    word_at(obj, 0xFB0u) = 0u;
    word_at(obj, 0xD8Cu) = 0u;
    word_at(obj, 0x01Cu) = 0xFFFFFFFFu;
    word_at(obj, 0x59Cu) = 0u;
    obj[0xD40u] = 0u;

    AsdTMTexTable_func_002c4e28(0x31u);
    camp_func_002a6214(0x31u, 0u);

    for (u32 i = 0u; i < 4u; ++i) {
        word_at(obj, 0x28Cu + i * 4u) = 0u;
        word_at(obj, 0x28Cu + i * 4u) = AsdText_func_002bda1c(0u);
    }

    PlaceWin_Init();
    ui_func_002a7540(0u);
    script_vm_func_001a15a0(0u);

    for (u32 qid = 0x15Eu; qid < 0x190u; ++qid) {
        const u8* node = static_cast<const u8*>(script_vm_func_002b6700(qid));
        if (node != nullptr && node[6] == 0u) {
            if (script_vm_func_0029923c(qid, 1u) == 0u) {
                script_vm_func_0028f15c(qid);
            }
        }
    }
}

// DECOMP_FUNC(0x002f38bc, 496)
extern "C" void func_0024742c(
    u32 color, float x0, float y0, float z0, float x1, float y1, float z1);

extern "C" void func_002f38bc() {
    auto draw_seg = [](u32 color, const float* a, const float* b) {
        func_0024742c(color, a[0], a[1], a[2], b[0], b[1], b[2]);
    };
    auto draw_ray = [](const float* origin, const float* dir) {
        const float end_x = origin[0] + dir[0] * 300.0f;
        const float end_y = origin[1] + dir[1] * 300.0f;
        const float end_z = origin[2] + dir[2] * 300.0f;
        func_0024742c(0xFF0000FFu, origin[0], origin[1], origin[2], end_x, end_y, end_z);
    };

    const s32* const count_ptr = reinterpret_cast<const s32*>(0x00447A28u);
    const u8* const* const objs = reinterpret_cast<const u8* const*>(0x004A0FE4u);
    const u8* const boxes = reinterpret_cast<const u8*>(0x004A0FE4u + 0x280u);

    for (s32 i = 0; i < *count_ptr; ++i) {
        const u8* const obj = objs[i];
        const u8* const inner = *reinterpret_cast<const u8* const*>(obj + 0x14u);
        const u32 mode = **reinterpret_cast<const u32* const*>(inner + 0x1Cu);
        const u8* const box = boxes + static_cast<u32>(i) * 0x178u;
        auto vec_at = [box](u32 off) -> const float* {
            return reinterpret_cast<const float*>(box + off);
        };

        if (mode == 1u) {
            const u32 kind = *reinterpret_cast<const u32*>(inner + 0x04u);
            if (kind == 0x27u) {
                draw_seg(0x00FF00FFu, vec_at(0x00u), vec_at(0x0Cu));
                draw_seg(0x00FF00FFu, vec_at(0x00u), vec_at(0x18u));
                draw_seg(0x00FF00FFu, vec_at(0x0Cu), vec_at(0x24u));
                draw_seg(0x00FF00FFu, vec_at(0x18u), vec_at(0x24u));
            } else {
                draw_seg(0x00FF00FFu, vec_at(0x18u), vec_at(0x24u));
            }
            draw_ray(vec_at(0x60u), vec_at(0x6Cu));
        } else if (mode == 2u) {
            draw_seg(0x00FF00FFu, vec_at(0x30u), vec_at(0x3Cu));
            draw_seg(0x00FF00FFu, vec_at(0x3Cu), vec_at(0x54u));
            draw_seg(0x00FF00FFu, vec_at(0x48u), vec_at(0x54u));
            draw_seg(0x00FF00FFu, vec_at(0x30u), vec_at(0x48u));
            draw_ray(vec_at(0x60u), vec_at(0x6Cu));
        }
    }
}

// DECOMP_FUNC(0x00125d88, 500)
extern "C" u32 ui_func_002c5f7c(u32 a, u32 b);
extern "C" void ui_func_002bf710(float alpha);
extern "C" void script_vm_func_002bef14();
extern "C" void ui_func_002bf460(u32 a, u32 b, u32 c, u32 d, u32 s0, u32 s1);
extern "C" u32 engine_func_002c583c(u32 a);
extern "C" void ui_func_002be77c(
    u32 a, s32 b, const char* text,
    float x, float y, float z, float sx, float sy);
extern "C" void engine_func_002aefc8(u32 a, const void* ptr, float x, float y);

extern "C" u32 ui_func_00125d88() {
    struct StateStack {
        u32 index;
        u32 reserved;
        u32 entries[4];
        u8 dirty;
        u8 pad[3];
        void (*on_change)(u32);
    };

    const u8* const overlay = *reinterpret_cast<const u8* const*>(0x0044E2E8u);
    if (*reinterpret_cast<const u32*>(overlay + 8u) != 1u) {
        return 0u;
    }

    auto sync_stack = [](StateStack* stk, u32 prev, u32 next) {
        if (stk->dirty != 0u || prev != next) {
            stk->on_change(next);
            stk->dirty = 0u;
        }
    };

    auto get_stack = []() -> StateStack* {
        u8* const base = *reinterpret_cast<u8* const*>(0x0044EA00u);
        return reinterpret_cast<StateStack*>(base + 0x124Cu);
    };

    const u32 pushed = ui_func_002c5f7c(1u, 0u);
    {
        StateStack* const stk = get_stack();
        const u32 idx = stk->index;
        const u32 prev = stk->entries[idx];
        stk->index = idx + 1u;
        stk->entries[idx + 1u] = pushed;
        sync_stack(stk, prev, pushed);
    }

    ui_func_002bf710(1.0f);
    script_vm_func_002bef14();
    ui_func_002bf460(2u, 0u, 0u, 0u, 0u, 0xBu);

    {
        StateStack* const stk = get_stack();
        const u32 old_idx = stk->index;
        const u32 prev = stk->entries[old_idx];
        const u32 new_idx = old_idx - 1u;
        stk->index = new_idx;
        const u32 top = stk->entries[new_idx];
        sync_stack(stk, prev, top);
    }

    static const char kLabelAlt[] = {
        '\x82', '\x6f', '\x82', '\x62', '\x83', '\x8d', '\x81', '\x5b', '\x83', '\x68', '\x00'
    };
    static const char kLabelNow[] = {
        '\x82', '\x71', '\x82', '\x6e', '\x82', '\x6c', '\x83', '\x8d', '\x81', '\x5b', '\x83', '\x68', '\x00'
    };
    static const char kLabelMsg[] = {
        '\x90', '\x5e', '\x81', '\x45', '\x8f', '\x97', '\x90', '\x5f', '\x93', '\x5d', '\x90', '\xb6', '\x87', '\x57', '\x00'
    };

    const char* const mode_label = (engine_func_002c583c(0u) != 0u) ? kLabelAlt : kLabelNow;
    ui_func_002be77c(3u, -1, mode_label, 296.0f, 194.0f, 0.0f, 1.0f, 1.0f);
    ui_func_002be77c(3u, -1, kLabelMsg, 296.0f, 208.0f, 0.0f, 1.0f, 1.0f);
    engine_func_002aefc8(1u, overlay + 0x10u, 228.0f, 228.0f);
    return 0u;
}

// DECOMP_FUNC(0x0015eb60, 500)
extern "C" float camp_func_002b9cf8(float base, float exp);
extern "C" void engine_func_002c3b48(void* ptr, u32 size);

extern "C" void func_0015eb60(u8* obj) {
    auto word_at = [obj](u32 off) -> u32& {
        return *reinterpret_cast<u32*>(obj + off);
    };
    auto sword_at = [obj](u32 off) -> s32& {
        return *reinterpret_cast<s32*>(obj + off);
    };
    auto float_at = [obj](u32 off) -> float {
        return *reinterpret_cast<const float*>(obj + off);
    };
    auto quantize_rate = [](u32 raw) -> u32 {
        float f = static_cast<float>(raw);
        if (!(f > 4.888f)) {
            f = 4.888f;
        }
        return static_cast<u32>(f * 0.20458265f) * 160u;
    };

    word_at(0x9Cu) = quantize_rate(word_at(0x04u));
    word_at(0xA0u) = 0u;
    word_at(0xA4u) = quantize_rate(word_at(0x0Cu));
    word_at(0xA8u) = 0u;

    sword_at(0xACu) = sword_at(0x30u);
    sword_at(0xB0u) = sword_at(0x34u);

    const float denom = (static_cast<float>(word_at(0x08u)) * 0.001f) * 32728.0f;
    for (u32 i = 0u; i < 2u; ++i) {
        word_at(0xB4u + i * 4u) = 0u;
        const float exp_val = (static_cast<float>(sword_at(0xACu + i * 4u)) * -3.0f) / denom;
        sword_at(0xBCu + i * 4u) = static_cast<s32>(camp_func_002b9cf8(10.0f, exp_val) * 128.0f);
    }

    word_at(0xC4u) = word_at(0x38u);
    word_at(0xC8u) = 0u;
    sword_at(0xCCu) = static_cast<s32>(float_at(0x10u) * 128.0f);
    sword_at(0xE0u) = static_cast<s32>(float_at(0x1Cu) * 128.0f);
    sword_at(0xE4u) = static_cast<s32>(float_at(0x20u) * 128.0f);

    float p = float_at(0x14u);
    if (sword_at(0x14u) > 0x3F733333) {
        p = 0.95f;
    }
    if (obj[0x24u] == 1u) {
        sword_at(0xE8u) = static_cast<s32>((p - 1.0f) * 128.0f);
        sword_at(0xECu) = static_cast<s32>(p * -128.0f);
    } else {
        sword_at(0xE8u) = static_cast<s32>((1.0f - p) * 128.0f);
        sword_at(0xECu) = static_cast<s32>(p * 128.0f);
    }

    engine_func_002c3b48(
        reinterpret_cast<void*>(static_cast<std::uintptr_t>(word_at(0x28u))),
        word_at(0x2Cu));
}

// DECOMP_FUNC(0x001e1d1c, 500)
extern "C" u32 engine_func_002c5978(
    const char* name, u32 prio, u32 a2, u32 a3, u32 fn, u32 dtor, u32 a6);
extern "C" void engine_func_002bf86c(char* dst, const char* src);
extern "C" void engine_func_0025c7d8(u32 id);
extern "C" void script_vm_func_0020118c();
extern "C" void camp_func_002c4c00(
    const char* name, u32 prio, u32 a2, u32 a3, u32 fn, u32 dtor, u32 a6, u32 parent);

extern "C" void engine_func_001e1d1c(const u8* launch) {
    u8* const obj = *reinterpret_cast<u8* const*>(0x0043E0D0u);
    auto word_at = [obj](u32 off) -> u32& {
        return *reinterpret_cast<u32*>(obj + off);
    };

    word_at(0x08u) = 0u;
    word_at(0x0Cu) = 0u;
    word_at(0x10u) = 0u;
    word_at(0x14u) = 0u;
    word_at(0x18u) = 0u;
    word_at(0x1Cu) = 0u;
    word_at(0x28u) = 0u;
    word_at(0x2Cu) = 0u;
    word_at(0x30u) = 0u;
    word_at(0x34u) = 0u;
    obj[0x20u] = 0u;
    obj[0x21u] = 0u;
    obj[0x22u] = 0u;
    obj[0x23u] = 0u;
    obj[0x24u] = 0u;
    obj[0x04u] = 0u;

    if (launch != nullptr) {
        u8* const params = reinterpret_cast<u8*>(0x004937C4u);
        *reinterpret_cast<u32*>(params + 0u) = *reinterpret_cast<const u32*>(launch + 0u);
        const u32 mode = *reinterpret_cast<const u32*>(launch + 4u);
        *reinterpret_cast<u32*>(params + 4u) = mode;
        if (mode == 0xFFFFFFFFu) {
            engine_func_002bf86c(
                reinterpret_cast<char*>(params + 8u),
                reinterpret_cast<const char*>(launch + 8u));
        } else {
            params[8u] = 0u;
        }
        word_at(0x00u) = engine_func_002c5978(
            "EVENT CALC", 2u, 0u, 0u, 0x0019F2D8u, 0x002CA010u, 0u);
        return;
    }

    if (engine_func_002c583c(2u) == 0u) {
        engine_func_0025c7d8(0x19u);
        engine_func_0025c7d8(0x1Bu);
        engine_func_0025c7d8(0x1Cu);
        script_vm_func_0020118c();
    }

    const u32 task = engine_func_002c5978(
        "EVENT VIEW CALC", 2u, 0u, 0u, 0x001E4C7Cu, 0x002CA010u, 0u);
    word_at(0x00u) = task;
    camp_func_002c4c00(
        "EVENT VIEW UDRAW", 0x73u, 0u, 0u, 0x0020F55Cu, 0x002E07A8u, 0u, task);
    camp_func_002c4c00(
        "EVENT VIEW DDRAW", 0xE6u, 0u, 0u, 0x002CA028u, 0x002F4AE0u, 0u, word_at(0x00u));
}

// DECOMP_FUNC(0x0038d59c, 500)
extern "C" void engine_func_002bb09c(void* dst);
extern "C" u64* engine_func_002bad80(u64* out, u32 arg);
extern "C" u32 func_0038b600(void* mgr);
extern "C" u32 engine_func_0039444c(void* ptr, u32* err_out, u32* flag_out);
extern "C" u32 func_0023a24c(void* ptr);
extern "C" void engine_func_0038b470(u64* out, void* mgr);
extern "C" u32 engine_func_002a1578(void* ptr);
extern "C" void func_002b49f4(void* mgr);
extern "C" u32 nn_sdk_func_0038b664(void* mgr);

extern "C" void engine_func_0038d59c(u8* out, u8* ctx) {
    out[0] = 1u;
    engine_func_002bb09c(out + 4);
    *reinterpret_cast<u32*>(out + 0x0Cu) = 0u;
    *reinterpret_cast<u32*>(out + 0x10u) = 0u;

    u64 tmp_ts = 0u;
    *reinterpret_cast<u64*>(out + 4) = *engine_func_002bad80(&tmp_ts, 0u);

    u8* const mgr = *reinterpret_cast<u8* const*>(0x00432FC8u);
    u32* const state_ptr = reinterpret_cast<u32*>(ctx + 4);
    const u32 state = *state_ptr;

    if (state == 0u) {
        u32 err = 0xE7E3FFFFu;
        u32 flag = 0u;
        if (engine_func_0039444c(ctx + 0x18u, &err, &flag) != 0u) {
            if ((func_0023a24c(mgr + 0x80u) & 0x80000000u) == 0u) {
                *state_ptr = 1u;
                return;
            }
            u64 ts2 = 0u;
            engine_func_0038b470(&ts2, mgr);
            *reinterpret_cast<u64*>(ctx + 0x0Cu) = ts2;
            if ((engine_func_002a1578(ctx + 0x0Cu) & 0x80000000u) == 0u) {
                *state_ptr = 1u;
                return;
            }
            *reinterpret_cast<u32*>(out + 4u) = *reinterpret_cast<const u32*>(ctx + 0x0Cu);
            *reinterpret_cast<u32*>(out + 8u) = *reinterpret_cast<const u32*>(ctx + 0x10u);
            out[0] = 0x64u;
            return;
        }
        if ((err & 0x80000000u) != 0u) {
            u64 ts2 = 0u;
            *reinterpret_cast<u64*>(out + 4u) = *engine_func_002bad80(&ts2, err);
            if (flag == 0u) {
                out[0] = 0x66u;
            } else {
                func_002b49f4(mgr);
                out[0] = 0x67u;
            }
        }
        return;
    }

    if (state == 1u) {
        if (nn_sdk_func_0038b664(mgr) != 0u) {
            *state_ptr = 2u;
            return;
        }
        *state_ptr = 3u;
        out[0] = 0u;
        return;
    }

    if (state == 2u) {
        if (func_0038b600(mgr) != 0u) {
            *state_ptr = 3u;
            out[0] = 0u;
        }
    }
}

// DECOMP_FUNC(0x0028640c, 504)
extern "C" void func_002b22fc(void* out_mtx, float rx, float ry, float rz);
extern "C" void func_002b71f8(void* dst_mtx, const void* a, const void* b);

extern "C" void func_0028640c(void* mat, s32 deg_x, s32 deg_y, s32 deg_z) {
    auto wrap_angle = [](s32 deg) -> float {
        s32 rem = deg % 360;
        if (deg < 0) {
            rem += 360;
        }
        return static_cast<float>(360 - rem) * (256.0f / 360.0f);
    };

    u8 tmp_mtx[0x40];
    if (deg_y != 0) {
        func_002b22fc(tmp_mtx, 0.0f, wrap_angle(deg_y), 0.0f);
        func_002b71f8(mat, mat, tmp_mtx);
    }
    if (deg_x != 0) {
        func_002b22fc(tmp_mtx, wrap_angle(deg_x), 0.0f, 0.0f);
        func_002b71f8(mat, mat, tmp_mtx);
    }
    if (deg_z != 0) {
        func_002b22fc(tmp_mtx, 0.0f, 0.0f, wrap_angle(deg_z));
        func_002b71f8(mat, mat, tmp_mtx);
    }
}

// DECOMP_FUNC(0x0035f1b0, 504)
extern "C" void func_0035f4a0(u16* dst, u32 max_len, const char* src);
extern "C" u32 func_0035f454(u8* obj, const u16* key, u32 max_len);
extern "C" void func_0035edd4(
    u8* obj, u32* out_flags, const u16* line, u32 len, u16* const* slots, u32 num_keys);

extern "C" u32 func_0035f1b0(
    u8* obj, u32* out_flags, void* stream, const char* const* keys, u32 num_keys) {
    u16* slots[16];
    u8* const slot_base = *reinterpret_cast<u8* const*>(obj + 0x2Cu);
    for (u32 i = 0u; i < 16u; ++i) {
        slots[i] = reinterpret_cast<u16*>(slot_base + i * 0x80u);
    }

    for (u32 i = 0u; i < num_keys; ++i) {
        if (keys[i] == nullptr) {
            return 0xE0E0EBF6u;
        }
        func_0035f4a0(slots[i], 0x40u, keys[i]);
    }

    if (obj[0x1Au] == 0u) {
        const u32 bit = 1u << obj[0x1Bu];
        for (u32 i = 0u; i < num_keys; ++i) {
            if (func_0035f454(obj, slots[i], 0x40u) != 0u) {
                out_flags[i] |= bit;
            }
        }
    }

    using GetSizeFn = u32 (*)(void*);
    using ReadFn = u32 (*)(void*, void*, u32);
    const u32* const vtbl = *reinterpret_cast<const u32* const*>(stream);
    const u32 size = reinterpret_cast<GetSizeFn>(static_cast<std::uintptr_t>(vtbl[9]))(stream);
    if (size < 2u || static_cast<s32>(size) > 0x4000) {
        return 0xD820EBECu;
    }

    void* const read_buf = *reinterpret_cast<void* const*>(obj + 0x24u);
    const u32 read_bytes = reinterpret_cast<ReadFn>(static_cast<std::uintptr_t>(vtbl[11]))(
        stream, read_buf, size);
    if (read_bytes != size) {
        return 0xD820EBECu;
    }

    const u16* const buf = reinterpret_cast<const u16*>(read_buf);
    if (buf[0] != 0xFEFFu) {
        return 0xF820EBF0u;
    }

    u32 start = 1u;
    u32 idx = 1u;
    if (size > 2u) {
        while (idx * 2u < size) {
            const u16 ch = buf[idx];
            if (ch == 0x000Au) {
                idx += 1u;
                func_0035edd4(obj, out_flags, buf + start, idx - start - 1u, slots, num_keys);
                start = idx;
            } else if (ch == 0x0000u) {
                return 0xF820EBF0u;
            }
            idx += 1u;
        }
        if (idx - 1u == start) {
            return 0u;
        }
    }

    func_0035edd4(obj, out_flags, buf + start, idx - start, slots, num_keys);
    return 0u;
}

// DECOMP_FUNC(0x0024ecc0, 532)
extern "C" u32 func_0026f370(
    float* out_val, u32 total_steps, u32 curr_step, float start_val, float target_val);
extern "C" u32 func_0026f294(
    s32* out_val, s32 target_x, s32 target_y, s32 total_steps, s32 curr_step, s32 mode);

extern "C" u32 script_vm_func_0024ecc0(u8* obj, u32 show) {
    auto word_at = [obj](u32 off) -> u32& {
        return *reinterpret_cast<u32*>(obj + off);
    };
    auto step_alpha = [&](u32 steps, float start_v, float end_v) {
        for (u32 i = 0u; i < 2u; ++i) {
            u8* const slot = obj + i * 0x14u;
            u32* const step = reinterpret_cast<u32*>(slot + 0x20u);
            func_0026f370(reinterpret_cast<float*>(slot + 0x14u), steps, *step, start_v, end_v);
            *step += 1u;
        }
    };
    auto step_pos = [&](u32 i, s32 tx, s32 ty, s32 steps) {
        u8* const slot = obj + i * 0x14u;
        u32* const step = reinterpret_cast<u32*>(slot + 0x48u);
        if (func_0026f294(reinterpret_cast<s32*>(slot + 0x40u), tx, ty, steps, *step, 1) != 0) {
            slot[0x4Cu] = 1u;
        } else {
            *step += 1u;
        }
    };

    if (show == 0u) {
        for (u32 i = 0u; i < 3u; ++i) {
            step_pos(i, 0, -330, 4);
        }
        if (word_at(0x114u) != 2u) {
            step_alpha(4u, 1.0f, 0.0f);
        }
    } else {
        if (word_at(0x108u) != 4u) {
            step_alpha(0xCu, 0.0f, 1.0f);
        }
        if (word_at(0x108u) != 2u) {
            for (u32 i = 0u; i < 3u; ++i) {
                u8* const slot = obj + i * 0x14u;
                if (i == 0u || *reinterpret_cast<const s32*>(slot + 0x34u) > 2) {
                    step_pos(i, 330, 0, 12);
                }
                *reinterpret_cast<float*>(slot + 0x3Cu) = 1.0f;
            }
        }
    }

    u32 done = 0u;
    if (*reinterpret_cast<const s32*>(obj + 0x28u) >= 0x3F800000
        && word_at(0x108u) == 2u
        && show != 0u) {
        done = 1u;
    }
    if (obj[0x74u] == 1u) {
        done = 1u;
    }
    return done;
}

// DECOMP_FUNC(0x003b8e60, 536)
extern "C" u32 script_vm_func_0022b2e0(void* ptr);
extern "C" u32 script_vm_func_0019dfbc(u32 handle);
extern "C" void script_vm_func_0022b1f8(void* obj);
extern "C" u32 shop_func_002337a0(void* ptr);
extern "C" void script_vm_func_0027e9e4(u32 a, u32 b);
extern "C" void script_vm_func_0027ea24(u32 a, u32 b);
extern "C" u32 script_vm_func_00291018(u32 bf, const char* entry);
extern "C" void script_vm_func_002971e4(u32 proc, u32 idx);
extern "C" void script_vm_func_002b8b78(u32 id);
extern "C" void* script_vm_func_002c5e2c(const char* path);
extern "C" u8* scrScriptProcess_func_002972f8(u32 bf, u32 mbm);

extern "C" void script_vm_func_003b8e60(u8* obj) {
    auto word_at = [obj](u32 off) -> u32& {
        return *reinterpret_cast<u32*>(obj + off);
    };
    auto set_state = [&](u32 s) {
        word_at(0x28u) = s;
        word_at(0x2Cu) = 0u;
    };

    const u32 ready = script_vm_func_0022b2e0(obj + 0x9Cu);
    if (script_vm_func_0019dfbc(word_at(0xD74u)) != 2u || ready == 0u) {
        return;
    }

    script_vm_func_0022b1f8(obj);
    *reinterpret_cast<u16*>(obj + 0x4Cu) = static_cast<u16>(shop_func_002337a0(obj + 0x9Cu));

    u8* const mgr = *reinterpret_cast<u8* const*>(0x00432FC8u);
    if (mgr[0xC1u] != 0u) {
        mgr[0xC1u] = 0u;
        set_state(0xAu);
        return;
    }

    const u32 mode = word_at(0xDB0u);
    if (mode == 1u) {
        set_state(9u);
        const u32 idx = script_vm_func_00291018(word_at(0xD94u), "scr_sbq_sysbtl");
        script_vm_func_002971e4(word_at(0xD9Cu), idx);
        word_at(0xDB0u) = 0u;
    } else if (mode == 2u) {
        set_state(9u);
        script_vm_func_002b8b78(0x9Eu);
        const u32 idx = script_vm_func_00291018(word_at(0xD94u), "scr_sbq_sysbtl");
        script_vm_func_002971e4(word_at(0xD9Cu), idx);
        word_at(0xDB0u) = 0u;
    } else if (mode == 3u) {
        set_state(0xBu);
        const u32 bf = static_cast<u32>(reinterpret_cast<std::uintptr_t>(
            script_vm_func_002c5e2c("battle/Result.bf")));
        word_at(0xDA0u) = bf;
        const u32 mbm = static_cast<u32>(reinterpret_cast<std::uintptr_t>(
            script_vm_func_002c5e2c("battle/ResultMsg.mbm")));
        word_at(0xDA4u) = mbm;
        u8* const proc = scrScriptProcess_func_002972f8(word_at(0xDA0u), mbm);
        word_at(0xDA8u) = static_cast<u32>(reinterpret_cast<std::uintptr_t>(proc));
        *reinterpret_cast<u32*>(proc + 0x108u) = 3u;
        const u32 idx = script_vm_func_00291018(word_at(0xDA0u), "ProcCharonRequestFirst");
        script_vm_func_002971e4(word_at(0xDA8u), idx);
        word_at(0xDB0u) = 0u;
    } else {
        script_vm_func_0027e9e4(0u, 0u);
        const u8* const d5c = *reinterpret_cast<const u8* const*>(obj + 0xD5Cu);
        script_vm_func_0027ea24(word_at(0xD80u), d5c[0x3Fu]);
        set_state(5u);
        if (mode == 4u) {
            word_at(0xDB0u) = 0u;
        }
    }
}

// DECOMP_FUNC(0x00294848, 540)
extern "C" const u8* engine_func_002b47cc(u32 item_id);
extern "C" u32 engine_func_0023d04c(void* obj, u32 slot, u32 a, u32 b, u32 body_id);
extern "C" void ui_func_002be7fc(char* dst, const char* fmt, ...);
extern "C" void engine_func_0023f440(void* obj, u32 slot, const char* path, u32 arg3);
extern "C" const u16* script_vm_func_002b66ec();

extern "C" void engine_func_00294848(void* obj, u32 slot, u32 item_id, u32 arg3) {
    const u8* const item = engine_func_002b47cc(item_id);
    char path[0x40];

    auto load_slot = [&](u32 s, const u8* it, const char* fmt, u32 body_id) {
        const u16 a = *reinterpret_cast<const u16*>(it + 0x70u);
        const u16 b = *reinterpret_cast<const u16*>(it + 0x72u);
        const u32 var = engine_func_0023d04c(obj, s, a, b, body_id);
        ui_func_002be7fc(path, fmt, a, b, var);
        engine_func_0023f440(obj, s, path, arg3);
    };

    if (slot == 0u) {
        if (item[0x52u] != 4u) {
            return;
        }
        load_slot(0u, item, "player/pl%02d_%03dhd%d.bam", 0u);
        return;
    }

    if (slot == 1u) {
        if (item[0x52u] != 5u) {
            return;
        }
        const u16 a = *reinterpret_cast<const u16*>(item + 0x70u);
        const u16 b = *reinterpret_cast<const u16*>(item + 0x72u);
        ui_func_002be7fc(path, "player/pl%02d_%03dbd0.bam", a, b);
        engine_func_0023f440(obj, 1u, path, arg3);

        const u16* const defaults = script_vm_func_002b66ec();
        load_slot(0u, engine_func_002b47cc(defaults[3]), "player/pl%02d_%03dhd%d.bam", item_id);
        load_slot(2u, engine_func_002b47cc(defaults[5]), "player/pl%02d_%03dlg%d.bam", item_id);
        return;
    }

    if (slot == 2u) {
        if (item[0x52u] != 6u) {
            return;
        }
        load_slot(2u, item, "player/pl%02d_%03dlg%d.bam", 0u);
        return;
    }

    engine_func_0023f440(obj, slot, path, arg3);
}

// DECOMP_FUNC(0x002dfad4, 544)
extern "C" u32 engine_func_002c0bcc(u32 max_val);
extern "C" float script_vm_func_00282600(float rad);
extern "C" float script_vm_func_00287e4c(
    float x0, float y0, float z0, float x1, float y1, float z1);

extern "C" u32 engine_func_002dfad4(u8* out) {
    u8* const g_state = *reinterpret_cast<u8* const*>(0x00447600u) + 0x3000u;

    for (s32 attempt = 0; attempt < 4; ++attempt) {
        const u8* const g_tgt = *reinterpret_cast<const u8* const*>(0x00447E88u);
        const u8* const g_cam = *reinterpret_cast<const u8* const*>(0x004474F4u);
        const u16 flag = *reinterpret_cast<const u16*>(0x0049FB1Cu + 0x44u);

        float px = *reinterpret_cast<const float*>(g_tgt + 0x1Cu);
        const float py = *reinterpret_cast<const float*>(g_tgt + 0x20u);
        float pz = *reinterpret_cast<const float*>(g_tgt + 0x24u);
        float ang = *reinterpret_cast<const float*>(g_cam + 0x18u);
        const s32 cnt = *reinterpret_cast<const s32*>(g_state + 0x44u);

        float dist;
        if (flag != 0u) {
            if (cnt > 0) {
                const float step = static_cast<float>((cnt + 1) >> 1) * 25.0f;
                ang += (cnt & 1) ? -step : step;
            }
            const float base_dist = (cnt > 12) ? 500.0f : 900.0f;
            dist = static_cast<float>(engine_func_002c0bcc(0x32u)) + base_dist;
        } else {
            if (cnt > 0) {
                const float step = static_cast<float>((cnt + 1) >> 1) * 35.0f;
                ang += (cnt & 1) ? -step : step;
            }
            const float base_dist = (cnt > 12) ? 250.0f : 560.0f;
            dist = static_cast<float>(engine_func_002c0bcc(0x32u)) + base_dist;
        }

        const float rad = ang * 0.017453292f;
        px += reinterpret_cast<float (*)(float)>(script_vm_func_0028277c)(rad) * dist;
        pz += script_vm_func_00282600(rad) * dist;
        *reinterpret_cast<s32*>(g_state + 0x44u) = cnt + 1;

        const float cand_pos[3] = {px, py + 35.0f, pz};
        const u8* const g_tgt2 = *reinterpret_cast<const u8* const*>(0x00447E88u);
        const float tgt_pos[3] = {
            *reinterpret_cast<const float*>(g_tgt2 + 0x1Cu),
            *reinterpret_cast<const float*>(g_tgt2 + 0x20u) + 35.0f,
            *reinterpret_cast<const float*>(g_tgt2 + 0x24u),
        };

        if (engine_func_0025b6e8(tgt_pos, cand_pos, nullptr) == -1) {
            *reinterpret_cast<float*>(out + 0x20u) = px;
            *reinterpret_cast<float*>(out + 0x24u) = py;
            *reinterpret_cast<float*>(out + 0x28u) = pz;
            *reinterpret_cast<float*>(out + 0x2Cu) = script_vm_func_00287e4c(
                cand_pos[0], cand_pos[1], cand_pos[2],
                tgt_pos[0], tgt_pos[1], tgt_pos[2]);
            return 1u;
        }
    }

    return 0u;
}

// DECOMP_FUNC(0x0032acb8, 544)
extern "C" s32 camp_func_0029f0f4(void* cursor);

extern "C" void script_vm_func_0032acb8(u32 skip) {
    using namespace camp_191cf4_calls;

    u8* const camp = *reinterpret_cast<u8* const*>(0x0043DD50u);
    if (skip != 0u) {
        return;
    }

    const u8* const slot = static_cast<const u8*>(camp_func_002a0fac()) + 0x0Eu;
    void* const cursor = camp + 0x660u;
    void* const list = camp + 0x78Au;
    const u32 asc = ((*slot & 0x80u) == 0u) ? 1u : 0u;

    if ((*slot & 0x7Fu) == 0x22u) {
        func_002b7f0a(list, camp_func_0029f0f4(cursor), 2, (asc != 0u) ? 0x001E15ECu : 0x002D03C4u);
    }
    if ((*slot & 0x7Fu) == 0x21u) {
        func_002b7f0a(list, camp_func_0029f0f4(cursor), 2, (asc != 0u) ? 0x001F6204u : 0x002DCAF8u);
    }
    if ((*slot & 0x7Fu) == 0x18u) {
        func_002b7f0a(list, camp_func_0029f0f4(cursor), 2, (asc != 0u) ? 0x0021938Cu : 0x002F274Cu);
    }
    if ((*slot & 0x7Fu) == 0x19u) {
        func_002b7f0a(list, camp_func_0029f0f4(cursor), 2, (asc != 0u) ? 0x001B1720u : 0x002192C0u);
    }
    if ((*slot & 0x7Fu) == 0x1Au) {
        func_002b7f0a(list, camp_func_0029f0f4(cursor), 2, (asc != 0u) ? 0x001E1694u : 0x002D0400u);
    }
}

// DECOMP_FUNC(0x00111090, 556)
extern "C" void* engine_func_0011b850(void* ptr);
extern "C" void* engine_func_0011b838(void* ptr);
extern "C" void* engine_func_002bac24(void* ptr);
extern "C" void* engine_func_002bac28(void* ptr);
extern "C" void* engine_func_00121ec4(void* ptr);
extern "C" void engine_func_002c541c(void* ptr, u32 zero);
extern "C" void* engine_func_00121ed8(void* ptr);
extern "C" u64 script_vm_func_00126edc(void* ptr);
extern "C" void engine_func_002bab5c(void* dst, const char* src, u32 len);
extern "C" void aocThread_func_00121e08(void* ptr, u32 stack_sz);
extern "C" void engine_func_0012701c(void* ptr);
extern "C" void engine_func_002baacc(void* ptr);

extern "C" u8* engine_func_00111090(u8* obj) {
    auto word_at = [obj](u32 off) -> u32& {
        return *reinterpret_cast<u32*>(obj + off);
    };

    engine_func_0011b850(obj + 0x20u);
    engine_func_0011b838(obj + 0x28u);
    engine_func_002bac24(obj + 0x7Cu);
    engine_func_002bac28(obj + 0x80u);
    engine_func_002bac24(obj + 0x84u);
    engine_func_00121ec4(obj + 0x88u);

    word_at(0x98u) = 0u;
    word_at(0x9Cu) = 0u;
    engine_func_002c541c(obj + 0x98u, 0u);

    word_at(0xA0u) = 0u;
    word_at(0xA4u) = 0u;
    engine_func_002c541c(obj + 0xA0u, 0u);

    engine_func_00121ed8(obj + 0xA8u);

    word_at(0x364u) = 0u;
    word_at(0x5A8u) = 0u;
    word_at(0x5ACu) = 0u;
    word_at(0x5B0u) = 0u;
    word_at(0x5B4u) = 0u;
    word_at(0x678u) = 0u;
    word_at(0x684u) = 0u;
    word_at(0x688u) = 0u;
    word_at(0x754u) = 0u;

    obj[0x758u] = 1u;
    engine_func_002bb09c(obj + 0x75Cu);
    word_at(0x764u) = 0u;
    word_at(0x768u) = 0u;
    u64 ts = 0u;
    *reinterpret_cast<u64*>(obj + 0x75Cu) = *engine_func_002bad80(&ts, 0u);

    word_at(0x76Cu) = 0u;
    obj[0xD50u] = 1u;
    word_at(0xD60u) = 0u;
    word_at(0x754u) = 0u;

    const u64 v1 = script_vm_func_00126edc(obj + 0x80u);
    word_at(0x14u) = (static_cast<u32>(v1 >> 32) & 0xFFFF0000u) | 2u;
    word_at(0x10u) = 0x00000E5Cu;

    const u64 v2 = script_vm_func_00126edc(obj + 0x80u);
    word_at(0x18u) = 0x00000E5Cu;
    word_at(0x1Cu) = static_cast<u32>(v2) & 0xFFFF0000u;

    script_vm_func_00126edc(obj + 0x80u);
    engine_func_002c4b30(obj + 0x04u, 0xBu);
    engine_func_002bab5c(obj + 0x04u, "1738159478", 0xBu);

    for (u32 off = 0x694u; off <= 0x6D0u; off += 4u) {
        word_at(off) = 0u;
    }

    engine_func_002c4b30(obj + 0x6D4u, 0x80u);
    aocThread_func_00121e08(obj + 0x88u, 0x8000u);
    engine_func_0012701c(obj + 0x98u);
    engine_func_002baacc(obj + 0x76Cu);

    word_at(0xD64u) = engine_func_002c5978(
        "Aoc Error Handling CALC", 2u, 0u, 0u, 0x00121D7Cu, 0u,
        static_cast<u32>(reinterpret_cast<std::uintptr_t>(obj)));
    return obj;
}

// DECOMP_FUNC(0x002ac0c4, 560)
extern "C" __attribute__((naked)) void func_002ac0c4() {
    asm volatile(
        ".arm\n"
        ".hword 0x4010, 0xe92d, 0x4a10, 0xee10\n"
        ".hword 0x1000, 0xe3a0, 0x21d0, 0xe59f\n"
        ".hword 0x0499, 0xe3a0, 0x0084, 0xe080\n"
        ".hword 0x8b02, 0xed2d, 0x0002, 0xe150\n"
        ".hword 0x001b, 0x9a00, 0x0004, 0xe1e0\n"
        ".hword 0x0080, 0xe1a0, 0x0c20, 0xe1b0\n"
        ".hword 0x0012, 0x0a00, 0x0467, 0xe3a0\n"
        ".hword 0x0084, 0xe150, 0x8b02, 0x8cbd\n"
        ".hword 0x0a68, 0x8d9f, 0x8010, 0x88bd\n"
        ".hword 0x019c, 0xe59f, 0x0084, 0xe150\n"
        ".hword 0x1001, 0x23a0, 0x000e, 0x2a00\n"
        ".hword 0x0002, 0xe3a0, 0xe149, 0xfbff\n"
        ".hword 0x0102, 0xe314, 0x0a61, 0x0d9f\n"
        ".hword 0x8b02, 0x0cbd, 0x0a00, 0x0e20\n"
        ".hword 0x8010, 0x08bd, 0x8b02, 0xecbd\n"
        ".hword 0x4010, 0xe8bd, 0xe139, 0xeaff\n"
        ".hword 0x0502, 0xe374, 0x8b02, 0xecbd\n"
        ".hword 0x0a00, 0x1e30, 0x0a58, 0x0d9f\n"
        ".hword 0x8010, 0xe8bd, 0x0a57, 0xeddf\n"
        ".hword 0x0102, 0xe314, 0x1a56, 0x1d9f\n"
        ".hword 0x1a56, 0x0d9f, 0x0a20, 0xee60\n"
        ".hword 0x2a56, 0xed9f, 0x1a56, 0xeddf\n"
        ".hword 0x3164, 0xe59f, 0x0a20, 0xee71\n"
        ".hword 0x1a51, 0xed9f, 0x0ae0, 0xeefd\n"
        ".hword 0x0a90, 0xee10, 0x0a90, 0xee00\n"
        ".hword 0x2003, 0xe200, 0x0ae0, 0xeef8\n"
        ".hword 0x0ac1, 0xee00, 0x1a4d, 0xed9f\n"
        ".hword 0x0ac2, 0xee00, 0x0a4d, 0xeddf\n"
        ".hword 0x1a21, 0xee00, 0x1a4a, 0xeddf\n"
        ".hword 0x1a01, 0xee40, 0x0a21, 0xee40\n"
        ".hword 0x0a80, 0xee20, 0x3003, 0xe08f\n"
        ".hword 0x3102, 0xe083, 0x0a00, 0xedd3\n"
        ".hword 0x3118, 0xe59f, 0x3003, 0xe08f\n"
        ".hword 0x3102, 0xe083, 0x1a00, 0xed93\n"
        ".hword 0x310c, 0xe59f, 0x3003, 0xe08f\n"
        ".hword 0x0a00, 0xee41, 0x2102, 0xe083\n"
        ".hword 0x0000, 0xe351, 0x1a00, 0xedd2\n"
        ".hword 0x0140, 0xe1a0, 0x0aa1, 0xee70\n"
        ".hword 0x0022, 0x0a00, 0x2fa0, 0xe080\n"
        ".hword 0x35fe, 0xe3a0, 0x10c2, 0xe1a0\n"
        ".hword 0x00c2, 0xe040, 0x1b81, 0xe083\n"
        ".hword 0x1a10, 0xee00, 0x0b80, 0xe083\n"
        ".hword 0x0a20, 0xee60, 0x0a10, 0xee00\n"
        ".hword 0x8a20, 0xee20, 0x0a10, 0xee18\n"
        ".hword 0x0000, 0xe350, 0x0009, 0x0a00\n"
        ".hword 0x0a10, 0xee18, 0x1103, 0xe280\n"
        ".hword 0x15fe, 0xe251, 0x000a, 0x1a00\n"
        ".hword 0x0002, 0xe3a0, 0xe101, 0xfbff\n"
        ".hword 0x0a1a, 0xed9f, 0x8b02, 0xecbd\n"
        ".hword 0x0a00, 0xee20, 0x8010, 0xe8bd\n"
        ".hword 0x0002, 0xe3a0, 0xe0fb, 0xfbff\n"
        ".hword 0x8b02, 0xecbd, 0x4010, 0xe8bd\n"
        ".hword 0xe0f0, 0xeaff, 0x0a10, 0xee18\n"
        ".hword 0xe0e3, 0xebff, 0x0004, 0xe350\n"
        ".hword 0xe0ec, 0x0bff, 0x0a48, 0xeeb0\n"
        ".hword 0x8b02, 0xecbd, 0x8010, 0xe8bd\n"
        ".hword 0x0a10, 0xee00, 0x1a17, 0xeddf\n"
        ".hword 0x8b02, 0xecbd, 0x1ac0, 0xeeb8\n"
        ".hword 0x0a15, 0xed9f, 0x0a21, 0xee01\n"
        ".hword 0x0ac0, 0xeebc, 0x0a20, 0xee20\n"
        ".hword 0x8010, 0xe8bd, 0x0000, 0x1e50\n"
        ".hword 0x0000, 0x3f80, 0x0000, 0x85a0\n"
        ".hword 0x0000, 0x7000, 0x0000, 0x0000\n"
        ".hword 0xaa3b, 0x40b8, 0x0000, 0xbf00\n"
        ".hword 0x0000, 0x3f00, 0x7000, 0x3e31\n"
        ".hword 0xfdf4, 0x3705, 0xbb12, 0x3d2a\n"
        ".hword 0xbb12, 0x3e2a, 0xffff, 0x3eff\n"
        ".hword 0xffff, 0x3f7f, 0xb8cc, 0x0016\n"
        ".hword 0xb8cc, 0x0016, 0xb89c, 0x0016\n"
        ".hword 0x0000, 0x4b00, 0x0000, 0x4e7e\n"
    );
}

// DECOMP_FUNC(0x002f2c00, 572)
extern "C" __attribute__((naked)) void ui_func_002f2c00() {
    asm volatile(
        ".arm\n"
        ".hword 0x0000, 0xe3a0, 0x34ec, 0xebff\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0004, 0x1a00, 0x0014, 0xe3a0\n"
        ".hword 0x34e7, 0xebff, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x000e, 0x0a00\n"
        ".hword 0x000c, 0xe594, 0x0028, 0xe350\n"
        ".hword 0x0006, 0x0a00, 0x0027, 0xe350\n"
        ".hword 0x502a, 0x03a0, 0x001a, 0x0a00\n"
        ".hword 0x0026, 0xe350, 0x5000, 0x11a0\n"
        ".hword 0x0014, 0x0a00, 0x0014, 0xea00\n"
        ".hword 0x0010, 0xe594, 0x0000, 0xe350\n"
        ".hword 0x0001, 0xc3a0, 0x0008, 0xc584\n"
        ".hword 0x0021, 0xea00, 0x0001, 0xe3a0\n"
        ".hword 0x34d3, 0xebff, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x0004, 0x1a00\n"
        ".hword 0x0016, 0xe3a0, 0x34ce, 0xebff\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0001, 0x0a00, 0x0002, 0xe3a0\n"
        ".hword 0x0008, 0xe584, 0x000c, 0xe594\n"
        ".hword 0x0026, 0xe350, 0x0000, 0x1a00\n"
        ".hword 0xa00c, 0xe584, 0x0029, 0xe355\n"
        ".hword 0x0003, 0xda00, 0x0010, 0xe594\n"
        ".hword 0x0000, 0xe350, 0x0001, 0xc240\n"
        ".hword 0x000a, 0xca00, 0x0001, 0xe375\n"
        ".hword 0x0009, 0x0a00, 0x0026, 0xe355\n"
        ".hword 0x0007, 0x2a00, 0x0010, 0xe594\n"
        ".hword 0x1005, 0xe7d9, 0x1008, 0xe7c0\n"
        ".hword 0x01d0, 0xe1c4, 0x0001, 0xe150\n"
        ".hword 0x0001, 0xb280, 0x0000, 0xaa00\n"
        ".hword 0x0010, 0xe584, 0x1010, 0xe594\n"
        ".hword 0x0000, 0xe3a0, 0x0008, 0xe7c1\n"
        ".hword 0x3014, 0xe3a0, 0x2086, 0xe3a0\n"
        ".hword 0x1007, 0xe1a0, 0x0006, 0xe1a0\n"
        ".hword 0x3f38, 0xebfe, 0x301c, 0xe284\n"
        ".hword 0x2021, 0xe284, 0x1f43, 0xe28f\n"
        ".hword 0x000d, 0xe1a0, 0x2eb6, 0xfaff\n"
        ".hword 0x300d, 0xe1a0, 0x2000, 0xe3a0\n"
        ".hword 0x1004, 0xe287, 0x0004, 0xe286\n"
        ".hword 0x0000, 0xe1a0, 0x5018, 0xe287\n"
        ".hword 0x3044, 0xe3a0, 0x2086, 0xe3a0\n"
        ".hword 0x1005, 0xe1a0, 0x0006, 0xe1a0\n"
        ".hword 0x3f28, 0xebfe, 0x0018, 0xe594\n"
        ".hword 0x0000, 0xe350, 0x002f, 0x1a00\n"
        ".hword 0x7000, 0xe3a0, 0xb0cc, 0xe59f\n"
        ".hword 0x8007, 0xe1a0, 0x6004, 0xe286\n"
        ".hword 0x5004, 0xe285, 0xa007, 0xe1a0\n"
        ".hword 0x0001, 0xea00, 0x0026, 0xe357\n"
        ".hword 0x0009, 0x2a00, 0x000c, 0xe594\n"
        ".hword 0x30a8, 0xe59f, 0x1005, 0xe1a0\n"
        ".hword 0x0007, 0xe150, 0x0007, 0xe7d9\n"
        ".hword 0x2004, 0x03a0, 0x2000, 0x13a0\n"
        ".hword 0x0000, 0xe5cb, 0x0006, 0xe1a0\n"
        ".hword 0x0000, 0xe1a0, 0xa001, 0xe28a\n"
        ".hword 0x000d, 0xe35a, 0x600a, 0xe286\n"
        ".hword 0x7001, 0xe287, 0xffee, 0xbaff\n"
        ".hword 0x8001, 0xe288, 0x0003, 0xe358\n"
        ".hword 0x6082, 0xe246, 0x500c, 0xe285\n"
        ".hword 0xa000, 0xb3a0, 0xffe8, 0xbaff\n"
        ".hword 0x000c, 0xe594, 0x806e, 0xe286\n"
        ".hword 0x6001, 0xe287, 0x0007, 0xe150\n"
        ".hword 0x2004, 0x03a0, 0x2000, 0x13a0\n"
        ".hword 0x3044, 0xe28f, 0x1005, 0xe1a0\n"
        ".hword 0x0008, 0xe1a0, 0x0000, 0xe1a0\n"
        ".hword 0x000c, 0xe594, 0x100c, 0xe285\n"
        ".hword 0x3030, 0xe28f, 0x0006, 0xe150\n"
        ".hword 0x2004, 0x03a0, 0x2000, 0x13a0\n"
        ".hword 0x0008, 0xe1a0, 0x0000, 0xe1a0\n"
        ".hword 0xd014, 0xe28d, 0x8ff0, 0xe8bd\n"
        ".hword 0x24f0, 0x0047, 0xec4f, 0x4ec4\n"
        ".hword 0x7325, 0x7325, 0x0000, 0x0000\n"
        ".hword 0x24c9, 0x0047, 0x5342, 0x0000\n"
        ".hword 0x4b4f, 0x0000\n"
    );
}

// DECOMP_FUNC(0x002f5348, 572)
extern "C" u32 engine_func_0024ada8(void* obj, const void* path, u32 mode);
extern "C" u32 engine_func_0024acf0(void* obj, const void* path, u32 mode);
extern "C" u32 engine_func_002cbf38(void* obj, const void* path, u32 mode);
extern "C" u32 engine_func_001ff988(void* obj, const void* path, u32 mode);
extern "C" u32 engine_func_00210188(void* obj, u32 zero, u32 off, u32 sz);
extern "C" u32 engine_func_001ff88c(void* obj, u32 zero, u32 off, u32 sz);
extern "C" u32 engine_func_001ffa08(void* obj, u32 zero, u32 off, u32 sz);
extern "C" u32 engine_func_0024ac80(void* obj);
extern "C" u32 engine_func_0024ac48(void* obj);
extern "C" u32 engine_func_0024ac10(void* obj);
extern "C" u32 engine_func_0024acb8(void* obj);
extern "C" void engine_func_002bb9c8(void* obj, u32 zero);

extern "C" u32 engine_func_002f5348(u32 kind, const void* path, u32 offset, u32 size) {
    u32 obj[7] = {0u, 0u, 0u, 0u, 0u, 0u, 0u};
    const u32* const vtt = reinterpret_cast<const u32*>(0x00420768u);
    const u32 vtbl0 = vtt[0];
    obj[0] = vtbl0;
    const s32 vbase_off = *reinterpret_cast<const s32*>(
        static_cast<std::uintptr_t>(vtbl0 - 0x30u));
    *reinterpret_cast<u32*>(reinterpret_cast<u8*>(obj) + vbase_off) = vtt[8];
    obj[1] = vtt[9];

    constexpr u32 kErr = 0xE7E3FFFFu;
    u32 open_res = kErr;
    if (kind == 0u) {
        open_res = engine_func_0024ada8(obj, path, 2u);
    } else if (kind == 1u) {
        open_res = engine_func_0024acf0(obj, path, 2u);
    } else if (kind == 2u) {
        open_res = engine_func_002cbf38(obj, path, 2u);
    } else if (kind == 3u) {
        open_res = engine_func_001ff988(obj, path, 2u);
    }

    if ((open_res & 0x80000000u) != 0u) {
        engine_func_002bb9c8(obj, 0u);
        return 0u;
    }

    u32 act_res = kErr;
    if (kind == 0u) {
        act_res = engine_func_00210188(obj, 0u, offset, size);
    } else if (kind == 1u) {
        act_res = engine_func_001ff88c(obj, 0u, offset, size);
    } else if (kind == 3u) {
        act_res = engine_func_001ffa08(obj, 0u, offset, size);
    }

    auto close_stream = [&]() -> u32 {
        if (kind == 0u) return engine_func_0024ac80(obj);
        if (kind == 1u) return engine_func_0024ac48(obj);
        if (kind == 2u) return engine_func_0024ac10(obj);
        if (kind == 3u) return engine_func_0024acb8(obj);
        return kErr;
    };

    if ((act_res & 0x80000000u) != 0u) {
        close_stream();
        engine_func_002bb9c8(obj, 0u);
        return 0u;
    }

    const u32 close_res = close_stream();
    engine_func_002bb9c8(obj, 0u);
    return ((close_res & 0x80000000u) == 0u) ? 1u : 0u;
}

// DECOMP_FUNC(0x00340328, 580)
extern "C" void* ui_func_00293c98();
extern "C" u32 script_vm_func_00240420(void* fs, const char* path);
extern "C" void engine_func_002a0c54(const char* path, u32 zero);
extern "C" u32 engine_func_0029a2d0(const char* path, u32 arg3);
extern "C" void* Tbb_GetSubTable(const void* container, u32 table_index);
extern "C" const u8* Tbb_GetPayloadData(void* table);
extern "C" u32 Tbb_GetRowCount(void* table);

extern "C" void battle_func_00340328(u8* obj, u32 map_id, u32 sub_id, u32 arg3) {
    auto word_at = [obj](u32 off) -> u32& {
        return *reinterpret_cast<u32*>(obj + off);
    };

    word_at(0x08u) = map_id;
    word_at(0x0Cu) = sub_id;

    constexpr const char* kDir = "battle/battle_map/";
    char path[0x40];

    ui_func_002be7fc(path, "%se%03d_%02d.bcenv", kDir, map_id, sub_id);
    if (script_vm_func_00240420(ui_func_00293c98(), path) == 0u) {
        ui_func_002be7fc(path, "%se%03d_%02d.bcenv", kDir, 1u, 1u);
        word_at(0x08u) = 1u;
        word_at(0x0Cu) = 1u;
    }
    engine_func_002a0c54(path, 0u);

    ui_func_002be7fc(path, "%sb%03d_%02d.bam", kDir, map_id, sub_id);
    if (script_vm_func_00240420(ui_func_00293c98(), path) == 0u) {
        ui_func_002be7fc(path, "%sb%03d_%02d.bam", kDir, 1u, 1u);
        word_at(0x08u) = 1u;
        word_at(0x0Cu) = 1u;
    }
    word_at(0x10u) = engine_func_0029a2d0(path, arg3);

    void* const sub_tbl = Tbb_GetSubTable(*reinterpret_cast<const void* const*>(0x004341F8u), 0u);
    const u8* const rows = Tbb_GetPayloadData(sub_tbl);
    const u32 count = Tbb_GetRowCount(sub_tbl);
    if (count == 0u) {
        return;
    }

    const u32 target_map = word_at(0x08u);
    for (u32 i = 0u; i < count; ++i) {
        const u8* const row = rows + i * 0x4Cu;
        if (*reinterpret_cast<const u16*>(row + 0u) == target_map
            && *reinterpret_cast<const u16*>(row + 2u) == word_at(0x0Cu)) {
            if (row == nullptr) {
                return;
            }
            for (u32 k = 0u; k < 2u; ++k) {
                const u8* const sub_entry = row + k * 0x24u;
                if (sub_entry[4u] != '0') {
                    ui_func_002be7fc(
                        path, "%s%s.bam", kDir, reinterpret_cast<const char*>(sub_entry + 4u));
                    word_at(0x14u + k * 4u) = engine_func_0029a2d0(path, arg3);
                    float* const pos = reinterpret_cast<float*>(obj + 0x28u + k * 0x0Cu);
                    pos[0] = static_cast<float>(*reinterpret_cast<const u16*>(sub_entry + 0x22u));
                    pos[1] = static_cast<float>(*reinterpret_cast<const u16*>(sub_entry + 0x24u));
                    pos[2] = static_cast<float>(*reinterpret_cast<const u16*>(sub_entry + 0x26u));
                }
            }
            return;
        }
    }
}

// DECOMP_FUNC(0x0026bed8, 584)
extern "C" void camp_func_001d12b0();

extern "C" void camp_func_0026bed8() {
    using namespace camp_191cf4_calls;

    u8* const camp = *reinterpret_cast<u8* const*>(0x0043DCF0u);
    const u8* const cfg = static_cast<const u8*>(camp_func_002a0fac());
    const u8 b = cfg[0];
    const u32 asc = ((b & 0x80u) == 0u) ? 1u : 0u;
    const u32 key = b & 0x7Fu;
    void* const list = camp + 0x738u;

    if (key == 2u) {
        func_002b7f0a(list, 0x18, 8, (asc != 0u) ? 0x0029226Cu : 0x0025CD64u);
    }
    if (key == 1u) {
        func_002b7f0a(list, 0x18, 8, (asc != 0u) ? 0x001B17ECu : 0x0021948Cu);
    }
    if (key == 4u) {
        func_002b7f0a(list, 0x18, 8, (asc != 0u) ? 0x00292200u : 0x0025CCF8u);
    }
    if (key == 5u) {
        func_002b7f0a(list, 0x18, 8, (asc != 0u) ? 0x0019205Cu : 0x001E1628u);
    }
    if (key == 0x1Fu) {
        func_002b7f0a(list, 0x18, 8, (asc != 0u) ? 0x001A8158u : 0x0020718Cu);
    }
    if (key == 3u) {
        func_002b7f0a(list, 0x18, 8, (asc != 0u) ? 0x001A8098u : 0x002070CCu);
    }

    camp_func_001d12b0();
}

// DECOMP_FUNC(0x0026adcc, 592)
extern "C" s32 ui_func_0029d8fc(s32 key);
extern "C" s32 func_001c35a0();
extern "C" s32 engine_func_0029ebf8(void* cursor);
extern "C" s32 script_vm_func_001c3588();
extern "C" s32 ui_func_002c615c(s32 num, s32 den);
extern "C" void camp_func_0029eb58(void* cursor, s32 idx);
extern "C" s32 camp_func_0029f260(void* cursor);
extern "C" s32 camp_func_0029f248(void* cursor);
extern "C" s32 camp_func_0029ebdc(void* cursor);
extern "C" s32 engine_func_0029eba8(void* cursor);
extern "C" void camp_func_0029edfc(void* cursor, s32 idx);
extern "C" void script_vm_func_002b91c4(u32 se_id);

extern "C" u32 camp_func_0026adcc(
    void* cursor, u32 pos_packed, u32 size_packed, s32 hold_key,
    s32 up_key, s32 down_key, u32 is_grid, u32 play_se) {
    const s32 st_up = ui_func_0029d8fc(static_cast<s16>(up_key));
    const s32 st_dn = ui_func_0029d8fc(static_cast<s16>(down_key));
    const s32 st_hd = ui_func_0029d8fc(static_cast<s16>(hold_key));
    constexpr u32 kSeId = 0x0100016Cu;

    if (st_up == 6 || st_up == 2) {
        s32 target = camp_func_0029f260(cursor) + camp_func_0029f248(cursor) - 1;
        if (is_grid != 0u) {
            target = camp_func_0029ebdc(cursor) + engine_func_0029eba8(cursor) - 1;
        }
        if (target >= 0) {
            if (is_grid != 0u) {
                camp_func_0029eb58(cursor, target);
            } else {
                camp_func_0029edfc(cursor, target);
            }
            if (play_se != 0u) {
                script_vm_func_002b91c4(kSeId);
            }
        }
        return 1u;
    }

    if (st_dn == 6 || st_dn == 2) {
        s32 target = camp_func_0029f260(cursor) + camp_func_0029f248(cursor) + 1;
        if (is_grid != 0u) {
            target = camp_func_0029ebdc(cursor) + engine_func_0029eba8(cursor) + 1;
            if (engine_func_0029ebf8(cursor) > target) {
                camp_func_0029eb58(cursor, target);
                if (play_se != 0u) {
                    script_vm_func_002b91c4(kSeId);
                }
            }
        } else {
            if (camp_func_0029f0f4(cursor) > target) {
                camp_func_0029edfc(cursor, target);
                if (play_se != 0u) {
                    script_vm_func_002b91c4(kSeId);
                }
            }
        }
        return 1u;
    }

    if (st_hd == 0) {
        return 0u;
    }

    const s32 rows = camp_func_0029f0f4(cursor);
    const s32 ty = static_cast<s16>(func_001c35a0() - (static_cast<s32>(pos_packed) >> 16));
    if (is_grid != 0u) {
        const s32 cols = engine_func_0029ebf8(cursor);
        const s32 tx = static_cast<s16>(script_vm_func_001c3588() - static_cast<s16>(pos_packed));
        const s32 w = static_cast<s16>(size_packed);
        if (tx >= 0 && w > tx) {
            const s32 idx = static_cast<s16>(ui_func_002c615c(tx * cols, w));
            camp_func_0029eb58(cursor, idx);
        }
    } else {
        const s32 h = static_cast<s32>(size_packed) >> 16;
        if (ty >= 0 && h > ty) {
            const s32 idx = static_cast<s16>(ui_func_002c615c(ty * rows, h));
            const s32 cur = camp_func_0029f248(cursor) + camp_func_0029f260(cursor);
            if (cur != idx && play_se != 0u) {
                script_vm_func_002b91c4(kSeId);
            }
            camp_func_0029edfc(cursor, idx);
        }
    }
    return 1u;
}

extern "C" u8* Task_func_002861f8(u32 a0, u32 a1, u32 a2, u32 a3, u32 s0_bits, u32 size, u32 prio, u32 a7, u32 a8);
extern "C" void ui_func_002bcf58(void* dst, const void* src, u32 size);
extern "C" void battle_func_00193b64(void* task);

// DECOMP_FUNC(0x002d81d0, 596)
extern "C" void* ui_func_002d81d0(
    u32 arg0, const void* arg1, const u8* arg2, u32 arg3, const u8* cfg,
    u32 s17_bits, u32 s0_bits, u32 r8_u, u32 /*pad*/, u32 r7_u, u32 s18_bits) {
    const u32 cfg_w0 = *reinterpret_cast<const u32*>(cfg);
    const u8 b11 = cfg[0x11];
    const u32 prio = ((cfg_w0 & 2u) != 0u || b11 == 3u || b11 == 1u) ? 4u : 3u;

    u8* task = nullptr;
    if (b11 == 0u) {
        task = Task_func_002861f8(0x001929BCu, 0x001AAC60u, 0u, 0u, s0_bits, 0x3F0u, prio, 0u, 0u);
    } else if (b11 == 1u) {
        task = Task_func_002861f8(0x001929BCu, 0u, 0x001AA5A0u, 0u, s0_bits, 0x3F0u, prio, 0u, 0u);
    } else if (b11 == 3u) {
        task = Task_func_002861f8(0x001929BCu, 0u, 0u, 0x001AA5A0u, s0_bits, 0x3F0u, prio, 0u, 0u);
    }

    if (task == nullptr) {
        return nullptr;
    }

    engine_func_002c4b30(task, 0x3F0u);

    constexpr u32 kNegHalf = 0xBF000000u;
    constexpr u32 kPosHalf = 0x3F000000u;
    *reinterpret_cast<u32*>(task + 0x26C) = kNegHalf;
    *reinterpret_cast<u32*>(task + 0x270) = kNegHalf;
    *reinterpret_cast<u32*>(task + 0x274) = 0u;
    *reinterpret_cast<u32*>(task + 0x280) = 0x00FF00FFu;

    *reinterpret_cast<u32*>(task + 0x284) = kNegHalf;
    *reinterpret_cast<u32*>(task + 0x288) = kPosHalf;
    *reinterpret_cast<u32*>(task + 0x28C) = 0u;
    *reinterpret_cast<u32*>(task + 0x298) = 0xFF0000FFu;

    *reinterpret_cast<u32*>(task + 0x29C) = kPosHalf;
    *reinterpret_cast<u32*>(task + 0x2A0) = kNegHalf;
    *reinterpret_cast<u32*>(task + 0x2A4) = 0u;
    *reinterpret_cast<u32*>(task + 0x2B0) = 0x0000FFFFu;

    *reinterpret_cast<u32*>(task + 0x2B4) = kPosHalf;
    *reinterpret_cast<u32*>(task + 0x2B8) = kPosHalf;
    *reinterpret_cast<u32*>(task + 0x2BC) = 0u;
    *reinterpret_cast<u32*>(task + 0x2C8) = 0xFFFF00FFu;

    task[0x380] = static_cast<u8>(arg3);
    ui_func_002bcf58(task, arg1, 0x134u);
    *reinterpret_cast<const u8**>(task + 0x354) = cfg;
    *reinterpret_cast<u32*>(task + 0x2D4) = 0u;
    *reinterpret_cast<u32*>(task + 0x2D8) = 0u;
    *reinterpret_cast<u32*>(task + 0x2DC) = 0u;

    if (task[0x380] != 0u) {
        ui_func_002bcf58(task + 0x134, arg2, 0xB0u);
    } else {
        for (u32 i = 0; i < 4u; ++i) {
            task[0x1DA + i] = arg2[0xA6 + i];
        }
    }

    *reinterpret_cast<u32*>(task + 0x268) = s18_bits;
    *reinterpret_cast<u16*>(task + 0x2D0) = 0u;
    *reinterpret_cast<u32*>(task + 0x37C) = arg0;
    battle_func_00193b64(task);
    *reinterpret_cast<u32*>(task + 0x384) = s17_bits;
    task[0x3E9] = static_cast<u8>(r8_u);
    *reinterpret_cast<u16*>(task + 0x3EC) = static_cast<u16>(r7_u);
    *reinterpret_cast<u16*>(task + 0x3EA) = static_cast<u16>(r7_u);
    return task;
}

extern "C" void func_001078d8();
extern "C" void func_00108b10();
extern "C" u32 engine_func_002c00d4(void* guard);
extern "C" void* func_0011c374();
extern "C" void func_0011c544(void* obj, void* arg);
extern "C" void script_vm_func_002bd9ec(void* dst, const void* src);
extern "C" void func_0011c404(void* obj, const void* src);
extern "C" void func_0011c4c8(void* obj, void* a1, u32 a2, void* a3, s32 a4);

// DECOMP_FUNC(0x0010b578, 604)
extern "C" u32 engine_func_0010b578() {
    func_001078d8();
    func_00108b10();

    u32* const guard = reinterpret_cast<u32*>(0x004729F8u);
    u8* const obj = reinterpret_cast<u8*>(0x004EAA88u);
    if ((*guard & 1u) == 0u && engine_func_002c00d4(guard) != 0u) {
        func_0011c544(obj, func_0011c374());
    }

    u8* const sub = obj + 0x58;
    if (*reinterpret_cast<u32*>(sub + 8) != 0u) {
        *reinterpret_cast<u16*>(obj + 4) = *reinterpret_cast<u16*>(sub + 0);
        *reinterpret_cast<u16*>(obj + 6) = *reinterpret_cast<u16*>(sub + 2);
        *reinterpret_cast<u32*>(sub + 8) = 0u;
    }

    script_vm_func_002bd9ec(sub + 0x12, sub + 0x0C);
    for (u32 i = 0; i < 3u; ++i) {
        *reinterpret_cast<u32*>(obj + 0x7C + i * 4u) = *reinterpret_cast<u32*>(obj + 0x70 + i * 4u);
    }
    func_0011c404(obj, sub + 0x0C);

    if (sub[5] == 1u) {
        const float vx = static_cast<float>(*reinterpret_cast<s16*>(sub + 0x0C));
        const float vy = static_cast<float>(*reinterpret_cast<s16*>(sub + 0x0E));
        const float vz = static_cast<float>(*reinterpret_cast<s16*>(sub + 0x10));
        const float len_sq = vx * vx + vy * vy + vz * vz;
        float len;
        asm("vsqrt.f32 %0, %1" : "=t"(len) : "t"(len_sq));
        const float inv_len = 1.0f / len;
        const float nx = vx * inv_len;
        const float ny = vy * inv_len;
        const float nz = vz * inv_len;

        const float* const r0 = reinterpret_cast<const float*>(sub + 0x30);
        const float* const r1 = reinterpret_cast<const float*>(sub + 0x40);
        const float* const r2 = reinterpret_cast<const float*>(sub + 0x50);
        const float ox = (r0[0] * nx + r0[1] * ny + r0[2] * nz) * len;
        const float oy = (r1[0] * nx + r1[1] * ny + r1[2] * nz) * len;
        const float oz = (r2[0] * nx + r2[1] * ny + r2[2] * nz) * len;

        auto clamp_s16 = [](s16 v) -> s16 {
            if (v <= -930) {
                return -930;
            }
            if (v > 930) {
                return 930;
            }
            return v;
        };
        *reinterpret_cast<s16*>(sub + 0x0C) = clamp_s16(static_cast<s16>(static_cast<s32>(ox)));
        *reinterpret_cast<s16*>(sub + 0x0E) = clamp_s16(static_cast<s16>(static_cast<s32>(oy)));
        *reinterpret_cast<s16*>(sub + 0x10) = clamp_s16(static_cast<s16>(static_cast<s32>(oz)));
    }

    func_0011c4c8(obj, sub + 0x18, 1u, sub + 0x0C, -1);
    return 1u;
}

extern "C" const u8* ui_func_00282b94(void* p, u32 a0);

// DECOMP_FUNC(0x003c1710, 612)
extern "C" void ui_func_003c1710(u32 arg0, u8* obj) {
    const u8* const g = reinterpret_cast<const u8*>(0x00439CE0u);
    const s32 fade_frames = *reinterpret_cast<const s32*>(g + 0x0C);
    if ((*reinterpret_cast<const u32*>(obj + 0x50) & 2u) == 0u) {
        return;
    }

    const u8* const unit = ui_func_00282b94(
        reinterpret_cast<void*>(arg0),
        static_cast<u32>(*reinterpret_cast<const s16*>(obj + 0x62)));
    if (unit == nullptr) {
        return;
    }

    if ((*reinterpret_cast<const u32*>(unit) & 0x80000u) == 0u ||
        *reinterpret_cast<const u32*>(obj + 0x64) == 0xFFFFu) {
        *reinterpret_cast<u32*>(obj + 0x6C) = 0xFFFFFFFFu;
        return;
    }

    u32 slot = *reinterpret_cast<u32*>(obj + 0x94);
    const u16 mask = *reinterpret_cast<const u16*>(unit + 0x1C6);
    if (slot == 0u) {
        for (u32 i = 0u; i < 11u; ++i) {
            if ((mask & (1u << i)) != 0u) {
                *reinterpret_cast<u32*>(obj + 0x94) = i;
                slot = i;
                break;
            }
        }
    }

    u32 target_color = *reinterpret_cast<const u32*>(g + 0x18);
    if (slot == 7u) {
        target_color = 0x52DEE7FFu;
    } else if (slot == 5u) {
        target_color = 0xB252CEFFu;
    } else if (slot == 6u) {
        target_color = 0xF721F9FFu;
    } else if (slot == 8u) {
        target_color = 0xEFD629FFu;
    } else if (slot == 9u) {
        target_color = 0x7E620CFFu;
    } else if (slot == 3u) {
        target_color = 0xFF4000FFu;
    }

    if (*reinterpret_cast<u32*>(obj + 0x90) != target_color) {
        *reinterpret_cast<u32*>(obj + 0x8C) = *reinterpret_cast<u32*>(obj + 0x6C);
        *reinterpret_cast<u32*>(obj + 0x90) = target_color;
        *reinterpret_cast<u32*>(obj + 0x80) = 0u;
    }

    const s32 timer = *reinterpret_cast<s32*>(obj + 0x80);
    if (timer < fade_frames) {
        const s32 next = timer + 1;
        *reinterpret_cast<s32*>(obj + 0x80) = next;
        const float t = static_cast<float>(next) / static_cast<float>(fade_frames);
        const u32 start_color = *reinterpret_cast<u32*>(obj + 0x8C);

        const s32 s3 = static_cast<s32>((start_color >> 24) & 0xFFu);
        const s32 s2 = static_cast<s32>((start_color >> 16) & 0xFFu);
        const s32 s1 = static_cast<s32>((start_color >> 8) & 0xFFu);
        const s32 s0 = static_cast<s32>(start_color & 0xFFu);

        const s32 d3 = static_cast<s32>((target_color >> 24) & 0xFFu) - s3;
        const s32 d2 = static_cast<s32>((target_color >> 16) & 0xFFu) - s2;
        const s32 d1 = static_cast<s32>((target_color >> 8) & 0xFFu) - s1;
        const s32 d0 = static_cast<s32>(target_color & 0xFFu) - s0;

        const u32 o3 = static_cast<u32>(s3 + static_cast<s32>(static_cast<float>(d3) * t));
        const u32 o2 = static_cast<u32>(s2 + static_cast<s32>(static_cast<float>(d2) * t));
        const u32 o1 = static_cast<u32>(s1 + static_cast<s32>(static_cast<float>(d1) * t));
        const u32 o0 = static_cast<u32>(s0 + static_cast<s32>(static_cast<float>(d0) * t)) & 0xFFu;

        *reinterpret_cast<u32*>(obj + 0x6C) = (o3 << 24) + (o2 << 16) + (o1 << 8) + o0;
        return;
    }

    *reinterpret_cast<u32*>(obj + 0x6C) = target_color;
    const s32 next = timer + 1;
    *reinterpret_cast<s32*>(obj + 0x80) = next;

    const float limit = (static_cast<float>(fade_frames) + 20.0f) + 4.0f;
    if (limit < static_cast<float>(next)) {
        u32 cand = slot + 1u;
        do {
            if ((mask & (1u << cand)) != 0u) {
                *reinterpret_cast<u32*>(obj + 0x94) = cand;
                break;
            }
            ++cand;
            if (cand > 10u) {
                cand = 0u;
            }
        } while (cand != slot);
    }
}

extern "C" u32 shop_func_00240e8c(void* p);
extern "C" const u8* camp_func_002bf6c8(void* obj, u32 id);
extern "C" void func_00230e54(void* obj, u32 id);
extern "C" void camp_func_00231d60(void* obj, u32 id, s32 x, s32 y, u32 layer, u32 flag);
extern "C" u32 battle_func_002c5fa4(u32 a0, u32 a1, u32 a2);
extern "C" void func_00230c80(void* obj, u32 a1, s32 x, s32 y, u32 a4, u32 a5, u32 color, u32 layer, const char* text);

// DECOMP_FUNC(0x003a11a4, 616)
extern "C" void shop_func_003a11a4(u8* self) {
    const u32 layer = *reinterpret_cast<const u32*>(self + 0x37C) + 6u;
    const u32 mode = *reinterpret_cast<const u32*>(self + 0x860);
    const u32 offset = (mode == 7u || mode == 8u) ? 1u : 2u;
    const u32 idx = shop_func_00240e8c(self + 0x880 + mode * 0x74u);

    const u8* const p0 = camp_func_002bf6c8(self + 0x394, idx + offset + 0x4Fu);
    s32 x = *reinterpret_cast<const s16*>(p0 + 8);
    s32 y = *reinterpret_cast<const s16*>(p0 + 0xA);
    const u8* const p1 = camp_func_002bf6c8(self + 0x394, 0xC8u);
    x += *reinterpret_cast<const s16*>(p1 + 8);
    y += *reinterpret_cast<const s16*>(p1 + 0xA);

    func_00230e54(self + 0x394, (mode == 8u) ? 9u : 8u);
    camp_func_00231d60(self + 0x394, 0xC2u, x, y, layer, 1u);
    camp_func_00231d60(self + 0x394, 0xC3u, x, y, layer, 1u);

    typedef void (*ApplyBlendFn)(u32);
    u8* const stack_base = *reinterpret_cast<u8**>(0x0044EA00u);
    u8* const stack = stack_base + 0x12AC;
    const u32 blend_val = battle_func_002c5fa4(6u, 1u, 0u);
    const u32 depth = *reinterpret_cast<u32*>(stack);
    const u32 prev_val = *reinterpret_cast<u32*>(stack + 8 + depth * 4u);
    const u32 next_depth = depth + 1u;
    *reinterpret_cast<u32*>(stack) = next_depth;
    *reinterpret_cast<u32*>(stack + 8 + next_depth * 4u) = blend_val;
    if (stack[0x18] != 0u || prev_val != blend_val) {
        reinterpret_cast<ApplyBlendFn>(*reinterpret_cast<const u32*>(stack + 0x1C))(blend_val);
        stack[0x18] = 0u;
    }

    if (self[0x878] != 0u) {
        camp_func_00231d60(self + 0x394, 0xC4u, x, y, layer + 1u, 1u);
    }
    if (self[0x879] != 0u) {
        camp_func_00231d60(self + 0x394, 0xC5u, x, y, layer + 1u, 1u);
    }

    u8* const stack2 = *reinterpret_cast<u8**>(0x0044EA00u) + 0x12AC;
    const u32 depth2 = *reinterpret_cast<u32*>(stack2);
    const u32 popped_val = *reinterpret_cast<u32*>(stack2 + 8 + depth2 * 4u);
    const u32 prev_depth = depth2 - 1u;
    *reinterpret_cast<u32*>(stack2) = prev_depth;
    const u32 restore_val = *reinterpret_cast<u32*>(stack2 + 8 + prev_depth * 4u);
    if (stack2[0x18] != 0u || popped_val != restore_val) {
        reinterpret_cast<ApplyBlendFn>(*reinterpret_cast<const u32*>(stack2 + 0x1C))(restore_val);
        stack2[0x18] = 0u;
    }

    const u32 count = *reinterpret_cast<const u32*>(self + 0x868);
    const u8* const p2 = camp_func_002bf6c8(self + 0x394, 0xC7u);
    const u32 color = (count == *reinterpret_cast<const u32*>(self + 0x86C)) ? 0xF49800FFu : 0xFFFFFFFFu;
    const s32 tx = x + *reinterpret_cast<const s16*>(p2 + 8);
    const s32 ty = y + *reinterpret_cast<const s16*>(p2 + 0xA);

    char buf[36];
    ui_func_002be7fc(buf, "%2d", count);
    func_00230c80(self + 0x394, 0u, tx, ty, 0u, 7u, color, layer, buf);
}

extern "C" u32 ui_func_002a63f8(u32 a0, u32 a1);
extern "C" void script_vm_func_003ba974(void* self);
extern "C" u32 script_vm_func_002c0ba8(u32 id);
extern "C" void engine_func_002350f4(u8* self, const char* name1, const char* name2);
extern "C" const u8* engine_func_0022ba54(void* p);
extern "C" void engine_func_0022b158(void* p, u32 a1, s32 a2);
extern "C" void engine_func_00234e70(void* p, s32 a1, u32 a2);
extern "C" const u8* engine_func_003bbd00(void* local_out);
extern "C" s32 engine_func_0022b144(void* local_in, s32 idx);
extern "C" u32 engine_func_002c32f0(const char* path, void* meta_out, u32 flag);
extern "C" void engine_func_002a06a0(void* p, u32 a1, u32 a2);
extern "C" void engine_func_0022b3d8(void* p, u32 a1);
extern "C" void engine_func_0023509c(void* p, u32 a1);
extern "C" void PlaceWin_ShowMessage(const void* msg);

// DECOMP_FUNC(0x003b97c4, 616)
extern "C" void engine_func_003b97c4(u8* self) {
    if (ui_func_002a63f8(0x21u, *reinterpret_cast<const u32*>(self + 0x90)) == 0u ||
        *reinterpret_cast<const u32*>(self + 0xD6C) == 0u ||
        *reinterpret_cast<const u32*>(self + 0xD70) == 0u) {
        return;
    }

    script_vm_func_003ba974(self);
    *reinterpret_cast<u32*>(self + 0x28) = 3u;
    *reinterpret_cast<u32*>(self + 0x2C) = 0u;

    auto call_2350f4 = reinterpret_cast<void (*)(void*, const char*, const char*)>(engine_func_002350f4);
    const u8* const info = *reinterpret_cast<const u8* const*>(self + 0xD5C);
    if (info[0x40] != 0x30u) {
        self[0xE58] = 1u;
        char path[0x80];
        char path2[0x80];
        ui_func_002be7fc(path, "mikado/%s", info + 0x40);

        u8* const e5c = *reinterpret_cast<u8**>(self + 0xE5C);
        const u16 h64 = *reinterpret_cast<const u16*>(info + 0x64);
        const u16 h66 = *reinterpret_cast<const u16*>((*reinterpret_cast<const u8* const*>(self + 0xD5C)) + 0x66);
        const bool use_alt = (h64 != 0u && script_vm_func_002c0ba8(h64) != 0u) ||
                             (h66 != 0u && script_vm_func_002c0ba8(h66) != 0u);
        if (use_alt) {
            ui_func_002be7fc(path2, "mikado/%s", (*reinterpret_cast<const u8* const*>(self + 0xD5C)) + 0x68);
            call_2350f4(e5c, path, path2);
        } else {
            call_2350f4(e5c, path, nullptr);
        }

        const u8* const sb = engine_func_0022ba54(self + 0x9C);
        engine_func_0022b158(*reinterpret_cast<void**>(self + 0xE5C), 0u, -1);
        engine_func_00234e70(*reinterpret_cast<void**>(self + 0xE5C), *reinterpret_cast<const s16*>(sb + 0x28), 1u);

        if (*reinterpret_cast<const s32*>((*reinterpret_cast<const u8* const*>(self + 0xD5C)) + 0x60) >= 0) {
            u32 local = 0u;
            const u8* anim_list = engine_func_003bbd00(&local);
            if (anim_list != nullptr) {
                for (s32 i = 0;
                     i < engine_func_0022b144(&local, *reinterpret_cast<const s32*>((*reinterpret_cast<const u8* const*>(self + 0xD5C)) + 0x60));
                     ++i) {
                    ui_func_002be7fc(path, "mikado/%s.bam", anim_list + i * 0x20);
                    *reinterpret_cast<u32*>(self + 0xE60 + i * 4) =
                        engine_func_002c32f0(path, self + 0xE88 + i * 4, 1u);
                }
                const s32 idx = *reinterpret_cast<const s8*>(sb + 0x2B);
                engine_func_002a06a0(
                    *reinterpret_cast<void**>(self + 0xE5C),
                    *reinterpret_cast<const u32*>(self + 0xE60 + idx * 4),
                    *reinterpret_cast<const u32*>(self + 0xE88 + idx * 4));
            }
        }

        const s16 s3c = *reinterpret_cast<const s16*>(self + 0x3C);
        const s16 sb28 = *reinterpret_cast<const s16*>(sb + 0x28);
        if ((s3c == 4 || s3c == 3) && (sb28 == 0 || sb28 == 6)) {
            engine_func_0022b3d8(*reinterpret_cast<void**>(self + 0xE5C), 1u);
            engine_func_0023509c(*reinterpret_cast<void**>(self + 0xE5C), 0u);
        } else {
            engine_func_0022b3d8(*reinterpret_cast<void**>(self + 0xE5C), 0u);
            engine_func_0023509c(*reinterpret_cast<void**>(self + 0xE5C), 1u);
        }
    }

    if (*reinterpret_cast<const u32*>(self + 0xDB0) != 1u) {
        PlaceWin_ShowMessage((*reinterpret_cast<const u8* const*>(self + 0xD5C)) + 2);
    }
}

extern "C" f32 func_0024bd60(s32 a0, s32 a1, const void* elem, f32 x, f32 y, f32 z, f32 eps);

// DECOMP_FUNC(0x002fca68, 620)
extern "C" s32 ui_func_002fca68(const float* p0, const float* p1, float* out) {
    s32 hit_idx = -1;
    const u8* const g = reinterpret_cast<const u8*>(0x00446FE8u);
    float cur_x = p0[0];
    float cur_y = p0[1];
    float cur_z = p0[2];
    float end_x = p1[0];
    float end_y = p1[1];
    float end_z = p1[2];

    auto vfp_fabsf = [](float x) -> float {
        float res;
        asm("vabs.f32 %0, %1" : "=t"(res) : "t"(x));
        return res;
    };

    for (s32 pass = 1; pass < 3; ++pass) {
        const u8* planes = nullptr;
        s32 count = 0;
        float eps = 5.0f;
        if (pass == 1) {
            planes = *reinterpret_cast<const u8* const*>(g + 0x20);
            count = *reinterpret_cast<const s32*>(g + 0x0C);
            eps = 8.0f;
            if (hit_idx == -1) {
                const float x0 = p0[0];
                const float y0 = p0[1];
                const float z0 = p0[2];
                end_x = p1[0];
                end_y = p1[1];
                end_z = p1[2];
                const float dx = x0 - end_x;
                const float dy = y0 - end_y;
                const float dz = z0 - end_z;
                const float len_sq = dx * dx + dy * dy + dz * dz;
                float len;
                asm("vsqrt.f32 %0, %1" : "=t"(len) : "t"(len_sq));
                const float inv_len = 1.0f / len;
                cur_x = x0 + (dx * inv_len) * 8.0f;
                cur_y = y0 + (dy * inv_len) * 8.0f;
                cur_z = z0 + (dz * inv_len) * 8.0f;
            }
        } else {
            planes = *reinterpret_cast<const u8* const*>(g + 0x24);
            count = *reinterpret_cast<const s32*>(g + 0x10);
        }

        for (s32 i = 0; i < count; ++i, planes += 0xA8) {
            if (planes[8] == 0u || (*reinterpret_cast<const u32*>(planes) & 1u) == 0u) {
                continue;
            }
            const float nx = *reinterpret_cast<const float*>(planes + 0x0C);
            const float ny = *reinterpret_cast<const float*>(planes + 0x10);
            const float nz = *reinterpret_cast<const float*>(planes + 0x14);
            const float pd = *reinterpret_cast<const float*>(planes + 0x18);

            const float d0 = (cur_x * nx + cur_y * ny + cur_z * nz) - pd;
            const float d1 = (end_x * nx + end_y * ny + end_z * nz) - pd;
            if (!((d0 < 0.0f && d1 >= 0.0f) || (d0 >= 0.0f && d1 < 0.0f))) {
                continue;
            }

            const float a0 = vfp_fabsf(d0);
            const float a1 = vfp_fabsf(d1);
            const float sum = a0 + a1;
            const float t = a0 / sum;
            const float vx = end_x - cur_x;
            const float vy = end_y - cur_y;
            const float vz = end_z - cur_z;
            const float dist = func_0024bd60(
                *reinterpret_cast<const s8*>(planes + 4),
                *reinterpret_cast<const s8*>(planes + 5),
                planes,
                cur_x + vx * t,
                cur_y + vy * t,
                cur_z + vz * t,
                eps);
            if (dist >= 0.0f) {
                hit_idx = i;
                const float t2 = (a0 + dist) / sum;
                cur_x = cur_x + vx * t2;
                cur_y = cur_y + vy * t2;
                cur_z = cur_z + vz * t2;
            }
        }
    }

    if (hit_idx == -1) {
        out[0] = p0[0];
        out[1] = p0[1];
        out[2] = p0[2];
    } else {
        out[0] = cur_x;
        out[1] = cur_y;
        out[2] = cur_z;
    }
    return hit_idx;
}

extern "C" u32 script_vm_func_00297674();
extern "C" void shop_func_00297178(void* self, u32 state);
extern "C" u32 script_vm_func_002a0f88();
extern "C" void func_00232974(void* self, void* buf);
extern "C" void script_vm_func_00295904(u32 id, const void* buf);
extern "C" void battle_func_002af854(void* p, u32 a1, u32 a2);
extern "C" void camp_func_0026a96c();
extern "C" const u32* camp_func_00220eb4(const void* buf, const void* rhs, u32 flag);
extern "C" s32 camp_func_00309f94(const void* buf, const void* rhs);

// DECOMP_FUNC(0x00397d5c, 624)
extern "C" void script_vm_func_00397d5c(u8* self) {
    u8 buf[0x14];
    if (self[0x658] == 0u) {
        if (script_vm_func_002a0f88() == 0u) {
            return;
        }
        func_00232974(self, buf);
        script_vm_func_00295904(0x32u, buf);
        script_vm_func_002971e4(*reinterpret_cast<const u32*>(self + 0x654), 1u);
        self[0x658] = 1u;
        script_vm_func_002b8b78(0x9Au);
        return;
    }

    if (script_vm_func_0019dfbc(*reinterpret_cast<const u32*>(self + 0x654)) != 2u) {
        return;
    }

    if (script_vm_func_00297674() != 0u) {
        shop_func_00297178(self, 2u);
        if (self[0x29] != 0u) {
            script_vm_func_002b8b78(0x97u);
            return;
        }
        const s8 b20 = *reinterpret_cast<const s8*>(self + 0x20);
        if (b20 == 2 || b20 == 6) {
            script_vm_func_002b8b78(0x96u);
        } else {
            script_vm_func_002b8b78(0x95u);
        }
        return;
    }

    battle_func_002af854(self + 0x794, 0u, 1u);
    const s8 b649 = *reinterpret_cast<const s8*>(self + 0x649);
    if (b649 != 0 && b649 != 1) {
        camp_func_0026a96c();
        shop_func_00297178(self, 7u);
        return;
    }

    func_00232974(self, buf);
    const s16* const t1_keys = reinterpret_cast<const s16*>(0x00405160u);
    const u16* const t1_vals = reinterpret_cast<const u16*>(0x00405368u);
    const s16* const t2_keys = reinterpret_cast<const s16*>(0x00405570u);
    const u16* const t2_vals = reinterpret_cast<const u16*>(0x00405618u);

    for (s32 i = 0; i <= 8; ++i) {
        const u8 b0 = self[0xB0 + i * 2];
        const s8 b1 = *reinterpret_cast<const s8*>(self + 0xB1 + i * 2);
        const s16 key = static_cast<s16>((static_cast<u16>(b0) << 8) | static_cast<u8>(b1));

        bool found = false;
        for (s32 j = 0; j < 0x104; ++j) {
            if (t1_keys[j] == key) {
                const u16 val = t1_vals[j];
                buf[i * 2] = static_cast<u8>(val >> 8);
                buf[i * 2 + 1] = static_cast<u8>(val);
                found = true;
                break;
            }
        }
        if (!found) {
            for (s32 j = 0; j < 0x54; ++j) {
                if (t2_keys[j] == key) {
                    const u16 val = t2_vals[j];
                    buf[i * 2] = static_cast<u8>(val >> 8);
                    buf[i * 2 + 1] = static_cast<u8>(val);
                    break;
                }
            }
        }
    }

    const u32* const res_ptr = camp_func_00220eb4(buf, self + 0x94E, 1u);
    const s32 len = camp_func_00309f94(buf, self + 0x94E);
    if (*res_ptr == 0u && len < 6) {
        camp_func_0026a96c();
        shop_func_00297178(self, 7u);
    } else {
        shop_func_00297178(self, 6u);
        script_vm_func_002971e4(*reinterpret_cast<const u32*>(self + 0x654), 4u);
    }
}

extern "C" u32 engine_func_0017f928(s32 b1, s32 b0);
extern "C" u32 engine_func_002c3290(const char* s);

// DECOMP_FUNC(0x001eb498, 628)
extern "C" s32 engine_func_001eb498(const s8* src, u16* dst, s32 count_only) {
    struct TagEntry {
        u16 code;
        u16 pad0;
        s32 has_arg;
        u32 pad1;
        const char* prefix;
    };

    const TagEntry* const table = reinterpret_cast<const TagEntry*>(0x00464DA8u);
    s32 src_off = 0;
    s32 out_idx = 0;

    for (;;) {
        const s8* const cur = src + src_off;
        const u32 ch = engine_func_0017f928(cur[1], cur[0]);
        if (ch == 0xFFFFu) {
            if (count_only == 0) {
                dst[out_idx] = 0xFFFFu;
            }
            return out_idx + 1;
        }

        bool handled_tag = false;
        for (s32 t = 0; table[t].code != 0xF890u; ++t) {
            const TagEntry& entry = table[t];
            if (entry.prefix == nullptr) {
                continue;
            }
            const u32 plen = engine_func_002c3290(entry.prefix);
            if (engine_func_002b45f8(entry.prefix, reinterpret_cast<const char*>(cur), plen) != 0) {
                continue;
            }

            u32 pos = engine_func_002c3290(entry.prefix);
            s32 has_extra = 0;
            u16 extra_val = 0;
            if (entry.has_arg != 0) {
                u32 acc = 0u;
                while (static_cast<u8>(cur[pos]) != 0u) {
                    const s8 c = cur[pos];
                    if (c == '>') {
                        ++pos;
                        break;
                    }
                    acc <<= 4;
                    if (c >= '0' && c <= '9') {
                        acc += static_cast<u32>(c - '0');
                    } else if (c >= 'A' && c <= 'F') {
                        acc += static_cast<u32>(c - 'A' + 10);
                    } else if (c >= 'a' && c <= 'f') {
                        acc += static_cast<u32>(c - 'a' + 10);
                    }
                    ++pos;
                }
                if (acc == 0xFFu) {
                    acc = 0u;
                }
                has_extra = 1;
                extra_val = static_cast<u16>(acc + 1u);
            }

            if (entry.code == 0xFFFFu) {
                break;
            }

            if (count_only == 0) {
                dst[out_idx] = static_cast<u16>((entry.code >> 8) | ((entry.code & 0xFFu) << 8));
            }
            ++out_idx;
            src_off += static_cast<s32>(pos);
            if (has_extra != 0) {
                if (count_only == 0) {
                    dst[out_idx] = extra_val;
                }
                ++out_idx;
            }
            handled_tag = true;
            break;
        }
        if (handled_tag) {
            continue;
        }

        if (count_only == 0) {
            dst[out_idx] = static_cast<u16>(ch);
        }
        ++out_idx;
        src_off += 2;

        const u16 rev_ch = static_cast<u16>(((ch >> 8) & 0xFFu) | ((ch & 0xFFu) << 8));
        if (rev_ch >= 0xF801u && rev_ch <= 0xF890u) {
            s32 n_extra = 0;
            for (s32 t = 0; table[t].code != 0xF890u; ++t) {
                if (table[t].code == rev_ch) {
                    n_extra = table[t].has_arg;
                    break;
                }
            }
            for (s32 k = 0; k < n_extra; ++k) {
                const u32 ex = engine_func_0017f928(src[src_off + 1], src[src_off]);
                if (count_only == 0) {
                    dst[out_idx] = static_cast<u16>(ex);
                }
                ++out_idx;
                src_off += 2;
            }
        }
    }
}

extern "C" u32 func_0023ebc0(void* p);
extern "C" u32 func_00385d0c(void* p);
extern "C" u32 func_00385d2c(void* p);
extern "C" const u8* script_vm_func_00235510(void* p, u32 idx);
extern "C" s32 camp_func_00385d14(void* p);
extern "C" void camp_func_002b7f08(void* base, u32 count, u32 elem_size, const void* cmp);
extern "C" s32 ui_func_00297004(u32 a0, s32 a1);
extern "C" void engine_func_0031e438(void* obj, const char* name, u32 a2);

// DECOMP_FUNC(0x0038350c, 628)
extern "C" void script_vm_func_0038350c(u8* self) {
    if (func_0023ebc0(self + 0x20) == 0u ||
        func_00385d0c(self + 0x20) == 0u ||
        func_00385d2c(self + 0x20) == 0u) {
        return;
    }

    const u8* const base = script_vm_func_00235510(self + 0x20, 0u);
    if (camp_func_00385d14(self + 0x20) > 0) {
        s32 i = 0;
        do {
            const u8* const entry = base + i * 0x88u;
            const s32 target = *reinterpret_cast<const s8*>(self + 0x10);
            if (static_cast<s32>(*reinterpret_cast<const u16*>(entry + 0x60)) == target) {
                const u16 req_flag = *reinterpret_cast<const u16*>(entry + 0x66);
                const u16 blk_flag = *reinterpret_cast<const u16*>(entry + 0x68);
                if ((req_flag == 0u || script_vm_func_002c0ba8(req_flag) != 0u) &&
                    (blk_flag == 0u || script_vm_func_002c0ba8(blk_flag) == 0u)) {
                    const s32 count = *reinterpret_cast<const s32*>(self + 0xD8C);
                    const u32 key = *reinterpret_cast<const u16*>(entry + 0x62);
                    bool dup = false;
                    for (s32 j = 0; j < count; ++j) {
                        if (*reinterpret_cast<const u32*>(self + 0xD60 + j * 8) == key) {
                            dup = true;
                            break;
                        }
                    }
                    if (!dup) {
                        *reinterpret_cast<s32*>(self + 0xD5C + count * 8) = i;
                        *reinterpret_cast<u32*>(self + 0xD60 + count * 8) = key;
                        const u32 next_count = static_cast<u32>(*reinterpret_cast<const s32*>(self + 0xD8C) + 1);
                        *reinterpret_cast<u32*>(self + 0xD8C) = next_count;
                        if (next_count >= 6u) {
                            break;
                        }
                    }
                }
            }
            ++i;
        } while (i < camp_func_00385d14(self + 0x20));
    }

    camp_func_002b7f08(
        self + 0xD5C,
        *reinterpret_cast<const u32*>(self + 0xD8C),
        8u,
        reinterpret_cast<const void*>(0x00381D8Cu));

    if (self[0x18] == 1u) {
        for (u32 slot = 0u; slot < 6u; ++slot) {
            const s32 count = *reinterpret_cast<const s32*>(self + 0xD8C);
            const u32 want = slot + 1u;
            s32 val = -1;
            for (s32 j = 0; j < count; ++j) {
                if (*reinterpret_cast<const u32*>(self + 0xD60 + j * 8) == want) {
                    const u8* const e = script_vm_func_00235510(
                        self + 0x20,
                        *reinterpret_cast<const u32*>(self + 0xD5C + j * 8));
                    const u16 h64 = *reinterpret_cast<const u16*>(e + 0x64);
                    val = (h64 == 2u) ? 1 : 2;
                    break;
                }
            }
            if (val < 0) {
                val = ui_func_00297004(1u, 2);
            }

            char name[0x40];
            ui_func_002be7fc(name, "hunter_company_npc%d_%d", want, val);
            void* const obj0 = *reinterpret_cast<void**>(*reinterpret_cast<u8**>(self + 0xD10 + slot * 4u) + 8);
            engine_func_0031e438(obj0, name, 0u);

            ui_func_002be7fc(name, "hunter_company_npc%d_%d_add1", want, val);
            void* const obj1 = *reinterpret_cast<void**>(*reinterpret_cast<u8**>(self + 0xD28 + slot * 4u) + 8);
            engine_func_0031e438(obj1, name, 0u);
        }
    }

    *reinterpret_cast<u32*>(self + 4) = 2u;
    *reinterpret_cast<u32*>(self + 8) = 0u;
}

extern "C" s32 engine_func_002c54d8(u32* out, u32 a1, u32 a2);
extern "C" void engine_func_002c5468(s32 err);
extern "C" s32 engine_func_002c5450(u32* out, u32 handle, u32 a2);
extern "C" void* engine_func_002c34a4(u32 a0, u32 a1, u32 a2, u32 size, u32 a4, u32 a5);
extern "C" void nn_sdk_func_002bcf34(void* dst, void* buf, u32 size);
extern "C" u32 nn_sdk_func_002bce50(
    void* thread_out, const void* desc, u32 entry, void* arg_ptr,
    u32 stack_top, u32 prio, s32 core, u32 a7);
extern "C" u32 func_002cbdac(u32 rc);

// DECOMP_FUNC(0x002237a0, 632)
extern "C" u32 SaveLoad_Thread_func_002237a0(u8* self, u32 mode) {
    self[1] = static_cast<u8>(mode);

    u32 tmp = 0u;
    s32 res = engine_func_002c54d8(&tmp, 0u, 1u);
    if (res >= 0) {
        *reinterpret_cast<u32*>(self + 0x4C) = tmp;
        res = 0;
    }
    if (res < 0) {
        engine_func_002c5468(res);
    }

    const s32 res2 = engine_func_002c5450(&tmp, *reinterpret_cast<const u32*>(self + 0x4C), 1u);
    if (res2 < 0) {
        engine_func_002c5468(res2);
    }

    void* const buf = engine_func_002c34a4(0x100u, 0x100u, 0u, 0x2000u, 0x1000u, 1u);
    *reinterpret_cast<void**>(self + 0x28) = buf;
    nn_sdk_func_002bcf34(self + 0x2C, buf, 0x2000u);

    u32 rc = 0xE7E3FFFFu;
    if (mode <= 3u) {
        struct ThreadDesc {
            u32 w0;
            u32 name_addr;
            u32 w2;
            u32 entry_addr;
        };
        u32 entry_addr = 0u;
        if (mode == 1u) {
            entry_addr = 0x002EF824u;
        } else if (mode == 0u || mode == 3u) {
            entry_addr = 0x002D8E0Cu;
        } else {
            entry_addr = 0x002D8ED4u;
        }

        ThreadDesc desc;
        desc.w0 = 4u;
        desc.name_addr = 0x003F70B0u;
        desc.w2 = 0x003F7210u;
        desc.entry_addr = 0x003F717Cu;
        u8* self_arg = self;
        const u32 stack_top = *reinterpret_cast<const u32*>(self + 0x34) + *reinterpret_cast<const u32*>(self + 0x38);
        rc = nn_sdk_func_002bce50(self + 0x44, &desc, entry_addr, &self_arg, stack_top, 0x11u, -2, 0u);
        if ((rc & 0x07E00000u) != 0x00600000u && static_cast<s32>(rc) < 0) {
            engine_func_002c5468(static_cast<s32>(rc));
        }
    }

    return (func_002cbdac(rc) == 0u) ? 1u : 0u;
}

extern "C" u8* ui_func_002c0ac8();
extern "C" void ui_func_002c1b64(void* g);
extern "C" void ui_func_002c3ba8(void* g);
extern "C" void func_0032af00();
extern "C" void ui_func_002c1d3c(void* g, u32 a1);
extern "C" void func_002b7a10(
    const float* c0, const float* c1, const float* c2, const float* c3,
    float x, float y, float w, float h, float z);
extern "C" void ui_func_002c1abc(void* g);
extern "C" void script_vm_func_00262a54(char* dst, const char* src, u32 max_len);

// DECOMP_FUNC(0x002016cc, 640)
extern "C" u32 ui_func_002016cc() {
    u8* const state = ui_func_002c0ac8();
    u8* const g = *reinterpret_cast<u8**>(0x0044EA00u);

    if (*reinterpret_cast<const u32*>(state + 0x10) != 1u) {
        ui_func_002c1b64(*reinterpret_cast<void**>(0x0044EA00u));
        ui_func_002c3ba8(*reinterpret_cast<void**>(0x0044EA00u));
        func_0032af00();

        const float alpha = *reinterpret_cast<const float*>(state + 0x6C);
        if (alpha != 0.0f) {
            ui_func_002c3ba8(*reinterpret_cast<void**>(0x0044EA00u));

            typedef void (*ApplyBlendFn)(u32);
            u8* const stack = *reinterpret_cast<u8**>(0x0044EA00u) + 0x124C;
            const u32 val = ui_func_002c5f7c(1u, 0u);
            const u32 depth = *reinterpret_cast<u32*>(stack);
            const u32 prev_val = *reinterpret_cast<u32*>(stack + 8 + depth * 4u);
            const u32 next_depth = depth + 1u;
            *reinterpret_cast<u32*>(stack) = next_depth;
            *reinterpret_cast<u32*>(stack + 8 + next_depth * 4u) = val;
            if (stack[0x18] != 0u || prev_val != val) {
                reinterpret_cast<ApplyBlendFn>(*reinterpret_cast<const u32*>(stack + 0x1C))(val);
                stack[0x18] = 0u;
            }

            float quad[4];
            quad[0] = 1.0f;
            quad[1] = 1.0f;
            quad[2] = 1.0f;
            quad[3] = *reinterpret_cast<const float*>(state + 0x6C);
            ui_func_002c1d3c(*reinterpret_cast<void**>(0x0044EA00u), 0u);
            func_002b7a10(quad, quad, quad, quad, 0.0f, 0.0f, 400.0f, 240.0f, 0.95703125f);

            u8* const stack2 = *reinterpret_cast<u8**>(0x0044EA00u) + 0x124C;
            const u32 depth2 = *reinterpret_cast<u32*>(stack2);
            const u32 popped = *reinterpret_cast<u32*>(stack2 + 8 + depth2 * 4u);
            const u32 prev_depth = depth2 - 1u;
            *reinterpret_cast<u32*>(stack2) = prev_depth;
            const u32 restore = *reinterpret_cast<u32*>(stack2 + 8 + prev_depth * 4u);
            if (stack2[0x18] != 0u || popped != restore) {
                reinterpret_cast<ApplyBlendFn>(*reinterpret_cast<const u32*>(stack2 + 0x1C))(restore);
                stack2[0x18] = 0u;
            }
        }
    } else {
        const s32 total = *reinterpret_cast<const s32*>(state + 0x60);
        s32 count = 10;
        s32 start = 0;
        if (total < 10) {
            count = total;
        } else {
            const s32 sel = *reinterpret_cast<const s32*>(state + 0x68);
            if (sel >= 10) {
                start = sel - 9;
            }
        }

        for (s32 i = 0; i < count; ++i) {
            const s32 idx = i + start;
            s32 color = -1;
            if (*reinterpret_cast<const s32*>(state + 0x68) == idx) {
                color = 0x00FF00FF;
                ui_func_002be77c(2u, 0x00FF00FF, ">", 8.0f, static_cast<float>(i * 14), 0.1f, 0.0f, 1.0f);
            }
            const char* const items = *reinterpret_cast<const char* const*>(state + 0x64);
            char buf[0x44];
            script_vm_func_00262a54(buf, items + idx * 0x228u, 0x40u);
            ui_func_002be77c(2u, color, buf, 20.0f, static_cast<float>(i * 14), 0.1f, 1.0f, 1.0f);
        }
    }

    (void)g;
    ui_func_002c1b64(*reinterpret_cast<void**>(0x0044EA00u));
    ui_func_002c1abc(*reinterpret_cast<void**>(0x0044EA00u));
    return 0u;
}

extern "C" u32 engine_func_0027d010();
extern "C" void script_vm_func_00152af8(void* p);
extern "C" void script_vm_func_002a7aa0(void* p);
extern "C" void engine_func_0028c8a8(void* sub, u32 a1, const void* vec);
extern "C" void engine_func_0028c880(void* sub, u32 a1, float f0, float f1, float f2);
extern "C" void engine_func_002a5a54(void* sub, float f0);
extern "C" void battle_func_00267420(s32 a0, f32 f0, f32 f1, f32 f2, f32 f3, f32 f4, f32 f5, f32 f6);

// DECOMP_FUNC(0x0027521c, 640)
extern "C" void engine_func_0027521c() {
    u8* const* const g_ptr = reinterpret_cast<u8* const*>(0x00447A48u);
    u8* const obj = *g_ptr;

    if (obj[4] == 0u) {
        const u8* const g8 = reinterpret_cast<const u8*>(0x0049F91Cu);
        for (s32 i = 0; i < 24; ++i) {
            u8* const e = (*g_ptr) + 0x1C + i * 0x28u;
            if (e[0] == 0u) {
                continue;
            }
            u32* const node_flags = *reinterpret_cast<u32**>(e + 0x18);
            const u32 flags = *node_flags;
            if (g8[0x22] != 0u) {
                if ((flags & 2u) == 0u) {
                    *node_flags = flags | 2u;
                    u8* const sub = *reinterpret_cast<u8**>(reinterpret_cast<u8*>(node_flags) + 8);
                    (*reinterpret_cast<u8**>(sub + 0x2C))[0x1F6] = 0u;
                }
                continue;
            }

            if ((flags & 2u) != 0u) {
                *node_flags = flags & ~2u;
                u8* const sub = *reinterpret_cast<u8**>(reinterpret_cast<u8*>(node_flags) + 8);
                (*reinterpret_cast<u8**>(sub + 0x2C))[0x1F6] = 1u;
            }

            if (e[1] != 0u) {
                u8* const sub0 = *reinterpret_cast<u8**>((*reinterpret_cast<u8**>(e + 0x18)) + 8);
                engine_func_0028c8a8(sub0, 0u, e + 4);
                u8* const sub1 = *reinterpret_cast<u8**>((*reinterpret_cast<u8**>(e + 0x18)) + 8);
                engine_func_0028c880(sub1, 0u, 0.0f, *reinterpret_cast<const float*>(e + 0x10), 0.0f);
                u8* const sub2 = *reinterpret_cast<u8**>((*reinterpret_cast<u8**>(e + 0x18)) + 8);
                if (*reinterpret_cast<const s32*>(sub2 + 0x38) != static_cast<s32>(*reinterpret_cast<const s16*>(e + 0x14))) {
                    engine_func_002a5a54(sub2, 0.0f);
                }
                e[1] = 0u;
            }
        }
        return;
    }

    const u32 state = *reinterpret_cast<const u32*>(obj);
    if (state == 0u) {
        for (s32 i = 23; i >= 0; --i) {
            void* const p = *reinterpret_cast<void**>((*g_ptr) + 0x34 + i * 0x28u);
            if (p != nullptr) {
                script_vm_func_00152af8(p);
            }
        }
        *reinterpret_cast<u32*>(*g_ptr) += 1u;
    } else if (state == 1u) {
        for (s32 i = 23; i >= 0; --i) {
            void* const p = *reinterpret_cast<void**>((*g_ptr) + 0x34 + i * 0x28u);
            if (p != nullptr) {
                script_vm_func_002a7aa0(p);
                *reinterpret_cast<u32*>((*g_ptr) + 0x34 + i * 0x28u) = 0u;
            }
        }
        u8* const o2 = *g_ptr;
        for (s32 i = 0; i < 24; ++i) {
            o2[0x1C + i * 0x28u] = 0u;
        }
        *reinterpret_cast<u32*>(o2) += 1u;
    } else if (state == 2u) {
        if (engine_func_0027d010() != 0u) {
            for (s32 i = 0; i < 24; ++i) {
                const u8* const e = (*g_ptr) + 0x1C + i * 0x28u;
                if (e[0] != 0u && *reinterpret_cast<const u16*>(e + 0x16) == 0x0Cu) {
                    const float* const f = reinterpret_cast<const float*>(e + 4);
                    battle_func_00267420(
                        *reinterpret_cast<const s16*>(e + 0x1C),
                        f[0], f[1], f[2], f[3], 600.0f, 350.0f, 160.0f);
                }
            }
            u8* const o2 = *g_ptr;
            o2[4] = 0u;
            *reinterpret_cast<u32*>(o2) = 0u;
        }
    }
}

// DECOMP_FUNC(0x0036ee9c, 640)
extern "C" u8* engine_func_0036ee9c(const u8* desc, void* alloc) {
    typedef u8* (*AllocFn)(void* alloc, u32 size, u32 align);
    auto call_alloc = [&](u32 size, u32 align) -> u8* {
        void** const vtbl = *reinterpret_cast<void***>(alloc);
        return reinterpret_cast<AllocFn>(vtbl[2])(alloc, size, align);
    };

    const u32 fmt = *reinterpret_cast<const u32*>(desc + 0x14);
    const s32 min_dim = (fmt == 0xCu) ? 16 : 8;

    u8* const hdr = call_alloc(0x3Cu, 4u);
    if (hdr != nullptr) {
        for (u32 i = 0; i < 15u; ++i) {
            *reinterpret_cast<u32*>(hdr + i * 4u) = 0u;
        }
    }

    const u32* const t0 = reinterpret_cast<const u32*>(0x004091F8u);
    const u32* const t1 = t0 + 0x0E;
    *reinterpret_cast<u32*>(hdr + 0x00) = 0x20000011u;
    *reinterpret_cast<u32*>(hdr + 0x04) = 0x4D495854u;
    *reinterpret_cast<u32*>(hdr + 0x08) = 0x05000000u;
    *reinterpret_cast<u32*>(hdr + 0x0C) = 0u;
    *reinterpret_cast<u32*>(hdr + 0x10) = 0u;
    *reinterpret_cast<u32*>(hdr + 0x14) = 0u;
    *reinterpret_cast<u32*>(hdr + 0x18) = *reinterpret_cast<const u32*>(desc + 0x00);
    *reinterpret_cast<u32*>(hdr + 0x1C) = *reinterpret_cast<const u32*>(desc + 0x04);
    *reinterpret_cast<u32*>(hdr + 0x20) = t0[fmt];
    *reinterpret_cast<u32*>(hdr + 0x24) = t1[fmt];
    *reinterpret_cast<u32*>(hdr + 0x28) = *reinterpret_cast<const u32*>(desc + 0x08);
    *reinterpret_cast<u32*>(hdr + 0x2C) = 0u;
    *reinterpret_cast<u32*>(hdr + 0x30) = *reinterpret_cast<const u32*>(desc + 0x0C);
    *reinterpret_cast<u32*>(hdr + 0x34) = fmt;

    u8* const sub = call_alloc(0x20u, 4u);
    if (sub != nullptr) {
        for (u32 i = 0; i < 8u; ++i) {
            *reinterpret_cast<u32*>(sub + i * 4u) = 0u;
        }
    }

    *reinterpret_cast<void**>(sub + 0x10) = alloc;
    *reinterpret_cast<u32*>(sub + 0x00) = *reinterpret_cast<const u32*>(desc + 0x00);
    *reinterpret_cast<u32*>(sub + 0x04) = *reinterpret_cast<const u32*>(desc + 0x04);
    *reinterpret_cast<u32*>(sub + 0x18) = *reinterpret_cast<const u32*>(desc + 0x10);
    const float bpp = reinterpret_cast<const float*>(0x00409268u)[fmt];
    *reinterpret_cast<u32*>(sub + 0x14) = static_cast<u32>(bpp * 8.0f);

    s32 w = *reinterpret_cast<const s32*>(desc + 0x00);
    s32 h = *reinterpret_cast<const s32*>(desc + 0x04);
    const s32 mips = *reinterpret_cast<const s32*>(desc + 0x08);
    s32 rem = mips;
    u32 total_bytes = 0u;
    while (rem > 0) {
        const u32 mip_bytes = static_cast<u32>(bpp * static_cast<float>(w) * static_cast<float>(h));
        total_bytes += mip_bytes;
        if (w == min_dim && h == min_dim) {
            *reinterpret_cast<u32*>(hdr + 0x28) = static_cast<u32>(mips - rem + 1);
            break;
        }
        if (w > min_dim) {
            w /= 2;
        }
        if (h > min_dim) {
            h /= 2;
        }
        --rem;
    }

    if (desc[0x19] == 0u) {
        *reinterpret_cast<u32*>(sub + 0x08) = 0u;
        *reinterpret_cast<u32*>(sub + 0x0C) = 0u;
    } else {
        u8* const px = call_alloc(total_bytes, 0x80u);
        if (desc[0x18] != 0u && total_bytes != 0u) {
            for (u32 i = 0; i < total_bytes; ++i) {
                px[i] = 0u;
            }
        }
        *reinterpret_cast<u32*>(sub + 0x08) = total_bytes;
        *reinterpret_cast<u32*>(sub + 0x0C) =
            (px != nullptr) ? static_cast<u32>(px - (sub + 0x0C)) : 0u;
    }

    *reinterpret_cast<u32*>(hdr + 0x38) =
        (sub != nullptr) ? static_cast<u32>(sub - (hdr + 0x38)) : 0u;
    return hdr;
}

extern "C" void func_0020d788();
extern "C" void func_002aa418(
    u32 c0, u32 c1, u32 c2, u32 c3,
    float x, float y, float w, float h,
    float u0, float v0, float u1, float v1, float z);

// DECOMP_FUNC(0x001f9c3c, 644)
extern "C" void func_001f9c3c() {
    u8* const g = *reinterpret_cast<u8* const*>(0x00447600u);
    if (g == nullptr || *reinterpret_cast<const u32*>(g + 4) != 8u ||
        reinterpret_cast<const u8*>(0x0049F91Cu)[0x20] != 0u) {
        return;
    }

    for (s32 i = 0; i < 32; ++i) {
        u8* const e = g + 0x34 + i * 0x180u;
        if (e[0] == 0u) {
            continue;
        }
        e[0x15C] = 0u;
        if (e[0x13E] == 0u || e[0x17C] == 0u || e[0x144] == 0u) {
            continue;
        }

        func_0020d788();
        if (e[0x7E] != 0u) {
            continue;
        }

        const float f80 = *reinterpret_cast<const float*>(e + 0x80);
        float px = 0.0f;
        float py = 0.0f;
        if (f80 > 0.0f) {
            if (f80 <= 90.0f) {
                px = 0.0f;
                py = f80 * 2.2f;
            } else {
                px = (f80 - 90.0f) * 1.9888889f;
                py = 198.0f;
            }
        } else {
            const float neg = -f80;
            if (neg <= 90.0f) {
                px = 358.0f;
                py = neg * 2.2f;
            } else {
                px = 358.0f - (neg - 90.0f) * 1.9888889f;
                py = 198.0f;
            }
        }

        const s32 rem = *reinterpret_cast<const s32*>(e + 0x140) % 20;
        const float u0 = (rem < 10) ? 0.0f : 0.328125f;
        const float u1 = 0.328125f;

        const s32 val148 = *reinterpret_cast<const s32*>(e + 0x148);
        u32 c0 = 0xFFFFFFFFu;
        u32 c1 = 0x2DB5FFFFu;
        if (val148 < 0x43C80000) {
            c0 = 0xEF6C3EFFu;
            c1 = 0xFE0B22FFu;
        } else if (val148 < 0x44480000) {
            c0 = 0xFBC30DFFu;
            c1 = 0xFF6C2BFFu;
        } else if (val148 < 0x44960000) {
            c0 = 0xFFF2C0FFu;
            c1 = 0xFFD52DFFu;
        }

        e[0x15C] = 1u;
        *reinterpret_cast<float*>(e + 0x160) = px + 12.0f;
        *reinterpret_cast<float*>(e + 0x164) = py + 12.0f;
        func_002aa418(c0, c1, c0, c1, px, py, 42.0f, 42.0f, u0, 0.0f, u1, 0.65625f, 0.0f);
        func_002aa418(0xFFu, 0xFFu, 0xFFu, 0xFFu, px, py, 42.0f, 42.0f, 0.65625f, 0.0f, 0.328125f, 0.65625f, 0.0f);
    }
}

extern "C" s32 shop_func_0029ebc4(void* p);
extern "C" s32 unite_func_002338ac(void* p);
extern "C" const u8* camp_func_002b9364(u32 id);
extern "C" u32 camp_func_0029d100(u32 item_id, u32 mode, u32 a2, u32 a3, u32 a4);

// DECOMP_FUNC(0x0022d33c, 652)
extern "C" void camp_func_0022d33c(u8* self) {
    if (*reinterpret_cast<const u32*>(self + 0x28) == 0u) {
        return;
    }

    const s32 start_idx = shop_func_0029ebc4(self + 0x20);
    const s32 count = unite_func_002338ac(self + 0x20);
    s32* const g_last = reinterpret_cast<s32*>(0x0043D9C8u);
    if (start_idx == g_last[1]) {
        return;
    }
    g_last[1] = start_idx;
    if (count <= 0) {
        return;
    }

    for (s32 i = 0; i < count; ++i) {
        const u16 item_id = *reinterpret_cast<const u16*>(self + (start_idx + i) * 32 + 0x5AC);
        const bool has_a4 = (self[0x5A4] != 0u);
        u32 color_cmp = 0xFFFFFFFFu;

        const s32 cur_idx = shop_func_0029ebc4(self + 0x20) + i;
        const u8* const entry = self + cur_idx * 32 + 0x5AC;
        const u8 mode = self[0x5A5];
        u32 val8 = 0u;
        if (has_a4) {
            if (mode == 0u) {
                val8 = entry[0xC];
            } else if (mode == 1u) {
                val8 = entry[0xD];
            }
        } else {
            if (mode == 0u) {
                const u8* const info = camp_func_002b9364(*reinterpret_cast<const u16*>(entry));
                if (info != nullptr) {
                    val8 = info[3];
                }
            } else if (mode == 1u) {
                val8 = entry[0xC];
            } else if (mode == 2u) {
                val8 = entry[0xD];
            }
        }

        if (self[0x5A4] == 1u && self[0x5A5] == 1u) {
            const s32 cur_idx2 = shop_func_0029ebc4(self + 0x20) + i;
            const u8* const entry2 = self + cur_idx2 * 32 + 0x5AC;
            u32 base_val = 0u;
            if (has_a4) {
                base_val = entry2[0xC];
            } else {
                const u8* const info = camp_func_002b9364(*reinterpret_cast<const u16*>(entry2));
                if (info != nullptr) {
                    base_val = info[3];
                }
            }
            if (val8 > base_val) {
                color_cmp = 0x72E027FFu;
            } else if (val8 < base_val) {
                color_cmp = 0xDC0F14FFu;
            }
        }

        u32* const g_arr = reinterpret_cast<u32*>(0x0049357Cu);
        g_arr[i] = val8;
        g_arr[10 + i] = color_cmp;

        const u32 arg_a4 = (self[0x5A4] != 0u) ? 1u : 0u;
        const u8* const pos0 = camp_func_002bf6c8(self + 0xC8, static_cast<u32>(i + 0x42F));
        const s32 x0 = *reinterpret_cast<const s16*>(pos0 + 8);
        const s32 y0 = *reinterpret_cast<const s16*>(pos0 + 0xA);
        const u32 ge100 = (*reinterpret_cast<const s8*>(self + 0x94) >= 100) ? 1u : 0u;
        const u32 price = camp_func_0029d100(item_id, self[0x5A5], arg_a4, ge100, 0u);

        u32 price_color = 0xFFFFFFFFu;
        if (self[0x5A4] == 1u) {
            const u32 ge100_2 = (*reinterpret_cast<const s8*>(self + 0x94) >= 100) ? 1u : 0u;
            const u32 base_price = camp_func_0029d100(item_id, 0u, arg_a4, ge100_2, 0u);
            if (price < base_price) {
                price_color = 0xDC0F14FFu;
            } else if (price > base_price) {
                price_color = 0x72E027FFu;
            }
        }

        const u8* const pos1 = camp_func_002bf6c8(self + 0xC8, 0x4C6u);
        u8* const g_out = reinterpret_cast<u8*>(0x004935CCu);
        *reinterpret_cast<s32*>(g_out + i * 4) = *reinterpret_cast<const s16*>(pos1 + 8) + x0;
        *reinterpret_cast<s32*>(g_out + 0x28 + i * 4) = *reinterpret_cast<const s16*>(pos1 + 0xA) + y0;
        ui_func_002be7fc(reinterpret_cast<char*>(g_out + 0x50 + i * 0x20), "%8u", price);
        *reinterpret_cast<u32*>(reinterpret_cast<u8*>(0x0049375Cu) + i * 4) = price_color;
    }
}

extern "C" u32 ui_func_0026b7cc();
extern "C" void engine_func_002b8584(u32 a0);
extern "C" void engine_func_002a150c(void* dst, u32 a1);
extern "C" void shop_func_002339e8(void* p);
extern "C" void shop_func_002339ac(void* p);
extern "C" void camp_func_00233ac0(void* self, s32 a1, u32 a2);
extern "C" u32 func_002f61a4();
extern "C" u32 camp_func_002c1830(u32 a0, u32 a1);
extern "C" void camp_func_002bc200(u32 id);
extern "C" void script_vm_func_00289984();
extern "C" void script_vm_func_0023554c();
extern "C" void func_002fea30();
extern "C" void camp_func_002b9008();
extern "C" void script_vm_func_00262bcc(u32 a0, u32 a1);

// DECOMP_FUNC(0x00392060, 656)
extern "C" void script_vm_func_00392060(u8* self) {
    auto finish_with_status = [&](u32 status) {
        *reinterpret_cast<u32*>(self + 4) = status;
        *reinterpret_cast<u32*>(self + 8) = 0u;
        u8* const vobj = *reinterpret_cast<u8**>(self + 0x208);
        if (vobj != nullptr) {
            typedef void (*Vfunc1)(u8*);
            void** const vtbl = *reinterpret_cast<void***>(vobj);
            reinterpret_cast<Vfunc1>(vtbl[1])(vobj);
            *reinterpret_cast<u32*>(self + 0x208) = 0u;
        }
    };

    const u32 state = *reinterpret_cast<const u32*>(self + 8);
    if (state == 0u) {
        engine_func_002b8584(0u);
        u32 tmp = 0u;
        engine_func_002a150c(&tmp, *reinterpret_cast<const u32*>(0x00433158u));
        *reinterpret_cast<u32*>(self) &= ~0x10u;

        u8* const g = *reinterpret_cast<u8* const*>(0x00432FC8u);
        *reinterpret_cast<u32*>(g + 0x754) &= ~0x100u;
        (*reinterpret_cast<u8* const*>(0x00433130u))[0x450C] = 0u;

        shop_func_002339e8(self + 0x2E8);
        shop_func_002339ac(self + 0x2B4);
        (*reinterpret_cast<u8* const*>(0x00432FC8u))[0xD50] = 2u;

        const u32 h = script_vm_func_00291018(*reinterpret_cast<const u32*>(self + 0x350), "aoc_IsConnect");
        script_vm_func_002971e4(*reinterpret_cast<const u32*>(self + 0x358), h);
        camp_func_00233ac0(self, 0, 1u);
        *reinterpret_cast<u32*>(self + 8) = 1u;
    } else if (state == 1u) {
        if (script_vm_func_0019dfbc(*reinterpret_cast<const u32*>(self + 0x358)) != 2u) {
            if (func_002f61a4() != 0u && camp_func_002c1830(1u, 1u) != 0u) {
                camp_func_002bc200(0x0100016Du);
                script_vm_func_00289984();
                script_vm_func_0023554c();
                func_002fea30();
                camp_func_002b9008();
                camp_func_002b9008();
                finish_with_status(0xFu);
            }
            return;
        }

        const u32 r = script_vm_func_00297674();
        if (r == 0u) {
            *reinterpret_cast<u32*>(self + 8) = 2u;
            script_vm_func_00126edc((*reinterpret_cast<u8* const*>(0x00432FC8u)) + 0x80);

            struct TimestampRec {
                u32 hdr;
                u64 ts;
                u32 w3;
                u32 w4;
            } rec{};
            rec.hdr = 0u;
            engine_func_002bb09c(&rec.ts);
            rec.w3 = 0u;
            rec.w4 = 0u;
            u64 tmp_ts = 0u;
            rec.ts = *engine_func_002bad80(&tmp_ts, 0u);
            *reinterpret_cast<u32*>(self + 0x210) = rec.hdr;
            *reinterpret_cast<u64*>(self + 0x214) = rec.ts;
            *reinterpret_cast<u32*>(self + 0x21C) = rec.w3;
            *reinterpret_cast<u32*>(self + 0x220) = rec.w4;

            camp_func_00233ac0(self, -1, 0u);
            script_vm_func_00262bcc(0x01000001u, 0xAu);
        } else if (r == 1u) {
            finish_with_status(0xFu);
        }
    } else if (state == 2u) {
        if (ui_func_0026b7cc() != 0u) {
            finish_with_status(4u);
        }
    }
}

// DECOMP_FUNC(0x0023f65c, 668)
extern "C" void engine_func_002c4b30(void* dst, u32 size);
extern "C" const char* engine_func_00240578(void* ctx);
extern "C" void engine_func_002bf86c(char* dst, const char* src);
extern "C" u32 script_vm_func_00240420(void* fs, const char* path);
extern "C" void engine_func_002c4360(u32 handle);
extern "C" void script_vm_func_00297704(const char* path, void* dst, u32 flag);
extern "C" void script_vm_func_00240158(u32* self, u8* ctx);
extern "C" void script_vm_func_00270298(u32 a0);
extern "C" void func_0033868c(void* ctx);
extern "C" void func_0033a378(void* ctx);
extern "C" void func_00338658(void* ctx);
extern "C" void func_0033a014(void* ctx);
extern "C" void func_003d7228(void* obj);
extern "C" const u8* ui_func_0027dca0(void* ctx, s32 id);
extern "C" u32 func_002406f8(void* ctx, u32 id);
extern "C" void battle_func_00250800(u32 a0, u32 a1, u32 a2, u32 a3, u32 a4, u32 a5, u32 a6);
extern "C" void script_vm_func_00255198(void* ctx);
extern "C" void ui_func_00394e88(u32 a0);
extern "C" u32 script_vm_func_002c2bd0(u32 ch);
extern "C" void script_vm_func_002c2ba4(u32 ch, u32 a1, u32 a2);
extern "C" u32 script_vm_func_00289924();
extern "C" void battle_func_0023fd38(void* self, void* ctx);

extern "C" void script_vm_func_0023f65c(u32* self, u8* ctx) {
    char buf0[0x80];
    engine_func_002c4b30(buf0, 0x80u);
    engine_func_002bf86c(buf0, engine_func_00240578(ctx));
    if (script_vm_func_00240420(ctx, buf0) != 0u) {
        self[0] = 0xBu;
        char buf1[0x80];
        engine_func_002c4b30(buf1, 0x80u);
        engine_func_002bf86c(buf1, engine_func_00240578(ctx));
        if (self[1] != 0u) {
            engine_func_002c4360(self[1]);
            self[1] = 0u;
        }
        script_vm_func_00297704(buf1, &self[1], 0u);
        self[0] = 0xCu;
        reinterpret_cast<void (*)(void*, void*)>(script_vm_func_00240158)(self, ctx);
        return;
    }

    u32* const f44a0 = reinterpret_cast<u32*>(ctx + 0x44A0);
    self[0] = 0xDu;
    if ((*f44a0 & 0x40000000u) == 0u) {
        script_vm_func_00270298(2u);
        *f44a0 |= 0x40000000u;
    }

    func_0033868c(ctx);
    func_0033a378(ctx);
    func_00338658(ctx);
    func_0033a014(ctx);
    func_003d7228(*reinterpret_cast<void* const*>(0x004342C8u));

    if (ctx[0x44B7] == 0u &&
        ((*reinterpret_cast<const u32*>(ctx + 0xE0) & 0x02000000u) != 0u || (*f44a0 & 2u) != 0u)) {
        for (s32 i = 4; i < 0x36; ++i) {
            u8* const e = (*reinterpret_cast<u8* const*>(ctx + 0x1E98)) + i * 0x114u;
            const u32 w50 = *reinterpret_cast<const u32*>(e + 0x50);
            if ((w50 & 1u) != 0u && (w50 & 2u) != 0u) {
                const u32 w54 = *reinterpret_cast<const u32*>(e + 0x54);
                if ((w54 & 8u) != 0u) {
                    *reinterpret_cast<u32*>(e + 0x54) = w54 & ~8u;
                    if ((*reinterpret_cast<const u16*>(e + 0x58) & 0x800u) == 0u) {
                        const u8* const unit = ui_func_0027dca0(ctx, *reinterpret_cast<const s16*>(e + 0x62));
                        if (func_002406f8(ctx, *reinterpret_cast<const u16*>(unit + 2)) == 0u) {
                            *reinterpret_cast<u16*>(e + 0x58) |= 0x800u;
                        }
                    }
                }
            }
        }

        battle_func_00250800(0u, 0u, 0x0100017Bu, 0u, 0u, 0u, 0u);
        script_vm_func_00255198(ctx);
        *f44a0 |= 0x00200000u;
        if ((*reinterpret_cast<const u32*>(ctx + 0xE4) & 0x20u) == 0u) {
            ui_func_00394e88(3u);
        }
    }

    if (script_vm_func_002c2bd0(0u) == 3u) {
        script_vm_func_002c2ba4(0u, 0xAu, 0xFFu);
    }
    if (script_vm_func_002c2bd0(1u) == 3u) {
        script_vm_func_002c2ba4(1u, 0xAu, 0xFFu);
    }
    if (script_vm_func_00289924() != 0u) {
        self[0] = 0xEu;
        self[3] = 0u;
        battle_func_0023fd38(self, ctx);
    }
}

// DECOMP_FUNC(0x0014a998, 672)
extern "C" void func_002ac0c4();

static inline u32 f32_bits_14a998(float v) {
    u32 u;
    __builtin_memcpy(&u, &v, sizeof(u));
    return u;
}

extern "C" void func_0014a998(const u8* ctx0, u8* out_desc, const u8* params, const u8* proj) {
    auto out_ptr = [out_desc]() -> u32* {
        const u32 off = *reinterpret_cast<const u32*>(out_desc + 0x10);
        return (off != 0u) ? reinterpret_cast<u32*>(out_desc + 0x10 + off) : nullptr;
    };

    out_ptr()[0] = 0u;
    out_ptr()[1] = 0x000F00E6u;
    out_ptr()[3] = 0x07FF00E8u;

    const auto exp_fn = reinterpret_cast<float (*)(float)>(func_002ac0c4);
    const u32 mode = *reinterpret_cast<const u32*>(params) & 0xFFu;
    const float p1 = *reinterpret_cast<const float*>(params + 4);
    const float p2 = *reinterpret_cast<const float*>(params + 8);
    const float p3 = *reinterpret_cast<const float*>(params + 0xC);

    float prev = 0.0f;
    s32 idx = 0;

    for (s32 step = 0; step <= 0x80; ++step) {
        float cur;
        if (*reinterpret_cast<const float*>(ctx0 + 0x160) == 0.0f) {
            const float t = static_cast<float>(step) * (-1.0f / 128.0f);
            const float num = *reinterpret_cast<const float*>(proj + 0x2C) +
                              *reinterpret_cast<const float*>(proj + 0x28) * t;
            const float den = *reinterpret_cast<const float*>(proj + 0x3C) +
                              *reinterpret_cast<const float*>(proj + 0x38) * t;
            cur = (-num) / den;
        } else {
            const float a = *reinterpret_cast<const float*>(ctx0 + 0x158);
            const float b = *reinterpret_cast<const float*>(ctx0 + 0x15C);
            const float t = static_cast<float>(step) * (1.0f / 128.0f);
            cur = a + t * (b - a);
        }

        if (cur <= p1) {
            cur = 1.0f;
        } else if (cur > p2) {
            cur = 0.0f;
        } else if (mode == 1u) {
            cur = (p2 - cur) / (p2 - p1);
        } else if (mode == 2u) {
            cur = exp_fn(-((cur - p1) * p3) / (p2 - p1));
        } else if (mode == 3u) {
            const float y = ((cur - p1) * p3) / (p2 - p1);
            cur = exp_fn(-(y * y));
        }

        if (step > 0) {
            float delta = (cur - prev + 2.0f) * 2048.0f;
            if (delta < 0.0f) {
                delta = 0.0f;
            } else if (static_cast<s32>(f32_bits_14a998(delta)) >= 0x46000000) {
                delta = 8191.0f;
            }
            const u32 diff_u13 = static_cast<u32>(static_cast<s32>(delta - 4096.0f)) & 0x1FFFu;

            u32 val_u11;
            const u32 prev_bits = f32_bits_14a998(prev);
            if (prev <= 0.0f || ((prev_bits << 1) >> 24) == 0xFFu) {
                val_u11 = 0u;
            } else {
                const float scaled = prev * 2048.0f;
                if (scaled >= 2048.0f) {
                    val_u11 = 0x7FFu;
                } else {
                    val_u11 = static_cast<u32>(scaled) & 0x7FFu;
                }
            }

            const u32 packed = diff_u13 | (val_u11 << 13);
            const u32 word_idx = (idx == 0) ? 2u : static_cast<u32>(idx + 3);
            ++idx;
            out_ptr()[word_idx] = packed;
        }

        prev = cur;
    }
}

// DECOMP_FUNC(0x0015b8f8, 680)
extern "C" void func_0015d888(u8** mat);
extern "C" u32 engine_func_002bc300(u32 ptr);

static inline u32 f32_bits_15b8f8(float v) {
    u32 u;
    __builtin_memcpy(&u, &v, sizeof(u));
    return u;
}

extern "C" void engine_func_0015b8f8(u8* self, const u8* src) {
    *reinterpret_cast<u32*>(self + 0x48) = 0x38u;
    u32* const desc = reinterpret_cast<u32*>(self + 0x10);
    desc[0] &= ~0xFu;
    desc[3] &= ~0x0FF00000u;
    desc[4] &= 0xF800F800u;
    desc[5] = (desc[5] & ~0x30u) & ~0x70000000u;
    desc[6] &= ~0x000F0000u;
    desc[7] &= 0xF0000000u;
    desc[13] = 0u;

    const u32 tex_off = *reinterpret_cast<const u32*>(src + 0x38);
    const u8* const tex_obj = (tex_off != 0u) ? (src + 0x38 + tex_off) : nullptr;
    u32 tex_ptr = *reinterpret_cast<const u32*>(tex_obj + 0x18);
    if (tex_ptr == 0u) {
        const u32 data_off = *reinterpret_cast<const u32*>(tex_obj + 0x0C);
        tex_ptr = (data_off != 0u) ? reinterpret_cast<u32>(tex_obj + 0x0C + data_off) : 0u;
    }

    desc[0] |= (*reinterpret_cast<const u32*>(src + 0x34) & 0xFu);
    desc[3] |= 0x00A00000u;
    desc[1] |= 0x000F0000u;
    desc[4] |= (*reinterpret_cast<const u32*>(src + 0x18) & 0x7FFu);
    desc[4] |= ((*reinterpret_cast<const u32*>(src + 0x1C) & ~0xF800u) << 16);
    desc[5] |= 0x20000000u;

    const u32 mat_off = *reinterpret_cast<const u32*>(self + 0x0C);
    u8* mat = (mat_off != 0u) ? (self + 0x0C + mat_off) : nullptr;
    if (mat != nullptr && (*reinterpret_cast<const u32*>(mat) & 0x80000000u) == 0u) {
        mat = nullptr;
    }

    desc[5] |= 0x00100000u;
    *reinterpret_cast<u32*>(mat + 8) = 1u;

    auto mat_sub = [](u8* m) -> u8* {
        const u32 moff = *reinterpret_cast<const u32*>(m + 4);
        return (moff != 0u) ? (m + 4 + moff) : nullptr;
    };

    u32* const sub24_init = reinterpret_cast<u32*>(mat_sub(mat) + 0x24);
    const u32 g0 = *reinterpret_cast<const u32*>(0x00422204u + 4u);
    const u32 g1 = *reinterpret_cast<const u32*>(0x0042221Cu + 4u);
    *sub24_init = (*sub24_init & ~4u) | ((g0 & 1u) << 2);
    *sub24_init = (*sub24_init & ~0x01000000u) | ((g1 & 1u) << 24);

    func_0015d888(&mat);

    *reinterpret_cast<u32*>(mat_sub(mat) + 0x24) |= 2u;
    u32* const sub24_b = reinterpret_cast<u32*>(mat_sub(mat) + 0x24);
    *sub24_b = (*sub24_b & ~0x7000u) | 0x1000u;
    u32* const sub24_c = reinterpret_cast<u32*>(mat_sub(mat) + 0x24);
    *sub24_c = (*sub24_c & ~0x700u) | 0x100u;

    const u32 gpu_addr = engine_func_002bc300(tex_ptr);
    desc[7] |= ((gpu_addr << 1) >> 4);
    desc[13] |= (src[0x3C] == 0u) ? 1u : 0u;

    const float f40 = *reinterpret_cast<const float*>(src + 0x40);
    const u32 f40_bits = f32_bits_15b8f8(f40);
    u32 val24;
    if (f40 <= 0.0f || ((f40_bits << 1) >> 24) == 0xFFu) {
        val24 = 0u;
    } else {
        const float scaled = f40 * 16777216.0f;
        if (static_cast<s32>(f32_bits_15b8f8(scaled)) >= 0x4B800000) {
            val24 = 0x00FFFFFFu;
        } else {
            val24 = static_cast<u32>(scaled);
        }
    }
    desc[13] |= (val24 & 0x00FFFFFEu);
}

// DECOMP_FUNC(0x002626fc, 684)
extern "C" const u8* camp_func_00311d20(u32 id1, u32 id2);
extern "C" u32 camp_func_0029ed44(void* self, u32 id);
extern "C" u32 camp_func_003c8fdc(void* self, u32 id1, u32 id2, u32 res_id);
extern "C" const u8* camp_func_002b9364(u32 id);
extern "C" const u8* camp_func_0029ec14(u32 id);
extern "C" void func_002b7f0a(void* base, s32 count, s32 size, u32 comparator);
extern "C" u32 camp_func_003c997c(void* self, u32 id1, u32 id2, u32 res_id);

extern "C" u32 camp_func_002626fc(u8* self, u32 id1, u32 id2, u32* out) {
    const u8* const pair = (id1 < id2) ? camp_func_00311d20(id1, id2) : camp_func_00311d20(id2, id1);
    if (pair == nullptr) {
        return 0u;
    }

    const u16 res_id = static_cast<u16>(*reinterpret_cast<const u32*>(pair + 4));
    if (res_id == 0u) {
        return 0u;
    }
    if (camp_func_0029ed44(self, res_id) == 0u) {
        return 0u;
    }
    if (camp_func_003c8fdc(self, id1, id2, *reinterpret_cast<const u32*>(pair + 4) & 0xFFFFu) == 0u) {
        return 0u;
    }

    u32 w0 = ((out[0] >> 15) << 15) | (id1 & ~0x8000u);
    w0 = (w0 & ~0x3FFF8000u) | ((id2 << 15) & 0x3FFF8000u);
    out[0] = w0;

    u32 w1 = (out[1] & 3u) | ((*reinterpret_cast<const u32*>(pair + 4) << 2) & 0x0001FFFFu);
    w1 = (w1 << 15) >> 15;
    out[1] = w1;

    const u8* const info = camp_func_002b9364(static_cast<u16>(*reinterpret_cast<const u32*>(pair + 4)));
    u16* const slots = reinterpret_cast<u16*>(self + 0x146);
    u32* const count_ptr = reinterpret_cast<u32*>(self + 0x178);

    for (s32 i = 0; i < 8; ++i) {
        const u16 sk = *reinterpret_cast<const u16*>(info + 0x3C + i * 2);
        if (sk != 0u) {
            slots[*count_ptr] = sk;
            *count_ptr += 1u;
        }
    }

    if (static_cast<s32>(*count_ptr) < 0x18) {
        slots[*count_ptr] = 0u;
    }

    for (s32 i = 0; i < 0x18; ++i) {
        if (slots[i] != 0u) {
            const u8* const sinfo = camp_func_0029ec14(slots[i]);
            if ((sinfo[3] & 0x20u) == 0u) {
                slots[i] = 0u;
            }
        }
    }

    func_002b7f0a(slots, static_cast<s32>(*count_ptr), 2, 0x002C6E7Cu);

    const s32 prev_count = static_cast<s32>(*count_ptr);
    *count_ptr = 0u;
    for (s32 i = 0; i < prev_count; ++i) {
        if (slots[i] == 0u) {
            break;
        }
        *count_ptr += 1u;
    }

    if (self[0x17D] != 0u) {
        u32 cost = info[3] * 20u;
        cost += *reinterpret_cast<const u16*>(info + 0x1A);
        cost += *reinterpret_cast<const u16*>(info + 0x1C);
        cost += *reinterpret_cast<const u16*>(info + 0x1E);
        cost += *reinterpret_cast<const u16*>(info + 0x20);
        cost += *reinterpret_cast<const u16*>(info + 0x22);
        for (s32 i = 0; i < 0x18; ++i) {
            if (slots[i] != 0u) {
                const u8* const sinfo = camp_func_0029ec14(slots[i]);
                cost += (sinfo[3] & 0x1Fu) * 5u;
            }
        }
        out[1] = (out[1] & 0x0001FFFFu) | (cost << 17);
    }

    return camp_func_003c997c(self, id1, id2, (out[1] & 0x0001FFFFu) >> 2);
}

// DECOMP_FUNC(0x0033ceb8, 684)
extern "C" void ui_func_002c1d3c(void* obj, u32 flag);
extern "C" void ui_func_002b7978(const float* a, const float* b, const float* c, const float* d,
                                 float s0, float s1, float s2, float s3, float s4);
extern "C" void ui_func_002bc2c4();
extern "C" void ui_func_002bf710(float alpha);
extern "C" float ui_func_0024807c(float s0, float s1, float s2, float s3);
extern "C" void ui_func_0033c960(void* self, s32 a1, float x, float y, float alpha);

extern "C" void ui_func_0033ceb8(u8* self) {
    if (*reinterpret_cast<const s32*>(self + 0x390) == 4) {
        return;
    }

    const float f394 = *reinterpret_cast<const float*>(self + 0x394);
    const float f398 = *reinterpret_cast<const float*>(self + 0x398);
    const float s17 = 1.0f - f394 * 0.25f;
    float rect[4] = {0.0f, 0.0f, 0.0f, (f398 * 0.25f) * s17 * 0.5f};

    ui_func_002c1d3c(*reinterpret_cast<void* const*>(0x0044EA00u), 0u);
    ui_func_002b7978(rect, rect, rect, rect, 0.0f, 0.0f, 400.0f, 240.0f, 0.87109375f);
    ui_func_002bc2c4();
    ui_func_002bf710(s17);

    const float f39c = *reinterpret_cast<const float*>(self + 0x39C);
    const float y_off = (4.0f - f39c) * 20.0f;
    const u32 y_pos = static_cast<u32>(static_cast<s32>(0.0f + y_off));
    ui_func_002bf460(2u, 0x14u, 0x54u, 0u, y_pos, 0x23u);
    ui_func_002bf460(2u, 0x14u, 0x55u, 0u, y_pos, 0x23u);

    const float f3a0 = *reinterpret_cast<const float*>(self + 0x3A0);
    const float x_off = ui_func_0024807c(30.0f, 0.0f, 8.0f, f3a0);
    const float item_alpha = (f3a0 * 0.125f) * s17;

    const s32 count = *reinterpret_cast<const s32*>(self + 0x2F4);
    for (s32 i = 0; i < count; ++i) {
        const u8* const item = self + i * 0x54;
        if (item[0x40] == 0u) {
            const s32 idx = *reinterpret_cast<const s32*>(item + 0x48);
            const float* const pt = reinterpret_cast<const float*>(self + 0x368 + idx * 8);
            ui_func_0033c960(self, 0x24, pt[0], pt[1] + y_off, s17);
        } else {
            const s32 n_2f8 = *reinterpret_cast<const s32*>(self + 0x2F8);
            const s32 n_2fc = *reinterpret_cast<const s32*>(self + 0x2FC);
            const s32 mode44 = *reinterpret_cast<const s32*>(item + 0x44);
            const s32 idx48 = *reinterpret_cast<const s32*>(item + 0x48);
            float x;
            float y;
            if (n_2f8 != 0 && n_2fc != 0) {
                if (mode44 == 1) {
                    x = static_cast<float>(idx48) * 76.0f + (400.0f - static_cast<float>(n_2f8) * 76.0f) * 0.5f + x_off;
                    y = *reinterpret_cast<const float*>(self + 0x388);
                } else {
                    x = static_cast<float>(idx48) * 76.0f + (400.0f - static_cast<float>(n_2fc) * 76.0f) * 0.5f + x_off;
                    y = *reinterpret_cast<const float*>(self + 0x38C);
                }
            } else {
                const s32 denom = (mode44 == 1) ? n_2f8 : n_2fc;
                const float y0 = *reinterpret_cast<const float*>(self + 0x388);
                const float y1 = *reinterpret_cast<const float*>(self + 0x38C);
                x = static_cast<float>(idx48) * 76.0f + (400.0f - static_cast<float>(denom) * 76.0f) * 0.5f + x_off;
                y = (y1 + y0) * 0.5f;
            }
            ui_func_0033c960(self, 0x24, x, y, item_alpha);
        }
    }
}

// DECOMP_FUNC(0x002bdeb8, 692)
extern "C" void func_002be4dc(u32 color);
extern "C" s32 ui_func_002c615c(s32 a, s32 b);
extern "C" const s16* camp_func_002bf6d0(u32 a, u32 b);
extern "C" void script_vm_func_002bef14();

extern "C" void ui_func_002bdeb8(s32 val, s32 x, s32 y, u32 show_sign) {
    const s16* layout = nullptr;
    s32 u_val = val;
    s32 first_pos = -1;

    if (show_sign != 0u) {
        if (val > 0) {
            func_002be4dc(0x008400FFu);
        } else if (val == 0) {
            func_002be4dc(0x787878FFu);
        } else {
            func_002be4dc(0xDC0F14FFu);
            u_val = -val;
            func_002be4dc(0xFF0000FFu);
        }
    } else {
        func_002be4dc(0xFFu);
        if (val < 0) {
            u_val = -val;
            func_002be4dc(0xFF0000FFu);
        }
    }

    auto draw_glyph = [&](u32 glyph) {
        ui_func_002bf460(2u, 0xDu, glyph,
                         static_cast<u32>(layout[4] + x),
                         static_cast<u32>(layout[5] + y),
                         0x10u);
    };

    if (u_val == 0) {
        layout = camp_func_002bf6d0(0xEu, 0x5Cu);
        draw_glyph(0u);
    } else {
        const s32 abs_val = (val < 0) ? -val : val;
        s32 div = 100000000;
        for (s32 pos = 0; div > 0; ++pos, div /= 10) {
            if (abs_val >= div) {
                if (first_pos < 0) {
                    first_pos = pos;
                }
                const s32 digit = ui_func_002c615c(u_val, div);
                layout = camp_func_002bf6d0(0xEu, static_cast<u32>(0x64 - pos));
                draw_glyph(static_cast<u32>(digit));
                u_val -= div * digit;
                if (pos == 2) {
                    layout = camp_func_002bf6d0(0xEu, 0x67u);
                    draw_glyph(0xCu);
                } else if (pos == 5) {
                    layout = camp_func_002bf6d0(0xEu, 0x66u);
                    draw_glyph(0xCu);
                }
            }
        }
    }

    if (show_sign != 0u) {
        if (first_pos >= 0) {
            layout = camp_func_002bf6d0(0xEu, static_cast<u32>(0x65 - first_pos));
        }
        if (val < 0) {
            draw_glyph(0xBu);
        } else if (val > 0) {
            draw_glyph(0xAu);
        }
    }

    script_vm_func_002bef14();
}

// DECOMP_FUNC(0x001e4190, 700)
extern "C" void script_vm_func_002aeb2c(u32 a0, u32 a1);
extern "C" void engine_func_002c5ab8(u32 a0, u32 a1);
extern "C" u32 script_vm_func_002c1de4(u32 a0, u32 a1);
extern "C" void ui_func_001a94fc(u32 a0, float s0, float s1, float s2, float s3, float s4, float s5);
extern "C" void func_001e38f8(u32 a0, u32 a1, u32 a2, u32 a3, float s0, float s1,
                              u32 s2, u32 s3, u32 s4, u32 s5, u32 s6,
                              u32 s7, u32 s8, s32 s9, s32 s10);
extern "C" void func_0025b98c();

static inline u32 f32_bits_1e4190(float v) {
    u32 u;
    __builtin_memcpy(&u, &v, sizeof(u));
    return u;
}

extern "C" void script_vm_func_001e4190(u32 a0, s32 a1) {
    const s32 r2 = (a1 == 0) ? 0 : ((a1 > 1) ? a1 : 0xF);
    u32* const g7 = reinterpret_cast<u32*>(0x00448C58u);
    u8* const g6 = reinterpret_cast<u8*>(0x0049F91Cu);

    g7[0x2C / 4] = a0;
    if (g6[0x228] != 0u) {
        g7[0x2C / 4] = 0u;
    }

    const u32 idx = g7[0x2C / 4];
    *reinterpret_cast<u32*>(g6 + 0x390) = idx;
    const u8* const entry = *reinterpret_cast<const u8* const*>(0x00448C58u) + idx * 0x30u;

    const s32 e0 = *reinterpret_cast<const s16*>(entry + 0);
    const s32 e2 = *reinterpret_cast<const s16*>(entry + 2);
    const s32 e4 = *reinterpret_cast<const s16*>(entry + 4);
    const s32 e6 = *reinterpret_cast<const s16*>(entry + 6);

    *reinterpret_cast<s32*>(g6 + 0x398) = e0;
    *reinterpret_cast<s32*>(g6 + 0x39C) = e2;
    *reinterpret_cast<s32*>(g6 + 0x3A0) = e4;
    *reinterpret_cast<s32*>(g6 + 0x3A4) = e6;

    if (r2 == 0) {
        *reinterpret_cast<float*>(g7 + 0x20 / 4) = 1.0f;
        g7[0x1C / 4] = static_cast<u32>(e0);
        *reinterpret_cast<float*>(g7 + 0x24 / 4) = 1.0f;
        g7[0x18 / 4] = static_cast<u32>(e0);
    } else {
        *reinterpret_cast<float*>(g7 + 0x20 / 4) = 0.0f;
        g7[0x1C / 4] = g7[0x18 / 4];
        *reinterpret_cast<float*>(g7 + 0x24 / 4) = static_cast<float>(r2);
        g7[0x18 / 4] = static_cast<u32>(e0);
    }

    s32* const table = reinterpret_cast<s32*>(g7[1]);
    table[e0 * 73] = e6;

    if (g7[0x30 / 4] != 0u) {
        script_vm_func_002aeb2c(0x38u, g7[0x34 / 4]);
        g7[0x30 / 4] = 0u;
    }

    g7[0x34 / 4] = (e0 > 0x31) ? 0u : static_cast<u32>(e0);
    engine_func_002c5ab8(0x38u, g7[0x34 / 4]);
    g7[0x30 / 4] = script_vm_func_002c1de4(0x38u, g7[0x34 / 4]);

    g7[0x0C / 4] = static_cast<u32>(e2);
    *reinterpret_cast<float*>(g7 + 0x10 / 4) = 0.0f;
    g7[0x14 / 4] = 0u;
    g7[0x3C / 4] = static_cast<u32>(e6);
    g7[0x28 / 4] = static_cast<u32>(e4);

    const float inv255 = 1.0f / 255.0f;
    ui_func_001a94fc(
        entry[8],
        static_cast<float>(entry[9]) * inv255,
        static_cast<float>(entry[10]) * inv255,
        static_cast<float>(entry[11]) * inv255,
        static_cast<float>(*reinterpret_cast<const s16*>(entry + 0xC)) * 100.0f,
        static_cast<float>(*reinterpret_cast<const s16*>(entry + 0xE)) * 100.0f,
        *reinterpret_cast<const float*>(entry + 0x10));

    func_001e38f8(
        0u, entry[0x14], entry[0x15], entry[0x16],
        static_cast<float>(*reinterpret_cast<const s16*>(entry + 0x1A)),
        *reinterpret_cast<const float*>(entry + 0x1C),
        entry[0x17], entry[0x18], entry[0x19], entry[0x20], entry[0x21],
        entry[0x22], entry[0x23],
        *reinterpret_cast<const s16*>(entry + 0x24),
        *reinterpret_cast<const s16*>(entry + 0x26));

    *reinterpret_cast<u32*>(g6 + 0x3A8) = entry[0x28];
    const s32 s2a = static_cast<s8>(entry[0x2A]);
    *reinterpret_cast<s32*>(g6 + 0x3AC) = s2a;
    *reinterpret_cast<s32*>(g6 + 0x3B0) = (s2a * 3) / 5;
    *reinterpret_cast<u32*>(g6 + 0x3B4) = entry[0x2B];
    *reinterpret_cast<u32*>(g6 + 0x3B8) = entry[0x2C];
    *reinterpret_cast<u32*>(g6 + 0x3BC) = entry[0x29];
    *reinterpret_cast<u32*>(g6 + 0x3C0) = entry[0x2D];
    *reinterpret_cast<u32*>(g6 + 0x3C4) = entry[0x2E];
    *reinterpret_cast<u32*>(g6 + 0x3C8) = entry[0x2F];

    float ang = static_cast<float>(*reinterpret_cast<const s16*>(entry + 0x1A)) + 180.0f;
    float* const g_f8fc = reinterpret_cast<float*>(0x0049F8F8u + 4u);
    *g_f8fc = ang;
    if (static_cast<s32>(f32_bits_1e4190(ang)) > 0x43B40000) {
        ang -= 360.0f;
        *g_f8fc = ang;
    }

    g7[0x38 / 4] = 0u;
    func_0025b98c();
}

// DECOMP_FUNC(0x003661c0, 708)
extern "C" void battle_func_003e3afc(u32 a0, u8* fbc, float* scale, u8* f4c, const void* sp0, const void* sp4);
extern "C" void func_0023d368(u8* f8c, u8* fbc, u8* f7c);
extern "C" u32 engine_func_002acbd8();
extern "C" void battle_func_002c00b4(u8* mtx, u32 val);

static inline u32 f32_bits_3661c0(float v) {
    u32 u;
    __builtin_memcpy(&u, &v, sizeof(u));
    return u;
}

extern "C" void engine_func_003661c0(u8* self, u32 a1, u32 a2) {
    u32* const f88 = reinterpret_cast<u32*>(self + 0x88);
    u32* const f38 = reinterpret_cast<u32*>(self + 0x38);

    if ((*f88 & 1u) == 0u) {
        *f38 &= ~2u;
    } else if ((*f38 & 2u) != 0u) {
        u8* const obj = *reinterpret_cast<u8* const*>(self + 0x0C);
        const void* sp0 = nullptr;
        const void* sp4 = nullptr;

        if (obj != nullptr) {
            using Fn18 = const void* (*)(u8*);
            using Fn1C = const void* (*)(u8*);
            sp0 = (*reinterpret_cast<Fn18* const*>(obj))[0x18 / 4](obj);
            sp4 = (*reinterpret_cast<Fn1C* const*>(obj))[0x1C / 4](obj);
        } else {
            u32* const guard = reinterpret_cast<u32*>(0x00476640u);
            u8* const def_mtx = reinterpret_cast<u8*>(0x004EFDF4u);
            for (s32 pass = 0; pass < 2; ++pass) {
                if ((*guard & 1u) == 0u && engine_func_002c00d4(guard) != 0u) {
                    battle_func_002c00b4(def_mtx, engine_func_002acbd8());
                    *reinterpret_cast<float*>(def_mtx + 0x30) = 1.0f;
                    *reinterpret_cast<float*>(def_mtx + 0x34) = 1.0f;
                    *reinterpret_cast<float*>(def_mtx + 0x38) = 1.0f;
                    *reinterpret_cast<u32*>(def_mtx + 0x3C) = 0x7E1u;
                }
            }
            sp0 = def_mtx;
            sp4 = def_mtx;
        }

        u8* const fbc = self + 0xBC;
        u8* const f4c = self + 0x4C;
        u8* const f8c = self + 0x8C;
        float scale[3];
        battle_func_003e3afc(a1, fbc, scale, f4c, sp0, sp4);

        const float len2 = scale[0] * scale[0] + scale[1] * scale[1] + scale[2] * scale[2];
        if (static_cast<s32>(f32_bits_3661c0(len2)) < 0x358637BE) {
            float eps;
            const u32 eps_bits = 0x358637BEu;
            __builtin_memcpy(&eps, &eps_bits, sizeof(eps));
            scale[0] = (scale[0] < 0.0f) ? -eps : eps;
            scale[1] = (scale[1] < 0.0f) ? -eps : eps;
            scale[2] = (scale[2] < 0.0f) ? -eps : eps;
        }

        *reinterpret_cast<float*>(fbc + 0x30) = scale[0];
        *reinterpret_cast<float*>(fbc + 0x34) = scale[1];
        *reinterpret_cast<float*>(fbc + 0x38) = scale[2];
        func_0023d368(f8c, fbc, f4c + 0x30);

        u32* const f3c = reinterpret_cast<u32*>(fbc + 0x3C);
        *f3c &= ~0x7E0u;
        if ((*f3c & 8u) == 0u) {
            *f3c &= ~0x600u;
            const float sx = *reinterpret_cast<const float*>(fbc + 0x30);
            const float sy = *reinterpret_cast<const float*>(fbc + 0x34);
            const float sz = *reinterpret_cast<const float*>(fbc + 0x38);
            if (sx == sy && sx == sz) {
                *f3c |= 0x400u;
                if (f32_bits_3661c0(sx) == 0x3F800000u) {
                    *f3c |= 0x200u;
                }
            }
        }

        self[0x12C] = 0u;
    }

    using Fn28 = void (*)(u8*);
    (*reinterpret_cast<Fn28* const*>(self))[0x28 / 4](self);

    *f88 &= ~0x800u;
    u8* const list = *reinterpret_cast<u8* const*>(self + 0x130);
    u8** it = *reinterpret_cast<u8***>(list + 8);
    u8** const end = *reinterpret_cast<u8***>(list + 0xC);
    for (; it != end; ++it) {
        u8* const child = *it;
        using FnChild = void (*)(u8*, u8*, u32);
        (*reinterpret_cast<FnChild* const*>(child))[0](child, self, a2);
    }
}

// DECOMP_FUNC(0x0013a62c, 712)
extern "C" void engine_func_002c5ff4(u32 a0, u8* a1, u32 size);
extern "C" void func_00139b64(u32 a0, const u16* a1, u32 size);
extern "C" void func_0014672c(u32 a0);
extern "C" void engine_func_002c3aa8(void* a0);
extern "C" s32 engine_func_002c42fc(u32* out_idx, u32* handles, s32 count, u32 wait_all, s64 timeout);
extern "C" void engine_func_002c5468(s32 err);
extern "C" void engine_func_002c3a24(void* a0);
extern "C" void func_00146758(u32 a0, void* dst, u32 size, u32* out_len);
extern "C" void func_001467ac(u32 id, void* dst);

extern "C" void engine_func_0013a62c(u8* self, s32 a1) {
    if (self[0x1318] != 0u) {
        return;
    }

    u16 sp30[2] = {0u, 0u};
    if (a1 == 0) {
        sp30[0] = 0u;
    } else {
        sp30[0] = 2u;
        engine_func_002c5ff4(*reinterpret_cast<const u32*>(self + 0x10A8), self + 0x18, 0x1080u);
        asm volatile("mcr p15, 0, %0, c7, c10, 4" : : "r"(0u) : "memory");
    }
    func_00139b64(2u, sp30, 4u);

    func_0014672c(0x4000u);
    engine_func_002c3aa8(self + 8);

    u32 sp_a4 = 0u;
    u32 sp_9c = *reinterpret_cast<const u32*>(self + 0);
    const s32 sync_res = engine_func_002c42fc(&sp_a4, &sp_9c, 1, 0u, -1);
    if (sync_res < 0) {
        engine_func_002c5468(sync_res);
    }

    s32 svc19_r0 = *reinterpret_cast<const s32*>(self + 0);
    asm volatile("svc 0x19" : "+r"(svc19_r0) : : "r1", "r2", "r3", "memory");
    if (svc19_r0 < 0) {
        engine_func_002c5468(svc19_r0);
    }

    self[0x1319] = static_cast<u8>(self[0x1319] + 1u);
    engine_func_002c3a24(self + 8);

    u16 sp28 = 0u;
    u32 sp_a0 = 0u;
    func_00146758(2u, &sp28, 2u, &sp_a0);

    u16 sp70[16];
    func_00146758(2u, sp70, (static_cast<u32>(sp28) << 1) & 0xFFFFu, &sp_a0);

    u32 sp10[2] = {0u, 0u};
    u32 sp18[2] = {0u, 0u};
    u32 sp20[2] = {0u, 0u};
    u32 sp90[2] = {0u, 0u};

    void* ptrs[15] = {
        self + 0x1098,
        sp90,
        sp18,
        sp20,
        self + 0x10A0,
        self + 0x10A8,
        self + 0x1300,
        sp10,
        self + 0x1308,
        self + 0x1310,
        self + 0x1584,
        self + 0x158C,
        self + 0x1594,
        self + 0x159C,
        self + 0x15A4,
    };

    for (s32 i = 0; i < static_cast<s32>(sp28); ++i) {
        func_001467ac(sp70[i], ptrs[i]);
        func_001467ac(static_cast<u32>(sp70[i]) | 0x10000u, static_cast<u8*>(ptrs[i]) + 4);
    }

    *reinterpret_cast<u32*>(self + 0x12F0) = sp10[0];
    *reinterpret_cast<u32*>(self + 0x12F4) = sp10[0] + 0xA00u;
    *reinterpret_cast<u32*>(self + 0x12F8) = sp10[1];
    *reinterpret_cast<u32*>(self + 0x12FC) = sp10[1] + 0xA00u;

    for (s32 i = 0; i < 0x18; ++i) {
        u8* const base = self + i * 4 + 0x1000;
        *reinterpret_cast<u32*>(base + 0x0B0) = sp90[0] + static_cast<u32>(i) * 0xC0u;
        *reinterpret_cast<u32*>(base + 0x170) = sp18[0] + static_cast<u32>(i) * 0x0Cu;
        *reinterpret_cast<u32*>(base + 0x230) = sp20[0] + static_cast<u32>(i) * 0x20u;
        *reinterpret_cast<u32*>(base + 0x110) = sp90[1] + static_cast<u32>(i) * 0xC0u;
        *reinterpret_cast<u32*>(base + 0x1D0) = sp18[1] + static_cast<u32>(i) * 0x0Cu;
        *reinterpret_cast<u32*>(base + 0x290) = sp20[1] + static_cast<u32>(i) * 0x20u;
    }

    func_0014672c(0x4000u);
    self[0x1319] = 0u;
    *reinterpret_cast<u16*>(self + 0x131A) = 4u;
    **reinterpret_cast<u16**>(self + 0x1098) = 4u;
    *reinterpret_cast<u16*>(self + 0x131A) = static_cast<u16>(*reinterpret_cast<const u16*>(self + 0x131A) + 1u);

    s32 svc18_r0 = *reinterpret_cast<const s32*>(self + 4);
    asm volatile("svc 0x18" : "+r"(svc18_r0) : : "r1", "r2", "r3", "memory");
    if (svc18_r0 < 0) {
        engine_func_002c5468(svc18_r0);
    }

    const u16 parity = *reinterpret_cast<const u16*>(self + 0x131A) & 1u;
    *reinterpret_cast<u16*>(self + 0x131E) = parity;
    *reinterpret_cast<u16*>(self + 0x131C) = parity;
    self[0x1318] = 1u;
}

// DECOMP_FUNC(0x00240158, 712)
extern "C" void ui_func_002bcf58(void* dst, const void* src, u32 size);
extern "C" void func_0033a250(void* ctx);
extern "C" void func_0033a06c(void* ctx);

extern "C" void script_vm_func_00240158(u32* self, u8* ctx) {
    const u8* const hdr = reinterpret_cast<const u8*>(self[1]);
    if (hdr == nullptr) {
        return;
    }

    u32* const f44a0 = reinterpret_cast<u32*>(ctx + 0x44A0);
    if ((*f44a0 & 0x200u) == 0u && hdr[0xA] == 1u) {
        const s32 ver = static_cast<s8>(hdr[4]) * 1000 +
                        static_cast<s8>(hdr[5]) * 100 +
                        static_cast<s8>(hdr[6]) * 10 +
                        static_cast<s8>(hdr[7]) - 0xD050;
        const u16 off8 = *reinterpret_cast<const u16*>(hdr + 8);
        const u32 total_sz = *reinterpret_cast<const u32*>(hdr + 0xC);
        const u8* src_ptr = hdr + off8;

        float* const f1ea4 = reinterpret_cast<float*>(ctx + 0x1EA4);
        for (s32 i = 0; i < 6; ++i) {
            f1ea4[i] = 0.0f;
        }
        *reinterpret_cast<u32*>(ctx + 0x1EBC) = 0u;

        if (ver == 0x44C) {
            ui_func_002bcf58(ctx + 0x1EA4, src_ptr, 0x118u);
            src_ptr += 0x118;
        }

        const u32 rem = total_sz - 0x118u;
        const u32 max_slots = static_cast<u32>((static_cast<u64>(rem) * 0xAAAAAAABull) >> 36);
        const s32 cap = static_cast<s32>(ctx[0x1E9D]);
        const u32 n = (cap < static_cast<s32>(max_slots)) ? static_cast<u32>(cap) : max_slots;
        ui_func_002bcf58(*reinterpret_cast<void* const*>(ctx + 0x1FBC), src_ptr, n * 0x18u);
    }

    func_0033a250(ctx);
    func_0033a06c(ctx);
    func_003d7228(*reinterpret_cast<void* const*>(0x004342C8u));

    if (ctx[0x44B7] == 0u &&
        ((*reinterpret_cast<const u32*>(ctx + 0xE0) & 0x02000000u) != 0u || (*f44a0 & 2u) != 0u)) {
        for (s32 i = 4; i < 0x36; ++i) {
            u8* const e = (*reinterpret_cast<u8* const*>(ctx + 0x1E98)) + i * 0x114u;
            const u32 w50 = *reinterpret_cast<const u32*>(e + 0x50);
            if ((w50 & 1u) != 0u && (w50 & 2u) != 0u) {
                const u32 w54 = *reinterpret_cast<const u32*>(e + 0x54);
                if ((w54 & 8u) != 0u) {
                    *reinterpret_cast<u32*>(e + 0x54) = w54 & ~8u;
                    if ((*reinterpret_cast<const u16*>(e + 0x58) & 0x800u) == 0u) {
                        const u8* const unit = ui_func_0027dca0(ctx, *reinterpret_cast<const s16*>(e + 0x62));
                        if (func_002406f8(ctx, *reinterpret_cast<const u16*>(unit + 2)) == 0u) {
                            *reinterpret_cast<u16*>(e + 0x58) |= 0x800u;
                        }
                    }
                }
            }
        }
        battle_func_00250800(0u, 0u, 0x0100017Bu, 0u, 0u, 0u, 0u);
    }

    self[0] = 0xDu;
    if ((*f44a0 & 0x40000000u) == 0u) {
        script_vm_func_00270298(2u);
        *f44a0 |= 0x40000000u;
    }
    if (script_vm_func_002c2bd0(0u) == 3u) {
        script_vm_func_002c2ba4(0u, 0xAu, 0xFFu);
    }
    if (script_vm_func_002c2bd0(1u) == 3u) {
        script_vm_func_002c2ba4(1u, 0xAu, 0xFFu);
    }
    if (script_vm_func_00289924() != 0u) {
        self[0] = 0xEu;
        self[3] = 0u;
        battle_func_0023fd38(self, ctx);
    }
}

// DECOMP_FUNC(0x00348188, 712)
extern "C" void func_0023e55c(float* dst, const float* src, const float* scale);

static inline u32 f32_bits_348188(float v) {
    u32 u;
    __builtin_memcpy(&u, &v, sizeof(u));
    return u;
}

static inline void sincos_lut_348188(float deg_scaled, float& out_s, float& out_c) {
    const s32 neg = (deg_scaled < 0.0f) ? 1 : 0;
    float a = (deg_scaled < 0.0f) ? -deg_scaled : deg_scaled;
    while (static_cast<s32>(f32_bits_348188(a)) >= 0x47800000) {
        a -= 65536.0f;
    }
    const u16 u = static_cast<u16>(static_cast<u32>(a));
    const u32 idx = u & 0xFFu;
    const float frac = a - static_cast<float>(u);
    const float* const entry = reinterpret_cast<const float*>(0x00407FC0u) + idx * 4u;
    float s = entry[0] + frac * entry[2];
    const float c = entry[1] + frac * entry[3];
    if (neg != 0) {
        s = -s;
    }
    out_s = s;
    out_c = c;
}

extern "C" void func_00348188(u8* self) {
    u8* const obj14 = *reinterpret_cast<u8* const*>(self + 0x14);
    using Fn8 = void (*)(u8*);
    (*reinterpret_cast<Fn8* const*>(obj14))[8 / 4](obj14);

    const s32 n = *reinterpret_cast<const s32*>(*reinterpret_cast<const u8* const*>(self + 0x60));
    if (n + 1 > 0) {
        for (s32 i = 0; i < n + 1; ++i) {
            u8* const arr = *reinterpret_cast<u8* const*>(self + 4);
            const u8* const cfg = *reinterpret_cast<const u8* const*>(self + 0x60);
            *reinterpret_cast<float*>(arr + i * 20 + 0x0C) += *reinterpret_cast<const float*>(cfg + 0x30);
            *reinterpret_cast<float*>(arr + i * 20 + 0x10) += *reinterpret_cast<const float*>(cfg + 0x34);
        }
    }

    const u8* const cfg = *reinterpret_cast<const u8* const*>(self + 0x60);
    float ang = *reinterpret_cast<const float*>(self + 0x58) + *reinterpret_cast<const float*>(cfg + 0x38);
    *reinterpret_cast<float*>(self + 0x58) = ang;
    if (static_cast<s32>(f32_bits_348188(ang)) >= 0x43B40000) {
        ang -= 360.0f;
        *reinterpret_cast<float*>(self + 0x58) = ang;
    } else if (ang < 0.0f) {
        ang += 360.0f;
        *reinterpret_cast<float*>(self + 0x58) = ang;
    }

    float sx, cx, sy, cy, sz, cz;
    sincos_lut_348188(0.0f, sx, cx);
    sincos_lut_348188(0.0f, sy, cy);
    sincos_lut_348188(ang * (256.0f / 360.0f), sz, cz);

    float* const m = reinterpret_cast<float*>(self + 0x18);
    m[0] = cz * cy;
    m[1] = (sx * cz) * sy - (cx * sz);
    m[2] = (sx * sz) + (cx * cz) * sy;
    m[3] = 0.0f;
    m[4] = sz * cy;
    m[5] = (cx * cz) + (sx * sz) * sy;
    m[6] = (cx * sz) * sy - (sx * cz);
    m[7] = 0.0f;
    m[8] = -sy;
    m[9] = sx * cy;
    m[10] = cx * cy;
    m[11] = 0.0f;
    m[12] = 0.0f;
    m[13] = 0.0f;
    m[14] = 0.0f;
    m[15] = 1.0f;

    const float sc = *reinterpret_cast<const float*>(self + 0x5C) + *reinterpret_cast<const float*>(cfg + 0x3C);
    *reinterpret_cast<float*>(self + 0x5C) = sc;
    const float v[3] = {sc, sc, 1.0f};
    func_0023e55c(m, m, v);
}

// DECOMP_FUNC(0x00266e88, 724)
static inline u32 f32_bits_266e88(float v) {
    u32 u;
    __builtin_memcpy(&u, &v, sizeof(u));
    return u;
}

static inline float vsqrt_266e88(float x) {
    float r;
    asm("vsqrt.f32 %0, %1" : "=t"(r) : "t"(x));
    return r;
}

static inline float vabs_266e88(float x) {
    float r;
    asm("vabs.f32 %0, %1" : "=t"(r) : "t"(x));
    return r;
}

extern "C" s32 script_vm_func_00266e88(const float* p0, const float* p1, float* out_pos) {
    const u8* const g_sl = reinterpret_cast<const u8*>(0x00446FE8u);
    s32 hit = -1;

    float cur_x = p0[0];
    float cur_y = p0[1];
    float cur_z = p0[2];
    float p1_x = p1[0];
    float p1_y = p1[1];
    float p1_z = p1[2];

    for (s32 pass = 0; pass < 3; ++pass) {
        const u8* arr;
        s32 count;
        float radius;

        if (pass == 0) {
            arr = reinterpret_cast<const u8*>(0x00493C5Cu);
            count = *reinterpret_cast<const s32*>(g_sl + 0x14);
            radius = 28.0f;
            if (hit == -1) {
                const float dx = cur_x - p1_x;
                const float dy = cur_y - p1_y;
                const float dz = cur_z - p1_z;
                const float inv_len = 1.0f / vsqrt_266e88(dx * dx + dy * dy + dz * dz);
                cur_x += (dx * inv_len) * radius;
                cur_y += (dy * inv_len) * radius;
                cur_z += (dz * inv_len) * radius;
            }
        } else if (pass == 1) {
            arr = *reinterpret_cast<const u8* const*>(g_sl + 0x20);
            count = *reinterpret_cast<const s32*>(g_sl + 0x0C);
            radius = 8.0f;
            if (hit == -1) {
                const float a0 = p0[0];
                const float a1 = p0[1];
                const float a2 = p0[2];
                p1_x = p1[0];
                p1_y = p1[1];
                p1_z = p1[2];
                const float dx = a0 - p1_x;
                const float dy = a1 - p1_y;
                const float dz = a2 - p1_z;
                const float inv_len = 1.0f / vsqrt_266e88(dx * dx + dy * dy + dz * dz);
                cur_x = a0 + (dx * inv_len) * radius;
                cur_y = a1 + (dy * inv_len) * radius;
                cur_z = a2 + (dz * inv_len) * radius;
            }
        } else {
            arr = *reinterpret_cast<const u8* const*>(g_sl + 0x24);
            count = *reinterpret_cast<const s32*>(g_sl + 0x10);
            radius = 8.0f;
        }

        for (s32 i = 0; i < count; ++i, arr += 0xA8) {
            if (arr[8] == 0u) {
                continue;
            }
            if (pass == 0 && arr[9] != 3u) {
                continue;
            }

            const float sx = cur_x;
            const float sy = cur_y;
            const float sz = cur_z;

            const float nx = *reinterpret_cast<const float*>(arr + 0x0C);
            const float ny = *reinterpret_cast<const float*>(arr + 0x10);
            const float nz = *reinterpret_cast<const float*>(arr + 0x14);
            const float pd = *reinterpret_cast<const float*>(arr + 0x18);

            const float d0 = sx * nx + sy * ny + sz * nz - pd;
            const float d1 = p1_x * nx + p1_y * ny + p1_z * nz - pd;

            if (!((d0 < 0.0f && d1 >= 0.0f) || (d0 >= 0.0f && d1 < 0.0f))) {
                continue;
            }

            const float ad0 = vabs_266e88(d0);
            const float ad1 = vabs_266e88(d1);
            const float denom = ad0 + ad1;
            const float vx = p1_x - sx;
            const float vy = p1_y - sy;
            const float vz = p1_z - sz;
            const float t = ad0 / denom;

            const float res = func_0024bd60(
                static_cast<s8>(arr[4]),
                static_cast<s8>(arr[5]),
                arr,
                sx + vx * t,
                sy + vy * t,
                sz + vz * t,
                radius);
            if (res < 0.0f) {
                continue;
            }

            const float t2 = (ad0 + res) / denom;
            if (static_cast<s32>(f32_bits_266e88(t2)) < 0x3F800000) {
                cur_x = sx + vx * t2;
                cur_y = sy + vy * t2;
                cur_z = sz + vz * t2;
            } else {
                cur_x = p1_x + vx * (-24.0f);
                cur_y = p1_y + vy * (-24.0f);
                cur_z = p1_z + vz * (-24.0f);
            }
            hit = i;
        }
    }

    if (hit == -1) {
        out_pos[0] = p0[0];
        out_pos[1] = p0[1];
        out_pos[2] = p0[2];
    } else {
        out_pos[0] = cur_x;
        out_pos[1] = cur_y;
        out_pos[2] = cur_z;
    }
    return hit;
}

// DECOMP_FUNC(0x002eef44, 728)
extern "C" s32 engine_func_00296f60(u32 idx);
extern "C" void battle_func_002ad6d8(float* dst, const float* mtx, const float* src);
extern "C" void script_vm_func_0027fe84(u32 mode);
extern "C" void script_vm_func_0027fd08(u32 id);
extern "C" void script_vm_func_00273ab0(u32 flag);

extern "C" u32 engine_func_002eef44() {
    const float p0 = static_cast<float>(engine_func_00296f60(0u));
    const float p1 = static_cast<float>(engine_func_00296f60(1u));
    const float p2 = static_cast<float>(engine_func_00296f60(2u));
    const float p3 = static_cast<float>(engine_func_00296f60(3u));

    float sx, cx, sy, cy, sz, cz;
    sincos_lut_348188(0.0f, sx, cx);
    sincos_lut_348188(p3 * (256.0f / 360.0f), sy, cy);
    sincos_lut_348188(0.0f, sz, cz);

    float m[12];
    m[0] = cz * cy;
    m[1] = (sx * cz) * sy - (cx * sz);
    m[2] = (sx * sz) + (cx * cz) * sy;
    m[3] = 0.0f;
    m[4] = sz * cy;
    m[5] = (cx * cz) + (sx * sz) * sy;
    m[6] = (cx * sz) * sy - (sx * cz);
    m[7] = 0.0f;
    m[8] = -sy;
    m[9] = sx * cy;
    m[10] = cx * cy;
    m[11] = 0.0f;

    float vec[3] = {0.0f, 0.0f, -1.0f};
    battle_func_002ad6d8(vec, m, vec);

    vec[0] = p0 - vec[0] * 500.0f;
    vec[1] = p1 - vec[1] * 500.0f;
    vec[2] = p2 - vec[2] * 500.0f;

    u8* const cam = reinterpret_cast<u8*>(0x0049F91Cu);
    *reinterpret_cast<float*>(cam + 0xC4) = vec[0];
    *reinterpret_cast<float*>(cam + 0xC8) = vec[1];
    *reinterpret_cast<float*>(cam + 0xCC) = vec[2];
    *reinterpret_cast<float*>(cam + 0xD0) = p0;
    *reinterpret_cast<float*>(cam + 0xD4) = p1;
    *reinterpret_cast<float*>(cam + 0xD8) = p2;
    *reinterpret_cast<float*>(cam + 0xDC) = 40.0f;

    u8* const st = *reinterpret_cast<u8* const*>(0x004474F4u);
    if (*reinterpret_cast<const u32*>(st) != 3u) {
        st[0xA4] = 1u;
        script_vm_func_0027fe84(3u);
        script_vm_func_0027fd08(0x1Du);
    }

    script_vm_func_00273ab0(1u);
    return 1u;
}

// DECOMP_FUNC(0x00352d98, 740)
extern "C" s32 func_003538d4(u8* self, u32 a1, u32 a2);
extern "C" u32 func_003538b8(u8* self);
extern "C" u32 func_003538c4(u8* self);
extern "C" void func_0035334c();
extern "C" void func_0023a3a4(const char* s);
extern "C" void func_003532a8(u8 flag);
extern "C" s32 func_0035fad8(u32 a1, u32 a2, const void* fp, u32 a3_4,
                              u32 s0, u32 s1, u32 s2, u32 s3, u32 s4,
                              u32 s5, u32 s6, u32 s7, u32 s8, u32 s9,
                              u32 s10, u32 s11, u32 s12, u32 s13, u32 s14);
extern "C" s32 engine_func_002b45f8(const char* a, const char* b, u32 max_len);
extern "C" u32 script_vm_func_002c607c(const char* s, char** endptr, s32 base);
extern "C" s32 func_0035382c(u8* self, const u32* pair, u16 code);

extern "C" s32 engine_func_00352d98(u8* self, u32 a1, u32 a2, const u8* a3) {
    const s32 r0 = func_003538d4(self, *reinterpret_cast<const u32*>(a3 + 0x10),
                                 *reinterpret_cast<const u32*>(a3 + 0x14));
    if (r0 < 0) {
        return r0;
    }

    const u32 v_38b8 = func_003538b8(self);
    const u32 v_38c4 = func_003538c4(self);
    func_0035334c();
    func_0023a3a4("Prices");
    func_0023a3a4("Ratings");
    func_0023a3a4("NewSince");
    func_0023a3a4("TitleVersion");
    func_0023a3a4("sys.ItemCode");
    func_003532a8(a3[0x28]);

    const void* const fp = (*reinterpret_cast<const u32*>(a3 + 0) != 0u)
        ? reinterpret_cast<const void*>(*reinterpret_cast<const u32*>(a3 + 0))
        : a3;
    const u32 r0_8 = (*reinterpret_cast<const u32*>(a3 + 8) != 0u)
        ? *reinterpret_cast<const u32*>(a3 + 8)
        : reinterpret_cast<u32>(a3);
    const u32 r1_18 = (*reinterpret_cast<const u32*>(a3 + 0x18) != 0u)
        ? *reinterpret_cast<const u32*>(a3 + 0x18)
        : reinterpret_cast<u32>(a3);
    const u32 r8_flag = (*reinterpret_cast<const u32*>(a3 + 0x18) != 0u) ? 1u : 0u;

    const s32 res = func_0035fad8(
        a1, a2, fp, *reinterpret_cast<const u32*>(a3 + 4),
        0x004E655Cu,
        *reinterpret_cast<const u32*>(0x00471A50u),
        r0_8,
        *reinterpret_cast<const u32*>(a3 + 0x0C),
        0x004E675Cu,
        *reinterpret_cast<const u32*>(0x00471A54u),
        v_38b8,
        v_38c4,
        r1_18,
        r8_flag,
        *reinterpret_cast<const u32*>(a3 + 0x2C),
        *reinterpret_cast<const u32*>(a3 + 0x30),
        reinterpret_cast<u32>(self + 4),
        *reinterpret_cast<const u32*>(self + 8),
        *reinterpret_cast<const u32*>(self + 0x0C));
    if (res < 0) {
        return res;
    }

    const u8* const hdr = *reinterpret_cast<const u8* const*>(self + 4);
    if (hdr == nullptr || *reinterpret_cast<const u32*>(hdr + 4) == 0u) {
        return 0;
    }

    for (u32 idx = 0u; ; ++idx) {
        const u8* const cur_hdr = *reinterpret_cast<const u8* const*>(self + 4);
        const u8* const item = (cur_hdr != nullptr && idx <= *reinterpret_cast<const u32*>(cur_hdr + 4))
            ? (*reinterpret_cast<const u8* const*>(cur_hdr) + idx * 0x30u)
            : nullptr;

        const u32 cnt = *reinterpret_cast<const u32*>(item + 0x1C);
        const char* str = nullptr;
        for (u32 k = 0u; k < cnt; ++k) {
            const char* const* const pairs = *reinterpret_cast<const char* const* const*>(item + 0x18);
            if (engine_func_002b45f8(pairs[k * 2u], "TitleVersion", 0x40u) == 0) {
                str = pairs[k * 2u + 1u];
                break;
            }
        }

        const u16 code = static_cast<u16>(script_vm_func_002c607c(str, nullptr, 10));
        const u32 w0 = *reinterpret_cast<const u32*>(item + 0);
        const u32 w4 = *reinterpret_cast<const u32*>(item + 4);

        const u32 p0 = (((w4 << 24) | (w0 >> 8)) << 12) >> 12;
        u32 lo8;
        if ((w4 >> 14) == 0x10u && static_cast<u16>(w4) == 0x8Cu) {
            lo8 = 0u;
        } else if ((w4 >> 14) == 0x10u && static_cast<u16>(w4) == 0xDu) {
            lo8 = 1u;
        } else {
            lo8 = 0xFFu;
        }
        const u32 hi16 = ((w4 >> 14) == 0x10u) ? 0u : ((w4 << 24) & 0xFFFF0000u);
        const u32 p1 = hi16 | ((w0 << 8) & 0xFF00u) | lo8;

        const u32 out_pair[2] = {p0, p1};
        const s32 sret = func_0035382c(self, out_pair, code);
        if (sret < 0) {
            return sret;
        }

        const u8* const next_hdr = *reinterpret_cast<const u8* const*>(self + 4);
        const u32 next_cnt = (next_hdr != nullptr) ? *reinterpret_cast<const u32*>(next_hdr + 4) : 0u;
        if (idx + 1u >= next_cnt) {
            break;
        }
    }

    return 0;
}

// DECOMP_FUNC(0x00396d24, 740)
extern "C" const u8* script_vm_func_0024f734(u32 id);
extern "C" u32 camp_func_00253634(u32 a0, u32 a1);
extern "C" u8* engine_func_00232c00(u8* self, u32 a1, u32 a2);
extern "C" void engine_func_00232b3c(u8* ent, u32 a1);
extern "C" void func_00232b28(u8* ent, const float* pos);
extern "C" void func_00232b14(u8* ent, const float* rot);
extern "C" void func_00232b00(u8* ent, const float* scl);
extern "C" u32 func_001e2860(u32 id);
extern "C" u32 battle_func_001fa3f4(u32 id);
extern "C" u32 script_vm_func_002c0ba8(u32 id);

static inline u32 f32_bits_396d24(float v) {
    u32 u;
    __builtin_memcpy(&u, &v, sizeof(u));
    return u;
}

static inline float vsqrt_396d24(float x) {
    float r;
    asm("vsqrt.f32 %0, %1" : "=t"(r) : "t"(x));
    return r;
}

extern "C" void engine_func_00396d24(u8* self, u32 mode) {
    const s32 total = *reinterpret_cast<const u16*>(self + 0xA0);
    if (total <= 0) {
        return;
    }

    u16 cand_ids[0x200];
    u16 cand_count = 0u;
    for (s32 i = 0; i < total; ++i) {
        const u16 id = *reinterpret_cast<const u16*>(self + 0xA2 + i * 2);
        bool used = false;
        for (s32 j = 0; j < 0x20; ++j) {
            const u8* const slot = *reinterpret_cast<const u8* const*>(self + 0x18 + j * 4);
            if (slot != nullptr && *reinterpret_cast<const u32*>(slot + 0x20) == id) {
                used = true;
                break;
            }
        }
        if (!used) {
            cand_ids[cand_count] = id;
            cand_count = static_cast<u16>(cand_count + 1u);
        }
    }

    if (cand_count == 0u) {
        return;
    }

    u32 chosen_id = 0u;
    if (mode == 0u) {
        chosen_id = cand_ids[engine_func_002c0bcc(static_cast<u16>(cand_count - 1u))];
    } else if (mode == 1u || mode == 2u) {
        const u8* const ref = *reinterpret_cast<const u8* const*>(0x00447E88u);
        const float px = *reinterpret_cast<const float*>(ref + 0x1C);
        const float py = *reinterpret_cast<const float*>(ref + 0x20);
        const float pz = *reinterpret_cast<const float*>(ref + 0x24);

        u16 filt_ids[0x200];
        u16 filt_count = 0u;
        for (s32 i = 0; i < cand_count; ++i) {
            const u8* const pt = script_vm_func_0024f734(cand_ids[i]);
            const float dx = px - static_cast<float>(*reinterpret_cast<const s16*>(pt + 2));
            const float dy = py - static_cast<float>(*reinterpret_cast<const s16*>(pt + 4));
            const float dz = pz - static_cast<float>(*reinterpret_cast<const s16*>(pt + 6));
            const float dist = vsqrt_396d24(dx * dx + dy * dy + dz * dz);
            const u32 bits = f32_bits_396d24(dist);

            bool keep = false;
            if (mode == 1u) {
                keep = static_cast<u32>(bits - 0x44610001u) < 0x00DA7FFFu;
            } else {
                keep = static_cast<u32>(bits + 0xBC69FFFFu) < 0x01E3FFFFu;
            }
            if (keep) {
                filt_ids[filt_count] = cand_ids[i];
                filt_count = static_cast<u16>(filt_count + 1u);
            }
        }
        if (filt_count == 0u) {
            return;
        }
        chosen_id = filt_ids[engine_func_002c0bcc(static_cast<u16>(filt_count - 1u))];
    }

    const u8* const pt = script_vm_func_0024f734(chosen_id);
    const float pos[3] = {
        static_cast<float>(*reinterpret_cast<const s16*>(pt + 2)),
        static_cast<float>(*reinterpret_cast<const s16*>(pt + 4)),
        static_cast<float>(*reinterpret_cast<const s16*>(pt + 6)),
    };
    const float rot[3] = {0.0f, 0.0f, 0.0f};
    const float scl[3] = {50.0f, 50.0f, 50.0f};

    const u32 r6_val = camp_func_00253634(
        *reinterpret_cast<const u32*>(self + 4),
        *reinterpret_cast<const u32*>(self + 8));
    u8* const ent = engine_func_00232c00(self, 0u, 0u);
    if (ent == nullptr) {
        return;
    }

    engine_func_00232b3c(ent, *reinterpret_cast<const u32*>(self + 0x98));
    func_00232b28(ent, pos);
    func_00232b14(ent, rot);
    func_00232b00(ent, scl);

    *reinterpret_cast<u32*>(ent + 0x1C) = r6_val;
    *reinterpret_cast<u32*>(ent + 0x20) = chosen_id;
    *reinterpret_cast<u32*>(ent + 0x60) = func_001e2860(r6_val);
    *reinterpret_cast<u32*>(ent + 0x64) = battle_func_001fa3f4(r6_val);

    if (script_vm_func_002c0ba8(0x529u) != 0u && mode == 1u) {
        using Fn14 = void (*)(u8*);
        (*reinterpret_cast<Fn14* const*>(ent))[0x14 / 4](ent);
    }
}

// DECOMP_FUNC(0x002d4fe0, 744)
extern "C" void engine_func_002c2b1c();
extern "C" s32 func_00256780();
extern "C" void script_vm_func_0027fbc8(float* x, float* y, s32 pad);
extern "C" void script_vm_func_00264368();
extern "C" float ui_func_002820a4(float x, float y);
extern "C" void script_vm_func_0028277c();
extern "C" float script_vm_func_00282600(float rad);
extern "C" void func_002ed03c();

static inline u32 f32_bits_2d4fe0(float v) {
    u32 u;
    __builtin_memcpy(&u, &v, sizeof(u));
    return u;
}

extern "C" void engine_func_002d4fe0(u8* self) {
    engine_func_002c2b1c();
    const u8* const g8 = reinterpret_cast<const u8*>(0x0049FC1Cu);
    if (g8[0x48] != 0u || *(g8 - 0x300 + 0x18) != 0u) {
        *reinterpret_cast<u32*>(self + 0xD94) = 0u;
        return;
    }

    u8* const player = *reinterpret_cast<u8* const*>(0x00447E88u);
    const float init_x = *reinterpret_cast<const float*>(player + 0x1C);
    const float init_y = *reinterpret_cast<const float*>(player + 0x20);
    const float init_z = *reinterpret_cast<const float*>(player + 0x24);
    *reinterpret_cast<float*>(player + 0x28) = init_x;
    *reinterpret_cast<float*>(player + 0x2C) = init_y;
    *reinterpret_cast<float*>(player + 0x30) = init_z;

    const s32 dash = func_00256780();
    float speed_scale = 1.0f;
    const float d_scaled = static_cast<float>(dash) * 0.01f;
    if (static_cast<s32>(f32_bits_2d4fe0(d_scaled)) > 0x40000000) {
        speed_scale = 2.0f;
    } else if (static_cast<s32>(f32_bits_2d4fe0(d_scaled)) > 0x3F800000) {
        speed_scale = d_scaled;
    }

    float stick_x = 0.0f;
    float stick_y = 0.0f;
    script_vm_func_0027fbc8(&stick_x, &stick_y, 0);
    script_vm_func_00264368();
    *reinterpret_cast<u32*>(self + 0xC0) = 0u;

    const u32 bx = f32_bits_2d4fe0(stick_x);
    const u32 by = f32_bits_2d4fe0(stick_y);
    const bool active = (bx >= 0xBF000000u) || (static_cast<s32>(bx) >= 0x3F000000) ||
                        (by >= 0xBF000000u) || (static_cast<s32>(by) >= 0x3F000000);

    if (!active) {
        const float spd = *reinterpret_cast<const float*>(self + 0x3C) * 0.7f;
        *reinterpret_cast<float*>(self + 0x3C) = spd;
        if (static_cast<s32>(f32_bits_2d4fe0(spd)) < 0x3A83126F) {
            *reinterpret_cast<float*>(self + 0x3C) = 0.0f;
        }
    } else {
        const u32 s3c_bits = *reinterpret_cast<const u32*>(self + 0x3C);
        const float base_spd = (static_cast<s32>(s3c_bits) > 0x3F800000)
            ? *reinterpret_cast<const float*>(self + 0x3C)
            : 1.0f;
        float spd = base_spd + base_spd * 0.7f;
        *reinterpret_cast<float*>(self + 0x3C) = spd;
        if (static_cast<s32>(f32_bits_2d4fe0(spd)) > 0x42700000) {
            spd = 60.0f;
        }
        *reinterpret_cast<float*>(self + 0x3C) = spd;

        const float rad = ui_func_002820a4(stick_x, stick_y);
        float yaw = -(rad * 57.3248405f - *reinterpret_cast<const float*>(self + 0x50));
        if (yaw < 0.0f) {
            yaw += 360.0f;
        }
        if (static_cast<s32>(f32_bits_2d4fe0(yaw)) > 0x43B40000) {
            yaw -= 360.0f;
        }
        *reinterpret_cast<float*>(*reinterpret_cast<u8* const*>(0x00447E88u) + 0x50) = yaw;
        *reinterpret_cast<u32*>(self + 0xC0) = 1u;
    }

    const s32 steps = (static_cast<s32>(*reinterpret_cast<const u32*>(self + 0x3C)) > 0x420C0000) ? 2 : 1;
    s32 col_res = 0;
    const auto sin_fn = reinterpret_cast<float (*)(float)>(script_vm_func_0028277c);
    const auto col_fn = reinterpret_cast<s32 (*)(float*, const float*)>(func_002ed03c);

    for (s32 step = 0; step < steps; ++step) {
        u8* const p = *reinterpret_cast<u8* const*>(0x00447E88u);
        const float prev_pos[3] = {
            *reinterpret_cast<const float*>(p + 0x1C),
            *reinterpret_cast<const float*>(p + 0x20),
            *reinterpret_cast<const float*>(p + 0x24),
        };
        *reinterpret_cast<float*>(p + 0x28) = prev_pos[0];
        *reinterpret_cast<float*>(p + 0x2C) = prev_pos[1];
        *reinterpret_cast<float*>(p + 0x30) = prev_pos[2];

        const float step_dist = (*reinterpret_cast<const float*>(self + 0x3C) / static_cast<float>(steps)) * speed_scale;
        const float sx = sin_fn(*reinterpret_cast<const float*>(p + 0x50) * 0.0174532924f);
        u8* const p2 = *reinterpret_cast<u8* const*>(0x00447E88u);
        *reinterpret_cast<float*>(p2 + 0x28) += sx * step_dist;

        const float cz = script_vm_func_00282600(*reinterpret_cast<const float*>(p2 + 0x50) * 0.0174532924f);
        u8* const p3 = *reinterpret_cast<u8* const*>(0x00447E88u);
        *reinterpret_cast<float*>(p3 + 0x30) += cz * step_dist;

        if (*reinterpret_cast<const u8*>(0x0049FC1Cu + 0xCC) == 0u) {
            col_res = col_fn(reinterpret_cast<float*>(p3 + 0x28), prev_pos);
        }

        u8* const p4 = *reinterpret_cast<u8* const*>(0x00447E88u);
        *reinterpret_cast<float*>(p4 + 0x1C) = (*reinterpret_cast<const float*>(p4 + 0x28) - *reinterpret_cast<const float*>(p4 + 0x1C)) +
                                               *reinterpret_cast<const float*>(p4 + 0x1C);
        *reinterpret_cast<float*>(p4 + 0x24) = (*reinterpret_cast<const float*>(p4 + 0x30) - *reinterpret_cast<const float*>(p4 + 0x24)) +
                                               *reinterpret_cast<const float*>(p4 + 0x24);
        if (col_res != 0) {
            break;
        }
    }

    u8* const pf = *reinterpret_cast<u8* const*>(0x00447E88u);
    *reinterpret_cast<u32*>(pf + 0x4C) = *reinterpret_cast<const u32*>(pf + 0x50);
    *reinterpret_cast<u32*>(pf + 0x40) = *reinterpret_cast<const u32*>(pf + 0x1C);
    *reinterpret_cast<u32*>(pf + 0x44) = *reinterpret_cast<const u32*>(pf + 0x20);
    *reinterpret_cast<u32*>(pf + 0x48) = *reinterpret_cast<const u32*>(pf + 0x24);
    *reinterpret_cast<float*>(pf + 0x34) = init_x;
    *reinterpret_cast<float*>(pf + 0x38) = init_y;
    *reinterpret_cast<float*>(pf + 0x3C) = init_z;
}

// DECOMP_FUNC(0x002aa504, 752)
extern "C" __attribute__((naked)) void script_vm_func_002aa504() {
    asm volatile(
        ".arm\n"
        ".hword 0x4070, 0xe92d, 0x4003, 0xe1a0\n"
        ".hword 0x5002, 0xe1a0, 0x3001, 0xe1a0\n"
        ".hword 0x2000, 0xe1a0, 0x0000, 0xe354\n"
        ".hword 0xc004, 0x11a0, 0xc005, 0x01a0\n"
        ".hword 0xef1c, 0xe16f, 0x0001, 0xe28e\n"
        ".hword 0xc01c, 0xe1a0, 0xe03f, 0x127e\n"
        ".hword 0xe01f, 0x027e, 0x0085, 0x4a00\n"
        ".hword 0x0000, 0xe353, 0x1f13, 0x116f\n"
        ".hword 0x1f12, 0x016f, 0x103f, 0x1271\n"
        ".hword 0x101f, 0x0271, 0x600e, 0xe051\n"
        ".hword 0x0083, 0x4a00, 0x0004, 0x5276\n"
        ".hword 0x0084, 0x5a00, 0x0020, 0xe24e\n"
        ".hword 0x0004, 0xe350, 0xc035, 0xd18c\n"
        ".hword 0xce2c, 0xe1a0, 0x1f8f, 0xe28f\n"
        ".hword 0xc10c, 0xe791, 0x001f, 0xe35e\n"
        ".hword 0xe020, 0x824e, 0x6020, 0xe26e\n"
        ".hword 0x0040, 0x8a00, 0x059c, 0xe081\n"
        ".hword 0x1611, 0xe1a0, 0x1e30, 0xe181\n"
        ".hword 0x0610, 0xe1a0, 0x0000, 0xe270\n"
        ".hword 0x1000, 0xe2e1, 0x019c, 0xe081\n"
        ".hword 0xc001, 0xe08c, 0x059c, 0xe081\n"
        ".hword 0x1611, 0xe1a0, 0x1e30, 0xe181\n"
        ".hword 0x0610, 0xe1a0, 0x0000, 0xe270\n"
        ".hword 0x1000, 0xe2e1, 0x0000, 0xe353\n"
        ".hword 0x019c, 0xe081, 0xc001, 0xe08c\n"
        ".hword 0x0007, 0x0a00, 0x059c, 0xe081\n"
        ".hword 0x1611, 0xe1a0, 0x1e30, 0xe181\n"
        ".hword 0x0610, 0xe1a0, 0x0000, 0xe270\n"
        ".hword 0x1000, 0xe2e1, 0x019c, 0xe081\n"
        ".hword 0xc001, 0xe08c, 0x129c, 0xe080\n"
        ".hword 0x1000, 0xe3a0, 0x039c, 0xe0a1\n"
        ".hword 0x0e30, 0xe1a0, 0x0611, 0xe180\n"
        ".hword 0x6590, 0xe084, 0x1e31, 0xe1a0\n"
        ".hword 0x4591, 0xe024, 0x2006, 0xe052\n"
        ".hword 0x3004, 0xe0c3, 0x0001, 0xe353\n"
        ".hword 0x0005, 0x3152, 0x8070, 0x38bd\n"
        ".hword 0x429c, 0xe086, 0x4000, 0xe3a0\n"
        ".hword 0x639c, 0xe0a4, 0x3000, 0xe3a0\n"
        ".hword 0xc020, 0xe26e, 0x6e36, 0xe1a0\n"
        ".hword 0x6c14, 0xe186, 0x4e34, 0xe1a0\n"
        ".hword 0xe596, 0xe08c, 0x0006, 0xe090\n"
        ".hword 0x1004, 0xe0a1, 0x200e, 0xe042\n"
        ".hword 0x0005, 0xe152, 0x8070, 0x38bd\n"
        ".hword 0x0001, 0xe290, 0x1000, 0xe2a1\n"
        ".hword 0x2005, 0xe042, 0xc005, 0xe052\n"
        ".hword 0x200c, 0x21a0, 0x0000, 0xe2b0\n"
        ".hword 0x1000, 0xe2a1, 0xc005, 0xe052\n"
        ".hword 0x200c, 0x21a0, 0x0000, 0xe2b0\n"
        ".hword 0x1000, 0xe2a1, 0x8070, 0xe8bd\n"
        ".hword 0x159c, 0xe080, 0x1000, 0xe3a0\n"
        ".hword 0x049c, 0xe0a1, 0x1611, 0xe1a0\n"
        ".hword 0x1e30, 0xe181, 0x0610, 0xe1a0\n"
        ".hword 0x0000, 0xe270, 0x1000, 0xe2e1\n"
        ".hword 0x019c, 0xe081, 0xc001, 0xe08c\n"
        ".hword 0x159c, 0xe080, 0x1000, 0xe3a0\n"
        ".hword 0x049c, 0xe0a1, 0x1611, 0xe1a0\n"
        ".hword 0x1e30, 0xe181, 0x0610, 0xe1a0\n"
        ".hword 0x0000, 0xe270, 0x1000, 0xe2e1\n"
        ".hword 0x019c, 0xe081, 0xc001, 0xe08c\n"
        ".hword 0xc001, 0xe24c, 0x129c, 0xe080\n"
        ".hword 0x1000, 0xe3a0, 0x039c, 0xe0a1\n"
        ".hword 0x0e31, 0xe1a0, 0x6590, 0xe081\n"
        ".hword 0x2006, 0xe052, 0x1490, 0xe021\n"
        ".hword 0x3001, 0xe0c3, 0x0004, 0xe153\n"
        ".hword 0x0005, 0x0152, 0x1000, 0x33a0\n"
        ".hword 0x8070, 0x38bd, 0x629c, 0xe081\n"
        ".hword 0x6000, 0xe3a0, 0x139c, 0xe0a6\n"
        ".hword 0x1000, 0xe3a0, 0x6e36, 0xe1a0\n"
        ".hword 0xe596, 0xe08c, 0x0006, 0xe080\n"
        ".hword 0x200e, 0xe052, 0xc496, 0xe02e\n"
        ".hword 0x300e, 0xe0c3, 0x0004, 0xe153\n"
        ".hword 0x0005, 0x0152, 0x8070, 0x38bd\n"
        ".hword 0x0001, 0xe280, 0x2005, 0xe052\n"
        ".hword 0x3004, 0xe0c3, 0x8070, 0xe8bd\n"
        ".hword 0x000c, 0xe92d, 0x1000, 0xe3a0\n"
        ".hword 0x0000, 0xe3a0, 0x9f60, 0xebfa\n"
        ".hword 0x807c, 0xe8bd, 0x1000, 0xe3a0\n"
        ".hword 0x0000, 0xe3a0, 0x8070, 0xe8bd\n"
        ".hword 0xe020, 0xe266, 0x0000, 0xe3a0\n"
        ".hword 0x1000, 0xe3a0, 0x4614, 0xe1a0\n"
        ".hword 0x4e35, 0xe184, 0x5615, 0xe1a0\n"
        ".hword 0xe005, 0xe052, 0xc004, 0xe0d3\n"
        ".hword 0x0000, 0xe0a0, 0x300c, 0x21a0\n"
        ".hword 0x200e, 0x21a0, 0x6001, 0xe256\n"
        ".hword 0x8070, 0x38bd, 0x40a4, 0xe1b0\n"
        ".hword 0x5065, 0xe1a0, 0xfff5, 0xeaff\n"
        ".hword 0xf0f0, 0xf0f0, 0x38e3, 0xe38e\n"
        ".hword 0x35e5, 0xd794, 0xcccc, 0xcccc\n"
        ".hword 0x30c3, 0xc30c, 0x8ba2, 0xba2e\n"
        ".hword 0x42c8, 0xb216, 0xaaaa, 0xaaaa\n"
        ".hword 0x0a3d, 0xa3d7, 0xd89d, 0x9d89\n"
        ".hword 0x25ed, 0x97b4, 0x2492, 0x9249\n"
        ".hword 0xcb08, 0x8d3d, 0x8888, 0x8888\n"
        ".hword 0x0842, 0x8421, 0x0000, 0x8000\n"
    );
}

extern "C" u8* engine_func_0029bddc(const char* path, u32 flag);
extern "C" void engine_func_002a06c8(u8* mod, u32 flag);
extern "C" void engine_func_00341578(u8* self, const char* path);
extern "C" void script_vm_func_002a0790(u32 a0);
extern "C" const u32* engine_func_002a8948(const u8* obj);
extern "C" const char* crt_func_00100c4c(const char* s1, const char* s2);

// DECOMP_FUNC(0x002350f4, 756)
extern "C" void engine_func_002350f4(u8* self, const char* name1, const char* name2) {
    *reinterpret_cast<u32*>(self + 0x1C) = 0u;
    *reinterpret_cast<u32*>(self + 0x18) = 0u;
    *reinterpret_cast<u32*>(self + 0x00) = 0u;
    *reinterpret_cast<u32*>(self + 0x08) = 0u;
    *reinterpret_cast<u32*>(self + 0x04) = 0u;
    *reinterpret_cast<u32*>(self + 0x0C) = 0u;
    self[0x15] = 0u;

    engine_func_002c4b30(self + 0x56C, 0x80u);

    char buf[0x80];
    ui_func_002be7fc(buf, "%s.bam", (name2 != nullptr) ? name2 : name1);
    *reinterpret_cast<u8**>(self + 0x1C) = engine_func_0029bddc(buf, 7u);
    engine_func_002a06c8(*reinterpret_cast<u8**>(self + 0x1C), 1u);

    ui_func_002be7fc(buf, "%s.bccam", name1);
    engine_func_00341578(self, buf);

    ui_func_002be7fc(buf, "%s.bcenv", name1);
    engine_func_002a0c54(buf, 0u);
    script_vm_func_002a0790(0u);

    const u8* const p56c = *reinterpret_cast<const u8* const*>(self + 0x56C);
    u32* const f1634 = reinterpret_cast<u32*>(self + 0x1634);
    f1634[0] = *reinterpret_cast<const u32*>(p56c + 0x58);
    f1634[1] = *reinterpret_cast<const u32*>(p56c + 0x68);
    f1634[2] = *reinterpret_cast<const u32*>(p56c + 0x78);

    const u32* const p_2a8 = engine_func_002a8948(p56c);
    u32* const f1640 = reinterpret_cast<u32*>(self + 0x1640);
    f1640[0] = p_2a8[0];
    f1640[1] = p_2a8[1];
    f1640[2] = p_2a8[2];

    u32* const f1610 = reinterpret_cast<u32*>(self + 0x1610);
    f1610[0] = f1640[0];
    f1610[1] = f1640[1];
    f1610[2] = f1640[2];

    u32* const f1604 = reinterpret_cast<u32*>(self + 0x1604);
    f1604[0] = f1634[0];
    f1604[1] = f1634[1];
    f1604[2] = f1634[2];

    const u8* const m1 = *reinterpret_cast<const u8* const*>(*reinterpret_cast<const u8* const*>(self + 0x1C) + 8);
    const u8* const m2 = *reinterpret_cast<const u8* const*>(m1 + 0x2C);
    const u8* node = *reinterpret_cast<const u8* const*>(m2 + 8);
    if (node != nullptr && (0x40000092u & ~(*reinterpret_cast<const u32*>(node))) != 0u) {
        node = nullptr;
    }

    const u32 off_e0 = *reinterpret_cast<const u32*>(node + 0xE0);
    const u8* const grp = (off_e0 != 0u) ? (node + 0xE0 + off_e0) : nullptr;
    const s32 count = *reinterpret_cast<const s32*>(grp + 0x18);
    for (s32 i = 0; i < count; ++i) {
        const u32 off_1c = *reinterpret_cast<const u32*>(grp + 0x1C);
        const u8* const arr = (off_1c != 0u) ? (grp + 0x1C + off_1c) : nullptr;
        const u8* entry = nullptr;
        if (arr != nullptr) {
            const u8* const base = arr + i * 0x10 + 0x28;
            const u32 off_e = *reinterpret_cast<const u32*>(base);
            if (off_e != 0u) {
                entry = base + off_e;
            }
        }
        const u32 off_name = *reinterpret_cast<const u32*>(entry);
        const char* const ename = (off_name != 0u) ? reinterpret_cast<const char*>(entry + off_name) : nullptr;
        if (crt_func_00100c4c(ename, "Dum_") != nullptr) {
            const u32* const src = reinterpret_cast<const u32*>(entry + 0x38);
            const s32 idx = *reinterpret_cast<const s32*>(self + 0x0C);
            u32* const dst = reinterpret_cast<u32*>(self + 0x1670 + idx * 12);
            dst[0] = src[0];
            dst[1] = src[1];
            dst[2] = src[2];
            *reinterpret_cast<s32*>(self + 0x0C) = idx + 1;
        }
    }

    if (*reinterpret_cast<const s32*>(self + 0x0C) > 0) {
        self[0x15] = 1u;

        ui_func_002be7fc(buf, "mikado/yaji.bam");
        *reinterpret_cast<u8**>(self + 0x24) = engine_func_0029bddc(buf, 7u);
        engine_func_002a06c8(*reinterpret_cast<u8**>(self + 0x24), 1u);

        ui_func_002be7fc(buf, "mikado/point.bam");
        *reinterpret_cast<u8**>(self + 0x20) = engine_func_0029bddc(buf, 7u);
        engine_func_002a06c8(*reinterpret_cast<u8**>(self + 0x20), 1u);

        const u32* const first_pt = reinterpret_cast<const u32*>(self + 0x1670);
        u32* const f1658 = reinterpret_cast<u32*>(self + 0x1658);
        f1658[0] = first_pt[0];
        f1658[1] = first_pt[1];
        f1658[2] = first_pt[2];

        void* const sub20 = *reinterpret_cast<void* const*>(*reinterpret_cast<const u8* const*>(self + 0x20) + 8);
        engine_func_0028c8a8(sub20, 0u, f1658);
    }
}

extern "C" f32 func_003e7430(u8* p, u32 idx);
extern "C" void func_0037fd88(u8* p, u8 b, f32 f);

// DECOMP_FUNC(0x00235ac4, 760)
extern "C" void ui_func_00235ac4(u8* self) {
    if (self[5] == 0u) {
        return;
    }
    u8* node = *reinterpret_cast<u8**>(self + 0xC4);
    if (node == nullptr) {
        return;
    }

    static constexpr f32 kInv127Cubed = 1.0f / (127.0f * 127.0f * 127.0f);
    static constexpr f32 kInv128 = 1.0f / 128.0f;
    static constexpr f32 kInv63 = 1.0f / 63.0f;
    static constexpr f32 kInv127 = 1.0f / 127.0f;

    const s32 v_6e = *reinterpret_cast<const signed short*>(self + 0x6E);
    const s32 v_70 = *reinterpret_cast<const signed short*>(self + 0x70);
    u8 interp0;
    if (v_6e <= v_70) {
        interp0 = self[0x6D];
    } else {
        const s32 d = static_cast<s32>(self[0x6D]) - static_cast<s32>(self[0x6C]);
        interp0 = static_cast<u8>((ui_func_002c615c(d * v_70, v_6e) + static_cast<s32>(self[0x6C])) & 0xFF);
    }

    u8* const p_c0 = *reinterpret_cast<u8**>(self + 0xC0);
    const u32 prod = static_cast<u32>(interp0) * static_cast<u32>(self[0x84]) * static_cast<u32>(p_c0[0x74]);
    const f32 t = static_cast<f32>(prod) * kInv127Cubed;
    const f32 s17 = (*reinterpret_cast<const f32*>(self + 0x08) * *reinterpret_cast<const f32*>(p_c0 + 0x14)) * (t * t);

    const s32 v_80 = *reinterpret_cast<const signed short*>(self + 0x80);
    const s32 v_82 = *reinterpret_cast<const signed short*>(self + 0x82);
    signed char v_s1;
    if (v_82 >= v_80) {
        v_s1 = *reinterpret_cast<const signed char*>(self + 0x7F);
    } else {
        const s32 d = static_cast<s32>(*reinterpret_cast<const signed char*>(self + 0x7F)) -
                      static_cast<s32>(*reinterpret_cast<const signed char*>(self + 0x7E));
        v_s1 = static_cast<signed char>(ui_func_002c615c(d * v_82, v_80) +
                                        static_cast<s32>(*reinterpret_cast<const signed char*>(self + 0x7E)));
    }

    const f32 s19 = *reinterpret_cast<const f32*>(p_c0 + 0x18) * *reinterpret_cast<const f32*>(self + 0x0C);
    const f32 s18 = (static_cast<f32>(v_s1) * kInv128) * static_cast<f32>(self[0x86]);

    const s32 v_74 = *reinterpret_cast<const signed short*>(self + 0x74);
    const s32 v_76 = *reinterpret_cast<const signed short*>(self + 0x76);
    signed char v_s2;
    if (v_76 >= v_74) {
        v_s2 = *reinterpret_cast<const signed char*>(self + 0x73);
    } else {
        const s32 d = static_cast<s32>(*reinterpret_cast<const signed char*>(self + 0x73)) -
                      static_cast<s32>(*reinterpret_cast<const signed char*>(self + 0x72));
        v_s2 = static_cast<signed char>(ui_func_002c615c(d * v_76, v_74) +
                                        static_cast<s32>(*reinterpret_cast<const signed char*>(self + 0x72)));
    }

    f32 s22 = static_cast<f32>(v_s2) * kInv63;
    if (s22 > 1.0f) {
        s22 = 1.0f;
    } else if (s22 < -1.0f) {
        s22 = -1.0f;
    }
    const f32 s16 = (*reinterpret_cast<const f32*>(self + 0x10) + *reinterpret_cast<const f32*>(p_c0 + 0x1C)) +
                    s22 * (*reinterpret_cast<const f32*>(self + 0x18) * *reinterpret_cast<const f32*>(p_c0 + 0x60));

    const s32 v_7a = *reinterpret_cast<const signed short*>(self + 0x7A);
    const s32 v_7c = *reinterpret_cast<const signed short*>(self + 0x7C);
    signed char v_s3;
    if (v_7c >= v_7a) {
        v_s3 = *reinterpret_cast<const signed char*>(self + 0x79);
    } else {
        const s32 d = static_cast<s32>(*reinterpret_cast<const signed char*>(self + 0x79)) -
                      static_cast<s32>(*reinterpret_cast<const signed char*>(self + 0x78));
        v_s3 = static_cast<signed char>(ui_func_002c615c(d * v_7c, v_7a) +
                                        static_cast<s32>(*reinterpret_cast<const signed char*>(self + 0x78)));
    }

    f32 s0_b = static_cast<f32>(v_s3) * kInv63;
    if (s0_b > 2.0f) {
        s0_b = 2.0f;
    } else if (s0_b < 0.0f) {
        s0_b = 0.0f;
    }
    const f32 s20 = s0_b + (*reinterpret_cast<const f32*>(self + 0x14) + *reinterpret_cast<const f32*>(p_c0 + 0x20));
    const f32 s21 = *reinterpret_cast<const f32*>(self + 0x98) + *reinterpret_cast<const f32*>(p_c0 + 0x24);
    const u8 r7 = (p_c0[0x2C] != 0u) ? p_c0[0x2C] : self[0x95];
    const f32 s23 = (p_c0[0x2C] != 0u) ? *reinterpret_cast<const f32*>(p_c0 + 0x28)
                                       : *reinterpret_cast<const f32*>(self + 0x9C);
    const f32 s22_out = ((static_cast<f32>(self[0x92]) * kInv127) - 1.0f) + *reinterpret_cast<const f32*>(p_c0 + 0x30);

    f32 arr[2];
    for (s32 i = 0; i < 2; ++i) {
        arr[i] = func_003e7430(p_c0, static_cast<u32>(i & 0xFF)) + static_cast<f32>(self[0x93 + i]) * kInv127;
    }

    while (node != nullptr) {
        *reinterpret_cast<f32*>(node + 0xCC) = s17;
        *reinterpret_cast<f32*>(node + 0xF0) = s18;
        *reinterpret_cast<f32*>(node + 0xD0) = s19;
        *reinterpret_cast<f32*>(node + 0xD4) = s16;
        *reinterpret_cast<f32*>(node + 0xD8) = s20;
        *reinterpret_cast<f32*>(node + 0xDC) = s21;
        func_0037fd88(node, r7, s23);
        *reinterpret_cast<f32*>(node + 0xE4) = s22_out;
        *reinterpret_cast<f32*>(node + 0xE8) = arr[0];
        *reinterpret_cast<f32*>(node + 0xEC) = arr[1];

        const u32* const src54 = reinterpret_cast<const u32*>(self + 0x54);
        u32* const dst_ac = reinterpret_cast<u32*>(node + 0xAC);
        dst_ac[0] = src54[0];
        dst_ac[1] = src54[1];
        dst_ac[2] = src54[2];
        *reinterpret_cast<u32*>(node + 0xB8) = *reinterpret_cast<const u32*>(self + 0x60);
        node[0xC4] = self[0x64];
        node = *reinterpret_cast<u8**>(node + 0x138);
    }
}

struct AocStatus0038ff58 {
    u32 w[5];
};

extern "C" void engine_func_00234278(void* out);
extern "C" u32 camp_func_0027ec84(const void* s);
extern "C" void battle_func_00233f0c(void* self);
extern "C" void shop_func_00297128();
extern "C" void engine_func_00234004(void* self, u32 a1, u32 a2);
extern "C" void engine_func_00233f4c(void* self, u32 a1);
extern "C" u8* engine_func_00234160(void* p, u32 a1);
extern "C" u32 engine_func_002a17c0(const void* s);
extern "C" u32 ui_func_0026f0d8(u32 a0);
extern "C" u32 shop_func_0029111c();

// DECOMP_FUNC(0x0038ff58, 760)
extern "C" void script_vm_func_0038ff58(u8* self) {
    AocStatus0038ff58 st;
    engine_func_00234278(&st);

    const u8* const g = *reinterpret_cast<const u8* const*>(0x00432FC8u);
    const s32 state = *reinterpret_cast<const s32*>(self + 8);

    switch (state) {
        case 0: {
            *reinterpret_cast<u32*>(self) |= 0x10000u;
            engine_func_00233f4c(self, 3u);
            const u32 h = script_vm_func_00291018(*reinterpret_cast<const u32*>(self + 0x350), "aoc_ExeDelete");
            script_vm_func_002971e4(*reinterpret_cast<const u32*>(self + 0x358), h);
            *reinterpret_cast<u32*>(self + 8) = 1u;
            camp_func_00233ac0(self, -1, 0u);
            break;
        }
        case 1: {
            if (ui_func_0026b7cc() == 0u) {
                break;
            }
            if ((*reinterpret_cast<const u32*>(self) & 0x200u) == 0u) {
                break;
            }
            script_vm_func_0019dfbc(*reinterpret_cast<const u32*>(self + 0x358));
            u8* const obj = engine_func_00234160(self + 0x20C, 3u);
            *reinterpret_cast<u8**>(self + 0x208) = obj;
            const u32 idx = shop_func_002337a0(self + 0x240);
            const u8* const tbl = *reinterpret_cast<const u8* const*>(g + 0x678);
            const u16 val = *reinterpret_cast<const u16*>(tbl + 0x9AAu + idx * 0x139u * 8u);
            *reinterpret_cast<u32*>(obj + 0x14) = val;
            *reinterpret_cast<u32*>(self + 8) = 2u;
            break;
        }
        case 2: {
            script_vm_func_0019dfbc(*reinterpret_cast<const u32*>(self + 0x358));
            void* const obj = *reinterpret_cast<void**>(self + 0x208);
            using QueryFn = AocStatus0038ff58 (*)(void*);
            const QueryFn fn = (*reinterpret_cast<QueryFn* const*>(obj))[3];
            st = fn(obj);
            if (camp_func_0027ec84(&st) != 0u) {
                battle_func_00233f0c(self);
                shop_func_00297128();
                *reinterpret_cast<u32*>(self + 8) = 3u;
            } else if (engine_func_002a17c0(&st) != 0u) {
                battle_func_00233f0c(self);
                shop_func_00297128();
                *reinterpret_cast<u32*>(self + 8) = 9999u;
                *reinterpret_cast<AocStatus0038ff58*>(self + 0x210) = st;
            }
            break;
        }
        case 3: {
            if (script_vm_func_002a0f88() == 0u) {
                break;
            }
            const u32 h = script_vm_func_00291018(*reinterpret_cast<const u32*>(self + 0x350), "aoc_Deleted");
            script_vm_func_002971e4(*reinterpret_cast<const u32*>(self + 0x358), h);
            engine_func_002b8584(0u);
            camp_func_00233ac0(self, 3, 1u);
            *reinterpret_cast<u32*>(self + 8) = 4u;
            break;
        }
        case 4: {
            script_vm_func_0019dfbc(*reinterpret_cast<const u32*>(self + 0x358));
            if (ui_func_0026f0d8(0x10u) == 0u) {
                break;
            }
            camp_func_002bc200(0x0100016Du);
            shop_func_00297128();
            *reinterpret_cast<u32*>(self + 8) = 5u;
            break;
        }
        case 5: {
            if (script_vm_func_002a0f88() == 0u) {
                break;
            }
            if (shop_func_0029111c() == 0u) {
                break;
            }
            void* const obj = *reinterpret_cast<void**>(self + 0x208);
            *reinterpret_cast<u32*>(self + 4) = 10u;
            *reinterpret_cast<u32*>(self + 8) = 0u;
            if (obj != nullptr) {
                using DtorFn = void (*)(void*);
                const DtorFn dtor = (*reinterpret_cast<DtorFn* const*>(obj))[1];
                dtor(obj);
                *reinterpret_cast<void**>(self + 0x208) = nullptr;
            }
            break;
        }
        case 9999: {
            engine_func_00234004(self, 5u, 3u);
            break;
        }
        default:
            break;
    }
}

// DECOMP_FUNC(0x0038fb3c, 772)
extern "C" __attribute__((naked)) void ui_func_0038fb3c() {
    asm volatile(
        ".arm\n"
        ".hword 0x4ff0, 0xe92d, 0xdb01, 0xe24d\n"
        ".hword 0xd024, 0xe24d, 0xc3de, 0xebfc\n"
        ".hword 0x5000, 0xe1a0, 0x0b05, 0xe280\n"
        ".hword 0x0fe6, 0xe280, 0x42c0, 0xe59f\n"
        ".hword 0x6000, 0xe590, 0x02bc, 0xe59f\n"
        ".hword 0x8000, 0xe590, 0x0000, 0xe594\n"
        ".hword 0xd00d, 0xebfc, 0x4000, 0xe594\n"
        ".hword 0x1000, 0xe3a0, 0x0001, 0xe3a0\n"
        ".hword 0xd8fe, 0xebfc, 0x4a01, 0xe284\n"
        ".hword 0x4f93, 0xe284, 0x9000, 0xe3a0\n"
        ".hword 0x1000, 0xe594, 0x2001, 0xe281\n"
        ".hword 0x3101, 0xe084, 0x1008, 0xe593\n"
        ".hword 0x3102, 0xe084, 0x2000, 0xe584\n"
        ".hword 0x0008, 0xe583, 0x2018, 0xe5d4\n"
        ".hword 0x0000, 0xe352, 0x0000, 0x0151\n"
        ".hword 0x0002, 0x0a00, 0x101c, 0xe594\n"
        ".hword 0xff31, 0xe12f, 0x9018, 0xe5c4\n"
        ".hword 0x0000, 0xe3a0, 0x7081, 0xe3a0\n"
        ".hword 0x3000, 0xe1a0, 0x0081, 0xe88d\n"
        ".hword 0x2005, 0xe3a0, 0x103a, 0xe3a0\n"
        ".hword 0x0002, 0xe3a0, 0xbe5c, 0xebfc\n"
        ".hword 0x0240, 0xe59f, 0x5b05, 0xe285\n"
        ".hword 0x5fe7, 0xe285, 0xa230, 0xe59f\n"
        ".hword 0x100e, 0xe890, 0x0187, 0xe08d\n"
        ".hword 0x100e, 0xe880, 0x1187, 0xe08d\n"
        ".hword 0x0000, 0xe595, 0x1100, 0xe791\n"
        ".hword 0x0008, 0xe1a0, 0x9342, 0xebfa\n"
        ".hword 0x9008, 0xe28d, 0x1000, 0xe1a0\n"
        ".hword 0x2009, 0xe1a0, 0x0008, 0xe1a0\n"
        ".hword 0x9348, 0xebfa, 0x1003, 0xe3a0\n"
        ".hword 0x0009, 0xe1a0, 0x8e62, 0xebfa\n"
        ".hword 0x5000, 0xe1a0, 0x102d, 0xe3a0\n"
        ".hword 0x003a, 0xe3a0, 0xbea2, 0xebfc\n"
        ".hword 0x100c, 0xe590, 0x30fa, 0xe1d0\n"
        ".hword 0x20f8, 0xe1d0, 0x2a76, 0xed9f\n"
        ".hword 0x10f0, 0xe1d1, 0x3a10, 0xee00\n"
        ".hword 0x1a74, 0xeddf, 0x1a74, 0xed9f\n"
        ".hword 0x00c1, 0xe082, 0x00c5, 0xe040\n"
        ".hword 0x4009, 0xe240, 0x0ac0, 0xeef8\n"
        ".hword 0x4a10, 0xee00, 0x2009, 0xe1a0\n"
        ".hword 0x100a, 0xe1a0, 0x0003, 0xe3a0\n"
        ".hword 0x0ac0, 0xeeb8, 0xbabb, 0xebfc\n"
        ".hword 0x01a8, 0xe59f, 0xb000, 0xe3a0\n"
        ".hword 0x9005, 0xe084, 0x1690, 0xe080\n"
        ".hword 0x0120, 0xe1a0, 0x1fc0, 0xe1a0\n"
        ".hword 0x1ea1, 0xe080, 0x1007, 0xe3c1\n"
        ".hword 0x8001, 0xe040, 0x1007, 0xe288\n"
        ".hword 0x0004, 0xe280, 0x2fc1, 0xe1a0\n"
        ".hword 0x2ea2, 0xe081, 0x2007, 0xe3c2\n"
        ".hword 0x1002, 0xe041, 0x1418, 0xe58d\n"
        ".hword 0x1fc0, 0xe1a0, 0x1ea1, 0xe080\n"
        ".hword 0x1007, 0xe3c1, 0xa001, 0xe040\n"
        ".hword 0x0007, 0xe28a, 0x1fc0, 0xe1a0\n"
        ".hword 0x1ea1, 0xe080, 0x1007, 0xe3c1\n"
        ".hword 0x0001, 0xe040, 0x041c, 0xe58d\n"
        ".hword 0x4000, 0xe3a0, 0x708b, 0xe08b\n"
        ".hword 0x5004, 0xe087, 0x1031, 0xe3a0\n"
        ".hword 0x003a, 0xe3a0, 0xbe70, 0xebfc\n"
        ".hword 0x60f8, 0xe1d0, 0x1031, 0xe285\n"
        ".hword 0x003a, 0xe3a0, 0xbe6c, 0xebfc\n"
        ".hword 0x10f8, 0xe1d0, 0x00fa, 0xe1d0\n"
        ".hword 0x0005, 0xe158, 0x1006, 0xe041\n"
        ".hword 0x1009, 0xe081, 0x0005, 0x115a\n"
        ".hword 0x3004, 0xe281, 0x0008, 0x1a00\n"
        ".hword 0x1081, 0xe3a0, 0x00f0, 0xe1cd\n"
        ".hword 0x20d4, 0xe281, 0x100e, 0xe3a0\n"
        ".hword 0x0002, 0xe3a0, 0xbdc2, 0xebfc\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0x0012, 0xea00, 0x1418, 0xe59d\n"
        ".hword 0x0005, 0xe151, 0x141c, 0x159d\n"
        ".hword 0x0005, 0x1151, 0x1081, 0xe3a0\n"
        ".hword 0x0007, 0x1a00, 0x00f0, 0xe1cd\n"
        ".hword 0x20d5, 0xe281, 0x100e, 0xe3a0\n"
        ".hword 0x0002, 0xe3a0, 0xbdb4, 0xebfc\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0x0004, 0xea00, 0x00f0, 0xe1cd\n"
        ".hword 0x2f55, 0xe3a0, 0x100e, 0xe3a0\n"
        ".hword 0x0002, 0xe3a0, 0xbdac, 0xebfc\n"
        ".hword 0x4001, 0xe284, 0x0003, 0xe354\n"
        ".hword 0xffd0, 0xbaff, 0xb001, 0xe28b\n"
        ".hword 0x0003, 0xe35b, 0xffcb, 0xbaff\n"
        ".hword 0x0054, 0xe59f, 0x0000, 0xe590\n"
        ".hword 0x4a01, 0xe280, 0x4f93, 0xe284\n"
        ".hword 0x0000, 0xe594, 0x1100, 0xe084\n"
        ".hword 0x0001, 0xe240, 0x1008, 0xe591\n"
        ".hword 0x0000, 0xe584, 0x0100, 0xe084\n"
        ".hword 0x2018, 0xe5d4, 0x0008, 0xe590\n"
        ".hword 0x0000, 0xe352, 0x0000, 0x0151\n"
        ".hword 0x0003, 0x0a00, 0x101c, 0xe594\n"
        ".hword 0xff31, 0xe12f, 0x0000, 0xe3a0\n"
        ".hword 0x0018, 0xe5c4, 0xdb01, 0xe28d\n"
        ".hword 0xd024, 0xe28d, 0x0000, 0xe3a0\n"
        ".hword 0x8ff0, 0xe8bd, 0xea00, 0x0044\n"
        ".hword 0x2fc8, 0x0043, 0x00ff, 0xf498\n"
        ".hword 0xf138, 0x003f, 0x0000, 0x3f80\n"
        ".hword 0x0000, 0x0000, 0x0000, 0x3f00\n"
        ".hword 0xcccd, 0xcccc\n"
    );
}

// DECOMP_FUNC(0x00264368, 776)
extern "C" __attribute__((naked)) void script_vm_func_00264368() {
    asm volatile(
        ".arm\n"
        ".hword 0x5ff0, 0xe92d, 0x9000, 0xe3a0\n"
        ".hword 0xa00a, 0xe3a0, 0x02d8, 0xe59f\n"
        ".hword 0x82c0, 0xe59f, 0x5009, 0xe1a0\n"
        ".hword 0x8b04, 0xed2d, 0x6009, 0xe1a0\n"
        ".hword 0x7009, 0xe1a0, 0x4000, 0xe590\n"
        ".hword 0x0000, 0xe598, 0x8aaa, 0xeddf\n"
        ".hword 0x9aaa, 0xeddf, 0x1050, 0xe594\n"
        ".hword 0x9aa9, 0xed9f, 0x8aa9, 0xed9f\n"
        ".hword 0x1018, 0xe580, 0x1094, 0xe5d4\n"
        ".hword 0x0000, 0xe351, 0x0006, 0x0a00\n"
        ".hword 0x90b0, 0xe5c0, 0x90b1, 0xe5c0\n"
        ".hword 0xabb2, 0xe1c0, 0x9bb4, 0xe1c0\n"
        ".hword 0x8a2e, 0xed80, 0x8a2f, 0xed80\n"
        ".hword 0x9a30, 0xed80, 0x1bf2, 0xe1d0\n"
        ".hword 0xb001, 0xe3a0, 0x0000, 0xe351\n"
        ".hword 0x1001, 0xc241, 0x1bb2, 0xc1c0\n"
        ".hword 0x1268, 0xe59f, 0x2018, 0xe5d1\n"
        ".hword 0x0000, 0xe352, 0x101c, 0x0591\n"
        ".hword 0x0000, 0x0351, 0x003e, 0x1a00\n"
        ".hword 0x10b0, 0xe5d0, 0x0000, 0xe351\n"
        ".hword 0x0053, 0x1a00, 0x00b1, 0xe5d0\n"
        ".hword 0x0000, 0xe350, 0x0009, 0x0a00\n"
        ".hword 0x0008, 0xe3a0, 0x74ec, 0xeb01\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0004, 0x1a00, 0x0007, 0xe3a0\n"
        ".hword 0x74e7, 0xeb01, 0x0000, 0xe350\n"
        ".hword 0x0000, 0x0598, 0x90b1, 0x05c0\n"
        ".hword 0x0000, 0xe598, 0x0bf2, 0xe1d0\n"
        ".hword 0x0006, 0xe350, 0x002a, 0xca00\n"
        ".hword 0x0008, 0xe3a0, 0x74de, 0xeb01\n"
        ".hword 0x0000, 0xe350, 0x5001, 0x13a0\n"
        ".hword 0x0007, 0xe3a0, 0x74da, 0xeb01\n"
        ".hword 0x0000, 0xe350, 0x0000, 0xe598\n"
        ".hword 0x6001, 0x13a0, 0x0bb2, 0xe1d0\n"
        ".hword 0x0000, 0xe350, 0x001e, 0x1a00\n"
        ".hword 0x4832, 0xeb00, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x0017, 0x1a00\n"
        ".hword 0x0008, 0xe3a0, 0x74ce, 0xeb01\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0015, 0x0a00, 0x0007, 0xe3a0\n"
        ".hword 0x74c9, 0xeb01, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x0010, 0x0a00\n"
        ".hword 0x0008, 0xe3a0, 0x6ebe, 0xeb01\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x000b, 0x1a00, 0x0007, 0xe3a0\n"
        ".hword 0x6eb9, 0xeb01, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x0006, 0x1a00\n"
        ".hword 0x0000, 0xe598, 0x00b1, 0xe5d0\n"
        ".hword 0x0000, 0xe350, 0x0002, 0x1a00\n"
        ".hword 0x5000, 0xe3a0, 0x6005, 0xe1a0\n"
        ".hword 0x7001, 0xe3a0, 0x0000, 0xe598\n"
        ".hword 0x10b0, 0xe5d0, 0x0000, 0xe351\n"
        ".hword 0x0013, 0x1a00, 0x0000, 0xe357\n"
        ".hword 0x002d, 0x0a00, 0xb0b0, 0xe5c0\n"
        ".hword 0x0a69, 0xeef0, 0x0a06, 0xed90\n"
        ".hword 0x8a83, 0xed80, 0x8a84, 0xed80\n"
        ".hword 0x00b8, 0xe280, 0x0a02, 0xec80\n"
        ".hword 0x8e0f, 0xeb00, 0x0ac8, 0xeeb4\n"
        ".hword 0x0000, 0xe598, 0xfa10, 0xeef1\n"
        ".hword 0x9bb4, 0xe1c0, 0x0a44, 0x3d9f\n"
        ".hword 0x0a30, 0x3d80, 0x9a30, 0x2d80\n"
        ".hword 0x00b0, 0xe5d0, 0x0000, 0xe350\n"
        ".hword 0x001b, 0x0a00, 0x0000, 0xe598\n"
        ".hword 0x8a3e, 0xeddf, 0x0a2f, 0xedd0\n"
        ".hword 0x0a06, 0xed90, 0x6af7, 0xeb00\n"
        ".hword 0x0a3b, 0xeddf, 0x0000, 0xe598\n"
        ".hword 0x0ae0, 0xeeb4, 0xfa10, 0xeef1\n"
        ".hword 0x0005, 0x8a00, 0x10bc, 0xe590\n"
        ".hword 0x1018, 0xe580, 0x90b0, 0xe5c0\n"
        ".hword 0xabb2, 0xe1c0, 0xb0b1, 0xe5c0\n"
        ".hword 0x0006, 0xea00, 0x0a30, 0xed90\n"
        ".hword 0x8ac0, 0xeeb4, 0xfa10, 0xeef1\n"
        ".hword 0x0a06, 0xed90, 0x0a28, 0xde30\n"
        ".hword 0x0a68, 0xce30, 0x0a06, 0xed80\n"
        ".hword 0x0000, 0xe598, 0x00b0, 0xe5d0\n"
        ".hword 0x0000, 0xe350, 0x000c, 0x0a00\n"
        ".hword 0x0017, 0xea00, 0x0000, 0xe355\n"
        ".hword 0x0003, 0x0a00, 0x0000, 0xe598\n"
        ".hword 0x0a06, 0xed90, 0x0a28, 0xee30\n"
        ".hword 0x0004, 0xea00, 0x0000, 0xe356\n"
        ".hword 0x0003, 0x0a00, 0x0000, 0xe598\n"
        ".hword 0x0a06, 0xed90, 0x0a68, 0xee30\n"
        ".hword 0x0a06, 0xed80, 0x0000, 0xe598\n"
        ".hword 0x0a18, 0xeddf, 0x2060, 0xe59f\n"
        ".hword 0x0a06, 0xed90, 0x0ac8, 0xeeb4\n"
        ".hword 0xfa10, 0xeef1, 0x0a20, 0x3e30\n"
        ".hword 0x1a10, 0xee10, 0x0a06, 0x3d80\n"
        ".hword 0x0002, 0xe151, 0x0a60, 0xae30\n"
        ".hword 0x0a06, 0xad80, 0x0000, 0xe598\n"
        ".hword 0x0018, 0xe590, 0x0050, 0xe584\n"
        ".hword 0x8b04, 0xecbd, 0x9ff0, 0xe8bd\n"
        ".hword 0x74f4, 0x0044, 0x0000, 0x4040\n"
        ".hword 0x0000, 0x4334, 0x0000, 0x3f80\n"
        ".hword 0x0000, 0x0000, 0x7060, 0x0044\n"
        ".hword 0xf91c, 0x0049, 0x0000, 0xbf80\n"
        ".hword 0x0000, 0x4170, 0x0000, 0x4178\n"
        ".hword 0x0000, 0x43b4, 0x0000, 0x43b4\n"
    );
}

// DECOMP_FUNC(0x00193024, 784)
extern "C" __attribute__((naked)) void func_00193024() {
    asm volatile(
        ".arm\n"
        ".hword 0x4ff0, 0xe92d, 0x4000, 0xe1a0\n"
        ".hword 0x6000, 0xe3a0, 0x8b04, 0xed2d\n"
        ".hword 0xd01c, 0xe24d, 0x2024, 0xe590\n"
        ".hword 0x1184, 0xe590, 0x8ab7, 0xed9f\n"
        ".hword 0x0018, 0xe280, 0x0002, 0xe151\n"
        ".hword 0x0018, 0xe58d, 0x0033, 0x1a00\n"
        ".hword 0x1c03, 0xe284, 0x00b0, 0xe1d1\n"
        ".hword 0x0001, 0xe240, 0x0070, 0xe6bf\n"
        ".hword 0x00b0, 0xe1c1, 0x0000, 0xe350\n"
        ".hword 0x6024, 0xe584, 0x0014, 0xca00\n"
        ".hword 0x5004, 0xe1b0, 0x4000, 0xe3a0\n"
        ".hword 0x0025, 0x0a00, 0x0104, 0xe085\n"
        ".hword 0x0238, 0xe590, 0xf98a, 0xeb03\n"
        ".hword 0x4001, 0xe284, 0x0032, 0xe354\n"
        ".hword 0xfff9, 0xbaff, 0x0228, 0xe595\n"
        ".hword 0x6024, 0xe585, 0x6028, 0xe585\n"
        ".hword 0x602c, 0xe585, 0x0000, 0xe350\n"
        ".hword 0x6030, 0xe585, 0x6000, 0x1580\n"
        ".hword 0xd01c, 0xe28d, 0x0005, 0xe1a0\n"
        ".hword 0x8b04, 0xecbd, 0x4ff0, 0xe8bd\n"
        ".hword 0xfa21, 0xea03, 0x0018, 0xe59d\n"
        ".hword 0x6000, 0xe584, 0x6004, 0xe584\n"
        ".hword 0x6008, 0xe584, 0x600c, 0xe584\n"
        ".hword 0x6010, 0xe584, 0x6014, 0xe584\n"
        ".hword 0x6018, 0xe584, 0x601c, 0xe584\n"
        ".hword 0x6020, 0xe584, 0x6028, 0xe584\n"
        ".hword 0x602c, 0xe584, 0x6030, 0xe584\n"
        ".hword 0x6034, 0xe584, 0x0000, 0xe58d\n"
        ".hword 0x300c, 0xe284, 0x2030, 0xe284\n"
        ".hword 0x1028, 0xe284, 0x0f5b, 0xe284\n"
        ".hword 0xf932, 0xeb03, 0xd01c, 0xe28d\n"
        ".hword 0x8b04, 0xecbd, 0x8ff0, 0xe8bd\n"
        ".hword 0x0230, 0xe594, 0xb1f8, 0xe59f\n"
        ".hword 0x0000, 0xe350, 0x0013, 0xba00\n"
        ".hword 0x0100, 0xe084, 0x0238, 0xe590\n"
        ".hword 0x0000, 0xe350, 0x1234, 0x0594\n"
        ".hword 0x000e, 0x1a00, 0x0230, 0xe594\n"
        ".hword 0x0000, 0xe151, 0x000b, 0x0a00\n"
        ".hword 0x0001, 0xe280, 0x3018, 0xe3e0\n"
        ".hword 0xc09b, 0xe0c2, 0xc242, 0xe1a0\n"
        ".hword 0x2fc2, 0xe04c, 0x0392, 0xe002\n"
        ".hword 0x0082, 0xe080, 0x0230, 0xe584\n"
        ".hword 0x0100, 0xe084, 0x0238, 0xe590\n"
        ".hword 0x0000, 0xe350, 0xfff0, 0x0aff\n"
        ".hword 0x0a00, 0xed94, 0x1034, 0xe594\n"
        ".hword 0x7000, 0xe3a0, 0x0ac0, 0xeebd\n"
        ".hword 0x0a10, 0xee10, 0x9001, 0xe040\n"
        ".hword 0x0000, 0xe359, 0x8a61, 0xcddf\n"
        ".hword 0x9a61, 0xcd9f, 0x004c, 0xda00\n"
        ".hword 0x0234, 0xe594, 0x2018, 0xe3e0\n"
        ".hword 0x0001, 0xe280, 0x309b, 0xe0c1\n"
        ".hword 0x3241, 0xe1a0, 0x1fc1, 0xe043\n"
        ".hword 0x0291, 0xe001, 0x6081, 0xe080\n"
        ".hword 0x0230, 0xe594, 0x0000, 0xe350\n"
        ".hword 0x0000, 0xb3a0, 0x0230, 0xb584\n"
        ".hword 0x0003, 0xba00, 0x0106, 0xe084\n"
        ".hword 0x0238, 0xe590, 0x0000, 0xe350\n"
        ".hword 0xf9d7, 0x1b03, 0x0a5f, 0xed94\n"
        ".hword 0x3220, 0xe594, 0x122c, 0xe5d4\n"
        ".hword 0x0a28, 0xee20, 0x5008, 0xe28d\n"
        ".hword 0x00ff, 0xe206, 0x2001, 0xe3a0\n"
        ".hword 0x000f, 0xe885, 0x8106, 0xe084\n"
        ".hword 0x1f8e, 0xe288, 0x021c, 0xe594\n"
        ".hword 0x3002, 0xe3a0, 0x2f5b, 0xe284\n"
        ".hword 0x0ac0, 0xeebc, 0x00f0, 0xe1cd\n"
        ".hword 0x0224, 0xe594, 0x1038, 0xe284\n"
        ".hword 0xaa10, 0xee10, 0xf8dd, 0xeb03\n"
        ".hword 0x0238, 0xe588, 0x5000, 0xe1a0\n"
        ".hword 0x1180, 0xe594, 0x2064, 0xe3a0\n"
        ".hword 0x0002, 0xe3a0, 0xf99b, 0xeb03\n"
        ".hword 0x0a48, 0xedd5, 0x300a, 0xe3a0\n"
        ".hword 0x2003, 0xe1a0, 0x0a20, 0xee30\n"
        ".hword 0x100a, 0xe1a0, 0x0000, 0xe3a0\n"
        ".hword 0x0a48, 0xed85, 0xf898, 0xeb03\n"
        ".hword 0x0a7d, 0xedd5, 0x2064, 0xe3a0\n"
        ".hword 0x0000, 0xe3a0, 0x0a20, 0xee20\n"
        ".hword 0x0a7d, 0xed85, 0x0a62, 0xed94\n"
        ".hword 0x0ac0, 0xeeb8, 0x0ad3, 0xed85\n"
        ".hword 0x1170, 0xe594, 0xf989, 0xeb03\n"
        ".hword 0x0a5b, 0xedd4, 0x2064, 0xe3a0\n"
        ".hword 0x0002, 0xe3a0, 0x0ae0, 0xeef8\n"
        ".hword 0x0a89, 0xee00, 0x0ad0, 0xed85\n"
        ".hword 0x8acf, 0xed85, 0x1174, 0xe594\n"
        ".hword 0xf85b, 0xeb03, 0x0ad1, 0xed85\n"
        ".hword 0x0034, 0xe594, 0x7001, 0xe287\n"
        ".hword 0x0009, 0xe157, 0x0001, 0xe280\n"
        ".hword 0x0034, 0xe584, 0x6234, 0xe584\n"
        ".hword 0xffb2, 0xbaff, 0x0018, 0xe59d\n"
        ".hword 0x1034, 0xe284, 0x200c, 0xe284\n"
        ".hword 0x00f8, 0xe1cd, 0x2004, 0xe58d\n"
        ".hword 0x3030, 0xe284, 0x2028, 0xe284\n"
        ".hword 0x102c, 0xe284, 0x0f5b, 0xe284\n"
        ".hword 0x4000, 0xe58d, 0xf7fd, 0xeb03\n"
        ".hword 0x0024, 0xe594, 0x0001, 0xe280\n"
        ".hword 0x0024, 0xe584, 0xd01c, 0xe28d\n"
        ".hword 0x8b04, 0xecbd, 0x8ff0, 0xe8bd\n"
        ".hword 0x0000, 0x0000, 0x851f, 0x51eb\n"
        ".hword 0x0000, 0x4120, 0xd70a, 0x3c23\n"
    );
}

// DECOMP_FUNC(0x001062e0, 788)
extern "C" __attribute__((naked)) void engine_func_001062e0() {
    asm volatile(
        ".arm\n"
        ".hword 0x5ff0, 0xe92d, 0x0001, 0xe3a0\n"
        ".hword 0xfd53, 0xeb06, 0x0000, 0xe350\n"
        ".hword 0x00ad, 0x1a00, 0xa2ec, 0xe59f\n"
        ".hword 0x92e4, 0xe59f, 0x82e8, 0xe59f\n"
        ".hword 0x5000, 0xe3a0, 0xb001, 0xe28a\n"
        ".hword 0x7005, 0xe1a0, 0x0000, 0xe355\n"
        ".hword 0x6000, 0xe3a0, 0x4285, 0xe089\n"
        ".hword 0x6020, 0x0289, 0x0001, 0x0a00\n"
        ".hword 0x0001, 0xe355, 0x62b8, 0x059f\n"
        ".hword 0x001c, 0xe594, 0x0001, 0xe310\n"
        ".hword 0x0095, 0x0a00, 0x0002, 0xe310\n"
        ".hword 0x0008, 0x0a00, 0x0000, 0xe594\n"
        ".hword 0x1f05, 0xeb00, 0x101c, 0xe594\n"
        ".hword 0x0004, 0xe311, 0x0037, 0x0a00\n"
        ".hword 0x0020, 0xe310, 0x0004, 0x03c1\n"
        ".hword 0x004e, 0x0a00, 0x008f, 0xea00\n"
        ".hword 0x0b02, 0xe310, 0x0007, 0x0a00\n"
        ".hword 0x1014, 0xe594, 0x000f, 0xe351\n"
        ".hword 0x0001, 0xd281, 0x0014, 0xd584\n"
        ".hword 0x0b02, 0xc3c0, 0x001c, 0xc584\n"
        ".hword 0x7014, 0xc584, 0x0085, 0xda00\n"
        ".hword 0x000c, 0xe594, 0x16cd, 0xeb00\n"
        ".hword 0x6000, 0xe5d8, 0x1254, 0xe59f\n"
        ".hword 0x2008, 0xe3a0, 0xeda9, 0xfa06\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0019, 0x1a00, 0x000c, 0xe594\n"
        ".hword 0x000a, 0xe150, 0x0016, 0x0a00\n"
        ".hword 0x000b, 0xe150, 0x14ff, 0x1280\n"
        ".hword 0x107d, 0x1251, 0x0012, 0x0a00\n"
        ".hword 0x14ff, 0xe280, 0x1081, 0xe251\n"
        ".hword 0x14ff, 0x1280, 0x1082, 0x1251\n"
        ".hword 0x000d, 0x0a00, 0x14ff, 0xe280\n"
        ".hword 0x1083, 0xe251, 0x14ff, 0x1280\n"
        ".hword 0x108a, 0x1251, 0x0008, 0x0a00\n"
        ".hword 0x14ff, 0xe280, 0x108b, 0xe251\n"
        ".hword 0x14ff, 0x1280, 0x108c, 0x1251\n"
        ".hword 0x14ff, 0x1280, 0x10a4, 0x1251\n"
        ".hword 0x0001, 0x0a00, 0x233f, 0xeb00\n"
        ".hword 0x6000, 0xe1a0, 0x0009, 0xe894\n"
        ".hword 0x2006, 0xe1a0, 0x100c, 0xe594\n"
        ".hword 0x1e52, 0xeb00, 0x001c, 0xe594\n"
        ".hword 0x0002, 0xe380, 0x0019, 0xea00\n"
        ".hword 0x0008, 0xe311, 0x0024, 0x0a00\n"
        ".hword 0x0000, 0xe594, 0x1008, 0xe594\n"
        ".hword 0x183b, 0xeb00, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x0053, 0x0a00\n"
        ".hword 0x001c, 0xe594, 0x000a, 0xe3c0\n"
        ".hword 0x001c, 0xe584, 0x700c, 0xe584\n"
        ".hword 0x7004, 0xe584, 0x7008, 0xe584\n"
        ".hword 0x0c01, 0xe310, 0x7014, 0xe584\n"
        ".hword 0x000a, 0x0a00, 0x1010, 0xe594\n"
        ".hword 0x0005, 0xe380, 0x001c, 0xe584\n"
        ".hword 0x2018, 0xe594, 0x7010, 0xe584\n"
        ".hword 0x100c, 0xe584, 0x2004, 0xe584\n"
        ".hword 0x0c01, 0xe3c0, 0x7018, 0xe584\n"
        ".hword 0x001c, 0xe584, 0x003f, 0xea00\n"
        ".hword 0x701c, 0xe584, 0x1000, 0xe594\n"
        ".hword 0x0004, 0xe598, 0x0000, 0xe151\n"
        ".hword 0x003a, 0x1a00, 0x101c, 0xe596\n"
        ".hword 0x0b01, 0xe311, 0x0037, 0x1a00\n"
        ".hword 0x0000, 0xe350, 0x0016, 0x1a00\n"
        ".hword 0x0017, 0xea00, 0x0010, 0xe311\n"
        ".hword 0x0018, 0x0a00, 0x0000, 0xe594\n"
        ".hword 0x2008, 0xe594, 0x1000, 0xe3a0\n"
        ".hword 0x1b59, 0xeb00, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x002b, 0x0a00\n"
        ".hword 0x001c, 0xe594, 0x0010, 0xe3c0\n"
        ".hword 0x0020, 0xe380, 0x001c, 0xe584\n"
        ".hword 0x0004, 0xe598, 0x1000, 0xe594\n"
        ".hword 0x0000, 0xe151, 0x0023, 0x1a00\n"
        ".hword 0x101c, 0xe596, 0x0b01, 0xe311\n"
        ".hword 0x0020, 0x1a00, 0x0000, 0xe350\n"
        ".hword 0x0001, 0x0a00, 0x7004, 0xe588\n"
        ".hword 0x001c, 0xea00, 0x0001, 0xe3a0\n"
        ".hword 0x0004, 0xe588, 0x0019, 0xea00\n"
        ".hword 0x0040, 0xe311, 0x0017, 0x0a00\n"
        ".hword 0x0005, 0xe894, 0x1001, 0xe3a0\n"
        ".hword 0x1b3f, 0xeb00, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x0011, 0x0a00\n"
        ".hword 0x001c, 0xe594, 0x0040, 0xe3c0\n"
        ".hword 0x0c02, 0xe310, 0x001c, 0xe584\n"
        ".hword 0x0002, 0x0a00, 0x0c0a, 0xe3c0\n"
        ".hword 0x0010, 0xe380, 0xffc7, 0xeaff\n"
        ".hword 0x0b02, 0xe310, 0x0b02, 0x13c0\n"
        ".hword 0x0008, 0x1380, 0x0005, 0x0a00\n"
        ".hword 0xffc2, 0xeaff, 0x0c01, 0xe310\n"
        ".hword 0x0002, 0x0a00, 0x003c, 0xe310\n"
        ".hword 0x0002, 0x0310, 0x0003, 0x0a00\n"
        ".hword 0x5001, 0xe285, 0x0002, 0xe355\n"
        ".hword 0xff57, 0xbaff, 0x9ff0, 0xe8bd\n"
        ".hword 0x1018, 0xe594, 0x0001, 0xe380\n"
        ".hword 0x001c, 0xe584, 0x0000, 0xe351\n"
        ".hword 0x0004, 0x1380, 0x001c, 0x1584\n"
        ".hword 0x2010, 0xe594, 0x7010, 0xe584\n"
        ".hword 0x1004, 0xe584, 0x200c, 0xe584\n"
        ".hword 0x0c01, 0xe3c0, 0x7018, 0xe584\n"
        ".hword 0xffac, 0xeaff, 0x53c4, 0x004c\n"
        ".hword 0x007b, 0x0100, 0xe098, 0x0044\n"
        ".hword 0x77ad, 0x0040\n"
    );
}

// DECOMP_FUNC(0x002f5584, 788)
extern "C" __attribute__((naked)) void engine_func_002f5584() {
    asm volatile(
        ".arm\n"
        ".hword 0x41f0, 0xe92d, 0xd020, 0xe24d\n"
        ".hword 0x4000, 0xe1a0, 0x0000, 0xe3a0\n"
        ".hword 0x5001, 0xe1a0, 0x12e8, 0xe59f\n"
        ".hword 0x0008, 0xe58d, 0x000c, 0xe58d\n"
        ".hword 0x0010, 0xe58d, 0x0014, 0xe58d\n"
        ".hword 0x0018, 0xe58d, 0x0000, 0xe591\n"
        ".hword 0x6003, 0xe1a0, 0x82cc, 0xe59f\n"
        ".hword 0x3000, 0xe1a0, 0x0000, 0xe58d\n"
        ".hword 0x3030, 0xe513, 0x0020, 0xe591\n"
        ".hword 0x7002, 0xe1a0, 0x200d, 0xe1a0\n"
        ".hword 0x0003, 0xe78d, 0x0024, 0xe591\n"
        ".hword 0x3002, 0xe1a0, 0x0000, 0xe354\n"
        ".hword 0x0004, 0xe58d, 0x1005, 0xe1a0\n"
        ".hword 0x2001, 0xe3a0, 0x0008, 0xe1a0\n"
        ".hword 0x0007, 0x0a00, 0x0001, 0xe354\n"
        ".hword 0x000a, 0x0a00, 0x0002, 0xe354\n"
        ".hword 0x000d, 0x0a00, 0x0003, 0xe354\n"
        ".hword 0x0003, 0x01a0, 0x28dc, 0x0bfc\n"
        ".hword 0x000b, 0xea00, 0x0003, 0xe1a0\n"
        ".hword 0x55e1, 0xebfd, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0x0006, 0xea00\n"
        ".hword 0x0003, 0xe1a0, 0x55ae, 0xebfd\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0x0001, 0xea00, 0x0003, 0xe1a0\n"
        ".hword 0x5a3b, 0xebff, 0x1bff, 0xe200\n"
        ".hword 0x1521, 0xe1a0, 0x0011, 0xe351\n"
        ".hword 0x0005, 0x1a00, 0x1b00, 0xe1a0\n"
        ".hword 0x1b21, 0xe1a0, 0x0064, 0xe351\n"
        ".hword 0x0001, 0xba00, 0x00b3, 0xe351\n"
        ".hword 0x0001, 0xda00, 0x1fa0, 0xe1b0\n"
        ".hword 0x0041, 0x0a00, 0x0000, 0xe354\n"
        ".hword 0x300d, 0xe1a0, 0x1005, 0xe1a0\n"
        ".hword 0x2006, 0xe1a0, 0x0008, 0xe1a0\n"
        ".hword 0x0007, 0x0a00, 0x0001, 0xe354\n"
        ".hword 0x000a, 0x0a00, 0x0002, 0xe354\n"
        ".hword 0x0003, 0x01a0, 0xaf19, 0x0bff\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0x0006, 0xea00, 0x0003, 0xe1a0\n"
        ".hword 0x59ca, 0xebff, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0x0001, 0xea00\n"
        ".hword 0x0003, 0xe1a0, 0xaad9, 0xebfc\n"
        ".hword 0x1102, 0xe210, 0x002a, 0x5a00\n"
        ".hword 0x0005, 0xe1b0, 0x0008, 0x0a00\n"
        ".hword 0x1004, 0xe1b0, 0x000a, 0x0a00\n"
        ".hword 0x0001, 0xe351, 0x000d, 0x0a00\n"
        ".hword 0x0002, 0xe354, 0xaf3b, 0x0bff\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0x000a, 0xea00, 0x118c, 0xe59f\n"
        ".hword 0x0184, 0xe59f, 0x0010, 0xe581\n"
        ".hword 0x0006, 0xea00, 0xf000, 0xe320\n"
        ".hword 0x59f1, 0xebff, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0x0001, 0xea00\n"
        ".hword 0xf000, 0xe320, 0xab03, 0xebfc\n"
        ".hword 0x0000, 0xe354, 0x300d, 0xe1a0\n"
        ".hword 0x1005, 0xe1a0, 0x2006, 0xe1a0\n"
        ".hword 0x0008, 0xe1a0, 0x0007, 0x0a00\n"
        ".hword 0x0001, 0xe354, 0x000a, 0x0a00\n"
        ".hword 0x0002, 0xe354, 0x0003, 0x01a0\n"
        ".hword 0xaeec, 0x0bff, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0x0006, 0xea00\n"
        ".hword 0x0003, 0xe1a0, 0x599d, 0xebff\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0x0001, 0xea00, 0x0003, 0xe1a0\n"
        ".hword 0xaaac, 0xebfc, 0x0102, 0xe210\n"
        ".hword 0x0033, 0x4a00, 0x0000, 0xe354\n"
        ".hword 0xc00d, 0xe1a0, 0x2007, 0xe1a0\n"
        ".hword 0x3006, 0xe1a0, 0x1000, 0xe3a0\n"
        ".hword 0x0008, 0xe1a0, 0x0007, 0x0a00\n"
        ".hword 0x0001, 0xe354, 0x000a, 0x0a00\n"
        ".hword 0x0002, 0xe354, 0x000c, 0x01a0\n"
        ".hword 0x81d9, 0x0bff, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0x0006, 0xea00\n"
        ".hword 0x000c, 0xe1a0, 0xaa6d, 0xebfc\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0x0001, 0xea00, 0x000c, 0xe1a0\n"
        ".hword 0x6ae0, 0xebfc, 0x0102, 0xe210\n"
        ".hword 0x001b, 0x4a00, 0x0000, 0xe354\n"
        ".hword 0x100d, 0xe1a0, 0x0008, 0xe1a0\n"
        ".hword 0x0009, 0x0a00, 0x0001, 0xe354\n"
        ".hword 0x000c, 0x0a00, 0x0002, 0xe354\n"
        ".hword 0x000f, 0x0a00, 0x0003, 0xe354\n"
        ".hword 0x0001, 0x01a0, 0x5528, 0x0bfd\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0x000b, 0xea00, 0x0001, 0xe1a0\n"
        ".hword 0x5515, 0xebfd, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0x0006, 0xea00\n"
        ".hword 0x0001, 0xe1a0, 0x5502, 0xebfd\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0x0001, 0xea00, 0x0001, 0xe1a0\n"
        ".hword 0x54ef, 0xebfd, 0x0102, 0xe210\n"
        ".hword 0x0005, 0x5a00, 0x1000, 0xe3a0\n"
        ".hword 0x000d, 0xe1a0, 0x1858, 0xebff\n"
        ".hword 0xd020, 0xe28d, 0x0000, 0xe3a0\n"
        ".hword 0x81f0, 0xe8bd, 0x1000, 0xe3a0\n"
        ".hword 0x000d, 0xe1a0, 0x1852, 0xebff\n"
        ".hword 0xd020, 0xe28d, 0x0001, 0xe3a0\n"
        ".hword 0x81f0, 0xe8bd, 0x0768, 0x0042\n"
        ".hword 0xffff, 0xe7e3, 0x4464, 0xc880\n"
        ".hword 0x51e8, 0x0046\n"
    );
}

// DECOMP_FUNC(0x003525b8, 796)
extern "C" __attribute__((naked)) void engine_func_003525b8() {
    asm volatile(
        ".arm\n"
        ".hword 0x4ff0, 0xe92d, 0x6001, 0xe1a0\n"
        ".hword 0x1010, 0xe283, 0x7002, 0xe1a0\n"
        ".hword 0xd054, 0xe24d, 0x0006, 0xe891\n"
        ".hword 0x4003, 0xe1a0, 0x5000, 0xe1a0\n"
        ".hword 0x04bd, 0xeb00, 0x1fa0, 0xe1b0\n"
        ".hword 0x0092, 0x1a00, 0x0005, 0xe1a0\n"
        ".hword 0x64f4, 0xe1cd, 0x04b1, 0xeb00\n"
        ".hword 0x0000, 0xe58d, 0x0005, 0xe1a0\n"
        ".hword 0x04b1, 0xeb00, 0x0004, 0xe58d\n"
        ".hword 0xb004, 0xe285, 0x60d8, 0xe1c5\n"
        ".hword 0x034f, 0xeb00, 0x0e27, 0xe28f\n"
        ".hword 0x9f63, 0xebfb, 0x0e27, 0xe28f\n"
        ".hword 0x9f61, 0xebfb, 0x0e27, 0xe28f\n"
        ".hword 0x9f5f, 0xebfb, 0x0f9d, 0xe28f\n"
        ".hword 0x9f5d, 0xebfb, 0x0f9f, 0xe28f\n"
        ".hword 0x9f5b, 0xebfb, 0x0028, 0xe5d4\n"
        ".hword 0x031a, 0xeb00, 0x0000, 0xe594\n"
        ".hword 0x1008, 0xe594, 0xc004, 0xe1a0\n"
        ".hword 0x0000, 0xe350, 0x0004, 0x01a0\n"
        ".hword 0x004c, 0xe58d, 0x3018, 0xe594\n"
        ".hword 0x0000, 0xe351, 0x100c, 0x01a0\n"
        ".hword 0x201c, 0xe594, 0x0000, 0xe353\n"
        ".hword 0x0003, 0x11a0, 0x0004, 0x01a0\n"
        ".hword 0x0000, 0xe352, 0x8004, 0xe1a0\n"
        ".hword 0x2004, 0x01a0, 0x402c, 0xe284\n"
        ".hword 0x9238, 0xe59f, 0x4010, 0xe894\n"
        ".hword 0xb038, 0xe58d, 0xa230, 0xe59f\n"
        ".hword 0xe034, 0xe58d, 0x63fc, 0xe1cd\n"
        ".hword 0x6001, 0x13a0, 0x6000, 0x03a0\n"
        ".hword 0x0000, 0xe353, 0x3001, 0x13a0\n"
        ".hword 0x7028, 0xe28d, 0x4030, 0xe58d\n"
        ".hword 0x3024, 0xe58d, 0x420c, 0xe59f\n"
        ".hword 0x0044, 0xe887, 0x700c, 0xe28d\n"
        ".hword 0x20d0, 0xe1cd, 0x4000, 0xe594\n"
        ".hword 0x0020, 0xe58d, 0x21f8, 0xe1cd\n"
        ".hword 0x21f4, 0xe59f, 0x4014, 0xe58d\n"
        ".hword 0x000c, 0xe598, 0x2000, 0xe592\n"
        ".hword 0x1008, 0xe58d, 0x9000, 0xe58d\n"
        ".hword 0x2004, 0xe58d, 0x0401, 0xe887\n"
        ".hword 0x7044, 0xe28d, 0x3004, 0xe59c\n"
        ".hword 0x0007, 0xe897, 0x34d0, 0xeb00\n"
        ".hword 0x1fa0, 0xe1b0, 0x0000, 0x03a0\n"
        ".hword 0x1fa0, 0xe1b0, 0x0047, 0x1a00\n"
        ".hword 0x0004, 0xe595, 0x7000, 0xe3a0\n"
        ".hword 0xb007, 0xe1a0, 0x0000, 0xe350\n"
        ".hword 0x004f, 0x0a00, 0x0004, 0xe590\n"
        ".hword 0x0000, 0xe350, 0xa010, 0x83a0\n"
        ".hword 0x004b, 0x9a00, 0x0004, 0xe595\n"
        ".hword 0x0000, 0xe350, 0x0006, 0x0a00\n"
        ".hword 0x2004, 0xe590, 0x0002, 0xe157\n"
        ".hword 0x0003, 0x8a00, 0x1000, 0xe590\n"
        ".hword 0x0087, 0xe087, 0x4200, 0xe081\n"
        ".hword 0x0000, 0xea00, 0x4000, 0xe3a0\n"
        ".hword 0x9f4e, 0xe28f, 0x801c, 0xe594\n"
        ".hword 0x6000, 0xe3a0, 0x0000, 0xe358\n"
        ".hword 0x000a, 0x9a00, 0x0018, 0xe594\n"
        ".hword 0x2040, 0xe3a0, 0x1009, 0xe1a0\n"
        ".hword 0x0186, 0xe790, 0x879b, 0xebfd\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0028, 0x0a00, 0x6001, 0xe286\n"
        ".hword 0x0006, 0xe158, 0xfff4, 0x8aff\n"
        ".hword 0x000b, 0xe1a0, 0x200a, 0xe3a0\n"
        ".hword 0x1000, 0xe3a0, 0xce32, 0xfafd\n"
        ".hword 0x2070, 0xe6ff, 0x0004, 0xe594\n"
        ".hword 0x1000, 0xe594, 0xcc00, 0xe1a0\n"
        ".hword 0x3421, 0xe18c, 0x0720, 0xe15a\n"
        ".hword 0xc070, 0x06ff, 0x3603, 0xe1a0\n"
        ".hword 0x008c, 0x035c, 0x3623, 0xe1a0\n"
        ".hword 0x0000, 0x03a0, 0x0004, 0x0a00\n"
        ".hword 0x0720, 0xe15a, 0x0070, 0x06ff\n"
        ".hword 0x000d, 0x0350, 0x00ff, 0x13a0\n"
        ".hword 0x0001, 0x03a0, 0xc0ff, 0xe3cc\n"
        ".hword 0x000c, 0xe180, 0x1401, 0xe1a0\n"
        ".hword 0x0cff, 0xe3c0, 0x1cff, 0xe201\n"
        ".hword 0x0001, 0xe180, 0x0004, 0xe58d\n"
        ".hword 0x100d, 0xe1a0, 0x0005, 0xe1a0\n"
        ".hword 0x3000, 0xe58d, 0x0402, 0xeb00\n"
        ".hword 0x1000, 0xe1a0, 0x0fa0, 0xe1b0\n"
        ".hword 0x0007, 0x0a00, 0x0001, 0xe1a0\n"
        ".hword 0xd054, 0xe28d, 0x8ff0, 0xe8bd\n"
        ".hword 0x1018, 0xe594, 0x0004, 0xe3a0\n"
        ".hword 0x0186, 0xe080, 0x0000, 0xe791\n"
        ".hword 0xffd5, 0xeaff, 0x0004, 0xe595\n"
        ".hword 0x7001, 0xe287, 0x0000, 0xe350\n"
        ".hword 0x0004, 0x1590, 0x0007, 0xe150\n"
        ".hword 0xffb3, 0x8aff, 0x0004, 0xe595\n"
        ".hword 0x0000, 0xe350, 0x0008, 0x1590\n"
        ".hword 0xd054, 0xe28d, 0x0000, 0x1350\n"
        ".hword 0x0050, 0x059f, 0x0000, 0x13a0\n"
        ".hword 0x8ff0, 0xe8bd, 0x7250, 0x6369\n"
        ".hword 0x7365, 0x0000, 0x6152, 0x6974\n"
        ".hword 0x676e, 0x0073, 0x654e, 0x5377\n"
        ".hword 0x6e69, 0x6563, 0x0000, 0x0000\n"
        ".hword 0x6954, 0x6c74, 0x5665, 0x7265\n"
        ".hword 0x6973, 0x6e6f, 0x0000, 0x0000\n"
        ".hword 0x7973, 0x2e73, 0x7449, 0x6d65\n"
        ".hword 0x6f43, 0x6564, 0x0000, 0x0000\n"
        ".hword 0x655c, 0x004e, 0x675c, 0x004e\n"
        ".hword 0x1a54, 0x0047, 0x1a50, 0x0047\n"
        ".hword 0x3908, 0xc8a1\n"
    );
}

// DECOMP_FUNC(0x0027d35c, 800)
extern "C" __attribute__((naked)) void script_vm_func_0027d35c() {
    asm volatile(
        ".arm\n"
        ".hword 0x02f0, 0xe59f, 0x4070, 0xe92d\n"
        ".hword 0x4000, 0xe590, 0x02dc, 0xe1c4\n"
        ".hword 0xac0a, 0xeb02, 0x62e0, 0xe59f\n"
        ".hword 0x0000, 0xe350, 0x0002, 0x0a00\n"
        ".hword 0x00d2, 0xe1d0, 0x02bc, 0xe1c6\n"
        ".hword 0x002e, 0xe5c6, 0x02cc, 0xe59f\n"
        ".hword 0x1045, 0xe5d0, 0x0000, 0xe351\n"
        ".hword 0x0005, 0x1a00, 0x001d, 0xe5d0\n"
        ".hword 0x0000, 0xe350, 0x0002, 0x0a00\n"
        ".hword 0x0045, 0xe5d4, 0x0000, 0xe350\n"
        ".hword 0x0004, 0x0a00, 0xf000, 0xe320\n"
        ".hword 0xca1a, 0xebff, 0x0001, 0xe3a0\n"
        ".hword 0x011d, 0xe5c6, 0x8070, 0xe8bd\n"
        ".hword 0xf000, 0xe320, 0xf819, 0xebfd\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x000c, 0x0a00, 0x0024, 0xe594\n"
        ".hword 0x0017, 0xe350, 0x0018, 0x1350\n"
        ".hword 0xe166, 0x1bff, 0x002c, 0xe594\n"
        ".hword 0x526c, 0xe59f, 0x0018, 0xe350\n"
        ".hword 0x0009, 0x0a00, 0x5f14, 0xebff\n"
        ".hword 0x0001, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0018, 0x0a00, 0x0025, 0xea00\n"
        ".hword 0x02dc, 0xe1c4, 0xdd2a, 0xebfc\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0xfff1, 0xeaff, 0xf000, 0xe320\n"
        ".hword 0x20ee, 0xeb00, 0x0001, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x001b, 0x1a00\n"
        ".hword 0x002c, 0xe3a0, 0x0dda, 0xeb01\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0016, 0x1a00, 0x0214, 0xe59f\n"
        ".hword 0x0028, 0xe586, 0x289e, 0xeb00\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0074, 0x0a00, 0x0003, 0xe350\n"
        ".hword 0x0072, 0x0a00, 0x8070, 0xe8bd\n"
        ".hword 0x02dc, 0xe1c4, 0xca0f, 0xebff\n"
        ".hword 0x1180, 0xe060, 0x0200, 0xe081\n"
        ".hword 0x0100, 0xe085, 0x0014, 0xe590\n"
        ".hword 0x0000, 0xe350, 0x0005, 0x0a00\n"
        ".hword 0x0028, 0xe586, 0x288e, 0xeb00\n"
        ".hword 0x0000, 0xe350, 0x0003, 0x1350\n"
        ".hword 0x0064, 0x0a00, 0x8070, 0xe8bd\n"
        ".hword 0x002c, 0xe594, 0x0018, 0xe350\n"
        ".hword 0x1030, 0x1594, 0x1001, 0x03a0\n"
        ".hword 0xc9fe, 0xebff, 0x1180, 0xe060\n"
        ".hword 0x0200, 0xe081, 0x5100, 0xe085\n"
        ".hword 0x0008, 0xe595, 0x0028, 0xe586\n"
        ".hword 0x0010, 0xe595, 0x0000, 0xe350\n"
        ".hword 0x000f, 0x0a00, 0x00fc, 0xe1d5\n"
        ".hword 0x0000, 0xe350, 0x0003, 0x0a00\n"
        ".hword 0x0daf, 0xeb01, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x0008, 0x0a00\n"
        ".hword 0x00fe, 0xe1d5, 0x0000, 0xe350\n"
        ".hword 0x0003, 0x0a00, 0x0da8, 0xeb01\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0001, 0x1a00, 0x0010, 0xe595\n"
        ".hword 0x0028, 0xe586, 0x002c, 0xe594\n"
        ".hword 0x0013, 0xe350, 0x0005, 0x0a00\n"
        ".hword 0x0018, 0xe350, 0x0019, 0x1a00\n"
        ".hword 0x20ac, 0xeb00, 0x0005, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x000a, 0x1a00\n"
        ".hword 0x0124, 0xe59f, 0x0d98, 0xeb01\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0005, 0x0a00, 0x0114, 0xe59f\n"
        ".hword 0x0d93, 0xeb01, 0x0000, 0xe350\n"
        ".hword 0x010c, 0x059f, 0x0028, 0x0586\n"
        ".hword 0x002b, 0x0a00, 0x002c, 0xe594\n"
        ".hword 0x0013, 0xe350, 0x0007, 0x1a00\n"
        ".hword 0x0030, 0xe594, 0x0004, 0xe350\n"
        ".hword 0x0004, 0xca00, 0x00b8, 0xe3a0\n"
        ".hword 0x0d87, 0xeb01, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x0020, 0x0a00\n"
        ".hword 0x0040, 0xe594, 0x0001, 0xe350\n"
        ".hword 0x0002, 0x1350, 0x001c, 0x0a00\n"
        ".hword 0x002c, 0xe594, 0x0029, 0xe350\n"
        ".hword 0x002a, 0x1350, 0x002b, 0x1350\n"
        ".hword 0x0017, 0x0a00, 0x4c35, 0xeb00\n"
        ".hword 0x0000, 0xe350, 0x1c01, 0x1240\n"
        ".hword 0x105f, 0x1251, 0x0012, 0x0a00\n"
        ".hword 0x0e16, 0xe350, 0x1c01, 0x1240\n"
        ".hword 0x1061, 0x1251, 0x000e, 0x0a00\n"
        ".hword 0x0f59, 0xe350, 0x1c01, 0x1240\n"
        ".hword 0x1065, 0x1251, 0x000a, 0x0a00\n"
        ".hword 0x1c01, 0xe240, 0x1066, 0xe251\n"
        ".hword 0x1c01, 0x1240, 0x1067, 0x1251\n"
        ".hword 0x0f5a, 0x1350, 0x0004, 0x0a00\n"
        ".hword 0x293c, 0xeb00, 0x0001, 0xe350\n"
        ".hword 0x0060, 0x059f, 0x0060, 0x159f\n"
        ".hword 0x0028, 0xe586, 0x0028, 0xe596\n"
        ".hword 0x282b, 0xeb00, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x0004, 0x0a00\n"
        ".hword 0x0003, 0xe350, 0xff62, 0x1aff\n"
        ".hword 0x0028, 0xe596, 0x4070, 0xe8bd\n"
        ".hword 0x27d3, 0xea00, 0xf000, 0xe320\n"
        ".hword 0xc976, 0xebff, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0xfff7, 0xeaff\n"
        ".hword 0x7e28, 0x0044, 0xf91c, 0x0049\n"
        ".hword 0xfa1c, 0x0049, 0x8e18, 0x0044\n"
        ".hword 0x0086, 0x0100, 0x062c, 0x0000\n"
        ".hword 0x0648, 0x0000, 0x007a, 0x0100\n"
        ".hword 0x0037, 0x0100, 0x0038, 0x0100\n"
    );
}

// DECOMP_FUNC(0x0037dc24, 800)
extern "C" __attribute__((naked)) void ui_func_0037dc24() {
    asm volatile(
        ".arm\n"
        ".hword 0x4ff0, 0xe92d, 0x6000, 0xe1a0\n"
        ".hword 0x7001, 0xe1a0, 0xd024, 0xe24d\n"
        ".hword 0xb000, 0xe3a0, 0x0085, 0xe5d0\n"
        ".hword 0x12f0, 0xe59f, 0x9003, 0xe1a0\n"
        ".hword 0x300b, 0xe1a0, 0x0290, 0xe002\n"
        ".hword 0x8048, 0xe59d, 0x00c0, 0xe596\n"
        ".hword 0x500b, 0xe1a0, 0x3291, 0xe0e2\n"
        ".hword 0x0000, 0xe358, 0x50c4, 0x1596\n"
        ".hword 0xa074, 0xe280, 0x0ab2, 0xeddf\n"
        ".hword 0x0342, 0xe1a0, 0x0000, 0x1355\n"
        ".hword 0x4fc2, 0xe040, 0x0005, 0x0a00\n"
        ".hword 0x4a10, 0xee00, 0x7126, 0xe5c5\n"
        ".hword 0x0ac0, 0xeeb8, 0x0a20, 0xee20\n"
        ".hword 0x0a00, 0xee20, 0x0a40, 0xed85\n"
        ".hword 0x0027, 0xe5d6, 0x0000, 0xe350\n"
        ".hword 0x0012, 0x0a00, 0x50c4, 0xe596\n"
        ".hword 0x0000, 0xe355, 0x0011, 0x0a00\n"
        ".hword 0x0090, 0xe5d5, 0x0004, 0xe350\n"
        ".hword 0x0007, 0x0a00, 0x4a10, 0xee00\n"
        ".hword 0x9120, 0xe585, 0x7126, 0xe5c5\n"
        ".hword 0x0ac0, 0xeeb8, 0x0a20, 0xee20\n"
        ".hword 0x0a00, 0xee20, 0x0a40, 0xed85\n"
        ".hword 0x0039, 0xea00, 0x0005, 0xe1a0\n"
        ".hword 0xcd3d, 0xebf6, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0x0001, 0xea00\n"
        ".hword 0x0000, 0xe355, 0x0032, 0x1a00\n"
        ".hword 0x0000, 0xe358, 0x823c, 0xe59f\n"
        ".hword 0xe004, 0xe28d, 0x0004, 0xe288\n"
        ".hword 0x8018, 0xe288, 0x100f, 0xe890\n"
        ".hword 0x0120, 0xe898, 0x100f, 0xe88e\n"
        ".hword 0x0018, 0xe28d, 0x200d, 0xe1a0\n"
        ".hword 0x0120, 0xe880, 0x0050, 0xe596\n"
        ".hword 0x4008, 0xe58d, 0x0081, 0xe88d\n"
        ".hword 0x0000, 0x13e0, 0x0009, 0x01a0\n"
        ".hword 0x000c, 0xe58d, 0x08d7, 0xe1d6\n"
        ".hword 0x0010, 0xe58d, 0x0001, 0xe5da\n"
        ".hword 0x1089, 0xe5d6, 0x601c, 0xe58d\n"
        ".hword 0x0001, 0xe080, 0x0014, 0xe58d\n"
        ".hword 0x104d, 0xe5d6, 0x00c0, 0xe596\n"
        ".hword 0x06df, 0xeb00, 0x5000, 0xe1b0\n"
        ".hword 0xf000, 0xe320, 0x006f, 0x0a00\n"
        ".hword 0x0128, 0xe5d5, 0x0000, 0xe350\n"
        ".hword 0x40c4, 0x1596, 0x0000, 0x1354\n"
        ".hword 0x000c, 0x0a00, 0x0128, 0xe5d4\n"
        ".hword 0x1128, 0xe5d5, 0x0001, 0xe150\n"
        ".hword 0x0005, 0x1a00, 0x107e, 0xe3a0\n"
        ".hword 0x0090, 0xe284, 0xdf2b, 0xebfa\n"
        ".hword 0x0004, 0xe1a0, 0xf000, 0xe320\n"
        ".hword 0xdf17, 0xebfa, 0x4138, 0xe594\n"
        ".hword 0x0000, 0xe354, 0xfff2, 0x1aff\n"
        ".hword 0x00c4, 0xe596, 0x0138, 0xe585\n"
        ".hword 0x50c4, 0xe586, 0x108c, 0xe5d6\n"
        ".hword 0x007f, 0xe351, 0x0090, 0x9285\n"
        ".hword 0xf033, 0x9bff, 0x108d, 0xe5d6\n"
        ".hword 0x007f, 0xe351, 0x0090, 0x9285\n"
        ".hword 0xf011, 0x9bff, 0x108e, 0xe5d6\n"
        ".hword 0x007f, 0xe351, 0x0090, 0x9285\n"
        ".hword 0x1018, 0x95c0, 0x108f, 0xe5d6\n"
        ".hword 0x007f, 0xe351, 0x0090, 0x9285\n"
        ".hword 0xdf12, 0x9bfa, 0x19f0, 0xe1d6\n"
        ".hword 0x007f, 0xe351, 0x0090, 0xd285\n"
        ".hword 0xeffd, 0xdbff, 0x004b, 0xe5d6\n"
        ".hword 0x0a1a, 0xed96, 0x0000, 0xe350\n"
        ".hword 0x0004, 0x0a00, 0x008a, 0xe5d6\n"
        ".hword 0x0007, 0xe040, 0x0a90, 0xee00\n"
        ".hword 0x0ae0, 0xeef8, 0x0a80, 0xee30\n"
        ".hword 0x008b, 0xe5d6, 0x0000, 0xe350\n"
        ".hword 0x0012, 0x0a00, 0x0090, 0xe000\n"
        ".hword 0x0a3d, 0xeddf, 0x2001, 0xe3a0\n"
        ".hword 0x0ac0, 0xeef4, 0xfa10, 0xeef1\n"
        ".hword 0x0a90, 0xee00, 0x1a40, 0x9eb0\n"
        ".hword 0x1a40, 0x8eb1, 0x0ae0, 0xeef8\n"
        ".hword 0x0a20, 0xee61, 0x0ae0, 0xeefd\n"
        ".hword 0x0a90, 0xee10, 0x02c0, 0xe1a0\n"
        ".hword 0x1100, 0xe080, 0x0005, 0xe1a0\n"
        ".hword 0x07bb, 0xeb00, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0x0003, 0xea00\n"
        ".hword 0x2000, 0xe3a0, 0x1009, 0xe1a0\n"
        ".hword 0x0005, 0xe1a0, 0x07b4, 0xeb00\n"
        ".hword 0x0049, 0xe5d6, 0x4e11, 0xe285\n"
        ".hword 0x708a, 0xe5c6, 0x0000, 0xe350\n"
        ".hword 0x00b4, 0xe1d4, 0x10b2, 0xe1d4\n"
        ".hword 0x7000, 0x13a0, 0x70ff, 0x03a0\n"
        ".hword 0x0001, 0xe150, 0x0001, 0x25d4\n"
        ".hword 0x8000, 0xe3a0, 0x0006, 0x2a00\n"
        ".hword 0x2001, 0xe5d4, 0x9000, 0xe5d4\n"
        ".hword 0x2009, 0xe042, 0x0092, 0xe000\n"
        ".hword 0x209e, 0xebfd, 0x0009, 0xe080\n"
        ".hword 0x00ff, 0xe200, 0x0000, 0xe5c4\n"
        ".hword 0x7001, 0xe5c4, 0x80b2, 0xe1c4\n"
        ".hword 0xb0b4, 0xe1c4, 0x00c0, 0xe596\n"
        ".hword 0x005c, 0xe5d0, 0x00c9, 0xe5c5\n"
        ".hword 0x00c0, 0xe596, 0x0034, 0xe5d0\n"
        ".hword 0x0124, 0xe5c5, 0x00c0, 0xe596\n"
        ".hword 0x0035, 0xe5d0, 0x0125, 0xe5c5\n"
        ".hword 0x14d1, 0xe1d6, 0x0134, 0xe595\n"
        ".hword 0x90be, 0xebfc, 0x0005, 0xe1a0\n"
        ".hword 0xd024, 0xe28d, 0x8ff0, 0xe8bd\n"
        ".hword 0x0409, 0x8102, 0x0204, 0x3c01\n"
        ".hword 0x19f8, 0x0041, 0x0000, 0x0000\n"
    );
}

// DECOMP_FUNC(0x0027b100, 804)
extern "C" __attribute__((naked)) void script_vm_func_0027b100() {
    asm volatile(
        ".arm\n"
        ".hword 0x41f0, 0xe92d, 0x5000, 0xe3a0\n"
        ".hword 0x72d4, 0xe59f, 0x62d4, 0xe59f\n"
        ".hword 0x8b10, 0xed2d, 0xbab4, 0xeddf\n"
        ".hword 0xcab4, 0xeddf, 0xbab4, 0xed9f\n"
        ".hword 0xdab4, 0xed9f, 0xcab4, 0xed9f\n"
        ".hword 0xdab4, 0xeddf, 0xeab4, 0xed9f\n"
        ".hword 0x8ab4, 0xed9f, 0x8ab4, 0xeddf\n"
        ".hword 0xeab4, 0xeddf, 0xfab4, 0xed9f\n"
        ".hword 0xaab4, 0xed9f, 0xfab4, 0xeddf\n"
        ".hword 0x0000, 0xe597, 0x1185, 0xe085\n"
        ".hword 0x4181, 0xe080, 0x0014, 0xe5f4\n"
        ".hword 0x0000, 0xe350, 0x009b, 0x0a00\n"
        ".hword 0x0000, 0xe596, 0x0004, 0xe350\n"
        ".hword 0x0002, 0x1a00, 0x0004, 0xe596\n"
        ".hword 0x0001, 0xe350, 0x002f, 0x0a00\n"
        ".hword 0x0024, 0xe594, 0x0002, 0xe350\n"
        ".hword 0x0014, 0x1a00, 0x0a02, 0xed94\n"
        ".hword 0x9a01, 0xedd4, 0x9a03, 0xed94\n"
        ".hword 0xaa6b, 0xee70, 0x0a07, 0xed94\n"
        ".hword 0x0a08, 0xee20, 0x1d76, 0xeb00\n"
        ".hword 0x9a0b, 0xee40, 0x0a07, 0xed94\n"
        ".hword 0x0a08, 0xee20, 0x1d13, 0xeb00\n"
        ".hword 0x9a0b, 0xee00, 0x3a4a, 0xeeb0\n"
        ".hword 0x2a6c, 0xeef0, 0x2a4d, 0xeeb0\n"
        ".hword 0x0a6a, 0xeef0, 0x0a69, 0xeeb0\n"
        ".hword 0x1a07, 0xedd4, 0x0000, 0xe3a0\n"
        ".hword 0x1a49, 0xeeb0, 0xb091, 0xebff\n"
        ".hword 0x0024, 0xe594, 0x000a, 0xe350\n"
        ".hword 0x0014, 0x1a00, 0x0a02, 0xed94\n"
        ".hword 0x9a01, 0xedd4, 0x9a03, 0xed94\n"
        ".hword 0xaa4c, 0xee70, 0x0a07, 0xed94\n"
        ".hword 0x0a08, 0xee20, 0x1d5e, 0xeb00\n"
        ".hword 0x9a0b, 0xee40, 0x0a07, 0xed94\n"
        ".hword 0x0a08, 0xee20, 0x1cfb, 0xeb00\n"
        ".hword 0x1a49, 0xeeb0, 0x3a4a, 0xeeb0\n"
        ".hword 0x2a6d, 0xeef0, 0x2a4d, 0xeeb0\n"
        ".hword 0x0a6a, 0xeef0, 0x1a07, 0xedd4\n"
        ".hword 0x1a0b, 0xee00, 0x0a69, 0xeeb0\n"
        ".hword 0x0000, 0xe3a0, 0xb079, 0xebff\n"
        ".hword 0x0024, 0xe594, 0x0007, 0xe350\n"
        ".hword 0x0013, 0x1a00, 0x0a07, 0xed94\n"
        ".hword 0x9a01, 0xedd4, 0xaa02, 0xedd4\n"
        ".hword 0x0a08, 0xee20, 0x9a03, 0xed94\n"
        ".hword 0x1d47, 0xeb00, 0x9a28, 0xee40\n"
        ".hword 0x0a07, 0xed94, 0x0a08, 0xee20\n"
        ".hword 0x1ce4, 0xeb00, 0x9a28, 0xee00\n"
        ".hword 0x3a4a, 0xeeb0, 0x2a6e, 0xeef0\n"
        ".hword 0x2a4f, 0xeeb0, 0x0a6a, 0xeef0\n"
        ".hword 0x0a69, 0xeeb0, 0x1a07, 0xedd4\n"
        ".hword 0x0000, 0xe3a0, 0x1a49, 0xeeb0\n"
        ".hword 0xb062, 0xebff, 0x0024, 0xe594\n"
        ".hword 0x0009, 0xe350, 0x0013, 0x1a00\n"
        ".hword 0x0a07, 0xed94, 0x9a01, 0xedd4\n"
        ".hword 0xaa02, 0xedd4, 0x0a08, 0xee20\n"
        ".hword 0x9a03, 0xed94, 0x1d30, 0xeb00\n"
        ".hword 0x9a28, 0xee40, 0x0a07, 0xed94\n"
        ".hword 0x0a08, 0xee20, 0x1ccd, 0xeb00\n"
        ".hword 0x1a49, 0xeeb0, 0x3a4a, 0xeeb0\n"
        ".hword 0x2a6e, 0xeef0, 0x2a4e, 0xeeb0\n"
        ".hword 0x0a6a, 0xeef0, 0x1a07, 0xedd4\n"
        ".hword 0x1a28, 0xee00, 0x0a69, 0xeeb0\n"
        ".hword 0x0000, 0xe3a0, 0xb04b, 0xebff\n"
        ".hword 0x0024, 0xe594, 0x000b, 0xe350\n"
        ".hword 0x0013, 0x1a00, 0x0a07, 0xed94\n"
        ".hword 0x9a01, 0xedd4, 0xaa02, 0xedd4\n"
        ".hword 0x0a08, 0xee20, 0x9a03, 0xed94\n"
        ".hword 0x1d19, 0xeb00, 0x9a28, 0xee40\n"
        ".hword 0x0a07, 0xed94, 0x0a08, 0xee20\n"
        ".hword 0x1cb6, 0xeb00, 0x1a49, 0xeeb0\n"
        ".hword 0x3a4a, 0xeeb0, 0x2a6e, 0xeef0\n"
        ".hword 0x2a4f, 0xeeb0, 0x0a6a, 0xeef0\n"
        ".hword 0x1a07, 0xedd4, 0x1a28, 0xee00\n"
        ".hword 0x0a69, 0xeeb0, 0x0000, 0xe3a0\n"
        ".hword 0xb034, 0xebff, 0x0024, 0xe594\n"
        ".hword 0x000f, 0xe350, 0x0007, 0x1a00\n"
        ".hword 0x2a4a, 0xeeb0, 0x1004, 0xe284\n"
        ".hword 0x1a07, 0xedd4, 0x0000, 0xe3a0\n"
        ".hword 0x0a03, 0xec91, 0x3a42, 0xeeb0\n"
        ".hword 0x2a42, 0xeef0, 0xb029, 0xebff\n"
        ".hword 0x0024, 0xe594, 0x0010, 0xe350\n"
        ".hword 0x0007, 0x1a00, 0x2a4a, 0xeeb0\n"
        ".hword 0x1004, 0xe284, 0x1a07, 0xedd4\n"
        ".hword 0x0000, 0xe3a0, 0x0a03, 0xec91\n"
        ".hword 0x3a42, 0xeeb0, 0x2a42, 0xeef0\n"
        ".hword 0xb01e, 0xebff, 0x0024, 0xe594\n"
        ".hword 0x0011, 0xe350, 0x0007, 0x1a00\n"
        ".hword 0x1a07, 0xedd4, 0x4004, 0xe284\n"
        ".hword 0x3a6f, 0xeeb0, 0x2a4a, 0xeef0\n"
        ".hword 0x0a03, 0xec94, 0x0000, 0xe3a0\n"
        ".hword 0x2a14, 0xed9f, 0xb013, 0xebff\n"
        ".hword 0x5001, 0xe285, 0x0018, 0xe355\n"
        ".hword 0xff5a, 0xbaff, 0x8b10, 0xecbd\n"
        ".hword 0x81f0, 0xe8bd, 0x7e70, 0x0044\n"
        ".hword 0xf91c, 0x0049, 0x0000, 0x43c8\n"
        ".hword 0x0000, 0x43af, 0x0000, 0x41a0\n"
        ".hword 0x0000, 0x42a0, 0x8000, 0x4409\n"
        ".hword 0x0000, 0x43fa, 0x0000, 0x4316\n"
        ".hword 0xfa35, 0x3c8e, 0x0000, 0xc18c\n"
        ".hword 0x0000, 0x4396, 0x0000, 0x4348\n"
        ".hword 0x0000, 0x4248, 0x0000, 0x4270\n"
        ".hword 0x0000, 0x42c8\n"
    );
}

// DECOMP_FUNC(0x00150320, 820)
extern "C" __attribute__((naked)) void ui_func_00150320() {
    asm volatile(
        ".arm\n"
        ".hword 0x4fff, 0xe92d, 0xd084, 0xe24d\n"
        ".hword 0x7002, 0xe1b0, 0x8001, 0xe1a0\n"
        ".hword 0x00be, 0x0a00, 0x022c, 0xe598\n"
        ".hword 0xb105, 0xe3a0, 0x6103, 0xe790\n"
        ".hword 0x9008, 0xe596, 0x0000, 0xe359\n"
        ".hword 0x0002, 0x0a00, 0x0000, 0xe599\n"
        ".hword 0x0000, 0xe1db, 0x9000, 0x13a0\n"
        ".hword 0x1240, 0xe591, 0x0051, 0xe5d9\n"
        ".hword 0x5103, 0xe791, 0x0000, 0xe350\n"
        ".hword 0x0005, 0x11a0, 0xc87a, 0x1b05\n"
        ".hword 0x0030, 0xe5d5, 0xa2bc, 0xe59f\n"
        ".hword 0x0000, 0xe350, 0x0001, 0x13a0\n"
        ".hword 0x0100, 0xe085, 0x100c, 0xe5b0\n"
        ".hword 0x4008, 0xe590, 0x0000, 0xe59a\n"
        ".hword 0x2004, 0xe1a0, 0x7267, 0xeb05\n"
        ".hword 0x0000, 0xe59a, 0x1003, 0xe3c4\n"
        ".hword 0x4000, 0xe081, 0x011a, 0xe3a0\n"
        ".hword 0x4000, 0xe58a, 0x0000, 0xe584\n"
        ".hword 0x0284, 0xe59f, 0x1004, 0xe284\n"
        ".hword 0xa000, 0xe3a0, 0x0401, 0xe881\n"
        ".hword 0x0028, 0xe597, 0x1274, 0xe59f\n"
        ".hword 0x000c, 0xe584, 0x0024, 0xe597\n"
        ".hword 0x0010, 0xe584, 0x0020, 0xe597\n"
        ".hword 0x0014, 0xe584, 0x0084, 0xe59d\n"
        ".hword 0x0008, 0xe590, 0x70a4, 0xe590\n"
        ".hword 0x0166, 0xe3a0, 0x01f8, 0xe1c4\n"
        ".hword 0x0008, 0xe596, 0x0000, 0xe350\n"
        ".hword 0x0002, 0x0a00, 0x1000, 0xe590\n"
        ".hword 0x1001, 0xe1db, 0x0000, 0x13a0\n"
        ".hword 0xb234, 0xe59f, 0x0050, 0xe5d0\n"
        ".hword 0x0000, 0xe350, 0x0020, 0x0a00\n"
        ".hword 0x200b, 0xe1a0, 0x0020, 0xe284\n"
        ".hword 0x1f52, 0xe287, 0x45a7, 0xeb05\n"
        ".hword 0x0054, 0xe284, 0x1f5e, 0xe287\n"
        ".hword 0x4596, 0xeb05, 0xa084, 0xe584\n"
        ".hword 0x1090, 0xe284, 0xa088, 0xe584\n"
        ".hword 0x05fe, 0xe3a0, 0xa08c, 0xe584\n"
        ".hword 0x0401, 0xe881, 0x109c, 0xe284\n"
        ".hword 0xa098, 0xe584, 0x0401, 0xe881\n"
        ".hword 0x10a8, 0xe284, 0xa0a4, 0xe584\n"
        ".hword 0x0401, 0xe881, 0x10c0, 0xe284\n"
        ".hword 0xa0b0, 0xe584, 0xa0b4, 0xe584\n"
        ".hword 0xa0b8, 0xe584, 0xa0bc, 0xe584\n"
        ".hword 0x0401, 0xe881, 0x10cc, 0xe284\n"
        ".hword 0xa0c8, 0xe584, 0x0401, 0xe881\n"
        ".hword 0x10d8, 0xe284, 0xa0d4, 0xe584\n"
        ".hword 0x0401, 0xe881, 0xa0e0, 0xe584\n"
        ".hword 0x001d, 0xea00, 0x008c, 0xe288\n"
        ".hword 0x2000, 0xe1a0, 0x0004, 0xe58d\n"
        ".hword 0x1f52, 0xe287, 0x0040, 0xe28d\n"
        ".hword 0x52f0, 0xeb05, 0x200b, 0xe1a0\n"
        ".hword 0x0020, 0xe284, 0x1040, 0xe28d\n"
        ".hword 0x4580, 0xeb05, 0x0008, 0xe1a0\n"
        ".hword 0xf000, 0xe320, 0x142c, 0xeb00\n"
        ".hword 0x1000, 0xe1a0, 0x2f5e, 0xe287\n"
        ".hword 0x0008, 0xe28d, 0x52e5, 0xeb05\n"
        ".hword 0x0054, 0xe284, 0x1008, 0xe28d\n"
        ".hword 0x4568, 0xeb05, 0x0008, 0xe1a0\n"
        ".hword 0xf000, 0xe320, 0x1422, 0xeb00\n"
        ".hword 0x2084, 0xe284, 0x1000, 0xe1a0\n"
        ".hword 0x0002, 0xe1a0, 0x4561, 0xeb05\n"
        ".hword 0x1004, 0xe59d, 0x00b4, 0xe284\n"
        ".hword 0x455e, 0xeb05, 0x0a4b, 0xed9f\n"
        ".hword 0x0a1c, 0xed8d, 0x0a1d, 0xed8d\n"
        ".hword 0x0a1e, 0xed8d, 0x0044, 0xe5b9\n"
        ".hword 0x0000, 0xe350, 0x7009, 0x1080\n"
        ".hword 0x700a, 0x01a0, 0x0000, 0xe357\n"
        ".hword 0x0005, 0x0a00, 0x0008, 0xe287\n"
        ".hword 0x0006, 0xe890, 0x0010, 0xe597\n"
        ".hword 0x0078, 0xe58d, 0x0070, 0xe28d\n"
        ".hword 0x0006, 0xe880, 0x00e4, 0xe284\n"
        ".hword 0x1070, 0xe28d, 0x458d, 0xeb05\n"
        ".hword 0x00f4, 0xe284, 0x1074, 0xe286\n"
        ".hword 0x458a, 0xeb05, 0x0f41, 0xe284\n"
        ".hword 0x1080, 0xe286, 0x4587, 0xeb05\n"
        ".hword 0xa114, 0xe584, 0x004c, 0xe596\n"
        ".hword 0x10c4, 0xe59f, 0x2f46, 0xe284\n"
        ".hword 0x00cc, 0xe590, 0x0003, 0xe882\n"
        ".hword 0x0000, 0xe3a0, 0x1030, 0xe5d5\n"
        ".hword 0x0000, 0xe351, 0x0001, 0x13a0\n"
        ".hword 0x0000, 0xe357, 0x0100, 0xe085\n"
        ".hword 0x0200, 0xe590, 0x0007, 0x0a00\n"
        ".hword 0x1004, 0xe5d7, 0x0000, 0xe351\n"
        ".hword 0x0004, 0x1a00, 0x104c, 0xe596\n"
        ".hword 0x20c8, 0xe591, 0x10cc, 0xe591\n"
        ".hword 0x1001, 0xe042, 0x0081, 0xe080\n"
        ".hword 0x1078, 0xe59f, 0x605c, 0xe59f\n"
        ".hword 0x4e12, 0xe284, 0x0102, 0xe380\n"
        ".hword 0x0003, 0xe884, 0x1024, 0xe285\n"
        ".hword 0x0000, 0xe596, 0x0f4a, 0xe280\n"
        ".hword 0x0000, 0xe586, 0x0006, 0xe891\n"
        ".hword 0x4002, 0xe1a0, 0x71cd, 0xeb05\n"
        ".hword 0x0000, 0xe596, 0x1003, 0xe3c4\n"
        ".hword 0x501c, 0xe285, 0x0001, 0xe080\n"
        ".hword 0x0000, 0xe586, 0x0012, 0xe895\n"
        ".hword 0x2004, 0xe1a0, 0x71c5, 0xeb05\n"
        ".hword 0x0000, 0xe596, 0x1003, 0xe3c4\n"
        ".hword 0x0001, 0xe080, 0x0000, 0xe586\n"
        ".hword 0xd094, 0xe28d, 0x8ff0, 0xe8bd\n"
        ".hword 0x52a0, 0x0046, 0x02c0, 0x804f\n"
        ".hword 0x02c0, 0x000f, 0x02c1, 0x03bf\n"
        ".hword 0x0000, 0x0000, 0x0228, 0x000f\n"
        ".hword 0x0227, 0x000f\n"
    );
}

// DECOMP_FUNC(0x0010f120, 836)
extern "C" __attribute__((naked)) void engine_func_0010f120() {
    asm volatile(
        ".arm\n"
        ".hword 0x4030, 0xe92d, 0x5000, 0xe1a0\n"
        ".hword 0x1a01, 0xe285, 0x8b06, 0xed2d\n"
        ".hword 0xd024, 0xe24d, 0x0001, 0xe3a0\n"
        ".hword 0x2003, 0xe3a0, 0x01e8, 0xe5c1\n"
        ".hword 0x21e9, 0xe5c1, 0x05b0, 0xe5c5\n"
        ".hword 0x01dc, 0xe5c1, 0x01e1, 0xe5c1\n"
        ".hword 0x1000, 0xe3a0, 0x2001, 0xe1a0\n"
        ".hword 0x15f4, 0xe5c5, 0x3282, 0xe085\n"
        ".hword 0x2001, 0xe282, 0xca01, 0xe283\n"
        ".hword 0x3282, 0xe085, 0x3a01, 0xe283\n"
        ".hword 0x1002, 0xe281, 0x0204, 0xe5cc\n"
        ".hword 0x000c, 0xe351, 0x2001, 0xe282\n"
        ".hword 0x0204, 0xe5c3, 0xfff4, 0xbaff\n"
        ".hword 0x0284, 0xe59f, 0xcc99, 0xeb06\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x30c2, 0x1b00, 0x4b01, 0xe285\n"
        ".hword 0x052c, 0xe585, 0x026c, 0xe59f\n"
        ".hword 0x4f4b, 0xe284, 0x3080, 0xe3a0\n"
        ".hword 0x2001, 0xe3a0, 0x100d, 0xe1a0\n"
        ".hword 0xdb1f, 0xeb06, 0xc000, 0xe594\n"
        ".hword 0x1000, 0xe1a0, 0x2000, 0xe59d\n"
        ".hword 0x3000, 0xe3a0, 0x000c, 0xe1a0\n"
        ".hword 0x3078, 0xeb00, 0x0000, 0xe3a0\n"
        ".hword 0xf000, 0xe320, 0xc968, 0xeb06\n"
        ".hword 0x0a10, 0xee00, 0x0000, 0xe3a0\n"
        ".hword 0x8a40, 0xeef8, 0xc96e, 0xeb06\n"
        ".hword 0x0a10, 0xee00, 0x8a89, 0xed9f\n"
        ".hword 0x9a87, 0xed9f, 0x0a68, 0xeef0\n"
        ".hword 0x2a48, 0xeeb0, 0x2a49, 0xeef0\n"
        ".hword 0x1a40, 0xeeb8, 0x1a48, 0xeef0\n"
        ".hword 0x0a48, 0xeeb0, 0x0b01, 0xe285\n"
        ".hword 0x0f7e, 0xe280, 0x4000, 0xe1a0\n"
        ".hword 0xb3d2, 0xeb06, 0x1001, 0xe3a0\n"
        ".hword 0x0004, 0xe1a0, 0xb3a0, 0xeb06\n"
        ".hword 0x0002, 0xe3a0, 0xf000, 0xe320\n"
        ".hword 0xc951, 0xeb06, 0x0a10, 0xee00\n"
        ".hword 0x0002, 0xe3a0, 0x8a40, 0xeef8\n"
        ".hword 0xc957, 0xeb06, 0x0a10, 0xee00\n"
        ".hword 0x2a49, 0xeef0, 0x2a48, 0xeeb0\n"
        ".hword 0x1a48, 0xeef0, 0x0a68, 0xeef0\n"
        ".hword 0x0b01, 0xe285, 0x1a40, 0xeeb8\n"
        ".hword 0x0a48, 0xeeb0, 0x0f8e, 0xe280\n"
        ".hword 0x4000, 0xe1a0, 0xb3bd, 0xeb06\n"
        ".hword 0x1001, 0xe3a0, 0x0004, 0xe1a0\n"
        ".hword 0xb38b, 0xeb06, 0x8a66, 0xeddf\n"
        ".hword 0x9a66, 0xed9f, 0x9a66, 0xeddf\n"
        ".hword 0xaa66, 0xed9f, 0x2a68, 0xeef0\n"
        ".hword 0x2a49, 0xeeb0, 0x1a69, 0xeef0\n"
        ".hword 0x1a4a, 0xeeb0, 0x0b01, 0xe285\n"
        ".hword 0x0f9e, 0xe280, 0x0a60, 0xeddf\n"
        ".hword 0x0a60, 0xed9f, 0x4000, 0xe1a0\n"
        ".hword 0xb3ac, 0xeb06, 0x1001, 0xe3a0\n"
        ".hword 0x0004, 0xe1a0, 0xb37a, 0xeb06\n"
        ".hword 0x2a68, 0xeef0, 0x2a49, 0xeeb0\n"
        ".hword 0x1a69, 0xeef0, 0x1a4a, 0xeeb0\n"
        ".hword 0x0b01, 0xe285, 0x0fae, 0xe280\n"
        ".hword 0x0a55, 0xeddf, 0x0a55, 0xed9f\n"
        ".hword 0x4000, 0xe1a0, 0xb39f, 0xeb06\n"
        ".hword 0x1001, 0xe3a0, 0x0004, 0xe1a0\n"
        ".hword 0xb36d, 0xeb06, 0x0a50, 0xed9f\n"
        ".hword 0x0a50, 0xeddf, 0x8a00, 0xed8d\n"
        ".hword 0x1004, 0xe28d, 0x4b01, 0xe285\n"
        ".hword 0x0a02, 0xec81, 0x4fbf, 0xe284\n"
        ".hword 0x0a4b, 0xed9f, 0x8a03, 0xed8d\n"
        ".hword 0x0a04, 0xed8d, 0x8a05, 0xed8d\n"
        ".hword 0x8a06, 0xed8d, 0x8a07, 0xed8d\n"
        ".hword 0x8a08, 0xed8d, 0x1001, 0xe3a0\n"
        ".hword 0x0004, 0xe1a0, 0xcbb3, 0xeb06\n"
        ".hword 0x300c, 0xe28d, 0x2018, 0xe28d\n"
        ".hword 0x100d, 0xe1a0, 0x0004, 0xe1a0\n"
        ".hword 0xcb54, 0xeb06, 0x8a3e, 0xed9f\n"
        ".hword 0x8a3e, 0xeddf, 0x9a3e, 0xed9f\n"
        ".hword 0x1a48, 0xeeb0, 0x0a68, 0xeef0\n"
        ".hword 0x0a49, 0xeeb0, 0x1a37, 0xeddf\n"
        ".hword 0x1001, 0xe3a0, 0x0004, 0xe1a0\n"
        ".hword 0xcb1f, 0xeb06, 0x4b03, 0xe285\n"
        ".hword 0x4004, 0xe284, 0x1001, 0xe3a0\n"
        ".hword 0x0004, 0xe1a0, 0xcb9f, 0xeb06\n"
        ".hword 0x300c, 0xe28d, 0x2018, 0xe28d\n"
        ".hword 0x100d, 0xe1a0, 0x0004, 0xe1a0\n"
        ".hword 0xcb40, 0xeb06, 0x1a48, 0xeeb0\n"
        ".hword 0x0a68, 0xeef0, 0x0a49, 0xeeb0\n"
        ".hword 0x1a2a, 0xeddf, 0x1001, 0xe3a0\n"
        ".hword 0x0004, 0xe1a0, 0xcb0e, 0xeb06\n"
        ".hword 0x0b01, 0xe285, 0x0f6d, 0xe280\n"
        ".hword 0xb311, 0xeb06, 0x4000, 0xe3a0\n"
        ".hword 0x10ff, 0xe204, 0x0284, 0xe085\n"
        ".hword 0x0a01, 0xe280, 0x0f7b, 0xe280\n"
        ".hword 0x2fe8, 0xeb00, 0x00ff, 0xe204\n"
        ".hword 0xf000, 0xe320, 0x2b35, 0xeb00\n"
        ".hword 0x1104, 0xe085, 0x1a01, 0xe281\n"
        ".hword 0x4001, 0xe284, 0x000c, 0xe354\n"
        ".hword 0x036c, 0xe581, 0xfff1, 0xbaff\n"
        ".hword 0xd024, 0xe28d, 0x8b06, 0xecbd\n"
        ".hword 0x8030, 0xe8bd, 0x2a48, 0x0001\n"
        ".hword 0x92a8, 0x0040, 0x0000, 0xbf80\n"
        ".hword 0x0000, 0x0000, 0x0000, 0xc120\n"
        ".hword 0x0000, 0x4120, 0x0000, 0xc040\n"
        ".hword 0x0000, 0x4040, 0x0000, 0x40a0\n"
        ".hword 0x0000, 0xc0a0, 0x0000, 0x4080\n"
        ".hword 0x0000, 0xc080, 0x0000, 0x42c8\n"
        ".hword 0x0000, 0x4416, 0x0000, 0x3f80\n"
        ".hword 0x5555, 0x3fd5, 0x0000, 0x46c8\n"
        ".hword 0x0000, 0x41a0, 0x0000, 0x41f0\n"
        ".hword 0xaaab, 0x3faa\n"
    );
}

// DECOMP_FUNC(0x0033138c, 836)
extern "C" __attribute__((naked)) void camp_func_0033138c() {
    asm volatile(
        ".arm\n"
        ".hword 0x47f0, 0xe92d, 0x000b, 0xe350\n"
        ".hword 0x6000, 0xe3a0, 0xd018, 0xe24d\n"
        ".hword 0xa31c, 0xe59f, 0x5000, 0xe1a0\n"
        ".hword 0x4000, 0xe59a, 0x60b0, 0x0284\n"
        ".hword 0x0004, 0x0a00, 0x000c, 0xe355\n"
        ".hword 0x6f45, 0x0284, 0x0001, 0x0a00\n"
        ".hword 0x000d, 0xe355, 0x6f5e, 0x0284\n"
        ".hword 0x001c, 0xe594, 0x0000, 0xe350\n"
        ".hword 0x001a, 0x0a00, 0x0001, 0xe350\n"
        ".hword 0x001e, 0x1a00, 0x7000, 0xe3a0\n"
        ".hword 0x12e0, 0xe59f, 0x001d, 0xe3a0\n"
        ".hword 0x7014, 0xe5cd, 0x38b8, 0xebfe\n"
        ".hword 0x2c0e, 0xe284, 0x3001, 0xe3a0\n"
        ".hword 0x10f6, 0xe1d2, 0x8004, 0xe28d\n"
        ".hword 0xc014, 0xe28d, 0x3010, 0xe58d\n"
        ".hword 0x700c, 0xe58d, 0x1002, 0xe888\n"
        ".hword 0x10f4, 0xe1d2, 0x1000, 0xe58d\n"
        ".hword 0x30f2, 0xe1d2, 0x2b03, 0xe284\n"
        ".hword 0x1000, 0xe1a0, 0x2f83, 0xe282\n"
        ".hword 0x0006, 0xe1a0, 0xb912, 0xebfd\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x000e, 0x1a00, 0x0007, 0xea00\n"
        ".hword 0x1001, 0xe3a0, 0x0006, 0xe1a0\n"
        ".hword 0xa285, 0xebfd, 0x001c, 0xe594\n"
        ".hword 0x0001, 0xe280, 0x001c, 0xe584\n"
        ".hword 0xd018, 0xe28d, 0x87f0, 0xe8bd\n"
        ".hword 0x1001, 0xe3a0, 0x0006, 0xe1a0\n"
        ".hword 0xb783, 0xebfd, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x000a, 0x0a00\n"
        ".hword 0x0034, 0xe284, 0xb5ca, 0xebfd\n"
        ".hword 0x29d8, 0xe1d4, 0x1000, 0xe1a0\n"
        ".hword 0x0002, 0xe1a0, 0xa009, 0xebfd\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0xa1c0, 0xebfd, 0xd018, 0xe28d\n"
        ".hword 0x87f0, 0xe8bd, 0x1001, 0xe3a0\n"
        ".hword 0x0000, 0xe3a0, 0x40e0, 0xebfe\n"
        ".hword 0x11d4, 0xe1dd, 0x8210, 0xe59f\n"
        ".hword 0x0001, 0xe190, 0x9001, 0xe288\n"
        ".hword 0x0001, 0x0a00, 0x000b, 0xe355\n"
        ".hword 0x001b, 0x0a00, 0x1001, 0xe3a0\n"
        ".hword 0x0001, 0xe1a0, 0x40d6, 0xebfe\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x003f, 0x0a00, 0x0000, 0xe3a0\n"
        ".hword 0xa1ac, 0xebfd, 0x0b01, 0xe284\n"
        ".hword 0x2000, 0xe3a0, 0x1003, 0xe3a0\n"
        ".hword 0x0fb5, 0xe280, 0x3170, 0xebfe\n"
        ".hword 0x0006, 0xe3a0, 0x0020, 0xe584\n"
        ".hword 0x0000, 0xe59a, 0x1005, 0xe3a0\n"
        ".hword 0x3018, 0xe280, 0x2018, 0xe590\n"
        ".hword 0x2024, 0xe580, 0x0082, 0xe883\n"
        ".hword 0x1001, 0xe3a0, 0x7014, 0xe580\n"
        ".hword 0x0006, 0xe1a0, 0x9fb8, 0xebfd\n"
        ".hword 0x0009, 0xe1a0, 0xf000, 0xe320\n"
        ".hword 0x0026, 0xea00, 0x0006, 0xe1a0\n"
        ".hword 0xb747, 0xebfd, 0x5000, 0xe1a0\n"
        ".hword 0x0006, 0xe1a0, 0xb73e, 0xebfd\n"
        ".hword 0x0005, 0xe080, 0x0080, 0xe084\n"
        ".hword 0x5b05, 0xe280, 0x07bc, 0xe1d5\n"
        ".hword 0x7a68, 0xebfd, 0x0000, 0xe350\n"
        ".hword 0x0009, 0x01a0, 0x0019, 0x0a00\n"
        ".hword 0x07bc, 0xe1d5, 0x2000, 0xe3a0\n"
        ".hword 0x1003, 0xe3a0, 0x002c, 0xe584\n"
        ".hword 0x0b01, 0xe284, 0x0fb5, 0xe280\n"
        ".hword 0x314d, 0xebfe, 0x000b, 0xe3a0\n"
        ".hword 0x0020, 0xe584, 0x0000, 0xe59a\n"
        ".hword 0x1005, 0xe3a0, 0x3018, 0xe280\n"
        ".hword 0x2018, 0xe590, 0x2024, 0xe580\n"
        ".hword 0x0082, 0xe883, 0x1001, 0xe3a0\n"
        ".hword 0x7014, 0xe580, 0x0006, 0xe1a0\n"
        ".hword 0x9f95, 0xebfd, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0xe47f, 0xebfc\n"
        ".hword 0x0001, 0xe3a0, 0xf000, 0xe320\n"
        ".hword 0xae44, 0xebfd, 0x0008, 0xe1a0\n"
        ".hword 0x2b09, 0xebfe, 0xd018, 0xe28d\n"
        ".hword 0x87f0, 0xe8bd, 0x1001, 0xe3a0\n"
        ".hword 0x0009, 0xe3a0, 0x4090, 0xebfe\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0xff96, 0x0aff, 0x000c, 0xe355\n"
        ".hword 0xff94, 0x0aff, 0x000b, 0xe355\n"
        ".hword 0x0002, 0x0a00, 0x000d, 0xe355\n"
        ".hword 0x000f, 0x0a00, 0x001a, 0xea00\n"
        ".hword 0x1000, 0xe3a0, 0x0003, 0xe3a0\n"
        ".hword 0xb406, 0xebfd, 0x000c, 0xe3a0\n"
        ".hword 0xf000, 0xe320, 0xb3e6, 0xebfd\n"
        ".hword 0x0010, 0xe3a0, 0xf000, 0xe320\n"
        ".hword 0xb3e3, 0xebfd, 0x0003, 0xe3a0\n"
        ".hword 0xf000, 0xe320, 0xb3e0, 0xebfd\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0x000b, 0xea00, 0x1000, 0xe3a0\n"
        ".hword 0x0004, 0xe3a0, 0xb3f7, 0xebfd\n"
        ".hword 0x0021, 0xe3a0, 0xf000, 0xe320\n"
        ".hword 0xb3d7, 0xebfd, 0x0010, 0xe3a0\n"
        ".hword 0xf000, 0xe320, 0xb3d4, 0xebfd\n"
        ".hword 0x0003, 0xe3a0, 0xf000, 0xe320\n"
        ".hword 0xb3d1, 0xebfd, 0x1044, 0xe59f\n"
        ".hword 0x0000, 0xe3a0, 0xb69f, 0xebfd\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0x1d8c, 0xebfe, 0x0031, 0xe5c4\n"
        ".hword 0x0000, 0xe59a, 0x1028, 0xe3a0\n"
        ".hword 0x3018, 0xe280, 0x2018, 0xe590\n"
        ".hword 0x2024, 0xe580, 0x0082, 0xe883\n"
        ".hword 0x7014, 0xe580, 0x0008, 0xe1a0\n"
        ".hword 0xffc4, 0xeaff, 0xda90, 0x0043\n"
        ".hword 0x056d, 0x0000, 0x016d, 0x0100\n"
        ".hword 0x32ff, 0x3232\n"
    );
}

// DECOMP_FUNC(0x00159028, 840)
extern "C" __attribute__((naked)) void func_00159028() {
    asm volatile(
        ".arm\n"
        ".hword 0xc4ff, 0xe3c0, 0x0003, 0xe020\n"
        ".hword 0x74ff, 0xe3c3, 0x3007, 0xe04c\n"
        ".hword 0x3c3f, 0xe283, 0x0102, 0xe200\n"
        ".hword 0x30ff, 0xe283, 0x4980, 0xe92d\n"
        ".hword 0x6e22, 0xe28f, 0x0009, 0xe92d\n"
        ".hword 0x3824, 0xe1a0, 0xb825, 0xe1a0\n"
        ".hword 0x6423, 0xe7d6, 0xe80b, 0xe1c5\n"
        ".hword 0x8803, 0xe1c4, 0x10a1, 0xe1b0\n"
        ".hword 0x6693, 0xe027, 0x2062, 0xe1b0\n"
        ".hword 0x0102, 0x23a0, 0x0000, 0x33a0\n"
        ".hword 0x7502, 0xe267, 0x0697, 0xe006\n"
        ".hword 0x76a4, 0xe1a0, 0x69a6, 0xe1a0\n"
        ".hword 0x6002, 0xe286, 0x6697, 0xe02c\n"
        ".hword 0xc202, 0xe26c, 0x782c, 0xe1a0\n"
        ".hword 0xc807, 0xe1cc, 0x0697, 0xe004\n"
        ".hword 0x069c, 0xe005, 0x77a1, 0xe1a0\n"
        ".hword 0x6825, 0xe084, 0x6326, 0xe1a0\n"
        ".hword 0x0796, 0xe00c, 0xc82c, 0xe1a0\n"
        ".hword 0x0b9c, 0xe007, 0x480c, 0xe1a0\n"
        ".hword 0x2007, 0xe052, 0x0c93, 0xe007\n"
        ".hword 0x1007, 0xe0c1, 0x0e9c, 0xe007\n"
        ".hword 0x0807, 0xe050, 0x2827, 0xe0d2\n"
        ".hword 0x089c, 0xe007, 0x2807, 0x3042\n"
        ".hword 0x2807, 0x2052, 0x1827, 0xe0c1\n"
        ".hword 0x7121, 0xe1a0, 0x0796, 0xe00c\n"
        ".hword 0xc82c, 0xe1a0, 0x0b9c, 0xe007\n"
        ".hword 0x0987, 0xe050, 0x26a7, 0xe0d2\n"
        ".hword 0x0c93, 0xe007, 0x2987, 0x3042\n"
        ".hword 0x2987, 0x2052, 0x16a7, 0xe0c1\n"
        ".hword 0x0e9c, 0xe007, 0x418c, 0xe084\n"
        ".hword 0x0187, 0xe050, 0x2ea7, 0xe0d2\n"
        ".hword 0x089c, 0xe007, 0x2187, 0x3042\n"
        ".hword 0x2187, 0x2052, 0x1ea7, 0xe0c1\n"
        ".hword 0x700c, 0xe59d, 0x1d01, 0xe1a0\n"
        ".hword 0x1322, 0xe181, 0x2d02, 0xe1a0\n"
        ".hword 0x77a1, 0xe1a0, 0x2320, 0xe182\n"
        ".hword 0x0796, 0xe00c, 0x0d00, 0xe1a0\n"
        ".hword 0xc82c, 0xe1a0, 0x0b9c, 0xe007\n"
        ".hword 0x5b0c, 0xe1a0, 0x452c, 0xe084\n"
        ".hword 0x2007, 0xe052, 0x0c93, 0xe007\n"
        ".hword 0x1007, 0xe0c1, 0x0e9c, 0xe007\n"
        ".hword 0x0807, 0xe050, 0x2827, 0xe0d2\n"
        ".hword 0x089c, 0xe007, 0x2807, 0x3042\n"
        ".hword 0x2807, 0x2052, 0x1827, 0xe0c1\n"
        ".hword 0x7121, 0xe1a0, 0x0796, 0xe00c\n"
        ".hword 0xc82c, 0xe1a0, 0x0b9c, 0xe007\n"
        ".hword 0x0987, 0xe050, 0x26a7, 0xe0d2\n"
        ".hword 0x0c93, 0xe007, 0x2987, 0x3042\n"
        ".hword 0x2987, 0x2052, 0x16a7, 0xe0c1\n"
        ".hword 0x0e9c, 0xe007, 0x0187, 0xe050\n"
        ".hword 0x2ea7, 0xe0d2, 0x089c, 0xe007\n"
        ".hword 0x2187, 0x3042, 0x2187, 0x2052\n"
        ".hword 0x1ea7, 0xe0c1, 0x1d01, 0xe1a0\n"
        ".hword 0x1322, 0xe181, 0x548c, 0xe095\n"
        ".hword 0x77a1, 0xe1a0, 0x2d02, 0xe1a0\n"
        ".hword 0x0796, 0xe00c, 0x2320, 0xe182\n"
        ".hword 0x4000, 0xe2a4, 0x0d00, 0xe1a0\n"
        ".hword 0xc82c, 0xe1a0, 0x0b9c, 0xe007\n"
        ".hword 0x6e0c, 0xe1a0, 0x2007, 0xe052\n"
        ".hword 0x0c93, 0xe007, 0x1007, 0xe0c1\n"
        ".hword 0x0e9c, 0xe007, 0x0807, 0xe050\n"
        ".hword 0x2827, 0xe0d2, 0x089c, 0xe007\n"
        ".hword 0x2807, 0x3042, 0x2807, 0x2052\n"
        ".hword 0x1827, 0xe0c1, 0x522c, 0xe095\n"
        ".hword 0x1701, 0xe1a0, 0x1922, 0xe181\n"
        ".hword 0x2702, 0xe1a0, 0x2920, 0xe182\n"
        ".hword 0x0700, 0xe1a0, 0x4000, 0xe2a4\n"
        ".hword 0x3803, 0xe188, 0x880b, 0xe18e\n"
        ".hword 0xe000, 0xe3a0, 0xb000, 0xe3a0\n"
        ".hword 0xc008, 0xe052, 0x7003, 0xe0d1\n"
        ".hword 0xe00e, 0xe0ae, 0x200c, 0x21a0\n"
        ".hword 0x1007, 0x21a0, 0x0000, 0xe090\n"
        ".hword 0x2002, 0xe0b2, 0x1001, 0xe0b1\n"
        ".hword 0xb00b, 0xe0ab, 0xc008, 0xe052\n"
        ".hword 0x7003, 0xe0d1, 0xb000, 0xe2db\n"
        ".hword 0xb000, 0xe3a0, 0xe00e, 0xe0ae\n"
        ".hword 0x200c, 0x21a0, 0x1007, 0x21a0\n"
        ".hword 0x0000, 0xe090, 0x2002, 0xe0b2\n"
        ".hword 0x1001, 0xe0b1, 0xb00b, 0xe0ab\n"
        ".hword 0xc008, 0xe052, 0x7003, 0xe0d1\n"
        ".hword 0xb000, 0xe2db, 0x200c, 0x21a0\n"
        ".hword 0x1007, 0x21a0, 0xe00e, 0xe0ae\n"
        ".hword 0x7002, 0xe191, 0x6001, 0x1386\n"
        ".hword 0x6e0e, 0xe096, 0x2000, 0xe2b5\n"
        ".hword 0x1000, 0xe2b4, 0x0189, 0x48bd\n"
        ".hword 0x8800, 0x48bd, 0x6006, 0xe096\n"
        ".hword 0x0189, 0xe8bd, 0x2002, 0xe0b2\n"
        ".hword 0x4800, 0xe8bd, 0x1001, 0xe0a1\n"
        ".hword 0x3001, 0xe243, 0xff1e, 0xe12f\n"
        ".hword 0x8080, 0x7e7f, 0x7c7d, 0x7a7b\n"
        ".hword 0x7879, 0x7677, 0x7576, 0x7374\n"
        ".hword 0x7172, 0x7071, 0x6e6f, 0x6d6e\n"
        ".hword 0x6c6c, 0x6a6b, 0x696a, 0x6868\n"
        ".hword 0x6667, 0x6566, 0x6464, 0x6363\n"
        ".hword 0x6162, 0x6061, 0x5f60, 0x5e5f\n"
        ".hword 0x5d5e, 0x5c5d, 0x5b5c, 0x5a5b\n"
        ".hword 0x595a, 0x5859, 0x5758, 0x5657\n"
        ".hword 0x5556, 0x5555, 0x5454, 0x5353\n"
        ".hword 0x5252, 0x5152, 0x5051, 0x5050\n"
        ".hword 0x4f4f, 0x4e4f, 0x4d4e, 0x4d4d\n"
        ".hword 0x4c4c, 0x4b4c, 0x4b4b, 0x4a4a\n"
        ".hword 0x494a, 0x4949, 0x4848, 0x4748\n"
        ".hword 0x4747, 0x4647, 0x4646, 0x4545\n"
        ".hword 0x4445, 0x4444, 0x4344, 0x4343\n"
        ".hword 0x4243, 0x4242, 0x4142, 0x4141\n"
    );
}

extern "C" u32 query_counter_2bffbc(u32) __asm__("ui_func_002bffbc");
extern "C" u32 query_repeat_2b902c(u32) __asm__("ui_func_002b902c");
extern "C" u32 query_mask_2c17d4(u32) __asm__("ui_func_002c17d4");
extern "C" u32 query_axis_27fbc8(float*, float*, u32) __asm__("script_vm_func_0027fbc8");
extern "C" float query_angle_2820a4(float, float) __asm__("ui_func_002820a4");

// DECOMP_FUNC(0x00254ca8, 840)
extern "C" __attribute__((minsize)) u32 ui_func_00254ca8(u32 id0, u32 id1, u32 mode) {
    u32 first = 0;
    u32 second = 0;
    if (mode == 0) {
        first = query_counter_2bffbc(id0);
        second = query_counter_2bffbc(id1);
    } else if (mode == 1) {
        first = query_repeat_2b902c(id0);
        second = query_repeat_2b902c(id1);
        if (query_mask_2c17d4(id0) && query_mask_2c17d4(id1)) second = 0;
    } else if (mode == 2) {
        first = query_mask_2c17d4(id0);
        second = query_mask_2c17d4(id1);
    }
    const u32 base = first | second;
    const u32 selector = (id0 >= 12 && id0 <= 15) ? 1 :
                         (id1 >= 12 && id1 <= 15) ? 2 : 0;
    if (!selector) return base;
    auto calibration = reinterpret_cast<volatile s16*>(0x00465278u);
    if (!*reinterpret_cast<volatile u8*>(0x00465288u)) return base;
    if (!query_mask_2c17d4(14) && !query_mask_2c17d4(15) &&
        !query_mask_2c17d4(12) && !query_mask_2c17d4(13)) return base;

    // Valid candidate domain: the original axis reader writes both outputs.
    // The original reads prior stack contents if it does not; no default is supplied.
    float x;
    float y;
    query_axis_27fbc8(&x, &y, 0);
    float angle = query_angle_2820a4(x, y) * 57.2957763671875f;
    if (angle < 0.0f) angle += 360.0f;
    if (x == 0.0f && y == 0.0f) return base;

    bool suppress = false;
    if (query_mask_2c17d4(14)) {
        const s32 a = calibration[0];
        const s32 b = calibration[1];
        if (static_cast<float>(a - b) + 360.0f > angle ||
            static_cast<s32>(__builtin_bit_cast(u32, angle)) >= static_cast<s32>(0x43b40000u)) {
            suppress = static_cast<float>(a) > angle || static_cast<float>(a + b) <= angle;
        }
    } else if (query_mask_2c17d4(15)) {
        const s32 a = calibration[2];
        const s32 b = calibration[3];
        suppress = static_cast<float>(a - b) > angle || static_cast<float>(a + b) <= angle;
    } else if (query_mask_2c17d4(12)) {
        const s32 a = calibration[4];
        const s32 b = calibration[5];
        suppress = static_cast<float>(a - b) > angle || static_cast<float>(a + b) <= angle;
    } else if (query_mask_2c17d4(13)) {
        const s32 a = calibration[6];
        const s32 b = calibration[7];
        suppress = static_cast<float>(a - b) > angle || !(static_cast<float>(a + b) > angle);
    } else {
        suppress = true;
    }
    if (suppress) {
        if (selector == 1) first = 0;
        else second = 0;
    }
    return first | second;
}

// DECOMP_FUNC(0x0039e788, 844)
extern "C" __attribute__((naked)) void engine_func_0039e788() {
    asm volatile(
        ".arm\n"
        ".hword 0x5ff0, 0xe92d, 0x4000, 0xe1a0\n"
        ".hword 0x90e1, 0xebfc, 0x7000, 0xe1a0\n"
        ".hword 0x0c01, 0xe284, 0x0062, 0xe280\n"
        ".hword 0x4dec, 0xebfa, 0xbb16, 0xe284\n"
        ".hword 0x0a02, 0xec90, 0x9066, 0xe3e0\n"
        ".hword 0x62fc, 0xe59f, 0x52fc, 0xe59f\n"
        ".hword 0x3abb, 0xed9f, 0x3abb, 0xeddf\n"
        ".hword 0xe000, 0xe3e0, 0x1000, 0xe3a0\n"
        ".hword 0x8c0d, 0xe287, 0xbfa2, 0xe28b\n"
        ".hword 0xaa06, 0xe284, 0x0042, 0xea00\n"
        ".hword 0x0000, 0xe351, 0x21b0, 0x159a\n"
        ".hword 0x003f, 0x0a00, 0x005a, 0xe5d8\n"
        ".hword 0x000c, 0xe350, 0x003e, 0x0a00\n"
        ".hword 0x0b80, 0xe594, 0x0000, 0xe352\n"
        ".hword 0x3000, 0xe3a0, 0x0fa0, 0xe080\n"
        ".hword 0x00c0, 0xe1a0, 0x0a10, 0xee01\n"
        ".hword 0x0b84, 0xe594, 0x0fa0, 0xe080\n"
        ".hword 0x1ac1, 0xeeb8, 0x00c0, 0xe1a0\n"
        ".hword 0x0a90, 0xee01, 0x1ae1, 0xeef8\n"
        ".hword 0x1a40, 0xee31, 0x1ae0, 0xee71\n"
        ".hword 0x1ac1, 0xeebd, 0x1ae1, 0xeefd\n"
        ".hword 0x0095, 0xda00, 0x0083, 0xe083\n"
        ".hword 0x0203, 0xe080, 0x0000, 0xe351\n"
        ".hword 0x0100, 0xe084, 0x0b03, 0x0280\n"
        ".hword 0x0fa2, 0x0280, 0x0a05, 0x1280\n"
        ".hword 0x0ea9, 0x1280, 0xc3b4, 0xe1d0\n"
        ".hword 0x0000, 0xe35c, 0x0087, 0x0a00\n"
        ".hword 0x4ac1, 0xeef8, 0x5ae1, 0xeef8\n"
        ".hword 0x2a07, 0xed90, 0x4a08, 0xed90\n"
        ".hword 0x2a09, 0xedd0, 0x5a0a, 0xed90\n"
        ".hword 0xc0ba, 0xe1d0, 0xc3b6, 0xe1c0\n"
        ".hword 0x6ac3, 0xee34, 0x4ae3, 0xee75\n"
        ".hword 0x2a46, 0xee32, 0x4a64, 0xee74\n"
        ".hword 0x4ac2, 0xeebd, 0x2ae4, 0xeebd\n"
        ".hword 0x4ae2, 0xeefc, 0x2ac5, 0xeefc\n"
        ".hword 0x4a0e, 0xed80, 0x2a0f, 0xed80\n"
        ".hword 0x4a10, 0xedc0, 0x2a11, 0xedc0\n"
        ".hword 0x7008, 0xe596, 0xc004, 0xe5d0\n"
        ".hword 0x0007, 0xe15c, 0x007e, 0x0a00\n"
        ".hword 0x008d, 0xe35c, 0x005c, 0x0a00\n"
        ".hword 0x008e, 0xe35c, 0x005d, 0x0a00\n"
        ".hword 0x005c, 0xe35c, 0x005e, 0x0a00\n"
        ".hword 0x005d, 0xe35c, 0x005f, 0x0a00\n"
        ".hword 0x0060, 0xea00, 0x2000, 0xe59b\n"
        ".hword 0xffbd, 0xeaff, 0x0d2e, 0xe284\n"
        ".hword 0x0000, 0xe352, 0x1001, 0xe890\n"
        ".hword 0x3000, 0xe3a0, 0x0a10, 0xee01\n"
        ".hword 0xca90, 0xee01, 0x2ac1, 0xeeb8\n"
        ".hword 0x1ae1, 0xeeb8, 0x1a40, 0xee72\n"
        ".hword 0x1a60, 0xee31, 0x1ae1, 0xeefd\n"
        ".hword 0x1ac1, 0xeebd, 0x005a, 0xda00\n"
        ".hword 0x0083, 0xe083, 0x0203, 0xe080\n"
        ".hword 0x0000, 0xe351, 0x0100, 0xe084\n"
        ".hword 0x0b03, 0x0280, 0x0fa2, 0x0280\n"
        ".hword 0x0a05, 0x1280, 0x0ea9, 0x1280\n"
        ".hword 0xc3b4, 0xe1d0, 0x0000, 0xe35c\n"
        ".hword 0x0031, 0x0a00, 0x4ae1, 0xeef8\n"
        ".hword 0x5ac1, 0xeef8, 0x2a03, 0xed90\n"
        ".hword 0x4a04, 0xed90, 0x2a05, 0xedd0\n"
        ".hword 0x5a06, 0xed90, 0xc0b8, 0xe1d0\n"
        ".hword 0xc3b6, 0xe1c0, 0x6ac3, 0xee34\n"
        ".hword 0x4ae3, 0xee75, 0x2a46, 0xee32\n"
        ".hword 0x4a64, 0xee74, 0x4ac2, 0xeebd\n"
        ".hword 0x2ae4, 0xeebd, 0x4ae2, 0xeefc\n"
        ".hword 0x2ac5, 0xeefc, 0x4a0e, 0xed80\n"
        ".hword 0x2a0f, 0xed80, 0x4a10, 0xedc0\n"
        ".hword 0x2a11, 0xedc0, 0x7008, 0xe596\n"
        ".hword 0xc004, 0xe5d0, 0x0007, 0xe15c\n"
        ".hword 0x001d, 0x0a00, 0x008d, 0xe35c\n"
        ".hword 0x0006, 0x0a00, 0x008e, 0xe35c\n"
        ".hword 0x0007, 0x0a00, 0x005c, 0xe35c\n"
        ".hword 0x0008, 0x0a00, 0x005d, 0xe35c\n"
        ".hword 0x0009, 0x0a00, 0x000a, 0xea00\n"
        ".hword 0x008e, 0xe357, 0x0012, 0x0a00\n"
        ".hword 0x0007, 0xea00, 0x008d, 0xe357\n"
        ".hword 0x000f, 0x0a00, 0x0004, 0xea00\n"
        ".hword 0x005d, 0xe357, 0x000c, 0x0a00\n"
        ".hword 0x0001, 0xea00, 0x005c, 0xe357\n"
        ".hword 0x0009, 0x0a00, 0xc2bc, 0xe1d0\n"
        ".hword 0x0000, 0xe35c, 0x0004, 0x135c\n"
        ".hword 0x9048, 0x0580, 0x0000, 0x0a00\n"
        ".hword 0xe048, 0xe580, 0x3001, 0xe283\n"
        ".hword 0x0002, 0xe153, 0xffbf, 0xbaff\n"
        ".hword 0x0019, 0xea00, 0xc2bc, 0xe1d0\n"
        ".hword 0x0000, 0xe35c, 0x0004, 0x135c\n"
        ".hword 0x5048, 0x0580, 0xfff6, 0x0aff\n"
        ".hword 0xfff4, 0xeaff, 0x008e, 0xe357\n"
        ".hword 0x001d, 0x0a00, 0x0007, 0xea00\n"
        ".hword 0x008d, 0xe357, 0x001a, 0x0a00\n"
        ".hword 0x0004, 0xea00, 0x005d, 0xe357\n"
        ".hword 0x0017, 0x0a00, 0x0001, 0xea00\n"
        ".hword 0x005c, 0xe357, 0x0014, 0x0a00\n"
        ".hword 0xc2bc, 0xe1d0, 0x0000, 0xe35c\n"
        ".hword 0x0004, 0x135c, 0x9048, 0x0580\n"
        ".hword 0x0000, 0x0a00, 0xe048, 0xe580\n"
        ".hword 0x3001, 0xe283, 0x0002, 0xe153\n"
        ".hword 0xff69, 0xbaff, 0x1001, 0xe281\n"
        ".hword 0x0002, 0xe351, 0xff4f, 0xbaff\n"
        ".hword 0x4c5a, 0xe284, 0x408d, 0xe284\n"
        ".hword 0x0000, 0xe3a0, 0x0000, 0xe5c4\n"
        ".hword 0x9ff0, 0xe8bd, 0x0000, 0x4320\n"
        ".hword 0x0000, 0x42f0, 0xf91c, 0x0049\n"
        ".hword 0x83ff, 0xb4ff, 0xc2bc, 0xe1d0\n"
        ".hword 0x0000, 0xe35c, 0x0004, 0x135c\n"
        ".hword 0x5048, 0x0580, 0xffeb, 0x0aff\n"
        ".hword 0xffe9, 0xeaff\n"
    );
}

// DECOMP_FUNC(0x00195044, 868)
extern "C" __attribute__((naked)) void camp_func_00195044() {
    asm volatile(
        ".arm\n"
        ".hword 0x034c, 0xe59f, 0x43f0, 0xe92d\n"
        ".hword 0xd01c, 0xe24d, 0x4000, 0xe590\n"
        ".hword 0x0344, 0xe594, 0x0000, 0xe350\n"
        ".hword 0x5000, 0x03a0, 0x0005, 0x0a00\n"
        ".hword 0x0001, 0xe350, 0x0027, 0x0a00\n"
        ".hword 0x0002, 0xe350, 0x5000, 0x03a0\n"
        ".hword 0x00b4, 0x1a00, 0x00b8, 0xea00\n"
        ".hword 0x0340, 0xe594, 0x0005, 0xe150\n"
        ".hword 0x0005, 0xba00, 0x0185, 0xe065\n"
        ".hword 0x1000, 0xe3a0, 0x0100, 0xe080\n"
        ".hword 0x0100, 0xe084, 0x0020, 0xe280\n"
        ".hword 0x905f, 0xeb04, 0x5001, 0xe285\n"
        ".hword 0x0005, 0xe355, 0xfff3, 0xbaff\n"
        ".hword 0x0e25, 0xe284, 0x08da, 0xe1d0\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x00a2, 0x0a00, 0x101a, 0xe3a0\n"
        ".hword 0x0030, 0xe3a0, 0x8dfd, 0xeb04\n"
        ".hword 0x5c03, 0xe284, 0x101b, 0xe3a0\n"
        ".hword 0x04b8, 0xe1c5, 0x0030, 0xe3a0\n"
        ".hword 0x8df8, 0xeb04, 0x04ba, 0xe1c5\n"
        ".hword 0x101c, 0xe3a0, 0x0030, 0xe3a0\n"
        ".hword 0x8df4, 0xeb04, 0x04bc, 0xe1c5\n"
        ".hword 0x05b8, 0xe1d5, 0x1001, 0xe3a0\n"
        ".hword 0x0003, 0xe280, 0x05b8, 0xe1c5\n"
        ".hword 0x1344, 0xe584, 0x008f, 0xea00\n"
        ".hword 0x5000, 0xe3a0, 0x0fb7, 0xe284\n"
        ".hword 0x27f6, 0xeb04, 0x0000, 0xe350\n"
        ".hword 0x9000, 0xe3a0, 0x001c, 0xda00\n"
        ".hword 0x6270, 0xe59f, 0x0085, 0xe084\n"
        ".hword 0x1000, 0xe3a0, 0x60f6, 0xe190\n"
        ".hword 0x0037, 0xe3a0, 0xaf61, 0xeb04\n"
        ".hword 0x8000, 0xe1a0, 0xf000, 0xe320\n"
        ".hword 0xaf54, 0xeb04, 0x7000, 0xe1a0\n"
        ".hword 0x0008, 0xe1a0, 0xaf3d, 0xeb04\n"
        ".hword 0x0000, 0xe156, 0xf000, 0xe320\n"
        ".hword 0x0007, 0x2a00, 0x0306, 0xe097\n"
        ".hword 0x0005, 0x0a00, 0x00f0, 0xe1d0\n"
        ".hword 0x0000, 0xe350, 0x0002, 0xaa00\n"
        ".hword 0xee34, 0xeb03, 0x1105, 0xe084\n"
        ".hword 0x035c, 0xe581, 0x5001, 0xe285\n"
        ".hword 0x0fb7, 0xe284, 0x27d9, 0xeb04\n"
        ".hword 0x0005, 0xe150, 0xf000, 0xe320\n"
        ".hword 0xffe2, 0xcaff, 0x101c, 0xe3a0\n"
        ".hword 0x0030, 0xe3a0, 0x9014, 0xe5cd\n"
        ".hword 0xa949, 0xeb04, 0x6000, 0xe1a0\n"
        ".hword 0x0fb7, 0xe284, 0x282a, 0xeb04\n"
        ".hword 0x5000, 0xe1a0, 0x0c03, 0xe284\n"
        ".hword 0x3004, 0xe28d, 0x14fa, 0xe1d0\n"
        ".hword 0x2014, 0xe28d, 0x0206, 0xe883\n"
        ".hword 0x2000, 0xe3a0, 0x9010, 0xe58d\n"
        ".hword 0x14f8, 0xe1d0, 0x1000, 0xe58d\n"
        ".hword 0x34fc, 0xe1d0, 0x1006, 0xe1a0\n"
        ".hword 0x0fb7, 0xe284, 0x29a2, 0xeb04\n"
        ".hword 0x61ac, 0xe59f, 0x0000, 0xe350\n"
        ".hword 0x0009, 0x0a00, 0x0fb7, 0xe284\n"
        ".hword 0x2817, 0xeb04, 0x0005, 0xe150\n"
        ".hword 0xf000, 0xe320, 0x004f, 0x0a00\n"
        ".hword 0x0006, 0xe1a0, 0x9bfa, 0xeb04\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0x004a, 0xea00, 0x1000, 0xe3a0\n"
        ".hword 0x0fb7, 0xe284, 0x2812, 0xeb04\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x002f, 0x0a00, 0x0fb7, 0xe284\n"
        ".hword 0x27ac, 0xeb04, 0x0005, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x0024, 0xda00\n"
        ".hword 0x0fb7, 0xe284, 0x2802, 0xeb04\n"
        ".hword 0x0005, 0xe150, 0xf000, 0xe320\n"
        ".hword 0x001f, 0x1a00, 0x0fb7, 0xe284\n"
        ".hword 0x27fd, 0xeb04, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x0004, 0x1a00\n"
        ".hword 0x0fb7, 0xe284, 0x27f2, 0xeb04\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0015, 0x0a00, 0x0fb7, 0xe284\n"
        ".hword 0x27f3, 0xeb04, 0x7000, 0xe1a0\n"
        ".hword 0x0fb7, 0xe284, 0x2795, 0xeb04\n"
        ".hword 0x0005, 0xe240, 0x0000, 0xe157\n"
        ".hword 0x0004, 0x1a00, 0x0fb7, 0xe284\n"
        ".hword 0x27e5, 0xeb04, 0x0004, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x0008, 0x0a00\n"
        ".hword 0x1000, 0xe3a0, 0x0fb7, 0xe284\n"
        ".hword 0x27eb, 0xeb04, 0x0fb7, 0xe284\n"
        ".hword 0xf000, 0xe320, 0x27e2, 0xeb04\n"
        ".hword 0x0005, 0xe150, 0xf000, 0xe320\n"
        ".hword 0xffdf, 0x0aff, 0x0fb7, 0xe284\n"
        ".hword 0x27dd, 0xeb04, 0x0005, 0xe150\n"
        ".hword 0xf000, 0xe320, 0x0015, 0x0a00\n"
        ".hword 0xffc4, 0xeaff, 0x1001, 0xe3a0\n"
        ".hword 0x0001, 0xe1a0, 0xb14a, 0xeb04\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x000e, 0x0a00, 0x008c, 0xe59f\n"
        ".hword 0x9bb9, 0xeb04, 0x5000, 0xe3a0\n"
        ".hword 0x2000, 0xe3a0, 0x0185, 0xe065\n"
        ".hword 0x1001, 0xe3a0, 0x0100, 0xe080\n"
        ".hword 0x0100, 0xe084, 0x0020, 0xe280\n"
        ".hword 0xa1e1, 0xeb04, 0x5001, 0xe285\n"
        ".hword 0x0005, 0xe355, 0xfff5, 0xbaff\n"
        ".hword 0x0002, 0xe3a0, 0x0344, 0xe584\n"
        ".hword 0x0340, 0xe594, 0x0001, 0xe280\n"
        ".hword 0x0340, 0xe584, 0xd01c, 0xe28d\n"
        ".hword 0x83f0, 0xe8bd, 0x0185, 0xe065\n"
        ".hword 0x0100, 0xe080, 0x0100, 0xe084\n"
        ".hword 0x0020, 0xe280, 0xa99e, 0xeb04\n"
        ".hword 0x5001, 0xe285, 0x0005, 0xe355\n"
        ".hword 0xfff7, 0xbaff, 0x0e25, 0xe284\n"
        ".hword 0x08da, 0xe1d0, 0x0000, 0xe350\n"
        ".hword 0x0003, 0x13a0, 0xffed, 0x0aff\n"
        ".hword 0xffeb, 0xeaff, 0xdd08, 0x0043\n"
        ".hword 0x0424, 0x0000, 0x016c, 0x0100\n"
        ".hword 0x016e, 0x0100\n"
    );
}

// DECOMP_FUNC(0x002668dc, 892)
extern "C" __attribute__((naked)) void script_vm_func_002668dc() {
    asm volatile(
        ".arm\n"
        ".hword 0x47f0, 0xe92d, 0x7310, 0xe59f\n"
        ".hword 0x8b0a, 0xed2d, 0xde51, 0xe24d\n"
        ".hword 0x5000, 0xe597, 0x0000, 0xe355\n"
        ".hword 0x00bc, 0x0a00, 0x0a98, 0xe595\n"
        ".hword 0x102a, 0xe3a0, 0xc1ec, 0xeb02\n"
        ".hword 0x82f0, 0xe59f, 0x1000, 0xe3a0\n"
        ".hword 0x0a9c, 0xe585, 0x1a94, 0xe585\n"
        ".hword 0x1a98, 0xe585, 0x0000, 0xe598\n"
        ".hword 0x6000, 0xe597, 0x0065, 0xe350\n"
        ".hword 0x001a, 0x1a00, 0x0004, 0xe598\n"
        ".hword 0x0001, 0xe350, 0x0046, 0x0a00\n"
        ".hword 0x0002, 0xe350, 0x0078, 0x0287\n"
        ".hword 0x0048, 0x0a00, 0x0003, 0xe350\n"
        ".hword 0x02b4, 0x059f, 0x0045, 0x0a00\n"
        ".hword 0x0004, 0xe350, 0x02ac, 0x059f\n"
        ".hword 0x0042, 0x0a00, 0x0005, 0xe350\n"
        ".hword 0x02a4, 0x059f, 0x003f, 0x0a00\n"
        ".hword 0x0006, 0xe350, 0x029c, 0x059f\n"
        ".hword 0x003c, 0x0a00, 0x0007, 0xe350\n"
        ".hword 0x0294, 0x059f, 0x0039, 0x0a00\n"
        ".hword 0x0008, 0xe350, 0x028c, 0x059f\n"
        ".hword 0x0036, 0x0a00, 0x0009, 0xe350\n"
        ".hword 0x0284, 0x059f, 0x0033, 0x0a00\n"
        ".hword 0x0a9c, 0xe596, 0x4000, 0xe3a0\n"
        ".hword 0x0004, 0xe590, 0x0000, 0xe350\n"
        ".hword 0x9001, 0xc3a0, 0x0012, 0xda00\n"
        ".hword 0x0a9c, 0xe596, 0x1004, 0xe1a0\n"
        ".hword 0xa520, 0xebfe, 0x0000, 0xe597\n"
        ".hword 0x0000, 0xe350, 0x0004, 0x0a00\n"
        ".hword 0x1204, 0xe084, 0x0181, 0xe080\n"
        ".hword 0x1b30, 0xe5d0, 0x0000, 0xe351\n"
        ".hword 0x9b30, 0x05c0, 0x1001, 0xe3a0\n"
        ".hword 0x0004, 0xe1a0, 0xfcef, 0xebff\n"
        ".hword 0x0a9c, 0xe596, 0x4001, 0xe284\n"
        ".hword 0x0004, 0xe590, 0x0004, 0xe150\n"
        ".hword 0xffec, 0xcaff, 0x0a9c, 0xe595\n"
        ".hword 0x4000, 0xe3a0, 0x0004, 0xe590\n"
        ".hword 0x0000, 0xe350, 0x0077, 0xda00\n"
        ".hword 0x7208, 0xe59f, 0xca82, 0xeddf\n"
        ".hword 0xca82, 0xed9f, 0x8a82, 0xed9f\n"
        ".hword 0x8a82, 0xeddf, 0x9a82, 0xed9f\n"
        ".hword 0x9a82, 0xeddf, 0xaa82, 0xed9f\n"
        ".hword 0xaa82, 0xeddf, 0xba82, 0xed9f\n"
        ".hword 0xba82, 0xeddf, 0x900d, 0xe1a0\n"
        ".hword 0x6028, 0xe28d, 0x0000, 0xe597\n"
        ".hword 0x0001, 0xe310, 0x0018, 0x1a00\n"
        ".hword 0x0006, 0xea00, 0x01f0, 0xe59f\n"
        ".hword 0x0679, 0xeb03, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0xffe4, 0xeaff\n"
        ".hword 0x0675, 0xeb03, 0xffe2, 0xeaff\n"
        ".hword 0x01a8, 0xe59f, 0x6597, 0xfa01\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x000b, 0x0a00, 0x11c4, 0xe59f\n"
        ".hword 0x0190, 0xe59f, 0xca00, 0xedc1\n"
        ".hword 0x8a01, 0xed81, 0x8a02, 0xed81\n"
        ".hword 0x8a03, 0xed81, 0xca04, 0xedc1\n"
        ".hword 0x8a05, 0xed81, 0x8a06, 0xed81\n"
        ".hword 0x8a07, 0xed81, 0xca08, 0xedc1\n"
        ".hword 0x0000, 0xe1a0, 0x1194, 0xe59f\n"
        ".hword 0x0009, 0xe1a0, 0x7e4d, 0xeb00\n"
        ".hword 0x0004, 0xe598, 0x1a62, 0xeddf\n"
        ".hword 0x0063, 0xe350, 0x0a9c, 0xe595\n"
        ".hword 0x0a4c, 0x0eb0, 0x0a68, 0x1eb0\n"
        ".hword 0x2a61, 0xeeb0, 0x0000, 0xe590\n"
        ".hword 0x1104, 0xe790, 0x2008, 0xe591\n"
        ".hword 0x100c, 0xe5b2, 0x0000, 0xe351\n"
        ".hword 0x1002, 0x1081, 0x00d7, 0xe1d1\n"
        ".hword 0x20d5, 0xe1d1, 0x30d8, 0xe1d1\n"
        ".hword 0x0030, 0xe240, 0x1031, 0xe242\n"
        ".hword 0x0100, 0xe080, 0x1a10, 0xee01\n"
        ".hword 0x2080, 0xe1a0, 0x2030, 0xe242\n"
        ".hword 0x2003, 0xe082, 0x2001, 0xe242\n"
        ".hword 0x2a90, 0xee00, 0x3040, 0xe595\n"
        ".hword 0x1ac1, 0xeeb8, 0x8a0a, 0xed8d\n"
        ".hword 0x8a0b, 0xed8d, 0x3064, 0xe243\n"
        ".hword 0x2ae0, 0xeef8, 0x8a0c, 0xed8d\n"
        ".hword 0x9a0d, 0xed8d, 0x8a0e, 0xed8d\n"
        ".hword 0x0083, 0xe083, 0x8a11, 0xed8d\n"
        ".hword 0x8a14, 0xed8d, 0x1100, 0xe086\n"
        ".hword 0x2a28, 0xee01, 0xba15, 0xedcd\n"
        ".hword 0x003c, 0xe28d, 0x1aa8, 0xee42\n"
        ".hword 0x9a02, 0xecc0, 0x0048, 0xe28d\n"
        ".hword 0x0a38, 0xeddf, 0xaa02, 0xecc0\n"
        ".hword 0x1a00, 0xed91, 0x2a02, 0xedd1\n"
        ".hword 0x1204, 0xe084, 0x1a02, 0xee31\n"
        ".hword 0x1aa1, 0xee72, 0x0181, 0xe085\n"
        ".hword 0x1b02, 0xe280, 0x1fab, 0xe281\n"
        ".hword 0x000c, 0xe28d, 0x2a40, 0xeef0\n"
        ".hword 0x2a40, 0xeeb0, 0x4001, 0xe284\n"
        ".hword 0x1a00, 0xed81, 0x0a01, 0xedc1\n"
        ".hword 0x1a02, 0xedc1, 0x0a03, 0xecdd\n"
        ".hword 0x3a05, 0xec90, 0x000c, 0xe281\n"
        ".hword 0x0a03, 0xecc0, 0x0018, 0xe281\n"
        ".hword 0x3a05, 0xec80, 0x0020, 0xe59d\n"
        ".hword 0x002c, 0xe581, 0x0a0c, 0xed81\n"
        ".hword 0x1034, 0xe281, 0x2a02, 0xec81\n"
        ".hword 0x0a9c, 0xe595, 0x0004, 0xe590\n"
        ".hword 0x0004, 0xe150, 0xff94, 0xcaff\n"
        ".hword 0xde51, 0xe28d, 0x8b0a, 0xecbd\n"
        ".hword 0x87f0, 0xe8bd, 0x7060, 0x0044\n"
        ".hword 0xf91c, 0x0049, 0x7128, 0x0044\n"
        ".hword 0x7178, 0x0044, 0x71c8, 0x0044\n"
        ".hword 0x7218, 0x0044, 0x7268, 0x0044\n"
        ".hword 0x72b8, 0x0044, 0x7308, 0x0044\n"
        ".hword 0x6630, 0x0047, 0x0000, 0x3f80\n"
        ".hword 0xf000, 0x456b, 0x0000, 0x0000\n"
        ".hword 0x7000, 0x455f, 0xe000, 0xc6bf\n"
        ".hword 0xb400, 0xc682, 0x2000, 0xc67d\n"
        ".hword 0xe000, 0xc671, 0x0000, 0xc63e\n"
        ".hword 0xc000, 0xc65a, 0x7088, 0x0044\n"
        ".hword 0xfd48, 0x004e, 0x7000, 0x44df\n"
        ".hword 0x0000, 0x4120\n"
    );
}

// DECOMP_FUNC(0x00159a44, 896)
extern "C" __attribute__((naked)) void engine_func_00159a44() {
    asm volatile(
        ".arm\n"
        ".hword 0x4ff0, 0xe92d, 0x5000, 0xe1a0\n"
        ".hword 0x4001, 0xe1a0, 0x8b04, 0xed2d\n"
        ".hword 0xd034, 0xe24d, 0x00dd, 0xe1d0\n"
        ".hword 0x0000, 0xe350, 0x0001, 0x1350\n"
        ".hword 0x0021, 0x1a00, 0x0000, 0xe595\n"
        ".hword 0x0000, 0xe350, 0x0008, 0x1595\n"
        ".hword 0x0000, 0x1350, 0x001c, 0x0a00\n"
        ".hword 0x0a03, 0xedd4, 0x0abf, 0xed9f\n"
        ".hword 0x0ac0, 0xeef4, 0xfa10, 0xeef1\n"
        ".hword 0x0017, 0x3a00, 0x0a90, 0xee10\n"
        ".hword 0x05fe, 0xe350, 0x0014, 0xca00\n"
        ".hword 0x0a04, 0xedd4, 0x0ac0, 0xeef4\n"
        ".hword 0xfa10, 0xeef1, 0x0010, 0x3a00\n"
        ".hword 0x0a90, 0xee10, 0x05fe, 0xe350\n"
        ".hword 0x000d, 0xca00, 0x0a06, 0xedd4\n"
        ".hword 0x0ac0, 0xeef4, 0xfa10, 0xeef1\n"
        ".hword 0x0009, 0x3a00, 0x0a90, 0xee10\n"
        ".hword 0x05fe, 0xe350, 0x0006, 0xca00\n"
        ".hword 0x0a07, 0xedd4, 0x0ac0, 0xeef4\n"
        ".hword 0xfa10, 0xeef1, 0x0002, 0x3a00\n"
        ".hword 0x0a90, 0xee10, 0x05fe, 0xe350\n"
        ".hword 0x0003, 0xda00, 0xd034, 0xe28d\n"
        ".hword 0x0000, 0xe3a0, 0x8b04, 0xecbd\n"
        ".hword 0x8ff0, 0xe8bd, 0x1000, 0xe594\n"
        ".hword 0x2ffa, 0xe3a0, 0x0278, 0xe59f\n"
        ".hword 0x0a9e, 0xeddf, 0x0291, 0xe001\n"
        ".hword 0x9aa0, 0xed9f, 0x9aa0, 0xeddf\n"
        ".hword 0x8aa0, 0xed9f, 0x2190, 0xe081\n"
        ".hword 0x2ffa, 0xe3a0, 0x6000, 0xe3a0\n"
        ".hword 0xb00d, 0xe1a0, 0xa621, 0xe1a0\n"
        ".hword 0x1008, 0xe594, 0x0001, 0xe35a\n"
        ".hword 0xa001, 0xb3a0, 0xa1bc, 0xe1cd\n"
        ".hword 0x0291, 0xe001, 0x1190, 0xe080\n"
        ".hword 0x9620, 0xe1a0, 0x0001, 0xe359\n"
        ".hword 0x9001, 0xb3a0, 0x0002, 0xe3a0\n"
        ".hword 0x91be, 0xe1cd, 0x00b6, 0xe1cd\n"
        ".hword 0x0004, 0xe594, 0x7014, 0xe594\n"
        ".hword 0x0a10, 0xee00, 0x0000, 0xe357\n"
        ".hword 0x7214, 0x059f, 0x0214, 0xe59f\n"
        ".hword 0x0a40, 0xeeb8, 0x1000, 0xe597\n"
        ".hword 0x2190, 0xe081, 0x0a20, 0xee20\n"
        ".hword 0x13a1, 0xe1a0, 0x12b0, 0xe1cd\n"
        ".hword 0x1004, 0xe597, 0x0a7e, 0xeddf\n"
        ".hword 0x1190, 0xe080, 0x8a20, 0xee60\n"
        ".hword 0x03a0, 0xe1a0, 0x02b2, 0xe1cd\n"
        ".hword 0x8086, 0xe08b, 0x02f0, 0xe1d8\n"
        ".hword 0x0100, 0xe080, 0x0280, 0xe1a0\n"
        ".hword 0x0a10, 0xee00, 0x0ac0, 0xeeb8\n"
        ".hword 0x0a09, 0xee20, 0x0a28, 0xeec0\n"
        ".hword 0x0a69, 0xeeb0, 0x8048, 0xeb05\n"
        ".hword 0x0a08, 0xee20, 0x6001, 0xe286\n"
        ".hword 0x0002, 0xe356, 0x0ac0, 0xeebd\n"
        ".hword 0x0a10, 0xee10, 0x02bc, 0xe1c8\n"
        ".hword 0xffee, 0xbaff, 0x0a06, 0xed94\n"
        ".hword 0x1198, 0xe59f, 0x21a8, 0xe59f\n"
        ".hword 0x0a08, 0xee20, 0x0a6a, 0xeddf\n"
        ".hword 0x0ac0, 0xeebc, 0x0a10, 0xee10\n"
        ".hword 0x02b6, 0xe1cd, 0x0a07, 0xed94\n"
        ".hword 0x0a08, 0xee20, 0x0ac0, 0xeebc\n"
        ".hword 0x0a10, 0xee10, 0x02b8, 0xe1cd\n"
        ".hword 0x0a03, 0xed94, 0x0a08, 0xee20\n"
        ".hword 0x0ac0, 0xeebc, 0x0a10, 0xee10\n"
        ".hword 0x02ba, 0xe1cd, 0x0008, 0xe597\n"
        ".hword 0x1091, 0xe080, 0x03a0, 0xe1a0\n"
        ".hword 0x02b4, 0xe1cd, 0x0a04, 0xed94\n"
        ".hword 0x0a10, 0xee10, 0x0002, 0xe150\n"
        ".hword 0x0020, 0xe5d4, 0x0a53, 0xcd9f\n"
        ".hword 0x0001, 0xe350, 0x0ac0, 0x1e70\n"
        ".hword 0x0052, 0x0a00, 0x1a08, 0xee20\n"
        ".hword 0x010a, 0xe08a, 0x3004, 0xe3a0\n"
        ".hword 0x1400, 0xe1a0, 0x30b0, 0xe1cd\n"
        ".hword 0x0a88, 0xee60, 0x0ae0, 0xeebd\n"
        ".hword 0x0ac1, 0xeefd, 0x2a10, 0xee10\n"
        ".hword 0x0a90, 0xee10, 0x23b0, 0xe1cd\n"
        ".hword 0x03b2, 0xe1cd, 0x0000, 0xe595\n"
        ".hword 0x2303, 0xe280, 0x2822, 0xe1a0\n"
        ".hword 0x2800, 0xe182, 0x2008, 0xe58d\n"
        ".hword 0x2008, 0xe595, 0x0001, 0xe152\n"
        ".hword 0x0021, 0x3a00, 0x2001, 0xe080\n"
        ".hword 0x3303, 0xe282, 0xc109, 0xe089\n"
        ".hword 0x3823, 0xe1a0, 0x2802, 0xe183\n"
        ".hword 0x200c, 0xe58d, 0x2008, 0xe595\n"
        ".hword 0x140c, 0xe081, 0x0001, 0xe152\n"
        ".hword 0x0017, 0x3a00, 0x2001, 0xe080\n"
        ".hword 0x3303, 0xe282, 0x3823, 0xe1a0\n"
        ".hword 0x2802, 0xe183, 0x2010, 0xe58d\n"
        ".hword 0x22f0, 0xe1dd, 0x2102, 0xe082\n"
        ".hword 0x1402, 0xe081, 0x2001, 0xe080\n"
        ".hword 0x3303, 0xe282, 0x3823, 0xe1a0\n"
        ".hword 0x2802, 0xe183, 0x32f2, 0xe1dd\n"
        ".hword 0x2014, 0xe58d, 0x2008, 0xe595\n"
        ".hword 0x3103, 0xe083, 0x1403, 0xe081\n"
        ".hword 0x0001, 0xe152, 0x0004, 0x3a00\n"
        ".hword 0x0001, 0xe080, 0x1303, 0xe280\n"
        ".hword 0x1821, 0xe1a0, 0x0800, 0xe181\n"
        ".hword 0x0018, 0xe58d, 0x0006, 0xe3a0\n"
        ".hword 0x00b0, 0xe1cd, 0x0000, 0xe595\n"
        ".hword 0x1008, 0xe595, 0xa77c, 0xeb05\n"
        ".hword 0x0000, 0xe595, 0x1008, 0xe595\n"
        ".hword 0x2c14, 0xeb05, 0x40dd, 0xe1d5\n"
        ".hword 0xf000, 0xe320, 0x8690, 0xeb05\n"
        ".hword 0x200d, 0xe1a0, 0x1004, 0xe1a0\n"
        ".hword 0xf123, 0xebff, 0xd034, 0xe28d\n"
        ".hword 0x8b04, 0xecbd, 0x8ff0, 0xe8bd\n"
        ".hword 0x0000, 0x0000, 0x3cc1, 0xd685\n"
        ".hword 0x126f, 0x3a83, 0x3278, 0x0047\n"
        ".hword 0xcccd, 0xcccc, 0xb000, 0x46ff\n"
        ".hword 0x0000, 0xc040, 0x0000, 0x4120\n"
        ".hword 0x0000, 0x4300, 0x3333, 0x3f73\n"
        ".hword 0x3333, 0x3f73, 0x0000, 0x3f80\n"
        ".hword 0x1a40, 0xeeb0, 0x0a40, 0xeeb1\n"
        ".hword 0x0a60, 0xee71, 0xffa8, 0xeaff\n"
    );
}

// DECOMP_FUNC(0x003a604c, 900)
extern "C" __attribute__((naked)) void engine_func_003a604c() {
    asm volatile(
        ".arm\n"
        ".hword 0x47f0, 0xe92d, 0x6001, 0xe1a0\n"
        ".hword 0x5002, 0xe1a0, 0x9000, 0xe3a0\n"
        ".hword 0x4003, 0xe1a0, 0x9380, 0xe480\n"
        ".hword 0x216a, 0xebfa, 0x0014, 0xe280\n"
        ".hword 0x2168, 0xebfa, 0x1334, 0xe59f\n"
        ".hword 0x3009, 0xe3a0, 0x2074, 0xe3a0\n"
        ".hword 0x1494, 0xe580, 0x0b01, 0xe280\n"
        ".hword 0x1324, 0xe59f, 0x00ec, 0xe280\n"
        ".hword 0x7fb1, 0xfafc, 0x0b01, 0xe280\n"
        ".hword 0x2318, 0xe59f, 0x1318, 0xe59f\n"
        ".hword 0x3009, 0xe3a0, 0x0014, 0xe280\n"
        ".hword 0x7fab, 0xfafc, 0x0a09, 0xe280\n"
        ".hword 0x0014, 0xe280, 0x8531, 0xebfb\n"
        ".hword 0x7b27, 0xe240, 0x70a8, 0xe247\n"
        ".hword 0x0007, 0xe1a0, 0xf99b, 0xebff\n"
        ".hword 0xc2f0, 0xe59f, 0x6010, 0xe587\n"
        ".hword 0x9000, 0xe587, 0xae86, 0xe287\n"
        ".hword 0x5014, 0xe5c7, 0x1000, 0xe3e0\n"
        ".hword 0x4018, 0xe587, 0x3004, 0xe28c\n"
        ".hword 0x0202, 0xe88a, 0x2018, 0xe283\n"
        ".hword 0x9007, 0xe78c, 0x0004, 0xe282\n"
        ".hword 0x9007, 0xe783, 0x9007, 0xe782\n"
        ".hword 0x1004, 0xe280, 0x9007, 0xe780\n"
        ".hword 0x9007, 0xe781, 0x9160, 0xe587\n"
        ".hword 0x9164, 0xe587, 0x9168, 0xe587\n"
        ".hword 0x9370, 0xe587, 0x9374, 0xe587\n"
        ".hword 0x9378, 0xe587, 0x901c, 0xe5c7\n"
        ".hword 0x0fea, 0xe287, 0x901d, 0xe5c7\n"
        ".hword 0x3533, 0xebfa, 0x302b, 0xe3a0\n"
        ".hword 0x2000, 0xe3a0, 0x1d05, 0xe3a0\n"
        ".hword 0x0d0e, 0xe287, 0x31ae, 0xebfa\n"
        ".hword 0x302b, 0xe3a0, 0x2000, 0xe3a0\n"
        ".hword 0x1d05, 0xe3a0, 0x0fe5, 0xe287\n"
        ".hword 0x31a9, 0xebfa, 0x1008, 0xe1a0\n"
        ".hword 0x0068, 0xe3a0, 0x70a4, 0xebfc\n"
        ".hword 0x0000, 0xe350, 0x0002, 0x0a00\n"
        ".hword 0x3492, 0xebfa, 0x1248, 0xe59f\n"
        ".hword 0x1000, 0xe580, 0x085c, 0xe587\n"
        ".hword 0xf61c, 0xebfa, 0x0014, 0xe5d7\n"
        ".hword 0x1018, 0xe597, 0x0000, 0xe350\n"
        ".hword 0x2006, 0x03a0, 0x2001, 0x13a0\n"
        ".hword 0x6a9a, 0xebfc, 0x00b0, 0xe1d0\n"
        ".hword 0x0000, 0xe350, 0x0001, 0x13a0\n"
        ".hword 0x001c, 0x15c7, 0x0010, 0xe597\n"
        ".hword 0x0001, 0xe350, 0x0011, 0x0a00\n"
        ".hword 0x001f, 0xe3a0, 0x037c, 0xe587\n"
        ".hword 0x9004, 0xe587, 0x0007, 0xe1a0\n"
        ".hword 0x9008, 0xe587, 0xedba, 0xebff\n"
        ".hword 0x10ff, 0xe3a0, 0x0000, 0xe3a0\n"
        ".hword 0x7324, 0xebfb, 0x10ff, 0xe3a0\n"
        ".hword 0x0001, 0xe3a0, 0x7321, 0xebfb\n"
        ".hword 0x61d8, 0xe59f, 0x0000, 0xe355\n"
        ".hword 0x001d, 0x0a00, 0x0001, 0xe355\n"
        ".hword 0x0032, 0x0a00, 0x004c, 0xea00\n"
        ".hword 0x1004, 0xe287, 0x000d, 0xe3a0\n"
        ".hword 0x0201, 0xe881, 0x9e91, 0xebfb\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0x9dd6, 0xebfb, 0x002b, 0xe3a0\n"
        ".hword 0xf000, 0xe320, 0x7b00, 0xebfc\n"
        ".hword 0x1000, 0xe3a0, 0x002b, 0xe3a0\n"
        ".hword 0x7e21, 0xebfc, 0x0083, 0xe3a0\n"
        ".hword 0x037c, 0xe587, 0x0007, 0xe1a0\n"
        ".hword 0xf975, 0xebff, 0x001d, 0xe5c7\n"
        ".hword 0x1001, 0xe3a0, 0x0000, 0xe3a0\n"
        ".hword 0xe909, 0xebfb, 0x1001, 0xe3a0\n"
        ".hword 0x0001, 0xe1a0, 0xe906, 0xebfb\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0x004e, 0xea00, 0x1001, 0xe3a0\n"
        ".hword 0x0004, 0xe1a0, 0x76b2, 0xebfe\n"
        ".hword 0x0006, 0xe354, 0x0007, 0x1354\n"
        ".hword 0x0008, 0x0a00, 0x0008, 0xe354\n"
        ".hword 0x0029, 0x0a00, 0x4138, 0xe59f\n"
        ".hword 0x0004, 0xe1a0, 0x850e, 0xebfb\n"
        ".hword 0x0001, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0023, 0x0a00, 0x0015, 0xea00\n"
        ".hword 0x0006, 0xe1a0, 0x8508, 0xebfb\n"
        ".hword 0x0001, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0019, 0x1a00, 0x001c, 0xea00\n"
        ".hword 0xe8df, 0xebfb, 0x001a, 0xea00\n"
        ".hword 0x1001, 0xe3a0, 0x0004, 0xe1a0\n"
        ".hword 0x7684, 0xebfe, 0x0005, 0xe354\n"
        ".hword 0xf000, 0xe320, 0x000b, 0x0a00\n"
        ".hword 0x0009, 0xe354, 0x0012, 0x0a00\n"
        ".hword 0x40e0, 0xe59f, 0x0004, 0xe1a0\n"
        ".hword 0x84f7, 0xebfb, 0x0001, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x000c, 0x0a00\n"
        ".hword 0x203c, 0xe3a0, 0x1000, 0xe3a0\n"
        ".hword 0x0004, 0xe1a0, 0xffeb, 0xeaff\n"
        ".hword 0x0006, 0xe1a0, 0x84ee, 0xebfb\n"
        ".hword 0x0001, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0003, 0x0a00, 0x203c, 0xe3a0\n"
        ".hword 0x1000, 0xe3a0, 0x0006, 0xe1a0\n"
        ".hword 0xffe2, 0xeaff, 0x0007, 0xe1a0\n"
        ".hword 0xf937, 0xebff, 0x8000, 0xe3a0\n"
        ".hword 0x001d, 0xe5c7, 0x0588, 0xe088\n"
        ".hword 0x4000, 0xe3a0, 0x5080, 0xe087\n"
        ".hword 0x6b07, 0xe285, 0x09b4, 0xe1d6\n"
        ".hword 0x0000, 0xe350, 0x000b, 0xda00\n"
        ".hword 0x0104, 0xe085, 0x0b03, 0xe280\n"
        ".hword 0x19b6, 0xe1d0, 0x0001, 0xe311\n"
        ".hword 0x0002, 0x0a00, 0x09b4, 0xe1d0\n"
        ".hword 0x1001, 0xe3a0, 0x76b1, 0xebfe\n"
        ".hword 0x09b4, 0xe1d6, 0x4001, 0xe284\n"
        ".hword 0x0004, 0xe150, 0xfff3, 0xcaff\n"
        ".hword 0x8001, 0xe288, 0x0009, 0xe358\n"
        ".hword 0xffe9, 0xbaff, 0x1001, 0xe3a0\n"
        ".hword 0x001c, 0xe3a0, 0xd755, 0xebfb\n"
        ".hword 0x0007, 0xe1a0, 0x87f0, 0xe8bd\n"
        ".hword 0x21d8, 0x0042, 0x757c, 0x0028\n"
        ".hword 0x1002, 0x0000, 0x0320, 0x003a\n"
        ".hword 0x5d24, 0x0001, 0x1ff8, 0x0042\n"
        ".hword 0x0060, 0x0100, 0x005b, 0x0100\n"
        ".hword 0x005c, 0x0100\n"
    );
}

// DECOMP_FUNC(0x003477f8, 904)
extern "C" __attribute__((naked)) void ui_func_003477f8() {
    asm volatile(
        ".arm\n"
        ".hword 0x43f0, 0xe92d, 0x4000, 0xe1a0\n"
        ".hword 0x8b02, 0xed2d, 0xd00c, 0xe24d\n"
        ".hword 0x0014, 0xe590, 0x1000, 0xe590\n"
        ".hword 0x1008, 0xe591, 0xff31, 0xe12f\n"
        ".hword 0x0004, 0xe594, 0x1060, 0xe594\n"
        ".hword 0x6338, 0xe59f, 0x8ace, 0xeddf\n"
        ".hword 0x0a03, 0xed90, 0x0a08, 0xedd1\n"
        ".hword 0x8acc, 0xed9f, 0x0a20, 0xee30\n"
        ".hword 0x0a03, 0xed80, 0x0004, 0xe594\n"
        ".hword 0x1060, 0xe594, 0x0a04, 0xed90\n"
        ".hword 0x0a09, 0xedd1, 0x0a20, 0xee30\n"
        ".hword 0x0a04, 0xed80, 0x0004, 0xe594\n"
        ".hword 0x1060, 0xe594, 0x0a08, 0xed90\n"
        ".hword 0x0a08, 0xedd1, 0x0a20, 0xee30\n"
        ".hword 0x0a08, 0xed80, 0x0004, 0xe594\n"
        ".hword 0x1060, 0xe594, 0x0a09, 0xed90\n"
        ".hword 0x0a09, 0xedd1, 0x0a20, 0xee30\n"
        ".hword 0x0a09, 0xed80, 0x0004, 0xe594\n"
        ".hword 0x1060, 0xe594, 0x0a0d, 0xed90\n"
        ".hword 0x0a08, 0xedd1, 0x0a20, 0xee30\n"
        ".hword 0x0a0d, 0xed80, 0x0004, 0xe594\n"
        ".hword 0x1060, 0xe594, 0x0a0e, 0xed90\n"
        ".hword 0x0a09, 0xedd1, 0x0a20, 0xee30\n"
        ".hword 0x0a0e, 0xed80, 0x0004, 0xe594\n"
        ".hword 0x1060, 0xe594, 0x0a12, 0xed90\n"
        ".hword 0x0a08, 0xedd1, 0x0a20, 0xee30\n"
        ".hword 0x0a12, 0xed80, 0x0004, 0xe594\n"
        ".hword 0x1060, 0xe594, 0x0a13, 0xed90\n"
        ".hword 0x0a09, 0xedd1, 0x0a20, 0xee30\n"
        ".hword 0x0a13, 0xed80, 0x5060, 0xe594\n"
        ".hword 0x1030, 0xe595, 0x0000, 0xe351\n"
        ".hword 0x0011, 0x0a00, 0x0014, 0xe594\n"
        ".hword 0x0004, 0xe590, 0xfa16, 0xebfd\n"
        ".hword 0x0000, 0xe351, 0x001a, 0x1a00\n"
        ".hword 0x0a0a, 0xedd5, 0x0a16, 0xed94\n"
        ".hword 0x0a20, 0xee30, 0x0a10, 0xee10\n"
        ".hword 0x0a16, 0xed84, 0x0006, 0xe150\n"
        ".hword 0x000c, 0xaa00, 0x0ac8, 0xeeb4\n"
        ".hword 0xfa10, 0xeef1, 0x000e, 0x3a00\n"
        ".hword 0x000f, 0xea00, 0x0a16, 0xed84\n"
        ".hword 0x000d, 0xea00, 0x0a0a, 0xedd5\n"
        ".hword 0x0a16, 0xed94, 0x0a20, 0xee30\n"
        ".hword 0x0a10, 0xee10, 0x0a16, 0xed84\n"
        ".hword 0x0006, 0xe150, 0x0001, 0xba00\n"
        ".hword 0x0a68, 0xee30, 0xfff4, 0xeaff\n"
        ".hword 0x0ac8, 0xeeb4, 0xfa10, 0xeef1\n"
        ".hword 0x0001, 0x2a00, 0x0a28, 0xee30\n"
        ".hword 0xffef, 0xeaff, 0x0a16, 0xed94\n"
        ".hword 0x0a7b, 0xeddf, 0x11ec, 0xe59f\n"
        ".hword 0x5000, 0xe3a0, 0x0a20, 0xee20\n"
        ".hword 0x0a48, 0xeef0, 0x0018, 0xe284\n"
        ".hword 0xc005, 0xe1a0, 0x3000, 0xe3a0\n"
        ".hword 0x0ac8, 0xeeb4, 0xfa10, 0xeef1\n"
        ".hword 0x0ac0, 0xeeb0, 0x6001, 0x33a0\n"
        ".hword 0x6000, 0x23a0, 0x2a10, 0xee10\n"
        ".hword 0x0001, 0xe152, 0x1a6e, 0xad9f\n"
        ".hword 0x0003, 0xba00, 0x0a41, 0xee30\n"
        ".hword 0x2a10, 0xee10, 0x0001, 0xe152\n"
        ".hword 0xfffb, 0xaaff, 0x1ae0, 0xeebc\n"
        ".hword 0x0000, 0xe355, 0x1a10, 0xee11\n"
        ".hword 0x1ac8, 0xeebc, 0x1071, 0xe6ff\n"
        ".hword 0x80ff, 0xe201, 0x2a10, 0xee11\n"
        ".hword 0x1ac0, 0xeebc, 0x2072, 0xe6ff\n"
        ".hword 0x7a10, 0xee11, 0x1a10, 0xee01\n"
        ".hword 0x1178, 0xe59f, 0x7077, 0xe6ff\n"
        ".hword 0x90ff, 0xe207, 0x1a41, 0xeef8\n"
        ".hword 0x2a10, 0xee01, 0x20ff, 0xe202\n"
        ".hword 0x2202, 0xe081, 0x2a41, 0xeef8\n"
        ".hword 0x7a10, 0xee01, 0x7208, 0xe081\n"
        ".hword 0x1209, 0xe081, 0x3a01, 0xedd7\n"
        ".hword 0x3a00, 0xed91, 0x4a01, 0xed91\n"
        ".hword 0x2a41, 0xeeb8, 0x1ae1, 0xee30\n"
        ".hword 0x0a00, 0xedd7, 0x1a62, 0xee78\n"
        ".hword 0x7008, 0xe287, 0x2a01, 0xedd2\n"
        ".hword 0x1008, 0xe281, 0x4a02, 0xecd7\n"
        ".hword 0x6a02, 0xecd1, 0x2a42, 0xee30\n"
        ".hword 0x0a00, 0xed92, 0x2008, 0xe282\n"
        ".hword 0x0a24, 0xee41, 0x5a02, 0xecd2\n"
        ".hword 0x3a05, 0xee41, 0x15fe, 0xe3a0\n"
        ".hword 0x0aa5, 0xee01, 0x2a86, 0xee41\n"
        ".hword 0x3a26, 0xee02, 0x4a07, 0xee02\n"
        ".hword 0x0a60, 0x1ef1, 0x0000, 0xe35c\n"
        ".hword 0x0a40, 0x1eb1, 0x0000, 0xe356\n"
        ".hword 0x3a43, 0x1eb1, 0x4a84, 0xee60\n"
        ".hword 0x2a84, 0xee23, 0x4a22, 0xee24\n"
        ".hword 0x6a40, 0xeeb1, 0x5a83, 0xee23\n"
        ".hword 0x5a83, 0xee60, 0x3a22, 0xee23\n"
        ".hword 0x0aa2, 0xee60, 0x2aa2, 0xee63\n"
        ".hword 0x4a00, 0xed80, 0x1a45, 0xeef0\n"
        ".hword 0x1a65, 0xeeb0, 0x3a04, 0xed80\n"
        ".hword 0x0a09, 0xedc0, 0x2a0a, 0xedc0\n"
        ".hword 0x1a80, 0xee54, 0x4a00, 0xee55\n"
        ".hword 0x1a00, 0xee02, 0x2a80, 0xee05\n"
        ".hword 0x1a01, 0xedc0, 0x4a06, 0xedc0\n"
        ".hword 0x1a02, 0xed80, 0x2a05, 0xed80\n"
        ".hword 0x6a08, 0xed80, 0x300c, 0xe580\n"
        ".hword 0x301c, 0xe580, 0x302c, 0xe580\n"
        ".hword 0x3030, 0xe580, 0x3034, 0xe580\n"
        ".hword 0x3038, 0xe5a0, 0x0a1a, 0xeddf\n"
        ".hword 0x1004, 0xe580, 0x0060, 0xe594\n"
        ".hword 0x0a17, 0xed94, 0x5004, 0xe28d\n"
        ".hword 0x1018, 0xe284, 0x1a0b, 0xed90\n"
        ".hword 0x200d, 0xe1a0, 0x0a01, 0xee30\n"
        ".hword 0x0a17, 0xed84, 0x1a0b, 0xed90\n"
        ".hword 0x0001, 0xe1a0, 0x1a20, 0xee31\n"
        ".hword 0x0a01, 0xee20, 0x0a17, 0xed84\n"
        ".hword 0x0a00, 0xed8d, 0x0a02, 0xec85\n"
        ".hword 0xda81, 0xebfb, 0xd00c, 0xe28d\n"
        ".hword 0x8b02, 0xecbd, 0x83f0, 0xe8bd\n"
        ".hword 0x0000, 0x43b4, 0x0000, 0x43b4\n"
        ".hword 0x0000, 0x0000, 0x0b61, 0x3f36\n"
        ".hword 0x0000, 0x4780, 0x0000, 0x4780\n"
        ".hword 0x7fc0, 0x0040, 0x0000, 0x3f80\n"
    );
}

// DECOMP_FUNC(0x001a7898, 928)
extern "C" __attribute__((naked)) void ui_func_001a7898() {
    asm volatile(
        ".arm\n"
        ".hword 0x4070, 0xe92d, 0x4000, 0xe1a0\n"
        ".hword 0x8b0a, 0xed2d, 0x765b, 0xeb04\n"
        ".hword 0x5000, 0xe1a0, 0x0017, 0xe5d4\n"
        ".hword 0x635c, 0xe59f, 0x0ad2, 0xeddf\n"
        ".hword 0xcad2, 0xed9f, 0x8ad2, 0xeddf\n"
        ".hword 0xaad2, 0xeddf, 0x8ad3, 0xed9f\n"
        ".hword 0x0000, 0xe350, 0x004c, 0x0a00\n"
        ".hword 0x1a04, 0xed95, 0x2a01, 0xed95\n"
        ".hword 0x0a06, 0xed95, 0x1a03, 0xedd5\n"
        ".hword 0x1a42, 0xee31, 0x0a61, 0xee30\n"
        ".hword 0x1a01, 0xee61, 0x1a08, 0xee48\n"
        ".hword 0x1a00, 0xee40, 0x2ae1, 0xeeb1\n"
        ".hword 0x1a82, 0xeeca, 0x9a21, 0xee61\n"
        ".hword 0x9a21, 0xee20, 0xaa21, 0xee28\n"
        ".hword 0x0a29, 0xee28, 0x0a0a, 0xee08\n"
        ".hword 0x0a89, 0xee08, 0x0a10, 0xee10\n"
        ".hword 0x05fe, 0xe350, 0x8a0a, 0x0d84\n"
        ".hword 0x000f, 0x0a00, 0x0a10, 0xee10\n"
        ".hword 0x0006, 0xe150, 0x0a0a, 0x0dc4\n"
        ".hword 0x000b, 0x0a00, 0x8326, 0xeb03\n"
        ".hword 0x0a0c, 0xee20, 0x0a48, 0xeef0\n"
        ".hword 0x0a0a, 0xed84, 0x0aa9, 0xee28\n"
        ".hword 0x0ac9, 0xee00, 0x8ac0, 0xeeb4\n"
        ".hword 0xfa10, 0xeef1, 0x0002, 0xda00\n"
        ".hword 0x0a0a, 0xed94, 0x0a40, 0xeeb1\n"
        ".hword 0x0a0a, 0xed84, 0x0a06, 0xed94\n"
        ".hword 0x1a01, 0xedd5, 0x0a08, 0xedd4\n"
        ".hword 0x1a03, 0xed95, 0x0a61, 0xee30\n"
        ".hword 0x1ac1, 0xee30, 0x0a00, 0xee60\n"
        ".hword 0x1a60, 0xeef0, 0x0a08, 0xee48\n"
        ".hword 0x1a08, 0xee48, 0x0a01, 0xee41\n"
        ".hword 0x1a01, 0xee41, 0x8ae1, 0xeef1\n"
        ".hword 0x1ae0, 0xeef1, 0x0aa1, 0xeeca\n"
        ".hword 0x0a20, 0xee20, 0x1a20, 0xee68\n"
        ".hword 0x0a20, 0xee61, 0x0a29, 0xee20\n"
        ".hword 0x0a8a, 0xee01, 0x0a89, 0xee00\n"
        ".hword 0x0a10, 0xee10, 0x05fe, 0xe350\n"
        ".hword 0x0a10, 0x1e10, 0x0006, 0x1150\n"
        ".hword 0x8a80, 0x1e68, 0x1a0a, 0xed95\n"
        ".hword 0x1a91, 0xeddf, 0x0a91, 0xeddf\n"
        ".hword 0x0a91, 0xed9f, 0x1a21, 0xee21\n"
        ".hword 0x0a20, 0xee61, 0x0a80, 0xee20\n"
        ".hword 0x828d, 0xeb03, 0x1a8d, 0xed9f\n"
        ".hword 0x0a00, 0xeec1, 0x0aa0, 0xee88\n"
        ".hword 0x0a09, 0xed84, 0x8b0a, 0xecbd\n"
        ".hword 0x8070, 0xe8bd, 0x0a0b, 0xed94\n"
        ".hword 0x1a87, 0xed9f, 0x000c, 0xe285\n"
        ".hword 0x0a01, 0xee20, 0x0a0b, 0xed84\n"
        ".hword 0x2a01, 0xed95, 0x0a06, 0xed95\n"
        ".hword 0x1a02, 0xec90, 0x9a41, 0xee30\n"
        ".hword 0x9ac2, 0xee71, 0x0aa9, 0xee29\n"
        ".hword 0x0a08, 0xee08, 0x0a09, 0xee09\n"
        ".hword 0xbac0, 0xeef1, 0x0aab, 0xee8a\n"
        ".hword 0xaa80, 0xee69, 0xba00, 0xee28\n"
        ".hword 0xaa00, 0xee29, 0x0a2a, 0xee28\n"
        ".hword 0x0a0b, 0xee08, 0x0a8a, 0xee08\n"
        ".hword 0x0a10, 0xee10, 0x05fe, 0xe350\n"
        ".hword 0x0a48, 0x0eb0, 0x000e, 0x0a00\n"
        ".hword 0x0a10, 0xee10, 0x0006, 0xe150\n"
        ".hword 0x0a0a, 0x0dc4, 0x000b, 0x0a00\n"
        ".hword 0x82d5, 0xeb03, 0x0a0c, 0xee20\n"
        ".hword 0x0a48, 0xeef0, 0x0a0a, 0xed84\n"
        ".hword 0x0aaa, 0xee28, 0x0aca, 0xee00\n"
        ".hword 0x0ac0, 0xeef4, 0xfa10, 0xeef1\n"
        ".hword 0x0a0a, 0xcd94, 0x0a40, 0xceb1\n"
        ".hword 0x0000, 0xda00, 0x0a0a, 0xed84\n"
        ".hword 0x0180, 0xe59f, 0xca48, 0xeef0\n"
        ".hword 0x1b01, 0xe280, 0x0a00, 0xedd0\n"
        ".hword 0x1a02, 0xedd0, 0x0a01, 0xed90\n"
        ".hword 0x1a03, 0xed90, 0x0aa1, 0xee4c\n"
        ".hword 0x2a01, 0xedd1, 0x0a81, 0xee0c\n"
        ".hword 0x1a00, 0xed91, 0x2a02, 0xed91\n"
        ".hword 0x1a03, 0xedd1, 0x0010, 0xe595\n"
        ".hword 0x1ac2, 0xee1c, 0x2aa1, 0xee4c\n"
        ".hword 0x0018, 0xe584, 0x1a60, 0xeef0\n"
        ".hword 0x2a60, 0xeeb0, 0x3a40, 0xeeb0\n"
        ".hword 0x4a82, 0xee61, 0x1a40, 0xeef0\n"
        ".hword 0x2a40, 0xeeb0, 0x5a20, 0xee23\n"
        ".hword 0x3a22, 0xee63, 0x4a41, 0xeeb1\n"
        ".hword 0x1a82, 0xee61, 0x2a60, 0xeeb0\n"
        ".hword 0x0aa2, 0xee60, 0x8aa9, 0xee63\n"
        ".hword 0x2a03, 0xee22, 0x3a22, 0xee20\n"
        ".hword 0x0a64, 0xeeb0, 0x2a45, 0xeef0\n"
        ".hword 0x0a81, 0xee01, 0x1a81, 0xee44\n"
        ".hword 0x2a01, 0xee52, 0x2a01, 0xee15\n"
        ".hword 0x1a60, 0xeeb0, 0xca29, 0xee21\n"
        ".hword 0x9a29, 0xee64, 0x8a88, 0xee42\n"
        ".hword 0xca88, 0xee01, 0x9a88, 0xee40\n"
        ".hword 0x8a09, 0xee40, 0xca09, 0xee02\n"
        ".hword 0x9a09, 0xee43, 0xa802, 0xeb00\n"
        ".hword 0x0000, 0xe350, 0xca07, 0x1dc4\n"
        ".hword 0x0003, 0x1a00, 0x0a05, 0xed95\n"
        ".hword 0x0a2d, 0xeddf, 0x0a60, 0xee30\n"
        ".hword 0x0a07, 0xed84, 0x0018, 0xe595\n"
        ".hword 0x0020, 0xe584, 0x0a0b, 0xed94\n"
        ".hword 0x1a06, 0xedd4, 0x0a00, 0xee6c\n"
        ".hword 0x1a80, 0xee29, 0x0a80, 0xee28\n"
        ".hword 0x0a80, 0xee31, 0x0a06, 0xed84\n"
        ".hword 0x0a07, 0xed94, 0x0a20, 0xee30\n"
        ".hword 0x0a07, 0xed84, 0x0a08, 0xed94\n"
        ".hword 0x0a01, 0xee30, 0x0a08, 0xed84\n"
        ".hword 0x0a0c, 0xed94, 0x1a06, 0xedd4\n"
        ".hword 0x0a40, 0xeeb1, 0x1a00, 0xee2b\n"
        ".hword 0x0a00, 0xee6a, 0x0a80, 0xee2a\n"
        ".hword 0x0a80, 0xee31, 0x0a06, 0xed84\n"
        ".hword 0x0a07, 0xed94, 0x0a01, 0xee30\n"
        ".hword 0x0a07, 0xed84, 0x0a08, 0xed94\n"
        ".hword 0x0a20, 0xee30, 0x0a08, 0xed84\n"
        ".hword 0x0a0c, 0xed94, 0x8ac0, 0xee7b\n"
        ".hword 0xff71, 0xeaff, 0x0000, 0x4300\n"
        ".hword 0xf983, 0x4222, 0x0000, 0xbf80\n"
        ".hword 0x0000, 0x3f80, 0x0000, 0xbf80\n"
        ".hword 0x0000, 0x0000, 0x0000, 0x3f00\n"
        ".hword 0x0b61, 0x3bb6, 0x0fdb, 0x4049\n"
        ".hword 0x0000, 0x42f0, 0xcccd, 0x3dcc\n"
        ".hword 0x7fc0, 0x0040, 0x0000, 0x42dc\n"
    );
}

// DECOMP_FUNC(0x002ed03c, 932)
extern "C" __attribute__((naked)) void func_002ed03c() {
    asm volatile(
        ".arm\n"
        ".hword 0x4ff3, 0xe92d, 0x0000, 0xe3e0\n"
        ".hword 0x2000, 0xe3a0, 0x8000, 0xe1a0\n"
        ".hword 0x9002, 0xe1a0, 0x735c, 0xe59f\n"
        ".hword 0x535c, 0xe59f, 0xc35c, 0xe59f\n"
        ".hword 0x8b0a, 0xed2d, 0xd004, 0xe24d\n"
        ".hword 0x1030, 0xe59d, 0x0a03, 0xecd1\n"
        ".hword 0x102c, 0xe59d, 0x8a00, 0xed91\n"
        ".hword 0x0a01, 0xed91, 0x8a02, 0xedd1\n"
        ".hword 0x03d0, 0xe587, 0xca48, 0xeeb0\n"
        ".hword 0xca40, 0xeef0, 0xba68, 0xeef0\n"
        ".hword 0x03d4, 0xe587, 0x1004, 0xe595\n"
        ".hword 0x0000, 0xe351, 0x0008, 0xda00\n"
        ".hword 0x0001, 0xe24c, 0x0001, 0xe311\n"
        ".hword 0x2001, 0x15e0, 0x10c1, 0xe1b0\n"
        ".hword 0x0003, 0x0a00, 0x2001, 0xe5c0\n"
        ".hword 0x1001, 0xe251, 0x2002, 0xe5e0\n"
        ".hword 0xfffb, 0x1aff, 0x1008, 0xe595\n"
        ".hword 0x42f4, 0xe59f, 0x0000, 0xe351\n"
        ".hword 0x0008, 0xda00, 0x0001, 0xe244\n"
        ".hword 0x0001, 0xe311, 0x2001, 0x15e0\n"
        ".hword 0x10c1, 0xe1b0, 0x0003, 0x0a00\n"
        ".hword 0x2001, 0xe5c0, 0x1001, 0xe251\n"
        ".hword 0x2002, 0xe5e0, 0xfffb, 0x1aff\n"
        ".hword 0x000c, 0xe595, 0xb2c4, 0xe59f\n"
        ".hword 0x0000, 0xe350, 0x0009, 0xda00\n"
        ".hword 0x0001, 0xe310, 0x0001, 0xe24b\n"
        ".hword 0x2001, 0x15e0, 0x100c, 0xe595\n"
        ".hword 0x10c1, 0xe1b0, 0x0003, 0x0a00\n"
        ".hword 0x2001, 0xe5c0, 0x1001, 0xe251\n"
        ".hword 0x2002, 0xe5e0, 0xfffb, 0x1aff\n"
        ".hword 0x0010, 0xe595, 0x3290, 0xe59f\n"
        ".hword 0x0000, 0xe350, 0x0009, 0xda00\n"
        ".hword 0x0001, 0xe310, 0x0001, 0xe243\n"
        ".hword 0x2001, 0x15e0, 0x1010, 0xe595\n"
        ".hword 0x10c1, 0xe1b0, 0x0003, 0x0a00\n"
        ".hword 0x2001, 0xe5c0, 0x1001, 0xe251\n"
        ".hword 0x2002, 0xe5e0, 0xfffb, 0x1aff\n"
        ".hword 0x2a60, 0xee78, 0x2a41, 0xee30\n"
        ".hword 0x0ae1, 0xee78, 0x1254, 0xe59f\n"
        ".hword 0x1aa2, 0xee22, 0x1a02, 0xee02\n"
        ".hword 0x1aa0, 0xee00, 0x0ac1, 0xeef1\n"
        ".hword 0x0a90, 0xee10, 0x0000, 0xe151\n"
        ".hword 0x0001, 0xc3a0, 0x0064, 0xca00\n"
        ".hword 0x6000, 0xe3a0, 0x0a8c, 0xeddf\n"
        ".hword 0xaa8c, 0xed9f, 0xa001, 0xe3a0\n"
        ".hword 0x9a20, 0xee30, 0xba8a, 0xed9f\n"
        ".hword 0x0050, 0xea00, 0x0000, 0xe356\n"
        ".hword 0x6001, 0x03a0, 0xfffc, 0x0aff\n"
        ".hword 0x0001, 0xe356, 0x6002, 0x03a0\n"
        ".hword 0xfff9, 0x0aff, 0x01e8, 0xe59f\n"
        ".hword 0x0002, 0xe356, 0x5000, 0xe3a0\n"
        ".hword 0x700c, 0x05b0, 0x4014, 0x0590\n"
        ".hword 0x7010, 0x15b0, 0x4014, 0x1590\n"
        ".hword 0x0000, 0xe357, 0x0041, 0xda00\n"
        ".hword 0x0008, 0xe5d4, 0x0000, 0xe350\n"
        ".hword 0x003a, 0x0a00, 0x0a03, 0xedd4\n"
        ".hword 0x0a04, 0xed94, 0x1a05, 0xed94\n"
        ".hword 0x0a20, 0xee68, 0x0a00, 0xee49\n"
        ".hword 0x0a06, 0xed94, 0x0a81, 0xee48\n"
        ".hword 0x9ac0, 0xee70, 0x0a4a, 0xeeb0\n"
        ".hword 0xaae9, 0xeef0, 0x0aea, 0xeeb4\n"
        ".hword 0xfa10, 0xeef1, 0x002d, 0xda00\n"
        ".hword 0x1a4a, 0xeef0, 0x1a68, 0xeeb0\n"
        ".hword 0x0a49, 0xeef0, 0x0a48, 0xeeb0\n"
        ".hword 0x20d5, 0xe1d4, 0x10d4, 0xe1d4\n"
        ".hword 0x3004, 0xe1a0, 0x000d, 0xe1a0\n"
        ".hword 0x0712, 0xebfe, 0x0a00, 0xed9d\n"
        ".hword 0xbac0, 0xeeb4, 0xfa10, 0xeef1\n"
        ".hword 0x0020, 0xca00, 0x000c, 0xe284\n"
        ".hword 0x0a03, 0xecd0, 0x0004, 0xe5d4\n"
        ".hword 0x0aa9, 0xee60, 0x1a29, 0xee21\n"
        ".hword 0x1aa9, 0xee61, 0x0001, 0xe350\n"
        ".hword 0x0a60, 0xee78, 0x1a41, 0xee39\n"
        ".hword 0x1ae1, 0xee78, 0x002a, 0x0a00\n"
        ".hword 0x0002, 0xe356, 0xa005, 0x07cb\n"
        ".hword 0x0002, 0x0a00, 0x0003, 0xe356\n"
        ".hword 0x0124, 0x059f, 0xa005, 0x07c0\n"
        ".hword 0x9acb, 0xeef4, 0xfa10, 0xeef1\n"
        ".hword 0x000c, 0x3a00, 0xaac0, 0xeef4\n"
        ".hword 0xfa10, 0xeef1, 0xaa00, 0xcdcd\n"
        ".hword 0x0a00, 0xed9d, 0x2a03, 0xedd4\n"
        ".hword 0x2a04, 0xed94, 0x3a05, 0xed94\n"
        ".hword 0x2a80, 0xee62, 0x2a00, 0xee22\n"
        ".hword 0x0a00, 0xee23, 0x8aa2, 0xee30\n"
        ".hword 0x9a02, 0xee31, 0x8a80, 0xee71\n"
        ".hword 0x5001, 0xe285, 0x0007, 0xe155\n"
        ".hword 0x40a8, 0xe284, 0xffbd, 0xbaff\n"
        ".hword 0x6001, 0xe286, 0x0004, 0xe356\n"
        ".hword 0xffab, 0xbaff, 0x002c, 0xe59d\n"
        ".hword 0x0a34, 0xed9f, 0x0a40, 0xee39\n"
        ".hword 0x8a00, 0xed80, 0x0a01, 0xed80\n"
        ".hword 0x8a02, 0xedc0, 0x0030, 0xe59d\n"
        ".hword 0xba02, 0xedc0, 0xca02, 0xec80\n"
        ".hword 0x0009, 0xe1a0, 0xd004, 0xe28d\n"
        ".hword 0x8b0a, 0xecbd, 0xd008, 0xe28d\n"
        ".hword 0x8ff0, 0xe8bd, 0x0074, 0xe59f\n"
        ".hword 0x0000, 0xe356, 0x63d0, 0xe5a0\n"
        ".hword 0x5004, 0xe580, 0x006c, 0x059f\n"
        ".hword 0x0002, 0x0a00, 0x0001, 0xe356\n"
        ".hword 0x0064, 0x059f, 0x0000, 0x1a00\n"
        ".hword 0xa005, 0xe7c0, 0x0001, 0xe378\n"
        ".hword 0x0002, 0xda00, 0x0aea, 0xeeb4\n"
        ".hword 0xfa10, 0xeef1, 0xaa00, 0x3dcd\n"
        ".hword 0x000c, 0xe284, 0x0a00, 0xed9d\n"
        ".hword 0x3a05, 0xedd4, 0x9001, 0xe3a0\n"
        ".hword 0x2a02, 0xec90, 0x3a00, 0xee22\n"
        ".hword 0x2a80, 0xee62, 0x2a80, 0xee23\n"
        ".hword 0x8a83, 0xee30, 0x0a4a, 0xeef0\n"
        ".hword 0x9a22, 0xee31, 0x8a82, 0xee71\n"
        ".hword 0x0a60, 0xeeb4, 0xfa10, 0xeef1\n"
        ".hword 0x8005, 0x01a0, 0xffcb, 0xeaff\n"
        ".hword 0xf91c, 0x0049, 0x6fe8, 0x0044\n"
        ".hword 0xe45c, 0x0049, 0xe65c, 0x0049\n"
        ".hword 0xe7dc, 0x0049, 0xe87c, 0x0049\n"
        ".hword 0xd70a, 0x3c23, 0x0000, 0x4170\n"
        ".hword 0x0000, 0x437a, 0x0000, 0x0000\n"
        ".hword 0x0000, 0x41c8\n"
    );
}

// DECOMP_FUNC(0x003c3c24, 936)
extern "C" __attribute__((naked)) void battle_func_003c3c24() {
    asm volatile(
        ".arm\n"
        ".hword 0x41f0, 0xe92d, 0x4000, 0xe1a0\n"
        ".hword 0x6001, 0xe1a0, 0x005c, 0xe591\n"
        ".hword 0x3000, 0xe3a0, 0xd008, 0xe24d\n"
        ".hword 0x2003, 0xe1a0, 0x1073, 0xe3a0\n"
        ".hword 0x62de, 0xebfa, 0x134c, 0xe59f\n"
        ".hword 0x201d, 0xe3a0, 0x0010, 0xe584\n"
        ".hword 0x623d, 0xebfa, 0x0010, 0xe594\n"
        ".hword 0x1001, 0xe3a0, 0x622f, 0xebfa\n"
        ".hword 0x0010, 0xe594, 0x1e33, 0xe28f\n"
        ".hword 0x7bb3, 0xebfa, 0x5b11, 0xe286\n"
        ".hword 0x50a8, 0xe285, 0x0010, 0xe594\n"
        ".hword 0x1000, 0xe595, 0x1004, 0xe201\n"
        ".hword 0x2121, 0xe1a0, 0x1000, 0xe3a0\n"
        ".hword 0x9a40, 0xebf9, 0x1000, 0xe595\n"
        ".hword 0x0010, 0xe594, 0x1008, 0xe201\n"
        ".hword 0x21a1, 0xe1a0, 0x1001, 0xe3a0\n"
        ".hword 0x9a3a, 0xebf9, 0x1000, 0xe595\n"
        ".hword 0x0010, 0xe594, 0x1010, 0xe201\n"
        ".hword 0x2221, 0xe1a0, 0x1002, 0xe3a0\n"
        ".hword 0x9a34, 0xebf9, 0x1000, 0xe595\n"
        ".hword 0x0010, 0xe594, 0x1020, 0xe201\n"
        ".hword 0x22a1, 0xe1a0, 0x1003, 0xe3a0\n"
        ".hword 0x9a2e, 0xebf9, 0x1000, 0xe595\n"
        ".hword 0x0010, 0xe594, 0x1040, 0xe201\n"
        ".hword 0x2321, 0xe1a0, 0x1005, 0xe3a0\n"
        ".hword 0x9a28, 0xebf9, 0x1000, 0xe595\n"
        ".hword 0x0010, 0xe594, 0x1080, 0xe201\n"
        ".hword 0x23a1, 0xe1a0, 0x1006, 0xe3a0\n"
        ".hword 0x9a22, 0xebf9, 0x02a0, 0xe59f\n"
        ".hword 0x7000, 0xe3a0, 0x3007, 0xe1a0\n"
        ".hword 0x0081, 0xe88d, 0x0294, 0xe59f\n"
        ".hword 0x1004, 0xe3a0, 0x2006, 0xe790\n"
        ".hword 0x0010, 0xe594, 0x9a03, 0xebf9\n"
        ".hword 0x1000, 0xe595, 0x0010, 0xe594\n"
        ".hword 0x1c01, 0xe201, 0x2421, 0xe1a0\n"
        ".hword 0x1007, 0xe3a0, 0x9a13, 0xebf9\n"
        ".hword 0x1000, 0xe595, 0x0010, 0xe594\n"
        ".hword 0x1c02, 0xe201, 0x24a1, 0xe1a0\n"
        ".hword 0x1008, 0xe3a0, 0x9a0d, 0xebf9\n"
        ".hword 0x1000, 0xe595, 0x0010, 0xe594\n"
        ".hword 0x1b01, 0xe201, 0x2521, 0xe1a0\n"
        ".hword 0x1009, 0xe3a0, 0x9a07, 0xebf9\n"
        ".hword 0x1000, 0xe595, 0x0010, 0xe594\n"
        ".hword 0x1b02, 0xe201, 0x25a1, 0xe1a0\n"
        ".hword 0x100a, 0xe3a0, 0x9a01, 0xebf9\n"
        ".hword 0x0e19, 0xe3a0, 0x0081, 0xe88d\n"
        ".hword 0x021c, 0xe59f, 0x3000, 0xe3a0\n"
        ".hword 0x100b, 0xe3a0, 0x2006, 0xe790\n"
        ".hword 0x0010, 0xe594, 0x99e3, 0xebf9\n"
        ".hword 0x9315, 0xebfb, 0x1204, 0xe59f\n"
        ".hword 0x2000, 0xe590, 0x3000, 0xe3a0\n"
        ".hword 0x0082, 0xe88d, 0x0010, 0xe594\n"
        ".hword 0x100c, 0xe3a0, 0x99db, 0xebf9\n"
        ".hword 0x1000, 0xe595, 0x0010, 0xe594\n"
        ".hword 0x1802, 0xe201, 0x28a1, 0xe1a0\n"
        ".hword 0x100d, 0xe3a0, 0x99eb, 0xebf9\n"
        ".hword 0x1000, 0xe595, 0x0010, 0xe594\n"
        ".hword 0x1501, 0xe201, 0x2b21, 0xe1a0\n"
        ".hword 0x100e, 0xe3a0, 0x99e5, 0xebf9\n"
        ".hword 0x1000, 0xe595, 0x0010, 0xe594\n"
        ".hword 0x1502, 0xe201, 0x2ba1, 0xe1a0\n"
        ".hword 0x100f, 0xe3a0, 0x99df, 0xebf9\n"
        ".hword 0x1000, 0xe595, 0x0010, 0xe594\n"
        ".hword 0x1401, 0xe201, 0x2c21, 0xe1a0\n"
        ".hword 0x1010, 0xe3a0, 0x99d9, 0xebf9\n"
        ".hword 0x1000, 0xe595, 0x0010, 0xe594\n"
        ".hword 0x1402, 0xe201, 0x2ca1, 0xe1a0\n"
        ".hword 0x1011, 0xe3a0, 0x99d3, 0xebf9\n"
        ".hword 0x1000, 0xe595, 0x0010, 0xe594\n"
        ".hword 0x1301, 0xe201, 0x2d21, 0xe1a0\n"
        ".hword 0x1012, 0xe3a0, 0x99cd, 0xebf9\n"
        ".hword 0x1000, 0xe595, 0x0010, 0xe594\n"
        ".hword 0x1302, 0xe201, 0x2da1, 0xe1a0\n"
        ".hword 0x1013, 0xe3a0, 0x99c7, 0xebf9\n"
        ".hword 0x1000, 0xe595, 0x0010, 0xe594\n"
        ".hword 0x1201, 0xe201, 0x2e21, 0xe1a0\n"
        ".hword 0x1014, 0xe3a0, 0x99c1, 0xebf9\n"
        ".hword 0x1000, 0xe595, 0x0010, 0xe594\n"
        ".hword 0x1202, 0xe201, 0x2ea1, 0xe1a0\n"
        ".hword 0x1015, 0xe3a0, 0x99bb, 0xebf9\n"
        ".hword 0x5b11, 0xe286, 0x50ac, 0xe285\n"
        ".hword 0x1016, 0xe3a0, 0x0000, 0xe595\n"
        ".hword 0x0001, 0xe200, 0x0007, 0xe190\n"
        ".hword 0x0010, 0xe594, 0x2001, 0x13a0\n"
        ".hword 0x2000, 0x03a0, 0x99b1, 0xebf9\n"
        ".hword 0x0000, 0xe595, 0x1017, 0xe3a0\n"
        ".hword 0x0002, 0xe200, 0x0007, 0xe190\n"
        ".hword 0x0010, 0xe594, 0x2001, 0x13a0\n"
        ".hword 0x2000, 0x03a0, 0x99a9, 0xebf9\n"
        ".hword 0x80cc, 0xe59f, 0x00cc, 0xe59f\n"
        ".hword 0x7004, 0xe58d, 0x8000, 0xe58d\n"
        ".hword 0x3000, 0xe3e0, 0x2006, 0xe790\n"
        ".hword 0x0010, 0xe594, 0x1018, 0xe3a0\n"
        ".hword 0x998a, 0xebf9, 0x0000, 0xe595\n"
        ".hword 0x1019, 0xe3a0, 0x0004, 0xe200\n"
        ".hword 0x0007, 0xe190, 0x0010, 0xe594\n"
        ".hword 0x2001, 0x13a0, 0x2000, 0x03a0\n"
        ".hword 0x9998, 0xebf9, 0x0004, 0xe3a0\n"
        ".hword 0x6b0b, 0xe286, 0x6fcd, 0xe286\n"
        ".hword 0x0081, 0xe88d, 0x2000, 0xe596\n"
        ".hword 0x0010, 0xe594, 0x3000, 0xe3a0\n"
        ".hword 0x101a, 0xe3a0, 0x9979, 0xebf9\n"
        ".hword 0x106c, 0xe59f, 0x7004, 0xe58d\n"
        ".hword 0x8000, 0xe58d, 0x0010, 0xe594\n"
        ".hword 0x2000, 0xe591, 0x3000, 0xe3e0\n"
        ".hword 0x101b, 0xe3a0, 0x9971, 0xebf9\n"
        ".hword 0x0000, 0xe595, 0x101c, 0xe3a0\n"
        ".hword 0x0040, 0xe200, 0x0007, 0xe190\n"
        ".hword 0x0010, 0xe594, 0xd008, 0xe28d\n"
        ".hword 0x2001, 0x13a0, 0x41f0, 0xe8bd\n"
        ".hword 0x2000, 0x03a0, 0x997d, 0xeaf9\n"
        ".hword 0x46e8, 0x0043, 0x7462, 0x206c\n"
        ".hword 0x6c46, 0x6761, 0x4d20, 0x6e65\n"
        ".hword 0x0075, 0x0000, 0x869f, 0x0001\n"
        ".hword 0x4a50, 0x0000, 0x49c8, 0x0000\n"
        ".hword 0xc9ff, 0x3b9a, 0x03e7, 0x0000\n"
        ".hword 0x2f2c, 0x0000, 0x9ad4, 0x0043\n"
    );
}

// DECOMP_FUNC(0x003655ec, 940)
extern "C" __attribute__((naked)) void engine_func_003655ec() {
    asm volatile(
        ".arm\n"
        ".hword 0x4ff0, 0xe92d, 0xd014, 0xe24d\n"
        ".hword 0x7000, 0xe1a0, 0x0000, 0xe3a0\n"
        ".hword 0x5001, 0xe1a0, 0x0000, 0xe58d\n"
        ".hword 0x1028, 0xe597, 0x0000, 0xe351\n"
        ".hword 0x1004, 0xe58d, 0x002a, 0x0a00\n"
        ".hword 0x4008, 0xe597, 0x8000, 0xe3a0\n"
        ".hword 0x00e0, 0xe284, 0x10e0, 0xe594\n"
        ".hword 0x0000, 0xe351, 0xb000, 0x1081\n"
        ".hword 0x0220, 0xe597, 0xb008, 0x01a0\n"
        ".hword 0x1000, 0xe590, 0x100c, 0xe591\n"
        ".hword 0xff31, 0xe12f, 0x0220, 0xe597\n"
        ".hword 0x1000, 0xe590, 0x102c, 0xe591\n"
        ".hword 0xff31, 0xe12f, 0x0008, 0xe58d\n"
        ".hword 0x1028, 0xe594, 0x6000, 0xe3a0\n"
        ".hword 0x0000, 0xe351, 0x202c, 0xc594\n"
        ".hword 0x0014, 0xda00, 0x0000, 0xe352\n"
        ".hword 0x002c, 0xe284, 0x0002, 0x1080\n"
        ".hword 0x0008, 0x01a0, 0x0000, 0xe350\n"
        ".hword 0xa000, 0x03a0, 0x0004, 0x0a00\n"
        ".hword 0x0206, 0xe080, 0x3028, 0xe5b0\n"
        ".hword 0x0000, 0xe353, 0xa000, 0x1083\n"
        ".hword 0xa008, 0x01a0, 0x0004, 0xe59a\n"
        ".hword 0x300c, 0xe59a, 0x0001, 0xe210\n"
        ".hword 0x0001, 0x0a00, 0x0001, 0xe353\n"
        ".hword 0x0005, 0x0a00, 0x6001, 0xe286\n"
        ".hword 0x0001, 0xe156, 0xffea, 0xbaff\n"
        ".hword 0x0000, 0xe59d, 0xd014, 0xe28d\n"
        ".hword 0x8ff0, 0xe8bd, 0x00ff, 0xe3c0\n"
        ".hword 0x9001, 0xe380, 0x0000, 0xe595\n"
        ".hword 0x4005, 0xe1a0, 0x2004, 0xe3a0\n"
        ".hword 0x1068, 0xe3a0, 0x3008, 0xe590\n"
        ".hword 0x0005, 0xe1a0, 0xff33, 0xe12f\n"
        ".hword 0x0000, 0xe350, 0x0018, 0x0a00\n"
        ".hword 0x2007, 0xe1a0, 0x3004, 0xe1a0\n"
        ".hword 0x100a, 0xe1a0, 0x480c, 0xebfb\n"
        ".hword 0x5000, 0xe1a0, 0x1079, 0xe6af\n"
        ".hword 0x4491, 0xebfb, 0x0102, 0xe210\n"
        ".hword 0xf000, 0xe320, 0x0003, 0x4a00\n"
        ".hword 0x0000, 0xe355, 0x0000, 0x159d\n"
        ".hword 0x000f, 0x1a00, 0x000b, 0xea00\n"
        ".hword 0x0000, 0xe355, 0x0008, 0x0a00\n"
        ".hword 0x0000, 0xe595, 0x1000, 0xe590\n"
        ".hword 0x0005, 0xe1a0, 0xff31, 0xe12f\n"
        ".hword 0x0004, 0xe595, 0x1000, 0xe590\n"
        ".hword 0x200c, 0xe591, 0x1005, 0xe1a0\n"
        ".hword 0xff32, 0xe12f, 0x5008, 0xe1a0\n"
        ".hword 0x0000, 0xe59d, 0x0102, 0xe380\n"
        ".hword 0x0000, 0xe58d, 0x1fa0, 0xe1b0\n"
        ".hword 0xffd3, 0x1aff, 0x0008, 0xe595\n"
        ".hword 0x4000, 0xe3a0, 0xa010, 0xe590\n"
        ".hword 0x0000, 0xe35a, 0x0047, 0xda00\n"
        ".hword 0x0008, 0xe595, 0x1014, 0xe5b0\n"
        ".hword 0x0000, 0xe351, 0x0001, 0x1080\n"
        ".hword 0x0000, 0x03a0, 0x0000, 0xe350\n"
        ".hword 0x0004, 0x0a00, 0x0204, 0xe080\n"
        ".hword 0x1028, 0xe5b0, 0x0000, 0xe351\n"
        ".hword 0x8000, 0x1081, 0x0000, 0x1a00\n"
        ".hword 0x8000, 0xe3a0, 0x0004, 0xe288\n"
        ".hword 0x1004, 0xe598, 0x0000, 0xe351\n"
        ".hword 0x9000, 0x1081, 0x101c, 0xe59b\n"
        ".hword 0x9000, 0x03a0, 0x001c, 0xe28b\n"
        ".hword 0x0000, 0xe351, 0x0001, 0x1080\n"
        ".hword 0x0000, 0x03a0, 0x0000, 0xe350\n"
        ".hword 0x100c, 0xe28d, 0x0000, 0x1359\n"
        ".hword 0x000c, 0xe58d, 0x1010, 0xe58d\n"
        ".hword 0x000c, 0x0a00, 0x0009, 0xe1a0\n"
        ".hword 0x76a3, 0xebfd, 0x2000, 0xe1a0\n"
        ".hword 0x0010, 0xe59d, 0x1009, 0xe1a0\n"
        ".hword 0x7675, 0xebfd, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x0003, 0x0a00\n"
        ".hword 0x100c, 0xe5b0, 0x0000, 0xe351\n"
        ".hword 0x0001, 0x1080, 0x0000, 0x1a00\n"
        ".hword 0x0000, 0xe3a0, 0x1024, 0xe595\n"
        ".hword 0x2008, 0xe59d, 0x0008, 0xe590\n"
        ".hword 0x0104, 0xe781, 0x1000, 0xe592\n"
        ".hword 0x201c, 0xe5b1, 0x0000, 0xe352\n"
        ".hword 0x1002, 0x1081, 0x1000, 0x03a0\n"
        ".hword 0x0000, 0xe351, 0x0004, 0x0a00\n"
        ".hword 0x0200, 0xe081, 0x1028, 0xe5b0\n"
        ".hword 0x0000, 0xe351, 0x0001, 0x1080\n"
        ".hword 0x0000, 0x1a00, 0x0000, 0xe3a0\n"
        ".hword 0x2054, 0xe595, 0x0020, 0xe280\n"
        ".hword 0x0104, 0xe782, 0x0010, 0xe598\n"
        ".hword 0x0000, 0xe350, 0x0000, 0x13a0\n"
        ".hword 0x0011, 0x0a00, 0x1034, 0xe595\n"
        ".hword 0x0104, 0xe781, 0x4001, 0xe284\n"
        ".hword 0x000a, 0xe154, 0xffb7, 0xbaff\n"
        ".hword 0x0004, 0xe59d, 0x1f8a, 0xe287\n"
        ".hword 0x000c, 0xe590, 0x5106, 0xe780\n"
        ".hword 0x00d4, 0xe59f, 0x0060, 0xe881\n"
        ".hword 0x1005, 0xe1a0, 0x20d7, 0xe190\n"
        ".hword 0x0007, 0xe1a0, 0xccde, 0xebf7\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0xff78, 0xeaff, 0x001c, 0xe5b8\n"
        ".hword 0x0000, 0xe350, 0x8000, 0x1088\n"
        ".hword 0x0008, 0xe597, 0x8000, 0x03a0\n"
        ".hword 0x0000, 0xe350, 0x0003, 0x0a00\n"
        ".hword 0x2000, 0xe590, 0x1094, 0xe59f\n"
        ".hword 0x1002, 0xe1d1, 0x0000, 0x13a0\n"
        ".hword 0x9010, 0xe28d, 0x10e0, 0xe5b0\n"
        ".hword 0x0000, 0xe351, 0x0001, 0x1080\n"
        ".hword 0x0000, 0x03a0, 0x101c, 0xe5b0\n"
        ".hword 0x0000, 0xe351, 0x0001, 0x1080\n"
        ".hword 0x0000, 0x03a0, 0x0000, 0xe350\n"
        ".hword 0x0000, 0x1358, 0x0010, 0xe58d\n"
        ".hword 0x000c, 0x0a00, 0x0008, 0xe1a0\n"
        ".hword 0x7653, 0xebfd, 0x2000, 0xe1a0\n"
        ".hword 0x1008, 0xe1a0, 0x0009, 0xe1a0\n"
        ".hword 0x7625, 0xebfd, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x0003, 0x0a00\n"
        ".hword 0x100c, 0xe5b0, 0x0000, 0xe351\n"
        ".hword 0x0001, 0x1080, 0x0000, 0x1a00\n"
        ".hword 0x0000, 0xe3a0, 0x8008, 0xe590\n"
        ".hword 0x0220, 0xe597, 0x1000, 0xe590\n"
        ".hword 0x100c, 0xe591, 0xff31, 0xe12f\n"
        ".hword 0x0004, 0xe590, 0x0308, 0xe080\n"
        ".hword 0xffbf, 0xeaff, 0x0231, 0x0000\n"
        ".hword 0x0092, 0x4000\n"
    );
}

// DECOMP_FUNC(0x00194a08, 948)
extern "C" __attribute__((naked)) void camp_func_00194a08() {
    asm volatile(
        ".arm\n"
        ".hword 0x4ff0, 0xe92d, 0x0330, 0xe59f\n"
        ".hword 0x4000, 0xe3a0, 0x8b02, 0xed2d\n"
        ".hword 0xd094, 0xe24d, 0x5000, 0xe590\n"
        ".hword 0x0fb7, 0xe285, 0x23ae, 0xeb04\n"
        ".hword 0x0000, 0xe350, 0x00a2, 0xda00\n"
        ".hword 0xb00b, 0xe3a0, 0x8ac3, 0xeddf\n"
        ".hword 0x8ac3, 0xed9f, 0x8c03, 0xe285\n"
        ".hword 0x0184, 0xe064, 0x0100, 0xe080\n"
        ".hword 0x0100, 0xe085, 0x0020, 0xe280\n"
        ".hword 0xa949, 0xeb04, 0x0000, 0xe354\n"
        ".hword 0x9000, 0xe1a0, 0x0006, 0x1a00\n"
        ".hword 0x0000, 0xe3a0, 0x2000, 0xe1a0\n"
        ".hword 0x0801, 0xe88d, 0x3009, 0xe1a0\n"
        ".hword 0x1030, 0xe3a0, 0x0002, 0xe3a0\n"
        ".hword 0xaab6, 0xeb04, 0x0fb7, 0xe285\n"
        ".hword 0x2397, 0xeb04, 0x0001, 0xe240\n"
        ".hword 0x0004, 0xe150, 0x0017, 0x1a00\n"
        ".hword 0x14fa, 0xe1d8, 0x04f8, 0xe1d8\n"
        ".hword 0x6020, 0xe28d, 0xc000, 0xe3a0\n"
        ".hword 0x1803, 0xe886, 0x2006, 0xe3a0\n"
        ".hword 0x3004, 0xe3a0, 0x04fc, 0xe1d8\n"
        ".hword 0xe00c, 0xe28d, 0x3014, 0xe58d\n"
        ".hword 0x2018, 0xe58d, 0x001c, 0xe58d\n"
        ".hword 0xa005, 0xe3a0, 0x1003, 0xe3a0\n"
        ".hword 0x0402, 0xe88e, 0xc009, 0xe3a0\n"
        ".hword 0x7008, 0xe3a0, 0x6007, 0xe3a0\n"
        ".hword 0x3030, 0xe3a0, 0x2000, 0xe3a0\n"
        ".hword 0x1009, 0xe1a0, 0x0fb7, 0xe285\n"
        ".hword 0x10c0, 0xe88d, 0xf051, 0xeb03\n"
        ".hword 0x1015, 0xe284, 0x0030, 0xe3a0\n"
        ".hword 0xaaf4, 0xeb04, 0x6000, 0xe1a0\n"
        ".hword 0x00fa, 0xe1d0, 0x2001, 0xe3a0\n"
        ".hword 0x1030, 0xe3a0, 0x0801, 0xe88d\n"
        ".hword 0x00f8, 0xe1d6, 0x3009, 0xe080\n"
        ".hword 0x0002, 0xe3a0, 0xaa8d, 0xeb04\n"
        ".hword 0x0fb7, 0xe285, 0xf000, 0xe320\n"
        ".hword 0x29cc, 0xeb04, 0x721c, 0xe59f\n"
        ".hword 0x0004, 0xe080, 0x1000, 0xe3a0\n"
        ".hword 0x0080, 0xe085, 0x70f7, 0xe190\n"
        ".hword 0x0037, 0xe3a0, 0xb0de, 0xeb04\n"
        ".hword 0x0000, 0xe58d, 0xf000, 0xe320\n"
        ".hword 0xb0d1, 0xeb04, 0xa000, 0xe1a0\n"
        ".hword 0x0000, 0xe59d, 0xb0ba, 0xeb04\n"
        ".hword 0x0000, 0xe157, 0xf000, 0xe320\n"
        ".hword 0x004d, 0x2a00, 0x7307, 0xe09a\n"
        ".hword 0x004b, 0x0a00, 0x1013, 0xe3a0\n"
        ".hword 0x0030, 0xe3a0, 0xaad3, 0xeb04\n"
        ".hword 0xa000, 0xe1a0, 0x2002, 0xe287\n"
        ".hword 0x1f71, 0xe28f, 0x0030, 0xe28d\n"
        ".hword 0xa719, 0xfa04, 0x00f8, 0xe1d6\n"
        ".hword 0x20f8, 0xe1da, 0x30fa, 0xe1d6\n"
        ".hword 0x10fa, 0xe1da, 0x2000, 0xe082\n"
        ".hword 0x1a48, 0xeeb0, 0x0001, 0xe083\n"
        ".hword 0x1009, 0xe082, 0x0a90, 0xee00\n"
        ".hword 0x1a10, 0xee00, 0x2a68, 0xeeb0\n"
        ".hword 0x1a41, 0xeef0, 0x118c, 0xe59f\n"
        ".hword 0x2030, 0xe28d, 0x0ae0, 0xeef8\n"
        ".hword 0x0ac0, 0xeeb8, 0x0002, 0xe3a0\n"
        ".hword 0xa6e7, 0xeb04, 0x1014, 0xe3a0\n"
        ".hword 0x0030, 0xe3a0, 0xaab9, 0xeb04\n"
        ".hword 0xa000, 0xe1a0, 0x003f, 0xe5d7\n"
        ".hword 0x0001, 0xe350, 0x0033, 0x0a00\n"
        ".hword 0x0037, 0xe5d7, 0x0030, 0xe350\n"
        ".hword 0x0fb7, 0xe285, 0x005b, 0x0a00\n"
        ".hword 0x2994, 0xeb04, 0x0004, 0xe080\n"
        ".hword 0x0080, 0xe085, 0x0b01, 0xe280\n"
        ".hword 0x02f4, 0xe1d0, 0x0100, 0xe085\n"
        ".hword 0x135c, 0xe590, 0x0070, 0xe28d\n"
        ".hword 0xef8e, 0xeb03, 0x3037, 0xe287\n"
        ".hword 0x2070, 0xe28d, 0x1e12, 0xe28f\n"
        ".hword 0x0030, 0xe28d, 0xa6ee, 0xfa04\n"
        ".hword 0x1002, 0xe3a0, 0x0030, 0xe28d\n"
        ".hword 0x8932, 0xeb04, 0x200c, 0xe59a\n"
        ".hword 0x10f8, 0xe1da, 0x30f8, 0xe1d6\n"
        ".hword 0x2a68, 0xeeb0, 0x20f0, 0xe1d2\n"
        ".hword 0x1002, 0xe081, 0x0000, 0xe041\n"
        ".hword 0x10fa, 0xe1da, 0x20fa, 0xe1d6\n"
        ".hword 0xc000, 0xe089, 0x0001, 0xe082\n"
        ".hword 0x100c, 0xe083, 0x0a10, 0xee00\n"
        ".hword 0x1a10, 0xee01, 0x2030, 0xe28d\n"
        ".hword 0x10ff, 0xe3a0, 0x0002, 0xe3a0\n"
        ".hword 0x0ac0, 0xeef8, 0x0ac1, 0xeeb8\n"
        ".hword 0x1a48, 0xeeb0, 0x1a41, 0xeef0\n"
        ".hword 0xa6b5, 0xeb04, 0x4001, 0xe284\n"
        ".hword 0x0fb7, 0xe285, 0x230c, 0xeb04\n"
        ".hword 0x0004, 0xe150, 0xf000, 0xe320\n"
        ".hword 0xff60, 0xcaff, 0xd094, 0xe28d\n"
        ".hword 0x8b02, 0xecbd, 0x8ff0, 0xe8bd\n"
        ".hword 0x0fb7, 0xe285, 0x2963, 0xeb04\n"
        ".hword 0x0004, 0xe080, 0x1088, 0xe59f\n"
        ".hword 0x0080, 0xe085, 0x0b01, 0xe280\n"
        ".hword 0x02f4, 0xe1d0, 0x0100, 0xe085\n"
        ".hword 0x035c, 0xe590, 0x2091, 0xe081\n"
        ".hword 0x20e0, 0xe3e0, 0x15a1, 0xe1a0\n"
        ".hword 0x0291, 0xe003, 0x2064, 0xe59f\n"
        ".hword 0x0203, 0xe080, 0x2092, 0xe080\n"
        ".hword 0x72a0, 0xe1a0, 0x0070, 0xe28d\n"
        ".hword 0xef54, 0xeb03, 0x1007, 0xe1a0\n"
        ".hword 0x7070, 0xe28d, 0x0080, 0xe28d\n"
        ".hword 0xef50, 0xeb03, 0x3010, 0xe287\n"
        ".hword 0x2070, 0xe28d, 0x1038, 0xe28f\n"
        ".hword 0x0030, 0xe28d, 0xa6b0, 0xfa04\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0xffbe, 0xeaff, 0xdd08, 0x0043\n"
        ".hword 0x0000, 0x3f80, 0x0000, 0x0000\n"
        ".hword 0x0424, 0x0000, 0x7325, 0x0000\n"
        ".hword 0x00ff, 0xe098, 0x7325, 0x4081\n"
        ".hword 0x7325, 0x0000, 0xb3c5, 0x91a2\n"
        ".hword 0x8889, 0x8888, 0x7325, 0x6782\n"
        ".hword 0x4081, 0x7325, 0x6c82, 0x0000\n"
        ".hword 0xf000, 0xe320, 0x2937, 0xeb04\n"
        ".hword 0x0004, 0xe080, 0x0080, 0xe085\n"
        ".hword 0x0b01, 0xe280, 0x02f4, 0xe1d0\n"
        ".hword 0x0100, 0xe085, 0x135c, 0xe590\n"
        ".hword 0x0070, 0xe28d, 0xef31, 0xeb03\n"
        ".hword 0x2070, 0xe28d, 0x1058, 0xe24f\n"
        ".hword 0x0030, 0xe28d, 0xa692, 0xfa04\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0xffa0, 0xeaff\n"
    );
}

// End of Batch 45 B.
