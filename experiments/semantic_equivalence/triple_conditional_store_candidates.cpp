#include <stdint.h>

using u8 = uint8_t;
using u32 = uint32_t;

// Isolated semantic reconstruction of 0x0034F978. The first argument is
// both the non-null guard and the first stored word. The destination is the
// object base plus four bytes; r1, r2, and r3 are written in that order.
extern "C" __attribute__((noinline, used)) u32 candidate_0034f978(
    volatile u8* object, u32 first, u32 second, u32 third) {
    u32 result = 0;
    if (first != 0) {
        volatile u32* fields = reinterpret_cast<volatile u32*>(object + 4);
        fields[0] = first;
        fields[1] = second;
        fields[2] = third;
        result = 1;
    }
    return result;
}

// Deliberately wrong controls; each differs along a separately tested axis.
extern "C" __attribute__((noinline, used)) u32 negative_wrong_guard(
    volatile u8* object, u32 first, u32 second, u32 third) {
    u32 result = 0;
    if (second != 0) {
        volatile u32* fields = reinterpret_cast<volatile u32*>(object + 4);
        fields[0] = first;
        fields[1] = second;
        fields[2] = third;
        result = 1;
    }
    return result;
}

extern "C" __attribute__((noinline, used)) u32 negative_wrong_offset(
    volatile u8* object, u32 first, u32 second, u32 third) {
    u32 result = 0;
    if (first != 0) {
        volatile u32* fields = reinterpret_cast<volatile u32*>(object);
        fields[0] = first;
        fields[1] = second;
        fields[2] = third;
        result = 1;
    }
    return result;
}

extern "C" __attribute__((noinline, used)) u32 negative_reversed_words(
    volatile u8* object, u32 first, u32 second, u32 third) {
    u32 result = 0;
    if (first != 0) {
        volatile u32* fields = reinterpret_cast<volatile u32*>(object + 4);
        fields[0] = third;
        fields[1] = second;
        fields[2] = first;
        result = 1;
    }
    return result;
}

extern "C" __attribute__((noinline, used)) u32 negative_unconditional_store(
    volatile u8* object, u32 first, u32 second, u32 third) {
    volatile u32* fields = reinterpret_cast<volatile u32*>(object + 4);
    fields[0] = first;
    fields[1] = second;
    fields[2] = third;
    return first != 0;
}

extern "C" __attribute__((noinline, used)) u32 negative_two_word_store(
    volatile u8* object, u32 first, u32 second, u32 third) {
    u32 result = 0;
    if (first != 0) {
        volatile u32* fields = reinterpret_cast<volatile u32*>(object + 4);
        fields[0] = first;
        fields[1] = second;
        result = 1;
    }
    return result;
}
