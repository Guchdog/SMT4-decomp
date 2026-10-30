# H2 input-handle producer audit

> **Superseded by the reviewed manager-state follow-up:**
> [h2-input-manager-touch-state-producer-audit.md](h2-input-manager-touch-state-producer-audit.md).
> That follow-up finds the `TOUCH CALC` callback that writes manager state and
> corrects the registration-record base described below. This report remains
> useful for its direct caller inventory and TitleConfig workspace findings.

## Finding

No statically proven producer in the pinned image initializes `TitleConfigWork+0x1C..+0x22` to registration handles. The actual title-config initializer writes two words of `0xFFFFFFFF` to `+0x1C` and `+0x20` via `UiConfig_FillPair`; these are the four halfwords Calc later reads as signed touch arguments at `+0x1C,+0x1E,+0x20,+0x22`. In Calc state 0, the three observed `UiTouch_RegisterRegion` return values go to `+0x14,+0x16,+0x18`, with `+0x1A` incremented after each call. The separate counter and handle stores do not reach `+0x1C..+0x22`.

The manager fields do have a static producer: `IfTouch_Init` initializes
`IfTouchWork+0x64E` to `-1` and registers internal callback `0x00107CCC` under
the task name `TOUCH CALC`. Its successful hit-test paths write the active
index at `+0x64E` and state byte at `+0x08`; other paths set or clear that byte.
The state byte's event meaning, runtime callback order, and relationship to
H2's four `TitleConfigWork` sentinels remain unresolved. See the reviewed
follow-up linked above.

## Pinned image and search method

All disassembly below is from `extracted/exefs/code.bin`, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, with function spans/names from `config/functions.csv`. The repository's `tools/split_asm.py --addr` was used to inspect the initializer, Calc, register helper, lookup helper, getter, and registration-counter helper. A read-only Capstone scan over the ledgered ARM/Thumb function spans found **83 direct `BL` sites in 18 functions** to `0x002B88C4`. This direct-call inventory does not cover computed `BLX` targets, runtime callback tables, malformed/out-of-span code, or memory corruption; it is not a whole-program alias proof.

| Caller function | Direct call PCs to `0x002B88C4` |
| --- | --- |
| `0x0018B878` | `0x0018B8F0` |
| `0x00195044` | `0x001950C8`, `0x001950DC`, `0x001950EC` |
| `0x001955BC` | `0x0019581C`, `0x0019584C`, `0x0019585C`, `0x0019586C` |
| `0x001A1E7C` | `0x001A1F80`, `0x001A1FE8`, `0x001A20B8`, `0x001A20C8`, `0x001A20D8` |
| `0x001C8D28` | `0x001C93CC`, `0x001C93DC` |
| `0x001CE98C` | `0x001CED34`, `0x001CED88` |
| `0x001E989C` (`TitleMain_Calc`) | `0x001E9AF8`, `0x001E9B08`, `0x001E9B18`, `0x001E9B28` |
| `0x001EA928` (`TitleConfig_Calc`) | `0x001EA9A4`, `0x001EA9C0`, `0x001EA9DC` |
| `0x002178A0` | `0x0021798C`, `0x002179F0`, `0x00217A34`, `0x00217A50`, `0x00217A74` |
| `0x0023046C` | `0x00230558`, `0x00230568` |
| `0x0023282C` | `0x00232890`, `0x002328A4`, `0x002328B4`, `0x002328D4`, `0x00232908`, `0x0023293C` |
| `0x00233804` | `0x00233884` |
| `0x002937C4` | `0x00293834`, `0x0029387C`, `0x002938BC`, `0x00293918`, `0x00293948`, `0x0029395C` |
| `0x002983DC` | `0x0029866C`, `0x002986F4`, `0x00298760`, `0x002987D0`, `0x002987E4`, `0x002987F4`, `0x00298864`, `0x00298878`, `0x00298888`, `0x002988A0`, `0x002988B4`, `0x002988C4`, `0x002988DC`, `0x00298958`, `0x0029899C`, `0x002989B8`, `0x002989DC`, `0x00298A14` |
| `0x00299E60` | `0x00299EA0`, `0x00299EB4`, `0x00299EC4`, `0x00299ED8`, `0x00299EEC`, `0x00299EFC`, `0x00299F4C`, `0x00299FB0`, `0x00299FE0`, `0x00299FF4` |
| `0x002A02C8` | `0x002A03DC`, `0x002A0400`, `0x002A0410`, `0x002A0420` |
| `0x00329404` | `0x003294D4`, `0x00329504`, `0x00329514`, `0x00329524` |
| `0x0032CB08` | `0x0032CEC4`, `0x0032D014`, `0x0032D084` |

The 18 entries establish there are many other touch-region clients. The inspection of their distinct call arguments/store bases (where source/inline ARM was available) shows unrelated screen or controller workspaces: examples include group `0x1D` at `0x00299E60`, group `0x24` at `0x002A02C8`, and group `0x2E` at `0x0023282C`. They do not pass the `TitleConfigWork*` as an output destination to the helper. A registration return is stored by the caller into its own supplied work layout; it is not globally written to all title workspaces.

## Exact title-config writer/read chain

