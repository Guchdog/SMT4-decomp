#include <cstdint>
typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;

extern "C" {
    u32 app_func_00296f60(u32);
    u8* app_func_00293c98();
    void app_func_00245318(u8*, u32);
    u8* engine_func_002c0e9c();
    void app_func_0028df54(u16);
}

extern "C" u32 h10_camp_appstore_getappparam_candidate() {
    u32 r4 = app_func_00296f60(0);
    u8* r0 = app_func_00293c98();
    app_func_00245318(r0, 4);
    u8* table = engine_func_002c0e9c();
    u16 val = *reinterpret_cast<u16*>(table + (r4 * 4));
    app_func_0028df54(val);
    return 1;
}

extern "C" void h10_camp_appstore_getappparam_mutation() {
    // Deliberate bug
}
