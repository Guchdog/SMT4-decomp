#!/usr/bin/env python3
"""
Patch 27 StatusDown state machine, field query, and cursor helper functions
in src/ui/status_down.cpp with verified C++ implementations using robust
brace matching.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = ROOT / "src" / "ui" / "status_down.cpp"

NEW_FUNCTIONS = {
    "StatusDown_SetActiveSoundId": """// DECOMP_FUNC(0x00215a44, 28)
void StatusDown_SetActiveSoundId(s16 id) {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    if (work != nullptr) {
        work->active_sound_id = id;
    }
}""",

    "StatusDown_IsState20": """// DECOMP_FUNC(0x00223b88, 40)
bool StatusDown_IsState20() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    if (work == nullptr) {
        return false;
    }
    return work->state == 0x14;
}""",

    "StatusDown_SetVisibility": """// DECOMP_FUNC(0x0026d8c0, 28)
void StatusDown_SetVisibility(u8 val) {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    if (work != nullptr) {
        work->visibility_flag = val;
    }
}""",

    "StatusDown_GetField2384": """// DECOMP_FUNC(0x0028cd5c, 28)
u32 StatusDown_GetField2384() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    if (work == nullptr) {
        return 0;
    }
    return work->field_2384;
}""",

    "StatusDown_IsInactiveOrState0": """// DECOMP_FUNC(0x0028cd78, 36)
bool StatusDown_IsInactiveOrState0() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    if (work == nullptr) {
        return true;
    }
    return work->state == 0;
}""",

    "StatusDown_IsNotTransitioning": """// DECOMP_FUNC(0x00293d2c, 36)
bool StatusDown_IsNotTransitioning() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    return (work->state != 0x12 && work->state != 0x14);
}""",

    "StatusDown_GetStatusMode": """// DECOMP_FUNC(0x00293e30, 28)
s8 StatusDown_GetStatusMode() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    if (work == nullptr) {
        return 0;
    }
    return work->status_mode;
}""",

    "StatusDown_IsNotState1": """// DECOMP_FUNC(0x0029c70c, 32)
bool StatusDown_IsNotState1() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    return work->state != 1;
}""",

    "StatusDown_IsNotState2": """// DECOMP_FUNC(0x0029c72c, 32)
bool StatusDown_IsNotState2() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    return work->state != 2;
}""",

    "StatusDown_EnterState3_Alt": """// DECOMP_FUNC(0x002d9618, 36)
void StatusDown_EnterState3_Alt() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    work->state_timer = 0;
    u32 prev = work->state;
    work->state = 3;
    work->prev_state = prev;
}""",

    "StatusDown_IsNotState4": """// DECOMP_FUNC(0x002efe0c, 32)
bool StatusDown_IsNotState4() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    return work->state != 4;
}""",

    "StatusDown_GetField2388": """// DECOMP_FUNC(0x002efe2c, 28)
s8 StatusDown_GetField2388() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    if (work == nullptr) {
        return 0;
    }
    return work->field_2388;
}""",

    "StatusDown_IsState7": """// DECOMP_FUNC(0x002f6524, 44)
bool StatusDown_IsState7() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    if (work == nullptr) {
        return false;
    }
    return work->state == 7;
}""",

    "StatusDown_EnterState3": """// DECOMP_FUNC(0x002f66e8, 36)
void StatusDown_EnterState3() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    work->state_timer = 0;
    u32 prev = work->state;
    work->state = 3;
    work->prev_state = prev;
}""",

    "StatusDown_EnterState6_Simple": """// DECOMP_FUNC(0x0030aa98, 40)
void StatusDown_EnterState6_Simple() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    if (work != nullptr) {
        u32 prev = work->state;
        work->state = 6;
        work->prev_state = prev;
    }
}""",

    "StatusDown_IsState15": """// DECOMP_FUNC(0x0030aac0, 32)
bool StatusDown_IsState15() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    return work->state == 0xF;
}""",

    "StatusDown_IsState10": """// DECOMP_FUNC(0x0030aae0, 32)
bool StatusDown_IsState10() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    return work->state == 0xA;
}""",

    "StatusDown_EnterState14": """// DECOMP_FUNC(0x0030ab00, 52)
void StatusDown_EnterState14(s32 selected_result) {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    if (selected_result == 0) {
        work->selected_result = -1;
    }
    work->state_timer = 0;
    u32 prev = work->state;
    work->state = 0xE;
    work->prev_state = prev;
}""",

    "StatusDown_EnterState4": """// DECOMP_FUNC(0x002efea4, 36)
