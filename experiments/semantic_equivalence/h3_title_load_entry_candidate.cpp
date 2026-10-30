#include <cstddef>
#include <cstdint>

namespace {
using u8 = std::uint8_t;
using s16 = std::int16_t;
using u32 = std::uint32_t;

struct SaveLoadManagerPrefix { u8 flags; u8 pad[3]; u8* work; };
static_assert(offsetof(SaveLoadManagerPrefix, work) == 4);

struct PresentationPoint { u8 pad[8]; s16 x; s16 y; };
static_assert(offsetof(PresentationPoint, x) == 8);
static_assert(offsetof(PresentationPoint, y) == 10);
} // namespace

extern "C" void h3_original_save_load_ui_calc(void*, void*) asm("h3_original_save_load_ui_calc");
extern "C" void* h3_original_get_presentation_point(u32, u32) asm("h3_original_get_presentation_point");

// Editable candidate for 0x0030A9A4. The original UI allocator and presentation
// lookup remain explicit dependencies; this reconstructs the title handoff and
// stores observed in the pinned ARM body.
extern "C" void h3_title_load_entry_candidate(void*) {
    h3_original_save_load_ui_calc(nullptr, nullptr);

    auto* const manager = reinterpret_cast<SaveLoadManagerPrefix*>(0x0044DE28);
    auto* const work = manager->work;
    *reinterpret_cast<u32*>(work + 0x14) = 0;
    manager->flags = 0;
    manager->pad[0] = 0;
    work[0x49] = 0;
    work[0x379] = 1;

    const auto* const point = static_cast<const PresentationPoint*>(
        h3_original_get_presentation_point(0x36, 3));
    *reinterpret_cast<float*>(work + 0x38) = static_cast<float>(point->x);
    *reinterpret_cast<float*>(work + 0x3C) = static_cast<float>(point->y);

    work[0x49] = 0;
    *reinterpret_cast<u32*>(work + 0x34) = 1;
    *reinterpret_cast<u32*>(work + 0x50) = 9;
}
