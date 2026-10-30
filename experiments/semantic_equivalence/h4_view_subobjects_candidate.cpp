#include <cstddef>

using u8 = unsigned char;
using u16 = unsigned short;
using u32 = unsigned int;
using s32 = int;
using f32 = float;

struct ViewCameraWork {
    u32 field_00;          // +0x00
    u32 field_04;          // +0x04
    u32 field_08;          // +0x08
    u8  pad_0c[4];         // +0x0C
    u8  field_10;          // +0x10
    u8  pad_11[3];         // +0x11
    f32 field_14;          // +0x14
    u8  pad_18[4];         // +0x18
    f32 pos[3];            // +0x1C..+0x24: X, Y, Z
    f32 target[3];         // +0x28..+0x30: target X, Y, Z
    u8  pad_34[12];        // +0x34
    f32 field_40;          // +0x40
    f32 field_44;          // +0x44
    f32 lookat[2];         // +0x48, +0x4C
    f32 pitch;             // +0x50
    u32 field_54;          // +0x54
    f32 distance;          // +0x58
    u8  field_5c;          // +0x5C
    u8  pad_5d[3];         // +0x5D
    u32 field_60;          // +0x60
    u8  pad_64[4];         // +0x64
    f32 field_68;          // +0x68
    u8  field_6c;          // +0x6C
    u8  pad_6d[3];         // +0x6D
    u32 field_70;          // +0x70
    f32 sec_target[3];     // +0x74..+0x7C
    f32 field_80;          // +0x80
    u32 field_84;          // +0x84
    u8  field_88;          // +0x88
    u8  pad_89[7];         // +0x89
    u32 field_90;          // +0x90
    f32 field_94;          // +0x94
    u8  pad_98[0x134 - 0x98]; // +0x98..+0x133
    u8  active_flag;       // +0x134
    u8  pad_135[0x15c - 0x135]; // +0x135..+0x15B
    f32 clip_far;          // +0x15C
    f32 clip_near;         // +0x160
    u32 field_164;         // +0x164
    u8  pad_168[8];        // +0x168
    u32 field_170;         // +0x170
    u32 field_174;         // +0x174
    u32 field_178;         // +0x178
    u32 field_17c;         // +0x17C
    u8  channel_flags[5];  // +0x180..0x184
    u8  pad_185[3];        // +0x185
    u32 target_actor;      // +0x188
    s32 sentinel_id;       // +0x18C
    u32 field_190;         // +0x190
    void* subobject;       // +0x194
    u8  field_198;         // +0x198
    u8  pad_199[3];        // +0x199
    u32 sub_channels[6];   // +0x19C..0x1B0
    u16 sub_flags[3];      // +0x1B4..0x1B8
    u8  pad_1ba[6];        // +0x1BA..0x1BF
};

static_assert(offsetof(ViewCameraWork, subobject) == 0x194, "offset 0x194");
static_assert(offsetof(ViewCameraWork, field_198) == 0x198, "offset 0x198");
static_assert(offsetof(ViewCameraWork, sub_channels) == 0x19C, "offset 0x19C");
static_assert(sizeof(ViewCameraWork) == 0x1C0, "size 0x1C0");

extern "C" void ui_subobject_load_player_00294a64(void* subobj, u32 size);
extern "C" void ui_subobject_set_channel_active_00343e90(void* subobj, u32 channel, u32 val, u32 size);
extern "C" void ui_subobject_set_channel_default_002946f4(void* subobj, u32 channel, u32 size);

extern "C" void h4_view_subobjects_candidate() {
    auto** view_slot = reinterpret_cast<ViewCameraWork**>(0x00447E88);
    ViewCameraWork* work = *view_slot;

    ui_subobject_load_player_00294a64(work->subobject, sizeof(ViewCameraWork));

    if (work->field_198 != 0) {
        for (u32 i = 0; i < 3; ++i) {
            u32 size_param = 0;
            if (i == 0 || i == 1 || i == 2) {
                size_param = sizeof(ViewCameraWork);
            }
            ui_subobject_set_channel_active_00343e90(
                work->subobject,
                static_cast<u8>(i),
                work->sub_channels[i],
                size_param
            );
        }
    } else {
        for (u32 i = 0; i < 3; ++i) {
            u32 size_param = 0;
            if (i == 0 || i == 1 || i == 2) {
                size_param = sizeof(ViewCameraWork);
            }
            ui_subobject_set_channel_default_002946f4(
                work->subobject,
                static_cast<u8>(i),
                size_param
            );
        }
    }
}

// Deliberately mutated negative control (swaps loop bound to 2 iterations)
extern "C" void h4_view_subobjects_mutation() {
    auto** view_slot = reinterpret_cast<ViewCameraWork**>(0x00447E88);
    ViewCameraWork* work = *view_slot;

    ui_subobject_load_player_00294a64(work->subobject, sizeof(ViewCameraWork));

    if (work->field_198 != 0) {
        for (u32 i = 0; i < 2; ++i) {
            ui_subobject_set_channel_active_00343e90(
                work->subobject,
                static_cast<u8>(i),
                work->sub_channels[i],
                sizeof(ViewCameraWork)
            );
        }
    } else {
        for (u32 i = 0; i < 2; ++i) {
            ui_subobject_set_channel_default_002946f4(
                work->subobject,
                static_cast<u8>(i),
                sizeof(ViewCameraWork)
            );
        }
    }
}
