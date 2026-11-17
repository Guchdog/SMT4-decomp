# 0x00121d70 production-conversion review

## Recommendation

The isolated leaf contract is well supported for a valid readable input: load one signed byte at `p+0x330`, return it sign-extended in `r0`/`s32`, and perform no writes. The current test candidate is useful for instruction-level evidence, but it should not be copied into production with `SignedByteRecord` as though that were a recovered game type. A narrow production conversion can keep the existing `s32 func_00121d70(const u8* p)` ABI and express the operation as a byte read plus explicit signed extension (or use `memcpy` to a local signed byte if the project's `u8` alias is not an alias-safe character type). The observed caller supports the offset and return use, but the runtime pointee's type, lifetime, and extent remain unresolved.

## Original and candidate evidence

Pinned original image SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Original bytes at `0x00121d70` are `030c80e2d003d0e11eff2fe1`, disassembling to `add r0,r0,#0x300; ldrsb r0,[r0,#0x30]; bx lr`. Thus the effective access is `p+0x330`, a one-byte signed load, with no memory writes and a signed 32-bit register result.

The isolated candidate is `candidate_00121d70(const SignedByteRecord*)`, with test-only `SignedByteRecord { u8 prefix[0x330]; s8 value; }` and an offset static assertion. It models the byte offset and signed value, but the struct type is not independently recovered from the game. At its old patch location `0x003fe6b4`, the compiled bytes are `331ea0e3d10090e11eff2fe1` (`mov r1,#0x330; ldrsb r0,[r0,r1]; bx lr`), 12 bytes and non-identical to the original.

The existing batch-002 reports identify the candidate source SHA-256 `4d5c8946eb186d9e4e0f5c8d3137a978db6847e270355b77a2040607054ed46d`, candidate object SHA-256 `ef053a4af5616a171e64e9a12c1d1e0876f97fcb9005543babbd0301ba5adcd7`, and the same pinned original. `build/semantic-equivalence/batch-002-callers/seed-7/report.json` hashes to `a75cea2e2f1af34040c4963712dea76882f7f1827355471461049550caef0780`; seed 20261024 report hashes to `ca85a82426f149d497d1d7e090da95818f799af9df9297fa0aea7751e61453b9`. Each reports 4,352 passing direct cases (all 256 byte values plus 4,096 randomized cases). The `wrong_signed_byte` control, which returns the byte unsigned, is detected at byte `0x80` (case 128). The report compares the signed result, data, access footprint and ABI-preserved state within its documented ordinary-RAM scope. The reports' overall pass includes other functions in the batch; the per-address row and caller row were inspected separately.

## Real caller, global input and limits

An independent aligned ARM BL/BLX scan over the configured text range finds one immediate direct branch to the leaf: `0x00110f44` inside `engine_func_00110f10`. It targets the function entry, with no interior branch targets. An aligned word scan over the complete pinned image finds no pointer word in `[0x00121d70, 0x00121d7c)`. These scans do not discover computed, indirect, relocated, Thumb, unaligned, or runtime-generated references and may decode data as instructions.

The real caller sequence is:

```text
0x00110f3c  ldr r5, [pc, #0x140]   ; literal at 0x00111084 -> global 0x00433158
0x00110f40  ldr r0, [r5]          ; runtime input pointer
0x00110f44  bl  0x00121d70
0x00110f48  cmp r0, #0
0x00110f4c  beq 0x00111008        ; zero result
0x00110f50  ...                   ; nonzero continuation
```

The caller therefore consumes only the zero/nonzero property, while the leaf's signed return remains part of its ABI. There is no null check between loading the global pointer and calling the leaf. The word at `0x00433158` is zero in the pinned static image; runtime initialization must populate it before this path is reached, but the reviewed evidence does not identify that producer or show a live capture. The global address also occurs in many image words, so this is shared state and not evidence of a unique record type.

The old caller-window test passes 512 cases per seed and exercises both continuations, but it starts exactly at the BL (`0x00110f44`) and sets `r0` to a synthetic ordinary-RAM object (`DATA+0x100`). It does not execute the preceding global load at `0x00110f40`, establish the global's runtime value, prove pointee lifetime/extent, or test the preceding setup. The synthetic object's base was four-byte aligned, although the machine byte load itself has no alignment requirement. The actual pointer must be non-null and readable through `p+0x330` for the C++ access to be defined and to avoid a fault; the actual extent/type and initialization remain unknown.

## Concrete production work and verification

For a production conversion, retain the current function's C linkage, `s32` return and `const u8*` parameter; do not introduce `SignedByteRecord` into the production interface. Prefer reading the byte through the project's alias-safe byte type and explicitly mapping `0x80..0xff` to `-128..-1`; if the project alias does not provide character-type object-representation access, copy one byte to a local with `memcpy` and sign-extend it. Do not add an alignment precondition solely for a byte load. Record that the readable span must include byte `+0x330`, and preserve the observed caller's no-null-check assumption without claiming null behavior.

Before accepting the conversion, compile and extract this exact production TU into fresh outputs, then run the two pinned original-versus-production seeds with all 256 signed byte values, random surrounding registers/memory, a signedness negative control, and memory/access/ABI comparisons. Add/retain a caller composition that starts at `0x00110f40`, sets `r5` to `0x00433158`, seeds that global with a valid synthetic pointee, executes the real load, BL, compare and both continuations; explicitly label the producer itself as unresolved. Recheck C linkage and the `s32` signature, scan entry/interior references, update the ledger to `non_matching` if compiled bytes differ, and do not make loader/game-runtime claims absent runtime evidence.

No source, ledger, or test files were modified for this read-only review. No compiler, emulator, or test runner was run.
