# H3 title-entry placement follow-up (120-byte candidate)

## Result

This follow-up supersedes the prior 136-byte placement assessment; that assessment described the previous candidate build. The current candidate symbol is 120 bytes and fits exactly in-place at `0x0030A9A4`, the original function window `[0x0030A9A4,0x0030AA1C)`. No entry trampoline or shared-cave allocation is needed for this in-place route. This establishes placement feasibility only; no replacement image was produced.

The current H1/H2 composed image remains `build/agent-work/H2-semantic/h2-init-ready-final-image/run-013/combined-build-final/code.combined.bin`, SHA-256 `7b2bc2983a890e1c4cf1ae71beca9f574260d98d6cfcdffb3bbb34bd3eb2b291`. In it, the 120-byte original H3 window is byte-for-byte unchanged from the pinned original; both window hashes are `c3d806fc13f5f57ce10915ddcd96805586cfdd8d186cb262266fefffe15a2996`. The next function begins at `0x0030AA1C`; its first 16 bytes are `f0412de90050a0e10010a0e30100a0e1` in both images. The 4-byte literal at `0x0030AA18` is `0x0044DE28` in both.

## Candidate and final-VMA relocations

- Source SHA-256: `1bc1bdfe6fb6abf637c4fc1ace3566c5a93b765d799f6ec2f15ffe57ad4d4966`.
- Candidate object SHA-256: `99f340df1497516e5214f6977289361461a1f8102250ec31165bd19e1f04aed9`.
- Symbol `h3_title_load_entry_candidate`: 120 bytes; exactly two ELF `R_ARM_CALL` relocations, no other relocation entries.
- Relocation at function offset `16`, final instruction VMA `0x0030A9B4`: `h3_original_save_load_ui_calc` → `0x00202950`. ARM BL displacement is `-0x10806C`; expected final word is `0xEBFBDFE5`.
- Relocation at function offset `60`, final instruction VMA `0x0030A9E0`: `h3_original_get_presentation_point` → `0x002BF6D0`. ARM BL displacement is `-0x4B318`; expected final word is `0xEBFED33A`.

Both targets are word-aligned ARM code addresses (bit 0 clear), and both displacements fit ARM BL's signed ±32 MiB range. The existing caller at `0x001EA348` is an ARM BL to `0x0030A9A4`, also bit 0 clear. The candidate object is compiled for ARMv6K ARM state. The candidate's final word at offset `116` is the manager literal `0x0044DE28`; its PC-relative load remains within the exact 120-byte replacement window.

## Required integration integrity assertions

1. Freeze and hash the current source, object, pinned original, and exact H1/H2 composed image before integration. Confirm the object/build flags and the two symbol-named `R_ARM_CALL` records.
2. Resolve the relocations at `0x0030A9B4` and `0x0030A9E0` to the targets above; independently decode both resulting BLs and verify target mode/bit 0.
3. Write exactly 120 bytes to `[0x0030A9A4,0x0030AA1C)`. Assert every byte outside that interval is identical to the H1/H2 input. Specifically verify the `0x0030AA1C` next-function entry and H2 integrity regions are unchanged.
4. Verify the manager literal and all PC-relative loads at their final VMAs; retain the candidate's required ARM state and return behavior.
5. Serialize and independently replay IPS, compare the full output image hash, then run H3 final-image differential and caller-composition checks with a wrong-target or wrong-body negative control. Runtime remains `not_run` until separately assigned.

## Evidence and packet status

This is read-only placement analysis. The two candidate object files already exist; this follow-up did not compile, patch, run tests/runners, build, or launch an emulator. Existing H3 differential and caller-composition reports are separate and do not prove the final in-place image.

The old `run-001/task.json` pins the previous source hash and is stale for this follow-up. The coordinator repaired the H3 dependency graph, and `run-002/task.json` was successfully prepared with the current candidate source hash. Its task goal text still says “136-byte” although the newly pinned source compiles to a 120-byte symbol; this report and run-002 input hash identify the current 120-byte candidate. No board file was edited.

## Handoff (current evidence only)

```json
{
  "task_id": "h3-title-entry-placement",
  "owner": "h3-placement",
  "outcome": "ready_for_review",
  "report": "docs/agent-work/h3-title-entry-placement.md",
  "source_sha256": "1bc1bdfe6fb6abf637c4fc1ace3566c5a93b765d799f6ec2f15ffe57ad4d4966",
  "object_sha256": "99f340df1497516e5214f6977289361461a1f8102250ec31165bd19e1f04aed9",
  "h1_h2_image_sha256": "7b2bc2983a890e1c4cf1ae71beca9f574260d98d6cfcdffb3bbb34bd3eb2b291",
  "placement": "in-place [0x0030A9A4,0x0030AA1C), 120 bytes",
  "relocations": [
    {"offset": 16, "type": "R_ARM_CALL", "target": "0x00202950", "expected_word": "0xEBFBDFE5"},
    {"offset": 60, "type": "R_ARM_CALL", "target": "0x002BF6D0", "expected_word": "0xEBFED33A"}
  ],
  "evidence": {"compiled": "not_run", "arm_differential": "not_run", "caller": "not_run", "runtime": "not_run"},
  "blocker": null,
  "unblock_condition": null,
  "next_action": "integrator resolves the two BL relocations, enforces exact 120-byte write bounds, and runs final-image offline checks"
}
```


