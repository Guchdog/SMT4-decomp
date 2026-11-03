# Independent review: 0x0011C5EC input-state reader contract

## Recommendation

**Ready for a bounded C++ implementation attempt**, with the scope and exclusions in the contract. I found no material branch, call-order, argument-mapping, write-order, or return-value error in `docs/agent-work/h2-input-state-reader-contract.md`. Keep the seven direct callees original initially and validate their interactions as a separate composition; this static review does not establish runtime reachability or physical input behavior.

## Independent checks

- Recomputed all ten `input_sha256` entries in the frozen `run001/task.json`; all matched. The pinned `code.bin` hash is `1f98884f…cfaa558`, and source/ledger hashes match the packet.
- Independently decoded the wrapper and direct callees as ARM from `extracted/exefs/code.bin`. The 40-byte stack frame and the early mode gate are correct. `0x0011C60C` calls `0x00128C2C`; its nested `0x00138F34` loads byte `0x0047388B`, and the wrapper returns zero on byte value 4 before context/output dereferences beyond its local sentinel initialization.
- Confirmed the calibration call and signed clamp fields/order; the six-argument `0x0012A758` call maps r0-r3 to object, output, request 1, and count pointer, with caller `[sp+0]` pointing at local u64 (`sp+0x10`) and `[sp+4]` at local index (`sp+0x0c`). The wrapper checks the signed count local and returns zero when it is non-positive. It ignores the helper return register.
- Confirmed the normalization call's fifth argument is the sign-extended output halfword at `+0x0c` at caller `[sp]`, with the other sample and pointer arguments in the stated registers. Selector dispatch 0/1/2 and invalid-selector no-call behavior match the contract.
- Confirmed the conditional context+0x30 transfer/clear, bit-0x2000 clear, derived `+4`/`+8` masks, global signed-byte short circuit, zero-store order (`output+0`, `+8`, `+4`, `+0x0c`, `+0x0e`), context+8 save, optional `0x0013BCAC` call, and final return one. The save precedes the optional postprocess.
- Verified literals at `0x0011C718` and `0x00138F40` resolve to `0x00471AD8` and `0x00473888`; the latter plus three is the tested mode byte. An aligned ARM direct-branch scan found one direct BL at `0x001078E8` and no B to the target. This does not exclude Thumb, indirect, or dynamic callers.

## Bounded seam and remaining limits

The proposed initial seam is sound: implement the wrapper with original callees and valid, disjoint context/output/source fixtures; separately control/stub dependencies to cover branches and record register/stack arguments and ordered writes. Then compose the original `0x001078D8` caller with the real reader. Candidate evidence should include count<=0 and count>0, mode byte 4/non-4, all selector choices, clamp boundaries, both flag paths, short-circuit combinations, and postprocess enabled/disabled.

No claim is established here about real hardware controls, input freshness, scheduling/cadence, runtime reachability, concurrent source mutation, aliasing, malformed ring states, or fault behavior outside valid mappings. No C++ conversion, compile, ARM execution, differential test, caller execution, or emulator test was performed in this review.

## Commands and provenance

- `python -c` packet hash recomputation: exit 0; all ten declared inputs matched.
- `python -c` literal reads plus branch scan: the combined exploratory command first exited 1 after the hash/literal output because Capstone instruction detail was not enabled for the scan. Re-running the scan with `md.detail=True` exited 0 and found only `0x001078E8: BL 0x0011C5EC` among aligned ARM direct branches.
- The packet's frozen image, source, contract, caller record, and tool hashes were unchanged during review. No implementation or shared files were edited.
