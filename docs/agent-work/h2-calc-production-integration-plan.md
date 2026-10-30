# H2 `TitleConfig_Calc` source-integration plan

## Recommendation

Promote the reviewed Calc logic as one readable implementation at its existing
production ledger entry, while retaining the original helper bodies as explicit
dependencies. Keep the implementation in
`src/engine/leaf_batch46_b.cpp` at the present
`script_vm_func_001ea928` definition. Replace only that function's `.hword`
assembly body and its `naked` attribute; leave the other batch functions and
their byte-identical wrappers alone. Preserving this symbol and TU keeps the
ledger extractor and surrounding compile target stable.

Before editing, reconcile the callback declaration in
`include/camp/title_flow.h`: it currently says
`void TitleConfig_Calc(void* arg)`, while the reviewed body returns an `s32`
(`0` on common/state-0..3 paths and `-1` for state 4). Confirm the callback
factory contract, then use one consistent C ABI declaration and implementation
type. The existing `script_vm_func_001ea928` entry is global C linkage; the
header API is in `smt4::camp`. Do not create a second out-of-line shim at the
same address or change the CSV symbol without an explicit symbol/patcher plan.
The old declaration has no other source call sites, but it is still an
interface/ABI discrepancy to resolve, not silently preserve.

Use `smt4::camp::TitleConfigWork` and its existing layout assertions as the
source of workspace offsets. The type already asserts size `0x158`, cursor at
`+0xE8`, script table pointers at `+0x14C/+0x150`, and the established work
fields. The last word is currently named `pad_154[4]`, although the Calc body
reads/writes it as a script result; name that field from the reviewed contract
if the shared interface owner accepts the field meaning. The `g_TitleConfigWork`
declaration is a pointer global at `0x0044E2D0`; config bytes are at
`0x0044E0F8` but are only declared as an incomplete extern array in the header.
Prefer typed workspace access while retaining explicit fixed-address access for
globals until their placement/linkage contract is verified. Keep the three
config mappers, four byte encoders, cursor/touch/script/task/render/audio and
state-decision functions as their existing original dependencies.

The candidate currently uses a typed `call<Result, Args...>(address, ...)`
adapter for absolute helper addresses. A production version must preserve each
consumed argument width/sign, return type, and the hard-float AAPCS behavior
(notably the effect-play call with two `float` arguments). Keep it local to the
Calc implementation unless a separately reviewed shared helper interface is
needed. Integer-to-function-pointer conversion is implementation-defined C++;
accept it only as an explicit ARMv6K Clang target assumption and test emitted
relocations/calls. Never change helper return types to `void` just because a
result is usually ignored. The existing build uses
`--target=armv6k-none-eabihf -mcpu=mpcore -mfpu=vfpv2 -mfloat-abi=hard -O2
-std=c++20 -ffreestanding -fno-exceptions -fno-rtti -nostdinc -nostdinc++`.

## Entry, size, and patch consequences

The original function starts at `0x001EA928`, is ARM state, and spans 1,796
bytes through `0x001EB02C`; its CSV row currently reads
`0x001ea928,1796,matching,script_vm,script_vm_func_001ea928,src/engine/leaf_batch46_b.cpp`.
The reviewed candidate body is 2,096 bytes. The experimental code-cave patch
branches the entry to VMA `0x003FE624`, the start of 2,524 bytes of zero text
padding, leaving 428 bytes. The patch writes the four-byte entry branch and
candidate body; its builder rebases four local absolute jump-table references.
The reviewed candidate's patched-image hash is
`c9ebf62679043512c22c684b50f9e9cbf1fe824e016f119c2de4bddf664eb45d`.

Those measurements are for the experimental candidate, not a guarantee about
the production TU's emitted body. A final patch must compile and extract the
production `script_vm_func_001ea928` symbol, check its size against the cave,
reject unsupported/external relocations, rebase any audited local table
references, and independently verify that the IPS reconstructs the exact image
that the differential ran. Do not reuse the old candidate-source patch hash as
the production artifact identity. Keep `code.bin` intact. An entry branch also
does not redirect any caller that branches into the middle of the original
1,796-byte body; verify there are no such supported entry references before
relying on the cave patch.

