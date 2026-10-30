# H2 contract research: `TitleConfig_Calc` (`0x001EA928`)

Status: researched from the pinned original instructions and existing title caller evidence; no implementation or emulator work performed.

## Scope and identity

- Original function: `[0x001EA928, 0x001EB02C)` (`1796` bytes), ARM mode, `script_vm_func_001ea928`; original image SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` (`config/game_info.json`).
- Function body in the checkout is retained as inline ARM in `src/engine/leaf_batch46_b.cpp`; `python tools/split_asm.py --addr 0x001EA928` was used to inspect the original decode. The jump table at `0x001EA950` contains these five code addresses: `0x001EA964`, `0x001EAA60`, `0x001EAF98`, `0x001EAFEC`, `0x001EB004`.
- The registered callback is passed to `AsdTask_CreateCalc` by `titleConfig_func_002f4ca0` (`0x002F4CA0`); its work pointer is the global at `0x0044E2D0` (`TitleConfigWork`, allocation `0x158`). The callback receives no meaningful explicit argument in the observed registration, but it ignores incoming `r0` and resolves the work globally.
- It saves/restores `r4-r8`, `r9-r11` aliases, `ip`, and `lr`, and restores SP. It returns `r0=0` on the common paths (`0x001EAFE4..0x001EAFE8`), but state 4 returns `r0=0xFFFFFFFF` at `0x001EB004`. Whether the task scheduler consumes this return is not established here; preserve and test it until its caller contract is known.

## State dispatch and initialization

At `0x001EA940`, the function reads `work->field_08`; values `0..4` dispatch through the table above and values `>=5` go to the common return (`0x001EAFE4`). This is an upper-bound check, not a signed validity check. State meanings below are descriptive labels inferred from effects, not recovered enum names.

| State | Path and observed behavior |
|---|---|
| 0 | `0x001EA964`: checks `ui_func_002a63f8(0x2f, 0)`; false returns unchanged. Then waits for `ui_func_002bf9f0(work+0x5c)`; if ready, requires nonzero `work+0x14c` and `work+0x150`. It obtains three halfwords from `camp_func_002b88c4(0x2f, 0x1f/0x20/0x21)` into `+0x14/+0x16/+0x18`, increments `+0x1a` after each, creates/updates the title message using list-cursor functions (`0x29F260`, `0x29F248`), TBB table `0x3A`, payload and `camp_func_0029f10c`, then calls `0x25A0D0` and `scrScriptProcess_func_002972f8(work+0x14c, work+0x150)`. It writes state `1` and the returned script value at `+0x14c`; if readiness/resource checks fail, it returns without advancing. |
| 1 | `0x001EAA60`: main active input/update path, detailed below. |
| 2 | `0x001EAF98`: polls `script_vm_func_0019dfbc(work+0x154)` and proceeds only when it returns `2`; then polls `script_vm_func_00297674()`. Return `1` sets state back to `1`; return `0` calls `camp_func_002bdac0(work+0x5c,1,0)`, sets state `3`, writes byte `1` to `0x0044E0FC` (config base `+4`), and returns through the common path. Branches/values other than `0` or `1` fall through without these writes. The semantic labels of the poll and result are unresolved; do not call these “save” or “confirm” without observing their contracts. |
| 3 | `0x001EAFEC`: checks `ui_func_002bf9f0(work+0x5c)`; if ready, assigns `r0=4` then sets state `4`; otherwise returns `0`. |
| 4 | `0x001EB004`: returns `-1` in `r0`. |
| `>=5` | common return `0`; no state repair is performed. |

## State-1 input, option update, and memory effects

The current list-cursor selection is derived from `work+0xE8` with `0x29F260` and `0x29F248`; the computed selection is used to address a TBB row payload in table `0x3A`. In the display calculation (`0x001EAA24..0x001EAA34`, repeated at `0x001EADE8..0x001EADF8` and `0x001EAEDC..0x001EAEEC`), the instructions compute `r1 = (selection*16 - selection)`, then `r1 = r1 + 4*r1`, then add `2*r1` to the payload base, followed by payload offset `0x16`. For ordinary non-wrapping indices this is `payload_base + 0x16 + selection*0x96` bytes. Thus selections 0, 1, and 2 address offsets `0x16`, `0xAC`, and `0x142` from the payload base. The index comes from cursor helpers whose valid range has not been established; these examples do not imply that malformed or larger selections are safe. A `camp_func_0029F10C` call displays the selected row using color `0x323232FF`. These same cursor and payload calculations recur when refreshing the selection after callback activity.

The function reads signed halfwords at work offsets `+0x1C`, `+0x1E`, `+0x20`, and `+0x22` as input/event handles and passes them to `ui_func_0029D8FC`. It branches on returned event codes `1`, `2`, and `6`; when code `1` is returned it also calls `script_vm_func_0025A0B4()` and tests whether the result is at least `1`. A separate event query uses `camp_func_002C1830` with IDs `4`, `3`, `0`, and `1`. On a recognized row action, the switch on current row/index `r7` is:

- `r7 == 0`: writes byte `0x32` to config `+0`, calls `Config_MapByteToIndexA(0x32)`, stores result at `work+0x28`.
- `r7 == 1`: writes bytes `0x50` to config `+1` and `0x30` to config `+3`; calls `Config_MapByteToIndexB(config[1])`, stores result at `work+0x2C`.
- `r7 == 2`: writes byte `0x50` to config `+2`; calls `Config_MapByteToIndexC(config[2])`, stores result at `work+0x30`.
- Any other row falls through without this row-specific mapping write.

For the current editable option value, the function uses the signed current event at `work+0x1E` / `+0x20` and the corresponding `ui_func_0029D8FC` results. Recognized decrement/increment paths change the selected word at `work + 4*selection + 0x28`, clamping decrement at `0` and increment at `10` (`0x001EABEC..0x001EAC54`). Thus `0..10` is a proven clamp for these paths, not yet a proven valid/displayed domain for every option or malformed cursor state. A query based on event handle `work+0x22` invokes `camp_func_002BF6D0`, `script_vm_func_001C3588`, `script_vm_func_001DD158`, and `ui_func_002C615C` to derive and store another value; that helper chain's range and purpose are not known.

After handling events, it converts work values back to bytes through `script_vm_func_001FE3B8(work+0x28)`, `script_vm_func_001EA7F0(work+0x2C)`, `script_vm_func_0021F3F8(work+0x30)`, and `script_vm_func_0020FDC8(work+0x2C)`, and stores the results to `0x0044E0F8 + {0,1,2,3}` (`0x001EACB4..0x001EACE4`). This is direct write evidence: the persistent/config-addressed block is mutated while state 1 runs, including two distinct encodings at bytes `+1` and `+3` derived from the same `work+0x2C` value. State 2 also writes byte `+4` on one branch. The function performs no visible storage-device/file write in these paths. The block's later save/flush owner, rollback behavior, and across-process persistence are **not established**.

At `0x001EAA90`, the callback saves the selected work option value in `sl`: `r6 = work + (selection<<2)`, then `sl = [r6+0x28]`, i.e. `work[0x28 + 4*selection]`. After input handling and possible option mutation, `0x001EACE8` reloads `[r6+0x28]` and compares it with this saved value. The changed/unchanged branch is therefore about whether this work option changed during the current callback invocation; it is not a comparison against the displayed TBB payload. On the changed path, the callback calls `script_vm_func_002C5A6C`, queries a value via `script_vm_func_0025A0A4`, and sends that to `script_vm_func_0025A004` for channels `0` and `1`. For `r7` equal to `0/1`, it calls `script_vm_func_002B91C4(0x0100016D)`; for `r7==2`, it additionally calls `script_vm_func_002BC210`, `script_vm_func_002BFF9C`, then `script_vm_func_002BFDFC` with VFP constant `0x3F34FDF4`, integer `0x2712`, and the preceding result. Exact sound/effect semantics are not proven.

When the selected work value remains equal to its `sl` entry snapshot, the function polls `camp_func_0029F278(work+0xE8,1)`. If true it refreshes selected row text and calls `0x25A0D0`. If false it scans up to three signed halfword event handles at work offsets `+0x14,+0x16,+0x18` for event code `6`; it then invokes `script_vm_func_002B91C4(0x0100016C)`, `camp_func_0029EDFC(cursor,index)`, and refreshes text, or polls event IDs through `camp_func_002C1830` and prepares `work+0x5C` via `camp_func_002BDAC0`. These callback/animation branches need their called-function contracts before they can safely be simplified.

## Secondary callback and readiness caller

`TitleConfig_Secondary` (`0x002CAEF0`, original decode) sets byte `work+4` to `1`, drains counters at `+0x1A` and `+0x24` by repeatedly calling `0x002B9008`, releases/zeros handles at `+0x154`, `+0x14C`, and `+0x150`, checks and destroys the task at `work+0`, and finally frees/zeros the `g_TitleConfigWork` global. This callback is registered as the second calculation callback during the initializer's task creation. The exact meaning of flag `+4`, counter cleanup calls, and task API return is not inferred from names.

`TitleConfig_IsReady` (`0x002FC0EC`) returns `1` if `g_TitleConfigWork == nullptr`; otherwise it calls `battle_func_002BF41C(work->calc_task)` and returns `0` while that task is alive, `1` once it is not. The real title caller is `TitleMain_Calc` state 10: at `0x001EA3C4` it waits while `TitleConfig_IsReady()==0`, then invokes `Title_ResetForBoot` at `0x001EA3D8` and returns the title to state 5. State 9 (`0x001EA398..0x001EA3C0`) calls `Script_PrepareTransition(0)`, calls `titleConfig_func_002f4ca0(nullptr)`, and sets title state 10.

Existing H1 integration notes report reaching `0x002F4CA0` then `0x001EA928` with allocated work and later returning through `0x001EA3D8` to title state 5 on cancellation; `g_ConfigBytes` remained `3250503000000000` and save files were unchanged in that no-edit scenario. This verifies one title caller/cancel trajectory only. It does not establish behavior after changing options, whether changes are committed or rolled back, nor persistence across a re-entry or process restart.

## Proof, inference, and blockers

**Proven directly by instructions:** global/work addresses and offsets above; state dispatch bounds and jump destinations; option word address formula; explicit decrement/increment clamps `0..10`; config-byte reads/writes; state-2 byte `+4` write; state-3/4 transitions and `r0=-1`; registration/return caller shape; readiness predicate and title state-10 caller.

**Inferred but requiring independent observation:** labels “input,” “row,” “option,” “decrement,” “increment,” “confirm,” “cancel,” “sound,” or “animation” are plausible from branch structure, event IDs, message rows, and existing no-edit cancellation evidence. No instruction alone proves UI key meanings, human-visible values, whether state-2 return `0/1` is confirmation/cancel, or whether config bytes are durable storage rather than a live shared mirror.

**Unresolved calls that block an editable, self-contained reconstruction:**

- Input/event decoding: `0x0029D8FC`, `0x0025A0B4`, `0x002C1830`, `0x0019DFBC`, `0x00297674`, `0x0029F278`, `0x0029EDFC`.
- Cursor/table/message and UI setup: `0x0029F260`, `0x0029F248`, `0x002C0EC4`, `0x002C0E9C`, `0x0029F10C`, `0x002B88C4`, `0x002BF9F0`, `0x002BDAC0`, `0x002C615C`.
- Mapping/re-encoding: mapper callees `0x002CAB70`, `0x0021F39C`, `0x002E0AF4` and encoders `0x001FE3B8`, `0x001EA7F0`, `0x0021F3F8`, `0x0020FDC8`.
- Script/audio/callback side effects: `0x002972F8`, `0x0025A0D0`, `0x002C5A6C`, `0x0025A0A4`, `0x0025A004`, `0x002B91C4`, `0x002BC210`, `0x002BFF9C`, `0x002BFDFC`, `0x002B9008`, `0x002A755C`, `0x002C4360`, `0x002BF41C`, `0x002C45B8`.

These are original dependencies, not grounds to pretend a reconstructed callback is standalone. Their contracts can be bounded or retained as original calls, but their behavior and state effects must be observed before integration. The config write paths and the exit/persistence policy are especially critical.

## Differential and caller evidence required

For a future candidate, freeze the original image, candidate, data tables, and caller setup. Use a runner that supports this non-leaf callback's calls, globals, UI work and VFP path; the existing leaf-only semantic experiment is out of scope. Compare original and candidate from identical initialized `TitleConfigWork`, input/event state, cursor/TBB payload, and config bytes. Capture return `r0` (including the state-4 `-1`), callee-saved registers/SP against ABI expectations, `work[0..0x158)`, `g_ConfigBytes[0..8)`, relevant script/task state, and the ordered called-service trace where stubs are used.

Directed cases must cover each dispatch state `0..4`, states `5` and a high unsigned state, state-0 readiness false/true and missing script handles, all decoded event results around `0/1/2/6`, cursor rows `0/1/2` and out-of-range sentinel/neighbor values, each option word at `0`, `1`, `9`, `10`, attempts decrementing at zero and incrementing at ten, and changed/unchanged paths against the selected work value's entry snapshot. Separately verify display TBB offsets `0x16 + selection*0x96` for selections `0`, `1`, and `2`, yielding `0x16`, `0xAC`, and `0x142`; use a `0x56` stride as a negative control. Add random valid initialized work/input states with at least two recorded seeds. Other negative controls should deliberately change a clamp, work option offset, or config `+3` encoding and must be detected by the contract observables. Invalid cursor indices should be tested as a robustness boundary, not silently excluded unless the original's caller proves they cannot occur.

Caller tests must run the real title state-9/10 sequence: enter through selection 2; observe registered main/secondary callbacks; exit without changes; then make an option change and take the cancellation path, comparing bytes, selected row, and title transition with the original. Also edit each option in both directions, attempt both boundaries, take each state-2 result path, exit through readiness, verify the title returns to state 5, and re-enter to compare config bytes and visible selections. On a matched test profile, separately capture all eight config bytes and save/config files before exit, after edit while still in state 1, after cancellation, after the other exit path, after re-entry, and after a clean game restart. Repeat against original and integrated candidate from matched copies of the same initial profile. These observations settle whether edits are live writes, reverted on cancel, committed on confirm, or durable across sessions; existing cancel evidence covers only “no edit, bytes unchanged.”

## Next action

Before implementing `TitleConfig_Calc`, resolve the input and state-2 decision calls or instrument a bounded original-vs-candidate harness that keeps them as original dependencies. Add an explicit persistence scenario because disassembly proves writes into `0x0044E0F8` but does not identify the durable flush/rollback contract.
