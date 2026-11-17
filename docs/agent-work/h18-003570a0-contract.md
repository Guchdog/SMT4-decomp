# Contract research: command-buffer initializer `0x003570a0` / `0x003570a4`

## Scope and provenance

- Task: `h18-contract-003570a0`, owner `h18_buffer_recon`.
- Reference: `extracted/exefs/code.bin`, pinned SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- Ledger rows: `0x003570a0` is a four-byte `matching` row (`func_003570a0`); `0x003570a4` is a 236-byte `matching` row (`engine_func_003570a4`). The second row's executable code returns at `0x00357174`; six words from `0x00357178` through `0x0035718c` are literal data in its recorded span.
- Supplementary inspection of the helper's current wrapper source: `src/engine/leaf_batch38_a.cpp`, SHA-256 `ecd6d37b2ab751ece877509321047544e83e16218a584cfeb8391303197747fe` (the file is not edited).
- Read-only disassembly artifacts are under `build/agent-work/batch-h18-001/h18-contract-003570a0/run-001/disasm/`.
- No compilation, runtime, emulator, or production edit was performed.

## Entry boundary and shared operation

The original bytes at `0x003570a0` decode as `mov r0,r0` (`00 00 a0 e1`). This instruction does not return: control falls through to `0x003570a4`, where the adjacent body begins with `push {r4,r5,r6,lr}`. Thus `.a0` is a four-byte entry seam into the `.a4` command-buffer operation, not a standalone no-op. Direct calls to either address enter the same body, with `.a0` callers executing one extra NOP.

The `.a4` body returns at `0x00357174` with `pop {r4,r5,r6,pc}`. It restores `r4-r6` and `sp`; there is no VFP use. The body uses the incoming `r0` as a writable command-buffer cursor, writes a command stream, and returns the advanced cursor in `r0`. There are no null, length, or capacity checks. The caller must provide aligned writable storage of sufficient size. No command-buffer reads are visible in the body; literals are fetched from code.

The typed declaration in `include/engine/block_batch.h` is `void* func_003570a0(void* buf)`, which agrees with the direct `.a0` callers. In contrast, `src/engine/leaf_batch29_c.cpp` declares/wraps `.a4` as `void engine_func_003570a4()` despite its observable pointer argument/return; that declaration is not an adequate typed contract.

## Command stream effects observed in `.a4`

The operation first calls `0x00138e38` with the incoming pointer in `r0`. That four-instruction-row-sized entry sets `r2=3`, `r1=0`, and then the PC falls through into the separate `0x00138e44` body, which writes a large fixed stream and returns its updated cursor. This is a compound helper across two ledger rows; the `.38` bytes do not contain a return instruction. The current source wrapper marks these exact bytes `.thumb`, but the pinned `.a4` caller uses ARM `BL` to the even address and the pinned bytes decode as ARM instructions. Confirm/reconcile that source mode annotation before relying on it for a rebuilt cross-entry call.

After that prefix helper returns its cursor `p`, `.a4` writes:

1. A 16-byte header at `p`: words `0`, `0x000f0201`, `0`, `0x000f0202`.
2. Zeroes `0x98` bytes starting at `p+0x10` via `0x002c4b30(dst=p+0x10, size=0x98)`, then sets word `p+0x14` to `0x823f0203`.
3. Twelve 24-byte descriptors starting at `p+0xa8`. Descriptor `i` contains words `i` and `0x803f0232`, followed by four zero words. Writes end after byte `p+0x1c7`.
4. More fixed command words using helper calls at `0x00357048(r0=cursor,r1=1)`, `0x003574f8(r0=cursor,r1=1)`, and `0x00356fa8(r0=cursor,r1=1)`, interleaved with direct stores. Those helper bodies append command words and return the advanced cursor in `r0`; their output data is formed from literals including `0x00200080`, `0x000f008f`, `0x000f01c6`, `0x000f0080`, `0x00010040`, `0x00e40100`, `0x01010000`, `0x000f0101`, `0x00010104`, `0x000f0107`, and `0x80310112`.
5. The final direct stores append words `0` and `0x000f011b`; returned `r0` points just beyond those words.

The original dependencies directly called by `.a4` are therefore `0x00138e38` (which falls through to `.44`), zero-fill helper `0x002c4b30`, and command emitters `0x00357048`, `0x003574f8`, and `0x00356fa8`. The zero-fill helper's disassembly writes zero bytes for its `(r0,r1)` destination/byte-count inputs. The command emitters' detailed fixed stores are visible in their disassembly/source, but the hardware meanings of their words are unresolved. No call from the `.a4` body is unaccounted for.

## Typed caller and real direct callers

