# H3 final image independent review

Owner: `h3-final-review`  
Task packet: `build/agent-work/H3-semantic/h3-final-image-review/run-001/task.json`  
Reviewed checkout: `C:\Users\altair\.codex\worktrees\semantic-equivalence-experiment\SMT4decomp` at `1f1179b8cdf22c3e4a5343cb8a528fde64f5aaeb`.

## Review result

**Offline review passes for the assigned scope; candidate is suitable to proceed to the separately owned runtime scenario.** This is not whole-game equivalence. The candidate remains a 120-byte ARM implementation at `0x0030A9A4` with original dependencies `0x00202950` and `0x002BF6D0`.

- Candidate SHA-256: `1bc1bdfe6fb6abf637c4fc1ace3566c5a93b765d799f6ec2f15ffe57ad4d4966`.
- Candidate object SHA-256 (rebuilt by the patch and caller runners): `99f340df1497516e5214f6977289361461a1f8102250ec31165bd19e1f04aed9`.
- Original image SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- Pinned H1/H2 base SHA-256: `7b2bc2983a890e1c4cf1ae71beca9f574260d98d6cfcdffb3bbb34bd3eb2b291`.

## Independent patch and branch checks

The candidate occupies exactly `[0x0030A9A4, 0x0030AA1C)`, 120 bytes, at file offset `0x20A9A4`. The H1/H2 base bytes in that window equal the pinned original. The inserted little-endian ARM `BL` instructions decode as follows:

| Source | Word | Decoded target | ARM/alignment check |
| --- | --- | --- | --- |
| `0x0030A9B4` | `0xEBFBDFE5` | `0x00202950` | ARM BL; target low bit 0; word aligned |
| `0x0030A9E0` | `0xEBFED33A` | `0x002BF6D0` | ARM BL; target low bit 0; word aligned |
| Caller `0x001EA348` | `0xEB048195` | `0x0030A9A4` | Preserved caller ARM BL; target low bit 0; word aligned |

The helper only accepts the two declared `R_ARM_CALL` symbols, requires ARM `BL` sites and rejects odd targets, unaligned/range-invalid displacements, and any relocation count other than two. No Thumb function pointer is introduced in this patch; the caller and both direct-call targets are ARM addresses with bit 0 clear.

The final image differs from H1/H2 only within the exact 120-byte entry window. I independently decoded the standard IPS literal/RLE records (495 records), replayed them onto the pinned original, and got the exact final image. IPS SHA-256: `b11128bd8b6510accb502f15423fabc5cf69999b01610ed7aadff31f5d5a7b8e`; final image SHA-256: `af2bc749364703ac11d1b663527a1ea339c571e14f89e0aa4e919c58f71436d8`.

## Commands and evidence

All newly generated check outputs were placed in the permitted writable E: checkout under:
`E:\SMT4decomp\build\agent-work\H3-semantic\h3-final-image-review\run-001\checks\`

| Command | Exit | Result/output |
| --- | ---: | --- |
| `python tools/h3_title_load_entry_experiment.py` | 0 | Direct ARM differential passed: zero, signed min/max, negative, and positive signed-halfword cases; wrong `+8` to `+6` negative control detected. Captured stdout: `checks/direct-differential.json`. Original dependencies are deterministic HLE stubs. |
| `python tools/h3_title_entry_patch.py --output E:\SMT4decomp\build\agent-work\H3-semantic\h3-final-image-review\run-001\checks\patch-composition` | 0 | Recompiled 120-byte candidate; both relocations linked; exact-window checks and IPS round trip passed. Report: `checks/patch-composition/report.json`; emitted image and IPS are in the same directory. |
| `python tools/h3_title_caller_composition.py --output E:\SMT4decomp\build\agent-work\H3-semantic\h3-final-image-review\run-001\checks\caller-composition --patched-code E:\SMT4decomp\build\agent-work\H3-semantic\h3-final-image-review\run-001\checks\patch-composition\code.h3-final.bin` | 0 | Caller differential passed on candidate and in-place final image; caller guard skip matched; next state 8; wrong-state negative control detected. Report: `checks/caller-composition/report.json`. |
| `python -m pytest -p no:cacheprovider tests/test_h3_title_caller_composition.py -q` | 0 | `1 passed in 0.96s`. Pytest stdout also included two `Windows fatal exception: access violation` traces at Unicorn `mem_map` (`tools/h3_title_caller_composition.py:85`) from this test. Treat the native-crash traces as a test-process anomaly despite pytest's zero exit and passing assertion; the direct caller runner above completed normally. This test was not repeated. |

The patch and caller runner report source/object hashes consistent with the packet and each other. The direct differential runner reads the existing `build/agent-work/H3-semantic/h3-title-entry/direct-call-obj/h3_title_load_entry_candidate.o`, whose source was independently confirmed at the packet hash; it prints rather than writes its report, so stdout was saved as shown above.

## Freeze drift and limitations

One declared read input changed after the packet snapshot: `docs/function-records/0x0030a9a4.md` was expected at SHA-256 `aa756a2a3ff8163d266a90ade2bbda83d9b730254b76d9c64bcdc0e799f6ec3d`, but currently hashes to `e046bf380d8878240d9528e67d361839c2d1a0c3b3a0d5f0545f3c810cad9446`. Other packet input hashes checked in this review matched. The candidate, helper, patcher, caller runner, and pinned reports stayed frozen. This drift did not change the tested source, image pins, or function body, but the coordinator should refresh/reconcile the record before the handoff is machine-checked.

Differential and caller checks use deterministic stubs for `0x00202950`, `0x002BF6D0`, and caller dependency `0x002A7604`; their internal behavior is not validated. Caller coverage is limited to the state-7 success gate and its nonzero skip guard; polling state 8, downstream save/load handling, allocator behavior, UI scheduling, and scene transition are not covered. No emulator/runtime scenario was run by this reviewer.

## Next action

Reconcile the function-record hash drift and note the pytest Unicorn teardown/access-violation output. Then the assigned runtime owner may run the autonomous offline-gated original-versus-final scenario. Preserve the no-runtime scope of this review.
