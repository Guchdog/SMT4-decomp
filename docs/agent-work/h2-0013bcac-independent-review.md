# Independent review: H2 input postprocessor `0x0013BCAC`

## Recommendation

The candidate is supported for its bounded contract: sequentially update record words at `+4` and `+8`, conditionally move word `+0` bit 4 to bit 8, clear bit 4 in `+4` and `+8`, and return the final raw word at `+8`. Fresh final-VMA and caller-composition evidence passed. Keep the current ledger classification `non_matching`; the compiled bytes differ from the pinned original.

## Contract audit

I disassembled the pinned ARM body `[0x0013BCAC,0x0013BD80)`. The first conditional transition sets current word bit 8 when any of these holds: current bits 4 and 8 are both set; current bit 4 is set while prior word bit 8 is clear; or current bit 8 is set while prior word bit 4 is clear. Otherwise it clears current bit 8. The helper repeats this logic for `+8` against prior word `+0` after storing the `+4` result. It then conditionally stores `(+0 & ~4) | 8` when `+0` bit 4 was set, stores `+4 & ~4`, and finally stores/returns `+8 & ~4`. Thus the observable store order is `+4`, `+8`, conditional `+0`, `+4`, `+8`; all unrelated bits are preserved. The original saves/restores `r4`, returns through `bx lr`, and restores entry SP.

The typed implementation uses volatile word accesses and has no relocations. Its 148-byte body fits the 212-byte slot, and the entry address is even ARM. The ledger row remains `non_matching`, which is truthful for the changed body.

## Fresh differential and composition

For the refreshed run002 packet, I verified all 19 frozen input hashes. The refreshed conversion note and function record now include the prior accepted independent review; their pinned SHA-256 values are `b5ff9c0fd872e1c2ec5b8c518bca1ea8cd7c9cb3945d4e3521624f513d5be78e` and `08e6d103fc0c8c25c595a936b4082a50de8bd8d8f20efbc71f8e1a30c945afbb`. The implementation source, runner and ledger remain pinned to the same content as before. I ran a separate fresh seed `20261229` into run002; it compiled the production TU to private output and passed:

- 192 direct cases: all 64 combinations of each word's bits 4/8 plus 128 seeded full-word cases; no differences in return, SP, callee-saved registers, record words, or non-stack writes.
- The mutation omitting the `(current bit 4 && current bit 8)` predicate was detected at `bit-matrix-04-00-08`.
- 32 cases through the original `0x0011C5EC` reader with the documented controlled ring-read seam; no differences. The optional helper ran in 16 cases, and in every such case `context+8` already matched output word `+0` at helper entry.

The pinned reader stores output word `+0` to `context+8` at `0x0011C6E8`, tests the optional-call gate, and conditionally calls the helper at `0x0011C6FC`. After that call it executes `add sp`, `mov r0,#1`, and restores registers, so the helper's raw return is discarded. The reader composition therefore confirms both the save-before-call order and the parent return behavior.

The runner independently replayed the 225-byte IPS to the staged image. My scope check found changed bytes only within the 212-byte slot (194 differing byte positions); the only call instruction to the candidate is an even ARM conditional branch from `0x0011C6FC` to `0x0013BCAC`. There are no candidate-body relocations.

Run002 report SHA-256: `336868d7105132026d6d3a50022346928e6863d5fa67b3932e104d7d92c351a7`. Its production source/object/body SHA-256 values remain `5cc64cf2df2c681b59dd2f581bc007fbc18662879f351d924d56564d8fb1cd82`, `df1b01a8cc49a52df34cc952b5631890f35860211fa1e417fe954ffd68d988be`, and `883a2c101cb126b989bc542800d1e195d85529758c5e39758763dbaf828d4078`. IPS replay matched the staged image; the 225-byte IPS changed 194 byte positions, all within the slot. The entry/caller branch is even ARM and the candidate body has no relocations.

## Limits

The supported domain is an aligned, fully mapped three-word record in ordinary RAM. The test excludes ABI save/restore scratch below SP from persistent-memory comparison. Invalid mappings and fault timing, concurrent observers, MMIO, physical input provenance, and H2 lifecycle/runtime behavior remain unproven. The reader composition uses a controlled ring-read seam and does not establish live input production. No full build or emulator run was performed by this review.

## Reproduction

```powershell
python tools/h2_13bcac_experiment.py --out build/agent-work/H2-semantic/h2-input-postprocess-0013bcac-review/run002/checks/review-seed-20261229 --seed 20261229
python tools/agent_workflow.py check-handoff --packet build/agent-work/H2-semantic/h2-input-postprocess-0013bcac-review/run002/task.json --handoff build/agent-work/H2-semantic/h2-input-postprocess-0013bcac-review/run002/handoff.json
```
