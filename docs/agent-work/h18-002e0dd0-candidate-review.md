# Independent review: bounded wrapper candidate `0x002e0dd0`

> **Historical correction:** The caller conclusion below that `ui_func_003bbfb0` returns `0x81` on a non-5 wrapper result was refuted by the pinned instruction bytes. At `0x003bc07c`, BNE targets `0x003bc02c` (`add sp,sp,#0x14`), skipping the `mov r0,#0x81` at `0x003bc028`; the non-5 path returns 0, and the 5 path returns `0x11`. See the [corrected independent caller review](h18-002e0dd0-caller-correction-review.md) and its linked byte/execution evidence. The historical text below is preserved as a record of the earlier, incorrect interpretation.

## Result

The experimental wrapper candidate has a plausible five-word AAPCS interface and matches the first callable body's observed orchestration under the runner's modeled helper hooks. The seeded reports provide bounded evidence for the wrapper path, including the bit-31 early return, helper ordering/arguments, fifth stack argument, and negative controls. This is not evidence for the true semantics of the helpers or object.

I found one concrete caller-record error: `ui_func_003bbfb0` returns `0x81` when the wrapper result is not 5, not zero. The pinned disassembly at `0x003bc074..0x003bc088` is `cmp r0,#5; movne r0,#0; bne 0x003bc02c; ... mov r0,#0x11; pop...`; the branch target `0x003bc02c` itself is `mov r0,#0x81` followed by the epilogue. The current contract and function record say “else 0”, and the caller runner only chooses a bit-31-set helper result, validating the 5-to-0x11 branch. It does not exercise the non-5 return mapping. Correct the record and add a caller case for a clear gate bit expecting `0x81` before claiming both caller outcomes are covered.

## ABI and helper call review

The original body saves `r4-r8,lr`, reads the fifth AAPCS word at entry `[sp]` (after the six-word push this is `[sp,#0x18]`), restores saved registers, and returns through `pop {...,pc}`. The experimental C ABI exposes four register arguments and a fifth stack argument. The candidate forwards the fifth word as the fourth argument to the second `0x00248e58` call. Its helper call target `0x002b5c2d` correctly sets the Thumb bit for the callable at `0x002b5c2c`; the original uses ARM `BLX` and resumes ARM after the helper.

The C++ body reads the global slot at `0x00464fac` and the object at context `+0x18`; it forwards observed register arguments and keys `0x6e`/`0x65`, gates on bit 31 from `0x00263534`, counts halfwords through `0x002b5c2c`, calls the value helper twice, then cleanup, returning 0 on the non-gated path and 5 on the gated path. The types are only mechanical ABI interfaces; the real object and helper meanings are unresolved.

The runner hooks four dependencies. Its gate returns a configured value; its counter scans a synthetic zero-terminated `u16` buffer; setter and cleanup hooks only log arguments. The original and candidate see those same models. Thus differential success establishes wrapper interaction against the models, not actual side effects, helper contracts, or application state. The two seeded reports each show 89 direct cases and three detected negative controls. Both cover the wrapper's direct normal and early-return paths. The caller windows use synthetic global/object fixtures and begin at BL sites rather than running prior setup.

## Compound span and placement

The `config/functions.csv` row remains one 724-byte (`0x2d4`) matching catalog span beginning at `0x002e0dd0`. The first callable control-flow body ends with its return at `0x002e0e54` and a literal at `0x002e0e58`; the next coherent VFP-heavy code begins at `0x002e0e5c` (offset `0x8c`, 140 bytes from the row start). The candidate emits 160 bytes, 20 bytes larger than that first-body boundary. It is experimental and is not placed over production bytes. A future in-place replacement cannot write the full candidate from `0x002e0dd0` without overlapping the adjacent VFP code. The adjacent body's identity/reachability and the rest of the compound catalog span remain unresolved; preserve them until a separately verified split or out-of-line placement exists.

## Recommendation and remaining limits

Keep the candidate as a bounded experiment, not a production promotion. First correct the `0x003bbfb0` non-5 caller result documentation and add the missing caller case. Any production layout work must preserve the code starting at `0x002e0e5c` and audit the full 724-byte catalog span. Recover the true helper/global/object effects before claiming full semantic behavior. No recompilation, runner rerun, production edit, emulator, or runtime validation was performed in this review.