void StatusDown_EnterState4() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    work->state_timer = 0;
    u32 prev = work->state;
    work->state = 4;
    work->prev_state = prev;
    StatusDown_SetupTouchRegions();
}""",

    "StatusDown_EnterState6": """// DECOMP_FUNC(0x0030ab34, 60)
void StatusDown_EnterState6() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    work->state_timer = 0;
    u32 prev = work->state;
    work->state = 6;
    work->prev_state = prev;
    StatusDown_SetupTouchRegions();
    work->request_close_flag = 0;
}""",

    "StatusDown_RequestClose": """// DECOMP_FUNC(0x00317f80, 36)
void StatusDown_RequestClose() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    if (work != nullptr) {
        work->request_close_flag = 1;
    }
}""",

    "StatusDown_SetSubIdsB": """// DECOMP_FUNC(0x002efe48, 68)
void StatusDown_SetSubIdsB(const u16* ids, s32 count) {
    if (count > 8) {
        return;
    }
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    for (int i = 0; i < 8; i++) {
        work->sub_ids_b[i] = 0;
    }
    AsdMem_Copy(work->sub_ids_b, ids, count * sizeof(u16));
}""",

    "StatusDown_SetSubIdsA": """// DECOMP_FUNC(0x0026abe0, 84)
void StatusDown_SetSubIdsA(const u16* ids, s32 count) {
    if (count > 8) {
        return;
    }
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    for (int i = 0; i < 8; i++) {
        work->sub_ids_a[i] = 0;
    }
    if (count < 0) {
        work->has_sub_ids_a = 0;
        return;
    }
    work->has_sub_ids_a = 1;
    AsdMem_Copy(work->sub_ids_a, ids, count * sizeof(u16));
}""",

    "StatusDown_PopFirstSubIdA": """// DECOMP_FUNC(0x0026b01c, 176)
void StatusDown_PopFirstSubIdA() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    u16 first_a = work->sub_ids_a[0];
    for (int i = 0; i < 8; i++) {
        if (work->sub_ids_b[i] != 0 && work->sub_ids_b[i] == first_a) {
            work->sub_ids_b[i] = 0;
        }
    }
    work->sub_ids_a[0] = 0;
    for (int i = 0; i < 7; i++) {
        for (int j = i; j < 7; j++) {
            if (work->sub_ids_a[j] == 0 && work->sub_ids_a[j + 1] != 0) {
                work->sub_ids_a[j] = work->sub_ids_a[j + 1];
                work->sub_ids_a[j + 1] = 0;
            }
        }
    }
}""",

    "StatusDown_GetPartyMaxIndex": """// DECOMP_FUNC(0x002efde0, 44)
s32 StatusDown_GetPartyMaxIndex() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    if (work == nullptr) {
        return 0;
    }
    return camp_func_0029f0f4(&work->list_cursor_main) - 1;
}""",

    "StatusDown_IsCursorAtLastPartySlot": """// DECOMP_FUNC(0x002f65d4, 76)
bool StatusDown_IsCursorAtLastPartySlot() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    if (work == nullptr) {
        return false;
    }
    s32 cur = camp_func_0029f248(&work->list_cursor_main);
    s32 max = camp_func_0029f0f4(&work->list_cursor_main) - 1;
    return cur == max;
}""",

    "StatusDown_GetSelectedPartyIndex": """// DECOMP_FUNC(0x0032303c, 40)
s32 StatusDown_GetSelectedPartyIndex() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    if (work == nullptr) {
        return -1;
    }
    return camp_func_0029f248(&work->list_cursor_main);
}""",
}

def main():
    text = SRC_PATH.read_text(encoding="utf-8")

    # Add missing extern "C" declarations if not present
    if 'camp_func_0029f0f4' not in text:
        target = 'void  AsdMem_Copy(void* dst, const void* src, u32 size);'
        replacement = target + '\n    s32   camp_func_0029f0f4(void* cursor);\n    s32   camp_func_0029f248(void* cursor);'
        text = text.replace(target, replacement, 1)

    # Perform replacement using brace counting
    for name, new_code in NEW_FUNCTIONS.items():
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
    print(f"Successfully patched all {len(NEW_FUNCTIONS)} functions in {SRC_PATH}!")

if __name__ == "__main__":
    main()
