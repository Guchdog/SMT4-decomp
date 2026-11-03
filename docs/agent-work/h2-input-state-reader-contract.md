# 0x0011C5EC: bounded input-state reader contract

## Scope and recommendation

A bounded C++ reconstruction of this 304-byte ARM wrapper is feasible if its seven direct callees remain original with exact ARM/hard-float ABI, including the six-argument 0x0012A758 call and stack outputs. Use disjoint, valid ordinary-memory fixtures first, controlled dependency seams plus separate original-callee compositions. Do not infer physical controls, input freshness, callback cadence, device ownership or a safe runtime input-write seam. Output/source aliasing, concurrent source mutation and callback/fault paths are not established and must remain outside initial claims. Slot placement and non-leaf relocations need separate validation.

## Entry, local state and branches

Inputs r0=context pointer, r1=output buffer; no incoming r2/r3 or caller stack arguments are read. The original pushes r4-r6/lr (16 bytes) then allocates 0x18 bytes, retaining context in r5 and output in r4; total frame 40 bytes. It writes 0xFFFFFFFF at local SP+0x10 and +0x14 (one 64-bit sentinel) and SP+0x0C (32-bit sentinel); SP+8 is output count, written by the direct helper 0x0012A758 before the wrapper reads it. After restoring SP/r4-r6 it returns 0 or 1 in r0. The wrapper contains no VFP operations; transitive callee state must follow each callee ABI. r7-r11/SP are preserved assuming callees obey ABI; r0-r3/r12/CPSR are scratch. No null check on context/output is performed before their respective uses; early mode exit may avoid dereferencing either. Exact fault behavior depends on mappings and helper execution.

1. At 0x0011C60C call 0x00128C2C(). This calls 0x00138F34, which returns byte at 0x0047388B, and returns 1 only if that byte is 4. If nonzero, wrapper immediately returns 0, with no wrapper output/context stores or remaining calls. Stack locals were already written. This is a fact about a byte, not a named physical mode.
2. Otherwise call 0x001285C4(context+0x0C). This direct leaf reads signed halfwords at relative +0,+2,+6,+8,+0xA. It conditionally clamps +0 to minimum 40, +2 to minimum 36, and +6,+8,+0xA to maximum 145; each changed field is stored in that order. Relative +4 is not clamped here. Thus even if a later read fails, context calibration may already change.
3. Load context[0] and then word +4 of the pointed object. At 0x0011C640 call `0x0012A758(object, output, 1, &local_count, &local_u64, &local_index)`: r0-r3 are those first four arguments, caller stack words SP+0/+4 contain pointers to SP+0x10 and SP+0x0C respectively. The wrapper ignores the helper's r0 and checks signed local_count >0. If <=0 it returns 0 without the subsequent transformation; helper and prior clamp effects are retained.
4. On positive count, load signed output halfwords +0x0E and +0x0C; call `0x00128610(context+0x0C, output+0x0C, output+0x0E, sign_extend(output[+0x0C]), sign_extend(output[+0x0E]))`, with the last argument at caller SP. That helper reads calibration selector byte at (context+0x0C)+0x0C; selectors 0/1/2 choose different signed calibration pairs and call 0x0013B9FC / 0x0013B8F8 / 0x0013BAE0 respectively; other selectors return without that call. Pointer outputs are halfword slots. Exact arithmetic and transitive effects belong to those original helpers, not this wrapper.
5. If byte context+0x30 is nonzero, copy current output word +0 to context+8, then write zero to context+0x30. Next load output word +0, clear bit 0x2000 and store back. Load context+8 as old: write `(new ^ old) & ~old` to output+4; reload old and write `old & ~new` to output+8. These words are raw bit transformations; first branch may set old from the pre-cleared output.
6. Call 0x002BB978(), a signed-byte read from 0x0044E362. Only if nonzero call 0x002BC9C8(), a signed-byte read from 0x0044E381. If the first is nonzero and second zero, write zeros in order to output +0, +8, +4 (words), then +0x0C, +0x0E (halfwords). Other paths skip this clear. Then copy the resulting output word +0 to context+8.
7. Read byte at 0x00471AD8 (literal 0x0011C718); if zero call 0x0013BCAC(output), otherwise skip. Finally return 1. The saved context+8 is updated **before** this optional postprocess and is not recomputed afterward.

