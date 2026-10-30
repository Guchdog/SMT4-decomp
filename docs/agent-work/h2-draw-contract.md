# H2 draw contract research: `TitleConfig_Draw` (`0x002CAFD0`)

Status: instruction-level contract research only; no C++ replacement, draw-command harness, or emulator session was run. Original code identity: ARM function `[0x002CAFD0, 0x002CB75C)` (`1932` bytes), pinned code image SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.

## Registration and inputs

The `0x002F4CA0` initializer registers `0x002CAFD0` as the draw callback in the `AsdTask_CreateDraw` tuple, with key `"TITLE_CONFIG D"` and priority `0xE6`; the created draw task receives the calc-task pointer. Initializer evidence establishes the backing object and subobject setup: `g_TitleConfigWork` at `0x0044E2D0`, `TitleConfigWork` size `0x158`, sprite group `+0x3C`, sprite `+0x5C`, cursor `+0xE8`; sprite group is bound to table `0x00407EC6`, and the cursor setup is called with immediate args `3,3,1` and stack values `0,1`. The task tuple's precise scheduler ordering remains a helper contract.

The draw function ignores the incoming callback argument, loads the work pointer from `0x0044E2D0`, and reads these fields:

- `work+0x08`: used to select the active/selected presentation branch when equal to `1`.
- `work+0x5C`: sprite passed to position helpers `0x002BEF7C` and `0x002BEF70`; their results are added to layout coordinates used by later draw calls.
- `work+0xE8`: list cursor. `0x0029F260` and `0x0029F248` supply scroll/selection terms; `0x0029D8E4` supplies the positive loop bound used for rows.
- `work+0x1C`, `+0x1E`, `+0x20`, `+0x22`: signed halfwords passed to `UiTouch_GetRegionTouchState` (`0x0029D8FC`) in active-state branches. Returned codes `1`, `2`, and `6` choose different subsequent UI calls/IDs. The hardware/user action associated with each code is not established by this function alone.
- `work+0x28 + 4*index`: option-value words. For each row the callback loads the selected/visible value and uses `value+0x5B` as the second argument to `camp_func_002BF6D0(0x2F, ...)` to get another layout node. This proves an option-dependent lookup; it does not prove the displayed wording/value without the node/table and draw-helper contracts.

