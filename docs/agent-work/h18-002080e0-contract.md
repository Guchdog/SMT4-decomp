# Contract research: `0x002080e0`

## Scope and provenance

- Assigned task: `h18-contract-002080e0`, owner `h18_recon_b`.
- Function catalog: `config/functions.csv` row `0x002080e0,704,matching,engine,engine_func_002080e0,src/engine/leaf_batch45_a.cpp`.
- Pinned image identity in `config/game_info.json`: `extracted/exefs/code.bin`, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- Read-only disassembly command: `python tools/split_asm.py --addr 0x002080e0 --out-dir build/agent-work/batch-h18-001/h18-contract-002080e0/run-001/disasm` (exit 0). Result: `build/agent-work/batch-h18-001/h18-contract-002080e0/run-001/disasm/engine/engine_func_002080e0.s`.
- No compilation or runtime validation performed, per task scope.

## Recovered behavior (observed from disassembly)

The body operates on a work/context pointer in `r1`, a global pointer loaded through `r4`, a 16-bit value in `r6`, and a float value in `s16` (another float in `s17` on one path). It is a non-leaf ARM function with ARM-state direct calls and one `BLX` call. It has a `0x98`-byte stack allocation, saves/restores `r4-r6`, `lr`, and `d8`, and returns through `pop {...,pc}` at `0x00208314`.

The primary paths are:

1. **Initialization/clear path:** write zero to `[r1+0x0c]`, write `r6` as halfword to `[r1+8]`, then branch to common return.
2. **Sky/map resource path:** sign-load halfword `[r1+6]`, call `0x0020e5a4`, store result at global-work offset `0x18`, and if positive format `map/sky/sky_%02d.bam`, load a `0x1c0`-byte resource through `0x0029a2d0`, store handle at global-work `+0x10`, increment halfword `+8`, and poll `0x002ae16c`. If ready, call `0x002a06c8` and two float-setting routines `0x002a5a54` and `0x00287300` with the saved `s16` value. When a halfword at global-work `+4` equals `0x13`, there is an additional call to `0x0028c8a8` with a stack-local triple initialized from `s16/s17`.
3. **Resource setup path:** if `[r1+0x20]` is nonzero, call `0x0025be50` with `[r1+0x24]` and size `0x38`; store returned handle to global-work `+0x0c`, set it up through `0x002a06c8`, and configure two float values with `0x002a5a54` and `0x00287300`. Then clear global-work halfword `+8`.
4. **Map resource path:** otherwise sign-load halfword `[r1+4]`. IDs `0x29`, `0x2a`, and `0x2b` are normalized to `(0x24,1)` in fields `[r1+0x1c]` and `[r1+0x1e]`; other IDs copy the signed `[r1+4]` and unsigned `[r1+6]` into those fields. The path formats `map/m%03d/m%03d_%02d.bam`, loads a `0x38`-byte resource via `0x0029a2d0`, stores handle at global-work `+0x0c`, and increments halfword `+8`.
5. **Resource poll path:** test the resource pointer at `[r1+0x0c]` with `0x002ae16c`; when ready, run the same resource setup/two float configuration calls and clear halfword `+8`.
6. Common return sets `r0=0` and restores the stack/registers.

Disassembly also decodes a separate short routine at `0x0020835c` (`bx lr` at `0x00208394`) and trailing constants/literals between the main return and that routine. It is inside the catalogued 704-byte span but is not reached by the main function's decoded control flow. Treating this tail as belonging to the same semantic function is not justified without further boundary/caller analysis.

## ABI and memory contract: evidence vs inference

**Observed:** no arguments are read from `r0` in the displayed main body; `r1` is dereferenced repeatedly. `r4` is used as an address from which a pointer is loaded, `r6` is written as a halfword, and `s16/s17` are used as floats. The return path explicitly sets `r0=0`. Calls include the callee-cleanup-sensitive `BLX` to `0x002be7fc` (formatter) and ARM `BL`s to listed helpers. Global-work structure offsets touched are `+0x04`, `+0x08`, `+0x0c`, `+0x10`, `+0x18`; the incoming `r1` structure offsets include `+0x04`, `+0x06`, `+0x08`, `+0x0c`, `+0x20`, `+0x24` and writes at `+0x1c/+0x1e`.

**Inference needing caller confirmation:** probable signature is a void/u32-returning state callback receiving a work pointer in `r1`, with other parameters or state held in registers by an enclosing dispatcher. `r4` appears to point to a global pointer slot, rather than to the work object itself. `s16` is plausibly a transition/animation parameter copied into resource objects. The function is not ABI-conventional at its recorded entry: no stack allocation/save prologue appears before its first instructions, yet the common exit adjusts `sp` by `0x98` and restores saved registers. This strongly suggests a boundary/entry issue, a nonstandard internal-call convention, or an omitted/shared prologue, and must be resolved before assigning a normal C++ signature. Do not promote the catalogued `matching` label into semantic evidence.

## Callers and references

- A Capstone sweep of aligned ARM instructions over the text segment for direct `BL/BLX` targeting `0x002080e0` found no direct immediate call.
- A 32-bit aligned scan of `code.bin` found one literal pointer equal to `0x002080e0` at virtual address `0x00467480` (in data/BSS address space mapping). This is evidence for a stored function pointer, but does not identify the table/object or the runtime dispatch site.
- The C++ source contains only the raw assembly wrapper; no typed declaration or source-level caller exists in `src/` (`rg` search).
- Indirect call sites, Thumb references, unaligned/data-embedded pointers, or a pointer table consumer are not resolved here. Caller mapping remains open.

## Bounded C++ proposal

Do not implement yet as a standalone ordinary function. First resolve the unusual entry/prologue and the pointer at `0x00467480`. If confirmed as a callback with the same register contract, the bounded editable slice is a state-machine helper with explicit inputs for the work record, resource/global-work slot, state/ID values, and float parameter; split out (a) path/ID normalization and resource-name construction, and (b) polling/configuration of a loaded resource. Keep existing resource services as external dependencies until their contracts are independently established. The assembly has a lot of calls and hidden global state; it is outside the leaf-only `semantic_experiment.py` harness scope.

## Validation required before promotion

1. Resolve the indirect function-pointer table around `0x00467480`, its consumer, callback ABI, and actual invocation context; verify whether `r1`, `r4`, `r6`, `s16/s17` are setup by caller or earlier shared entry code.
2. Confirm object layouts and effects for both structures from all callers and the helper implementations at `0x0020e5a4`, `0x0029a2d0`, `0x002ae16c`, `0x002a06c8`, `0x002a5a54`, `0x00287300`, `0x0028c8a8`, `0x0025be50`, and `0x002be7fc`.
3. Define an offline harness with synthetic state and stubbed resource services that records calls, formatted paths, stores, polling phases, and float values; compare original and candidate across branch IDs (`0x13`, `0x29..0x2b`, other IDs), null/non-null resource pointer, pending/ready/failed polls, and counter wraparound at halfword `+8`.
4. Add a caller-composition case using the real dispatch/table contract. Verify ARM/Thumb interworking for function-pointer bit 0 and run offline differential + caller composition before any emulator launch. Runtime comparison, if needed, is integrator-owned and follows the emulator guide.

## Handoff status

- Recovered semantic outline: partial, disassembly-only.
- ABI/caller contract: unresolved (prologue mismatch and indirect xref are key blockers).
- Compiled C++ / differential / caller / runtime evidence: `not_run`.
- Precise next action: identify the table containing `0x00467480` and its consumer/caller to establish the real callback ABI and entry boundary; then re-document a typed contract before implementation.
