#pragma once

#include "types.h"

namespace smt4::camp {

// H1-only editable message path. The shared ARM message entry remains separate.
extern "C" u32 H1_SetTitleHelpMessage(const char* message, u32 rgba);

} // namespace smt4::camp
