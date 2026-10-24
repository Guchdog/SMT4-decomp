# H1 title transition-readiness audit

Scope: static ARM analysis of `0x001E9FD4..0x001EA128`, its transition into
the help window at `0x001EA12C`, and the called readiness/fade routines named
in the request. This is not a new candidate, a runtime observation, or proof
of visible UI behavior.

## Pinned evidence and boundary

The source image is `extracted/exefs/code.bin`, SHA-256
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, matching
`config/game_info.json`. The callback words are preserved at
`src/ui/ui_runtime2.cpp` (`ui_func_001e989c`); the helper words are preserved
in `src/engine/leaf_batch16_a.cpp`, `leaf_batch16_c.cpp`, `leaf_batch15_b.cpp`,
`leaf_batch16_c.cpp`, `leaf_batch38_a.cpp`, and `leaf_batch41_b.cpp`. The
addresses below are direct ARM disassembly of that pinned image. No execution
of this path in Azahar or a shared callback harness was performed here.

## Branch and field dependencies

At entry `0x001E9FD4`, `r4` is the title work pointer. The first two calls
receive the child object reached from `work+0x8C`:

```text
work+0x8C -> resource handle
handle+0x08 -> child object
```

The relevant control flow is:

1. Call `0x0025A274(child)`; if `r0 == 0`, branch to help at `0x001EA12C`.
2. Otherwise call `0x002D569C(child)`; if `r0 == 0`, branch to help.
3. If both return nonzero, read `work+0x94` as a byte. Nonzero branches
   directly to help (`0x001EA010`). Zero enters the transition block at
   `0x001EA070`.
4. That block mutates the `+0x8C` and `+0x90` resource handles/objects, stores
   byte `1` to `work+0x94` at `0x001EA128`, then falls through to help.

Thus the direct route to the help-window entry does **not** require both
readiness predicates to be true: either predicate returning zero also reaches
the help window. The nonzero path through both predicates is the one gated by
`work+0x94`.

`work+0x94` is initialized to zero by the title constructor at `0x001EB0E4`.
Within this callback, `0x001E9F6C` reads it to choose which resource side is
updated when `work+0x96` is nonzero and preview-ready; in the present window it
selects direct fallthrough versus the `+0x8C`/`+0x90` transition. The latter
sets it to one only at the end. This supports a one-way transition-flag
interpretation for this path, but does not establish a global invariant or
that it is always exactly 0/1 under every callback state.

## Readiness helper contracts (observed instructions)

`0x0025A274` (`src/engine/leaf_batch16_a.cpp`) is 72 bytes. Despite the
existing callback declaration name `UiModel_IsVisible`, the instructions
implement a compound predicate, not a simple visibility-byte read:

- Load signed word `child+0x34`; `<= 0` returns `1` immediately.
- Else load `child+0x4C`; null returns `1`.
- Else test bit 0 of the word at `child`; set returns `0`.
- Otherwise compare floats at `[child+0x4C]+0x38` and `+0x48`; less-than
  returns `0`, otherwise `1`.

The float compare also inherits ARM/VFP unordered-condition behavior; a normal
finite-number interpretation should not be extended to NaNs without a test.
The direct fast path `child+0x34 <= 0` avoids every read after that field.

`0x002D569C` (`src/engine/leaf_batch16_c.cpp`) is a 96-byte predicate:

- Signed `child+0x58 <= 0` returns `1` immediately.
- Otherwise follow `child+0x2C`; if its `+0x148` word is zero, return `1`.
- Else use fields `+0x28` and `+0x14C` to index a pointer table described by
  `[nested+0x28]` (stride) and `[nested+0x1C]` (base). A null selected entry
  returns `1`.
- For a nonnull selected record, compare its floats at `+0x48` and `+0x38`;
  the helper clears the return value on the ARM `HI` condition, otherwise the
  nonzero record pointer remains in `r0`.

No stores are present in either readiness body. Their names in the callback
declaration (`IsVisible`/`IsReady`) are labels, not proof of user-facing
visibility or asset-loading semantics. The one directly reusable minimal
contract for the second helper is its early return on signed `child+0x58 <= 0`.

## Transition mutations and helper call ABI

The transition block begins at `0x001EA070` and ends with
`strb r7,[r4,#0x94]` at `0x001EA128`. Static memory/call effects:

- Resource handle at `work+0x8C`: handle word `+0` has bit `4` set if clear,
  its child object's `+0x74` receives live VFP `s16`, then `0x0029BDB4` is
  called. Handle bit `2` is set; the byte at
  `child+0x2C+0x1F6` is cleared; `work+0x98` receives `s16`.
- Resource handle at `work+0x90`: call `0x002872A4(child)` with `s0=s16`, then
  call `0x0020FFA0(child)` also with `s0=s16`. Handle bit `2` is cleared and
  `child+0x2C+0x1F6` is set. If handle bit `4` is set, it is cleared, child
  `+0x74` receives live `s17`, and `0x0029BDB4` is called.
- Finally `work+0x94` becomes 1. Conditional flag-bit branches determine
  whether the two `0x0029BDB4` calls occur. The word at handle `+0` is read and
  written; the target byte is in the nested object, not the handle.

