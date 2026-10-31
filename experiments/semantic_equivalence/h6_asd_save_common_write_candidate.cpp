#include <cstdint>

typedef uint32_t u32;
typedef uint8_t u8;

extern "C" {
    void* AsdMem_Alloc_002c54f0(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void  AsdMem_Free(void* ptr);
    void  AsdMem_CopyFrom(const void* src, void* dst, u32 size);
    u32   AsdSave_Write(u32 device, u32 file, const void* buffer, u32 size);
}

extern "C" u32 h6_asd_save_common_write_candidate(u32 device, u32 file, const void* header, const void* payload, u32 payload_size) {
    u32 total = payload_size + 0x80;
    u8* buffer = static_cast<u8*>(AsdMem_Alloc_002c54f0(0x100, 0x100, 0, total, 1));
    if (!buffer) return 0;
    if (header) {
        AsdMem_CopyFrom(header, buffer, 0x80);
    }
    if (payload && payload_size > 0) {
        AsdMem_CopyFrom(payload, buffer + 0x80, payload_size);
    }
    u32 result = AsdSave_Write(device, file, buffer, total);
    AsdMem_Free(buffer);
    return result;
}

extern "C" u32 h6_asd_save_common_write_mutation(u32 device, u32 file, const void* header, const void* payload, u32 payload_size) {
    return 0xDEADBEEF;
}
