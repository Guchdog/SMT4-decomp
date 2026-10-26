#include "types.h"

// Experimental reconstruction of the single-threaded behavior at 0x002C00D4.
// This is an ordinary 32-bit load/store, not an atomic synchronization API.
extern "C" __attribute__((noinline)) u32 candidate_002c00d4(u32* flag) {
    const u32 previous = *flag;
    if (previous != 0)
        return 0;

    *flag = 1;
    return 1;
}
