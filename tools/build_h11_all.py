#!/usr/bin/env python3
"""Build and verify all Milestone H11 semantic C++ candidates (Shops, Black Market & Terminals)."""
import os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

EXP_DIR = ROOT / 'experiments/semantic_equivalence'
EXP_DIR.mkdir(parents=True, exist_ok=True)
BUILD_DIR = ROOT / 'build/h11_candidates'
BUILD_DIR.mkdir(parents=True, exist_ok=True)

# 1. Shop_SetSelectedItem (0x0022A60C, 52 bytes)
f1 = EXP_DIR / 'h11_shop_setselecteditem_candidate.cpp'
f1.write_text('''#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

struct ShopContext {
    u8 pad0[0x4C];
    u32 selected_item; // 0x4C
    u8 pad1[0x11];     // 0x50..0x60
    u8 dirty_flag;     // 0x61
    u8 is_locked;      // 0x62
};

extern "C" void h11_shop_setselecteditem_candidate(ShopContext* ctx, u32 item_id) {
    if (ctx->is_locked == 0) {
        if (ctx->selected_item != item_id) {
            ctx->dirty_flag = 1;
        }
        ctx->selected_item = item_id;
    }
}

extern "C" void h11_shop_setselecteditem_mutation(ShopContext* ctx, u32 item_id) {
    ctx->dirty_flag = 0xFF;
}
''', encoding='utf-8')

# 2. Shop_CheckHasNewInventoryItem (0x0022FC98, 48 bytes)
f2 = EXP_DIR / 'h11_shop_checkhasnew_candidate.cpp'
f2.write_text('''#include <cstdint>
typedef uint32_t u32;

extern "C" {
    u32 shop_func_0026f0d8(u32 type);
    u32 shop_func_002b902c(u32 flag);
}

extern "C" u32 h11_shop_checkhasnew_candidate(void* ctx) {
    u32 res = 0;
    if (shop_func_0026f0d8(6) != 0) {
        res = 1;
    }
    if (shop_func_002b902c(7) != 0) {
        res = 1;
    }
    return res;
}

extern "C" u32 h11_shop_checkhasnew_mutation(void* ctx) {
    return 0xDEADBEEF;
}
''', encoding='utf-8')

# 3. Shop_CheckHasSpecialStockItem (0x0022FCC8, 48 bytes)
f3 = EXP_DIR / 'h11_shop_checkhasspecial_candidate.cpp'
f3.write_text('''#include <cstdint>
typedef uint32_t u32;

extern "C" {
    u32 shop_func_0026f0d8(u32 type);
    u32 shop_func_002b902c(u32 flag);
}

extern "C" u32 h11_shop_checkhasspecial_candidate(void* ctx) {
    u32 res = 0;
    if (shop_func_0026f0d8(5) != 0) {
        res = 1;
    }
    if (shop_func_002b902c(8) != 0) {
        res = 1;
    }
    return res;
}

extern "C" u32 h11_shop_checkhasspecial_mutation(void* ctx) {
    return 0xDEADBEEF;
}
''', encoding='utf-8')

# 4. Shop_PushItemRecord (0x00230680, 108 bytes)
f4 = EXP_DIR / 'h11_shop_pushitemrecord_candidate.cpp'
f4.write_text('''#include <cstdint>
typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;

extern "C" void h11_shop_pushitemrecord_candidate(u8* shop_buf, u16 item_id, u16 flag1, u16 flag2, u16 flag3) {
    u16* count_ptr = reinterpret_cast<u16*>(shop_buf + 0x1000);
    u32 count = *count_ptr;
    u8* entry = shop_buf + (count * 4);
    *reinterpret_cast<u16*>(entry) = item_id;
    u16 flags = *reinterpret_cast<u16*>(entry + 2);
    flags = (flags & ~0x0001) | (flag1 & 0x0001);
    flags = (flags & ~0x0002) | ((flag2 & 0x0001) << 1);
    flags = (flags & ~0x03FC) | ((flag3 & 0x00FF) << 2);
    *reinterpret_cast<u16*>(entry + 2) = flags;
    *count_ptr = static_cast<u16>(count + 1);
}

extern "C" void h11_shop_pushitemrecord_mutation(u8* shop_buf, u16 item_id, u16 flag1, u16 flag2, u16 flag3) {
    if (shop_buf) shop_buf[0] = 0xFF;
}
''', encoding='utf-8')

# 5. Shop_IsEquipSlotMatch (0x00230D24, 140 bytes)
f5 = EXP_DIR / 'h11_shop_isequipslotmatch_candidate.cpp'
f5.write_text('''#include <cstdint>
typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;

extern "C" {
    void* sub_2B66EC(void* unit);
    u32 sub_2AE64C(u32 slot_id);
}

extern "C" u32 h11_shop_isequipslotmatch_candidate(void* unit, u32 slot_id) {
    u8* equip_table = static_cast<u8*>(sub_2B66EC(unit));
    u32 cat = sub_2AE64C(slot_id);
    u32 offset = 0;
    if (cat == 2) offset = 0;
    else if (cat == 3) offset = 2;
    else if (cat == 4) offset = 6;
    else if (cat == 5) offset = 8;
    else if (cat == 6) offset = 10;
    else if (cat == 7) offset = 12;
    else if (cat == 8) offset = 4;
    else return 0;
    u16 equipped_id = *reinterpret_cast<u16*>(equip_table + offset);
    return (slot_id == equipped_id) ? 1 : 0;
}

extern "C" u32 h11_shop_isequipslotmatch_mutation(void* unit, u32 slot_id) {
    return 0xDEADBEEF;
}
''', encoding='utf-8')

