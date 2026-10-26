#include <stdint.h>

// Reconstructed from the pinned H1 title/message helper at 0x0029F10C.
// The supported non-null domain requires a valid, readable input buffer of at
// least 128 bytes and each copied line to contain at most 64 bytes. The pinned
// body does not enforce either limit; callers outside this domain are not
// modeled as safe C++ object accesses. The manager and help-work pointers are
// valid writable pointers, as they are on the observed initialized path.
namespace {
static uint8_t* help_work() {
    constexpr uintptr_t manager_address = 0x0043DA28u;
    const auto* work_slot = reinterpret_cast<const volatile uint32_t*>(
        manager_address + 4u);
    return reinterpret_cast<uint8_t*>(static_cast<uintptr_t>(*work_slot));
}

static void store_u32(uint8_t* address, uint32_t value) {
    address[0] = static_cast<uint8_t>(value);
    address[1] = static_cast<uint8_t>(value >> 8);
    address[2] = static_cast<uint8_t>(value >> 16);
    address[3] = static_cast<uint8_t>(value >> 24);
}
} // namespace

extern "C" __attribute__((noinline)) void* h1_title_message_forward_copy_candidate(
    void* destination, const void* source, uint32_t length) {
    // Defined only for non-overlapping ranges. The pinned routine copies
    // forward and does not provide memmove semantics.
    auto* to = static_cast<uint8_t*>(destination);
    const auto* from = static_cast<const uint8_t*>(source);
    for (uint32_t i = 0; i < length; ++i)
        to[i] = from[i];
    return to + length;
}

extern "C" uint32_t h1_title_message_candidate(
    const uint8_t* message, uint32_t color) {
    uint8_t* const work = help_work();
    store_u32(work + 0x4CC, color);
    store_u32(work + 0x550, 0);
    work[0x554] = 0xFF;

    if (message == nullptr) {
        work[0x4CB] = 0;
        return 0xFFu;
    }

    // The original clears exactly 0x80 bytes as 32 word stores.
    for (uint32_t offset = 0; offset < 0x80; offset += 4)
        store_u32(work + 0x4D0 + offset, 0);

    uint32_t line = 0;
    uint32_t line_start = 0;
    for (uint32_t index = 0; index < 0x80; ++index) {
        const uint8_t byte = message[index];
        if (byte == 0 || byte == 0x0A) {
            auto* destination = work + 0x4D0 + line * 0x40;
            h1_title_message_forward_copy_candidate(
                destination, message + line_start, index - line_start);
            if (byte == 0)
                break;
            ++line;
            line_start = index + 1;
            if (line > 1)
                break;
        }
    }

    work[0x55C] = 0;
    work[0x4CB] = 1;
    return 1;
}