## Direct callees and their boundaries

| Address | Direct behavior or bounded seam |
| --- | --- |
| 0x00128C2C | calls 0x00138F34; returns `(byte[0x0047388B] == 4)`; no direct data writes. |
| 0x001285C4 | five conditional signed-halfword clamps described above; no calls. |
| 0x0012A758 | initializes `*count=0`; clips positive requested count to 7; reads a ring/source object and retries if sequence fields change, copies up to requested 16-byte records using words at source-record +0x28/+0x2C/+0x30 and halfwords +0x34/+0x36, then updates caller count, timestamp and index outputs. Here requested count is 1. It can return with count zero; its full source consistency, alias and retry termination assumptions require valid, stable fixtures. |
| 0x00128610 | dispatches by calibration selector 0/1/2 to the three original normalization helpers above, using supplied signed samples and output pointers; invalid selector does not call them. |
| 0x002BB978 / 0x002BC9C8 | sign-extend bytes at 0x0044E362 / 0x0044E381 respectively. |
| 0x0013BCAC | optional postprocess reads output words +0/+4/+8, updates bits 2/3 of those words through conditional stores; it may modify output after context+8 is saved. Keep original or model all paths including store order. |

The input reader is non-leaf, and some callees themselves call other helpers or loop. Do not use a generic leaf-only relocation harness or assume the 0x0012A758 return register is its copied count. The `0x0013BCAC` body uses conditional writes, and exact intermediate output is relevant when helpers observe memory or aliases.

## H2 and H4 relation

Pinned direct caller 0x001078E8 inside 0x001078D8 loads context from [0x004650A0] and passes output 0x004E3C28. The converted counter refresh normalizes this wrapper's return into byte/word availability at 0x004650A4 and updates 31 logical counters. Its previously reported differential used a **controlled reader**, not this real body. The first 16-byte state record at 0x004E3C28 overlaps buffers described by the earlier H4 axis-reader work; the alternate state location 0x004E3C48 and broader producer/scheduler behavior cannot be inferred from this one-record request. No direct reader-to-camera call or live camera/input behavior is proven. The historical producer audit and current refresh record should be read with their stated bounds; they do not prove all buffer words are freshly populated by this function.

An image-wide aligned ARM scan found one raw BL to 0x0011C5EC at 0x001078E8, no B; this can match data and does not rule out Thumb, dynamic or indirect callers. This is static provenance only, not proof of runtime reachability or cadence.

## Differential plan and limits

Direct fixtures should compare return, full context and output bytes, ordered global/context/output stores, call arguments including stack slots, r4-r11/SP and fault class on both original/candidate: mode byte 4 vs others; calibrations at/below/above signed clamp boundaries; count<=0 and positive from real or controlled reader; output initialized distinctly; flag +0x30 set/clear with input bit 0x2000; old/new bit combinations; signed flags 0 and nonzero, all short-circuit combinations; postprocess byte zero/nonzero and bit 2/3 combinations. Include negative controls for clamp thresholds, output field offsets, reversed change masks, omitted short-circuit, clear-store order and save-before-postprocess. Compose the original 0x001078D8 with identical full reader fixtures and compare all 31 counters and availability, then separately test real 0x0012A758 ring fixtures, normalization selector branches and postprocess. Controlled stubs must record six arguments and output/write ordering; they are not evidence of producer liveness.

Invalid or overlapping context/output/source, malformed ring state, concurrent mutation/retry, unreadable pointers, arithmetic/fault corners and live hardware behavior are unsupported until characterized. No compilation, ARM execution, debugger or emulator was performed.

## Provenance

All declared packet input hashes matched when recomputed. Pinned image SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; wrapper source `src/engine/leaf_batch30_a.cpp` `f423b4e325f298ede2c742620c87baf361a665cfb525af818fdc6c0cd007e30c`; ledger `config/functions.csv` `2021ccbc7833a33de97e7322cbf94eaa5739e72a4214bb2eb13cf3ad4643f442`. Read-only `python -` scripts using Capstone ARM disassembly at 0x0011C5EC and its seven direct callee addresses, aligned ARM B/BL scan, literal reads, and SHA-256 packet comparison exited 0.
