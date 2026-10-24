// Semantic-only candidates. Production source and the matching ledger remain unchanged.
#include <stdint.h>

using u32 = uint32_t;

// Caller evidence: AOC texture/archive initializers populate a four-word
// descriptor consumed through their returned handle (source, zero, buffer,
// size). The script-VM caller at 0x0038DEBC constructs the same four-word
// shape on its stack, then passes it to 0x00354C30. Its domain-specific type
// name is not recovered; this neutral layout records only observed offsets.
struct FourWordDescriptor {
    void* source;       // +0x00
    u32 reserved_04;    // +0x04
    void* buffer;       // +0x08
    u32 size;           // +0x0C
};
static_assert(sizeof(void*) == 4);
static_assert(sizeof(FourWordDescriptor) == 0x10);
static_assert(__builtin_offsetof(FourWordDescriptor, reserved_04) == 0x04);
static_assert(__builtin_offsetof(FourWordDescriptor, buffer) == 0x08);
static_assert(__builtin_offsetof(FourWordDescriptor, size) == 0x0C);

extern "C" FourWordDescriptor* candidate_00352950(
    FourWordDescriptor* object, void* source, void* buffer, u32 size) {
    object->source = source;
    object->reserved_04 = 0;
    object->buffer = buffer;
    object->size = size;
    return object;
}

extern "C" FourWordDescriptor* candidate_003530f8(
    FourWordDescriptor* object, void* source, void* buffer, u32 size) {
    object->source = source;
    object->reserved_04 = 0;
    object->buffer = buffer;
    object->size = size;
    return object;
}

extern "C" FourWordDescriptor* candidate_00354d28(
    FourWordDescriptor* object, void* source, void* buffer, u32 size) {
    object->source = source;
    object->reserved_04 = 0;
    object->buffer = buffer;
    object->size = size;
    return object;
}

// Targeted negative control: the reserved word must be zero.
extern "C" FourWordDescriptor* wrong_initializer_nonzero_reserved(
    FourWordDescriptor* object, void* source, void* buffer, u32 size) {
    object->source = source;
    object->reserved_04 = 1;
    object->buffer = buffer;
    object->size = size;
    return object;
}
