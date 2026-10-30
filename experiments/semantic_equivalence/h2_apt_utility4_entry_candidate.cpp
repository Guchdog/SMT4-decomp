// Experimental isolated reconstruction. The real wrapper remains a dependency.
using Word = unsigned int;
using Wrapper = Word (*)(Word, Word, Word, Word, Word, Word);
static Wrapper const original_wrapper = reinterpret_cast<Wrapper>(0x002B5A1C);
extern "C" Word candidate_002c0efc() {
    return original_wrapper(4, 0, 0, 0, 0, 0);
}
extern "C" Word wrong_command() {
    return original_wrapper(5, 0, 0, 0, 0, 0);
}
extern "C" Word wrong_argument() {
    return original_wrapper(4, 0, 0, 0, 1, 0);
}
extern "C" Word discarded_return() {
    original_wrapper(4, 0, 0, 0, 0, 0);
    return 0;
}
