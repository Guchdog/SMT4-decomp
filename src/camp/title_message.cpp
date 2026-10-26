#include "title_message.h"
#include "camp/unite.h"

namespace smt4::camp {
namespace {

constexpr u32 kTextOffset = 0x4D0;
constexpr u32 kTextBytes = 0x80;
constexpr u32 kLineBytes = 0x40;
constexpr u32 kMaxInputBytes = 0x80;

void StoreU32(u8* destination, u32 value) {
    destination[0] = static_cast<u8>(value);
    destination[1] = static_cast<u8>(value >> 8);
    destination[2] = static_cast<u8>(value >> 16);
    destination[3] = static_cast<u8>(value >> 24);
}

void ForwardCopy(u8* destination, const u8* source, u32 count) {
    for (u32 i = 0; i < count; ++i) {
        destination[i] = source[i];
    }
}

// Validate before writing so an unsupported string cannot partially update
// the live ButtonHelp work object. The input must expose 128 readable bytes.
bool IsSupportedMessage(const u8* message, u32& length) {
    u32 line_length = 0;
    u32 line_count = 1;
    for (u32 i = 0; i < kMaxInputBytes; ++i) {
        const u8 byte = message[i];
        if (byte == 0) {
            length = i;
            return true;
        }
        if (byte == '\n') {
            if (line_count == 2) {
                return false;
            }
            ++line_count;
            line_length = 0;
            continue;
        }
        if (++line_length > kLineBytes) {
            return false;
        }
    }
    return false;
}

} // namespace

extern "C" u32 H1_SetTitleHelpMessage(const char* message, u32 rgba) {
    ButtonHelpWork* const work = g_ButtonHelpManager.work;
    if (work == nullptr) {
        return 0;
    }

    u8* const bytes = work->raw;
    if (message != nullptr) {
        u32 message_length = 0;
        if (!IsSupportedMessage(reinterpret_cast<const u8*>(message), message_length)) {
            return 0;
        }

        for (u32 offset = 0; offset < kTextBytes; offset += 4) {
            StoreU32(bytes + kTextOffset + offset, 0);
        }

        u32 line = 0;
        u32 line_start = 0;
        for (u32 i = 0; i <= message_length; ++i) {
            const bool at_end = (i == message_length);
            const u8 byte = at_end ? 0 : static_cast<const u8*>(
                static_cast<const void*>(message))[i];
            if (at_end || byte == 0 || byte == '\n') {
                ForwardCopy(bytes + kTextOffset + line * kLineBytes,
                            reinterpret_cast<const u8*>(message) + line_start,
                            i - line_start);
                if (at_end || byte == 0) {
                    break;
                }
                ++line;
                line_start = i + 1;
            }
        }
    }

    StoreU32(bytes + 0x4CC, rgba);
    StoreU32(bytes + 0x550, 0);
    bytes[0x554] = 0xFF;
    if (message == nullptr) {
        bytes[0x4CB] = 0;
        return 0xFF;
    }
    bytes[0x55C] = 0;
    bytes[0x4CB] = 1;
    return 1;
}

} // namespace smt4::camp
