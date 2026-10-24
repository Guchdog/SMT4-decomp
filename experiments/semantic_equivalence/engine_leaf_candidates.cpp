#include <stdint.h>

using u8 = uint8_t;
using u32 = uint32_t;

// Isolated semantic candidates for the 19 ARM leaf routines. These are not
// production replacements. Copy implementations snapshot all source words
// before performing any stores, matching the original vector-load/store
// overlap behavior for aligned ordinary RAM.
#define DEFINE_PLAIN_COPY(name)                                      \
    extern "C" __attribute__((noinline, used)) void name(            \
        void* destination, const void* source) {                      \
        const u32* src = static_cast<const u32*>(source);             \
        u32* dst = static_cast<u32*>(destination);                    \
        const u32 a = src[0];                                        \
        const u32 b = src[1];                                        \
        const u32 c = src[2];                                        \
        const u32 d = src[3];                                        \
        dst[0] = a;                                                   \
        dst[1] = b;                                                   \
        dst[2] = c;                                                   \
        dst[3] = d;                                                   \
    }

DEFINE_PLAIN_COPY(candidate_002c7084)
DEFINE_PLAIN_COPY(candidate_002dd080)
DEFINE_PLAIN_COPY(candidate_002f3450)
DEFINE_PLAIN_COPY(candidate_002f98e0)
DEFINE_PLAIN_COPY(candidate_002faf08)
DEFINE_PLAIN_COPY(candidate_00302764)
DEFINE_PLAIN_COPY(candidate_00315960)
DEFINE_PLAIN_COPY(candidate_0031ab34)

#define DEFINE_OFFSET_COPY(name)                                     \
    extern "C" __attribute__((noinline, used)) void name(            \
        void* destination, const void* source) {                      \
        const u32* src = static_cast<const u32*>(source);             \
        u32* dst = static_cast<u32*>(destination) + 4;                \
        const u32 a = src[0];                                        \
        const u32 b = src[1];                                        \
        const u32 c = src[2];                                        \
        const u32 d = src[3];                                        \
        dst[0] = a;                                                   \
        dst[1] = b;                                                   \
        dst[2] = c;                                                   \
        dst[3] = d;                                                   \
    }

DEFINE_OFFSET_COPY(candidate_002c6eb0)
DEFINE_OFFSET_COPY(candidate_002df400)
DEFINE_OFFSET_COPY(candidate_002e8114)
DEFINE_OFFSET_COPY(candidate_002e8284)
DEFINE_OFFSET_COPY(candidate_002f3280)
DEFINE_OFFSET_COPY(candidate_00304154)
DEFINE_OFFSET_COPY(candidate_0030f234)

#define DEFINE_WORD_GETTER(name)                                      \
    extern "C" __attribute__((noinline, used)) u32 name(             \
        const u8* base) {                                             \
        return *reinterpret_cast<const u32*>(base + 4);              \
    }

DEFINE_WORD_GETTER(candidate_003f5a68)
DEFINE_WORD_GETTER(candidate_003f5e34)
DEFINE_WORD_GETTER(candidate_003f635c)
DEFINE_WORD_GETTER(candidate_003f6800)

// Deliberately wrong forward-copy controls. Volatile forces each read/write
// pair to remain ordered, so a rightward overlap exposes the missing snapshot.
extern "C" __attribute__((noinline, used)) void negative_plain_forward_copy(
    void* destination, const void* source) {
    volatile u32* dst = static_cast<volatile u32*>(destination);
    const volatile u32* src = static_cast<const volatile u32*>(source);
    dst[0] = src[0];
    dst[1] = src[1];
    dst[2] = src[2];
    dst[3] = src[3];
}

extern "C" __attribute__((noinline, used)) void negative_offset_forward_copy(
    void* destination, const void* source) {
    volatile u32* dst = static_cast<volatile u32*>(destination) + 4;
    const volatile u32* src = static_cast<const volatile u32*>(source);
    dst[0] = src[0];
    dst[1] = src[1];
    dst[2] = src[2];
    dst[3] = src[3];
}

extern "C" __attribute__((noinline, used)) u32 negative_getter_offset(
    const u8* base) {
    return *reinterpret_cast<const u32*>(base + 8);
}
