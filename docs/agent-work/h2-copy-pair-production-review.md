# Independent review: production `UiConfig_CopyPair` (`0x002ADB40`)

## Review decision

Accept the typed production source and exact helper body for the target-specific ordinary-memory contract covered by the pinned instructions and the production differential. The implementation retains the two-register interface, original return in `r0`, read-before-write order, and target ARM unaligned word-access behavior without typed `u32*` dereferences. The object is relocation-free and its 20 bytes are identical to the pinned original. This supports the helper representation and local ABI; it does not establish valid extents/lifetimes for every dynamic caller, MMIO/fault equivalence, or H2 UI/persistence/runtime behavior.

## Source, interface, ABI, and exact body

The current source is `src/engine/leaf_matching.cpp` (SHA-256 `90238ffc67607cdb8578d1ce65aa6370389deb527423d3b0b278e43f6f621da2`). Its definition is `extern "C" u32 ui_func_002adb40(void* destination, const void* source)`. The shared header declares the same two arguments and return type. All four listed assembly-caller translation units (`leaf_batch19_a`, `leaf_batch24_c`, `leaf_batch26_c`, `leaf_batch28_c`) use a matching `extern "C"` declaration; `src/camp/title_flow.cpp` uses `u32 (*)(void*, const void*)` for the initializer tail branch. No signature discrepancy remains among the declared consumers inspected.

The function's inline ARM assembly performs exactly:

```asm
ldr r2, [source]
ldr r3, [source, #4]
str r2, [destination]
str r3, [destination, #4]
```

The two `=&r` outputs hold both loaded words; early-clobber prevents them from overlapping the input pointer registers. The `memory` clobber prevents the compiler from moving surrounding memory accesses across the sequence. The compiler return expression converts `destination` back to `u32`, preserving the original `r0`; generated code ends in `bx lr`. The emitted body is 20 bytes, has no relocations, and matches the pinned bytes exactly: `002091e5043091e5002080e5043080e51eff2fe1`. I independently extracted the existing compile-TU object and compared its bytes with the pinned image at `0x002ADB40`; equality was true. The object SHA-256 is `b59d0fa7d71b58be50b08ef10a9c0061816c5b37c3f23c5318a39313869bd3e3`.

Because the accesses remain explicit ARM `LDR`/`STR`, the source does not impose C++ `u32` pointer alignment on caller addresses. This deliberately preserves target-specific ordinary-memory semantics, including tested unaligned addresses and the read-only odd `ERROR` literal. It is not portable C++ memory access and makes no claim for MMIO, invalid mappings, protection faults, concurrent observers, or other processor/configuration behavior.

## Differential and negative-control review

The frozen production helper report is `build/agent-work/H2-semantic/h2-copy-pair-readable-production/run-001/checks/production-helper-differential/report.json`, SHA-256 `81c0570ec34c10c67ef6713961a4674da24ebfc0066d30f5b8b4924e0ee60df6`. Its source hash matches the task packet; the pinned image hash is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. It records the production object hash above, the exact 20-byte body, equality to the pinned original, and zero relocations as enforced by the runner.

The report's 545 cases consist of 33 directed cases and 512 seeded cases (seed 7). Directed coverage is complete for all 16 source/destination alignment combinations modulo four; all 15 possible byte-start deltas from -7 through +7 that produce overlap between two eight-byte ranges; the real H2 source address `0x0044E0F8`; and the odd read-only `ERROR` source at `0x004656F1` with aligned stack destination. The seeded cases vary overlap delta and data. All 545 positive comparisons pass, with no first counterexample. The runner compares continuation/return `r0`, callee-saved state, RAM/stack, and access footprints. It maps the image read/execute and synthetic data/stack writable, so the actual error string is exercised as a read-only image source.

The negative control uses a sequential forward-copy body on `destination=source+4` with distinct source words. The original captures both words before either store, yielding the expected overlapped result `[a,a,b]`; the wrong control's second load observes the first store and produces `[a,a,a]`. The report records `data memory differs` and `detected: true`, which is the expected sensitivity for the order property at issue.

The focused test file statically verifies the 33 directed-case inventory, all alignment labels, all overlap labels, the H2/error addresses, aligned error destination, and that overlap cases share the same arena. It does not execute the differential itself. I inspected the tests but did not run them.

## Consumers and caller domains

Five separate consumer-TU object outputs are present, and each object SHA-256 recomputes to its adjacent `.o.json` metadata:

| Consumer TU | Object SHA-256 |
|---|---|
| `src/engine/leaf_batch19_a.cpp` | `db2481d7e3174e2d8d89f75020bef88300b7b83f48732af736a8c0704fea0099` |
| `src/engine/leaf_batch24_c.cpp` | `41736d16db77218e21f3a611ae7457065596d822b4a34cfcc370f9cee445f052` |
| `src/engine/leaf_batch26_c.cpp` | `24ccaa20f9c6c372557906d0a6112e6a38a841ba9d83ffac3f9cfd83e8186c04` |
| `src/engine/leaf_batch28_c.cpp` | `4bc66fc19da96dea8a1bbbb8b38b9de189198758371b7962d96d7d58c447d2da` |
| `src/camp/title_flow.cpp` | `432664ba70073ff98c2fed19559d4f663f0e4dd9732c519e1bf66eda4dcfe82d` |

The caller-surface audit records 28 direct `BL` sites plus the H2 initializer tail `B`, with additional paths through two forwarding wrappers. Its earlier recommendation was scoped to the aligned-only experimental `u32*` candidate; it identifies the odd read-only source and dynamic pointer cases that needed broader evidence. The production implementation and current 545-case report now exercise all pointer alignment residues and the actual odd read-only `ERROR` source, so the alignment/read-only findings no longer block this exact-body implementation.

Caller domains still open are dynamic object validity and range: several save/load, TBB, parser, and UI paths receive pointers from helpers or opaque structures. The helper needs eight readable bytes at source and eight writable bytes at destination. The local differential's synthetic memory confirms those operations for exercised valid mapped ranges, but neither that experiment nor the static caller inventory proves each dynamic object is alive and has the full span. Actual callers that pass inaccessible memory would fault in the original too; no general fault/exception contract is claimed. MMIO remains excluded. The H2 initializer's source is the configuration global and its destination is `TitleConfigWork+0x34`; the two ranges are statically disjoint and word-aligned, and H2 initializer integration records this helper at its original matching address. This review does not validate the wider titleConfig callback, UI, persistence, restart, or emulator scenario.

## Evidence and next step

- Input identities checked against the packet: `src/engine/leaf_matching.cpp` `90238ffc…f621da2`, `include/engine/leaf_matching.h` `a6201da7…8c06b55`, caller-surface review `533577c6…eb51435`, production integration report `2cabff3b…ad6bd8`, and differential report `81c0570e…ee60df6`.
- Existing helper object extraction: `python -c "from tools.asm_diff import extract_elf_functions_detailed as e; ..."`; result is the 20-byte body above, no relocations, equal to pinned image bytes.
- Existing consumer artifacts were inspected read-only and each `.o` hash matched its `.o.json` metadata. The integration report records separate ARMv6K compiles for all five consumers. This review did not rebuild any object.
- The direct-call report's dynamic pointer extent/lifetime limits remain; H2 runtime and user-visible behavior remain outside this helper review.

Next, preserve the typed declaration and exact in-place implementation. Keep the helper record tied to the ordinary-memory target contract and retain the open dynamic-caller extent/lifetime and runtime limits in broader H2 acceptance.
