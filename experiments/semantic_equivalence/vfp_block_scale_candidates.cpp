#include <stdint.h>

using f32 = float;

// Isolated semantic reconstructions of two matching ARM/VFP routines.
// They load all source lanes and scale factors before writing the destination,
// preserving the original behavior when ordinary RAM buffers overlap.
extern "C" __attribute__((noinline, used)) void candidate_0015f6d4(
    f32* destination, const f32* factors, const f32* source) {
    const f32 x0 = source[0];
    const f32 x1 = source[1];
    const f32 x2 = source[2];
    const f32 x3 = source[3];
    const f32 x4 = source[4];
    const f32 x5 = source[5];
    const f32 x6 = source[6];
    const f32 x7 = source[7];
    const f32 x8 = source[8];
    const f32 x9 = source[9];
    const f32 x10 = source[10];
    const f32 x11 = source[11];
    const f32 f0 = factors[0];
    const f32 f1 = factors[1];
    const f32 f2 = factors[2];

    const f32 y0 = x0 * f0;
    const f32 y1 = x1 * f0;
    const f32 y2 = x2 * f0;
    const f32 y3 = x3 * f0;
    const f32 y4 = x4 * f1;
    const f32 y5 = x5 * f1;
    const f32 y6 = x6 * f1;
    const f32 y7 = x7 * f1;
    const f32 y8 = x8 * f2;
    const f32 y9 = x9 * f2;
    const f32 y10 = x10 * f2;
    const f32 y11 = x11 * f2;

    destination[0] = y0;
    destination[1] = y1;
    destination[2] = y2;
    destination[3] = y3;
    destination[4] = y4;
    destination[5] = y5;
    destination[6] = y6;
    destination[7] = y7;
    destination[8] = y8;
    destination[9] = y9;
    destination[10] = y10;
    destination[11] = y11;
}

extern "C" __attribute__((noinline, used)) void candidate_00256ed8(
    f32* destination, const f32* factors, const f32* source) {
    const f32 x0 = source[0];
    const f32 x1 = source[1];
    const f32 x2 = source[2];
    const f32 x3 = source[3];
    const f32 x4 = source[4];
    const f32 x5 = source[5];
    const f32 x6 = source[6];
    const f32 x7 = source[7];
    const f32 x8 = source[8];
    const f32 x9 = source[9];
    const f32 x10 = source[10];
    const f32 x11 = source[11];
    const f32 f0 = factors[0];
    const f32 f1 = factors[1];
    const f32 f2 = factors[2];

    const f32 y0 = x0 * f0;
    const f32 y1 = x1 * f0;
    const f32 y2 = x2 * f0;
    const f32 y3 = x3 * f0;
    const f32 y4 = x4 * f1;
    const f32 y5 = x5 * f1;
    const f32 y6 = x6 * f1;
    const f32 y7 = x7 * f1;
    const f32 y8 = x8 * f2;
    const f32 y9 = x9 * f2;
    const f32 y10 = x10 * f2;
    const f32 y11 = x11 * f2;

    destination[0] = y0;
    destination[1] = y1;
    destination[2] = y2;
    destination[3] = y3;
    destination[4] = y4;
    destination[5] = y5;
    destination[6] = y6;
    destination[7] = y7;
    destination[8] = y8;
    destination[9] = y9;
    destination[10] = y10;
    destination[11] = y11;
}

// Deliberate negative controls for factor grouping and lane order.
extern "C" __attribute__((noinline, used)) void wrong_factor_0015f6d4(
    f32* destination, const f32* factors, const f32* source) {
    for (unsigned i = 0; i < 12; ++i)
        destination[i] = source[i] * factors[(i / 4 + 1) % 3];
}

extern "C" __attribute__((noinline, used)) void wrong_lane_00256ed8(
    f32* destination, const f32* factors, const f32* source) {
    for (unsigned i = 0; i < 12; ++i)
        destination[i] = source[(i + 1) % 12] * factors[i / 4];
}
