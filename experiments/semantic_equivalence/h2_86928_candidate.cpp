#include <stdint.h>

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
extern "C" void script_vm_func_002b8b78(uint32_t);
extern "C" void engine_func_002b8584(uint32_t);
extern "C" void battle_func_0028df54(uint32_t);
extern "C" void ui_func_0028df3c(uint32_t);
extern "C" void script_vm_func_0028df0c(uint32_t);

extern "C" __attribute__((minsize)) uint32_t candidate_00286928(
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
    uint32_t global_object = *reinterpret_cast<volatile uint32_t*>(object + 4);
    if (arg5 != 0) {
        ui_func_002c4bf0(global_object, 0x20);
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
