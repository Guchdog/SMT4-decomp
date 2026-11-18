#include "types.h"

namespace h18_00207ffc {
using SkyId = s32 (*)(s32);
using CreateResource = u32 (*)(u32, const void*, u32);
using LoadResource = u32 (*)(char*, u32);
using PollResource = u32 (*)(u32);
using SetupResource = void (*)(u32, u32);
using SetFloat = void (*)(u32, u32, float);
using SetVector = void (*)(u32, u32, const float*);
using Format = s32 (*)(char*, const char*, ...);

inline u8* context() {
    return *reinterpret_cast<u8* volatile*>(0x004474D8u);
}

inline u16 read_u16(const u8* p, u32 off) {
    return *reinterpret_cast<const u16*>(p + off);
}
inline s16 read_s16(const u8* p, u32 off) {
    return *reinterpret_cast<const s16*>(p + off);
}
inline u32 read_u32(const u8* p, u32 off) {
    return *reinterpret_cast<const u32*>(p + off);
}
inline void write_u16(u8* p, u32 off, u16 value) {
    *reinterpret_cast<u16*>(p + off) = value;
}
inline void write_u32(u8* p, u32 off, u32 value) {
    *reinterpret_cast<u32*>(p + off) = value;
}

__attribute__((always_inline)) inline void setup_and_set_floats(
    u32 resource, u32 context_resource_offset) {
    const auto setup = reinterpret_cast<SetupResource>(0x002A06C8u);
    const auto set_a = reinterpret_cast<SetFloat>(0x002A5A54u);
    const auto set_b = reinterpret_cast<SetFloat>(0x00287300u);
    setup(resource, 1);
    u8* current_context = context();
    u32 current_resource = read_u32(current_context, context_resource_offset);
    u32 target = *reinterpret_cast<const u32*>(current_resource + 8);
    set_a(target, 0, 0.0f);
    current_context = context();
    current_resource = read_u32(current_context, context_resource_offset);
    target = *reinterpret_cast<const u32*>(current_resource + 8);
    set_b(target, 0, 0.0f);
}

inline void configure_extra(u32 resource, float s17) {
    const auto set_vector = reinterpret_cast<SetVector>(0x0028C8A8u);
    const float values[3] = {0.0f, s17, 0.0f};
    const u32 target = *reinterpret_cast<const u32*>(resource + 8);
    set_vector(target, 0, values);
}
}  // namespace h18_00207ffc

extern "C" u32 h18_00207ffc_candidate() {
    using namespace h18_00207ffc;
    const auto sky_id = reinterpret_cast<SkyId>(0x0020E5A4u);
    const auto create_resource = reinterpret_cast<CreateResource>(0x0025BE50u);
    const auto load_resource = reinterpret_cast<LoadResource>(0x0029A2D0u);
    const auto poll = reinterpret_cast<PollResource>(0x002AE16Cu);
    const auto format = reinterpret_cast<Format>(0x002BE7FCu);
    constexpr float kSecondVectorValue = -20000.0f;

    u8* self = context();
    const s16 state = read_s16(self, 8);

    if (state == 99) return 1;
    if (state < 0 || state > 11) return 0;

    if (state == 0) {
        const u32 setting = *reinterpret_cast<volatile const u32*>(0x0049FC7Cu);
        if (setting == 1) {
            write_u32(self, 0x0C, 0);
            write_u16(self, 8, 99);
            return 0;
        }
        const u32 embedded = read_u32(self, 0x28);
        if (embedded != 0) {
            const u32 result = create_resource(embedded,
                reinterpret_cast<const void*>(read_u32(self, 0x2C)), 0x1C0);
            self = context();
            write_u32(self, 0x10, result);
            setup_and_set_floats(result, 0x10);
            if (read_u16(context(), 4) == 0x13) {
                configure_extra(*reinterpret_cast<const u32*>(context() + 0x10),
                                kSecondVectorValue);
            }
            write_u16(context(), 8, 10);
            return 0;
        }

        const s32 id = sky_id(read_s16(self, 6));
        self = context();
        write_u32(self, 0x18, static_cast<u32>(id));
        if (id <= 0) {
            write_u16(self, 8, 10);
            return 0;
        }
        char path[0x80];
        format(path, reinterpret_cast<const char*>(0x00208328u), id);
        const u32 resource = load_resource(path, 0x1C0);
        self = context();
        write_u32(self, 0x10, resource);
        write_u16(self, 8, static_cast<u16>(read_u16(self, 8) + 1));
        if (poll(read_u32(context(), 0x10)) == 0) return 0;
        self = context();
        setup_and_set_floats(read_u32(self, 0x10), 0x10);
        if (read_u16(context(), 4) == 0x13) {
            configure_extra(read_u32(context(), 0x10), kSecondVectorValue);
        }
        write_u16(context(), 8, 10);
        return 0;
    }

    if (state == 1) {
        if (poll(read_u32(self, 0x10)) == 0) return 0;
        setup_and_set_floats(read_u32(context(), 0x10), 0x10);
        if (read_u16(context(), 4) == 0x13) {
            configure_extra(read_u32(context(), 0x10), kSecondVectorValue);
        }
        write_u16(context(), 8, 10);
        return 0;
    }

    if (state == 10) {
        const u32 embedded = read_u32(self, 0x20);
        if (embedded != 0) {
            const u32 result = create_resource(embedded,
                reinterpret_cast<const void*>(read_u32(self, 0x24)), 0x38);
            self = context();
            write_u32(self, 0x0C, result);
            setup_and_set_floats(result, 0x0C);
            write_u16(context(), 8, 99);
            return 0;
        }

        const s32 map_id = read_s16(self, 4);
        if (map_id == 0x29 || map_id == 0x2A || map_id == 0x2B) {
            write_u16(self, 0x1C, 0x24);
            write_u16(self, 0x1E, 1);
        } else {
            write_u16(self, 0x1C, static_cast<u16>(map_id));
            write_u16(self, 0x1E, read_u16(self, 6));
        }
        const s32 format_id = read_s16(self, 0x1C);
        const s32 format_variant = read_s16(self, 0x1E);
        char path[0x80];
        format(path, reinterpret_cast<const char*>(0x00208340u),
               format_id, format_id, format_variant);
        const u32 resource = load_resource(path, 0x38);
        self = context();
        write_u32(self, 0x0C, resource);
        write_u16(self, 8, static_cast<u16>(read_u16(self, 8) + 1));
        return 0;
    }

    if (state == 11) {
        if (poll(read_u32(self, 0x0C)) == 0) return 0;
        setup_and_set_floats(read_u32(context(), 0x0C), 0x0C);
        write_u16(context(), 8, 99);
        return 0;
    }

    return 0;
}
