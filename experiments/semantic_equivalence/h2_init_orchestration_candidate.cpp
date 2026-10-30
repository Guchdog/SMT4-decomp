#include <cstddef>
#include <cstdint>

namespace {
using u32 = std::uint32_t;
using s32 = std::int32_t;
using u8 = std::uint8_t;
using Calc = void (*)(void*);
using Alloc = void* (*)(u32, u32, u32, u32, u32);
using CreateCalc = void* (*)(const char*, u32, u32, u32, Calc, Calc, void*);
using CreateDraw = void* (*)(const char*, u32, u32, u32, Calc, u32, u32, void*);
using GroupInit = void (*)(void*);
using GroupBind = void (*)(void*, u32, u32, u32, u32, u32, u32, u32,
                           u32, u32, u32);
using SpriteSetup = void (*)(void*, u32, s32, void*, u32, float);
using SpriteSetAnim = void (*)(void*, s32, s32);
using CursorSetup = void (*)(void*, s32, s32, s32, s32, s32);
using LoadTable = u32 (*)(const char*, void*, u32);
using SoundPlay = void (*)(s32);
using ResetUi = void (*)(u32, u32);
using FillPair = void (*)(void*, u32);
using Mapper = u32 (*)(u8);
using CopyPair = u32 (*)(void*, const void*);

template <typename Function>
Function at(std::uintptr_t address) {
    return reinterpret_cast<Function>(address);
}

constexpr std::uintptr_t kAlloc = 0x002C4B84;
constexpr std::uintptr_t kCreateCalc = 0x002C5978;
constexpr std::uintptr_t kCreateDraw = 0x002C4C00;
constexpr std::uintptr_t kGroupInit = 0x002C3344;
constexpr std::uintptr_t kGroupBind = 0x002C32F8;
constexpr std::uintptr_t kSpriteSetup = 0x002BDB2C;
constexpr std::uintptr_t kSpriteSetAnim = 0x002BDAC0;
constexpr std::uintptr_t kCursorSetup = 0x0029FAE8;
constexpr std::uintptr_t kLoadTable = 0x00297704;
constexpr std::uintptr_t kSoundPlay = 0x002B8B78;
constexpr std::uintptr_t kResetUi = 0x0029F10C;
constexpr std::uintptr_t kFillPair = 0x0027EDF8;
constexpr std::uintptr_t kMapA = 0x002CAB70;
constexpr std::uintptr_t kMapB = 0x0021F39C;
constexpr std::uintptr_t kMapC = 0x002E0AF4;
constexpr std::uintptr_t kCopyPair = 0x002ADB40;
constexpr std::uintptr_t kWorkGlobal = 0x0044E2D0;
constexpr std::uintptr_t kConfigGlobal = 0x0044E0F8;
constexpr std::uintptr_t kSpriteTable = 0x00407EC6;
constexpr std::uintptr_t kCalcTaskName = 0x002F4E84;
constexpr std::uintptr_t kDrawTaskName = 0x002F4E9C;
constexpr std::uintptr_t kConfigScriptName = 0x002F4EB4;
constexpr std::uintptr_t kConfigMessageName = 0x002F4EC4;

struct TitleConfigWorkPrefix {
    u32 calc_task;
    u8 bytes[0x158 - sizeof(u32)];
};
static_assert(sizeof(TitleConfigWorkPrefix) == 0x158);
} // namespace

// Experiment-only readable candidate for 0x002F4CA0. It preserves the real
// entry ABI (r0 is ignored), addresses and order. Calls into the pinned engine
// remain indirect original dependencies so the differential harness can
// observe/stub each direct helper boundary. It is not a promoted production
// replacement: task/resource/UI helper semantics remain outside this body.
template <u32 kEntryCount>
static std::uint32_t initialize_title_config(void*) {
    auto** const work_global = reinterpret_cast<TitleConfigWorkPrefix**>(kWorkGlobal);
    auto* const work = static_cast<TitleConfigWorkPrefix*>(
        at<Alloc>(kAlloc)(0x100, 0x100, 0, 0x158, 1));
    *work_global = work;

    auto* const calc_task = at<CreateCalc>(kCreateCalc)(
        reinterpret_cast<const char*>(kCalcTaskName), 2, 0, 0,
        reinterpret_cast<Calc>(0x001EA928),
        reinterpret_cast<Calc>(0x002CAEF0), work);
    *reinterpret_cast<void**>(work) = calc_task;
    (void)at<CreateDraw>(kCreateDraw)(
        reinterpret_cast<const char*>(kDrawTaskName), 0xE6, 0, 0,
        reinterpret_cast<Calc>(0x002CAFD0), 0, 0, calc_task);

    auto* const group = reinterpret_cast<u8*>(work) + 0x3C;
    at<GroupInit>(kGroupInit)(group);
    at<GroupBind>(kGroupBind)(group, static_cast<u32>(kSpriteTable), kEntryCount,
                              0, 0, 0, 0, 0, 0, 0, 0);
    auto* const sprite = reinterpret_cast<u8*>(work) + 0x5C;
    at<SpriteSetup>(kSpriteSetup)(sprite, 0x2F, 0, group, 0xC9, 1.0f);
    at<SpriteSetAnim>(kSpriteSetAnim)(sprite, 0, 0);
    at<CursorSetup>(kCursorSetup)(reinterpret_cast<u8*>(work) + 0xE8,
                                  3, 3, 1, 0, 1);

    *reinterpret_cast<u32*>(reinterpret_cast<u8*>(work) + 8) = 0;
    *reinterpret_cast<std::uint16_t*>(reinterpret_cast<u8*>(work) + 0x1A) = 0;
    at<FillPair>(kFillPair)(reinterpret_cast<u8*>(work) + 0x1C, 0xFFFFFFFF);
    *reinterpret_cast<std::uint16_t*>(reinterpret_cast<u8*>(work) + 0x24) = 0;
    (void)at<LoadTable>(kLoadTable)(reinterpret_cast<const char*>(kConfigScriptName),
                                    reinterpret_cast<u8*>(work) + 0x14C, 0);
    (void)at<LoadTable>(kLoadTable)(reinterpret_cast<const char*>(kConfigMessageName),
                                    reinterpret_cast<u8*>(work) + 0x150, 0);
    at<SoundPlay>(kSoundPlay)(0x99);
    at<ResetUi>(kResetUi)(0, 0x323232FF);

    auto* const config = reinterpret_cast<const u8*>(kConfigGlobal);
    *reinterpret_cast<u32*>(reinterpret_cast<u8*>(work) + 0x28) =
        at<Mapper>(kMapA)(config[0]);
    *reinterpret_cast<u32*>(reinterpret_cast<u8*>(work) + 0x2C) =
        at<Mapper>(kMapB)(config[1]);
    *reinterpret_cast<u32*>(reinterpret_cast<u8*>(work) + 0x30) =
        at<Mapper>(kMapC)(config[2]);

    // Match the original's final eight-byte copy and inherited return value.
    return at<CopyPair>(kCopyPair)(reinterpret_cast<u8*>(work) + 0x34, config);
}

extern "C" std::uint32_t candidate_002f4ca0(void* arg) {
    return initialize_title_config<0x18>(arg);
}

// Deliberate negative control: binds the sprite table with one fewer entry.
extern "C" std::uint32_t candidate_002f4ca0_wrong_count(void* arg) {
    return initialize_title_config<0x17>(arg);
}

