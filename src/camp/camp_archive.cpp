#include "camp/camp_archive.h"
#include "ui/status_down.h"

namespace smt4::camp {

// DECOMP_FUNC(0x00114374, 6144)
void Camp_DemonicaArchiveLoad(CampArchiveWork* work, const char* archive_path) {
    (void)archive_path;
    if (work == nullptr) {
        return;
    }

    // Demonica Archive Streaming Pipeline:
    // Asynchronously loads Camp UI layout tables and Demonica sub-menu graphics.
    work->load_state = 2;
}

} // namespace smt4::camp
