// Readable semantic candidate for TitleConfig_Calc (0x001EA928).
// External engine behavior remains behind the pinned original service addresses.
using u8 = unsigned char;
using u16 = unsigned short;
using s16 = short;
using s32 = int;
using u32 = unsigned int;

static constexpr u32 kWorkGlobal = 0x0044E2D0u;
static constexpr u32 kConfig = 0x0044E0F8u;
static constexpr u32 kTbbTouch = 0x0100016Cu;
static constexpr u32 kTbbEdit = 0x0100016Du;
static constexpr u32 kTbbExit = 0x0100016Eu;

template <typename Result, typename... Args>
static __attribute__((always_inline)) inline Result call(u32 address, Args... args) {
    using Function = Result (*)(Args...);
    return reinterpret_cast<Function>(address)(args...);
}

static __attribute__((always_inline)) inline u32* work_global() {
    return reinterpret_cast<u32*>(kWorkGlobal);
}

static __attribute__((always_inline)) inline u8* config_bytes() {
    return reinterpret_cast<u8*>(kConfig);
}

static __attribute__((always_inline)) inline u32* word(u32* work, u32 offset) {
    return reinterpret_cast<u32*>(reinterpret_cast<u8*>(work) + offset);
}

static __attribute__((always_inline)) inline void display_row(u32* work, u32 row) {
    const u32 scroll = call<u32>(0x0029F260u, work + 0x3A);
    const u32 selected = call<u32>(0x0029F248u, work + 0x3A);
    const u32 table = call<u32>(0x002C0EC4u, 0x3Au, 1u);
    u32 payload = call<u32>(0x002C0E9Cu, table);
    const u32 tbb_index = scroll + selected;
    payload += 0x16u + tbb_index * 0x96u;
    call<void>(0x0029F10Cu, payload, 0x323232FFu);
}

static __attribute__((always_inline)) inline void map_row_default(u32* work, u32 row) {
    u8* config = config_bytes();
    if (row == 0) {
        config[0] = 0x32;
        *word(work, 0x28) = call<u32>(0x002CAB70u, 0x32u);
    } else if (row == 1) {
        config[1] = 0x50;
        config[3] = 0x30;
        *word(work, 0x2C) = call<u32>(0x0021F39Cu, static_cast<u32>(config[1]));
    } else if (row == 2) {
        config[2] = 0x50;
        *word(work, 0x30) = call<u32>(0x002E0AF4u, static_cast<u32>(config[2]));
    }
    call<void>(0x002B91C4u, kTbbEdit);
}

static __attribute__((always_inline)) inline void encode_live_values(u32* work) {
    u8* config = config_bytes();
    config[0] = static_cast<u8>(call<u32>(0x001FE3B8u, *word(work, 0x28)));
    config[1] = static_cast<u8>(call<u32>(0x001EA7F0u, *word(work, 0x2C)));
    config[2] = static_cast<u8>(call<u32>(0x0021F3F8u, *word(work, 0x30)));
    config[3] = static_cast<u8>(call<u32>(0x0020FDC8u, *word(work, 0x2C)));
}

static __attribute__((always_inline)) inline void changed_value_effects(u32 row) {
    call<void>(0x002C5A6Cu);
    u32 value = call<u32>(0x0025A0A4u);
    call<void>(0x0025A004u, 0u, value, 1u);
    value = call<u32>(0x0025A0A4u);
    call<void>(0x0025A004u, 1u, value, 1u);
    if (row == 0 || row == 1) {
        call<void>(0x002B91C4u, kTbbEdit);
    } else if (row == 2) {
        call<void>(0x002BC210u);
        const u32 result = call<u32>(0x002BFF9Cu);
        const float effect_parameter = *reinterpret_cast<const float*>(0x001EB01Cu);
        call<void, u32, u32, u32, u32, float, float>(
            0x002BFDFCu, 0u, 0x2712u, result, 2u, effect_parameter, effect_parameter);
    }
}

