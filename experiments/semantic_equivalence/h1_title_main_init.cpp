#include <cstddef>
#include <cstdint>

namespace {
using u8 = std::uint8_t;
using u16 = std::uint16_t;
using u32 = std::uint32_t;
using s32 = std::int32_t;
using Calc = void (*)(void*);
using Draw = void (*)(void*);

struct TitleMainWork {
    void* calc_task;
    u8 flag_04;
    u8 pad_05[3];
    u32 field_08;
    u32 field_0c;
    u8 flag_10;
    u8 pad_11[0x2f];
    float field_40[8];
    u8 flag_60;
    u8 flag_61;
    u8 flag_62;
    u8 flag_63;
    float field_64;
    float field_68;
    float field_6c;
    u16 field_70;
    u16 field_72;
    u32 field_74;
    u32 field_78;
    u8 flag_7c;
    u8 pad_7d[3];
    u32 field_80;
    u8 flag_84;
    u8 flag_85;
    u8 flag_86;
    u8 pad_87;
    u32 resource_88;
    u32 resource_8c;
    u32 resource_90;
    u8 flag_94;
    u8 flag_95;
    u8 flag_96;
    u8 pad_97;
    float field_98;
    s32 state_9c;
};
static_assert(sizeof(TitleMainWork) == 0xA0);
static_assert(offsetof(TitleMainWork, field_40) == 0x40);
static_assert(offsetof(TitleMainWork, flag_95) == 0x95);

using AllocAlign = void* (*)(u32, u32, u32, u32, u32);
using CreateCalc = void* (*)(const char*, u32, u32, u32, Calc, u32, u32);
using CreateDraw = void* (*)(const char*, u32, u32, u32, Draw, u32, u32, void*);
constexpr std::uintptr_t kGlobalTitleMainWork = 0x0044E300;
constexpr std::uintptr_t kAllocAlign = 0x002C54F0;
constexpr std::uintptr_t kCreateCalc = 0x002C5978;
constexpr std::uintptr_t kCreateDraw = 0x002C4C00;
constexpr std::uintptr_t kTitleMainSecondary = 0x002CA6F4;
constexpr std::uintptr_t kTitleMainCalc = 0x001E989C;
constexpr std::uintptr_t kDrawLeft = 0x0020FD5C;
constexpr std::uintptr_t kDrawRight = 0x0021F36C;
constexpr std::uintptr_t kDrawDown = 0x002CA7A8;

__attribute__((always_inline)) inline void initialize(const u8* arg, bool bad_argument_control) {
    auto** global = reinterpret_cast<TitleMainWork**>(kGlobalTitleMainWork);
    auto alloc = reinterpret_cast<AllocAlign>(kAllocAlign);
    TitleMainWork* work = static_cast<TitleMainWork*>(
        alloc(0x10000, 0x100, 0, 0xA0, 1));
    *global = work;

    work->field_08 = 0;
    work->field_0c = 0;
    work->flag_10 = 1;
    for (float& value : work->field_40) value = 0.0f;
    work->flag_60 = 1;
    work->flag_63 = 0;
    work->flag_61 = 0;
    work->flag_62 = 0;
    work->field_80 = 2;
    work->field_70 = 0;
    work->field_72 = 0;
    work->field_74 = 0;
    work->field_78 = 0;
    work->field_64 = 0.0f;
    work->field_68 = 0.0f;
    work->flag_7c = 0;
    work->flag_84 = 1;
    work->flag_86 = 0;
    work->flag_85 = 1;
    work->flag_96 = 0;
    work->flag_94 = 0;
    work->field_98 = 0.0f;
    work->flag_95 = 0;
    work->flag_04 = 0;
    if (arg != nullptr) {
        work->flag_95 = *arg;
        work->flag_10 = bad_argument_control ? 1 : 0;
    }

    auto create_calc = reinterpret_cast<CreateCalc>(kCreateCalc);
    void* task = create_calc(reinterpret_cast<const char*>(0x001EB1F8), 2, 0, 0,
                             reinterpret_cast<Calc>(kTitleMainCalc),
                             static_cast<u32>(kTitleMainSecondary), 0);
    work->calc_task = task;

    auto create_draw = reinterpret_cast<CreateDraw>(kCreateDraw);
    create_draw(reinterpret_cast<const char*>(0x001EB204), 0x76, 0, 0,
                reinterpret_cast<Draw>(kDrawLeft), 0, 0, task);
    create_draw(reinterpret_cast<const char*>(0x001EB218), 0xD4, 0, 0,
                reinterpret_cast<Draw>(kDrawRight), 0, 0, task);
    create_draw(reinterpret_cast<const char*>(0x001EB230), 0xE7, 0, 0,
                reinterpret_cast<Draw>(kDrawDown), 0, 0, task);
}
} // namespace

extern "C" __attribute__((used, visibility("default")))
void candidate_title_main_init(const u8* arg) {
    initialize(arg, false);
}

// Deliberately incorrect negative control: it preserves the initialized-one
// flag at +0x10 when an argument is supplied.
extern "C" __attribute__((used, visibility("default")))
void negative_title_main_init(const u8* arg) {
    initialize(arg, true);
}


