#include "types.h"

extern "C" {
void func_002c68bc(void* p, const void* desc, u32 arg2, u32 arg3);
}

// Five callable initialization/teardown thunks embedded after the third
// texture-conversion leaf block. Literal pairs between them stay data rows.
// DECOMP_FUNC(0x0017f5c0, 12)
__attribute__((used)) void func_0017f5c0(unsigned int* object) {
    *object = 0;
}

// DECOMP_FUNC(0x0017f5cc, 20)
void func_0017f5cc() {
    func_002c68bc(reinterpret_cast<void*>(0x004DACE0), reinterpret_cast<const void*>(0x00361C24), 0x40, 2);
}

// DECOMP_FUNC(0x0017f5e8, 16)
void func_0017f5e8(unsigned int* object) {
    object[0] = 0;
    object[1] = 0;
}

// DECOMP_FUNC(0x0017f5f8, 16)
void func_0017f5f8(unsigned int* object) {
    object[0] = 0;
    object[1] = 0;
}

// DECOMP_FUNC(0x0017f608, 20)
void func_0017f608() {
    func_002c68bc(reinterpret_cast<void*>(0x004E5290), reinterpret_cast<const void*>(0x003578E8), 4, 3);
}
