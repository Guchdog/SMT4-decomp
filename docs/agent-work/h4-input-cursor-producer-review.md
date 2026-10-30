# H4 cursor/count copy helper: independent static review

## Result

I independently disassembled the pinned `extracted/exefs/code.bin` at `0x0011C5EC`, `0x0012A758`, and `0x0012A900`. The packet's declared input hashes all match the working files. The ARM image supports the bounded claims that `0x0011C5EC` passes the source object, a one-record request, output buffer, and caller-local result storage to `0x0012A758`; the helper copies indexed 16-byte records and validates a source snapshot before publishing its output count/cursor values. This does not establish who writes the source object, its high-level type, physical input provenance, or a C++ contract.

One important qualification: the consistency path is an **unbounded retry loop in the helper**. Any runtime observation may bound its own capture duration/retry observations, but must not imply that the target helper itself has a retry limit. The signed remainder arithmetic can yield a negative index if its effective input is negative; the source-index range therefore depends on an unproved domain invariant. Capture the actual executed source pointer rather than infer a selected slot from the earlier `0x0011C640` snapshot.

## Static verification against pinned ARM

The `code.bin` SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, matching `task.json` and the recon report. `config/functions.csv` also matches the packet pin. I ran the repository's read-only `tools/split_asm.py` disassembler for each function listed in the handoff checks; these commands print assembly and do not create output files.

### Caller arguments and caller-local outputs

At `0x0011C5EC`, the function saves the root in `r5` and the output pointer in `r4`; it allocates 0x18 bytes and initializes a two-word local pair at `[sp+0x10]` and `[sp+0x14]`, plus a local word at `[sp+0x0C]`, to `0xFFFFFFFF`. After the precheck and setup call:

- `r0 = *(*(root) + 4)` is loaded by `ldr r0,[r0,#4]` at `0x0011C630` after loading `*root` at `0x0011C620`. At the separately reported runtime probe this was `0x10000000`; that observation is not a proof for all calls.
- `r1 = r4`, the caller's output pointer (`0x004E3C28` in the previously reported run).
- `r2 = 1` at `0x0011C638`.
- `r3 = sp+8`, the address of a local returned-count word.
- Stack argument 1 (`[sp]`) points to the two-word local pair at `sp+0x10`; stack argument 2 (`[sp+4]`) points to the local word at `sp+0x0C`.

This is a six-argument ARM call shape (four register arguments plus two stack pointers). The callee saves the incoming `r3` at its entry stack `+0x20` and reads the two caller stack arguments at its entry stack `+0x48/+0x4C`, consistent with that mapping. At successful stable completion, it writes the selected result count through `r3`, writes the two snapshot words through the first stack pointer, and writes its final count/cursor word through the second stack pointer. Those destinations are caller-local storage. In the observed caller setup they are stack locals, **not writes to the source object's `+0/+8/+0x10` fields**. The helper only loads and rereads those source fields in the inspected body.

The source fields are loaded at `0x0012A780..790`: a word at `source+0x10`, then two `LDRD` pairs at `source+0` and `source+8`. The registers and arithmetic treat the two 64-bit values as snapshot/cursor values for this algorithm, and the word at `+0x10` participates as the count/index input. This does not prove semantic names such as event count, timestamp, producer sequence, or device identifier.

### Count selection and modulo-8 indexed copy

The helper zeros the selected-count output through `r3` before its early exits (`0x0012A760..76C`). A signed request `r2 <= 0` returns immediately; positive request is capped at 7 (`0x0012A770..77C`). A negative source `+0x10` word returns early. If the source word is zero and the two 64-bit source snapshots match, the code additionally checks the signed high word and may set the effective count to 7; this is a special branch, not evidence that the source word is always an item count. Caller cursors and snapshot values then determine a signed available-item count, which is capped by the request before entering the copy loop.

For loop item `i` in `r5`, the address arithmetic at `0x0012A83C..858` is exact:

1. Form `x = effective_r4 - i + 8`.
2. Compute signed remainder by 8 using `ASR`, sign correction, `BIC #7`, then subtraction (`0x0012A848..854`). This is ARM signed-remainder behavior; it is not an unconditional normalization into `[0,7]` for negative `x`.
3. Set destination `r7 = output + (i << 4)` and source `r3 = source + (remainder << 4)`.

