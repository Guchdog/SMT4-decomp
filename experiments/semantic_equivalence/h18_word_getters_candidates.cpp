#include <cstdint>

#define H18_WORD_GETTER(address) \
    extern "C" std::uint32_t candidate_##address(const std::uint32_t* words) { \
        return words[1]; \
    }

H18_WORD_GETTER(003f5a68)
H18_WORD_GETTER(003f5e34)
H18_WORD_GETTER(003f635c)
H18_WORD_GETTER(003f6800)

// Deliberately incorrect controls used only by the focused runner.
extern "C" __attribute__((naked, used)) std::uint32_t negative_wrong_return(const std::uint32_t*) {
    asm volatile("mov r0, #0\n bx lr");
}
extern "C" __attribute__((naked, used)) std::uint32_t negative_changed_flags(const std::uint32_t*) {
    asm volatile("ldr r0, [r0, #4]\n cmp r0, #0\n bx lr");
}
extern "C" __attribute__((naked, used)) std::uint32_t negative_write_memory(const std::uint32_t*) {
    asm volatile("str r0, [r0]\n ldr r0, [r0, #4]\n bx lr");
}
extern "C" __attribute__((naked, used)) std::uint32_t control_caller_saved_clobber(const std::uint32_t*) {
    asm volatile("mov r1, #0\n ldr r0, [r0, #4]\n bx lr");
}
