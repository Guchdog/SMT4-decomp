// Differential-test adapters for the existing private TexConv implementation.
// This translation unit includes production source only to exercise its current
// C++ helper without editing or linking it into a production path.
#include "../../src/engine/tex_convert.cpp"

// The differential runner links this file freestanding. Keep the production
// helper's fixed-size memcpy operations executable without a libc dependency.
extern "C" __attribute__((used, noinline)) void* memcpy(void* destination,
                                                        const void* source,
                                                        __SIZE_TYPE__ size)
{
    auto* out = static_cast<volatile unsigned char*>(destination);
    const auto* in = static_cast<const volatile unsigned char*>(source);
    for (__SIZE_TYPE__ index = 0; index < size; ++index)
        out[index] = in[index];
    return destination;
}

namespace smt4::engine {

extern "C" __attribute__((used)) void candidate_001721e4(const u8* src, u8* dst,
                                                           u32 count)
{
    const u8* source = src;
    u8* destination = dst;
    TexConv_001721e4(source, destination, count, 0x400u);
}

extern "C" __attribute__((used)) void candidate_001787e4(const u8* src, u8* dst,
                                                           u32 count)
{
    const u8* source = src;
    u8* destination = dst;
    TexConv_001721e4(source, destination, count, 0x100u);
}

extern "C" __attribute__((used)) void candidate_0017ede4(const u8* src, u8* dst,
                                                           u32 count)
{
    const u8* source = src;
    u8* destination = dst;
    TexConv_001721e4(source, destination, count, 0x200u);
}

extern "C" __attribute__((used)) void negative_wrong_stride_100(const u8* src,
                                                                  u8* dst,
                                                                  u32 count)
{
    const u8* source = src;
    u8* destination = dst;
    TexConv_001721e4(source, destination, count, 0x400u);
}

extern "C" __attribute__((used)) void negative_row_copy_instead_of_average(
    const u8* src, u8* dst, u32 count)
{
    const u8* source = src;
    u8* destination = dst;
    for (u32 row = 0; row < count; ++row) {
        u32 value;
        __builtin_memcpy(&value, source, sizeof value);
        destination[0] = static_cast<u8>(value);
        destination[1] = static_cast<u8>(value >> 8);
        destination[2] = static_cast<u8>(value >> 16);
        destination[3] = static_cast<u8>(value >> 24);
        source += 0x100u;
        destination += 0x100u;
    }
}

} // namespace smt4::engine
