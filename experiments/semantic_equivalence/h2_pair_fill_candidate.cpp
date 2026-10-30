using u32 = unsigned int;

extern "C" void candidate_0027edf8(u32* destination, u32 value) {
    u32 repeated = value & 0xFFu;
    repeated |= repeated << 8;
    repeated |= repeated << 16;
    destination[0] = repeated;
    destination[1] = repeated;
}

extern "C" void candidate_0027edf8_wrong_one_word(u32* destination, u32 value) {
    u32 repeated = value & 0xFFu;
    repeated |= repeated << 8;
    repeated |= repeated << 16;
    destination[0] = repeated;
}
