# Independent review: nullable getter `0x0014ec5c`

## Result

The candidate is a reasonable semantic reconstruction for aligned readable ordinary RAM on the 32-bit little-endian ARM target. The null return, four-byte field read at `+0x1c`, pointer-width assumption, and no-write behavior agree with the original instruction sequence. The supplied differential evidence exercises production C++ and both observed caller windows under two seeds; both negative controls are detected. This review did not rerun those runners.

## Contract and implementation

The original bytes `000050e31c0090151eff2fe1` decode as `cmp r0,#0; ldrne r0,[r0,#0x1c]; bx lr`. C ABI is `void*(void*)`. The candidate returns null for null input; otherwise it copies the four field-representation bytes into `u32` with inline memcpy and converts that 32-bit target address to `void*`. The `sizeof(void*) == sizeof(u32)` assertion records the target ABI assumption. It does not name a record type or use a potentially aliasing typed load. No stores are present.

This interpretation is target-specific: byte order and the integer-to-pointer conversion rely on the configured little-endian ARM32 target. The field's actual pointee type, object type, and lifetime are not established.

## Callers and evidence

The pinned reference scan identifies two direct BL sites: `0x002a62a0` in `engine_func_002a6228` and `0x002aebe0` in `engine_func_002aeb78`. Both callers guard null before the call. Immediately after the first call, `r0` is overwritten by `[r4]`; after the second, `r2` is assigned from `r5`. The returned field is therefore not consumed in these observed windows. The tests start at the caller guards; they do not execute preceding helpers or prove producer/object provenance.

Both pinned seed reports (7 and 20261024) show 261 direct cases, 66 windows per caller, and detection of `returns_base` and `nonnull_on_null` negative controls. The runner builds the production source and reports no relocation in the tested symbol. It normalizes ordinary-RAM reads to covered bytes, since the source and original may use different read widths; state, return, writes, memory, fault, and continuation comparisons remain in scope. These are bounded offline results, not runtime or whole-game evidence.

## Span and limits

The ledger preserves the original 12-byte range and correctly labels it `non_matching`. The compiled replacement symbol is reported as 44 bytes. It exceeds the old span by 32 bytes, so it cannot be substituted as a 12-byte in-place body without relocation/trampoline or another layout change; the ledger's original size is a source-range claim, not a compiled-size guarantee. The next ledger entry begins at `0x0014ec68`, so do not treat the 44-byte object-code size as permission to overwrite adjacent bytes.

The tests cover aligned ordinary RAM and 32-bit field values. Invalid/unreadable addresses, MMIO, concurrency, partial-fault ordering, runtime loader behavior, and game execution are untested. Caller windows do not establish the field's real runtime provenance. No full build or emulator was run in this review.

## Recommendation

Accept the bounded semantic evidence for the typed C++ source and its tested domain, keeping `non_matching` truthful. Preserve the 44-byte versus 12-byte distinction in any future patch/placement plan, and retain the unresolved runtime object/pointee provenance and loader/runtime coverage as limitations.
