# Independent review: `UiTouch_GetRegionTouchState` (`0x0029D8FC`)

## Review decision

The production-source implementation is boundedly acceptable as a typed reconstruction of the pinned getter for an initialized, addressable touch manager and the signed-handle ABI established by H2 callers. The compiled production body is relocation-free and byte-identical to the candidate body exercised by the differential. The differential passes 589,824 calls over every signed-16 handle for nine selected active indices, and the wrong-index control is detected.

This is source-level evidence only. The compiled body is 44 bytes while the original function span is 40 bytes; the ledger is `non_matching`, and the helper has not been placed into the H2 code.bin/IPS image. The result does not establish touch-event meaning, callback ordering, H2 UI behavior, or runtime equivalence. The state-byte matrix also has a small matching-path gap noted below.

## Pinned behavior and signed ABI

The pinned image identity is US v0.1.0 `code.bin`, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Decoding the 40-byte ledger span at `0x0029D8FC` gives the executed sequence:

```asm
ldr   r1, [pc, #0x18]       ; literal 0x0043DCB0, IfTouchGlobal
ldr   r2, [pc, #0x18]       ; literal 0x0000064E
ldr   r1, [r1, #4]          ; IfTouchGlobal.work_ptr (0x0043DCB4)
ldrsh r2, [r2, r1]          ; signed halfword manager+0x64E
cmp   r2, r0
ldrbeq r0, [r1, #8]         ; raw state byte, zero-extended
movne r0, #0
bx    lr
```

The `IfTouchWork` declaration places `active_panel_id` at `+0x64E`; `IfTouch_Init` allocates the `0x680`-byte manager and initializes this field to `-1`. The helper itself has no null check, so its precondition is an initialized global manager pointer with readable fields at `+0x64E` and `+0x08`. It performs no guest-memory writes. The matched byte is returned unsigned in `r0`, widened to `s32`; mismatch returns zero.

The H2 `TitleConfig_Calc` caller sites found in the pinned ARM scan are `0x001EAAA4`, `0x001EAB60`, `0x001EAB98`, `0x001EAC5C`, and `0x001EAE40`. Each site has a preceding `LDRSH` into `r0` from its handle field (`work+0x1C`, `+0x1E`, `+0x20`, `+0x22`, or a loop-selected halfword) before the call. This establishes sign-extended negative sentinels such as `-1` at the actual H2 call boundary; the first harness attempt's zero-extended `0x0000FFFF` was not the production ABI and its mismatch was correctly treated as a fixture error. The fresh report followed the correction and tests all signed values as `handle & 0xFFFFFFFF`.

## Typed source and object identity

The production definition in `src/engine/leaf_batch23_b.cpp` is:

```cpp
extern "C" s32 ui_func_0029d8fc(s16 handle)
```

It reads the manager pointer at `0x0043DCB4`, loads manager `+0x64E` through `volatile s16*`, returns zero on inequality, and loads `+0x08` through `volatile u8*` on equality. This preserves the original signed comparison and unsigned state-byte result for the intended target ABI. Candidate source is `experiments/semantic_equivalence/h2_touch_state_candidate.cpp`.

Identities independently recomputed from the existing package:

- Production TU source SHA-256: `aab4ddc85e79e0a6695de2ece14992ae6b318237c5cc91bb5bb6cc933bba8e10`.
- Candidate source SHA-256: `e0eb7ce75061dfe6ba8c2dcc982ec6e7da74fb71a1fb07f8f24c683943540ddf`.
- Production object SHA-256: `afd795b4019a8d56147b3d83076a2e47b53306afe726366c080ce20ff4defe7d`.
- Differential candidate object SHA-256: `40d8922324587c13ba21c57e372d725ec4a3d997b4b7e66086477a51cc3965c7`.
- Both extracted functions are 44 bytes, relocation-free, and byte-identical to each other; body SHA-256 is `93009b8cb88b1571215f7f7a3f8fec53b6afcf49a1e3710b87e7d45713a1667b`.
- Differential report file SHA-256: `70cf3f0680bfb5161b353a1f520e511937a17ed2015d09f73e38b834cff648e2`.

The 44-byte body exceeds the pinned 40-byte span, so this C++ body cannot simply replace the function in place. The source integration did not change `code.bin` or create an IPS patch for this helper. The truthful ledger row is `non_matching` for the source reconstruction; this is not code-image integration evidence.

## Differential matrix and sensitivity

The report claims `status: passed`, `cases: 589824`, no first mismatch, and no writes from either execution. It tests all 65,536 signed-16 handle bit patterns against each of nine active-index values `(-32768, -1, 0, 1, 9, 10, 11, 12, 32767)`. Five raw state values `(0, 1, 2, 6, 255)` are loaded into the manager byte. For each call, the reference is pinned ARM and the candidate body is the compiled C++ blob. The runner checks faults, return value, PC, SP, `r4-r11` preservation, and guest writes. The machine setup installs a valid manager pointer and mapped manager memory, so it validates initialized-manager behavior only.

The wrong-index mutant ignores `active_panel_id`. On the directed sensitivity case active `10`, handle `11`, state `6`, original returns `0` and mutant returns `6`; the report records `negative_control.detected: true`. This is a suitable control for omission of the equality test.

Coverage qualification: the state byte is selected as `STATE_VALUES[(handle + 32768) % 5]`, independent of active index. Because active values are only the listed nine, matching-handle cases exercise returned bytes `{0, 2, 6, 255}`; state `1` is present in the matrix only on nonmatching cases and is never returned by the equality branch. Also, only five of the byte's 256 possible values are sampled. The source and compiled body directly return any `u8`, so this gap does not contradict the body, but the report should not be described as having demonstrated every raw state value on the match path or the full byte domain. A small directed follow-up can set a matching handle with state `1`; exhaustive byte coverage would require all 256 matching states.

The focused test file checks the matrix size and chosen boundary/index/state sets, verifies expected signed examples, confirms mutant sensitivity at the comparator level, and checks the comparison helper's fault/callee-saved cases. I inspected it but did not run it. The production integration report records that 6/6 focused tests and the differential command passed; this reviewer did not rerun them.

## Evidence boundary and follow-up

Accept this as a bounded helper-source reconstruction for a valid initialized manager, signed `s16` handle inputs, and the tested active-index/state sample. Preserve explicit limits:

- Manager allocation success, pointer validity/lifetime, and runtime initialization order are preconditions. The null-manager case is not guarded or validated.
- The active index's event meaning, the byte at `+0x08`, physical input mapping, callback cadence/order relative to H2 Calc, and relation to H2 registered regions are unresolved.
- The test uses nine selected active indices and five sampled state bytes, not every active manager state or all 256 byte values; matching-path state `1` is missing.
- The 44-byte production function does not fit the original 40-byte span. No code.bin patch/IPS replacement for this helper was made, so runtime calls still execute the original image body.
- Passing this helper differential does not establish H2 navigation, visible UI, cancel/confirm, persistence, restart, or Azahar runtime acceptance.

Next, optionally add a matching-handle state-1 directed case (and all 256 state bytes if the full raw-byte domain is to be claimed), then have the integrator decide whether to provide reviewed code placement for the 44-byte source body. Keep user-visible/runtime acceptance separate and blocked on the unresolved producer timing and input/event meanings.
