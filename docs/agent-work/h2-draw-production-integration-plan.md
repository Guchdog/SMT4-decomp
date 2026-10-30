# H2 `TitleConfig_Draw` production integration plan

## Recommendation and current gate

Keep the Draw implementation experimental until the combined Calc+Draw patch
has a reviewed executable placement for both bodies. The isolated Draw
candidate is behaviorally reviewed after its unsigned TBB correction, but its
current synthetic-injection test is not a final-address patch test. More
decisively, the only currently audited executable cave is already occupied by
the production-source Calc body and is too small for both callbacks.

Promote the implementation in place in
`src/engine/leaf_batch43_a.cpp`, replacing only the naked inline-assembly body
for `ui_func_002cafd0` at `0x002CAFD0`. Keep the CSV symbol and TU mapping. Use
the readable candidate as the starting point, preserve original helper calls,
and confirm the callback's C ABI return contract against the task factory before
settling the source declaration: the current production header declares
`void TitleConfig_Draw(void*)`, while the isolated candidate returns `u32`
to preserve the observed normal-return `r0=0`. Do not silently change the
callback type or introduce a second symbol at the same guest address.

## Source, object, and helper facts

- The production wrapper is `ui_func_002cafd0` in the `leaf_batch43_a.cpp`
  batch, presently a naked function containing original `.hword` bytes. Its
  ledger row is
  `0x002cafd0,1932,matching,ui,ui_func_002cafd0,src/engine/leaf_batch43_a.cpp`.
  The original span is `[0x002CAFD0, 0x002CB75C)`.
- The reviewed source is `experiments/semantic_equivalence/h2_draw_candidate.cpp`
  (`bef32aa76f533cb15d1372b9e4eace6b7a2c4dbfd7d95bd57877ab0f130fcc6e`). Its
  corrected table guard is `static_cast<u32>(absolute_index) < 3u`, matching
  ARM `cmp r7,#3; bhs` for negative and `>=3` values.
- The reviewed isolated object is
  `000b4855164bfa7c8775ab32a4a02b936e9c878435c29f0ab8d95ebcffc9b9c2` and its
  extracted callback is 2,252 bytes. The test runner reports no applied
  relocations; inspection of the saved ELF symbol also found no relocations.
  That is true of this candidate object only. Compile and inspect the
  production TU's extracted symbol before assuming its relocation set is the
  same.
- The candidate calls the cursor, panel/sprite, layout, TBB, formatter/font,
  render-value, and touch helpers at their original absolute addresses. Its
  renderer-cache path reads the original render root/cache and conditionally
  invokes the original indirect callback. Keep these as original dependencies
  in the first production slice. Verify AAPCS register/stack arguments and
  hard-float VFP arguments in the production-object/final-address differential;
  the isolated harness already compares ordered helper arguments and
  `r4-r11`, SP, and `d8-d15` for its mock boundaries.
- The signedness-review report
  (`40106e77c35d57230573b787e80f6cac089c814e5493f62d324e1cda96e2471a`)
  records 46/46 isolated cases, with explicit absolute indices `-1` and `3`,
  and a detected wrong-TBB-stride negative control. The earlier 44-case run is
  superseded on signedness by this 46-case report. These callback cases use
  controlled cursor/layout/TBB/render/touch helpers and do not establish
  caller reachability, visible labels, or real resource behavior.

## Combined patch and placement constraint