`src/engine/block_batch.cpp` contains a readable typed draft of `battle_func_0034a4e4` inside `#if 0`; it is not compiled production C++. The draft allocates a command buffer with `engine_func_002bc9d8(0x208)`, retains its start pointer, calls `func_003570a0(cmd_buf)` after the particle command passes, stores the returned cursor, computes `(cursor-start)&~3`, passes that size to `func_002af630`, and then calls `func_00364f78(context,0x44,0)`. This caller contract strongly confirms that the target returns the end cursor. The original active ARM body at `0x0034a4e4` also calls `.a0` at `0x0034afac`, stores returned `r0`, aligns the used-byte difference against its saved buffer base, calls `0x002af630`, then calls `0x00364f78` with `(context,0x44,0)`.

Aligned immediate ARM `BL`/`BLX` scan found exactly:

| Site | Target | Containing function | Caller evidence |
| --- | --- | --- | --- |
| `0x00342858` | `.a0` | `battle_func_00342488` | `ldr r0,[sp]`; `bl .a0`; `str r0,[sp]`; compute aligned size from saved `fp`; call `0x002af630`; then call `0x00364f78` with `(object,0x44,0)`. |
| `0x0034afac` | `.a0` | `battle_func_0034a4e4` | `ldr r0,[sp]`; `bl .a0`; store returned cursor; compute aligned size relative to saved buffer; call `0x002af630`; then call `0x00364f78` with `(context,0x44,0)`. |
| `0x0034de64` | `.a4` | `engine_func_0034de5c` | Entry input `r0` buffer reaches `.a4`; after return, `mov r1,r0` passes the returned cursor to `ui_func_002b6030` as its second argument. |

An aligned-word scan of the image's text/rodata/data found no pointer word equal to either entry (or its low-bit-set form). No aligned direct BLX-immediate sites were found. Register-indirect BLX, computed or unaligned references, and runtime callback dispatch are not covered. The direct-call scan examines aligned words and can mistake data for instruction encodings, although the three listed call sites were independently decoded in their containing functions. These are static call paths, not runtime invocation evidence.

The direct callers and their post-call behavior establish a `void* (void*)`-like ABI for both entries, with returned `r0` consumed. `.a0` callers pass only the command-buffer cursor in `r0`; `.a4`'s direct caller does likewise. `r1/r2` are initialized by `.a4`'s first helper as needed. This does not prove the allocator's exact capacity from all callers; `0x208` is observed in both particle-buffer allocation paths in the original disassembly and the disabled typed draft.

## Narrow C++ and validation strategy

The narrow unit is one typed command-buffer initializer, `void* init_command_stream(void* cursor)`, representing the common `.a0`-through-`.a4` operation. Preserve both original entry addresses as aliases/thunks if promoted; `.a0` must no longer be treated as a standalone no-op. The candidate should use explicit `u32` stores and a typed 12-element descriptor loop, and either inline the fixed helper stores or keep each helper as an explicitly typed original dependency. Do not infer command names/semantics from the constants alone.

Existing `tools/semantic_experiment.py` `Runner` and `compile_candidate_symbols` support relocation-free leaf code; they reject calls/relocations. A candidate that calls the original helper services needs a bounded composite harness that resolves those original ARM helper targets, maps the private pinned image, and compares the whole output range, returned cursor, memory footprint, preserved registers and continuation. A focused caller window should start at each real `.a0` BL and stop just after its continuation/size calculation; test `.a4` through its `.de64` call seam separately if the `engine_func_0034de5c` pre-state is prepared. Test both entry addresses, distinct-prefilled buffers, two seeded valid buffers, exact boundary/sentinel writes, return cursor and saved registers/SP, plus negative controls for a changed descriptor stride/header, omitted zeroing, and wrong returned cursor. The caller `func_00138e38` is especially important: its 12-byte prefix intentionally falls into the adjacent 240-byte `.44` helper body, so the harness must model that cross-row execution and ARM-state branch correctly.

## Evidence level and open questions

- Boundary, disassembly, typed declaration/draft, and immediate caller behavior: statically recovered; caller evidence is partial because runtime use and indirect references are unknown.
- Compiled C++, ARM differential, caller-composition execution, and runtime: `not_run` as assigned.
- Open: what each emitted command means to the graphics/command processor; exact allocated capacity for arbitrary callers; whether other indirect callers exist; and how the `.thumb` mode annotation on `0x00138e38` should be corrected while preserving exact source accounting.
- Next action: independent review, then implement/validate one bounded initializer plus dual-entry preservation and a non-leaf/cross-row caller harness. Do not promote either `matching` ledger row based on this report alone.
