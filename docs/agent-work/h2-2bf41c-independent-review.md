# Independent review: `0x002BF41C` task-registry lookup

## Decision

The C++ implementation is supported for the documented readable-registry domain. The original and candidate agree on bucket selection, row stride, node fields, equality, null termination, and the no-match result. The direct differential covers all 4,096 buckets plus boundary/list cases and detects both targeted mutations. The original `TitleConfig_IsReady` body is also exercised with the converted helper installed at the final address for five controlled states.

Recommend bounded semantic promotion with the current `non_matching` ledger status. The task-list fixtures are synthetic and acyclic; no scheduler lifecycle, mutation ordering, natural runtime frequency, or H2 runtime acceptance is established.

## Frozen identity and original algorithm

All 20 run001 packet input hashes match. The pinned `code.bin` SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The 68-byte original span at `0x002BF41C` hashes to `abc87f735e4d84f179da2ad9d7349c4913956be1b7e3d153004a0f785898447a`.

Pinned ARM decoding shows:

1. Load the registry-table global pointer from `0x004E3CF4`.
2. Compute `bucket_index = handle >> 20`, then load the bucket head from `table + bucket_index*8`.
3. While the node pointer is nonzero, compare the word at `node+0x28` with the original `r0` handle. Return 1 immediately on equality; otherwise follow the word at `node+0x4C`.
4. Return 0 after an empty bucket or a null next pointer.

The unsigned 32-bit shift yields indices 0 through 4095 for every possible handle. The table is indexed with an 8-byte stride though only the first word is read. The candidate C++ follows that layout, preserves the raw `u32` task bits via `uintptr_t` conversion, and uses `u32(void*)` / `u32` return. It has no explicit null-handle special case: handle zero selects bucket zero and can match a node whose stored handle is also zero. A null registry pointer, unreadable table/node, malformed node, or cyclic chain can fault or fail to terminate; those are correctly excluded from the claimed contract.

The candidate report body is 68 bytes, SHA-256 `c6f7dce448693f282f4b7fec497998560bd9610a0b91cbbc746673fe47a948bc`, with no relocations. It differs from original bytes, matching the ledger’s `non_matching` label. It uses only caller-saved registers `r0-r3` and no stack. The original likewise only clobbers caller-saved registers, uses no stack, and performs loads only; both preserve the tested callee-saved registers and SP and issue no writes.

## Direct differential and controls

The report exercises 4,096 matching lookups, one for each bucket index, using handles of the form `(index << 20) | 0x54321`. It then tests nine empty/boundary handles, five first/middle/tail/miss chain queries, and 64 deterministic 8-node random chains (seed `20261104`). The fixture maps 4,096 8-byte buckets and nodes at `+0x28` / `+0x4C`; the chain tail is null. The direct comparator checks `r0`, `r4-r11`, SP, all guest writes, completion, and faults. The two mutation controls detect a shifted bucket calculation (`>>19`) and a shifted stored-handle field (`+0x2C`), both on input `0x00100001`.

This establishes the tested bucket and list logic for well-formed readable registries. It does not test cycles, invalid pointers, null registry-global contents, concurrent registry changes, or allocator/task lifetime. Null-task behavior is tested in the ready-gate composition rather than the direct bucket sweep.

## Caller signatures and ready-gate composition

The packet-declared caller translation units declare `extern "C" u32 battle_func_002bf41c(void* task)`. The `TitleConfig_IsReady` C++ body uses this prototype and passes the first word of `TitleConfigWork` as the task pointer. The pinned original ready body at `0x002FC0EC` loads `g_TitleConfigWork` from `0x0044E2D0`; if null it returns 1 without the registry call. Otherwise it loads `work[0]`, calls `0x002BF41C`, returns 0 for a nonzero registry result, and returns 1 for zero.

`run_ready_composition()` compares that original ready-gate body on the pinned image and with only the helper replaced at its final address. Its five cases are consistent with the algorithm:

- null work: returns ready (1), no registry call;
- registered nonzero task: helper receives `0x00123456`, returns 1, ready returns 0;
- unregistered nonzero task: helper receives `0x00123456`, returns 0, ready returns 1;
- null task absent from bucket zero: helper receives 0, returns 0, ready returns 1;
- null task stored in bucket zero: helper receives 0, matches the zero node key, returns 1, ready returns 0.

Both images produce matching full execution observations and helper-entry traces. This is direct composition with the real original ready gate, not a TitleMain outer state transition or runtime scheduler test. Fixture memory is separated from the code mapping: bucket table `0x00900000`, nodes from `0x00910000`, work area `0x00990000`; the globals remain at their pinned absolute addresses.

Outside the packet-declared caller TUs, I found legacy aliases `int AsdUi_IsRegistered(void*)` in `asd_text.cpp` and `asd_render_ui.cpp` for address `0x002BF41C`. The integer and `u32` return both use a 32-bit AAPCS result register, and these aliases consume the result as a boolean, so I found no ABI counterexample. Those two files were not declared packet inputs; they are not covered by the frozen caller-signature audit above. If a broad source-level type-consistency claim is made, preserve or normalize those aliases deliberately.

## Evidence status and limitations

- Compiled body: **reported passed**, 68 bytes and zero relocations; this reviewer did not compile.
- ARM differential: **reported passed** for 4,096 buckets, nine empty/boundary inputs, five chain positions, 64 random chains, and two detected controls. This reviewer did not rerun it.
- Caller: **partial but strong for the ready gate**; five controlled cases execute the original `TitleConfig_IsReady` body with the helper at its final address. The task scheduler and outer TitleMain state machine are not exercised.
- Runtime: **not run**. No natural call frequency, task-list mutation/order, task lifetime, or H2 acceptance is established.

No implementation counterexample found. Keep the `non_matching` classification and the readable acyclic-registry preconditions. The report is `build/agent-work/H2-semantic/h2-bf41c-task-registry-convert/run001/report.json`, SHA-256 `73e74da3493e29ff3278194b4c36000b51d915ed28f74075d6c90a0407a9007f`.

## Review actions

- Recomputed all 20 packet-declared input hashes and the original 68-byte function-span hash.
- Decoded original helper and ready-gate instructions; read the C++ body/prototypes, runner, function records, and controlled ready-composition logic.
- Parsed the pinned report and checked the case matrix, negative controls, and final-address helper events.
- No compiler, test runner, build, or emulator was run.

## Run002 addendum — legacy alias declarations

Run002 pins 22 inputs; independently recomputing every `input_sha256` entry found no missing files or hash mismatches. The two newly pinned caller translation units now both declare `u32 AsdUi_IsRegistered(void* handle)` for `0x002BF41C`: `src/engine/asd_text.cpp` and `src/engine/asd_render_ui.cpp`. This agrees with the candidate's raw `u32(void*)` helper signature and with the packet's typed `extern "C" u32 battle_func_002bf41c(void*)` declarations. The inspected uses are truth tests: the inline assembly in `asd_text.cpp` moves the handle into `r0`, calls the helper, then compares `r0` with zero; the two C++ call sites in `asd_render_ui.cpp` use `if (!AsdUi_IsRegistered(...))`. Both are consistent with the helper's 0/1 result and are unchanged in behavior by the declaration normalization.

Therefore the run001 alias concern is resolved as a source-level type-consistency issue. I found no caller-signature or result-consumption counterexample. The coordinator reports that the full 204-TU ARMv6K build passed after normalization; I did not rerun it. The pinned offline report remains the basis for the helper differential and `TitleConfig_IsReady` composition claims. Recommendation remains bounded semantic acceptance with ledger status `non_matching`; the tested registry shape and synthetic caller fixture do not establish scheduler lifecycle, natural call frequency, or H2 runtime acceptance.
