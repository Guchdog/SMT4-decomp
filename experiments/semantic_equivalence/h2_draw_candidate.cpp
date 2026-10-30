// Experimental readable reconstruction of TitleConfig_Draw (0x002CAFD0).
// Rendering, cursor, TBB, layout, and input semantics remain original helpers.
using u8 = unsigned char;
using s16 = short;
using s32 = int;
using u32 = unsigned int;
using f32 = float;

static constexpr u32 kWorkGlobal = 0x0044E2D0u;
static constexpr u32 kRenderRootGlobal = 0x0044EA00u;
static constexpr u32 kTextFormatString = 0x002CB410u; // original "%s" literal
static constexpr u32 kUnselectedColor = 0xE09800FFu;
static constexpr u32 kSelectedColor = 0x72E027FFu;

template <typename Result, typename... Args>
static __attribute__((always_inline)) inline Result call(u32 address, Args... args) {
    using Function = Result (*)(Args...);
    return reinterpret_cast<Function>(address)(args...);
}

static __attribute__((always_inline)) inline u32 word(const void* base, u32 offset) {
    return *reinterpret_cast<const u32*>(reinterpret_cast<const u8*>(base) + offset);
}

static __attribute__((always_inline)) inline s16 half(const void* base, u32 offset) {
    return *reinterpret_cast<const s16*>(reinterpret_cast<const u8*>(base) + offset);
}

static __attribute__((always_inline)) inline void panel(u32 node, s32 x, s32 y,
                                                          u32 aux, bool with_aux = true) {
    if (with_aux) {
        call<void>(0x002BF558u, 2u, 0x2Fu, node, static_cast<u32>(x),
                   static_cast<u32>(y), aux);
    } else {
        call<void>(0x002BF460u, 2u, 0x2Fu, node, static_cast<u32>(x),
                   static_cast<u32>(y), aux);
    }
}

static __attribute__((always_inline)) inline void cached_render_update(u32 first, u32 second) {
    u32* root = reinterpret_cast<u32*>(kRenderRootGlobal);
    u8* cache = reinterpret_cast<u8*>(*root) + 0x1000u + 0x2ACu;
    const u32 value = call<u32>(0x002C5FA4u, 6u, first, second);
    const u32 index = *reinterpret_cast<u32*>(cache);
    u32* slot = reinterpret_cast<u32*>(cache + index * 4u + 8u);
    const u32 previous = *slot;
    *slot = value;
    if (cache[0x18] != 0 || previous != value) {
        const u32 callback = *reinterpret_cast<u32*>(cache + 0x1Cu);
        // The original indirect BLX preserves the just-returned render value
        // in r0 as its incoming argument even though this callback is opaque.
        call<void>(callback, value);
        cache[0x18] = 0;
    }
}

static __attribute__((always_inline)) inline bool active_touch(s32 result) {
    return result == 1 || result == 2 || result == 6;
}

