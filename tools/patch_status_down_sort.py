#!/usr/bin/env python3
"""
Patch 9 StatusDown sort comparator functions in src/ui/status_down.cpp
with verified C++ implementations.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = ROOT / "src" / "ui" / "status_down.cpp"

NEW_SORT_FUNCTIONS = {
    "StatusDown_SkillSortByNameAsc": """// DECOMP_FUNC(0x001f6174, 48)
s32 StatusDown_SkillSortByNameAsc(const void* a, const void* b) {
    const auto* ea = static_cast<const StatusDownListEntry*>(a);
    const auto* eb = static_cast<const StatusDownListEntry*>(b);
    const auto* sa = reinterpret_cast<const SkillTableEntry*>(camp_func_00257744(ea->value));
    const auto* sb = reinterpret_cast<const SkillTableEntry*>(camp_func_00257744(eb->value));
    return static_cast<s32>(sa->sort_order) - static_cast<s32>(sb->sort_order);
}""",

    "StatusDown_SkillSortByIdAsc": """// DECOMP_FUNC(0x00206be8, 80)
s32 StatusDown_SkillSortByIdAsc(const void* a, const void* b) {
    const auto* ea = static_cast<const StatusDownListEntry*>(a);
    const auto* eb = static_cast<const StatusDownListEntry*>(b);
    const auto* ia = reinterpret_cast<const ItemTableEntry*>(camp_func_002b9364(ea->id));
    const auto* ib = reinterpret_cast<const ItemTableEntry*>(camp_func_002b9364(eb->id));
    s32 diff = static_cast<s32>(ia->category) - static_cast<s32>(ib->category);
    if (diff != 0) {
        return diff;
    }
    diff = static_cast<s32>(ib->rarity) - static_cast<s32>(ia->rarity);
    if (diff != 0) {
        return diff;
    }
    return static_cast<s32>(ia->id) - static_cast<s32>(ib->id);
}""",

    "StatusDown_SkillSortByIdDesc": """// DECOMP_FUNC(0x002e4534, 80)
s32 StatusDown_SkillSortByIdDesc(const void* a, const void* b) {
    const auto* ea = static_cast<const StatusDownListEntry*>(a);
    const auto* eb = static_cast<const StatusDownListEntry*>(b);
    const auto* ia = reinterpret_cast<const ItemTableEntry*>(camp_func_002b9364(ea->id));
    const auto* ib = reinterpret_cast<const ItemTableEntry*>(camp_func_002b9364(eb->id));
    s32 diff = static_cast<s32>(ib->category) - static_cast<s32>(ia->category);
    if (diff != 0) {
        return diff;
    }
    diff = static_cast<s32>(ib->rarity) - static_cast<s32>(ia->rarity);
    if (diff != 0) {
        return diff;
    }
    return static_cast<s32>(ia->id) - static_cast<s32>(ib->id);
}""",

    "StatusDown_SkillSortByCostAsc": """// DECOMP_FUNC(0x001f60dc, 152)
s32 StatusDown_SkillSortByCostAsc(const void* a, const void* b) {
    const auto* ea = static_cast<const StatusDownListEntry*>(a);
    const auto* eb = static_cast<const StatusDownListEntry*>(b);
    const auto* sa = reinterpret_cast<const SkillTableEntry*>(camp_func_00257744(ea->value));
    const auto* sb = reinterpret_cast<const SkillTableEntry*>(camp_func_00257744(eb->value));
    s32 ca = func_00257678(sa->cost_raw);
    s32 cb = func_00257678(sb->cost_raw);
    s32 diff = ca - cb;
    if (diff != 0) {
        return diff;
    }
    const auto* ia = reinterpret_cast<const ItemTableEntry*>(camp_func_002b9364(ea->id));
    const auto* ib = reinterpret_cast<const ItemTableEntry*>(camp_func_002b9364(eb->id));
    diff = static_cast<s32>(ia->category) - static_cast<s32>(ib->category);
    if (diff != 0) {
        return diff;
    }
    diff = static_cast<s32>(ib->rarity) - static_cast<s32>(ia->rarity);
    if (diff != 0) {
        return diff;
    }
    return static_cast<s32>(ia->id) - static_cast<s32>(ib->id);
}""",

    "StatusDown_SkillSortByCostDesc": """// DECOMP_FUNC(0x002dc96c, 152)
s32 StatusDown_SkillSortByCostDesc(const void* a, const void* b) {
    const auto* ea = static_cast<const StatusDownListEntry*>(a);
    const auto* eb = static_cast<const StatusDownListEntry*>(b);
    const auto* sa = reinterpret_cast<const SkillTableEntry*>(camp_func_00257744(ea->value));
    const auto* sb = reinterpret_cast<const SkillTableEntry*>(camp_func_00257744(eb->value));
    s32 ca = func_00257678(sa->cost_raw);
    s32 cb = func_00257678(sb->cost_raw);
    s32 diff = cb - ca;
    if (diff != 0) {
        return diff;
    }
    const auto* ia = reinterpret_cast<const ItemTableEntry*>(camp_func_002b9364(ea->id));
    const auto* ib = reinterpret_cast<const ItemTableEntry*>(camp_func_002b9364(eb->id));
    diff = static_cast<s32>(ib->category) - static_cast<s32>(ia->category);
    if (diff != 0) {
        return diff;
    }
    diff = static_cast<s32>(ib->rarity) - static_cast<s32>(ia->rarity);
    if (diff != 0) {
        return diff;
    }
    return static_cast<s32>(ia->id) - static_cast<s32>(ib->id);
}""",

    "StatusDown_ItemSortByTypeAsc": """// DECOMP_FUNC(0x00206c38, 132)
