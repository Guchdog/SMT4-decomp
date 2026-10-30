// Experimental in-place implementation of the original APT utility-4 entry.
// The linker resolves apt_wrapper to the original function at 0x002B5A1C.
using Word = unsigned int;

extern "C" Word apt_wrapper(Word, Word, Word, Word, Word, Word);

extern "C" __attribute__((minsize)) Word candidate_002c0efc() {
    return apt_wrapper(4, 0, 0, 0, 0, 0);
}

extern "C" __attribute__((minsize)) Word wrong_command_002c0efc() {
    return apt_wrapper(5, 0, 0, 0, 0, 0);
}
