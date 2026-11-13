#include "types.h"

static __attribute__((always_inline)) inline float inline_vsqrt_f32(float value) {
    float result;
    asm volatile("vsqrt.f32 %0, %1" : "=t"(result) : "t"(value));
    return result;
}

// Batch 45 A: fully decoded ARM TODO functions, preserved byte-for-byte.

// DECOMP_FUNC(0x003d8704, 456)
extern "C" void battle_func_003d8704(void* obj, u32 preset_id, u32 slot_id) {
    u32 offset = 0x568;
    if (slot_id == 1) {
        offset = 0x5AC;
    } else if (slot_id == 2) {
        offset = 0x5F0;
    }

    auto* const target = reinterpret_cast<float*>(static_cast<u8*>(obj) + offset);

    switch (preset_id) {
    case 0:
        target[0x00 / 4] = 0.0f;
        target[0x04 / 4] = 6.3f;
        target[0x08 / 4] = 44.5f;
        target[0x18 / 4] = 0.0f;
        target[0x1C / 4] = 0.0f;
        target[0x20 / 4] = -1.0f;
        target[0x30 / 4] = 44.5f;
        target[0x34 / 4] = 0.0f;
        target[0x38 / 4] = 0.0f;
        target[0x40 / 4] = 35.0f;
        break;

    case 1:
    case 4:
        target[0x00 / 4] = 0.0f;
        target[0x04 / 4] = 2.3f;
        target[0x08 / 4] = 55.0f;
        target[0x18 / 4] = 0.0f;
        target[0x1C / 4] = 0.0f;
        target[0x20 / 4] = -1.0f;
        target[0x30 / 4] = 55.0f;
        target[0x34 / 4] = -7.7f;
        target[0x38 / 4] = 180.0f;
        target[0x40 / 4] = 35.0f;
        break;

    case 2:
        target[0x00 / 4] = 0.7f;
        target[0x04 / 4] = 5.3f;
        target[0x08 / 4] = 39.6f;
        target[0x18 / 4] = 0.8f;
        target[0x1C / 4] = 0.0f;
        target[0x20 / 4] = -0.6f;
        target[0x30 / 4] = 39.6f;
        target[0x34 / 4] = -6.2f;
        target[0x38 / 4] = 180.0f;
        target[0x40 / 4] = 35.0f;
        break;

    case 3:
        target[0x00 / 4] = 1.8f;
        target[0x04 / 4] = 4.0f;
        target[0x08 / 4] = 46.5f;
        target[0x18 / 4] = 0.0f;
        target[0x1C / 4] = 0.0f;
        target[0x20 / 4] = -1.0f;
        target[0x30 / 4] = 46.5f;
        target[0x34 / 4] = -9.9f;
        target[0x38 / 4] = 180.0f;
        target[0x40 / 4] = 30.0f;
        break;

    case 5:
        target[0x00 / 4] = 0.0f;
        target[0x04 / 4] = 2.3f;
        target[0x08 / 4] = 53.3f;
        target[0x18 / 4] = 0.0f;
        target[0x1C / 4] = 0.0f;
        target[0x20 / 4] = -1.0f;
        target[0x30 / 4] = 53.3f;
        target[0x34 / 4] = -7.7f;
        target[0x38 / 4] = 180.0f;
        target[0x40 / 4] = 35.0f;
        break;

    default:
        break;
    }
}

// DECOMP_FUNC(0x00250108, 480)
extern "C" void func_00250108(float* m, const float* v, u32 mode) {
    if (mode == 0) {
        // Set to scale matrix
        m[0]  = v[0]; m[1]  = 0.0f; m[2]  = 0.0f; m[3]  = 0.0f;
        m[4]  = 0.0f; m[5]  = v[1]; m[6]  = 0.0f; m[7]  = 0.0f;
        m[8]  = 0.0f; m[9]  = 0.0f; m[10] = v[2]; m[11] = 0.0f;
        m[12] = 0.0f; m[13] = 0.0f; m[14] = 0.0f; m[15] = 1.0f;
    } else if (mode == 1) {
        // Pre-multiply by scale (scale rows 0..2)
        m[0] *= v[0]; m[1] *= v[0]; m[2] *= v[0];
        m[4] *= v[1]; m[5] *= v[1]; m[6] *= v[1];
        m[8] *= v[2]; m[9] *= v[2]; m[10] *= v[2];
    } else if (mode == 2) {
        // Post-multiply by scale (scale columns 0..2)
        m[0]  *= v[0]; m[1]  *= v[1]; m[2]  *= v[2];
        m[4]  *= v[0]; m[5]  *= v[1]; m[6]  *= v[2];
        m[8]  *= v[0]; m[9]  *= v[1]; m[10] *= v[2];
        m[12] *= v[0]; m[13] *= v[1]; m[14] *= v[2];
    }
}

// DECOMP_FUNC(0x0024bfbc, 528)
extern "C" u32 ui_func_002be7fc(char* dst, const char* fmt, ...);

extern "C" u32 camp_func_0024bfbc(char* out_buf, u32 element_id) {
    const char* str = nullptr;
    switch (element_id) {
    case 0:
        str = "\x82\x6f\x82\x88\x82\x99\x82\x93"; // Phys
        break;
    case 1:
        str = "\x82\x66\x82\x95\x82\x8e"; // Gun
        break;
    case 2:
        str = "\x82\x65\x82\x89\x82\x92\x82\x85"; // Fire
        break;
    case 3:
        str = "\x82\x68\x82\x83\x82\x85"; // Ice
        break;
    case 4:
        str = "\x82\x64\x82\x8c\x82\x85\x82\x83"; // Elec
        break;
    case 5:
        str = "\x82\x65\x82\x8f\x82\x92\x82\x83\x82\x85"; // Force
        break;
    case 6:
        str = "\x82\x6b\x82\x89\x82\x87\x82\x88\x82\x94"; // Light
        break;
    case 7:
        str = "\x82\x63\x82\x81\x82\x92\x82\x8b"; // Dark
        break;
    case 0xB:
        str = "\x82\x6f\x82\x8f\x82\x89\x82\x93\x82\x8f\x82\x8e"; // Poison
        break;
    case 0xC:
        str = "\x82\x6f\x82\x81\x82\x8e\x82\x89\x82\x83"; // Panic
        break;
    case 0xD:
        str = "\x82\x72\x82\x8c\x82\x85\x82\x85\x82\x90"; // Sleep
        break;
    case 0xE:
        str = "\x82\x61\x82\x89\x82\x8e\x82\x84"; // Bind
        break;
    case 0xF:
        str = "\x82\x72\x82\x89\x82\x83\x82\x8b"; // Sick
        break;
    case 0x10:
        str = "\x82\x6b\x82\x8f\x82\x93\x82\x94"; // Lost
        break;
    case 0x11:
        str = "\x82\x60\x82\x8c\x82\x8d\x82\x89\x82\x87\x82\x88\x82\x94\x82\x99"; // Almighty
        break;
    case 0x12:
        str = "\x82\x67\x82\x85\x82\x81\x82\x8c"; // Heal
        break;
    default:
        return 0;
    }
    return ui_func_002be7fc(out_buf, str);
}

// DECOMP_FUNC(0x0022e008, 572)
//
// Camp menu selection-change dispatcher. The incoming r0 points at the camp
// work area. The function resolves the current list entry, compares its id
// against the selected id stored in the work area, and (depending on the menu
// mode / animation sub-mode) rebinds the selection, builds the per-selection
// scratch record on the stack, and refreshes the menu.
extern "C" u32 shop_func_002337a0(const void* list);
extern "C" u32 script_vm_func_0029e398(const void* entry);
extern "C" void camp_func_0029db40(u32 id);
extern "C" void camp_func_0029d924(u32 enable);
extern "C" u32 camp_func_0022d33c(u8* work);
extern "C" u8* camp_func_002a8a08(u32 sub_mode);
extern "C" u8* camp_func_002b9364(u32 id);
extern "C" void ui_func_002bcf58(void* dst, const void* src, u32 size);
extern "C" void engine_func_002c4b30(void* dst, u32 size);
extern "C" void camp_func_0024be90(u8* base, u32 bit_index);
extern "C" void script_vm_func_0029c950(void* ctx);
extern "C" void script_vm_func_0029c784(void* ctx, u32 keep_scroll);
extern "C" void script_vm_func_0029c768(u32 value);
extern "C" void ui_func_00258c58(u32 value);
extern "C" u32 camp_func_0029e260(u32 value);

namespace {

constexpr u32 kEntryTableOffset = 0x5A8;      // u16 count / start of 0x20-byte entries
constexpr u32 kModeOffset = 0x5A4;            // 0 = plain selection path, 1 = menu mode
constexpr u32 kSubModeOffset = 0x5A5;         // animation sub-mode for kModeOffset == 1
constexpr u32 kDirtyOffset = 0x5A7;           // pending-refresh flag
constexpr u32 kSelectedIdOffset = 0xA5B2;     // u16 currently selected list id
constexpr u32 kEntrySize = 0x20;
constexpr u32 kEntryIdOffset = 4;             // u16 id inside a list entry

constexpr u32 kSelectRecordSize = 0x604;      // per-selection record copied to scratch
constexpr u32 kScratchSize = 0x610;           // stack scratch area used by the original
constexpr u32 kScratchZeroBegin = 0x4C;
constexpr u32 kScratchZeroEnd = 0x88;
constexpr u32 kScratchClearOffset = 0x8C;
constexpr u32 kScratchClearSize = 0x500;

constexpr u32 kCampListCountOffset = 0x910B;  // u8 number of list slots
constexpr u32 kCampListIndexOffset = 0x90F0;  // s8 slot indices, one per list position
constexpr u32 kCampListRecordBase = 0x90;     // record + 0x90 is the copy source
constexpr u32 kCampListIdOffset = 0xD6;       // u16 id inside a slot record
constexpr u32 kCampListRecordStride = 0x604;  // 1540-byte list records

inline u8& byte_at(void* base, u32 offset) {
    return *reinterpret_cast<u8*>(static_cast<u8*>(base) + offset);
}

inline u16& half_at(void* base, u32 offset) {
    return *reinterpret_cast<u16*>(static_cast<u8*>(base) + offset);
}

}  // namespace

extern "C" u32 camp_func_0022e008(u8* work) {
    if (half_at(work, kEntryTableOffset) == 0) {
        // Empty list: forward the disabled-state notification as a tail call.
        return camp_func_0029e260(0);
    }

    const u32 index = shop_func_002337a0(work + 0x20);
    u8* const entry = work + kEntryTableOffset + index * kEntrySize;
    const u16 id = half_at(entry, kEntryIdOffset);

    if (script_vm_func_0029e398(entry) == 0) {
        return 0;
    }

    u16* const selected_id = reinterpret_cast<u16*>(work + kSelectedIdOffset);

    if (byte_at(work, kModeOffset) != 1) {
        if (*selected_id == id) {
            return *selected_id;
        }
        camp_func_0029db40(id);
        camp_func_0029d924(1);
        const u32 result = camp_func_0022d33c(work);
        *selected_id = id;
        return result;
    }

    // Menu mode. With no pending refresh, reselecting the same id is a no-op.
    if (byte_at(work, kDirtyOffset) == 0 && *selected_id == id) {
        return *selected_id;
    }

    if (byte_at(work, kSubModeOffset) != 1) {
        camp_func_0029db40(id);
        script_vm_func_0029c768(0);
        if (byte_at(work, kDirtyOffset) != 0) {
            ui_func_00258c58(0);
        } else {
            camp_func_0029d924(1);
        }
    } else {
        // Animation sub-mode: locate the slot record backing the selection.
        u8* const list = camp_func_002a8a08(1);
        u8* record_base = nullptr;
        const u32 count = byte_at(list, kCampListCountOffset);
        for (u32 i = 0; i < count; ++i) {
            const s8 slot = static_cast<s8>(byte_at(list, kCampListIndexOffset + i));
            if (slot < 0) {
                continue;
            }
            u8* const record = list + static_cast<u32>(slot) * kCampListRecordStride;
            record_base = record + kCampListRecordBase;
            if (half_at(record, kCampListIdOffset) == id) {
                break;
            }
        }

        camp_func_0029db40(id);
        u8* const info = camp_func_002b9364(id);

        u8 scratch[kScratchSize];
        ui_func_002bcf58(scratch, record_base, kSelectRecordSize);

        for (u32 offset = kScratchZeroBegin; offset <= kScratchZeroEnd; offset += 4) {
            *reinterpret_cast<u32*>(scratch + offset) = 0;
        }
        engine_func_002c4b30(scratch + kScratchClearOffset, kScratchClearSize);

        camp_func_0024be90(scratch, half_at(info, 0x38));
        script_vm_func_0029c950(scratch);

        half_at(scratch, 0x44) = 0;
        half_at(scratch, 0x2A) = half_at(scratch, 0x0E);
        half_at(scratch, 0x2C) = half_at(scratch, 0x10);

        script_vm_func_0029c784(scratch, 0);
        script_vm_func_0029c768(1);

        if (byte_at(work, kDirtyOffset) != 0) {
            ui_func_00258c58(1);
        } else {
            camp_func_0029d924(1);
        }
    }

    byte_at(work, kDirtyOffset) = 0;
    const u32 result = camp_func_0022d33c(work);
    *selected_id = id;
    return result;
}

// DECOMP_FUNC(0x002580a8, 576)
extern "C" s32 ui_func_00297004(s32 min_val, s32 max_val);

struct UiShakeState {
    float amp_x;
    float amp_y;
    float offset_x;
    float offset_y;
    s16 max_timer;
    s16 timer;
};

extern "C" void ui_func_002580a8(UiShakeState* state) {
    s16 max_timer = state->max_timer;
    s16 timer = state->timer;

    if (max_timer != -1 && max_timer <= timer) {
        if (state != nullptr) {
            state->amp_x = 0.0f;
            state->amp_y = 0.0f;
            state->offset_x = 0.0f;
            state->offset_y = 0.0f;
            state->max_timer = 0;
            state->timer = 0;
        }
        return;
    }

    if (timer < 0) {
        state->timer = timer + 1;
        state->offset_x = 0.0f;
        state->offset_y = 0.0f;
        return;
    }

    float amp_x = state->amp_x;
    float amp_y = state->amp_y;

    if (max_timer != -1 && max_timer > 3) {
        s32 remaining = max_timer - timer;
        if (remaining <= 3) {
            float damping = static_cast<float>(remaining) * 0.25f;
            amp_x *= damping;
            amp_y *= damping;
        }
    }

    s32 rand_x_int = ui_func_00297004(static_cast<s32>(amp_x * 50.0f), static_cast<s32>(amp_x * 100.0f));
    s32 rand_y_int = ui_func_00297004(static_cast<s32>(amp_y * 50.0f), static_cast<s32>(amp_y * 100.0f));

    float mag_x = static_cast<float>(rand_x_int) * 0.01f;
    float mag_y = static_cast<float>(rand_y_int) * 0.01f;

    s32 sign_x = (ui_func_00297004(0, 1) != 0) ? 1 : -1;
    s32 sign_y = (ui_func_00297004(0, 1) != 0) ? 1 : -1;

    float prev_x = state->offset_x;
    float prev_y = state->offset_y;

    s32 sign_prev_x = (prev_x > 0.0f) ? 1 : -1;
    s32 sign_prev_y = (prev_y > 0.0f) ? 1 : -1;

    if (prev_x == 0.0f && prev_y == 0.0f) {
        state->offset_x = mag_x * static_cast<float>(sign_x);
        state->offset_y = mag_y * static_cast<float>(sign_y);
    } else {
        bool choose_branch_y = false;
        if (prev_x == 0.0f) {
            choose_branch_y = true;
        } else if (prev_y == 0.0f) {
            choose_branch_y = false;
        } else {
            choose_branch_y = (ui_func_00297004(0, 1) == 0);
        }

        if (choose_branch_y) {
            state->offset_x = mag_x * static_cast<float>(sign_x);
            state->offset_y = mag_y * static_cast<float>(sign_prev_y);
        } else {
            state->offset_x = mag_x * static_cast<float>(sign_prev_x);
            state->offset_y = mag_y * static_cast<float>(sign_y);
        }
    }

    if (state->timer < 0x7FFE) {
        state->timer++;
    }
}

// DECOMP_FUNC(0x0029dcd4, 576)
extern "C" u8* camp_func_002b9364(u32 skill_id);
extern "C" void camp_func_0029f088(u32 widget_id, u32 a1, u32 a2);
extern "C" void ui_func_00290a68(char* dst, u32 val);
extern "C" void script_vm_func_00295904(u32 widget_id, const char* str);
extern "C" void shop_func_0024beac(char* dst, u32 target_scope);
extern "C" void engine_func_001f4480(u32 a0, u32 a1, u32 a2, char* dst);
extern "C" void script_vm_func_00296d8c(void* obj, u32 a1, u32 a2, u32 a3, u32 sp0, void* sp1, u32 sp2);

extern "C" void camp_func_0029dcd4(void* target, u32 arg1, u32 skill_id, u32 sub_id) {
    auto* mgr = reinterpret_cast<void**>(0x0043da28);
    auto* work = reinterpret_cast<u8*>(mgr[1]);

    u8* skill = camp_func_002b9364(skill_id);
    if (!skill) {
        work[0x4cb] = 0;
        return;
    }

    work[0x55c] = 1;
    work[0x4cb] = 1;

    u16 flags = *reinterpret_cast<u16*>(skill + 8);
    u32 min_hits = (flags >> 5) & 7;
    u32 max_hits = (flags >> 8) & 7;

    char buf[128];
    if (min_hits == max_hits) {
        camp_func_0029f088(0x25, 0xffffffff, 0);
    } else {
        char str_min[8];
        char str_max[8];
        ui_func_00290a68(str_min, min_hits);
        ui_func_00290a68(str_max, max_hits);
        ui_func_002be7fc(buf, "%s\x81\x60%s", str_min, str_max);
        script_vm_func_00295904(0x25, buf);
    }

    u8 element_id = skill[0x0a];
    camp_func_0024bfbc(buf, element_id);
    script_vm_func_00295904(0x26, buf);

    u32 target_scope = (flags >> 1) & 0xf;
    shop_func_0024beac(buf, target_scope);
    script_vm_func_00295904(0x27, buf);

    u8 ailment_id = skill[0x0c];
    const char* ailment_str = nullptr;
    if (ailment_id == 0) {
        ailment_str = "\x82\x6d\x82\x8f\x82\x8e\x82\x85";
    } else if (ailment_id == 1) {
        ailment_str = "\x82\x6a\x82\x6e";
    } else if (ailment_id == 5) {
        ailment_str = "\x82\x6f\x82\x8f\x82\x89\x82\x93\x82\x8f\x82\x8e";
    } else if (ailment_id == 6) {
        ailment_str = "\x82\x6f\x82\x81\x82\x8e\x82\x89\x82\x83";
    } else if (ailment_id == 7) {
        ailment_str = "\x82\x72\x82\x8c\x82\x85\x82\x85\x82\x90";
    } else if (ailment_id == 8) {
        ailment_str = "\x82\x61\x82\x89\x82\x8e\x82\x84";
    } else if (ailment_id == 9) {
        ailment_str = "\x82\x72\x82\x89\x82\x83\x82\x8b";
    }
    if (ailment_str != nullptr) {
        ui_func_002be7fc(buf, ailment_str);
    }
    script_vm_func_00295904(0x28, buf);

    engine_func_001f4480(0, sub_id, skill_id, buf);
    script_vm_func_00295904(0x29, buf);

    void* draw_target = (target != nullptr) ? target : mgr[2];
    void* render_handle = *reinterpret_cast<void**>(work + 0x558);
    script_vm_func_00296d8c(render_handle, 3, 0xffffffff, 0, 3, draw_target, arg1);
}

// DECOMP_FUNC(0x003beb40, 576)
//
// Integer percentage-like estimator for a unit pair. It combines the primary
// record's stat scaled by 4.5 with the caller-supplied base/scale floats, two
// category multipliers, a status multiplier, a per-record 0.8/1.0 factor, the
// view builder's percentage, an optional battle-object bonus, the camp
// modifier table, and an affinity percentage. The result is converted to a
// signed integer by the FPSCR rounding conversion in the tail.
extern "C" void* ui_func_00293c98();
extern "C" u8* ui_func_0027dca0(void* ui, s32 unit_id);
extern "C" float ui_func_0022a824(s32 category, float unit_id);
extern "C" float ui_func_003be898(s32 primary_id, s32 secondary_id);
extern "C" u8* ui_func_00282b94(void* ui, s32 unit_id);
extern "C" void camp_func_002475e4(void* view, void* ui, const u8* row);
extern "C" void func_0022ac9c(u16 id, void* out);
extern "C" void* battle_func_002ae3f0(void* ctx);
extern "C" s32 script_vm_func_002ae394(void* ctx);
extern "C" s32 func_0028412c(void* object, s32 count, s32 flag);
extern "C" u8* camp_func_0023ebf0();

namespace ui_beb40 {

// Offsets inside a primary/secondary record. The record pointers returned by
// 0x27DCA0 are row + 0xCC, so record + 0xF4 / + 0x14B are row + 0x1C0 /
// row + 0x217.
constexpr u32 kRecordFlags = 0x00;        // u8 flags
constexpr u32 kPrimaryStat = 0xF4;        // s16 stat added as stat * 4.5
constexpr u32 kSecondaryAffinity = 0x14B; // u8 affinity-table index

constexpr u32 kGlobalFlags = 0x44A0;      // u32 flag word on the UI singleton
constexpr u32 kGlobalFlagsSuppressCamp = 0x40000; // bit 18 disables the table

constexpr u32 kRowBonusFlag = 0x02;       // row[0] bit 1 gates the bonus lookup
constexpr u8 kRecordScaledFlag = 0x04;    // record[0] bit 2 selects 0.8

constexpr s32 kCategoryPrimary = 8;       // 0x22A824 category for the primary id
constexpr s32 kCategorySecondary = 10;    // 0x22A824 category for the secondary id

constexpr float kStatScale = 4.5f;
constexpr float kOneThird = 1.0f / 3.0f;
constexpr float kPercentScale = 0.01f;
constexpr float kHalf = 0.5f;
constexpr float kUnscaled = 1.0f;
constexpr float kScaled = 0.8f;

constexpr u32 kViewPercentOffset = 8;     // u16 percentage inside the view
constexpr u32 kViewAffinityOffset = 0x0E; // indexed affinity byte table
constexpr u32 kViewSentinelOffset = 2;    // u16 forwarded to 0x22AC9C

struct View {
    u8 bytes[0x22];
};

inline u16 load_u16(const u8* p) {
    return static_cast<u16>(p[0] | (static_cast<u16>(p[1]) << 8));
}

}  // namespace ui_beb40

extern "C" s32 ui_func_003beb40(void* ctx, s32 primary_id, s32 secondary_id,
                                s32 range_a, s32 range_b, float base_value,
                                float scale) {
    void* const ui = ui_func_00293c98();
    const u8* const primary_record = ui_func_0027dca0(ui, primary_id);
    const u8* const secondary_record = ui_func_0027dca0(ui, secondary_id);

    const s16 primary_stat =
        *reinterpret_cast<const s16*>(primary_record + ui_beb40::kPrimaryStat);
    const u8 primary_flags = primary_record[ui_beb40::kRecordFlags];
    const float record_scale =
        (primary_flags & ui_beb40::kRecordScaledFlag) != 0
            ? ui_beb40::kScaled
            : ui_beb40::kUnscaled;

    const float category_primary = ui_func_0022a824(
        ui_beb40::kCategoryPrimary, static_cast<float>(primary_id));
    const float category_secondary = ui_func_0022a824(
        ui_beb40::kCategorySecondary, static_cast<float>(secondary_id));
    const float status_scale = ui_func_003be898(primary_id, secondary_id);
    const float combined_scale =
        category_primary * category_secondary * status_scale;

    ui_beb40::View view;
    const u8* const primary_row = ui_func_00282b94(ui, primary_id);
    camp_func_002475e4(&view, ui, primary_row);

    // The original forwards view[2..3] to the id mapper and never reads the
    // written word, but keeps the call in the sequence.
    u32 mapped_id = 0;
    func_0022ac9c(
        ui_beb40::load_u16(view.bytes + ui_beb40::kViewSentinelOffset),
        &mapped_id);

    void* const ui_again = ui_func_00293c98();
    const u8* const bonus_row = ui_func_00282b94(ui_again, primary_id);

    s32 bonus = 0;
    if ((*reinterpret_cast<const u32*>(bonus_row) & ui_beb40::kRowBonusFlag) != 0) {
        void* const object = battle_func_002ae3f0(ctx);
        if (object != nullptr) {
            bonus = func_0028412c(object, script_vm_func_002ae394(ctx), 1);
        }
    }

    const u16 view_percent =
        ui_beb40::load_u16(view.bytes + ui_beb40::kViewPercentOffset);
    const s32 range_sum = static_cast<s32>(
        static_cast<u32>(range_a) + static_cast<u32>(range_b));

    // Same operation order as the original: base, 1/3, caller scale, combined
    // helper factors, record factor, view percentage, divisor, bonus.
    float result =
        (base_value + static_cast<float>(primary_stat) * ui_beb40::kStatScale) *
        ui_beb40::kOneThird * scale;
    result = result * combined_scale;
    result = result * record_scale;
    result = result *
             (static_cast<float>(view_percent) * ui_beb40::kPercentScale);
    result = result / (ui_beb40::kHalf * static_cast<float>(range_sum));
    result = result + 0.0f;
    result = result + static_cast<float>(bonus);

    const u32 global_flags = *reinterpret_cast<const u32*>(
        static_cast<u8*>(ui_again) + ui_beb40::kGlobalFlags);
    if ((global_flags & ui_beb40::kGlobalFlagsSuppressCamp) == 0) {
        const u8* const camp = camp_func_0023ebf0();
        const float multiplier =
            (secondary_record[ui_beb40::kRecordFlags] &
             ui_beb40::kRecordScaledFlag) != 0
                ? *reinterpret_cast<const float*>(camp)
                : *reinterpret_cast<const float*>(camp + 8);
        result = result * multiplier;
    }

    const u8 affinity_index = secondary_record[ui_beb40::kSecondaryAffinity];
    const u8 affinity =
        view.bytes[ui_beb40::kViewAffinityOffset + affinity_index];
    if (affinity != 0) {
        result = result *
                 (static_cast<float>(affinity) * ui_beb40::kPercentScale);
    }

    return static_cast<s32>(result);
}

// DECOMP_FUNC(0x002a72fc, 580)
//
// Script VM context teardown. Releases every owned object in a fixed order,
// clears the owning pointer slot, and returns 1. The context is a live work
// area; the helper functions below perform the actual per-object destruction
// and are not reconstructed here.
extern "C" void ui_func_002a7bd4(void* ctx);
extern "C" void script_vm_func_002a7b50(void* obj);
extern "C" void script_vm_func_002aeb2c(u32 id, u32 value);
extern "C" void engine_func_002aea7c(u32 id);
extern "C" void func_002a4974(void* unused);
extern "C" void func_0014c968(void* unused);
extern "C" void func_0014c970(void* unused);
extern "C" void engine_func_002a4ef0(void* obj);
extern "C" void engine_func_002b2520(void* obj);
extern "C" void script_vm_func_00152af8(void* obj);
extern "C" void script_vm_func_002a7aa0(void* obj);
extern "C" void script_vm_func_002a7604(u32 value);
extern "C" void script_vm_func_002a755c(void* obj);
extern "C" void engine_func_002c4360(void* obj);
extern "C" void script_vm_func_002c0128();
extern "C" void ui_func_002a7540(u32 value);

namespace script_vm_2a72fc {

constexpr u32 kObjectLoopBase = 0x28C;   // 4 owned object pointers
constexpr u32 kObjectLoopCount = 4;
constexpr u32 kSharedSlotA = 0xFAC;      // primary shared resource
constexpr u32 kSharedSlotB = 0xFB8;      // secondary shared resource
constexpr u32 kSubObjectLoopBaseA = 0xD10; // 6 sub-object pointers
constexpr u32 kSubObjectLoopBaseB = 0xD28; // 6 paired sub-object pointers
constexpr u32 kSubObjectLoopCount = 6;

inline void*& pointer_at(u8* ctx, u32 offset) {
    return *reinterpret_cast<void**>(ctx + offset);
}

}  // namespace script_vm_2a72fc

extern "C" __attribute__((noinline)) u32 script_vm_func_002a72fc(u8* ctx) {
    using namespace script_vm_2a72fc;

    ui_func_002a7bd4(ctx);

    for (u32 i = 0; i < kObjectLoopCount; ++i) {
        void*& slot = pointer_at(ctx, kObjectLoopBase + 4 * i);
        if (slot != nullptr) {
            script_vm_func_002a7b50(slot);
            slot = nullptr;
        }
    }

    script_vm_func_002aeb2c(0x31, 0);
    engine_func_002aea7c(0x31);

    func_002a4974(ctx + 0x20);
    func_0014c968(ctx + 0x20);
    func_0014c970(ctx + 0x20);

    // 0xFAC: destroy the primary shared resource, then run the secondary
    // cleanup only if the first helper left the slot populated. The original
    // reloads the slot between the two calls, so mirror that here.
    {
        void*& slot = pointer_at(ctx, kSharedSlotA);
        if (slot != nullptr) {
            engine_func_002a4ef0(slot);
            if (slot != nullptr) {
                engine_func_002b2520(slot);
            }
            slot = nullptr;
        }
    }

    // 0xFB8: the second helper receives the reloaded slot value, and the
    // global 0x2A7604(0) notification is only sent when the slot was
    // initially populated.
    {
        void*& slot = pointer_at(ctx, kSharedSlotB);
        if (slot != nullptr) {
            script_vm_func_00152af8(slot);
            script_vm_func_002a7aa0(pointer_at(ctx, kSharedSlotB));
            slot = nullptr;
            script_vm_func_002a7604(0);
        }
    }

    // Both six-entry sub-object arrays are drained unconditionally: the
    // original loop has no null test and passes whatever the slot holds
    // (including null) to both helpers before clearing it.
    for (u32 i = 0; i < kSubObjectLoopCount; ++i) {
        const u32 offset_a = kSubObjectLoopBaseA + 4 * i;
        const u32 offset_b = kSubObjectLoopBaseB + 4 * i;

        script_vm_func_00152af8(pointer_at(ctx, offset_a));
        script_vm_func_002a7aa0(pointer_at(ctx, offset_a));
        pointer_at(ctx, offset_a) = nullptr;

        script_vm_func_00152af8(pointer_at(ctx, offset_b));
        script_vm_func_002a7aa0(pointer_at(ctx, offset_b));
        pointer_at(ctx, offset_b) = nullptr;
    }

    // Nine individually typed object slots. Both the order and the helper
    // selected for each slot are part of the teardown contract.
    {
        void*& slot = pointer_at(ctx, 0x5A8);
        if (slot != nullptr) {
            script_vm_func_002a755c(slot);
            slot = nullptr;
        }
    }
    {
        void*& slot = pointer_at(ctx, 0x5A0);
        if (slot != nullptr) {
            engine_func_002c4360(slot);
            slot = nullptr;
        }
    }
    {
        void*& slot = pointer_at(ctx, 0x5A4);
        if (slot != nullptr) {
            engine_func_002c4360(slot);
            slot = nullptr;
        }
    }
    {
        void*& slot = pointer_at(ctx, 0x5B4);
        if (slot != nullptr) {
            script_vm_func_002a755c(slot);
            slot = nullptr;
        }
    }
    {
        void*& slot = pointer_at(ctx, 0x5AC);
        if (slot != nullptr) {
            engine_func_002c4360(slot);
            slot = nullptr;
        }
    }
    {
        void*& slot = pointer_at(ctx, 0x5B0);
        if (slot != nullptr) {
            engine_func_002c4360(slot);
            slot = nullptr;
        }
    }
    {
        void*& slot = pointer_at(ctx, 0x5C0);
        if (slot != nullptr) {
            script_vm_func_002a755c(slot);
            slot = nullptr;
        }
    }
    {
        void*& slot = pointer_at(ctx, 0x5B8);
        if (slot != nullptr) {
            engine_func_002c4360(slot);
            slot = nullptr;
        }
    }
    {
        void*& slot = pointer_at(ctx, 0x5BC);
        if (slot != nullptr) {
            engine_func_002c4360(slot);
            slot = nullptr;
        }
    }

    script_vm_func_002c0128();

    // The original tail-calls 0x2A7540(1) from its epilogue (the function is
    // laid out immediately after this body, so the epilogue falls through
    // into it) and then returns with r0 still 1.
    ui_func_002a7540(1);
    return 1;
}

// DECOMP_FUNC(0x002a1578, 584)
extern "C" u32 engine_func_002a1578(const u32* p_val) {
    if (p_val == nullptr) {
        return 0;
    }
    u32 val = *p_val;
    if (val == 0) {
        return 0;
    }

    u32 category = (val >> 10) & 0xFF;

    if (category == 0x11) {
        u32 sub_id = val & 0x3FF;
        if (sub_id >= 0x104 && sub_id < 0x118) {
            return 0xC8A13909;
        }
        return 0xC9413915;
    }

    if (category == 0x20) {
        if (val == 0xC8A08035) {
            return 0xC8613916;
        }
        return val;
    }

    if (category == 0x34) {
        switch (val) {
        case 0xC920D095: return 0xC941390D;
        case 0xC920D073: return 0xC941390A;
        case 0xC860D069: return 0xC8613914;
        case 0xC860D06E: return 0xC8613913;
        case 0xC900D075: return 0xC8A13905;
        case 0xC920D086: return 0xC941390C;
        case 0xC920D08C: return 0xC941390E;
        case 0xC920D08F: return 0xC941390B;
        case 0xE0A0D0A9: return 0xC94138C2;
        case 0xC920D0A4: return 0xC941390F;
        case 0xC920D0A7: return 0xC9413910;
        case 0xC920D0A8: return 0xC9413940;
        case 0xE0C0D066: return 0xE0C13897;
        case 0xE0E0D068: return 0xE0E1388F;
        case 0xC8A0D018: return 0xC9413917;
        case 0xD860D020: return 0xD861388E;
        case 0xD860D024: return 0xD861389A;
        case 0xD880D023: return 0xD8813896;
        default: break;
        }
        return val;
    }

    return val;
}

// DECOMP_FUNC(0x003aa014, 592)
//
// Battle-screen value text. Looks up the screen anchor in the battle layout
// table, notifies the three per-id draw helpers, formats one record value as
// "%4d" and emits a positioned draw call; then repeats with a second record
// field and a second label. `flag` selects the alternate (selected/detail)
// layout, label set and coordinate set. The 0xFBEB39FF / 0x6BBB2CFF words are
// forwarded to the draw helper unchanged; their meaning is not established.
namespace battle_aa014 {

constexpr u32 kFrameCountOffset = 0x594;   // u32 counter bumped for flag != 0
constexpr u32 kLayoutBaseOffset = 0xC8;    // battle layout table base
constexpr u32 kModeByteOffset = 0x56D;     // s8 mode selector for 0x22D994

constexpr u32 kLayoutPlain = 0x40E;        // layout record key, flag == 0
constexpr u32 kLayoutSelected = 0x42F;     // layout record key, flag != 0

constexpr u32 kAnchorXOffset = 8;          // s16 x inside a layout record
constexpr u32 kAnchorYOffset = 0xA;        // s16 y inside a layout record

constexpr u16 kLabelIdPlainFirst = 0x48F;
constexpr u16 kLabelIdSelectedFirst = 0x49D;
constexpr u16 kLabelIdPlainSecond = 0x493;
constexpr u16 kLabelIdSelectedSecond = 0x4A1;

constexpr u32 kRecordFlagByteOffset = 2;   // u8 forwarded to 0x22DB5C
constexpr u32 kRecordFirstWordOffset = 4;  // u32 for the first label
constexpr u32 kRecordSecondWordOffset = 8; // u32 for the second label

constexpr u32 kOpaqueFirst = 0xFBEB39FF;   // forwarded draw argument
constexpr u32 kOpaqueSecond = 0x6BBB2CFF;  // forwarded draw argument
constexpr u32 kOpaqueEmpty = 0xFFFFFFFF;   // flag == 0 substitution

constexpr int kTextSize = 0x2C;            // formatted label scratch buffer

}  // namespace battle_aa014

extern "C" u8* camp_func_002bf6c8(void* table, u32 key);
extern "C" void ui_func_0022d994(void* ctx, void* work, u32 frame, int mode);
extern "C" void camp_func_0022de40(void* ctx, int mode, int id, void* work,
                                   int flag, u32 frame);
extern "C" void script_vm_func_0022dd28(void* ctx, int id, void* work, int flag,
                                        u32 frame);
extern "C" void script_vm_func_0022dc40(void* ctx, int id, void* work, int flag,
                                        u32 frame);
extern "C" u8* battle_func_002b087c(u32 id);
extern "C" void ui_func_0022db5c(void* ctx, int value, void* work, int flag,
                                 u32 frame, int unused);
extern "C" void func_00230c80(void* gfx, int mode, int x, int y, int arg0,
                              int arg1, u32 constant, u32 frame,
                              const char* text);

extern "C" void battle_func_003aa014(void* ctx, void* work, int flag, int id) {
    using namespace battle_aa014;

    u8* const ctx_bytes = static_cast<u8*>(ctx);
    u8* const work_bytes = static_cast<u8*>(work);
    const bool selected = flag != 0;

    const u32 frame =
        *reinterpret_cast<const u32*>(ctx_bytes + kFrameCountOffset) +
        (selected ? 1u : 0u);

    const u8* const layout = camp_func_002bf6c8(
        ctx_bytes + kLayoutBaseOffset,
        reinterpret_cast<u32>(
            work_bytes + (selected ? kLayoutSelected : kLayoutPlain)));
    const s32 base_x =
        *reinterpret_cast<const s16*>(layout + kAnchorXOffset);
    const s32 base_y =
        *reinterpret_cast<const s16*>(layout + kAnchorYOffset);

    if (selected) {
        ui_func_0022d994(
            ctx, work, frame,
            *reinterpret_cast<const s8*>(ctx_bytes + kModeByteOffset));
    }

    camp_func_0022de40(ctx, 1, id, work, flag, frame);
    script_vm_func_0022dd28(ctx, id, work, flag, frame);
    script_vm_func_0022dc40(ctx, id, work, flag, frame);

    const u32 record_id = static_cast<u32>(id) & 0xFFFFu;
    const u8* record = battle_func_002b087c(record_id);
    const int record_flag =
        record != nullptr ? record[kRecordFlagByteOffset] : 0;
    ui_func_0022db5c(ctx, record_flag, work, flag, frame, -1);

    record = battle_func_002b087c(record_id);
    const u32 first_value =
        record != nullptr
            ? *reinterpret_cast<const u32*>(record + kRecordFirstWordOffset)
            : 0;

    const u8* const first_label = camp_func_002bf6c8(
        ctx_bytes + kLayoutBaseOffset,
        selected ? kLabelIdSelectedFirst : kLabelIdPlainFirst);
    const s32 first_x =
        base_x + *reinterpret_cast<const s16*>(first_label + kAnchorXOffset);
    const s32 first_y =
        base_y + *reinterpret_cast<const s16*>(first_label + kAnchorYOffset);

    char text[kTextSize];
    ui_func_002be7fc(text, "%4d", first_value);
    func_00230c80(ctx_bytes + kLayoutBaseOffset, 0, first_x, first_y, 0, 7,
                  selected ? kOpaqueFirst : kOpaqueEmpty, frame, text);

    record = battle_func_002b087c(record_id);
    const u32 second_value =
        record != nullptr
            ? *reinterpret_cast<const u32*>(record + kRecordSecondWordOffset)
            : 0;

    const u8* const second_label = camp_func_002bf6c8(
        ctx_bytes + kLayoutBaseOffset,
        static_cast<u32>(selected ? kLabelIdSelectedSecond
                                  : kLabelIdPlainSecond));
    const s32 second_x =
        base_x + *reinterpret_cast<const s16*>(second_label + kAnchorXOffset);
    const s32 second_y =
        base_y + *reinterpret_cast<const s16*>(second_label + kAnchorYOffset);

    ui_func_002be7fc(text, "%4d", second_value);
    func_00230c80(ctx_bytes + kLayoutBaseOffset, 0, second_x, second_y, 0, 7,
                  selected ? kOpaqueSecond : kOpaqueEmpty, frame, text);
}

// DECOMP_FUNC(0x002d7f0c, 596)
extern "C" u32 ui_func_002c5f7c(u32 mode, u32 sub_mode);
extern "C" u32 ui_func_002c5218();
extern "C" void func_00288310(void* gpu_state);
extern "C" void ui_func_002c5188(void* gpu_state, u32 val);
extern "C" void func_0024a9d4(u32 mode, u32 flag);
extern "C" void func_0024c564(u32 val);
extern "C" void engine_func_00281adc(u32 val);
extern "C" void ui_func_002c1abc(void* gpu_state);
extern "C" void ui_func_002c1b64(void* gpu_state);

struct UiRenderStack {
    u32 depth;
    u32 unk_04;
    u32 entries[5];
    u8 callback_flag;
    u8 pad[3];
    void (*callback)();
};

static inline void UiRenderStack_Push(UiRenderStack* stack, u32 new_val) {
    u32 depth = stack->depth;
    u32 prev_val = stack->entries[depth];
    u32 new_depth = depth + 1;
    stack->depth = new_depth;
    stack->entries[new_depth] = new_val;
    if (stack->callback_flag != 0 || prev_val != new_val) {
        if (stack->callback) {
            stack->callback();
        }
        stack->callback_flag = 0;
    }
}

static inline void UiRenderStack_Pop(UiRenderStack* stack) {
    u32 depth = stack->depth;
    u32 prev_val = stack->entries[depth];
    u32 new_depth = depth - 1;
    stack->depth = new_depth;
    u32 new_val = stack->entries[new_depth];
    if (stack->callback_flag != 0 || prev_val != new_val) {
        if (stack->callback) {
            stack->callback();
        }
        stack->callback_flag = 0;
    }
}

static inline void UiRenderContext_RunTransition(u32 mode) {
    u8* gpu_state = *reinterpret_cast<u8**>(0x0044ea00);
    auto* stack0 = reinterpret_cast<UiRenderStack*>(gpu_state + 0x11ec);
    auto* stack1 = reinterpret_cast<UiRenderStack*>(gpu_state + 0x124c);
    auto* stack2 = reinterpret_cast<UiRenderStack*>(gpu_state + 0x12ac);

    UiRenderStack_Push(stack0, 0);
    UiRenderStack_Push(stack1, ui_func_002c5f7c(1, 0));
    UiRenderStack_Push(stack2, stack2->entries[stack2->depth]);

    u8* state_obj = reinterpret_cast<u8*>(0x0044ea80);
    if (*state_obj != 0) {
        func_00288310(gpu_state);
    } else {
        ui_func_002c5188(gpu_state, ui_func_002c5218());
    }

    func_0024a9d4(mode, 1);

    u32 val_20 = *reinterpret_cast<u32*>(state_obj + 0x20);
    if (val_20 != 0) {
        func_0024c564(val_20);
    }

    u32 val_10 = *reinterpret_cast<u32*>(state_obj + 0x10);
    if (val_10 != 0) {
        engine_func_00281adc(val_10);
    }

    u32 val_2c = *reinterpret_cast<u32*>(state_obj + 0x2c);
    if (val_2c != 0) {
        func_0024c564(val_2c);
    }

    ui_func_002c1abc(gpu_state);
    ui_func_002c1b64(gpu_state);

    UiRenderStack_Pop(stack0);
    UiRenderStack_Pop(stack1);
    UiRenderStack_Pop(stack2);
}

extern "C" void ui_func_002d7f0c() {
    UiRenderContext_RunTransition(1);
}

// DECOMP_FUNC(0x002e1b90, 596)
extern "C" void ui_func_002e1b90() {
    UiRenderContext_RunTransition(2);
}

// DECOMP_FUNC(0x0037aac4, 596)
//
// UI resource pass for a virtual UI object. The primary id (key) is resolved
// once into key_handle, then four pending {id, handle} entries are walked:
// every entry whose cached handle is zero is requested from the resource owner
// (0x2AF648) and resolved (0x235E08); every live entry is bound into a local
// four-element result array (0x37C034) and, when binding reports -1 or 2,
// committed (0x37B82C) and bound once more against a different owner pointer.
// The object's callback receives command 0 (failure) on any request/commit
// failure and command 1 (success) with the key, the raw entry ids, the bound
// array and the per-entry flags when the pass completes. No-callback exits
// only restore the callee-saved registers; the value the original leaves in r0
// there is a leftover of the last helper call (unspecified).
//
// `owner` payload starts at +0xC and is dereferenced unconditionally; `extra`
// is optional and is null-checked before the +0xC adjustment.
namespace ui_aa_c4 {

// 8-byte pending-entry record (array stride 8).
struct Entry {
    s32 id;      // +0x00: resource id; -1 means "unused"
    u32 handle;  // +0x04: resolved handle; 0 means "not resolved yet"
};

// Callback commands observed in the original.
constexpr u32 kCommandError = 0;
constexpr u32 kCommandSuccess = 1;

// Callback arguments: command, pointer to the primary key, pointer to the
// object's raw Entry array (ids with stride 8), pointer to the local bound
// array, pointer to the local per-entry flag bytes, callback context.
using Callback = u32 (*)(u32 command, const u32* key, const Entry* ids,
                         const Entry* bound, const u8* flags, u32 context);

// Virtual UI object; only the region touched by this routine is described.
struct Object {
    u8 pad_00[0x1C];
    void* owner;         // +0x1C: resource owner; its payload starts at +0xC
    u32 owner_param;     // +0x20: forwarded to every owner call
    Callback callback;   // +0x24: null = no callback
    u32 callback_ctx;    // +0x28: last callback argument
    void* extra;         // +0x2C: optional secondary owner
    u32 aux;             // +0x30: forwarded to 0x37C034
    u32 key;             // +0x34: primary resource id; -1 means "unused"
    u32 key_handle;      // +0x38: resolved primary handle; 0 = unresolved
    Entry entries[4];    // +0x3C: pending entries (id at +0x3C+8*i)
};
static_assert(sizeof(Object) == 0x5C);

constexpr u32 kOwnerPayloadOffset = 0xC;
constexpr u32 kModePrimary = 1;  // 0x2AF648 mode for the primary key
constexpr u32 kModeEntry = 4;    // 0x2AF648 mode for a pending entry
constexpr u32 kEntryCount = 4;
constexpr u32 kNoId = 0xFFFFFFFFu;

// The original adds 0xC to the owner pointer without a null check
// (`ldm r0, {r0, r2}; add r0, r0, #0xc`).
static void* owner_payload(void* owner) {
    return reinterpret_cast<void*>(
        reinterpret_cast<uintptr_t>(owner) + kOwnerPayloadOffset);
}

// The bind argument is the only owner pointer that the original null-checks
// (`cmp r0, #0; addne r0, r0, #0xc`).
static void* optional_owner_payload(void* owner) {
    return owner != nullptr ? owner_payload(owner) : nullptr;
}

}  // namespace ui_aa_c4

extern "C" u32 engine_func_002af648(void* owner, u32 id, u32 param, u32 mode,
                                     u32 flags);
extern "C" u32 engine_func_00235e08(void* owner, u32 id);
extern "C" s32 engine_func_0037c034(ui_aa_c4::Entry* entry, u8* flag,
                                     u32 handle, u32 aux, void* extra);
extern "C" u32 engine_func_0037b82c(void* owner, u32 handle, u32 param);
// Fills `count` records of `stride` bytes by calling `init` with each record.
extern "C" void ui_func_002c5f58(ui_aa_c4::Entry* entries,
                                  void (*init)(ui_aa_c4::Entry*), u32 stride,
                                  u32 count);
// Writes {-1, 0} into the 8-byte record (ROM routine at 0x0014C158).
extern "C" void func_0014c158(ui_aa_c4::Entry* entry);

extern "C" void ui_func_0037aac4(void* self) {
    using namespace ui_aa_c4;

    Object* const obj = static_cast<Object*>(self);

    if (obj->key_handle == 0) {
        const u32 key = obj->key;  // cached across the whole block
        if (key != kNoId) {
            if (engine_func_002af648(owner_payload(obj->owner), key,
                                     obj->owner_param, kModePrimary, 0) == 0) {
                if (obj->callback != nullptr) {
                    obj->callback(kCommandError, nullptr, nullptr, nullptr,
                                  nullptr, obj->callback_ctx);
                    return;
                }
            }
            obj->key_handle =
                engine_func_00235e08(owner_payload(obj->owner), key);
        }
    }

    Entry bound[kEntryCount];
    ui_func_002c5f58(bound, func_0014c158, sizeof(Entry), kEntryCount);

    u8 flags[kEntryCount] = {0, 0, 0, 0};

    for (u32 i = 0; i < kEntryCount; ++i) {
        Entry* const entry = &bound[i];

        if (obj->entries[i].handle == 0) {
            const u32 id = obj->entries[i].id;  // cached across the request
            if (id == kNoId) {
                continue;
            }
            if (engine_func_002af648(owner_payload(obj->owner), id,
                                     obj->owner_param, kModeEntry, 0) == 0) {
                if (obj->callback != nullptr) {
                    obj->callback(kCommandError, nullptr, nullptr, nullptr,
                                  nullptr, obj->callback_ctx);
                    return;
                }
            }
            obj->entries[i].handle =
                engine_func_00235e08(owner_payload(obj->owner), id);
        }

        // The original re-reads the id here, after the request/resolve calls.
        if (obj->entries[i].id == kNoId) {
            continue;
        }

        s32 result = engine_func_0037c034(entry, &flags[i],
                                          obj->entries[i].handle, obj->aux,
                                          optional_owner_payload(obj->extra));
        if (result == -1 || result == 2) {
            if (engine_func_0037b82c(owner_payload(obj->owner),
                                     obj->entries[i].handle,
                                     obj->owner_param) == 0) {
                if (obj->callback != nullptr) {
                    obj->callback(kCommandError, nullptr, nullptr, nullptr,
                                  nullptr, obj->callback_ctx);
                }
                return;
            }
            // Retry bind, this time with the owner pointer as the extra
            // argument. The result is discarded.
            engine_func_0037c034(entry, &flags[i], obj->entries[i].handle,
                                 obj->aux, optional_owner_payload(obj->owner));
        }
    }

    if (obj->callback != nullptr) {
        obj->callback(kCommandSuccess, &obj->key, obj->entries, bound, flags,
                      obj->callback_ctx);
    }
}

// DECOMP_FUNC(0x001325d8, 600)
//
// Engine frame/render synchronisation. The routine first runs a one-time
// registration sequence for the global render registries, then calls the
// engine readiness probe, optionally dumps the pending command words as
// "0x%08x," (four per row) and finally releases the per-frame render state.
// `state` (r1) is forwarded verbatim to 0x2ABBB8; `reserved` (r2) is never
// read.  The 4th argument (r3) enables the command-word dump.
namespace engine_1325d8 {

// Static guard/state block at 0x004DAD80 (`r7` in the original).
constexpr u32 kStateAddr = 0x004DAD80;
constexpr u32 kStateActiveByte = 0x04;    // u8: subsystem registered
constexpr u32 kStateInitedByte = 0x05;    // u8: one-time init completed
constexpr u32 kStateLockHandle = 0x08;    // handle of 0x2C50D0/0x2C52F0/0x2C5094
constexpr u32 kStateRenderHandle = 0x10;  // handle of 0x2ABB68/0x138BB8/0x2ABB50

// Global registries reached through the 0x00464Bxx pointer table.
constexpr u32 kRegistryAAddr = 0x00464B84;  // object whose first word is a vtable
constexpr u32 kRegistryBAddr = 0x00464B8C;  // token for 0x2ABE74 / 0x2C028C
constexpr u32 kRegistryCAddr = 0x00464B7C;  // object with words at +4 and +8
constexpr u32 kRegistryDAddr = 0x00464B94;  // second initialisation token
constexpr u32 kRegistryVtableOffset = 0x10; // indirect-call slot
constexpr u32 kRegistryValueOffset = 0x08;  // word exchanged with 0x2ABDF4
constexpr u32 kRegistryOwnerOffset = 0x04;  // word read by 0x2ABDF4
constexpr u32 kRegistryArgOffset = 0x10;    // bias applied to registry A

// Command-word cursor walked by the optional dump loop.
constexpr u32 kCommandCursorAddr = 0x004652A0;  // u32 current cursor
constexpr u32 kCommandWordStride = 4;

// Dump formatting bounds.
constexpr u32 kDumpColumnLimit = 0x100;  // capacity argument / column base
constexpr u32 kDumpFieldLimit = 0xFF;    // second bound argument
constexpr u32 kDumpRowWidth = 4;         // entries per row before the reset
constexpr u32 kScratchBytes = 0x108;      // scratch at sp+8 in the original

// Object layout: object+0x14 points at the two-word 0x2ABC9C range.
constexpr u32 kObjContextOffset = 0x04;   // u32 forwarded as the dump context
constexpr u32 kObjSourceOffset = 0x14;    // u32 pointer to the range source
constexpr u32 kObjExtraOffset = 0x18;     // u32 fifth 0x2ABC9C argument
constexpr u32 kSourceBeginOffset = 0x0C;  // u32 first range word
constexpr u32 kSourceEndOffset = 0x10;    // u32 second range word

}  // namespace engine_1325d8

extern "C" void engine_func_002abe74(void* object, u32 token);
extern "C" void engine_func_002abdf4(void* object, u32 value);
extern "C" void func_002abde8(void* object);
extern "C" void engine_func_002c50d0(void* handle);
extern "C" void func_002abc9c(void* dst, u32 first, u32 second, u32 context,
                              u32 extra);
extern "C" void engine_func_002c52f0(void* handle, u32 flag);
extern "C" void engine_func_002c028c(void* registry, u32 token);
extern "C" s32 func_001384f8(void);
extern "C" void battle_func_002abb68(void* handle);
extern "C" s32 engine_func_0013c030(char* dst, u32 size, u32 field,
                                    const char* format, u32 value);
extern "C" void func_00138bb8(void* handle);
extern "C" void func_002abbb8(void* object, u32 value, u32 flag);
extern "C" void battle_func_002c5094(void* handle);
extern "C" void func_002b77b8(void* object);
extern "C" void func_002abb50(void* block);

namespace engine_1325d8 {

// 0x132634 / 0x1326B8: indirect call through the registry vtable slot 0x10.
static __attribute__((always_inline)) inline void
call_registry_callback(void* registry, u32 value) {
    u8* const vtable = *reinterpret_cast<u8**>(registry);
    using Callback = void (*)(void* self, u32 argument);
    const Callback callback =
        *reinterpret_cast<const Callback*>(vtable + kRegistryVtableOffset);
    callback(registry, value);
}

// 0x132658 / 0x13270C / 0x132790: build the range scratch object.
static __attribute__((always_inline)) inline void
build_scratch(void* dst, const void* object, u32 context) {
    const u8* const bytes = static_cast<const u8*>(object);
    const u8* const source =
        *reinterpret_cast<const u8* const*>(bytes + kObjSourceOffset);
    func_002abc9c(dst,
                  *reinterpret_cast<const u32*>(source + kSourceBeginOffset),
                  *reinterpret_cast<const u32*>(source + kSourceEndOffset),
                  context,
                  *reinterpret_cast<const u32*>(bytes + kObjExtraOffset));
}

// 0x132604..0x1326D8: one-time registration of the render registries.  Each
// registry pointer is re-read after every call because the originals do.
static __attribute__((always_inline)) inline void
register_render_registries(const void* object, u32 context, void* scratch) {
    engine_func_002abe74(
        reinterpret_cast<u8*>(*reinterpret_cast<u32*>(kRegistryAAddr)) +
            kRegistryArgOffset,
        *reinterpret_cast<const u32*>(kRegistryBAddr));

    u8* const registry_c = *reinterpret_cast<u8**>(kRegistryCAddr);
    u8* const registry_a = *reinterpret_cast<u8**>(kRegistryAAddr);
    engine_func_002abdf4(
        *reinterpret_cast<void**>(registry_c + kRegistryValueOffset),
        *reinterpret_cast<const u32*>(registry_c + kRegistryOwnerOffset));
    call_registry_callback(
        registry_a,
        *reinterpret_cast<const u32*>(registry_c + kRegistryValueOffset));
    func_002abde8(
        *reinterpret_cast<void**>(registry_c + kRegistryValueOffset));

    engine_func_002c50d0(
        *reinterpret_cast<void**>(kStateAddr + kStateLockHandle));

    build_scratch(scratch, object, context);

    engine_func_002c52f0(
        *reinterpret_cast<void**>(kStateAddr + kStateLockHandle), 0);
    engine_func_002c028c(*reinterpret_cast<void**>(kRegistryAAddr),
                         *reinterpret_cast<const u32*>(kRegistryBAddr));

    engine_func_002abe74(
        reinterpret_cast<u8*>(*reinterpret_cast<u32*>(kRegistryAAddr)) +
            kRegistryArgOffset,
        *reinterpret_cast<const u32*>(kRegistryDAddr));

    u8* const registry_c2 = *reinterpret_cast<u8**>(kRegistryCAddr);
    u8* const registry_a2 = *reinterpret_cast<u8**>(kRegistryAAddr);
    engine_func_002abdf4(
        *reinterpret_cast<void**>(registry_c2 + kRegistryValueOffset),
        *reinterpret_cast<const u32*>(registry_c2 + kRegistryOwnerOffset));
    call_registry_callback(
        registry_a2,
        *reinterpret_cast<const u32*>(registry_c2 + kRegistryValueOffset));
    func_002abde8(
        *reinterpret_cast<void**>(registry_c2 + kRegistryValueOffset));
}

}  // namespace engine_1325d8

extern "C" void engine_func_001325d8(void* obj, u32 state, u32 reserved,
                                     u32 dump_commands) {
    using namespace engine_1325d8;

    const u8* const object = static_cast<const u8*>(obj);
    u8* const static_state = reinterpret_cast<u8*>(kStateAddr);
    const u32 context =
        *reinterpret_cast<const u32*>(object + kObjContextOffset);
    u8 scratch[kScratchBytes];

    if (static_state[kStateActiveByte] != 0 &&
        static_state[kStateInitedByte] == 0) {
        register_render_registries(object, context, scratch);
        static_state[kStateInitedByte] = 1;
    }

    if (func_001384f8() == 0) {
        battle_func_002abb68(
            *reinterpret_cast<void**>(kStateAddr + kStateRenderHandle));
    }

    if (dump_commands != 0) {
        // The cursor is snapshotted before the construction call and re-read
        // afterwards; the loop only runs when the call advanced it.
        u32 cursor = *reinterpret_cast<const u32*>(kCommandCursorAddr);
        build_scratch(scratch, object, context);

        u32 end = 0;
        if (cursor != 0) {
            end = *reinterpret_cast<const u32*>(kCommandCursorAddr);
        }

        if (cursor != 0 && end != 0 && cursor < end) {
            u32 column = 0;
            u32 row = 0;
            while (cursor < end) {
                const u32 word = *reinterpret_cast<const u32*>(cursor);
                const s32 written = engine_func_0013c030(
                    reinterpret_cast<char*>(scratch) + column,
                    kDumpColumnLimit - column, kDumpFieldLimit - column,
                    "0x%08x,", word);
                ++row;
                column += static_cast<u32>(written);
                if (row == kDumpRowWidth) {
                    column = 0;
                    row = 0;
                }
                cursor += kCommandWordStride;
            }
        }
    } else {
        build_scratch(scratch, object, context);
    }

    func_00138bb8(*reinterpret_cast<void**>(kStateAddr + kStateRenderHandle));

    if (static_state[kStateActiveByte] != 0 &&
        static_state[kStateInitedByte] != 0) {
        func_002abbb8(reinterpret_cast<void*>(context), state, 1);
        battle_func_002c5094(
            *reinterpret_cast<void**>(kStateAddr + kStateLockHandle));
        func_002b77b8(reinterpret_cast<void*>(context));
    }

    func_002abbb8(reinterpret_cast<void*>(context), state, 1);
    func_002abb50(*reinterpret_cast<void**>(kStateAddr + kStateRenderHandle));
}

// Helpers called by engine_func_0037fd94.  Declarations are kept next to the
// reconstruction so the recovered argument widths and order stay explicit.
extern "C" u32 func_002a21b8(u32 value, u32 layout_mode);           // 0x002a21b8
extern "C" void engine_func_002c5ff4(void* dst, const void* src, u32 size);  // memcpy
extern "C" void func_0037c36c(u16* anchor, const void* layout, u32 count,
                              u32 base);                            // 0x0037c36c
extern "C" void func_0015d14c(u32* slot_list, s32 index,
                              const void* entry);                   // 0x0015d14c
extern "C" void engine_func_002bd448(void* entry);                  // 0x002bd448
extern "C" void func_0015d91c(u32* slot_list, s32 index, void* entry,
                              u32 bind);                            // 0x0015d91c

namespace engine_37fd94 {

// Byte offsets recovered from the ARM body.  `self` is the receiver; `desc`
// points at a header whose first 0x30 bytes also form descriptor 0.  Later
// descriptors are at desc + 0x30 * index, so the +0x3E/+0x40/+0x42 tail reads
// intentionally reach into the bytes that follow the 0x30-byte descriptor.
constexpr u32 kSelfFlagByte = 0x7C;
constexpr u32 kSelfWord = 0x78;
constexpr u32 kSelfSlotList = 0x134;
constexpr u32 kSelfAnchorArray = 0x60;
constexpr u32 kSelfTailArray = 0x6C;

constexpr u32 kDescriptorStride = 0x30;
constexpr u32 kDescModeByte = 0x00;
constexpr u32 kDescFlagByte = 0x01;
constexpr u32 kDescWord = 0x0C;
constexpr u32 kDescSpanWord = 0x10;
constexpr u32 kDescBaseWord = 0x14;
constexpr u32 kDescLayout = 0x18;
constexpr u32 kDescTail = 0x3E;
constexpr u32 kLayoutBytes = 0x20;

constexpr u32 kSlotCountOffset = 0x08;
constexpr u32 kEntryStride = 0x30;
constexpr u32 kEntrySecond = 0x18;
constexpr u32 kEntryWord0 = 0x00;
constexpr u32 kEntryWord1 = 0x04;
constexpr u32 kEntryAnchor = 0x08;
constexpr u32 kEntryFlag = 0x10;

// The original rounds a non-zero span down to a multiple of 14 by multiplying
// with 0x49249249 and keeping bits [63:34].
constexpr u64 kSpanDivisorMagic = 0x49249249ull;
constexpr u32 kSpanDivisorShift = 34;
constexpr u32 kSpanGranule = 14;

static __attribute__((always_inline)) inline u16 load_u16(const void* p) {
    u16 value;
    __builtin_memcpy(&value, p, sizeof(value));
    return value;
}

static __attribute__((always_inline)) inline void store_u16(void* p, u16 value) {
    __builtin_memcpy(p, &value, sizeof(value));
}

static __attribute__((always_inline)) inline u32 load_u32(const void* p) {
    u32 value;
    __builtin_memcpy(&value, p, sizeof(value));
    return value;
}

static __attribute__((always_inline)) inline void store_u32(void* p, u32 value) {
    __builtin_memcpy(p, &value, sizeof(value));
}

}  // namespace engine_37fd94

// Rebuilds the two 0x30-byte layout records for every descriptor entry.  The
// original returns the loop bound in r0 on both the early and normal exits.
// When descriptor byte 0 is not 3, the layout buffer handed to 0x0015D14C was
// never initialised by the original either; its contents are not part of the
// recovered contract.
extern "C" u32 engine_func_0037fd94(u8* self, const u8* desc, u32 span) {
    using namespace engine_37fd94;

    self[kSelfFlagByte] = desc[kDescFlagByte];
    store_u32(self + kSelfWord, load_u32(desc + kDescWord));

    if (span != 0 && desc[kDescModeByte] == 3) {
        const u64 product =
            (static_cast<u64>(span) + 1) * kSpanDivisorMagic;
        span = kSpanGranule *
               static_cast<u32>(product >> kSpanDivisorShift);
    }

    const u32 primary =
        func_002a21b8(load_u32(desc + kDescWord), desc[kDescModeByte]);
    // The original also evaluates the span word through the same scaler, but
    // discards the result; the call itself remains observable.
    (void)func_002a21b8(load_u32(desc + kDescSpanWord), desc[kDescModeByte]);

    u8* const slot_list =
        reinterpret_cast<u8*>(load_u32(self + kSelfSlotList));
    const s32 count = static_cast<s32>(load_u32(slot_list + kSlotCountOffset));
    if (count <= 0) {
        return static_cast<u32>(count);
    }

    u8 layout[kLayoutBytes];

    for (s32 index = 0; index < count; ++index) {
        const u32 scaled_index = static_cast<u32>(index) * 3u;  // index * 0x30
        const u8* const desc_entry = desc + scaled_index * 16u;
        const u32 base = load_u32(desc_entry + kDescBaseWord);

        const u8* primary_bytes = reinterpret_cast<const u8*>(base);
        if (span != 0) {
            primary_bytes = reinterpret_cast<const u8*>(
                base + func_002a21b8(span, desc[kDescModeByte]));
        }

        const u8 layout_mode = desc[kDescModeByte];
        u8* const anchor = self + scaled_index * 2u + kSelfAnchorArray;
        u8* const tail = self + scaled_index * 2u + kSelfTailArray;

        if (layout_mode == 3) {
            const u8* const layout_src = desc_entry + kDescLayout;
            engine_func_002c5ff4(layout, layout_src, kLayoutBytes);
            if (span == 0) {
                store_u16(anchor + 0, load_u16(layout_src + 0x20));
                store_u16(anchor + 2, load_u16(layout_src + 0x22));
                store_u16(anchor + 4, load_u16(layout_src + 0x24));
            } else {
                store_u16(anchor + 0, load_u16(primary_bytes));
                store_u16(anchor + 2, load_u16(layout_src + 0x22));
                store_u16(anchor + 4, load_u16(layout_src + 0x24));
                func_0037c36c(reinterpret_cast<u16*>(anchor), layout, span,
                              base);
            }

            if (desc[kDescFlagByte] != 0) {
                store_u16(tail + 0, load_u16(desc_entry + kDescTail + 0x00));
                store_u16(tail + 2, load_u16(desc_entry + kDescTail + 0x02));
                store_u16(tail + 4, load_u16(desc_entry + kDescTail + 0x04));
            }

            func_0015d14c(
                reinterpret_cast<u32*>(load_u32(self + kSelfSlotList)), index,
                layout);
        }

        u8* const entry = self + scaled_index * 16u;
        u8* const entry_second = entry + kEntrySecond;

        engine_func_002bd448(entry);
        store_u32(entry + kEntryWord0, reinterpret_cast<u32>(primary_bytes));
        store_u32(entry + kEntryWord1,
                  load_u32(desc + kDescSpanWord) - span);
        entry[kEntryFlag] = 0;
        if (desc[kDescModeByte] == 3) {
            store_u32(entry + kEntryAnchor, reinterpret_cast<u32>(anchor));
        }
        func_0015d91c(
            reinterpret_cast<u32*>(load_u32(self + kSelfSlotList)), index,
            entry, desc[kDescFlagByte] == 0 ? 1u : 0u);

        if (desc[kDescFlagByte] != 0) {
            engine_func_002bd448(entry_second);
            store_u32(entry_second + kEntryWord0, primary + base);
            store_u32(entry_second + kEntryWord1,
                      load_u32(desc + kDescSpanWord) -
                          load_u32(self + kSelfWord));
            entry_second[kEntryFlag] = 1;
            if (desc[kDescModeByte] == 3) {
                store_u32(entry_second + kEntryAnchor,
                          reinterpret_cast<u32>(tail));
            }
            func_0015d91c(
                reinterpret_cast<u32*>(load_u32(self + kSelfSlotList)), index,
                entry_second, 1);
        }
    }

    return static_cast<u32>(count);
}

// 0x002392e0 loads the record list stored at self+0x55C.  The object at
// self[0] is a dispatch table; slot +0x08 returns the payload size/status,
// slot +0x28 resets/prepares the record source and slot +0x34 reads the
// payload into the caller buffer.  The payload starts with an 8-byte header
// (marker 0x6767 at +0, record count at +4) followed by that many 8-byte
// records.  self+0x560 is the count field inside the copied header and
// self+0x564 is the first destination record.  The original retries the whole
// read once and commits the records only after the marker and the derived
// count ((payload_size - 8) / 8) validate.
extern "C" u32 ui_func_002adb40(void* destination, const void* source);
extern "C" void* func_00239b54(u32 size, u32 alignment);
extern "C" void func_00239b84(void* ptr);

namespace ui_2392e0 {

constexpr u32 kDispatchOffset = 0x00;
constexpr u32 kHandleOffset = 0x04;
constexpr u32 kHeaderOffset = 0x55C;
constexpr u32 kCountOffset = 0x560;
constexpr u32 kRecordsOffset = 0x564;

constexpr u32 kOpenSlot = 0x08;
constexpr u32 kResetSlot = 0x28;
constexpr u32 kReadSlot = 0x34;

constexpr u32 kStagingCapacity = 0x320;
constexpr u32 kStagingAlignment = 4;
constexpr u32 kHeaderBytes = 8;
constexpr u16 kHeaderMarker = 0x6767;

constexpr u32 kOpenOperation = 5;
constexpr u32 kOpenArgument = 2;
constexpr u32 kReadSelector = 5;
constexpr u32 kReadFlag = 0x12;

constexpr u32 kStatusLowMask = 0x3FF;
constexpr u32 kStatusErrorValue = 0x3F7;
constexpr u32 kStatusKindMask = 0x3FC00;
constexpr u32 kStatusKindShift = 10;
constexpr u32 kAcceptedKind = 0x11;
constexpr u32 kMinimumLow = 0x64;
constexpr u32 kMaximumLow = 0xB3;

static __attribute__((always_inline)) inline u16 load_u16(const void* p) {
    u16 value;
    __builtin_memcpy(&value, p, sizeof(value));
    return value;
}

static __attribute__((always_inline)) inline u32 load_u32(const void* p) {
    u32 value;
    __builtin_memcpy(&value, p, sizeof(value));
    return value;
}

static __attribute__((always_inline)) inline void store_u32(void* p, u32 value) {
    __builtin_memcpy(p, &value, sizeof(value));
}

using OpenFn = s32 (*)(void* self, u32 handle, u32 operation, u32 argument,
                       u32* size);
using ResetFn = s32 (*)(void* self, u32 handle, u32 first, u32 second,
                        u32 third);
using ReadFn = s32 (*)(void* self, void* buffer, u32 size, u32* written,
                       u32 handle, u32 selector, u32 flag);

template <typename Fn>
static __attribute__((always_inline)) inline Fn load_table_entry(
    const u8* self, u32 slot) {
    const u8* const table =
        reinterpret_cast<const u8*>(load_u32(self + kDispatchOffset));
    Fn entry;
    __builtin_memcpy(&entry, table + slot, sizeof(entry));
    return entry;
}

}  // namespace ui_2392e0

extern "C" u32 ui_func_002392e0(void* self_raw) {
    using namespace ui_2392e0;
    u8* const self = static_cast<u8*>(self_raw);

    if (load_u32(self + kHandleOffset) == 0) {
        return 0;
    }

    u32 size = 0;
    u32 written = 0;

    s32 status = load_table_entry<OpenFn>(self, kOpenSlot)(
        self, load_u32(self + kHandleOffset), kOpenOperation, kOpenArgument,
        &size);
    if ((static_cast<u32>(status) & kStatusLowMask) == kStatusErrorValue) {
        return 0;
    }

    bool prepare_source;
    if (size == 0) {
        prepare_source = true;
    } else {
        const u32 status_bits = static_cast<u32>(status);
        const u32 kind = (status_bits & kStatusKindMask) >> kStatusKindShift;
        const u32 low = status_bits & kStatusLowMask;
        prepare_source = kind == kAcceptedKind && low >= kMinimumLow &&
                         low <= kMaximumLow;
    }
    if (prepare_source) {
        if (load_table_entry<ResetFn>(self, kResetSlot)(
                self, load_u32(self + kHandleOffset), 0, 0, 0) < 0) {
            return 0;
        }
    }

    void* const buffer = func_00239b54(kStagingCapacity, kStagingAlignment);
    if (buffer == nullptr) {
        store_u32(self + kCountOffset, 0);
        return 0;
    }

    const auto payload_is_valid = [&]() {
        return load_u16(self + kHeaderOffset) == kHeaderMarker &&
               load_u32(self + kCountOffset) == (size - kHeaderBytes) >> 3;
    };

    status = load_table_entry<ReadFn>(self, kReadSlot)(
        self, buffer, size, &written, load_u32(self + kHandleOffset),
        kReadSelector, kReadFlag);
    if (status < 0) {
        goto fail_free;
    }

    if (written != 0) {
        ui_func_002adb40(self + kHeaderOffset, buffer);
    }

    if (payload_is_valid()) {
        goto copy_records;
    }

    if (load_table_entry<ResetFn>(self, kResetSlot)(
            self, load_u32(self + kHandleOffset), 0, 0, 0) < 0) {
        goto fail_free;
    }
    status = load_table_entry<OpenFn>(self, kOpenSlot)(
        self, load_u32(self + kHandleOffset), kOpenOperation, kOpenArgument,
        &size);
    if (status < 0) {
        goto fail_zero_count;
    }
    status = load_table_entry<ReadFn>(self, kReadSlot)(
        self, buffer, size, &written, load_u32(self + kHandleOffset),
        kReadSelector, kReadFlag);
    if (status < 0) {
        goto fail_zero_count;
    }

    ui_func_002adb40(self + kHeaderOffset, buffer);
    if (payload_is_valid()) {
        goto copy_records;
    }

fail_zero_count:
    store_u32(self + kCountOffset, 0);
fail_free:
    func_00239b84(buffer);
    return 0;

copy_records:
    for (u32 index = 0; index < load_u32(self + kCountOffset); ++index) {
        ui_func_002adb40(self + kRecordsOffset + index * 8u,
                         static_cast<const u8*>(buffer) + kHeaderBytes +
                             index * 8u);
    }
    func_00239b84(buffer);
    return load_u32(self + kCountOffset);
}

// ---------------------------------------------------------------------------
// 0x002A399C -- AsdPart_SetScale(part, scale)
//
// Stores the new uniform scale at part+0x60, derives the inherited factor
// (part+0x74 * scale), then walks the child list at part+0x8C.  Each child
// dispatches through its instance (child+0x90; 16-bit type at +4) into the
// 0x00464110 type table, whose entries are 0x44 bytes:
//   * child flag 0x100: the scaled child quad (+0x20) is handed to hook +0x2C;
//   * otherwise:        the derived child factor is handed to hook +0x28;
//   * child flag 0x080: a quad composed from the parent (+0x00/+0x40) and the
//                       child (+0x40) is handed to hook +0x20.
// The shared 0x004EA81C render block stages the quads between the arithmetic
// steps, and every hook receives a pointer to a private stack copy because the
// +0x2C implementations retain that pointer.
// ---------------------------------------------------------------------------

namespace asd_part_scale_002a399c {

struct Vec4 {
    f32 value[4];
};

/** Effect-part instance hung off a node at +0x90. */
struct PartInstance {
    u8  pad_00[0x04];
    u16 type;                   // +0x04: `ldrh r2,[r0,#4]`
    u8  pad_06[0x02];
    void* context;              // +0x08: `ldrne r0,[r0,#8]` (hook argument)
};
static_assert(offsetof(PartInstance, type) == 0x04);
static_assert(offsetof(PartInstance, context) == 0x08);

/** One effect-part child (or the manager header used as `self`). */
struct PartNode {
    Vec4 position;              // +0x00: copied to the render block +0x110
    u8  pad_10[0x10];
    Vec4 quad_20;               // +0x20: source quad for the +0x2C hook
    u8  pad_30[0x10];
    Vec4 quad_40;               // +0x40: parent/child composition quad
    u8  pad_50[0x10];
    f32 local_scale;            // +0x60: `vldr s0,[r4,#0x60]`
    u8  pad_64[0x04];
    u32 flags;                  // +0x68: tested against 0x100, 0x80 and 4
    u8  pad_6c[0x08];
    f32 scale_unit;             // +0x74: `vldr s1,[r0,#0x74]` on `self`
    u8  pad_78[0x0C];
    u32 scale_flags;            // +0x84: `tst r0,#1`
    u8  pad_88[0x04];
    PartNode* children;         // +0x8C: list head
    PartInstance* instance;     // +0x90: dispatch object
    u8  pad_94[0x18];
    PartNode* next;             // +0xAC: `ldr r4,[r4,#0xac]`
    u8  pad_b0[0x10];
};
static_assert(offsetof(PartNode, position) == 0x00);
static_assert(offsetof(PartNode, quad_20) == 0x20);
static_assert(offsetof(PartNode, quad_40) == 0x40);
static_assert(offsetof(PartNode, local_scale) == 0x60);
static_assert(offsetof(PartNode, flags) == 0x68);
static_assert(offsetof(PartNode, scale_unit) == 0x74);
static_assert(offsetof(PartNode, scale_flags) == 0x84);
static_assert(offsetof(PartNode, children) == 0x8C);
static_assert(offsetof(PartNode, instance) == 0x90);
static_assert(offsetof(PartNode, next) == 0xAC);
static_assert(sizeof(PartNode) == 0xC0);

/** One 0x44-byte entry of the effect-type table at 0x00464110. */
struct TypeEntry {
    u8   pad_00[0x20];
    void (*set_quad)(void* context, const Vec4* quad);        // +0x20
    u8   pad_24[0x04];
    void (*set_scale)(void* context, f32 scale);              // +0x28
    void (*set_quad_ref)(void* context, const Vec4* quad);    // +0x2C
    u8   pad_30[0x14];
};
static_assert(offsetof(TypeEntry, set_quad) == 0x20);
static_assert(offsetof(TypeEntry, set_scale) == 0x28);
static_assert(offsetof(TypeEntry, set_quad_ref) == 0x2C);
static_assert(sizeof(TypeEntry) == 0x44);

/** Vector/colour quad slots of the 0x004EA81C scratch block. */
struct RenderState {
    u8   pad_000[0x100];
    Vec4 vector;                // +0x100
    Vec4 color;                 // +0x110
};
static_assert(offsetof(RenderState, vector) == 0x100);
static_assert(offsetof(RenderState, color) == 0x110);

inline RenderState& render_state() {
    return *reinterpret_cast<RenderState*>(0x004EA81Cu);
}

inline TypeEntry* type_entries() {
    return reinterpret_cast<TypeEntry*>(0x00464110u);
}

constexpr u32 kFlagUseScaledQuad = 0x100u;  // child +0x68 bit 8
constexpr u32 kFlagComposeQuad   = 0x080u;  // child +0x68 bit 7
constexpr u32 kFlagOverrideY     = 0x004u;  // child +0x68 bit 2
constexpr u32 kFlagInheritScale  = 0x001u;  // child +0x84 bit 0
constexpr f32 kOverriddenY       = 5.0f;   // `vldr s17,[pc,#0x218]`

inline f32 child_factor(const PartNode* node, f32 inherited) {
    return (node->scale_flags & kFlagInheritScale) != 0
               ? node->local_scale * inherited
               : node->local_scale;
}

inline void scale_quad(Vec4& quad, f32 factor) {
    quad.value[0] *= factor;
    quad.value[1] *= factor;
    quad.value[2] *= factor;
    quad.value[3] *= factor;
}

inline void add_quad(Vec4& dst, const Vec4& src) {
    dst.value[0] += src.value[0];
    dst.value[1] += src.value[1];
    dst.value[2] += src.value[2];
    dst.value[3] += src.value[3];
}

}  // namespace asd_part_scale_002a399c

// DECOMP_FUNC(0x002a399c, 604)
extern "C" void engine_func_002a399c(void* part_raw, f32 scale) {
    using namespace asd_part_scale_002a399c;

    PartNode* const self = static_cast<PartNode*>(part_raw);

    // 0x002A39AC..0x002A39B8: the unit is read before the new scale is stored.
    const f32 scale_unit = self->scale_unit;
    self->local_scale = scale;
    const f32 inherited = scale_unit * scale;

    for (PartNode* node = self->children; node != nullptr; node = node->next) {
        // 0x002A39D0..0x002A3A00: two mutually exclusive per-child hook paths.
        if ((node->flags & kFlagUseScaledQuad) != 0) {
            RenderState& state = render_state();
            state.vector = node->quad_20;
            scale_quad(state.vector, child_factor(node, inherited));

            // The +0x2C hook keeps the pointer, so hand it a private copy.
            Vec4 quad = state.vector;
            PartInstance* const instance = node->instance;
            const TypeEntry* const type = &type_entries()[instance->type];
            if (type->set_quad_ref != nullptr) {
                type->set_quad_ref(instance->context, &quad);
            }
        } else {
            const f32 factor = child_factor(node, inherited);
            PartInstance* const instance = node->instance;
            const TypeEntry* const type = &type_entries()[instance->type];
            if (type->set_scale != nullptr) {
                type->set_scale(instance->context, factor);
            }
        }

        // 0x002A3A68..0x002A3B9C: compose the parent/child quad and hand it to
        // the +0x20 hook.  Every field is reloaded after the calls above.
        if ((node->flags & kFlagComposeQuad) != 0) {
            RenderState& state = render_state();
            state.vector = self->quad_40;
            state.color = self->position;
            add_quad(state.vector, state.color);
            if ((node->flags & kFlagOverrideY) != 0) {
                state.vector.value[1] = kOverriddenY;
            }
            state.color = node->quad_40;
            scale_quad(state.color, inherited);
            add_quad(state.vector, state.color);

            Vec4 quad = state.vector;
            PartInstance* const instance = node->instance;
            const TypeEntry* const type = &type_entries()[instance->type];
            if (type->set_quad != nullptr) {
                type->set_quad(instance->context, &quad);
            }
        }
    }
}

// ---------------------------------------------------------------------------
// 0x002E7E94 -- effParts child-node destroy.
//
// Detaches `node` from the manager's doubly linked child list (manager +0x80
// count, +0x88 tail, +0x8C head; node +0xAC next, +0xB0 prev), then:
//
//   1. 0x002E7EA0..0x002E7ED0: unlink and decrement the manager count (no null
//      checks beyond the two link tests);
//   2. 0x002E7ED4: a node that carries flag 0x1 is released on its own, with no
//      further list or particle work;
//   3. 0x002E7EE0..0x002E7F6C: every remaining member that carries flag 0x1 and
//      the same particle pointer is destroyed recursively.  Each recursive call
//      removes a member, so the head-first rescan terminates;
//   4. 0x002E7F70..0x002E8068: unless the node carries flag 0x2, every member
//      whose low flag bits are exactly 0x2 and whose +0x94 holds this node's
//      particle is unbound (flag 0x2 and +0x94 cleared) and re-parented with
//      0x0025C888(manager, member, firstMember); the first member is
//      re-parented onto itself and then serves as the anchor for the rest;
//   5. 0x002E806C..0x002E80DC: unless the node carries flag 0x1, its particle
//      is destroyed -- the +0x10 type-table callback runs on
//      particle->instance when that pointer is non-null, the two owned blocks
//      at +0x18 and +0x28 are freed and their three-word records cleared, and
//      the particle itself is freed;
//   6. 0x002E80E0: the node is freed by a tail call to 0x002C4360.
//
// Layouts mirror include/engine/asd_effect.h (EffPartsSource, EffPartsNode,
// EffPartsParticle, EffPartsTypeEntry); only the fields read or written here
// are named.  The 0x00464110 entry hook at +0x10 is the destructor
// counterpart of the +0x14 create_instance slot: entry 1's +0x10 target
// (0x001F7104) frees the object it receives, so only particle->instance is
// passed to it and the particle is released separately.
// ---------------------------------------------------------------------------

namespace eff_parts_destroy_002e7e94 {

struct EffPartsNode;

/** Manager/header prefix used by this routine (see EffPartsSource). */
struct EffPartsSource {
    u8 pad_00[0x80];
    u32 count;                  // +0x80: `ldr r0,[r5,#0x80]`
    u8 pad_84[0x04];
    EffPartsNode* last;         // +0x88: children.last
    EffPartsNode* first;        // +0x8C: children.first
};
static_assert(offsetof(EffPartsSource, count) == 0x80);
static_assert(offsetof(EffPartsSource, last) == 0x88);
static_assert(offsetof(EffPartsSource, first) == 0x8C);

/** One 0x2C-byte per-particle record (see EffPartsParticle). */
struct EffPartsParticle {
    u8 pad_00[0x04];
    u16 type;                   // +0x04: `ldrh r1,[r5,#4]` type-table index
    u8 pad_06[0x02];
    void* instance;             // +0x08: argument of the +0x10 table hook
    u16 field_0c;               // +0x0C: untouched here
    u8 pad_0e[0x02];
    u32 data_0;                 // +0x10: cleared with the +0x18 block
    u32 size_0;                 // +0x14: cleared with the +0x18 block
    void* alloc_0;              // +0x18: freed when non-null
    u16 field_1c;               // +0x1C: untouched here
    u8 pad_1e[0x02];
    u32 data_1;                 // +0x20: cleared with the +0x28 block
    u32 size_1;                 // +0x24: cleared with the +0x28 block
    void* alloc_1;              // +0x28: freed when non-null
};
static_assert(offsetof(EffPartsParticle, type) == 0x04);
static_assert(offsetof(EffPartsParticle, instance) == 0x08);
static_assert(offsetof(EffPartsParticle, data_0) == 0x10);
static_assert(offsetof(EffPartsParticle, size_0) == 0x14);
static_assert(offsetof(EffPartsParticle, alloc_0) == 0x18);
static_assert(offsetof(EffPartsParticle, data_1) == 0x20);
static_assert(offsetof(EffPartsParticle, size_1) == 0x24);
static_assert(offsetof(EffPartsParticle, alloc_1) == 0x28);
static_assert(sizeof(EffPartsParticle) == 0x2C);

/** One 0xC0-byte child node (see EffPartsNode). */
struct EffPartsNode {
    u8 pad_00[0x80];
    u32 count;                  // +0x80: shared prefix, not read on a member
    u8 pad_84[0x04];
    u8 field_88;                // +0x88..+0x8A: byte triplet, untouched here
    u8 field_89;
    u8 field_8a;
    u8 pad_8b;
    EffPartsNode* first;        // +0x8C: child list head, not read on a member
    EffPartsParticle* particle;// +0x90: `ldr r5,[r4,#0x90]`
    u32 field_94;               // +0x94: bound particle pointer / record index
    u32 flags;                  // +0x98: `tst r0,#1` / `tst r0,#2`
    u8 pad_9c[0x10];            // +0x9C name[0x10]
    EffPartsNode* next;         // +0xAC
    EffPartsNode* prev;         // +0xB0
};
static_assert(offsetof(EffPartsNode, count) == 0x80);
static_assert(offsetof(EffPartsNode, first) == 0x8C);
static_assert(offsetof(EffPartsNode, particle) == 0x90);
static_assert(offsetof(EffPartsNode, field_94) == 0x94);
static_assert(offsetof(EffPartsNode, flags) == 0x98);
static_assert(offsetof(EffPartsNode, next) == 0xAC);
static_assert(offsetof(EffPartsNode, prev) == 0xB0);

/** One 0x44-byte entry of the 0x00464110 table (see EffPartsTypeEntry). */
struct EffPartsTypeEntry {
    u8 pad_00[0x10];
    void (*destroy_instance)(void* instance);  // +0x10: `ldr r1,[r1,#0x10]`
    void* (*create_instance)(void* instance);  // +0x14: not called here
    u8 pad_18[0x2C];
};
static_assert(offsetof(EffPartsTypeEntry, destroy_instance) == 0x10);
static_assert(offsetof(EffPartsTypeEntry, create_instance) == 0x14);
static_assert(sizeof(EffPartsTypeEntry) == 0x44);

constexpr u32 kFlagAlias = 0x00000001u;  // node +0x98 bit 0
constexpr u32 kFlagBound = 0x00000002u;  // node +0x98 bit 1
constexpr u32 kFlagMask = 0x00000003u;   // `and r2,r2,#3`

inline EffPartsTypeEntry* type_entries() {
    return reinterpret_cast<EffPartsTypeEntry*>(0x00464110u);
}

/** First member carrying flag 0x1 and the particle pointer `particle`. */
inline EffPartsNode* find_alias(EffPartsSource* manager,
                                EffPartsParticle* particle) {
    for (EffPartsNode* member = manager->first; member != nullptr;
         member = member->next) {
        if ((member->flags & kFlagAlias) != 0 && member->particle == particle) {
            return member;
        }
    }
    return nullptr;
}

/** First member whose low flag bits are exactly 0x2 and whose +0x94 holds
 *  `particle`. */
inline EffPartsNode* find_bound(EffPartsSource* manager,
                                EffPartsParticle* particle) {
    const u32 key = reinterpret_cast<u32>(particle);
    for (EffPartsNode* member = manager->first; member != nullptr;
         member = member->next) {
        if ((member->flags & kFlagMask) == kFlagBound &&
            member->field_94 == key) {
            return member;
        }
    }
    return nullptr;
}

}  // namespace eff_parts_destroy_002e7e94

// 0x0025C888: effParts child re-parenting helper (still a raw block; the
// manager, current child and anchor are forwarded unchanged).
extern "C" void engine_func_0025c888(void* manager, void* child, void* parent);

// DECOMP_FUNC(0x002e7e94, 604)
extern "C" void engine_func_002e7e94(void* manager_raw, void* node_raw) {
    using namespace eff_parts_destroy_002e7e94;

    EffPartsSource* const manager = static_cast<EffPartsSource*>(manager_raw);
    EffPartsNode* const node = static_cast<EffPartsNode*>(node_raw);

    // 0x002E7EA0..0x002E7ED0: unlink from the doubly linked child list.
    EffPartsNode* const next = node->next;
    EffPartsNode* const prev = node->prev;
    if (prev != nullptr) {
        prev->next = next;
    } else {
        manager->first = next;
    }
    if (next != nullptr) {
        next->prev = node->prev;
    } else {
        manager->last = node->prev;
    }
    manager->count = manager->count - 1;

    // 0x002E7ED4: an alias node is released without touching the list.
    if ((node->flags & kFlagAlias) != 0) {
        engine_func_002c4360(node);
        return;
    }

    // 0x002E7EE0..0x002E7F6C: destroy the remaining aliases of this particle.
    // Both the head and the particle pointer are reloaded after every call.
    for (EffPartsNode* member = find_alias(manager, node->particle);
         member != nullptr;
         member = find_alias(manager, node->particle)) {
        engine_func_002e7e94(manager, member);
    }

    // 0x002E7F70..0x002E8068: move the members bound to this particle over to
    // the first of them.
    if ((node->flags & kFlagBound) == 0) {
        EffPartsNode* const anchor = find_bound(manager, node->particle);
        if (anchor != nullptr) {
            anchor->flags &= ~kFlagBound;
            anchor->field_94 = 0;
            engine_func_0025c888(manager, anchor, anchor);

            for (EffPartsNode* member = find_bound(manager, node->particle);
                 member != nullptr;
                 member = find_bound(manager, node->particle)) {
                engine_func_0025c888(manager, member, anchor);
            }
        }
    }

    // 0x002E806C..0x002E80DC: release the particle and its owned blocks.
    if ((node->flags & kFlagAlias) == 0) {
        EffPartsParticle* const particle = node->particle;
        if (particle->instance != nullptr) {
            const EffPartsTypeEntry* const entry =
                &type_entries()[particle->type];
            entry->destroy_instance(particle->instance);
        }
        if (particle->alloc_0 != nullptr) {
            engine_func_002c4360(particle->alloc_0);
            particle->data_0 = 0;
            particle->size_0 = 0;
            particle->alloc_0 = nullptr;
        }
        if (particle->alloc_1 != nullptr) {
            engine_func_002c4360(particle->alloc_1);
            particle->data_1 = 0;
            particle->size_1 = 0;
            particle->alloc_1 = nullptr;
        }
        engine_func_002c4360(particle);
    }

    // 0x002E80E0: release the node itself (tail call into 0x002C4360).
    engine_func_002c4360(node);
}

// ---------------------------------------------------------------------------
// 0x00339D98 -- battle-main start/resume state machine (604 B).
//
// Entered with the 0x4A58-byte battle main work in r0.  The routine takes the
// global recursive lock embedded at work+0x4A00 and drives a resumable
// 14-state dispatch stored at work+0x49FE (halfword):
//
//   state 0      : 0x00394EE0(); advance to state 1.
//   state 1      : poll 0x0039493C().  When it returns non-zero, copy the
//                  three global pointers at 0x00435D90+0x0C/+0x10/+0x14 to
//                  work+0x2248/+0x224C/+0x2250, create the script process with
//                  (script = global+0x14, msg = global+0x0C), store it at
//                  work+0x2254 and clear process->state (+0x108).  Advance to
//                  state 2.
//   state 2..7   : each waits for the pointer stored by the previous state,
//                  then copies one more global pointer:
//                    state 2: work+0x2250 != 0 -> work+0x2230 = global+0x18
//                    state 3: work+0x2230 != 0 -> work+0x2234 = global+0x1C
//                    state 4: work+0x2234 != 0 -> work+0x2238 = global+0x20
//                    state 5: work+0x2238 != 0 -> work+0x2240 = global+0x28
//                    state 6: work+0x2240 != 0 -> work+0x223C = global+0x24
//                    state 7: work+0x223C != 0 -> work+0x2244 = global+0x2C
//   state 8      : wait for work+0x2244, then 0x0023EBC8(0x3E).
//   state 9      : wait for that result, then 0x00328F60().
//   state 10     : wait for it, then 0x003291D8().
//   state 11     : wait for it, advance to state 12.
//   state 12     : advance to state 13.
//   state 13     : set work+0x49FC bit 0 and advance to state 14.
//
// Any failed wait jumps to the halfword at work+0x49FC, whose bit 0 is tested;
// while it is clear the dispatch repeats from the current state.  When bit 0
// is set the routine releases the lock with a tail call to 0x002C3A24 and
// returns.  A dispatch value of 14 or more also reaches that same test, so an
// entry with such a state and a clear bit 0 never terminates (the original
// loops forever; the invalidity is caller-provided).
//
// `state` at +0x49FE and `flag` at +0x49FC are the only halves of that word;
// the original reloads both with `ldrh` on every dispatch.  The seven pointers
// at 0x00435D90+0x0C..+0x2C are read-only here; the +0x4A00 lock belongs to
// the work object and is never dereferenced by this routine.
// ---------------------------------------------------------------------------

namespace btl_main_start_00339d98 {

/** Read-only prefix of the global battle-manager block at 0x00435D90. */
struct BtlMainManagerGlobals {
    u8 pad_00[0x0C];
    void* field_0c;                 // +0x0C: `ldr r1,[r0,#0xc]`, msg argument
    void* field_10;                 // +0x10: `ldr r2,[r0,#0x10]`
    void* field_14;                 // +0x14: `ldr r0,[r0,#0x14]`, script argument
    void* field_18;                 // +0x18: stored to work+0x2230
    void* field_1c;                 // +0x1C: stored to work+0x2234
    void* field_20;                 // +0x20: stored to work+0x2238
    void* field_24;                 // +0x24: stored to work+0x223C
    void* field_28;                 // +0x28: stored to work+0x2240
    void* field_2c;                 // +0x2C: stored to work+0x2244
};
static_assert(offsetof(BtlMainManagerGlobals, field_0c) == 0x0C);
static_assert(offsetof(BtlMainManagerGlobals, field_14) == 0x14);
static_assert(offsetof(BtlMainManagerGlobals, field_2c) == 0x2C);

/** Part of a script process returned by 0x002972F8 (state is +0x108). */
struct ScriptProcessState {
    u8 pad_00[0x108];
    u32 state;                      // +0x108: `str r1,[r0,#0x108]` with r1 = 0
};
static_assert(offsetof(ScriptProcessState, state) == 0x108);

/** Battle main work prefix touched by this routine (size 0x4A58). */
struct BtlMainWorkStart {
    u8 pad_0000[0x2230];
    void* field_2230;               // +0x2230: `str r1,[r0,#0x230]`
    void* field_2234;               // +0x2234: `str r1,[r0,#0x234]`
    void* field_2238;               // +0x2238: `str r1,[r0,#0x238]`
    void* field_223c;               // +0x223C: `str r1,[r0,#0x23c]`
    void* field_2240;               // +0x2240: `str r1,[r0,#0x240]`
    void* field_2244;               // +0x2244: `ldr r0,[r1,r5]`, state-8 gate
    void* field_2248;               // +0x2248: `str r1,[r6,#0x248]`
    void* field_224c;               // +0x224C: `str r2,[r6,#0x24c]`
    void* field_2250;               // +0x2250: `str r0,[r6,#0x250]`
    ScriptProcessState* field_2254; // +0x2254: `str r0,[r6,#0x254]`
    u8 pad_2258[0x49FC - 0x2258];
    u16 flag;                       // +0x49FC: `ldrh r1,[r4,#0xfc]`, bit 0
    u16 state;                      // +0x49FE: `ldrh r0,[r4,#0xfe]`, dispatch
    u8 pad_4a00[0x4A58 - 0x4A00];   // +0x4A00..+0x4A58: recursive lock storage
};
static_assert(offsetof(BtlMainWorkStart, field_2230) == 0x2230);
static_assert(offsetof(BtlMainWorkStart, field_2244) == 0x2244);
static_assert(offsetof(BtlMainWorkStart, field_2254) == 0x2254);
static_assert(offsetof(BtlMainWorkStart, flag) == 0x49FC);
static_assert(offsetof(BtlMainWorkStart, state) == 0x49FE);
static_assert(sizeof(BtlMainWorkStart) == 0x4A58);

constexpr u32 kScriptProcessId = 0x3EU;  // `mov r0,#0x3e` before 0x0023EBC8

inline BtlMainManagerGlobals* globals() {
    return reinterpret_cast<BtlMainManagerGlobals*>(0x00435D90u);
}

} // namespace btl_main_start_00339d98

extern "C" void engine_func_002c3aa8(void* lock);
extern "C" void engine_func_002c3a24(void* lock);
extern "C" u32 script_vm_func_00394ee0(void);
extern "C" u32 engine_func_0039493c(void);
extern "C" btl_main_start_00339d98::ScriptProcessState*
scrScriptProcess_func_002972f8(void* script, void* msg);
extern "C" u32 script_vm_func_0023ebc8(u32 id);
extern "C" void engine_func_00328f60(void);
extern "C" void engine_func_003291d8(void);

extern "C" void script_vm_func_00339d98(
    btl_main_start_00339d98::BtlMainWorkStart* work) {
    using btl_main_start_00339d98::globals;
    using btl_main_start_00339d98::kScriptProcessId;

    u8* const base = reinterpret_cast<u8*>(work);
    void* const lock = base + 0x4A00;
    engine_func_002c3aa8(lock);

    for (;;) {
        switch (work->state) {
        case 0:
            script_vm_func_00394ee0();
            work->state = 1;
            [[fallthrough]];
        case 1:
            if (engine_func_0039493c() == 0) {
                goto iteration_done;
            }
            work->field_2248 = globals()->field_0c;
            work->field_224c = globals()->field_10;
            work->field_2250 = globals()->field_14;
            work->field_2254 = scrScriptProcess_func_002972f8(
                globals()->field_14, globals()->field_0c);
            work->field_2254->state = 0;
            work->state = 2;
            [[fallthrough]];
        case 2:
            if (work->field_2250 == nullptr) {
                goto iteration_done;
            }
            work->field_2230 = globals()->field_18;
            work->state = 3;
            [[fallthrough]];
        case 3:
            if (work->field_2230 == nullptr) {
                goto iteration_done;
            }
            work->field_2234 = globals()->field_1c;
            work->state = 4;
            [[fallthrough]];
        case 4:
            if (work->field_2234 == nullptr) {
                goto iteration_done;
            }
            work->field_2238 = globals()->field_20;
            work->state = 5;
            [[fallthrough]];
        case 5:
            if (work->field_2238 == nullptr) {
                goto iteration_done;
            }
            work->field_2240 = globals()->field_28;
            work->state = 6;
            [[fallthrough]];
        case 6:
            if (work->field_2240 == nullptr) {
                goto iteration_done;
            }
            work->field_223c = globals()->field_24;
            work->state = 7;
            [[fallthrough]];
        case 7:
            if (work->field_223c == nullptr) {
                goto iteration_done;
            }
            work->field_2244 = globals()->field_2c;
            work->state = 8;
            [[fallthrough]];
        case 8:
            if (work->field_2244 == nullptr) {
                goto iteration_done;
            }
            work->state = 9;
            [[fallthrough]];
        case 9:
            if (script_vm_func_0023ebc8(kScriptProcessId) == 0) {
                goto iteration_done;
            }
            work->state = 10;
            [[fallthrough]];
        case 10:
            engine_func_00328f60();
            work->state = 11;
            [[fallthrough]];
        case 11:
            engine_func_003291d8();
            work->state = 12;
            [[fallthrough]];
        case 12:
            work->state = 13;
            [[fallthrough]];
        case 13:
            work->flag = static_cast<u16>(work->flag | 1U);
            work->state = 14;
            break;
        default:
            break;
        }

    iteration_done:
        if ((work->flag & 1U) != 0) {
            break;
        }
    }

    engine_func_002c3a24(lock);
}

// DECOMP_FUNC(0x0014cae4, 608)
//
// Resolve one texture slot's on-disk variant name and install the decoded
// "STEX" texture.  All offsets below come from the original ARM loads; the
// record at slot+0x604 holds 0x20-byte sibling entries that "-<n>" names
// refer back to.
extern "C" void engine_func_002bf86c(char* dst, const char* src);        // 0x002BF86C strcpy
extern "C" void engine_func_002b67e0(char* dst, const char* src);        // 0x002B67E0 strcat
extern "C" u32 engine_func_002c3290(const char* text);                   // 0x002C3290 strlen
extern "C" s32 engine_func_002c1a48(const void* lhs, const void* rhs,
                                   u32 size);                            // 0x002C1A48 memcmp
extern "C" void engine_func_002c4360(void* object);                      // 0x002C4360 free
extern "C" void* engine_func_002a4828(void* manager, const char* name,
                                      const char* variant_name,
                                      u32* out_size, u32 mode, u32 size,
                                      u32 user);                         // 0x002A4828

namespace smt4::engine {
struct AocTMSpr;
void* aocTexCtrl_func_002a465c(AocTMSpr* sprite, u32 flags, u32 size);   // 0x002A465C
void* AsdTexture_func_002bd940(u32 kind);                                // 0x002BD940
}  // namespace smt4::engine

struct EngineTextureDescriptor {
    u8 pad_000[0x08];
    const char* name;                 // +0x08
    u8 pad_00C;
    u8 variant;                       // +0x0D, non-zero selects .cmp / alt upload
};

struct EngineTextureSlot {
    const u8* source;                 // +0x00, inline path string starts at +0x0C
    EngineTextureDescriptor* desc;    // +0x04
    void* texture;                    // +0x08
    void* loaded;                     // +0x0C
    u32 flags;                        // +0x10, bit 0x10000 selects the high variant
};

extern "C" s32 engine_func_0014cae4(const char* base_name,
                                    EngineTextureSlot* slot, u32 user) {
    constexpr u32 kBufferSize = 0x80;
    constexpr u32 kSiblingTableEnd = 0x604;
    constexpr u32 kSiblingStride = 0x20;

    char variant_name[kBufferSize];
    char base_path[kBufferSize];
    u32 asset_size = 0;

    // 0x14CAF0: both record pointers are latched before the first helper call.
    // The source record carries its path string inline at +0x0C.
    const u8* const source_record = slot->source;
    EngineTextureDescriptor* const desc = slot->desc;

    engine_func_002bf86c(
        variant_name, reinterpret_cast<const char*>(source_record + 0x0C));

    if (desc->name[0] == '-') {
        // "-<n>" selects the n-th preceding 0x20-byte sibling entry; the
        // address arithmetic is the original's signed-byte shift.
        const s32 relative = static_cast<s32>(static_cast<s8>(desc->name[1]));
        const uintptr_t sibling_address =
            reinterpret_cast<uintptr_t>(slot) + kSiblingTableEnd
            - static_cast<uintptr_t>(relative * static_cast<s32>(kSiblingStride));
        void* const sibling = *reinterpret_cast<void**>(sibling_address);
        const char* const sibling_name = *reinterpret_cast<const char* const*>(
            static_cast<u8*>(sibling) + 8);
        engine_func_002b67e0(variant_name, sibling_name);
    } else {
        engine_func_002b67e0(variant_name, desc->name);
    }

    if (desc->variant != 0) {
        engine_func_002b67e0(variant_name, ".cmp");
    } else {
        engine_func_002b67e0(variant_name, ".stex");
    }

    if (engine_func_002c3290(desc->name) == 0) {
        slot->texture = nullptr;
        return 0;
    }

    engine_func_002bf86c(base_path, base_name);

    const u32 flags = slot->flags;
    if ((flags & ~0x10000u) != 0) {
        return 0;
    }

    // 0x14CBB0..0x14CBD0: request mode 1 or 3, toggled when variant != 0.
    const u32 base_mode = (flags & 0x10000u) != 0 ? 3u : 1u;
    const u32 load_mode = desc->variant != 0 ? (base_mode ^ 2u) : base_mode;

    void* data = engine_func_002a4828(
        *reinterpret_cast<void**>(0x00433130), base_path, variant_name,
        &asset_size, load_mode, kBufferSize, user);
    if (data == nullptr) {
        return 0;
    }

    if (desc->variant != 0) {
        data = smt4::engine::aocTexCtrl_func_002a465c(
            static_cast<smt4::engine::AocTMSpr*>(data), base_mode, kBufferSize);
    }

    if (engine_func_002c1a48(data, "STEX", 4) != 0) {
        engine_func_002c4360(data);
        return 0;
    }

    if (*reinterpret_cast<u32*>(static_cast<u8*>(data) + 0x24) != 0) {
        slot->texture = nullptr;
    } else {
        // 0x14CC80..0x14CD24: publish the decoded header into an AsdTexture.
        void* const texture = smt4::engine::AsdTexture_func_002bd940(
            (slot->flags & 0x10000u) != 0 ? 1u : 0u);
        slot->texture = texture;

        u8* const object = static_cast<u8*>(texture);
        const u8* const header = static_cast<const u8*>(data);

        *reinterpret_cast<u32*>(object + 0x04) =
            *reinterpret_cast<const u32*>(header + 0x08);
        *reinterpret_cast<u32*>(object + 0x14) =
            *reinterpret_cast<const u32*>(header + 0x0C);
        *reinterpret_cast<u32*>(object + 0x18) =
            *reinterpret_cast<const u32*>(header + 0x10);
        *reinterpret_cast<u32*>(object + 0x1C) =
            *reinterpret_cast<const u32*>(header + 0x18);
        *reinterpret_cast<u32*>(object + 0x20) =
            *reinterpret_cast<const u32*>(header + 0x14);
        *reinterpret_cast<u32*>(object + 0x28) =
            asset_size - *reinterpret_cast<const u32*>(header + 0x20);
        *reinterpret_cast<u32*>(object + 0x2C) |= 0x10u;

        if (*reinterpret_cast<const u32*>(header + 0x04) == 1) {
            *reinterpret_cast<u32*>(object + 0x3C) = 1;
            *reinterpret_cast<u32*>(object + 0x40) = 1;
        }

        *reinterpret_cast<u32*>(object + 0x24) =
            static_cast<u32>(reinterpret_cast<uintptr_t>(data))
            + *reinterpret_cast<const u32*>(header + 0x20);
    }

    slot->loaded = data;
    slot->flags = slot->flags | 2u;
    return 1;
}

// DECOMP_FUNC(0x0035b364, 616)
//
// UTF-16 message-macro scanner.  The scanned object is also the sentinel of a
// circular doubly-linked list: its first two words are the list next/prev
// pointers, and every token becomes a 0x10-byte node taken from `allocator`
// (0x00238C44 is a 16-byte-unit pool allocator).  Scanning starts at the
// object's pre-existing `cursor` field, never rewinds, and stops when the
// cursor reaches `length`.
//
// Unquoted text: "\Q" switches to verbatim mode, "\E" outside verbatim mode
// aborts the scan with 2, the two space characters are dropped, and every other
// character becomes a node handed to the per-character member-function-pointer
// table at 0x00472B80 (indexed by character - 0x20, 8 bytes per entry:
// {handler, this-adjust}).  Every shipped adjust word is zero, so the handler
// always receives the object itself and the address of the new node.
//
// Verbatim text produces one literal type-0 character node per non-space
// character until "\E" is consumed.
//
// Returns 0 after appending the type-0x12 terminator node, 1 when the node
// allocator returns null, 2 for a stray "\E", otherwise the first non-zero
// handler result (the scan stops there).

struct MsgNode {
    MsgNode* next;   // +0x00
    MsgNode* prev;   // +0x04
    u8 type;         // +0x08
    u8 reserved09;   // +0x09
    u16 character;   // +0x0A
    u16 value;       // +0x0C
    u16 reserved0E;  // +0x0E
};

struct MsgScanner {
    MsgNode* head;     // +0x00 list head (newest node; the object is the
                       //        circular list's sentinel)
    MsgNode* tail;     // +0x04 list tail (oldest node)
    void* allocator;   // +0x08
    const u16* text;   // +0x0C
    u32 cursor;        // +0x10
    u32 length;        // +0x14
    s32 depth;         // +0x18
};

extern "C" void* func_00238c44(void* allocator, u32 units);

// Per-character handlers reached through the 0x00472B80 dispatch table; the
// table stores no this-adjustment, so they are entered as (this, &node).
extern "C" s32 func_0035b254(MsgScanner* self, MsgNode** node);  // '.'
extern "C" s32 func_0035b294(MsgScanner* self, MsgNode** node);  // '+'
extern "C" s32 func_0035b2d4(MsgScanner* self, MsgNode** node);  // '$'
extern "C" s32 func_0035b324(MsgScanner* self, MsgNode** node);  // '-'
extern "C" s32 func_0035bbc4(MsgScanner* self, MsgNode** node);  // any other
extern "C" s32 func_0035bbf8(MsgScanner* self, MsgNode** node);  // '*'
extern "C" s32 func_0035bc38(MsgScanner* self, MsgNode** node);  // '?'
extern "C" s32 func_0035bc78(MsgScanner* self, MsgNode** node);  // '&'
extern "C" s32 func_0035bcf8(MsgScanner* self, MsgNode** node);  // '\'
extern "C" s32 func_0035bd64(MsgScanner* self, MsgNode** node);  // '{'
extern "C" s32 func_0035bf8c(MsgScanner* self, MsgNode** node);  // '^'
extern "C" s32 func_0035bfcc(MsgScanner* self, MsgNode** node);  // '|'
extern "C" s32 func_0035c128(MsgScanner* self, MsgNode** node);  // '('
extern "C" s32 func_0035c168(MsgScanner* self, MsgNode** node);  // ')'
extern "C" s32 func_0035c1a8(MsgScanner* self, MsgNode** node);  // '['
extern "C" s32 func_0035c210(MsgScanner* self, MsgNode** node);  // ']'

namespace {

constexpr u16 kEscape = 0x5C;           // '\'
constexpr u16 kVerbatimStart = 0x51;    // 'Q'
constexpr u16 kVerbatimEnd = 0x45;      // 'E'
constexpr u16 kSpace = 0x0020;
constexpr u16 kIdeographicSpace = 0x3000;
constexpr u8 kCharacterType = 0x00;
constexpr u8 kTerminatorType = 0x12;

// 0x00238C44(allocator, 1), prepended to the object's circular list.
__attribute__((always_inline)) inline MsgNode* append_node(MsgScanner* self) {
    MsgNode* const node =
        static_cast<MsgNode*>(func_00238c44(self->allocator, 1));
    if (node == nullptr) {
        return nullptr;
    }
    node->next = self->head;
    node->prev = reinterpret_cast<MsgNode*>(self);
    self->head = node;
    node->next->prev = node;
    return node;
}

// 0x00472B80 member-function-pointer dispatch for the current character.
__attribute__((always_inline)) inline s32 dispatch_node(MsgScanner* self,
                                                       MsgNode** node) {
    switch (self->text[self->cursor]) {
    case 0x24: return func_0035b2d4(self, node);
    case 0x26: return func_0035bc78(self, node);
    case 0x28: return func_0035c128(self, node);
    case 0x29: return func_0035c168(self, node);
    case 0x2A: return func_0035bbf8(self, node);
    case 0x2B: return func_0035b294(self, node);
    case 0x2D: return func_0035b324(self, node);
    case 0x2E: return func_0035b254(self, node);
    case 0x3F: return func_0035bc38(self, node);
    case 0x5B: return func_0035c1a8(self, node);
    case 0x5C: return func_0035bcf8(self, node);
    case 0x5D: return func_0035c210(self, node);
    case 0x5E: return func_0035bf8c(self, node);
    case 0x7B: return func_0035bd64(self, node);
    case 0x7C: return func_0035bfcc(self, node);
    default: return func_0035bbc4(self, node);
    }
}

}  // namespace

extern "C" s32 func_0035b364(MsgScanner* self, void* allocator,
                             const u16* text, u32 length) {
    self->allocator = allocator;
    self->text = text;
    self->length = length;
    self->depth = 0;

    bool verbatim = false;

    while (self->cursor != self->length) {
        const u32 cursor = self->cursor;
        const u32 last = self->length - 1;

        if (verbatim) {
            if (cursor != last && self->text[cursor] == kEscape &&
                self->text[cursor + 1] == kVerbatimEnd) {
                self->cursor = cursor + 2;
                verbatim = false;
            } else if (self->text[cursor] == kSpace ||
                       self->text[cursor] == kIdeographicSpace) {
                self->cursor = cursor + 1;
            } else {
                MsgNode* const node = append_node(self);
                if (node == nullptr) {
                    return 1;
                }
                node->type = kCharacterType;
                node->character = self->text[self->cursor];
                self->cursor = self->cursor + 1;
            }
            continue;
        }

        if (cursor != last && self->text[cursor] == kEscape &&
            self->text[cursor + 1] == kVerbatimStart) {
            self->cursor = cursor + 2;
            verbatim = true;
            continue;
        }
        if (cursor != last && self->text[cursor] == kEscape &&
            self->text[cursor + 1] == kVerbatimEnd) {
            return 2;
        }
        if (self->text[cursor] == kSpace ||
            self->text[cursor] == kIdeographicSpace) {
            self->cursor = cursor + 1;
            continue;
        }

        MsgNode* const node = append_node(self);
        if (node == nullptr) {
            return 1;
        }
        MsgNode* slot = node;
        const s32 result = dispatch_node(self, &slot);
        if (result != 0) {
            return result;
        }
    }

    MsgNode* const terminator = append_node(self);
    if (terminator == nullptr) {
        return 1;
    }
    terminator->type = kTerminatorType;
    return 0;
}

// ---------------------------------------------------------------------------
// Message-macro tree builder.
//
// 0x0035C754 continues the token walk started by 0x0035C65C and turns the
// token chain into 0x20-byte container nodes handed to the message macro
// callbacks.  The parse state initialised by 0x0035D9D0 / 0x0035D914 has:
//   +0x00 node        current scanner node (token type byte at node + 0x08)
//   +0x04 head        circular result-list sentinel next (sentinel = state + 4)
//   +0x08 tail        circular result-list sentinel prev
//   +0x0C pool        allocator passed to 0x00238C44 for containers
//   +0x10 reserved
//   +0x14 child_pool  copied into every new container's +0x10
//   +0x18 depth       (not touched here; 0x0035D6AC maintains it)
//
// A token type selects two handlers from the shipped tables at 0x00472B40
// (first) and 0x00472BD8 (second), eight bytes per entry {handler, adjust}:
//   * adjust even: call handler with `state` as `this`;
//   * adjust odd: `this` is state + (adjust >> 1) and the callee is
//     *(u32*)(*(u32*)this + handler), the ARM member-function-pointer form.
//     Every shipped entry has adjust == 0; the odd form is kept because the
//     binary implements it and the table lives in writable data.
//
// First handler: 1 opens a nested container, 0 runs the second handler,
// anything else is returned to the caller.  Second handler: 0 and 1 continue
// the loop with the value it stored (the original compares against 1 with a
// conditional compare against 0), anything else is returned.

struct MsgTreeState {
    u32 node;         // +0x00
    u32 head;         // +0x04
    u32 tail;         // +0x08
    u32 pool;         // +0x0C
    u32 reserved10;   // +0x10
    u32 child_pool;   // +0x14
    u32 depth;        // +0x18
};

// Two 16-byte units from 0x00238C44.  +0x00/+0x04 are list links; a nested
// reference stores the container it points at in +0x08 and the byte 1 in
// +0x0C, a container stores the empty nested list header in +0x08..+0x14.
struct MsgTreeNode {
    u32 next;    // +0x00
    u32 prev;    // +0x04
    u32 inner0;  // +0x08
    u32 inner1;  // +0x0C
    u32 pool;    // +0x10
    u32 inner2;  // +0x14
    u32 inner3;  // +0x18
};

struct MsgHandlerSlot {
    u32 handler;  // +0x00
    u32 adjust;   // +0x04
};

extern "C" s32 func_0035c65c(MsgTreeState* state, u32* value_out, u32* value);
extern "C" void* func_00238c44(void* pool, u32 units);
extern "C" void func_00237f10(u8* payload);
extern "C" void func_00237efc(u8* payload, const u32* value);

namespace {

constexpr u32 kMsgHandlerTable = 0x00472B40;
constexpr u32 kMsgSecondHandlerOffset = 0x98;
constexpr u32 kMsgNodeUnits = 2;
constexpr u32 kMsgNestedType = 1;

__attribute__((always_inline)) inline u8 msg_token_type(const MsgTreeState* state) {
    return *reinterpret_cast<const u8*>(state->node + 8);
}

// Insert `node` at the front of the circular list whose sentinel lives at
// `head` (the sentinel's own address is stored in node->prev).
__attribute__((always_inline)) inline void link_msg_node(u32* head,
                                                         MsgTreeNode* node) {
    node->next = *head;
    node->prev = reinterpret_cast<u32>(head);
    *head = reinterpret_cast<u32>(node);
    reinterpret_cast<MsgTreeNode*>(node->next)->prev =
        reinterpret_cast<u32>(node);
}

typedef s32 (*MsgFirstHandler)(MsgTreeState*, u32*, u32*);
typedef s32 (*MsgSecondHandler)(MsgTreeState*, u32*, u32*, u32*);

struct MsgHandlerCall {
    MsgTreeState* self;  // r0
    u32 fn;              // blx target
};

// Resolve one {handler, adjust} slot exactly as the ARM call sequence does.
__attribute__((always_inline)) inline MsgHandlerCall resolve_msg_handler(
    u32 table, MsgTreeState* state, u32 type) {
    const MsgHandlerSlot* const slot = reinterpret_cast<const MsgHandlerSlot*>(
        table + type * sizeof(MsgHandlerSlot));
    const u32 adjust = slot->adjust;
    MsgHandlerCall call;
    // `add r0, r4, r0, asr #1`: the adjust word is shifted arithmetically.
    call.self = reinterpret_cast<MsgTreeState*>(
        reinterpret_cast<u32>(state) + (static_cast<s32>(adjust) >> 1));
    if (adjust & 1) {
        const u32* const object = reinterpret_cast<const u32*>(call.self);
        call.fn = *reinterpret_cast<const u32*>(*object + slot->handler);
    } else {
        call.fn = slot->handler;
    }
    return call;
}

// Allocate a container from the state pool and push it onto the result list.
__attribute__((always_inline)) inline MsgTreeNode* make_msg_container(
    MsgTreeState* state) {
    MsgTreeNode* const node = static_cast<MsgTreeNode*>(
        func_00238c44(reinterpret_cast<void*>(state->pool), kMsgNodeUnits));
    if (node == nullptr) {
        return nullptr;
    }
    // Empty nested-list header at +0x08; +0x10 is cleared by the header
    // constructor and then loaded with the pool copy.
    node->pool = 0;
    node->inner0 = reinterpret_cast<u32>(node) + 8;
    node->inner2 = 0;
    node->inner1 = reinterpret_cast<u32>(node) + 8;
    link_msg_node(&state->head, node);
    node->pool = state->child_pool;
    return node;
}

// Allocate a reference node inside `parent`'s nested list pointing at
// `container`.  Returns false when the parent's pool is exhausted.
__attribute__((always_inline)) inline bool link_nested_container(
    u32 parent, MsgTreeNode* container) {
    MsgTreeNode* const node = static_cast<MsgTreeNode*>(func_00238c44(
        reinterpret_cast<void*>(
            *reinterpret_cast<const u32*>(parent + 0x10)),
        kMsgNodeUnits));
    if (node == nullptr) {
        return false;
    }
    func_00237f10(reinterpret_cast<u8*>(node) + 8);
    link_msg_node(reinterpret_cast<u32*>(parent + 8), node);
    u32 value = reinterpret_cast<u32>(container);
    func_00237efc(reinterpret_cast<u8*>(node) + 8, &value);
    return true;
}

}  // namespace

// DECOMP_FUNC(0x0035c754, 616)
extern "C" s32 func_0035c754(MsgTreeState* state, u32* out, u32* value) {
    u32 parsed = 0;
    u32 initial = *value;
    s32 result = func_0035c65c(state, &parsed, &initial);
    if (result != 0) {
        return result;
    }

    if (msg_token_type(state) != kMsgNestedType) {
        *out = parsed;
        return 0;
    }

    MsgTreeNode* const container = make_msg_container(state);
    if (container == nullptr) {
        return 2;
    }
    if (!link_nested_container(parsed, container)) {
        return 2;
    }

    for (;;) {
        if (msg_token_type(state) != kMsgNestedType) {
            *out = reinterpret_cast<u32>(container);
            return 0;
        }
        state->node = *reinterpret_cast<const u32*>(state->node + 4);

        u32 inner_value = *value;
        u32 first_out = 0;
        u32 second_out = 0;

        for (;;) {
            const MsgHandlerCall first =
                resolve_msg_handler(kMsgHandlerTable, state,
                                    msg_token_type(state));
            u32 first_value = inner_value;
            result = reinterpret_cast<MsgFirstHandler>(first.fn)(
                first.self, &first_out, &first_value);
            if (result == 1) {
                if (!link_nested_container(inner_value, container)) {
                    return 2;
                }
                break;
            }
            if (result != 0) {
                return result;
            }

            const MsgHandlerCall second = resolve_msg_handler(
                kMsgHandlerTable + kMsgSecondHandlerOffset, state,
                msg_token_type(state));
            u32 second_value = inner_value;
            u32 previous = first_out;
            result = reinterpret_cast<MsgSecondHandler>(second.fn)(
                second.self, &second_out, &second_value, &previous);
            // 0x35C92C compares against 1 and then conditionally against 0, so
            // both 0 and 1 continue the loop with the second handler's value;
            // any other result is returned.
            if (result != 0 && result != 1) {
                return result;
            }
            inner_value = second_out;
        }
    }
}

// DECOMP_FUNC(0x00131950, 620)
//
// Vector commit for the shared engine state.  `self` owns the state at +0x04
// and a notification sink at +0x0C.  The state holds a pointer array delimited
// by the begin/end pair at +0xBC/+0xC0; the routine runs the introsort stage
// over that array (0x123C24), then finishes with the same 16-element
// insertion-sort split the library sort uses, and finally tail-calls the sink's
// vtable entry +0x14 with (sink, state), returning its result.
//
// Element ordering comes from 0x2B3B6C: it reads element + 8 to reach a key
// object, applies a `0x40000001` validity-mask test to that object's first
// word, and compares the key object's u32 at +0x4C; a null element sorts
// before every non-null element.  That helper ignores its first parameter, so
// the original could materialise a separate stack scratch object per call site;
// this reconstruction passes one stateless local for all four sites.
extern "C" void func_00123c24(void** first, void** last, s32 depth);
extern "C" s32 battle_func_002b3b6c(const void* comparator, void* left,
                                    void* right);

namespace engine_131950 {

// The part of `self` this routine reads.
struct Owner {
    u8 pad_00[0x04];
    u8* state;          // +0x04: shared engine state (forwarded to the sink)
    void* reserved_08;  // +0x08: not read here
    void* sink;         // +0x0C: object notified through vtable +0x14
};

// The sorted vector header inside the shared state.
struct State {
    u8 pad_00[0xBC];
    void** begin;       // +0xBC
    void** end;         // +0xC0
};

constexpr u32 kNotifySlotOffset = 0x14;  // vtable entry used by the tail call
constexpr s32 kInsertionThreshold = 16;  // 0x10, compared signed in the original

using NotifyFn = u32 (*)(void* sink, u8* state);

// Stateless comparison object; 0x2B3B6C never reads its first argument.
struct Comparator {
    u32 unused;
};

inline bool less(Comparator& comparator, void* left, void* right) {
    return battle_func_002b3b6c(&comparator, left, right) != 0;
}

// 0x1319E4 / 0x131B1C: inlined backward word copy.  Every word of
// [first, last) moves one slot up, walking from the high end downwards.
inline void shift_right_one(void** first, void** last) {
    for (void** dst = last; dst != first; --dst) {
        dst[0] = dst[-1];
    }
}

// 0x131A08 / 0x131B40: walk `key` down while it compares before its
// predecessor.  Unbounded by design: the caller guarantees *first is not
// ordered after key.
inline void unguarded_linear_insert(void** last, void* key,
                                    Comparator& comparator) {
    void** prev = last - 1;
    while (less(comparator, key, prev[0])) {
        last[0] = prev[0];
        last = prev;
        --prev;
    }
    last[0] = key;
}

// 0x131AD0 / 0x131A60: insertion sort with the leading-element fast path.
inline void insertion_sort(void** first, void** last, Comparator& comparator) {
    for (void** current = first + 1; current != last; ++current) {
        void* const key = current[0];
        if (less(comparator, key, first[0])) {
            shift_right_one(first, current);
            first[0] = key;
        } else {
            unguarded_linear_insert(current, key, comparator);
        }
    }
}

// 0x131A60: sort the tail of the vector without the leading-element test.
inline void unguarded_insertion_sort(void** first, void** last,
                                     Comparator& comparator) {
    for (void** current = first; current != last; ++current) {
        unguarded_linear_insert(current, current[0], comparator);
    }
}

}  // namespace engine_131950

extern "C" u32 engine_func_00131950(void* self) {
    using namespace engine_131950;

    Owner* const owner = static_cast<Owner*>(self);
    State* const state = reinterpret_cast<State*>(owner->state);

    void** const begin = state->begin;
    void** const end = state->end;

    Comparator comparator;

    if (begin != end) {
        const s32 count = static_cast<s32>(
            reinterpret_cast<const u8*>(end) -
            reinterpret_cast<const u8*>(begin)) >> 2;

        // Introsort stage; the original forwards the element count as the
        // helper's depth bound (0x131978 `asr r2, r4, #2`).
        func_00123c24(begin, end, count);

        if (count <= kInsertionThreshold) {
            insertion_sort(begin, end, comparator);
        } else {
            void** const middle = begin + kInsertionThreshold;
            insertion_sort(begin, middle, comparator);
            unguarded_insertion_sort(middle, end, comparator);
        }
    }

    // Tail call: (sink, state) through the sink's vtable slot 0x14.  The
    // original re-reads both owner fields here, so keep the reload.
    void* const sink = owner->sink;
    u8* const current_state = owner->state;
    void** const vtable = *reinterpret_cast<void***>(sink);
    const NotifyFn notify =
        reinterpret_cast<NotifyFn>(vtable[kNotifySlotOffset / 4]);
    return notify(sink, current_state);
}

// ---------------------------------------------------------------------------
// 0x00256078: commit a script command request into a freshly claimed slot.
//
// ABI recovered from the ARM listing:
//   r0 = owner work area, r1 = 0x18C-byte request record, r2 = mode,
//   r3 = slot index, [sp] = flag (read as `ldr r9, [sp, #0x20]` after the
//   0x20-byte `push {r4-r10, lr}`).
//
// The routine clears the request's 15-word transfer tail [0x14C, 0x188),
// claims a unit slot according to `mode`, copies the request to slot+0xCC and
// resolves the slot payload handle.  All modes then run the same join, which
//   * echoes the 16-bit index at slot+8 and slot_table[index]+0x62,
//   * zeroes the 0x3C-byte actor scratch area at slot+0x72, the transfer
//     fields slot+0xAE..slot+0xBE and slot+0x258..slot+0x274,
//   * sets slot bit 29 when the stack `flag` is non-zero,
//   * copies the slot's pre-existing u16 at +0x6E into slot_table[index]+0x60
//     and writes the 0x281/0x481/0x881 marker at slot_table[index]+0x50,
// and finally tail-branches to 0x00255318(index, 0xC, 0x003BE980(slot), 0).
// The original restores r4-r10+lr before that branch, so the return value is
// whatever 0x00255318 leaves in r0.
//
// Modes outside {0, 1, 2} leave the slot pointer at zero and still run the
// join: the original then stores through addresses 8/0x72/... and takes a data
// abort when address 0 is unmapped.  The six constant call sites pass 0, 1 or
// 2; the seventh (0x003C14DC) forwards its own argument, which its caller
// compares against 0 and 1.  The null-slot path is reproduced verbatim.
extern "C" u8* battle_func_00256418(void* owner, s32 index, u32 want_occupied);
extern "C" u8* script_vm_func_0033a7d4(void* owner);
extern "C" u8* script_vm_func_002b66ec();
extern "C" u8* camp_func_002a89e4(s32 index);
extern "C" void engine_func_002c3b48(void* dst, u32 size);
extern "C" u32 camp_func_003be980(const void* slot);
extern "C" u32 script_vm_func_00255318(s32 index, u32 kind, u32 value,
                                        s32 flag);

namespace {

constexpr u32 kRequestSize = 0x18Cu;         // bytes copied into the slot
constexpr u32 kRequestTailBegin = 0x14Cu;    // transfer tail cleared in place
constexpr u32 kRequestTailEnd = 0x188u;      // exclusive

constexpr u32 kSlotDataOffset = 0xCCu;       // request copy inside the slot
constexpr u32 kSlotKindOffset = 0x00u;       // `strd` writes kind + 0
constexpr u32 kSlotKindAuxOffset = 0x04u;
constexpr u32 kSlotIndexEchoOffset = 0x08u;  // u16 index echo
constexpr u32 kSlotRequestIdOffset = 0x6Eu;  // u16 copied to the slot table
constexpr u32 kSlotScratchOffset = 0x72u;    // 0x3C zeroed bytes
constexpr u32 kSlotScratchSize = 0x3Cu;
constexpr u32 kSlotMode0IndexOffset = 0xD4u; // request s16 at +8
constexpr u32 kSlotMode1IdOffset = 0xCEu;    // request u16 at +2
constexpr u32 kSlotMode1ByteOffset = 0x1A0u; // request byte 0xD4
constexpr u32 kSlotHandleMode0Flagged = 0x278u;
constexpr u32 kSlotHandleMode0Plain = 0x27Cu;
constexpr u32 kSlotHandleMode2 = 0x280u;
constexpr u32 kSlotHandleMode1 = 0x284u;

constexpr u32 kSlotTableOffset = 0x1E98u;    // *(owner+0x1E98) -> 0x114 rows
constexpr u32 kSlotTableStride = 0x114u;
constexpr u32 kMode0CountOffset = 0x1FC4u;   // u16, wraps modulo 2^16
constexpr u32 kMode1CountOffset = 0x1FC6u;   // u16, wraps modulo 2^16
constexpr u32 kMode2FlagOffset = 0x49C4u;    // u8 list-selection flag

constexpr u32 kSlotTableMarkerOffset = 0x50u;
constexpr u32 kSlotTableRequestIdOffset = 0x60u;
constexpr u32 kSlotTableIndexOffset = 0x62u;

constexpr u32 kKindMode0Flagged = 7u;
constexpr u32 kKindMode0Plain = 9u;
constexpr u32 kKindMode1 = 0x11u;
constexpr u32 kKindMode2 = 0x21u;
constexpr u32 kSlotBitMode1 = 0x100u;
constexpr u32 kSlotBitFlagArgument = 0x20000000u;

constexpr u32 kCampRecordOffset = 0x910Cu;      // from the 0x002A8A08 base
constexpr u32 kCampRecordStatusOffset = 0x44u;  // u16 selection status
constexpr u32 kCampModeArgument = 0x21u;        // still in r0 at the call

// The literal pool holds the two upper markers; index < 4 produces 0x281
// instead (the unconditional 0x81 store is always overwritten).
constexpr u32 kMarkerLow = 0x281u;
constexpr u32 kMarkerMiddle = 0x481u;
constexpr u32 kMarkerHigh = 0x881u;
constexpr s32 kMarkerLowBoundary = 4;
constexpr s32 kMarkerHighBoundary = 0x36;

constexpr u32 kTailKind = 0xCu;
constexpr s32 kTailFlag = 0;

inline u8 LoadU8(const void* base, u32 offset) {
    return *reinterpret_cast<const u8*>(static_cast<const u8*>(base) + offset);
}

inline u16 LoadU16(const void* base, u32 offset) {
    return *reinterpret_cast<const u16*>(static_cast<const u8*>(base) + offset);
}

inline s16 LoadS16(const void* base, u32 offset) {
    return *reinterpret_cast<const s16*>(static_cast<const u8*>(base) + offset);
}

inline u32 LoadU32(const void* base, u32 offset) {
    return *reinterpret_cast<const u32*>(static_cast<const u8*>(base) + offset);
}

inline void StoreU8(void* base, u32 offset, u8 value) {
    *reinterpret_cast<u8*>(static_cast<u8*>(base) + offset) = value;
}

inline void StoreU16(void* base, u32 offset, u16 value) {
    *reinterpret_cast<u16*>(static_cast<u8*>(base) + offset) = value;
}

inline void StoreU32(void* base, u32 offset, u32 value) {
    *reinterpret_cast<u32*>(static_cast<u8*>(base) + offset) = value;
}

}  // namespace

// DECOMP_FUNC(0x00256078, 620)
extern "C" u32 script_vm_func_00256078(void* owner, u8* request, u32 mode,
                                        s32 index, u32 flag) {
    u8* const owner_bytes = static_cast<u8*>(owner);

    for (u32 offset = kRequestTailBegin; offset < kRequestTailEnd; offset += 4) {
        StoreU32(request, offset, 0);
    }

    u8* slot = nullptr;

    switch (mode) {
    case 0: {
        // Claim the free unit at `index`, then select the payload from the
        // copied request byte 0.
        slot = battle_func_00256418(owner, index, 0);
        ui_func_002bcf58(slot + kSlotDataOffset, request, kRequestSize);
        if ((LoadU8(slot, kSlotDataOffset) & 1u) != 0) {
            StoreU32(slot, kSlotKindOffset, kKindMode0Flagged);
            StoreU32(slot, kSlotKindAuxOffset, 0);
            StoreU32(slot, kSlotHandleMode0Flagged,
                     reinterpret_cast<u32>(script_vm_func_002b66ec()));
        } else {
            StoreU32(slot, kSlotKindOffset, kKindMode0Plain);
            StoreU32(slot, kSlotKindAuxOffset, 0);
            StoreU32(slot, kSlotHandleMode0Plain,
                     reinterpret_cast<u32>(camp_func_002a89e4(
                         LoadS16(slot, kSlotMode0IndexOffset))));
        }
        StoreU16(owner_bytes, kMode0CountOffset,
                 static_cast<u16>(LoadU16(owner_bytes, kMode0CountOffset) + 1u));
        break;
    }
    case 1: {
        // Claim the first free unit from index 4 up to 0x35.
        slot = script_vm_func_0033a7d4(owner);
        ui_func_002bcf58(slot + kSlotDataOffset, request, kRequestSize);
        StoreU32(slot, kSlotKindOffset, kKindMode1);
        StoreU32(slot, kSlotKindAuxOffset, 0);
        StoreU32(slot, kSlotHandleMode1,
                 reinterpret_cast<u32>(
                     battle_func_002b087c(LoadU16(slot, kSlotMode1IdOffset))));
        if (LoadU8(slot, kSlotMode1ByteOffset) == 1u) {
            StoreU32(slot, kSlotKindOffset,
                     LoadU32(slot, kSlotKindOffset) | kSlotBitMode1);
        }
        StoreU16(owner_bytes, kMode1CountOffset,
                 static_cast<u16>(LoadU16(owner_bytes, kMode1CountOffset) + 1u));
        break;
    }
    case 2: {
        // Claim the free unit at `index` and bind the current camp list
        // record; the owner flag mirrors bit 1 of its status.
        slot = battle_func_00256418(owner, index, 0);
        ui_func_002bcf58(slot + kSlotDataOffset, request, kRequestSize);
        StoreU32(slot, kSlotKindOffset, kKindMode2);
        StoreU32(slot, kSlotKindAuxOffset, 0);
        u8* const camp_record =
            camp_func_002a8a08(kCampModeArgument) + kCampRecordOffset;
        StoreU32(slot, kSlotHandleMode2, reinterpret_cast<u32>(camp_record));
        StoreU8(owner_bytes, kMode2FlagOffset,
                (LoadU16(camp_record, kCampRecordStatusOffset) & 2u) != 0 ? 0u
                                                                         : 1u);
        break;
    }
    default:
        // The original keeps r4 = 0 here and falls through into the join.
        break;
    }

    const u16 index_u16 = static_cast<u16>(index);

    StoreU16(slot, kSlotIndexEchoOffset, index_u16);
    engine_func_002c3b48(slot + kSlotScratchOffset, kSlotScratchSize);
    StoreU32(slot, 0xAEu, 0);
    StoreU32(slot, 0xB2u, 0);
    StoreU32(slot, 0xB6u, 0);
    StoreU32(slot, 0xBAu, 0);
    StoreU16(slot, 0xBEu, 0);
    for (u32 offset = 0x258u; offset <= 0x274u; offset += 4) {
        StoreU32(slot, offset, 0);
    }
    if (flag != 0) {
        StoreU32(slot, kSlotKindOffset,
                 LoadU32(slot, kSlotKindOffset) | kSlotBitFlagArgument);
    }

    u8* const slot_table =
        reinterpret_cast<u8*>(LoadU32(owner_bytes, kSlotTableOffset));
    u8* const entry = slot_table + static_cast<u32>(index) * kSlotTableStride;
    u32 marker = kMarkerHigh;
    if (index < kMarkerLowBoundary) {
        marker = kMarkerLow;
    } else if (index < kMarkerHighBoundary) {
        marker = kMarkerMiddle;
    }
    StoreU32(entry, kSlotTableMarkerOffset, marker);
    StoreU16(entry, kSlotTableRequestIdOffset,
             LoadU16(slot, kSlotRequestIdOffset));
    StoreU16(entry, kSlotTableIndexOffset, index_u16);

    return script_vm_func_00255318(index, kTailKind, camp_func_003be980(slot),
                                    kTailFlag);
}

// ---------------------------------------------------------------------------
// 0x003AA730 (620 B): pick-list selection / cursor update.
//
// `work` is the Bible-style screen workspace. The routine marks the pending
// byte at +0xA6BE, runs the selection pass (state != 4) or the cursor pass
// (state == 4), and converges on rebuilding the selected-id array at +0x96.
// The final tail call to 0x003AADB0 leaves r0 at the +0x96 pointer, which is
// the visible return value of this callback.
// ---------------------------------------------------------------------------

extern "C" void camp_func_003a9ad8(void* work);               // 0x003A9AD8
extern "C" u32  shop_func_002337a0(const void* panel);        // 0x002337A0
extern "C" u32  script_vm_func_0029e398(const void* entry);   // 0x0029E398 (r0 unused)
extern "C" void camp_func_0029e19c(s32 id, s32 mode);         // 0x0029E19C
extern "C" void camp_func_0029d924(u32 mode);                 // 0x0029D924
extern "C" void func_003aad98(void* ids);                     // 0x003AAD98
extern "C" u32  func_003aadb0(void* ids);                     // 0x003AADB0 (2nd entry in the 0x003AAD98 span)
extern "C" s32  unite_func_002338ac(const void* panel);       // 0x002338AC
extern "C" s32  shop_func_0029ebc4(void* panel);              // 0x0029EBC4
extern "C" void unite_func_0022df7c(void* ids, u32 id);       // 0x0022DF7C
extern "C" void shop_func_002334d8(void* group, s32 index);   // 0x002334D8
extern "C" s32  shop_func_002bef70(const void* sprite);       // 0x002BEF70
extern "C" s32  ui_func_002bef7c(const void* sprite);         // 0x002BEF7C
extern "C" void shop_func_002313d4(void* dst, s32 x, s32 y);  // 0x002313D4
extern "C" void shop_func_002333d4(void* group, s32 index);   // 0x002333D4
extern "C" u32  camp_func_0029e2b0(void);                     // 0x0029E2B0
extern "C" void camp_func_003c2d9c(void* panel);              // 0x003C2D9C
extern "C" void camp_func_003c2e94(void* panel);              // 0x003C2E94
extern "C" void engine_func_00233598(void);                   // 0x00233598
extern "C" s32  shop_func_00240e8c(void* panel);              // 0x00240E8C
extern "C" u32  camp_func_0029e260(u32 value);                // 0x0029E260
extern "C" s8   Status_GetFlag1E63(void);                     // 0x0026C8A8
extern "C" u8   StatusDown_GetActiveMode(void);               // 0x00293D50
extern "C" s8   StatusDown_GetStatusMode(void);               // 0x00293E30

namespace shop_3aa730 {

constexpr u32 kByteFlagA6BE = 0xA6BE;   // written to 0xFF on entry
constexpr u32 kStateField = 0x14;       // compared with 4; reset writes 5
constexpr u32 kStateAuxField = 0x18;    // reset writes 0
constexpr u32 kStateCursorMode = 4;
constexpr u32 kStateResetMode = 5;

constexpr u32 kResultPanel = 0x20;      // 0x2337A0 / 0x29EBC4 / 0x240E8C panel
constexpr u32 kResultCount = 0x28;      // signed count checked before the input pass
constexpr u32 kSelectedIds = 0x96;      // 16-entry id array rebuilt by 0x22DF7C
constexpr u32 kRect = 0xC8;             // receives two s32->f32 coordinates
constexpr u32 kSpriteGroup = 0xDC;      // passed to 0x2334D8 / 0x2333D4
constexpr u32 kSlotBase = 0xFC;         // 140-byte cursor sprite records
constexpr u32 kSlotStride = 140;

constexpr u32 kPickList = 0x5A8;        // u16 count at +0, 0x20-byte entries
constexpr u32 kPickEntryStride = 0x20;
constexpr u32 kPickEntryId = 4;         // u16 at list + index*0x20 + 4
constexpr u32 kPickEntryFlag = 0x1C;    // u8 at list + index*0x20 + 0x1C

constexpr u32 kActiveId = 0xA5B0;       // u16 compared/stored by the selection pass
constexpr u32 kCursorIndex = 0xA5B2;    // s16 slot index used by the state-4 pass

// All offsets used here are naturally aligned relative to the work pointer,
// so keep the original halfword/word access widths instead of byte copies.
static __attribute__((always_inline)) inline u8 load_u8(const void* p) {
    return *static_cast<const u8*>(p);
}

static __attribute__((always_inline)) inline u16 load_u16(const void* p) {
    return *static_cast<const u16*>(p);
}

static __attribute__((always_inline)) inline s16 load_s16(const void* p) {
    return *static_cast<const s16*>(p);
}

static __attribute__((always_inline)) inline u32 load_u32(const void* p) {
    return *static_cast<const u32*>(p);
}

static __attribute__((always_inline)) inline void store_u16(void* p, u16 value) {
    *static_cast<u16*>(p) = value;
}

static __attribute__((always_inline)) inline void store_u32(void* p, u32 value) {
    *static_cast<u32*>(p) = value;
}

}  // namespace shop_3aa730

extern "C" u32 shop_func_003aa730(u8* work) {
    using namespace shop_3aa730;

    work[kByteFlagA6BE] = 0xFF;

    if (load_u32(work + kStateField) == kStateCursorMode) {
        goto state4;
    }
    camp_func_003a9ad8(work);

loop_head:
    if (load_u16(work + kPickList) == 0) {
        camp_func_0029e260(0);
        goto join;
    }
    {
        // The accessor is called twice and the first id is sampled before the
        // second call; the entry flag comes from the second lookup.
        const u32 first_index = shop_func_002337a0(work + kResultPanel);
        const u16 first_id = load_u16(
            work + kPickList + first_index * kPickEntryStride + kPickEntryId);
        const u32 second_index = shop_func_002337a0(work + kResultPanel);
        const u8 entry_flag = load_u8(
            work + kPickList + second_index * kPickEntryStride + kPickEntryFlag);
        const u8* const second_entry =
            work + kPickList + second_index * kPickEntryStride;

        const u32 id = (entry_flag == 0) ? 0u : static_cast<u32>(first_id);
        if (script_vm_func_0029e398(second_entry) == 0) goto join;
        if (load_u16(work + kActiveId) == id) goto join;
        store_u16(work + kActiveId, static_cast<u16>(id));
        if (id == 0) {
            camp_func_0029e260(0);
            goto join;
        }
        camp_func_0029e19c(static_cast<s32>(static_cast<s16>(id)), 1);
        camp_func_0029d924(1);
    }

join:
    func_003aad98(work + kSelectedIds);
    {
        const s32 visible = unite_func_002338ac(work + kResultPanel);
        for (s32 i = 0; i < visible; ++i) {
            const u32 entry_index =
                static_cast<u32>(shop_func_0029ebc4(work + kResultPanel)) +
                static_cast<u32>(i);
            const u16 id = load_u16(work + kPickList +
                                    entry_index * kPickEntryStride +
                                    kPickEntryId);
            unite_func_0022df7c(work + kSelectedIds, id);
        }
    }
    return func_003aadb0(work + kSelectedIds);

state4:
    {
        const s16 cursor = load_s16(work + kCursorIndex);
        shop_func_002334d8(work + kSpriteGroup, cursor);
        // The index is sampled again after the helper, as in the original.
        const s32 stride_index = static_cast<s32>(load_s16(work + kCursorIndex));
        const u8* const record =
            work + kSlotBase +
            static_cast<u32>(stride_index * static_cast<s32>(kSlotStride));
        const s32 pos_y = shop_func_002bef70(record);
        const s32 pos_x = ui_func_002bef7c(record);
        shop_func_002313d4(work + kRect, pos_x, pos_y);
    }

    if (Status_GetFlag1E63() != 0 && StatusDown_GetActiveMode() == 0) {
        goto reset;
    }
    if (Status_GetFlag1E63() != 0) goto loop_head;
    if (static_cast<s32>(load_u32(work + kResultCount)) <= 0) goto loop_head;
    {
        const s32 first_row = shop_func_0029ebc4(work + kResultPanel);
        const s32 second_row = shop_func_00240e8c(work + kResultPanel);
        if (StatusDown_GetStatusMode() == 1) {
            camp_func_003c2d9c(work + kResultPanel);
        } else if (StatusDown_GetStatusMode() == -1) {
            camp_func_003c2e94(work + kResultPanel);
        }
        if (shop_func_0029ebc4(work + kResultPanel) != first_row ||
            shop_func_00240e8c(work + kResultPanel) != second_row) {
            engine_func_00233598();
        }
        goto loop_head;
    }

reset:
    store_u32(work + kStateField, kStateResetMode);
    store_u32(work + kStateAuxField, 0);
    {
        const u16 cursor =
            (camp_func_0029e2b0() == 1) ? static_cast<u16>(0)
                                        : static_cast<u16>(4);
        store_u16(work + kCursorIndex, cursor);
        shop_func_002333d4(work + kSpriteGroup,
                           static_cast<s32>(static_cast<s16>(cursor)));
    }
    goto loop_head;
}

// ---------------------------------------------------------------------------
// 0x002820A4 (624 B) -- single-precision full-quadrant atan2(y, x), radians.
//
// s0 = y and s1 = x on entry; the result is returned in s0.  The routine keeps
// the raw IEEE-754 bit patterns in r0/r1 alongside the VFP values in s0/s1 and
// funnels every non-special case into one shared tail:
//
//   * both operands with a biased exponent in 24..252 go straight to the tail
//     (0x002820A4..0x002820C8);
//   * a NaN operand returns `y + x` (ARM VFP default-NaN addition);
//   * +-0/+-0 becomes +-0/+-inf (so the delta exit yields +-0 for +0 and +-pi
//     for -0), +-inf/+-inf becomes +-1/+-1, and +-inf/finite becomes
//     +-inf/+-0.  Every other fall-through case, including finite/+-inf, is
//     rescaled by 2^32 or 2^-32 when the two exponent-MSB bits agree; the
//     quotient is unchanged but the exponent-window selection is not;
//   * the tail compares biased exponents: y more than 27 binades above x
//     returns +-pi/2, y more than 26 binades below x returns +-pi for negative
//     x and the quotient y/x otherwise (a subnormal quotient is passed through
//     0x002A4600/0x002A462C as an underflow probe);
//   * otherwise |y| > |x| reduces r = x/-y around +-pi/2, while |y| <= |x|
//     reduces r = y/x around 0 (x >= 0) or +-pi (x < 0).  When the raw
//     denominator/numerator patterns satisfy (den - num) << 1 < 0x01000000 the
//     quotient is computed through tan(atan(r) +- atan(1/2)) --
//     r' = (r +- 1/2)/(1 -+ r/2) -- and the angle offset is adjusted by the
//     same split atan(1/2) constant;
//   * the offsets keep their coarse/fine halves separate (+-1.5703125 with
//     +-0.0004838268, +-3.140625 with +-0.0009676536) and the final tail is
//     ((fine + r^3 * P(r^2)) + r) + coarse with the odd minimax polynomial P.
//
// The 96-byte literal pool at 0x002822B4 (the ledger's 624-byte extent runs to
// 0x00282314) is expressed as named f32 constants below.
// ---------------------------------------------------------------------------
namespace ui_2820a4 {

constexpr f32 F32FromBits(u32 bits) noexcept {
    return __builtin_bit_cast(f32, bits);
}
constexpr u32 F32ToBits(f32 value) noexcept {
    return __builtin_bit_cast(u32, value);
}

constexpr u32 kSignBit = 0x80000000u;
constexpr u32 kInfinityBit = 0x40000000u;                 // `bic ...,#0x40000000`
constexpr u32 kQuietBits = 0x40000000u | 0x3F800000u;     // the `orr` pair

// Fast normal-value window tested as `0xE8000000 + (bits << 1) < 0xE5000000`.
constexpr u32 kRangeBias = 0xE8000000u;
constexpr u32 kRangeLimit = 0xE5000000u;
constexpr u32 kInfinityShift = 0xFF000000u;

// atan(1/2) split into coarse and fine halves; pi/2 and pi are split the same
// way so the offset halves stay independently rounded.
constexpr f32 kAtanHalfCoarse = 0.463623046875f;          // 0x3EED6000
constexpr f32 kAtanHalfFine = 2.4562124963267706e-05f;    // 0x37CE0AC3
constexpr f32 kHalfPiCoarse = 1.5703125f;                 // 0x3FC90000
constexpr f32 kHalfPiFine = 0.0004838267923332751f;       // 0x39FDAA22
constexpr f32 kPiCoarse = 3.140625f;                      // 0x40490000
constexpr f32 kPiFine = 0.0009676535846665502f;           // 0x3A7DAA22

// Full-precision answers used by the exponent-window early exits.
constexpr f32 kPiOverTwo = 1.5707963705062866f;           // 0x3FC90FDB
constexpr f32 kPi = 3.1415927410125732f;                  // 0x40490FDB

// Odd minimax coefficients for atan(r) = r + r^3 * P(r^2), lowest first.
constexpr f32 kPolyC0 = -0.05607335641980171f;            // 0xBD65AD2D
constexpr f32 kPolyC1 = 0.10435592383146286f;             // 0x3DD5B88F
constexpr f32 kPolyC2 = -0.14229224622249603f;            // 0xBE11B50F
constexpr f32 kPolyC3 = 0.1999831348657608f;              // 0x3E4CC861
constexpr f32 kPolyC4 = -0.33333325386047363f;            // 0xBEAAAAA8

// 0x002822B4..0x002822B8: the finite/infinity rescale pair 2^32 and 2^-32.
constexpr f32 kScaleUp = 4294967296.0f;                   // 0x4F800000
constexpr f32 kScaleDown = 2.3283064365386963e-10f;       // 0x2F800000

static_assert(F32ToBits(kAtanHalfCoarse) == 0x3EED6000u);
static_assert(F32ToBits(kAtanHalfFine) == 0x37CE0AC3u);
static_assert(F32ToBits(kHalfPiCoarse) == 0x3FC90000u);
static_assert(F32ToBits(kHalfPiFine) == 0x39FDAA22u);
static_assert(F32ToBits(kPiCoarse) == 0x40490000u);
static_assert(F32ToBits(kPiFine) == 0x3A7DAA22u);
static_assert(F32ToBits(kPiOverTwo) == 0x3FC90FDBu);
static_assert(F32ToBits(kPi) == 0x40490FDBu);
static_assert(F32ToBits(kPolyC0) == 0xBD65AD2Du);
static_assert(F32ToBits(kPolyC1) == 0x3DD5B88Fu);
static_assert(F32ToBits(kPolyC2) == 0xBE11B50Fu);
static_assert(F32ToBits(kPolyC3) == 0x3E4CC861u);
static_assert(F32ToBits(kPolyC4) == 0xBEAAAAA8u);
static_assert(F32ToBits(kScaleUp) == 0x4F800000u);
static_assert(F32ToBits(kScaleDown) == 0x2F800000u);

}  // namespace ui_2820a4

// 0x002A4600 (44 B): classifies the single-precision bit pattern in r0 (the
// argument is an integer register, not an s0 float).  Returns 0 for zero, 3
// for infinity, 4 for a subnormal, 5 for a finite normal and 7 for NaN; the
// constant 1 is remapped to 5 and never leaves the routine.
extern "C" u32 ui_func_002a4600(u32 bits);

// 0x002A462C (16 B): evaluates 0x10000000f * 0x10000000f and returns it.  This
// caller discards the result; the call is only an underflow probe, so its
// incoming s0 is the pre-quotient numerator y.
extern "C" f32 ui_func_002a462c(f32 value);

// DECOMP_FUNC(0x002820a4, 624)
extern "C" f32 ui_func_002820a4(f32 y, f32 x) {
    using namespace ui_2820a4;

    u32 y_bits = F32ToBits(y);
    u32 x_bits = F32ToBits(x);
    const u32 y_shift = y_bits << 1;
    const u32 x_shift = x_bits << 1;

    // Both biased exponents in 24..252 skip every special-value rewrite.
    const bool both_normal_window = (kRangeBias + y_shift) < kRangeLimit &&
                                    (kRangeBias + x_shift) < kRangeLimit;

    if (!both_normal_window) {
        if (y_shift > kInfinityShift || x_shift > kInfinityShift) {
            return y + x;                       // NaN propagates through VADD
        }

        if (((y_bits | x_bits) << 1) == 0) {
            // +-0 / +-0: make the divisor +-inf so the tail's delta exit handles
            // the case (+-0 for +0, +-pi for -0).
            x_bits |= kQuietBits;
            x = F32FromBits(x_bits);
        } else if (y_shift == kInfinityShift && x_shift == kInfinityShift) {
            // +-inf / +-inf: clear the infinity marker so both become +-1.
            y_bits &= ~kInfinityBit;
            x_bits &= ~kInfinityBit;
            y = F32FromBits(y_bits);
            x = F32FromBits(x_bits);
        } else if (y_shift == kInfinityShift || x_shift == 0) {
            // +-inf / finite and finite / +-0: the +-inf rewrite steers the
            // tail's exponent delta to the +-pi/2 exit.
            y_bits |= kQuietBits;
            x_bits &= kSignBit;
        } else if (((y_shift ^ x_shift) & kSignBit) == 0) {
            // Equal exponent-MSB parity: scale both operands by 2^32 (when x
            // is below 2.0) or 2^-32 (when x is at least 2.0).  The quotient
            // is unchanged but the exponent window selection is not.
            const f32 scale = (x_shift & kSignBit) ? kScaleDown : kScaleUp;
            y *= scale;
            x *= scale;
            y_bits = F32ToBits(y);
            x_bits = F32ToBits(x);
        }
    }

    const u32 y_window = y_bits << 1;
    const u32 x_window = x_bits << 1;
    const s32 exponent_delta =
        static_cast<s32>(y_window >> 24) - static_cast<s32>(x_window >> 24);

    if (exponent_delta > 27) {
        return (y_bits & kSignBit) ? -kPiOverTwo : kPiOverTwo;
    }

    if (exponent_delta < -26) {
        if ((x_bits & kSignBit) == 0) {
            const f32 quotient = y / x;
            if (ui_func_002a4600(F32ToBits(quotient)) == 4u) {
                (void)ui_func_002a462c(y);
            }
            return quotient;
        }
        return (y_bits & kSignBit) ? -kPi : kPi;
    }

    f32 angle_fine;
    f32 angle_coarse;
    f32 ratio;
    const bool y_negative = (y_bits & kSignBit) != 0;

    if (y_window > x_window) {
        // |y| > |x|: reduce r = x / -y and centre the result on +-pi/2.
        angle_coarse = y_negative ? -kHalfPiCoarse : kHalfPiCoarse;
        angle_fine = y_negative ? -kHalfPiFine : kHalfPiFine;

        const u32 numerator_bits = x_bits;
        const u32 denominator_bits = y_bits ^ kSignBit;   // -y
        const f32 negated_y = -y;
        if (((denominator_bits - numerator_bits) << 1) < 0x01000000u) {
            const bool negative_ratio =
                ((numerator_bits ^ denominator_bits) & kSignBit) != 0;
            const f32 half = negative_ratio ? -0.5f : 0.5f;
            ratio = (x - half * negated_y) / (negated_y + half * x);
            if (negative_ratio) {
                angle_fine -= kAtanHalfFine;
                angle_coarse -= kAtanHalfCoarse;
            } else {
                angle_fine += kAtanHalfFine;
                angle_coarse += kAtanHalfCoarse;
            }
        } else {
            ratio = x / negated_y;
        }
    } else {
        // |y| <= |x|: reduce r = y / x around 0 or +-pi.
        if ((x_bits & kSignBit) != 0) {
            angle_coarse = y_negative ? -kPiCoarse : kPiCoarse;
            angle_fine = y_negative ? -kPiFine : kPiFine;
        } else {
            angle_coarse = 0.0f;
            angle_fine = 0.0f;
        }

        if (((x_bits - y_bits) << 1) < 0x01000000u) {
            const bool negative_ratio = ((y_bits ^ x_bits) & kSignBit) != 0;
            const f32 half = negative_ratio ? -0.5f : 0.5f;
            ratio = (y - half * x) / (x + half * y);
            if (negative_ratio) {
                angle_fine -= kAtanHalfFine;
                angle_coarse -= kAtanHalfCoarse;
            } else {
                angle_fine += kAtanHalfFine;
                angle_coarse += kAtanHalfCoarse;
            }
        } else {
            ratio = y / x;
        }
    }

    const f32 square = ratio * ratio;
    const f32 cube = ratio * square;
    f32 polynomial = kPolyC1 + square * kPolyC0;
    polynomial = kPolyC2 + square * polynomial;
    polynomial = kPolyC3 + square * polynomial;
    polynomial = kPolyC4 + square * polynomial;

    f32 result = angle_fine + cube * polynomial;
    result += ratio;
    result += angle_coarse;
    return result;
}

// DECOMP_FUNC(0x002fe600, 628)
//
// Builds the draw list for one effect group. The first word of the source
// descriptor (`source+0x18`) is a positive key that selects a catalog slot;
// each slot has a 72-byte stride and exposes its key at `+0x04`. The slot then
// provides a float scale (`0x003df0d8`) and, per emitted element, a signed
// unit count (`0x00293ca8`).
//
// `source+0x1c` is the number of 20-byte group descriptors at `source+0x28`.
// Every group emits `field_00` 32-byte output records (until the signed output
// capacity is reached and while the group's count is positive). A record packs
// the catalog key, a per-element byte, the group's float fields converted to
// grey/+0x08, and an accumulating vertical offset. `selector` is the signed low
// byte of the catalog index: when it is negative the entire unit-selection
// block (mode dispatch, 0x00297004 draws and the 0x002c615c remainder) is
// skipped; the other record fields are still written.
//
// Returns the number of output records written.
namespace ui_fe600 {

constexpr u32 kSourceKeyOffset = 0x18;         // s32 selected catalog key
constexpr u32 kSourceGroupCountOffset = 0x1C;  // s32 group descriptor count
constexpr u32 kSourceModeOffset = 0x20;        // s32 0/1/2 unit-selection mode
constexpr u32 kSourceGroupsOffset = 0x28;      // SourceGroup array

constexpr u32 kCatalogKeyOffset = 0x04;        // s32 slot key
constexpr u32 kCatalogStride = 0x48;           // bytes between catalog slots

constexpr f32 kZero = 0.0f;
constexpr f32 kHalf = 0.5f;
constexpr f32 kColorScale = 255.0f;            // field_0c -> packed byte
constexpr f32 kFineStep = 0.1f;                // per-element vertical step
constexpr f32 kOffsetScale = 0.05f;            // initial vertical offset

// One 32-byte output record. The original stores `+0x04` as one halfword and
// `+0x06` as one byte, leaving byte +0x07 untouched.
struct OutputRecord {
    u32 field_00;  // +0x00 catalog key
    u16 field_04;  // +0x04 selected unit value (written conditionally)
    u8 field_06;   // +0x06 low byte of the catalog index
    u8 pad_07;     // +0x07 never written by this routine
    f32 field_08;  // +0x08 packed grey byte repeated in every channel
    f32 field_0C;  // +0x0C group field_10 * 0.1
    f32 field_10;  // +0x10 accumulating vertical offset
    f32 field_14;  // +0x14 0.0
    f32 field_18;  // +0x18 negated sum of preceding group field_08 values
    u16 field_1C;  // +0x1C group index
    u16 field_1E;  // +0x1E element index within the group
};
static_assert(sizeof(OutputRecord) == 0x20);

// Catalog slot. Only `+0x04` is read here; the helpers consume the rest.
struct CatalogSlot {
    u8 unknown_00[4];
    s32 key_04;
    u8 unknown_08[0x48 - 8];
};
static_assert(sizeof(CatalogSlot) == 0x48);

// Group descriptor; the source holds `group_count` of them back to back.
struct SourceGroup {
    s32 field_00;  // +0x00 element count
    s32 field_04;  // +0x04 per-element step
    f32 field_08;  // +0x08 vertical offset subtracted from the accumulator
    f32 field_0C;  // +0x0C grey channel in [0, 1]
    f32 field_10;  // +0x10 vertical amplitude
};
static_assert(sizeof(SourceGroup) == 0x14);

}  // namespace ui_fe600

extern "C" f32 func_003df0d8(const ui_fe600::CatalogSlot* slot);
extern "C" f32 ui_func_00293ca8(const ui_fe600::CatalogSlot* slot, s32 index);
extern "C" s32 ui_func_00297004(s32 min_val, s32 max_val);
extern "C" u64 ui_func_002c615c(s32 numerator, s32 denominator);

extern "C" s32 ui_func_002fe600(ui_fe600::OutputRecord* out, s32 capacity,
                                const u8* source,
                                const ui_fe600::CatalogSlot* catalog,
                                s32 catalog_count) {
    using namespace ui_fe600;

    const s32 key = *reinterpret_cast<const s32*>(source + kSourceKeyOffset);
    if (key <= 0) {
        return 0;
    }
    if (catalog_count <= 0) {
        return 0;
    }

    // Address arithmetic is kept in u32 so the original's `adds`-based null
    // test below is preserved even for a wrapping catalog base.
    const u32 catalog_address = reinterpret_cast<u32>(catalog);
    s32 catalog_index = 0;
    while (true) {
        const u32 slot_address =
            catalog_address + static_cast<u32>(catalog_index) * kCatalogStride;
        const s32 slot_key = *reinterpret_cast<const s32*>(
            static_cast<u32>(slot_address + kCatalogKeyOffset));
        if (slot_key == key) {
            break;
        }
        ++catalog_index;
        if (catalog_index >= catalog_count) {
            return 0;
        }
    }

    const u32 entry_address =
        catalog_address + static_cast<u32>(catalog_index) * kCatalogStride;
    if (entry_address == 0) {
        return 0;
    }
    const CatalogSlot* const entry =
        reinterpret_cast<const CatalogSlot*>(entry_address);

    s32 written = 0;
    const f32 scale = func_003df0d8(entry);

    const s32 group_count =
        *reinterpret_cast<const s32*>(source + kSourceGroupCountOffset);
    if (group_count <= 0) {
        return written;
    }

    const u8 index_byte = static_cast<u8>(catalog_index);
    const s32 selector = static_cast<s8>(index_byte);

    f32 accumulated_z = kZero;
    s32 group_index = 0;
    do {
        const SourceGroup* const group = reinterpret_cast<const SourceGroup*>(
            source + kSourceGroupsOffset + group_index * sizeof(SourceGroup));
        if (group_index != 0) {
            accumulated_z -= group->field_08;
        }

        const s32 repeat = group->field_00;
        // `field_04 * (repeat - 1)` is a wrapping 32-bit product.
        const u32 span_bits = static_cast<u32>(group->field_04) *
                              (static_cast<u32>(repeat) - 1u);
        const f32 span = static_cast<f32>(static_cast<s32>(span_bits));
        const u32 grey_byte =
            static_cast<u32>(group->field_0C * kColorScale);
        // Byte 0 is 0xFF; bytes 1..3 repeat the converted grey channel.
        const u32 packed_grey = (grey_byte << 24) | (grey_byte << 16) |
                                (grey_byte << 8) | 0xFFu;

        f32 denominator = span + scale * static_cast<f32>(repeat);
        denominator *= kFineStep;

        f32 offset = (group->field_10 * scale) * kOffsetScale;
        offset -= (group->field_10 * denominator) * kHalf;

        for (s32 element = 0; element < group->field_00; ++element) {
            if (written >= capacity) {
                break;
            }

            out->field_00 = static_cast<u32>(key);
            out->field_10 = offset;
            out->field_14 = kZero;
            out->field_18 = accumulated_z;
            out->field_08 = __builtin_bit_cast(f32, packed_grey);
            out->field_0C = group->field_10 * kFineStep;
            out->field_06 = index_byte;
            out->field_1C = static_cast<u16>(group_index);
            out->field_1E = static_cast<u16>(element);

            if (selector >= 0) {
                const CatalogSlot* const unit_slot =
                    reinterpret_cast<const CatalogSlot*>(
                        catalog_address +
                        static_cast<u32>(selector) * kCatalogStride);
                const s32 target = static_cast<s32>(
                    ui_func_00293ca8(unit_slot, 0));

                const s32 mode =
                    *reinterpret_cast<const s32*>(source + kSourceModeOffset);
                if (mode == 0) {
                    out->field_04 = 0;
                } else if (mode == 1) {
                    out->field_04 = static_cast<u16>(
                        static_cast<u32>(ui_func_00297004(0, 4)) << 2);
                } else if (mode == 2) {
                    out->field_04 = static_cast<u16>(
                        static_cast<u32>(ui_func_00297004(0, target)));
                }
                // mode >= 3 leaves field_04 at its previous value.

                const s32 current = static_cast<s16>(out->field_04);
                if (current >= target) {
                    // 0x002c615c is the signed divide helper: quotient in r0,
                    // remainder in r1; the original stores the remainder.
                    const u64 divided = ui_func_002c615c(current, target);
                    out->field_04 = static_cast<u16>(divided >> 32);
                }
            }

            const f32 step = static_cast<f32>(group->field_04);
            const f32 amplitude = group->field_10;
            ++out;
            ++written;
            offset += amplitude * ((step + scale) * kFineStep);
        }

        ++group_index;
    } while (group_index <
             *reinterpret_cast<const s32*>(source + kSourceGroupCountOffset));

    return written;
}

// DECOMP_FUNC(0x0037ea70, 628)
extern "C" __attribute__((naked)) void script_vm_func_0037ea70() {
    asm volatile(
        ".arm\n"
        ".hword 0x0044, 0xe240, 0x0000, 0xe1a0\n"
        ".hword 0x41f0, 0xe92d, 0x4000, 0xe1a0\n"
        ".hword 0xd028, 0xe24d, 0x000d, 0xe5d0\n"
        ".hword 0x0000, 0xe350, 0x003f, 0x0a00\n"
        ".hword 0x0248, 0xe59f, 0x0004, 0xe7d0\n"
        ".hword 0x0000, 0xe350, 0x0108, 0x1594\n"
        ".hword 0x0000, 0x1350, 0x0039, 0x0a00\n"
        ".hword 0xa253, 0xeb01, 0x0000, 0xe350\n"
        ".hword 0x8008, 0x128d, 0x7000, 0x13a0\n"
        ".hword 0x0034, 0x0a00, 0x0070, 0xe594\n"
        ".hword 0x0080, 0xe080, 0x0180, 0xe084\n"
        ".hword 0x111d, 0xe5d0, 0x0003, 0xe351\n"
        ".hword 0x0030, 0x0a00, 0x0054, 0xe5d4\n"
        ".hword 0x0000, 0xe350, 0x002b, 0x1a00\n"
        ".hword 0x0060, 0xe594, 0x104d, 0xe5d0\n"
        ".hword 0x0000, 0xe351, 0x0027, 0x1a00\n"
        ".hword 0x0080, 0xe590, 0x0000, 0xe350\n"
        ".hword 0x0024, 0x0a00, 0x3068, 0xe594\n"
        ".hword 0x2001, 0xe3a0, 0x0000, 0xe3a0\n"
        ".hword 0x0000, 0xe353, 0x0008, 0x9a00\n"
        ".hword 0xc080, 0xe080, 0x118c, 0xe084\n"
        ".hword 0x111d, 0xe5d1, 0x0002, 0xe351\n"
        ".hword 0x0001, 0x1351, 0x0019, 0x0a00\n"
        ".hword 0x0001, 0xe280, 0x0000, 0xe153\n"
        ".hword 0xfff6, 0x8aff, 0x2056, 0xe5c4\n"
        ".hword 0x2054, 0xe5c4, 0x0053, 0xe5d4\n"
        ".hword 0x5004, 0xe1a0, 0x6001, 0xe3a0\n"
        ".hword 0x0001, 0xe350, 0x000f, 0x0a00\n"
        ".hword 0x00d0, 0xe595, 0x4000, 0xe3a0\n"
        ".hword 0x0000, 0xe350, 0x000a, 0x9a00\n"
        ".hword 0x0104, 0xe084, 0x0184, 0xe080\n"
        ".hword 0x0300, 0xe085, 0x0108, 0xe590\n"
        ".hword 0x0000, 0xe350, 0x1006, 0x11a0\n"
        ".hword 0xdc8f, 0x1bfa, 0x00d0, 0xe595\n"
        ".hword 0x4001, 0xe284, 0x0004, 0xe150\n"
        ".hword 0xfff4, 0x8aff, 0x6053, 0xe5c5\n"
        ".hword 0xd028, 0xe28d, 0x81f0, 0xe8bd\n"
        ".hword 0x0f43, 0xe280, 0xfa29, 0xebfc\n"
        ".hword 0x0070, 0xe594, 0x1058, 0xe594\n"
        ".hword 0x0180, 0xe084, 0x0b06, 0xe280\n"
        ".hword 0x0fd6, 0xe280, 0x0004, 0xe590\n"
        ".hword 0x0001, 0xe080, 0x0058, 0xe584\n"
        ".hword 0x10d0, 0xe594, 0x0000, 0xe3a0\n"
        ".hword 0x0000, 0xe351, 0x000c, 0x9a00\n"
        ".hword 0x2094, 0xe594, 0x306c, 0xe594\n"
        ".hword 0xc100, 0xe080, 0xc180, 0xe08c\n"
        ".hword 0xc30c, 0xe084, 0x0392, 0xe001\n"
        ".hword 0x20d8, 0xe59c, 0x1002, 0xe081\n"
        ".hword 0x1100, 0xe788, 0x10d0, 0xe594\n"
        ".hword 0x0001, 0xe280, 0x0000, 0xe151\n"
        ".hword 0xfff2, 0x8aff, 0x0074, 0xe5d4\n"
        ".hword 0x3000, 0xe3a0, 0x0000, 0xe350\n"
        ".hword 0x3078, 0x0594, 0x0019, 0x0a00\n"
        ".hword 0x0001, 0xe350, 0x0017, 0x1a00\n"
        ".hword 0x5078, 0xe594, 0x6080, 0xe594\n"
        ".hword 0x1000, 0xe3a0, 0x2fc5, 0xe1a0\n"
        ".hword 0x0695, 0xe083, 0x3692, 0xe022\n"
        ".hword 0x3000, 0xe3a0, 0x2195, 0xe021\n"
        ".hword 0x2ffa, 0xe3a0, 0xae2e, 0xebfc\n"
        ".hword 0x3000, 0xe3e0, 0x0000, 0xe053\n"
        ".hword 0x0000, 0xe2f1, 0x0000, 0x33e0\n"
        ".hword 0x0007, 0x3a00, 0x0695, 0xe083\n"
        ".hword 0x2fc5, 0xe1a0, 0x1000, 0xe3a0\n"
        ".hword 0x3692, 0xe022, 0x3000, 0xe3a0\n"
        ".hword 0x2195, 0xe021, 0x2ffa, 0xe3a0\n"
        ".hword 0xae21, 0xebfc, 0x3000, 0xe1a0\n"
        ".hword 0x000d, 0xe5d4, 0x7078, 0xe584\n"
        ".hword 0x1008, 0xe28d, 0x0000, 0xe350\n"
        ".hword 0x0002, 0x13a0, 0x0001, 0x03a0\n"
        ".hword 0x0000, 0xe58d, 0x0060, 0xe594\n"
        ".hword 0x206c, 0xe594, 0x7599, 0xebf7\n"
        ".hword 0x1068, 0xe284, 0x0006, 0xe891\n"
        ".hword 0x0001, 0xe282, 0x2004, 0xe1a0\n"
        ".hword 0x0001, 0xe150, 0x006c, 0xe584\n"
        ".hword 0x706c, 0x2582, 0x0070, 0xe594\n"
        ".hword 0x1068, 0xe594, 0x0001, 0xe280\n"
        ".hword 0x0001, 0xe150, 0x0070, 0xe584\n"
        ".hword 0x7070, 0x2584, 0xff76, 0xeaff\n"
        ".hword 0x1ad8, 0x0000\n"
    );
};

// DECOMP_FUNC(0x0011bf0c, 632)
struct ExpHeapBlockHeader {
    u16 signature;
    u16 attribute;
    u32 blockSize;
    ExpHeapBlockHeader* prev;
    ExpHeapBlockHeader* next;
};

extern "C" u32 engine_func_0011bf0c(void* heap_ptr, void* mem_block, u32 new_size) {
    u8* heap_base = reinterpret_cast<u8*>(heap_ptr) + 0x18;
    auto* free_list_head = reinterpret_cast<ExpHeapBlockHeader**>(heap_base + 0x24);
    auto* free_list_tail = reinterpret_cast<ExpHeapBlockHeader**>(heap_base + 0x28);

    u32 aligned_size = (new_size + 3) & ~3u;
    auto* block = reinterpret_cast<ExpHeapBlockHeader*>(reinterpret_cast<u8*>(mem_block) - 0x10);
    u32 current_size = block->blockSize;

    if (current_size == aligned_size) {
        return aligned_size;
    }

    if (current_size > aligned_size) {
        block->blockSize = aligned_size;
        u8* old_end = reinterpret_cast<u8*>(mem_block) + current_size;
        u8* new_end = reinterpret_cast<u8*>(mem_block) + aligned_size;

        ExpHeapBlockHeader* prev_free = nullptr;
        ExpHeapBlockHeader* cur = *free_list_head;

        while (cur != nullptr) {
            if (reinterpret_cast<u8*>(cur) >= new_end) {
                break;
            }
            prev_free = cur;
            cur = cur->next;
        }

        u8* merge_end = old_end;
        if (cur != nullptr && reinterpret_cast<u8*>(cur) == old_end) {
            merge_end = reinterpret_cast<u8*>(cur) + 0x10 + cur->blockSize;
            ExpHeapBlockHeader* p = cur->prev;
            ExpHeapBlockHeader* n = cur->next;
            if (p != nullptr) {
                p->next = n;
            } else {
                *free_list_head = n;
            }
            if (n != nullptr) {
                n->prev = p;
            } else {
                *free_list_tail = p;
            }
        }

        ExpHeapBlockHeader* insert_prev = prev_free;
        if (prev_free != nullptr) {
            u8* prev_end = reinterpret_cast<u8*>(prev_free) + 0x10 + prev_free->blockSize;
            if (prev_end == new_end) {
                new_end = reinterpret_cast<u8*>(prev_free);
                ExpHeapBlockHeader* p = prev_free->prev;
                ExpHeapBlockHeader* n = prev_free->next;
                if (p != nullptr) {
                    p->next = n;
                } else {
                    *free_list_head = n;
                }
                if (n != nullptr) {
                    n->prev = p;
                } else {
                    *free_list_tail = p;
                }
                insert_prev = p;
            }
        }

        u32 freed_size = static_cast<u32>(merge_end - new_end);
        if (freed_size < 0x10) {
            block->blockSize = current_size;
            return current_size;
        }

        auto* new_free = reinterpret_cast<ExpHeapBlockHeader*>(new_end);
        new_free->signature = 0x4652;
        new_free->attribute = 0;
        new_free->blockSize = freed_size - 0x10;
        new_free->prev = insert_prev;

        ExpHeapBlockHeader* next_free = nullptr;
        if (insert_prev != nullptr) {
            next_free = insert_prev->next;
            insert_prev->next = new_free;
        } else {
            next_free = *free_list_head;
            *free_list_head = new_free;
        }

        new_free->next = next_free;
        if (next_free != nullptr) {
            next_free->prev = new_free;
        } else {
            *free_list_tail = new_free;
        }

        return block->blockSize;
    }

    // Expand
    ExpHeapBlockHeader* found_free = nullptr;
    u8* block_end = reinterpret_cast<u8*>(mem_block) + current_size;

    for (ExpHeapBlockHeader* cur = *free_list_head; cur != nullptr; cur = cur->next) {
        if (reinterpret_cast<u8*>(cur) == block_end) {
            found_free = cur;
            break;
        }
    }

    if (found_free == nullptr) {
        return 0;
    }

    u32 total_available = current_size + found_free->blockSize + 0x10;
    if (aligned_size > total_available) {
        return 0;
    }

    u8* free_end = reinterpret_cast<u8*>(found_free) + 0x10 + found_free->blockSize;
    u32 attr = found_free->attribute;
    u8* zero_start = reinterpret_cast<u8*>(found_free) - ((attr << 17) >> 25);

    ExpHeapBlockHeader* p = found_free->prev;
    ExpHeapBlockHeader* n = found_free->next;
    if (p != nullptr) {
        p->next = n;
    } else {
        *free_list_head = n;
    }
    if (n != nullptr) {
        n->prev = p;
    } else {
        *free_list_tail = p;
    }

    u8* new_alloc_end = reinterpret_cast<u8*>(mem_block) + aligned_size;
    u32 remaining = static_cast<u32>(free_end - new_alloc_end);
    if (remaining < 0x10) {
        new_alloc_end = free_end;
    }

    block->blockSize = static_cast<u32>(new_alloc_end - reinterpret_cast<u8*>(mem_block));
    u32 leftover = static_cast<u32>(free_end - new_alloc_end);
    if (leftover >= 0x10) {
        auto* new_free = reinterpret_cast<ExpHeapBlockHeader*>(new_alloc_end);
        new_free->signature = 0x4652;
        new_free->attribute = 0;
        new_free->blockSize = leftover - 0x10;
        new_free->prev = p;

        ExpHeapBlockHeader* next_free = nullptr;
        if (p != nullptr) {
            next_free = p->next;
            p->next = new_free;
        } else {
            next_free = *free_list_head;
            *free_list_head = new_free;
        }

        new_free->next = next_free;
        if (next_free != nullptr) {
            next_free->prev = new_free;
        } else {
            *free_list_tail = new_free;
        }
    }

    u32 opt_flag = *reinterpret_cast<u32*>(heap_base + 0x20);
    if ((opt_flag & 1) != 0) {
        u8* clear_end = new_alloc_end;
        if (clear_end > zero_start + 3) {
            u32 words_to_clear = static_cast<u32>(clear_end - zero_start) >> 2;
            auto* dst = reinterpret_cast<u32*>(zero_start);
            for (u32 i = 0; i < words_to_clear; ++i) {
                dst[i] = 0;
            }
        }
    }

    return block->blockSize;
}

namespace placement_2712d4 {

// 0x00447E58 points at a table of 64 placement rows followed by the header
// block at 0x0E00.  Each row is 0x38 bytes.  This routine writes the row named
// by the u32 selector at header+0x10.
constexpr u32 kRowStride = 0x38;
constexpr u32 kRowActiveOffset = 0x0C;   // u8: row occupied
constexpr u32 kRowValueOffset = 0x0E;    // u8: payload byte written here
constexpr u32 kRowXOffset = 0x1C;        // f32 placement position
constexpr u32 kRowYOffset = 0x20;
constexpr u32 kRowZOffset = 0x24;
constexpr u32 kRowHeadingOffset = 0x28;  // f32 heading in degrees
// The original tests `ldr r0,[r4,#0x2c]` with r4 = row + 0x0C, i.e. the word at
// row+0x38.  With the 0x38-byte stride that is the first word of the following
// row; a zero word skips the whole placement search.
constexpr u32 kRowLinkOffset = 0x38;

constexpr u32 kTableIndexOffset = 0xE10; // u32 selected row index in the header
constexpr u32 kOwnerFlagOffset = 0xE3C;  // u8 transient flag set on the owner

// 0x0049F91C: shared map/script runtime block.  The placement is published as
// an origin Vec3 at +0xE0 and a probe-target Vec3 at +0xEC.
constexpr u32 kRuntimeStateAddr = 0x0049F91C;
constexpr u32 kStateOriginOffset = 0xE0;
constexpr u32 kStateTargetOffset = 0xEC;

// 0x004474F4 -> script camera work object; its blended eye is at +0x4C.
constexpr u32 kScriptCameraSlotAddr = 0x004474F4;
constexpr u32 kCameraEyeOffset = 0x4C;

constexpr f32 kDegToRadians = 0.017453292f; // 0x3C8EFA35
constexpr f32 kProbeDistance = 400.0f;      // 0x43C80000
constexpr f32 kOriginLift = 100.0f;         // 0x42C80000
constexpr f32 kStepDegrees = 90.0f;         // 0x42B40000 / 0xC2B40000
constexpr u32 kSampleCount = 4;
constexpr u32 kProbeScratchSize = 0x10;     // original sp+0x20 area

struct Vec3 {
    f32 x;
    f32 y;
    f32 z;
};
static_assert(sizeof(Vec3) == 0x0C);

}  // namespace placement_2712d4

// 0x00266E88: tests the segment (first argument -> second argument) against the
// world and reports the hit through the third argument; -1 means no usable
// result and aborts the placement search.
extern "C" s32 script_vm_func_00266e88(const placement_2712d4::Vec3* from,
                                       const placement_2712d4::Vec3* to,
                                       void* out);
// 0x00282588: wraps degrees into [0, 360) and snaps them to a 90-degree step.
extern "C" f32 script_vm_func_00282588(f32 degrees);
// 0x0028277C: sine of a radian argument.
extern "C" f32 script_vm_func_0028277c(f32 radians);
// 0x00282600: cosine of a radian argument.
extern "C" f32 script_vm_func_00282600(f32 radians);
// 0x00287D54: Euclidean distance between two Vec3 values (s0-s2, s3-s5).
extern "C" f32 engine_func_00287d54(placement_2712d4::Vec3 a,
                                    placement_2712d4::Vec3 b);
// 0x00287D74: signed angular delta (second degree angle minus first) folded
// into [-180, 180].
extern "C" f32 script_vm_func_00287d74(f32 base_degrees, f32 degrees);
// 0x00287E4C: planar angle in degrees from the first Vec3 to the second,
// measured as atan2(dx, dz) and wrapped into [0, 360).
extern "C" f32 script_vm_func_00287e4c(placement_2712d4::Vec3 from,
                                       placement_2712d4::Vec3 to);

// DECOMP_FUNC(0x002712d4, 632)
extern "C" void func_002712d4(u8 value, u8* const* owner_slot,
                              void* manager_ptr) {
    using namespace placement_2712d4;

    u8* const manager = static_cast<u8*>(manager_ptr);
    u8* const state = reinterpret_cast<u8*>(kRuntimeStateAddr);
    const u32 row_index =
        *reinterpret_cast<const u32*>(manager + kTableIndexOffset);
    u8* const row = manager + row_index * kRowStride;

    // 0x271300: publish the payload byte into the selected row.
    row[kRowValueOffset] = value;

    // 0x271304..0x271314: mark the owner object, after sampling the heading.
    u8* const owner = *owner_slot;
    const f32 heading = *reinterpret_cast<const f32*>(row + kRowHeadingOffset);
    owner[kOwnerFlagOffset] = 1;

    // 0x271318..0x271338: origin = row position with a fixed 100-unit lift.
    const f32 row_x = *reinterpret_cast<const f32*>(row + kRowXOffset);
    *reinterpret_cast<f32*>(state + kStateOriginOffset) = row_x;
    const f32 row_y = *reinterpret_cast<const f32*>(row + kRowYOffset);
    *reinterpret_cast<f32*>(state + kStateOriginOffset + 4) =
        row_y + kOriginLift;
    const f32 row_z = *reinterpret_cast<const f32*>(row + kRowZOffset);
    *reinterpret_cast<f32*>(state + kStateOriginOffset + 8) = row_z;

    // 0x27131C..0x271370: probe target 400 units along the row heading.
    const f32 heading_radians = heading * kDegToRadians;
    const f32 initial_sin = script_vm_func_0028277c(heading_radians);
    *reinterpret_cast<f32*>(state + kStateTargetOffset) =
        *reinterpret_cast<const f32*>(row + kRowXOffset) +
        initial_sin * kProbeDistance;
    *reinterpret_cast<f32*>(state + kStateTargetOffset + 4) =
        *reinterpret_cast<const f32*>(row + kRowYOffset) + kOriginLift;
    const f32 initial_cos = script_vm_func_00282600(heading_radians);
    *reinterpret_cast<f32*>(state + kStateTargetOffset + 8) =
        *reinterpret_cast<const f32*>(row + kRowZOffset) +
        initial_cos * kProbeDistance;

    // 0x271374..0x27137C: nothing to search when the link word is clear.
    if (*reinterpret_cast<const u32*>(row + kRowLinkOffset) == 0) {
        return;
    }

    u8 probe_scratch[kProbeScratchSize];

    placement_2712d4::Vec3 origin;
    origin.x = *reinterpret_cast<const f32*>(state + kStateOriginOffset);
    origin.y = *reinterpret_cast<const f32*>(state + kStateOriginOffset + 4);
    origin.z = *reinterpret_cast<const f32*>(state + kStateOriginOffset + 8);

    placement_2712d4::Vec3 target;
    target.x = *reinterpret_cast<const f32*>(state + kStateTargetOffset);
    target.y = *reinterpret_cast<const f32*>(state + kStateTargetOffset + 4);
    target.z = *reinterpret_cast<const f32*>(state + kStateTargetOffset + 8);

    // 0x2713A8..0x2713B0: reject an unusable segment result.
    if (script_vm_func_00266e88(&target, &origin, probe_scratch) == -1) {
        return;
    }

    // 0x2713B4..0x2713C0: the improvement threshold starts at the distance to
    // the unsnapped probe target.
    f32 best_distance = engine_func_00287d54(origin, target);

    // 0x2713C8..0x271404: face the camera eye, then pick the 90-degree turn
    // direction that shortens the planar angular delta.
    const placement_2712d4::Vec3 camera_eye =
        *reinterpret_cast<const placement_2712d4::Vec3*>(
            *reinterpret_cast<u8* const*>(kScriptCameraSlotAddr) +
            kCameraEyeOffset);
    const placement_2712d4::Vec3 row_position = {
        *reinterpret_cast<const f32*>(row + kRowXOffset),
        *reinterpret_cast<const f32*>(row + kRowYOffset),
        *reinterpret_cast<const f32*>(row + kRowZOffset),
    };
    const f32 camera_angle =
        script_vm_func_00287e4c(row_position, camera_eye);
    const f32 angular_delta = script_vm_func_00287d74(heading, camera_angle);
    const f32 step_degrees =
        angular_delta < 0.0f ? -kStepDegrees : kStepDegrees;

    // 0x271408..0x2714D0: four probes at 90-degree offsets around the heading.
    f32 best_heading = heading;
    f32 offset_degrees = 0.0f;
    for (u32 sample = 0; sample < kSampleCount; ++sample) {
        const f32 snapped = script_vm_func_00282588(
            *reinterpret_cast<const f32*>(row + kRowHeadingOffset) +
            offset_degrees);
        const f32 snapped_radians = snapped * kDegToRadians;

        const f32 sin_value = script_vm_func_0028277c(snapped_radians);
        *reinterpret_cast<f32*>(state + kStateTargetOffset) =
            *reinterpret_cast<const f32*>(row + kRowXOffset) +
            sin_value * kProbeDistance;
        const f32 cos_value = script_vm_func_00282600(snapped_radians);
        *reinterpret_cast<f32*>(state + kStateTargetOffset + 8) =
            *reinterpret_cast<const f32*>(row + kRowZOffset) +
            cos_value * kProbeDistance;

        origin.x = *reinterpret_cast<const f32*>(state + kStateOriginOffset);
        origin.y =
            *reinterpret_cast<const f32*>(state + kStateOriginOffset + 4);
        origin.z =
            *reinterpret_cast<const f32*>(state + kStateOriginOffset + 8);

        target.x = *reinterpret_cast<const f32*>(state + kStateTargetOffset);
        target.y =
            *reinterpret_cast<const f32*>(state + kStateTargetOffset + 4);
        target.z =
            *reinterpret_cast<const f32*>(state + kStateTargetOffset + 8);

        // 0x271478..0x271484: a rejected segment stores the snapped heading and
        // leaves the published target at the rejected sample.
        if (script_vm_func_00266e88(&target, &origin, probe_scratch) == -1) {
            *reinterpret_cast<f32*>(row + kRowHeadingOffset) = snapped;
            return;
        }

        // 0x271498..0x2714C0: the original measures the candidate twice when it
        // wins: once for the comparison and once for the new threshold.
        if (engine_func_00287d54(origin, target) < best_distance) {
            best_heading = snapped;
            best_distance = engine_func_00287d54(origin, target);
        }

        offset_degrees += step_degrees;
    }

    // 0x2714D4..0x271508: republish the winning probe target.
    const f32 best_radians = best_heading * kDegToRadians;
    const f32 final_sin = script_vm_func_0028277c(best_radians);
    *reinterpret_cast<f32*>(state + kStateTargetOffset) =
        *reinterpret_cast<const f32*>(row + kRowXOffset) +
        final_sin * kProbeDistance;
    *reinterpret_cast<f32*>(state + kStateTargetOffset + 4) =
        *reinterpret_cast<const f32*>(row + kRowYOffset) + kOriginLift;
    const f32 final_cos = script_vm_func_00282600(best_radians);
    *reinterpret_cast<f32*>(state + kStateTargetOffset + 8) =
        *reinterpret_cast<const f32*>(row + kRowZOffset) +
        final_cos * kProbeDistance;
}

// DECOMP_FUNC(0x00392acc, 632)
// ---------------------------------------------------------------------------
// 0x00392ACC (632 B): message-source state machine.
//
// The routine drives a 32-bit state word at +0x08 while it owns a polymorphic
// message source at +0x208:
//   0 -> 1 -> {2, 3, 4, 0x270F}
// State 0/2 create a source through 0x00234160 (kind 0 and 4 respectively);
// states 1/3 query the source through vtable slot +0x0C, which returns a
// 20-byte message by value; state 4 runs a signed three-tick countdown. The
// deleting destructor (vtable slot +0x04) releases the source before +0x208 is
// cleared. The last 20-byte message is staged at +0x210, and the new source's
// u16 table id is stored at +0x14 of the object created in state 2.
//
// The body is ARM up to 0x00392D30. The 16 bytes at 0x00392D34..0x00392D40 are
// its literal pool: 0x0000270F, 0x00432FC8, 0x00000139 and 0x000009AA.
// The only reference to the entry point in the pinned image is the handler
// table word at 0x003FF0A4; no static caller exists.
// ---------------------------------------------------------------------------

// 20-byte message moved by value through the helper ABI. Only the first byte
// has recovered meaning: 0, 0x66 ('f') and 0x67 ('g') select distinct tails.
struct Message00392acc {
    u8 opcode;    // +0x00
    u8 pad[3];
    u32 field_04; // +0x04
    u32 field_08; // +0x08
    u32 field_0c; // +0x0C
    u32 field_10; // +0x10
};

static_assert(sizeof(Message00392acc) == 0x14,
              "0x00392ACC messages are 20 bytes");

struct MessageSource00392acc;

// Only the three slots touched by this routine are named. Slot 3 returns a
// 20-byte value; the ARM ABI passes the hidden return slot in r0 and `this` in
// r1, so it is modelled with those two leading parameters.
struct MessageSourceVtable00392acc {
    void (*full_destructor)(MessageSource00392acc*);                   // +0x00
    void (*deleting_destructor)(MessageSource00392acc*);               // +0x04
    void (*unobserved)(MessageSource00392acc*);                        // +0x08
    void (*read_message)(Message00392acc* out,
                         MessageSource00392acc* source);               // +0x0C
};

struct MessageSource00392acc {
    const MessageSourceVtable00392acc* vtable;  // +0x00
};

extern "C" void  engine_func_00234278(void* storage);                   // 0x00234278
extern "C" void* engine_func_00234160(void* owner, u32 kind);           // 0x00234160
extern "C" u32   shop_func_002337a0(const void* list);                  // 0x002337A0
extern "C" u32   camp_func_0027ec84(const void* message);               // 0x0027EC84
extern "C" u32   engine_func_002a17c0(const void* message);             // 0x002A17C0
extern "C" void  func_002342b8(void* context,
                               const Message00392acc* message);        // 0x002342B8
extern "C" void  engine_func_00234004(void* context, u32 arg1, u32 arg2); // 0x00234004

namespace engine_392acc {

// Caller-context offsets (ARM access widths in parentheses).
constexpr u32 kResult        = 0x004;  // u32 result code
constexpr u32 kState         = 0x008;  // u32 state selector
constexpr u32 kCounter       = 0x00C;  // s32 countdown used by state 4
constexpr u32 kSource        = 0x208;  // Source* owned pointer
constexpr u32 kFactoryOwner  = 0x20C;  // passed to 0x00234160 (unread there)
constexpr u32 kStagedMessage = 0x210;  // 20-byte staged message
constexpr u32 kList          = 0x240;  // passed to 0x002337A0
constexpr u32 kCreatedId     = 0x014;  // u32 id stored in the new source

// The root pointer is sampled once, after the entry constructor, and only its
// +0x678 table base is reloaded later.
constexpr u32 kGlobalRootAddress = 0x00432FC8;
constexpr u32 kGlobalTable       = 0x678;
constexpr u32 kTableLead         = 0x9AA;  // halfword offset into the table
constexpr u32 kTableStride       = 0x139;  // scale: (index * 0x139) << 3

constexpr u32 kStateStart       = 0;
constexpr u32 kStateRead        = 1;
constexpr u32 kStateCreate      = 2;
constexpr u32 kStateReadCreated = 3;
constexpr u32 kStateCountdown   = 4;
constexpr u32 kStateSignal      = 0x270F;

constexpr u32 kResultAfterCountdown = 6;   // state-4 expiry result
constexpr u32 kResultAfterMessage   = 10;  // zero-opcode result in state 3
constexpr u32 kSignalArg0           = 5;
constexpr u32 kSignalArg1           = 3;
constexpr u32 kFactoryStartKind     = 0;
constexpr u32 kFactoryCreateKind    = 4;
constexpr s32 kInitialCountdown     = 3;

constexpr u8 kOpcodeF = 0x66;  // 'f' literal byte comparison
constexpr u8 kOpcodeG = 0x67;  // 'g' literal byte comparison

static __attribute__((always_inline)) inline u32 load_u32(const void* p) {
    return *static_cast<const u32*>(p);
}

static __attribute__((always_inline)) inline void store_u32(void* p, u32 value) {
    *static_cast<u32*>(p) = value;
}

static __attribute__((always_inline)) inline void store_s32(void* p, s32 value) {
    *static_cast<s32*>(p) = value;
}

// 0x00392BD8/0x00392C80: vtable slot 0x0C writes the message into a temporary
// slot, then the routine copies all five words onto its own message object.
static __attribute__((always_inline)) inline void read_source_message(
    MessageSource00392acc* source, Message00392acc* message) {
    Message00392acc slot;
    source->vtable->read_message(&slot, source);
    *message = slot;
}

// Shared opcode tail of states 1 and 3 (0x00392C14..0x00392C68). It is reached
// only after 0x002A17C0 reports opcode >= 0x64.
static void dispatch_message(u8* self, const Message00392acc& message) {
    switch (message.opcode) {
    case kOpcodeF: {
        // 0x00392C38..0x00392C4C: the 20-byte value is copied to a private
        // stack slot and the callee receives a pointer to that copy. Clang's
        // ARM aggregate convention would split a by-value 20-byte parameter
        // across r1-r3 and the stack, so the recovered invisible-reference
        // argument is declared explicitly.
        Message00392acc forwarded = message;
        func_002342b8(self, &forwarded);
        return;
    }
    case kOpcodeG:
        store_u32(self + kState, kStateCountdown);
        store_s32(self + kCounter, kInitialCountdown);
        return;
    default:
        store_u32(self + kState, kStateSignal);
        *reinterpret_cast<Message00392acc*>(self + kStagedMessage) = message;
        return;
    }
}

}  // namespace engine_392acc

extern "C" void engine_func_00392acc(void* context) {
    using namespace engine_392acc;

    u8* const self = static_cast<u8*>(context);

    // The entry constructor runs before the global root is sampled.
    Message00392acc message;
    engine_func_00234278(&message);

    const u8* const root =
        *reinterpret_cast<const u8* const*>(kGlobalRootAddress);

    switch (load_u32(self + kState)) {
    case kStateStart: {
        MessageSource00392acc* const created =
            static_cast<MessageSource00392acc*>(
                engine_func_00234160(self + kFactoryOwner,
                                     kFactoryStartKind));
        store_u32(self + kState, kStateRead);
        *reinterpret_cast<MessageSource00392acc**>(self + kSource) = created;
        return;
    }

    case kStateRead: {
        // The original dereferences +0x208 without a null check.
        read_source_message(
            *reinterpret_cast<MessageSource00392acc**>(self + kSource),
            &message);
        if (camp_func_0027ec84(&message) != 0) {
            store_u32(self + kState, kStateCreate);
            return;
        }
        if (engine_func_002a17c0(&message) == 0) return;
        dispatch_message(self, message);
        return;
    }

    case kStateCreate: {
        MessageSource00392acc* const previous =
            *reinterpret_cast<MessageSource00392acc**>(self + kSource);
        if (previous != nullptr) {
            previous->vtable->deleting_destructor(previous);
        }
        MessageSource00392acc* const created =
            static_cast<MessageSource00392acc*>(
                engine_func_00234160(self + kFactoryOwner,
                                     kFactoryCreateKind));
        *reinterpret_cast<MessageSource00392acc**>(self + kSource) = created;

        const u32 index = shop_func_002337a0(self + kList);
        const u8* const table =
            *reinterpret_cast<const u8* const*>(root + kGlobalTable);
        const u32 table_offset = kTableLead + ((index * kTableStride) << 3);
        *reinterpret_cast<u32*>(
            reinterpret_cast<u8*>(created) + kCreatedId) =
            *reinterpret_cast<const u16*>(table + table_offset);

        store_u32(self + kState, kStateReadCreated);
        return;
    }

    case kStateReadCreated: {
        read_source_message(
            *reinterpret_cast<MessageSource00392acc**>(self + kSource),
            &message);
        if (camp_func_0027ec84(&message) != 0) {
            MessageSource00392acc* const previous =
                *reinterpret_cast<MessageSource00392acc**>(self + kSource);
            store_u32(self + kResult, kResultAfterMessage);
            store_u32(self + kState, kStateStart);
            if (previous != nullptr) {
                previous->vtable->deleting_destructor(previous);
                *reinterpret_cast<MessageSource00392acc**>(self + kSource) =
                    nullptr;
            }
            return;
        }
        if (engine_func_002a17c0(&message) == 0) return;
        dispatch_message(self, message);
        return;
    }

    case kStateCountdown: {
        // SUBS + BGT: the subtraction wraps in 32 bits and the wrapped result
        // is interpreted as signed, so keep the arithmetic unsigned.
        const u32 decremented = load_u32(self + kCounter) - 1u;
        store_u32(self + kCounter, decremented);
        if (static_cast<s32>(decremented) > 0) return;
        MessageSource00392acc* const previous =
            *reinterpret_cast<MessageSource00392acc**>(self + kSource);
        store_u32(self + kResult, kResultAfterCountdown);
        store_u32(self + kState, kStateStart);
        if (previous != nullptr) {
            previous->vtable->deleting_destructor(previous);
            *reinterpret_cast<MessageSource00392acc**>(self + kSource) = nullptr;
        }
        return;
    }

    case kStateSignal:
        engine_func_00234004(self, kSignalArg0, kSignalArg1);
        return;

    default:
        return;
    }
}

// DECOMP_FUNC(0x0033631c, 640)
extern "C" void engine_func_0033631c(void* context, u32 channel_index) {
    auto* const channel_base = static_cast<u8*>(context) + (channel_index * 4);

    auto* const p_current_color = reinterpret_cast<u32*>(channel_base + 0x4A0C);
    const u32 start_color = *reinterpret_cast<const u32*>(channel_base + 0x4A14);
    const u32 end_color = *reinterpret_cast<const u32*>(channel_base + 0x4A1C);
    auto* const p_state = reinterpret_cast<u32*>(channel_base + 0x4A24);
    auto* const p_step = reinterpret_cast<s32*>(channel_base + 0x4A2C);
    const s32 max_steps = *reinterpret_cast<const s32*>(channel_base + 0x4A34);

    u32 state = *p_state;
    if (state >= 7) {
        return;
    }

    if (state == 0) {
        state = 1;
        *p_state = 1;
    }

    if (state == 1) {
        const s32 cur_step = *p_step;
        const float t = static_cast<float>(cur_step) / static_cast<float>(max_steps);
        const float factor = 1.0f - t;

        const u32 diff_a = (start_color & 0xFF000000) - (end_color & 0xFF000000);
        const u32 cur_a = ((end_color & 0xFF000000) + static_cast<u32>(static_cast<float>(diff_a) * factor)) & 0xFF000000;

        const u32 diff_r = (start_color & 0x00FF0000) - (end_color & 0x00FF0000);
        const u32 cur_r = ((end_color & 0x00FF0000) + static_cast<u32>(static_cast<float>(diff_r) * factor)) & 0x00FF0000;

        const u32 diff_g = (start_color & 0x0000FF00) - (end_color & 0x0000FF00);
        const u32 cur_g = ((end_color & 0x0000FF00) + static_cast<u32>(static_cast<float>(diff_g) * factor)) & 0x0000FF00;

        const u32 diff_b = (start_color & 0x000000FF) - (end_color & 0x000000FF);
        const u32 cur_b = ((end_color & 0x000000FF) + static_cast<u32>(static_cast<float>(diff_b) * factor)) & 0x000000FF;

        *p_current_color = cur_a | cur_r | cur_g | cur_b;
        const s32 next_step = cur_step + 1;
        *p_step = next_step;

        if (next_step >= max_steps) {
            *p_state = 2;
        }
        return;
    }

    if (state == 2) {
        *p_current_color = end_color;
        *p_state = 3;
        return;
    }

    if (state == 3) {
        return;
    }

    if (state == 4) {
        state = 5;
        *p_state = 5;
    }

    if (state == 5) {
        const s32 cur_step = *p_step;
        const float factor = static_cast<float>(cur_step) / static_cast<float>(max_steps);

        const u32 diff_a = (end_color & 0xFF000000) - (start_color & 0xFF000000);
        const u32 cur_a = ((start_color & 0xFF000000) + static_cast<u32>(static_cast<float>(diff_a) * factor)) & 0xFF000000;

        const u32 diff_r = (end_color & 0x00FF0000) - (start_color & 0x00FF0000);
        const u32 cur_r = ((start_color & 0x00FF0000) + static_cast<u32>(static_cast<float>(diff_r) * factor)) & 0x00FF0000;

        const u32 diff_g = (end_color & 0x0000FF00) - (start_color & 0x0000FF00);
        const u32 cur_g = ((start_color & 0x0000FF00) + static_cast<u32>(static_cast<float>(diff_g) * factor)) & 0x0000FF00;

        const u32 diff_b = (end_color & 0x000000FF) - (start_color & 0x000000FF);
        const u32 cur_b = ((start_color & 0x000000FF) + static_cast<u32>(static_cast<float>(diff_b) * factor)) & 0x000000FF;

        *p_current_color = cur_a | cur_r | cur_g | cur_b;
        const s32 next_step = cur_step + 1;
        *p_step = next_step;

        if (next_step >= max_steps) {
            *p_state = 6;
        }
        return;
    }

    if (state == 6) {
        *p_current_color = end_color;
        *p_state = 7;
        return;
    }
}

// ---------------------------------------------------------------------------
// 0x00339B18 -- battle-main unit-slot setup (640 B).
//
// Entered with the 0x4A58-byte battle main work in r0.  The routine resets the
// 42 unit-slot pairs at work+0x1FE4/+0x1FE8, clears the 42-entry id scratch at
// work+0x43A8 and the 3600-byte block at work+0x357C, then selects up to four
// source ids:
//
//   * work+0x44A8 bit 0x40 set: use the four preset ids 0x225, 0x1E1, 0x218,
//     0x83 (the count is forced to 4);
//   * otherwise work+0x2F34 (party count) 1..4: use the first `count` of the
//     same four preset ids;
//   * otherwise (party count 0 or > 4): scan the twelve party-slot records
//     returned by 0x0026F25C, take the first four whose u16 at +0x48 is
//     non-zero, and copy that id into the next work+0x43A8 word.
//
// Every selected id is resolved through 0x002B087C and the s16 at +0x88 is
// stored in the 42-word stack scratch array.  The collected count is written
// to work+0x4390.
//
// The final pass walks the collected values: a value already present in the
// 42-entry pointer registry at work+0x2134 (matched against record+4) is
// skipped; otherwise 0x00294334(value, 1) returns the unit record, which is
// stored in the first free registry slot when one exists (a full registry is
// left unchanged) and the value is appended to work+0x1FE8 with stride 8.
// The number of appended values is written to work+0x438C and also returned
// in r0; the return value of the routine is therefore the collected count.
//
// 0x002B087C and 0x0026F25C are dereferenced without null checks, as in the
// original.  The original also reloads work+0x2F34 before testing the flag
// bit; that read is not observable and is omitted here.
// ---------------------------------------------------------------------------

namespace btl_unit_setup_00339b18 {

/** Unit record prefix shared by the 0x2134 registry (id at +4). */
struct UnitRecord {
    u8 pad_00[4];
    s32 id;                          // +0x04: `ldr r3,[r1,#4]`
};
static_assert(offsetof(UnitRecord, id) == 4);

/** One 8-byte unit-slot pair at work+0x1FE4. */
struct UnitSlot {
    s32 flag;                        // +0x00: `str r3,[r4]` with r3 = 0
    s32 id;                          // +0x04: `str ip,[r0]` with ip = -1
};
static_assert(sizeof(UnitSlot) == 8);

/** Battle-main work fields touched by this routine. */
struct BtlUnitSetupWork {
    u8 pad_0000[0x1fe4];
    UnitSlot slots[42];              // +0x1FE4: cleared flag/id pairs
    UnitRecord* registry[42];        // +0x2134: 42-entry unit-record table
    u8 pad_21dc[0x2f34 - 0x21dc];
    u32 party_count;                 // +0x2F34: 1..4 selects the preset ids
    u8 pad_2f38[0x357c - 0x2f38];
    u8 clear_block[0xe10];           // +0x357C: 3600 bytes zeroed
    s32 added_count;                 // +0x438C: values appended to slots
    s32 collected_count;             // +0x4390: selected id count
    u8 pad_4394[0x43a8 - 0x4394];
    s32 selected_ids[42];            // +0x43A8: 42-entry id scratch (0xA8 B)
    u8 pad_4450[0x44a8 - 0x4450];
    u32 flags;                       // +0x44A8: only bit 0x40 is tested
};
static_assert(offsetof(BtlUnitSetupWork, slots) == 0x1fe4);
static_assert(offsetof(BtlUnitSetupWork, registry) == 0x2134);
static_assert(offsetof(BtlUnitSetupWork, party_count) == 0x2f34);
static_assert(offsetof(BtlUnitSetupWork, clear_block) == 0x357c);
static_assert(offsetof(BtlUnitSetupWork, added_count) == 0x438c);
static_assert(offsetof(BtlUnitSetupWork, collected_count) == 0x4390);
static_assert(offsetof(BtlUnitSetupWork, selected_ids) == 0x43a8);
static_assert(offsetof(BtlUnitSetupWork, flags) == 0x44a8);

constexpr u32 kSlotCount = 42;        // `mov r1,#0x2a`
constexpr u32 kIdScratchSize = 0xa8;  // 42 * sizeof(s32)
constexpr u32 kClearSize = 0xe10;     // 3600 bytes at +0x357C
constexpr u32 kScanCount = 12;        // `cmp r6,#0xc`
constexpr u32 kMaxSelected = 4;       // `cmp r4,#4`
constexpr u32 kFlagsPreset = 0x40;    // `tst r1,#0x40`
constexpr u32 kPartyIdOffset = 0x48;  // u16 inside a 0x26F25C record
constexpr u32 kLookupValueOffset = 0x88;  // s16 inside a 0x2B087C record
constexpr u32 kCreateMode = 1;        // second argument of 0x00294334

}  // namespace btl_unit_setup_00339b18

// 0x002C4450 is a byte-fill helper: r0 = destination, r1 = byte count,
// r2 = fill byte (only the low byte is used).  It tail-calls 0x002C3B4C.
extern "C" void camp_func_002c4450(void* dst, u32 size, s32 value);
// 0x0026F25C returns the twelve party-slot records; null for index >= 12.
extern "C" u8* camp_func_0026f25c(u32 index);
// 0x00294334 returns the unit record for `id`, creating it when absent.
extern "C" btl_unit_setup_00339b18::UnitRecord* engine_func_00294334(
    s32 id, u32 mode);

// 0x002C4B30 (void* dst, u32 size) and 0x002B087C (u32 id) are declared
// earlier in this translation unit with the signatures used here.

extern "C" u32 engine_func_00339b18(
    btl_unit_setup_00339b18::BtlUnitSetupWork* work) {
    using namespace btl_unit_setup_00339b18;

    for (u32 i = 0; i < kSlotCount; ++i) {
        work->slots[i].flag = 0;
        work->slots[i].id = -1;
    }

    s32 values[kSlotCount];
    camp_func_002c4450(values, kIdScratchSize, -1);
    camp_func_002c4450(work->selected_ids, kIdScratchSize, -1);
    engine_func_002c4b30(work->clear_block, kClearSize);

    const u32 flags = work->flags;
    s32 count;
    bool auto_scanned = false;

    if ((flags & kFlagsPreset) != 0) {
        count = static_cast<s32>(kMaxSelected);
    } else {
        const u32 party_count = work->party_count;
        if (party_count - 1u > kMaxSelected - 1u) {
            // No valid preset count: scan the twelve party-slot records.
            u32 index = 0;
            s32 collected = 0;
            while (collected < static_cast<s32>(kMaxSelected) &&
                   index < kScanCount) {
                const u8* const party = camp_func_0026f25c(index);
                const u16 id =
                    *reinterpret_cast<const u16*>(party + kPartyIdOffset);
                if (id != 0) {
                    work->selected_ids[collected] = id;
                    const u8* const record =
                        battle_func_002b087c(static_cast<u32>(id));
                    values[collected] = *reinterpret_cast<const s16*>(
                        record + kLookupValueOffset);
                    ++collected;
                }
                ++index;
            }
            work->collected_count = collected;
            count = collected;
            auto_scanned = true;
        } else {
            count = static_cast<s32>(party_count);
        }
    }

    if (!auto_scanned) {
        for (s32 i = 0; i < count; ++i) {
            switch (i) {
            case 0:
                work->selected_ids[0] = 0x225;
                break;
            case 1:
                work->selected_ids[1] = 0x1e1;
                break;
            case 2:
                work->selected_ids[2] = 0x218;
                break;
            case 3:
                work->selected_ids[3] = 0x83;
                break;
            default:
                break;
            }
            const u16 id = static_cast<u16>(work->selected_ids[i]);
            const u8* const record =
                battle_func_002b087c(static_cast<u32>(id));
            values[i] =
                *reinterpret_cast<const s16*>(record + kLookupValueOffset);
        }
        work->collected_count = count;
    }

    const s32 collected = work->collected_count;
    s32 added = 0;
    if (collected > 0) {
        for (s32 i = 0; i < collected; ++i) {
            const s32 id = values[i];
            u32 slot = 0;
            while (slot < kSlotCount) {
                const UnitRecord* const record = work->registry[slot];
                if (record != nullptr && record->id == id) {
                    break;
                }
                ++slot;
            }
            if (slot == kSlotCount) {
                UnitRecord* const created =
                    engine_func_00294334(id, kCreateMode);
                slot = 0;
                while (slot < kSlotCount) {
                    if (work->registry[slot] == nullptr) {
                        break;
                    }
                    ++slot;
                }
                if (slot != kSlotCount) {
                    work->registry[slot] = created;
                }
                work->slots[added].id = values[i];
                ++added;
            }
        }
    }
    work->added_count = added;
    return static_cast<u32>(collected);
}

// ---------------------------------------------------------------------------
// 0x0035532C: submit a service request and start its asynchronous operation.
//
// The request slot is the 16-byte object whose vtable is 0x004209F8:
// +0x00 vtable, +0x04 session handle, +0x08/+0x0C two response words.
// 0x0035654C is vtable slot 0 and builds the operation object (vtable
// 0x00420998) into its second argument.  0x00239F84 returns the slot handle,
// lazily creating it when it is zero, and 0x002ADB54 sends the release command
// with the two response words.
//
// The original leaves both response words undefined when 0x002ADB84 fails and
// still feeds them to the release command.  They are initialized to zero here
// so that this path is deterministic; see the function record for the limit.
// The per-return destructor copies (0x003566F8's body) are represented by the
// two helpers below; each original path's duplicate second copy always finds
// the response words already zero and is omitted.
// ---------------------------------------------------------------------------

namespace srv_request_0035532c {

// 0x004209F8 is the request slot's vtable.  The target never dereferences it;
// it only stores the pointer into the slot.
constexpr u32 kRequestVtable = 0x004209f8;

// 0x0044E650+0x10 holds the service session handle (`ldr r0,[r6,#0x10]`).
constexpr u32 kServiceStateAddress = 0x0044e650;
constexpr u32 kSessionHandleOffset = 0x10;

// 0x002ADB84 arguments: r2 = command, r3 = argument, stack words = submit
// buffer pointer and count.
constexpr u32 kSubmitCommand = 3;
constexpr u32 kSubmitArgument = 1;
constexpr u32 kSubmitBufferCount = 1;

// Parameter block and descriptor handed to 0x0035654C.  The descriptor's first
// word and the parameter block's first word are both 2.
constexpr u32 kDescriptorType = 2;
constexpr u32 kIconTag = 0x6e6f6369;  // "icon"
constexpr u32 kDescriptorSize = 0x0c;
constexpr u32 kCreateFlag = 1;

// Second stack word of the operation's vtable slot 0 call.
constexpr u32 kStartStackArgument = 0x36c0;

struct RequestObject {
    u32 vtable;     // +0x00: 0x004209F8, only ever stored
    u32 handle;     // +0x04: session handle, zero until created
    u32 response0;  // +0x08: first 0x002ADB84 response word
    u32 response1;  // +0x0C: second 0x002ADB84 response word
};
static_assert(sizeof(RequestObject) == 0x10);
static_assert(offsetof(RequestObject, handle) == 0x04);
static_assert(offsetof(RequestObject, response0) == 0x08);
static_assert(offsetof(RequestObject, response1) == 0x0c);

// [sp+0x2C] = {sp+0x2C, 1}; the first word points at itself.
struct SubmitBuffer {
    u32 self;   // +0x00: address of this word
    u32 count;  // +0x04: 1
};
static_assert(sizeof(SubmitBuffer) == 0x08);

struct Descriptor {
    u32 type;          // +0x00: 2
    const void* data;  // +0x04: parameter block
    u32 size;          // +0x08: 0x0C
};
static_assert(sizeof(Descriptor) == 0x0c);

struct IconParameter {
    u32 type;   // +0x00: 2
    u32 tag;    // +0x04: "icon"
    u32 value;  // +0x08: 0
};
static_assert(sizeof(IconParameter) == 0x0c);

struct OperationObject;

// Only slots 0x00 and 0x2C of the 0x00420998 operation vtable are used.
struct OperationVtable {
    s32 (*start)(OperationObject* self, u32* output, u32 arg2, u32 arg3,
                 u32 stack0, u32 stack1);  // +0x00
    void* reserved[10];                    // +0x04..0x2B
    void (*release)(OperationObject* self);  // +0x2C
};
static_assert(offsetof(OperationVtable, release) == 0x2c);

struct OperationObject {
    const OperationVtable* vtable;  // +0x00
    u32 handle;                     // +0x04
};
static_assert(offsetof(OperationObject, vtable) == 0x00);

}  // namespace srv_request_0035532c

// 0x002ADB84 submits one IPC command through the thread-local request buffer.
// On success it writes the two response words and returns `command`; on failure
// it returns the negative SVC status and leaves the response buffer untouched.
extern "C" s32 func_002adb84(const u32* handle, u32* response, u32 command,
                             u32 argument, const u32* buffer,
                             u32 buffer_size);

// 0x002ADB54 submits the release command.  Its second argument (r1) is not read
// by the callee, so the reconstruction passes an explicit zero.
extern "C" s32 func_002adb54(const u32* handle, u32 unused, u32 value0,
                             u32 value1);

// 0x00239F84 returns request->handle and creates it when it is zero.
extern "C" u32 nn_sdk_func_00239f84(
    srv_request_0035532c::RequestObject* request);

// 0x0035654C is request->vtable[0]; it builds the operation object and stores
// it through the second argument.
extern "C" s32 func_0035654c(
    srv_request_0035532c::RequestObject* request,
    srv_request_0035532c::OperationObject** operation,
    const srv_request_0035532c::Descriptor* descriptor, u32 flag);

namespace srv_request_0035532c {

// Inline body of the request-slot destructor (0x003566F8).  Every original
// return site contains this sequence; the duplicated second copy in each path
// always finds the response words already zero and is therefore omitted.
//
// The failure tails (0x3553A4, 0x3554BC, 0x3554F8) reload both response words
// after 0x00239F84 returns, while the start-success tail (0x355534) reuses the
// pair it loaded before the call.  Both forms are kept because the getter is
// external and the two paths really do differ if it writes the slot.
static inline void release_request_reloaded(RequestObject* request) {
    if ((request->response0 | request->response1) != 0) {
        const u32 handle = nn_sdk_func_00239f84(request);
        func_002adb54(&handle, 0, request->response0, request->response1);
        request->response0 = 0;
        request->response1 = 0;
    }
    request->handle = 0;
}

static inline void release_request_cached(RequestObject* request) {
    const u32 response0 = request->response0;
    const u32 response1 = request->response1;
    if ((response0 | response1) != 0) {
        const u32 handle = nn_sdk_func_00239f84(request);
        func_002adb54(&handle, 0, response0, response1);
        request->response0 = 0;
        request->response1 = 0;
    }
    request->handle = 0;
}

}  // namespace srv_request_0035532c

// DECOMP_FUNC(0x0035532c, 640)
extern "C" s32 camp_func_0035532c(u32 argument) {
    using namespace srv_request_0035532c;

    RequestObject request = {};
    request.vtable = kRequestVtable;

    u32 handle = *reinterpret_cast<u32*>(kServiceStateAddress +
                                         kSessionHandleOffset);
    u32 response[2] = {0, 0};

    SubmitBuffer submit = {};
    submit.self = reinterpret_cast<u32>(&submit.self);
    submit.count = kSubmitBufferCount;

    const s32 submit_status =
        func_002adb84(&handle, response, kSubmitCommand, kSubmitArgument,
                      &submit.self, kSubmitBufferCount);
    if (submit_status < 0) {
        release_request_reloaded(&request);
        return submit_status;
    }

    // The original reloads the global handle after the command succeeds.
    request.handle = *reinterpret_cast<u32*>(kServiceStateAddress +
                                             kSessionHandleOffset);
    request.response0 = response[0];
    request.response1 = response[1];

    IconParameter icon = {};
    icon.type = kDescriptorType;
    icon.tag = kIconTag;
    icon.value = 0;

    Descriptor descriptor = {};
    descriptor.type = kDescriptorType;
    descriptor.data = &icon;
    descriptor.size = kDescriptorSize;

    OperationObject* operation = nullptr;
    const s32 create_status =
        func_0035654c(&request, &operation, &descriptor, kCreateFlag);
    if (create_status < 0) {
        release_request_reloaded(&request);
        return create_status;
    }

    u32 operation_output = 0;
    const s32 start_status = operation->vtable->start(
        operation, &operation_output, 0, 0, argument, kStartStackArgument);
    operation->vtable->release(operation);

    if (start_status < 0) {
        release_request_reloaded(&request);
        return start_status;
    }
    release_request_cached(&request);
    return 0;
}

// ---------------------------------------------------------------------------
// 0x0038E58C -- message-driven handler (640 B).
//
// Same shape as 0x00392ACC below (entry message constructor, owned "source"
// object with a two-slot vtable, byte-opcode dispatch), but a shorter state
// graph: 0 start -> 1 read -> 2 recreate -> 3 read-created -> 4 resolve ->
// 5 countdown, plus the 0x270F signal state.  The state-4 value is resolved by
// 0x002A1578; a negative (bit-31) result stages a 0x64 message and enters the
// signal state, otherwise the countdown runs.  State 5 expiry stores result 6,
// returns to state 0 and releases the owned source.  Literal pool at
// 0x0038E804/0x0038E808: 0x0000270F, 0x00432FC8.  No static caller exists in
// the pinned image.
// ---------------------------------------------------------------------------

// 0x00234368 writes its two-word result through r0 and receives the game-root
// pointer in r1.  Modeled with an explicit out pointer; the return register is
// not consumed by 0x0038E58C.
extern "C" void engine_func_00234368(u32* out_pair, const void* context); // 0x00234368

namespace engine_e58c {

// 0x0038E58C consumes the same 20-byte message layout and two-slot source
// vtable as 0x00392ACC; only the first message byte has recovered meaning.
using Message = Message00392acc;
using MessageSource = MessageSource00392acc;

// Caller-context offsets (ARM access widths in parentheses).
constexpr u32 kResult          = 0x004;  // u32 result code (state 5 expiry)
constexpr u32 kState           = 0x008;  // u32 state selector
constexpr u32 kCounter         = 0x00C;  // s32 countdown used by state 5
constexpr u32 kSource          = 0x208;  // Source* owned pointer
constexpr u32 kFactoryOwner    = 0x20C;  // passed to 0x00234160
constexpr u32 kStagedMessage   = 0x210;  // 20-byte staged message
constexpr u32 kStagedPayload   = 0x214;  // 8-byte value inside a staged 0x64

// Sampled once at entry; handed to 0x00234368 as its context argument.
constexpr u32 kGlobalRootAddress = 0x00432FC8;

constexpr u32 kStateStart       = 0;
constexpr u32 kStateRead        = 1;
constexpr u32 kStateCreate      = 2;
constexpr u32 kStateReadCreated = 3;
constexpr u32 kStateResolve     = 4;
constexpr u32 kStateCountdown   = 5;
constexpr u32 kStateSignal      = 0x270F;

constexpr u32 kFactoryStartKind  = 0;
constexpr u32 kFactoryCreateKind = 5;
constexpr u32 kSignalArg0        = 0x0C;
constexpr u32 kSignalArg1        = 3;
constexpr u32 kResultAfterCountdown = 6;
constexpr s32 kInitialCountdown  = 3;

constexpr u8 kOpcodeF        = 0x66;  // 'f' forward tail (meaning unknown)
constexpr u8 kOpcodeG        = 0x67;  // 'g' countdown tail (meaning unknown)
constexpr u8 kStagedOpcode   = 0x64;  // first byte of the state-4 staged message

// 0x0038E664/0x0038E708: vtable slot 0x0C writes the 20-byte message into the
// caller's slot; the routine then copies all five words onto its own message.
static __attribute__((always_inline)) inline void read_source_message(
    MessageSource* source, Message* message) {
    Message slot;
    source->vtable->read_message(&slot, source);
    *message = slot;
}

// Shared opcode tail of states 1 and 3.  It is reached only after 0x002A17C0
// reports opcode >= 0x64.  The 0x66 path hands 0x002342B8 a pointer to a
// private 20-byte copy of the message.
static void dispatch_message(u8* self, const Message& message) {
    switch (message.opcode) {
    case kOpcodeF: {
        Message forwarded = message;
        func_002342b8(self, &forwarded);
        return;
    }
    case kOpcodeG:
        *reinterpret_cast<u32*>(self + kState) = kStateCountdown;
        *reinterpret_cast<s32*>(self + kCounter) = kInitialCountdown;
        return;
    default:
        *reinterpret_cast<u32*>(self + kState) = kStateSignal;
        *reinterpret_cast<Message*>(self + kStagedMessage) = message;
        return;
    }
}

}  // namespace engine_e58c

extern "C" void engine_func_0038e58c(void* context) {
    using namespace engine_e58c;

    u8* const self = static_cast<u8*>(context);

    // The entry constructor runs before the global root is sampled.
    Message message;
    engine_func_00234278(&message);

    const void* const root =
        *reinterpret_cast<const void* const*>(kGlobalRootAddress);

    switch (*reinterpret_cast<const u32*>(self + kState)) {
    case kStateStart: {
        void* const created =
            engine_func_00234160(self + kFactoryOwner, kFactoryStartKind);
        *reinterpret_cast<u32*>(self + kState) = kStateRead;
        *reinterpret_cast<void**>(self + kSource) = created;
        return;
    }

    case kStateRead: {
        // The original dereferences +0x208 without a null check.
        read_source_message(
            *reinterpret_cast<MessageSource**>(self + kSource), &message);
        if (camp_func_0027ec84(&message) != 0) {
            *reinterpret_cast<u32*>(self + kState) = kStateCreate;
            return;
        }
        if (engine_func_002a17c0(&message) == 0) return;
        dispatch_message(self, message);
        return;
    }

    case kStateCreate: {
        MessageSource* const previous =
            *reinterpret_cast<MessageSource**>(self + kSource);
        if (previous != nullptr) {
            previous->vtable->deleting_destructor(previous);
        }
        void* const created =
            engine_func_00234160(self + kFactoryOwner, kFactoryCreateKind);
        *reinterpret_cast<u32*>(self + kState) = kStateReadCreated;
        *reinterpret_cast<void**>(self + kSource) = created;
        return;
    }

    case kStateReadCreated: {
        read_source_message(
            *reinterpret_cast<MessageSource**>(self + kSource), &message);
        if (camp_func_0027ec84(&message) != 0) {
            *reinterpret_cast<u32*>(self + kState) = kStateResolve;
            return;
        }
        if (engine_func_002a17c0(&message) == 0) return;
        dispatch_message(self, message);
        return;
    }

    case kStateResolve: {
        // 0x00234368 fills the two-word pair; 0x002A1578 maps it.  A bit-31
        // (negative) result fails the resolve: stage 0x64 with the raw pair.
        u32 pair[2];
        engine_func_00234368(pair, root);
        const u32 mapped = engine_func_002a1578(pair);
        if ((mapped & 0x80000000u) == 0) {
            *reinterpret_cast<u32*>(self + kState) = kStateCountdown;
            *reinterpret_cast<s32*>(self + kCounter) = kInitialCountdown;
            return;
        }
        *reinterpret_cast<u32*>(self + kState) = kStateSignal;
        *reinterpret_cast<u8*>(self + kStagedMessage) = kStagedOpcode;
        *reinterpret_cast<u32*>(self + kStagedPayload) = pair[0];
        *reinterpret_cast<u32*>(self + kStagedPayload + 4) = pair[1];
        return;
    }

    case kStateCountdown: {
        // SUBS + BGT: the subtraction wraps in 32 bits and the wrapped result
        // is interpreted as signed, so keep the arithmetic unsigned.
        const u32 decremented =
            *reinterpret_cast<const u32*>(self + kCounter) - 1u;
        *reinterpret_cast<u32*>(self + kCounter) = decremented;
        if (static_cast<s32>(decremented) > 0) return;

        MessageSource* const previous =
            *reinterpret_cast<MessageSource**>(self + kSource);
        *reinterpret_cast<u32*>(self + kResult) = kResultAfterCountdown;
        *reinterpret_cast<u32*>(self + kState) = kStateStart;
        if (previous != nullptr) {
            previous->vtable->deleting_destructor(previous);
            *reinterpret_cast<MessageSource**>(self + kSource) = nullptr;
        }
        return;
    }

    case kStateSignal:
        engine_func_00234004(self, kSignalArg0, kSignalArg1);
        return;

    default:
        return;
    }
}

// 0x001A7CAC builds a camp selection record from a table entry (modes 0/3) or
// from the 0x34-byte detail record (mode 1), then hands the finished record to
// the camp selection updater.  Mode 3 skips the free-slot scan and id-flag
// updates; every other mode still refreshes the record.
extern "C" void engine_func_002c4b30(void* dst, u32 size);
extern "C" u8* camp_func_002a8a08(u32 sub_mode);
extern "C" u32 func_002032b8(u32 id, u32 value);
extern "C" u32 script_vm_func_001dd9f4(u32 id, u32 value);
extern "C" u8* camp_func_002b9364(u32 id);
extern "C" u32 camp_func_002883bc(u32 id, void* out);
extern "C" void script_vm_func_0029c950(void* ctx);
extern "C" u32 camp_func_0029c084(void* ctx);

namespace {

constexpr u32 k001a7cacZeroFillSize = 0x604;      // full record cleared first
constexpr u32 k001a7cacSlotListOffset = 0x90F0;   // s8 slot indices in the list
constexpr u32 k001a7cacSlotListCount = 0x18;
constexpr u32 k001a7cacIdOffset = 0x46;           // u16
constexpr u32 k001a7cacArgumentByteOffset = 0x4A; // u8
constexpr u32 k001a7cacEntryFlagByteOffset = 0x48; // u8
constexpr u32 k001a7cacDetailBitsOffset = 0x16;   // u8, bits 5..2
constexpr u32 k001a7cacDetailWordOffset = 0x30;   // u32
constexpr u32 k001a7cacEntryBitIndexOffset = 0x38; // u16
constexpr u32 k001a7cacBitMapOffset = 0x4C;
constexpr u32 k001a7cacBitIndexMask = 7u;
constexpr u32 k001a7cacBitIndexShift = 3u;
constexpr u32 k001a7cacDetailNibbleShift = 2u;
constexpr u32 k001a7cacDetailNibbleMask = 0x0F;
constexpr u32 k001a7cacModeTableCopy = 0;
constexpr u32 k001a7cacModeDetail = 1;
constexpr u32 k001a7cacModeNoScan = 3;

// The original zero-fill helper returns `dst + size`; that leftover value is
// what the following 0x002A8A08 call receives in r0 (the callee ignores it).
inline u32 zero_fill_return(const void* dst, u32 size) {
    return reinterpret_cast<u32>(dst) + size;
}

}  // namespace

extern "C" u32 camp_func_001a7cac(void* record, u32 slot, u32 id, u32 mode) {
    u8* const self = static_cast<u8*>(record);
    const u16 id16 = static_cast<u16>(id);

    engine_func_002c4b30(self, k001a7cacZeroFillSize);
    *reinterpret_cast<u16*>(self + k001a7cacIdOffset) = id16;
    *reinterpret_cast<u8*>(self + k001a7cacArgumentByteOffset) =
        static_cast<u8>(slot);

    if (mode != k001a7cacModeNoScan) {
        // Replace the first free (negative) slot index; the loop is bounded by
        // the fixed 24-entry list, not by the separate count byte.
        u8* const slots = camp_func_002a8a08(
                              zero_fill_return(self, k001a7cacZeroFillSize)) +
                          k001a7cacSlotListOffset;
        for (u32 i = 0; i < k001a7cacSlotListCount; ++i) {
            if (static_cast<s8>(slots[i]) < 0) {
                slots[i] = static_cast<u8>(slot);
                break;
            }
        }
        func_002032b8(id16, 1);
        script_vm_func_001dd9f4(id16, 1);
    }

    u8* const entry = camp_func_002b9364(id16);

    if (mode == k001a7cacModeTableCopy || mode == k001a7cacModeNoScan) {
        *reinterpret_cast<u8*>(self + k001a7cacEntryFlagByteOffset) =
            *reinterpret_cast<const u8*>(entry + 3);
        *reinterpret_cast<u16*>(self + 0x00) =
            *reinterpret_cast<const u16*>(entry + 0x14);
        *reinterpret_cast<u16*>(self + 0x02) =
            *reinterpret_cast<const u16*>(entry + 0x16);
        *reinterpret_cast<u16*>(self + 0x04) =
            *reinterpret_cast<const u16*>(entry + 0x1A);
        *reinterpret_cast<u16*>(self + 0x08) =
            *reinterpret_cast<const u16*>(entry + 0x1E);
        *reinterpret_cast<u16*>(self + 0x0A) =
            *reinterpret_cast<const u16*>(entry + 0x20);
        *reinterpret_cast<u16*>(self + 0x0C) =
            *reinterpret_cast<const u16*>(entry + 0x22);
        *reinterpret_cast<u16*>(self + 0x06) =
            *reinterpret_cast<const u16*>(entry + 0x1C);
        *reinterpret_cast<u16*>(self + 0x1C) = 0;
        *reinterpret_cast<u16*>(self + 0x1E) = 0;
        *reinterpret_cast<u16*>(self + 0x20) =
            *reinterpret_cast<const u16*>(entry + 0x1A);
        *reinterpret_cast<u16*>(self + 0x24) =
            *reinterpret_cast<const u16*>(entry + 0x1E);
        *reinterpret_cast<u16*>(self + 0x26) =
            *reinterpret_cast<const u16*>(entry + 0x20);
        *reinterpret_cast<u16*>(self + 0x28) =
            *reinterpret_cast<const u16*>(entry + 0x22);
        *reinterpret_cast<u16*>(self + 0x22) =
            *reinterpret_cast<const u16*>(entry + 0x1C);
        *reinterpret_cast<u16*>(self + 0x34) =
            *reinterpret_cast<const u16*>(entry + 0x3C);
        *reinterpret_cast<u16*>(self + 0x36) =
            *reinterpret_cast<const u16*>(entry + 0x3E);
        *reinterpret_cast<u16*>(self + 0x38) =
            *reinterpret_cast<const u16*>(entry + 0x40);
        *reinterpret_cast<u16*>(self + 0x3A) =
            *reinterpret_cast<const u16*>(entry + 0x42);
        *reinterpret_cast<u16*>(self + 0x3C) =
            *reinterpret_cast<const u16*>(entry + 0x44);
        *reinterpret_cast<u16*>(self + 0x3E) =
            *reinterpret_cast<const u16*>(entry + 0x46);
        *reinterpret_cast<u16*>(self + 0x40) =
            *reinterpret_cast<const u16*>(entry + 0x48);
        *reinterpret_cast<u16*>(self + 0x42) =
            *reinterpret_cast<const u16*>(entry + 0x4A);

        const u16 bit_index =
            *reinterpret_cast<const u16*>(entry + k001a7cacEntryBitIndexOffset);
        u8* const map_byte =
            self + k001a7cacBitMapOffset +
            static_cast<u32>(bit_index >> k001a7cacBitIndexShift);
        *map_byte = static_cast<u8>(
            *map_byte | (1u << (bit_index & k001a7cacBitIndexMask)));
    } else if (mode == k001a7cacModeDetail) {
        // 0x002883BC expands the 0x34-byte detail record on the stack.
        u8 detail[0x34];
        camp_func_002883bc(id16, detail);

        *reinterpret_cast<u8*>(self + k001a7cacEntryFlagByteOffset) = detail[0];
        *reinterpret_cast<u16*>(self + 0x00) =
            *reinterpret_cast<const u16*>(detail + 0x18);
        *reinterpret_cast<u16*>(self + 0x02) =
            *reinterpret_cast<const u16*>(detail + 0x1A);
        *reinterpret_cast<u16*>(self + 0x04) =
            *reinterpret_cast<const u16*>(detail + 0x02);
        *reinterpret_cast<u16*>(self + 0x08) =
            *reinterpret_cast<const u16*>(detail + 0x06);
        *reinterpret_cast<u16*>(self + 0x0A) =
            *reinterpret_cast<const u16*>(detail + 0x08);
        *reinterpret_cast<u16*>(self + 0x0C) =
            *reinterpret_cast<const u16*>(detail + 0x0A);
        *reinterpret_cast<u16*>(self + 0x06) =
            *reinterpret_cast<const u16*>(detail + 0x04);
        *reinterpret_cast<u16*>(self + 0x1C) = 0;
        *reinterpret_cast<u16*>(self + 0x1E) = 0;
        *reinterpret_cast<u16*>(self + 0x20) =
            *reinterpret_cast<const u16*>(detail + 0x0C);
        *reinterpret_cast<u16*>(self + 0x24) =
            *reinterpret_cast<const u16*>(detail + 0x10);
        *reinterpret_cast<u16*>(self + 0x26) =
            *reinterpret_cast<const u16*>(detail + 0x12);
        *reinterpret_cast<u16*>(self + 0x28) =
            *reinterpret_cast<const u16*>(detail + 0x14);
        *reinterpret_cast<u16*>(self + 0x22) =
            *reinterpret_cast<const u16*>(detail + 0x0E);
        *reinterpret_cast<u16*>(self + 0x34) =
            *reinterpret_cast<const u16*>(detail + 0x1C);
        *reinterpret_cast<u16*>(self + 0x36) =
            *reinterpret_cast<const u16*>(detail + 0x1E);
        *reinterpret_cast<u16*>(self + 0x38) =
            *reinterpret_cast<const u16*>(detail + 0x20);
        *reinterpret_cast<u16*>(self + 0x3A) =
            *reinterpret_cast<const u16*>(detail + 0x22);
        *reinterpret_cast<u16*>(self + 0x3C) =
            *reinterpret_cast<const u16*>(detail + 0x24);
        *reinterpret_cast<u16*>(self + 0x3E) =
            *reinterpret_cast<const u16*>(detail + 0x26);
        *reinterpret_cast<u16*>(self + 0x40) =
            *reinterpret_cast<const u16*>(detail + 0x28);
        *reinterpret_cast<u16*>(self + 0x42) =
            *reinterpret_cast<const u16*>(detail + 0x2A);
        *reinterpret_cast<u32*>(self + 0x30) =
            *reinterpret_cast<const u32*>(detail + k001a7cacDetailWordOffset);
        *reinterpret_cast<u8*>(self + 0x601) = static_cast<u8>(
            (detail[k001a7cacDetailBitsOffset] >> k001a7cacDetailNibbleShift) &
            k001a7cacDetailNibbleMask);

        const u16 bit_index =
            *reinterpret_cast<const u16*>(entry + k001a7cacEntryBitIndexOffset);
        u8* const map_byte =
            self + k001a7cacBitMapOffset +
            static_cast<u32>(bit_index >> k001a7cacBitIndexShift);
        *map_byte = static_cast<u8>(
            *map_byte | (1u << (bit_index & k001a7cacBitIndexMask)));
    }

    script_vm_func_0029c950(self);
    *reinterpret_cast<u16*>(self + 0x2A) =
        *reinterpret_cast<const u16*>(self + 0x0E);
    *reinterpret_cast<u16*>(self + 0x2C) =
        *reinterpret_cast<const u16*>(self + 0x10);
    return camp_func_0029c084(self);
}

// DECOMP_FUNC(0x003949e8, 644)
//
// Effect-table lookup and effect-command dispatch.  The routine formats each
// 0x24-byte table entry's 16-byte name as "<name>.eft", compares it with the
// requested name, and on a match forwards the entry's two command/id pairs to
// 0x00250800 together with a five-way sector code derived from the float
// argument.  On success the entry's +0x20 word is copied into the UI/effect
// singleton and 1 is returned.
//
// Sector mapping (`selector` = r2):
//   * 2, 5, 8, 9, 12 -- thresholds are the absolute constants in the literal
//     pool at 0x394C48..0x394C54;
//   * 6, 7, 11       -- sector 3 unconditionally (jump-table targets 0x394BB0);
//   * 3, 4, 10 and every other selector (including the jump table's default
//     and selector 13) -- thresholds relative to the float at
//     *(*(0x004342C8) + 0x574).
//
// 0x002BE7FC is Thumb code (reached with `blx`); all other callees are ARM.
// The jump table at 0x394AC0 has 11 entries; index 11 (selector 13) and
// selectors outside 2..13 take the default 0x394B30 path.
namespace engine_3949e8 {

// One effect-table record.  Offsets are exactly the loads/stores in the body:
// the 16-byte name is the "%s.eft" input, +0x10/+0x18 are the nonzero-checked
// command words, +0x14/+0x1C their zero-extended 16-bit ids, +0x20 the word
// copied into the UI singleton.
struct EffectEntry {
    char name[0x10];    // +0x00
    u32 command_a;      // +0x10  `ldr r2,[r5,#0x10]`
    u16 id_a;           // +0x14  `ldrh r0,[r5,#0x14]`
    u16 pad_16;         // +0x16
    u32 command_b;      // +0x18  `ldr r2,[r5,#0x18]`
    u16 id_b;           // +0x1C  `ldrh r0,[r5,#0x1C]`
    u16 pad_1E;         // +0x1E
    u32 state_value;    // +0x20  `ldr r0,[r5,#0x20]`
};
static_assert(sizeof(EffectEntry) == 0x24, "effect entry stride is 0x24");

constexpr u32 kEffectTableAddress = 0x00436028;  // `ldr sl,[pc,#0x21C]`
constexpr u32 kFirstEntryIndex = 0;
constexpr u32 kLastEntryIndex = 0x190;           // `cmp r4,#0x190; ble`
constexpr u32 kNameBufferSize = 0x20;            // `sub sp,sp,#0x20`
constexpr u32 kGlobalConfigAddress = 0x004342C8; // `ldr r0,[pc,#0x124]`
constexpr u32 kReferenceOffset = 0x574;          // `ldr r0,[r0,#0x574]`
constexpr u32 kUiResultOffset = 0x49E4;          // 0x4800 + 0x1E4

constexpr f32 F32FromBits(u32 bits) noexcept {
    return __builtin_bit_cast(f32, bits);
}

// Absolute sector thresholds (literal pool 0x394C48..0x394C54).
constexpr f32 kAbsoluteOuterLow = F32FromBits(0xC03DC290u);  // -2.9650002
constexpr f32 kAbsoluteInnerLow = F32FromBits(0xBF7D70A4u);  // -0.99000001
constexpr f32 kAbsoluteInnerHigh = F32FromBits(0x403C28F6u); //  2.9400001
constexpr f32 kAbsoluteOuterHigh = F32FromBits(0x3F770A3Eu); //  0.96500003

// Relative sector offsets (literal pool 0x394C58..0x394C68).
constexpr f32 kReferenceInner = 9.0f;    // 0x41100000
constexpr f32 kReferenceOuter = 17.0f;   // 0x41880000

// 0x394AEC..0x394B2C: four ordered comparisons produce sectors 5, 4, 1, 2 and
// the fall-through sector 3.
inline s32 AbsoluteSector(f32 angle) noexcept {
    if (angle < kAbsoluteOuterLow) {
        return 5;
    }
    if (angle < kAbsoluteInnerLow) {
        return 4;
    }
    if (angle > kAbsoluteInnerHigh) {
        return 1;
    }
    if (angle > kAbsoluteOuterHigh) {
        return 2;
    }
    return 3;
}

// 0x394B30..0x394BAC: the same ordering around the reference angle read from
// the global config object.
inline s32 RelativeSector(f32 angle) noexcept {
    const f32 reference = *reinterpret_cast<const f32*>(
        *reinterpret_cast<const u8* const*>(kGlobalConfigAddress) +
        kReferenceOffset);
    if (angle < reference - kReferenceOuter) {
        return 5;
    }
    if (angle < reference - kReferenceInner) {
        return 4;
    }
    if (angle > reference + kReferenceOuter) {
        return 1;
    }
    if (angle > reference + kReferenceInner) {
        return 2;
    }
    return 3;
}

}  // namespace engine_3949e8

extern "C" u32 engine_func_002c583c(u32 index);
extern "C" u32 ui_func_002be7fc(char* dst, const char* format, ...);
extern "C" s32 engine_func_002aa7f4(const char* a, const char* b);
extern "C" void* ui_func_00293c98();
extern "C" s32 battle_func_00250800(s32 a, s32 b, u32 command, s32 d, s32 e,
                                    s32 f, s32 g);

extern "C" u32 engine_func_003949e8(const char* name, u32 arg1, s32 selector,
                                    f32 angle) {
    using namespace engine_3949e8;

    // 0x394A04..0x394A10: the guard returns a word from a global table; any
    // nonzero value aborts before the lookup.
    if (engine_func_002c583c(1) != 0) {
        return 0;
    }

    // 0x394A14..0x394AA0: linear search over 0x191 entries.
    const EffectEntry* found = nullptr;
    for (u32 index = kFirstEntryIndex; index <= kLastEntryIndex; ++index) {
        char text[kNameBufferSize] = {};
        const EffectEntry* const entry =
            reinterpret_cast<const EffectEntry*>(kEffectTableAddress) + index;
        ui_func_002be7fc(text, "%s.eft", entry->name);
        if (engine_func_002aa7f4(text, name) == 0) {
            found = entry;
            break;
        }
    }

    // 0x394AA8..0x394AB8: the UI/effect singleton is fetched before the sector
    // switch, and the relative path dereferences the config pointer before the
    // found/not-found test.
    u8* const ui = static_cast<u8*>(ui_func_00293c98());

    s32 sector;
    switch (selector) {
    case 2:
    case 5:
    case 8:
    case 9:
    case 12:
        sector = AbsoluteSector(angle);
        break;
    case 6:
    case 7:
    case 11:
        sector = 3;
        break;
    case 3:
    case 4:
    case 10:
    default:
        sector = RelativeSector(angle);
        break;
    }

    // 0x394BB4..0x394BB8: no entry means no dispatch and no state write.
    if (found == nullptr) {
        return 0;
    }

    // 0x394BBC..0x394BE0: first (id, command) pair; the stack words are
    // [sp] = 0, [sp+4] = sector, [sp+8] = 0.
    if (found->command_a != 0) {
        battle_func_00250800(static_cast<s32>(found->id_a),
                             static_cast<s32>(arg1), found->command_a, 0, 0,
                             sector, 0);
    }

    // 0x394BE4..0x394C08: second pair, identical layout.
    if (found->command_b != 0) {
        battle_func_00250800(static_cast<s32>(found->id_b),
                             static_cast<s32>(arg1), found->command_b, 0, 0,
                             sector, 0);
    }

    // 0x394C0C..0x394C18: publish the entry's +0x20 word in the singleton.
    *reinterpret_cast<u32*>(ui + kUiResultOffset) = found->state_value;
    return 1;
}

// DECOMP_FUNC(0x003e9ba8, 652)
extern "C" u32 engine_func_002c2be8(const float* rgba);

static inline u32 pack_pica_float20(float f) {
    union {
        float f;
        u32 u;
    } cvt;
    cvt.f = f;
    const u32 u = cvt.u;
    const u32 sign = (u >> 31) & 1;
    const s32 exp = static_cast<s32>((u >> 23) & 0xFF);
    const u32 mant = u & 0x7FFFFF;

    const u32 sign_bit = sign ? 0x80000u : 0u;
    if ((u & 0x7FFFFFFFu) == 0) {
        return sign_bit;
    }

    const s32 new_exp = exp - 64;
    const u32 mant_12 = mant >> 11;
    if (new_exp < 0) {
        return 0;
    }
    if (new_exp > 0x7F) {
        return 0x7F000u | sign_bit;
    }

    return sign_bit | (static_cast<u32>(new_exp) << 12) | mant_12;
}

extern "C" void engine_func_003e9ba8(void** p_obj, void* target, const float* data) {
    if (p_obj == nullptr || *p_obj == nullptr) {
        return;
    }
    auto* const obj = static_cast<u8*>(*p_obj);
    const u32 type = *reinterpret_cast<const u32*>(obj + 0x14);
    auto* const dst = static_cast<u8*>(target);

    switch (type) {
    case 0:
    case 1:
    case 2:
    case 3: {
        const u32 offset = 0xBC + (type * 0x10);
        auto* const col = reinterpret_cast<float*>(dst + offset);
        col[0] = data[0];
        col[1] = data[1];
        col[2] = data[2];
        col[3] = data[3];
        const u32 packed = engine_func_002c2be8(col);
        *reinterpret_cast<u32*>(dst + 0xFC + (type * 4)) = packed;
        break;
    }
    case 4: {
        const float dx = data[0];
        const float dy = data[1];
        const float dz = data[2];
        const float len_sq = dx * dx + dy * dy + dz * dz;
        const float inv_len = 1.0f / inline_vsqrt_f32(len_sq);
        auto* const dir = reinterpret_cast<float*>(dst + 0x10C);
        dir[0] = dx * inv_len;
        dir[1] = dy * inv_len;
        dir[2] = dz * inv_len;
        break;
    }
    case 5: {
        const float near_dist = data[0];
        *reinterpret_cast<float*>(dst + 0x120) = near_dist;
        const float far_dist = *reinterpret_cast<const float*>(dst + 0x124);
        float diff = far_dist - near_dist;
        const float abs_diff = diff < 0.0f ? -diff : diff;
        if (abs_diff < 0.01f) {
            diff = 0.01f;
        }
        const float scale = 1.0f / diff;
        const float bias = -near_dist / diff;
        *reinterpret_cast<u32*>(dst + 0x128) = pack_pica_float20(scale);
        *reinterpret_cast<u32*>(dst + 0x12C) = pack_pica_float20(bias);
        break;
    }
    case 6: {
        const float far_dist = data[0];
        *reinterpret_cast<float*>(dst + 0x124) = far_dist;
        const float near_dist = *reinterpret_cast<const float*>(dst + 0x120);
        float diff = far_dist - near_dist;
        const float abs_diff = diff < 0.0f ? -diff : diff;
        if (abs_diff < 0.01f) {
            diff = 0.01f;
        }
        const float scale = 1.0f / diff;
        const float bias = -near_dist / diff;
        *reinterpret_cast<u32*>(dst + 0x128) = pack_pica_float20(scale);
        *reinterpret_cast<u32*>(dst + 0x12C) = pack_pica_float20(bias);
        break;
    }
    default:
        break;
    }
}

// DECOMP_FUNC(0x00150f54, 656)
//
// Two-slot blend/effect updater.  The object owns two 0x10-byte slots; each slot
// has two signed saturating counters (0x4C/0x50 and 0x2C/0x30) and two float
// ranges (0x44/0x48 and 0x24/0x28).  The counters are advanced, a clamped blend
// factor is published through 0x002A3418 when either counter moved, the slot's
// two type-2 elements are retired through 0x00153160 / 0x001531AC, then the
// object-level counters (0x0C/0x10 and 0x1C/0x20) advance and the final blend
// factor is published through 0x002BCE38.
//
// The callees below are still byte-preserved in their own translation units;
// these declarations recover the AAPCS contract observed at each call site:
//   0x002B4EB8  func_002b4eb8(void* obj, u32 slot)    - rearm the slot elements
//   0x002A3418  func_002a3418(s8 slot, f32 value)     - publish slot blend
//   0x00153160  func_00153160(void* element) -> u32   - slot 0 element alive?
//   0x001531AC  func_001531AC(void* element) -> u32   - slot 1 element alive?
//   0x002BB270  engine_func_002bb270() -> void*       - notification list head
//   0x001579D8  func_001579d8(void* list, u32 flags)  - OR the flag into entries
//   0x002BCE38  engine_func_002bce38(f32 value)       - publish object blend
extern "C" void func_002b4eb8(void* obj, u32 slot);
extern "C" void func_002a3418(s8 slot, f32 value);
extern "C" u32 func_00153160(void* element);
extern "C" u32 func_001531ac(void* element);
extern "C" void* engine_func_002bb270();
extern "C" void func_001579d8(void* list, u32 flags);
extern "C" void engine_func_002bce38(f32 value);

namespace {

constexpr s32 kSlotCount = 2;
constexpr s32 kElementCount = 2;
constexpr u32 kSlotStride = 0x10;
constexpr u32 kElementStride = 8;
constexpr u32 kFirstElementOffset = 0x2A0;
constexpr u32 kElementTypeOffset = 4;
constexpr u8 kActiveElementType = 2;
constexpr u32 kNotificationFlags = 0x40;
constexpr f32 kUnitScale = 1.0f;
constexpr f32 kClampMax = 1.0f;

// 0x151018..0x151034: greater than kClampMax saturates, values that are not
// less than zero (including unordered/NaN) pass through, otherwise zero.
inline f32 clamp_high(f32 value) {
    if (value > kClampMax) {
        return kClampMax;
    }
    if (!(value < 0.0f)) {
        return value;
    }
    return 0.0f;
}

// 0x151080..0x151098: greater than kClampMax saturates, then negative values
// become zero (unordered/NaN passes through untouched).
inline f32 clamp_low(f32 value) {
    if (value > kClampMax) {
        value = kClampMax;
    }
    if (value < 0.0f) {
        value = 0.0f;
    }
    return value;
}

// 0x150FD0..0x15100C and 0x151034..0x151078: at or past the limit the range's
// end value is used, otherwise start + (end - start) * counter / limit.
inline f32 lerp_counter(const u8* slot, u32 start_offset, u32 end_offset,
                        u32 counter_offset, u32 limit_offset) {
    const s32 counter = *reinterpret_cast<const s32*>(slot + counter_offset);
    const s32 limit = *reinterpret_cast<const s32*>(slot + limit_offset);
    if (counter >= limit) {
        return *reinterpret_cast<const f32*>(slot + end_offset);
    }
    const f32 start = *reinterpret_cast<const f32*>(slot + start_offset);
    const f32 end = *reinterpret_cast<const f32*>(slot + end_offset);
    return start + ((end - start) * static_cast<f32>(counter)) /
                       static_cast<f32>(limit);
}

}  // namespace

extern "C" void func_00150f54(void* object) {
    auto* const obj = static_cast<u8*>(object);

    for (s32 i = 0; i < kSlotCount; ++i) {
        u8* const slot = obj + static_cast<u32>(i) * kSlotStride;

        bool first_advanced = false;
        const s32 first_counter = *reinterpret_cast<const s32*>(slot + 0x50);
        if (first_counter < *reinterpret_cast<const s32*>(slot + 0x4C)) {
            *reinterpret_cast<s32*>(slot + 0x50) = first_counter + 1;
            first_advanced = true;
        }

        bool active;
        const s32 second_counter = *reinterpret_cast<const s32*>(slot + 0x30);
        if (second_counter < *reinterpret_cast<const s32*>(slot + 0x2C)) {
            const s32 advanced_counter = second_counter + 1;
            *reinterpret_cast<s32*>(slot + 0x30) = advanced_counter;
            if (advanced_counter >= *reinterpret_cast<const s32*>(slot + 0x2C)) {
                func_002b4eb8(object, static_cast<u32>(i) & 0xFFu);
            }
            active = true;
        } else {
            active = first_advanced;
        }

        if (active) {
            const f32 first_value = clamp_high(
                lerp_counter(slot, 0x44, 0x48, 0x50, 0x4C));
            const f32 second_value = clamp_low(
                lerp_counter(slot, 0x24, 0x28, 0x30, 0x2C));
            func_002a3418(static_cast<s8>(i),
                          second_value * (first_value * kUnitScale));
        }

        for (s32 j = 0; j < kElementCount; ++j) {
            u8* const element = slot + static_cast<u32>(j) * kElementStride +
                                kFirstElementOffset;
            void* const payload = *reinterpret_cast<void* const*>(element);
            if (payload == nullptr ||
                element[kElementTypeOffset] != kActiveElementType) {
                continue;
            }
            const u32 stays_alive = (j == 0) ? func_00153160(payload)
                                             : func_001531ac(payload);
            if (stays_alive == 0) {
                *reinterpret_cast<u32*>(element) = 0;
                element[kElementTypeOffset] = 0;
            }
        }
    }

    if (*reinterpret_cast<const s32*>(obj + 0x0C) >
        *reinterpret_cast<const s32*>(obj + 0x10)) {
        *reinterpret_cast<s32*>(obj + 0x10) =
            *reinterpret_cast<const s32*>(obj + 0x10) + 1;
        func_001579d8(engine_func_002bb270(), kNotificationFlags);
    }

    if (*reinterpret_cast<const s32*>(obj + 0x20) <
        *reinterpret_cast<const s32*>(obj + 0x1C)) {
        *reinterpret_cast<s32*>(obj + 0x20) =
            *reinterpret_cast<const s32*>(obj + 0x20) + 1;
        func_001579d8(engine_func_002bb270(), kNotificationFlags);
    }

    const f32 final_value = clamp_high(
        lerp_counter(obj, 0x14, 0x18, 0x20, 0x1C) * kUnitScale);
    engine_func_002bce38(final_value);
}

// Direct callees of camp_func_002583a4. 0x00340C30 fills two float pairs for
// the caller's view record, 0x002A2DDC resolves/mutates one selection slot,
// and 0x002C25F0 is a 4-byte veneer that tail-branches to func_0014782C.
extern "C" void camp_func_00340c30(void* object, float* out_pair_a,
                                   float* out_pair_b);
extern "C" void camp_func_002a2ddc(void** entry, const u32* key);
extern "C" void engine_func_002c25f0(void* object, u32 value);

namespace {

constexpr u32 kCampRuntimeGlobal = 0x0043DD90;
constexpr u32 kObjectRequiredFlags = 0x10000001;
constexpr u32 kChildActiveFlag = 0x40000000;
constexpr f32 kHalf = 0.5f;

inline u32 load_u32(const void* base, u32 offset) {
    return *reinterpret_cast<const u32*>(static_cast<const u8*>(base) + offset);
}

inline s32 load_s32(const void* base, u32 offset) {
    return *reinterpret_cast<const s32*>(static_cast<const u8*>(base) + offset);
}

inline s16 load_s16(const void* base, u32 offset) {
    return *reinterpret_cast<const s16*>(static_cast<const u8*>(base) + offset);
}

// Raw reads used where the original unconditionally dereferences an address it
// may have resolved to null; volatile keeps the load and its fault behaviour.
inline u32 raw_load_u32(u32 address) {
    return *reinterpret_cast<const volatile u32*>(
        static_cast<u32>(address));
}

inline s32 raw_load_s32(u32 address) {
    return *reinterpret_cast<const volatile s32*>(
        static_cast<u32>(address));
}

// Node fields that hold a relative offset: zero means the node is absent,
// otherwise the target is the field address plus the offset.
inline u8* resolve_relative(u32 field_address) {
    const u32 offset = raw_load_u32(field_address);
    return offset != 0 ? reinterpret_cast<u8*>(field_address + offset)
                       : nullptr;
}

}  // namespace

// DECOMP_FUNC(0x002583a4, 664)
// Camp-scene transform pass. `self` is the caller's render/view record; every
// caller passes <camp work> + 0x38. The global at 0x0043DD90 supplies the camp
// manager, whose +0x194 and +0x298 fields are the two signed entry counts.
// Phase 1 walks the render object selected by manager[0x94 + 4*i] and adds the
// 0x00340C30 offset pair to each float pair referenced by the selected child
// element. Phase 2 re-resolves the manager[0x198 + 4*i] selection, notifies
// 0x002A2DDC, and clears the +0x2B0 word of its group record. The original
// leaves the manager's +0x298 load in r0 on every return path.
extern "C" u32 camp_func_002583a4(void* self) {
    u8* const manager = *reinterpret_cast<u8**>(kCampRuntimeGlobal);

    float unused_pair[2];
    float offset_pair[2];
    camp_func_00340c30(self, unused_pair, offset_pair);

    // Phase 1: manager entries at +0x94 (object selector) and +0x96 (element
    // key selector), one 4-byte slot per index.
    for (s32 i = 0; i < load_s32(manager, 0x194); ++i) {
        u8* const slot = manager + static_cast<u32>(i) * 4;

        u8* object_root = *reinterpret_cast<u8**>(manager + 0x84);
        object_root = *reinterpret_cast<u8**>(object_root + 8);
        object_root = *reinterpret_cast<u8**>(object_root + 0x2C);
        object_root = *reinterpret_cast<u8**>(object_root + 8);

        // ARM relative-offset table at object_root + 0xC8.
        const u32 table_address = reinterpret_cast<u32>(object_root) + 0xC8;
        const u32 table_offset = raw_load_u32(table_address);
        const u32 table_base = table_offset != 0 ? table_address + table_offset
                                                 : 0u;
        const u32 object_slot =
            table_base + static_cast<u32>(load_s16(slot, 0x94)) * 4u;
        u8* const object = resolve_relative(object_slot);

        // All bits of 0x10000001 must be set; other bits are ignored.
        if (object == nullptr ||
            (load_u32(object, 0) & kObjectRequiredFlags) !=
                kObjectRequiredFlags) {
            continue;
        }

        const s32 child_count = load_s32(object, 0x38);
        for (s32 child_index = 0; child_index < child_count; ++child_index) {
            const u32 child_table_field = reinterpret_cast<u32>(object) + 0x3C;
            const u32 child_table_offset = raw_load_u32(child_table_field);
            const u32 child_table_base =
                child_table_offset != 0 ? child_table_field + child_table_offset
                                        : 0u;
            const u32 child_slot =
                child_table_base + static_cast<u32>(child_index) * 4u;
            u8* const child = resolve_relative(child_slot);

            if (child == nullptr ||
                (load_u32(child, 0) & kChildActiveFlag) == 0) {
                continue;
            }

            const u32 data_offset = load_u32(child, 0x18);
            const u32 element_count = load_u32(child, 0x28);
            const u32 data_span = load_u32(child, 0x14);
            const u32 data_base =
                data_offset != 0
                    ? reinterpret_cast<u32>(child) + 0x18 + data_offset
                    : 0u;
            const s32 match_key = load_s16(slot, 0x96) + 4;

            for (u32 element_index = 0; element_index < element_count;
                 ++element_index) {
                const u32 element_table_field =
                    reinterpret_cast<u32>(child) + 0x2C;
                const u32 element_table_offset =
                    raw_load_u32(element_table_field);
                const u32 element_table_base =
                    element_table_offset != 0
                        ? element_table_field + element_table_offset
                        : 0u;
                const u32 element_slot =
                    element_table_base + element_index * 4u;
                u8* const element = resolve_relative(element_slot);

                // A null element still faults at element + 4 in the original.
                if (raw_load_s32(reinterpret_cast<u32>(element) + 4) !=
                    match_key) {
                    continue;
                }

                const s32 data_index =
                    raw_load_s32(reinterpret_cast<u32>(element) + 0x30);
                if (data_index < 0) {
                    break;
                }

                u32 cursor = data_base + static_cast<u32>(data_index);
                const u32 end = data_base + data_span;
                if (cursor < end) {
                    const u32 stride = load_u32(child, 0x24);
                    do {
                        f32 x = *reinterpret_cast<const f32*>(cursor);
                        f32 y = *reinterpret_cast<const f32*>(cursor + 4);
                        x = x - kHalf;
                        y = y - kHalf;
                        x = x + kHalf;
                        y = y + kHalf;
                        *reinterpret_cast<f32*>(cursor) = x;
                        *reinterpret_cast<f32*>(cursor + 4) = y;
                        x = x + offset_pair[0];
                        y = y + offset_pair[1];
                        *reinterpret_cast<f32*>(cursor) = x;
                        *reinterpret_cast<f32*>(cursor + 4) = y;
                        cursor += stride;
                    } while (cursor < end);
                }

                engine_func_002c25f0(reinterpret_cast<void*>(data_base),
                                     data_span);
            }
        }
    }

    // Phase 2: manager entries at +0x198 (group/table selector), +0x19A
    // (relative slot selector) and a 0x2B0 reset on the selected group.
    for (s32 i = 0; i < load_s32(manager, 0x298); ++i) {
        u8* chain = *reinterpret_cast<u8**>(manager + 0x84);
        chain = *reinterpret_cast<u8**>(chain + 8);
        chain = *reinterpret_cast<u8**>(chain + 0x2C);

        const u8* const slot =
            manager + 0x100 + static_cast<u32>(i) * 4;
        const u32 lookup = load_u32(chain, 0x164);
        const u32 entry =
            load_u32(reinterpret_cast<const void*>(lookup),
                     static_cast<u32>(load_s16(slot, 0x98)) * 4u);
        const u32 group = load_u32(reinterpret_cast<const void*>(entry), 0x3C);

        const u32 group_slot =
            group + 0x274 + static_cast<u32>(load_s16(slot, 0x9A)) * 4u;
        u8* selected = resolve_relative(group_slot);

        // The original reads selected + 8 before discarding the value; keep
        // the read so a null selection faults at address 8 as it did.
        (void)raw_load_u32(reinterpret_cast<u32>(selected) + 8);

        const u32* const key =
            reinterpret_cast<const u32*>(load_u32(self, 0xC));
        camp_func_002a2ddc(reinterpret_cast<void**>(&selected), key);
        *reinterpret_cast<u32*>(group + 0x2B0) = 0;
    }

    return load_u32(manager, 0x298);
}

// 0x001188d0: UI list-panel refresh. The status byte gates the whole body,
// the kind byte selects one of two 0x2BF6D0 node lists, and a UI command is
// pushed onto render layer 3 for the duration of the body and popped after it.
extern "C" u32 ui_func_002c5f7c(u32 mode, u32 sub_mode);
extern "C" void func_002befdc(u8* base, u32 group, u32 value);
extern "C" u32 func_002bef88(u8* base, u32 group);
extern "C" u8* camp_func_002bf6d0(u32 group, u32 node_index);
extern "C" void ui_func_002bda00(u8* render, u32 v1, u32 v2, f32 value);
extern "C" void func_002b792c(u8* render, s32 x, s32 y, u32 arg3, f32 scale,
                              u32 arg5, u32 arg6);
extern "C" u32 func_002bf558(u32 arg0, u32 arg1, u32 arg2, s32 arg3,
                             s32 arg4, s32 arg5);
extern "C" f32 func_00126754(u8* render, u32 index);

// DECOMP_FUNC(0x001188d0, 660)
// Panel layout proven by the ARM: +0x04 render object pointer, +0x08 status
// byte (1 or 5 accepted), +0x09 kind byte (0x0B list / 0x13 grid), +0x18
// signed selected row, +0x20 signed row count.
extern "C" void ui_func_001188d0(u8* panel) {
    const u8 status = panel[8];
    if (status != 1 && status != 5) {
        return;
    }

    // Push the 0xF10 viewport command on the layer-3 render stack.
    func_002befdc(*reinterpret_cast<u8**>(0x0044EA00), 3,
                  ui_func_002c5f7c(1, 0));

    const u8 kind = panel[9];
    if (kind == 0x0B) {
        // Nine candidate node ids; the panel count selects the list window.
        static const s32 kNodeIds[9] = {0xA8, 0xA9, 0x9C, 0x9D, 0x9E,
                                        0xB0, 0xB1, 0xB2, 0xB3};
        const s32 count = *reinterpret_cast<const s32*>(panel + 0x20);
        s32 window = 0;
        if (count == 3) {
            window = 2;
        } else if (count == 4) {
            window = 5;
        }

        if (count > 0) {
            s32 index = 0;
            do {
                const u8* const node = camp_func_002bf6d0(
                    0x0E, static_cast<u32>(kNodeIds[window + index]));
                u8* const render = *reinterpret_cast<u8**>(panel + 4);
                if (*reinterpret_cast<const s32*>(panel + 0x18) == index) {
                    *reinterpret_cast<u32*>(render + 0xB0) = 0x0A;
                    ui_func_002bda00(render, 0, 0xFFFFFFFFu, 0.0f);
                } else {
                    *reinterpret_cast<u32*>(render + 0xB0) = 0x0B;
                    ui_func_002bda00(render, 0, 0x5A5A5AFFu, 0.0f);
                }
                func_002b792c(
                    *reinterpret_cast<u8**>(panel + 4),
                    *reinterpret_cast<const s16*>(node + 8),
                    static_cast<s32>(*reinterpret_cast<const s16*>(node + 0x0A)) - 4,
                    0x33, 1.0f, 6, static_cast<u32>(index));
                ++index;
            } while (*reinterpret_cast<const s32*>(panel + 0x20) > index);
        }

        // Both handled kinds share the original's post-loop render reset.
        *reinterpret_cast<u32*>(*reinterpret_cast<u8**>(panel + 4) + 0xB0) = 0;
        ui_func_002bda00(*reinterpret_cast<u8**>(panel + 4), 0, 0x646464FFu,
                         0.0f);
    } else if (kind == 0x13) {
        const u8* const origin = camp_func_002bf6d0(0x3A, 0x97);
        if (*reinterpret_cast<const s32*>(panel + 0x20) > 0) {
            s32 index = 0;
            do {
                const u8* const node = camp_func_002bf6d0(
                    0x3A, static_cast<u32>(index) + 0x98);
                const s32 node_x = *reinterpret_cast<const s16*>(node + 8);
                const s32 node_y = *reinterpret_cast<const s16*>(node + 0x0A);
                if (*reinterpret_cast<const s32*>(panel + 0x18) == index) {
                    // The fifth and sixth arguments are the row y extent and
                    // the 0x0B panel kind; 0x2BF558 consumes both.
                    func_002bf558(2, 0x3A, 0x12, node_x, node_y, 0x0B);
                    *reinterpret_cast<u32*>(
                        *reinterpret_cast<u8**>(panel + 4) + 0xB0) = 0x0F;
                } else {
                    func_002bf558(2, 0x3A, 0x11, node_x, node_y, 0x0B);
                    *reinterpret_cast<u32*>(
                        *reinterpret_cast<u8**>(panel + 4) + 0xB0) = 0x0E;
                }
                // 0x126754 returns the row scale as a float. Both the origin
                // extent and that scale are halved with an arithmetic shift
                // (round toward -infinity, not truncation).
                const s32 scale = static_cast<s32>(func_00126754(
                    *reinterpret_cast<u8**>(panel + 4),
                    static_cast<u32>(index)));
                const u8* const anchor =
                    *reinterpret_cast<u8* const*>(origin + 0x0C);
                const s32 anchor_x = *reinterpret_cast<const s16*>(anchor);
                const u32 x =
                    static_cast<u32>(*reinterpret_cast<const s16*>(origin + 8)) +
                    static_cast<u32>(node_x) +
                    static_cast<u32>(anchor_x >> 1) -
                    static_cast<u32>(scale >> 1);
                const u32 y =
                    static_cast<u32>(*reinterpret_cast<const s16*>(origin + 0x0A)) +
                    static_cast<u32>(node_y);
                func_002b792c(*reinterpret_cast<u8**>(panel + 4),
                              static_cast<s32>(x), static_cast<s32>(y),
                              0x33, 1.0f, 6, static_cast<u32>(index));
                ++index;
            } while (*reinterpret_cast<const s32*>(panel + 0x20) > index);
        }

        *reinterpret_cast<u32*>(*reinterpret_cast<u8**>(panel + 4) + 0xB0) = 0;
        ui_func_002bda00(*reinterpret_cast<u8**>(panel + 4), 0, 0x646464FFu,
                         0.0f);
    }

    func_002bef88(*reinterpret_cast<u8**>(0x0044EA00), 3);
}

// DECOMP_FUNC(0x003abd08, 668)
//
// Camp party-row draw. `ctx` is the camp work object, `work` the layout key
// base, `index` selects one 0x20-byte record slot at ctx + 0x5A8, `flag`
// selects the selected (non-zero) or plain (zero) layout/label/constant set,
// and `arg5` is an opaque row word that is also converted to the
// (0x100 - arg5) / 0x100 text scale. The slot's u16 id is read twice: the early
// copy feeds 0x2890D0 and the copy made after 0x22D994 feeds 0x262EDC, so the
// two loads are kept at their original program points.
namespace camp_bd08 {

constexpr u32 kLayoutBaseOffset = 0xC8;    // table pointer passed to lookups
constexpr u32 kLayoutPlainKey = 0x40E;     // work-relative key, flag == 0
constexpr u32 kLayoutSelectedKey = 0x42F;  // work-relative key, flag != 0
constexpr u32 kModeByteOffset = 0x56D;     // signed mode selector, flag != 0

constexpr u32 kRowSlotStride = 0x20;       // ctx + 0x5A8 + index*0x20
constexpr u32 kRowIdOffset = 0x5AC;        // u16 id inside the slot
constexpr u32 kRowValueOffset = 0x5B4;     // s32 formatted with "%8d"
constexpr u32 kRowTextOffset = 0x5C8;      // text pointer forwarded to 0x2BE744

constexpr u32 kAnchorXOffset = 8;          // s16 x inside a layout record
constexpr u32 kAnchorYOffset = 0xA;        // s16 y inside a layout record

constexpr u32 kFrameModePlain = 2;         // r1 for 0x2BE744, flag == 0
constexpr u32 kFrameModeSelected = 3;      // r1 for 0x2BE744, flag != 0
constexpr u32 kFrameKeyPlain = 0x4CE;      // lookup key for the frame record
constexpr u32 kFrameKeySelected = 0x4E0;
constexpr u32 kBarLabelPlain = 0x4CD;      // 0x2BF6C8 label for the bar row
constexpr u32 kBarLabelSelected = 0x476;
constexpr u32 kBarHelperSelected = 0x4DF;  // 0x231D60 id = 0x476 + 0x69
constexpr u32 kTextLabelPlain = 0x4DE;     // 0x2BF6C8 label for the text
constexpr u32 kTextLabelSelected = 0x4F0;

constexpr u32 kColorPlain = 0xFF;          // 0x2BE744 rgba, flag == 0
constexpr u32 kColorSelected = 0xFFFFFFFF; // 0x2BE744 rgba, flag != 0
constexpr u32 kColorHasItems = 0x5A5A5AFF; // replaces the rgba when 0x262EDC
constexpr u32 kDrawConstant = 0xFFFFFFFF;  // third stack word for 0x230C80

constexpr f32 kScaleUnit = 0.00390625f;    // 1/256, applied after int convert
constexpr f32 kZero = 0.0f;
constexpr f32 kOne = 1.0f;

constexpr s32 kNoBars = 0;                 // 0x2B6F74 draw-bars stack word
constexpr s32 kNoRowOffset = 0;            // 0x2B6F74 row-offset stack word
constexpr int kDrawMode = 0;               // 0x230C80 r1
constexpr int kDrawWidthIndex = 7;         // 0x230C80 second stack word

}  // namespace camp_bd08

extern "C" u8* camp_func_002bf6c8(void* table, u32 key);
extern "C" void ui_func_0022d994(void* ctx, void* work, u32 frame, int mode);
extern "C" u32 camp_func_00262edc(u16 target_id);
extern "C" void func_002be744(const void* rect, int font_id, u32 rgba,
                              const char* text, f32 x, f32 y, f32 scale_x,
                              f32 rotation, f32 scale_y);
// 0x231D60 reads its two trailing arguments from the stack with `vldmia`, so
// they are architected stack words (raw float bit patterns), not VFP arguments.
extern "C" void camp_func_00231d60(void* map_state, s32 id, s32 x, s32 y,
                                   u32 a_bits, u32 b_bits);
extern "C" void func_00231d4c(const void* src, f32* out);
extern "C" u32 camp_func_002890d0(u32 id);
extern "C" void camp_func_002b6f74(s16 demon_id, s32 x, s32 y, s32 prio,
                                   s32 draw_bars, s32 a5);
extern "C" u32 ui_func_002be7fc(char* dst, const char* format, ...);
extern "C" void func_00230c80(void* gfx, int mode, int x, int y, int arg0,
                              int arg1, u32 constant, u32 frame,
                              const char* text);

extern "C" void camp_func_003abd08(void* ctx, void* work, u32 index, u32 flag,
                                   u32 arg5) {
    using namespace camp_bd08;

    u8* const ctx_bytes = static_cast<u8*>(ctx);
    u8* const work_bytes = static_cast<u8*>(work);

    // 0x3ABD24..0x3ABD48: (s32)(0x100 - arg5) converted to float, then / 256.
    const f32 scale =
        static_cast<f32>(static_cast<s32>(0x100u - arg5)) * kScaleUnit;

    // `sl` in the original: ctx + index*0x20, reused for every slot read.
    u8* const slot = ctx_bytes + (index * kRowSlotStride);

    // Early id copy, kept in the frame until 0x2890D0 (no reload before it).
    const u16 early_id = *reinterpret_cast<const u16*>(slot + kRowIdOffset);

    const u8* const layout = camp_func_002bf6c8(
        ctx_bytes + kLayoutBaseOffset,
        flag == 0 ? reinterpret_cast<u32>(work_bytes + kLayoutPlainKey)
                  : reinterpret_cast<u32>(work_bytes + kLayoutSelectedKey));
    const s32 base_x = *reinterpret_cast<const s16*>(layout + kAnchorXOffset);
    const s32 base_y = *reinterpret_cast<const s16*>(layout + kAnchorYOffset);

    u32 frame_mode;  // r1 for 0x2BE744 (plain/selected font mode)
    u32 frame_key;   // lookup key for the frame record
    u32 color;       // forwarded to 0x2BE744
    if (flag == 0) {
        frame_mode = kFrameModePlain;
        frame_key = kFrameKeyPlain;
        color = kColorPlain;
    } else {
        ui_func_0022d994(
            ctx, work, arg5,
            *reinterpret_cast<const s8*>(ctx_bytes + kModeByteOffset));
        frame_mode = kFrameModeSelected;
        frame_key = kFrameKeySelected;
        color = kColorSelected;
    }

    // Id reload after 0x22D994 (the slot may have changed in between).
    const u16 current_id =
        *reinterpret_cast<const u16*>(slot + kRowIdOffset);
    if (camp_func_00262edc(current_id) != 0) {
        color = kColorHasItems;
    }

    const u32 text_word = *reinterpret_cast<const u32*>(slot + kRowTextOffset);

    const u8* const frame_record =
        camp_func_002bf6c8(ctx_bytes + kLayoutBaseOffset, frame_key);
    const s32 frame_x =
        *reinterpret_cast<const s16*>(frame_record + kAnchorXOffset) + base_x;
    const s32 frame_y =
        *reinterpret_cast<const s16*>(frame_record + kAnchorYOffset) + base_y;

    func_002be744(ctx_bytes + kLayoutBaseOffset,
                  static_cast<int>(frame_mode), color,
                  reinterpret_cast<const char*>(text_word),
                  static_cast<f32>(frame_x), static_cast<f32>(frame_y), scale,
                  kZero, kOne);

    u32 bar_label;
    if (flag == 0) {
        bar_label = kBarLabelPlain;
    } else {
        bar_label = kBarLabelSelected;
        camp_func_00231d60(ctx_bytes + kLayoutBaseOffset, kBarHelperSelected,
                           base_x, base_y, arg5, 1u);
    }

    const u8* const bar_record =
        camp_func_002bf6c8(ctx_bytes + kLayoutBaseOffset, bar_label);
    f32 offset[2];
    func_00231d4c(ctx_bytes + kLayoutBaseOffset, offset);
    // The integer anchor sums are converted to float, offset by the copied
    // pair and truncated back with vcvt.s32.f32.
    const s32 bar_x = static_cast<s32>(
        static_cast<f32>(*reinterpret_cast<const s16*>(
                             bar_record + kAnchorXOffset) +
                         base_x) +
        offset[0]);
    const s32 bar_y = static_cast<s32>(
        static_cast<f32>(*reinterpret_cast<const s16*>(
                             bar_record + kAnchorYOffset) +
                         base_y) +
        offset[1]);

    const s16 bars_id = static_cast<s16>(camp_func_002890d0(early_id));
    camp_func_002b6f74(bars_id, bar_x, bar_y, static_cast<s32>(arg5), kNoBars,
                       kNoRowOffset);

    char text[0x20];
    const s32 row_value =
        *reinterpret_cast<const s32*>(slot + kRowValueOffset);
    ui_func_002be7fc(text, "%8d", row_value);

    const u8* const text_record = camp_func_002bf6c8(
        ctx_bytes + kLayoutBaseOffset,
        flag == 0 ? kTextLabelPlain : kTextLabelSelected);
    const s32 text_x =
        *reinterpret_cast<const s16*>(text_record + kAnchorXOffset) + base_x;
    const s32 text_y =
        *reinterpret_cast<const s16*>(text_record + kAnchorYOffset) + base_y;
    func_00230c80(ctx_bytes + kLayoutBaseOffset, kDrawMode, text_x, text_y, 0,
                  kDrawWidthIndex, kDrawConstant, arg5, text);
}

// DECOMP_FUNC(0x0032fc54, 672)
//
// Issues one, two or three glyph-run draws from a 0x38-byte request block.
// The request carries two byte-table indices (0x0C..0x30), two extent words
// that must match, two flag bits and a helper-ready word (0x34).  Each index
// selects one byte from each of two 0x25-byte rows of the table at
// 0x0040B828; a nonzero row pair enables that draw.  Draws are issued through
// six global function-pointer slots whose pinned image contents are
//   <= 0x100: func_00167244 (first descriptor) / func_00167274 (next two)
//   <= 0x200: func_0016AFBC (first)            / func_0016AFEC (next two)
//   <= 0x400: func_001634CC (first)            / func_001634FC (next two)
// The slot addresses below are the load targets of the original `ldr/ldr/blx`
// sequences, so the indirect dispatch is preserved exactly.  Every renderer
// receives a seven-word descriptor on the stack in r0; its return value is not
// used by this function (r0 is reloaded before the next observation).
namespace leaf_fc54 {

// Request block built by the caller at 0x3F5FD0..0x3F60B4 and passed in r0.
// Every access in the original is a 32-bit load; the block is 0x38 bytes.
struct Request {
    u32 word_00;  // descriptor word 0, primary draw
    u32 word_04;  // descriptor word 0, secondary draw
    u32 word_08;  // descriptor word 0, third draw
    u32 word_0C;  // descriptor word 1, primary draw
    u32 word_10;  // descriptor word 1, secondary draw
    u32 word_14;  // descriptor word 1, third draw
    u32 word_18;  // descriptor word 2 (halved for the secondary pair)
    u32 word_1C;  // descriptor word 3 (halved for the secondary pair)
    u32 word_20;  // extent, must equal word_24; selects the renderer class
    u32 word_24;  // extent, must equal word_20
    u32 word_28;  // first table index, 0x0C..0x30
    u32 word_2C;  // second table index, 0x0C..0x30
    u32 word_30;  // flag bits: bit 0 primary draw, bit 1 secondary/third draw
    u32 word_34;  // 0: not ready; 1: issue renderer calls
};
static_assert(sizeof(Request) == 0x38);

// Seven-word argument block placed on the stack and passed in r0.
struct DrawArgs {
    u32 word_00;
    u32 word_04;
    u32 word_08;
    u32 word_0C;
    u32 word_10;
    u32 word_14;
    u32 word_18;
};
static_assert(sizeof(DrawArgs) == 0x1C);

using DrawFn = void (*)(const DrawArgs*);

// Two 0x25-byte rows indexed by the raw request index (0x0C..0x30), plus the
// third-row pointer forwarded as the last descriptor word.
constexpr u32 kTableAddr = 0x0040B828;
constexpr u32 kTableRowStride = 0x25;
constexpr u32 kTableExtraOffset = 0x56;

constexpr u32 kIndexMin = 0x0C;
constexpr u32 kIndexCount = 0x25;  // 0x0C..0x30 inclusive

constexpr u32 kExtentSmallMax = 0x100;
constexpr u32 kExtentMediumMax = 0x200;
constexpr u32 kExtentLargeMax = 0x400;

constexpr u32 kModeReady = 1;
constexpr u32 kFlagPrimary = 1;
constexpr u32 kFlagSecondary = 2;

// Global function-pointer slots; the pinned image contents are the six
// renderers listed above.
constexpr u32 kSlotSmallFirst = 0x001672A4;   // -> func_00167244
constexpr u32 kSlotSmallNext = 0x001672A8;    // -> func_00167274
constexpr u32 kSlotMediumFirst = 0x0016B01C;  // -> func_0016AFBC
constexpr u32 kSlotMediumNext = 0x0016B020;   // -> func_0016AFEC
constexpr u32 kSlotLargeFirst = 0x0016352C;   // -> func_001634CC
constexpr u32 kSlotLargeNext = 0x00163530;    // -> func_001634FC

constexpr s32 kErrorNotReady = -1;        // mvn r0,#0
constexpr s32 kErrorExtentMismatch = -3;  // mvn r0,#2
constexpr s32 kErrorIndex = -4;           // mvn r0,#3
constexpr s32 kErrorExtentTooLarge = -5;  // mvn r0,#4

inline void call_slot(u32 slot, const DrawArgs* args) {
    const DrawFn renderer = *reinterpret_cast<const DrawFn*>(slot);
    renderer(args);
}

// Issues one draw through the slot triplet selected by the request extent.
// The call is skipped unless word_34 == 1; returns false when the extent
// exceeds 0x400 (the original returns -5 in that case).
inline bool draw_for_extent(const Request* request, u32 slot_small,
                            u32 slot_medium, u32 slot_large,
                            const DrawArgs* args) {
    const u32 extent = request->word_20;
    if (extent <= kExtentSmallMax) {
        if (request->word_34 == kModeReady) {
            call_slot(slot_small, args);
        }
    } else if (extent <= kExtentMediumMax) {
        if (request->word_34 == kModeReady) {
            call_slot(slot_medium, args);
        }
    } else if (extent <= kExtentLargeMax) {
        if (request->word_34 == kModeReady) {
            call_slot(slot_large, args);
        }
    } else {
        return false;
    }
    return true;
}

}  // namespace leaf_fc54

extern "C" s32 func_0032fc54(leaf_fc54::Request* request) {
    using namespace leaf_fc54;

    if (request->word_34 == 0) {
        return kErrorNotReady;
    }
    if (request->word_20 != request->word_24) {
        return kErrorExtentMismatch;
    }

    const u32 first_index = request->word_28;
    if (first_index - kIndexMin >= kIndexCount) {
        return kErrorIndex;
    }
    const u32 second_index = request->word_2C;
    if (second_index < kIndexMin || second_index > kIndexMin + kIndexCount - 1) {
        return kErrorIndex;
    }

    const u8* const table = reinterpret_cast<const u8*>(kTableAddr);
    const u32 primary_flags = request->word_30;
    const u8 first_row0 = table[first_index];
    const u8 first_row1 = table[first_index + kTableRowStride];
    const u8 second_row0 = table[second_index];
    const u8 second_row1 = table[second_index + kTableRowStride];
    const u32 table_extra = reinterpret_cast<u32>(table + kTableExtraOffset);

    s32 result = 0;

    if ((primary_flags & kFlagPrimary) != 0 && first_row0 != 0 &&
        first_row1 != 0) {
        DrawArgs args;
        args.word_00 = request->word_00;
        args.word_04 = request->word_0C;
        args.word_08 = request->word_18;
        args.word_0C = request->word_1C;
        args.word_10 = first_row0;
        args.word_14 = first_row1;
        args.word_18 = table_extra;
        result = 1;

        if (!draw_for_extent(request, kSlotSmallFirst, kSlotMediumFirst,
                             kSlotLargeFirst, &args)) {
            return kErrorExtentTooLarge;
        }
    }

    if ((request->word_30 & kFlagSecondary) != 0 && second_row0 != 0 &&
        second_row1 != 0) {
        DrawArgs args;
        args.word_00 = request->word_04;
        args.word_04 = request->word_10;
        args.word_08 = request->word_18 >> 1;
        args.word_0C = request->word_1C >> 1;
        args.word_10 = second_row0;
        args.word_14 = second_row1;
        args.word_18 = table_extra;
        result |= 2;

        if (!draw_for_extent(request, kSlotSmallNext, kSlotMediumNext,
                             kSlotLargeNext, &args)) {
            return kErrorExtentTooLarge;
        }

        args.word_00 = request->word_08;
        args.word_04 = request->word_14;
        if (!draw_for_extent(request, kSlotSmallNext, kSlotMediumNext,
                             kSlotLargeNext, &args)) {
            return kErrorExtentTooLarge;
        }
    }

    return result;
}
// DECOMP_FUNC(0x001a1954, 676)
//
// Publishes the current camp/UI context into the UI work base held at
// *(0x0043E2A8 + 4). An 0x80-byte record is assembled at the start of that
// work base and then copied to work+0x24794.
extern "C" void ui_func_002bcf58(void* dst, const void* src, u32 size);
extern "C" bool script_vm_func_002c0ba8(u32 flag_id);
extern "C" s32 engine_func_002891e0(s32 id);

namespace ui_1a1954 {

constexpr u32 kManagerAddr = 0x0043E2A8;    // UI manager singleton
constexpr u32 kHandleField = 0x04;          // work base = *(u32*)(kManagerAddr + 4)
constexpr u32 kPublishOffset = 0x24794;     // snapshot destination inside work base
constexpr u32 kPublishSize = 0x80;
constexpr u32 kStatusByteOffset = 0x24BB0;  // work-base flag byte

constexpr u32 kFlagStatus0 = 0x67A;         // status bits 0..3
constexpr u32 kFlagStatus1 = 0x67B;
constexpr u32 kFlagStatus2 = 0x679;
constexpr u32 kFlagStatus3 = 0x678;
constexpr u32 kFlagExtra = 0x410;           // out[0x64] enable

constexpr u32 kRecordTableOffset = 0x90;      // first 0x604-byte record
constexpr u32 kRecordStride = 0x604;
constexpr u32 kRecordFieldOffset = 0x4A;      // u16 field inside a record
constexpr u32 kRecordSelectorOffset = 0x910C; // three signed record indices

constexpr s32 kEngineStateSpecial = 3;        // result that substitutes 1000
constexpr u16 kEngineStateOverride = 1000;
constexpr u16 kEngineStateSentinel = 0x18;    // out[0x58] value re-checked below
constexpr u8 kRotatedMode = 2;                // ctx[2] value that zeroes rows

inline u8* work_base() {
    return reinterpret_cast<u8*>(
        reinterpret_cast<u32*>(kManagerAddr)[kHandleField / 4]);
}

} // namespace ui_1a1954

extern "C" void ui_func_001a1954(u8* ctx) {
    using namespace ui_1a1954;

    u8* const out = work_base();

    *reinterpret_cast<u16*>(out + 0x4E) = *reinterpret_cast<u16*>(ctx + 0x00);
    ui_func_002bcf58(out, ctx + 0x54, 0x12);
    out[0x10] = 0;

    *reinterpret_cast<u32*>(out + 0x12) = *reinterpret_cast<u32*>(ctx + 0x08);
    *reinterpret_cast<u32*>(out + 0x16) = *reinterpret_cast<u32*>(ctx + 0x0C);
    *reinterpret_cast<u32*>(out + 0x1A) = *reinterpret_cast<u32*>(ctx + 0x10);
    *reinterpret_cast<u16*>(out + 0x1E) = *reinterpret_cast<u16*>(ctx + 0x14);
    *reinterpret_cast<u32*>(out + 0x20) = *reinterpret_cast<u32*>(ctx + 0x38);
    *reinterpret_cast<u16*>(out + 0x24) = *reinterpret_cast<u16*>(ctx + 0x32);
    *reinterpret_cast<u16*>(out + 0x26) = *reinterpret_cast<u16*>(ctx + 0x34);

    ui_func_002bcf58(out + 0x30, ctx + 0x24, 0x0E);

    *reinterpret_cast<u32*>(out + 0x3E) = *reinterpret_cast<u32*>(ctx + 0x16);
    *reinterpret_cast<u32*>(out + 0x42) = *reinterpret_cast<u32*>(ctx + 0x1A);
    *reinterpret_cast<u32*>(out + 0x46) = *reinterpret_cast<u32*>(ctx + 0x1E);
    *reinterpret_cast<u16*>(out + 0x4A) = *reinterpret_cast<u16*>(ctx + 0x22);
    out[0x4C] = ctx[0x7E];

    out[0x4D] = 0;
    if (script_vm_func_002c0ba8(kFlagStatus0)) {
        out[0x4D] |= 0x01;
    }
    if (script_vm_func_002c0ba8(kFlagStatus1)) {
        out[0x4D] |= 0x02;
    }
    if (script_vm_func_002c0ba8(kFlagStatus2)) {
        out[0x4D] |= 0x04;
    }
    if (script_vm_func_002c0ba8(kFlagStatus3)) {
        out[0x4D] |= 0x08;
    }

    *reinterpret_cast<u32*>(out + 0x50) = *reinterpret_cast<u32*>(ctx + 0x1F458);
    *reinterpret_cast<u32*>(out + 0x54) = 0;

    *reinterpret_cast<u16*>(out + 0x58) = ctx[0xA839];
    *reinterpret_cast<u16*>(out + 0x5A) = ctx[0xA83A];
    if (engine_func_002891e0(ctx[0xA839]) == kEngineStateSpecial) {
        *reinterpret_cast<u16*>(out + 0x58) = kEngineStateOverride;
    }

    const u8 alternate = ctx[0xA83B];
    if (alternate != 0) {
        *reinterpret_cast<u16*>(out + 0x5A) = alternate;
    } else if (*reinterpret_cast<u16*>(out + 0x58) == kEngineStateSentinel) {
        const s8 delta = static_cast<s8>(ctx[0xAFCA]);
        if (delta != 0) {
            *reinterpret_cast<u16*>(out + 0x58) =
                static_cast<u16>(static_cast<s32>(delta) +
                                 static_cast<s32>(kEngineStateOverride));
        } else {
            *reinterpret_cast<u16*>(out + 0x5A) = alternate;
        }
    }

    out[0x63] = work_base()[kStatusByteOffset];
    out[0x64] = script_vm_func_002c0ba8(kFlagExtra) ? 1 : 0;
    if (out[0x4D] == 0) {
        *reinterpret_cast<u16*>(out + 0x66) = 0;
    }

    out[0x62] = ctx[0x02];
    if (ctx[0x02] == kRotatedMode) {
        *reinterpret_cast<u16*>(out + 0x5C) = 0;
        *reinterpret_cast<u16*>(out + 0x5E) = 0;
        *reinterpret_cast<u16*>(out + 0x60) = 0;
    } else {
        for (u32 slot = 0; slot < 3; ++slot) {
            const s8 index =
                static_cast<s8>(ctx[kRecordSelectorOffset + slot]);
            u16 value = 0;
            if (index >= 0) {
                const u8* const record =
                    ctx + kRecordTableOffset +
                    static_cast<u32>(index) * kRecordStride;
                value = *reinterpret_cast<const u16*>(
                    record + kRecordFieldOffset);
            }
            *reinterpret_cast<u16*>(out + 0x5C + slot * 2) = value;
        }
    }

    ui_func_002bcf58(work_base() + kPublishOffset, out, kPublishSize);
}

// DECOMP_FUNC(0x00137730, 680)
extern "C" __attribute__((naked)) void battle_func_00137730() {
    asm volatile(
        ".arm\n"
        ".hword 0x5fff, 0xe92d, 0x4000, 0xe1a0\n"
        ".hword 0x704c, 0xe28d, 0x0801, 0xe897\n"
        ".hword 0x1038, 0xe59d, 0x5048, 0xe59d\n"
        ".hword 0x6044, 0xe59d, 0xa040, 0xe59d\n"
        ".hword 0x0c05, 0xe350, 0xe000, 0x03a0\n"
        ".hword 0x0001, 0x03a0, 0x0018, 0x0a00\n"
        ".hword 0x0c05, 0xe240, 0x0001, 0xe250\n"
        ".hword 0xe001, 0x03a0, 0x0002, 0x03a0\n"
        ".hword 0x0013, 0x0a00, 0x0001, 0xe350\n"
        ".hword 0x000f, 0x1a00, 0xe002, 0xe3a0\n"
        ".hword 0x000e, 0xe1a0, 0x700e, 0xe1a0\n"
        ".hword 0xc240, 0xe59f, 0x000c, 0xe151\n"
        ".hword 0x800c, 0xe041, 0x1003, 0x03a0\n"
        ".hword 0x0012, 0x0a00, 0x000a, 0xaa00\n"
        ".hword 0x1902, 0xe241, 0x1051, 0xe251\n"
        ".hword 0x1001, 0x03a0, 0x000d, 0x0a00\n"
        ".hword 0x0005, 0xe351, 0x1004, 0x03a0\n"
        ".hword 0x000a, 0x0a00, 0xd010, 0xe28d\n"
        ".hword 0x9ff0, 0xe8bd, 0x7001, 0xe3a0\n"
        ".hword 0xffee, 0xeaff, 0x0001, 0xe358\n"
        ".hword 0x1000, 0x03a0, 0x0003, 0x0a00\n"
        ".hword 0x1c0d, 0xe248, 0x100b, 0xe251\n"
        ".hword 0x1002, 0x03a0, 0xfff4, 0x1aff\n"
        ".hword 0x000c, 0xe155, 0x8902, 0xe245\n"
        ".hword 0x8057, 0xe248, 0xc002, 0x03a0\n"
        ".hword 0x8003, 0x03a0, 0x0014, 0x0a00\n"
        ".hword 0x000a, 0xaa00, 0xc902, 0xe245\n"
        ".hword 0xc051, 0xe25c, 0xc003, 0x03a0\n"
        ".hword 0x8001, 0x03a0, 0x000e, 0x0a00\n"
        ".hword 0x0005, 0xe35c, 0xc002, 0x03a0\n"
        ".hword 0x8004, 0x03a0, 0x000a, 0x0a00\n"
        ".hword 0xd010, 0xe28d, 0x9ff0, 0xe8bd\n"
        ".hword 0x0001, 0xe358, 0xc004, 0x03a0\n"
        ".hword 0x8000, 0x03a0, 0x0004, 0x0a00\n"
        ".hword 0xcc0d, 0xe248, 0xc00b, 0xe25c\n"
        ".hword 0xc002, 0x03a0, 0x800c, 0x01a0\n"
        ".hword 0xffd9, 0x1aff, 0x0000, 0xe352\n"
        ".hword 0x0000, 0x1353, 0xffd6, 0x0aff\n"
        ".hword 0x0000, 0xe35a, 0x0000, 0x1356\n"
        ".hword 0xffd3, 0x0aff, 0x9038, 0xe3a0\n"
        ".hword 0x9188, 0xe009, 0x8007, 0xe201\n"
        ".hword 0x1020, 0xe594, 0x0000, 0xe35b\n"
        ".hword 0xb018, 0xe594, 0x5003, 0xe3a0\n"
        ".hword 0x1181, 0xe061, 0x009a, 0xe00a\n"
        ".hword 0x1101, 0xe08b, 0x0796, 0xe00b\n"
        ".hword 0x5000, 0xe5c1, 0x5004, 0xe59d\n"
        ".hword 0x5004, 0xe581, 0x503c, 0xe59d\n"
        ".hword 0x5008, 0xe581, 0x7014, 0xe591\n"
        ".hword 0x7007, 0xe3c7, 0x7008, 0xe187\n"
        ".hword 0x7038, 0xe3c7, 0x7009, 0xe187\n"
        ".hword 0x7014, 0xe581, 0x20bc, 0xe1c1\n"
        ".hword 0x30be, 0xe1c1, 0xa1b0, 0xe1c1\n"
        ".hword 0x0040, 0x03c7, 0xb1b2, 0xe1c1\n"
        ".hword 0x001d, 0x0a00, 0x8010, 0xe591\n"
        ".hword 0x900c, 0xe591, 0x2078, 0xe6ff\n"
        ".hword 0x3079, 0xe6ff, 0x0003, 0xe152\n"
        ".hword 0xa828, 0x21a0, 0x0829, 0x215a\n"
        ".hword 0x0014, 0x2a00, 0x0002, 0xe350\n"
        ".hword 0x0006, 0x0a00, 0x0000, 0xe3e0\n"
        ".hword 0x2002, 0xe043, 0x0828, 0xe080\n"
        ".hword 0x0092, 0xe000, 0x0c90, 0xe000\n"
        ".hword 0x0000, 0xe045, 0x000a, 0xea00\n"
        ".hword 0x0003, 0xe35c, 0x0002, 0xe043\n"
        ".hword 0x8010, 0x03a0, 0x8008, 0x13a0\n"
        ".hword 0x0008, 0xe110, 0x0008, 0x1040\n"
        ".hword 0x2001, 0xe246, 0x0290, 0xe000\n"
        ".hword 0x0c90, 0xe000, 0x0fa0, 0xe080\n"
        ".hword 0x00c0, 0xe045, 0x0008, 0xe581\n"
        ".hword 0x0040, 0xe387, 0x2d06, 0xe3a0\n"
        ".hword 0x0d06, 0xe3c0, 0x238e, 0xe002\n"
        ".hword 0x0002, 0xe180, 0x2054, 0xe59d\n"
        ".hword 0x0014, 0xe581, 0x0020, 0xe352\n"
        ".hword 0x0c02, 0x0380, 0x0c02, 0x13c0\n"
        ".hword 0x0b03, 0xe3c0, 0x0014, 0xe581\n"
        ".hword 0x0d7c, 0xeb00, 0x1020, 0xe594\n"
        ".hword 0x0044, 0xe59f, 0x1001, 0xe281\n"
        ".hword 0x1020, 0xe584, 0x10a0, 0xe590\n"
        ".hword 0x0004, 0xe151, 0x0008, 0x1a00\n"
        ".hword 0x1012, 0xe5d0, 0x0000, 0xe351\n"
        ".hword 0x0005, 0x0a00, 0x1011, 0xe5d0\n"
        ".hword 0x0000, 0xe351, 0x0002, 0x1a00\n"
        ".hword 0x1001, 0xe3a0, 0x1011, 0xe5c0\n"
        ".hword 0x0b0c, 0xeb06, 0xd010, 0xe28d\n"
        ".hword 0x5ff0, 0xe8bd, 0x0d6d, 0xea00\n"
        ".hword 0x8057, 0x0000, 0x6290, 0x004c\n"
    );
};

// DECOMP_FUNC(0x0021e3c0, 680)
extern "C" __attribute__((naked)) void engine_func_0021e3c0() {
    asm volatile(
        ".arm\n"
        ".hword 0x4070, 0xe92d, 0x6280, 0xe59f\n"
        ".hword 0xd080, 0xe24d, 0x0000, 0xe596\n"
        ".hword 0x10f8, 0xe1d0, 0x000a, 0xe351\n"
        ".hword 0x0006, 0x0a00, 0x000b, 0xe351\n"
        ".hword 0x0039, 0x0a00, 0x000c, 0xe351\n"
        ".hword 0x004e, 0x0a00, 0x0063, 0xe351\n"
        ".hword 0x0092, 0x1a00, 0x0029, 0xea00\n"
        ".hword 0x40fa, 0xe1d0, 0xc383, 0xeb00\n"
        ".hword 0x0004, 0xe150, 0x5063, 0xe3a0\n"
        ".hword 0x002c, 0xda00, 0x0004, 0xe1a0\n"
        ".hword 0xf719, 0xeb00, 0x20f0, 0xe1d0\n"
        ".hword 0x0000, 0xe352, 0x0022, 0xba00\n"
        ".hword 0x1000, 0xe596, 0x30f4, 0xe1d1\n"
        ".hword 0x0003, 0xe152, 0x001e, 0x1a00\n"
        ".hword 0x20f2, 0xe1d0, 0x30f6, 0xe1d1\n"
        ".hword 0x0003, 0xe152, 0x001a, 0x1a00\n"
        ".hword 0x00f4, 0xe1d0, 0x0064, 0xe350\n"
        ".hword 0x0017, 0xaa00, 0x0000, 0xe3a0\n"
        ".hword 0x40ba, 0xe1c1, 0x2180, 0xe080\n"
        ".hword 0x2182, 0xe081, 0x2014, 0xe5d2\n"
        ".hword 0x0000, 0xe352, 0x0003, 0x0a00\n"
        ".hword 0x0001, 0xe280, 0x0018, 0xe350\n"
        ".hword 0xfff7, 0xbaff, 0x0000, 0xe3e0\n"
        ".hword 0x0070, 0xe6bf, 0x0001, 0xe370\n"
        ".hword 0x00bc, 0xe1c1, 0x50b8, 0x01c1\n"
        ".hword 0x0004, 0x0a00, 0x000b, 0xe3a0\n"
        ".hword 0x00b8, 0xe1c1, 0xd080, 0xe28d\n"
        ".hword 0x0000, 0xe3a0, 0x8070, 0xe8bd\n"
        ".hword 0xd080, 0xe28d, 0x0001, 0xe3a0\n"
        ".hword 0x8070, 0xe8bd, 0x4001, 0xe284\n"
        ".hword 0xc356, 0xeb00, 0x0000, 0xe154\n"
        ".hword 0xf000, 0xe320, 0xffd2, 0xbaff\n"
        ".hword 0x0000, 0xe596, 0x50b8, 0xe1c0\n"
        ".hword 0xfff4, 0xeaff, 0x00fa, 0xe1d0\n"
        ".hword 0xf6e9, 0xeb00, 0x1000, 0xe596\n"
        ".hword 0x30f4, 0xe1d0, 0x2000, 0xe3a0\n"
        ".hword 0xc0fc, 0xe1d1, 0xc18c, 0xe08c\n"
        ".hword 0x118c, 0xe081, 0x4014, 0xe281\n"
        ".hword 0x3038, 0xe581, 0x2040, 0xe5c1\n"
        ".hword 0x20f4, 0xe1d0, 0x1f53, 0xe28f\n"
        ".hword 0x000d, 0xe1a0, 0x80bc, 0xfa02\n"
        ".hword 0x1007, 0xe3a0, 0x000d, 0xe1a0\n"
        ".hword 0xef6e, 0xeb01, 0x0028, 0xe584\n"
        ".hword 0x1000, 0xe596, 0x000c, 0xe3a0\n"
        ".hword 0x00b8, 0xe1c1, 0x0045, 0xea00\n"
        ".hword 0x00fa, 0xe1d0, 0xf6d2, 0xeb00\n"
        ".hword 0x5000, 0xe1a0, 0x0000, 0xe596\n"
        ".hword 0x10fc, 0xe1d0, 0x1181, 0xe081\n"
        ".hword 0x0181, 0xe080, 0x4014, 0xe280\n"
        ".hword 0x003c, 0xe590, 0x3f06, 0xeb02\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0038, 0x0a00, 0x0028, 0xe594\n"
        ".hword 0x1001, 0xe3a0, 0x0857, 0xeb02\n"
        ".hword 0x00f6, 0xe1d5, 0x0a10, 0xee00\n"
        ".hword 0x0ac0, 0xeeb8, 0x0a01, 0xed84\n"
        ".hword 0x00f8, 0xe1d5, 0x0a10, 0xee00\n"
        ".hword 0x0ac0, 0xeeb8, 0x0a02, 0xed84\n"
        ".hword 0x00fa, 0xe1d5, 0x0a10, 0xee00\n"
        ".hword 0x0ac0, 0xeeb8, 0x0a03, 0xed84\n"
        ".hword 0x00fc, 0xe1d5, 0x0a10, 0xee00\n"
        ".hword 0x0ac0, 0xeeb8, 0x0a07, 0xed84\n"
        ".hword 0x00f6, 0xe1d5, 0x0a10, 0xee00\n"
        ".hword 0x0ac0, 0xeeb8, 0x0a04, 0xed84\n"
        ".hword 0x0024, 0xe594, 0x0006, 0xe350\n"
        ".hword 0x00fe, 0x01d5, 0x00f8, 0x11d5\n"
        ".hword 0x0a10, 0xee00, 0x0ac0, 0xeeb8\n"
        ".hword 0x0a05, 0xed84, 0x00fa, 0xe1d5\n"
        ".hword 0x0a10, 0xee00, 0x0001, 0xe3a0\n"
        ".hword 0x0ac0, 0xeeb8, 0x0a06, 0xed84\n"
        ".hword 0x1000, 0xe596, 0x2010, 0xe591\n"
        ".hword 0x2001, 0xe282, 0x2010, 0xe581\n"
        ".hword 0x0000, 0xe5c4, 0x0001, 0xe5c4\n"
        ".hword 0x0002, 0xe5c4, 0x0000, 0xe596\n"
        ".hword 0x00fa, 0xe1d0, 0x0044, 0xe584\n"
        ".hword 0x0010, 0xe5d5, 0x0000, 0xe350\n"
        ".hword 0x0002, 0x0a00, 0x1010, 0xe285\n"
        ".hword 0x002c, 0xe284, 0x8490, 0xeb02\n"
        ".hword 0x0000, 0xe596, 0x200a, 0xe3a0\n"
        ".hword 0x10ba, 0xe1d0, 0x1001, 0xe281\n"
        ".hword 0x10ba, 0xe1c0, 0x20b8, 0xe1c0\n"
        ".hword 0xd080, 0xe28d, 0x0000, 0xe3a0\n"
        ".hword 0x8070, 0xe8bd, 0x7e70, 0x0044\n"
        ".hword 0x616d, 0x2f70, 0x626f, 0x2f6a\n"
        ".hword 0x626f, 0x5f6a, 0x3025, 0x6432\n"
        ".hword 0x622e, 0x6d61, 0x0000, 0x0000\n"
    );
};

// DECOMP_FUNC(0x002fe358, 680)
extern "C" __attribute__((naked)) void ui_func_002fe358() {
    asm volatile(
        ".arm\n"
        ".hword 0x4ff0, 0xe92d, 0x4003, 0xe1a0\n"
        ".hword 0x7000, 0xe1a0, 0x9001, 0xe1a0\n"
        ".hword 0x0ffa, 0xe3a0, 0x1f4b, 0xe280\n"
        ".hword 0x8b02, 0xed2d, 0xd0fc, 0xe24d\n"
        ".hword 0x30d4, 0xe1d2, 0x80d5, 0xe1d2\n"
        ".hword 0x60d6, 0xe1d2, 0xa030, 0xe243\n"
        ".hword 0xc0d7, 0xe1d2, 0x008a, 0xe160\n"
        ".hword 0xa188, 0xe088, 0x8208, 0xe08a\n"
        ".hword 0x6106, 0xe086, 0x0108, 0xe080\n"
        ".hword 0x300a, 0xe5d2, 0x0d4b, 0xe240\n"
        ".hword 0x5128, 0xe59d, 0x0086, 0xe080\n"
        ".hword 0x8a8d, 0xed9f, 0x0e21, 0xe240\n"
        ".hword 0x0000, 0xe353, 0xb000, 0xe3a0\n"
        ".hword 0x8000, 0xe08c, 0x001c, 0x0a00\n"
        ".hword 0x0001, 0xe353, 0x0000, 0x13a0\n"
        ".hword 0x0022, 0x1a00, 0x00b8, 0xe1d2\n"
        ".hword 0x0001, 0xe158, 0x0002, 0xe080\n"
        ".hword 0x200c, 0xe592, 0xa020, 0xa590\n"
        ".hword 0xa008, 0xb590, 0x10f0, 0xa280\n"
        ".hword 0x10d8, 0xb280, 0x01f4, 0xe59f\n"
        ".hword 0x20f0, 0xa242, 0x20d8, 0xb242\n"
        ".hword 0x0000, 0xe158, 0x0002, 0xba00\n"
        ".hword 0x0e4b, 0xe358, 0x1004, 0xe281\n"
        ".hword 0x2004, 0xa242, 0x0007, 0xe1a0\n"
        ".hword 0x62a2, 0xe1a0, 0x0009, 0xe156\n"
        ".hword 0x6009, 0xc1a0, 0x2286, 0xe1a0\n"
        ".hword 0xfaca, 0xebfe, 0x0e4b, 0xe358\n"
        ".hword 0xf000, 0xe320, 0x0041, 0x1a00\n"
        ".hword 0x0033, 0xea00, 0x00b8, 0xe1d2\n"
        ".hword 0x0001, 0xe158, 0x0008, 0xba00\n"
        ".hword 0x2000, 0xe082, 0x3004, 0xe1a0\n"
        ".hword 0x1009, 0xe1a0, 0x0007, 0xe1a0\n"
        ".hword 0x5000, 0xe58d, 0x0067, 0xeb00\n"
        ".hword 0xd0fc, 0xe28d, 0x8b02, 0xecbd\n"
        ".hword 0x8ff0, 0xe8bd, 0x6002, 0xe080\n"
        ".hword 0x0001, 0xe3a0, 0x0024, 0xe58d\n"
        ".hword 0x0028, 0xe58d, 0x002c, 0xe58d\n"
        ".hword 0x116c, 0xe59f, 0x300a, 0xe3a0\n"
        ".hword 0x2014, 0xe3a0, 0x0030, 0xe28d\n"
        ".hword 0xb020, 0xe58d, 0x1eaf, 0xfaff\n"
        ".hword 0x1000, 0xe596, 0x20c8, 0xe3a0\n"
        ".hword 0x0030, 0xe28d, 0x1020, 0xe58d\n"
        ".hword 0x1004, 0xe596, 0x1024, 0xe58d\n"
        ".hword 0x1008, 0xe596, 0x1028, 0xe58d\n"
        ".hword 0x100c, 0xe596, 0x102c, 0xe58d\n"
        ".hword 0x1010, 0xe286, 0xfaa3, 0xebfe\n"
        ".hword 0x8a02, 0xed8d, 0x8a05, 0xed8d\n"
        ".hword 0x0a48, 0xeddf, 0x0a48, 0xed9f\n"
        ".hword 0x8a06, 0xed8d, 0x000c, 0xe28d\n"
        ".hword 0x3004, 0xe1a0, 0x0a02, 0xec80\n"
        ".hword 0x2008, 0xe28d, 0x0a07, 0xedcd\n"
        ".hword 0x1009, 0xe1a0, 0x0007, 0xe1a0\n"
        ".hword 0x5000, 0xe58d, 0x003f, 0xeb00\n"
        ".hword 0xd0fc, 0xe28d, 0x8b02, 0xecbd\n"
        ".hword 0x8ff0, 0xe8bd, 0x0000, 0xe356\n"
        ".hword 0x000a, 0xda00, 0x0001, 0xe316\n"
        ".hword 0x000c, 0xe247, 0x0020, 0x1280\n"
        ".hword 0x8a00, 0x1d80, 0x10c6, 0xe1b0\n"
        ".hword 0x0004, 0x0a00, 0x8a08, 0xed80\n"
        ".hword 0x0040, 0xe280, 0x1001, 0xe251\n"
        ".hword 0x8a00, 0xed80, 0xfffa, 0x1aff\n"
        ".hword 0x1006, 0xe049, 0x0000, 0xe351\n"
        ".hword 0x0008, 0xda00, 0x0286, 0xe087\n"
        ".hword 0x3006, 0xe280, 0x2004, 0xe280\n"
        ".hword 0xc000, 0xe3e0, 0xc020, 0xe480\n"
        ".hword 0xc020, 0xe4c3, 0x1001, 0xe251\n"
        ".hword 0xb2b0, 0xe0c2, 0xfffa, 0x1aff\n"
        ".hword 0x0000, 0xe356, 0x3000, 0xe3a0\n"
        ".hword 0x0011, 0xda00, 0x0000, 0xe355\n"
        ".hword 0xc283, 0xc087, 0x0000, 0xe3a0\n"
        ".hword 0x1000, 0xc59c, 0x0009, 0xda00\n"
        ".hword 0x2180, 0xe080, 0x2182, 0xe084\n"
        ".hword 0x2004, 0xe592, 0x0001, 0xe152\n"
        ".hword 0x0001, 0x1a00, 0x0006, 0xe5cc\n"
        ".hword 0x0002, 0xea00, 0x0001, 0xe280\n"
        ".hword 0x0000, 0xe155, 0xfff5, 0xcaff\n"
        ".hword 0x3001, 0xe283, 0x0003, 0xe156\n"
        ".hword 0xffed, 0xcaff, 0x3004, 0xe1a0\n"
        ".hword 0x200a, 0xe1a0, 0x1006, 0xe1a0\n"
        ".hword 0x0007, 0xe1a0, 0x5000, 0xe58d\n"
        ".hword 0x905c, 0xebff, 0xd0fc, 0xe28d\n"
        ".hword 0x0006, 0xe1a0, 0x8b02, 0xecbd\n"
        ".hword 0x8ff0, 0xe8bd, 0x0000, 0x0000\n"
        ".hword 0x044c, 0x0000, 0x3fec, 0x0033\n"
        ".hword 0x0000, 0x4040, 0x0000, 0x40a0\n"
    );
};

// DECOMP_FUNC(0x003ac688, 680)
extern "C" __attribute__((naked)) void ui_func_003ac688() {
    asm volatile(
        ".arm\n"
        ".hword 0x000c, 0xe59f, 0x1005, 0xe3a0\n"
        ".hword 0x0004, 0xe590, 0x101d, 0xe5c0\n"
        ".hword 0xff1e, 0xe12f, 0xd9e0, 0x0043\n"
        ".hword 0x025c, 0xe59f, 0x47f0, 0xe92d\n"
        ".hword 0x6003, 0xe3a0, 0x8002, 0xe3a0\n"
        ".hword 0x7000, 0xe3a0, 0x4004, 0xe590\n"
        ".hword 0x9001, 0xe3a0, 0xa004, 0xe3a0\n"
        ".hword 0x0470, 0xe5d4, 0x0006, 0xe350\n"
        ".hword 0x001c, 0xe5c4, 0xf100, 0x379f\n"
        ".hword 0x003b, 0xea00, 0xc6ec, 0x003a\n"
        ".hword 0xc73c, 0x003a, 0xc6f4, 0x003a\n"
        ".hword 0xc79c, 0x003a, 0xc74c, 0x003a\n"
        ".hword 0xc7ac, 0x003a, 0x8470, 0xe5c4\n"
        ".hword 0x0033, 0xea00, 0x5000, 0xe3a0\n"
        ".hword 0x1005, 0xe1a0, 0x0022, 0xe3a0\n"
        ".hword 0xe73c, 0xebfb, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x002c, 0x0a00\n"
        ".hword 0x5001, 0xe285, 0x0002, 0xe355\n"
        ".hword 0xfff6, 0xbaff, 0x00f8, 0xe1d4\n"
        ".hword 0x0000, 0xe350, 0x0026, 0xba00\n"
        ".hword 0x1001, 0xe3a0, 0x9ea0, 0xebfb\n"
        ".hword 0x0000, 0xe350, 0x9470, 0x15c4\n"
        ".hword 0x0021, 0xea00, 0x001d, 0xe5d4\n"
        ".hword 0x0004, 0xe350, 0xa470, 0x05c4\n"
        ".hword 0x001d, 0xea00, 0x5c02, 0xe284\n"
        ".hword 0x07f0, 0xe1d5, 0x0008, 0xe350\n"
        ".hword 0x0001, 0xb280, 0x07b0, 0xb1c5\n"
        ".hword 0x07f2, 0xe1d5, 0x0008, 0xe350\n"
        ".hword 0x0001, 0xb280, 0x07b2, 0xb1c5\n"
        ".hword 0x0040, 0xe284, 0x4c9d, 0xebfc\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x000f, 0x0a00, 0x6470, 0xe5c4\n"
        ".hword 0x0008, 0xe3a0, 0x601e, 0xe5c4\n"
        ".hword 0x07b0, 0xe1c5, 0x07b2, 0xe1c5\n"
        ".hword 0x0009, 0xea00, 0x001d, 0xe5d4\n"
        ".hword 0x0005, 0xe350, 0x0006, 0x1a00\n"
        ".hword 0x0004, 0xea00, 0x0f56, 0xe284\n"
        ".hword 0x4c8e, 0xebfc, 0x0000, 0xe350\n"
        ".hword 0x0006, 0x13a0, 0x0000, 0x0a00\n"
        ".hword 0x0470, 0xe5c4, 0x001e, 0xe5d4\n"
        ".hword 0x0005, 0xe350, 0xf100, 0x379f\n"
        ".hword 0x0049, 0xea00, 0xc8fc, 0x003a\n"
        ".hword 0xc880, 0x003a, 0xc8ec, 0x003a\n"
        ".hword 0xc7e8, 0x003a, 0xc840, 0x003a\n"
        ".hword 0x001f, 0xe5d4, 0x0004, 0xe350\n"
        ".hword 0x0041, 0x1a00, 0x2000, 0xe3a0\n"
        ".hword 0x1002, 0xe1a0, 0x00cc, 0xe284\n"
        ".hword 0xa01e, 0xe5c4, 0x0c12, 0xebfc\n"
        ".hword 0x2000, 0xe3a0, 0x1001, 0xe3a0\n"
        ".hword 0x0f79, 0xe284, 0x0c0e, 0xebfc\n"
        ".hword 0x00dc, 0xe1c4, 0x01f4, 0xe1c4\n"
        ".hword 0x01f8, 0xe1d4, 0x0000, 0xe350\n"
        ".hword 0x002d, 0xba00, 0x1001, 0xe3a0\n"
        ".hword 0x9f4c, 0xebfb, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0x0028, 0xea00\n"
        ".hword 0x0f79, 0xe284, 0x4c69, 0xebfc\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0029, 0x0a00, 0x0004, 0xe594\n"
        ".hword 0x1014, 0xe594, 0x0001, 0xe150\n"
        ".hword 0x0003, 0x0a00, 0x00f8, 0xe1d4\n"
        ".hword 0x0000, 0xe350, 0x1001, 0xa3a0\n"
        ".hword 0xa4c9, 0xabfb, 0x7004, 0xe584\n"
        ".hword 0x901e, 0xe5c4, 0x001e, 0xea00\n"
        ".hword 0x01f8, 0xe1d4, 0x0000, 0xe350\n"
        ".hword 0x001b, 0xba00, 0x1001, 0xe3a0\n"
        ".hword 0x9e47, 0xebfb, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x0016, 0x0a00\n"
        ".hword 0x0014, 0xe594, 0x100c, 0xe594\n"
        ".hword 0x0001, 0xe150, 0x0003, 0x1a00\n"
        ".hword 0x1018, 0xe594, 0x00f4, 0xe1c4\n"
        ".hword 0x801e, 0xe5c4, 0x000e, 0xea00\n"
        ".hword 0x01f8, 0xe1d4, 0x0000, 0xe350\n"
        ".hword 0x1001, 0xa3a0, 0xa4b2, 0xabfb\n"
        ".hword 0x00dc, 0xe1c4, 0x01f4, 0xe1c4\n"
        ".hword 0x01f8, 0xe1d4, 0x0000, 0xe350\n"
        ".hword 0xffd1, 0xaaff, 0x701f, 0xe5c4\n"
        ".hword 0x0003, 0xea00, 0x00cc, 0xe284\n"
        ".hword 0x4c3e, 0xebfc, 0x0000, 0xe350\n"
        ".hword 0x601e, 0x15c4, 0x0000, 0xe3a0\n"
        ".hword 0x87f0, 0xe8bd, 0xd9e0, 0x0043\n"
        ".hword 0x001c, 0xe59f, 0x4010, 0xe92d\n"
        ".hword 0x0000, 0xe590, 0x0000, 0xe590\n"
        ".hword 0x1000, 0xe590, 0x100c, 0xe591\n"
        ".hword 0xff31, 0xe12f, 0x0000, 0xe3a0\n"
        ".hword 0x8010, 0xe8bd, 0xd990, 0x0043\n"
    );
};

// DECOMP_FUNC(0x001d00f8, 684)
extern "C" __attribute__((naked)) void camp_func_001d00f8() {
    asm volatile(
        ".arm\n"
        ".hword 0x47f0, 0xe92d, 0x4000, 0xe1a0\n"
        ".hword 0x8000, 0xe3a0, 0x9000, 0xe3e0\n"
        ".hword 0x8b04, 0xed2d, 0x0008, 0xe590\n"
        ".hword 0x8aa0, 0xeddf, 0x0000, 0xe350\n"
        ".hword 0x9a9f, 0xcddf, 0x9a9f, 0xcd9f\n"
        ".hword 0x0099, 0xda00, 0x0004, 0xe594\n"
        ".hword 0x0088, 0xe080, 0x00b0, 0xe1d0\n"
        ".hword 0x0000, 0xe350, 0x0055, 0x0a00\n"
        ".hword 0x3ab5, 0xeb03, 0x0004, 0xe594\n"
        ".hword 0x0088, 0xe080, 0x50b0, 0xe1d0\n"
        ".hword 0x0005, 0xe1a0, 0x3ab0, 0xeb03\n"
        ".hword 0x6000, 0xe1a0, 0x0003, 0xe5d0\n"
        ".hword 0x001f, 0xe200, 0x0a10, 0xee00\n"
        ".hword 0x0005, 0xe1a0, 0x0a40, 0xeeb8\n"
        ".hword 0x8a40, 0xeeb0, 0x8a29, 0xee00\n"
        ".hword 0x69e3, 0xeb02, 0x102c, 0xe5d4\n"
        ".hword 0x7000, 0xe1a0, 0x0005, 0xe1a0\n"
        ".hword 0x0007, 0xe151, 0x8a09, 0x0e38\n"
        ".hword 0x7898, 0xeb03, 0xa000, 0xe1b0\n"
        ".hword 0xf000, 0xe320, 0x0015, 0x0a00\n"
        ".hword 0x0010, 0xe594, 0x5000, 0xe3a0\n"
        ".hword 0x0000, 0xe350, 0x0011, 0xda00\n"
        ".hword 0x000c, 0xe594, 0x0085, 0xe080\n"
        ".hword 0x00b0, 0xe1d0, 0x0000, 0xe350\n"
        ".hword 0x0008, 0x0a00, 0xcfbd, 0xeb02\n"
        ".hword 0x100a, 0xe1a0, 0xf000, 0xe320\n"
        ".hword 0x69a7, 0xeb02, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x0001, 0x0a00\n"
        ".hword 0x8a09, 0xee38, 0x0003, 0xea00\n"
        ".hword 0x0010, 0xe594, 0x5001, 0xe285\n"
        ".hword 0x0005, 0xe150, 0xffed, 0xcaff\n"
        ".hword 0x0020, 0xe594, 0x5000, 0xe3a0\n"
        ".hword 0x0000, 0xe350, 0x0011, 0xda00\n"
        ".hword 0x001c, 0xe594, 0x0085, 0xe080\n"
        ".hword 0x00b0, 0xe1d0, 0x69bc, 0xeb02\n"
        ".hword 0x0007, 0xe150, 0x8a49, 0x0e38\n"
        ".hword 0x001c, 0xe594, 0x0085, 0xe080\n"
        ".hword 0x00b0, 0xe1d0, 0x3a7a, 0xeb03\n"
        ".hword 0x0002, 0xe5d0, 0x1002, 0xe5d6\n"
        ".hword 0x5001, 0xe285, 0x0000, 0xe151\n"
        ".hword 0x8a49, 0x0e38, 0x0020, 0xe594\n"
        ".hword 0x0005, 0xe150, 0xffed, 0xcaff\n"
        ".hword 0x0000, 0xe359, 0x0002, 0xaa00\n"
        ".hword 0x8a48, 0xeef0, 0x9008, 0xe1a0\n"
        ".hword 0x000c, 0xea00, 0x8ac8, 0xeef4\n"
        ".hword 0xfa10, 0xeef1, 0x0009, 0xca00\n"
        ".hword 0x8a48, 0xeef4, 0xfa10, 0xeef1\n"
        ".hword 0xfff6, 0x1aff, 0x0004, 0xe594\n"
        ".hword 0x1088, 0xe080, 0x2089, 0xe080\n"
        ".hword 0x00b0, 0xe1d1, 0x10b0, 0xe1d2\n"
        ".hword 0x0001, 0xe150, 0xffef, 0x9aff\n"
        ".hword 0x0008, 0xe594, 0x8001, 0xe288\n"
        ".hword 0x0008, 0xe150, 0xffa0, 0xcaff\n"
        ".hword 0x0000, 0xe359, 0x0038, 0xba00\n"
        ".hword 0x001c, 0xe284, 0x1004, 0xe594\n"
        ".hword 0x0005, 0xe890, 0x1089, 0xe081\n"
        ".hword 0x10b0, 0xe1d1, 0x0082, 0xe080\n"
        ".hword 0x10b0, 0xe1c0, 0x0020, 0xe594\n"
        ".hword 0x0001, 0xe280, 0x0020, 0xe584\n"
        ".hword 0x0004, 0xe594, 0x0089, 0xe080\n"
        ".hword 0x00b0, 0xe1d0, 0x7843, 0xeb03\n"
        ".hword 0x6000, 0xe1b0, 0x7000, 0xe3a0\n"
        ".hword 0x0021, 0x0a00, 0x0010, 0xe594\n"
        ".hword 0x5000, 0xe3a0, 0x0000, 0xe350\n"
        ".hword 0x001d, 0xda00, 0x000c, 0xe594\n"
        ".hword 0x0085, 0xe080, 0x00b0, 0xe1d0\n"
        ".hword 0x0000, 0xe350, 0x0014, 0x0a00\n"
        ".hword 0xcf68, 0xeb02, 0x1006, 0xe1a0\n"
        ".hword 0xf000, 0xe320, 0x6952, 0xeb02\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x000d, 0x0a00, 0x001c, 0xe284\n"
        ".hword 0x100c, 0xe594, 0x0005, 0xe890\n"
        ".hword 0x1085, 0xe081, 0x10b0, 0xe1d1\n"
        ".hword 0x0082, 0xe080, 0x10b0, 0xe1c0\n"
        ".hword 0x0020, 0xe594, 0x0001, 0xe280\n"
        ".hword 0x0020, 0xe584, 0x000c, 0xe594\n"
        ".hword 0x0085, 0xe080, 0x70b0, 0xe1c0\n"
        ".hword 0x0003, 0xea00, 0x0010, 0xe594\n"
        ".hword 0x5001, 0xe285, 0x0005, 0xe150\n"
        ".hword 0xffe1, 0xcaff, 0x0004, 0xe594\n"
        ".hword 0x0089, 0xe080, 0x70b0, 0xe1c0\n"
        ".hword 0x0001, 0xe3a0, 0x8b04, 0xecbd\n"
        ".hword 0x87f0, 0xe8bd, 0x8b04, 0xecbd\n"
        ".hword 0x0000, 0xe3a0, 0x87f0, 0xe8bd\n"
        ".hword 0x0000, 0x0000, 0xd70a, 0x3c23\n"
        ".hword 0x0000, 0x3f80\n"
    );
};

// DECOMP_FUNC(0x0033bdc8, 684)
extern "C" __attribute__((naked)) void script_vm_func_0033bdc8() {
    asm volatile(
        ".arm\n"
        ".hword 0x47f0, 0xe92d, 0xde61, 0xe24d\n"
        ".hword 0x8002, 0xe1a0, 0xa001, 0xe1a0\n"
        ".hword 0x7000, 0xe1a0, 0x1000, 0xe1a0\n"
        ".hword 0x900d, 0xe1a0, 0x2280, 0xe59f\n"
        ".hword 0x0009, 0xe1a0, 0x0459, 0xebfe\n"
        ".hword 0xb304, 0xebfd, 0x6000, 0xe1a0\n"
        ".hword 0x0c91, 0xe280, 0x404a, 0xe5dd\n"
        ".hword 0x10d8, 0xe1d0, 0x5000, 0xe3e0\n"
        ".hword 0x0004, 0xe151, 0x5000, 0x03a0\n"
        ".hword 0x0006, 0x0a00, 0x10d9, 0xe1d0\n"
        ".hword 0x0004, 0xe151, 0x5001, 0x03a0\n"
        ".hword 0x0002, 0x0a00, 0x00da, 0xe1d0\n"
        ".hword 0x0004, 0xe150, 0x5002, 0x03a0\n"
        ".hword 0x004a, 0xe5d7, 0x800b, 0xebfd\n"
        ".hword 0x2000, 0xe3a0, 0x100a, 0xe1a0\n"
        ".hword 0x0004, 0xe1a0, 0x8187, 0xebfd\n"
        ".hword 0x0004, 0xe1a0, 0xf000, 0xe320\n"
        ".hword 0xb2e3, 0xebfd, 0x0000, 0xe355\n"
        ".hword 0x4000, 0xe1a0, 0x0003, 0xba00\n"
        ".hword 0x004a, 0xe5d4, 0x1005, 0xe086\n"
        ".hword 0x1a09, 0xe281, 0x0108, 0xe5c1\n"
        ".hword 0x1000, 0xe3a0, 0x0001, 0xe084\n"
        ".hword 0x2001, 0xe089, 0x304c, 0xe5d0\n"
        ".hword 0xc04c, 0xe5d2, 0x1002, 0xe281\n"
        ".hword 0x0040, 0xe351, 0x300c, 0xe183\n"
        ".hword 0x304c, 0xe5c0, 0x304d, 0xe5d0\n"
        ".hword 0x204d, 0xe5d2, 0xa009, 0xe1a0\n"
        ".hword 0x2003, 0xe182, 0x204d, 0xe5c0\n"
        ".hword 0xfff1, 0xbaff, 0x0000, 0xe3a0\n"
        ".hword 0x2000, 0xe084, 0x1000, 0xe08a\n"
        ".hword 0x308c, 0xe5d2, 0x108c, 0xe5d1\n"
        ".hword 0x0001, 0xe280, 0x1003, 0xe081\n"
        ".hword 0x00ff, 0xe351, 0x10ff, 0xc3a0\n"
        ".hword 0x0c05, 0xe350, 0x108c, 0xe5c2\n"
        ".hword 0xfff4, 0xbaff, 0x0004, 0xe1a0\n"
        ".hword 0x8067, 0xebfd, 0x9000, 0xe3a0\n"
        ".hword 0x6009, 0xe1a0, 0x5009, 0xe1a0\n"
        ".hword 0x7085, 0xe08a, 0x13b4, 0xe1d7\n"
        ".hword 0x0000, 0xe351, 0x0006, 0x0a00\n"
        ".hword 0x0004, 0xe1a0, 0xbeb8, 0xebfc\n"
        ".hword 0x0000, 0xe350, 0x03b4, 0xe1d7\n"
        ".hword 0x001a, 0x0a00, 0x0000, 0xe350\n"
        ".hword 0x9001, 0x1289, 0x5001, 0xe285\n"
        ".hword 0x0008, 0xe355, 0xfff1, 0xbaff\n"
        ".hword 0x3140, 0xe59f, 0x2002, 0xe3a0\n"
        ".hword 0x1008, 0xe3a0, 0x0008, 0xe1a0\n"
        ".hword 0xeff2, 0xfbfd, 0x0004, 0xe1a0\n"
        ".hword 0xf000, 0xe320, 0x8312, 0xebfd\n"
        ".hword 0x2000, 0xe1a0, 0x0008, 0xe266\n"
        ".hword 0x0000, 0xe350, 0x0002, 0xda00\n"
        ".hword 0x1086, 0xe088, 0x0000, 0xe3a0\n"
        ".hword 0x00b0, 0xe1c1, 0x1001, 0xe242\n"
        ".hword 0x0000, 0xe351, 0x0017, 0xda00\n"
        ".hword 0x0001, 0xe312, 0x0032, 0xe284\n"
        ".hword 0x0007, 0x1a00, 0x0003, 0xea00\n"
        ".hword 0x1086, 0xe088, 0x6001, 0xe286\n"
        ".hword 0x00b0, 0xe1c1, 0xffe2, 0xeaff\n"
        ".hword 0x30b2, 0xe1f0, 0x0000, 0xe353\n"
        ".hword 0x6001, 0x0246, 0xc0b2, 0xe1d0\n"
        ".hword 0x10c1, 0xe1b0, 0x3000, 0xe3a0\n"
        ".hword 0x0007, 0x0a00, 0x0000, 0xe35c\n"
        ".hword 0xc0b4, 0xe1f0, 0x6001, 0x0246\n"
        ".hword 0x0000, 0xe35c, 0xc0b2, 0xe1d0\n"
        ".hword 0x3001, 0x0243, 0x1001, 0xe251\n"
        ".hword 0xfff7, 0x1aff, 0x6003, 0xe086\n"
        ".hword 0x0001, 0xe252, 0x0003, 0x4a00\n"
        ".hword 0x0080, 0xe084, 0x03b4, 0xe1d0\n"
        ".hword 0x0000, 0xe350, 0x6001, 0x0246\n"
        ".hword 0x0000, 0xe356, 0x2000, 0xd3a0\n"
        ".hword 0x0018, 0xca00, 0x0082, 0xe088\n"
        ".hword 0x30b0, 0xe1d0, 0x0000, 0xe353\n"
        ".hword 0x0009, 0x0a00, 0x0008, 0xe359\n"
        ".hword 0x0009, 0xe1a0, 0x0006, 0xaa00\n"
        ".hword 0x1080, 0xe084, 0x13b4, 0xe1d1\n"
        ".hword 0x0000, 0xe351, 0x000a, 0x0a00\n"
        ".hword 0x0001, 0xe280, 0x0008, 0xe350\n"
        ".hword 0xfff8, 0xbaff, 0x2001, 0xe282\n"
        ".hword 0x0008, 0xe352, 0xffee, 0xbaff\n"
        ".hword 0x0004, 0xe1a0, 0x8243, 0xebfd\n"
        ".hword 0xde61, 0xe28d, 0x0000, 0xe3a0\n"
        ".hword 0x87f0, 0xe8bd, 0x0080, 0xe084\n"
        ".hword 0x33b4, 0xe1c0, 0xfff4, 0xeaff\n"
        ".hword 0x0004, 0xe1a0, 0x823b, 0xebfd\n"
        ".hword 0xde61, 0xe28d, 0x0001, 0xe3a0\n"
        ".hword 0x87f0, 0xe8bd, 0x0604, 0x0000\n"
        ".hword 0x13e8, 0x0020\n"
    );
};

// DECOMP_FUNC(0x003a3e98, 684)
extern "C" __attribute__((naked)) void shop_func_003a3e98() {
    asm volatile(
        ".arm\n"
        ".hword 0x41f0, 0xe92d, 0x5000, 0xe1a0\n"
        ".hword 0x0008, 0xe590, 0x0000, 0xe350\n"
        ".hword 0x000e, 0x0a00, 0x0001, 0xe350\n"
        ".hword 0x008d, 0x1a00, 0x0168, 0xe595\n"
        ".hword 0xe83f, 0xebf7, 0x0002, 0xe350\n"
        ".hword 0x0089, 0x1a00, 0x0003, 0xe3a0\n"
        ".hword 0x1000, 0xe3a0, 0x00f4, 0xe1c5\n"
        ".hword 0x1264, 0xe59f, 0x0000, 0xe3a0\n"
        ".hword 0xec8b, 0xebfb, 0x41f0, 0xe8bd\n"
        ".hword 0x0001, 0xe3a0, 0xccff, 0xeafb\n"
        ".hword 0x0000, 0xe3a0, 0xccfd, 0xebfb\n"
        ".hword 0x0168, 0xe595, 0xf000, 0xe320\n"
        ".hword 0xe82f, 0xebf7, 0x1000, 0xe3a0\n"
        ".hword 0x0001, 0xe1a0, 0xea6d, 0xebfb\n"
        ".hword 0x0005, 0xe1a0, 0xf000, 0xe320\n"
        ".hword 0x2f8f, 0xebfa, 0x4000, 0xe1a0\n"
        ".hword 0x0005, 0xe1a0, 0x2f75, 0xebfa\n"
        ".hword 0x0860, 0xe595, 0x1080, 0xe080\n"
        ".hword 0x0280, 0xe061, 0x0100, 0xe085\n"
        ".hword 0x0888, 0xe590, 0x0000, 0xe350\n"
        ".hword 0x0002, 0xda00, 0x6c72, 0xebfb\n"
        ".hword 0x0000, 0xe350, 0x4001, 0x13a0\n"
        ".hword 0x0860, 0xe595, 0x1580, 0xe080\n"
        ".hword 0x2080, 0xe080, 0x0280, 0xe062\n"
        ".hword 0x1081, 0xe085, 0x0100, 0xe085\n"
        ".hword 0x6b03, 0xe281, 0x6094, 0xe286\n"
        ".hword 0x0d22, 0xe280, 0x3e0b, 0xebfa\n"
        ".hword 0x0100, 0xe086, 0x1860, 0xe595\n"
        ".hword 0x60b0, 0xe1d0, 0x0008, 0xe351\n"
        ".hword 0x000a, 0x1a00, 0x1006, 0xe1a0\n"
        ".hword 0x0005, 0xe1a0, 0x3364, 0xebfa\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0004, 0x0a00, 0x0006, 0xe1a0\n"
        ".hword 0xaf8e, 0xebfb, 0x0001, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x0006, 0xda00\n"
        ".hword 0x0000, 0xe354, 0x0004, 0x0a00\n"
        ".hword 0x3aa2, 0xebfa, 0x0005, 0xe1a0\n"
        ".hword 0x41f0, 0xe8bd, 0x100b, 0xe3a0\n"
        ".hword 0x2a03, 0xeafa, 0xf000, 0xe320\n"
        ".hword 0x2f3c, 0xebfa, 0x7164, 0xe59f\n"
        ".hword 0x4b02, 0xe285, 0x0000, 0xe350\n"
        ".hword 0x4064, 0xe284, 0x000b, 0x1a00\n"
        ".hword 0x6801, 0xe285, 0x6c5d, 0xe286\n"
        ".hword 0x04fc, 0xe1d6, 0xe640, 0xebfb\n"
        ".hword 0x0006, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0004, 0x0a00, 0x2f23, 0xebfa\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0036, 0x1a00, 0x0008, 0xea00\n"
        ".hword 0x0864, 0xe595, 0x1001, 0xe3a0\n"
        ".hword 0x0180, 0xe797, 0x0000, 0xe584\n"
        ".hword 0x0005, 0xe1a0, 0x2f86, 0xebfa\n"
        ".hword 0x41f0, 0xe8bd, 0xf000, 0xe320\n"
        ".hword 0x2f13, 0xeafa, 0x04fe, 0xe1d6\n"
        ".hword 0xe62d, 0xebfb, 0x0006, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x0027, 0x0a00\n"
        ".hword 0x493e, 0xebfb, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x002d, 0x0a00\n"
        ".hword 0x0000, 0xe3a0, 0x33c6, 0xebfa\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0x3a59, 0xebfa, 0x1001, 0xe3a0\n"
        ".hword 0x0fea, 0xe285, 0x3cd4, 0xebfa\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0xcc26, 0xebfb, 0x1014, 0xe5d5\n"
        ".hword 0x0a15, 0xe285, 0x0ed6, 0xe280\n"
        ".hword 0x0001, 0xe351, 0x7001, 0xe3a0\n"
        ".hword 0x1002, 0x13a0, 0x7000, 0x0580\n"
        ".hword 0x1000, 0x1580, 0x085c, 0xe595\n"
        ".hword 0x3e4c, 0xebfa, 0x0b02, 0xe285\n"
        ".hword 0x0028, 0xe280, 0x3e3a, 0xebfa\n"
        ".hword 0x05f0, 0xe1d6, 0x4000, 0xe3a0\n"
        ".hword 0x0000, 0xe350, 0x0005, 0xda00\n"
        ".hword 0xf000, 0xe320, 0x53cb, 0xebfc\n"
        ".hword 0x05f0, 0xe1d6, 0x4001, 0xe284\n"
        ".hword 0x0004, 0xe150, 0xfff9, 0xcaff\n"
        ".hword 0x7008, 0xe585, 0x81f0, 0xe8bd\n"
        ".hword 0x0864, 0xe595, 0x1001, 0xe3a0\n"
        ".hword 0x0180, 0xe087, 0x0004, 0xe590\n"
        ".hword 0x0000, 0xe584, 0x0005, 0xe1a0\n"
        ".hword 0x2f4f, 0xebfa, 0x41f0, 0xe8bd\n"
        ".hword 0xf000, 0xe320, 0x2edc, 0xeafa\n"
        ".hword 0xf000, 0xe320, 0xc98b, 0xebfa\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0xffef, 0x0aff, 0x3a45, 0xebfa\n"
        ".hword 0x0005, 0xe1a0, 0x41f0, 0xe8bd\n"
        ".hword 0x2ea0, 0xeafa, 0x32ff, 0x3232\n"
        ".hword 0xe020, 0x0044\n"
    );
};

// DECOMP_FUNC(0x0026bc28, 688)
extern "C" __attribute__((naked)) void camp_func_0026bc28() {
    asm volatile(
        ".arm\n"
        ".hword 0x4ff0, 0xe92d, 0x0000, 0xe3a0\n"
        ".hword 0xd00c, 0xe24d, 0x4000, 0xe1a0\n"
        ".hword 0x1294, 0xe59f, 0x5000, 0xe591\n"
        ".hword 0x0028, 0xe585, 0xf000, 0xe320\n"
        ".hword 0xf36e, 0xeb00, 0x0004, 0xe080\n"
        ".hword 0x0a09, 0xe280, 0x0fd0, 0xe1d0\n"
        ".hword 0x0000, 0xe350, 0x0002, 0xba00\n"
        ".hword 0x0028, 0xe595, 0x0001, 0xe280\n"
        ".hword 0x0028, 0xe585, 0x4001, 0xe284\n"
        ".hword 0x0018, 0xe354, 0xfff2, 0xbaff\n"
        ".hword 0xf362, 0xeb00, 0x0a09, 0xe280\n"
        ".hword 0x010b, 0xe5d0, 0x000c, 0xe350\n"
        ".hword 0x0002, 0x83a0, 0x0001, 0x93a0\n"
        ".hword 0x0030, 0xe585, 0xf35b, 0xeb00\n"
        ".hword 0x4000, 0xe1a0, 0x0a09, 0xe280\n"
        ".hword 0x1000, 0xe3a0, 0x2018, 0xe3a0\n"
        ".hword 0x00f0, 0xe280, 0xc181, 0xe085\n"
        ".hword 0x30d1, 0xe0d0, 0x2001, 0xe252\n"
        ".hword 0x1001, 0xe281, 0x3738, 0xe58c\n"
        ".hword 0xfff9, 0x1aff, 0x0083, 0xeb00\n"
        ".hword 0x4a09, 0xe284, 0x010b, 0xe5d4\n"
        ".hword 0x0003, 0xe310, 0x6120, 0xe1a0\n"
        ".hword 0x6001, 0x1286, 0x0d25, 0xe285\n"
        ".hword 0xcbb0, 0xeb00, 0x7000, 0xe1a0\n"
        ".hword 0x0d25, 0xe285, 0xcd55, 0xeb00\n"
        ".hword 0xb000, 0xe1a0, 0x0b02, 0xe285\n"
        ".hword 0x0f82, 0xe280, 0x8000, 0xe1a0\n"
        ".hword 0x0008, 0xe58d, 0xcba7, 0xeb00\n"
        ".hword 0xa000, 0xe1a0, 0x0008, 0xe1a0\n"
        ".hword 0xcd4c, 0xeb00, 0x110b, 0xe5d4\n"
        ".hword 0x8000, 0xe1a0, 0x9001, 0xe3a0\n"
        ".hword 0x000c, 0xe351, 0x0010, 0x2a00\n"
        ".hword 0x3004, 0xe3a0, 0x2006, 0xe1a0\n"
        ".hword 0x0d25, 0xe285, 0x9000, 0xe58d\n"
        ".hword 0x9004, 0xe58d, 0xcf69, 0xeb00\n"
        ".hword 0x9000, 0xe58d, 0x9004, 0xe58d\n"
        ".hword 0x010b, 0xe5d4, 0x3004, 0xe3a0\n"
        ".hword 0x2001, 0xe286, 0x1004, 0xe280\n"
        ".hword 0x0008, 0xe59d, 0xcf61, 0xeb00\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0x0011, 0xea00, 0x002c, 0xe595\n"
        ".hword 0x9000, 0xe58d, 0x9004, 0xe58d\n"
        ".hword 0x0000, 0xe350, 0x0045, 0x0a00\n"
        ".hword 0x100c, 0xe241, 0x3004, 0xe3a0\n"
        ".hword 0x2003, 0xe3a0, 0x0d25, 0xe285\n"
        ".hword 0xcf54, 0xeb00, 0x9000, 0xe58d\n"
        ".hword 0x9004, 0xe58d, 0x010b, 0xe5d4\n"
        ".hword 0x3004, 0xe3a0, 0x2003, 0xe1a0\n"
        ".hword 0x1008, 0xe240, 0x0008, 0xe59d\n"
        ".hword 0xcf4c, 0xeb00, 0x1007, 0xe1a0\n"
        ".hword 0x0d25, 0xe285, 0xcb65, 0xeb00\n"
        ".hword 0x100b, 0xe1a0, 0x0d25, 0xe285\n"
        ".hword 0xcc0b, 0xeb00, 0x0008, 0xe59d\n"
        ".hword 0x100a, 0xe1a0, 0xcb5f, 0xeb00\n"
        ".hword 0x0008, 0xe59d, 0x1008, 0xe1a0\n"
        ".hword 0xcc05, 0xeb00, 0x0b02, 0xe285\n"
        ".hword 0x0f69, 0xe280, 0x0008, 0xe58d\n"
        ".hword 0xcb6c, 0xeb00, 0x7000, 0xe1a0\n"
        ".hword 0x0008, 0xe59d, 0xcd11, 0xeb00\n"
        ".hword 0xa000, 0xe1a0, 0x0b02, 0xe285\n"
        ".hword 0x0f9b, 0xe280, 0xb000, 0xe1a0\n"
        ".hword 0xcb64, 0xeb00, 0x5000, 0xe1a0\n"
        ".hword 0x000b, 0xe1a0, 0xcd09, 0xeb00\n"
        ".hword 0x8000, 0xe1a0, 0x9000, 0xe58d\n"
        ".hword 0x9004, 0xe58d, 0x110b, 0xe5d4\n"
        ".hword 0x0008, 0xe59d, 0x3004, 0xe3a0\n"
        ".hword 0x2006, 0xe1a0, 0xcf29, 0xeb00\n"
        ".hword 0x9000, 0xe58d, 0x9004, 0xe58d\n"
        ".hword 0x010b, 0xe5d4, 0x3004, 0xe3a0\n"
        ".hword 0x2001, 0xe286, 0x1004, 0xe280\n"
        ".hword 0x000b, 0xe1a0, 0xcf21, 0xeb00\n"
        ".hword 0x0008, 0xe59d, 0x1007, 0xe1a0\n"
        ".hword 0xcb3a, 0xeb00, 0x0008, 0xe59d\n"
        ".hword 0x100a, 0xe1a0, 0xcbe0, 0xeb00\n"
        ".hword 0x1005, 0xe1a0, 0x000b, 0xe1a0\n"
        ".hword 0xcb34, 0xeb00, 0xd00c, 0xe28d\n"
        ".hword 0x1008, 0xe1a0, 0x000b, 0xe1a0\n"
        ".hword 0x4ff0, 0xe8bd, 0xcbd8, 0xea00\n"
        ".hword 0x3004, 0xe3a0, 0x2003, 0xe3a0\n"
        ".hword 0x100c, 0xe3a0, 0x0d25, 0xe285\n"
        ".hword 0xcf0e, 0xeb00, 0x3004, 0xe3a0\n"
        ".hword 0x0008, 0xe59d, 0x2003, 0xe1a0\n"
        ".hword 0x1010, 0xe3a0, 0x9000, 0xe58d\n"
        ".hword 0x9004, 0xe58d, 0xcf07, 0xeb00\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0xffb7, 0xeaff, 0xdcf0, 0x0043\n"
    );
};

// DECOMP_FUNC(0x00300710, 688)
extern "C" __attribute__((naked)) void engine_func_00300710() {
    asm volatile(
        ".arm\n"
        ".hword 0x4ff0, 0xe92d, 0xd074, 0xe24d\n"
        ".hword 0x0000, 0xe3a0, 0x5a0f, 0xebfe\n"
        ".hword 0x0060, 0xe58d, 0x0001, 0xe3a0\n"
        ".hword 0x5a0c, 0xebfe, 0x0068, 0xe58d\n"
        ".hword 0x4d58, 0xebfe, 0x8000, 0xe1a0\n"
        ".hword 0x0178, 0xe59f, 0x0000, 0xe590\n"
        ".hword 0xf914, 0xebfd, 0x4000, 0xe3a0\n"
        ".hword 0x9b07, 0xe288, 0xa004, 0xe1a0\n"
        ".hword 0xb001, 0xe3a0, 0x6d7f, 0xe288\n"
        ".hword 0x9fa6, 0xe289, 0x0054, 0xe58d\n"
        ".hword 0x0000, 0xe596, 0x1204, 0xe084\n"
        ".hword 0x1304, 0xe081, 0x5181, 0xe080\n"
        ".hword 0x0000, 0xe595, 0x0001, 0xe310\n"
        ".hword 0x0048, 0x0a00, 0x0040, 0xe310\n"
        ".hword 0x0046, 0x1a00, 0x00f8, 0xe1d5\n"
        ".hword 0x0000, 0xe350, 0x0043, 0xba00\n"
        ".hword 0x0068, 0xe59d, 0x7000, 0xe3a0\n"
        ".hword 0x0000, 0xe350, 0x0004, 0x0a00\n"
        ".hword 0x0001, 0xe350, 0x000b, 0x0a00\n"
        ".hword 0x0002, 0xe350, 0x7060, 0x059d\n"
        ".hword 0x0010, 0xea00, 0x0100, 0xe59f\n"
        ".hword 0x1100, 0xe59f, 0x20f5, 0xe190\n"
        ".hword 0x0060, 0xe59d, 0x0092, 0xe000\n"
        ".hword 0x1091, 0xe0c0, 0x12c0, 0xe1a0\n"
        ".hword 0x7fc0, 0xe041, 0x0007, 0xea00\n"
        ".hword 0x1f6e, 0xe3a0, 0x00dc, 0xe59f\n"
        ".hword 0x20f5, 0xe191, 0x1060, 0xe59d\n"
        ".hword 0x0192, 0xe001, 0x1190, 0xe0c0\n"
        ".hword 0x12c0, 0xe1a0, 0x7fc0, 0xe041\n"
        ".hword 0x0008, 0xe1a0, 0x4057, 0xebfd\n"
        ".hword 0x0184, 0xe1a0, 0x0034, 0xe58d\n"
        ".hword 0xb044, 0xe58d, 0xb048, 0xe58d\n"
        ".hword 0xa4fc, 0xe1cd, 0x1038, 0xe28d\n"
        ".hword 0xa040, 0xe58d, 0x0801, 0xe881\n"
        ".hword 0x2c01, 0xe285, 0x002c, 0xe58d\n"
        ".hword 0xa028, 0xe58d, 0x0030, 0xe58d\n"
        ".hword 0xa2f0, 0xe1cd, 0xa014, 0xe58d\n"
        ".hword 0xa018, 0xe58d, 0xa01c, 0xe58d\n"
        ".hword 0x3bf4, 0xe1d2, 0x2bf6, 0xe1d2\n"
        ".hword 0x1008, 0xe28d, 0x0000, 0xe3e0\n"
        ".hword 0x2010, 0xe58d, 0x0009, 0xe881\n"
        ".hword 0x3000, 0xe3a0, 0x0081, 0xe88d\n"
        ".hword 0x00f8, 0xe1d5, 0x1000, 0xe599\n"
        ".hword 0x2100, 0xe080, 0x0300, 0xe082\n"
        ".hword 0x2100, 0xe081, 0x1054, 0xe59d\n"
        ".hword 0x0003, 0xe1a0, 0x52da, 0xebfd\n"
        ".hword 0x3000, 0xe3a0, 0xa004, 0xe58d\n"
        ".hword 0x2034, 0xe59f, 0x1054, 0xe59d\n"
        ".hword 0x0003, 0xe1a0, 0xa000, 0xe58d\n"
        ".hword 0xa008, 0xe58d, 0x3fd7, 0xebfd\n"
        ".hword 0x4001, 0xe284, 0x0004, 0xe354\n"
        ".hword 0xffac, 0xbaff, 0xd074, 0xe28d\n"
        ".hword 0x0001, 0xe3a0, 0x8ff0, 0xe8bd\n"
        ".hword 0x427c, 0x0043, 0x01ba, 0x0000\n"
        ".hword 0x851f, 0x51eb, 0x01b5, 0x0100\n"
        ".hword 0x10e8, 0xe59f, 0x1000, 0xe7d1\n"
        ".hword 0x0000, 0xe351, 0x0035, 0x0a00\n"
        ".hword 0x10dc, 0xe59f, 0x3000, 0xe791\n"
        ".hword 0x0000, 0xe353, 0x1000, 0xd3a0\n"
        ".hword 0x0014, 0xda00, 0x1001, 0xe203\n"
        ".hword 0x0000, 0xe351, 0x2000, 0xe3a0\n"
        ".hword 0x0010, 0xda00, 0xc082, 0xe082\n"
        ".hword 0xc182, 0xe08c, 0xc10c, 0xe080\n"
        ".hword 0xcc57, 0xe28c, 0xc088, 0xe5dc\n"
        ".hword 0x0000, 0xe35c, 0x0006, 0x0a00\n"
        ".hword 0x1082, 0xe082, 0x1182, 0xe081\n"
        ".hword 0x0101, 0xe080, 0x0b15, 0xe280\n"
        ".hword 0x0fdf, 0xe280, 0x0000, 0xe590\n"
        ".hword 0xff1e, 0xe12f, 0x2001, 0xe282\n"
        ".hword 0x0001, 0xe152, 0xffee, 0xbaff\n"
        ".hword 0x0003, 0xe151, 0x0019, 0xaa00\n"
        ".hword 0x2081, 0xe081, 0x2181, 0xe082\n"
        ".hword 0x2102, 0xe080, 0x2c57, 0xe282\n"
        ".hword 0xc088, 0xe5d2, 0x0000, 0xe35c\n"
        ".hword 0x0005, 0x0a00, 0x2081, 0xe081\n"
        ".hword 0x1181, 0xe082, 0x0101, 0xe080\n"
        ".hword 0x0b15, 0xe280, 0x0fdf, 0xe280\n"
        ".hword 0x0007, 0xea00, 0x20b4, 0xe5d2\n"
        ".hword 0x0000, 0xe352, 0x0006, 0x0a00\n"
        ".hword 0x2081, 0xe081, 0x1181, 0xe082\n"
        ".hword 0x0101, 0xe080, 0x0b15, 0xe280\n"
        ".hword 0x0fea, 0xe280, 0x0000, 0xe590\n"
        ".hword 0xff1e, 0xe12f, 0x1002, 0xe281\n"
        ".hword 0x0001, 0xe153, 0xffe5, 0xcaff\n"
        ".hword 0x0000, 0xe3e0, 0xff1e, 0xe12f\n"
        ".hword 0x575d, 0x0000, 0x5758, 0x0000\n"
    );
};

// DECOMP_FUNC(0x003d0f48, 688)
extern "C" __attribute__((naked)) void engine_func_003d0f48() {
    asm volatile(
        ".arm\n"
        ".hword 0x5ff0, 0xe92d, 0x4000, 0xe1a0\n"
        ".hword 0x0000, 0xe3a0, 0xb001, 0xe3a0\n"
        ".hword 0x2000, 0xe594, 0x3200, 0xe080\n"
        ".hword 0x3300, 0xe083, 0x2d7f, 0xe282\n"
        ".hword 0x2000, 0xe592, 0x2183, 0xe792\n"
        ".hword 0x0002, 0xe312, 0x0020, 0x0312\n"
        ".hword 0x0002, 0x1a00, 0x0010, 0xe312\n"
        ".hword 0x2000, 0x0081, 0xb038, 0x05c2\n"
        ".hword 0x0001, 0xe280, 0x0004, 0xe350\n"
        ".hword 0xfff0, 0xbaff, 0x0000, 0xe594\n"
        ".hword 0x2000, 0xe3e0, 0x1003, 0xe3a0\n"
        ".hword 0x0a01, 0xe280, 0x0efe, 0xe280\n"
        ".hword 0xcd28, 0xebfb, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0x5e93, 0xebfb\n"
        ".hword 0x0a09, 0xe280, 0x810b, 0xe5d0\n"
        ".hword 0x0108, 0xe1a0, 0xd620, 0xebfb\n"
        ".hword 0x0000, 0xe358, 0x7000, 0xe1a0\n"
        ".hword 0x6000, 0xe3a0, 0x0009, 0xda00\n"
        ".hword 0x3008, 0xe1a0, 0x1001, 0xe287\n"
        ".hword 0x2002, 0xe280, 0xc000, 0xe3a0\n"
        ".hword 0x5000, 0xe3e0, 0x5004, 0xe4c0\n"
        ".hword 0xc004, 0xe4c1, 0x3001, 0xe253\n"
        ".hword 0xc004, 0xe4c2, 0xfffa, 0x1aff\n"
        ".hword 0x0000, 0xe358, 0x5000, 0xe3a0\n"
        ".hword 0x0076, 0xda00, 0xf000, 0xe320\n"
        ".hword 0x5e7c, 0xebfb, 0x0005, 0xe080\n"
        ".hword 0x0a09, 0xe280, 0x0fd0, 0xe1d0\n"
        ".hword 0x0000, 0xe350, 0x0021, 0xba00\n"
        ".hword 0x5e76, 0xebfb, 0x0005, 0xe080\n"
        ".hword 0x0a09, 0xe280, 0x0fd0, 0xe1d0\n"
        ".hword 0x5e69, 0xebfb, 0x9000, 0xe1b0\n"
        ".hword 0xf000, 0xe320, 0x0019, 0x0a00\n"
        ".hword 0x1001, 0xe3a0, 0x377e, 0xebfb\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0014, 0x1a00, 0x100a, 0xe3a0\n"
        ".hword 0x0009, 0xe1a0, 0x3778, 0xebfb\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x000e, 0x1a00, 0x1002, 0xe3a0\n"
        ".hword 0x0009, 0xe1a0, 0x3772, 0xebfb\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0008, 0x1a00, 0xa106, 0xe087\n"
        ".hword 0x5000, 0xe5ca, 0x0048, 0xe5d9\n"
        ".hword 0x0001, 0xe5ca, 0x04b6, 0xe1d9\n"
        ".hword 0xa0af, 0xebfb, 0x0002, 0xe5d0\n"
        ".hword 0x6001, 0xe286, 0x0002, 0xe5ca\n"
        ".hword 0x5001, 0xe285, 0x0005, 0xe158\n"
        ".hword 0xffd3, 0xcaff, 0x0000, 0xe356\n"
        ".hword 0x0048, 0x0a00, 0x3128, 0xe59f\n"
        ".hword 0x2004, 0xe3a0, 0x1006, 0xe1a0\n"
        ".hword 0x0007, 0xe1a0, 0x9b8b, 0xfbfb\n"
        ".hword 0x0003, 0xe356, 0x6003, 0xc3a0\n"
        ".hword 0x0002, 0xca00, 0x0000, 0xe356\n"
        ".hword 0x0000, 0xd3a0, 0x0013, 0xda00\n"
        ".hword 0x0001, 0xe206, 0x0001, 0xe350\n"
        ".hword 0x0010, 0x1a00, 0x1000, 0xe594\n"
        ".hword 0x2000, 0xe5d7, 0x1a01, 0xe281\n"
        ".hword 0x1efd, 0xe281, 0x2001, 0xe282\n"
        ".hword 0x1008, 0xe891, 0x221b, 0xe1a0\n"
        ".hword 0x3002, 0xe183, 0x2fc2, 0xe18c\n"
        ".hword 0x2004, 0xe581, 0x3000, 0xe581\n"
        ".hword 0x1000, 0xe594, 0x2000, 0xe5d7\n"
        ".hword 0x1a01, 0xe281, 0x1efe, 0xe281\n"
        ".hword 0x2001, 0xe282, 0x2000, 0xe5c1\n"
        ".hword 0x0006, 0xe150, 0x0027, 0xaa00\n"
        ".hword 0x1100, 0xe087, 0x2000, 0xe594\n"
        ".hword 0x3000, 0xe5d1, 0x9a01, 0xe280\n"
        ".hword 0x2a01, 0xe282, 0x3001, 0xe283\n"
        ".hword 0x2efd, 0xe282, 0x331b, 0xe1a0\n"
        ".hword 0xc000, 0xe592, 0x5004, 0xe592\n"
        ".hword 0x8fc3, 0xe1a0, 0x300c, 0xe183\n"
        ".hword 0xc008, 0xe185, 0x1008, 0xe882\n"
        ".hword 0x9efe, 0xe289, 0x2000, 0xe5d1\n"
        ".hword 0x3000, 0xe594, 0xac1f, 0xe280\n"
        ".hword 0x2001, 0xe282, 0x0002, 0xe280\n"
        ".hword 0x2009, 0xe7c3, 0x3000, 0xe594\n"
        ".hword 0x2004, 0xe5d1, 0x0006, 0xe150\n"
        ".hword 0x3a01, 0xe283, 0x2001, 0xe282\n"
        ".hword 0x3efd, 0xe283, 0x221b, 0xe1a0\n"
        ".hword 0xc000, 0xe593, 0x5004, 0xe593\n"
        ".hword 0x8fc2, 0xe1a0, 0x200c, 0xe182\n"
        ".hword 0xc008, 0xe185, 0x1004, 0xe883\n"
        ".hword 0xa0e1, 0xe28a, 0x1004, 0xe5d1\n"
        ".hword 0x2000, 0xe594, 0x1001, 0xe281\n"
        ".hword 0x100a, 0xe7c2, 0xffd7, 0xbaff\n"
        ".hword 0x0007, 0xe1a0, 0x5ff0, 0xe8bd\n"
        ".hword 0xff6f, 0xeaf9, 0xb580, 0x0032\n"
    );
};

// DECOMP_FUNC(0x00204d6c, 692)
extern "C" __attribute__((naked)) void camp_func_00204d6c() {
    asm volatile(
        ".arm\n"
        ".hword 0x4ff0, 0xe92d, 0x8b04, 0xed2d\n"
        ".hword 0x5000, 0xe1a0, 0x6001, 0xe1a0\n"
        ".hword 0xd054, 0xe24d, 0x7002, 0xe1a0\n"
        ".hword 0x1003, 0xe1a0, 0x001a, 0xe3a0\n"
        ".hword 0xea4f, 0xeb02, 0x4000, 0xe1a0\n"
        ".hword 0x00fa, 0xe1d0, 0x90b5, 0xe3a0\n"
        ".hword 0x2019, 0xe3a0, 0x0006, 0xe080\n"
        ".hword 0x0201, 0xe88d, 0x00f8, 0xe1d4\n"
        ".hword 0x101a, 0xe3a0, 0x3005, 0xe080\n"
        ".hword 0x0002, 0xe3a0, 0xe9e6, 0xeb02\n"
        ".hword 0x11fc, 0xe59f, 0x8a7f, 0xed9f\n"
        ".hword 0x8a7f, 0xeddf, 0x9a7f, 0xed9f\n"
        ".hword 0x0000, 0xe357, 0xa010, 0xe28d\n"
        ".hword 0xb008, 0xe3a0, 0x001a, 0xe3a0\n"
        ".hword 0x0046, 0x0a00, 0xea3a, 0xeb02\n"
        ".hword 0x8000, 0xe1a0, 0x0007, 0xe1a0\n"
        ".hword 0xe07f, 0xeb02, 0x2000, 0xe1a0\n"
        ".hword 0x1f75, 0xe28f, 0x0010, 0xe28d\n"
        ".hword 0xe67e, 0xfa02, 0x00fa, 0xe1d4\n"
        ".hword 0x10fa, 0xe1d8, 0x20f8, 0xe1d4\n"
        ".hword 0x30f8, 0xe1d8, 0x0001, 0xe080\n"
        ".hword 0x0006, 0xe080, 0x1003, 0xe082\n"
        ".hword 0x1005, 0xe081, 0x0a90, 0xee00\n"
        ".hword 0x1a10, 0xee00, 0x2a48, 0xeeb0\n"
        ".hword 0x1a68, 0xeef0, 0x1a49, 0xeeb0\n"
        ".hword 0x1088, 0xe59d, 0x0ae0, 0xeef8\n"
        ".hword 0x0ac0, 0xeeb8, 0x2010, 0xe28d\n"
        ".hword 0x0002, 0xe3a0, 0xe64b, 0xeb02\n"
        ".hword 0x1180, 0xe59f, 0x001a, 0xe3a0\n"
        ".hword 0xea1d, 0xeb02, 0x1000, 0xe3a0\n"
        ".hword 0x1000, 0xe58d, 0x1004, 0xe58d\n"
        ".hword 0x20fa, 0xe1d0, 0x10fa, 0xe1d4\n"
        ".hword 0x30f8, 0xe1d4, 0x00f8, 0xe1d0\n"
        ".hword 0x1002, 0xe081, 0x2006, 0xe081\n"
        ".hword 0x0003, 0xe080, 0x1005, 0xe080\n"
        ".hword 0x0077, 0xe6bf, 0x30b5, 0xe3a0\n"
        ".hword 0xc838, 0xeb02, 0x1140, 0xe59f\n"
        ".hword 0x001a, 0xe3a0, 0xea0c, 0xeb02\n"
        ".hword 0x8000, 0xe1a0, 0x0007, 0xe1a0\n"
        ".hword 0x217b, 0xeb02, 0x2000, 0xe1a0\n"
        ".hword 0x1f4a, 0xe28f, 0x0010, 0xe28d\n"
        ".hword 0xe650, 0xfa02, 0x2004, 0xe28d\n"
        ".hword 0xb000, 0xe58d, 0x0600, 0xe882\n"
        ".hword 0x00fa, 0xe1d4, 0x20fa, 0xe1d8\n"
        ".hword 0x10f8, 0xe1d4, 0x30f8, 0xe1d8\n"
        ".hword 0x2000, 0xe082, 0x2006, 0xe082\n"
        ".hword 0x0003, 0xe081, 0x1005, 0xe080\n"
        ".hword 0x3001, 0xe3a0, 0x0000, 0xe3a0\n"
        ".hword 0xe49e, 0xeb02, 0xd054, 0xe28d\n"
        ".hword 0x8b04, 0xecbd, 0x8ff0, 0xe8bd\n"
        ".hword 0xf000, 0xe320, 0xe9f2, 0xeb02\n"
        ".hword 0x7000, 0xe1a0, 0x10d0, 0xe28f\n"
        ".hword 0x0010, 0xe28d, 0xe639, 0xfa02\n"
        ".hword 0x00fa, 0xe1d4, 0x20fa, 0xe1d7\n"
        ".hword 0x10f8, 0xe1d4, 0x30f8, 0xe1d7\n"
        ".hword 0x0002, 0xe080, 0x0006, 0xe080\n"
        ".hword 0x1003, 0xe081, 0x1005, 0xe081\n"
        ".hword 0x0a90, 0xee00, 0x1a10, 0xee00\n"
        ".hword 0x2a48, 0xeeb0, 0x1a68, 0xeef0\n"
        ".hword 0x1a49, 0xeeb0, 0x10c8, 0xe59f\n"
        ".hword 0x0ae0, 0xeef8, 0x0ac0, 0xeeb8\n"
        ".hword 0x2010, 0xe28d, 0x0002, 0xe3a0\n"
        ".hword 0xe606, 0xeb02, 0x1070, 0xe59f\n"
        ".hword 0x001a, 0xe3a0, 0xe9d8, 0xeb02\n"
        ".hword 0x7000, 0xe1a0, 0x10a4, 0xe28f\n"
        ".hword 0x0010, 0xe28d, 0xe61f, 0xfa02\n"
        ".hword 0x2004, 0xe28d, 0xb000, 0xe58d\n"
        ".hword 0x0600, 0xe882, 0x00fa, 0xe1d4\n"
        ".hword 0x20fa, 0xe1d7, 0x10f8, 0xe1d4\n"
        ".hword 0x30f8, 0xe1d7, 0x2000, 0xe082\n"
        ".hword 0x2006, 0xe082, 0x0003, 0xe081\n"
        ".hword 0x1005, 0xe080, 0x3001, 0xe3a0\n"
        ".hword 0x0000, 0xe3a0, 0xe46d, 0xeb02\n"
        ".hword 0xd054, 0xe28d, 0x8b04, 0xecbd\n"
        ".hword 0x8ff0, 0xe8bd, 0x040f, 0x0000\n"
        ".hword 0x0000, 0x3f80, 0x0000, 0x0000\n"
        ".hword 0x0000, 0x3e96, 0x7325, 0x0000\n"
        ".hword 0x040e, 0x0000, 0x0521, 0x0000\n"
        ".hword 0x6425, 0x0000, 0x6d82, 0x8582\n"
        ".hword 0x9782, 0x4081, 0x9282, 0x8582\n"
        ".hword 0x8782, 0x8982, 0x9382, 0x9482\n"
        ".hword 0x9282, 0x8182, 0x9482, 0x8982\n"
        ".hword 0x8f82, 0x8e82, 0x4081, 0x9082\n"
        ".hword 0x8f82, 0x9382, 0x9382, 0x8982\n"
        ".hword 0x8282, 0x8c82, 0x8582, 0x4981\n"
        ".hword 0x0000, 0x0000, 0x5aff, 0x5a5a\n"
        ".hword 0x2d2d, 0x002d\n"
    );
};

// DECOMP_FUNC(0x00338f30, 692)
extern "C" __attribute__((naked)) void script_vm_func_00338f30() {
    asm volatile(
        ".arm\n"
        ".hword 0x41f0, 0xe92d, 0x6901, 0xe280\n"
        ".hword 0x6e4a, 0xe286, 0x5000, 0xe1a0\n"
        ".hword 0x8b02, 0xed2d, 0x0000, 0xe596\n"
        ".hword 0x3284, 0xe59f, 0x0006, 0xe3c0\n"
        ".hword 0x0000, 0xe586, 0x3005, 0xe793\n"
        ".hword 0x3020, 0xe203, 0x2003, 0xe1b0\n"
        ".hword 0x0036, 0x1a00, 0x226c, 0xe59f\n"
        ".hword 0x2005, 0xe792, 0x0901, 0xe312\n"
        ".hword 0x0032, 0x1a00, 0x0902, 0xe312\n"
        ".hword 0x002e, 0x1a00, 0x0c02, 0xe310\n"
        ".hword 0x002e, 0x1a00, 0x20e0, 0xe595\n"
        ".hword 0x4000, 0xe3a0, 0x0801, 0xe312\n"
        ".hword 0x0028, 0x1a00, 0x0802, 0xe312\n"
        ".hword 0x0028, 0x1a00, 0x0000, 0xe351\n"
        ".hword 0x0004, 0x0a00, 0x0063, 0xe3a0\n"
        ".hword 0x1723, 0xebfc, 0x0046, 0xe350\n"
        ".hword 0x0022, 0xba00, 0x0081, 0xea00\n"
        ".hword 0x114c, 0xe5d5, 0x0001, 0xe351\n"
        ".hword 0x000a, 0x0a00, 0x0002, 0xe351\n"
        ".hword 0x001a, 0x0a00, 0x0003, 0xe351\n"
        ".hword 0x001a, 0x0a00, 0x8a80, 0xeddf\n"
        ".hword 0x8a68, 0xeeb0, 0xf5c2, 0xebfd\n"
        ".hword 0x07b2, 0xe1d0, 0x0002, 0xe310\n"
        ".hword 0x001f, 0x1a00, 0x0015, 0xea00\n"
        ".hword 0x0104, 0xe085, 0x00c8, 0xe590\n"
        ".hword 0x0000, 0xe350, 0x0007, 0x0a00\n"
        ".hword 0x0070, 0xe6ff, 0x00d6, 0xebfe\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0002, 0x0a00, 0x0002, 0xe5d0\n"
        ".hword 0x0027, 0xe350, 0xffec, 0x0aff\n"
        ".hword 0x4001, 0xe284, 0x0006, 0xe354\n"
        ".hword 0xfff0, 0xbaff, 0x1000, 0xe596\n"
        ".hword 0x1008, 0xe381, 0x0063, 0xea00\n"
        ".hword 0x0006, 0xe380, 0x0000, 0xe586\n"
        ".hword 0x8b02, 0xecbd, 0x81f0, 0xe8bd\n"
        ".hword 0xf000, 0xe320, 0xf5a6, 0xebfd\n"
        ".hword 0x42f6, 0xe1d0, 0xf000, 0xe320\n"
        ".hword 0xf5a3, 0xebfd, 0x02f8, 0xe1d0\n"
        ".hword 0x0004, 0xe080, 0x0a10, 0xee00\n"
        ".hword 0x8ac0, 0xeeb8, 0x7000, 0xe3a0\n"
        ".hword 0x4007, 0xe1a0, 0xf000, 0xe320\n"
        ".hword 0xbe62, 0xebfd, 0x0004, 0xe080\n"
        ".hword 0x0c91, 0xe280, 0x00d8, 0xe1d0\n"
        ".hword 0x0000, 0xe350, 0x000f, 0xba00\n"
        ".hword 0x0004, 0xe1a0, 0x6d24, 0xebfc\n"
        ".hword 0x14b4, 0xe1d0, 0x0002, 0xe311\n"
        ".hword 0x0b01, 0x0311, 0x0004, 0x0311\n"
        ".hword 0x0008, 0x1a00, 0x11f8, 0xe1d0\n"
        ".hword 0x01fa, 0xe1d0, 0x0001, 0xe080\n"
        ".hword 0x0a10, 0xee00, 0x0ac0, 0xeeb8\n"
        ".hword 0x0ac8, 0xeeb4, 0xfa10, 0xeef1\n"
        ".hword 0x0a10, 0xce00, 0x8ac0, 0xceb8\n"
        ".hword 0x4001, 0xe284, 0x0003, 0xe354\n"
        ".hword 0xffe5, 0xbaff, 0x4000, 0xe3a0\n"
        ".hword 0x0104, 0xe085, 0x00c8, 0xe590\n"
        ".hword 0x0000, 0xe350, 0x000d, 0x0a00\n"
        ".hword 0x0070, 0xe6ff, 0xdde0, 0xebfd\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0008, 0x0a00, 0x11b2, 0xe1d0\n"
        ".hword 0x01b4, 0xe1d0, 0x0001, 0xe080\n"
        ".hword 0x0a10, 0xee00, 0x0a40, 0xeeb8\n"
        ".hword 0x0ae8, 0xeeb4, 0xfa10, 0xeef1\n"
        ".hword 0x0a10, 0xce00, 0x8a40, 0xcef8\n"
        ".hword 0x4001, 0xe284, 0x0006, 0xe354\n"
        ".hword 0xffea, 0xbaff, 0x0a29, 0xed9f\n"
        ".hword 0x0a68, 0xee78, 0x0a80, 0xee20\n"
        ".hword 0x0ac0, 0xeebd, 0x0a10, 0xee10\n"
        ".hword 0x002d, 0xe280, 0x4007, 0xe080\n"
        ".hword 0x16a6, 0xebfc, 0x4a10, 0xee00\n"
        ".hword 0x0a07, 0xedd0, 0x0ac0, 0xeeb8\n"
        ".hword 0x0a80, 0xee20, 0x0ac0, 0xeebd\n"
        ".hword 0x4a10, 0xee10, 0x7945, 0xebfd\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0003, 0x0a00, 0x7941, 0xebfd\n"
        ".hword 0x0001, 0xe350, 0x4050, 0x03a0\n"
        ".hword 0x0004, 0xea00, 0x001e, 0xe354\n"
        ".hword 0x401e, 0xb3a0, 0x0001, 0xba00\n"
        ".hword 0x0046, 0xe354, 0x4046, 0xc3a0\n"
        ".hword 0xf000, 0xe320, 0x0000, 0xe3a0\n"
        ".hword 0x4000, 0xe084, 0x0064, 0xe3a0\n"
        ".hword 0x16a1, 0xebfc, 0x0004, 0xe150\n"
        ".hword 0xf000, 0xe320, 0xff9f, 0xdaff\n"
        ".hword 0x1000, 0xe596, 0x1006, 0xe381\n"
        ".hword 0x1000, 0xe586, 0x8b02, 0xecbd\n"
        ".hword 0x81f0, 0xe8bd, 0x44ac, 0x0000\n"
        ".hword 0x44a8, 0x0000, 0x0000, 0x0000\n"
        ".hword 0xcccd, 0x3e4c\n"
    );
};

// DECOMP_FUNC(0x003a211c, 696)
extern "C" __attribute__((naked)) void shop_func_003a211c() {
    asm volatile(
        ".arm\n"
        ".hword 0x4ff0, 0xe92d, 0x5000, 0xe1a0\n"
        ".hword 0xd02c, 0xe24d, 0x2860, 0xe590\n"
        ".hword 0x037c, 0xe590, 0x0009, 0xe352\n"
        ".hword 0xf102, 0x379f, 0x0013, 0xea00\n"
        ".hword 0x2160, 0x003a, 0x2168, 0x003a\n"
        ".hword 0x2168, 0x003a, 0x2170, 0x003a\n"
        ".hword 0x2170, 0x003a, 0x2170, 0x003a\n"
        ".hword 0x2178, 0x003a, 0x2180, 0x003a\n"
        ".hword 0x2188, 0x003a, 0x1000, 0xe3a0\n"
        ".hword 0x0008, 0xea00, 0x1001, 0xe3a0\n"
        ".hword 0x0006, 0xea00, 0x1002, 0xe3a0\n"
        ".hword 0x0004, 0xea00, 0x100b, 0xe3a0\n"
        ".hword 0x0002, 0xea00, 0x1003, 0xe3a0\n"
        ".hword 0x0000, 0xea00, 0x1004, 0xe3a0\n"
        ".hword 0x3000, 0xe3a0, 0x0000, 0xe58d\n"
        ".hword 0x2003, 0xe1a0, 0x0d0e, 0xe285\n"
        ".hword 0x3b2c, 0xebfa, 0x937c, 0xe595\n"
        ".hword 0x6001, 0xe3a0, 0x6004, 0xe58d\n"
        ".hword 0x9000, 0xe58d, 0x0864, 0xe595\n"
        ".hword 0x4b02, 0xe285, 0x3000, 0xe3a0\n"
        ".hword 0x1061, 0xe280, 0x4064, 0xe284\n"
        ".hword 0x2003, 0xe1a0, 0x0d0e, 0xe285\n"
        ".hword 0x3ee3, 0xebfa, 0x3000, 0xe3a0\n"
        ".hword 0x2003, 0xe1a0, 0x1065, 0xe3a0\n"
        ".hword 0x0d0e, 0xe285, 0x6004, 0xe58d\n"
        ".hword 0x9000, 0xe58d, 0x3edc, 0xebfa\n"
        ".hword 0x3000, 0xe3a0, 0x2003, 0xe1a0\n"
        ".hword 0x1066, 0xe3a0, 0x0d0e, 0xe285\n"
        ".hword 0x6004, 0xe58d, 0x9000, 0xe58d\n"
        ".hword 0x3ed5, 0xebfa, 0x11bc, 0xe59f\n"
        ".hword 0x2000, 0xe594, 0x01b8, 0xe59f\n"
        ".hword 0x30e4, 0xe281, 0xa008, 0xe28d\n"
        ".hword 0x1188, 0xe893, 0x0182, 0xe080\n"
        ".hword 0x0014, 0xe890, 0x1188, 0xe88a\n"
        ".hword 0x30f4, 0xe281, 0x7018, 0xe28d\n"
        ".hword 0x1009, 0xe893, 0x1100, 0xe591\n"
        ".hword 0x6004, 0xe58d, 0x9000, 0xe58d\n"
        ".hword 0x1024, 0xe58d, 0x1009, 0xe887\n"
        ".hword 0x0008, 0xe28d, 0x3000, 0xe3a0\n"
        ".hword 0x1102, 0xe790, 0x2003, 0xe1a0\n"
        ".hword 0x0d0e, 0xe285, 0x3ebe, 0xebfa\n"
        ".hword 0x0018, 0xe28d, 0x6004, 0xe58d\n"
        ".hword 0x9000, 0xe58d, 0x1104, 0xe790\n"
        ".hword 0x3000, 0xe3a0, 0x2003, 0xe1a0\n"
        ".hword 0x0d0e, 0xe285, 0x3eb6, 0xebfa\n"
        ".hword 0x0004, 0xe595, 0x0005, 0xe350\n"
        ".hword 0x0009, 0x1350, 0x004b, 0x0a00\n"
        ".hword 0x0006, 0xe350, 0x000a, 0x1350\n"
        ".hword 0x0048, 0x0a00, 0x0007, 0xe350\n"
        ".hword 0x000b, 0x1350, 0x0045, 0x0a00\n"
        ".hword 0x000f, 0xe350, 0x0010, 0x1350\n"
        ".hword 0x6000, 0x13a0, 0x0041, 0x0a00\n"
        ".hword 0x0860, 0xe595, 0x1580, 0xe080\n"
        ".hword 0x2080, 0xe080, 0x0280, 0xe062\n"
        ".hword 0x1081, 0xe085, 0x0100, 0xe085\n"
        ".hword 0x8b03, 0xe281, 0xbd22, 0xe280\n"
        ".hword 0x8094, 0xe288, 0x000b, 0xe1a0\n"
        ".hword 0xf236, 0xebfb, 0xa000, 0xe1a0\n"
        ".hword 0x000b, 0xe1a0, 0x456d, 0xebfa\n"
        ".hword 0x7000, 0xe250, 0x4000, 0xe3a0\n"
        ".hword 0x000f, 0xda00, 0x0000, 0xe356\n"
        ".hword 0x0004, 0x0a00, 0x000b, 0xe1a0\n"
        ".hword 0x7ade, 0xebfa, 0x0004, 0xe150\n"
        ".hword 0xf000, 0xe320, 0x0005, 0x0a00\n"
        ".hword 0x0004, 0xe08a, 0x2000, 0xe3a0\n"
        ".hword 0x3100, 0xe088, 0x1001, 0xe284\n"
        ".hword 0x0005, 0xe1a0, 0x340b, 0xebfa\n"
        ".hword 0x4001, 0xe284, 0x0007, 0xe154\n"
        ".hword 0xffef, 0xbaff, 0x0000, 0xe356\n"
        ".hword 0x0008, 0x159b, 0x0000, 0x1350\n"
        ".hword 0x0009, 0xda00, 0x000b, 0xe1a0\n"
        ".hword 0x4511, 0xebfa, 0x4100, 0xe088\n"
        ".hword 0x000b, 0xe1a0, 0x7ac9, 0xebfa\n"
        ".hword 0x1001, 0xe280, 0x3004, 0xe1a0\n"
        ".hword 0x2001, 0xe3a0, 0x0005, 0xe1a0\n"
        ".hword 0x33fa, 0xebfa, 0x000b, 0xe1a0\n"
        ".hword 0x7ac2, 0xebfa, 0x6000, 0xe1a0\n"
        ".hword 0x000b, 0xe1a0, 0xf20d, 0xebfb\n"
        ".hword 0x385c, 0xe595, 0x4b02, 0xe285\n"
        ".hword 0x1000, 0xe1a0, 0x405c, 0xe284\n"
        ".hword 0x2006, 0xe1a0, 0x0003, 0xe1a0\n"
        ".hword 0x4434, 0xebfa, 0x0000, 0xe594\n"
        ".hword 0x1000, 0xe590, 0x2010, 0xe591\n"
        ".hword 0x1009, 0xe1a0, 0xff32, 0xe12f\n"
        ".hword 0xd02c, 0xe28d, 0x8ff0, 0xe8bd\n"
        ".hword 0x6001, 0xe3a0, 0xffbb, 0xeaff\n"
        ".hword 0x7594, 0x0040, 0xe020, 0x0044\n"
    );
};

// DECOMP_FUNC(0x0023187c, 700)
extern "C" __attribute__((naked)) void script_vm_func_0023187c() {
    asm volatile(
        ".arm\n"
        ".hword 0x4ff0, 0xe92d, 0x0065, 0xe351\n"
        ".hword 0x7000, 0xe3a0, 0x9000, 0xe1a0\n"
        ".hword 0x6001, 0xe1a0, 0x8b08, 0xed2d\n"
        ".hword 0xd014, 0xe24d, 0x8a93, 0xed9f\n"
        ".hword 0x700c, 0xe58d, 0x9a48, 0xeeb0\n"
        ".hword 0x9a48, 0xeef0, 0x8a48, 0xeef0\n"
        ".hword 0x0006, 0x0a00, 0x0066, 0xe356\n"
        ".hword 0x0a8d, 0xed9f, 0x0a8d, 0xeddf\n"
        ".hword 0x0007, 0x0a00, 0x0067, 0xe356\n"
        ".hword 0x0009, 0x0a00, 0x000c, 0xea00\n"
        ".hword 0x8a89, 0xed9f, 0x9a89, 0xed9f\n"
        ".hword 0x9a89, 0xeddf, 0x8a89, 0xeddf\n"
        ".hword 0x0007, 0xea00, 0x8a40, 0xeeb0\n"
        ".hword 0x9a87, 0xed9f, 0x9a87, 0xeddf\n"
        ".hword 0x0002, 0xea00, 0x8a40, 0xeeb0\n"
        ".hword 0x9a85, 0xed9f, 0x9a85, 0xeddf\n"
        ".hword 0x8a60, 0xeef0, 0xa013, 0xe3a0\n"
        ".hword 0x5000, 0xe3a0, 0x000d, 0xe1a0\n"
        ".hword 0xff54, 0xebff, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x006b, 0xda00\n"
        ".hword 0xb000, 0xe3a0, 0xaa7c, 0xed9f\n"
        ".hword 0xaa7c, 0xeddf, 0xba7c, 0xed9f\n"
        ".hword 0x1005, 0xe1a0, 0x000d, 0xe1a0\n"
        ".hword 0xff3b, 0xebff, 0x4000, 0xe1a0\n"
        ".hword 0x00d0, 0xe1d0, 0x0006, 0xe150\n"
        ".hword 0x005a, 0x1a00, 0x00b4, 0xe1d4\n"
        ".hword 0x0000, 0xe350, 0x0003, 0x0a00\n"
        ".hword 0x3c93, 0xeb02, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x0053, 0x0a00\n"
        ".hword 0x00b6, 0xe1d4, 0x0000, 0xe350\n"
        ".hword 0x0003, 0x0a00, 0x3c8c, 0xeb02\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x004c, 0x1a00, 0x00f8, 0xe1d4\n"
        ".hword 0x0005, 0xe350, 0x8194, 0x059f\n"
        ".hword 0x0002, 0x0a00, 0x0006, 0xe350\n"
        ".hword 0x818c, 0x159f, 0x818c, 0x059f\n"
        ".hword 0x3008, 0xe28d, 0x2004, 0xe28d\n"
        ".hword 0x1008, 0xe1a0, 0x000a, 0xe1a0\n"
        ".hword 0x6a91, 0xeb00, 0x10fe, 0xe1d4\n"
        ".hword 0x21f0, 0xe1d4, 0x1a89, 0xeeca\n"
        ".hword 0x1a90, 0xee00, 0x0a01, 0xed9d\n"
        ".hword 0x0087, 0xe087, 0x0207, 0xe080\n"
        ".hword 0x7001, 0xe287, 0x0100, 0xe089\n"
        ".hword 0x2ae0, 0xeeb8, 0x2a90, 0xee00\n"
        ".hword 0xae88, 0xe5a0, 0x1001, 0xe5d4\n"
        ".hword 0x1004, 0xe5c0, 0x0ae0, 0xeef8\n"
        ".hword 0x1a28, 0xee8b, 0x10b8, 0xe1d4\n"
        ".hword 0x2a48, 0xee32, 0x12bc, 0xe1c0\n"
        ".hword 0x1002, 0xe5d4, 0x1005, 0xe5c0\n"
        ".hword 0x2ae9, 0xee70, 0xb2be, 0xe1c0\n"
        ".hword 0xb0b6, 0xe1c0, 0x1a82, 0xee61\n"
        ".hword 0x2ac0, 0xeeb8, 0x30b4, 0xe1d4\n"
        ".hword 0x0ac0, 0xeeb8, 0x33b0, 0xe1c0\n"
        ".hword 0x30b6, 0xe1d4, 0x33b2, 0xe1c0\n"
        ".hword 0x80b8, 0xe1c0, 0x0a0a, 0xee62\n"
        ".hword 0x2a22, 0xee21, 0x1ae1, 0xeebd\n"
        ".hword 0x0a05, 0xed80, 0x1a10, 0xee11\n"
        ".hword 0x1ac2, 0xeebd, 0x1071, 0xe6bf\n"
        ".hword 0x2a10, 0xee11, 0x1a10, 0xee01\n"
        ".hword 0x2072, 0xe6bf, 0x1ac1, 0xeef8\n"
        ".hword 0x2a10, 0xee01, 0x2ae0, 0xee31\n"
        ".hword 0x1ac1, 0xeef8, 0x1ac2, 0xeebd\n"
        ".hword 0x0ae0, 0xee71, 0x1a10, 0xee11\n"
        ".hword 0x0ae0, 0xeefd, 0x1071, 0xe6bf\n"
        ".hword 0x2a90, 0xee10, 0x1a90, 0xee00\n"
        ".hword 0x100c, 0xe280, 0x2072, 0xe6bf\n"
        ".hword 0x2a10, 0xee01, 0x0ae0, 0xeef8\n"
        ".hword 0x1ac1, 0xeeb8, 0x0a02, 0xecc1\n"
        ".hword 0x1000, 0xe3e0, 0x0a02, 0xed9d\n"
        ".hword 0x0ac0, 0xeeb8, 0x0a06, 0xed80\n"
        ".hword 0xb3b4, 0xe1c0, 0x1048, 0xe580\n"
        ".hword 0x5001, 0xe285, 0x000d, 0xe1a0\n"
        ".hword 0xfee8, 0xebff, 0x0005, 0xe150\n"
        ".hword 0xf000, 0xe320, 0xff97, 0xcaff\n"
        ".hword 0x005c, 0xe59f, 0x105c, 0xe59f\n"
        ".hword 0x7009, 0xe780, 0x000c, 0xe59d\n"
        ".hword 0x0009, 0xe781, 0xd014, 0xe28d\n"
        ".hword 0x8b08, 0xecbd, 0x8ff0, 0xe8bd\n"
        ".hword 0x0000, 0x0000, 0xd000, 0xc684\n"
        ".hword 0x8800, 0x4710, 0x3800, 0xc6c7\n"
        ".hword 0x7800, 0x46e6, 0x8800, 0xc690\n"
        ".hword 0x7000, 0x4714, 0x3000, 0x46f2\n"
        ".hword 0xa000, 0xc68c, 0x6000, 0x46ea\n"
        ".hword 0x7000, 0xc694, 0x0000, 0x3f00\n"
        ".hword 0x8000, 0x439e, 0x0000, 0x43c8\n"
        ".hword 0x1bc3, 0x0000, 0x1bc5, 0x0000\n"
        ".hword 0x1bc4, 0x0000, 0x5a88, 0x0000\n"
        ".hword 0x61b0, 0x0000\n"
    );
};

// DECOMP_FUNC(0x003bedd0, 700)
extern "C" __attribute__((naked)) void ui_func_003bedd0() {
    asm volatile(
        ".arm\n"
        ".hword 0x4ff0, 0xe92d, 0x6002, 0xe1a0\n"
        ".hword 0x7000, 0xe1a0, 0x8003, 0xe1a0\n"
        ".hword 0xb001, 0xe1a0, 0x8b0a, 0xed2d\n"
        ".hword 0xd054, 0xe24d, 0x00a4, 0xe28d\n"
        ".hword 0x8a40, 0xeef0, 0x9a60, 0xeef0\n"
        ".hword 0x0600, 0xe890, 0xaa28, 0xeddd\n"
        ".hword 0xca9a, 0xed9f, 0x8a9a, 0xed9f\n"
        ".hword 0x53a2, 0xebfb, 0x1006, 0xe1a0\n"
        ".hword 0x0000, 0xe58d, 0xfba1, 0xebfa\n"
        ".hword 0x4000, 0xe1a0, 0x0000, 0xe59d\n"
        ".hword 0x1008, 0xe1a0, 0xfb9d, 0xebfa\n"
        ".hword 0x5000, 0xe1a0, 0x0ff2, 0xe1d4\n"
        ".hword 0x1ff0, 0xe1d4, 0x2000, 0xe5d4\n"
        ".hword 0x0a10, 0xee00, 0x1a90, 0xee00\n"
        ".hword 0x0004, 0xe312, 0x8a8b, 0x1d9f\n"
        ".hword 0x0007, 0xe3a0, 0xaac0, 0xeeb8\n"
        ".hword 0x6a10, 0xee00, 0xbae0, 0xeeb8\n"
        ".hword 0x0ac0, 0xeeb8, 0xae70, 0xebf9\n"
        ".hword 0x9a40, 0xeeb0, 0x8a10, 0xee00\n"
        ".hword 0x000a, 0xe3a0, 0x0ac0, 0xeeb8\n"
        ".hword 0xae6b, 0xebf9, 0xba40, 0xeef0\n"
        ".hword 0x1008, 0xe1a0, 0x0006, 0xe1a0\n"
        ".hword 0xfe84, 0xebff, 0x0a40, 0xeef0\n"
        ".hword 0x0a2b, 0xee29, 0x0000, 0xe59d\n"
        ".hword 0x1006, 0xe1a0, 0x9a20, 0xee20\n"
        ".hword 0x0f3d, 0xebfb, 0x2000, 0xe1a0\n"
        ".hword 0x1000, 0xe59d, 0x0028, 0xe28d\n"
        ".hword 0x21cd, 0xebfa, 0x0028, 0xe28d\n"
        ".hword 0x8000, 0xe3a0, 0x0a08, 0xec90\n"
        ".hword 0x0004, 0xe28d, 0x104c, 0xe28d\n"
        ".hword 0x0a08, 0xec80, 0x0048, 0xe59d\n"
        ".hword 0x0024, 0xe58d, 0x00b6, 0xe1dd\n"
        ".hword 0x804c, 0xe58d, 0xaf70, 0xebf9\n"
        ".hword 0x536e, 0xebfb, 0x1006, 0xe1a0\n"
        ".hword 0x0f2b, 0xebfb, 0x0000, 0xe590\n"
        ".hword 0x0002, 0xe310, 0x000a, 0x0a00\n"
        ".hword 0x0007, 0xe1a0, 0xbd3d, 0xebfb\n"
        ".hword 0x6000, 0xe1b0, 0x0006, 0x0a00\n"
        ".hword 0x0007, 0xe1a0, 0xbd22, 0xebfb\n"
        ".hword 0x1000, 0xe1a0, 0x2001, 0xe3a0\n"
        ".hword 0x0006, 0xe1a0, 0x1484, 0xebfb\n"
        ".hword 0x8000, 0xe1a0, 0x00bc, 0xe1dd\n"
        ".hword 0x100a, 0xe089, 0x1a10, 0xee01\n"
        ".hword 0x0a10, 0xee00, 0xba52, 0xeddf\n"
        ".hword 0x1a52, 0xeddf, 0x0a52, 0xeddf\n"
        ".hword 0x0000, 0xe357, 0x1ac1, 0xeeb8\n"
        ".hword 0x0a40, 0xeeb8, 0x1a21, 0xee21\n"
        ".hword 0x0a2b, 0xee20, 0x0012, 0xca00\n"
        ".hword 0x1aea, 0xeeb8, 0x0001, 0xe35b\n"
        ".hword 0x0007, 0x0a00, 0x1a01, 0xee3a\n"
        ".hword 0x0a20, 0xee61, 0x0aa8, 0xee60\n"
        ".hword 0x0aa9, 0xee60, 0x0a89, 0xee60\n"
        ".hword 0x0a88, 0xee60, 0x0a80, 0xee20\n"
        ".hword 0x0010, 0xea00, 0x1a01, 0xee3b\n"
        ".hword 0x0a20, 0xee61, 0x0aa8, 0xee60\n"
        ".hword 0x0aa9, 0xee60, 0x0a89, 0xee60\n"
        ".hword 0x0a88, 0xee60, 0x0a80, 0xee20\n"
        ".hword 0x0008, 0xea00, 0xaa21, 0xee0b\n"
        ".hword 0x2a38, 0xed9f, 0x8a02, 0xee4a\n"
        ".hword 0x0aa0, 0xee68, 0x0aa9, 0xee60\n"
        ".hword 0x0a89, 0xee60, 0x0a88, 0xee60\n"
        ".hword 0x0a80, 0xee60, 0x0a81, 0xee80\n"
        ".hword 0x8a90, 0xee00, 0x0000, 0xe59d\n"
        ".hword 0x0901, 0xe280, 0x0a0c, 0xee30\n"
        ".hword 0x0ae0, 0xeef8, 0x0e4a, 0xe280\n"
        ".hword 0x0000, 0xe590, 0x0701, 0xe310\n"
        ".hword 0x8a20, 0xee30, 0x000d, 0x1a00\n"
        ".hword 0x0000, 0xe5d4, 0x0004, 0xe310\n"
        ".hword 0x0000, 0xe5d5, 0x0004, 0xe200\n"
        ".hword 0x0002, 0x0a00, 0x0000, 0xe350\n"
        ".hword 0x0015, 0x0a00, 0x0001, 0xea00\n"
        ".hword 0x0000, 0xe350, 0x0012, 0x0a00\n"
        ".hword 0xf000, 0xe320, 0xfef5, 0xebf9\n"
        ".hword 0x0a00, 0xed90, 0x8a08, 0xee20\n"
        ".hword 0x014b, 0xe5d5, 0x1004, 0xe28d\n"
        ".hword 0x0001, 0xe080, 0x000e, 0xe5d0\n"
        ".hword 0x0a10, 0xee00, 0x0000, 0xe350\n"
        ".hword 0x0002, 0x0a00, 0x0a40, 0xeeb8\n"
        ".hword 0x0a2b, 0xee20, 0x8a00, 0xee28\n"
        ".hword 0xd054, 0xe28d, 0x0ac8, 0xeebd\n"
        ".hword 0x8b0a, 0xecbd, 0x0a10, 0xee10\n"
        ".hword 0x8ff0, 0xe8bd, 0xf000, 0xe320\n"
        ".hword 0xfee2, 0xebf9, 0x0a02, 0xed90\n"
        ".hword 0xf000, 0xe320, 0xffea, 0xeaff\n"
        ".hword 0x0000, 0x0000, 0x0000, 0x3f80\n"
        ".hword 0xcccd, 0x3f4c, 0xd70a, 0x3c23\n"
        ".hword 0x0000, 0x3f00, 0xaaab, 0x3eaa\n"
        ".hword 0x0000, 0x4090\n"
    );
};

// DECOMP_FUNC(0x002080e0, 704)
extern "C" __attribute__((naked)) void engine_func_002080e0() {
    asm volatile(
        ".arm\n"
        ".hword 0x0000, 0xe3a0, 0x000c, 0xe581\n"
        ".hword 0x60b8, 0xe1c1, 0x0085, 0xea00\n"
        ".hword 0x00f6, 0xe1d1, 0x192a, 0xeb00\n"
        ".hword 0x1000, 0xe594, 0x0000, 0xe350\n"
        ".hword 0x0018, 0xe581, 0x50b8, 0xd1c1\n"
        ".hword 0x007e, 0xda00, 0x2000, 0xe1a0\n"
        ".hword 0x1e21, 0xe28f, 0x0008, 0xe28d\n"
        ".hword 0xd9b7, 0xfa02, 0x1d07, 0xe3a0\n"
        ".hword 0x0008, 0xe28d, 0x4869, 0xeb02\n"
        ".hword 0x1000, 0xe594, 0x0010, 0xe581\n"
        ".hword 0x00b8, 0xe1d1, 0x0001, 0xe280\n"
        ".hword 0x00b8, 0xe1c1, 0x0000, 0xe594\n"
        ".hword 0x0010, 0xe590, 0x9808, 0xeb02\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x006c, 0x0a00, 0x0000, 0xe594\n"
        ".hword 0x1001, 0xe3a0, 0x0010, 0xe590\n"
        ".hword 0x6158, 0xeb02, 0x0000, 0xe594\n"
        ".hword 0x0a48, 0xeeb0, 0x1000, 0xe3a0\n"
        ".hword 0x0010, 0xe590, 0x0008, 0xe590\n"
        ".hword 0x7635, 0xeb02, 0x0000, 0xe594\n"
        ".hword 0x0a48, 0xeeb0, 0x1000, 0xe3a0\n"
        ".hword 0x0010, 0xe590, 0x0008, 0xe590\n"
        ".hword 0xfc5a, 0xeb01, 0x0000, 0xe594\n"
        ".hword 0x10b4, 0xe1d0, 0x0013, 0xe351\n"
        ".hword 0xffcb, 0x1aff, 0x8a22, 0xed8d\n"
        ".hword 0x8a24, 0xed8d, 0x8a23, 0xedcd\n"
        ".hword 0x0010, 0xe590, 0x2088, 0xe28d\n"
        ".hword 0x1000, 0xe3a0, 0x0008, 0xe590\n"
        ".hword 0x11b8, 0xeb02, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0xffc0, 0xeaff\n"
        ".hword 0x0020, 0xe591, 0x0000, 0xe350\n"
        ".hword 0x0015, 0x0a00, 0x1024, 0xe591\n"
        ".hword 0x2038, 0xe3a0, 0x4f19, 0xeb01\n"
        ".hword 0x1000, 0xe594, 0x000c, 0xe581\n"
        ".hword 0x1001, 0xe3a0, 0x6133, 0xeb02\n"
        ".hword 0x0000, 0xe594, 0x0a48, 0xeeb0\n"
        ".hword 0x1000, 0xe3a0, 0x000c, 0xe590\n"
        ".hword 0x0008, 0xe590, 0x7610, 0xeb02\n"
        ".hword 0x0000, 0xe594, 0x0a48, 0xeeb0\n"
        ".hword 0x1000, 0xe3a0, 0x000c, 0xe590\n"
        ".hword 0x0008, 0xe590, 0xfc35, 0xeb01\n"
        ".hword 0x0000, 0xe594, 0x60b8, 0xe1c0\n"
        ".hword 0x0034, 0xea00, 0x00f4, 0xe1d1\n"
        ".hword 0x0029, 0xe350, 0x0015, 0x0a00\n"
        ".hword 0x002a, 0xe350, 0x002b, 0x1350\n"
        ".hword 0x0012, 0x0a00, 0x20b6, 0xe1d1\n"
        ".hword 0x01bc, 0xe1c1, 0x21be, 0xe1c1\n"
        ".hword 0x01fe, 0xe1d1, 0x0000, 0xe58d\n"
        ".hword 0x21fc, 0xe1d1, 0x10d4, 0xe28f\n"
        ".hword 0x0008, 0xe28d, 0x3002, 0xe1a0\n"
        ".hword 0xd961, 0xfa02, 0x1038, 0xe3a0\n"
        ".hword 0x0008, 0xe28d, 0x4813, 0xeb02\n"
        ".hword 0x1000, 0xe594, 0x000c, 0xe581\n"
        ".hword 0x00b8, 0xe1d1, 0x0001, 0xe280\n"
        ".hword 0x00b8, 0xe1c1, 0x001b, 0xea00\n"
        ".hword 0x2024, 0xe3a0, 0x0001, 0xe3a0\n"
        ".hword 0x21bc, 0xe1c1, 0x01be, 0xe1c1\n"
        ".hword 0xffea, 0xeaff, 0x000c, 0xe591\n"
        ".hword 0x97ad, 0xeb02, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x0011, 0x0a00\n"
        ".hword 0x0000, 0xe594, 0x1001, 0xe3a0\n"
        ".hword 0x000c, 0xe590, 0x60fd, 0xeb02\n"
        ".hword 0x0000, 0xe594, 0x0a48, 0xeeb0\n"
        ".hword 0x1000, 0xe3a0, 0x000c, 0xe590\n"
        ".hword 0x0008, 0xe590, 0x75da, 0xeb02\n"
        ".hword 0x0000, 0xe594, 0x0a48, 0xeeb0\n"
        ".hword 0x1000, 0xe3a0, 0x000c, 0xe590\n"
        ".hword 0x0008, 0xe590, 0xfbff, 0xeb01\n"
        ".hword 0x0000, 0xe594, 0x60b8, 0xe1c0\n"
        ".hword 0x0000, 0xe3a0, 0xd098, 0xe28d\n"
        ".hword 0x8b02, 0xecbd, 0x8070, 0xe8bd\n"
        ".hword 0x74d8, 0x0044, 0x0000, 0x0000\n"
        ".hword 0x4000, 0xc69c, 0xf91c, 0x0049\n"
        ".hword 0x616d, 0x2f70, 0x6b73, 0x2f79\n"
        ".hword 0x6b73, 0x5f79, 0x3025, 0x6432\n"
        ".hword 0x622e, 0x6d61, 0x0000, 0x0000\n"
        ".hword 0x616d, 0x2f70, 0x256d, 0x3330\n"
        ".hword 0x2f64, 0x256d, 0x3330, 0x5f64\n"
        ".hword 0x3025, 0x6432, 0x622e, 0x6d61\n"
        ".hword 0x0000, 0x0000, 0x0034, 0xe59f\n"
        ".hword 0x1000, 0xe3a0, 0x2280, 0xe590\n"
        ".hword 0x002c, 0xe59f, 0x0001, 0xe352\n"
        ".hword 0x0000, 0xe590, 0x11b4, 0x11c0\n"
        ".hword 0x0005, 0x1a00, 0x2001, 0xe3a0\n"
        ".hword 0x21b4, 0xe1c0, 0x1020, 0xe580\n"
        ".hword 0x1024, 0xe580, 0x1028, 0xe580\n"
        ".hword 0x102c, 0xe580, 0xff1e, 0xe12f\n"
        ".hword 0xf91c, 0x0049, 0x74d8, 0x0044\n"
    );
};

// DECOMP_FUNC(0x0018b39c, 708)
extern "C" __attribute__((naked)) void camp_func_0018b39c() {
    asm volatile(
        ".arm\n"
        ".hword 0x4ff0, 0xe92d, 0x7000, 0xe1a0\n"
        ".hword 0x0298, 0xe59f, 0xd054, 0xe24d\n"
        ".hword 0x6001, 0xe1a0, 0x8000, 0xe590\n"
        ".hword 0x0008, 0xe1a0, 0x4fa8, 0xeb04\n"
        ".hword 0x0008, 0xe1a0, 0x4fa0, 0xeb04\n"
        ".hword 0xb00b, 0xe3a0, 0x3007, 0xe1a0\n"
        ".hword 0x2000, 0xe3a0, 0x102f, 0xe3a0\n"
        ".hword 0x0002, 0xe3a0, 0x0840, 0xe88d\n"
        ".hword 0xd05d, 0xeb04, 0x0260, 0xe59f\n"
        ".hword 0x1020, 0xe3a0, 0x004c, 0xe58d\n"
        ".hword 0x002f, 0xe3a0, 0xd0b6, 0xeb04\n"
        ".hword 0x4000, 0xe1a0, 0x00f8, 0xe1d0\n"
        ".hword 0x10fa, 0xe1d4, 0xa244, 0xe59f\n"
        ".hword 0x0007, 0xe080, 0x0048, 0xe58d\n"
        ".hword 0x9006, 0xe081, 0x5000, 0xe59a\n"
        ".hword 0x2000, 0xe3a0, 0x1001, 0xe3a0\n"
        ".hword 0x0006, 0xe3a0, 0xeadf, 0xeb04\n"
        ".hword 0x5a01, 0xe285, 0x5fab, 0xe285\n"
        ".hword 0x1000, 0xe595, 0x2101, 0xe085\n"
        ".hword 0x1008, 0xe592, 0x0008, 0xe582\n"
        ".hword 0x2018, 0xe5d5, 0x0000, 0xe352\n"
        ".hword 0x0000, 0x0151, 0x0003, 0x0a00\n"
        ".hword 0x101c, 0xe595, 0xff31, 0xe12f\n"
        ".hword 0x0000, 0xe3a0, 0x0018, 0xe5c5\n"
        ".hword 0x0a00, 0xe88d, 0x3048, 0xe59d\n"
        ".hword 0x200c, 0xe3a0, 0x102f, 0xe3a0\n"
        ".hword 0x0002, 0xe3a0, 0xcffa, 0xeb04\n"
        ".hword 0x5000, 0xe59a, 0x2000, 0xe3a0\n"
        ".hword 0x1007, 0xe3a0, 0x0006, 0xe3a0\n"
        ".hword 0xeac6, 0xeb04, 0x5a01, 0xe285\n"
        ".hword 0x5fab, 0xe285, 0x1000, 0xe595\n"
        ".hword 0x2101, 0xe085, 0x1008, 0xe592\n"
        ".hword 0x0008, 0xe582, 0x2018, 0xe5d5\n"
        ".hword 0x0000, 0xe352, 0x0000, 0x0151\n"
        ".hword 0x0003, 0x0a00, 0x101c, 0xe595\n"
        ".hword 0xff31, 0xe12f, 0x0000, 0xe3a0\n"
        ".hword 0x0018, 0xe5c5, 0x0010, 0xe3a0\n"
        ".hword 0x0004, 0xe58d, 0x3048, 0xe59d\n"
        ".hword 0x2001, 0xe3a0, 0x102f, 0xe3a0\n"
        ".hword 0x0002, 0xe3a0, 0x9000, 0xe58d\n"
        ".hword 0xd01d, 0xeb04, 0x9168, 0xe59f\n"
        ".hword 0x5000, 0xe3e0, 0x0009, 0xe1a0\n"
        ".hword 0xd5ad, 0xeb04, 0x0000, 0xe350\n"
        ".hword 0xaea5, 0xe189, 0x0004, 0x0a00\n"
        ".hword 0x000a, 0xe1a0, 0xd5a8, 0xeb04\n"
        ".hword 0x0000, 0xe350, 0x5002, 0x13a0\n"
        ".hword 0x0008, 0x1a00, 0x000a, 0xe1a0\n"
        ".hword 0xd5a3, 0xeb04, 0x0000, 0xe350\n"
        ".hword 0x5001, 0x13a0, 0x0003, 0x1a00\n"
        ".hword 0x0009, 0xe1a0, 0xd59e, 0xeb04\n"
        ".hword 0x0000, 0xe350, 0x5000, 0x13a0\n"
        ".hword 0x1000, 0xe3a0, 0x0036, 0xe3a0\n"
        ".hword 0xd660, 0xeb04, 0xa000, 0xe1a0\n"
        ".hword 0xf000, 0xe320, 0xd653, 0xeb04\n"
        ".hword 0x9000, 0xe1a0, 0x000a, 0xe1a0\n"
        ".hword 0xd63c, 0xeb04, 0x0000, 0xe155\n"
        ".hword 0xf000, 0xe320, 0x002a, 0x2a00\n"
        ".hword 0x5385, 0xe099, 0x0028, 0x0a00\n"
        ".hword 0x101a, 0xe3a0, 0x002f, 0xe3a0\n"
        ".hword 0xd055, 0xeb04, 0x9000, 0xe1a0\n"
        ".hword 0x2005, 0xe1a0, 0x10cc, 0xe28f\n"
        ".hword 0x0008, 0xe28d, 0xcc9b, 0xfa04\n"
        ".hword 0x00fa, 0xe1d4, 0x10f8, 0xe1d4\n"
        ".hword 0x20fa, 0xe1d9, 0x30f8, 0xe1d9\n"
        ".hword 0x1a2e, 0xed9f, 0x0002, 0xe080\n"
        ".hword 0x1003, 0xe081, 0x0006, 0xe080\n"
        ".hword 0x1007, 0xe081, 0x0a90, 0xee00\n"
        ".hword 0x1a10, 0xee00, 0x1a41, 0xeef0\n"
        ".hword 0x104c, 0xe59d, 0x2008, 0xe28d\n"
        ".hword 0x2a23, 0xed9f, 0x0ae0, 0xeef8\n"
        ".hword 0x0ac0, 0xeeb8, 0x0002, 0xe3a0\n"
        ".hword 0xcc68, 0xeb04, 0x00a8, 0xe5d8\n"
        ".hword 0x0001, 0xe350, 0x0008, 0xe1a0\n"
        ".hword 0x000b, 0x0a00, 0x4f1c, 0xeb04\n"
        ".hword 0x0100, 0xe088, 0x3080, 0xe590\n"
        ".hword 0x5000, 0xe58d, 0x10fa, 0xe1d4\n"
        ".hword 0x00f8, 0xe1d4, 0x2006, 0xe081\n"
        ".hword 0x1007, 0xe080, 0x0002, 0xe3a0\n"
        ".hword 0x2e33, 0xeb00, 0xd054, 0xe28d\n"
        ".hword 0x8ff0, 0xe8bd, 0xf000, 0xe320\n"
        ".hword 0x4f0f, 0xeb04, 0x0100, 0xe088\n"
        ".hword 0x3080, 0xe590, 0x5000, 0xe58d\n"
        ".hword 0x10fa, 0xe1d4, 0x00f8, 0xe1d4\n"
        ".hword 0x2006, 0xe081, 0x1007, 0xe080\n"
        ".hword 0x0003, 0xe3a0, 0xfff1, 0xeaff\n"
        ".hword 0xdc58, 0x0043, 0x00ff, 0xe098\n"
        ".hword 0xea00, 0x0044, 0x0555, 0x0000\n"
        ".hword 0x7325, 0x0000, 0x0000, 0x3f80\n"
        ".hword 0x0000, 0x0000\n"
    );
};

// DECOMP_FUNC(0x00193b64, 712)
extern "C" __attribute__((naked)) void battle_func_00193b64() {
    asm volatile(
        ".arm\n"
        ".hword 0x4070, 0xe92d, 0x4000, 0xe1a0\n"
        ".hword 0x0c02, 0xe280, 0x5001, 0xe1a0\n"
        ".hword 0x00e1, 0xe280, 0x524f, 0xeb04\n"
        ".hword 0x0000, 0xe3a0, 0x02ec, 0xe584\n"
        ".hword 0x02f0, 0xe584, 0x02f4, 0xe584\n"
        ".hword 0x02f8, 0xe584, 0x02fc, 0xe584\n"
        ".hword 0x0300, 0xe584, 0x0304, 0xe584\n"
        ".hword 0x0308, 0xe584, 0x030c, 0xe584\n"
        ".hword 0x0310, 0xe584, 0x0314, 0xe584\n"
        ".hword 0x0318, 0xe584, 0x031c, 0xe584\n"
        ".hword 0x0320, 0xe584, 0x0324, 0xe584\n"
        ".hword 0x0328, 0xe584, 0x032c, 0xe584\n"
        ".hword 0x0330, 0xe584, 0x0334, 0xe584\n"
        ".hword 0x0338, 0xe584, 0x0034, 0xe5d5\n"
        ".hword 0x0a93, 0xed9f, 0x1005, 0xe1a0\n"
        ".hword 0x0a90, 0xee00, 0x0a60, 0xeef8\n"
        ".hword 0x0a79, 0xedc4, 0x0035, 0xe5d5\n"
        ".hword 0x0a90, 0xee00, 0x0a60, 0xeef8\n"
        ".hword 0x0a7a, 0xedc4, 0x0036, 0xe5d5\n"
        ".hword 0x0a90, 0xee00, 0x0a60, 0xeef8\n"
        ".hword 0x0a7b, 0xedc4, 0x0037, 0xe5d5\n"
        ".hword 0x0a90, 0xee00, 0x0a60, 0xeef8\n"
        ".hword 0x0a7c, 0xedc4, 0x0038, 0xe595\n"
        ".hword 0x01f4, 0xe584, 0x0040, 0xe595\n"
        ".hword 0x01f8, 0xe584, 0x0044, 0xe595\n"
        ".hword 0x01fc, 0xe584, 0x03fc, 0xe1d5\n"
        ".hword 0x0a90, 0xee00, 0x0ae0, 0xeef8\n"
        ".hword 0x0a80, 0xedc4, 0x04f8, 0xe1d5\n"
        ".hword 0x0a90, 0xee00, 0x0ae0, 0xeef8\n"
        ".hword 0x0a81, 0xedc4, 0x04fa, 0xe1d5\n"
        ".hword 0x0a90, 0xee00, 0x0ae0, 0xeef8\n"
        ".hword 0x0a82, 0xedc4, 0x04fc, 0xe1d5\n"
        ".hword 0x0a90, 0xee00, 0x0004, 0xe1a0\n"
        ".hword 0x0ae0, 0xeef8, 0x0a83, 0xedc4\n"
        ".hword 0x0a84, 0xed84, 0x0a85, 0xed84\n"
        ".hword 0x0a86, 0xed84, 0x0a87, 0xed84\n"
        ".hword 0x0a88, 0xed84, 0x0a89, 0xed84\n"
        ".hword 0x0a8a, 0xed84, 0x0a8b, 0xed84\n"
        ".hword 0x0a8c, 0xed84, 0x0a8d, 0xed84\n"
        ".hword 0x0a8e, 0xed84, 0xda17, 0xeb00\n"
        ".hword 0x1050, 0xe594, 0x0000, 0xe351\n"
        ".hword 0x0041, 0x0a00, 0x03bc, 0xe1d4\n"
        ".hword 0x0000, 0xe350, 0x000b, 0x0a00\n"
        ".hword 0x2001, 0xe3a0, 0x0002, 0xe3a0\n"
        ".hword 0xf6fe, 0xeb03, 0x0ac0, 0xeebd\n"
        ".hword 0x13bc, 0xe1d4, 0x0a10, 0xee10\n"
        ".hword 0x0000, 0xe041, 0x0070, 0xe6bf\n"
        ".hword 0x0a10, 0xee00, 0x03bc, 0xe1c4\n"
        ".hword 0x0ac0, 0xeeb8, 0x0a80, 0xed84\n"
        ".hword 0x04b8, 0xe1d4, 0x0000, 0xe350\n"
        ".hword 0x000d, 0x0a00, 0x1050, 0xe594\n"
        ".hword 0x2001, 0xe3a0, 0x0002, 0xe3a0\n"
        ".hword 0xf6ee, 0xeb03, 0x0ac0, 0xeebd\n"
        ".hword 0x14b8, 0xe1d4, 0x0a10, 0xee10\n"
        ".hword 0x0000, 0xe041, 0x0070, 0xe6bf\n"
        ".hword 0x0a10, 0xee00, 0x04b8, 0xe1c4\n"
        ".hword 0x0004, 0xe584, 0x0ac0, 0xeeb8\n"
        ".hword 0x0a81, 0xed84, 0x04ba, 0xe1d4\n"
        ".hword 0x0000, 0xe350, 0x000d, 0x0a00\n"
        ".hword 0x1050, 0xe594, 0x2001, 0xe3a0\n"
        ".hword 0x0002, 0xe3a0, 0xf6dd, 0xeb03\n"
        ".hword 0x0ac0, 0xeebd, 0x14ba, 0xe1d4\n"
        ".hword 0x0a10, 0xee10, 0x0000, 0xe041\n"
        ".hword 0x0070, 0xe6bf, 0x0a10, 0xee00\n"
        ".hword 0x04ba, 0xe1c4, 0x0008, 0xe584\n"
        ".hword 0x0ac0, 0xeeb8, 0x0a82, 0xed84\n"
        ".hword 0x04bc, 0xe1d4, 0x0000, 0xe350\n"
        ".hword 0x000d, 0x0a00, 0x1050, 0xe594\n"
        ".hword 0x2001, 0xe3a0, 0x0002, 0xe3a0\n"
        ".hword 0xf6cc, 0xeb03, 0x0ac0, 0xeebd\n"
        ".hword 0x14bc, 0xe1d4, 0x0a10, 0xee10\n"
        ".hword 0x0000, 0xe041, 0x0070, 0xe6bf\n"
        ".hword 0x0a10, 0xee00, 0x04bc, 0xe1c4\n"
        ".hword 0x000c, 0xe584, 0x0ac0, 0xeeb8\n"
        ".hword 0x0a83, 0xed84, 0x1005, 0xe1a0\n"
        ".hword 0x0004, 0xe1a0, 0x6504, 0xeb00\n"
        ".hword 0x1005, 0xe1a0, 0x0004, 0xe1a0\n"
        ".hword 0x26a6, 0xeb01, 0x1005, 0xe1a0\n"
        ".hword 0x0004, 0xe1a0, 0x26d6, 0xeb01\n"
        ".hword 0x1005, 0xe1a0, 0x0004, 0xe1a0\n"
        ".hword 0x68ca, 0xeb01, 0x1005, 0xe1a0\n"
        ".hword 0x0004, 0xe1a0, 0x693e, 0xeb01\n"
        ".hword 0x1005, 0xe1a0, 0x0004, 0xe1a0\n"
        ".hword 0x68f3, 0xeb01, 0x1005, 0xe1a0\n"
        ".hword 0x0004, 0xe1a0, 0xbc52, 0xeb01\n"
        ".hword 0x1005, 0xe1a0, 0x0004, 0xe1a0\n"
        ".hword 0xbc97, 0xeb01, 0x1005, 0xe1a0\n"
        ".hword 0x0004, 0xe1a0, 0x4070, 0xe8bd\n"
        ".hword 0xbcdb, 0xea01, 0x0000, 0x0000\n"
    );
};

// DECOMP_FUNC(0x003e4ebc, 712)
extern "C" __attribute__((naked)) void func_003e4ebc() {
    asm volatile(
        ".arm\n"
        ".hword 0x47f0, 0xe92d, 0x4001, 0xe1a0\n"
        ".hword 0x8000, 0xe1a0, 0xa000, 0xe3a0\n"
        ".hword 0x5003, 0xe1a0, 0x8b02, 0xed2d\n"
        ".hword 0xd008, 0xe24d, 0x7000, 0xe592\n"
        ".hword 0x9030, 0xe59d, 0xa000, 0xe58d\n"
        ".hword 0x8a40, 0xeef0, 0x0000, 0xe359\n"
        ".hword 0x003c, 0x0594, 0x8aa2, 0xed9f\n"
        ".hword 0x6002, 0xe1a0, 0x0000, 0x058d\n"
        ".hword 0x0010, 0xe317, 0x0011, 0x1a00\n"
        ".hword 0x0000, 0xe59d, 0x0080, 0xe3c0\n"
        ".hword 0x0000, 0xe58d, 0x0000, 0xe596\n"
        ".hword 0x100c, 0xe592, 0x0002, 0xe310\n"
        ".hword 0x0a48, 0x1eb0, 0x0a68, 0x0eb0\n"
        ".hword 0x0000, 0xe351, 0x000c, 0xe282\n"
        ".hword 0x2000, 0x1081, 0x200a, 0x01a0\n"
        ".hword 0x100d, 0xe1a0, 0x0004, 0xe1a0\n"
        ".hword 0x6f7e, 0xebfe, 0x003c, 0xe594\n"
        ".hword 0x0b02, 0xe380, 0x003c, 0xe584\n"
        ".hword 0x0008, 0xe317, 0x0011, 0x1a00\n"
        ".hword 0x0000, 0xe59d, 0x0c01, 0xe3c0\n"
        ".hword 0x0000, 0xe58d, 0x0000, 0xe596\n"
        ".hword 0x1010, 0xe596, 0x0001, 0xe310\n"
        ".hword 0x0a48, 0x1eb0, 0x0a68, 0x0eb0\n"
        ".hword 0x0000, 0xe351, 0x0010, 0xe286\n"
        ".hword 0x2000, 0x1081, 0x200a, 0x01a0\n"
        ".hword 0x100d, 0xe1a0, 0x0004, 0xe1a0\n"
        ".hword 0x703c, 0xebfe, 0x003c, 0xe594\n"
        ".hword 0x0b02, 0xe380, 0x003c, 0xe584\n"
        ".hword 0x0020, 0xe317, 0x005f, 0x0a00\n"
        ".hword 0x0000, 0xe359, 0x0042, 0x0a00\n"
        ".hword 0x0010, 0xe317, 0x0011, 0x0a00\n"
        ".hword 0x100c, 0xe285, 0x0004, 0xe1a0\n"
        ".hword 0x0a03, 0xec91, 0x9c81, 0xebf9\n"
        ".hword 0x0a03, 0xed95, 0x0a48, 0xeeb4\n"
        ".hword 0xfa10, 0xeef1, 0x0009, 0x1a00\n"
        ".hword 0x0a04, 0xed95, 0x0a48, 0xeeb4\n"
        ".hword 0xfa10, 0xeef1, 0x0a05, 0x0d95\n"
        ".hword 0x0a48, 0x0eb4, 0xfa10, 0x0ef1\n"
        ".hword 0x0002, 0x1a00, 0x0000, 0xe59d\n"
        ".hword 0x0080, 0xe380, 0x0000, 0xe58d\n"
        ".hword 0x0008, 0xe317, 0x0015, 0x0a00\n"
        ".hword 0x0018, 0xe285, 0x0007, 0xe890\n"
        ".hword 0x000c, 0xe584, 0x101c, 0xe584\n"
        ".hword 0x202c, 0xe584, 0x003c, 0xe594\n"
        ".hword 0x0b02, 0xe380, 0x003c, 0xe584\n"
        ".hword 0x0a06, 0xed95, 0x0a48, 0xeeb4\n"
        ".hword 0xfa10, 0xeef1, 0x0009, 0x1a00\n"
        ".hword 0x0a07, 0xed95, 0x0a48, 0xeeb4\n"
        ".hword 0xfa10, 0xeef1, 0x0a08, 0x0d95\n"
        ".hword 0x0a48, 0x0eb4, 0xfa10, 0x0ef1\n"
        ".hword 0x0002, 0x1a00, 0x0000, 0xe59d\n"
        ".hword 0x0c01, 0xe380, 0x0000, 0xe58d\n"
        ".hword 0x0020, 0xe317, 0x0014, 0x0a00\n"
        ".hword 0x0007, 0xe895, 0x3030, 0xe284\n"
        ".hword 0x0007, 0xe883, 0x003c, 0xe594\n"
        ".hword 0x0b02, 0xe380, 0x003c, 0xe584\n"
        ".hword 0x0a02, 0xec95, 0x0a60, 0xeeb4\n"
        ".hword 0xfa10, 0xeef1, 0x000a, 0x1a00\n"
        ".hword 0x0a02, 0xedd5, 0x0a60, 0xeeb4\n"
        ".hword 0xfa10, 0xeef1, 0x0006, 0x1a00\n"
        ".hword 0x0000, 0xe59d, 0x0b01, 0xe380\n"
        ".hword 0x0000, 0xe58d, 0x1000, 0xe595\n"
        ".hword 0x05fe, 0xe351, 0x0c02, 0x0380\n"
        ".hword 0x0000, 0x058d, 0x103c, 0xe594\n"
        ".hword 0x2000, 0xe59d, 0x0004, 0xe1a0\n"
        ".hword 0x1101, 0xe3c1, 0x103c, 0xe584\n"
        ".hword 0x305b, 0xe5d8, 0x0000, 0xe353\n"
        ".hword 0x1008, 0x1381, 0x1008, 0x03c1\n"
        ".hword 0x103c, 0xe580, 0x105c, 0xe5d8\n"
        ".hword 0x0000, 0xe351, 0x103c, 0xe590\n"
        ".hword 0x1010, 0x1381, 0x1010, 0x03c1\n"
        ".hword 0x103c, 0xe580, 0x105d, 0xe5d8\n"
        ".hword 0x0000, 0xe351, 0x103c, 0xe590\n"
        ".hword 0x1004, 0x1381, 0x1004, 0x03c1\n"
        ".hword 0x103c, 0xe580, 0x1002, 0xe1a0\n"
        ".hword 0x702c, 0xebfe, 0xd008, 0xe28d\n"
        ".hword 0x8b02, 0xecbd, 0x87f0, 0xe8bd\n"
        ".hword 0x0000, 0xe59d, 0x0a68, 0xeeb0\n"
        ".hword 0x100d, 0xe1a0, 0x0c06, 0xe3c0\n"
        ".hword 0x0000, 0xe58d, 0x2000, 0xe596\n"
        ".hword 0x0030, 0xe284, 0x0004, 0xe312\n"
        ".hword 0x2014, 0xe5b6, 0x0004, 0x0a00\n"
        ".hword 0x0000, 0xe352, 0x0a48, 0xeeb0\n"
        ".hword 0xa006, 0x1082, 0x200a, 0xe1a0\n"
        ".hword 0x0002, 0xea00, 0x0000, 0xe352\n"
        ".hword 0xa006, 0x1082, 0x200a, 0xe1a0\n"
        ".hword 0x6f68, 0xebfe, 0x003c, 0xe594\n"
        ".hword 0x0b02, 0xe380, 0x003c, 0xe584\n"
        ".hword 0xff88, 0xeaff, 0x0000, 0x0000\n"
    );
};

// DECOMP_FUNC(0x0015a7c0, 720)
extern "C" __attribute__((naked)) void ui_func_0015a7c0() {
    asm volatile(
        ".arm\n"
        ".hword 0x47f0, 0xe92d, 0x4002, 0xe1a0\n"
        ".hword 0x7000, 0xe1a0, 0x8b02, 0xed2d\n"
        ".hword 0xd048, 0xe24d, 0x0008, 0xe590\n"
        ".hword 0x0008, 0xe590, 0x2068, 0xe590\n"
        ".hword 0x0001, 0xe152, 0x0085, 0xda00\n"
        ".hword 0x20a4, 0xe597, 0x006c, 0xe590\n"
        ".hword 0x9280, 0xe59f, 0x8f52, 0xe282\n"
        ".hword 0x2101, 0xe041, 0x6008, 0xe594\n"
        ".hword 0x5082, 0xe080, 0x0000, 0xe599\n"
        ".hword 0xa264, 0xe59f, 0x214e, 0xe285\n"
        ".hword 0x8a95, 0xed9f, 0x8a95, 0xeddf\n"
        ".hword 0x10bc, 0xe286, 0x0404, 0xe8a0\n"
        ".hword 0x1c78, 0xeb05, 0x0000, 0xe599\n"
        ".hword 0x2152, 0xe285, 0x10cc, 0xe286\n"
        ".hword 0x0018, 0xe280, 0x0000, 0xe589\n"
        ".hword 0x0404, 0xe8a0, 0x1c71, 0xeb05\n"
        ".hword 0x0000, 0xe599, 0x0018, 0xe280\n"
        ".hword 0x0000, 0xe589, 0x00b8, 0xe596\n"
        ".hword 0x0000, 0xe350, 0x0022, 0x0a00\n"
        ".hword 0x0a26, 0xed94, 0x0a2a, 0xedd4\n"
        ".hword 0x1a2e, 0xed94, 0x8a11, 0xedcd\n"
        ".hword 0xc038, 0xe28d, 0x3038, 0xe28d\n"
        ".hword 0x2008, 0xe1a0, 0x1003, 0xe1a0\n"
        ".hword 0x0007, 0xe1a0, 0x0a03, 0xec8c\n"
        ".hword 0x1c41, 0xeb05, 0x0000, 0xe599\n"
        ".hword 0x2156, 0xe285, 0x1038, 0xe28d\n"
        ".hword 0x0404, 0xe8a0, 0x1c5b, 0xeb05\n"
        ".hword 0x0000, 0xe599, 0x215e, 0xe285\n"
        ".hword 0x10e8, 0xe286, 0x0018, 0xe280\n"
        ".hword 0x0000, 0xe589, 0x0404, 0xe8a0\n"
        ".hword 0x1c54, 0xeb05, 0x0000, 0xe599\n"
        ".hword 0x0018, 0xe280, 0x0000, 0xe589\n"
        ".hword 0x00b8, 0xe596, 0x0002, 0xe350\n"
        ".hword 0x001e, 0x0a00, 0x01a8, 0xe59f\n"
        ".hword 0x4003, 0xe245, 0x0000, 0xe590\n"
        ".hword 0x0001, 0xe310, 0x0051, 0x0a00\n"
        ".hword 0x005c, 0xea00, 0x017c, 0xe594\n"
        ".hword 0x300d, 0xe1a0, 0x2008, 0xe1a0\n"
        ".hword 0x0000, 0xe58d, 0x0180, 0xe594\n"
        ".hword 0x1003, 0xe1a0, 0x0004, 0xe58d\n"
        ".hword 0x0184, 0xe594, 0x0008, 0xe58d\n"
        ".hword 0x8a03, 0xed8d, 0x0007, 0xe1a0\n"
        ".hword 0x1c1d, 0xeb05, 0x1004, 0xe28d\n"
        ".hword 0x1a00, 0xeddd, 0x201c, 0xe28d\n"
        ".hword 0x0a03, 0xec91, 0x1a61, 0xeef1\n"
        ".hword 0x1018, 0xe28d, 0x0015, 0xe285\n"
        ".hword 0x0a40, 0xeeb1, 0x1a41, 0xeeb1\n"
        ".hword 0x0a60, 0xeef1, 0x1a06, 0xedcd\n"
        ".hword 0x0a03, 0xec82, 0x0045, 0xea00\n"
        ".hword 0x017c, 0xe594, 0x3028, 0xe28d\n"
        ".hword 0x2008, 0xe1a0, 0x0028, 0xe58d\n"
        ".hword 0x0180, 0xe594, 0x1003, 0xe1a0\n"
        ".hword 0x002c, 0xe58d, 0x0184, 0xe594\n"
        ".hword 0x0030, 0xe58d, 0x8a0d, 0xed8d\n"
        ".hword 0x0007, 0xe1a0, 0x1c04, 0xeb05\n"
        ".hword 0x10f8, 0xe596, 0x20fc, 0xe596\n"
        ".hword 0x3018, 0xe28d, 0x0006, 0xe883\n"
        ".hword 0x8a08, 0xed8d, 0x8a09, 0xed8d\n"
        ".hword 0x0a3f, 0xed96, 0x0ac8, 0xeeb4\n"
        ".hword 0xfa10, 0xeef1, 0x001a, 0xda00\n"
        ".hword 0x10d8, 0xe59f, 0x0a10, 0xee10\n"
        ".hword 0x0000, 0xe151, 0x0016, 0xda00\n"
        ".hword 0x0a33, 0xeddf, 0x0a20, 0xee20\n"
        ".hword 0x7279, 0xeb05, 0x0a07, 0xed8d\n"
        ".hword 0x8a0d, 0xedcd, 0x0000, 0xe599\n"
        ".hword 0x215a, 0xe285, 0x1028, 0xe28d\n"
        ".hword 0x0404, 0xe8a0, 0x1c0b, 0xeb05\n"
        ".hword 0x0000, 0xe599, 0x1018, 0xe28d\n"
        ".hword 0x2162, 0xe285, 0x0018, 0xe280\n"
        ".hword 0x0000, 0xe589, 0x0404, 0xe8a0\n"
        ".hword 0x1c04, 0xeb05, 0x0000, 0xe599\n"
        ".hword 0x0018, 0xe280, 0x0000, 0xe589\n"
        ".hword 0xd048, 0xe28d, 0x8b02, 0xecbd\n"
        ".hword 0x87f0, 0xe8bd, 0x0a48, 0xeeb4\n"
        ".hword 0xfa10, 0xeef1, 0x0a1b, 0x0d9f\n"
        ".hword 0x0a07, 0x0d8d, 0x8a0d, 0x0dcd\n"
        ".hword 0x8a0d, 0x1d8d, 0xffe6, 0xeaff\n"
        ".hword 0x004c, 0xe59f, 0x95a8, 0xfa05\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0006, 0x0a00, 0x0048, 0xe59f\n"
        ".hword 0x8a00, 0xed80, 0x8a01, 0xed80\n"
        ".hword 0x8a02, 0xed80, 0x8a03, 0xed80\n"
        ".hword 0x0024, 0xe59f, 0x0000, 0xe1a0\n"
        ".hword 0x102c, 0xe59f, 0x0019, 0xe284\n"
        ".hword 0x2102, 0xe280, 0x0000, 0xe599\n"
        ".hword 0xffdf, 0xeaff, 0x0000, 0x0000\n"
        ".hword 0x0000, 0x3f80, 0x02c0, 0x804f\n"
        ".hword 0x52a0, 0x0046, 0x662c, 0x0047\n"
        ".hword 0x0fdb, 0x4049, 0xf983, 0x4222\n"
        ".hword 0x0054, 0x3f80, 0xfd38, 0x004e\n"
    );
};

// DECOMP_FUNC(0x00349c64, 720)
extern "C" __attribute__((naked)) void engine_func_00349c64() {
    asm volatile(
        ".arm\n"
        ".hword 0x0001, 0xe3a0, 0xff1e, 0xe12f\n"
        ".hword 0x0000, 0xe1a0, 0x4ff0, 0xe92d\n"
        ".hword 0xd074, 0xe24d, 0x6000, 0xe3a0\n"
        ".hword 0x2001, 0xe3a0, 0x4000, 0xe1a0\n"
        ".hword 0x00ff, 0xe3a0, 0x606c, 0xe58d\n"
        ".hword 0x6068, 0xe5cd, 0x6060, 0xe5cd\n"
        ".hword 0x6008, 0xe5cd, 0x2069, 0xe5cd\n"
        ".hword 0x2061, 0xe5cd, 0x2009, 0xe5cd\n"
        ".hword 0x726c, 0xe59f, 0x006a, 0xe5cd\n"
        ".hword 0x0062, 0xe5cd, 0x000a, 0xe5cd\n"
        ".hword 0xb001, 0xe1a0, 0x006b, 0xe5cd\n"
        ".hword 0x0063, 0xe5cd, 0x000b, 0xe5cd\n"
        ".hword 0x1068, 0xe28d, 0x2f8f, 0xe28f\n"
        ".hword 0x0008, 0xe287, 0x6064, 0xe58d\n"
        ".hword 0x600c, 0xe58d, 0xde3e, 0xebfd\n"
        ".hword 0x1060, 0xe28d, 0x2f8d, 0xe28f\n"
        ".hword 0x0008, 0xe287, 0xde3a, 0xebfd\n"
        ".hword 0x1008, 0xe28d, 0x2f8b, 0xe28f\n"
        ".hword 0x0008, 0xe287, 0xde36, 0xebfd\n"
        ".hword 0x1000, 0xe3a0, 0x2020, 0xe28d\n"
        ".hword 0x0001, 0xe1a0, 0x6020, 0xe5cd\n"
        ".hword 0x6024, 0xe58d, 0x6028, 0xe58d\n"
        ".hword 0x602c, 0xe58d, 0x3101, 0xe082\n"
        ".hword 0x1001, 0xe281, 0x0002, 0xe280\n"
        ".hword 0xc101, 0xe082, 0x6010, 0xe583\n"
        ".hword 0x000c, 0xe350, 0x1001, 0xe281\n"
        ".hword 0x6010, 0xe58c, 0xfff6, 0x3aff\n"
        ".hword 0x1007, 0xe3a0, 0x1024, 0xe5cd\n"
        ".hword 0x000f, 0xe3a0, 0x3003, 0xe3a0\n"
        ".hword 0x0025, 0xe5cd, 0x0068, 0xe28d\n"
        ".hword 0x3020, 0xe5cd, 0x0038, 0xe58d\n"
        ".hword 0x200b, 0xe3a0, 0x3008, 0xe28d\n"
        ".hword 0x1060, 0xe28d, 0x000b, 0xe1a0\n"
        ".hword 0x3030, 0xe58d, 0x1034, 0xe58d\n"
        ".hword 0x2026, 0xe5cd, 0x53d4, 0xeb02\n"
        ".hword 0x0010, 0xe584, 0x0100, 0xe1a0\n"
        ".hword 0x1005, 0xe1a0, 0x634c, 0xebfc\n"
        ".hword 0x0008, 0xe584, 0x0010, 0xe594\n"
        ".hword 0x1005, 0xe1a0, 0x0100, 0xe1a0\n"
        ".hword 0x6347, 0xebfc, 0x0004, 0xe584\n"
        ".hword 0x0010, 0xe594, 0x1005, 0xe1a0\n"
        ".hword 0x0100, 0xe1a0, 0x6342, 0xebfc\n"
        ".hword 0x000c, 0xe584, 0x0010, 0xe594\n"
        ".hword 0x0000, 0xe350, 0x0000, 0xe3a0\n"
        ".hword 0x0009, 0xda00, 0x1008, 0xe594\n"
        ".hword 0x6100, 0xe781, 0x1004, 0xe594\n"
        ".hword 0x6100, 0xe781, 0x100c, 0xe594\n"
        ".hword 0x6100, 0xe781, 0x1010, 0xe594\n"
        ".hword 0x0001, 0xe280, 0x0000, 0xe151\n"
        ".hword 0xfff5, 0xcaff, 0x0010, 0xe594\n"
        ".hword 0x5000, 0xe3a0, 0x0000, 0xe350\n"
        ".hword 0x0040, 0xda00, 0xa128, 0xe59f\n"
        ".hword 0x7005, 0xe3a0, 0x8004, 0xe3a0\n"
        ".hword 0x9006, 0xe3a0, 0x2005, 0xe3a0\n"
        ".hword 0x1005, 0xe1a0, 0x000b, 0xe1a0\n"
        ".hword 0xc4d6, 0xebfb, 0x6000, 0xe1b0\n"
        ".hword 0xf000, 0xe320, 0x000b, 0x0a00\n"
        ".hword 0x000a, 0xe1a0, 0xe170, 0xebfd\n"
        ".hword 0x0000, 0xe350, 0x1006, 0x11a0\n"
        ".hword 0xc47e, 0x1bfb, 0x1008, 0xe594\n"
        ".hword 0x3005, 0xe1a0, 0x200b, 0xe1a0\n"
        ".hword 0x0105, 0xe781, 0x1020, 0xe28d\n"
        ".hword 0x7000, 0xe58d, 0x350f, 0xeb00\n"
        ".hword 0x2004, 0xe3a0, 0x1005, 0xe1a0\n"
        ".hword 0x000b, 0xe1a0, 0xc4c3, 0xebfb\n"
        ".hword 0x6000, 0xe1b0, 0xf000, 0xe320\n"
        ".hword 0x000b, 0x0a00, 0x000a, 0xe1a0\n"
        ".hword 0xe15d, 0xebfd, 0x0000, 0xe350\n"
        ".hword 0x1006, 0x11a0, 0xc46b, 0x1bfb\n"
        ".hword 0x1004, 0xe594, 0x3005, 0xe1a0\n"
        ".hword 0x200b, 0xe1a0, 0x0105, 0xe781\n"
        ".hword 0x1020, 0xe28d, 0x8000, 0xe58d\n"
        ".hword 0x34fc, 0xeb00, 0x2006, 0xe3a0\n"
        ".hword 0x1005, 0xe1a0, 0x000b, 0xe1a0\n"
        ".hword 0xc4b0, 0xebfb, 0x6000, 0xe1b0\n"
        ".hword 0xf000, 0xe320, 0x000b, 0x0a00\n"
        ".hword 0x000a, 0xe1a0, 0xe14a, 0xebfd\n"
        ".hword 0x0000, 0xe350, 0x1006, 0x11a0\n"
        ".hword 0xc458, 0x1bfb, 0x100c, 0xe594\n"
        ".hword 0x3005, 0xe1a0, 0x200b, 0xe1a0\n"
        ".hword 0x0105, 0xe781, 0x1020, 0xe28d\n"
        ".hword 0x9000, 0xe58d, 0x34e9, 0xeb00\n"
        ".hword 0x0010, 0xe594, 0x5001, 0xe285\n"
        ".hword 0x0005, 0xe150, 0xffc2, 0xcaff\n"
        ".hword 0xd074, 0xe28d, 0x8ff0, 0xe8bd\n"
        ".hword 0x6f50, 0x6973, 0x6974, 0x6e6f\n"
        ".hword 0x0000, 0x0000, 0xe54c, 0x0047\n"
        ".hword 0x6f43, 0x6f6c, 0x0072, 0x0000\n"
        ".hword 0x5461, 0x7865, 0x6f43, 0x726f\n"
        ".hword 0x0064, 0x0000, 0x07ac, 0x0000\n"
    );
};

// DECOMP_FUNC(0x00107208, 724)
extern "C" __attribute__((naked)) void engine_func_00107208() {
    asm volatile(
        ".arm\n"
        ".hword 0x4ff0, 0xe92d, 0xd00c, 0xe24d\n"
        ".hword 0xe71b, 0xeb06, 0x7000, 0xe1a0\n"
        ".hword 0xe705, 0xeb06, 0x0000, 0xe350\n"
        ".hword 0x5000, 0xe3a0, 0x0004, 0xe58d\n"
        ".hword 0x0027, 0xda00, 0x0105, 0xe085\n"
        ".hword 0x0285, 0xe080, 0x1100, 0xe087\n"
        ".hword 0x0100, 0xe7d7, 0xb001, 0xe5d1\n"
        ".hword 0x60b2, 0xe1d1, 0x0000, 0xe35b\n"
        ".hword 0x0005, 0x0a00, 0x0006, 0xe356\n"
        ".hword 0x6000, 0x03a0, 0x0004, 0x0a00\n"
        ".hword 0x0007, 0xe356, 0x6001, 0x03a0\n"
        ".hword 0x0001, 0xea00, 0x0007, 0xe356\n"
        ".hword 0x6006, 0x03a0, 0x0000, 0xe58d\n"
        ".hword 0xe679, 0xeb06, 0x8000, 0xe1a0\n"
        ".hword 0x1000, 0xe59d, 0x2006, 0xe1a0\n"
        ".hword 0x000b, 0xe1a0, 0xe65e, 0xeb06\n"
        ".hword 0x0000, 0xe358, 0x4000, 0xe1a0\n"
        ".hword 0x0000, 0x03a0, 0x0002, 0x05c4\n"
        ".hword 0x0003, 0xe5d4, 0x101f, 0xe200\n"
        ".hword 0x0001, 0xe351, 0x000a, 0x9a00\n"
        ".hword 0x1001, 0xe240, 0x001f, 0xe3c0\n"
        ".hword 0x101f, 0xe201, 0x0001, 0xe180\n"
        ".hword 0x0003, 0xe5c4, 0x0004, 0xe59d\n"
        ".hword 0x5001, 0xe285, 0x0000, 0xe155\n"
        ".hword 0xffd7, 0xbaff, 0xd00c, 0xe28d\n"
        ".hword 0x8ff0, 0xe8bd, 0x001f, 0xe3c0\n"
        ".hword 0x0003, 0xe5c4, 0x1000, 0xe59d\n"
        ".hword 0x2006, 0xe1a0, 0x000b, 0xe1a0\n"
        ".hword 0x299e, 0xeb00, 0x1088, 0xe088\n"
        ".hword 0x90b0, 0xe1d4, 0x1081, 0xe080\n"
        ".hword 0xa004, 0xe281, 0x10b6, 0xe1d1\n"
        ".hword 0x0000, 0xe351, 0x9000, 0x03a0\n"
        ".hword 0x0036, 0x0a00, 0x0ffa, 0xe351\n"
        ".hword 0x0008, 0x2a00, 0x0063, 0xe3a0\n"
        ".hword 0xe62b, 0xeb06, 0x10b2, 0xe1da\n"
        ".hword 0x0000, 0xe151, 0x002f, 0x9a00\n"
        ".hword 0x00b0, 0xe1da, 0x0000, 0xe350\n"
        ".hword 0x9000, 0x11a0, 0x002b, 0xea00\n"
        ".hword 0x3190, 0xe59f, 0x2002, 0xe5d4\n"
        ".hword 0x0391, 0xe003, 0x1001, 0xe3a0\n"
        ".hword 0x3c41, 0xe283, 0x3089, 0xe283\n"
        ".hword 0x3c23, 0xe1a0, 0xc001, 0xe243\n"
        ".hword 0x1c11, 0xe1a0, 0x0002, 0xe111\n"
        ".hword 0x1008, 0xe58d, 0x001f, 0x1a00\n"
        ".hword 0x1001, 0xe288, 0x0000, 0xe351\n"
        ".hword 0x6000, 0xe3a0, 0x0011, 0xda00\n"
        ".hword 0xe07c, 0xe3e0, 0x8001, 0xe283\n"
        ".hword 0x0e93, 0xe00e, 0x2001, 0xe1a0\n"
        ".hword 0x1088, 0xe088, 0xc083, 0xe083\n"
        ".hword 0x0006, 0xe280, 0x8388, 0xe061\n"
        ".hword 0xc383, 0xe06c, 0x30b0, 0xe1d0\n"
        ".hword 0x018c, 0xe153, 0x0002, 0xda00\n"
        ".hword 0x0188, 0xe153, 0x618e, 0xb086\n"
        ".hword 0x6003, 0xb086, 0x2001, 0xe252\n"
        ".hword 0x0006, 0xe280, 0xfff6, 0x1aff\n"
        ".hword 0x0063, 0xe3a0, 0xe600, 0xeb06\n"
        ".hword 0x0006, 0xe150, 0xf000, 0xe320\n"
        ".hword 0x0004, 0x2a00, 0x1002, 0xe5d4\n"
        ".hword 0x0008, 0xe59d, 0x90b0, 0xe1da\n"
        ".hword 0x0001, 0xe180, 0x0002, 0xe5c4\n"
        ".hword 0x00e4, 0xe59f, 0xe5ed, 0xeb06\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0010, 0x0a00, 0x00d4, 0xe59f\n"
        ".hword 0xe5e8, 0xeb06, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x000b, 0x1a00\n"
        ".hword 0x0000, 0xe35b, 0x0002, 0x0a00\n"
        ".hword 0x0001, 0xe35b, 0x0004, 0x0a00\n"
        ".hword 0x0006, 0xea00, 0x0000, 0xe59d\n"
        ".hword 0x0008, 0xe350, 0x0009, 0x0a00\n"
        ".hword 0x0002, 0xea00, 0x0000, 0xe59d\n"
        ".hword 0x0009, 0xe350, 0x0005, 0x0a00\n"
        ".hword 0x00b0, 0xe1d4, 0x0000, 0xe350\n"
        ".hword 0x0009, 0x0a00, 0x0000, 0xe359\n"
        ".hword 0x0009, 0x0a00, 0xff98, 0xeaff\n"
        ".hword 0x1003, 0xe5d4, 0x0000, 0xe3a0\n"
        ".hword 0x00b0, 0xe1c4, 0x103f, 0xe3c1\n"
        ".hword 0x0002, 0xe5c4, 0x1003, 0xe5c4\n"
        ".hword 0xff91, 0xeaff, 0x0000, 0xe359\n"
        ".hword 0xff8f, 0x0aff, 0x90b0, 0xe1c4\n"
        ".hword 0x00b4, 0xe1da, 0x1003, 0xe5d4\n"
        ".hword 0x0000, 0xe35b, 0x001f, 0xe200\n"
        ".hword 0x101f, 0xe3c1, 0x0001, 0xe180\n"
        ".hword 0x0003, 0xe5c4, 0x0000, 0xe59d\n"
        ".hword 0x0005, 0x0a00, 0x1ff2, 0xeb00\n"
        ".hword 0x0000, 0xe350, 0x0003, 0x15d4\n"
        ".hword 0x0020, 0x1380, 0xff80, 0x0aff\n"
        ".hword 0xff7e, 0xeaff, 0xf000, 0xe320\n"
        ".hword 0x1ffa, 0xeb00, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0xfff5, 0xeaff\n"
        ".hword 0x4189, 0x0000, 0x0668, 0x0000\n"
        ".hword 0x01d7, 0x0000\n"
    );
};

// DECOMP_FUNC(0x002e0dd0, 724)
extern "C" __attribute__((naked)) void engine_func_002e0dd0() {
    asm volatile(
        ".arm\n"
        ".hword 0x41f0, 0xe92d, 0xc000, 0xe1a0\n"
        ".hword 0x6002, 0xe1a0, 0x8074, 0xe59f\n"
        ".hword 0x2001, 0xe1a0, 0x5018, 0xe59d\n"
        ".hword 0x7003, 0xe1a0, 0x0004, 0xe598\n"
        ".hword 0x4005, 0xe3a0, 0x100c, 0xe1a0\n"
        ".hword 0x0018, 0xe590, 0x09cc, 0xebfe\n"
        ".hword 0x0102, 0xe210, 0x0011, 0x4a00\n"
        ".hword 0x0006, 0xe1a0, 0x5386, 0xfaff\n"
        ".hword 0x3080, 0xe1a0, 0x0004, 0xe598\n"
        ".hword 0x2006, 0xe1a0, 0x106e, 0xe3a0\n"
        ".hword 0x0018, 0xe590, 0xa00b, 0xebfd\n"
        ".hword 0x0004, 0xe598, 0x3005, 0xe1a0\n"
        ".hword 0x2007, 0xe1a0, 0x1065, 0xe3a0\n"
        ".hword 0x0018, 0xe590, 0xa005, 0xebfd\n"
        ".hword 0x0004, 0xe598, 0x0018, 0xe590\n"
        ".hword 0x60a3, 0xebfd, 0x4000, 0xe3a0\n"
        ".hword 0x0004, 0xe1a0, 0x81f0, 0xe8bd\n"
        ".hword 0x4fa8, 0x0046, 0xca10, 0xee10\n"
        ".hword 0x1238, 0xe59f, 0x4030, 0xe92d\n"
        ".hword 0x2102, 0xe3dc, 0x2fac, 0x01a0\n"
        ".hword 0xd024, 0xe24d, 0xcb82, 0x01a0\n"
        ".hword 0x0007, 0x0a00, 0x308c, 0xe1a0\n"
        ".hword 0x248c, 0xe1a0, 0xec23, 0xe1a0\n"
        ".hword 0x3fac, 0xe1a0, 0xc10e, 0xe791\n"
        ".hword 0x2822, 0xe1a0, 0x2b83, 0xe182\n"
        ".hword 0xc002, 0xe18c, 0xea90, 0xee10\n"
        ".hword 0x2102, 0xe3de, 0x2fae, 0x01a0\n"
        ".hword 0x2b82, 0x01a0, 0x0007, 0x0a00\n"
        ".hword 0x308e, 0xe1a0, 0x248e, 0xe1a0\n"
        ".hword 0x4c23, 0xe1a0, 0x3fae, 0xe1a0\n"
        ".hword 0xe104, 0xe791, 0x2822, 0xe1a0\n"
        ".hword 0x2b83, 0xe182, 0x200e, 0xe182\n"
        ".hword 0x4a10, 0xee11, 0x3102, 0xe3d4\n"
        ".hword 0x3fa4, 0x01a0, 0x3b83, 0x01a0\n"
        ".hword 0x0007, 0x0a00, 0xe084, 0xe1a0\n"
        ".hword 0x3484, 0xe1a0, 0x5c2e, 0xe1a0\n"
        ".hword 0xefa4, 0xe1a0, 0x4105, 0xe791\n"
        ".hword 0x3823, 0xe1a0, 0x3b8e, 0xe183\n"
        ".hword 0x3004, 0xe183, 0xe1fc, 0xe591\n"
        ".hword 0xcc02, 0xe18c, 0xc000, 0xe58d\n"
        ".hword 0x440e, 0xe1a0, 0xe803, 0xe1a0\n"
        ".hword 0x3823, 0xe184, 0x2422, 0xe18e\n"
        ".hword 0x20f4, 0xe1cd, 0x2a90, 0xee11\n"
        ".hword 0x3102, 0xe3d2, 0x2fa2, 0x01a0\n"
        ".hword 0xcb82, 0x01a0, 0x0007, 0x0a00\n"
        ".hword 0xc082, 0xe1a0, 0x3482, 0xe1a0\n"
        ".hword 0xec2c, 0xe1a0, 0xcfa2, 0xe1a0\n"
        ".hword 0xe10e, 0xe791, 0x2823, 0xe1a0\n"
        ".hword 0x2b8c, 0xe182, 0xc002, 0xe18e\n"
        ".hword 0x3a10, 0xee12, 0x2102, 0xe3d3\n"
        ".hword 0x2fa3, 0x01a0, 0x2b82, 0x01a0\n"
        ".hword 0x0007, 0x0a00, 0xe083, 0xe1a0\n"
        ".hword 0x2483, 0xe1a0, 0xec2e, 0xe1a0\n"
        ".hword 0x3fa3, 0xe1a0, 0xe10e, 0xe791\n"
        ".hword 0x2822, 0xe1a0, 0x2b83, 0xe182\n"
        ".hword 0x200e, 0xe182, 0x3c02, 0xe18c\n"
        ".hword 0x2422, 0xe1a0, 0x201c, 0xe58d\n"
        ".hword 0x3018, 0xe58d, 0x2000, 0xe590\n"
        ".hword 0x3102, 0xe3d2, 0x2fa2, 0x01a0\n"
        ".hword 0xcb82, 0x01a0, 0x0007, 0x0a00\n"
        ".hword 0x3082, 0xe1a0, 0xc482, 0xe1a0\n"
        ".hword 0xec23, 0xe1a0, 0x3fa2, 0xe1a0\n"
        ".hword 0xe10e, 0xe791, 0x282c, 0xe1a0\n"
        ".hword 0x2b83, 0xe182, 0xc002, 0xe18e\n"
        ".hword 0x2004, 0xe590, 0x3102, 0xe3d2\n"
        ".hword 0x2fa2, 0x01a0, 0x3b82, 0x01a0\n"
        ".hword 0x0007, 0x0a00, 0x3082, 0xe1a0\n"
        ".hword 0xe482, 0xe1a0, 0x4c23, 0xe1a0\n"
        ".hword 0x3fa2, 0xe1a0, 0x4104, 0xe791\n"
        ".hword 0x282e, 0xe1a0, 0x2b83, 0xe182\n"
        ".hword 0x3002, 0xe184, 0x2008, 0xe590\n"
        ".hword 0xe102, 0xe3d2, 0x2fa2, 0x01a0\n"
        ".hword 0x2b82, 0x01a0, 0x0007, 0x0a00\n"
        ".hword 0xe082, 0xe1a0, 0x4482, 0xe1a0\n"
        ".hword 0x5c2e, 0xe1a0, 0xefa2, 0xe1a0\n"
        ".hword 0x5105, 0xe791, 0x2824, 0xe1a0\n"
        ".hword 0x2b8e, 0xe182, 0x2005, 0xe182\n"
        ".hword 0x000c, 0xe590, 0xe102, 0xe3d0\n"
        ".hword 0x0fa0, 0x01a0, 0x0b80, 0x01a0\n"
        ".hword 0x0007, 0x0a00, 0xe080, 0xe1a0\n"
        ".hword 0x4480, 0xe1a0, 0x5c2e, 0xe1a0\n"
        ".hword 0xefa0, 0xe1a0, 0x1105, 0xe791\n"
        ".hword 0x0824, 0xe1a0, 0x0b8e, 0xe180\n"
        ".hword 0x0001, 0xe180, 0x1400, 0xe1a0\n"
        ".hword 0x0802, 0xe1a0, 0x1822, 0xe181\n"
        ".hword 0x0423, 0xe180, 0x2c03, 0xe18c\n"
        ".hword 0x01f0, 0xe1cd, 0x200c, 0xe58d\n"
        ".hword 0x2018, 0xe28d, 0x100c, 0xe28d\n"
        ".hword 0x000d, 0xe1a0, 0x20de, 0xebff\n"
        ".hword 0xd024, 0xe28d, 0x8030, 0xe8bd\n"
        ".hword 0x31a0, 0x004e\n"
    );
};

// DECOMP_FUNC(0x003a719c, 724)
extern "C" __attribute__((naked)) void script_vm_func_003a719c() {
    asm volatile(
        ".arm\n"
        ".hword 0x5ff0, 0xe92d, 0x6000, 0xe3a0\n"
        ".hword 0xde61, 0xe24d, 0x4000, 0xe1a0\n"
        ".hword 0x9006, 0xe1a0, 0x8006, 0xe1a0\n"
        ".hword 0x3ce5, 0xebfb, 0xb000, 0xe1a0\n"
        ".hword 0x0b01, 0xe284, 0x5c05, 0xe284\n"
        ".hword 0x0f57, 0xe280, 0x0000, 0xe58d\n"
        ".hword 0x0af8, 0xe1d5, 0x0000, 0xe350\n"
        ".hword 0x000a, 0xda00, 0x5fcb, 0xebfb\n"
        ".hword 0x6000, 0xe1a0, 0x94a9, 0xebfa\n"
        ".hword 0x9000, 0xe1a0, 0xbd58, 0xebfa\n"
        ".hword 0x0000, 0xe356, 0x8000, 0xe1a0\n"
        ".hword 0x0002, 0x1a00, 0x0000, 0xe59d\n"
        ".hword 0x01d2, 0xe1d0, 0x6000, 0xe1a0\n"
        ".hword 0xf000, 0xe320, 0x15a6, 0xebfb\n"
        ".hword 0x0000, 0xe350, 0x7000, 0xe3a0\n"
        ".hword 0xa001, 0xe3a0, 0x0016, 0x0a00\n"
        ".hword 0x1014, 0xe284, 0x0009, 0xe3a0\n"
        ".hword 0x0081, 0xe881, 0xdc20, 0xebfb\n"
        ".hword 0x0001, 0xe350, 0x0ca5, 0xe284\n"
        ".hword 0x1005, 0x13a0, 0xabb4, 0x01c0\n"
        ".hword 0x1bb4, 0x11c0, 0x1bf4, 0xe1d0\n"
        ".hword 0x00dc, 0xe284, 0x3061, 0xebfa\n"
        ".hword 0x00a4, 0xe5d5, 0x0000, 0xe350\n"
        ".hword 0x0001, 0x03a0, 0xd721, 0x0bfb\n"
        ".hword 0x0590, 0xe594, 0xf000, 0xe320\n"
        ".hword 0x31df, 0xebfa, 0x0000, 0xe59d\n"
        ".hword 0xde61, 0xe28d, 0x5ff0, 0xe8bd\n"
        ".hword 0x31cc, 0xeafa, 0x0000, 0xe356\n"
        ".hword 0x6b01, 0xe284, 0x6f6a, 0xe286\n"
        ".hword 0x0021, 0x0a00, 0x0020, 0xe284\n"
        ".hword 0x3143, 0xebfa, 0x0280, 0xe086\n"
        ".hword 0x50b4, 0xe1d0, 0x0005, 0xe1a0\n"
        ".hword 0x57ee, 0xebfc, 0x1000, 0xe1a0\n"
        ".hword 0x600d, 0xe1a0, 0x0006, 0xe1a0\n"
        ".hword 0x616e, 0xebfc, 0x1006, 0xe1a0\n"
        ".hword 0x0008, 0xe3a0, 0xb991, 0xebfb\n"
        ".hword 0x1001, 0xe3a0, 0x0005, 0xe1a0\n"
        ".hword 0x5755, 0xebfc, 0x1000, 0xe1a0\n"
        ".hword 0x0006, 0xe1a0, 0x6165, 0xebfc\n"
        ".hword 0x1006, 0xe1a0, 0x0010, 0xe3a0\n"
        ".hword 0xb988, 0xebfb, 0x05a0, 0xe594\n"
        ".hword 0x1006, 0xe3a0, 0xbfbd, 0xebfb\n"
        ".hword 0x0001, 0xe3a0, 0xf000, 0xe320\n"
        ".hword 0xe71b, 0xebfb, 0x4014, 0xe284\n"
        ".hword 0x0007, 0xe3a0, 0x0081, 0xe884\n"
        ".hword 0x2dcf, 0xebfa, 0xde61, 0xe28d\n"
        ".hword 0x9ff0, 0xe8bd, 0x0000, 0xe35b\n"
        ".hword 0x0016, 0x0a00, 0x00a4, 0xe5d5\n"
        ".hword 0x0000, 0xe350, 0x0001, 0x03a0\n"
        ".hword 0xd6ee, 0x0bfb, 0x1138, 0xe59f\n"
        ".hword 0x0000, 0xe3a0, 0xdf75, 0xebfb\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0xd66d, 0xebfb, 0x1001, 0xe3a0\n"
        ".hword 0x00dc, 0xe284, 0x3021, 0xebfa\n"
        ".hword 0x0001, 0xe3a0, 0xf000, 0xe320\n"
        ".hword 0xe703, 0xebfb, 0x4014, 0xe284\n"
        ".hword 0x000b, 0xe3a0, 0x0081, 0xe884\n"
        ".hword 0x2d9c, 0xebfa, 0xde61, 0xe28d\n"
        ".hword 0x5ff0, 0xe8bd, 0x151c, 0xeafb\n"
        ".hword 0x10f0, 0xe59f, 0x0000, 0xe359\n"
        ".hword 0x0000, 0xe3e0, 0x002a, 0x0a00\n"
        ".hword 0x0004, 0xe581, 0x00a5, 0xe5d5\n"
        ".hword 0x0001, 0xe280, 0x0070, 0xe6af\n"
        ".hword 0x0001, 0xe350, 0x05a5, 0xe5c4\n"
        ".hword 0x75a5, 0xc5c4, 0x2da8, 0xebfa\n"
        ".hword 0xa5a7, 0xe5c4, 0x00a5, 0xe5d5\n"
        ".hword 0x0001, 0xe350, 0x004c, 0x03a0\n"
        ".hword 0x004d, 0x13a0, 0x45ee, 0xebfc\n"
        ".hword 0x0020, 0xe284, 0xf000, 0xe320\n"
        ".hword 0x30f5, 0xebfa, 0x0280, 0xe086\n"
        ".hword 0x10a5, 0xe5d5, 0x00b4, 0xe1d0\n"
        ".hword 0x0001, 0xe351, 0x4070, 0xe6bf\n"
        ".hword 0x000a, 0x0a00, 0x500d, 0xe1a0\n"
        ".hword 0x0074, 0xe6ff, 0x1005, 0xe1a0\n"
        ".hword 0xd987, 0xebfb, 0x2074, 0xe6ff\n"
        ".hword 0x3005, 0xe1a0, 0x1001, 0xe3a0\n"
        ".hword 0x0000, 0xe3a0, 0xda33, 0xebfb\n"
        ".hword 0xde61, 0xe28d, 0x9ff0, 0xe8bd\n"
        ".hword 0x0074, 0xe6ff, 0x2503, 0xebfc\n"
        ".hword 0xde61, 0xe28d, 0x2074, 0xe6ff\n"
        ".hword 0x5ff0, 0xe8bd, 0x3000, 0xe1a0\n"
        ".hword 0x1001, 0xe3a0, 0x0000, 0xe3a0\n"
        ".hword 0xda28, 0xeafb, 0x0000, 0xe358\n"
        ".hword 0xffb3, 0x0aff, 0x0004, 0xe581\n"
        ".hword 0x0001, 0xe3a0, 0xe6c8, 0xebfb\n"
        ".hword 0x2014, 0xe284, 0x0008, 0xe3a0\n"
        ".hword 0x0081, 0xe882, 0x1007, 0xe3a0\n"
        ".hword 0x05a0, 0xe594, 0xbf61, 0xebfb\n"
        ".hword 0xde61, 0xe28d, 0x5ff0, 0xe8bd\n"
        ".hword 0x2d77, 0xeafa, 0x32ff, 0x3232\n"
        ".hword 0xd9c8, 0x0043\n"
    );
};

// DECOMP_FUNC(0x003922f0, 728)
extern "C" __attribute__((naked)) void engine_func_003922f0() {
    asm volatile(
        ".arm\n"
        ".hword 0x43f0, 0xe92d, 0xd03c, 0xe24d\n"
        ".hword 0x4000, 0xe1a0, 0x000d, 0xe1a0\n"
        ".hword 0x87dc, 0xebfa, 0x12b0, 0xe59f\n"
        ".hword 0x0008, 0xe594, 0x82a4, 0xe59f\n"
        ".hword 0x7003, 0xe3a0, 0x6000, 0xe591\n"
        ".hword 0x0003, 0xe350, 0x9005, 0xe3a0\n"
        ".hword 0x5000, 0xe3a0, 0x005b, 0x0a00\n"
        ".hword 0x001c, 0xaa00, 0x0000, 0xe350\n"
        ".hword 0x0027, 0x0a00, 0x0001, 0xe350\n"
        ".hword 0x002d, 0x0a00, 0x0002, 0xe350\n"
        ".hword 0x0014, 0x1a00, 0x0208, 0xe594\n"
        ".hword 0x0000, 0xe350, 0x0002, 0x0a00\n"
        ".hword 0x1000, 0xe590, 0x1004, 0xe591\n"
        ".hword 0xff31, 0xe12f, 0x1002, 0xe3a0\n"
        ".hword 0x0f83, 0xe284, 0x877d, 0xebfa\n"
        ".hword 0x5000, 0xe1a0, 0x0208, 0xe584\n"
        ".hword 0x0d09, 0xe284, 0x8509, 0xebfa\n"
        ".hword 0x2240, 0xe59f, 0x1678, 0xe596\n"
        ".hword 0x0290, 0xe000, 0x2238, 0xe59f\n"
        ".hword 0x0180, 0xe082, 0x00b0, 0xe191\n"
        ".hword 0x0014, 0xe585, 0x7008, 0xe584\n"
        ".hword 0xd03c, 0xe28d, 0x83f0, 0xe8bd\n"
        ".hword 0x0004, 0xe350, 0x005c, 0x0a00\n"
        ".hword 0x0005, 0xe350, 0x0070, 0x0a00\n"
        ".hword 0x0c27, 0xe240, 0x000f, 0xe250\n"
        ".hword 0xfff6, 0x1aff, 0x2003, 0xe3a0\n"
        ".hword 0x1005, 0xe3a0, 0x0004, 0xe1a0\n"
        ".hword 0x870d, 0xebfa, 0xd03c, 0xe28d\n"
        ".hword 0x83f0, 0xe8bd, 0x1000, 0xe3a0\n"
        ".hword 0x0f83, 0xe284, 0x875f, 0xebfa\n"
        ".hword 0x1001, 0xe3a0, 0x1008, 0xe5a4\n"
        ".hword 0x0200, 0xe584, 0xd03c, 0xe28d\n"
        ".hword 0x83f0, 0xe8bd, 0x1208, 0xe594\n"
        ".hword 0x0000, 0xe591, 0x200c, 0xe590\n"
        ".hword 0x0014, 0xe28d, 0xff32, 0xe12f\n"
        ".hword 0x5014, 0xe28d, 0x100f, 0xe895\n"
        ".hword 0x100f, 0xe88d, 0x000d, 0xe1a0\n"
        ".hword 0xb219, 0xebfb, 0x0000, 0xe350\n"
        ".hword 0x0002, 0x13a0, 0x0002, 0x0a00\n"
        ".hword 0x0008, 0xe584, 0xd03c, 0xe28d\n"
        ".hword 0x83f0, 0xe8bd, 0x000d, 0xe1a0\n"
        ".hword 0x3ce0, 0xebfc, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0xffd3, 0x0aff\n"
        ".hword 0x0000, 0xe5dd, 0x0066, 0xe350\n"
        ".hword 0x0002, 0x0a00, 0x0067, 0xe350\n"
        ".hword 0x0008, 0x1a00, 0x0040, 0xea00\n"
        ".hword 0x100f, 0xe89d, 0x5028, 0xe28d\n"
        ".hword 0x100f, 0xe885, 0x1028, 0xe28d\n"
        ".hword 0x0004, 0xe1a0, 0x878f, 0xebfa\n"
        ".hword 0xd03c, 0xe28d, 0x83f0, 0xe8bd\n"
        ".hword 0x100f, 0xe89d, 0x8008, 0xe5a4\n"
        ".hword 0x4f82, 0xe284, 0x100f, 0xe884\n"
        ".hword 0xd03c, 0xe28d, 0x83f0, 0xe8bd\n"
        ".hword 0x1208, 0xe594, 0x0000, 0xe591\n"
        ".hword 0x200c, 0xe590, 0x0014, 0xe28d\n"
        ".hword 0xff32, 0xe12f, 0x6014, 0xe28d\n"
        ".hword 0x100f, 0xe896, 0x100f, 0xe88d\n"
        ".hword 0x000d, 0xe1a0, 0xb1f0, 0xebfb\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0007, 0x0a00, 0x0208, 0xe594\n"
        ".hword 0x2004, 0xe284, 0x100a, 0xe3a0\n"
        ".hword 0x0022, 0xe882, 0x0000, 0xe350\n"
        ".hword 0x002e, 0x1a00, 0xd03c, 0xe28d\n"
        ".hword 0x83f0, 0xe8bd, 0x000d, 0xe1a0\n"
        ".hword 0x3cb2, 0xebfc, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0xffa5, 0x0aff\n"
        ".hword 0x0000, 0xe5dd, 0x0066, 0xe350\n"
        ".hword 0xffd4, 0x0aff, 0x0067, 0xe350\n"
        ".hword 0x0004, 0x03a0, 0xffd9, 0x1aff\n"
        ".hword 0xffc2, 0xeaff, 0x1006, 0xe1a0\n"
        ".hword 0x0020, 0xe28d, 0x878f, 0xebfa\n"
        ".hword 0x02d0, 0xe1cd, 0x01f8, 0xe1cd\n"
        ".hword 0x0018, 0xe28d, 0x3c0f, 0xebfc\n"
        ".hword 0x0fa0, 0xe1b0, 0xf000, 0xe320\n"
        ".hword 0x0007, 0x0a00, 0x8008, 0xe584\n"
        ".hword 0x2064, 0xe3a0, 0x01d8, 0xe1cd\n"
        ".hword 0x2210, 0xe5c4, 0x4f85, 0xe284\n"
        ".hword 0x0003, 0xe884, 0xd03c, 0xe28d\n"
        ".hword 0x83f0, 0xe8bd, 0x9008, 0xe5a4\n"
        ".hword 0x7004, 0xe584, 0xd03c, 0xe28d\n"
        ".hword 0x83f0, 0xe8bd, 0x000c, 0xe594\n"
        ".hword 0x0001, 0xe240, 0x0000, 0xe350\n"
        ".hword 0x000c, 0xe584, 0xff83, 0xcaff\n"
        ".hword 0x0208, 0xe594, 0x2004, 0xe284\n"
        ".hword 0x1006, 0xe3a0, 0x0022, 0xe882\n"
        ".hword 0x0000, 0xe350, 0xff7d, 0x0aff\n"
        ".hword 0x1000, 0xe590, 0x1004, 0xe591\n"
        ".hword 0xff31, 0xe12f, 0x5208, 0xe584\n"
        ".hword 0xd03c, 0xe28d, 0x83f0, 0xe8bd\n"
        ".hword 0x270f, 0x0000, 0x2fc8, 0x0043\n"
        ".hword 0x0139, 0x0000, 0x09aa, 0x0000\n"
    );
};

// DECOMP_FUNC(0x002f9914, 736)
extern "C" __attribute__((naked)) void func_002f9914() {
    asm volatile(
        ".arm\n"
        ".hword 0x5ff0, 0xe92d, 0xa034, 0xe5b0\n"
        ".hword 0x0008, 0xe280, 0x0202, 0xe890\n"
        ".hword 0x00b0, 0xe891, 0x6034, 0xe599\n"
        ".hword 0xb03c, 0xe595, 0x0006, 0xe15a\n"
        ".hword 0x0001, 0xda00, 0x0000, 0xe356\n"
        ".hword 0x00a1, 0x1a00, 0x0038, 0xe595\n"
        ".hword 0x1298, 0xe59f, 0x0080, 0xe080\n"
        ".hword 0x0180, 0xe081, 0x100c, 0xe590\n"
        ".hword 0x0005, 0xe1a0, 0xff31, 0xe12f\n"
        ".hword 0xc0d5, 0xebfd, 0x1034, 0xe595\n"
        ".hword 0xaa10, 0xee00, 0x6a90, 0xee00\n"
        ".hword 0x0001, 0xe080, 0x0034, 0xe585\n"
        ".hword 0x0000, 0xe59b, 0x1008, 0xe597\n"
        ".hword 0x1ac0, 0xeeb8, 0x0ae0, 0xeef8\n"
        ".hword 0x3008, 0xe590, 0x00f2, 0xe1d0\n"
        ".hword 0x2030, 0xe591, 0x8038, 0xe599\n"
        ".hword 0x1001, 0xe240, 0x0054, 0xe597\n"
        ".hword 0x3030, 0xe593, 0x0004, 0xe380\n"
        ".hword 0x0a20, 0xee81, 0x0054, 0xe587\n"
        ".hword 0x0000, 0xe59b, 0xc054, 0xe590\n"
        ".hword 0xc004, 0xe38c, 0xc054, 0xe580\n"
        ".hword 0x00c4, 0xe5d9, 0x0000, 0xe350\n"
        ".hword 0x007f, 0x1a00, 0x0000, 0xe358\n"
        ".hword 0x7000, 0xe3a0, 0x007c, 0x9a00\n"
        ".hword 0x6210, 0xe59f, 0x2a82, 0xeddf\n"
        ".hword 0xe081, 0xe081, 0x000c, 0xe593\n"
        ".hword 0xc204, 0xe59f, 0x0000, 0xe586\n"
        ".hword 0x0010, 0xe593, 0x9c01, 0xe28c\n"
        ".hword 0xae12, 0xe28c, 0x0004, 0xe586\n"
        ".hword 0x0014, 0xe593, 0xbe11, 0xe28c\n"
        ".hword 0x1e11, 0xe28c, 0x0008, 0xe586\n"
        ".hword 0x0c01, 0xe28c, 0x0a04, 0xecd6\n"
        ".hword 0x5c01, 0xe28c, 0x0a04, 0xecc9\n"
        ".hword 0x0a04, 0xecca, 0x9024, 0xe593\n"
        ".hword 0x9000, 0xe586, 0x9028, 0xe593\n"
        ".hword 0x9004, 0xe586, 0x902c, 0xe593\n"
        ".hword 0x9008, 0xe586, 0x9a10, 0xee04\n"
        ".hword 0x3a02, 0xec96, 0x2a47, 0xed8c\n"
        ".hword 0x3a03, 0xec8b, 0x0a03, 0xecc6\n"
        ".hword 0x0a06, 0xedc2, 0x9004, 0xe596\n"
        ".hword 0x901c, 0xe582, 0x9008, 0xe596\n"
        ".hword 0x9020, 0xe582, 0x0a00, 0xedd0\n"
        ".hword 0x1a00, 0xed91, 0x0ac1, 0xee70\n"
        ".hword 0x0a00, 0xedc0, 0x0a01, 0xedd0\n"
        ".hword 0x1a01, 0xed91, 0x0ac1, 0xee70\n"
        ".hword 0x0a01, 0xedc0, 0x0a02, 0xedd0\n"
        ".hword 0x1a02, 0xed91, 0x0ac1, 0xee70\n"
        ".hword 0x0a02, 0xedc0, 0x1a03, 0xed90\n"
        ".hword 0x0a03, 0xedd1, 0x0a60, 0xee71\n"
        ".hword 0x0a03, 0xedc0, 0x1a00, 0xedd5\n"
        ".hword 0x0a01, 0xedd5, 0x1aa1, 0xee21\n"
        ".hword 0x1aa0, 0xee00, 0x0a02, 0xedd5\n"
        ".hword 0x1aa0, 0xee00, 0x0ac1, 0xeef1\n"
        ".hword 0x0ae2, 0xeef4, 0xfa10, 0xeef1\n"
        ".hword 0x0007, 0xda00, 0x2aa0, 0xee81\n"
        ".hword 0x3a01, 0xed95, 0x1a02, 0xed95\n"
        ".hword 0x2a00, 0xed85, 0x1a20, 0xeec3\n"
        ".hword 0x1a01, 0xedc5, 0x3a20, 0xee81\n"
        ".hword 0x3a02, 0xed85, 0x0a00, 0xedd4\n"
        ".hword 0x1a40, 0xed9c, 0x5e12, 0xe28c\n"
        ".hword 0x0a80, 0xee60, 0x1c01, 0xe28c\n"
        ".hword 0x0000, 0xe357, 0x1a20, 0xee21\n"
        ".hword 0x1a40, 0xed8c, 0x1a41, 0xed9c\n"
        ".hword 0x1a20, 0xee21, 0x1a41, 0xed8c\n"
        ".hword 0x1a42, 0xed9c, 0x1a20, 0xee21\n"
        ".hword 0x1a42, 0xed8c, 0x1a43, 0xed9c\n"
        ".hword 0x0a20, 0xee61, 0x0a43, 0xedcc\n"
        ".hword 0x0a40, 0xeddc, 0x1a48, 0xed9c\n"
        ".hword 0x0a81, 0xee70, 0x0a40, 0xedcc\n"
        ".hword 0x0a01, 0xedd1, 0x1a01, 0xed95\n"
        ".hword 0xcc01, 0xe28c, 0x0a81, 0xee70\n"
        ".hword 0x0a01, 0xedc1, 0x0a02, 0xedd1\n"
        ".hword 0x1a02, 0xed95, 0x0a81, 0xee70\n"
        ".hword 0x0a02, 0xedc1, 0x1a03, 0xed95\n"
        ".hword 0x0a03, 0xedd1, 0x0a81, 0xee70\n"
        ".hword 0x0a03, 0xedc1, 0x1023, 0xe89c\n"
        ".hword 0x1023, 0xe886, 0x500c, 0xe282\n"
        ".hword 0x0000, 0xe582, 0x0004, 0xe596\n"
        ".hword 0x0004, 0xe582, 0x0008, 0xe596\n"
        ".hword 0x0008, 0xe582, 0x003c, 0xe283\n"
        ".hword 0x1003, 0xe890, 0x1003, 0xe885\n"
        ".hword 0x000a, 0x0a00, 0x0024, 0xe243\n"
        ".hword 0x5024, 0xe282, 0x1003, 0xe890\n"
        ".hword 0x1003, 0xe885, 0x7001, 0xe287\n"
        ".hword 0x0008, 0xe157, 0x2030, 0xe282\n"
        ".hword 0x3030, 0xe283, 0x4004, 0xe284\n"
        ".hword 0xff85, 0x3aff, 0x9ff0, 0xe8bd\n"
        ".hword 0xc10e, 0xe083, 0xc048, 0xe24c\n"
        ".hword 0x5024, 0xe282, 0x1003, 0xe89c\n"
        ".hword 0x1003, 0xe885, 0xfff2, 0xeaff\n"
        ".hword 0x2718, 0x0047, 0x0000, 0x0000\n"
        ".hword 0x2550, 0x0047, 0xa81c, 0x004e\n"
    );
};

// DECOMP_FUNC(0x002931f0, 740)
extern "C" __attribute__((naked)) void camp_func_002931f0() {
    asm volatile(
        ".arm\n"
        ".hword 0x40f0, 0xe92d, 0x5b0d, 0xe280\n"
        ".hword 0x500c, 0xe285, 0x4000, 0xe1a0\n"
        ".hword 0x0000, 0xe595, 0xd01c, 0xe24d\n"
        ".hword 0x3014, 0xeb00, 0x6000, 0xe1a0\n"
        ".hword 0x0000, 0xe595, 0x300b, 0xeb00\n"
        ".hword 0x5000, 0xe086, 0x1000, 0xe3a0\n"
        ".hword 0x0004, 0xe1a0, 0x1345, 0xeb00\n"
        ".hword 0x0001, 0xe350, 0x0028, 0x0a00\n"
        ".hword 0x1000, 0xe3a0, 0x0004, 0xe1a0\n"
        ".hword 0x1340, 0xeb00, 0x0002, 0xe350\n"
        ".hword 0x007e, 0x0a00, 0x1000, 0xe3a0\n"
        ".hword 0x0004, 0xe1a0, 0x133b, 0xeb00\n"
        ".hword 0x0007, 0xe350, 0x0091, 0x0a00\n"
        ".hword 0x1000, 0xe3a0, 0x0004, 0xe1a0\n"
        ".hword 0x1336, 0xeb00, 0x0003, 0xe350\n"
        ".hword 0x0017, 0x1a00, 0x1258, 0xe59f\n"
        ".hword 0x6000, 0xe3a0, 0x0faf, 0xe281\n"
        ".hword 0x42cc, 0xe591, 0x100d, 0xe890\n"
        ".hword 0x12d0, 0xe591, 0x4010, 0xe58d\n"
        ".hword 0x4006, 0xe1a0, 0x1014, 0xe58d\n"
        ".hword 0x100d, 0xe88d, 0x002e, 0xe284\n"
        ".hword 0xffcb, 0xebff, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x0083, 0x0a00\n"
        ".hword 0x0005, 0xe156, 0x6001, 0x1286\n"
        ".hword 0x0080, 0x1a00, 0x0104, 0xe79d\n"
        ".hword 0x00ff, 0xe200, 0x10f9, 0xebfe\n"
        ".hword 0x1208, 0xe59f, 0xf000, 0xe320\n"
        ".hword 0x2f8f, 0xeb00, 0xd01c, 0xe28d\n"
        ".hword 0x80f0, 0xe8bd, 0x7a03, 0xe284\n"
        ".hword 0x6b16, 0xe284, 0x005c, 0xe597\n"
        ".hword 0x6f6f, 0xe286, 0x0000, 0xe350\n"
        ".hword 0x0009, 0x0a00, 0x0000, 0xe355\n"
        ".hword 0x003b, 0x0a00, 0x0267, 0xeb00\n"
        ".hword 0x0b11, 0xe280, 0x00a8, 0xe280\n"
        ".hword 0x0000, 0xe590, 0x0040, 0xe310\n"
        ".hword 0x0005, 0x11a0, 0x0042, 0x0a00\n"
        ".hword 0x005f, 0xea00, 0x0000, 0xe355\n"
        ".hword 0x0011, 0x0a00, 0x0001, 0xe355\n"
        ".hword 0x0014, 0x1a00, 0x0e41, 0xe3a0\n"
        ".hword 0xb61e, 0xeb00, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x000f, 0x0a00\n"
        ".hword 0x8ceb, 0xeb00, 0x10b2, 0xe1d0\n"
        ".hword 0x0000, 0xe351, 0x00b4, 0x11d0\n"
        ".hword 0x0000, 0x1350, 0x0009, 0x0a00\n"
        ".hword 0x0000, 0xe596, 0xd01c, 0xe28d\n"
        ".hword 0x1001, 0xe3a0, 0x40f0, 0xe8bd\n"
        ".hword 0xda09, 0xea01, 0x0000, 0xe596\n"
        ".hword 0xd01c, 0xe28d, 0x1000, 0xe3a0\n"
        ".hword 0x40f0, 0xe8bd, 0x0f9f, 0xea02\n"
        ".hword 0x6002, 0xe245, 0x0e41, 0xe3a0\n"
        ".hword 0xb608, 0xeb00, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x0005, 0x0a00\n"
        ".hword 0x8cd5, 0xeb00, 0x10b2, 0xe1d0\n"
        ".hword 0x0000, 0xe351, 0x00b4, 0x11d0\n"
        ".hword 0x0000, 0x1350, 0x0000, 0x1a00\n"
        ".hword 0x6001, 0xe245, 0xf000, 0xe320\n"
        ".hword 0x0238, 0xeb00, 0x0b11, 0xe280\n"
        ".hword 0x00a8, 0xe280, 0x0000, 0xe590\n"
        ".hword 0x0040, 0xe310, 0x0001, 0x1286\n"
        ".hword 0x0018, 0x1a00, 0x005c, 0xe597\n"
        ".hword 0x0200, 0xe084, 0x0086, 0xe080\n"
        ".hword 0x0b0d, 0xe280, 0x01bc, 0xe1d0\n"
        ".hword 0x0012, 0xea00, 0x0080, 0xe084\n"
        ".hword 0x0b0e, 0xe280, 0x0ff4, 0xe1d0\n"
        ".hword 0x557b, 0xeb00, 0x4000, 0xe1a0\n"
        ".hword 0x04b6, 0xe1d0, 0x7508, 0xeb00\n"
        ".hword 0x3000, 0xe1a0, 0x24b6, 0xe1d4\n"
        ".hword 0x0000, 0xe596, 0xd01c, 0xe28d\n"
        ".hword 0x1002, 0xe3a0, 0x40f0, 0xe8bd\n"
        ".hword 0x2a2d, 0xea00, 0x005c, 0xe597\n"
        ".hword 0x0200, 0xe084, 0x0085, 0xe080\n"
        ".hword 0x0b0d, 0xe280, 0x01ba, 0xe1d0\n"
        ".hword 0x0000, 0xe350, 0x0016, 0x1a00\n"
        ".hword 0xd01c, 0xe28d, 0x80f0, 0xe8bd\n"
        ".hword 0xf000, 0xe320, 0x0213, 0xeb00\n"
        ".hword 0x0b11, 0xe280, 0x00a8, 0xe280\n"
        ".hword 0x0000, 0xe590, 0x0040, 0xe310\n"
        ".hword 0x0006, 0x0a00, 0x020d, 0xeb00\n"
        ".hword 0x1005, 0xe1a0, 0xf000, 0xe320\n"
        ".hword 0xe847, 0xebff, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0x0004, 0xea00\n"
        ".hword 0xf000, 0xe320, 0x0205, 0xeb00\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0xe818, 0xebff, 0x0000, 0xe350\n"
        ".hword 0xff8d, 0x0aff, 0xd01c, 0xe28d\n"
        ".hword 0x40f0, 0xe8bd, 0x25d2, 0xea00\n"
        ".hword 0x0085, 0xe084, 0x0b0d, 0xe280\n"
        ".hword 0x08b0, 0xe1d0, 0xd01c, 0xe28d\n"
        ".hword 0x40f0, 0xe8bd, 0xfbc5, 0xeaff\n"
        ".hword 0x4001, 0xe284, 0x0006, 0xe354\n"
        ".hword 0xff73, 0xbaff, 0xd01c, 0xe28d\n"
        ".hword 0x80f0, 0xe8bd, 0x0fe4, 0x0040\n"
        ".hword 0x32ff, 0x3232\n"
    );
};

// DECOMP_FUNC(0x002a34a4, 740)
extern "C" __attribute__((naked)) void engine_func_002a34a4() {
    asm volatile(
        ".arm\n"
        ".hword 0x41f0, 0xe92d, 0x2002, 0xe3a0\n"
        ".hword 0x8000, 0xe3a0, 0x4000, 0xe1a0\n"
        ".hword 0x8b04, 0xed2d, 0xd018, 0xe24d\n"
        ".hword 0x8a40, 0xeeb0, 0x5008, 0xe590\n"
        ".hword 0x9aab, 0xed9f, 0x0f9d, 0xe285\n"
        ".hword 0x82a8, 0xe585, 0x82b0, 0xe585\n"
        ".hword 0x82c8, 0xe585, 0x82b4, 0xe585\n"
        ".hword 0x2174, 0xe585, 0x2004, 0xe3a0\n"
        ".hword 0x2170, 0xe585, 0x82ac, 0xe585\n"
        ".hword 0x2274, 0xe595, 0x0000, 0xe352\n"
        ".hword 0x0002, 0x1080, 0x0008, 0x01a0\n"
        ".hword 0x0000, 0xe351, 0x0004, 0xe58d\n"
        ".hword 0x0015, 0x0a00, 0x01d0, 0xe1c4\n"
        ".hword 0x1000, 0xe041, 0x1141, 0xe1a0\n"
        ".hword 0x0000, 0xe351, 0x4024, 0xd285\n"
        ".hword 0x0005, 0xda00, 0x1024, 0xe594\n"
        ".hword 0x0000, 0xe351, 0x0000, 0xc590\n"
        ".hword 0x0000, 0xd3a0, 0x4024, 0xe280\n"
        ".hword 0x82b4, 0xe580, 0x8a28, 0xed84\n"
        ".hword 0x8a29, 0xed84, 0x8a2a, 0xed84\n"
        ".hword 0x9a2b, 0xed84, 0x00a0, 0xe284\n"
        ".hword 0x7da5, 0xeb00, 0x00d8, 0xe584\n"
        ".hword 0xd018, 0xe28d, 0x8b04, 0xecbd\n"
        ".hword 0x81f0, 0xe8bd, 0x1008, 0xe5b0\n"
        ".hword 0x0000, 0xe351, 0x0001, 0x1080\n"
        ".hword 0x0008, 0x01a0, 0x1000, 0xe590\n"
        ".hword 0x0242, 0xe351, 0x0045, 0x0a00\n"
        ".hword 0x0010, 0xe58d, 0x0010, 0xe28d\n"
        ".hword 0x7ff7, 0xeb00, 0x01ec, 0xe59f\n"
        ".hword 0x1000, 0xe590, 0x0004, 0xe28d\n"
        ".hword 0xfe10, 0xebff, 0x0004, 0xe59d\n"
        ".hword 0x100c, 0xe5b0, 0x0000, 0xe351\n"
        ".hword 0x0001, 0x1080, 0x0008, 0x01a0\n"
        ".hword 0x0000, 0xe350, 0x0002, 0x0a00\n"
        ".hword 0x1000, 0xe590, 0x0102, 0xe311\n"
        ".hword 0x0000, 0x03a0, 0x0000, 0xe58d\n"
        ".hword 0x100d, 0xe1a0, 0x0008, 0xe28d\n"
        ".hword 0xfdf8, 0xebff, 0x000c, 0xe59d\n"
        ".hword 0x1014, 0xe590, 0x1a07, 0xe3c1\n"
        ".hword 0x1a01, 0xe381, 0x1014, 0xe580\n"
        ".hword 0x100d, 0xe1a0, 0x0008, 0xe28d\n"
        ".hword 0xfdf0, 0xebff, 0x000c, 0xe59d\n"
        ".hword 0x0a49, 0xeeb0, 0x700d, 0xe1a0\n"
        ".hword 0x1014, 0xe590, 0x1c07, 0xe3c1\n"
        ".hword 0x1c01, 0xe381, 0x1014, 0xe580\n"
        ".hword 0x016c, 0xe59f, 0x8a40, 0xeef0\n"
        ".hword 0x0005, 0xe5d0, 0x0000, 0xe350\n"
        ".hword 0x0000, 0xe59d, 0x8a57, 0x1ddf\n"
        ".hword 0x000c, 0xe280, 0x8a00, 0xedc0\n"
        ".hword 0x8a01, 0xedc0, 0x8a02, 0xedc0\n"
        ".hword 0x0a03, 0xed80, 0x0000, 0xe59d\n"
        ".hword 0x000c, 0xe280, 0x7d68, 0xeb00\n"
        ".hword 0x6000, 0xe1a0, 0x1007, 0xe1a0\n"
        ".hword 0x0008, 0xe28d, 0xfdd7, 0xebff\n"
        ".hword 0x000c, 0xe59d, 0x1fa2, 0xe285\n"
        ".hword 0x3000, 0xe3a0, 0x6008, 0xe580\n"
        ".hword 0x0288, 0xe595, 0x0000, 0xe350\n"
        ".hword 0x2001, 0x1080, 0x2008, 0x01a0\n"
        ".hword 0x1005, 0xe3a0, 0xc181, 0xe061\n"
        ".hword 0x010c, 0xe082, 0x002c, 0xe280\n"
        ".hword 0xc010, 0xe590, 0x000f, 0xe31c\n"
        ".hword 0x0009, 0x1a00, 0x0004, 0xea00\n"
        ".hword 0x101c, 0xe5b0, 0x0000, 0xe351\n"
        ".hword 0x0001, 0x1080, 0x0008, 0x01a0\n"
        ".hword 0xffb4, 0xeaff, 0x0004, 0xe590\n"
        ".hword 0x000f, 0xe200, 0x000f, 0xe350\n"
        ".hword 0x002c, 0x0a00, 0x0004, 0xe351\n"
        ".hword 0x3001, 0xe1a0, 0xff90, 0xaaff\n"
        ".hword 0x1008, 0xe283, 0xe0e4, 0xe592\n"
        ".hword 0xc001, 0xe3a0, 0xc11c, 0xe1a0\n"
        ".hword 0x100c, 0xe1ce, 0x100c, 0xe181\n"
        ".hword 0x10e4, 0xe582, 0x1001, 0xe283\n"
        ".hword 0x0181, 0xe061, 0x1001, 0xe281\n"
        ".hword 0x0100, 0xe082, 0x002c, 0xe280\n"
        ".hword 0x3004, 0xe590, 0xc0ff, 0xe3c3\n"
        ".hword 0xc0e3, 0xe38c, 0xc004, 0xe580\n"
        ".hword 0x300c, 0xe590, 0x30ff, 0xe3c3\n"
        ".hword 0x3001, 0xe383, 0x300c, 0xe580\n"
        ".hword 0xc010, 0xe590, 0x3005, 0xe3a0\n"
        ".hword 0x3010, 0xe480, 0xc00f, 0xe3cc\n"
        ".hword 0xc001, 0xe38c, 0xc000, 0xe580\n"
        ".hword 0x0181, 0xe061, 0x0100, 0xe082\n"
        ".hword 0x002c, 0xe280, 0x1004, 0xe590\n"
        ".hword 0x20ff, 0xe3c1, 0x20fd, 0xe382\n"
        ".hword 0x2004, 0xe580, 0x100c, 0xe590\n"
        ".hword 0x10ff, 0xe3c1, 0x1010, 0xe381\n"
        ".hword 0x100c, 0xe580, 0x1010, 0xe590\n"
        ".hword 0x100f, 0xe3c1, 0x1001, 0xe381\n"
        ".hword 0x1010, 0xe580, 0xff66, 0xeaff\n"
        ".hword 0x1001, 0xe251, 0xffc0, 0x5aff\n"
        ".hword 0xffd2, 0xeaff, 0x0000, 0x3f80\n"
        ".hword 0x4b70, 0x0046, 0x4af0, 0x0046\n"
        ".hword 0x0000, 0x0000\n"
    );
};

// DECOMP_FUNC(0x0021dac4, 744)
extern "C" __attribute__((naked)) void engine_func_0021dac4() {
    asm volatile(
        ".arm\n"
        ".hword 0x4ff0, 0xe92d, 0x4002, 0xe1a0\n"
        ".hword 0x7000, 0xe1a0, 0x9001, 0xe1a0\n"
        ".hword 0x8b02, 0xed2d, 0xd044, 0xe24d\n"
        ".hword 0x940e, 0xeb02, 0x8aae, 0xed9f\n"
        ".hword 0x0000, 0xe354, 0x6000, 0xe1a0\n"
        ".hword 0x8000, 0xe3a0, 0xa000, 0xe3e0\n"
        ".hword 0xb001, 0xe3a0, 0x000a, 0x0a00\n"
        ".hword 0x7c0d, 0xe286, 0x4000, 0xe3a0\n"
        ".hword 0x0ed3, 0xe1d7, 0x0000, 0xe350\n"
        ".hword 0x0072, 0xda00, 0x0004, 0xe086\n"
        ".hword 0x0c0d, 0xe280, 0x10e4, 0xe5d0\n"
        ".hword 0x0002, 0xe351, 0x0097, 0x1a00\n"
        ".hword 0x006f, 0xea00, 0x4000, 0xe3a0\n"
        ".hword 0x16ff, 0xeb04, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x0067, 0xda00\n"
        ".hword 0x0b03, 0xe286, 0xbb03, 0xe286\n"
        ".hword 0x0f7b, 0xe280, 0xbf79, 0xe28b\n"
        ".hword 0x8c0d, 0xe286, 0x003c, 0xe58d\n"
        ".hword 0x0004, 0xe1a0, 0xe347, 0xeb00\n"
        ".hword 0x5000, 0xe1a0, 0x00d0, 0xe1d0\n"
        ".hword 0x0001, 0xe370, 0x0056, 0x0a00\n"
        ".hword 0x0007, 0xe150, 0x0054, 0x1a00\n"
        ".hword 0x00d1, 0xe1d5, 0x0009, 0xe150\n"
        ".hword 0x0051, 0x1a00, 0x01f0, 0xe1d5\n"
        ".hword 0xa000, 0xe3a0, 0x0000, 0xe350\n"
        ".hword 0x000f, 0x0a00, 0x8c04, 0xeb02\n"
        ".hword 0x0000, 0xe350, 0x0063, 0xe3a0\n"
        ".hword 0x0004, 0x0a00, 0x8c09, 0xeb02\n"
        ".hword 0x11d3, 0xe1d5, 0x0000, 0xe151\n"
        ".hword 0x0045, 0xba00, 0x000b, 0xea00\n"
        ".hword 0xf000, 0xe320, 0x8c03, 0xeb02\n"
        ".hword 0x11d2, 0xe1d5, 0x0000, 0xe151\n"
        ".hword 0xa1f0, 0xa1d5, 0x003e, 0xba00\n"
        ".hword 0x0004, 0xea00, 0x0063, 0xe3a0\n"
        ".hword 0x8bfc, 0xeb02, 0x11d3, 0xe1d5\n"
        ".hword 0x0000, 0xe151, 0x0038, 0xba00\n"
        ".hword 0x0000, 0xe3a0, 0x1c13, 0xe284\n"
        ".hword 0x1030, 0xe58d, 0x2024, 0xe28d\n"
        ".hword 0x1040, 0xe58d, 0x0034, 0xe58d\n"
        ".hword 0x1001, 0xe3a0, 0x0038, 0xe58d\n"
        ".hword 0x001c, 0xe58d, 0x0020, 0xe58d\n"
        ".hword 0x0013, 0xe882, 0x1000, 0xe3e0\n"
        ".hword 0x0014, 0xe58d, 0x0018, 0xe58d\n"
        ".hword 0x00f0, 0xe1cd, 0x000c, 0xe58d\n"
        ".hword 0x0010, 0xe58d, 0x0008, 0xe58d\n"
        ".hword 0x20fa, 0xe1d5, 0x30f8, 0xe1d5\n"
        ".hword 0x00f6, 0xe1d5, 0x10f4, 0xe1d5\n"
        ".hword 0xc0f2, 0xe1d5, 0x2a10, 0xee00\n"
        ".hword 0x3a90, 0xee00, 0x0a10, 0xee01\n"
        ".hword 0x1a10, 0xee03, 0xca10, 0xee02\n"
        ".hword 0x303a, 0xe3a0, 0x2ac0, 0xeef8\n"
        ".hword 0x1ae0, 0xeef8, 0x1ac1, 0xeeb8\n"
        ".hword 0x0ac3, 0xeef8, 0x0ac2, 0xeeb8\n"
        ".hword 0x2a48, 0xeeb0, 0x2f4b, 0xe28f\n"
        ".hword 0x1000, 0xe3a0, 0x0005, 0xe3a0\n"
        ".hword 0xc5f7, 0xeb00, 0x1ed3, 0xe1d8\n"
        ".hword 0x0002, 0xe3a0, 0x000b, 0xe7c1\n"
        ".hword 0x1ed3, 0xe1d8, 0x003c, 0xe59d\n"
        ".hword 0x4000, 0xe7c1, 0x0ed3, 0xe1d8\n"
        ".hword 0x0080, 0xe086, 0x0c0d, 0xe280\n"
        ".hword 0xafb4, 0xe1c0, 0x0ed3, 0xe1d8\n"
        ".hword 0x1040, 0xe59d, 0x0080, 0xe086\n"
        ".hword 0x0c0e, 0xe280, 0x10b4, 0xe1c0\n"
        ".hword 0x00e3, 0xe5d8, 0x0001, 0xe280\n"
        ".hword 0x0de3, 0xe5c6, 0x4001, 0xe284\n"
        ".hword 0x1697, 0xeb04, 0x0004, 0xe150\n"
        ".hword 0xf000, 0xe320, 0xff9d, 0xcaff\n"
        ".hword 0xd044, 0xe28d, 0x8b02, 0xecbd\n"
        ".hword 0x8ff0, 0xe8bd, 0x5edc, 0xe1d0\n"
        ".hword 0x0005, 0xe1a0, 0xe2e1, 0xeb00\n"
        ".hword 0x2030, 0xe28d, 0x1c13, 0xe285\n"
        ".hword 0x502c, 0xe58d, 0x0102, 0xe882\n"
        ".hword 0x1024, 0xe28d, 0x8038, 0xe58d\n"
        ".hword 0x801c, 0xe58d, 0x8020, 0xe58d\n"
        ".hword 0x0900, 0xe881, 0x2a48, 0xeeb0\n"
        ".hword 0x800c, 0xe58d, 0x8010, 0xe58d\n"
        ".hword 0x8014, 0xe58d, 0x8018, 0xe58d\n"
        ".hword 0x0500, 0xe88d, 0x8008, 0xe58d\n"
        ".hword 0x10fa, 0xe1d0, 0x30f8, 0xe1d0\n"
        ".hword 0x20f6, 0xe1d0, 0xc0f4, 0xe1d0\n"
        ".hword 0x1a90, 0xee01, 0x00f2, 0xe1d0\n"
        ".hword 0x3a10, 0xee01, 0x2a90, 0xee00\n"
        ".hword 0xca10, 0xee00, 0x0a10, 0xee03\n"
        ".hword 0x2ae1, 0xeef8, 0x303a, 0xe3a0\n"
        ".hword 0x1ac1, 0xeef8, 0x1ae0, 0xeeb8\n"
        ".hword 0x0ac0, 0xeef8, 0x0ac3, 0xeeb8\n"
        ".hword 0x2028, 0xe28f, 0x1000, 0xe3a0\n"
        ".hword 0x0005, 0xe3a0, 0xc5b6, 0xeb00\n"
        ".hword 0x0ed3, 0xe1d7, 0x4001, 0xe284\n"
        ".hword 0x0004, 0xe150, 0xff5e, 0xcaff\n"
        ".hword 0xd044, 0xe28d, 0x8b02, 0xecbd\n"
        ".hword 0x8ff0, 0xe8bd, 0x0000, 0x4348\n"
        ".hword 0x4f50, 0x594c, 0x0000, 0x0000\n"
    );
};

// DECOMP_FUNC(0x003a4144, 744)
extern "C" __attribute__((naked)) void camp_func_003a4144() {
    asm volatile(
        ".arm\n"
        ".hword 0x4070, 0xe92d, 0x4000, 0xe1a0\n"
        ".hword 0xe8c5, 0xebfb, 0x0000, 0xe350\n"
        ".hword 0x001b, 0x0a00, 0xe8af, 0xebfb\n"
        ".hword 0x0000, 0xe3a0, 0xf380, 0xebfb\n"
        ".hword 0x0004, 0xe1a0, 0x3188, 0xebfa\n"
        ".hword 0x1010, 0xe594, 0x0000, 0xe3a0\n"
        ".hword 0x0001, 0xe351, 0x1860, 0xe594\n"
        ".hword 0x0007, 0x0a00, 0x0007, 0xe351\n"
        ".hword 0x000b, 0x0a00, 0x0008, 0xe351\n"
        ".hword 0x1007, 0x03a0, 0x1005, 0x13a0\n"
        ".hword 0x1004, 0xe5a4, 0x0004, 0xe584\n"
        ".hword 0x8070, 0xe8bd, 0x0008, 0xe351\n"
        ".hword 0x100f, 0x13a0, 0x1010, 0x03a0\n"
        ".hword 0x1004, 0xe5a4, 0x0004, 0xe584\n"
        ".hword 0x8070, 0xe8bd, 0x1006, 0xe3a0\n"
        ".hword 0x1004, 0xe5a4, 0x0004, 0xe584\n"
        ".hword 0x8070, 0xe8bd, 0x0860, 0xe594\n"
        ".hword 0x1580, 0xe080, 0x2080, 0xe080\n"
        ".hword 0x0280, 0xe062, 0x1081, 0xe084\n"
        ".hword 0x5b03, 0xe281, 0x0100, 0xe084\n"
        ".hword 0x5094, 0xe285, 0x0d22, 0xe280\n"
        ".hword 0x3d6b, 0xebfa, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0xe874, 0xebfb\n"
        ".hword 0x000f, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x006a, 0x0a00, 0x000f, 0xaa00\n"
        ".hword 0x0003, 0xe350, 0x0042, 0x0a00\n"
        ".hword 0x0007, 0xe350, 0x001e, 0x0a00\n"
        ".hword 0x000c, 0xe350, 0xffdd, 0x1aff\n"
        ".hword 0x2966, 0xebfa, 0x0000, 0xe350\n"
        ".hword 0x0a01, 0xe3a0, 0x10b5, 0xe190\n"
        ".hword 0x0049, 0x0a00, 0x0005, 0xe1a0\n"
        ".hword 0x4070, 0xe8bd, 0x2004, 0xe3a0\n"
        ".hword 0x31a8, 0xe59f, 0x6c61, 0xeafb\n"
        ".hword 0x0010, 0xe350, 0x0047, 0x0a00\n"
        ".hword 0x001c, 0xe350, 0xffcf, 0x1aff\n"
        ".hword 0x2958, 0xebfa, 0x0000, 0xe350\n"
        ".hword 0x0a01, 0xe3a0, 0x10b5, 0xe190\n"
        ".hword 0x0004, 0x0a00, 0x0005, 0xe1a0\n"
        ".hword 0x4070, 0xe8bd, 0x2004, 0xe3a0\n"
        ".hword 0x3174, 0xe59f, 0x6c53, 0xeafb\n"
        ".hword 0x0005, 0xe1a0, 0x4070, 0xe8bd\n"
        ".hword 0x2004, 0xe3a0, 0x3164, 0xe59f\n"
        ".hword 0x6c4e, 0xeafb, 0x0860, 0xe594\n"
        ".hword 0x0008, 0xe350, 0x0009, 0x0a00\n"
        ".hword 0x2946, 0xebfa, 0x0000, 0xe350\n"
        ".hword 0x0a01, 0xe3a0, 0x10b5, 0xe190\n"
        ".hword 0x0014, 0x0a00, 0x0005, 0xe1a0\n"
        ".hword 0x4070, 0xe8bd, 0x2004, 0xe3a0\n"
        ".hword 0x3134, 0xe59f, 0x6c41, 0xeafb\n"
        ".hword 0xf000, 0xe320, 0x293b, 0xebfa\n"
        ".hword 0x0000, 0xe350, 0x0a01, 0xe3a0\n"
        ".hword 0x10b5, 0xe190, 0x0004, 0x0a00\n"
        ".hword 0x0005, 0xe1a0, 0x4070, 0xe8bd\n"
        ".hword 0x2004, 0xe3a0, 0x310c, 0xe59f\n"
        ".hword 0x6c36, 0xeafb, 0x0005, 0xe1a0\n"
        ".hword 0x4070, 0xe8bd, 0x2004, 0xe3a0\n"
        ".hword 0x30fc, 0xe59f, 0x6c31, 0xeafb\n"
        ".hword 0x0005, 0xe1a0, 0x4070, 0xe8bd\n"
        ".hword 0x2004, 0xe3a0, 0x30ec, 0xe59f\n"
        ".hword 0x6c2c, 0xeafb, 0xf000, 0xe320\n"
        ".hword 0x2926, 0xebfa, 0x0000, 0xe350\n"
        ".hword 0x0a01, 0xe3a0, 0x10b5, 0xe190\n"
        ".hword 0x0004, 0x0a00, 0x0005, 0xe1a0\n"
        ".hword 0x4070, 0xe8bd, 0x2004, 0xe3a0\n"
        ".hword 0x30c4, 0xe59f, 0x6c21, 0xeafb\n"
        ".hword 0x0005, 0xe1a0, 0x4070, 0xe8bd\n"
        ".hword 0x2004, 0xe3a0, 0x30b4, 0xe59f\n"
        ".hword 0x6c1c, 0xeafb, 0x0005, 0xe1a0\n"
        ".hword 0x4070, 0xe8bd, 0x2004, 0xe3a0\n"
        ".hword 0x30a4, 0xe59f, 0x6c17, 0xeafb\n"
        ".hword 0xf000, 0xe320, 0x2911, 0xebfa\n"
        ".hword 0x0000, 0xe350, 0x0a01, 0xe3a0\n"
        ".hword 0x10b5, 0xe190, 0x0004, 0x0a00\n"
        ".hword 0x0005, 0xe1a0, 0x4070, 0xe8bd\n"
        ".hword 0x2004, 0xe3a0, 0x307c, 0xe59f\n"
        ".hword 0x6c0c, 0xeafb, 0x0005, 0xe1a0\n"
        ".hword 0x4070, 0xe8bd, 0x2004, 0xe3a0\n"
        ".hword 0x306c, 0xe59f, 0x6c07, 0xeafb\n"
        ".hword 0xf000, 0xe320, 0x2901, 0xebfa\n"
        ".hword 0x0000, 0xe350, 0x0a01, 0xe3a0\n"
        ".hword 0x10b5, 0xe190, 0x0004, 0x0a00\n"
        ".hword 0x0005, 0xe1a0, 0x4070, 0xe8bd\n"
        ".hword 0x2004, 0xe3a0, 0x3044, 0xe59f\n"
        ".hword 0x6bfc, 0xeafb, 0x0005, 0xe1a0\n"
        ".hword 0x4070, 0xe8bd, 0x2004, 0xe3a0\n"
        ".hword 0x3034, 0xe59f, 0x6bf7, 0xeafb\n"
        ".hword 0x65c4, 0x003a, 0x66e8, 0x003a\n"
        ".hword 0x0244, 0x003a, 0x0890, 0x003a\n"
        ".hword 0x08d4, 0x003a, 0x0978, 0x003a\n"
        ".hword 0x0918, 0x003a, 0xff60, 0x0039\n"
        ".hword 0x0380, 0x003a, 0xff40, 0x0039\n"
        ".hword 0xfef4, 0x0039, 0x0334, 0x003a\n"
        ".hword 0x0294, 0x003a, 0x0804, 0x003a\n"
    );
};

// DECOMP_FUNC(0x002d3a74, 760)
extern "C" __attribute__((naked)) void script_vm_func_002d3a74() {
    asm volatile(
        ".arm\n"
        ".hword 0x5ff0, 0xe92d, 0x9000, 0xe3a0\n"
        ".hword 0xb063, 0xe3a0, 0x82dc, 0xe59f\n"
        ".hword 0xa001, 0xe3a0, 0x0000, 0xe598\n"
        ".hword 0x00f8, 0xe1d0, 0x0000, 0xe350\n"
        ".hword 0x0007, 0x0a00, 0x0001, 0xe350\n"
        ".hword 0x0039, 0x0a00, 0x0002, 0xe350\n"
        ".hword 0x0042, 0x0a00, 0x0063, 0xe350\n"
        ".hword 0x0001, 0x03a0, 0x0030, 0x0a00\n"
        ".hword 0x002e, 0xea00, 0x6000, 0xe3a0\n"
        ".hword 0x5006, 0xe1a0, 0x4006, 0xe1a0\n"
        ".hword 0xdd09, 0xebfd, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x0029, 0xda00\n"
        ".hword 0x0004, 0xe1a0, 0x3166, 0xeb00\n"
        ".hword 0x10f0, 0xe1d0, 0x0001, 0xe371\n"
        ".hword 0x000c, 0x0a00, 0x2000, 0xe598\n"
        ".hword 0x30f4, 0xe1d2, 0x0003, 0xe151\n"
        ".hword 0x0008, 0x1a00, 0x10f2, 0xe1d0\n"
        ".hword 0x00f6, 0xe1d2, 0x0000, 0xe151\n"
        ".hword 0x0004, 0x1a00, 0x0074, 0xe6bf\n"
        ".hword 0x2f13, 0xeb00, 0x0000, 0xe350\n"
        ".hword 0x5001, 0x0285, 0x6001, 0x0286\n"
        ".hword 0x4001, 0xe284, 0xdcf2, 0xebfd\n"
        ".hword 0x0004, 0xe150, 0xf000, 0xe320\n"
        ".hword 0xffe8, 0xcaff, 0x0000, 0xe355\n"
        ".hword 0x0010, 0x0a00, 0x0001, 0xe355\n"
        ".hword 0x0000, 0x0598, 0x1000, 0x1598\n"
        ".hword 0xa014, 0x0580, 0x0002, 0x13a0\n"
        ".hword 0x0014, 0x1581, 0x0000, 0xe598\n"
        ".hword 0x0000, 0xe356, 0xb0b8, 0x01c0\n"
        ".hword 0x0001, 0x03a0, 0x0004, 0x0a00\n"
        ".hword 0x90ba, 0xe1c0, 0x10b8, 0xe1d0\n"
        ".hword 0x1001, 0xe281, 0x10b8, 0xe1c0\n"
        ".hword 0x0000, 0xe3a0, 0x9ff0, 0xe8bd\n"
        ".hword 0x0000, 0xe598, 0x9014, 0xe580\n"
        ".hword 0xfff1, 0xeaff, 0x01d8, 0xe59f\n"
        ".hword 0x2d07, 0xe3a0, 0x0003, 0xe890\n"
        ".hword 0x20ad, 0xebfe, 0x1000, 0xe598\n"
        ".hword 0x20fa, 0xe1d1, 0x2182, 0xe081\n"
        ".hword 0x0018, 0xe582, 0x00b8, 0xe1d1\n"
        ".hword 0x0001, 0xe280, 0x00b8, 0xe1c1\n"
        ".hword 0x7000, 0xe3a0, 0x4007, 0xe1a0\n"
        ".hword 0xdccb, 0xebfd, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x004f, 0xda00\n"
        ".hword 0x0004, 0xe1a0, 0x3128, 0xeb00\n"
        ".hword 0x5000, 0xe1a0, 0x00f0, 0xe1d0\n"
        ".hword 0x0001, 0xe370, 0x0044, 0x0a00\n"
        ".hword 0x1000, 0xe598, 0x20f4, 0xe1d1\n"
        ".hword 0x0002, 0xe150, 0x0040, 0x1a00\n"
        ".hword 0x00f2, 0xe1d5, 0x10f6, 0xe1d1\n"
        ".hword 0x0001, 0xe150, 0x003c, 0x1a00\n"
        ".hword 0x0074, 0xe6bf, 0x2ed4, 0xeb00\n"
        ".hword 0x0000, 0xe350, 0x0000, 0x0598\n"
        ".hword 0x1000, 0x03a0, 0x0036, 0x1a00\n"
        ".hword 0x2201, 0xe061, 0x2102, 0xe080\n"
        ".hword 0x2024, 0xe5d2, 0x0000, 0xe352\n"
        ".hword 0x0003, 0x0a00, 0x1001, 0xe281\n"
        ".hword 0x0010, 0xe351, 0xfff7, 0xbaff\n"
        ".hword 0x1000, 0xe3e0, 0x0000, 0xe357\n"
        ".hword 0x2071, 0xe6bf, 0x20bc, 0xe1c0\n"
        ".hword 0x1010, 0xe590, 0x2202, 0xe062\n"
        ".hword 0x6102, 0xe080, 0x1001, 0xe281\n"
        ".hword 0x1010, 0xe580, 0xa024, 0xe5e6\n"
        ".hword 0x1c15, 0xe284, 0x9008, 0xe586\n"
        ".hword 0xa004, 0xe586, 0x00f4, 0xe1d5\n"
        ".hword 0x0a10, 0xee00, 0x0ac0, 0xeeb8\n"
        ".hword 0x0a03, 0xed86, 0x00f6, 0xe1d5\n"
        ".hword 0x0a10, 0xee00, 0x0ac0, 0xeeb8\n"
        ".hword 0x0a04, 0xed86, 0x00f8, 0xe1d5\n"
        ".hword 0x0a10, 0xee00, 0x0ac0, 0xeeb8\n"
        ".hword 0x0a05, 0xed86, 0x00fa, 0xe1d5\n"
        ".hword 0x0a10, 0xee00, 0x0ac0, 0xeeb8\n"
        ".hword 0x0a06, 0xed86, 0x901c, 0xe586\n"
        ".hword 0xa020, 0xe5c6, 0x1038, 0xe586\n"
        ".hword 0x4024, 0xe586, 0x001a, 0x0a00\n"
        ".hword 0xa028, 0xe5c6, 0x0000, 0xe598\n"
        ".hword 0x10fa, 0xe1d0, 0x0181, 0xe080\n"
        ".hword 0x1000, 0xe3a0, 0x0018, 0xe590\n"
        ".hword 0xc5ee, 0xebfe, 0x002c, 0xe586\n"
        ".hword 0xa030, 0xe5c6, 0x1001, 0xe3a0\n"
        ".hword 0x9034, 0xe586, 0x3274, 0xebff\n"
        ".hword 0x7001, 0xe287, 0x4001, 0xe284\n"
        ".hword 0xdc7b, 0xebfd, 0x0004, 0xe150\n"
        ".hword 0xf000, 0xe320, 0xffaf, 0xcaff\n"
        ".hword 0xf000, 0xe320, 0x86c0, 0xebfe\n"
        ".hword 0x0000, 0xe598, 0x10ba, 0xe1d0\n"
        ".hword 0x1001, 0xe281, 0x10ba, 0xe1c0\n"
        ".hword 0xb0b8, 0xe1c0, 0x0001, 0xe3a0\n"
        ".hword 0x9ff0, 0xe8bd, 0x9028, 0xe5c6\n"
        ".hword 0x902c, 0xe586, 0x9030, 0xe5c6\n"
        ".hword 0x0000, 0xe598, 0x10fa, 0xe1d0\n"
        ".hword 0x1034, 0xe586, 0x0181, 0xe080\n"
        ".hword 0x1001, 0xe3a0, 0x0018, 0xe590\n"
        ".hword 0x325b, 0xebff, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0xffe3, 0xeaff\n"
        ".hword 0x7a60, 0x0044, 0xfc0c, 0x0049\n"
    );
};

// DECOMP_FUNC(0x0031f6d0, 768)
extern "C" __attribute__((naked)) void ui_func_0031f6d0() {
    asm volatile(
        ".arm\n"
        ".hword 0x41f0, 0xe92d, 0x4000, 0xe1a0\n"
        ".hword 0x6001, 0xe1a0, 0x82dc, 0xe59f\n"
        ".hword 0x72dc, 0xe59f, 0x8b02, 0xed2d\n"
        ".hword 0x0038, 0xe590, 0x8ab5, 0xed9f\n"
        ".hword 0x1098, 0xe0c0, 0x5fc0, 0xe040\n"
        ".hword 0x0000, 0xe355, 0x0084, 0xda00\n"
        ".hword 0x0c01, 0xe287, 0x1e12, 0xe287\n"
        ".hword 0x0a04, 0xec90, 0x0002, 0xe1a0\n"
        ".hword 0x0a04, 0xec81, 0x1005, 0xe1a0\n"
        ".hword 0x9a8f, 0xebfe, 0x1a10, 0xee00\n"
        ".hword 0x11d8, 0xe1d6, 0x5a90, 0xee00\n"
        ".hword 0x0001, 0xe080, 0x2098, 0xe0c1\n"
        ".hword 0x1ac0, 0xeeb8, 0x0ae0, 0xeef8\n"
        ".hword 0x1fc1, 0xe041, 0x1101, 0xe041\n"
        ".hword 0x1081, 0xe080, 0x0001, 0xe281\n"
        ".hword 0x3098, 0xe0c2, 0x0a20, 0xee81\n"
        ".hword 0x2fc2, 0xe042, 0x2102, 0xe042\n"
        ".hword 0x0082, 0xe080, 0x0100, 0xe084\n"
        ".hword 0x003c, 0xe590, 0x2400, 0xe1a0\n"
        ".hword 0x5800, 0xe1a0, 0xcc22, 0xe1a0\n"
        ".hword 0x2c25, 0xe1a0, 0x50ff, 0xe200\n"
        ".hword 0x3c20, 0xe1a0, 0x5a10, 0xee02\n"
        ".hword 0x3a90, 0xee00, 0xca10, 0xee01\n"
        ".hword 0x2a90, 0xee01, 0x0e11, 0xe287\n"
        ".hword 0x2a42, 0xeeb8, 0x0a60, 0xeef8\n"
        ".hword 0x1a41, 0xeeb8, 0x1a61, 0xeef8\n"
        ".hword 0x2a08, 0xee22, 0x0a88, 0xee60\n"
        ".hword 0x1a08, 0xee21, 0x1a88, 0xee61\n"
        ".hword 0x0a04, 0xecc0, 0x0101, 0xe084\n"
        ".hword 0x003c, 0xe590, 0xc0ff, 0xe200\n"
        ".hword 0x1400, 0xe1a0, 0x3800, 0xe1a0\n"
        ".hword 0x2c20, 0xe1a0, 0xca10, 0xee02\n"
        ".hword 0x1c21, 0xe1a0, 0x3c23, 0xe1a0\n"
        ".hword 0x2a90, 0xee00, 0x1a10, 0xee01\n"
        ".hword 0x3a90, 0xee01, 0x2a42, 0xeeb8\n"
        ".hword 0x0c01, 0xe287, 0x0a60, 0xeef8\n"
        ".hword 0x1a41, 0xeeb8, 0x1a61, 0xeef8\n"
        ".hword 0x2a08, 0xee22, 0x0a88, 0xee60\n"
        ".hword 0x1a08, 0xee21, 0x1a88, 0xee61\n"
        ".hword 0x0a04, 0xecc0, 0x0a6e, 0xeddf\n"
        ".hword 0x1a40, 0xed97, 0x0ac0, 0xee70\n"
        ".hword 0x1a20, 0xee21, 0x1a40, 0xed87\n"
        ".hword 0x1a41, 0xed97, 0x1a20, 0xee21\n"
        ".hword 0x1a41, 0xed87, 0x1a42, 0xed97\n"
        ".hword 0x1a20, 0xee21, 0x1a42, 0xed87\n"
        ".hword 0x1a43, 0xed97, 0x0a20, 0xee61\n"
        ".hword 0x0a43, 0xedc7, 0x0a44, 0xedd7\n"
        ".hword 0x1e12, 0xe287, 0x0e11, 0xe287\n"
        ".hword 0x0a80, 0xee60, 0x0a44, 0xedc7\n"
        ".hword 0x0a45, 0xedd7, 0x0a80, 0xee60\n"
        ".hword 0x0a45, 0xedc7, 0x0a46, 0xedd7\n"
        ".hword 0x0a80, 0xee60, 0x0a46, 0xedc7\n"
        ".hword 0x0a47, 0xedd7, 0x0a80, 0xee20\n"
        ".hword 0x0a47, 0xed87, 0x0a40, 0xed97\n"
        ".hword 0x0a44, 0xedd7, 0x0a20, 0xee30\n"
        ".hword 0x0a40, 0xed87, 0x0a41, 0xed97\n"
        ".hword 0x0a45, 0xedd7, 0x0a20, 0xee30\n"
        ".hword 0x0a41, 0xed87, 0x0a42, 0xed97\n"
        ".hword 0x0a46, 0xedd7, 0x0a20, 0xee30\n"
        ".hword 0x0a42, 0xed87, 0x0a47, 0xedd7\n"
        ".hword 0x0a43, 0xed97, 0x0a20, 0xee30\n"
        ".hword 0x0a43, 0xed87, 0x100c, 0xe891\n"
        ".hword 0x112c, 0xe597, 0x111c, 0xe587\n"
        ".hword 0x100c, 0xe880, 0x0a40, 0xed97\n"
        ".hword 0x0a44, 0xedd7, 0x0a20, 0xee20\n"
        ".hword 0x0a40, 0xed87, 0x0a41, 0xed97\n"
        ".hword 0x0a45, 0xedd7, 0x0a20, 0xee20\n"
        ".hword 0x0a41, 0xed87, 0x0a42, 0xed97\n"
        ".hword 0x0a46, 0xedd7, 0x0a20, 0xee20\n"
        ".hword 0x0a42, 0xed87, 0x0a47, 0xedd7\n"
        ".hword 0x0a43, 0xed97, 0x0a20, 0xee20\n"
        ".hword 0x0a43, 0xed87, 0x8b02, 0xecbd\n"
        ".hword 0x81f0, 0xe8bd, 0x01d8, 0xe1d6\n"
        ".hword 0x0100, 0xe084, 0x003c, 0xe590\n"
        ".hword 0x1400, 0xe1a0, 0x3800, 0xe1a0\n"
        ".hword 0xcc21, 0xe1a0, 0x2c20, 0xe1a0\n"
        ".hword 0x1c23, 0xe1a0, 0x2a10, 0xee00\n"
        ".hword 0xca90, 0xee00, 0x30ff, 0xe200\n"
        ".hword 0x1a90, 0xee01, 0x3a10, 0xee01\n"
        ".hword 0x0f46, 0xe287, 0x2a40, 0xeef8\n"
        ".hword 0x0a60, 0xeeb8, 0x2a61, 0xeeb8\n"
        ".hword 0x1a41, 0xeef8, 0x0a88, 0xee62\n"
        ".hword 0x0a08, 0xee20, 0x1a08, 0xee22\n"
        ".hword 0x1a88, 0xee61, 0x0a44, 0xedc7\n"
        ".hword 0x0a45, 0xed87, 0x1a02, 0xec80\n"
        ".hword 0x0a44, 0xedd7, 0x0a40, 0xed97\n"
        ".hword 0x0a20, 0xee20, 0x0a40, 0xed87\n"
        ".hword 0x0a41, 0xed97, 0x0a45, 0xedd7\n"
        ".hword 0x0a20, 0xee20, 0x0a41, 0xed87\n"
        ".hword 0x0a42, 0xed97, 0x0a46, 0xedd7\n"
        ".hword 0x0a20, 0xee20, 0x0a42, 0xed87\n"
        ".hword 0x0a47, 0xedd7, 0x0a43, 0xed97\n"
        ".hword 0x0a20, 0xee20, 0x0a43, 0xed87\n"
        ".hword 0x8b02, 0xecbd, 0x81f0, 0xe8bd\n"
        ".hword 0xaaab, 0x2aaa, 0xa81c, 0x004e\n"
        ".hword 0x8081, 0x3b80, 0x0000, 0x3f80\n"
    );
};

// DECOMP_FUNC(0x001197c4, 772)
extern "C" __attribute__((naked)) void engine_func_001197c4() {
    asm volatile(
        ".arm\n"
        ".hword 0x47f0, 0xe92d, 0x52f4, 0xe59f\n"
        ".hword 0x7008, 0xe285, 0x0007, 0xe1a0\n"
        ".hword 0xa8b3, 0xeb06, 0x0015, 0xe5d5\n"
        ".hword 0x0000, 0xe350, 0x00a6, 0x0a00\n"
        ".hword 0x0004, 0xe595, 0x8000, 0xe3a0\n"
        ".hword 0x4008, 0xe1a0, 0x0000, 0xe350\n"
        ".hword 0x009e, 0xda00, 0x0005, 0xe1a0\n"
        ".hword 0x0000, 0xe354, 0x2004, 0xa590\n"
        ".hword 0x0004, 0xa152, 0x0095, 0xda00\n"
        ".hword 0x6000, 0xe595, 0x0000, 0xe354\n"
        ".hword 0x0007, 0xda00, 0x0001, 0xe314\n"
        ".hword 0x6070, 0x1596, 0x00c4, 0xe1b0\n"
        ".hword 0x0003, 0x0a00, 0x1070, 0xe596\n"
        ".hword 0x0001, 0xe250, 0x6070, 0xe591\n"
        ".hword 0xfffb, 0x1aff, 0x0000, 0xe356\n"
        ".hword 0x0088, 0x0a00, 0x0090, 0xe596\n"
        ".hword 0x0040, 0xe310, 0x0085, 0x0a00\n"
        ".hword 0x0038, 0xe596, 0x6428, 0xeb00\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0045, 0x0a00, 0x0090, 0xe596\n"
        ".hword 0x0002, 0xe310, 0x0002, 0x0380\n"
        ".hword 0x0090, 0x0586, 0x0075, 0x0a00\n"
        ".hword 0x1016, 0xe5d5, 0x0000, 0xe351\n"
        ".hword 0x0078, 0x0a00, 0x0020, 0xe310\n"
        ".hword 0x0015, 0x0a00, 0x0078, 0xe596\n"
        ".hword 0x1084, 0xe596, 0x0000, 0xe151\n"
        ".hword 0x000b, 0xca00, 0x1a10, 0xee00\n"
        ".hword 0x0a90, 0xee00, 0x1a25, 0xed96\n"
        ".hword 0x0038, 0xe596, 0x0ac0, 0xeeb8\n"
        ".hword 0x0ae0, 0xeef8, 0x1a20, 0xeec0\n"
        ".hword 0x0a81, 0xee21, 0xb672, 0xeb00\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0x0060, 0xea00, 0x0038, 0xe596\n"
        ".hword 0x0a25, 0xed96, 0xb66c, 0xeb00\n"
        ".hword 0x0090, 0xe596, 0x0020, 0xe3c0\n"
        ".hword 0x0023, 0xea00, 0x0010, 0xe310\n"
        ".hword 0x005b, 0x0a00, 0x1078, 0xe596\n"
        ".hword 0x2084, 0xe596, 0x0001, 0xe152\n"
        ".hword 0x000c, 0xca00, 0x2a10, 0xee01\n"
        ".hword 0x1a90, 0xee00, 0x0a25, 0xed96\n"
        ".hword 0x0038, 0xe596, 0x1ac1, 0xeef8\n"
        ".hword 0x0ae0, 0xeef8, 0x1aa0, 0xee81\n"
        ".hword 0x0a40, 0xeef0, 0x0ac1, 0xee00\n"
        ".hword 0xb659, 0xeb00, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0x0047, 0xea00\n"
        ".hword 0x0010, 0xe3c0, 0x0c01, 0xe310\n"
        ".hword 0x0090, 0xe586, 0x0005, 0x0a00\n"
        ".hword 0x0038, 0xe596, 0x1001, 0xe3a0\n"
        ".hword 0x02aa, 0xeb01, 0x0090, 0xe596\n"
        ".hword 0x0c01, 0xe3c0, 0x0006, 0xea00\n"
        ".hword 0x0080, 0xe310, 0x003b, 0x0a00\n"
        ".hword 0x0038, 0xe596, 0x1002, 0xe3a0\n"
        ".hword 0x02a2, 0xeb01, 0x0090, 0xe596\n"
        ".hword 0x0080, 0xe3c0, 0x0090, 0xe586\n"
        ".hword 0x0034, 0xea00, 0x0038, 0xe596\n"
        ".hword 0x0004, 0xe5d0, 0x0002, 0xe350\n"
        ".hword 0x0030, 0x0a00, 0x0090, 0xe596\n"
        ".hword 0x0002, 0xe310, 0x002d, 0x0a00\n"
        ".hword 0x108c, 0xe596, 0x0000, 0xe351\n"
        ".hword 0x0004, 0x0a00, 0x0001, 0xe351\n"
        ".hword 0x0002, 0x03c0, 0x0c02, 0x0380\n"
        ".hword 0xffef, 0x0aff, 0x0025, 0xea00\n"
        ".hword 0x0008, 0xe285, 0x9000, 0xe1a0\n"
        ".hword 0xa839, 0xeb06, 0x3000, 0xe595\n"
        ".hword 0x0006, 0xe1a0, 0x1005, 0xe1a0\n"
        ".hword 0x2003, 0xe1b0, 0x0010, 0x0a00\n"
        ".hword 0x0000, 0xe153, 0x002b, 0x1a00\n"
        ".hword 0x0000, 0xe352, 0x000c, 0x0a00\n"
        ".hword 0x0000, 0xe152, 0x0031, 0x1a00\n"
        ".hword 0x2074, 0xe590, 0x0000, 0xe352\n"
        ".hword 0x0028, 0x0a00, 0x3070, 0xe590\n"
        ".hword 0x3070, 0xe582, 0x0070, 0xe596\n"
        ".hword 0x0000, 0xe350, 0x2074, 0x1583\n"
        ".hword 0x0004, 0xe591, 0x0001, 0xe240\n"
        ".hword 0x0004, 0xe585, 0x006c, 0xe596\n"
        ".hword 0x0000, 0xe350, 0xaa4e, 0x1b06\n"
        ".hword 0x0038, 0xe596, 0x0000, 0xe350\n"
        ".hword 0x8efb, 0x1b06, 0x0006, 0xe1a0\n"
        ".hword 0xf000, 0xe320, 0xaa48, 0xeb06\n"
        ".hword 0x0009, 0xe1a0, 0xf000, 0xe320\n"
        ".hword 0xa7f6, 0xeb06, 0x4001, 0xe244\n"
        ".hword 0x0016, 0xe5d5, 0x0000, 0xe350\n"
        ".hword 0x0002, 0x0a00, 0x0084, 0xe596\n"
        ".hword 0x0001, 0xe280, 0x0084, 0xe586\n"
        ".hword 0x0004, 0xe595, 0x4001, 0xe284\n"
        ".hword 0x0004, 0xe150, 0xff60, 0xcaff\n"
        ".hword 0x0016, 0xe5d5, 0x0000, 0xe350\n"
        ".hword 0x8016, 0x15c5, 0x0007, 0xe1a0\n"
        ".hword 0x47f0, 0xe8bd, 0xa7e5, 0xea06\n"
        ".hword 0x3070, 0xe593, 0x0000, 0xe353\n"
        ".hword 0xffce, 0x1aff, 0xffde, 0xeaff\n"
        ".hword 0x0070, 0xe596, 0x0000, 0xe350\n"
        ".hword 0x8074, 0x1580, 0x0000, 0x1581\n"
        ".hword 0x8000, 0x0581, 0xffd5, 0xeaff\n"
        ".hword 0x2070, 0xe592, 0x0000, 0xe352\n"
        ".hword 0xffc8, 0x1aff, 0xffd1, 0xeaff\n"
        ".hword 0x3154, 0x004e\n"
    );
};

// DECOMP_FUNC(0x00205628, 772)
extern "C" __attribute__((naked)) void engine_func_00205628() {
    asm volatile(
        ".arm\n"
        ".hword 0x02f8, 0xe59f, 0x41f0, 0xe92d\n"
        ".hword 0x5000, 0xe590, 0x0020, 0xe595\n"
        ".hword 0x0004, 0xe350, 0x001d, 0x0a00\n"
        ".hword 0x0006, 0xe350, 0x0032, 0x0a00\n"
        ".hword 0x0008, 0xe350, 0x002f, 0x1a00\n"
        ".hword 0x0b02, 0xe285, 0x0f9b, 0xe280\n"
        ".hword 0x4000, 0xe3a0, 0x8000, 0xe1a0\n"
        ".hword 0x6564, 0xeb02, 0x0000, 0xe350\n"
        ".hword 0x006d, 0xda00, 0x0004, 0xe085\n"
        ".hword 0x0678, 0xe5d0, 0x0000, 0xe350\n"
        ".hword 0x0063, 0x0a00, 0x0b02, 0xe285\n"
        ".hword 0x0f82, 0xe280, 0x1004, 0xe1a0\n"
        ".hword 0x5000, 0xe1a0, 0x4fb1, 0xeb02\n"
        ".hword 0x1000, 0xe3a0, 0x0005, 0xe1a0\n"
        ".hword 0x6088, 0xeb02, 0x1004, 0xe1a0\n"
        ".hword 0x0008, 0xe1a0, 0x4fab, 0xeb02\n"
        ".hword 0x0008, 0xe1a0, 0x41f0, 0xe8bd\n"
        ".hword 0x1000, 0xe3a0, 0x6081, 0xea02\n"
        ".hword 0x0b02, 0xe285, 0x00dc, 0xe280\n"
        ".hword 0x4000, 0xe3a0, 0x6000, 0xe1a0\n"
        ".hword 0x654a, 0xeb02, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x000d, 0xda00\n"
        ".hword 0x0004, 0xe085, 0x0678, 0xe5d0\n"
        ".hword 0x0000, 0xe350, 0x0003, 0x0a00\n"
        ".hword 0x1004, 0xe1a0, 0x0006, 0xe1a0\n"
        ".hword 0x41f0, 0xe8bd, 0x4f97, 0xea02\n"
        ".hword 0x4001, 0xe284, 0x0006, 0xe1a0\n"
        ".hword 0x653c, 0xeb02, 0x0004, 0xe150\n"
        ".hword 0xf000, 0xe320, 0xfff1, 0xcaff\n"
        ".hword 0x81f0, 0xe8bd, 0x0b02, 0xe285\n"
        ".hword 0x0f69, 0xe280, 0x7000, 0xe3a0\n"
        ".hword 0x8000, 0xe1a0, 0x6672, 0xeb02\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0xfff6, 0xdaff, 0x4000, 0xe3a0\n"
        ".hword 0x0008, 0xe1a0, 0x652d, 0xeb02\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0028, 0xda00, 0x6107, 0xe084\n"
        ".hword 0x0186, 0xe085, 0x0c07, 0xe280\n"
        ".hword 0x03bc, 0xe1d0, 0x0000, 0xe350\n"
        ".hword 0x001c, 0x0a00, 0x1004, 0xe1a0\n"
        ".hword 0x0008, 0xe1a0, 0x4f79, 0xeb02\n"
        ".hword 0x1007, 0xe1a0, 0x0008, 0xe1a0\n"
        ".hword 0x6050, 0xeb02, 0x002c, 0xe595\n"
        ".hword 0x0000, 0xe350, 0x000a, 0x0a00\n"
        ".hword 0x0001, 0xe350, 0xffdf, 0x1aff\n"
        ".hword 0x000c, 0xe356, 0xffdd, 0xbaff\n"
        ".hword 0x1004, 0xe1a0, 0x0d25, 0xe285\n"
        ".hword 0x4f6c, 0xeb02, 0x1004, 0xe247\n"
        ".hword 0x0d25, 0xe285, 0x41f0, 0xe8bd\n"
        ".hword 0x6042, 0xea02, 0x000c, 0xe356\n"
        ".hword 0xffd4, 0xaaff, 0x1004, 0xe1a0\n"
        ".hword 0x0d25, 0xe285, 0x4f63, 0xeb02\n"
        ".hword 0x1007, 0xe1a0, 0x0d25, 0xe285\n"
        ".hword 0x41f0, 0xe8bd, 0x6039, 0xea02\n"
        ".hword 0x4001, 0xe284, 0x0008, 0xe1a0\n"
        ".hword 0x6504, 0xeb02, 0x0004, 0xe150\n"
        ".hword 0xf000, 0xe320, 0xffd6, 0xcaff\n"
        ".hword 0x7001, 0xe287, 0x0008, 0xe1a0\n"
        ".hword 0x663d, 0xeb02, 0x0007, 0xe150\n"
        ".hword 0xf000, 0xe320, 0xffca, 0xcaff\n"
        ".hword 0x81f0, 0xe8bd, 0x4001, 0xe284\n"
        ".hword 0x0008, 0xe1a0, 0x64f7, 0xeb02\n"
        ".hword 0x0004, 0xe150, 0xf000, 0xe320\n"
        ".hword 0xff91, 0xcaff, 0x7001, 0xe3a0\n"
        ".hword 0x0008, 0xe1a0, 0x6630, 0xeb02\n"
        ".hword 0x0001, 0xe350, 0xf000, 0xe320\n"
        ".hword 0xffb4, 0xdaff, 0x4000, 0xe3a0\n"
        ".hword 0x0008, 0xe1a0, 0x64eb, 0xeb02\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x002d, 0xda00, 0x0107, 0xe084\n"
        ".hword 0x6004, 0xe240, 0x0186, 0xe085\n"
        ".hword 0x0c07, 0xe280, 0x03bc, 0xe1d0\n"
        ".hword 0x0000, 0xe350, 0x0020, 0x0a00\n"
        ".hword 0x1004, 0xe1a0, 0x0008, 0xe1a0\n"
        ".hword 0x4f36, 0xeb02, 0x1007, 0xe1a0\n"
        ".hword 0x0008, 0xe1a0, 0x600d, 0xeb02\n"
        ".hword 0x002c, 0xe595, 0x0000, 0xe350\n"
        ".hword 0x000c, 0x0a00, 0x0001, 0xe350\n"
        ".hword 0xff9c, 0x1aff, 0x000c, 0xe356\n"
        ".hword 0xff9a, 0xbaff, 0x0b02, 0xe285\n"
        ".hword 0x1004, 0xe1a0, 0x0f82, 0xe280\n"
        ".hword 0x4000, 0xe1a0, 0x4f27, 0xeb02\n"
        ".hword 0x1003, 0xe247, 0x0004, 0xe1a0\n"
        ".hword 0x41f0, 0xe8bd, 0x5ffd, 0xea02\n"
        ".hword 0x000c, 0xe356, 0xff8f, 0xaaff\n"
        ".hword 0x0b02, 0xe285, 0x1004, 0xe1a0\n"
        ".hword 0x0f82, 0xe280, 0x4000, 0xe1a0\n"
        ".hword 0x4f1c, 0xeb02, 0x1007, 0xe1a0\n"
        ".hword 0x0004, 0xe1a0, 0x41f0, 0xe8bd\n"
        ".hword 0x5ff2, 0xea02, 0x4001, 0xe284\n"
        ".hword 0x0008, 0xe1a0, 0x64bd, 0xeb02\n"
        ".hword 0x0004, 0xe150, 0xf000, 0xe320\n"
        ".hword 0xffd1, 0xcaff, 0x7001, 0xe287\n"
        ".hword 0x0008, 0xe1a0, 0x65f6, 0xeb02\n"
        ".hword 0x0007, 0xe150, 0xf000, 0xe320\n"
        ".hword 0xffc5, 0xcaff, 0x81f0, 0xe8bd\n"
        ".hword 0xdcf0, 0x0043\n"
    );
};

// DECOMP_FUNC(0x0034f30c, 772)
extern "C" __attribute__((naked)) void engine_func_0034f30c() {
    asm volatile(
        ".arm\n"
        ".hword 0x4fff, 0xe92d, 0x5001, 0xe1a0\n"
        ".hword 0x6002, 0xe1a0, 0x7003, 0xe1a0\n"
        ".hword 0x8b04, 0xed2d, 0xd02c, 0xe24d\n"
        ".hword 0x0008, 0xe591, 0x9070, 0xe59d\n"
        ".hword 0x0006, 0xe350, 0x0014, 0xe591\n"
        ".hword 0xa001, 0x03a0, 0xa002, 0x13a0\n"
        ".hword 0x0020, 0xe58d, 0xb018, 0xe591\n"
        ".hword 0x0c02, 0xe350, 0x0b01, 0xc3a0\n"
        ".hword 0x0000, 0xc589, 0x0003, 0xca00\n"
        ".hword 0x0c01, 0xe350, 0x0c02, 0xc3a0\n"
        ".hword 0x0c01, 0xd3a0, 0x0000, 0xe589\n"
        ".hword 0x0002, 0xe35a, 0x0004, 0x0589\n"
        ".hword 0x0c02, 0xe35b, 0x0b01, 0xc3a0\n"
        ".hword 0x001c, 0xc58d, 0x0003, 0xca00\n"
        ".hword 0x0c01, 0xe35b, 0x0c02, 0xc3a0\n"
        ".hword 0x0c01, 0xd3a0, 0x001c, 0xe58d\n"
        ".hword 0x0000, 0xe35a, 0x4000, 0xe3a0\n"
        ".hword 0x0077, 0xda00, 0x0080, 0xe080\n"
        ".hword 0x0024, 0xe58d, 0x00cb, 0xe1a0\n"
        ".hword 0x0028, 0xe58d, 0x0020, 0xe59d\n"
        ".hword 0x8a92, 0xed9f, 0x8a92, 0xeddf\n"
        ".hword 0x9a92, 0xed9f, 0x80c0, 0xe1a0\n"
        ".hword 0x0001, 0xea00, 0x0001, 0xe354\n"
        ".hword 0x0032, 0x0a00, 0x003c, 0xe59d\n"
        ".hword 0x1000, 0xe599, 0x2024, 0xe59d\n"
        ".hword 0x0004, 0xe590, 0x0291, 0xe00c\n"
        ".hword 0x1000, 0xe590, 0x2080, 0xe3a0\n"
        ".hword 0x3000, 0xe591, 0x100c, 0xe1a0\n"
        ".hword 0xff33, 0xe12f, 0x0000, 0xe350\n"
        ".hword 0x0104, 0xe786, 0x0070, 0x0a00\n"
        ".hword 0x1000, 0xe599, 0x2024, 0xe59d\n"
        ".hword 0x0291, 0xe001, 0xd1ce, 0xebfd\n"
        ".hword 0x0008, 0xe595, 0x0004, 0xe350\n"
        ".hword 0x0005, 0x1350, 0x0027, 0x0a00\n"
        ".hword 0x0002, 0xe350, 0x0003, 0x1350\n"
        ".hword 0x0035, 0x0a00, 0x1104, 0xe796\n"
        ".hword 0x31d8, 0xe59f, 0x21d0, 0xe59f\n"
        ".hword 0x1014, 0xe58d, 0x300c, 0xe58d\n"
        ".hword 0x1020, 0xe59d, 0x0000, 0xe3a0\n"
        ".hword 0x0018, 0xe58d, 0x2010, 0xe58d\n"
        ".hword 0x0803, 0xe88d, 0x0284, 0xe087\n"
        ".hword 0x1000, 0xe599, 0x201c, 0xe59d\n"
        ".hword 0x3000, 0xe3a0, 0xacd7, 0xebfb\n"
        ".hword 0x0024, 0xe595, 0x0001, 0xe350\n"
        ".hword 0x0037, 0x0a00, 0x0002, 0xe350\n"
        ".hword 0x0a68, 0x0eb0, 0x0284, 0x0087\n"
        ".hword 0x0039, 0x0a00, 0x0003, 0xe350\n"
        ".hword 0x0a49, 0x0eb0, 0x0284, 0x0087\n"
        ".hword 0x0035, 0x0a00, 0x0035, 0xea00\n"
        ".hword 0x0008, 0xe595, 0x0004, 0xe350\n"
        ".hword 0x0005, 0x1350, 0x0002, 0x0a00\n"
        ".hword 0x0002, 0xe350, 0x0003, 0x1350\n"
        ".hword 0xffc5, 0x1aff, 0x0000, 0xe596\n"
        ".hword 0x0004, 0xe586, 0xffd3, 0xeaff\n"
        ".hword 0x1104, 0xe796, 0x3144, 0xe59f\n"
        ".hword 0x213c, 0xe59f, 0x0000, 0xe3a0\n"
        ".hword 0x300c, 0xe58d, 0x0018, 0xe58d\n"
        ".hword 0x1014, 0xe58d, 0x2010, 0xe58d\n"
        ".hword 0x0901, 0xe88d, 0x0498, 0xe003\n"
        ".hword 0x1000, 0xe599, 0x201c, 0xe59d\n"
        ".hword 0x0284, 0xe087, 0xacb3, 0xebfb\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0xffd8, 0xeaff, 0xc028, 0xe59d\n"
        ".hword 0x10fc, 0xe59f, 0x00fc, 0xe59f\n"
        ".hword 0x2104, 0xe796, 0xe028, 0xe59d\n"
        ".hword 0x3000, 0xe3a0, 0x049c, 0xe00c\n"
        ".hword 0x00fc, 0xe1cd, 0x21f4, 0xe1cd\n"
        ".hword 0x0020, 0xe59d, 0x1004, 0xe28d\n"
        ".hword 0xc000, 0xe58d, 0x4001, 0xe881\n"
        ".hword 0x0284, 0xe087, 0x1000, 0xe599\n"
        ".hword 0x201c, 0xe59d, 0xac9f, 0xebfb\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0xffc4, 0xeaff, 0x0a48, 0xeeb0\n"
        ".hword 0x0284, 0xe087, 0x0a05, 0xed80\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0x0000, 0xea00, 0x0a05, 0xed80\n"
        ".hword 0x4001, 0xe284, 0x000a, 0xe154\n"
        ".hword 0xff91, 0xbaff, 0x0008, 0xe595\n"
        ".hword 0x1001, 0xe3a0, 0x2e41, 0xe3a0\n"
        ".hword 0x0001, 0xe350, 0x0003, 0x1350\n"
        ".hword 0x0005, 0x1350, 0x000e, 0x0a00\n"
        ".hword 0xc03c, 0xe59d, 0x0b01, 0xe3a0\n"
        ".hword 0x3000, 0xe3a0, 0x0028, 0xe58c\n"
        ".hword 0x003c, 0xe59d, 0x202c, 0xe580\n"
        ".hword 0x003c, 0xe59d, 0x3034, 0xe580\n"
        ".hword 0x003c, 0xe59d, 0x1038, 0xe580\n"
        ".hword 0x0001, 0xe3a0, 0xd02c, 0xe28d\n"
        ".hword 0x8b04, 0xecbd, 0xd010, 0xe28d\n"
        ".hword 0x8ff0, 0xe8bd, 0xc03c, 0xe59d\n"
        ".hword 0x3b01, 0xe3a0, 0x0000, 0xe3a0\n"
        ".hword 0x2028, 0xe58c, 0x203c, 0xe59d\n"
        ".hword 0x302c, 0xe582, 0x203c, 0xe59d\n"
        ".hword 0x1034, 0xe582, 0x103c, 0xe59d\n"
        ".hword 0x0038, 0xe581, 0xffef, 0xeaff\n"
        ".hword 0x0000, 0x42b4, 0x0000, 0x4334\n"
        ".hword 0x0000, 0x4387, 0x1401, 0x0000\n"
        ".hword 0x6754, 0x0000\n"
    );
};

// DECOMP_FUNC(0x002108d0, 788)
extern "C" __attribute__((naked)) void ui_func_002108d0() {
    asm volatile(
        ".arm\n"
        ".hword 0x47f0, 0xe92d, 0x02f4, 0xe59f\n"
        ".hword 0x8b04, 0xed2d, 0xd008, 0xe24d\n"
        ".hword 0x4004, 0xe590, 0x6b01, 0xe284\n"
        ".hword 0x04c4, 0xe5d4, 0x0000, 0xe350\n"
        ".hword 0x00ad, 0x0a00, 0x72d8, 0xe59f\n"
        ".hword 0x0000, 0xe597, 0xcca9, 0xeb02\n"
        ".hword 0x5000, 0xe597, 0x1000, 0xe3a0\n"
        ".hword 0x0001, 0xe3a0, 0xd59a, 0xeb02\n"
        ".hword 0x5a01, 0xe285, 0x5f93, 0xe285\n"
        ".hword 0x8000, 0xe3a0, 0x1000, 0xe595\n"
        ".hword 0x2001, 0xe281, 0x3101, 0xe085\n"
        ".hword 0x1008, 0xe593, 0x3102, 0xe085\n"
        ".hword 0x2000, 0xe585, 0x0008, 0xe583\n"
        ".hword 0x2018, 0xe5d5, 0x0000, 0xe352\n"
        ".hword 0x0000, 0x0151, 0x0002, 0x0a00\n"
        ".hword 0x101c, 0xe595, 0xff31, 0xe12f\n"
        ".hword 0x8018, 0xe5c5, 0x0010, 0xe594\n"
        ".hword 0x0000, 0xe350, 0x0001, 0x1350\n"
        ".hword 0x0002, 0x0a00, 0x0002, 0xe350\n"
        ".hword 0x0003, 0x1350, 0x0077, 0x1a00\n"
        ".hword 0xf000, 0xe320, 0x00f3, 0xebfe\n"
        ".hword 0x00c5, 0xe5d6, 0x0000, 0xe350\n"
        ".hword 0x0072, 0x0a00, 0x04c8, 0xe5d4\n"
        ".hword 0x0001, 0xe350, 0x0fdf, 0xe284\n"
        ".hword 0x0020, 0x0a00, 0x26da, 0xeb02\n"
        ".hword 0x0b01, 0xe284, 0x0008, 0xe280\n"
        ".hword 0x26d7, 0xeb02, 0x00c5, 0xe5d6\n"
        ".hword 0x0000, 0xe350, 0x00cb, 0x15d6\n"
        ".hword 0x0000, 0x1350, 0x0065, 0x0a00\n"
        ".hword 0x03a8, 0xe594, 0x05fe, 0xe350\n"
        ".hword 0x0062, 0xba00, 0x101d, 0xe3a0\n"
        ".hword 0x0012, 0xe3a0, 0xbb3f, 0xeb02\n"
        ".hword 0x155c, 0xe5d4, 0x8a7f, 0xed9f\n"
        ".hword 0x8a7f, 0xeddf, 0x9a7f, 0xed9f\n"
        ".hword 0x0000, 0xe351, 0x5c05, 0xe284\n"
        ".hword 0x6006, 0xe3a0, 0x001f, 0x0a00\n"
        ".hword 0x0140, 0xe88d, 0x0a48, 0xeeb0\n"
        ".hword 0x20fa, 0xe1d0, 0x10f8, 0xe1d0\n"
        ".hword 0x0558, 0xe594, 0x3015, 0xe3a0\n"
        ".hword 0x9bc7, 0xeb02, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0x0025, 0xea00\n"
        ".hword 0xf000, 0xe320, 0xb956, 0xeb02\n"
        ".hword 0x9000, 0xe1a0, 0x0fdf, 0xe284\n"
        ".hword 0xb950, 0xeb02, 0x5000, 0xe1a0\n"
        ".hword 0xa010, 0xe3a0, 0x3009, 0xe1a0\n"
        ".hword 0x2000, 0xe3a0, 0x1012, 0xe3a0\n"
        ".hword 0x0002, 0xe3a0, 0x0420, 0xe88d\n"
        ".hword 0xba84, 0xeb02, 0x3009, 0xe1a0\n"
        ".hword 0x2001, 0xe3a0, 0x1012, 0xe3a0\n"
        ".hword 0x0002, 0xe3a0, 0x0420, 0xe88d\n"
        ".hword 0xba7e, 0xeb02, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0xffcc, 0xeaff\n"
        ".hword 0x1054, 0xe5d5, 0x20fa, 0xe1d0\n"
        ".hword 0x0000, 0xe351, 0x001d, 0x0a00\n"
        ".hword 0x00f8, 0xe1d0, 0x2a90, 0xee00\n"
        ".hword 0x2a48, 0xeeb0, 0x0a10, 0xee00\n"
        ".hword 0x1a68, 0xeef0, 0x1a49, 0xeeb0\n"
        ".hword 0x14cc, 0xe594, 0x0ae0, 0xeef8\n"
        ".hword 0x2e4d, 0xe284, 0x0ac0, 0xeeb8\n"
        ".hword 0x0003, 0xe3a0, 0xb732, 0xeb02\n"
        ".hword 0x101e, 0xe3a0, 0x0012, 0xe3a0\n"
        ".hword 0xbb04, 0xeb02, 0x105c, 0xe5d5\n"
        ".hword 0x0000, 0xe351, 0x0011, 0x0a00\n"
        ".hword 0x1001, 0xe3a0, 0x1004, 0xe58d\n"
        ".hword 0x6000, 0xe58d, 0x0a48, 0xeeb0\n"
        ".hword 0x20fa, 0xe1d0, 0x10f8, 0xe1d0\n"
        ".hword 0x0558, 0xe594, 0x3015, 0xe3a0\n"
        ".hword 0x9b8f, 0xeb02, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0x0015, 0xea00\n"
        ".hword 0x10f8, 0xe1d0, 0x0e4d, 0xe284\n"
        ".hword 0x8d43, 0xebff, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0xffe7, 0xeaff\n"
        ".hword 0x1054, 0xe5d5, 0x20fa, 0xe1d0\n"
        ".hword 0x0001, 0xe351, 0x0025, 0x0a00\n"
        ".hword 0x00f8, 0xe1d0, 0x2a90, 0xee00\n"
        ".hword 0x2a48, 0xeeb0, 0x0a10, 0xee00\n"
        ".hword 0x1a68, 0xeef0, 0x1a49, 0xeeb0\n"
        ".hword 0x14cc, 0xe594, 0x0ae0, 0xeef8\n"
        ".hword 0x2e51, 0xe284, 0x0ac0, 0xeeb8\n"
        ".hword 0x0003, 0xe3a0, 0xb70a, 0xeb02\n"
        ".hword 0x0000, 0xe597, 0x4a01, 0xe280\n"
        ".hword 0x4f93, 0xe284, 0x0000, 0xe594\n"
        ".hword 0x1100, 0xe084, 0x0001, 0xe240\n"
        ".hword 0x1008, 0xe591, 0x0000, 0xe584\n"
        ".hword 0x0100, 0xe084, 0x2018, 0xe5d4\n"
        ".hword 0x0008, 0xe590, 0x0000, 0xe352\n"
        ".hword 0x0000, 0x0151, 0x0002, 0x0a00\n"
        ".hword 0x101c, 0xe594, 0xff31, 0xe12f\n"
        ".hword 0x8018, 0xe5c4, 0x0000, 0xe597\n"
        ".hword 0xc3f1, 0xeb02, 0x0000, 0xe597\n"
        ".hword 0xf000, 0xe320, 0xc3c4, 0xeb02\n"
        ".hword 0x0000, 0xe3a0, 0xd008, 0xe28d\n"
        ".hword 0x8b04, 0xecbd, 0x87f0, 0xe8bd\n"
        ".hword 0x10f8, 0xe1d0, 0x0e51, 0xe284\n"
        ".hword 0x8d13, 0xebff, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0xffdf, 0xeaff\n"
        ".hword 0xda28, 0x0043, 0xea00, 0x0044\n"
        ".hword 0x0000, 0x3f80, 0x0000, 0x0000\n"
        ".hword 0x147b, 0x3f6e\n"
    );
};

// DECOMP_FUNC(0x0033f5d4, 788)
extern "C" __attribute__((naked)) void func_0033f5d4() {
    asm volatile(
        ".arm\n"
        ".hword 0x4fff, 0xe92d, 0x0b02, 0xed2d\n"
        ".hword 0xd024, 0xe24d, 0x2010, 0xe590\n"
        ".hword 0x1a18, 0xed9d, 0x1a1a, 0xeddd\n"
        ".hword 0x20be, 0xe1d2, 0x0001, 0xe152\n"
        ".hword 0x00ac, 0xda00, 0x3002, 0xe3a0\n"
        ".hword 0x2ab6, 0xed9f, 0x3101, 0xe083\n"
        ".hword 0x2a06, 0xed8d, 0x2a07, 0xed8d\n"
        ".hword 0x2ab3, 0xed9f, 0x4008, 0xe3a0\n"
        ".hword 0x2a04, 0xed8d, 0x2a05, 0xed8d\n"
        ".hword 0x2024, 0xe590, 0x5010, 0xe3a0\n"
        ".hword 0xc101, 0xe082, 0x10b3, 0xe192\n"
        ".hword 0x60b0, 0xe1dc, 0x300c, 0xe3a0\n"
        ".hword 0x2001, 0xe246, 0xe002, 0xe081\n"
        ".hword 0xc001, 0xe28e, 0x0006, 0xe15c\n"
        ".hword 0x8020, 0xc590, 0x7006, 0xe1a0\n"
        ".hword 0x1004, 0xc3a0, 0x0070, 0xda00\n"
        ".hword 0x9086, 0xe086, 0x9189, 0xe081\n"
        ".hword 0x9009, 0xe798, 0x9a10, 0xee02\n"
        ".hword 0x2ac2, 0xeeb8, 0x0ac2, 0xeeb4\n"
        ".hword 0xfa10, 0xeef1, 0x008f, 0x8a00\n"
        ".hword 0xc086, 0xe086, 0x118c, 0xe081\n"
        ".hword 0x1001, 0xe798, 0x1a10, 0xee02\n"
        ".hword 0x2ac2, 0xeeb8, 0x2a40, 0xeeb4\n"
        ".hword 0xfa10, 0xeef1, 0x0006, 0x1157\n"
        ".hword 0x0011, 0x1a00, 0x618c, 0xe084\n"
        ".hword 0x118c, 0xe798, 0x2006, 0xe798\n"
        ".hword 0x718c, 0xe083, 0x7008, 0xe087\n"
        ".hword 0x2018, 0xe58d, 0x2000, 0xe597\n"
        ".hword 0x6014, 0xe3a0, 0x818c, 0xe085\n"
        ".hword 0xc18c, 0xe086, 0x201c, 0xe58d\n"
        ".hword 0x6020, 0xe590, 0x200c, 0xe086\n"
        ".hword 0xc008, 0xe796, 0xc010, 0xe58d\n"
        ".hword 0x2000, 0xe592, 0x2014, 0xe58d\n"
        ".hword 0x004b, 0xea00, 0x7013, 0xe3e0\n"
        ".hword 0x718c, 0xe087, 0x600f, 0xe3e0\n"
        ".hword 0x7007, 0xe798, 0x918c, 0xe084\n"
        ".hword 0x618c, 0xe086, 0x7a10, 0xee02\n"
        ".hword 0x1007, 0xe041, 0x9008, 0xe089\n"
        ".hword 0xa006, 0xe088, 0x3a00, 0xed99\n"
        ".hword 0x3a00, 0xedda, 0x2ac2, 0xeef8\n"
        ".hword 0x1a10, 0xee02, 0x1017, 0xe3e0\n"
        ".hword 0x118c, 0xe081, 0xb00b, 0xe3e0\n"
        ".hword 0x1001, 0xe798, 0x718c, 0xe08b\n"
        ".hword 0x2ac2, 0xeeb8, 0x918c, 0xe083\n"
        ".hword 0x9008, 0xe089, 0x2a62, 0xee70\n"
        ".hword 0xa007, 0xe088, 0x8007, 0xe3e0\n"
        ".hword 0xb014, 0xe3a0, 0x818c, 0xe088\n"
        ".hword 0xb18c, 0xe08b, 0x0a82, 0xee82\n"
        ".hword 0x2a63, 0xee33, 0x2a06, 0xed8d\n"
        ".hword 0x2a00, 0xedd9, 0x3a00, 0xed9a\n"
        ".hword 0x9003, 0xe3e0, 0xa18c, 0xe085\n"
        ".hword 0x2ac3, 0xee72, 0x918c, 0xe089\n"
        ".hword 0x2a07, 0xedcd, 0xc020, 0xe590\n"
        ".hword 0x2a22, 0xee60, 0xa00c, 0xe08a\n"
        ".hword 0x2008, 0xe08c, 0x3a00, 0xed9a\n"
        ".hword 0x3a00, 0xedd2, 0xb00c, 0xe08b\n"
        ".hword 0xc009, 0xe08c, 0x3a63, 0xee73\n"
        ".hword 0x3a04, 0xedcd, 0x3a00, 0xed9b\n"
        ".hword 0x4a00, 0xed9c, 0x4a44, 0xee33\n"
        ".hword 0x3a02, 0xee20, 0x2a23, 0xee20\n"
        ".hword 0x0a04, 0xee20, 0x3a06, 0xed8d\n"
        ".hword 0x2a07, 0xedcd, 0x2a04, 0xed8d\n"
        ".hword 0x0a05, 0xed8d, 0xc020, 0xe590\n"
        ".hword 0x600c, 0xe086, 0xc007, 0xe08c\n"
        ".hword 0x3a00, 0xedd6, 0x3a83, 0xee33\n"
        ".hword 0x3a06, 0xed8d, 0x3a00, 0xed9c\n"
        ".hword 0x2a22, 0xee73, 0x2a07, 0xedcd\n"
        ".hword 0xc020, 0xe590, 0x6008, 0xe08c\n"
        ".hword 0xc009, 0xe08c, 0x2a00, 0xedd6\n"
        ".hword 0x2a82, 0xee32, 0x2a04, 0xed8d\n"
        ".hword 0x2a00, 0xed9c, 0x0a00, 0xee32\n"
        ".hword 0x0a05, 0xed8d, 0x0000, 0xe351\n"
        ".hword 0x0012, 0xaa00, 0xc08e, 0xe08e\n"
        ".hword 0x1020, 0xe590, 0xe18c, 0xe084\n"
        ".hword 0x318c, 0xe083, 0x3001, 0xe083\n"
        ".hword 0x400e, 0xe791, 0x118c, 0xe791\n"
        ".hword 0xe18c, 0xe085, 0x2014, 0xe3a0\n"
        ".hword 0xc18c, 0xe082, 0x4018, 0xe58d\n"
        ".hword 0x2000, 0xe593, 0x201c, 0xe58d\n"
        ".hword 0x2020, 0xe590, 0x300e, 0xe082\n"
        ".hword 0x3000, 0xe593, 0x3010, 0xe58d\n"
        ".hword 0x200c, 0xe792, 0x2014, 0xe58d\n"
        ".hword 0x0a1e, 0xed9f, 0x2a04, 0xed9d\n"
        ".hword 0x2064, 0xe59d, 0x2a00, 0xee22\n"
        ".hword 0x0000, 0xe352, 0x2a04, 0xed8d\n"
        ".hword 0x2a05, 0xed9d, 0x0a00, 0xee22\n"
        ".hword 0x0a05, 0xed8d, 0x000d, 0x0a00\n"
        ".hword 0x3010, 0xe28d, 0x2018, 0xe28d\n"
        ".hword 0x1a00, 0xed8d, 0x20f4, 0xe1cd\n"
        ".hword 0x0a60, 0xeeb0, 0x1a03, 0xedcd\n"
        ".hword 0x23d4, 0xe1cd, 0xf76c, 0xebff\n"
        ".hword 0xd03c, 0xe28d, 0x8ff0, 0xe8bd\n"
        ".hword 0x6001, 0xe286, 0x000c, 0xe156\n"
        ".hword 0xff64, 0xbaff, 0xffd4, 0xeaff\n"
        ".hword 0x0a60, 0xeeb0, 0x1a00, 0xed8d\n"
        ".hword 0x23d4, 0xe1cd, 0xfa2a, 0xebfb\n"
        ".hword 0xd03c, 0xe28d, 0x8ff0, 0xe8bd\n"
        ".hword 0x0000, 0x0000, 0x0000, 0x42c8\n"
        ".hword 0xd70a, 0x3c23\n"
    );
};

// DECOMP_FUNC(0x00126920, 792)
extern "C" __attribute__((naked)) void ui_func_00126920() {
    asm volatile(
        ".arm\n"
        ".hword 0x4ff0, 0xe92d, 0xb300, 0xe59f\n"
        ".hword 0x8b02, 0xed2d, 0xd03c, 0xe24d\n"
        ".hword 0x5000, 0xe59b, 0x0000, 0xe355\n"
        ".hword 0x00b7, 0x0a00, 0x05ec, 0xe595\n"
        ".hword 0x0005, 0xe350, 0x0003, 0x0a00\n"
        ".hword 0x0002, 0xe350, 0x0003, 0x1350\n"
        ".hword 0x00b1, 0x0a00, 0x00a4, 0xea00\n"
        ".hword 0x0b01, 0xe285, 0x15e8, 0xe595\n"
        ".hword 0x0f65, 0xe280, 0x1e08, 0xeb06\n"
        ".hword 0x4000, 0xe3a0, 0x8aaf, 0xed9f\n"
        ".hword 0x9004, 0xe1a0, 0x7b01, 0xe285\n"
        ".hword 0x6104, 0xe085, 0x0630, 0xe596\n"
        ".hword 0x0000, 0xe350, 0x0093, 0x0a00\n"
        ".hword 0x62a3, 0xeb06, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x008e, 0x0a00\n"
        ".hword 0x8000, 0xe59b, 0xa010, 0xe28d\n"
        ".hword 0x0000, 0xe358, 0x0080, 0x0a00\n"
        ".hword 0x05e4, 0xe598, 0x0000, 0xe350\n"
        ".hword 0x0013, 0x0a00, 0x1dec, 0xeb06\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x000f, 0x0a00, 0x05e4, 0xe598\n"
        ".hword 0x1264, 0xe59f, 0x200a, 0xe1a0\n"
        ".hword 0x0008, 0xe590, 0x1104, 0xe791\n"
        ".hword 0x1da5, 0xeb06, 0x0000, 0xe354\n"
        ".hword 0xf000, 0xe320, 0x0004, 0x1a00\n"
        ".hword 0x1b01, 0xe288, 0x0a06, 0xed9d\n"
        ".hword 0x0a90, 0xedd1, 0x0a20, 0xee30\n"
        ".hword 0x0a06, 0xed8d, 0x0000, 0xe350\n"
        ".hword 0x0069, 0x0a00, 0x3010, 0xe28d\n"
        ".hword 0x0000, 0xe354, 0x0007, 0xe893\n"
        ".hword 0x3030, 0xe28d, 0x0007, 0xe883\n"
        ".hword 0x0014, 0x0a00, 0x0b01, 0xe285\n"
        ".hword 0x0f7d, 0xe280, 0x0003, 0xe890\n"
        ".hword 0x0001, 0xe150, 0x0001, 0x0a00\n"
        ".hword 0x0001, 0xe350, 0x0016, 0x0a00\n"
        ".hword 0x0a95, 0xedd7, 0x0a06, 0xed9d\n"
        ".hword 0x0a20, 0xee30, 0x0a06, 0xed8d\n"
        ".hword 0x2a10, 0xee00, 0x0a94, 0xedd7\n"
        ".hword 0x0a20, 0xee30, 0x0a0e, 0xed8d\n"
        ".hword 0x0600, 0xe595, 0x00c8, 0xe350\n"
        ".hword 0x15fc, 0x1595, 0x00c8, 0x1351\n"
        ".hword 0x0012, 0x0a00, 0x0016, 0xea00\n"
        ".hword 0x0a92, 0xedd7, 0x0a06, 0xed9d\n"
        ".hword 0x0a20, 0xee30, 0x0a06, 0xed8d\n"
        ".hword 0x2a10, 0xee00, 0x0a91, 0xedd7\n"
        ".hword 0x0a20, 0xee30, 0x0a0e, 0xed8d\n"
        ".hword 0xfff0, 0xeaff, 0x0a95, 0xedd7\n"
        ".hword 0x0a06, 0xed9d, 0x0a20, 0xee30\n"
        ".hword 0x0a06, 0xed8d, 0x2a10, 0xee00\n"
        ".hword 0x0a95, 0xedd7, 0x0a20, 0xee30\n"
        ".hword 0x0a0e, 0xed8d, 0xffe7, 0xeaff\n"
        ".hword 0x0000, 0xe354, 0x000e, 0x0a00\n"
        ".hword 0x05fc, 0xe595, 0x00c8, 0xe350\n"
        ".hword 0x002a, 0x0a00, 0x0a76, 0xed97\n"
        ".hword 0x2030, 0xe28d, 0x1010, 0xe28d\n"
        ".hword 0x0ac0, 0xeebd, 0x0a00, 0xed8d\n"
        ".hword 0x9004, 0xe58d, 0x35e0, 0xe595\n"
        ".hword 0x0630, 0xe596, 0x1d0e, 0xeb06\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0x0036, 0xea00, 0x00c8, 0xe350\n"
        ".hword 0x0003, 0x0a00, 0x05fc, 0xe595\n"
        ".hword 0x00c8, 0xe350, 0x000d, 0x0a00\n"
        ".hword 0x0016, 0xea00, 0x0a76, 0xed97\n"
        ".hword 0x0001, 0xe3a0, 0x2030, 0xe28d\n"
        ".hword 0x0ac0, 0xeebd, 0x1010, 0xe28d\n"
        ".hword 0x0a00, 0xed8d, 0x0004, 0xe58d\n"
        ".hword 0x0630, 0xe595, 0x35e0, 0xe595\n"
        ".hword 0x1cfb, 0xeb06, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0x0009, 0xea00\n"
        ".hword 0x0a76, 0xed97, 0x0007, 0xe3a0\n"
        ".hword 0x2030, 0xe28d, 0x0ac0, 0xeebd\n"
        ".hword 0x1010, 0xe28d, 0x0a00, 0xed8d\n"
        ".hword 0x0004, 0xe58d, 0x0630, 0xe595\n"
        ".hword 0x35e0, 0xe595, 0x1cee, 0xeb06\n"
        ".hword 0x4001, 0xe3a0, 0xff7f, 0xeaff\n"
        ".hword 0x0a76, 0xed97, 0x0007, 0xe3a0\n"
        ".hword 0x2030, 0xe28d, 0x0ac0, 0xeebd\n"
        ".hword 0x1010, 0xe28d, 0x0a00, 0xed8d\n"
        ".hword 0x0004, 0xe58d, 0x35e0, 0xe595\n"
        ".hword 0x0630, 0xe596, 0x1ce2, 0xeb06\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0x000a, 0xea00, 0x0000, 0xe354\n"
        ".hword 0x0011, 0x0a00, 0x1a76, 0xed97\n"
        ".hword 0x3e25, 0xe287, 0x15e0, 0xe595\n"
        ".hword 0x1ac1, 0xeebd, 0x0a02, 0xec93\n"
        ".hword 0x0630, 0xe596, 0x2a10, 0xee11\n"
        ".hword 0x4728, 0xeb00, 0x9630, 0xe586\n"
        ".hword 0x4001, 0xe284, 0x0004, 0xe354\n"
        ".hword 0xff64, 0xbaff, 0x0006, 0xe3a0\n"
        ".hword 0x05ec, 0xe585, 0xd03c, 0xe28d\n"
        ".hword 0x0000, 0xe3a0, 0x8b02, 0xecbd\n"
        ".hword 0x8ff0, 0xe8bd, 0x0a76, 0xed97\n"
        ".hword 0x0630, 0xe595, 0x15e0, 0xe595\n"
        ".hword 0x0ac0, 0xeebd, 0x2a10, 0xee10\n"
        ".hword 0x0a48, 0xeeb0, 0x0a40, 0xeef0\n"
        ".hword 0xffec, 0xeaff, 0xd03c, 0xe28d\n"
        ".hword 0x0001, 0xe3a0, 0x8b02, 0xecbd\n"
        ".hword 0x8ff0, 0xe8bd, 0xdfc0, 0x0043\n"
        ".hword 0x0000, 0x0000, 0xe048, 0x0043\n"
    );
};

// DECOMP_FUNC(0x003be55c, 792)
extern "C" __attribute__((naked)) void ui_func_003be55c() {
    asm volatile(
        ".arm\n"
        ".hword 0x4fff, 0xe92d, 0x4003, 0xe1a0\n"
        ".hword 0x0b02, 0xed2d, 0x8b02, 0xed2d\n"
        ".hword 0xd02c, 0xe24d, 0x8a40, 0xeeb0\n"
        ".hword 0x7074, 0xe59d, 0x55c6, 0xebfb\n"
        ".hword 0xa000, 0xe1a0, 0x0040, 0xe59d\n"
        ".hword 0xbf99, 0xebfb, 0x8000, 0xe1a0\n"
        ".hword 0x0004, 0xe1a0, 0xd8af, 0xebfb\n"
        ".hword 0x6000, 0xe1a0, 0x1070, 0xe59d\n"
        ".hword 0x000a, 0xe1a0, 0x117b, 0xebfb\n"
        ".hword 0x0004, 0xe58d, 0x1007, 0xe1a0\n"
        ".hword 0x000a, 0xe1a0, 0x1177, 0xebfb\n"
        ".hword 0x9000, 0xe1a0, 0x2004, 0xe59d\n"
        ".hword 0x100a, 0xe1a0, 0x0008, 0xe28d\n"
        ".hword 0x2406, 0xebfa, 0x0026, 0xe5dd\n"
        ".hword 0x4000, 0xe3e0, 0x5004, 0xe1a0\n"
        ".hword 0x0000, 0xe350, 0xb001, 0xe3a0\n"
        ".hword 0x0002, 0x1a00, 0x1025, 0xe5dd\n"
        ".hword 0x0000, 0xe351, 0x0099, 0x1a00\n"
        ".hword 0x0000, 0xe358, 0x005a, 0x0a00\n"
        ".hword 0x1038, 0xe598, 0x087f, 0xe311\n"
        ".hword 0x0094, 0x1a00, 0x22bc, 0xe1d8\n"
        ".hword 0x3023, 0xe5d8, 0x2a10, 0xee00\n"
        ".hword 0x0002, 0xe353, 0x0a40, 0xeeb8\n"
        ".hword 0xf103, 0x379f, 0x0032, 0xea00\n"
        ".hword 0xe6e8, 0x003b, 0xe624, 0x003b\n"
        ".hword 0x0902, 0xe311, 0x0005, 0x0a00\n"
        ".hword 0x0f6e, 0xe3a0, 0xb000, 0xe3a0\n"
        ".hword 0x00f9, 0xe190, 0x0fa0, 0xe080\n"
        ".hword 0x40c0, 0xe1a0, 0x0028, 0xea00\n"
        ".hword 0x0000, 0xe350, 0x0026, 0x0a00\n"
        ".hword 0x02d7, 0xe1dd, 0x0a48, 0xeef0\n"
        ".hword 0x1070, 0xe59d, 0x0000, 0xe58d\n"
        ".hword 0x32d8, 0xe1dd, 0x0040, 0xe59d\n"
        ".hword 0x2007, 0xe1a0, 0x0134, 0xeb00\n"
        ".hword 0x1026, 0xe5dd, 0x4000, 0xe1a0\n"
        ".hword 0x0000, 0xe351, 0x0004, 0x0a00\n"
        ".hword 0x01d8, 0xe59f, 0x1490, 0xe0c0\n"
        ".hword 0x4fc0, 0xe040, 0x0064, 0xe354\n"
        ".hword 0x4064, 0xc3a0, 0x0004, 0xe59d\n"
        ".hword 0x1c01, 0xe280, 0x01c0, 0xe59f\n"
        ".hword 0x1cb6, 0xe1d1, 0x0c02, 0xe311\n"
        ".hword 0x0005, 0x0a00, 0x1184, 0xe084\n"
        ".hword 0x1204, 0xe081, 0x2190, 0xe0c1\n"
        ".hword 0x22c1, 0xe1a0, 0x1fc1, 0xe042\n"
        ".hword 0x4001, 0xe044, 0x119c, 0xe59f\n"
        ".hword 0x10b9, 0xe191, 0x0080, 0xe311\n"
        ".hword 0x0005, 0x0a00, 0x1184, 0xe084\n"
        ".hword 0x1204, 0xe081, 0x1190, 0xe0c0\n"
        ".hword 0x12c0, 0xe1a0, 0x0fc0, 0xe041\n"
        ".hword 0x4000, 0xe084, 0x0178, 0xe59f\n"
        ".hword 0x000a, 0xe790, 0x0701, 0xe310\n"
        ".hword 0x000e, 0x1a00, 0x0000, 0xe35b\n"
        ".hword 0x000c, 0x0a00, 0x0000, 0xe354\n"
        ".hword 0x000a, 0xda00, 0x015c, 0xe59f\n"
        ".hword 0x100a, 0xe790, 0x1040, 0xe201\n"
        ".hword 0x0001, 0xe1b0, 0x0005, 0x1a00\n"
        ".hword 0x00e0, 0xe59a, 0x0202, 0xe310\n"
        ".hword 0x0002, 0x1a00, 0x000f, 0xe3a0\n"
        ".hword 0x0142, 0xebfa, 0x4000, 0xe084\n"
        ".hword 0x003c, 0xe59d, 0x0000, 0xe350\n"
        ".hword 0x0039, 0x0a00, 0x0026, 0xe5dd\n"
        ".hword 0x0000, 0xe350, 0x0028, 0x0a00\n"
        ".hword 0x0f6e, 0xe3a0, 0x00f9, 0xe190\n"
        ".hword 0x0000, 0xe154, 0x4000, 0xc1a0\n"
        ".hword 0x0023, 0xea00, 0x0000, 0xe356\n"
        ".hword 0x003a, 0x0a00, 0x06b6, 0xe1d6\n"
        ".hword 0x0000, 0xe350, 0x5000, 0x11a0\n"
        ".hword 0x0069, 0xe5d6, 0x0000, 0xe350\n"
        ".hword 0x0018, 0x0a00, 0x006d, 0xe357\n"
        ".hword 0x8a39, 0xed9f, 0x000b, 0xaa00\n"
        ".hword 0x1007, 0xe1a0, 0x000a, 0xe1a0\n"
        ".hword 0xfd41, 0xebfa, 0x0ebe, 0xe1d0\n"
        ".hword 0x1069, 0xe5d6, 0x0180, 0xe160\n"
        ".hword 0x0a10, 0xee00, 0x0ac0, 0xeeb8\n"
        ".hword 0x0a08, 0xee20, 0x0ac0, 0xeebd\n"
        ".hword 0x5a10, 0xee10, 0x0009, 0xea00\n"
        ".hword 0x006d, 0xe247, 0xa887, 0xebfb\n"
        ".hword 0x01b0, 0xe1d0, 0x1069, 0xe5d6\n"
        ".hword 0x0180, 0xe160, 0x0a10, 0xee00\n"
        ".hword 0x0ac0, 0xeeb8, 0x0a08, 0xee20\n"
        ".hword 0x0ac0, 0xeebd, 0x5a10, 0xee10\n"
        ".hword 0x003c, 0xe59d, 0x0000, 0xe350\n"
        ".hword 0x0004, 0x0a00, 0x0004, 0xe1a0\n"
        ".hword 0xd02c, 0xe28d, 0x8b02, 0xecbd\n"
        ".hword 0xd018, 0xe28d, 0x8ff0, 0xe8bd\n"
        ".hword 0x006d, 0xe357, 0x0008, 0xaa00\n"
        ".hword 0x0050, 0xe59f, 0x00b9, 0xe190\n"
        ".hword 0x0008, 0xe200, 0x0000, 0xe350\n"
        ".hword 0x0001, 0x1355, 0x0000, 0xda00\n"
        ".hword 0x5001, 0xe3a0, 0x0005, 0xe1a0\n"
        ".hword 0xfff0, 0xeaff, 0x006d, 0xe247\n"
        ".hword 0xa86a, 0xebfb, 0x1003, 0xe3a0\n"
        ".hword 0xf000, 0xe320, 0x8181, 0xebfb\n"
        ".hword 0x0000, 0xe350, 0x0001, 0x1355\n"
        ".hword 0xfff5, 0xdaff, 0xfff3, 0xeaff\n"
        ".hword 0x0000, 0xe3e0, 0xffe5, 0xeaff\n"
        ".hword 0x5556, 0x5555, 0x851f, 0x51eb\n"
        ".hword 0x01c6, 0x0000, 0x44a0, 0x0000\n"
        ".hword 0x44ac, 0x0000, 0xd70a, 0x3c23\n"
    );
};

// DECOMP_FUNC(0x00110910, 796)
extern "C" __attribute__((naked)) void engine_func_00110910() {
    asm volatile(
        ".arm\n"
        ".hword 0x47f0, 0xe92d, 0xdc06, 0xe24d\n"
        ".hword 0x4000, 0xe3a0, 0xa000, 0xe1a0\n"
        ".hword 0x0020, 0xe590, 0x0000, 0xe350\n"
        ".hword 0x0008, 0x9a00, 0x04ff, 0xe3c4\n"
        ".hword 0x1024, 0xe59a, 0x0180, 0xe080\n"
        ".hword 0x0180, 0xe081, 0x7a8a, 0xeb00\n"
        ".hword 0x0020, 0xe59a, 0x4001, 0xe284\n"
        ".hword 0x0004, 0xe150, 0xfff6, 0x8aff\n"
        ".hword 0x0030, 0xe59a, 0x5028, 0xe28a\n"
        ".hword 0x0002, 0xe350, 0x0033, 0x3a00\n"
        ".hword 0x700d, 0xe1a0, 0x12a8, 0xe59f\n"
        ".hword 0x3080, 0xe3a0, 0x200c, 0xe3a0\n"
        ".hword 0x0007, 0xe1a0, 0xd577, 0xfa06\n"
        ".hword 0x0008, 0xe595, 0x0000, 0xe350\n"
        ".hword 0x0010, 0x0a00, 0x100c, 0xe595\n"
        ".hword 0x0008, 0xe285, 0x6001, 0xe1a0\n"
        ".hword 0x40d4, 0xe241, 0xa9f5, 0xeb06\n"
        ".hword 0x0098, 0xe5d4, 0x1050, 0xe594\n"
        ".hword 0x2006, 0xe1a0, 0x0001, 0xe080\n"
        ".hword 0x0010, 0xe6e7, 0x0080, 0xe080\n"
        ".hword 0x0100, 0xe087, 0x1004, 0xe280\n"
        ".hword 0xbb6d, 0xeb06, 0x0008, 0xe595\n"
        ".hword 0x0000, 0xe350, 0xffee, 0x1aff\n"
        ".hword 0x9000, 0xe3a0, 0x6007, 0xe1a0\n"
        ".hword 0x7089, 0xe089, 0x0107, 0xe796\n"
        ".hword 0x0000, 0xe350, 0x8107, 0x1086\n"
        ".hword 0x000a, 0x0a00, 0x1004, 0xe598\n"
        ".hword 0x0008, 0xe1a0, 0x40d4, 0xe241\n"
        ".hword 0xa9de, 0xeb06, 0x0008, 0xe285\n"
        ".hword 0x100c, 0xe285, 0x20d4, 0xe284\n"
        ".hword 0xbb5b, 0xeb06, 0x0107, 0xe796\n"
        ".hword 0x0000, 0xe350, 0xfff4, 0x1aff\n"
        ".hword 0x9001, 0xe289, 0x0080, 0xe359\n"
        ".hword 0xffec, 0xbaff, 0x11f4, 0xe59f\n"
        ".hword 0x3080, 0xe3a0, 0x200c, 0xe3a0\n"
        ".hword 0x0006, 0xe1a0, 0xd7a2, 0xfa06\n"
        ".hword 0x0050, 0xe59a, 0x5048, 0xe28a\n"
        ".hword 0x0002, 0xe350, 0x0033, 0x3a00\n"
        ".hword 0x700d, 0xe1a0, 0x11d0, 0xe59f\n"
        ".hword 0x3080, 0xe3a0, 0x200c, 0xe3a0\n"
        ".hword 0x0007, 0xe1a0, 0xd53f, 0xfa06\n"
        ".hword 0x0008, 0xe595, 0x0000, 0xe350\n"
        ".hword 0x0010, 0x0a00, 0x100c, 0xe595\n"
        ".hword 0x0008, 0xe285, 0x6001, 0xe1a0\n"
        ".hword 0x40d4, 0xe241, 0xa9bd, 0xeb06\n"
        ".hword 0x0098, 0xe5d4, 0x1050, 0xe594\n"
        ".hword 0x2006, 0xe1a0, 0x0001, 0xe080\n"
        ".hword 0x0010, 0xe6e7, 0x0080, 0xe080\n"
        ".hword 0x0100, 0xe087, 0x1004, 0xe280\n"
        ".hword 0xbb35, 0xeb06, 0x0008, 0xe595\n"
        ".hword 0x0000, 0xe350, 0xffee, 0x1aff\n"
        ".hword 0x9000, 0xe3a0, 0x6007, 0xe1a0\n"
        ".hword 0x7089, 0xe089, 0x0107, 0xe796\n"
        ".hword 0x0000, 0xe350, 0x8107, 0x1086\n"
        ".hword 0x000a, 0x0a00, 0x1004, 0xe598\n"
        ".hword 0x0008, 0xe1a0, 0x40d4, 0xe241\n"
        ".hword 0xa9a6, 0xeb06, 0x0008, 0xe285\n"
        ".hword 0x100c, 0xe285, 0x20d4, 0xe284\n"
        ".hword 0xbb23, 0xeb06, 0x0107, 0xe796\n"
        ".hword 0x0000, 0xe350, 0xfff4, 0x1aff\n"
        ".hword 0x9001, 0xe289, 0x0080, 0xe359\n"
        ".hword 0xffec, 0xbaff, 0x111c, 0xe59f\n"
        ".hword 0x3080, 0xe3a0, 0x200c, 0xe3a0\n"
        ".hword 0x0006, 0xe1a0, 0xd76a, 0xfa06\n"
        ".hword 0x0070, 0xe59a, 0x4068, 0xe28a\n"
        ".hword 0x0002, 0xe350, 0x0032, 0x3a00\n"
        ".hword 0x600d, 0xe1a0, 0x10f8, 0xe59f\n"
        ".hword 0x3080, 0xe3a0, 0x200c, 0xe3a0\n"
        ".hword 0x0006, 0xe1a0, 0xd507, 0xfa06\n"
        ".hword 0x0008, 0xe594, 0x0000, 0xe350\n"
        ".hword 0x000f, 0x0a00, 0x100c, 0xe594\n"
        ".hword 0x0008, 0xe284, 0x50d4, 0xe241\n"
        ".hword 0xa986, 0xeb06, 0x0098, 0xe5d5\n"
        ".hword 0x1050, 0xe595, 0x20d4, 0xe285\n"
        ".hword 0x0001, 0xe080, 0x0010, 0xe6e7\n"
        ".hword 0x0080, 0xe080, 0x0100, 0xe086\n"
        ".hword 0x1004, 0xe280, 0xbafe, 0xeb06\n"
        ".hword 0x0008, 0xe594, 0x0000, 0xe350\n"
        ".hword 0xffef, 0x1aff, 0x9000, 0xe3a0\n"
        ".hword 0x5006, 0xe1a0, 0x6089, 0xe089\n"
        ".hword 0x0106, 0xe795, 0x0000, 0xe350\n"
        ".hword 0x7106, 0x1085, 0x000a, 0x0a00\n"
        ".hword 0x1004, 0xe597, 0x0007, 0xe1a0\n"
        ".hword 0x8001, 0xe1a0, 0xa96f, 0xeb06\n"
        ".hword 0x0008, 0xe284, 0x100c, 0xe284\n"
        ".hword 0x2008, 0xe1a0, 0xbaec, 0xeb06\n"
        ".hword 0x0106, 0xe795, 0x0000, 0xe350\n"
        ".hword 0xfff4, 0x1aff, 0x9001, 0xe289\n"
        ".hword 0x0080, 0xe359, 0xffec, 0xbaff\n"
        ".hword 0x1048, 0xe59f, 0x3080, 0xe3a0\n"
        ".hword 0x200c, 0xe3a0, 0x0005, 0xe1a0\n"
        ".hword 0xd733, 0xfa06, 0xf000, 0xe320\n"
        ".hword 0xa988, 0xeb06, 0x4000, 0xe1a0\n"
        ".hword 0xf000, 0xe320, 0xbef9, 0xeb00\n"
        ".hword 0xdc06, 0xe28d, 0x0004, 0xe1a0\n"
        ".hword 0x47f0, 0xe8bd, 0x1000, 0xe3a0\n"
        ".hword 0xa927, 0xea06, 0x3bf4, 0x0012\n"
        ".hword 0xd8dc, 0x0011, 0x3c0c, 0x0012\n"
        ".hword 0xd8e0, 0x0011, 0x3bdc, 0x0012\n"
        ".hword 0xd8d8, 0x0011\n"
    );
};

// DECOMP_FUNC(0x0037c4e8, 800)
extern "C" __attribute__((naked)) void ui_func_0037c4e8() {
    asm volatile(
        ".arm\n"
        ".hword 0x47f0, 0xe92d, 0x4001, 0xe1a0\n"
        ".hword 0xd078, 0xe24d, 0x6000, 0xe1a0\n"
        ".hword 0x1304, 0xe59f, 0x2901, 0xe3a0\n"
        ".hword 0xfdf0, 0xebff, 0x0000, 0xe350\n"
        ".hword 0x0095, 0x0a00, 0x0010, 0xe596\n"
        ".hword 0x1018, 0xe28d, 0x0010, 0xe584\n"
        ".hword 0x03b0, 0xe1d6, 0x08b0, 0xe1c4\n"
        ".hword 0x0006, 0xe1a0, 0xaac3, 0xeb01\n"
        ".hword 0x0000, 0xe350, 0x008c, 0x0a00\n"
        ".hword 0x0006, 0xe1a0, 0xaac8, 0xeb01\n"
        ".hword 0x8000, 0xe1a0, 0x0006, 0xe1a0\n"
        ".hword 0xaab3, 0xeb01, 0x0004, 0xe350\n"
        ".hword 0x7000, 0xe1a0, 0x7004, 0x83a0\n"
        ".hword 0x7040, 0xe584, 0x803c, 0xe584\n"
        ".hword 0x0018, 0xe5dd, 0xfb83, 0xebff\n"
        ".hword 0x0018, 0xe5c4, 0x001c, 0xe59d\n"
        ".hword 0x5000, 0xe3a0, 0x001c, 0xe584\n"
        ".hword 0x0019, 0xe5dd, 0x0000, 0xe350\n"
        ".hword 0x0001, 0x13a0, 0x0020, 0xe5c4\n"
        ".hword 0x0020, 0xe59d, 0x0000, 0xe357\n"
        ".hword 0x9008, 0x828d, 0x0024, 0xe584\n"
        ".hword 0x0024, 0xe59d, 0x0028, 0xe584\n"
        ".hword 0x0030, 0xe59d, 0x002c, 0xe584\n"
        ".hword 0x002c, 0xe59d, 0x0030, 0xe584\n"
        ".hword 0x003c, 0xe59d, 0x0034, 0xe584\n"
        ".hword 0x0038, 0xe59d, 0x0038, 0xe584\n"
        ".hword 0x0021, 0x9a00, 0x2005, 0xe1a0\n"
        ".hword 0x1008, 0xe28d, 0x0006, 0xe1a0\n"
        ".hword 0xaaac, 0xeb01, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x0062, 0x0a00\n"
        ".hword 0x0008, 0xe5dd, 0x1185, 0xe065\n"
        ".hword 0x1004, 0xe081, 0x0044, 0xe5c1\n"
        ".hword 0x0009, 0xe5dd, 0x0045, 0xe5c1\n"
        ".hword 0x000a, 0xe5dd, 0x0046, 0xe5c1\n"
        ".hword 0x000b, 0xe5dd, 0x0047, 0xe5c1\n"
        ".hword 0x000c, 0xe5dd, 0x0048, 0xe5c1\n"
        ".hword 0x200c, 0xe5dd, 0x0000, 0xe3a0\n"
        ".hword 0x0000, 0xe352, 0x0007, 0xda00\n"
        ".hword 0x3000, 0xe089, 0x2000, 0xe081\n"
        ".hword 0x3005, 0xe5d3, 0x0001, 0xe280\n"
        ".hword 0x3049, 0xe5c2, 0x200c, 0xe5dd\n"
        ".hword 0x0000, 0xe152, 0xfff7, 0xcaff\n"
        ".hword 0x5001, 0xe285, 0x0007, 0xe155\n"
        ".hword 0xffdd, 0x3aff, 0x0018, 0xe5d4\n"
        ".hword 0x9000, 0xe3a0, 0x0003, 0xe350\n"
        ".hword 0x0a90, 0xe5c6, 0x0044, 0x0a00\n"
        ".hword 0x0000, 0xe358, 0x000f, 0x0a00\n"
        ".hword 0x0001, 0xe208, 0x0001, 0xe350\n"
        ".hword 0x1000, 0xe3a0, 0x1001, 0x03a0\n"
        ".hword 0x9060, 0x0584, 0x0008, 0xe150\n"
        ".hword 0x0008, 0x2a00, 0x2101, 0xe084\n"
        ".hword 0x1001, 0xe281, 0x0002, 0xe280\n"
        ".hword 0x3101, 0xe084, 0x9060, 0xe582\n"
        ".hword 0x0008, 0xe150, 0x1001, 0xe281\n"
        ".hword 0x9060, 0xe583, 0xfff6, 0x3aff\n"
        ".hword 0x0004, 0xe596, 0x0000, 0xe350\n"
        ".hword 0xa883, 0x1b01, 0x104c, 0xe59d\n"
        ".hword 0x0008, 0xe280, 0x4001, 0xe080\n"
        ".hword 0x0024, 0xe59d, 0x1030, 0xe59d\n"
        ".hword 0x0001, 0xe240, 0x2951, 0xebfd\n"
        ".hword 0xa000, 0xe1a0, 0x0020, 0xe59d\n"
        ".hword 0x1030, 0xe59d, 0x294d, 0xebfd\n"
        ".hword 0x5000, 0xe1a0, 0x002c, 0xe59d\n"
        ".hword 0x0598, 0xe001, 0x2000, 0xe3a0\n"
        ".hword 0x4190, 0xe027, 0x0014, 0xe596\n"
        ".hword 0x1000, 0xe590, 0x3040, 0xe591\n"
        ".hword 0x1004, 0xe1a0, 0xff33, 0xe12f\n"
        ".hword 0x1040, 0xe286, 0x503c, 0xe586\n"
        ".hword 0xa038, 0xe586, 0x0290, 0xe881\n"
        ".hword 0x2c24, 0xe596, 0x0000, 0xe352\n"
        ".hword 0x9058, 0x0586, 0x0024, 0x059d\n"
        ".hword 0x000a, 0x0a00, 0x9000, 0xe58d\n"
        ".hword 0x1c28, 0xe596, 0x000d, 0xe1a0\n"
        ".hword 0xff32, 0xe12f, 0x0000, 0xe350\n"
        ".hword 0x0009, 0x0a00, 0x0000, 0xe59d\n"
        ".hword 0x0050, 0xe586, 0x0018, 0xe596\n"
        ".hword 0x0010, 0xe590, 0x9058, 0xe586\n"
        ".hword 0x005c, 0xe586, 0x0006, 0xe1a0\n"
        ".hword 0x9054, 0xe586, 0xfdeb, 0xebff\n"
        ".hword 0x0001, 0xe3a0, 0xd078, 0xe28d\n"
        ".hword 0x87f0, 0xe8bd, 0x0000, 0xe358\n"
        ".hword 0x7000, 0xe3a0, 0xffc9, 0x9aff\n"
        ".hword 0x3007, 0xe1a0, 0x200c, 0xe28d\n"
        ".hword 0x1050, 0xe28d, 0x0006, 0xe1a0\n"
        ".hword 0xaa45, 0xeb01, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0xfff2, 0x0aff\n"
        ".hword 0x0087, 0xe087, 0x0187, 0xe080\n"
        ".hword 0x2020, 0xe3a0, 0x0100, 0xe086\n"
        ".hword 0x5c0a, 0xe280, 0x5092, 0xe285\n"
        ".hword 0x1050, 0xe28d, 0x0005, 0xe1a0\n"
        ".hword 0x260d, 0xebfd, 0x17b0, 0xe1dd\n"
        ".hword 0x0107, 0xe084, 0x7001, 0xe287\n"
        ".hword 0x12b0, 0xe1c5, 0x17b2, 0xe1dd\n"
        ".hword 0x0007, 0xe158, 0x12b2, 0xe1c5\n"
        ".hword 0x17b4, 0xe1dd, 0x12b4, 0xe1c5\n"
        ".hword 0x10bc, 0xe1dd, 0x12b6, 0xe1c5\n"
        ".hword 0x10be, 0xe1dd, 0x12b8, 0xe1c5\n"
        ".hword 0x11b0, 0xe1dd, 0x12ba, 0xe1c5\n"
        ".hword 0x5060, 0xe580, 0xffdd, 0x8aff\n"
        ".hword 0xffa6, 0xeaff, 0xb380, 0x004e\n"
    );
};

// DECOMP_FUNC(0x003f31d8, 800)
extern "C" __attribute__((naked)) void func_003f31d8() {
    asm volatile(
        ".arm\n"
        ".hword 0x41f0, 0xe92d, 0x1000, 0xe3a0\n"
        ".hword 0x4080, 0xe59f, 0x1010, 0xe584\n"
        ".hword 0x0014, 0xe284, 0x2000, 0xe3e0\n"
        ".hword 0x7b02, 0xe284, 0x0006, 0xe880\n"
        ".hword 0x601c, 0xe284, 0x7f8f, 0xe287\n"
        ".hword 0x5001, 0xe1a0, 0x0006, 0xe1b0\n"
        ".hword 0x1005, 0x11a0, 0xb450, 0x1bfd\n"
        ".hword 0x8105, 0xe084, 0x8b05, 0xe288\n"
        ".hword 0x8f77, 0xe288, 0x0000, 0xe357\n"
        ".hword 0x0000, 0xe588, 0x606c, 0xe286\n"
        ".hword 0x0000, 0x03a0, 0x0002, 0x0a00\n"
        ".hword 0x1005, 0xe1a0, 0x0007, 0xe1a0\n"
        ".hword 0xb46d, 0xebfd, 0x1000, 0xe598\n"
        ".hword 0x5001, 0xe285, 0x0018, 0xe355\n"
        ".hword 0x707c, 0xe287, 0x0068, 0xe581\n"
        ".hword 0xffeb, 0xbaff, 0x0004, 0xe1a0\n"
        ".hword 0x41f0, 0xe8bd, 0x2008, 0xe59f\n"
        ".hword 0x1008, 0xe59f, 0xcaf8, 0xeaf8\n"
        ".hword 0x8568, 0x004e, 0x0000, 0x0010\n"
        ".hword 0x0124, 0x0036, 0x2068, 0xe59f\n"
        ".hword 0x0000, 0xe3e0, 0x1000, 0xe1a0\n"
        ".hword 0x3b02, 0xe3a0, 0x00f0, 0xe1c2\n"
        ".hword 0x0058, 0xe59f, 0x1000, 0xe3a0\n"
        ".hword 0x2001, 0xe1a0, 0x0006, 0xe880\n"
        ".hword 0x1601, 0xe3a0, 0x0048, 0xe59f\n"
        ".hword 0x2702, 0xe3a0, 0xcf75, 0xe280\n"
        ".hword 0x000a, 0xe88c, 0xcf77, 0xe280\n"
        ".hword 0x3080, 0xe3a0, 0x000c, 0xe88c\n"
        ".hword 0x3f7a, 0xe280, 0x21e4, 0xe580\n"
        ".hword 0x1000, 0xe3a0, 0x2c05, 0xe3a0\n"
        ".hword 0x0006, 0xe883, 0x201c, 0xe59f\n"
        ".hword 0x11f0, 0xe5a0, 0x0004, 0xe280\n"
        ".hword 0x3007, 0xe242, 0x000e, 0xe880\n"
        ".hword 0xff1e, 0xe12f, 0x5080, 0x0046\n"
        ".hword 0x5088, 0x0046, 0x39e0, 0x004e\n"
        ".hword 0x8058, 0x0000, 0x201c, 0xe59f\n"
        ".hword 0x0000, 0xe3e0, 0x1000, 0xe1a0\n"
        ".hword 0x00f0, 0xe1c2, 0x0010, 0xe59f\n"
        ".hword 0x1000, 0xe3a0, 0x2001, 0xe1a0\n"
        ".hword 0x0006, 0xe880, 0xff1e, 0xe12f\n"
        ".hword 0x4c68, 0x0046, 0x4c70, 0x0046\n"
        ".hword 0x201c, 0xe59f, 0x0000, 0xe3e0\n"
        ".hword 0x1000, 0xe1a0, 0x00f8, 0xe1c2\n"
        ".hword 0x0010, 0xe59f, 0x1000, 0xe3a0\n"
        ".hword 0x2001, 0xe1a0, 0x0006, 0xe880\n"
        ".hword 0xff1e, 0xe12f, 0x3e18, 0x0043\n"
        ".hword 0x3e28, 0x0043, 0x201c, 0xe59f\n"
        ".hword 0x0000, 0xe3e0, 0x1000, 0xe1a0\n"
        ".hword 0x00f0, 0xe1c2, 0x0010, 0xe59f\n"
        ".hword 0x1000, 0xe3a0, 0x2001, 0xe1a0\n"
        ".hword 0x0006, 0xe880, 0xff1e, 0xe12f\n"
        ".hword 0x19c8, 0x0047, 0x19d0, 0x0047\n"
        ".hword 0x201c, 0xe59f, 0x0000, 0xe3e0\n"
        ".hword 0x1000, 0xe1a0, 0x00f0, 0xe1c2\n"
        ".hword 0x0010, 0xe59f, 0x1000, 0xe3a0\n"
        ".hword 0x2001, 0xe1a0, 0x0006, 0xe880\n"
        ".hword 0xff1e, 0xe12f, 0x1c30, 0x0047\n"
        ".hword 0x1c38, 0x0047, 0x201c, 0xe59f\n"
        ".hword 0x0000, 0xe3e0, 0x1000, 0xe1a0\n"
        ".hword 0x00f0, 0xe1c2, 0x0010, 0xe59f\n"
        ".hword 0x1000, 0xe3a0, 0x2001, 0xe1a0\n"
        ".hword 0x0006, 0xe880, 0xff1e, 0xe12f\n"
        ".hword 0x3070, 0x0043, 0x3078, 0x0043\n"
        ".hword 0x201c, 0xe59f, 0x0000, 0xe3e0\n"
        ".hword 0x1000, 0xe1a0, 0x00f0, 0xe1c2\n"
        ".hword 0x0010, 0xe59f, 0x1000, 0xe3a0\n"
        ".hword 0x2001, 0xe1a0, 0x0006, 0xe880\n"
        ".hword 0xff1e, 0xe12f, 0x30c0, 0x0043\n"
        ".hword 0x30c8, 0x0043, 0x201c, 0xe59f\n"
        ".hword 0x0000, 0xe3e0, 0x1000, 0xe1a0\n"
        ".hword 0x00f0, 0xe1c2, 0x0010, 0xe59f\n"
        ".hword 0x1000, 0xe3a0, 0x2001, 0xe1a0\n"
        ".hword 0x0006, 0xe880, 0xff1e, 0xe12f\n"
        ".hword 0x3148, 0x0043, 0x3150, 0x0043\n"
        ".hword 0x201c, 0xe59f, 0x0000, 0xe3e0\n"
        ".hword 0x1000, 0xe1a0, 0x00f8, 0xe1c2\n"
        ".hword 0x0010, 0xe59f, 0x1000, 0xe3a0\n"
        ".hword 0x2001, 0xe1a0, 0x0006, 0xe880\n"
        ".hword 0xff1e, 0xe12f, 0xe598, 0x0044\n"
        ".hword 0xe5a8, 0x0044, 0x2034, 0xe59f\n"
        ".hword 0x0000, 0xe3e0, 0x1000, 0xe1a0\n"
        ".hword 0x3040, 0xe3a0, 0x00f8, 0xe1c2\n"
        ".hword 0x0024, 0xe59f, 0x1000, 0xe3a0\n"
        ".hword 0x2001, 0xe1a0, 0x0006, 0xe880\n"
        ".hword 0x0010, 0xe240, 0x2008, 0xe3a0\n"
        ".hword 0x1000, 0xe580, 0x100c, 0xe59f\n"
        ".hword 0x000c, 0xe59f, 0x4aaf, 0xeafb\n"
        ".hword 0x1a38, 0x0047, 0x1a48, 0x0047\n"
        ".hword 0x3120, 0x0035, 0x62c0, 0x004e\n"
        ".hword 0x201c, 0xe59f, 0x0000, 0xe3e0\n"
        ".hword 0x1000, 0xe1a0, 0x00f0, 0xe1c2\n"
        ".hword 0x0010, 0xe59f, 0x1000, 0xe3a0\n"
        ".hword 0x2001, 0xe1a0, 0x0006, 0xe880\n"
        ".hword 0xff1e, 0xe12f, 0x2570, 0x0047\n"
        ".hword 0x2578, 0x0047, 0x201c, 0xe59f\n"
        ".hword 0x0000, 0xe3e0, 0x1000, 0xe1a0\n"
        ".hword 0x00f0, 0xe1c2, 0x0010, 0xe59f\n"
        ".hword 0x1000, 0xe3a0, 0x2001, 0xe1a0\n"
        ".hword 0x0006, 0xe880, 0xff1e, 0xe12f\n"
        ".hword 0x2798, 0x0047, 0x27a0, 0x0047\n"
    );
};

// DECOMP_FUNC(0x0027d010, 804)
extern "C" __attribute__((naked)) void engine_func_0027d010() {
    asm volatile(
        ".arm\n"
        ".hword 0x41f0, 0xe92d, 0x6300, 0xe59f\n"
        ".hword 0xd080, 0xe24d, 0x7000, 0xe3a0\n"
        ".hword 0x8001, 0xe3a0, 0x0000, 0xe596\n"
        ".hword 0x10fa, 0xe1d0, 0x0000, 0xe351\n"
        ".hword 0x0006, 0x0a00, 0x0001, 0xe351\n"
        ".hword 0x0047, 0x0a00, 0x0002, 0xe351\n"
        ".hword 0x006e, 0x0a00, 0x0063, 0xe351\n"
        ".hword 0x00b0, 0x1a00, 0x0028, 0xea00\n"
        ".hword 0x40fc, 0xe1d0, 0x49b3, 0xeb02\n"
        ".hword 0x0004, 0xe150, 0x7063, 0xe3a0\n"
        ".hword 0x0021, 0xda00, 0x0004, 0xe1a0\n"
        ".hword 0x37ae, 0xebff, 0x10d0, 0xe1d0\n"
        ".hword 0x0000, 0xe351, 0x0017, 0xba00\n"
        ".hword 0x2000, 0xe596, 0x30f6, 0xe1d2\n"
        ".hword 0x0003, 0xe151, 0x0013, 0x1a00\n"
        ".hword 0x10d1, 0xe1d0, 0x20f8, 0xe1d2\n"
        ".hword 0x0002, 0xe151, 0x000f, 0x1a00\n"
        ".hword 0x10fc, 0xe1d0, 0x50fe, 0xe1d0\n"
        ".hword 0x0000, 0xe351, 0x0004, 0x0a00\n"
        ".hword 0x0001, 0xe1a0, 0x0ebd, 0xeb01\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0006, 0x0a00, 0x0000, 0xe355\n"
        ".hword 0x000e, 0x0a00, 0x0005, 0xe1a0\n"
        ".hword 0x0eb6, 0xeb01, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x0009, 0x0a00\n"
        ".hword 0x4001, 0xe284, 0x4991, 0xeb02\n"
        ".hword 0x0004, 0xe150, 0xf000, 0xe320\n"
        ".hword 0xffdd, 0xcaff, 0x0000, 0xe596\n"
        ".hword 0x70ba, 0xe1c0, 0xd080, 0xe28d\n"
        ".hword 0x0001, 0xe3a0, 0x81f0, 0xe8bd\n"
        ".hword 0x1000, 0xe596, 0x0000, 0xe3a0\n"
        ".hword 0x40bc, 0xe1c1, 0x2100, 0xe080\n"
        ".hword 0x2182, 0xe081, 0x201c, 0xe5d2\n"
        ".hword 0x0000, 0xe352, 0x0003, 0x0a00\n"
        ".hword 0x0001, 0xe280, 0x0018, 0xe350\n"
        ".hword 0xfff7, 0xbaff, 0x0000, 0xe3e0\n"
        ".hword 0x0070, 0xe6bf, 0x0001, 0xe370\n"
        ".hword 0x00be, 0xe1c1, 0x70ba, 0x01c1\n"
        ".hword 0xffeb, 0x0aff, 0x00ba, 0xe1d1\n"
        ".hword 0x0001, 0xe280, 0x00ba, 0xe1c1\n"
        ".hword 0xd080, 0xe28d, 0x0000, 0xe3a0\n"
        ".hword 0x81f0, 0xe8bd, 0x00fc, 0xe1d0\n"
        ".hword 0x3770, 0xebff, 0x1000, 0xe596\n"
        ".hword 0x20f2, 0xe1d0, 0x00fe, 0xe1d1\n"
        ".hword 0x0100, 0xe080, 0x0180, 0xe081\n"
        ".hword 0x401c, 0xe280, 0x23b2, 0xe1c0\n"
        ".hword 0x1f66, 0xe28f, 0x000d, 0xe1a0\n"
        ".hword 0x059b, 0xfa01, 0x01b6, 0xe1d4\n"
        ".hword 0x000e, 0xe350, 0x0009, 0x0a00\n"
        ".hword 0x1007, 0xe3a0, 0x000d, 0xe1a0\n"
        ".hword 0x744a, 0xeb00, 0x0018, 0xe584\n"
        ".hword 0x7024, 0xe5c4, 0x0000, 0xe596\n"
        ".hword 0x10ba, 0xe1d0, 0x1001, 0xe281\n"
        ".hword 0x10ba, 0xe1c0, 0x0053, 0xea00\n"
        ".hword 0x0000, 0xe596, 0x1014, 0xe5d0\n"
        ".hword 0x0000, 0xe351, 0x0018, 0x0a00\n"
        ".hword 0x1018, 0xe590, 0x1101, 0xe081\n"
        ".hword 0x0181, 0xe080, 0x1001, 0xe3a0\n"
        ".hword 0x0034, 0xe590, 0x20ac, 0xeb00\n"
        ".hword 0x0018, 0xe584, 0x8024, 0xe5c4\n"
        ".hword 0x0000, 0xe596, 0x10ba, 0xe1d0\n"
        ".hword 0x1001, 0xe281, 0x10ba, 0xe1c0\n"
        ".hword 0x0000, 0xe596, 0x00fc, 0xe1d0\n"
        ".hword 0x3746, 0xebff, 0x5000, 0xe1a0\n"
        ".hword 0x0000, 0xe596, 0x10fe, 0xe1d0\n"
        ".hword 0x1101, 0xe081, 0x0181, 0xe080\n"
        ".hword 0x401c, 0xe280, 0x0040, 0xe5d0\n"
        ".hword 0x0000, 0xe350, 0x000b, 0x1a00\n"
        ".hword 0x0005, 0xea00, 0x1038, 0xe3a0\n"
        ".hword 0x000d, 0xe1a0, 0x7423, 0xeb00\n"
        ".hword 0x0018, 0xe584, 0xf000, 0xe320\n"
        ".hword 0xffd6, 0xeaff, 0x0018, 0xe594\n"
        ".hword 0xc3c5, 0xeb00, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x002b, 0x0a00\n"
        ".hword 0x01b6, 0xe1d4, 0x000e, 0xe350\n"
        ".hword 0x0003, 0x1a00, 0x0000, 0xe596\n"
        ".hword 0x8014, 0xe5c0, 0x10fe, 0xe1d0\n"
        ".hword 0x1018, 0xe580, 0x0018, 0xe594\n"
        ".hword 0x1001, 0xe3a0, 0x8d0f, 0xeb00\n"
        ".hword 0x8000, 0xe5c4, 0x8001, 0xe5c4\n"
        ".hword 0x00f4, 0xe1d5, 0x0a10, 0xee00\n"
        ".hword 0x0ac0, 0xeeb8, 0x0a01, 0xed84\n"
        ".hword 0x00f6, 0xe1d5, 0x0a10, 0xee00\n"
        ".hword 0x0ac0, 0xeeb8, 0x0a02, 0xed84\n"
        ".hword 0x00f8, 0xe1d5, 0x0a10, 0xee00\n"
        ".hword 0x0ac0, 0xeeb8, 0x0a03, 0xed84\n"
        ".hword 0x00fa, 0xe1d5, 0x0a10, 0xee00\n"
        ".hword 0x0ac0, 0xeeb8, 0x0a04, 0xed84\n"
        ".hword 0x71b4, 0xe1c4, 0x0000, 0xe596\n"
        ".hword 0x10fc, 0xe1d0, 0x1a02, 0xe281\n"
        ".hword 0x101c, 0xe584, 0x10bc, 0xe1d5\n"
        ".hword 0x12b0, 0xe1c4, 0x10be, 0xe1d5\n"
        ".hword 0x12b2, 0xe1c4, 0x1010, 0xe590\n"
        ".hword 0x1001, 0xe281, 0x1010, 0xe580\n"
        ".hword 0x10bc, 0xe1d0, 0x1001, 0xe281\n"
        ".hword 0x10bc, 0xe1c0, 0x70ba, 0xe1c0\n"
        ".hword 0xd080, 0xe28d, 0x0000, 0xe3a0\n"
        ".hword 0x81f0, 0xe8bd, 0x7a48, 0x0044\n"
        ".hword 0x616d, 0x2f70, 0x6e75, 0x7469\n"
        ".hword 0x752f, 0x3025, 0x6433, 0x622e\n"
        ".hword 0x6d61, 0x0000\n"
    );
};

// DECOMP_FUNC(0x003c5900, 804)
extern "C" __attribute__((naked)) void battle_func_003c5900() {
    asm volatile(
        ".arm\n"
        ".hword 0x4070, 0xe92d, 0x4000, 0xe1a0\n"
        ".hword 0x0010, 0xe590, 0x5001, 0xe1a0\n"
        ".hword 0x42ed, 0xebfa, 0x001a, 0xe350\n"
        ".hword 0x1000, 0xe1a0, 0xf100, 0x379f\n"
        ".hword 0x8070, 0xe8bd, 0x598c, 0x003c\n"
        ".hword 0x59a0, 0x003c, 0x59b4, 0x003c\n"
        ".hword 0x59c8, 0x003c, 0x59e0, 0x003c\n"
        ".hword 0x59f8, 0x003c, 0x5a0c, 0x003c\n"
        ".hword 0x5a20, 0x003c, 0x5a34, 0x003c\n"
        ".hword 0x5a48, 0x003c, 0x5a60, 0x003c\n"
        ".hword 0x5a78, 0x003c, 0x5a90, 0x003c\n"
        ".hword 0x5aa8, 0x003c, 0x5ac0, 0x003c\n"
        ".hword 0x5ad4, 0x003c, 0x5aec, 0x003c\n"
        ".hword 0x5b04, 0x003c, 0x5b18, 0x003c\n"
        ".hword 0x5b30, 0x003c, 0x5b48, 0x003c\n"
        ".hword 0x5b5c, 0x003c, 0x5b70, 0x003c\n"
        ".hword 0x5b84, 0x003c, 0x5b98, 0x003c\n"
        ".hword 0x5bac, 0x003c, 0x0010, 0xe594\n"
        ".hword 0x9310, 0xebf9, 0x1228, 0xe59f\n"
        ".hword 0x0005, 0xe781, 0x8070, 0xe8bd\n"
        ".hword 0x0010, 0xe594, 0x930b, 0xebf9\n"
        ".hword 0x1218, 0xe59f, 0x0005, 0xe781\n"
        ".hword 0x8070, 0xe8bd, 0x0010, 0xe594\n"
        ".hword 0x9306, 0xebf9, 0x1208, 0xe59f\n"
        ".hword 0x0005, 0xe781, 0x8070, 0xe8bd\n"
        ".hword 0x0010, 0xe594, 0x9309, 0xebf9\n"
        ".hword 0x11f8, 0xe59f, 0x0000, 0xe590\n"
        ".hword 0x0005, 0xe781, 0x8070, 0xe8bd\n"
        ".hword 0x0010, 0xe594, 0x9303, 0xebf9\n"
        ".hword 0x11e4, 0xe59f, 0x0000, 0xe590\n"
        ".hword 0x0005, 0xe781, 0x8070, 0xe8bd\n"
        ".hword 0x0010, 0xe594, 0x92f5, 0xebf9\n"
        ".hword 0x11d0, 0xe59f, 0x0005, 0xe781\n"
        ".hword 0x8070, 0xe8bd, 0x0010, 0xe594\n"
        ".hword 0x92f0, 0xebf9, 0x1d8b, 0xe3a0\n"
        ".hword 0x0005, 0xe781, 0x8070, 0xe8bd\n"
        ".hword 0x0010, 0xe594, 0x92eb, 0xebf9\n"
        ".hword 0x11ac, 0xe59f, 0x0005, 0xe781\n"
        ".hword 0x8070, 0xe8bd, 0x0010, 0xe594\n"
        ".hword 0x92e6, 0xebf9, 0x119c, 0xe59f\n"
        ".hword 0x0005, 0xe781, 0x8070, 0xe8bd\n"
        ".hword 0x0010, 0xe594, 0x92e9, 0xebf9\n"
        ".hword 0x118c, 0xe59f, 0x0000, 0xe590\n"
        ".hword 0x0005, 0xe781, 0x8070, 0xe8bd\n"
        ".hword 0x0010, 0xe594, 0x92e3, 0xebf9\n"
        ".hword 0x1178, 0xe59f, 0x0000, 0xe590\n"
        ".hword 0x0005, 0xe781, 0x8070, 0xe8bd\n"
        ".hword 0x0010, 0xe594, 0x92dd, 0xebf9\n"
        ".hword 0x1164, 0xe59f, 0x0000, 0xe590\n"
        ".hword 0x0005, 0xe781, 0x8070, 0xe8bd\n"
        ".hword 0x0010, 0xe594, 0x92d7, 0xebf9\n"
        ".hword 0x1150, 0xe59f, 0x0000, 0xe590\n"
        ".hword 0x0005, 0xe781, 0x8070, 0xe8bd\n"
        ".hword 0x0010, 0xe594, 0x92d1, 0xebf9\n"
        ".hword 0x113c, 0xe59f, 0x0000, 0xe590\n"
        ".hword 0x0005, 0xe781, 0x8070, 0xe8bd\n"
        ".hword 0x0010, 0xe594, 0x92c3, 0xebf9\n"
        ".hword 0x1128, 0xe59f, 0x0005, 0xe781\n"
        ".hword 0x8070, 0xe8bd, 0x0010, 0xe594\n"
        ".hword 0x92c6, 0xebf9, 0x1118, 0xe59f\n"
        ".hword 0x0000, 0xe590, 0x0005, 0xe781\n"
        ".hword 0x8070, 0xe8bd, 0x0010, 0xe594\n"
        ".hword 0x92c0, 0xebf9, 0x1104, 0xe59f\n"
        ".hword 0x0000, 0xe590, 0x0005, 0xe781\n"
        ".hword 0x8070, 0xe8bd, 0x0010, 0xe594\n"
        ".hword 0x92b2, 0xebf9, 0x10f0, 0xe59f\n"
        ".hword 0x0005, 0xe781, 0x8070, 0xe8bd\n"
        ".hword 0x0010, 0xe594, 0x92b5, 0xebf9\n"
        ".hword 0x10e0, 0xe59f, 0x0000, 0xe590\n"
        ".hword 0x0005, 0xe781, 0x8070, 0xe8bd\n"
        ".hword 0x0010, 0xe594, 0x92af, 0xebf9\n"
        ".hword 0x10cc, 0xe59f, 0x0000, 0xe590\n"
        ".hword 0x0005, 0xe781, 0x8070, 0xe8bd\n"
        ".hword 0x0010, 0xe594, 0x92a1, 0xebf9\n"
        ".hword 0x10b8, 0xe59f, 0x0005, 0xe781\n"
        ".hword 0x8070, 0xe8bd, 0x0010, 0xe594\n"
        ".hword 0x929c, 0xebf9, 0x10a8, 0xe59f\n"
        ".hword 0x0005, 0xe781, 0x8070, 0xe8bd\n"
        ".hword 0x0010, 0xe594, 0x9297, 0xebf9\n"
        ".hword 0x1c23, 0xe3a0, 0x0005, 0xe781\n"
        ".hword 0x8070, 0xe8bd, 0x0010, 0xe594\n"
        ".hword 0x9292, 0xebf9, 0x1084, 0xe59f\n"
        ".hword 0x0005, 0xe781, 0x8070, 0xe8bd\n"
        ".hword 0x0010, 0xe594, 0x928d, 0xebf9\n"
        ".hword 0x1074, 0xe59f, 0x0005, 0xe781\n"
        ".hword 0x8070, 0xe8bd, 0x0010, 0xe594\n"
        ".hword 0x9290, 0xebf9, 0x1064, 0xe59f\n"
        ".hword 0x0000, 0xe590, 0x0005, 0xe781\n"
        ".hword 0x8070, 0xe8bd, 0x22a8, 0x0000\n"
        ".hword 0x22ac, 0x0000, 0x22b0, 0x0000\n"
        ".hword 0x22b4, 0x0000, 0x22b8, 0x0000\n"
        ".hword 0x22bc, 0x0000, 0x22c4, 0x0000\n"
        ".hword 0x22c8, 0x0000, 0x22cc, 0x0000\n"
        ".hword 0x22d0, 0x0000, 0x22d4, 0x0000\n"
        ".hword 0x22d8, 0x0000, 0x22dc, 0x0000\n"
        ".hword 0x22e0, 0x0000, 0x22e4, 0x0000\n"
        ".hword 0x22e8, 0x0000, 0x22ec, 0x0000\n"
        ".hword 0x22f0, 0x0000, 0x22f4, 0x0000\n"
        ".hword 0x22f8, 0x0000, 0x22fc, 0x0000\n"
        ".hword 0x2304, 0x0000, 0x2308, 0x0000\n"
        ".hword 0x230c, 0x0000\n"
    );
};

// DECOMP_FUNC(0x0022bac0, 808)
extern "C" __attribute__((naked)) void func_0022bac0() {
    asm volatile(
        ".arm\n"
        ".hword 0x4ff8, 0xe92d, 0x4000, 0xe1a0\n"
        ".hword 0x6001, 0xe1a0, 0x9002, 0xe081\n"
        ".hword 0x00d8, 0xe1c4, 0x7002, 0xe081\n"
        ".hword 0x0007, 0xe150, 0x005f, 0x3a00\n"
        ".hword 0x0006, 0xe041, 0x0002, 0xe150\n"
        ".hword 0x5004, 0xe594, 0x2000, 0x31a0\n"
        ".hword 0x0000, 0xe352, 0x1005, 0xe081\n"
        ".hword 0xc002, 0xe047, 0x3002, 0xe041\n"
        ".hword 0x0002, 0xe040, 0x100c, 0x1085\n"
        ".hword 0x0007, 0x0a00, 0x5003, 0xe1a0\n"
        ".hword 0xc001, 0xe1b0, 0x5000, 0x15d5\n"
        ".hword 0x1001, 0xe28c, 0x3001, 0xe283\n"
        ".hword 0x5000, 0x15cc, 0x2001, 0xe252\n"
        ".hword 0xfff7, 0x1aff, 0x0000, 0xe350\n"
        ".hword 0x003c, 0x0a00, 0x0006, 0xe159\n"
        ".hword 0x001d, 0x8a00, 0x1004, 0xe594\n"
        ".hword 0x0106, 0xe370, 0x2009, 0xe081\n"
        ".hword 0x1006, 0xe081, 0x0004, 0x9a00\n"
        ".hword 0x3001, 0xe4d1, 0x0001, 0xe250\n"
        ".hword 0x3001, 0xe4c2, 0xfffb, 0x1aff\n"
        ".hword 0x0030, 0xea00, 0x0001, 0xe350\n"
        ".hword 0x0001, 0xd3a0, 0x0001, 0xda00\n"
        ".hword 0x0000, 0xe350, 0x002b, 0xda00\n"
        ".hword 0x0001, 0xe310, 0x1001, 0xe241\n"
        ".hword 0x2001, 0xe242, 0x0001, 0x0a00\n"
        ".hword 0x3001, 0xe5f1, 0x3001, 0xe5e2\n"
        ".hword 0x00c0, 0xe1b0, 0x0023, 0x0a00\n"
        ".hword 0x3001, 0xe5d1, 0x0001, 0xe250\n"
        ".hword 0x3001, 0xe5c2, 0x3002, 0xe5f1\n"
        ".hword 0x3002, 0xe5e2, 0xfff9, 0x1aff\n"
        ".hword 0x001c, 0xea00, 0x1004, 0xe594\n"
        ".hword 0x2000, 0xe089, 0x3000, 0xe086\n"
        ".hword 0x2001, 0xe082, 0x0106, 0xe370\n"
        ".hword 0x1003, 0xe081, 0x0004, 0x9a00\n"
        ".hword 0x3001, 0xe571, 0x0001, 0xe250\n"
        ".hword 0x3001, 0xe562, 0xfffb, 0x1aff\n"
        ".hword 0x0010, 0xea00, 0x0001, 0xe350\n"
        ".hword 0x0001, 0xd3a0, 0x0001, 0xda00\n"
        ".hword 0x0000, 0xe350, 0x000b, 0xda00\n"
        ".hword 0x0001, 0xe310, 0x0001, 0x0a00\n"
        ".hword 0x3001, 0xe571, 0x3001, 0xe562\n"
        ".hword 0x00c0, 0xe1b0, 0x0005, 0x0a00\n"
        ".hword 0x3001, 0xe551, 0x0001, 0xe250\n"
        ".hword 0x3001, 0xe542, 0x3002, 0xe571\n"
        ".hword 0x3002, 0xe562, 0xfff9, 0x1aff\n"
        ".hword 0x000c, 0xe594, 0x1004, 0xe594\n"
        ".hword 0x0000, 0xe159, 0x9000, 0x21a0\n"
        ".hword 0x0006, 0xe081, 0x1009, 0xe081\n"
        ".hword 0x0000, 0xe041, 0x0000, 0xe350\n"
        ".hword 0x005c, 0xda00, 0x00c0, 0xe1b0\n"
        ".hword 0x005a, 0x0a00, 0x0001, 0xe250\n"
        ".hword 0xfffd, 0x1aff, 0x0057, 0xea00\n"
        ".hword 0x1007, 0xe1a0, 0x014b, 0xeb00\n"
        ".hword 0x5000, 0xe594, 0x1000, 0xe3a0\n"
        ".hword 0xa000, 0xe1b0, 0x8001, 0xe1a0\n"
        ".hword 0x0025, 0x0a00, 0xa000, 0xe58d\n"
        ".hword 0x1000, 0xe595, 0x0005, 0xe1a0\n"
        ".hword 0x2000, 0xe591, 0x100a, 0xe1a0\n"
        ".hword 0xff32, 0xe12f, 0xb000, 0xe1b0\n"
        ".hword 0x0005, 0x1a00, 0x1000, 0xe595\n"
        ".hword 0x2000, 0xe59d, 0x0005, 0xe1a0\n"
        ".hword 0x3008, 0xe591, 0x1130, 0xe59f\n"
        ".hword 0xff33, 0xe12f, 0x100b, 0xe1b0\n"
        ".hword 0x800a, 0x11a0, 0x0014, 0x1a00\n"
        ".hword 0x000a, 0xe157, 0x0040, 0x0a00\n"
        ".hword 0x0000, 0xe357, 0x0010, 0x0a00\n"
        ".hword 0x1000, 0xe595, 0xa007, 0xe1a0\n"
        ".hword 0x0005, 0xe1a0, 0x2000, 0xe591\n"
        ".hword 0x1007, 0xe1a0, 0xff32, 0xe12f\n"
        ".hword 0x8000, 0xe1b0, 0x0005, 0x1a00\n"
        ".hword 0x1000, 0xe595, 0x0005, 0xe1a0\n"
        ".hword 0x200a, 0xe1a0, 0x3008, 0xe591\n"
        ".hword 0x10dc, 0xe59f, 0xff33, 0xe12f\n"
        ".hword 0x1008, 0xe1b0, 0x8007, 0x11a0\n"
        ".hword 0x002d, 0x0a00, 0x2004, 0xe594\n"
        ".hword 0xc006, 0xe1b0, 0x0001, 0x11a0\n"
        ".hword 0x0007, 0x0a00, 0xa002, 0xe1a0\n"
        ".hword 0x3000, 0xe1b0, 0xa000, 0x15da\n"
        ".hword 0x0001, 0xe283, 0x2001, 0xe282\n"
        ".hword 0xa000, 0x15c3, 0xc001, 0xe25c\n"
        ".hword 0xfff7, 0x1aff, 0x200c, 0xe594\n"
        ".hword 0x0004, 0xe594, 0xc006, 0xe052\n"
        ".hword 0x2006, 0xe080, 0x0009, 0x1081\n"
        ".hword 0x0007, 0x0a00, 0x6002, 0xe1a0\n"
        ".hword 0x3000, 0xe1b0, 0x6000, 0x15d6\n"
        ".hword 0x0001, 0xe283, 0x2001, 0xe282\n"
        ".hword 0x6000, 0x15c3, 0xc001, 0xe25c\n"
        ".hword 0xfff7, 0x1aff, 0x0004, 0xe284\n"
        ".hword 0x2004, 0xe594, 0x0102, 0xe880\n"
        ".hword 0x000c, 0xe594, 0x0002, 0xe080\n"
        ".hword 0x0002, 0xe040, 0x0000, 0xe350\n"
        ".hword 0x0003, 0xda00, 0x00c0, 0xe1b0\n"
        ".hword 0x0001, 0x0a00, 0x0001, 0xe250\n"
        ".hword 0xfffd, 0x1aff, 0x1002, 0xe1a0\n"
        ".hword 0x2000, 0xe595, 0x0005, 0xe1a0\n"
        ".hword 0x2004, 0xe592, 0xff32, 0xe12f\n"
        ".hword 0x0001, 0xe3a0, 0x700c, 0xe584\n"
        ".hword 0x8ff8, 0xe8bd, 0x2000, 0xe595\n"
        ".hword 0x0005, 0xe1a0, 0x2004, 0xe592\n"
        ".hword 0xff32, 0xe12f, 0x0000, 0xe3a0\n"
        ".hword 0x8ff8, 0xe8bd, 0xfe40, 0x0040\n"
    );
};

// DECOMP_FUNC(0x002eeb2c, 816)
extern "C" __attribute__((naked)) void camp_func_002eeb2c() {
    asm volatile(
        ".arm\n"
        ".hword 0x43f0, 0xe92d, 0xd024, 0xe24d\n"
        ".hword 0x7001, 0xe3a0, 0x62f8, 0xe59f\n"
        ".hword 0x42f8, 0xe59f, 0x0023, 0xe5d6\n"
        ".hword 0x0000, 0xe350, 0x0005, 0x0a00\n"
        ".hword 0x0002, 0xe5d4, 0x0000, 0xe350\n"
        ".hword 0x0002, 0x1a00, 0x0001, 0xe3a0\n"
        ".hword 0x7002, 0xe5c4, 0x9b7c, 0xebfc\n"
        ".hword 0x0014, 0xe596, 0x5000, 0xe3a0\n"
        ".hword 0x0003, 0xe350, 0x0000, 0xe5d4\n"
        ".hword 0x0002, 0x0a00, 0x0000, 0xe350\n"
        ".hword 0x0012, 0x0a00, 0x0014, 0xea00\n"
        ".hword 0x0000, 0xe350, 0x0001, 0x1a00\n"
        ".hword 0x17f8, 0xebfb, 0x7000, 0xe5c4\n"
        ".hword 0xf000, 0xe320, 0x7f79, 0xebfc\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0017, 0x0a00, 0x5000, 0xe5c4\n"
        ".hword 0x0002, 0xe5d4, 0x0000, 0xe350\n"
        ".hword 0x0012, 0x0a00, 0x0000, 0xe3a0\n"
        ".hword 0x9b65, 0xebfc, 0x5002, 0xe5c4\n"
        ".hword 0xf000, 0xe320, 0x000d, 0xea00\n"
        ".hword 0x5004, 0xe584, 0x7000, 0xe5c4\n"
        ".hword 0x5001, 0xe5c4, 0x0001, 0xe5d4\n"
        ".hword 0x0000, 0xe350, 0x000a, 0x0a00\n"
        ".hword 0x0000, 0xe3a0, 0x5023, 0xe5c6\n"
        ".hword 0x1c99, 0xebfe, 0x5000, 0xe5c4\n"
        ".hword 0x5001, 0xe5c4, 0x0002, 0xe5d4\n"
        ".hword 0x0000, 0xe350, 0xffec, 0x1aff\n"
        ".hword 0x0001, 0xe3a0, 0xd024, 0xe28d\n"
        ".hword 0x83f0, 0xe8bd, 0x0004, 0xe594\n"
        ".hword 0x8224, 0xe59f, 0x9224, 0xe59f\n"
        ".hword 0x0000, 0xe350, 0x0002, 0x0a00\n"
        ".hword 0x000a, 0xe350, 0x0011, 0x1a00\n"
        ".hword 0x0005, 0xea00, 0x0000, 0xe598\n"
        ".hword 0x101c, 0xe280, 0x0028, 0xe280\n"
        ".hword 0x000e, 0xe891, 0x000e, 0xe880\n"
        ".hword 0x0017, 0xea00, 0x722c, 0xe5c6\n"
        ".hword 0x3c70, 0xebfe, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0x1cf5, 0xebfe\n"
        ".hword 0x0001, 0xe3a0, 0xf000, 0xe320\n"
        ".hword 0x1c7b, 0xebfe, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0x1c70, 0xebfe\n"
        ".hword 0x0004, 0xe594, 0x000b, 0xe350\n"
        ".hword 0x0006, 0x1a00, 0x7022, 0xe5c6\n"
        ".hword 0x0000, 0xe599, 0x500a, 0xe5c0\n"
        ".hword 0x1c03, 0xebfe, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0x3c5d, 0xebfe\n"
        ".hword 0x0004, 0xe594, 0x0014, 0xe350\n"
        ".hword 0x0002, 0xaa00, 0x0004, 0xe594\n"
        ".hword 0x0001, 0xe280, 0x0004, 0xe584\n"
        ".hword 0x0064, 0xe350, 0x002e, 0xaa00\n"
        ".hword 0x000c, 0xe350, 0x0031, 0xda00\n"
        ".hword 0xb325, 0xeb00, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x002d, 0x0a00\n"
        ".hword 0x1bd4, 0xebfe, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0x1b98, 0xebfe\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0x1b66, 0xebfe, 0x1000, 0xe3a0\n"
        ".hword 0x0001, 0xe1a0, 0x6e62, 0xebfe\n"
        ".hword 0x1096, 0xe3a0, 0x1a52, 0xed9f\n"
        ".hword 0x001e, 0xe3a0, 0x2082, 0xe3a0\n"
        ".hword 0x01f0, 0xe1cd, 0x1018, 0xe58d\n"
        ".hword 0x101c, 0xe58d, 0x2000, 0xe58d\n"
        ".hword 0x2004, 0xe58d, 0x3a41, 0xeeb0\n"
        ".hword 0x2a41, 0xeef0, 0x2a41, 0xeeb0\n"
        ".hword 0x1a41, 0xeef0, 0x20c8, 0xe3a0\n"
        ".hword 0x0008, 0xe58d, 0x000c, 0xe58d\n"
        ".hword 0x4a41, 0xed9f, 0x3a41, 0xeddf\n"
        ".hword 0x0a42, 0xeddf, 0x0a42, 0xed9f\n"
        ".hword 0x3082, 0xe3a0, 0x1002, 0xe1a0\n"
        ".hword 0x0002, 0xe1a0, 0x975e, 0xebfe\n"
        ".hword 0x0064, 0xe3a0, 0x0004, 0xe584\n"
        ".hword 0x7023, 0xe5c6, 0x1e8f, 0xebfe\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0x0004, 0xea00, 0xf000, 0xe320\n"
        ".hword 0x2714, 0xebff, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x0002, 0x0a00\n"
        ".hword 0xd024, 0xe28d, 0x0000, 0xe3a0\n"
        ".hword 0x83f0, 0xe8bd, 0x0001, 0xe3a0\n"
        ".hword 0x522c, 0xe5c6, 0x47e2, 0xebfe\n"
        ".hword 0x5022, 0xe5c6, 0xf000, 0xe320\n"
        ".hword 0x1b19, 0xebfe, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0x1af1, 0xebfe\n"
        ".hword 0x0004, 0xe596, 0xf000, 0xe320\n"
        ".hword 0x3a4d, 0xebfe, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0x19ff, 0xebfe\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0x19ae, 0xebfe, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0x190b, 0xebfe\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0x1703, 0xebfe, 0x0000, 0xe599\n"
        ".hword 0x700a, 0xe5c0, 0x1ba6, 0xebfe\n"
        ".hword 0x0000, 0xe598, 0x0194, 0xe590\n"
        ".hword 0xb0ba, 0xebfe, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0x1504, 0xebfe\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0x14f5, 0xebfe, 0x7001, 0xe5c4\n"
        ".hword 0xd024, 0xe28d, 0x0000, 0xe3a0\n"
        ".hword 0x83f0, 0xe8bd, 0xf91c, 0x0049\n"
        ".hword 0x7518, 0x0044, 0x7e88, 0x0044\n"
        ".hword 0x74d8, 0x0044, 0x0000, 0x3fc0\n"
        ".hword 0x0000, 0x41f0, 0x0000, 0x0000\n"
        ".hword 0x0000, 0xbf00, 0x0000, 0x42b4\n"
    );
};

// DECOMP_FUNC(0x00286928, 820)

extern "C" uint32_t engine_func_002c1f28();
extern "C" uint32_t camp_func_002b89a0();
extern "C" uint32_t battle_func_002b8d24(uint8_t*, uint32_t);
extern "C" uint32_t engine_func_0028e974(uint8_t*, uint32_t, uint32_t, uint32_t,
                                         uint32_t, uint32_t, uint32_t);
extern "C" uint32_t engine_func_002b787c(uint32_t);
extern "C" void camp_func_0028df98(uint8_t*, uint32_t);
extern "C" void ui_func_002c4bf0(uint32_t, uint32_t);
extern "C" void func_002b90f0(uint32_t, uint32_t);
extern "C" uint32_t func_002f5b2c(uint32_t);
extern "C" uint32_t func_002d65b4(uint32_t);
extern "C" uint32_t camp_func_0028df70(uint32_t);
extern "C" uint32_t camp_func_002b8ccc();
extern "C" uint32_t script_vm_func_002b8b78(uint32_t request);
extern "C" void engine_func_002b8584(uint32_t);
extern "C" void battle_func_0028df54(uint32_t);
extern "C" void ui_func_0028df3c(uint32_t);
extern "C" void script_vm_func_0028df0c(uint32_t);

extern "C" __attribute__((minsize)) uint32_t engine_func_00286928(
    uint32_t raw_r0, uint32_t raw_r1, uint32_t incoming_r2,
    uint32_t raw_selector, uint32_t arg5, uint32_t arg6) {
    auto table = reinterpret_cast<volatile uint32_t*>(0x0043e188);
    uint8_t* default_object = reinterpret_cast<uint8_t*>(table[1]);
    uint8_t* object = default_object;
    uint32_t selector = raw_selector;
    uint32_t mode = 0;
    uint32_t flag = 0;
    uint32_t initial_byte = 0;
    const bool selector_11_to_15 = raw_selector >= 11 && raw_selector <= 15 && raw_selector != 12;
    const bool remap_to_special = selector_11_to_15 || raw_selector == 19;
    if (remap_to_special) {
        object = reinterpret_cast<uint8_t*>(table[2]);
        if (raw_selector != 19) selector = 11;
    }
    if (raw_selector == 12) object = reinterpret_cast<uint8_t*>(table[3]);
    flag = raw_selector == 11 || raw_selector == 13;
    mode = flag;
    initial_byte = raw_selector == 13 || raw_selector == 15;

    *reinterpret_cast<volatile uint8_t*>(object + 0x2d) = static_cast<uint8_t>(initial_byte);
    *reinterpret_cast<volatile uint8_t*>(object + 0x5e) = static_cast<uint8_t>(mode);

    if (incoming_r2 != 0) {
        uint8_t state = object[8];
        if (state == 4) return 1;
        if (state == 5) {
            battle_func_0028df54(*reinterpret_cast<volatile uint32_t*>(object + 0x18));
            return 1;
        }
        if (state == 0) {
            if (object[0x2e] == 0) {
                if (selector == 11 || selector == 19) {
                    if (default_object != nullptr && default_object[8] != 0) return 0;
                    battle_func_0028df54(*reinterpret_cast<volatile uint32_t*>(object + 0x18));
                    ui_func_0028df3c(0xffffffff);
                    script_vm_func_0028df0c(0);
                }
                return 1;
            }
            *reinterpret_cast<volatile uint8_t*>(object + 0x2e) = 0;
            engine_func_0028e974(object, raw_r0, raw_r1, selector, 0x1a, 1, 0);
            if (object[0x35] == 0)
                camp_func_0028df98(object, object[9]);
            return 0;
        }
        if (engine_func_002c1f28() == 0) return 0;
        if (camp_func_002b89a0() == 0) return 0;
        state = object[8];
        if (state == 3 || state == 0) return 0;
        battle_func_002b8d24(object, object[9]);
        *reinterpret_cast<volatile uint8_t*>(object + 8) = 3;
        *reinterpret_cast<volatile uint8_t*>(object + 0x35) = 0;
        return 0;
    }

    if (flag != 0) {
        *reinterpret_cast<volatile uint8_t*>(object + 0x5f) = 1;
        *reinterpret_cast<volatile uint8_t*>(default_object + 0x5f) = 1;
    }
    *reinterpret_cast<volatile uint8_t*>(object + 0x36) = static_cast<uint8_t>(arg5);
    *reinterpret_cast<volatile uint32_t*>(object + 0x10) =
        selector == 6 ? 0x035ab9ff : 0x320202ff;

    if (object[8] != 0) {
        *reinterpret_cast<volatile uint8_t*>(object + 0x2e) = 1;
        battle_func_002b8d24(object, object[9]);
        *reinterpret_cast<volatile uint8_t*>(object + 8) = 3;
        *reinterpret_cast<volatile uint8_t*>(object + 0x35) = 0;
        return 0;
    } else {
        uint32_t query_a = engine_func_002c1f28();
        if (query_a != 0 && camp_func_002b89a0() != 0) return 1;
        engine_func_0028e974(object, raw_r0, raw_r1, selector, 0x1a, 1, arg6);
    }

    if (selector == 11 || selector == 19)
        *reinterpret_cast<volatile uint32_t*>(object + 0x20) =
            engine_func_002b787c(*reinterpret_cast<volatile uint32_t*>(object + 4));
    if (object[0x35] == 0)
        camp_func_0028df98(object, object[9]);
    if (arg5 != 0) {
        uint32_t global_object = *reinterpret_cast<volatile uint32_t*>(object + 4);
        ui_func_002c4bf0(global_object, 0x20);
        global_object = *reinterpret_cast<volatile uint32_t*>(object + 4);
        func_002b90f0(global_object, 0x40);
    }
    *reinterpret_cast<volatile uint8_t*>(object + 0xa12) = 0;
    for (uint32_t i = 0; i != 6; ++i) {
        *reinterpret_cast<volatile uint8_t*>(object + 0xa13 + i) =
            static_cast<uint8_t>(func_002f5b2c(i));
        *reinterpret_cast<volatile uint16_t*>(object + 0xa1a + 2 * i) =
            static_cast<uint16_t>(func_002d65b4(i));
    }
    uint8_t row = object[9];
    if (row >= 7 && row <= 9 && camp_func_0028df70(0) == 5) {
        *reinterpret_cast<volatile uint8_t*>(object + 0xa26) = 1;
        *reinterpret_cast<volatile uint8_t*>(object + 0xa12) =
            static_cast<uint8_t>(camp_func_002b8ccc());
        script_vm_func_002b8b78(0xdc);
    }
    if (selector == 19) engine_func_002b8584(1);
    return 0;
}


// DECOMP_FUNC(0x0032b0b4, 820)
extern "C" __attribute__((naked)) void ui_func_0032b0b4() {
    asm volatile(
        ".arm\n"
        ".hword 0x40f0, 0xe92d, 0x1000, 0xe3a0\n"
        ".hword 0x02d8, 0xe59f, 0x72d8, 0xe59f\n"
        ".hword 0x8b08, 0xed2d, 0xd014, 0xe24d\n"
        ".hword 0x4000, 0xe590, 0x5000, 0xe597\n"
        ".hword 0x0001, 0xe3a0, 0x6ba7, 0xebfe\n"
        ".hword 0x5a01, 0xe285, 0x5f93, 0xe285\n"
        ".hword 0x6000, 0xe3a0, 0x1000, 0xe595\n"
        ".hword 0x2001, 0xe281, 0x3101, 0xe085\n"
        ".hword 0x1008, 0xe593, 0x3102, 0xe085\n"
        ".hword 0x2000, 0xe585, 0x0008, 0xe583\n"
        ".hword 0x2018, 0xe5d5, 0x0000, 0xe352\n"
        ".hword 0x0000, 0x0151, 0x0002, 0x0a00\n"
        ".hword 0x101c, 0xe595, 0xff31, 0xe12f\n"
        ".hword 0x6018, 0xe5c5, 0x0020, 0xe5d4\n"
        ".hword 0x11be, 0xe1d4, 0x0000, 0xe350\n"
        ".hword 0x0000, 0xe3a0, 0x0007, 0x0a00\n"
        ".hword 0x0002, 0xe351, 0x0e32, 0x03a0\n"
        ".hword 0x000b, 0x0a00, 0x225c, 0xe59f\n"
        ".hword 0x0003, 0xe351, 0x0004, 0x1351\n"
        ".hword 0x0010, 0x0a00, 0x0006, 0xea00\n"
        ".hword 0x0002, 0xe351, 0x0248, 0x059f\n"
        ".hword 0x0003, 0x0a00, 0x2244, 0xe59f\n"
        ".hword 0x0003, 0xe351, 0x0004, 0x1351\n"
        ".hword 0x0008, 0x0a00, 0x1004, 0xe594\n"
        ".hword 0x0003, 0xe351, 0x0007, 0x0a00\n"
        ".hword 0x0004, 0xe351, 0x0005, 0x1351\n"
        ".hword 0x000b, 0x0a00, 0x0006, 0xe351\n"
        ".hword 0x0006, 0x0a00, 0x0067, 0xea00\n"
        ".hword 0x0002, 0xe1a0, 0xfff4, 0xeaff\n"
        ".hword 0x1008, 0xe594, 0x0000, 0xe151\n"
        ".hword 0x0003, 0xca00, 0x0061, 0xea00\n"
        ".hword 0x0008, 0xe594, 0x0014, 0xe350\n"
        ".hword 0x005e, 0xaa00, 0xf000, 0xe320\n"
        ".hword 0xd709, 0xebfd, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0x6812, 0xebfe\n"
        ".hword 0x8a77, 0xeddf, 0xba77, 0xeddf\n"
        ".hword 0x8a02, 0xedcd, 0x8a03, 0xedcd\n"
        ".hword 0x8a04, 0xedcd, 0x0a04, 0xedd0\n"
        ".hword 0x1a01, 0xedd0, 0x0a06, 0xed90\n"
        ".hword 0x1a03, 0xed90, 0x0ae1, 0xee70\n"
        ".hword 0x9a6f, 0xeddf, 0x0a41, 0xee30\n"
        ".hword 0x5000, 0xe1a0, 0x1aa0, 0xee20\n"
        ".hword 0x1aa8, 0xee08, 0x1a00, 0xee00\n"
        ".hword 0xbac1, 0xeeb1, 0x1a8b, 0xee8b\n"
        ".hword 0xaa81, 0xee20, 0x9a01, 0xee20\n"
        ".hword 0xaa81, 0xee68, 0x0a8a, 0xee28\n"
        ".hword 0x0aaa, 0xee08, 0x0a89, 0xee09\n"
        ".hword 0x0a10, 0xee10, 0x05fe, 0xe350\n"
        ".hword 0x8a68, 0x0eb0, 0x000d, 0x0a00\n"
        ".hword 0x0a10, 0xee10, 0x1101, 0xe280\n"
        ".hword 0x1502, 0xe291, 0x8a5b, 0x0d9f\n"
        ".hword 0x0008, 0x0a00, 0x74df, 0xebfd\n"
        ".hword 0x0a59, 0xeddf, 0x8a20, 0xee20\n"
        ".hword 0x0a8a, 0xee29, 0x0a68, 0xeef0\n"
        ".hword 0x0ac9, 0xee00, 0x0ae8, 0xeeb4\n"
        ".hword 0xfa10, 0xeef1, 0x8a48, 0x3eb1\n"
        ".hword 0x0a53, 0xed9f, 0x1a04, 0xed95\n"
        ".hword 0x1a50, 0xeddf, 0x2a00, 0xee6a\n"
        ".hword 0x0a80, 0xee6a, 0x0a00, 0xee29\n"
        ".hword 0x0008, 0xe28d, 0x1a02, 0xec80\n"
        ".hword 0x2a06, 0xed95, 0x2a04, 0xed8d\n"
        ".hword 0x1a22, 0xee31, 0x0aa0, 0xee71\n"
        ".hword 0x0a00, 0xee32, 0x1a4a, 0xeddf\n"
        ".hword 0x1a02, 0xed8d, 0x0a03, 0xedcd\n"
        ".hword 0x0a04, 0xed8d, 0x0a43, 0xed9f\n"
        ".hword 0x0a43, 0xeddf, 0x1a43, 0xed9f\n"
        ".hword 0x8a40, 0xee7b, 0x0a0a, 0xed95\n"
        ".hword 0x0a20, 0xee20, 0x0a01, 0xee20\n"
        ".hword 0x0a21, 0xee20, 0x7451, 0xebfd\n"
        ".hword 0x1a3e, 0xed9f, 0x0004, 0xe594\n"
        ".hword 0x0a00, 0xeec1, 0x0006, 0xe350\n"
        ".hword 0x0aa0, 0xee88, 0x0003, 0x1a00\n"
        ".hword 0x0a02, 0xedd4, 0x1a38, 0xed9f\n"
        ".hword 0x0ae0, 0xeef8, 0xbac1, 0xee40\n"
        ".hword 0x0a36, 0xeddf, 0x3008, 0xe28d\n"
        ".hword 0x1000, 0xe3a0, 0x0aa0, 0xee6b\n"
        ".hword 0x0ae0, 0xeefc, 0x0a90, 0xee10\n"
        ".hword 0x0a48, 0xeef0, 0x0c01, 0xe240\n"
        ".hword 0x0041, 0xe88d, 0x207c, 0xe5b4\n"
        ".hword 0x0004, 0xe594, 0x4c17, 0xeb00\n"
        ".hword 0x0000, 0xe597, 0x4a01, 0xe280\n"
        ".hword 0x4f93, 0xe284, 0x0000, 0xe594\n"
        ".hword 0x1100, 0xe084, 0x0001, 0xe240\n"
        ".hword 0x1008, 0xe591, 0x0000, 0xe584\n"
        ".hword 0x0100, 0xe084, 0x2018, 0xe5d4\n"
        ".hword 0x0008, 0xe590, 0x0000, 0xe352\n"
        ".hword 0x0000, 0x0151, 0x0002, 0x0a00\n"
        ".hword 0x101c, 0xe594, 0xff31, 0xe12f\n"
        ".hword 0x6018, 0xe5c4, 0x0000, 0xe597\n"
        ".hword 0x59f8, 0xebfe, 0x0000, 0xe597\n"
        ".hword 0xf000, 0xe320, 0x59cb, 0xebfe\n"
        ".hword 0xd014, 0xe28d, 0x0000, 0xe3a0\n"
        ".hword 0x8b08, 0xecbd, 0x80f0, 0xe8bd\n"
        ".hword 0xdd90, 0x0043, 0xea00, 0x0044\n"
        ".hword 0x0375, 0x0000, 0x028e, 0x0000\n"
        ".hword 0x0311, 0x0000, 0x0000, 0x0000\n"
        ".hword 0x0000, 0x3f80, 0x0000, 0xbf80\n"
        ".hword 0x0000, 0x4300, 0xf983, 0x4222\n"
        ".hword 0x0000, 0xc0f0, 0x0000, 0x41a0\n"
        ".hword 0x0000, 0xc1a0, 0x0000, 0x3f00\n"
        ".hword 0x0b61, 0x3bb6, 0x0fdb, 0x4049\n"
        ".hword 0x0000, 0x42f0, 0xcccd, 0x3d4c\n"
        ".hword 0x0000, 0x437f\n"
    );
};

// DECOMP_FUNC(0x003ad98c, 844)
extern "C" __attribute__((naked)) void battle_func_003ad98c() {
    asm volatile(
        ".arm\n"
        ".hword 0x4ff0, 0xe92d, 0xa000, 0xe3a0\n"
        ".hword 0xb001, 0xe1a0, 0x4304, 0xe59f\n"
        ".hword 0x0304, 0xe59f, 0x8b02, 0xed2d\n"
        ".hword 0xd024, 0xe24d, 0x8020, 0xe594\n"
        ".hword 0x1004, 0xe280, 0x2065, 0xe280\n"
        ".hword 0x3066, 0xe280, 0xa008, 0xe780\n"
        ".hword 0xa008, 0xe781, 0xa008, 0xe7c2\n"
        ".hword 0x0008, 0xe288, 0xa008, 0xe7c3\n"
        ".hword 0x1d7c, 0xebf9, 0x0c22, 0xe288\n"
        ".hword 0x63a6, 0xebf9, 0x0a02, 0xe288\n"
        ".hword 0x100b, 0xe1a0, 0x0e46, 0xe280\n"
        ".hword 0xb02a, 0xebf7, 0x0020, 0xe594\n"
        ".hword 0xc2b8, 0xe59f, 0x1b01, 0xe280\n"
        ".hword 0x2b03, 0xe280, 0x1f81, 0xe281\n"
        ".hword 0x3a01, 0xe280, 0xa0b0, 0xe18c\n"
        ".hword 0x2008, 0xe282, 0x1c5d, 0xe281\n"
        ".hword 0x3f83, 0xe283, 0x2c5d, 0xe282\n"
        ".hword 0x3c5d, 0xe283, 0x0a07, 0xe280\n"
        ".hword 0xaab6, 0xe1c1, 0x0e51, 0xe280\n"
        ".hword 0xaab6, 0xe1c2, 0xaab6, 0xe1c3\n"
        ".hword 0xaab6, 0xe1c0, 0x0a07, 0xe288\n"
        ".hword 0x0eea, 0xe280, 0x4000, 0xe1a0\n"
        ".hword 0x001c, 0xe58d, 0x0020, 0xe58d\n"
        ".hword 0x563e, 0xebfc, 0x1260, 0xe59f\n"
        ".hword 0x0e5b, 0xe3a0, 0x20c0, 0xe3a0\n"
        ".hword 0x30c0, 0xe241, 0x3004, 0xe58d\n"
        ".hword 0x1014, 0xe58d, 0xc0e4, 0xe3a0\n"
        ".hword 0x30e4, 0xe243, 0x2008, 0xe58d\n"
        ".hword 0x0018, 0xe58d, 0x20fc, 0xe3a0\n"
        ".hword 0x10fc, 0xe243, 0x0004, 0xe1a0\n"
        ".hword 0xa00c, 0xe58d, 0xa010, 0xe58d\n"
        ".hword 0xc000, 0xe58d, 0x561a, 0xebfc\n"
        ".hword 0x8a88, 0xed9f, 0x7000, 0xe3a0\n"
        ".hword 0x90f1, 0xe3a0, 0x0218, 0xe59f\n"
        ".hword 0x5507, 0xe088, 0x4000, 0xe3a0\n"
        ".hword 0xa005, 0xe7c0, 0x0184, 0xe064\n"
        ".hword 0x0a48, 0xeeb0, 0x0100, 0xe080\n"
        ".hword 0x3020, 0xe59d, 0x0100, 0xe085\n"
        ".hword 0x6b1f, 0xe280, 0x6fd3, 0xe286\n"
        ".hword 0x2e7d, 0xe3a0, 0x100d, 0xe3a0\n"
        ".hword 0x0006, 0xe1a0, 0x9000, 0xe58d\n"
        ".hword 0x4014, 0xebfc, 0x1003, 0xe3a0\n"
        ".hword 0x0006, 0xe1a0, 0x4552, 0xebfc\n"
        ".hword 0x4001, 0xe284, 0x0005, 0xe354\n"
        ".hword 0xffed, 0xbaff, 0x4902, 0xe285\n"
        ".hword 0x0a48, 0xeeb0, 0x4f82, 0xe284\n"
        ".hword 0x3020, 0xe59d, 0x2ffa, 0xe3a0\n"
        ".hword 0x1015, 0xe3a0, 0x0004, 0xe1a0\n"
        ".hword 0x9000, 0xe58d, 0x4005, 0xebfc\n"
        ".hword 0x1009, 0xe3a0, 0x0004, 0xe1a0\n"
        ".hword 0x4543, 0xebfc, 0x4902, 0xe285\n"
        ".hword 0x0a48, 0xeeb0, 0x4fa5, 0xe284\n"
        ".hword 0x3020, 0xe59d, 0x2184, 0xe59f\n"
        ".hword 0x1015, 0xe3a0, 0x0004, 0xe1a0\n"
        ".hword 0x9000, 0xe58d, 0x3ff9, 0xebfc\n"
        ".hword 0x1009, 0xe3a0, 0x0004, 0xe1a0\n"
        ".hword 0x4537, 0xebfc, 0x0107, 0xe087\n"
        ".hword 0x1164, 0xe59f, 0x0280, 0xe088\n"
        ".hword 0x4b2f, 0xe280, 0x0a48, 0xeeb0\n"
        ".hword 0xa000, 0xe7c1, 0x4fd3, 0xe284\n"
        ".hword 0x3020, 0xe59d, 0x214c, 0xe59f\n"
        ".hword 0x1015, 0xe3a0, 0x0004, 0xe1a0\n"
        ".hword 0x9000, 0xe58d, 0x3fe9, 0xebfc\n"
        ".hword 0x100a, 0xe3a0, 0x0004, 0xe1a0\n"
        ".hword 0x4527, 0xebfc, 0x7001, 0xe287\n"
        ".hword 0x0010, 0xe357, 0xffbe, 0xbaff\n"
        ".hword 0x7a07, 0xe288, 0x4000, 0xe3a0\n"
        ".hword 0x7eea, 0xe287, 0x0053, 0xe3a0\n"
        ".hword 0x0a48, 0xeeb0, 0x0094, 0xe001\n"
        ".hword 0x010c, 0xe59f, 0x210c, 0xe59f\n"
        ".hword 0x3007, 0xe1a0, 0x5101, 0xe088\n"
        ".hword 0x6a0e, 0xe285, 0xa0b5, 0xe180\n"
        ".hword 0x60ac, 0xe286, 0x1015, 0xe3a0\n"
        ".hword 0x0006, 0xe1a0, 0x9000, 0xe58d\n"
        ".hword 0x3fd2, 0xebfc, 0x100b, 0xe3a0\n"
        ".hword 0x0006, 0xe1a0, 0x4510, 0xebfc\n"
        ".hword 0x5a0e, 0xe285, 0x0a48, 0xeeb0\n"
        ".hword 0x5f4e, 0xe285, 0x20d0, 0xe59f\n"
        ".hword 0x3007, 0xe1a0, 0x1015, 0xe3a0\n"
        ".hword 0x0005, 0xe1a0, 0x9000, 0xe58d\n"
        ".hword 0x3fc6, 0xebfc, 0x100c, 0xe3a0\n"
        ".hword 0x0005, 0xe1a0, 0x4504, 0xebfc\n"
        ".hword 0x4001, 0xe284, 0x000c, 0xe354\n"
        ".hword 0xffdf, 0xbaff, 0x100b, 0xe1a0\n"
        ".hword 0x0fe9, 0xe3a0, 0x51f0, 0xebfc\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x3e75, 0x1bfe, 0x208c, 0xe59f\n"
        ".hword 0x1a05, 0xe288, 0x1e4d, 0xe281\n"
        ".hword 0x0a48, 0xeeb0, 0x0008, 0xe782\n"
        ".hword 0xa000, 0xe5c1, 0x00e0, 0xe59b\n"
        ".hword 0x2000, 0xe3a0, 0x0701, 0xe310\n"
        ".hword 0x0001, 0xe3a0, 0x0000, 0x15c1\n"
        ".hword 0x0000, 0xe58d, 0x0901, 0xe288\n"
        ".hword 0x0dfb, 0xe280, 0x301c, 0xe59d\n"
        ".hword 0x100e, 0xe3a0, 0x4000, 0xe1a0\n"
        ".hword 0x3fa8, 0xebfc, 0xd024, 0xe28d\n"
        ".hword 0x0004, 0xe1a0, 0x8b02, 0xecbd\n"
        ".hword 0x2000, 0xe3a0, 0x4ff0, 0xe8bd\n"
        ".hword 0x100d, 0xe3a0, 0x06eb, 0xeafc\n"
        ".hword 0x9c88, 0x0043, 0x7e38, 0x0000\n"
        ".hword 0x5da6, 0x0000, 0x1cbc, 0x0040\n"
        ".hword 0x0000, 0x3f80, 0x832c, 0x0000\n"
        ".hword 0x03ea, 0x0000, 0xbfe4, 0x0000\n"
        ".hword 0x03ee, 0x0000, 0xe1c4, 0x0000\n"
        ".hword 0x0bba, 0x0000, 0x0bbe, 0x0000\n"
        ".hword 0x7e20, 0x0000\n"
    );
};

// DECOMP_FUNC(0x00198fcc, 848)
extern "C" __attribute__((naked)) void camp_func_00198fcc() {
    asm volatile(
        ".arm\n"
        ".hword 0x43f0, 0xe92d, 0x5b15, 0xe280\n"
        ".hword 0x4000, 0xe1a0, 0x5fd6, 0xe285\n"
        ".hword 0x0a05, 0xe280, 0x332c, 0xe59f\n"
        ".hword 0x1000, 0xe595, 0xd00c, 0xe24d\n"
        ".hword 0x202c, 0xe3a0, 0x0e76, 0xe280\n"
        ".hword 0x7bc3, 0xfb04, 0x7000, 0xe3a0\n"
        ".hword 0x7000, 0xe58d, 0x7004, 0xe58d\n"
        ".hword 0x6000, 0xe595, 0x0007, 0xe1a0\n"
        ".hword 0x8001, 0xe3a0, 0x0000, 0xe356\n"
        ".hword 0x002b, 0xda00, 0x2b15, 0xe284\n"
        ".hword 0x3b15, 0xe284, 0x0001, 0xe316\n"
        ".hword 0x100d, 0xe1a0, 0xc000, 0xe3a0\n"
        ".hword 0x2fd1, 0xe282, 0x3fc6, 0xe283\n"
        ".hword 0x0003, 0x0a00, 0xc001, 0xe3a0\n"
        ".hword 0x202c, 0xe282, 0x302c, 0xe283\n"
        ".hword 0x8000, 0xe58d, 0xe0c6, 0xe1b0\n"
        ".hword 0x001d, 0x0a00, 0x0000, 0xe35c\n"
        ".hword 0x0006, 0xda00, 0x0a0b, 0xed92\n"
        ".hword 0x0a0b, 0xedd3, 0x0ac0, 0xeef4\n"
        ".hword 0xfa10, 0xeef1, 0x0001, 0x2a00\n"
        ".hword 0x0001, 0xe350, 0x0001, 0xb280\n"
        ".hword 0x9001, 0xe28c, 0x0000, 0xe359\n"
        ".hword 0x9100, 0xe791, 0x9001, 0xe289\n"
        ".hword 0x9100, 0xe781, 0x0006, 0xda00\n"
        ".hword 0x0a16, 0xed92, 0x0a16, 0xedd3\n"
        ".hword 0x0ac0, 0xeef4, 0xfa10, 0xeef1\n"
        ".hword 0x0001, 0x2a00, 0x0001, 0xe350\n"
        ".hword 0x0001, 0xb280, 0xe001, 0xe25e\n"
        ".hword 0x9100, 0xe791, 0x2058, 0xe282\n"
        ".hword 0x3058, 0xe283, 0x9001, 0xe289\n"
        ".hword 0xc002, 0xe28c, 0x9100, 0xe781\n"
        ".hword 0xffe1, 0x1aff, 0x2c57, 0xe284\n"
        ".hword 0x005e, 0xe5d2, 0x0000, 0xe350\n"
        ".hword 0x000e, 0x1a00, 0x1000, 0xe59d\n"
        ".hword 0x0c57, 0xe284, 0x005f, 0xe280\n"
        ".hword 0x0000, 0xe351, 0x1004, 0xe59d\n"
        ".hword 0x0002, 0xca00, 0x0000, 0xe351\n"
        ".hword 0x0003, 0xca00, 0x0005, 0xea00\n"
        ".hword 0x0000, 0xe351, 0x7000, 0xc5c0\n"
        ".hword 0x0000, 0xca00, 0x8000, 0xe5c0\n"
        ".hword 0x0204, 0xe59f, 0x8004, 0xe7c0\n"
        ".hword 0x0000, 0xe356, 0x0000, 0xe3a0\n"
        ".hword 0x006b, 0xda00, 0xc000, 0xe59d\n"
        ".hword 0x3004, 0xe59d, 0x1004, 0xe26c\n"
        ".hword 0xc005, 0xe26c, 0xe004, 0xe263\n"
        ".hword 0x6005, 0xe263, 0x3fa1, 0xe081\n"
        ".hword 0xcfac, 0xe08c, 0xefae, 0xe08e\n"
        ".hword 0x6fa6, 0xe086, 0x105f, 0xe5d2\n"
        ".hword 0x0000, 0xe351, 0x1000, 0xe59d\n"
        ".hword 0x0025, 0x0a00, 0x0000, 0xe151\n"
        ".hword 0x1004, 0xd59d, 0x0001, 0xe311\n"
        ".hword 0x0010, 0x0a00, 0x1005, 0xe261\n"
        ".hword 0x8080, 0xe080, 0x1fa1, 0xe081\n"
        ".hword 0x10c1, 0xe080, 0x7c01, 0xe281\n"
        ".hword 0x9c01, 0xe281, 0x1180, 0xe088\n"
        ".hword 0x70a1, 0xe287, 0x1101, 0xe084\n"
        ".hword 0x8901, 0xe281, 0x8d5e, 0xe288\n"
        ".hword 0x1b15, 0xe281, 0x1fe1, 0xe281\n"
        ".hword 0x90aa, 0xe289, 0x7000, 0xe588\n"
        ".hword 0x9000, 0xe581, 0x0044, 0xea00\n"
        ".hword 0x1004, 0xe261, 0x9080, 0xe080\n"
        ".hword 0x1fa1, 0xe081, 0x10c1, 0xe080\n"
        ".hword 0x7c01, 0xe281, 0x8c01, 0xe281\n"
        ".hword 0x1180, 0xe089, 0x70a6, 0xe287\n"
        ".hword 0x1101, 0xe084, 0x9901, 0xe281\n"
        ".hword 0x9d5e, 0xe289, 0x1b15, 0xe281\n"
        ".hword 0x1fe1, 0xe281, 0x80af, 0xe288\n"
        ".hword 0x7000, 0xe589, 0x8000, 0xe581\n"
        ".hword 0x0033, 0xea00, 0x0000, 0xe151\n"
        ".hword 0x001e, 0xda00, 0x0001, 0xe311\n"
        ".hword 0x000d, 0x0a00, 0x10cc, 0xe080\n"
        ".hword 0x9080, 0xe080, 0x7c01, 0xe281\n"
        ".hword 0x8f55, 0xe281, 0x1180, 0xe089\n"
        ".hword 0x704a, 0xe287, 0x1101, 0xe084\n"
        ".hword 0x9901, 0xe281, 0x9d5e, 0xe289\n"
        ".hword 0x1b15, 0xe281, 0x1fe1, 0xe281\n"
        ".hword 0x7000, 0xe589, 0x8000, 0xe581\n"
        ".hword 0x0021, 0xea00, 0x10c3, 0xe080\n"
        ".hword 0x9080, 0xe080, 0x7c01, 0xe281\n"
        ".hword 0x8c01, 0xe281, 0x1180, 0xe089\n"
        ".hword 0x7065, 0xe287, 0x1101, 0xe084\n"
        ".hword 0x9901, 0xe281, 0x9d5e, 0xe289\n"
        ".hword 0x1b15, 0xe281, 0x1fe1, 0xe281\n"
        ".hword 0x806d, 0xe288, 0x7000, 0xe589\n"
        ".hword 0x8000, 0xe581, 0x0012, 0xea00\n"
        ".hword 0x1004, 0xe59d, 0x0001, 0xe311\n"
        ".hword 0x1000, 0xe59d, 0x1001, 0xe040\n"
        ".hword 0x0013, 0x0a00, 0x10c6, 0xe081\n"
        ".hword 0x8080, 0xe080, 0x7c01, 0xe281\n"
        ".hword 0x9c01, 0xe281, 0x1180, 0xe088\n"
        ".hword 0x703b, 0xe287, 0x1101, 0xe084\n"
        ".hword 0x8901, 0xe281, 0x8d5e, 0xe288\n"
        ".hword 0x1b15, 0xe281, 0x1fe1, 0xe281\n"
        ".hword 0x9045, 0xe289, 0x7000, 0xe588\n"
        ".hword 0x9000, 0xe581, 0x1000, 0xe595\n"
        ".hword 0x0001, 0xe280, 0x0000, 0xe151\n"
        ".hword 0xff9d, 0xcaff, 0xd00c, 0xe28d\n"
        ".hword 0x83f0, 0xe8bd, 0x10ce, 0xe081\n"
        ".hword 0x9080, 0xe080, 0x7c01, 0xe281\n"
        ".hword 0x8c01, 0xe281, 0x1180, 0xe089\n"
        ".hword 0x7059, 0xe287, 0x1101, 0xe084\n"
        ".hword 0x9901, 0xe281, 0x9d5e, 0xe289\n"
        ".hword 0x1b15, 0xe281, 0x1fe1, 0xe281\n"
        ".hword 0x8061, 0xe288, 0x7000, 0xe589\n"
        ".hword 0x8000, 0xe581, 0xffea, 0xeaff\n"
        ".hword 0x1c34, 0x001d, 0x575e, 0x0000\n"
    );
};

// DECOMP_FUNC(0x00199700, 848)
extern "C" __attribute__((naked)) void camp_func_00199700() {
    asm volatile(
        ".arm\n"
        ".hword 0x4070, 0xe92d, 0x4000, 0xe1a0\n"
        ".hword 0x02f0, 0xe590, 0x0014, 0xe350\n"
        ".hword 0xf100, 0x379f, 0x8070, 0xe8bd\n"
        ".hword 0x9714, 0x0019, 0x9768, 0x0019\n"
        ".hword 0x9778, 0x0019, 0x9794, 0x0019\n"
        ".hword 0x97b0, 0x0019, 0x97f8, 0x0019\n"
        ".hword 0x9850, 0x0019, 0x9878, 0x0019\n"
        ".hword 0x9768, 0x0019, 0x98a0, 0x0019\n"
        ".hword 0x98d8, 0x0019, 0x9910, 0x0019\n"
        ".hword 0x9948, 0x0019, 0x9970, 0x0019\n"
        ".hword 0x98d8, 0x0019, 0x998c, 0x0019\n"
        ".hword 0x99bc, 0x0019, 0x99e4, 0x0019\n"
        ".hword 0x9a00, 0x0019, 0x9a28, 0x0019\n"
        ".hword 0x0020, 0xe284, 0x4070, 0xe8bd\n"
        ".hword 0x1002, 0xe3a0, 0x962d, 0xea04\n"
        ".hword 0x1002, 0xe3a0, 0x0020, 0xe284\n"
        ".hword 0x962a, 0xeb04, 0x00ac, 0xe284\n"
        ".hword 0x4070, 0xe8bd, 0x1003, 0xe3a0\n"
        ".hword 0x9626, 0xea04, 0x1004, 0xe3a0\n"
        ".hword 0x0020, 0xe284, 0x9623, 0xeb04\n"
        ".hword 0x00ac, 0xe284, 0x4070, 0xe8bd\n"
        ".hword 0x1005, 0xe3a0, 0x961f, 0xea04\n"
        ".hword 0x1002, 0xe3a0, 0x0020, 0xe284\n"
        ".hword 0x961c, 0xeb04, 0x5000, 0xe3a0\n"
        ".hword 0x1c42, 0xe285, 0x0185, 0xe065\n"
        ".hword 0x1069, 0xe281, 0x0100, 0xe080\n"
        ".hword 0x6100, 0xe084, 0x00ac, 0xe286\n"
        ".hword 0x7e40, 0xeb04, 0x00ac, 0xe286\n"
        ".hword 0x1006, 0xe3a0, 0x9611, 0xeb04\n"
        ".hword 0x5001, 0xe285, 0x0004, 0xe355\n"
        ".hword 0xfff2, 0xbaff, 0x8070, 0xe8bd\n"
        ".hword 0x1238, 0xe59f, 0x00ac, 0xe284\n"
        ".hword 0x7e36, 0xeb04, 0x1230, 0xe59f\n"
        ".hword 0x0f4e, 0xe284, 0x7e33, 0xeb04\n"
        ".hword 0x5228, 0xe59f, 0x1018, 0xe3a0\n"
        ".hword 0x00ac, 0xe284, 0x2005, 0xe1a0\n"
        ".hword 0xf24b, 0xeb03, 0x2005, 0xe1a0\n"
        ".hword 0x1018, 0xe3a0, 0x0f4e, 0xe284\n"
        ".hword 0xf247, 0xeb03, 0x1007, 0xe3a0\n"
        ".hword 0x00ac, 0xe284, 0x95fb, 0xeb04\n"
        ".hword 0x0f4e, 0xe284, 0x4070, 0xe8bd\n"
        ".hword 0x1008, 0xe3a0, 0x95f7, 0xea04\n"
        ".hword 0x11ec, 0xe59f, 0x00ac, 0xe284\n"
        ".hword 0x7e20, 0xeb04, 0x1002, 0xe3a0\n"
        ".hword 0x0020, 0xe284, 0x95f1, 0xeb04\n"
        ".hword 0x00ac, 0xe284, 0x4070, 0xe8bd\n"
        ".hword 0x1009, 0xe3a0, 0x95ed, 0xea04\n"
        ".hword 0x11c8, 0xe59f, 0x00ac, 0xe284\n"
        ".hword 0x7e16, 0xeb04, 0x1002, 0xe3a0\n"
        ".hword 0x0020, 0xe284, 0x95e7, 0xeb04\n"
        ".hword 0x00ac, 0xe284, 0x4070, 0xe8bd\n"
        ".hword 0x100a, 0xe3a0, 0x95e3, 0xea04\n"
        ".hword 0x02f8, 0xe594, 0x1001, 0xe3a0\n"
        ".hword 0x2080, 0xe080, 0x0380, 0xe062\n"
        ".hword 0x1180, 0xe081, 0x00ac, 0xe284\n"
        ".hword 0x7e08, 0xeb04, 0x1002, 0xe3a0\n"
        ".hword 0x0020, 0xe284, 0x95d9, 0xeb04\n"
        ".hword 0x00ac, 0xe284, 0x4070, 0xe8bd\n"
        ".hword 0x100b, 0xe3a0, 0x95d5, 0xea04\n"
        ".hword 0x12f8, 0xe594, 0x0001, 0xe3a0\n"
        ".hword 0x2081, 0xe081, 0x1381, 0xe062\n"
        ".hword 0x1181, 0xe080, 0x00ac, 0xe284\n"
        ".hword 0x7dfa, 0xeb04, 0x1002, 0xe3a0\n"
        ".hword 0x0020, 0xe284, 0x95cb, 0xeb04\n"
        ".hword 0x00ac, 0xe284, 0x4070, 0xe8bd\n"
        ".hword 0x1002, 0xe3a0, 0x95c7, 0xea04\n"
        ".hword 0x12f8, 0xe594, 0x0001, 0xe3a0\n"
        ".hword 0x2081, 0xe081, 0x1381, 0xe062\n"
        ".hword 0x1181, 0xe080, 0x00ac, 0xe284\n"
        ".hword 0x7dec, 0xeb04, 0x1002, 0xe3a0\n"
        ".hword 0x0020, 0xe284, 0x95bd, 0xeb04\n"
        ".hword 0x00ac, 0xe284, 0x4070, 0xe8bd\n"
        ".hword 0x100c, 0xe3a0, 0x95b9, 0xea04\n"
        ".hword 0x1002, 0xe3a0, 0x0020, 0xe284\n"
        ".hword 0x95b6, 0xeb04, 0x1002, 0xe3a0\n"
        ".hword 0x00ac, 0xe284, 0x95b3, 0xeb04\n"
        ".hword 0x0f4e, 0xe284, 0x4070, 0xe8bd\n"
        ".hword 0x100d, 0xe3a0, 0x95af, 0xea04\n"
        ".hword 0x1002, 0xe3a0, 0x0020, 0xe284\n"
        ".hword 0x95ac, 0xeb04, 0x00ac, 0xe284\n"
        ".hword 0x4070, 0xe8bd, 0x100f, 0xe3a0\n"
        ".hword 0x95a8, 0xea04, 0x02f8, 0xe594\n"
        ".hword 0x1ffa, 0xe3a0, 0x0190, 0xe001\n"
        ".hword 0x00ac, 0xe284, 0x7dcf, 0xeb04\n"
        ".hword 0x1002, 0xe3a0, 0x0020, 0xe284\n"
        ".hword 0x95a0, 0xeb04, 0x00ac, 0xe284\n"
        ".hword 0x4070, 0xe8bd, 0x1010, 0xe3a0\n"
        ".hword 0x959c, 0xea04, 0x1002, 0xe3a0\n"
        ".hword 0x0020, 0xe284, 0x9599, 0xeb04\n"
        ".hword 0x1002, 0xe3a0, 0x00ac, 0xe284\n"
        ".hword 0x9596, 0xeb04, 0x0f4e, 0xe284\n"
        ".hword 0x4070, 0xe8bd, 0x100e, 0xe3a0\n"
        ".hword 0x9592, 0xea04, 0x1002, 0xe3a0\n"
        ".hword 0x0020, 0xe284, 0x958f, 0xeb04\n"
        ".hword 0x00ac, 0xe284, 0x4070, 0xe8bd\n"
        ".hword 0x1011, 0xe3a0, 0x958b, 0xea04\n"
        ".hword 0x1044, 0xe59f, 0x00ac, 0xe284\n"
        ".hword 0x7db4, 0xeb04, 0x1002, 0xe3a0\n"
        ".hword 0x0020, 0xe284, 0x9585, 0xeb04\n"
        ".hword 0x00ac, 0xe284, 0x4070, 0xe8bd\n"
        ".hword 0x1012, 0xe3a0, 0x9581, 0xea04\n"
        ".hword 0x0020, 0xe284, 0x4070, 0xe8bd\n"
        ".hword 0x1013, 0xe3a0, 0x957d, 0xea04\n"
        ".hword 0x59d9, 0x0000, 0x59da, 0x0000\n"
        ".hword 0x59db, 0x0000, 0x7149, 0x0000\n"
        ".hword 0x30b1, 0x0001, 0x7071, 0x0006\n"
    );
};

// DECOMP_FUNC(0x0031c494, 856)
extern "C" __attribute__((naked)) void script_vm_func_0031c494() {
    asm volatile(
        ".arm\n"
        ".hword 0x41f0, 0xe92d, 0x5000, 0xe3a0\n"
        ".hword 0x0000, 0xe350, 0x6001, 0xe1a0\n"
        ".hword 0x7002, 0xe1a0, 0x4005, 0xe1a0\n"
        ".hword 0x0006, 0xaa00, 0x688d, 0xebfe\n"
        ".hword 0x5000, 0xe1a0, 0x0001, 0xe3a0\n"
        ".hword 0xe6ba, 0xebfd, 0x0000, 0xe350\n"
        ".hword 0x00ba, 0x1a00, 0x0009, 0xea00\n"
        ".hword 0xf000, 0xe320, 0x3143, 0xebfe\n"
        ".hword 0x4000, 0xe1b0, 0xf000, 0xe320\n"
        ".hword 0x00b4, 0x0a00, 0x1001, 0xe3a0\n"
        ".hword 0x0a58, 0xebfe, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x00af, 0x1a00\n"
        ".hword 0x16b0, 0xe1d6, 0x02e8, 0xe59f\n"
        ".hword 0x6000, 0xe3a0, 0x101f, 0xe241\n"
        ".hword 0x0005, 0xe351, 0xf101, 0x379f\n"
        ".hword 0x00a8, 0xea00, 0xc524, 0x0031\n"
        ".hword 0xc5a4, 0x0031, 0xc624, 0x0031\n"
        ".hword 0xc6a4, 0x0031, 0xc724, 0x0031\n"
        ".hword 0x0000, 0xe355, 0x0009, 0x0a00\n"
        ".hword 0x11f2, 0xe1d5, 0x0000, 0xe151\n"
        ".hword 0x009a, 0xaa00, 0x0000, 0xe357\n"
        ".hword 0x1003, 0x0281, 0x11b2, 0x01c5\n"
        ".hword 0x11f2, 0xe1d5, 0x0ffa, 0xe351\n"
        ".hword 0x01b2, 0xa1c5, 0x0094, 0xea00\n"
        ".hword 0x10f4, 0xe1d4, 0x0000, 0xe151\n"
        ".hword 0x6001, 0xa3a0, 0x0005, 0xaa00\n"
        ".hword 0x0000, 0xe357, 0x1003, 0x0281\n"
        ".hword 0x10b4, 0x01c4, 0x10f4, 0xe1d4\n"
        ".hword 0x0ffa, 0xe351, 0x00b4, 0xa1c4\n"
        ".hword 0x12f0, 0xe1d4, 0x0000, 0xe151\n"
        ".hword 0x0086, 0xaa00, 0x0000, 0xe357\n"
        ".hword 0x1003, 0x0281, 0x12b0, 0x01c4\n"
        ".hword 0x12f0, 0xe1d4, 0x0ffa, 0xe351\n"
        ".hword 0x02b0, 0xa1c4, 0x0080, 0xea00\n"
        ".hword 0x0000, 0xe355, 0x0009, 0x0a00\n"
        ".hword 0x11f6, 0xe1d5, 0x0000, 0xe151\n"
        ".hword 0x007a, 0xaa00, 0x0000, 0xe357\n"
        ".hword 0x1003, 0x0281, 0x11b6, 0x01c5\n"
        ".hword 0x11f6, 0xe1d5, 0x0ffa, 0xe351\n"
        ".hword 0x01b6, 0xa1c5, 0x0074, 0xea00\n"
        ".hword 0x10f8, 0xe1d4, 0x0000, 0xe151\n"
        ".hword 0x6001, 0xa3a0, 0x0005, 0xaa00\n"
        ".hword 0x0000, 0xe357, 0x1003, 0x0281\n"
        ".hword 0x10b8, 0x01c4, 0x10f8, 0xe1d4\n"
        ".hword 0x0ffa, 0xe351, 0x00b8, 0xa1c4\n"
        ".hword 0x12f4, 0xe1d4, 0x0000, 0xe151\n"
        ".hword 0x0066, 0xaa00, 0x0000, 0xe357\n"
        ".hword 0x1003, 0x0281, 0x12b4, 0x01c4\n"
        ".hword 0x12f4, 0xe1d4, 0x0ffa, 0xe351\n"
        ".hword 0x02b4, 0xa1c4, 0x0060, 0xea00\n"
        ".hword 0x0000, 0xe355, 0x0009, 0x0a00\n"
        ".hword 0x11f4, 0xe1d5, 0x0000, 0xe151\n"
        ".hword 0x005a, 0xaa00, 0x0000, 0xe357\n"
        ".hword 0x1003, 0x0281, 0x11b4, 0x01c5\n"
        ".hword 0x11f4, 0xe1d5, 0x0ffa, 0xe351\n"
        ".hword 0x01b4, 0xa1c5, 0x0054, 0xea00\n"
        ".hword 0x10f6, 0xe1d4, 0x0000, 0xe151\n"
        ".hword 0x6001, 0xa3a0, 0x0005, 0xaa00\n"
        ".hword 0x0000, 0xe357, 0x1003, 0x0281\n"
        ".hword 0x10b6, 0x01c4, 0x10f6, 0xe1d4\n"
        ".hword 0x0ffa, 0xe351, 0x00b6, 0xa1c4\n"
        ".hword 0x12f2, 0xe1d4, 0x0000, 0xe151\n"
        ".hword 0x0046, 0xaa00, 0x0000, 0xe357\n"
        ".hword 0x1003, 0x0281, 0x12b2, 0x01c4\n"
        ".hword 0x12f2, 0xe1d4, 0x0ffa, 0xe351\n"
        ".hword 0x02b2, 0xa1c4, 0x0040, 0xea00\n"
        ".hword 0x0000, 0xe355, 0x0009, 0x0a00\n"
        ".hword 0x11f8, 0xe1d5, 0x0000, 0xe151\n"
        ".hword 0x003a, 0xaa00, 0x0000, 0xe357\n"
        ".hword 0x1003, 0x0281, 0x11b8, 0x01c5\n"
        ".hword 0x11f8, 0xe1d5, 0x0ffa, 0xe351\n"
        ".hword 0x01b8, 0xa1c5, 0x0034, 0xea00\n"
        ".hword 0x10fa, 0xe1d4, 0x0000, 0xe151\n"
        ".hword 0x6001, 0xa3a0, 0x0005, 0xaa00\n"
        ".hword 0x0000, 0xe357, 0x1003, 0x0281\n"
        ".hword 0x10ba, 0x01c4, 0x10fa, 0xe1d4\n"
        ".hword 0x0ffa, 0xe351, 0x00ba, 0xa1c4\n"
        ".hword 0x12f6, 0xe1d4, 0x0000, 0xe151\n"
        ".hword 0x0026, 0xaa00, 0x0000, 0xe357\n"
        ".hword 0x1003, 0x0281, 0x12b6, 0x01c4\n"
        ".hword 0x12f6, 0xe1d4, 0x0ffa, 0xe351\n"
        ".hword 0x02b6, 0xa1c4, 0x0020, 0xea00\n"
        ".hword 0x0000, 0xe355, 0x0009, 0x0a00\n"
        ".hword 0x11fa, 0xe1d5, 0x0000, 0xe151\n"
        ".hword 0x001a, 0xaa00, 0x0000, 0xe357\n"
        ".hword 0x1003, 0x0281, 0x11ba, 0x01c5\n"
        ".hword 0x11fa, 0xe1d5, 0x0ffa, 0xe351\n"
        ".hword 0x01ba, 0xa1c5, 0x0014, 0xea00\n"
        ".hword 0x10fc, 0xe1d4, 0x0000, 0xe151\n"
        ".hword 0x6001, 0xa3a0, 0x0005, 0xaa00\n"
        ".hword 0x0000, 0xe357, 0x1003, 0x0281\n"
        ".hword 0x10bc, 0x01c4, 0x10fc, 0xe1d4\n"
        ".hword 0x0ffa, 0xe351, 0x00bc, 0xa1c4\n"
        ".hword 0x12f8, 0xe1d4, 0x0000, 0xe151\n"
        ".hword 0x0006, 0xaa00, 0x0000, 0xe357\n"
        ".hword 0x1003, 0x0281, 0x12b8, 0x01c4\n"
        ".hword 0x12f8, 0xe1d4, 0x0ffa, 0xe351\n"
        ".hword 0x02b8, 0xa1c4, 0x0000, 0xea00\n"
        ".hword 0x6001, 0xe3a0, 0x0006, 0xe197\n"
        ".hword 0x0002, 0x0a00, 0x000a, 0xea00\n"
        ".hword 0x0001, 0xe3a0, 0x81f0, 0xe8bd\n"
        ".hword 0x0000, 0xe355, 0x0004, 0x0a00\n"
        ".hword 0x0000, 0xe3a0, 0xf38f, 0xebfd\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0x0001, 0xea00, 0x0004, 0xe1a0\n"
        ".hword 0x005b, 0xebfe, 0x0006, 0xe1a0\n"
        ".hword 0x81f0, 0xe8bd, 0x03e7, 0x0000\n"
    );
};

// DECOMP_FUNC(0x00124c48, 864)
extern "C" __attribute__((naked)) void ui_func_00124c48() {
    asm volatile(
        ".arm\n"
        ".hword 0x47f0, 0xe92d, 0x8000, 0xe1a0\n"
        ".hword 0x029c, 0xe59f, 0x8b02, 0xed2d\n"
        ".hword 0xd008, 0xe24d, 0x6fd1, 0xeb06\n"
        ".hword 0x0000, 0xe350, 0x009f, 0x0a00\n"
        ".hword 0xa288, 0xe59f, 0x0008, 0xe59a\n"
        ".hword 0x0b01, 0xe280, 0x0fd5, 0xe280\n"
        ".hword 0x68bf, 0xeb06, 0x4000, 0xe1a0\n"
        ".hword 0x0008, 0xe59a, 0x0b01, 0xe280\n"
        ".hword 0x0fd5, 0xe280, 0x68b7, 0xeb06\n"
        ".hword 0x5000, 0xe1a0, 0x0008, 0xe59a\n"
        ".hword 0x0b01, 0xe280, 0x0fd5, 0xe280\n"
        ".hword 0x0a08, 0xed90, 0x0008, 0xe59a\n"
        ".hword 0x8a40, 0xeeb0, 0x18d2, 0xe1d0\n"
        ".hword 0x0000, 0xe351, 0x0006, 0xda00\n"
        ".hword 0x0e7e, 0xe280, 0x68ae, 0xeb06\n"
        ".hword 0x1008, 0xe59a, 0x4000, 0xe084\n"
        ".hword 0x0e7e, 0xe281, 0x68a7, 0xeb06\n"
        ".hword 0x5000, 0xe085, 0x1000, 0xe3a0\n"
        ".hword 0x0001, 0xe3a0, 0x84a6, 0xeb06\n"
        ".hword 0x7214, 0xe59f, 0x2000, 0xe1a0\n"
        ".hword 0x1003, 0xe3a0, 0x0000, 0xe597\n"
        ".hword 0x68b9, 0xeb06, 0x0a48, 0xeeb0\n"
        ".hword 0xf000, 0xe320, 0x6a83, 0xeb06\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0x6881, 0xeb06, 0x8a7b, 0xed9f\n"
        ".hword 0x0000, 0xe358, 0x000a, 0x0a00\n"
        ".hword 0x1094, 0xe3a0, 0x000e, 0xe3a0\n"
        ".hword 0x6a6a, 0xeb06, 0x0a48, 0xeeb0\n"
        ".hword 0x6000, 0xe1a0, 0x0000, 0xe597\n"
        ".hword 0x55cd, 0xeb06, 0x0ac0, 0xeebd\n"
        ".hword 0x0a10, 0xee10, 0x4000, 0xe084\n"
        ".hword 0x0003, 0xea00, 0x10c0, 0xe3a0\n"
        ".hword 0x000e, 0xe3a0, 0x6a5f, 0xeb06\n"
        ".hword 0x6000, 0xe1a0, 0x900b, 0xe3a0\n"
        ".hword 0x00fa, 0xe1d6, 0x2000, 0xe3a0\n"
        ".hword 0x100e, 0xe3a0, 0x0005, 0xe080\n"
        ".hword 0x0201, 0xe88d, 0x00f8, 0xe1d6\n"
        ".hword 0x3004, 0xe080, 0x0002, 0xe3a0\n"
        ".hword 0x69f6, 0xeb06, 0x0008, 0xe59a\n"
        ".hword 0x20fa, 0xe1d6, 0x10f8, 0xe1d6\n"
        ".hword 0x3000, 0xe3a0, 0x006c, 0xe590\n"
        ".hword 0x2005, 0xe082, 0x1004, 0xe081\n"
        ".hword 0x6446, 0xeb06, 0x0008, 0xe59a\n"
        ".hword 0x0080, 0xe5d0, 0x0000, 0xe350\n"
        ".hword 0x001c, 0x0a00, 0x0000, 0xe358\n"
        ".hword 0x0005, 0x0a00, 0x1c01, 0xe3a0\n"
        ".hword 0x000e, 0xe3a0, 0x6a43, 0xeb06\n"
        ".hword 0x6000, 0xe1a0, 0xf000, 0xe320\n"
        ".hword 0x0003, 0xea00, 0x1130, 0xe59f\n"
        ".hword 0x000e, 0xe3a0, 0x6a3d, 0xeb06\n"
        ".hword 0x6000, 0xe1a0, 0x200c, 0xe3a0\n"
        ".hword 0x00fa, 0xe1d6, 0x100e, 0xe3a0\n"
        ".hword 0x0005, 0xe080, 0x0201, 0xe88d\n"
        ".hword 0x00f8, 0xe1d6, 0x3004, 0xe080\n"
        ".hword 0x0002, 0xe3a0, 0x69d5, 0xeb06\n"
        ".hword 0x10fa, 0xe1d6, 0x0008, 0xe59a\n"
        ".hword 0x30f8, 0xe1d6, 0x2005, 0xe081\n"
        ".hword 0x1004, 0xe083, 0x0074, 0xe590\n"
        ".hword 0x3001, 0xe3a0, 0x6425, 0xeb06\n"
        ".hword 0x5008, 0xe59a, 0x00a1, 0xe5d5\n"
        ".hword 0x0000, 0xe350, 0x0025, 0x0a00\n"
        ".hword 0x0b01, 0xe285, 0x0fd5, 0xe280\n"
        ".hword 0x6000, 0xe1a0, 0x684e, 0xeb06\n"
        ".hword 0x4000, 0xe1a0, 0x0006, 0xe1a0\n"
        ".hword 0x6848, 0xeb06, 0x0a48, 0xeeb0\n"
        ".hword 0x8000, 0xe1a0, 0x0000, 0xe597\n"
        ".hword 0x5583, 0xeb06, 0x4a90, 0xee00\n"
        ".hword 0x1c01, 0xe3a0, 0x000e, 0xe3a0\n"
        ".hword 0x0ae0, 0xeef8, 0x0a20, 0xee30\n"
        ".hword 0x0ac0, 0xeebd, 0x6a10, 0xee10\n"
        ".hword 0x6a14, 0xeb06, 0x4000, 0xe1a0\n"
        ".hword 0x00fa, 0xe1d0, 0x2016, 0xe3a0\n"
        ".hword 0x100e, 0xe3a0, 0x0008, 0xe080\n"
        ".hword 0x0201, 0xe88d, 0x00f8, 0xe1d4\n"
        ".hword 0x3006, 0xe080, 0x0002, 0xe3a0\n"
        ".hword 0x69ac, 0xeb06, 0x209c, 0xe595\n"
        ".hword 0x10fa, 0xe1d4, 0x00f8, 0xe1d4\n"
        ".hword 0xc000, 0xe262, 0x2008, 0xe081\n"
        ".hword 0x1006, 0xe080, 0x3001, 0xe3a0\n"
        ".hword 0x000c, 0xe1a0, 0x63fb, 0xeb06\n"
        ".hword 0x0a0e, 0xed9f, 0x6a0f, 0xeb06\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0x680d, 0xeb06, 0x0000, 0xe597\n"
        ".hword 0x1003, 0xe3a0, 0x6827, 0xeb06\n"
        ".hword 0xd008, 0xe28d, 0x8b02, 0xecbd\n"
        ".hword 0x87f0, 0xe8bd, 0x0402, 0x0000\n"
        ".hword 0xe188, 0x0043, 0xea00, 0x0044\n"
        ".hword 0x3d71, 0x3e8a, 0x011f, 0x0000\n"
        ".hword 0x0000, 0x3f80, 0x1090, 0xe59f\n"
        ".hword 0x2004, 0xe591, 0x0000, 0xe352\n"
        ".hword 0x1000, 0x13a0, 0x001e, 0x0a00\n"
        ".hword 0x3101, 0xe082, 0x3494, 0xe5d3\n"
        ".hword 0x0000, 0xe153, 0x0003, 0x1a00\n"
        ".hword 0xc001, 0xe082, 0xc4b8, 0xe5dc\n"
        ".hword 0x0000, 0xe35c, 0x0011, 0x1a00\n"
        ".hword 0x0008, 0xe353, 0x0002, 0x0a00\n"
        ".hword 0x0009, 0xe353, 0x0007, 0x0a00\n"
        ".hword 0x000e, 0xea00, 0x0004, 0xe350\n"
        ".hword 0x000c, 0x1a00, 0x3001, 0xe082\n"
        ".hword 0x34b8, 0xe5d3, 0x0000, 0xe353\n"
        ".hword 0x0006, 0x1a00, 0x0007, 0xea00\n"
        ".hword 0x0003, 0xe350, 0x0005, 0x1a00\n"
        ".hword 0x3001, 0xe082, 0x34b8, 0xe5d3\n"
        ".hword 0x0000, 0xe353, 0x0001, 0x0a00\n"
        ".hword 0x0001, 0xe3a0, 0xff1e, 0xe12f\n"
        ".hword 0x1001, 0xe281, 0x0006, 0xe351\n"
        ".hword 0xffe0, 0xbaff, 0x0000, 0xe3a0\n"
        ".hword 0xff1e, 0xe12f, 0xda28, 0x0043\n"
    );
};

// DECOMP_FUNC(0x00341578, 892)
extern "C" __attribute__((naked)) void engine_func_00341578() {
    asm volatile(
        ".arm\n"
        ".hword 0x4ff0, 0xe92d, 0x5000, 0xe1a0\n"
        ".hword 0x0001, 0xe1a0, 0x8b02, 0xed2d\n"
        ".hword 0xd034, 0xe24d, 0x1226, 0xebfe\n"
        ".hword 0xb000, 0xe1a0, 0x0018, 0xe585\n"
        ".hword 0x1048, 0xe5b0, 0x2000, 0xe3a0\n"
        ".hword 0x8acb, 0xeddf, 0x0000, 0xe351\n"
        ".hword 0x0001, 0x1080, 0x0002, 0x01a0\n"
        ".hword 0x0000, 0xe350, 0x101c, 0x1280\n"
        ".hword 0x0044, 0xe59b, 0x1000, 0x03a0\n"
        ".hword 0x1004, 0xe58d, 0x0200, 0xe081\n"
        ".hword 0x0000, 0xe151, 0xa001, 0x13a0\n"
        ".hword 0x0030, 0xe58d, 0x008c, 0x0a00\n"
        ".hword 0x0004, 0xe59d, 0x100c, 0xe5b0\n"
        ".hword 0x0000, 0xe351, 0x4000, 0x1081\n"
        ".hword 0x4000, 0x03a0, 0x06f2, 0xebfe\n"
        ".hword 0x6000, 0xe1a0, 0xf000, 0xe320\n"
        ".hword 0x06f6, 0xebfe, 0x3008, 0xe3a0\n"
        ".hword 0x8014, 0xe28d, 0x7000, 0xe3a0\n"
        ".hword 0x1004, 0xe3a0, 0xa00c, 0xe5cd\n"
        ".hword 0x3010, 0xe58d, 0x0082, 0xe888\n"
        ".hword 0x2000, 0xe1a0, 0x701c, 0xe58d\n"
        ".hword 0x1024, 0xe58d, 0x0008, 0xe28d\n"
        ".hword 0x1006, 0xe1a0, 0x7020, 0xe58d\n"
        ".hword 0x7028, 0xe58d, 0xa02c, 0xe5cd\n"
        ".hword 0x4008, 0xe58d, 0x06d1, 0xebfe\n"
        ".hword 0x6290, 0xe59f, 0x4000, 0xe1b0\n"
        ".hword 0x0008, 0x0a00, 0x0000, 0xe594\n"
        ".hword 0x1008, 0xe590, 0x0004, 0xe1a0\n"
        ".hword 0xff31, 0xe12f, 0x0006, 0xe150\n"
        ".hword 0x0003, 0x0a00, 0x0000, 0xe590\n"
        ".hword 0x0000, 0xe350, 0xfffa, 0x1aff\n"
        ".hword 0x4007, 0xe1a0, 0x6260, 0xe59f\n"
        ".hword 0x0000, 0xe354, 0x0008, 0x0a00\n"
        ".hword 0x0000, 0xe594, 0x1008, 0xe590\n"
        ".hword 0x0004, 0xe1a0, 0xff31, 0xe12f\n"
        ".hword 0x0006, 0xe150, 0x0003, 0x0a00\n"
        ".hword 0x0000, 0xe590, 0x0000, 0xe350\n"
        ".hword 0xfffa, 0x1aff, 0x4007, 0xe1a0\n"
        ".hword 0x0000, 0xe595, 0x0100, 0xe085\n"
        ".hword 0x456c, 0xe580, 0x8268, 0xe594\n"
        ".hword 0x907c, 0xe59b, 0x0000, 0xe358\n"
        ".hword 0x0048, 0x0a00, 0x0008, 0xe598\n"
        ".hword 0x0000, 0xe359, 0x6000, 0xe3a0\n"
        ".hword 0x8a04, 0xed90, 0x0043, 0xda00\n"
        ".hword 0x1080, 0xe59b, 0x0080, 0xe28b\n"
        ".hword 0x0000, 0xe351, 0x0001, 0x1080\n"
        ".hword 0x0000, 0x03a0, 0x0000, 0xe350\n"
        ".hword 0x0004, 0x0a00, 0x0206, 0xe080\n"
        ".hword 0x1028, 0xe5b0, 0x0000, 0xe351\n"
        ".hword 0x0000, 0x03a0, 0x0001, 0x1080\n"
        ".hword 0x1040, 0xe3a0, 0x0008, 0xe58d\n"
        ".hword 0x1010, 0xe58d, 0x8a03, 0xed8d\n"
        ".hword 0x4008, 0xe28d, 0x7000, 0xe3a0\n"
        ".hword 0xa014, 0xe5cd, 0x06a4, 0xebfe\n"
        ".hword 0x0000, 0xe58d, 0x0000, 0xe590\n"
        ".hword 0x2004, 0xe3a0, 0x1074, 0xe3a0\n"
        ".hword 0x3008, 0xe590, 0x0000, 0xe59d\n"
        ".hword 0xff33, 0xe12f, 0x0000, 0xe350\n"
        ".hword 0x0008, 0x0a00, 0x1000, 0xe59d\n"
        ".hword 0x926c, 0xebfd, 0x7000, 0xe1a0\n"
        ".hword 0x01d4, 0xe1dd, 0x1004, 0xe1a0\n"
        ".hword 0x0000, 0xe58d, 0x0007, 0xe1a0\n"
        ".hword 0x20dc, 0xe1cd, 0x914c, 0xebfd\n"
        ".hword 0x0000, 0xe595, 0x1008, 0xe1a0\n"
        ".hword 0x0380, 0xe085, 0x0106, 0xe080\n"
        ".hword 0x75ec, 0xe580, 0x0000, 0xe597\n"
        ".hword 0x200c, 0xe590, 0x0007, 0xe1a0\n"
        ".hword 0xff32, 0xe12f, 0x0000, 0xe595\n"
        ".hword 0x1a68, 0xeeb0, 0x0380, 0xe085\n"
        ".hword 0x0106, 0xe080, 0x75ec, 0xe590\n"
        ".hword 0x1044, 0xe287, 0x0050, 0xe597\n"
        ".hword 0x4030, 0xe287, 0x0a02, 0xec91\n"
        ".hword 0x104c, 0xe597, 0xff31, 0xe12f\n"
        ".hword 0x0a02, 0xedd4, 0x4008, 0xe284\n"
        ".hword 0x6001, 0xe286, 0x0a02, 0xec84\n"
        ".hword 0x0009, 0xe156, 0xa058, 0xe5c7\n"
        ".hword 0x0008, 0xe595, 0x0001, 0xe280\n"
        ".hword 0x0008, 0xe585, 0xffbb, 0xbaff\n"
        ".hword 0x0000, 0xe595, 0x0001, 0xe280\n"
        ".hword 0x0000, 0xe585, 0x0004, 0xe59d\n"
        ".hword 0x1030, 0xe59d, 0x0010, 0xe280\n"
        ".hword 0x0001, 0xe150, 0x0004, 0xe58d\n"
        ".hword 0xff72, 0x1aff, 0x1001, 0xe3a0\n"
        ".hword 0x002c, 0xe285, 0x027d, 0xebfe\n"
        ".hword 0x7b01, 0xe285, 0x7f4d, 0xe287\n"
        ".hword 0x0d15, 0xe285, 0x8a00, 0xedc7\n"
        ".hword 0x8a01, 0xedc7, 0x8a02, 0xedc7\n"
        ".hword 0x0a2a, 0xed9f, 0x8a00, 0xedc0\n"
        ".hword 0x8a01, 0xedc0, 0x0a02, 0xed80\n"
        ".hword 0x4b01, 0xe285, 0x1a27, 0xed9f\n"
        ".hword 0x0a25, 0xeddf, 0x8a53, 0xedc4\n"
        ".hword 0x1a25, 0xeddf, 0x1a54, 0xed84\n"
        ".hword 0x6b01, 0xe285, 0x0a55, 0xedc4\n"
        ".hword 0x6f57, 0xe286, 0x1a56, 0xedc4\n"
        ".hword 0x8a00, 0xedc6, 0x0a01, 0xedc6\n"
        ".hword 0x8a02, 0xedc6, 0x0a5a, 0xed84\n"
        ".hword 0x002c, 0xe285, 0xffbc, 0xebfd\n"
        ".hword 0x3006, 0xe1a0, 0x2d15, 0xe285\n"
        ".hword 0x1007, 0xe1a0, 0x002c, 0xe285\n"
        ".hword 0x0204, 0xebfe, 0x4e15, 0xe284\n"
        ".hword 0x1a14, 0xeddf, 0x1001, 0xe3a0\n"
        ".hword 0x0a03, 0xec94, 0x002c, 0xe285\n"
        ".hword 0x01d3, 0xebfe, 0x002c, 0xe285\n"
        ".hword 0xf000, 0xe320, 0x5dcc, 0xebfd\n"
        ".hword 0xd034, 0xe28d, 0x0005, 0xe1a0\n"
        ".hword 0x8b02, 0xecbd, 0x2000, 0xe3e0\n"
        ".hword 0x4ff0, 0xe8bd, 0x1000, 0xe3a0\n"
        ".hword 0x0007, 0xea00, 0x0000, 0x0000\n"
        ".hword 0xe858, 0x0044, 0xe820, 0x0044\n"
        ".hword 0x0000, 0x40a0, 0x0000, 0x3f80\n"
        ".hword 0x0000, 0x41f0, 0x4000, 0x461c\n"
        ".hword 0x5555, 0x3fd5\n"
    );
};

// DECOMP_FUNC(0x001909b0, 920)
extern "C" __attribute__((naked)) void camp_func_001909b0() {
    asm volatile(
        ".arm\n"
        ".hword 0x41f0, 0xe92d, 0x4000, 0xe1a0\n"
        ".hword 0x0a03, 0xe280, 0x1000, 0xe3a0\n"
        ".hword 0x205c, 0xe590, 0x6001, 0xe3a0\n"
        ".hword 0x2102, 0xe084, 0x2a03, 0xe282\n"
        ".hword 0x2e47, 0xe282, 0x1000, 0xe582\n"
        ".hword 0x305c, 0xe590, 0x235c, 0xe59f\n"
        ".hword 0x3103, 0xe084, 0x3a03, 0xe283\n"
        ".hword 0x3e46, 0xe283, 0x1000, 0xe583\n"
        ".hword 0x1004, 0xe782, 0x005c, 0xe590\n"
        ".hword 0x0000, 0xe350, 0x0005, 0x1a00\n"
        ".hword 0x1001, 0xe3a0, 0x0004, 0xe1a0\n"
        ".hword 0x1d4c, 0xeb04, 0x0000, 0xe3a0\n"
        ".hword 0x0000, 0xe350, 0x00ac, 0x1a00\n"
        ".hword 0x1001, 0xe3a0, 0x0004, 0xe1a0\n"
        ".hword 0x1d46, 0xeb04, 0x5b0d, 0xe284\n"
        ".hword 0x0001, 0xe350, 0x500c, 0xe285\n"
        ".hword 0x003d, 0x0a00, 0x1001, 0xe3a0\n"
        ".hword 0x0004, 0xe1a0, 0x1d3f, 0xeb04\n"
        ".hword 0x0002, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x004b, 0x0a00, 0x1001, 0xe3a0\n"
        ".hword 0x0004, 0xe1a0, 0x1d39, 0xeb04\n"
        ".hword 0x0007, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0067, 0x0a00, 0x1001, 0xe3a0\n"
        ".hword 0x0004, 0xe1a0, 0x1d33, 0xeb04\n"
        ".hword 0x0003, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x007a, 0x0a00, 0x1001, 0xe3a0\n"
        ".hword 0x0004, 0xe1a0, 0x1d2d, 0xeb04\n"
        ".hword 0x0006, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x008d, 0x0a00, 0x1001, 0xe3a0\n"
        ".hword 0x0004, 0xe1a0, 0x1d27, 0xeb04\n"
        ".hword 0x0008, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0087, 0x0a00, 0x1001, 0xe3a0\n"
        ".hword 0x0004, 0xe1a0, 0x1d21, 0xeb04\n"
        ".hword 0x0005, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0083, 0x0a00, 0x1001, 0xe3a0\n"
        ".hword 0x0004, 0xe1a0, 0x1d1b, 0xeb04\n"
        ".hword 0x000a, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0084, 0x0a00, 0x1001, 0xe3a0\n"
        ".hword 0x0004, 0xe1a0, 0x1d15, 0xeb04\n"
        ".hword 0x0004, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0085, 0x0a00, 0x1001, 0xe3a0\n"
        ".hword 0x0004, 0xe1a0, 0x1d0f, 0xeb04\n"
        ".hword 0x0009, 0xe350, 0x2001, 0xe3a0\n"
        ".hword 0x0086, 0x0a00, 0x1000, 0xe3a0\n"
        ".hword 0x0004, 0xe1a0, 0x1e30, 0xeb04\n"
        ".hword 0x1224, 0xe59f, 0x0000, 0xe3a0\n"
        ".hword 0x3979, 0xeb04, 0x0006, 0xe1a0\n"
        ".hword 0x81f0, 0xe8bd, 0x0a03, 0xe284\n"
        ".hword 0x0f86, 0xe280, 0x0000, 0xe585\n"
        ".hword 0x2001, 0xe3a0, 0x1009, 0xe3a0\n"
        ".hword 0x0004, 0xe1a0, 0x1e24, 0xeb04\n"
        ".hword 0x5000, 0xe3a0, 0x2000, 0xe3a0\n"
        ".hword 0x0185, 0xe065, 0x1002, 0xe1a0\n"
        ".hword 0x0100, 0xe080, 0x0100, 0xe084\n"
        ".hword 0x0b03, 0xe280, 0x0f96, 0xe280\n"
        ".hword 0x7b39, 0xeb04, 0x5001, 0xe285\n"
        ".hword 0x0006, 0xe355, 0xfff4, 0xbaff\n"
        ".hword 0xffe6, 0xeaff, 0xf000, 0xe320\n"
        ".hword 0x0c44, 0xeb04, 0x0b11, 0xe280\n"
        ".hword 0x00a8, 0xe280, 0x0000, 0xe590\n"
        ".hword 0x0040, 0xe310, 0x0006, 0x1a00\n"
        ".hword 0x0c3e, 0xeb04, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0x0c20, 0xeb04\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0045, 0x0a00, 0x0a03, 0xe284\n"
        ".hword 0x0f9f, 0xe280, 0x0000, 0xe585\n"
        ".hword 0x2001, 0xe3a0, 0x1009, 0xe3a0\n"
        ".hword 0x0004, 0xe1a0, 0x1e02, 0xeb04\n"
        ".hword 0x5000, 0xe3a0, 0x2000, 0xe3a0\n"
        ".hword 0x0185, 0xe065, 0x1002, 0xe1a0\n"
        ".hword 0x0100, 0xe080, 0x0100, 0xe084\n"
        ".hword 0x0b03, 0xe280, 0x0f96, 0xe280\n"
        ".hword 0x7b17, 0xeb04, 0x5001, 0xe285\n"
        ".hword 0x0006, 0xe355, 0xfff4, 0xbaff\n"
        ".hword 0xffc4, 0xeaff, 0x0a03, 0xe284\n"
        ".hword 0x0e2e, 0xe280, 0x7000, 0xe1a0\n"
        ".hword 0x3937, 0xeb04, 0x0000, 0xe350\n"
        ".hword 0xf000, 0xe320, 0x002a, 0xda00\n"
        ".hword 0x2001, 0xe3a0, 0x100b, 0xe3a0\n"
        ".hword 0x0004, 0xe1a0, 0x7000, 0xe585\n"
        ".hword 0x1de9, 0xeb04, 0x5000, 0xe3a0\n"
        ".hword 0x2000, 0xe3a0, 0x0185, 0xe065\n"
        ".hword 0x1002, 0xe1a0, 0x0100, 0xe080\n"
        ".hword 0x0100, 0xe084, 0x0b03, 0xe280\n"
        ".hword 0x0f96, 0xe280, 0x7afe, 0xeb04\n"
        ".hword 0x5001, 0xe285, 0x0006, 0xe355\n"
        ".hword 0xfff4, 0xbaff, 0xffab, 0xeaff\n"
        ".hword 0x0a03, 0xe284, 0x0fd1, 0xe280\n"
        ".hword 0x7000, 0xe1a0, 0x391e, 0xeb04\n"
        ".hword 0x0000, 0xe350, 0xf000, 0xe320\n"
        ".hword 0x0011, 0xda00, 0x2001, 0xe3a0\n"
        ".hword 0x100d, 0xe3a0, 0x0004, 0xe1a0\n"
        ".hword 0x7000, 0xe585, 0x1dd0, 0xeb04\n"
        ".hword 0x5000, 0xe3a0, 0x2000, 0xe3a0\n"
        ".hword 0x0185, 0xe065, 0x1002, 0xe1a0\n"
        ".hword 0x0100, 0xe080, 0x0100, 0xe084\n"
        ".hword 0x0b03, 0xe280, 0x0f96, 0xe280\n"
        ".hword 0x7ae5, 0xeb04, 0x5001, 0xe285\n"
        ".hword 0x0006, 0xe355, 0xfff4, 0xbaff\n"
        ".hword 0xff92, 0xeaff, 0x6000, 0xe3a0\n"
        ".hword 0xff93, 0xeaff, 0x2001, 0xe3a0\n"
        ".hword 0x1017, 0xe3a0, 0x0004, 0xe1a0\n"
        ".hword 0x1dbd, 0xeb04, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0xff89, 0xeaff\n"
        ".hword 0x2001, 0xe3a0, 0x101a, 0xe3a0\n"
        ".hword 0x0004, 0xe1a0, 0x1db6, 0xeb04\n"
        ".hword 0xf000, 0xe320, 0xf000, 0xe320\n"
        ".hword 0xff82, 0xeaff, 0x2001, 0xe3a0\n"
        ".hword 0x101b, 0xe3a0, 0x0004, 0xe1a0\n"
        ".hword 0x1daf, 0xeb04, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0xff7b, 0xeaff\n"
        ".hword 0x1019, 0xe3a0, 0x0004, 0xe1a0\n"
        ".hword 0x1da9, 0xeb04, 0xf000, 0xe320\n"
        ".hword 0xf000, 0xe320, 0xff75, 0xeaff\n"
        ".hword 0x3504, 0x0000, 0x32ff, 0x3232\n"
    );
};

// DECOMP_FUNC(0x003fbe64, 920)
extern "C" __attribute__((naked)) void func_003fbe64() {
    asm volatile(
        ".arm\n"
        ".hword 0x4ff0, 0xe92d, 0x6000, 0xe1a0\n"
        ".hword 0xd00c, 0xe24d, 0xa001, 0xe3a0\n"
        ".hword 0x8000, 0xe3a0, 0xc004, 0xe5b0\n"
        ".hword 0x3008, 0xe590, 0x1004, 0xe58d\n"
        ".hword 0x9001, 0xe283, 0x2203, 0xe08c\n"
        ".hword 0x000c, 0xe042, 0x4240, 0xe1a0\n"
        ".hword 0x4000, 0xe58d, 0x0008, 0xe596\n"
        ".hword 0x0009, 0xe150, 0x003e, 0x3a00\n"
        ".hword 0x0004, 0xe043, 0x0001, 0xe350\n"
        ".hword 0x5000, 0x31a0, 0x500a, 0x21a0\n"
        ".hword 0x3005, 0xe040, 0x0005, 0xe049\n"
        ".hword 0x0000, 0xe355, 0x2205, 0xe042\n"
        ".hword 0x0200, 0x108c, 0x000f, 0x0a00\n"
        ".hword 0x1000, 0xe1b0, 0xc002, 0xe1a0\n"
        ".hword 0x0010, 0xe281, 0x2010, 0xe282\n"
        ".hword 0x0008, 0x0a00, 0x7000, 0xe59c\n"
        ".hword 0x7000, 0xe581, 0x7004, 0xe59c\n"
        ".hword 0x7004, 0xe581, 0x700c, 0xe59c\n"
        ".hword 0x700c, 0xe581, 0x1008, 0xe587\n"
        ".hword 0xc008, 0xe581, 0x100c, 0xe58c\n"
        ".hword 0x5001, 0xe255, 0xffef, 0x1aff\n"
        ".hword 0x700a, 0xe084, 0x2004, 0xe1a0\n"
        ".hword 0x1007, 0xe1a0, 0x0006, 0xe1a0\n"
        ".hword 0xc291, 0xebf8, 0x000c, 0xe596\n"
        ".hword 0x0000, 0xe157, 0x7000, 0x21a0\n"
        ".hword 0x0004, 0xe596, 0x5204, 0xe080\n"
        ".hword 0x7207, 0xe080, 0x0007, 0xe155\n"
        ".hword 0x009b, 0x2a00, 0x4005, 0xe1a0\n"
        ".hword 0x5010, 0xe285, 0x0008, 0xe594\n"
        ".hword 0x0000, 0xe350, 0x0004, 0x1150\n"
        ".hword 0x0007, 0x1a00, 0x1004, 0xe594\n"
        ".hword 0x0000, 0xe351, 0x000a, 0x0a00\n"
        ".hword 0x0000, 0xe594, 0x2000, 0xe590\n"
        ".hword 0x2004, 0xe592, 0xff32, 0xe12f\n"
        ".hword 0x0005, 0xea00, 0x100c, 0xe594\n"
        ".hword 0x100c, 0xe580, 0x00d8, 0xe1c4\n"
        ".hword 0x0008, 0xe581, 0x8008, 0xe584\n"
        ".hword 0x800c, 0xe584, 0x0007, 0xe155\n"
        ".hword 0x8004, 0xe584, 0xffe8, 0x3aff\n"
        ".hword 0x0083, 0xea00, 0x1009, 0xe1a0\n"
        ".hword 0xc07b, 0xebf8, 0x7000, 0xe596\n"
        ".hword 0x1000, 0xe3a0, 0x5000, 0xe1b0\n"
        ".hword 0x8001, 0xe1a0, 0x0025, 0x0a00\n"
        ".hword 0x2000, 0xe597, 0x1205, 0xe1a0\n"
        ".hword 0x0007, 0xe1a0, 0x2000, 0xe592\n"
        ".hword 0x1008, 0xe58d, 0xff32, 0xe12f\n"
        ".hword 0xb000, 0xe1b0, 0x0005, 0x1a00\n"
        ".hword 0x0000, 0xe597, 0x1210, 0xe59f\n"
        ".hword 0x2008, 0xe59d, 0x3008, 0xe590\n"
        ".hword 0x0007, 0xe1a0, 0xff33, 0xe12f\n"
        ".hword 0x100b, 0xe1b0, 0x8005, 0x11a0\n"
        ".hword 0x0014, 0x1a00, 0x0005, 0xe159\n"
        ".hword 0x0054, 0x0a00, 0x0000, 0xe359\n"
        ".hword 0x0010, 0x0a00, 0x2000, 0xe597\n"
        ".hword 0x1209, 0xe1a0, 0x0007, 0xe1a0\n"
        ".hword 0x8001, 0xe1a0, 0x2000, 0xe592\n"
        ".hword 0xff32, 0xe12f, 0x5000, 0xe1b0\n"
        ".hword 0x0005, 0x1a00, 0x1000, 0xe597\n"
        ".hword 0x0007, 0xe1a0, 0x2008, 0xe1a0\n"
        ".hword 0x3008, 0xe591, 0x11b0, 0xe59f\n"
        ".hword 0xff33, 0xe12f, 0x1005, 0xe1b0\n"
        ".hword 0x8009, 0x11a0, 0x0041, 0x0a00\n"
        ".hword 0x3004, 0xe596, 0x5004, 0xe1b0\n"
        ".hword 0x0001, 0x11a0, 0x000f, 0x0a00\n"
        ".hword 0x2000, 0xe1b0, 0xc003, 0xe1a0\n"
        ".hword 0x0010, 0xe282, 0x3010, 0xe283\n"
        ".hword 0x0008, 0x0a00, 0xb000, 0xe59c\n"
        ".hword 0xb000, 0xe582, 0xb004, 0xe59c\n"
        ".hword 0xb004, 0xe582, 0xb00c, 0xe59c\n"
        ".hword 0xb00c, 0xe582, 0x2008, 0xe58b\n"
        ".hword 0xc008, 0xe582, 0x200c, 0xe58c\n"
        ".hword 0x5001, 0xe255, 0xffef, 0x1aff\n"
        ".hword 0x300c, 0xe596, 0x2004, 0xe596\n"
        ".hword 0x000a, 0xe084, 0x5004, 0xe053\n"
        ".hword 0x3204, 0xe082, 0x0200, 0x1081\n"
        ".hword 0x000f, 0x0a00, 0x2000, 0xe1b0\n"
        ".hword 0xc003, 0xe1a0, 0x0010, 0xe282\n"
        ".hword 0x3010, 0xe283, 0x0008, 0x0a00\n"
        ".hword 0x4000, 0xe59c, 0x4000, 0xe582\n"
        ".hword 0x4004, 0xe59c, 0x4004, 0xe582\n"
        ".hword 0x400c, 0xe59c, 0x400c, 0xe582\n"
        ".hword 0x2008, 0xe584, 0xc008, 0xe582\n"
        ".hword 0x200c, 0xe58c, 0x5001, 0xe255\n"
        ".hword 0xffef, 0x1aff, 0x0004, 0xe286\n"
        ".hword 0x5004, 0xe596, 0x0102, 0xe880\n"
        ".hword 0x000c, 0xe596, 0xa005, 0xe1a0\n"
        ".hword 0x8200, 0xe085, 0x0008, 0xe155\n"
        ".hword 0xb000, 0x33a0, 0x001d, 0x2a00\n"
        ".hword 0x4005, 0xe1a0, 0x5010, 0xe285\n"
        ".hword 0x0008, 0xe594, 0x0000, 0xe350\n"
        ".hword 0x0004, 0x1150, 0x000e, 0x1a00\n"
        ".hword 0x1004, 0xe594, 0x0000, 0xe351\n"
        ".hword 0x0011, 0x0a00, 0x0000, 0xe594\n"
        ".hword 0x2000, 0xe590, 0x2004, 0xe592\n"
        ".hword 0xff32, 0xe12f, 0x000c, 0xea00\n"
        ".hword 0x2000, 0xe597, 0x0007, 0xe1a0\n"
        ".hword 0x2004, 0xe592, 0xff32, 0xe12f\n"
        ".hword 0xd00c, 0xe28d, 0x0000, 0xe3a0\n"
        ".hword 0x8ff0, 0xe8bd, 0x100c, 0xe594\n"
        ".hword 0x100c, 0xe580, 0x00d8, 0xe1c4\n"
        ".hword 0x0008, 0xe581, 0xb008, 0xe584\n"
        ".hword 0xb00c, 0xe584, 0x0008, 0xe155\n"
        ".hword 0xb004, 0xe584, 0xffe1, 0x3aff\n"
        ".hword 0x2000, 0xe597, 0x100a, 0xe1a0\n"
        ".hword 0x0007, 0xe1a0, 0x2004, 0xe592\n"
        ".hword 0xff32, 0xe12f, 0x900c, 0xe586\n"
        ".hword 0x0000, 0xe59d, 0x1004, 0xe596\n"
        ".hword 0x0200, 0xe091, 0x0009, 0x0a00\n"
        ".hword 0x1004, 0xe59d, 0x2000, 0xe591\n"
        ".hword 0x2000, 0xe580, 0x2004, 0xe591\n"
        ".hword 0x2004, 0xe580, 0x200c, 0xe591\n"
        ".hword 0x200c, 0xe580, 0x0008, 0xe582\n"
        ".hword 0x1008, 0xe580, 0x000c, 0xe581\n"
        ".hword 0xd00c, 0xe28d, 0x0001, 0xe3a0\n"
        ".hword 0x8ff0, 0xe8bd, 0xff98, 0x0040\n"
    );
};

// End of Batch 45 A.
