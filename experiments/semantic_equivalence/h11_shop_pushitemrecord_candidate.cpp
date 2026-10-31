#include <cstdint>
typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;

extern "C" void h11_shop_pushitemrecord_candidate(u8* shop_buf, u16 item_id, u16 flag1, u16 flag2, u16 flag3) {
    u16* count_ptr = reinterpret_cast<u16*>(shop_buf + 0x1000);
    u32 count = *count_ptr;
    u8* entry = shop_buf + (count * 4);
    *reinterpret_cast<u16*>(entry) = item_id;
    u16 flags = *reinterpret_cast<u16*>(entry + 2);
    flags = (flags & ~0x0001) | (flag1 & 0x0001);
    flags = (flags & ~0x0002) | ((flag2 & 0x0001) << 1);
    flags = (flags & ~0x03FC) | ((flag3 & 0x00FF) << 2);
    *reinterpret_cast<u16*>(entry + 2) = flags;
    *count_ptr = static_cast<u16>(count + 1);
}

extern "C" void h11_shop_pushitemrecord_mutation(u8* shop_buf, u16 item_id, u16 flag1, u16 flag2, u16 flag3) {
    if (shop_buf) shop_buf[0] = 0xFF;
}