1. **Initializer `titleConfig_func_002F4CA0`.** The pinned instructions allocate `0x158` bytes and publish the pointer at `0x0044E2D0`. At `0x002F4DBC` it forms `work+0x1C`; at `0x002F4DB8` it sets `r1=-1`; `0x002F4DC4` calls `UiConfig_FillPair` (`0x0027EDF8`). The helper masks the value to a byte, replicates that byte across the word, and issues `str [p]` and `str [p,#4]`. With `-1`, it directly initializes bytes `+0x1C..+0x23` to all ones. `+0x24` is separately zeroed. This is the only confirmed initialization of the target span in the initializer.
2. **Calc `script_vm_func_001EA928`, state 0.** At `0x001EA99C..0x001EA9A4`, it calls `UiTouch_RegisterRegion(0x2F,0x1F)` and stores returned `r0` with `strh [work,#0x14]` at `0x001EA9A8`; then calls `(0x2F,0x20)` and stores at `+0x16` (`0x001EA9BC..0x001EA9C4`); then `(0x2F,0x21)` and stores at `+0x18` (`0x001EA9D8..0x001EA9E0`). Between them it increments the halfword at `+0x1A`. No instruction in this sequence stores into `+0x1C..+0x22`.
3. **Calc active state.** It reads signed halfwords at `+0x1C` (`0x001EAA94`), `+0x1E` (`0x001EAB58`), `+0x20` (`0x001EAB94`), and `+0x22` (`0x001EAC58`) before calling `UiTouch_GetRegionTouchState` (`0x0029D8FC`). The getter loads the manager pointer from global `0x0043DCB0`, reads signed halfword `IfTouchWork+0x64E`, compares that to the passed `s16`, and returns byte `IfTouchWork+0x08` only on equality, else zero. It neither reads the title workspace nor writes any work field.
4. **Secondary callback `TitleConfig_Secondary` (`0x002CAEF0`).** It obtains the current title-work pointer from `0x0044E2D0`; directly sets `work+4`, reads counters `+0x1A/+0x24`, calls `0x002B9008`, and clears resource words at `+0x154`, `+0x14C`, `+0x150` before task/global cleanup. No direct store targets `+0x1C..+0x22`.
5. **Registration helper `camp_func_002B88C4`.** It gets the `IfTouchWork*` from global `0x0043DCB0`, calls `camp_func_002BF6D0` with the group/node arguments to resolve the group's node record, and reads coordinates/flags. It reads/increments the registration count at `IfTouchWork+0x64A`, but writes the indexed record at `IfTouchWork+8*index+{0xA,0xC,0xE,0x10}` (not `+0x600+8*index`). Since initialization starts the count at 10, successful H2 registrations return indices 10, 11, and 12. If capacity reaches `0xC8` it returns `-1`; on successful insertion it returns the pre-increment index in `r0`. The caller—not this helper—stores that returned index. Neither the helper nor its lookup receives the `TitleConfigWork*`; its writes are based on the manager global. Its data lookup includes runtime table pointers/record contents, so exact region geometry and node semantics remain unresolved.
6. **Counter helper `camp_func_002B9008`.** It also uses the manager global and changes only the halfword count at `IfTouchWork+0x64A` (decrementing when the count exceeds 10). The TitleConfig secondary callback's counter drain through this service does not clear or rewrite TitleConfig handle fields. It is manager/list bookkeeping, not a producer for the Calc polled offsets.

The direct title-main touch registrations are a useful counterexample to confusing equal field offsets: `TitleMain_Calc` (`0x001E989C`) registers group `0x11`, nodes `0x14,0x15,0x18,0x19` at call PCs `0x001E9AF8..0x001E9B28`. The returned halfwords are placed in the separate `TitleMainWork` touch array beginning at `+0x74` (`TitleTouchHandles` points at `&work->field_74`). The State-8/10 reset repeats those four registrations. These do not write `TitleConfigWork`; the work object is independently allocated/published at `0x0044E2D0`, while the title-main object is at `0x0044E300`.

## What the evidence rules out and what it does not

**Ruled out by the inspected direct paths:** the three registration returns from the observed Calc state-0 path are not stored in `+0x1C..+0x22`; `UiTouch_RegisterRegion` itself only writes manager-side records and the manager count; the initializer explicitly fills all four polled halfwords with `-1`; and the secondary callback/counter helper has no direct write there. The register handle convention from `0x002B88C4` yields an insertion index or `-1`, not a direct pointer or a TitleConfigWork offset.

**Not ruled out:** other untraced indirect calls, runtime-computed writes, or aliasing through an unexpected object/pointer could modify the TitleConfig bytes. The static caller inventory is for direct `BL` instructions across ledgered spans. The manager producer is now identified: it initializes the active index to `-1`, then writes an indexed value on hit-test paths, while the state byte is set/cleared by several branches. Whether `-1` sentinel queries can yield a meaningful nonzero state during the real H2 schedule, how the callback's index relates to the three registered region indices, and why Calc polls four separate halfwords remain unresolved. Neither caller names nor node IDs establish physical touch/input mappings.

## Bounded next observation

Do not seed or mutate `TitleConfigWork+0x1C..+0x22` as event state. For a future approved read-only runtime observer, capture the title-work pointer and bytes `+0x1C..+0x24` after initializer completion; record each Calc register call's `(r0=0x2F,r1=node)` and return `r0`, the caller's destination address, and post-store bytes. At the `TOUCH CALC` callback entry and the hit-test writes, capture `IfTouchWork+0x08`, `+0x64A`, `+0x64C`, and `+0x64E`; at each `UiTouch_GetRegionTouchState` call capture its argument and returned byte. Capture registration records at `IfTouchWork+8*index+{0xA,0xC,0xE,0x10}` for indices 10, 11, and 12. This will establish the real callback cadence, state behavior, and relation between hit indices and H2 registrations; physical mapping still needs separate provenance. Keep logical service results as explicit offline mocks until those observations are independently reviewed.

No compiler, emulator, RSP, profile write, game write, or keyboard/mouse input was used for this audit.