`asm_diff.py --addr 0x001ea928` compiles the translation unit selected by the
CSV row, extracts the named symbol, and compares it with the original bytes.
After a readable C++ promotion, an exact mismatch and nonzero CLI exit are
expected diagnostic evidence. It is not a semantic rejection criterion. The
function row's `size` remains the original 1,796-byte size; `src_file` and
symbol should stay unchanged if implementation remains in-place.

## Small reproducible promotion sequence

1. Freeze the reviewed inputs and prepare a coordinator-owned production
   integration packet. Replace only the Calc wrapper; apply the approved return
   type/interface update and typed `TitleConfigWork` field naming in the shared
   header if the ABI audit requires it. Keep the experimental candidate and its
   old reports as history, not as the acceptance source.
2. Compile only the affected TU to a fresh private object with one job, for
   example:

   ```powershell
   python tools/build_check.py --repo-root . --tu src/engine/leaf_batch46_b.cpp `
     --out-dir build/agent-work/H2-semantic/h2-calc-production-integration/obj `
     --jobs 1 --force
   ```

   This establishes that the source TU compiles; it does not link a replacement
   image or prove behavior. If the shared callback/workspace ABI changes, also
   compile each affected consumer TU and perform the repository's one
   integrator-owned batch build after worker compiles have stopped.
3. Extract the production symbol from that exact object and add a
   production-source mode to the task-local patch/differential wrapper (or a
   coordinator-owned small wrapper) so it calls the existing audited patch
   builder with the production bytes. Record the production source, object,
   original image, IPS and patched image hashes. Fail closed on unexpected
   symbol size, external relocations, cave overlap/capacity or image drift.
4. Run the production-extracted final-address Calc sequence differential for
   seeds 7 and 20261024, including state-0 wait/ready, state-1 no-op/logical
   decrement/increment and both clamp bounds, state-1 to states 2/3, pending
   script polling, all state-2 decision values, state-3 readiness, and the
   wrong-logical-map control. Run its focused tests and `py_compile`. Separately
   rerun the existing State-9/10 initializer composition on the same
   production-derived patch to confirm its exact registered Calc address and
   no regression in readiness/reset. The current offline caller report does not
   schedule Calc; it proves initializer registration only.
5. Run `asm_diff.py --addr 0x001ea928` as a byte diagnostic and record its
   expected nonmatch without weakening it. Run the affected production-TU build
   and the relevant focused callers/tests; the coordinator owns the wider
   batch regression once, after sources are frozen. Do not run the bulk/full
   build separately for each worker.
6. On integration acceptance, change only this CSV row's status from
   `matching` to the supported `non_matching` classification, keeping the
   original address, size, symbol, category and source path truthful. Update
   `docs/function-records/0x001ea928.md` with the promoted source/object/patch
   hashes, tested domains, exact sequence counts and remaining dependencies.
   Do not label differing source bytes `matching`. Keep semantic behavior
   evidence separate from ledger byte identity.
7. Treat runtime as a later, separately owned acceptance layer. The current
   evidence is offline callback behavior under HLE controls; it does not establish
   actual service behavior, title scheduler composition for Calc, visible
   editing, persistence, profile state, or Azahar behavior. A later runtime
   packet must use an explicitly defined original-versus-patched CLI/GDB
   scenario and disposable matched profiles. This plan itself performs no
   runtime/input operation.

## Current evidence boundary

The current candidate has reviewed ARM callback and final-address differential
evidence, plus persistent offline callback sequences: the latest lower-bound
follow-up reports 16/16 sequences and 54/54 ticks across seeds 7 and 20261024,
with the wrong logical-map negative control detected. The State-9/10
initializer-composition runner checks the original caller's registration tuple,
readiness pending/ready and reset path but does not schedule or execute Calc.
These are prerequisites for production integration, not production source
build evidence or whole-title approval. The helper internals, physical input
producer, UI, persistence and runtime remain unresolved.