The callback has no visible direct stores into `TitleConfigWork` or `g_ConfigBytes`. It does write a renderer-state cache reached through global pointer `0x0044EA00` (base plus `0x1000+0x2AC`, then a row-indexed record at `+8`; it also clears that record's byte `+0x18` after an indirect callback). The corresponding indirect function pointer is loaded from record `+0x1C`. These cache and callback side effects are observable and must not be omitted from a behavioral comparison. Other effects inside called renderer, font, layout, or callback helpers remain possible.

## Row traversal and presentation setup

After querying scroll and selected-row values, the function gets the loop bound from `0x0029D8E4(work+0xE8)`. If the signed result is `<=0`, it exits without entering the row loop. Otherwise row index `r5` starts at zero, executes while `r5 < bound`, and increments once per iteration. The cursor helper's valid range and precise meaning of the bound are dependencies; initializer cursor args and the later `index < 3` guard suggest a three-row control, but do not on their own prove every cursor-helper result.

For each row, it initializes a local `0x5C`-byte draw/format area, gets the node `camp_func_002BF6D0(0x2F, r5+0x1F)`, and reads signed halfwords at node offsets `+8` and `+0xA`. Sprite-position outputs and these node coordinates feed later calls. It computes the absolute list index from cursor scroll plus loop row. If `work+8 == 1` and the current row equals the selected row (the code compares `scroll + r5` against `scroll + selected`), it sets a local selected flag and uses color word `0x72E027FF`; other rows use `0xE09800FF`. These are proven arguments passed onward; the exact visible color/selection rendering depends on the consumer helpers.

For absolute list indices below `3`, it gets the payload for TBB table `0x3A` (subtable selector `1`) and addresses the row descriptor at `payload_base + absolute_index*0x96`. This is encoded by `rsb r1,r7,r7,lsl #4`, `add r1,r1,r1,lsl #2`, then `add r2,r0,r1,lsl #1`; unlike the `TitleConfig_Calc` text path it has no `+0x16` on this descriptor pointer. It passes the descriptor and a PC-relative format string to `UiText_Format` (`0x002BE7FC`) to populate the local buffer, then passes that buffer, color, layout-derived coordinates and scale values to `0x002BE77C` (`UiFont_DrawText` in other checked-in declarations). The explicit `index < 3` branch prevents this TBB lookup for indices `3` and above, but is not proof that invalid cursor state is safe elsewhere.

The rest of each row issues direct panel/node calls and text-format/draw calls. The exact encodings in the function include `0x002BF460` and `0x002BF558` with group `0x2F`, command/node IDs including `0x0C`, `0x0D`, `0x10`, `0x15`, `0x1A`, and `0x1B..0x32`; in active state the results of touch-region queries at offsets `+0x1E`, `+0x20`, and `+0x22` gate alternate calls. These IDs/arguments are recoverable. Mapping them to labels such as “music”, “sound effects”, “slider”, “selected”, or “pressed” requires the message, layout, panel, and event helper contracts or an observed draw trace.

## Rendering calls, branches, and ABI

The key called operations and their instruction-level role are:

- `0x002BEF7C` / `0x002BEF70`: read sprite position components from `work+0x5C`; the checked-in leaf implementations read sprite fields at `+0x0C` and `+0x10` and shift by 12.
- `0x0029F260`, `0x0029F248`, `0x0029D8E4`: cursor-dependent scroll/selection/row-bound values. Exact valid domains still depend on cursor setup and helper behavior.
- `0x002BF6D0`: returns layout nodes for group `0x2F` and node indices derived from the row, `0x1A`, and option value `0x5B+value`; the function consumes node halfwords at `+8/+0xA`.
- `0x002C0EC4` / `0x002C0E9C`: obtain TBB table/payload data for table `0x3A`.
- `0x002BE7FC`: formats a string into the local buffer using a table-derived row descriptor and PC-relative format data.
- `0x002BE77C`: consumes the local buffer and rendering parameters for the font/text output.
- `0x002BF460` / `0x002BF558`: direct sprite-node/panel-style UI draws, with group and node IDs plus layout-derived coordinates and flags. Use the original argument trace because signatures vary in current call-site declarations.
- `0x0029D8FC`: reads registered touch-region state; codes `1`, `2`, and `6` affect active-state draw branches. Their input meanings are not proven here.
- `0x002C5FA4`: called repeatedly with mode `6` and changing small parameters. The output is stored in a GPU/render-state record; if its change predicate requires it, the record's function pointer at `+0x1C` is invoked indirectly, then cache flag `+0x18` is cleared.

The callback saves `r4-r11`, `lr`, and `d8`, reserves `0x5C` stack bytes, and restores all of them on its single return path; it returns `r0=0`. It uses VFP registers for sprite scale/coordinate arithmetic and thus is outside a leaf-only integer runner. The row-local formatting buffer, renderer cache, draw-helper calls, and possible indirect callbacks are part of its observable behavior.

## Proven rendering facts versus inferred visible meaning

**Proven by instructions and constructor layout:** draw callback address and registration key/priority; global work pointer; exact work offsets; the count-controlled row loop and TBB guard; TBB table ID and `0x96` row addressing; option-word address formula; active-state equality/highlight branch; hard-coded colors and panel/text command arguments; text and renderer call order; render-cache stores/conditional indirect calls; ABI save/restore and return value.

**Inferred, not proven by this callback:** there are three visible audio options corresponding by order to the first three config bytes; color constants mean selected versus unselected in the visible UI; returned TBB payload text is the user-facing row label; `value+0x5B` renders the audible value; touch states correspond to A/B/d-pad actions; panel/node IDs correspond to specific speaker/volume icons. These are plausible from the initializer and `TitleConfig_Calc` shape, but require actual table contents/helper contracts or original runtime draw observations.

**Unresolved helpers / preconditions:** the valid state and range of `UiListCursor`, exact result contract for `0x0029D8E4`, TBB payload layout/encoding for table `0x3A`, layout-node semantics for group `0x2F`, text/panel rendering parameter contracts, renderer-cache lifecycle and indirect callback targets, and ordering with calc are not established by this body. The valid candidate domain should use an initializer-created work object, loaded table/resource data, and stable cursor/event state. Treat null globals, missing tables, malformed indices, and concurrent calc mutation as separate fault/domain boundaries; do not invent recovery behavior.

## Bounded differential and real-caller test proposal

Use a runner for non-leaf ARM/VFP callbacks with stable initialized work, table payloads, GPU state, and controllable external calls. Execute original and candidate from byte-identical snapshots of `TitleConfigWork`, renderer cache at `0x0044EA00`, TBB `0x3A`, layout group `0x2F`, touch-region service state, and sprite positions. Instrument and compare the ordered command trace and arguments for `0x002BF460`, `0x002BF558`, `0x002BE7FC`, `0x002BE77C`, plus `0x002C5FA4` and any triggered indirect callback; compare the exact changed renderer-cache bytes and any helper-observed memory. Also assert identical `work[0..0x158)` and `g_ConfigBytes[0..8)` across the draw call, while allowing caller-saved registers and unconsumed `r0` to differ. Compare callee-saved registers, SP, and `d8` against ABI expectations.

Keep calc stopped/frozen during a draw. Start with the initializer-created row count and valid cursor states: `work+8` equal to `0` and `1`; selected row 0, 1, and 2; scroll offset zero, plus a nonzero offset only if an original initialized cursor state permits one; each of three option words at low, middle, and high values; no touch event and each decoder result `1`, `2`, and `6` for the region handles. Cover a nonpositive loop bound through a controlled helper result if that state is permitted, and an absolute row index `3` to verify the TBB guard skips payload lookup. Add a malformed-cursor case only to characterize the original; do not assume the out-of-domain behavior is safe. Use two recorded seeds only after the stable directed matrix, with identical frozen helper/table inputs and randomization limited to valid initialized fields. A negative-control candidate with the wrong TBB stride or suppressed active-row branch must differ in the recorded TBB/formatted draw commands as expected.

Then test the real draw-task composition from the title state-9 initializer and active calc state: observe the registered draw callback, freeze a reached frame after calc has settled, run one draw invocation in original and candidate, and compare the same command trace and cache state. A screenshot can help identify user-visible mapping but is not a substitute for matching execution commands, TBB data access, or memory effects. No such candidate/caller evidence is available yet.

## Next action

Before implementing the draw callback, resolve or explicitly retain as original dependencies the renderer, format, TBB, cursor, layout, and indirect-cache helpers. Record the actual command trace for each of the three valid row indices so the `0x96` addressing and selected-state branch are tied to the real initialized caller without claiming unsupported text/color meanings.