The payload transfer at `0x0012A85C..894` copies five fields from that selected source slot: words at `+0x28`, `+0x2C`, `+0x30`, and halfwords at `+0x34`, `+0x36`, into output `+0`, `+4`, `+8`, `+0xC`, `+0xE`. The slot stride is 16 bytes; with a proven nonnegative ring index 0..7, the highest copied source byte is `+0xA6`/`+0xA7` (the final halfword at slot 7), consistent with the recon's `+0xA7` bound. The static code alone does not prove the necessary index-domain invariant. For the observed caller's request `r2=1`, no more than one output record is copied.

The recon's conditional source-offset examples for effective `r4=3` or `6` and `i=0` follow from the formula. They remain hypothetical: the earlier probe at `0x0011C640` gives the call arguments, but does not record the later effective `r4`, loop index, or executed source pointer. The recommended additional probe at the copy instruction must capture `r3` and `r7` (or equivalent effective addresses) on the actual execution to prove the selected source slot and raw destination bytes.

### Consistency retry and output stores

After copying, `0x0012A89C..8A8` rereads source `+0x10`, `+0`, and `+8`, then compares these with the saved snapshot at `0x0012A8AC..8D4`. Any mismatch branches directly back to `0x0012A780`. There is no retry counter, retry ceiling, backoff, or failure return for repeated snapshot changes in this loop. If the source never stabilizes, this helper can continue retrying indefinitely. On a stable snapshot, `0x0012A8DC..8F4` commits the selected count and caller-local cursor/count outputs. Early exits occur before these success stores, while the selected-count output was already cleared at entry.

After return, the caller reads its result count at `0x0011C644`; a nonpositive value returns failure. For a positive result it consumes the output halfwords at `+0xC/+0xE` via `0x00128610`, then modifies or may clear output fields before returning. Thus the destination bytes immediately after the helper are the raw copied record; the post-transform record is a separate later state and should be captured separately if relevant. This caller does not make the helper's source-index selection knowable from the call-entry snapshot alone.

### Separate `0x0012A900` path and scan limits

The neighboring `0x0011C3C0` caller invokes `0x0012A900`, a distinct helper. Its copy loop uses an 8-byte destination stride, calculates an 8-byte source stride, and copies halfwords from source `+0x20/+0x22` plus a byte from `+0x24` into destination `+0/+2/+4`. This is not the 16-byte `0x0012A758` layout. The shared-looking cursor/count header access does not prove that the two callers use the same object base or producer.

The recon correctly bounds its writer search to aligned ARM direct-call/literal references. That does not exclude Thumb code, indirect or computed references, runtime-created pointers, code/data ambiguity, or external code. No source-header or indexed-payload writer is established by the inspected paths; this is a bounded negative finding, not proof that no such writer exists.

## Audit of the proposed next observation

The proposed read-only trace is appropriately scoped if implemented at these points:

- At `0x0011C640`, record all incoming GPRs, stack pointer/arguments, and read back the two caller-local cursor/count values through the actual pointer values. Record source address validation and `source+0/+8/+0x10` snapshot.
- At the executed copy loop after effective-address calculation (preferably before the first payload load at `0x0012A85C`), record `r3` (selected source slot), `r7` (destination slot), `r5` loop index, the source snapshot and the five source fields. This establishes the selected address for that execution; a formula-only estimate does not.
- At return from `0x0012A758` / before the transform call at `0x0011C650`, read the destination's 16 bytes to capture the raw copied record. Capture again after the caller's transform return only if the separate post-transform state is wanted.
- Keep source and process identity with each event. Read-only pointer validation and independent readback are suitable safeguards; do not write guest memory, infer a producer, or call the fields physical/live input.

The static recon's recommendation for a bounded read-only runtime observation captures the requested argument, cursor, selected-slot, raw-copy, and post-transform distinctions. Clarify that external observation limits do not bound the target's internal consistency loop. The existing earlier runtime source-span capture is not itself a dynamic trace of this selected index or its five loads.

## Evidence level and remaining limits

This is a static ARM disassembly review only. I did not run tests, build, emulator, GDB, or source-save access. Existing runtime and producer reports are cited only for their previously described observations; they do not extend this review into an active-input or producer proof. Remaining questions include source writer/ownership, valid signed index range, whether the writer follows a stable snapshot protocol, actual selected source slot during a live call, and real source semantics. The next useful evidence is the separately assigned, read-only dynamic trace described above, with an external time/observation limit and no claim that the helper's own retry is bounded.
