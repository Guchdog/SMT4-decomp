# Independent review: logical input query `0x002C17D4` — run001

## Recommendation

The frozen run001 evidence supports proceeding with bounded semantic integration of the 92-byte query helper. I found no counterexample in the controlled direct matrix or the mode-2 dispatcher composition. The exact-slot candidate is relocation-free, fits its 92-byte slot, and is reached by both original ARM calls at `0x002C18F0` and `0x002C19B0` through the even ARM entry `0x002C17D4`.

One deliberate machine-access difference needs to remain explicit: original ARM reads the mode word with a 4-byte load; the compiled candidate uses a 1-byte load because only bit 0 affects the result. The frozen profile treats `0x004650A8` as aligned ordinary RAM and the harness compares address/order while recording the width difference. This supports the tested RAM semantics. It does not prove behavior for MMIO, unusual mappings, concurrent writers, or other domains where access width/observation itself matters.

## Frozen provenance and exact-slot patch

All 25 run001 packet input hashes recompute exactly. Key identities:

- Pinned image: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`
- Candidate source: `96edef236cc91508b242b0aa1e81a969137ed7477f9a687052b5ba4ed889666b`
- Production source: `c72dd70c13d5720208b073a6ff86b16473d7f2e03f9142c5c5151b59245e63c9`
- Candidate object: `6e566dee27733881d42b9075e6a267b03b4b8199543ff4a2e0de397e9485ee2f`
- Production object / focused `leaf_batch32_c.o`: `76056485f87a0e36f1874c7690ef076340fde6237f4560f5e90256e1f44be7ba`
- Conversion report: `f1f6e680d858a08307bd7ded0f84b8eda2355941c3b6053223878e08497f68a8`

Candidate and production bodies are both 92 bytes with no relocations, within the 92-byte slot at `0x002C17D4`. The report records staged image SHA-256 `4674b3d6b6864b69d90c0ad32d39a929cbd100b1b0eafa42f995c44320a44efc`, IPS SHA-256 `5f4414fade6508ca824f68ec5417cb7cf8786a398f5e0146addb493e505c9cb0`, successful IPS roundtrip, and 80 changed bytes confined to the declared slot. The two original call sites resolve to the even ARM entry; the candidate also returns via `BX LR`. The ledger classifies the byte-different source as `non_matching`.

## Contract and mode-load width

For unsigned ID `r0`, IDs `>=31` return zero before any query-table read. IDs 0–30 read the row at `0x004099C0 + 8*id`; a nonzero first word returns zero immediately and suppresses mask/mode/state reads. Otherwise the second word is the mask, the mode word at `0x004650A8` selects one of two fixed state words (`0x004E3C48` if bit 0 is set, `0x004E3C28` otherwise), and the return is normalized to zero or one according to `(state & mask) != 0`. The function makes no writes or helper calls.

The table bytes pinned in the original image have zero gates for IDs 0–15 and gate 1 for IDs 16–30. The report tests all 31 pinned IDs, out-of-range and high-bit IDs, both mode-bit selections with unrelated high bits, gates, masks and distinct state words. Four controls are caught: off-by-one ID bound, wrong table stride, wrong mode bit and inverted gate. The mode narrowing changes only the observed access width at the aligned mode address; the report correctly expects 4 bytes in original and 1 byte in candidate while checking the same address/read order and result. No claim of MMIO or concurrent-access equivalence is supported.

## Mode-2 dispatcher composition

The conversion runner builds the staged image from the pinned original image, replacing only the helper slot. Each caller run then executes the original `0x002C1830` dispatcher body from either the original or staged image, with the same controlled table, mode and state fixtures. Though the `wrapper_run` helper has an unused `original` parameter, its actual executable image is its `image` argument: the baseline receives the pinned original, and the staged profile receives the original image plus only the helper replacement. This does not introduce a dispatcher replacement into the comparison.

Seventeen cases cover IDs 3–6 through primary hit, secondary `id+9` hit, no hit, and both-bits-set short circuit, plus out-of-range ID 31. The trace confirms primary query first, secondary only after primary zero, the expected secondary IDs 12–15, return normalization, read addresses/order, and original-versus-staged equality. For the both-set cases, only the primary query runs. These cases exercise the dispatcher’s mode-2 composition around this helper, not the full dispatcher contract or natural mode-2 runtime reachability.

The other caller family at `0x0029F278` is statically mapped to four call sites and its `0x20` skip is documented, but this runner does not execute the full cursor-updater paths. The disagreement in earlier producer audits about refresh-table stride remains unresolved; this query itself reads fixed state addresses independent of ID, so that conflict does not create a counterexample to the tested helper behavior.

## Limits and next action

The direct matrix uses controlled table/state fixtures; mode-2 caller fixtures use the original dispatcher with controlled inputs. These do not prove physical-control meanings, producer refresh cadence, natural state transitions, runtime input delivery, table immutability, global concurrency, malformed-memory behavior, or the four full `0x0029F278` cursor paths. Runtime was not run, and I did not compile or execute the harness. Proceed with bounded semantic integration while retaining the 1-byte-versus-4-byte load caveat and the unresolved producer/cursor limits.
