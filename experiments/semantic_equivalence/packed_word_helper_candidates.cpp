// Isolated semantic experiment for three byte-identical ARM leaf helpers.
// The C++ signature is an AAPCS test model (four word registers plus a fifth
// word at [sp]); callers have not been identified, so it is not asserted as
// the game's source-level ABI.
using u32 = unsigned int;
using u64 = unsigned long long;
static_assert(sizeof(u32) == 4, "the observed helper uses 32-bit words");
static_assert(sizeof(u64) == 8, "the harness models the returned register pair");

#define PACKED_HELPER(NAME) \
extern "C" __attribute__((noinline)) u64 NAME( \
    u32 ignored_r0, u32 low_r1, u32 source_r2, u32 source_r3, u32 stack_word) { \
  (void)ignored_r0; \
  const u32 high = (stack_word << 24) | (source_r3 << 13) | \
                   ((source_r2 << 30) >> 8) | 0x00200000u; \
  return (static_cast<u64>(high) << 32) | low_r1; \
}

PACKED_HELPER(candidate_003f8808)
PACKED_HELPER(candidate_003f88e4)
PACKED_HELPER(candidate_003f89cc)

// Deliberately wrong controls: each changes one observable part of the
// register-level result. All operands remain unsigned, so no C++ shift UB.
extern "C" __attribute__((noinline)) u64 wrong_stack_shift(
    u32 ignored_r0, u32 low_r1, u32 source_r2, u32 source_r3, u32 stack_word) {
  (void)ignored_r0;
  const u32 high = (stack_word << 23) | (source_r3 << 13) |
                   ((source_r2 << 30) >> 8) | 0x00200000u;
  return (static_cast<u64>(high) << 32) | low_r1;
}

extern "C" __attribute__((noinline)) u64 wrong_r2_lane(
    u32 ignored_r0, u32 low_r1, u32 source_r2, u32 source_r3, u32 stack_word) {
  (void)ignored_r0;
  const u32 high = (stack_word << 24) | (source_r3 << 13) |
                   ((source_r2 << 30) >> 7) | 0x00200000u;
  return (static_cast<u64>(high) << 32) | low_r1;
}

extern "C" __attribute__((noinline)) u64 wrong_r1_return(
    u32 ignored_r0, u32 low_r1, u32 source_r2, u32 source_r3, u32 stack_word) {
  (void)ignored_r0;
  const u32 high = (stack_word << 24) | (source_r3 << 13) |
                   ((source_r2 << 30) >> 8) | 0x00200000u;
  return (static_cast<u64>(high) << 32) | (low_r1 ^ 1u);
}

extern "C" __attribute__((noinline)) u64 wrong_constant(
    u32 ignored_r0, u32 low_r1, u32 source_r2, u32 source_r3, u32 stack_word) {
  (void)ignored_r0;
  const u32 high = (stack_word << 24) | (source_r3 << 13) |
                   ((source_r2 << 30) >> 8) | 0x00100000u;
  return (static_cast<u64>(high) << 32) | low_r1;
}
