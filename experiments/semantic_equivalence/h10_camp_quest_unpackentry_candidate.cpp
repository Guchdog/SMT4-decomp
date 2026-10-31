#include <cstdint>
typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;

extern "C" {
    u8* Quest_GetStaticDef_002b087c(u32 id);
    void AsdMem_Zero_002c4b30(void* ptr, u32 size);
    void Quest_InitEntrySub_002bcf58(void* ptr);
    u8* Quest_GetDynamicRecord_002b9364(u32 id);
    void Quest_FormatTitle_0024be90(void* out, u16 flag);
}

extern "C" void h10_camp_quest_unpackentry_candidate(u32 quest_id, u8* out) {
    u8* def = Quest_GetStaticDef_002b087c(quest_id);
    AsdMem_Zero_002c4b30(out, 0x604);

    *reinterpret_cast<u16*>(out + 0x46) = static_cast<u16>(quest_id);
    out[0x48] = def[2];

    *reinterpret_cast<u16*>(out) = *reinterpret_cast<u16*>(def + 4);
    *reinterpret_cast<u16*>(out + 2) = *reinterpret_cast<u16*>(def + 8);
    *reinterpret_cast<u16*>(out + 4) = *reinterpret_cast<u16*>(def + 0xc);
    *reinterpret_cast<u16*>(out + 6) = *reinterpret_cast<u16*>(def + 0xe);
    *reinterpret_cast<u16*>(out + 8) = *reinterpret_cast<u16*>(def + 0x10);
    *reinterpret_cast<u16*>(out + 0xa) = *reinterpret_cast<u16*>(def + 0x12);
    *reinterpret_cast<u16*>(out + 0xc) = *reinterpret_cast<u16*>(def + 0x14);

    Quest_InitEntrySub_002bcf58(out + 0x1c);

    *reinterpret_cast<u32*>(out + 0xe) = *reinterpret_cast<u32*>(out);
    *reinterpret_cast<u32*>(out + 0x12) = *reinterpret_cast<u32*>(out + 4);
    *reinterpret_cast<u32*>(out + 0x16) = *reinterpret_cast<u32*>(out + 8);
    *reinterpret_cast<u16*>(out + 0x1a) = *reinterpret_cast<u16*>(out + 0xc);

    for (int i = 0; i < 8; ++i) {
        *reinterpret_cast<u16*>(out + 0x34 + i * 2) = *reinterpret_cast<u16*>(def + 0x48 + i * 2);
    }

    u8* rec = Quest_GetDynamicRecord_002b9364(quest_id);
    u16 flag = *reinterpret_cast<u16*>(rec + 0x38);
    Quest_FormatTitle_0024be90(out, flag);

    *reinterpret_cast<u16*>(out + 0x2a) = *reinterpret_cast<u16*>(out + 0xe);
    *reinterpret_cast<u16*>(out + 0x2c) = *reinterpret_cast<u16*>(out + 0x10);
}

extern "C" void h10_camp_quest_unpackentry_mutation(u32 quest_id, u8* out) {
    if (out) out[0] = 0xFF;
}
