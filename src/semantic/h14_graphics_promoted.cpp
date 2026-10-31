#include <cstdint>
typedef uint32_t u32;

struct AsdGpuWork {
    u32 pad;
    u32 heap_size;
};

extern "C" {
    extern AsdGpuWork g_AsdGpuWork_00471b48;
}

extern "C" u32 h14_asdgpu_heapsize_promoted() {
    return g_AsdGpuWork_00471b48.heap_size;
}

extern "C" u32 h14_asdgpu_heapsize_mutation() {
    return 0;
}
