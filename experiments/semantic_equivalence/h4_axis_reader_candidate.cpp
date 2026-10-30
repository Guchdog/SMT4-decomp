using u8 = unsigned char;
using s16 = short;
using u32 = unsigned int;
extern "C" float h4_original_deadzone(float* value, float threshold);
extern "C" int h4_axis_reader_candidate(float* out_x, float* out_y, u32 mode) {
    const auto* state = reinterpret_cast<const u8*>(0x004650a0);
    const auto* calibration = *reinterpret_cast<const u8* const*>(state);
    const u8 selector = calibration[0x18];
    const u32 axis = selector == 0 ? 0 : selector == 1 ? 1 : 2;
    const auto* lo = reinterpret_cast<const s16*>(calibration + 0x0c);
    const auto* hi = reinterpret_cast<const s16*>(calibration + 0x12);
    const float span = static_cast<float>(static_cast<int>(hi[axis]) - static_cast<int>(lo[axis]));
    if (mode >= 2 || *reinterpret_cast<const u32*>(state + 4) < mode) return 0;
    const u32 flags = *reinterpret_cast<const u32*>(state + 8);
    const auto* sample = reinterpret_cast<const u8*>(flags & 1 ? 0x004e3c48 : 0x004e3c28 + mode * 16);
    float x = static_cast<float>(*reinterpret_cast<const s16*>(sample + 0x0c)) / span;
    float y = static_cast<float>(*reinterpret_cast<const s16*>(sample + 0x0e)) / span;
    const float threshold = *reinterpret_cast<const float*>(state + 0x14);
    if (threshold != 0.0f) {
        h4_original_deadzone(&x, threshold);
        h4_original_deadzone(&y, threshold);
        if (x == 0.0f && y == 0.0f) return 0;
    }
    if (out_x) *out_x = x;
    if (out_y) *out_y = y;
    return 1;
}