// The callback argument is ignored by the original. Return zero on the one
// normal exit path; a null global/work pointer remains outside this candidate's
// tested initialized-state domain, matching the original's unchecked reads.
extern "C" __attribute__((noinline)) u32 candidate_002cafd0(void* unused_callback_arg) {
    (void)unused_callback_arg;
    u32* global = reinterpret_cast<u32*>(kWorkGlobal);
    u8* work = reinterpret_cast<u8*>(*global);

    const s32 sprite_x = static_cast<s32>(call<u32>(0x002BEF7Cu, work + 0x5Cu));
    const s32 sprite_y = static_cast<s32>(call<u32>(0x002BEF70u, work + 0x5Cu));
    const bool title_config_active = word(work, 8) == 1;

    // Common panel setup uses six stack/register arguments in the original.
    panel(0x0Cu, sprite_x, sprite_y, 0x0Bu, true);

    const s32 initial_scroll = call<s32>(0x0029F260u, work + 0xE8u);
    const s32 selected_row = call<s32>(0x0029F248u, work + 0xE8u);
    const s32 selected_absolute = selected_row + initial_scroll;
    s32 row = 0;
    s32 row_count = call<s32>(0x0029D8E4u, work + 0xE8u);

    while (row_count > 0 && row < row_count) {
        bool selected = false;
        u32 text_color = kUnselectedColor;
        if (title_config_active) {
            const s32 scroll_now = call<s32>(0x0029F260u, work + 0xE8u);
            if (scroll_now + row == selected_absolute) {
                selected = true;
                text_color = kSelectedColor;
            }
        }

        u8* row_node = reinterpret_cast<u8*>(
            call<u32>(0x002BF6D0u, 0x2Fu, static_cast<u32>(row + 0x1F)));
        const s32 row_node_x = half(row_node, 8);
        const s32 row_node_y = half(row_node, 0xA);
        const s32 row_x = sprite_x + row_node_x;
        const s32 row_y = sprite_y + row_node_y;

        cached_render_update(1u, 0u);

        if (selected) {
            panel(0x0Du, row_x, row_y, 0x0Bu, false);
            cached_render_update(7u, 0u);
            panel(1u, row_x, row_y, 0x10u, true);
            cached_render_update(1u, 0u);
            panel(2u, row_x, row_y, 0x15u, true);
            cached_render_update(7u, 0u);
        } else {
            panel(0x0Cu, row_x, row_y, 0x0Bu, false);
            cached_render_update(7u, 0u);
            panel(1u, row_x, row_y, 0x10u, true);
        }

        u8* heading_node = reinterpret_cast<u8*>(
            call<u32>(0x002BF6D0u, 0x2Fu, 0x1Au));
        const s32 absolute_index = call<s32>(0x0029F260u, work + 0xE8u) + row;
        // The original uses CMP followed by BHS, so this range test is unsigned.
        if (static_cast<u32>(absolute_index) < 3u) {
            const u32 table = call<u32>(0x002C0EC4u, 0x3Au, 1u);
            const u32 payload = call<u32>(0x002C0E9Cu, table);
            const u32 descriptor = payload + static_cast<u32>(absolute_index) * 0x96u;
            char formatted[0x5Cu];
            call<void>(0x002BE7FDu, formatted, kTextFormatString, descriptor);

            const s32 text_x = sprite_y + row_node_y + half(heading_node, 0xA);
            const s32 text_y = sprite_x + row_node_x + half(heading_node, 8);
            call<void>(0x002BE77Cu, 2u, text_color, formatted,
                       static_cast<f32>(text_y), static_cast<f32>(text_x),
                       0.0f, 0.0f, 1.0f);
        }

        if (!selected) {
            // The nonactive row path draws the paired row marker here before
            // the common option-value panel and cursor lookup.
            call<void>(0x002BF460u, 2u, 0x2Fu, 0x1Bu,
                       static_cast<u32>(row_x), static_cast<u32>(row_y), 0x1Fu);
        }

        if (selected) {
            panel(0x1Cu, row_x, row_y, 0x1Fu, false);
            const s32 row_touch = call<s32>(0x0029D8FCu,
                                             static_cast<u32>(static_cast<s32>(half(work, 0x1C))));
            if (active_touch(row_touch)) {
                cached_render_update(1u, 0u);
                panel(0x1Du, row_x, row_y, 0x1Fu, false);
                cached_render_update(7u, 0u);
            }
        }

        // The original fetches the option after the header/touch branch and
        // after issuing the common row-value panel command.
        const s32 option_index = call<s32>(0x0029F260u, work + 0xE8u) + row;
        u32* value_words = reinterpret_cast<u32*>(work + 0x28u);
        const s32 option_value = static_cast<s32>(value_words[option_index]);
        panel(3u, row_x, row_y, 0x1Fu, true);
        u8* value_node = reinterpret_cast<u8*>(call<u32>(
            0x002BF6D0u, 0x2Fu, static_cast<u32>(option_value + 0x5B)));

        if (selected) {
            const s32 decrement_touch = call<s32>(0x0029D8FCu,
                static_cast<u32>(static_cast<s32>(half(work, 0x1E))));
            if (active_touch(decrement_touch)) {
                panel(5u, row_x, row_y, 0x15u, true);
            } else {
                panel(4u, row_x, row_y, 0x1Fu, true);
            }
            const s32 increment_touch = call<s32>(0x0029D8FCu,
                static_cast<u32>(static_cast<s32>(half(work, 0x20))));
            if (active_touch(increment_touch)) {
                panel(7u, row_x, row_y, 0x15u, true);
            } else {
                panel(6u, row_x, row_y, 0x1Fu, true);
            }
            const s32 special_touch = call<s32>(0x0029D8FCu,
                static_cast<u32>(static_cast<s32>(half(work, 0x22))));
            const s32 node_y = half(value_node, 0xA);
            const s32 node_x = half(value_node, 8);
            if (active_touch(special_touch)) {
                call<void>(0x002BF460u, 2u, 0x2Fu, 0x32u,
                           static_cast<u32>(row_x + node_x),
                           static_cast<u32>(row_y + node_y), 0x29u);
            } else {
                call<void>(0x002BF460u, 2u, 0x2Fu, 0x31u,
                           static_cast<u32>(row_x + node_x),
                           static_cast<u32>(row_y + node_y), 0x29u);
            }
        } else {
            panel(4u, row_x, row_y, 0x1Fu, true);
            panel(6u, row_x, row_y, 0x1Fu, true);
            call<void>(0x002BF460u, 2u, 0x2Fu, 0x31u,
                       static_cast<u32>(row_x + half(value_node, 8)),
                       static_cast<u32>(row_y + half(value_node, 0xA)), 0x29u);
        }

        ++row;
        row_count = call<s32>(0x0029D8E4u, work + 0xE8u);
    }
    return 0;
}
