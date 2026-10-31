#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

extern "C" {
    void* sub_2C0EC4(u32 table_id, u32 sub_id);
    void* sub_2C0E9C(void* table_handle);
    u32 sub_2C0E4C(void* table_handle);
}

extern "C" void* h11_shop_getcatalogentry_candidate(void* ctx, u32 index) {
    void* handle = sub_2C0EC4(0x17, 0);
    if (index >= sub_2C0E4C(handle)) {
        return nullptr;
    }
    u8* table_base = static_cast<u8*>(sub_2C0E9C(handle));
    return table_base + (index << 7);
}

extern "C" void* h11_shop_getcatalogentry_mutation(void* ctx, u32 index) {
    return reinterpret_cast<void*>(0xDEADBEEF);
}
