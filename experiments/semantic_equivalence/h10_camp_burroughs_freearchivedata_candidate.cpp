#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

extern "C" {
    void AsdMem_Free_0035aea8(void** ptr);
}

extern "C" void h10_camp_burroughs_freearchivedata_candidate(void* obj) {
    u8* p = static_cast<u8*>(obj);
    void** slot = reinterpret_cast<void**>(p + 0x18);
    if (*slot) {
        AsdMem_Free_0035aea8(slot);
        *slot = nullptr;
    }
}

extern "C" void h10_camp_burroughs_freearchivedata_mutation(void* obj) {
    // Deliberate bug
}