static __attribute__((always_inline)) inline void changed_row_effects(u32* work) {
    call<void>(0x002C5A6Cu);
    u32 value = call<u32>(0x0025A0A4u);
    call<void>(0x0025A004u, 0u, value, 1u);
    value = call<u32>(0x0025A0A4u);
    call<void>(0x0025A004u, 1u, value, 1u);
    (void)work;
}

extern "C" s32 candidate_001ea928() {
    u32* work = reinterpret_cast<u32*>(*work_global());
    u8* config = config_bytes();
    const u32 state = *word(work, 0x08);

    if (state >= 5u) {
        return 0;
    }
    if (state == 0u) {
        if (call<s32>(0x002A63F8u, 0x2Fu, 0u) == 0) {
            return 0;
        }
        if (call<s32>(0x002BF9F0u, reinterpret_cast<u8*>(work) + 0x5Cu) == 0 ||
            *word(work, 0x14C) == 0 || *word(work, 0x150) == 0) {
            return 0;
        }
        *reinterpret_cast<u16*>(reinterpret_cast<u8*>(work) + 0x14) =
            static_cast<u16>(call<u32>(0x002B88C4u, 0x2Fu, 0x1Fu));
        ++*reinterpret_cast<u16*>(reinterpret_cast<u8*>(work) + 0x1A);
        *reinterpret_cast<u16*>(reinterpret_cast<u8*>(work) + 0x16) =
            static_cast<u16>(call<u32>(0x002B88C4u, 0x2Fu, 0x20u));
        ++*reinterpret_cast<u16*>(reinterpret_cast<u8*>(work) + 0x1A);
        *reinterpret_cast<u16*>(reinterpret_cast<u8*>(work) + 0x18) =
            static_cast<u16>(call<u32>(0x002B88C4u, 0x2Fu, 0x21u));
        ++*reinterpret_cast<u16*>(reinterpret_cast<u8*>(work) + 0x1A);
        display_row(work, 0);
        call<void>(0x0025A0D0u);
        const u32 script_result = call<u32>(0x002972F8u, *word(work, 0x14C), *word(work, 0x150));
        *word(work, 0x08) = 1;
        *word(work, 0x154) = script_result;
        return 0;
    }

    if (state == 1u) {
        const u32 scroll = call<u32>(0x0029F260u, work + 0x3A);
        const u32 row = call<u32>(0x0029F248u, work + 0x3A);
        const u32 selection = scroll + row;
        const u32 selection_offset = selection * 4u + 0x28u;
        u32* selected_value = word(work, selection_offset);
        const u32 entry_value = *selected_value;

        (void)call<u32>(0x002C0E9Cu,
            call<u32>(0x002C0EC4u, 0x3Au, 1u));
        const s16 row_handle = *reinterpret_cast<s16*>(reinterpret_cast<u8*>(work) + 0x1C);
        if (row_handle >= 0) {
            const s32 touch = call<s32>(0x0029D8FCu, row_handle);
            if (touch == 6 || call<s32>(0x002C1830u, 9u, 1u) != 0) {
                map_row_default(work, row);
            }
        }

        bool decrement = false;
        bool increment = false;
        const s32 touch_dec = call<s32>(0x0029D8FCu,
            *reinterpret_cast<s16*>(reinterpret_cast<u8*>(work) + 0x1E));
        if (touch_dec == 1) {
            decrement = call<s32>(0x0025A0B4u) < 1;
        } else if (touch_dec == 2) {
            decrement = true;
        }
        const s32 touch_inc = call<s32>(0x0029D8FCu,
            *reinterpret_cast<s16*>(reinterpret_cast<u8*>(work) + 0x20));
        if (touch_inc == 1) {
            increment = call<s32>(0x0025A0B4u) < 1;
        } else if (touch_inc == 2) {
            increment = true;
        }

        if (!decrement) {
            decrement = call<s32>(0x002C1830u, 4u, 0u) != 0;
        }
        if (decrement) {
            if (*selected_value != 0u) {
                --*selected_value;
            }
            call<void>(0x002C1830u, 4u, 0u);
        } else if (!increment && call<s32>(0x002C1830u, 3u, 0u) != 0) {
            increment = true;
        }
        if (increment) {
            if (*selected_value < 10u) {
                ++*selected_value;
            }
            call<void>(0x002C1830u, 3u, 0u);
        }

        if (!decrement && !increment) {
            const s16 special_handle = *reinterpret_cast<s16*>(reinterpret_cast<u8*>(work) + 0x22);
            const s32 special = call<s32>(0x0029D8FCu, special_handle);
            if (special == 1 || special == 2) {
                const u32* info = reinterpret_cast<const u32*>(
                    call<u32>(0x002BF6D0u, 0x2Fu, 0x33u));
                const s32 script_value = call<s32>(0x001C3588u);
                const s32 current = call<s32>(0x001DD158u, special_handle);
                // ARM performs these register operations modulo 2^32. Keep
                // the helper arguments' bit patterns without signed overflow.
                const u32 difference = static_cast<u32>(script_value) -
                                       static_cast<u32>(current);
                const u32 scale = difference * 5u;
                const u32 doubled_scale = scale * 2u;
                const s16 limit = *reinterpret_cast<const s16*>(info[3]);
                *selected_value = call<u32>(0x002C615Cu,
                    doubled_scale, static_cast<u32>(limit), scale);
            }
        }

        encode_live_values(work);
        if (*selected_value != entry_value) {
            changed_value_effects(row);
            return 0;
        }

        if (call<s32>(0x0029F278u, work + 0x3A, 1u) != 0) {
            work = reinterpret_cast<u32*>(*work_global());
            display_row(work, 0);
            call<void>(0x0025A0D0u);
            return 0;
        }

        const u32 selected_row = call<u32>(0x0029F248u,
            reinterpret_cast<u8*>(work) + 0xE8u);
        for (u32 handled = 0; handled < 3u; ++handled) {
            if (handled == selected_row) {
                continue;
            }
            const s16 handle = *reinterpret_cast<s16*>(reinterpret_cast<u8*>(work) + 0x14u + handled * 2u);
            if (call<s32>(0x0029D8FCu, handle) == 6) {
                call<void>(0x002B91C4u, kTbbTouch);
                call<void>(0x0029EDFCu, reinterpret_cast<u8*>(work) + 0xE8u, handled);
                work = reinterpret_cast<u32*>(*work_global());
                display_row(work, 0);
                call<void>(0x0025A0D0u);
                return 0;
            }
        }

        if (call<s32>(0x002C1830u, 0u, 1u) != 0) {
            call<void>(0x002BC200u, kTbbEdit);
            call<void>(0x002971E4u, *word(work, 0x154), 2u);
            *word(work, 0x08) = 2;
            return 0;
        }
        if (call<s32>(0x002C1830u, 1u, 1u) != 0) {
            call<void>(0x002BC200u, kTbbExit);
            call<void>(0x002BDAC0u, reinterpret_cast<u8*>(work) + 0x5Cu, 1u, 0u);
            call<void>(0x002ADB40u, config, reinterpret_cast<u8*>(work) + 0x34u);
            changed_row_effects(work);
            *word(work, 0x08) = 3;
            return 0;
        }
        return 0;
    }

    if (state == 2u) {
        if (call<s32>(0x0019DFBCu, *word(work, 0x154)) != 2) {
            return 0;
        }
        const s32 result = call<s32>(0x00297674u);
        if (result == 1) {
            *word(work, 0x08) = 1;
        } else if (result == 0) {
            call<void>(0x002BDAC0u, reinterpret_cast<u8*>(work) + 0x5Cu, 1u, 0u);
            config[4] = 1;
            *word(work, 0x08) = 3;
        }
        return 0;
    }

    if (state == 3u) {
        if (call<s32>(0x002BF9F0u, reinterpret_cast<u8*>(work) + 0x5Cu) != 0) {
            *word(work, 0x08) = 4;
        }
        return 0;
    }
    return -1;
}
