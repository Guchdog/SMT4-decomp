# H2 Calc input and cursor seam research

Status: static contract research only. No candidate code, emulator, debugger session, RSP write, OS input, or profile change was used.

## Scope and pinned identity

This report follows the input and cursor dependencies called by `TitleConfig_Calc` (`0x001EA928`) in the pinned original image `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The actual caller is the title main-menu state-9 transition: it calls `titleConfig_func_002f4ca0(nullptr)`, which registers Calc and secondary callback `0x002CAEF0`; the title enters state 10 and waits on `TitleConfig_IsReady` before its state-5 reset. The initializer creates `TitleConfigWork` (`0x158` bytes), sets up cursor at `work+0xE8`, and calls `UiConfig_FillPair(work+0x1C,-1)`. The pinned calc and init reports document these caller facts and the no-edit H1 traversal; that traversal does not validate deterministic input.

## Helper chain: proven instruction behavior

### `UiTouch_GetRegionTouchState` (`0x0029D8FC`)

The ARM body loads `g_IfTouchGlobal` at `0x0043DCB0`, obtains its work pointer, reads the signed halfword `IfTouchWork+0x64E` (`active_panel_id`), and compares it with the signed `s16` argument. A mismatch returns `0`; a match returns the raw byte at `IfTouchWork+0x08`. Therefore Calc's comparisons against return values `1`, `2`, and `6` are comparisons against that byte. The value's enum meaning, producer, and relationship to a physical touch/button event are not established by this helper.

There is a concrete workspace mismatch: the initializer fills the words at
`TitleConfigWork+0x1C` and `+0x20` with `0xFFFFFFFF`; Calc reads four signed
halfwords at `+0x1C,+0x1E,+0x20,+0x22` as arguments to
`UiTouch_GetRegionTouchState`. In Calc state 0, `UiTouch_RegisterRegion`
(`0x002B88C4`) is called for group `0x2F`, node IDs `0x1F,0x20,0x21`, and its
returned registration indices are stored at `work+0x14,+0x16,+0x18`. No
producer was found that replaces the four `+0x1C..+0x22` values; do not treat
them as writable event bytes. The manager state producer is now known:
`IfTouch_Init` initializes `IfTouchWork+0x64E` to `-1` and registers callback
`0x00107CCC` under task name `TOUCH CALC`. Hit-test paths write an index to
`+0x64E` and set/clear the byte at `+0x08`; the getter returns that byte when
the passed signed halfword matches. The meaning/timing of that byte and its
relationship to the H2 sentinel values remain unresolved. Registration records
are stored at `IfTouchWork+8*index+{0xA,0xC,0xE,0x10}` with the count at
`+0x64A`; the `+0x600` base is used for trailing manager fields, not the record
array. See the [reviewed manager-state producer audit](h2-input-manager-touch-state-producer-audit.md).

### `camp_func_002C1830(id, mode)`

This helper receives a logical control ID in `r0` and mode in `r1`; IDs `>=11` return zero. Mode 0 dispatches to `ui_func_002B902C(id)`, mode 1 to `ui_func_002BFFBC(id)`, and mode 2 to `ui_func_002C17D4(id)`. IDs 3, 4, 5, and 6 may issue secondary logical queries for IDs `0xC..0xF` if the primary query is false. Several IDs can route to additional class-based controller/key query helpers. These instructions prove a logical-query API and its arguments/branch structure, not physical button names or key mappings.

Calc calls this helper with `(9,1)`, `(4,0)`, `(3,0)`, `(0,1)`, and `(1,1)` in its active state. Preserve these exact logical IDs and modes when testing. The pinned table maps IDs 9, 4, 3, 0, and 1 to masks `0x400`, `0x20`, `0x10`, `0x1`, and `0x2`; all 31 masks are tested against the same refreshed state dword at `0x004E3C28`, while each logical ID selects a separate counter at `0x004E3C58 + 4*id`. The mode-0 queries for IDs 4 and 3 can fall back to IDs `0xD` and `0xC`, masks `0x20000000` and `0x10000000`, in the same state dword. These are internal state bits, not physical button names. The refresh obtains an input snapshot through `func_0011C5EC`; complete state population, scheduler timing, and device/frontend provenance remain unresolved. See the [logical table audit](h2-logical-input-table-producer-audit.md).

### `camp_func_0029F278(cursor, mode)` and cursor observers

The title initializer passes `work+0xE8` to `UiListCursor_Setup` (`0x0029FAE8`) with arguments `r1=3,r2=3,r3=1` and stack values `{0,1}`. The checked-in `UiListCursor` span is `0x64` bytes; the disabled field is at `+0x62`, total item count at `+0x50`, and the two axis subrecords start at `+0` and `+0x28`. `camp_func_0029F278(cursor,1)` is an updating/mutating routine, not a pure selection getter: it checks the disabled flag, reads cursor fields, queries logical input through `0x002C17D4` and other engine helpers, updates internal flags/timers, and returns a change/status value. Calc uses its return to decide whether to refresh row/message work. The meanings of all internal flags and downstream control mappings remain incomplete.

`0x0029F248` and `0x0029F260` expose selected-row and scroll-offset values through downstream cursor getters. Their wrappers return zero when the cursor disabled flag is nonzero. The setup establishes a total count of 3, but does not by itself prove every reachable row value or malformed-cursor behavior.

### `script_vm_func_0019DFBC(task)`

This routine indexes a per-task script dispatch table using task fields around `+0x18` and `+0xBC`, calls the selected handler, and updates task fields `+0xCC`/`+0xD0` depending on its return. A handler result of zero makes this wrapper return 2; result two advances counters and returns 1; result one clears a field and loops. Calc state 2 polls it with `work+0x154` and proceeds only on return 2. The indirect script handler and its effects are unresolved. This is a script readiness/progress dependency, not a demonstrated HID/input seam.

## Is there a safe pre-Calc guest-state input seam?

No valid guest-state injection address or byte representation is established by current evidence. The manager byte returned by `0x0029D8FC` has a proven writer in the `TOUCH CALC` callback, but its state meanings, runtime cadence, and relationship to H2's `-1` query arguments remain unresolved. The global logical-input counters have a proven refresh path, while the producer of their underlying `0x004E3C28` state and a synchronization window remain unresolved. Mutating `work+0x1C..+0x22`, `IfTouchWork+8`, or guessed fields in the global input tables would still write an undocumented event state. Editing `g_ConfigBytes` would bypass Calc input and is not an equivalent control event.

A safe **offline function-test seam** is available as an explicit harness boundary: invoke Calc from an initialized, captured caller state while intercepting the documented logical service call `(id,mode)` and supplying its returned integer. This tests Calc's logical-event contract only; it does not demonstrate that an Azahar guest event can be injected or that the real helper producer will generate that result. For example, a controlled `(4,0) -> 1` can test the branch Calc associates with that query while all unrelated service results remain zero; its physical control meaning is unknown.

## Bounded observation and test plan

For any future original-versus-candidate function harness, freeze the pinned original, candidate, tables, initialized work/global memory and caller setup. At each relevant helper boundary record call-site PC, `r0-r3` at entry, `r0` on return, caller PC, and the immediately consumed condition/result. Also snapshot `TitleConfigWork[0..0x158)`, `g_ConfigBytes[0..8)`, the full `0x64` cursor before and after `0x0029F278`, `g_IfTouchGlobal` and its pointer, `IfTouchWork+0x08`, `+0x64A..+0x64E`, and registered-region records at `IfTouchWork+8*index+{0xA,0xC,0xE,0x10}` for H2 indices 10, 11, and 12. For logical queries, record the exact ID/mode and any consulted global/table bytes only after their addresses are independently confirmed. For state 2, capture script task fields `+0x18,+0xBC,+0xCC,+0xD0`, selected dispatch index/table target, and handler return. Compare callee-saved registers/SP and ordered service trace to the ABI contract; do not make equality claims about unused caller-saved scratch.

Minimal function-level controls:

1. **No-op negative control:** from a valid initialized caller snapshot, make every modeled logical input query return zero and keep cursor input stable. Run one Calc tick and record its normal config-byte mirror writes and full work/cursor delta; “no-op” means no logical event, not necessarily no memory writes. The original/candidate deltas and call traces should agree.
2. **Positive logical-event control:** repeat from the same snapshot, but make only `(4,0)` return one and keep all other query results zero. Compare the resulting work/config/cursor delta, display/service trace, and return against the original. This tests the ID 4 logical branch, not a named physical button. A second directed case may use `(3,0) -> 1` to cover the other logical branch. Include return-zero controls for both.
3. **Touch boundary:** do not synthesize a touch result by writing `work+0x1C..+0x22` or `IfTouchWork+8`. The static producer and task registration are known; a runtime observer must capture the real manager fields, registered indices, callback branches, and getter arguments/results to determine whether the sentinel arguments match during H2. Until observed, touch results 1/2/6 remain value-path tests only if supplied at a harness service boundary, not guest-state injection cases.
4. **Cursor path:** retain the original cursor/input services in the differential harness where possible. Test setup's count of three, stable no-event tick, each valid observed row, movement boundary behavior, disabled cursor, and out-of-range/sentinel behavior separately. Do not assert malformed values safe unless the original/caller constrains them.

Existing checked-in `experiments/semantic_equivalence/azahar_hit_flag.py` cannot collect the required state: it supports connect/attach, software breakpoints, continue, PC read, remove and detach, but not guest memory/register reads or `M`/`P`. The separate runtime contract documents a future isolated Azahar approach and states that `M`/`P` support has not been probed. Any later RSP capability test must be separately assigned/reviewed, use a staged executable and private disposable user tree, verify executable/hash/path/PID and loopback port isolation, and first identify an independently documented writable scratch location. Use read-only observations and a no-op/round-trip control before a reversible write, verify packet replies and read-back, restore the exact saved bytes/register, and stop on any unsupported or unexpected response. No suitable scratch region or valid event-state address is currently identified, so no RSP write test is safe to specify as immediately executable. Never fall back to OS keyboard/mouse automation in that route.

## Evidence levels, limitations, and next action

**Directly supported:** helper instruction behavior and arguments above; initializer's cursor setup and sentinel fills; Calc's exact logical query IDs/modes; `IfTouch_Init` registration of the `TOUCH CALC` callback and explicit manager initialization; the callback's manager field writes; registration-record layout; title state-9/10 caller chain; absence of memory/register read/write capability in the checked-in RSP script.

**Inference/unknown:** physical button labels for logical IDs; meaning and runtime cadence of `IfTouchWork+8`; whether H2's `-1` arguments produce useful results during the actual callback schedule; relation between the manager callback's index and H2's registered region indices; producer/update chain for global key maps; indirect script handler effects; cursor valid/malformed domain; whether a deterministic event can be injected into a real guest before Calc.

**Validation not performed:** no compiled candidate, ARM differential, caller test, emulator run, RSP probe, or profile interaction. Existing H1 no-edit traversal is not deterministic-input evidence. There is no supported claim of runtime input equivalence.

Next observe the known manager callback and H2 registration/getter values in a safe, approved runtime session, and continue resolving the logical-state table/source path from pinned instructions. Keep manager and logical input as explicit original dependencies in offline tests; do not write guest input fields until a synchronized, documented injection seam is independently reviewed.
