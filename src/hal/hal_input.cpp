#include "hal/hal_input.h"

#if defined(__arm__)

namespace smt4::hal {

static bool s_input_init = false;
static u32 s_raw_buttons = 0;
static u32 s_prev_buttons = 0;
static TouchData s_raw_touch{};
static AnalogData s_raw_circle_pad{};
static InputState s_current_state{};

bool Input_Init() {
    s_input_init = true;
    s_raw_buttons = 0;
    s_prev_buttons = 0;
    s_raw_touch = TouchData{};
    s_raw_circle_pad = AnalogData{};
    s_current_state = InputState{};
    return true;
}

void Input_Poll() {
    s_current_state.buttons_pressed = s_raw_buttons & ~s_prev_buttons;
    s_current_state.buttons_released = s_prev_buttons & ~s_raw_buttons;
    s_current_state.buttons_held = s_raw_buttons;
    s_prev_buttons = s_raw_buttons;
    s_current_state.touch = s_raw_touch;
    s_current_state.circle_pad = s_raw_circle_pad;
}

InputState Input_GetState() {
    return s_current_state;
}

void Input_SetButton(ButtonMask button, bool down) {
    if (down) {
        s_raw_buttons |= static_cast<u32>(button);
    } else {
        s_raw_buttons &= ~static_cast<u32>(button);
    }
}

void Input_SetTouch(bool down, u16 x, u16 y) {
    s_raw_touch.touching = down;
    s_raw_touch.x = x;
    s_raw_touch.y = y;
}

void Input_SetCirclePad(f32 x, f32 y) {
    if (x < -1.0f) x = -1.0f;
    if (x > 1.0f) x = 1.0f;
    if (y < -1.0f) y = -1.0f;
    if (y > 1.0f) y = 1.0f;
    s_raw_circle_pad.x = x;
    s_raw_circle_pad.y = y;
}

void Input_InjectState(const InputState& state) {
    s_raw_buttons = state.buttons_held;
    s_raw_touch = state.touch;
    s_raw_circle_pad = state.circle_pad;
}

} // namespace smt4::hal

#else // Native Host (Windows / Linux / macOS)

#include <algorithm>
#include <cstring>

namespace smt4::hal {

static bool s_input_init = false;
static u32 s_raw_buttons = 0;
static u32 s_prev_buttons = 0;
static TouchData s_raw_touch{};
static AnalogData s_raw_circle_pad{};
static InputState s_current_state{};

bool Input_Init() {
    s_input_init = true;
    s_raw_buttons = 0;
    s_prev_buttons = 0;
    s_raw_touch = TouchData{};
    s_raw_circle_pad = AnalogData{};
    s_current_state = InputState{};
    return true;
}

void Input_Poll() {
    if (!s_input_init) return;

    s_current_state.buttons_pressed = s_raw_buttons & ~s_prev_buttons;
    s_current_state.buttons_released = s_prev_buttons & ~s_raw_buttons;
    s_current_state.buttons_held = s_raw_buttons;
    s_prev_buttons = s_raw_buttons;

    s_current_state.touch = s_raw_touch;
    s_current_state.circle_pad = s_raw_circle_pad;
}

InputState Input_GetState() {
    return s_current_state;
}

void Input_SetButton(ButtonMask button, bool down) {
    if (down) {
        s_raw_buttons |= static_cast<u32>(button);
    } else {
        s_raw_buttons &= ~static_cast<u32>(button);
    }
}

void Input_SetTouch(bool down, u16 x, u16 y) {
    s_raw_touch.touching = down;
    s_raw_touch.x = x;
    s_raw_touch.y = y;
}

void Input_SetCirclePad(f32 x, f32 y) {
    if (x < -1.0f) x = -1.0f;
    if (x > 1.0f) x = 1.0f;
    if (y < -1.0f) y = -1.0f;
    if (y > 1.0f) y = 1.0f;
    s_raw_circle_pad.x = x;
    s_raw_circle_pad.y = y;
}

void Input_InjectState(const InputState& state) {
    s_raw_buttons = state.buttons_held;
    s_raw_touch = state.touch;
    s_raw_circle_pad = state.circle_pad;
}

} // namespace smt4::hal

#endif
