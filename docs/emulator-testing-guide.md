# Guide: Testing Semantic Reconstructions with the Azahar 3DS Emulator

This document describes how the project tests decompiled C++ code against the original game binary using the **Azahar** (Citra-based Nintendo 3DS) emulator via the GDB Remote Serial Protocol (RSP).

---

## 1. Environment & Setup

- **Emulator:**
  - Stock reference: `E:\emulador3ds\azahar.exe`
  - **Recommended Private Loopback-Bound Build:** `build/agent-work/H2-semantic/h2-private-azahar-source/build-clang64/bin/Release/azahar.exe`
    - Binds the GDB stub socket strictly to `127.0.0.1` (`htonl(INADDR_LOOPBACK)`) instead of `0.0.0.0` (`INADDR_ANY`), satisfying loopback-only listener checks (`tools/h2_azahar_rsp_probe.py`).
    - Supports `qfProcessInfo` / `qsProcessInfo` in `gdbstub.cpp` for automatic discovery of the `sdds4` process ID.
    - Filters `H2Observer` callbacks by `program_id == 0x00040000000E5C00ULL` and never halts guest execution on diagnostic observer errors.
- **Game ROM:** Decrypted Nintendo 3DS CCI format:
  `E:\emulador3ds\00040000000E5C00 Shin Megami Tensei IV (CTR-P-AMXE) (v0.1.0) (U).piratelegit-decrypted.cci`
- **GDB Stub Port:** `127.0.0.1:<port>` (pass `-g <port>` on the CLI for isolated ephemeral ports, or `24689` default).
  Azahar's built-in GDB stub allows programmatic control of CPU execution, breakpoints (`Z0`), register inspection (`p`/`P`), and memory read/write (`m`/`M`) at full Dynarmic JIT speed.
- **Isolated Portable User Directory:**
  Stage `app/azahar.exe` with an adjacent `app/user/` directory seeded with `sysdata/mac.txt` and `nand/data/.../config` (and optional `load/mods/00040000000E5C00/exefs/code.ips` for patched runs) so the user's `%APPDATA%\Azahar` profile is never touched.

---

## 1.5 Mandatory Offline-First Gate (Before Launching Azahar)

Never use the emulator for blind trial-and-error debugging. Before launching Azahar for any milestone slice:
1. **Static ARM/Thumb Interworking Check:** Verify that every branch target, callback pointer, and literal pool entry targeting a Thumb function sets bit 0 (`addr | 1`), and every ARM target clears bit 0 (`addr & ~1`).
2. **Offline Differential & Caller-Composition Harness:** Run `tools/semantic_experiment.py` and milestone caller-composition checks (e.g., `tools/h2_caller_validation.py`) in Unicorn/ARM emulation to prove register/memory/return equivalence across boundary and negative-control inputs in < 1 second.

---

## 2. Testing Architecture: Automated Differential Runtime Harness

Rather than requiring manual gamepad input, tests are 100% automated via Python using GDB RSP over a TCP socket (`tools/h1_track_capture.py` and `scratch/run_azahar_h1_slice_runtime.py`).

```
+-------------------------------------------------------------------------+
|                         Python Test Runner                              |
|                                                                         |
|  1. Subprocess launch Azahar with decrypted .cci                        |
|  2. Connect socket to 127.0.0.1:24689 (GDB RSP)                         |
|  3. Run unpatched sequence -> record state snapshots (registers & RAM)  |
|  4. Live-inject compiled C++ slice into Code Cave (0x003FE720)          |
|  5. Patch call site to branch to Code Cave                              |
|  6. Run identical patched sequence -> record state snapshots            |
|  7. Compare original vs. patched snapshots: fail if any drift           |
|  8. Assert SDMC save files and g_ConfigBytes are 100% unmodified        |
+-------------------------------------------------------------------------+
                                    |  TCP (port 24689)
                                    v
+-------------------------------------------------------------------------+
|                         Azahar (Citra Core)                             |
|                                                                         |
|   ARMv6K Core 0 <---> Memory (0x00100000..0x0FFFFFFF)                   |
|                        - .text / Code: 0x00100000                       |
|                        - TitleMainWork: *0x0044E300                     |
|                        - ConfigBytes: 0x0044E0F8                        |
|                        - Unused Code Cave: 0x003FE720                   |
+-------------------------------------------------------------------------+
```

