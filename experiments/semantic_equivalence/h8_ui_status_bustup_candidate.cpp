#include <cstdint>

typedef uint32_t u32;
typedef uint8_t u8;
typedef int8_t s8;

struct StatusBustUpWork {
    s8 ref_count;
    u8 pad[3];
    void* buffer1;
    void* buffer2;
};

extern "C" {
    void AsdRes_002c4e28(u32 id);
    void AsdRes_002c5b04(u32 id, u32 flag);
    void* AsdMem_Alloc_002c4b84(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void engine_func_002c3b48(void* ptr, u32 size);

    extern StatusBustUpWork g_StatusBustUpWork_0044e158;
}

extern "C" void h8_ui_status_bustup_candidate() {
    StatusBustUpWork* work = &g_StatusBustUpWork_0044e158;
    if (work->ref_count <= 0) {
        AsdRes_002c4e28(0x17);
        AsdRes_002c5b04(0x23, 0);
        if (!work->buffer1) {
            void* b1 = AsdMem_Alloc_002c4b84(0x100, 0x100, 0, 0x266, 1);
            work->buffer1 = b1;
            engine_func_002c3b48(b1, 0x266);
        }
        if (!work->buffer2) {
            void* b2 = AsdMem_Alloc_002c4b84(0x100, 0x100, 0, 0x81, 1);
            work->buffer2 = b2;
            engine_func_002c3b48(b2, 0x81);
        }
    }
    work->ref_count++;
}

extern "C" void h8_ui_status_bustup_mutation() {
    g_StatusBustUpWork_0044e158.ref_count = -1;
}
