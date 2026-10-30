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
    f32 clip_far;          // +0x15C: 1000.0f
    f32 clip_near;         // +0x160: 5.0f
    u32 field_164;         // +0x164
    u8  pad_168[8];        // +0x168
    u32 field_170;         // +0x170
    u32 field_174;         // +0x174
    u32 field_178;         // +0x178
    u32 field_17c;         // +0x17C
    u8  channel_flags[5];  // +0x180..0x184
    u8  pad_185[3];        // +0x185
    u32 target_actor;      // +0x188
    s32 sentinel_id;       // +0x18C: -1
    u32 field_190;         // +0x190
    void* subobject;       // +0x194
    u8  field_198;         // +0x198
    u8  pad_199[3];        // +0x199
    u32 sub_channels[6];   // +0x19C..0x1B0
    u16 sub_flags[3];      // +0x1B4..0x1B8
};

static_assert(offsetof(ViewCameraWork, field_00) == 0x00, "offset 0x00");
static_assert(offsetof(ViewCameraWork, field_10) == 0x10, "offset 0x10");
static_assert(offsetof(ViewCameraWork, field_14) == 0x14, "offset 0x14");
static_assert(offsetof(ViewCameraWork, pos) == 0x1C, "offset 0x1C");
static_assert(offsetof(ViewCameraWork, target) == 0x28, "offset 0x28");
static_assert(offsetof(ViewCameraWork, field_40) == 0x40, "offset 0x40");
static_assert(offsetof(ViewCameraWork, lookat) == 0x48, "offset 0x48");
static_assert(offsetof(ViewCameraWork, pitch) == 0x50, "offset 0x50");
static_assert(offsetof(ViewCameraWork, distance) == 0x58, "offset 0x58");
static_assert(offsetof(ViewCameraWork, field_70) == 0x70, "offset 0x70");
static_assert(offsetof(ViewCameraWork, sec_target) == 0x74, "offset 0x74");
static_assert(offsetof(ViewCameraWork, field_90) == 0x90, "offset 0x90");
static_assert(offsetof(ViewCameraWork, active_flag) == 0x134, "offset 0x134");
static_assert(offsetof(ViewCameraWork, clip_far) == 0x15C, "offset 0x15C");
static_assert(offsetof(ViewCameraWork, clip_near) == 0x160, "offset 0x160");
static_assert(offsetof(ViewCameraWork, field_164) == 0x164, "offset 0x164");
static_assert(offsetof(ViewCameraWork, field_170) == 0x170, "offset 0x170");
static_assert(offsetof(ViewCameraWork, channel_flags) == 0x180, "offset 0x180");
static_assert(offsetof(ViewCameraWork, sentinel_id) == 0x18C, "offset 0x18C");
static_assert(offsetof(ViewCameraWork, subobject) == 0x194, "offset 0x194");
static_assert(offsetof(ViewCameraWork, sub_channels) == 0x19C, "offset 0x19C");
static_assert(offsetof(ViewCameraWork, sub_flags) == 0x1B4, "offset 0x1B4");

extern "C" void* AsdMem_Alloc_002c23f8(u32 size);
extern "C" void ui_subobject_constructor_00294a98(void* obj);

extern "C" void h4_view_init_candidate() {
    auto** view_slot = reinterpret_cast<ViewCameraWork**>(0x00447E88);
    ViewCameraWork* work = *view_slot;
    auto* gate = reinterpret_cast<u8*>(0x0049F91C);

    work->field_00 = 0;
    work->field_04 = 0;
    work->field_08 = 0;
    work->field_10 = 0;
    work->field_14 = 0.0f;
    work->pos[0] = 10.0f;
    work->pos[1] = 0.0f;
    work->pos[2] = 10.0f;
    work->target[0] = 10.0f;
    work->target[1] = 0.0f;
    work->target[2] = 10.0f;
    work->field_40 = 10.0f;
    work->field_44 = 0.0f;
    work->lookat[0] = 10.0f;
    work->lookat[1] = -90.0f;
    work->pitch = -90.0f;
    work->field_54 = 0;
    work->distance = 5.0f;
    work->field_5c = 0;
    work->field_60 = 0;
    work->field_68 = 0.0f;
    work->field_6c = 0;
    work->field_70 = 0;
    work->sec_target[0] = 0.0f;
    work->sec_target[1] = 0.0f;
    work->sec_target[2] = 0.0f;
    work->field_80 = 0.0f;
    work->field_84 = 0;
    work->field_88 = 0;
    work->field_90 = 0;
    work->field_94 = 0.0f;
    work->active_flag = 1;
    work->clip_far = 100.0f;
    work->clip_near = 1000.0f;

    void* sub = AsdMem_Alloc_002c23f8(0x100);
    if (sub != nullptr) {
        ui_subobject_constructor_00294a98(sub);
        *reinterpret_cast<const void**>(sub) = reinterpret_cast<const void*>(0x00420420);
    }

    work->subobject = sub;
    work->field_198 = 0;
    for (int i = 0; i < 6; ++i) {
        work->sub_channels[i] = 0;
    }
    for (int i = 0; i < 3; ++i) {
        work->sub_flags[i] = 0;
    }
    work->field_164 = 0;
    work->field_170 = 0;
    work->field_174 = 0;
    work->field_178 = 0;
    work->field_17c = 0;
    for (int i = 0; i < 5; ++i) {
        work->channel_flags[i] = 0;
    }
    work->target_actor = 0;
    work->sentinel_id = -1;
    work->field_190 = 0;

    // Global repeat gate at 0x0049F91C
    *reinterpret_cast<u8*>(gate + 0x17c) = 0;
    *reinterpret_cast<f32*>(gate + 0x180) = 0.0f;
    *reinterpret_cast<f32*>(gate + 0x184) = 0.0f;
    *reinterpret_cast<f32*>(gate + 0x188) = 0.0f;
    *reinterpret_cast<f32*>(gate + 0x18c) = 0.0f;
    *reinterpret_cast<u16*>(gate + 0x194) = 0;
    *reinterpret_cast<u8*>(gate + 0x198) = 0;
    *reinterpret_cast<u8*>(gate + 0x199) = 0;
    *reinterpret_cast<u8*>(gate + 0x19a) = 0;
    *reinterpret_cast<u8*>(gate + 0x1a0) = 0;
    *reinterpret_cast<u32*>(gate + 0x1a4) = 0;
    *reinterpret_cast<f32*>(gate + 0x1a8) = 0.0f;
    *reinterpret_cast<f32*>(gate + 0x1ac) = 0.0f;
    *reinterpret_cast<f32*>(gate + 0x1b0) = 0.0f;
    *reinterpret_cast<f32*>(gate + 0x1b4) = 0.0f;
}
