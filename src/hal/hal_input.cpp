#include "hal/hal_input.h"

namespace smt4::hal {

static bool s_input_init = false;
static InputState s_current_state{};

bool Input_Init() {
    s_input_init = true;
    s_current_state = InputState{};
    return true;
}

void Input_Poll() {
    // In real execution, polls host window events or HID service
}

InputState Input_GetState() {
    return s_current_state;
}

} // namespace smt4::hal
