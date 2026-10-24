#include <stdint.h>

using f32 = float;

// Semantic reconstruction of two matching ARM/VFP routines. The source and
// factors are fully captured before any destination writes, preserving the
// original ordinary-RAM behavior for overlapping aligned buffers.
extern "C" __attribute__((noinline, used)) void candidate_0023d368(
    f32* destination, const f32* source, const f32* factors) {
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
    const f32 y1 = x1 * f1;
    const f32 y2 = x2 * f2;
    const f32 y4 = x4 * f0;
    const f32 y5 = x5 * f1;
    const f32 y6 = x6 * f2;
    const f32 y8 = x8 * f0;
    const f32 y9 = x9 * f1;
    const f32 y10 = x10 * f2;

    destination[0] = y0;
    destination[1] = y1;
    destination[2] = y2;
    destination[3] = x3;
    destination[4] = y4;
    destination[5] = y5;
    destination[6] = y6;
    destination[7] = x7;
    destination[8] = y8;
    destination[9] = y9;
    destination[10] = y10;
    destination[11] = x11;
}

extern "C" __attribute__((noinline, used)) void candidate_0023e55c(
    f32* destination, const f32* source, const f32* factors) {
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
    const f32 y1 = x1 * f1;
    const f32 y2 = x2 * f2;
    const f32 y4 = x4 * f0;
    const f32 y5 = x5 * f1;
    const f32 y6 = x6 * f2;
    const f32 y8 = x8 * f0;
    const f32 y9 = x9 * f1;
    const f32 y10 = x10 * f2;

    destination[0] = y0;
    destination[1] = y1;
    destination[2] = y2;
    destination[3] = x3;
    destination[4] = y4;
    destination[5] = y5;
    destination[6] = y6;
    destination[7] = x7;
    destination[8] = y8;
    destination[9] = y9;
    destination[10] = y10;
    destination[11] = x11;
}

// Deliberate controls: wrong factor routing and wrong source-lane order.
extern "C" __attribute__((noinline, used)) void wrong_factor_0023d368(
    f32* destination, const f32* source, const f32* factors) {
    const f32 x0 = source[0], x1 = source[1], x2 = source[2];
    const f32 x3 = source[3], x4 = source[4], x5 = source[5];
    const f32 x6 = source[6], x7 = source[7], x8 = source[8];
    const f32 x9 = source[9], x10 = source[10], x11 = source[11];
    const f32 f0 = factors[0], f1 = factors[1], f2 = factors[2];
    destination[0] = x0 * f1;
    destination[1] = x1 * f2;
    destination[2] = x2 * f0;
    destination[3] = x3;
    destination[4] = x4 * f1;
    destination[5] = x5 * f2;
    destination[6] = x6 * f0;
    destination[7] = x7;
    destination[8] = x8 * f1;
    destination[9] = x9 * f2;
    destination[10] = x10 * f0;
    destination[11] = x11;
}

extern "C" __attribute__((noinline, used)) void wrong_lane_0023e55c(
    f32* destination, const f32* source, const f32* factors) {
    const f32 x0 = source[0], x1 = source[1], x2 = source[2];
    const f32 x3 = source[3], x4 = source[4], x5 = source[5];
    const f32 x6 = source[6], x7 = source[7], x8 = source[8];
    const f32 x9 = source[9], x10 = source[10], x11 = source[11];
    const f32 f0 = factors[0], f1 = factors[1], f2 = factors[2];
    destination[0] = x1 * f0;
    destination[1] = x2 * f1;
    destination[2] = x3 * f2;
    destination[3] = x3;
    destination[4] = x5 * f0;
    destination[5] = x6 * f1;
    destination[6] = x7 * f2;
    destination[7] = x7;
    destination[8] = x9 * f0;
    destination[9] = x10 * f1;
    destination[10] = x11 * f2;
    destination[11] = x11;
}
