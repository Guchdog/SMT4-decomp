// Readable replacements for titleConfig's three persisted-byte lookups.
// The table boundaries are recovered from the pinned original at 0x004077EB,
// 0x004077F6, and 0x00407801. The valid caller domain is a zero-extended byte.

using u32 = unsigned int;

extern "C" u32 candidate_002cab70(u32 value) {
    if (value <= 0) return 0;
    if (value <= 10) return 1;
    if (value <= 20) return 2;
    if (value <= 25) return 3;
    if (value <= 30) return 4;
    if (value <= 35) return 5;
    if (value <= 40) return 6;
    if (value <= 45) return 7;
    if (value <= 50) return 8;
    if (value <= 70) return 9;
    if (value <= 90) return 10;
    return 0;
}

extern "C" u32 candidate_0021f39c(u32 value) {
    if (value <= 0) return 0;
    if (value <= 10) return 1;
    if (value <= 20) return 2;
    if (value <= 30) return 3;
    if (value <= 40) return 4;
    if (value <= 50) return 5;
    if (value <= 60) return 6;
    if (value <= 70) return 7;
    if (value <= 80) return 8;
    if (value <= 100) return 9;
    if (value <= 120) return 10;
    return 0;
}

extern "C" u32 candidate_002e0af4(u32 value) {
    if (value <= 0) return 0;
    if (value <= 10) return 1;
    if (value <= 20) return 2;
    if (value <= 30) return 3;
    if (value <= 40) return 4;
    if (value <= 50) return 5;
    if (value <= 60) return 6;
    if (value <= 70) return 7;
    if (value <= 80) return 8;
    if (value <= 100) return 9;
    if (value <= 120) return 10;
    return 0;
}

// Deliberately incorrect fixture: accepts 11 in bin 1 instead of bin 2.
extern "C" u32 candidate_002cab70_wrong_map(u32 value) {
    if (value <= 0) return 0;
    if (value <= 11) return 1;
    if (value <= 20) return 2;
    if (value <= 25) return 3;
    if (value <= 30) return 4;
    if (value <= 35) return 5;
    if (value <= 40) return 6;
    if (value <= 45) return 7;
    if (value <= 50) return 8;
    if (value <= 70) return 9;
    if (value <= 90) return 10;
    return 0;
}
