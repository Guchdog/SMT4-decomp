#include <stdint.h>
extern "C" __attribute__((minsize)) uint32_t candidate_002b8d24(uint8_t* object, uint32_t selector) {
    using Reset = uint8_t* (*)(uint8_t*, uint32_t, uint32_t);
    using Process = uint32_t (*)(uint8_t*, uint32_t);
    using SetByte = uint8_t* (*)(uint8_t*, uint32_t);
    auto reset = reinterpret_cast<Reset>(0x002af854);
    auto process = reinterpret_cast<Process>(0x002bf030);
    auto set_byte = reinterpret_cast<SetByte>(0x001384f0);
    if (selector >= 19) return reinterpret_cast<uint32_t>(object);
    if (selector == 1 || selector == 10)
        return reinterpret_cast<uint32_t>(reset(object + 0xc4, 2, 0));
    if ((selector >= 2 && selector <= 5) || selector >= 16) {
        reset(object + 0xc4, 2, 0);
        reset(object + 0x1dc, 2, 0);
        return reinterpret_cast<uint32_t>(set_byte(object + 0x150, 0));
    }
    if (selector == 6) {
        auto value = *reinterpret_cast<uint32_t*>(object + 0xe4);
        if (value != 0x3f800000) return value;
        return reinterpret_cast<uint32_t>(reset(object + 0xc4, 2, 0));
    }
    if (selector >= 7 && selector <= 9) {
        reset(object + 0xc4, 2, 0);
        return reinterpret_cast<uint32_t>(reset(object + 0x40c, 2, 0));
    }
    if (selector == 11) {
        process(object + 0xc4, 7);
        process(object + 0x268, 7);
        return reinterpret_cast<uint32_t>(set_byte(object + 0x380, 0));
    }
    if (selector == 12) {
        for (uint32_t i = 0; i < 5; ++i)
            if (object[0x37 + i]) reset(object + 0x498 + i * 140, 5, 0);
        *reinterpret_cast<uint32_t*>(object + 0x28) = 0;
        return 0;
    }
    return reinterpret_cast<uint32_t>(object);
}