# 6. Shop_CalcPurchasableQty (0x00230DB0, 100 bytes)
f6 = EXP_DIR / 'h11_shop_calcpurchasableqty_candidate.cpp'
f6.write_text('''#include <cstdint>
typedef uint32_t u32;
typedef int32_t s32;
typedef uint8_t u8;

extern "C" {
    void* sub_22EBBC();
    s32 sub_2C615C(void* p, u32 item_id);
    s32 sub_2B9100(void* ctx);
    s32 sub_28FDE4(void* ctx);
}

extern "C" s32 h11_shop_calcpurchasableqty_candidate(void* ctx, u32 item_id) {
    void* p = sub_22EBBC();
    s32 qty = sub_2C615C(p, item_id);
    if (qty < 0) {
        qty = 0;
    } else if (qty > 99) {
        qty = 99;
    }
    s32 max_bag = sub_2B9100(ctx);
    s32 current_bag = sub_28FDE4(ctx);
    s32 remaining = max_bag - current_bag;
    if (qty < 0) {
        qty = 0;
    }
    if (remaining < qty) {
        qty = remaining;
    }
    return qty;
}

extern "C" s32 h11_shop_calcpurchasableqty_mutation(void* ctx, u32 item_id) {
    return -999;
}
''', encoding='utf-8')

# 7. Terminal_SetUnlockFlag (0x00263734, 68 bytes)
f7 = EXP_DIR / 'h11_terminal_setunlockflag_candidate.cpp'
f7.write_text('''#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

extern "C" void* sub_2BBD40();

extern "C" void h11_terminal_setunlockflag_candidate(u32 terminal_id, u32 state) {
    if (terminal_id >= 32) return;
    u8* work = static_cast<u8*>(sub_2BBD40());
    u8* bitset = work + 8;
    u32 byte_idx = terminal_id >> 3;
    u8 mask = static_cast<u8>(1u << (terminal_id & 7));
    if (state != 0) {
        bitset[byte_idx] |= mask;
    } else {
        bitset[byte_idx] &= ~mask;
    }
}

extern "C" void h11_terminal_setunlockflag_mutation(u32 terminal_id, u32 state) {
    u8* work = static_cast<u8*>(sub_2BBD40());
    if (work) work[0] = 0xFF;
}
''', encoding='utf-8')

# 8. Terminal_IsUnlocked (0x00263778, 60 bytes)
f8 = EXP_DIR / 'h11_terminal_isunlocked_candidate.cpp'
f8.write_text('''#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

extern "C" void* sub_2BBD40();

extern "C" u32 h11_terminal_isunlocked_candidate(u32 terminal_id) {
    if (terminal_id >= 32) return 0;
    u8* work = static_cast<u8*>(sub_2BBD40());
    u8* bitset = work + 8;
    u32 byte_idx = terminal_id >> 3;
    u8 mask = static_cast<u8>(1u << (terminal_id & 7));
    return (bitset[byte_idx] & mask) ? 1 : 0;
}

extern "C" u32 h11_terminal_isunlocked_mutation(u32 terminal_id) {
    return 0xDEADBEEF;
}
''', encoding='utf-8')

candidates = [
    (f1, 'h11_shop_setselecteditem', 'h11_shop_setselecteditem_candidate', 0x0022A60C, 52),
    (f2, 'h11_shop_checkhasnew', 'h11_shop_checkhasnew_candidate', 0x0022FC98, 48),
    (f3, 'h11_shop_checkhasspecial', 'h11_shop_checkhasspecial_candidate', 0x0022FCC8, 48),
    (f4, 'h11_shop_pushitemrecord', 'h11_shop_pushitemrecord_candidate', 0x00230680, 108),
    (f5, 'h11_shop_isequipslotmatch', 'h11_shop_isequipslotmatch_candidate', 0x00230D24, 140),
    (f6, 'h11_shop_calcpurchasableqty', 'h11_shop_calcpurchasableqty_candidate', 0x00230DB0, 100),
    (f7, 'h11_terminal_setunlockflag', 'h11_terminal_setunlockflag_candidate', 0x00263734, 68),
    (f8, 'h11_terminal_isunlocked', 'h11_terminal_isunlocked_candidate', 0x00263778, 60),
]

all_passed = True
total_window = 0
total_compiled = 0

print("=== Compiling all 8 Milestone H11 Semantic Candidates (Shops, Black Market & Terminals) ===")
for src, name, cand_fn, addr, orig_size in candidates:
    obj = BUILD_DIR / f'{name}.o'
    res = compile_tu_armv6k(src, obj, ROOT)
    if res.returncode != 0:
        print(f"FAILED to compile {src}: {res.stderr}")
        all_passed = False
        continue

    funcs = extract_elf_functions_detailed(obj)
    if cand_fn not in funcs:
        print(f"FAILED: symbol {cand_fn} not found in {obj}")
        all_passed = False
        continue

    code, relocs = funcs[cand_fn]
    cand_size = len(code)
    margin = orig_size - cand_size
    total_window += orig_size
    total_compiled += cand_size

    status = "OK" if margin >= 0 else "OVERFLOW"
    if margin < 0:
        all_passed = False

    print(f"[{status}] {name:<36} | Cand: {cand_size:>4} B | Window: {orig_size:>4} B | Headroom: +{margin:>4} B | Relocs: {len(relocs)}")

print("-" * 80)
print(f"Total window: {total_window} B | Total compiled: {total_compiled} B | Overall headroom: +{total_window - total_compiled} B")

if not all_passed:
    sys.exit(1)

print("\nALL 8 H11 CANDIDATES SUCCESSFULLY BUILT WITHIN ORIGINAL WINDOW FOOTPRINTS!")
