# H7 Script VM and Event Runtime Architecture Reconnaissance Record

- **Milestone:** H7 (Script VM and Event Execution / Máquina virtual de scripts y eventos)
- **Status:** Complete & Reviewed
- **Target Subsystems:** FlowScript Event Runner, Dialogue Window Subsystem (ComWin, InfoWin, GuestWin), Event Visual Effects

## 1. Subsystem Boundaries and Mappings

SMT4 script VM and event runtime execution is organized into three cooperating layers:

1. **Dialogue and Message Window Subsystems (`0x0010A748`, `0x0010AEE4`, `0x0010AF84`, `0x0010B350`):**
   - `ComWin_Init` (`0x0010A748`): Common dialogue window initialization. Allocates 0x30-byte work buffer (`0x002c4b84`), zeroes memory, registers calculation task (`0x002c5978`, priority 0x6) and draw task (`0x002c4c00`, priority 0x6) under calculation task parent handle `r4[0]`, allocates message state workspace (`0x0010a624`), and binds window assets.
   - `ComWin_Reset` (`0x0010AEE4`): Dialog window reset. Clears active sprite pointers across 8 entries, resets window coordinate caches, resets internal states, and zeroes work flags.
   - `InfoWin_Init` (`0x0010AF84`): Notification/info window workspace setup. Initializes info panel layout, registers calculation and draw tasks, and sets up animated UI sprites at offset `work + 0x24` via `UiAnimSprite_SetupEx` (`0x002BDB2C`) and `UiAnimSprite_SetMode` (`0x002BDAC0`).
   - `GuestWin_Init` (`0x0010B350`): Guest/NPC dialog window workspace setup. Registers calculation and draw tasks, initializes guest sprite group at `work + 0x10` and panel sprite at `work + 0x30`.

2. **FlowScript Event Runner and Script Processes (`0x001D374C`, `0x001D38FC`):**
   - `nameMain_Init` (`0x001D374C`): FlowScript naming prompt initialization. Sets up name entry dialog flow, allocates process structure, clears buffer via `0x00282E6C`, loads naming resources, and binds callback tasks.
   - `onesRoom_Init` (`0x001D38FC`): Barracks / personal room event script loader. Loads `"ones_room/onesRoom.bf"` (`0x001D3A40`) and `"ones_room/onesRoom.mbm"` (`0x001D3A58`), sets process state `proc[0x108] = 2`, and dispatches script initialization via `0x002971E4(proc, 0)`.

3. **Event Command Visual Effects (`0x0025955C`, `0x0030A4FC`):**
   - `eventCommand_func_0025955c` (`0x0025955C`): Screen under-fade transition runner. Initializes fade task `"EventMessUnderFade_Proc"` (`0x0025972C`) and draw task `"EventMessUnderFade_Draw"` (`0x00259748`), calculating frame step interpolation: fade-in (`flag != 0`, `step = alpha / frames`) starting from 0.0, or fade-out (`flag == 0`, `step = -(alpha / frames)`) starting from parameter alpha.
   - `EventEffect_func_0030a4fc` (`0x0030A4FC`): Event visual effect screen blink / flash initializer. Configures duration, color RGB channels, alpha interpolation curve, and registers callback tasks via `0x002A63F8`.