s32 StatusDown_ItemSortByTypeAsc(const void* a, const void* b) {
    const auto* ea = static_cast<const StatusDownListEntry*>(a);
    const auto* eb = static_cast<const StatusDownListEntry*>(b);
    u16 va = ea->value;
    u16 vb = eb->value;
    if (va == 0) {
        return vb != 0 ? 1 : 0;
    }
    if (vb == 0) {
        return -1;
    }
    s32 diff = static_cast<s32>(va) - static_cast<s32>(vb);
    if (diff != 0) {
        return diff;
    }
    const auto* ia = reinterpret_cast<const ItemTableEntry*>(camp_func_002b9364(ea->id));
    const auto* ib = reinterpret_cast<const ItemTableEntry*>(camp_func_002b9364(eb->id));
    diff = static_cast<s32>(ia->category) - static_cast<s32>(ib->category);
    if (diff != 0) {
        return diff;
    }
    diff = static_cast<s32>(ib->rarity) - static_cast<s32>(ia->rarity);
    if (diff != 0) {
        return diff;
    }
    return static_cast<s32>(ia->id) - static_cast<s32>(ib->id);
}""",

    "StatusDown_ItemSortByTypeDesc": """// DECOMP_FUNC(0x002e4584, 132)
s32 StatusDown_ItemSortByTypeDesc(const void* a, const void* b) {
    const auto* ea = static_cast<const StatusDownListEntry*>(a);
    const auto* eb = static_cast<const StatusDownListEntry*>(b);
    u16 va = ea->value;
    u16 vb = eb->value;
    if (va == 0) {
        return vb != 0 ? 1 : 0;
    }
    if (vb == 0) {
        return -1;
    }
    s32 diff = static_cast<s32>(vb) - static_cast<s32>(va);
    if (diff != 0) {
        return diff;
    }
    const auto* ia = reinterpret_cast<const ItemTableEntry*>(camp_func_002b9364(ea->id));
    const auto* ib = reinterpret_cast<const ItemTableEntry*>(camp_func_002b9364(eb->id));
    diff = static_cast<s32>(ib->category) - static_cast<s32>(ia->category);
    if (diff != 0) {
        return diff;
    }
    diff = static_cast<s32>(ia->rarity) - static_cast<s32>(ib->rarity);
    if (diff != 0) {
        return diff;
    }
    return static_cast<s32>(ib->id) - static_cast<s32>(ia->id);
}""",

    "StatusDown_ItemSortByIdAsc": """// DECOMP_FUNC(0x00206cbc, 124)
s32 StatusDown_ItemSortByIdAsc(const void* a, const void* b) {
    const auto* ea = static_cast<const StatusDownListEntry*>(a);
    const auto* eb = static_cast<const StatusDownListEntry*>(b);
    u16 va = ea->value;
    u16 vb = eb->value;
    if (va == 0) {
        return vb != 0 ? 1 : 0;
    }
    if (vb == 0) {
        return -1;
    }
    const auto* ia = reinterpret_cast<const ItemTableEntry*>(camp_func_002b9364(ea->id));
    const auto* ib = reinterpret_cast<const ItemTableEntry*>(camp_func_002b9364(eb->id));
    s32 diff = static_cast<s32>(ia->category) - static_cast<s32>(ib->category);
    if (diff != 0) {
        return diff;
    }
    diff = static_cast<s32>(ib->rarity) - static_cast<s32>(ia->rarity);
    if (diff != 0) {
        return diff;
    }
    return static_cast<s32>(ia->id) - static_cast<s32>(ib->id);
}""",

    "StatusDown_ItemSortByIdDesc": """// DECOMP_FUNC(0x002e4608, 124)
s32 StatusDown_ItemSortByIdDesc(const void* a, const void* b) {
    const auto* ea = static_cast<const StatusDownListEntry*>(a);
    const auto* eb = static_cast<const StatusDownListEntry*>(b);
    u16 va = ea->value;
    u16 vb = eb->value;
    if (va == 0) {
        return vb != 0 ? 1 : 0;
    }
    if (vb == 0) {
        return -1;
    }
    const auto* ia = reinterpret_cast<const ItemTableEntry*>(camp_func_002b9364(ea->id));
    const auto* ib = reinterpret_cast<const ItemTableEntry*>(camp_func_002b9364(eb->id));
    s32 diff = static_cast<s32>(ib->category) - static_cast<s32>(ia->category);
    if (diff != 0) {
        return diff;
    }
    diff = static_cast<s32>(ia->rarity) - static_cast<s32>(ib->rarity);
    if (diff != 0) {
        return diff;
    }
    return static_cast<s32>(ib->id) - static_cast<s32>(ia->id);
}""",
}

def main():
    text = SRC_PATH.read_text(encoding="utf-8")

    for name, new_code in NEW_SORT_FUNCTIONS.items():
        pos = text.find(name + '(')
        if pos == -1:
            pos = text.find(name + ' (')
        if pos == -1:
            pos = text.find(name)
        assert pos != -1, f"Function {name} not found"

        brace_start = text.find('{', pos)
        depth = 0
        brace_end = -1
        for i in range(brace_start, len(text)):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    brace_end = i
                    break
        assert brace_end != -1, f"Matching brace not found for {name}"

        func_start = text.rfind('// DECOMP_FUNC', 0, pos)
        if func_start != -1 and text[func_start:pos].count('{') > 0:
            func_start = text.rfind('\n', 0, pos) + 1
        elif func_start == -1:
            func_start = text.rfind('\n', 0, pos) + 1

        text = text[:func_start] + new_code + text[brace_end + 1:]
        print(f"Replaced {name}")

    SRC_PATH.write_text(text, encoding="utf-8")
    print(f"Successfully patched all {len(NEW_SORT_FUNCTIONS)} sort functions in {SRC_PATH}!")

if __name__ == "__main__":
    main()