The pinned image has `.text` at VMA `0x00100000`, size `0x002FE624`, ending at
`0x003FE624`; its page-aligned end is `0x003FF000`. The existing Calc patch
builder identifies only the `0x003FE624..0x00400000` zero-padding cave, with
capacity 2,524 (`0x9DC`) bytes. The production-source Calc integration report
uses 2,096 bytes there, leaving 428 bytes. Its current original/patched image
hashes are respectively
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` and
`c9ebf62679043512c22c684b50f9e9cbf1fe824e016f119c2de4bddf664eb45d`; the
production object is `94197ad141393099a25e679b73457f127c54c7155fa4d8c2ff25270f8ca620fd`.
That Calc body has four audited local `R_ARM_ABS32` jump-table references.

The combined callback bodies total `2,096 + 2,252 = 4,348` bytes, which
exceeds the known cave by 1,824 bytes before any cave alignment allowance. A
second call to `tools/h2_calc_code_patch.py` cannot solve this: that builder
assumes the original pinned image, one Calc entry, and the one zero cave. It
would overwrite the first body or reject the already-populated cave. The
reviewed Draw runner instead executes its candidate at synthetic VMA
`0x01000000`; its 46-case result does not establish a Draw branch/cave in the
guest image. A read-only scan found no all-zero run of 64 bytes or more inside
the actual `.text` bytes outside the page-tail cave. Do not infer executable
permission or ownership for spare `.rodata`, `.data`, or `.bss` bytes. In
particular, `.data` page tail has a nominal 2,492 bytes but is not an audited
executable region.

Therefore the immediate missing support is a second *verified executable*
placement plus a combined patch builder/manifest. A placement audit must prove
the bytes are unused, executable in the target's segment permissions, large
enough for the extracted Draw body, within ARM branch reach, and safe from
literal/table/data ownership and interior-entry callers. If no such placement
exists, stop promotion and ask the integrator to choose another supported code
placement strategy; do not truncate, overlap Calc, overwrite the next function,
or treat raw zero bytes in a non-text segment as an executable cave.

## Bounded promotion and evidence sequence

1. After the placement gate is resolved, replace the existing production
   wrapper body in place and compile
   `src/engine/leaf_batch43_a.cpp` with `build_check.py` into a fresh private
   output using one job. Extract `ui_func_002cafd0` from that exact object and
   record its symbol size, source/object hashes, and every relocation. The
   prior 2,252-byte standalone object is a sizing hint only. Keep helper
   prototypes local unless a shared interface change is separately assigned;
   reconcile the header return declaration before claiming ABI closure.
2. Extend a task-local or coordinator-owned patch builder to create one image
   from the pinned original with **both** replacements. It must reserve
   disjoint final VMA ranges for Calc and Draw, branch each original entry to
   its assigned body, rebase only explicitly supported local relocations,
   reject external/unexpected relocations, check capacity/overlap/branch range,
   and verify that independent IPS application reproduces the exact image
   tested. Verify no supported references branch into either overwritten
   original body. Record one manifest containing both entries, placements,
   object/source hashes, relocation maps, patch records, and complete image/IPS
   hashes. Preserve the pinned original bytes.
3. Adapt the Draw differential to call the production-extracted symbol at its
   actual guest VMA in the combined image. Run the reviewed 46 directed cases,
   including `-1`, `3`, cache-dirty/matching and touch `1/2/6` branches, and
   retain the wrong-stride negative control. Compare return/fault/PC, work,
   config, render-cache bytes, ordered helper/callback traces, and callee-saved
   ABI state. The existing synthetic-injection report is prior isolated
   evidence, not a substitute for this placement test.
4. On that same combined image, rerun the current production-source Calc
   sequence differential (seeds 7 and 20261024; 16 sequences/54 ticks and the
   wrong-logical-map control). Then add a bounded caller-composition test that
   starts from the original title initializer's task registration tuple and
   invokes/schedules the Draw callback with initialized work/resource/cache
   fixtures while keeping Calc frozen. Assert the registered Calc and Draw
   addresses, shared work context and observed callback order, but label mocked
   service behavior as HLE. The existing offline initializer composition
   proves registration forwarding/readiness/reset only; it does not schedule
   or execute Draw.
5. Run `py_compile` and the focused Draw/Calc/caller tests. The coordinator
   owns the affected wider build after source freeze. Run `asm_diff.py
   --addr 0x002cafd0` only as an exact-byte diagnostic; a readable C++ body is
   expected to differ. Record that mismatch truthfully and do not weaken the
   exact checker.
6. Only after independent review and supported combined-image evidence, change
   the Draw CSV status from `matching` to `non_matching`; preserve its original
   address, original size `1932`, symbol, category, and TU mapping. Update
   `docs/function-records/0x002cafd0.md` with the promoted source/object,
   combined image/IPS, cave and relocation map, cases and controls, caller
   scope, original helper dependencies, and remaining limits. Do not claim
   matching bytes or whole-title equivalence.
7. Treat visible menu behavior and runtime as later acceptance. The current
   H2 milestones still lack a defined original-versus-patched Draw runtime
   scenario and real renderer/resource services. Any Azahar/GDB/CLI comparison
   needs its own explicit owner and same-state original/combined profile; this
   plan uses no emulator, RSP, profile, or host input.

## Evidence boundary

The source-level candidate and reviewed isolated differential support the Draw
callback only under the declared helper fixtures. Calc now has production-TU
object and final-address persistent-sequence evidence, but its current patch
uses the sole audited cave. There is no combined Calc+Draw image, production
Draw TU build, caller-executed Draw sequence, or runtime comparison in this
plan. The cave/permission discovery and combined patch-builder extension are
prerequisites, not completed integration.
