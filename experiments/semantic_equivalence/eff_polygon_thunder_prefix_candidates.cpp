// Isolated semantic candidates for the pre-geometry point-count prefix only.
// These do not replace or model allocation, geometry creation, or rendering.
extern "C" __attribute__((noinline)) void candidate_thunder_min3(void* object) {
    auto* bytes = static_cast<unsigned char*>(object);
    auto* points = reinterpret_cast<unsigned int*>(bytes + 0x3c);
    unsigned int count = *points;
    if (count <= 3u) {
        count = 3u;
    }
    *points = count;
}

extern "C" __attribute__((noinline)) void candidate_thunder_min3_odd(void* object) {
    auto* bytes = static_cast<unsigned char*>(object);
    auto* points = reinterpret_cast<unsigned int*>(bytes + 0x3c);
    unsigned int count = *points;
    if (count <= 3u) {
        count = 3u;
    }
    *points = count;
    if ((count & 1u) == 0u) {
        *points = count + 1u;
    }
}

// Deliberate controls used to prove that the focused comparator detects a
// wrong clamp and a missing odd-count adjustment.
extern "C" __attribute__((noinline)) void candidate_wrong_min2(void* object) {
    auto* bytes = static_cast<unsigned char*>(object);
    auto* points = reinterpret_cast<unsigned int*>(bytes + 0x3c);
    unsigned int count = *points;
    if (count <= 2u) {
        count = 2u;
    }
    *points = count;
}

extern "C" __attribute__((noinline)) void candidate_wrong_no_odd(void* object) {
    auto* bytes = static_cast<unsigned char*>(object);
    auto* points = reinterpret_cast<unsigned int*>(bytes + 0x3c);
    unsigned int count = *points;
    if (count <= 3u) {
        count = 3u;
    }
    *points = count;
}
