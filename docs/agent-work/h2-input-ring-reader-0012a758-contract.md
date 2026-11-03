# Static contract: input ring reader `0x0012A758`

Status: recovered from pinned US v0.1.0 ARM and the exact `0x0011C5EC` call. No build, compiler, differential, or emulator was run.

## Identity and ABI

`0x0012A758..0x0012A900` is the 424-byte ARM function. Pinned `code.bin` SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; the exact function slice SHA-256 is recorded below. `config/functions.csv` currently classifies the span `matching`; this is code identity only, not a producer or lifecycle contract. Its source mirror is `src/engine/leaf_batch16_c.cpp`.

The six-argument ABI is:

| Location | Meaning |
| --- | --- |
| `r0` | source/ring object pointer |
| `r1` | output record buffer |
| `r2` | signed requested record count |
| `r3` | pointer to signed 32-bit count output |
| entry `[sp]` | pointer to 64-bit cursor/timestamp input and output |
| entry `[sp+4]` | pointer to 32-bit ring index input and output |

The entry pushes `r0-r11,lr` (52 bytes), allocates 20 local bytes, and restores SP/LR in its epilogue. It preserves `r4-r11`; `r0-r3` are caller-saved scratch and are not restored. The raw `r0` return is path-dependent: early exits before the stable commit leave the original source pointer in `r0`, while the stable path loads the `index_inout` pointer into `r0` for the final index store and returns with that pointer. The H2 caller ignores this raw return. It clobbers `r12` and condition flags, uses no VFP registers, and makes no BL/helper calls.

## Ordered behavior

1. The function writes zero to `*count_out` before testing the request. If signed `requested <= 0`, it returns immediately; it does not read the source object or touch the timestamp/index outputs or record buffer. The count pointer is therefore required even for nonpositive requests.
2. Positive requests are capped at 7. The retry loop snapshots `source+0x10` as an index/count word, a 64-bit pair at `source+0` and another 64-bit pair at `source+8`.
3. If the `+0x10` word is negative, it returns with count still zero and cursor outputs unchanged. If it is zero and the two pairs differ, it continues with effective index zero. If it is zero and the pairs are equal, a negative signed high word at `source+4` returns; otherwise the effective index is set to 7.
4. It reads the 64-bit input cursor through the first stack pointer and compares it with the pair at `source+0` as a signed 64-bit comparison. Available-record calculation is branch-sensitive:
   - cursor `>=` the `source+0` pair: `effective_index - *index_inout`;
   - cursor `<` that pair and the high word at `source+0xC` is negative: `effective_index + 1`;
   - otherwise, cursor `<` the pair at `source+8`: the capped request;
   - otherwise: `effective_index - *index_inout + 8`.
   It caps this result above by the requested count but does not clamp it below zero.
5. If the resulting count is positive, it copies that many 16-byte records. For each loop index `i`, the machine computes the signed remainder-by-8 slot from `effective_index - i + 8` (for canonical indices 0..7 this is `(effective_index-i+8) % 8`). Destination is `output + 16*i`; source slot base is `source + 16*slot`. It copies words at slot-base `+0x28`, `+0x2C`, `+0x30`, then halfwords at `+0x34`, `+0x36` into output `+0`, `+4`, `+8`, `+0xC`, `+0xE` in that store order.
6. Before committing out-parameters, it rereads `source+0x10`, both 64-bit pairs, and retries from the snapshot if any differ. There is no retry limit. A failed attempt may already have written record bytes to the output before the changed snapshot is detected; only the count/cursor outputs are withheld until a stable pass.
7. On a stable pass, it writes the computed count to `*count_out`, stores the original pair at `source+0` to the timestamp output (high word at `+4` first, then low word at `+0`), then stores the effective index to `*index_inout`. This commit occurs even when the computed count is nonpositive and no records were copied. Early returns in steps 1 and 3 do not update timestamp/index.

## Exact `0x0011C5EC` caller tuple

At `0x0011C640`, `func_0011c5ec(context,output)` calls this helper as follows:

- `r0 = *(*(u32*)context + 4)`: it first loads the object pointer from `context[0]`, then the source pointer from that object's word `+4`.
- `r1 = output`, preserved by the wrapper from its input `r1`.
- `r2 = 1`, so a successful call copies at most one record.
- `r3 = SP+8`, the local signed count output. The wrapper does not initialize this word itself, but the helper initializes it before request handling.
- entry `[sp] = SP+0x10`, pointer to a local 64-bit value initialized to `0xFFFFFFFFFFFFFFFF`.
- entry `[sp+4] = SP+0x0C`, pointer to a local 32-bit value initialized to `0xFFFFFFFF`.

