# Independent review: H2 Calc production-source integration

## Review result and recommendation

The production `TitleConfig_Calc` body is bounded to the ledgered
`script_vm_func_001ea928` implementation, with the header's callback return
type updated to `s32`. The production TU object, extracted symbol, final-address
patch, both 68-case runs, persistent two-seed sequences, initializer-composition
report, and byte diagnostic have consistent frozen identities. I found no
counterexample in the supplied offline evidence. The original helper calls
remain dependencies, and the runtime-facing evidence is still partial.

**Recommendation:** accept the Calc source as a semantically supported,
non-byte-identical function replacement under the exercised callback/HLE
contracts, and classify its ledger row `non_matching` before batch closure. Do
not mark H2 complete or claim visible editing, persistence, or runtime parity.
The current `config/functions.csv` row still says `matching`, while
`asm_diff.py` reports a byte mismatch; that classification is stale under the
project's exact-label rule and needs an integrator-owned update. Keep the
original address, original size, symbol, category, and source path in the row.

## Source, interface, and helper contract

- `git diff` shows the production implementation change in one contiguous
  replacement of the original inline-ARM body at `0x001EA928`; no other
  `DECOMP_FUNC` definition in `src/engine/leaf_batch46_b.cpp` changed. The
  `include/camp/title_flow.h` diff changes the `TitleConfig_Calc` return
  declaration from `void` to `s32` and updates the config-byte comment. The
  CSV itself has not yet changed.
- The candidate/production callback ignores incoming `r0` and reads work and
  config from their fixed globals, matching the pinned callback's use. The
  original returns `r0=0` on common paths and `r0=0xffffffff` (`-1`) for state
  4. The production `s32` return preserves that observed behavior, and the
  differential covers the terminal state. The original title constructor
  registers the callback as a literal address; the supplied evidence does not
  show that the task factory consumes the return value. Also, the header's
  namespaced C++ declaration `smt4::camp::TitleConfig_Calc` is not the same
  linker symbol as the global `extern "C" script_vm_func_001ea928`; the
  constructor's address registration avoids a mismatch in this path, but the
  declaration should not be presented as a factory-verified typed callback
  binding.
- `TitleConfigWork` remains the established `0x158` layout with its offset/size
  assertions. The production code keeps the three map helpers and four encoder
  helpers at their original addresses, along with cursor, touch, script/task,
  render, audio, animation, resource and state-decision services. It does not
  silently fold those helpers into the callback implementation. The typed
  function-pointer adapter is compiled for ARMv6K hard-float; the two-float
  effect call is explicitly typed with `float` arguments. This is target-ABI
  evidence, not a contract for those helpers' internal behavior.

## Production object, relocations, cave, and patch identity

I inspected the frozen production object without compiling. The object at
`checks/final-seed-7-20261026/leaf_batch46_b.o` is 170,296 bytes with SHA-256
`94197ad141393099a25e679b73457f127c54c7155fa4d8c2ff25270f8ca620fd`. Extracting
`script_vm_func_001ea928` reproduces section offset `0x184c4` and symbol size
2,096 bytes. The normalized body SHA-256 is
`289279cf481db93fedb740a020683d8c44be6f5fc2c283b15aee72e4a1bab20c`.

The extracted object carries four symbol-less `R_ARM_ABS32` relocations at
body offsets 60, 64, 68, and 72. Their raw translation-unit section addends
`0x18510`, `0x18684`, `0x18630`, and `0x18668` normalize by subtracting the
symbol section offset to body-local offsets `0x4c`, `0x1c0`, `0x16c`, and
`0x1a4`. Rebasing at cave VMA `0x003FE624` yields
`0x003FE670`, `0x003FE7E4`, `0x003FE790`, and `0x003FE7C8`, all within the
2,096-byte body. The builder rejects unsupported types/symbols, explicit
addends, duplicate/out-of-body references, and any count other than four.
Patch-builder unit tests cover TU-to-function normalization, out-of-function
references, unsupported relocation types, bad cave references, occupied cave
bytes, wrong image identity, and IPS round-trip.