---

## 3. Step-by-Step Test Execution Flow

### Step 1: Launch and Attach
1. Spawn Azahar as a background process:
   ```python
   proc = subprocess.Popen(["E:/emulador3ds/azahar.exe", str(CCI_PATH)])
   ```
2. Wait for TCP port `24689` to become open, then establish a socket connection.
3. Handshake with GDB RSP:
   ```python
   rsp.command("qSupported:multiprocess+;swbreak+;hwbreak+;QStartNoAckMode+")
   rsp.command("QStartNoAckMode")
   rsp.command("!")
   rsp.command("vAttach;b")
   ```

### Step 2: Step to Target State using Breakpoints
Breakpoints are placed using standard GDB RSP packets:
- Set software breakpoint: `Z0,<addr_hex>,4`
- Remove software breakpoint: `z0,<addr_hex>,4`
- Resume execution: `c` (or continue with timeout)

Example helper:
```python
def step_to_pc(rsp, target_pc, timeout=10.0):
    rsp.command(f"Z0,{target_pc:x},4")
    try:
        reply = rsp.continue_for(timeout)
        return {"stop_reply": reply, "pc": hex(rsp.reg(15) or 0)}
    finally:
        rsp.command(f"z0,{target_pc:x},4")
```

### Step 3: Non-Destructive Controlled Input Injection
To test navigation (e.g. D-pad Up/Down, A button, B button) deterministically without external UI inputs or timing races, the test hooks the input query helper in memory for **one single frame**:
- In H1, `UiInput_Trigger` (`0x002B902C`) queries logical button IDs (`5` = Up, `6` = Down).
- The test writes a small 16-byte ARM stub to `0x002B902C`:
  ```arm
  cmp r0, #trig_id   ; check requested trigger ID
  moveq r0, #1       ; return 1 if matching
  movne r0, #0       ; return 0 otherwise
  bx lr
  ```
- After single-stepping past the navigation slice (`0x001E9DE0`), the original 16 bytes of `0x002B902C` are immediately restored.
- In the same way, `UiInput_Trigger2(0)` at `0x002BFFBC` is temporarily hooked to simulate confirmation (A button) or cancel (B button).

### Step 4: Live Code Injection (Code Caves)
Instead of requiring an emulator restart or modifying disk files:
1. Production translation units (`src/ui/ui_runtime2.cpp`, `src/ui/tbb_loader.cpp`) are compiled with `clang++` targeting 3DS ARMv6K (`-target armv6k-none-eabi -mcpu=mpcore -mfloat-abi=hard -mfpu=vfp`).
2. The compiled function symbol (e.g. `H1_TitleMain_UpdateNavigationSlice`, 256 bytes) is extracted from the `.o` ELF object.
3. The runner writes the compiled bytes directly into an unused code cave in RAM (e.g. `0x003FE720`):
   ```python
   rsp_write_mem(rsp, CAVE_ADDR, compiled_bytes)
   ```
4. The call site (or slice continuation shim) in `ui_func_001e989c` is patched to jump to `CAVE_ADDR` using an encoded ARM `BL` instruction:
   ```python
   def encode_bl(source_pc, target_pc):
       offset = (target_pc - (source_pc + 8)) >> 2
       return struct.pack("<I", 0xEB000000 | (offset & 0x00FFFFFF))
   ```
5. A breakpoint on `CAVE_ADDR` verifies that the live emulator hits the newly injected C++ function.

### Step 5: State Snapshotting and Verification
At each milestone step, a full state dictionary is captured:
- Program Counter (`PC`), Stack Pointer (`SP`), registers `r0..r12`, `d8..d15`, `s16..s19`.
- Dereference of work structures: `work_ptr = rsp.u32(0x0044E300)`.
- State attributes: `selection_08`, `cached_0c`, `timer_64`, `blend_68`, `fade_6c`, `flag_94`, `fade_98`, `state_9c`.
- Text string memory at string pointers (e.g., verifying that `"Configure audio settings."` is loaded at `0x001EA15C`).