`0x0029BDB4` is represented by exact instructions in
`src/engine/leaf_batch15_b.cpp`. At these call sites `r0` is the child object
and `s0` is the float. It always stores `s0` to child `+0x78`; if signed
`child+0x34 > 0`, it loads child `+0x74`, multiplies by `s0`, and stores the
product to `[child+0x4C]+0x40` when that pointer is nonnull. This raw ABI is
more specific than the source declaration `UiModel_ApplyAlpha(f32)`.

Important entry/continuation caveat: `0x002872A4` and `0x0020FFA0` each begin
with a conditional early-return sequence, then **fall through in the ROM** to
their adjacent helper bodies when their gate is positive. The 12-byte exact
wrappers in `leaf_batch38_a.cpp` are not the full positive-gate behavior.

- `0x002872A4`: read signed child `+0x34`; `<=0` returns. Otherwise execution
  falls through at `0x002872B0` into the preserved 80-byte body
  `func_002872b0` (`leaf_batch16_c.cpp`). It reads child `+0x4C`; when nonnull,
  loads a callback pointer from nested `+0x4C`, accesses additional nested
  floats/fields (`+0x38`, `+0x3C`, `+0x44`, `+0x48`, `+0x50`, `+0x58`), uses
  `s0` in a VFP comparison/min-like selection, performs `BLX r1`, stores
  callback results/state, sets nested byte `+0x58`, then returns. This is not
  established as a pure “reset fade” operation by the prefix alone.
- `0x0020FFA0`: read signed child `+0x58`; `<=0` returns. Otherwise execution
  falls through at `0x0020FFAC` into the preserved 132-byte body
  `func_0020ffac` (`leaf_batch41_b.cpp`). It follows child `+0x2C`, checks
  `+0x148`, looks up a selected record from `+0x28`/`+0x14C`, uses VFP state
  and record fields, makes an indirect `BLX`, stores record `+0x38/+0x3C`,
  and sets record byte `+0x58`. It is not a scalar parameter setter on the
  positive-gate route.

The 12-byte prefixes and adjacent full bodies are already preserved as exact
ARM source partitions, so a runner can execute the original code. Reusing
only the prefix declarations as candidate stubs would be unsound for positive
`+0x34` / `+0x58` values. The body at `0x0020FFAC` is exactly the continuation
of the called entry; preserve that contiguous ROM code or call the complete
body with the proper return behavior. The dynamic `BLX` callees still need
valid function pointers and state, or explicit, call-counted stubs in an
isolated harness.

## Minimal defensible route to the help fallthrough

For a narrow control-flow test stopping at `0x001EA12C`, the smallest
instruction-backed route is:

- Valid, mapped `r4` title work; nonnull `work+0x8C` handle; nonnull child at
  `handle+8`.
- Child signed word `+0x34 = 0` so `0x0025A274` returns 1 after one field read.
- Child signed word `+0x58 = 0` so `0x002D569C` returns 1 after one field read.
- `work+0x94 = 1` so the branch at `0x001EA010` goes directly to
  `0x001EA12C`.

This route executes both original helper bodies and both branches, but does
not need child `+0`, `+0x4C`, `+0x2C`, nested records, VFP comparisons, or the
`work+0x90` resource. It is a synthetic branch-coverage setup, not evidence
that a real title state has those values. It can verify reachability and the
minimal reads without claiming transition mutations or help presentation.

To cover the mutation path instead, use `work+0x94=0` and both helper returns
nonzero, then provide valid `+0x8C` and `+0x90` handles; writable child fields
`+0x74/+0x78`; and valid nested pointers at `child+0x2C` for the `+0x1F6`
byte writes. Even if the two fade entries take their early returns, those
handle/child/subobject accesses remain required. To keep both 0x29BDB4 calls
out of this synthetic minimal mutation route, handle `+0` bit 4 must already
be set for `+0x8C` and clear for `+0x90`; otherwise model their writes and
child state. This configuration exercises one path only and does not claim
that the flags match normal runtime state.

## Evidence classes and unknowns

**Observed statically:** code bytes, conditional branches, memory offsets,
VFP operations, direct call destinations, nested pointer dereferences, direct
flag/byte/float writes, and two conditional indirect calls described above.
These observations are reproducible from the pinned `code.bin` and exact
source partitions.

**Inferred:** `work+0x94` gates a resource transition; handle bits 2 and 4 and
the nested `+0x1F6` byte participate in a visual/fade state exchange. This is
based on use patterns, not a verified renderer-level contract. Names such as
“visible”, “ready”, “fade”, and “reset” remain provisional semantic labels.

**Unknown:** real values and invariants of `work+0x94`, `child+0x34/+0x58`,
`s16/s17`, and handle bits on live execution; whether helpers' indirect
callbacks are reached on the normal title path; indirect callee behavior;
exact rendering/timing consequences; and the visible UI result. No static
caller scan or harness in this audit establishes these. A full-path test must
retain FP state and the correct object graph, and should first trace the
original ARM continuously through the help-window entry before substituting
any helper or composing a C++ candidate.