The reviewed `.text` ends at `0x003FE624`; page padding gives a 2,524-byte
(`0x9DC`) cave. The 2,096-byte body leaves 428 bytes. The branch at
`0x001EA928` is `3d4f08ea` and targets `0x003FE624`. The original image hash is
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; the
patched image hash is
`c9ebf62679043512c22c684b50f9e9cbf1fe824e016f119c2de4bddf664eb45d`; IPS hash
is `0b671f4f40c172984e730d0387899ce47abe8f2ee5e90043a2e481aa591cf781`. I
independently reapplied the frozen `code.ips` to the pinned original image and
got the reported patched hash. The patch records change the four-byte entry
and cave body; the original `code.bin` is not changed.

The wrong-branch final-address control (branch to cave plus four) fails to
reach the return sentinel in both seed reports. This exercises the entry
redirect, not a separate mutated execution for each relocation. I also found no
complete supported mid-body-entry audit in the supplied integration packet;
because an entry-only patch leaves the remainder of the original body in place,
verify that no supported caller enters the old body after its first word before
shipping a runtime patch.

## Differential, sequence, caller, and byte evidence

- Production final-address differential, seed 7: 68/68 cases passed; report
  SHA-256 `6ca0d9b0c33a5ce1a08a560920b1888420476bc74c3330ebb00ff616d4857a14`.
- Production final-address differential, seed 20261024: 68/68 passed; report
  SHA-256 `5c4cc3eff11684d8d167e6dc9b1c7cf45a6811cd5feab21d86a56ba46eebf6d0`.
  Both reports use the same production source hash, object hash, original image,
  and patched image; each detects the wrong-branch target control.
- Production persistent run: 16/16 sequences and 54/54 ticks passed across
  seeds 7 and 20261024. Report SHA-256
  `b9cb49c8f93bb0c2a72f7c449aa9c3ff47c3efe975f59913cb46ba5d5d946d81`. It
  includes the repeated decrement at zero, increment at ten, State-0 wait and
  ready, State-2 result values 0..3, State-3 readiness, and a detected wrong
  logical-map control.
- Initializer caller composition: 3/3 cases passed with the exact production
  Calc-patched image; report SHA-256
  `144119150c1c6fbfbb57add4a67a017265088599e58d68b7d67143937718e8b8`. Its
  wrong-Calc-callback address control is detected. This test checks registration,
  readiness and reset boundaries; it does **not** schedule or execute Calc.
- The recorded focused suite reports 22 tests passed. I inspected the
  production patch tests, including relocation normalization/rejection and IPS
  preservation/round-trip cases, but did not rerun tests or compile.
- `asm_diff.py --addr 0x001ea928` exits 1 as expected: original 1,796 bytes vs
  compiled 2,096 bytes, 10.91% byte match and 7.39% mnemonic match. This is
  useful diagnostic evidence and not a semantic rejection. It does mean the
  current CSV `matching` status must be corrected before integration closure.

## Functional limits and closure advice

The Calc differential uses shared deterministic service outcomes; cursor,
touch, resource, task/script, rendering, sound/audio, animation, and
state-decision helper internals are not validated. The logical `(id,mode)`
responses are harness controls, not physical input or button mapping. The
initializer runner tests callback registration and readiness but does not run
Calc through the title scheduler. No visible screen/UI test, changed-option
cancel-versus-other-exit comparison, re-entry test, save/profile observation,
or clean restart persistence test is present. The meaning of State-2 results
and the special bounded-helper return domain remain unresolved. No Azahar,
emulator, RSP, keyboard, or mouse interaction occurred.

Before final source/ledger closure, the integrator should update the function
row to `non_matching`, record the production source/object/patch identities and
tested domain in the function record, and verify supported entry references do
not target the old body interior. Keep H2's milestone status open until the
specified original-vs-patched edit/exit/re-entry and persistence/runtime cases
are compared on matched disposable profiles. This review itself was read-only;
it did not edit the source, header, ledger, or frozen reports.
