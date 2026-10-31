#pragma once
#include "hal_types.h"

namespace smt4::hal {

enum ButtonMask : u32 {
    BtnA      = (1 << 0),
    BtnB      = (1 << 1),
    BtnSelect = (1 << 2),
    BtnStart  = (1 << 3),
    BtnRight  = (1 << 4),
    BtnLeft   = (1 << 5),
    BtnUp     = (1 << 6),
    BtnDown   = (1 << 7),
    BtnR      = (1 << 8),
    BtnL      = (1 << 9),
    BtnX      = (1 << 10),
    BtnY      = (1 << 11),
};

struct TouchData {
    bool touching;
    u16  x;
    u16  y;
};

struct AnalogData {
    f32 x; // -1.0 .. +1.0
    f32 y; // -1.0 .. +1.0
};

struct InputState {
    u32        buttons_held;
    u32        buttons_pressed;
    u32        buttons_released;
    TouchData  touch;
    AnalogData circle_pad;
};

bool Input_Init();
void Input_Poll();
InputState Input_GetState();

void Input_SetButton(ButtonMask button, bool down);
void Input_SetTouch(bool down, u16 x, u16 y);
void Input_SetCirclePad(f32 x, f32 y);
void Input_InjectState(const InputState& state);

} // namespace smt4::hal
