# Independent review: in-place H2 titleConfig initializer

## Decision

The production C++ is a credible source reconstruction of the initializer's orchestration and exactly fits the original 572-byte symbol slot. The code keeps the original entry address, uses the same helper call order and arguments, ignores incoming `r0`, and explicitly restores the pair-copy helper's result to `r0` before returning. The string addresses and proposed 68-byte pool layout are internally consistent with the string-placement audit.

This is **not yet suitable as a final patched image or promoted implementation**. No production-object original-versus-C++ differential, merged IPS/image, production caller composition, or runtime test exists. The object references the reserved `.rodata` tail addresses, but the pool bytes have not yet been added to a patched image. The audit shows that the proposed range is file-backed zero padding within the `.rodata` allocation; it does not prove runtime mapping/protection or that the patched loader exposes the strings there. Keep the source and ledger classification as recorded (`non_matching`) while final-image evidence remains open.

## Identity and slot fit

All `input_sha256` entries in the refreshed run-002 packet match the current checkout. The relevant identities are:

- Production source `src/camp/title_flow.cpp`: SHA-256 `11b5360c77aecb4ab0e510774fd42a1cb479e8343aff4bb1a30d4cadeccc1b5e`.
- Production TU object `.../run-001/checks/production-tu/camp/title_flow.o`: SHA-256 `432664ba70073ff98c2fed19559d4f663f0e4dd9732c519e1bf66eda4dcfe82d`.
- Extracted symbol `_ZN4smt44camp25titleConfig_func_002f4ca0EPv`: 572 bytes, zero ELF relocations, body SHA-256 `5d77e804a00fbb2d670e0c42e15ba2a61bb6362387fde008eaf8f79562aa8c4b`.
- Pinned reference `code.bin`: SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- Integration report: `docs/agent-work/h2-init-inplace-production-integration.md`, SHA-256 `933d7be93362a27a87578bc00c1a6d8ce34e1dc09f963c78d6f6601dd0eee3d2`.

The body exactly matches `[0x002F4CA0,0x002F4EDC)`; there is no size overrun or ELF relocation to resolve. The refreshed function record and CSV both now classify the changed source as `non_matching`, which is correct. The body-size result is a compile/slot-fit fact, not proof that its fixed addresses resolve correctly in a final patched image.

## Call order and ABI review

I compared the current source against the pinned `python tools/split_asm.py --addr 0x002f4ca0` listing and the accepted function record. The main sequence agrees:

1. Call `AsdMem_Alloc(0x100,0x100,0,0x158,1)`; publish the returned workspace at `0x0044E2D0` without a null check.
2. Create the calc task with priority 2, callbacks `0x001EA928` / `0x002CAEF0`, and the work pointer; store its returned handle at `work+0`.
3. Create the draw task with priority `0xE6`, callback `0x002CAFD0`, and the calc handle; ignore the returned draw handle.
4. Initialize and bind the sprite group using `0x00407EC6` and count `0x18`; set up the sprite and animation; set up the cursor with `(3,3,1,0,1)`.
5. Clear fields `+8`, `+0x1A`, and `+0x24` in the observed order, fill `+0x1C` with `0xFFFFFFFF`, then enqueue `camp/config.bf` and `camp/config.mbm` at `+0x14C/+0x150`.
6. Play sound `0x99`, reset UI with `(0,0x323232FF)`, map config bytes 0/1/2 into `+0x28/+0x2C/+0x30`, and copy the first eight config bytes to `+0x34`.

The original entry does not use the incoming context before replacing `r0` for allocation; the C++ parameter is unnamed and ignored. Both declarations are `void`. The original tail sets `r0` to the copy destination and branches to `0x002ADB40`; the source types the copy call as returning `u32` and emits `mov r0, copy_result`, preserving the original normal return value while retaining the header's `void` declaration. The source then emits three NOPs to occupy the exact slot. The copy helper is still an original dependency. There is no production-symbol differential to confirm the generated return register and callee-saved behavior against the original; that should be included in the final-image check.

The production source also preserves the original unchecked allocation result and uses original allocator, task, sprite/cursor, async table, sound/reset, mapping/fill/copy helpers. Their behavior remains outside this isolated production-symbol evidence.

## String pool review

The four source pointer constants match the audited values and payloads:

| Address | Bytes including NUL | String |
|---|---:|---|
| `0x0042AB78` | 18 | `TITLE_CONFIG_MAIN` |
| `0x0042AB8C` | 15 | `TITLE_CONFIG D` |
| `0x0042AB9C` | 15 | `camp/config.bf` |
| `0x0042ABAC` | 16 | `camp/config.mbm` |

They occupy four-byte slots of 20, 16, 16, and 16 bytes: offsets `0x00`, `0x14`, `0x24`, and `0x34`, ending at `0x0042ABBC`. The audit maps the pool to decompressed image offsets `[0x0032AB78,0x0032ABBC)`. It fits the 1,160-byte zero-filled tail from the `.rodata` declared end `0x0042AB78` to its page allocation end `0x0042B000`. All four old string literals fell within the replaced original function; the static scan found no external references into the overwritten function interior or to the old strings.

The source has retargeted its constants, and the extracted object is relocation-free, but the production-integration task did not create the corresponding 68-byte patch record. Thus a final image must still write those exact strings and padding at the proposed file offsets alongside the 572-byte body, then independently verify serialized patch application and all bytes outside the authorized records. The segment is described as `.rodata`, but ExHeader metadata does not expose an explicit protection bit and no loader/runtime test confirmed read-only access or byte-for-byte exposure of this page tail. Treat the range as a statically audited placement proposal pending that check.

## Evidence limits and next action

The production task ran a one-job TU compile and extracted the exact production symbol, but did not run an original-versus-production differential. The two-seed ARM differential and `0x18`/`0x17` wrong-group-count control belong to the separate experimental candidate, which still uses the original inline-string addresses. Those results do not validate this production object or the new pool. The offline State-9/10 caller composition previously tested an injected candidate body, not this production symbol and pool. No production caller test, final IPS/image, scheduler execution, real helper behavior, UI input, persistence, or emulator runtime was established.

Next, create one reproducible patch with the exact 572-byte in-place body plus 68-byte pool, verify the string bytes/padding and authorized ranges, and run a production-object differential at `0x002F4CA0` with the pool mapped at `0x0042AB78`. Compare four task/resource string arguments, helper order, return `r0`, PC/SP, callee-saved state, work/global/config bytes, and include distinct config inputs, incoming-context variation, and a wrong-group-count negative control. Then run the State-9/10 caller against that exact final image without synthetic initializer reinjection. Keep helper HLE boundaries explicit and runtime/persistence claims open until separately tested.
