using u32 = unsigned int;

// Both words are fetched before the first destination store. This preserves
// the original behavior when source and destination overlap by one word.
extern "C" u32* candidate_002adb40(u32* destination, const u32* source) {
    const u32 first = source[0];
    const u32 second = source[1];
    destination[0] = first;
    destination[1] = second;
    return destination;
}

// Deliberately wrong fixture: sequential copy corrupts source[1] when the
// destination begins one word above the source.
extern "C" u32* candidate_002adb40_wrong_forward(u32* destination,
                                                 const u32* source) {
    destination[0] = source[0];
    destination[1] = source[1];
    return destination;
}
