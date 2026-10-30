using u32 = unsigned int;
using u64 = unsigned long long;
extern "C" u64 h4_integer_divide_candidate(u32 dividend, u32 divisor) {
    if (divisor == 0) return static_cast<u64>(dividend) << 32;
    const bool neg_a = (dividend >> 31) != 0;
    const bool neg_b = (divisor >> 31) != 0;
    const u32 a = neg_a ? 0u - dividend : dividend;
    const u32 b = neg_b ? 0u - divisor : divisor;
    u32 q = 0, rem = 0;
    for (int bit = 31; bit >= 0; --bit) {
        rem = (rem << 1) | ((a >> bit) & 1u);
        if (rem >= b) { rem -= b; q |= 1u << bit; }
    }
    if (neg_a != neg_b) q = 0u - q;
    if (neg_a) rem = 0u - rem;
    return (static_cast<u64>(rem) << 32) | q;
}
