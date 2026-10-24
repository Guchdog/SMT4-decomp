// Isolated semantic experiment only. These functions are not production code.
// The original routines load 12 float lanes from src, then three addends,
// add them to lanes 3/7/11, and store the 12 results to dst.
// Volatile accesses keep the load-before-store ordering visible for alias cases.

extern "C" void candidate_0023e4e4(volatile float *dst,
                                  const volatile float *addend,
                                  const volatile float *src) {
  float x0 = src[0]; float x1 = src[1]; float x2 = src[2]; float x3 = src[3];
  float x4 = src[4]; float x5 = src[5]; float x6 = src[6]; float x7 = src[7];
  float x8 = src[8]; float x9 = src[9]; float x10 = src[10]; float x11 = src[11];
  float y0 = addend[0]; float y1 = addend[1]; float y2 = addend[2];
  x3 = x3 + y0; x7 = x7 + y1; x11 = x11 + y2;
  dst[0] = x0; dst[1] = x1; dst[2] = x2; dst[3] = x3;
  dst[4] = x4; dst[5] = x5; dst[6] = x6; dst[7] = x7;
  dst[8] = x8; dst[9] = x9; dst[10] = x10; dst[11] = x11;
}

extern "C" void candidate_002a3788(volatile float *dst,
                                  const volatile float *addend,
                                  const volatile float *src) {
  float x0 = src[0]; float x1 = src[1]; float x2 = src[2]; float x3 = src[3];
  float x4 = src[4]; float x5 = src[5]; float x6 = src[6]; float x7 = src[7];
  float x8 = src[8]; float x9 = src[9]; float x10 = src[10]; float x11 = src[11];
  float y0 = addend[0]; float y1 = addend[1]; float y2 = addend[2];
  x3 = x3 + y0; x7 = x7 + y1; x11 = x11 + y2;
  dst[0] = x0; dst[1] = x1; dst[2] = x2; dst[3] = x3;
  dst[4] = x4; dst[5] = x5; dst[6] = x6; dst[7] = x7;
  dst[8] = x8; dst[9] = x9; dst[10] = x10; dst[11] = x11;
}

// Negative controls: wrong destination lanes and subtraction must be caught.
extern "C" void wrong_lanes_0023e4e4(volatile float *dst,
                                    const volatile float *addend,
                                    const volatile float *src) {
  float x[12];
  for (unsigned i = 0; i != 12; ++i) x[i] = src[i];
  float y0 = addend[0]; float y1 = addend[1]; float y2 = addend[2];
  x[2] = x[2] + y0; x[6] = x[6] + y1; x[10] = x[10] + y2;
  for (unsigned i = 0; i != 12; ++i) dst[i] = x[i];
}

extern "C" void wrong_operation_0023e4e4(volatile float *dst,
                                         const volatile float *addend,
                                         const volatile float *src) {
  float x[12];
  for (unsigned i = 0; i != 12; ++i) x[i] = src[i];
  float y0 = addend[0]; float y1 = addend[1]; float y2 = addend[2];
  x[3] = x[3] - y0; x[7] = x[7] - y1; x[11] = x[11] - y2;
  for (unsigned i = 0; i != 12; ++i) dst[i] = x[i];
}

extern "C" void wrong_lanes_002a3788(volatile float *dst,
                                    const volatile float *addend,
                                    const volatile float *src) {
  float x[12];
  for (unsigned i = 0; i != 12; ++i) x[i] = src[i];
  float y0 = addend[0]; float y1 = addend[1]; float y2 = addend[2];
  x[2] = x[2] + y0; x[6] = x[6] + y1; x[10] = x[10] + y2;
  for (unsigned i = 0; i != 12; ++i) dst[i] = x[i];
}

extern "C" void wrong_operation_002a3788(volatile float *dst,
                                         const volatile float *addend,
                                         const volatile float *src) {
  float x[12];
  for (unsigned i = 0; i != 12; ++i) x[i] = src[i];
  float y0 = addend[0]; float y1 = addend[1]; float y2 = addend[2];
  x[3] = x[3] - y0; x[7] = x[7] - y1; x[11] = x[11] - y2;
  for (unsigned i = 0; i != 12; ++i) dst[i] = x[i];
}