### Step 6: Differential Assertion & Save Guard
The test script runs the exact same scenario twice:
1. **Unpatched (original `code.bin`):** Records baseline trace array `orig_events`.
2. **Patched (compiled C++):** Records trace array `patched_events`.
3. Every step is asserted:
   ```python
   matched = all(orig[k] == patch[k] for k in ("selection_08", "cached_0c", "state_9c", "help_text", ...))
   ```
4. **Safety Check:** A SHA-256 snapshot of `%APPDATA%\Azahar\sdmc\...` is taken before and after the run. If any save file is written or changed, the test fails closed.

---

## 4. How to Run the Emulator Test

### Automated CLI Execution
Run the runner directly from PowerShell or Bash:
```powershell
python "scratch/run_azahar_h1_slice_runtime.py"
```

### Expected Output
```
Launching Azahar for original-vs-patched H1 runtime comparison...
Running unpatched original State-5 sequence...
[original] At 0x001EA15C: pc=0x1ea15c, r0=0x86c9d1c, r1=0x323232ff
[original] move_down_1_to_2: selection=2, cached=2
[original] move_down_2_to_3: selection=3, cached=3
[original] wrap_down_3_to_0: selection=0, cached=0
[original] wrap_up_0_to_3: selection=3, cached=3
[original] move_up_3_to_2: selection=2, cached=2
[original] Reached titleConfig_func_002f4ca0 (0x002F4CA0)
[original] Reached TitleConfig_Calc (0x001EA928), g_TitleConfigWork=0x86e4700
[original] Reached Title_ResetForBoot (0x001EA3D8)
[original] Returned to State 5 ready: selection=2, state_9c=5
Installing compiled production H1 slice in live Azahar process...
Confirmed live execution at CAVE_SLICE_ADDR=0x3fe720, r0=0xffffea0
Running patched production State-5 sequence...
[patched] At 0x001EA15C: pc=0x1ea15c, r0=0x86c9d1c, r1=0x323232ff
[patched] move_down_1_to_2: selection=2, cached=2
[patched] move_down_2_to_3: selection=3, cached=3
[patched] wrap_down_3_to_0: selection=0, cached=0
[patched] wrap_up_0_to_3: selection=3, cached=3
[patched] move_up_3_to_2: selection=2, cached=2
[patched] Reached titleConfig_func_002f4ca0 (0x002F4CA0)
[patched] Reached TitleConfig_Calc (0x001EA928), g_TitleConfigWork=0x86e4700
[patched] Reached Title_ResetForBoot (0x001EA3D8)
[patched] Returned to State 5 ready: selection=2, state_9c=5
Runtime verification PASS: .../runtime-report.json
```

---

## 5. Applying This Pattern to Future Milestones (e.g. H2 Audio Settings)

To test a new milestone such as **H2 (Title Audio Settings)**:
1. **Identify Entry & Exit Points:**
   - Entry: `titleConfig_func_002f4ca0` (`0x002F4CA0`) and `TitleConfig_Calc` (`0x001EA928`).
   - Work buffer: `g_TitleConfigWork` (`*0x0044E2D0`).
   - Config storage: `g_ConfigBytes` (`0x0044E0F8`).
2. **Define Test Scenarios:**
   - Navigating audio sliders (BGM volume, SE volume, Voice volume).
   - Changing a value $\rightarrow$ confirming whether `g_ConfigBytes` updates identically.
   - Cancel without saving $\rightarrow$ confirming `g_ConfigBytes` remains unchanged.
3. **Use Temporary Triggers:**
   - Hook D-pad Left (`0x002B902C` ID `0x07`) and Right (`ID 0x08`) to adjust sliders.
   - Hook A button (`UiInput_Trigger2(0)`) to commit or B button (`UiInput_Trigger2(1)`) to cancel.
4. **Compare Original vs Patched:**
   - Compile reconstructed `TitleConfig` functions into a code cave, branch from the original call sites, and compare state structures and `g_ConfigBytes` before/after.