The wrapper ignores the helper's raw `r0` and branches on the signed count output (`<=0` returns wrapper result 0). In the known `0x001078D8` direct caller, `context` comes from `*[0x004650A0]` and `output` is `0x004E3C28`; this is a one-record refresh into the primary input-state buffer. The all-ones local cursor/index values are the actual first-call inputs, but their semantic meaning (for example, “latest”) is not named by this call alone. The wrapper may clamp calibration fields before calling the reader, and later transforms/clears the copied record; the post-wrapper buffer is not necessarily a raw ring record.

## Memory bounds, sequence protocol, and unresolved lifecycle

For a valid ordinary-memory source and a canonical slot index 0..7, the data loads reach through source offset `0xA7` (the ring payload begins at `+0x28`, has eight 16-byte slots, and contains a 16-byte copied record). The header reads at `+0`, `+8`, and `+0x10` also require readable source memory. A positive request needs valid, writable count/timestamp/index outputs and writable output space for up to `min(requested,7)` records; the H2 caller requests one record and therefore supplies a 16-byte output. Pointer validity, alignment, object extent, aliasing, and fault order are not checked by the function.

The snapshot/recheck resembles a sequence-consistency protocol but has no explicit memory barrier, atomic access, lock, or bounded retry. A producer that keeps changing the three snapshot fields can make it spin indefinitely. The reader neither identifies nor calls the producer, does not establish that the payload is coherent with the header, and cannot prove freshness, cadence, physical control mapping, device identity, scheduler ownership, or lifetime. Overlapping source/output/out-parameters and noncanonical/negative/overflowing index values are outside the supported domain until separately characterized.

The existing `tools/h2_11c5ec_experiment.py` intercepts `0x0012A758` with a controlled seam. It records the six arguments, writes a fixture count/record/cursor outputs, and returns a controlled `r0`; it does not execute this 424-byte body. Thus the existing wrapper differential/compositions validate the `0x0011C5EC` behavior given that seam and actual caller ABI, not the real ring read, branch calculation, copy, retry, or producer lifecycle.

## Conversion recommendation

A readable C++ translation is semantically feasible while retaining the direct memory operations and signed 64-bit comparisons. The function has no external helper dependency, but its signed remainder-by-8 and unbounded sequence retry must be preserved; do not replace retry with a fixed retry count or use unsigned `%` without matching the ARM negative case. The 424-byte slot is 106 ARM words and the original occupies the whole span; static analysis cannot establish whether typed C++ will fit. Compile a focused candidate before making an in-place placement claim. If it is larger, keep readable semantics and decide placement separately rather than shrinking via opaque assembly.

The direct differential should cover requests `INT_MIN,-1,0,1,7,8,INT_MAX`, signed index boundaries and all zero/negative index branches, every cursor/pair comparison branch, ring slots 0..7 and wrap, count outputs 0..7 and the case where computed count is nonpositive, stable snapshots and mutation at each recheck field, retries where output is partially written before retry, exact commit store order, preserved `r4-r11`/SP, caller-saved register effects, and the path-dependent raw return. Include negative controls for signed pair compare, cap 7, ring modulus, field offsets, snapshot comparisons, and output/cursor commit ordering. Separately compose exact caller tuple `(r2=1, timestamp=UINT64_MAX, index=UINT32_MAX)` and compare both direct reader and wrapper results; retain a controlled seam only as a separate wrapper test, not as evidence for this body.

## Provenance and checks

- Reference image SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- Original 424-byte function SHA-256: `a623c194afbc2bd075a18614cfcc517ca1ed7e2dad4812a77b9096235a46e68c`.
- Target source SHA-256: `5cc64cf2df2c681b59dd2f581bc007fbc18662879f351d924d56564d8fb1cd82`.
- All declared run002 input hashes recomputed successfully.
- Read-only checks: `python -B tools/split_asm.py --addr 0x0012a758 --limit 1`; `python -B tools/split_asm.py --addr 0x0011c5ec --limit 1`; pinned wrapper/record/runner inspection; packet SHA-256 verification.

No source, ledger, README, board, build cache, or emulator state was changed.


Coordinator countercheck: direct execution of the pinned original at `0x0012A758` with a stable positive one-record case returned `r0=0x00530020`, the supplied `index_inout` pointer, with count 1 and committed index 3. This disproves the earlier source-pointer-only return description; the conversion and direct differential must cover both early and stable return paths. The same observed execution preserved the callee-saved contract, but does not characterize caller-saved register values.
