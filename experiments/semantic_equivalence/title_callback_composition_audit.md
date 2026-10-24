# H1 title callback composition audit

Scope: determine whether the existing navigation reducer, touch reducer, and
help-selection caller window can be composed into one bounded semantic
callback candidate. This is static ARM control/data-flow evidence plus the
contracts of the isolated experiments; it is not an emulator observation.

## Finding

Do not claim a composed callback candidate yet. In requested execution order,
the first uncovered boundary is between the navigation reducer's stop at
`0x001E9DE0` and touch polling's start at `0x001E9E4C`: the intervening original
ARM block updates animation state using work memory and VFP registers. Even if
that block is preserved as an original-code partition, the larger blocker after
touch is the branch at `0x001E9EB8` to `0x001E9F4C`, followed by a UI transition
path through `0x001EA128`. That path reads and mutates several live work-block
fields and dereferences separate UI objects before reaching the help caller
window at `0x001EA12C`.

The first gap decodes as: load/increment/store `work+0x64` at
`0x001E9DE0..0x001E9DE8`; compare against literal-backed limits; conditionally
load, add/subtract and store VFP values through `work+0x64/+0x68` in
`0x001E9DF0..0x001E9E48`. It therefore requires the same work block and FP
state produced by the preceding callback path. It is not represented by either
current reducer. A safe next increment can execute this exact original block in
the same Unicorn machine, recording its read/write footprint and FP state; a
standalone fused C++ candidate must first reconstruct those semantics.

The gap is not a neutral bridge and cannot be replaced with a no-op, zeroed RAM,
or a direct jump to help without narrowing the equivalence claim. Specifically:

- `0x001E9F4C..0x001E9FD0` reads `work+0x96`, gates on
  `Camp_IsPreviewReady` (`0x0025A2BC`), reads/writes `work+0x94`, and follows
  pointers from `work+0x90` (and nested `+8`, `+0x2C`) while changing widget
  flags and animation state. It conditionally calls `0x0029BDB4` and calls
  `0x00210030`.
- `0x001E9FD4..0x001EA010` dereferences `work+0x8C` and nested object pointers,
  calls readiness helper `0x0025A274`, then `0x002D569C`, and branches based on
  their results and `work+0x94`.
- `0x001EA01C..0x001EA128` contains another set of widget-flag, VFP animation,
  and child-object mutations, with calls to `0x0029BDB4`, `0x002872A4`, and
  `0x0020FFA0`; it sets `work+0x94` before falling through to help selection.
- The help window `0x001EA12C..0x001EA15C` is not a pure arithmetic lookup:
  it calls `0x002C0EC4` and `0x002C0E9C` using the global TBB manager/table
  context and real `TitleTable.tbb`, then prepares `Camp_SetSlotMessage`
  (`0x0029F10C`) arguments. Existing evidence stops before that callee, so it
  does not establish its UI side effects.

There is a second contract gap on the touch side. The original callback calls
`UiTouch_GetRegionTouchState` (`0x0029D8FC`) twice for each region during the
first scan (testing states 1 then 2), then once more per region during the
state-6 scan. The current touch harness supplies a stable response keyed by
region handle. That is a valid explicit reducer contract, but it does not
establish that real helper results remain stable across those nine calls or
capture its physical/timing behavior.

## Evidence boundary and current experiments

The pinned `code.bin` identity used by the existing H1 harnesses is SHA-256
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
Capstone decoding of that image establishes the branch and helper-call sites
above. The navigation, touch, and help experiments separately execute their
bounded original ARM windows; their current reports/contracts are documented
in `title_navigation_family_audit.md` and `title_help_presentation_audit.md`.
Those separate passes do not share a continuous machine state and therefore do
not prove a composed callback.

Known mutable/intermediate state includes:

- Work block: `+8` cursor, `+0xC` cached cursor, `+0x63` touch-confirm byte,
  `+0x64/+0x68` animation fields, `+0x8C/+0x90` UI object pointers,
  `+0x94/+0x96` transition flags, `+0x98` animation value, and touch-region
  handles beginning at `+0x74`.
- Global pointer read through `r8` at the navigation/touch windows; the
  isolated touch runner explicitly installs it and its region handles.
- VFP registers and memory-backed float values used in the animation path.
- Nested UI object memory and helper effects for preview readiness, widgets,
  animation, and text presentation.
- TBB global slot and the real title table, already established by the help
  caller-window test but not shared with the navigation/touch harness state.

Zero-filled pages in a future runner would only be acceptable for bytes proven
unread/unmodified on the exercised branch; the current harnesses do not prove
that for the transition path.

## Smallest defensible next partition

1. Extend the existing touch experiment only to the next bounded decision
   point, preserving the original ARM block `0x001E9F4C..0x001EA128` and its
   actual branch conditions. First map the minimum object graph reached on one
   explicit path and enumerate every helper call, memory access, and VFP input.
2. Add explicit hooks only where a callee cannot yet execute; each hook must
   have a call-counted response contract and record arguments plus relevant
   before/after memory. Do not model widget/renderer effects as ordinary RAM
   writes unless the original callee contract is independently established.
3. Once a branch reaches `0x001EA12C`, continue the same machine into the
   original TBB getters with the real table installed, and stop at
   `0x001EA15C`. Keep `Camp_SetSlotMessage` as an explicit recorded boundary
   until its observable contract is tested.
4. Only after that caller-window run shares state with navigation/touch should
   a fused candidate be attempted. The current separate C++ reducers remain
   valid only for their stated subcontracts.

For continuity through the callback, the navigation-to-touch animation gap
must either execute as original ARM with explicit initial FP/work state or be
isolated as its own verified partition. A later C++ composition still cannot
skip the touch-to-help transition described above.

## Commands and limits

Existing component checks:

```powershell
python -m unittest tests.test_title_navigation_family_experiment -v
python -m unittest tests.test_title_touch_family_experiment -v
python -m unittest tests.test_title_help_presentation_experiment -v
```

This audit adds no function to either byte-exact or semantic-reconstruction
counts. No production source, ledger, README/MODLOG, ROM, or Azahar state was
changed. The full callback, physical input behavior, widget/text rendering,
and whole-game equivalence remain unverified.
