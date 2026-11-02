# Independent implementation review: `0x002B8D24`

## Scope and frozen inputs

Read-only review of the assigned run-001 packet, candidate, differential runner, function record, prior static contract review, original pinned code and compiled production preview. No canonical build or emulator was run. Every path/hash in `task.json`'s `input_sha256` map still matches its recorded SHA-256. The reference image is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.

The candidate's behavior matches the exhaustive static selector contract for its documented domain: unsigned selectors `>=19` return raw `object`; selectors 0/13/14/15 return `object`; groups 1/10, 2–5/16–18, 6, 7–9, 11, and 12 issue the documented helper calls, preserve their order, and return the documented raw value. Case 6 compares the raw word at `object+0xE4` to `0x3F800000`, returning the original bits on mismatch; this is not numerical float equality. Case 12 checks all five flag bytes and clears the word at `object+0x28` after the loop. The fixed dependencies `0x002AF854`, `0x002BF030`, and `0x001384F0` are called with even ARM addresses and the correct argument order. The candidate does not claim to reconstruct their deeper behavior.

## Build, size, and runner review

The handoff reports `python tools/h2_8d24_experiment.py` exit 0 and the task-owned production-preview TU compile exit 0. The preserved runner output reports 116 direct comparisons, two compositions through original `0x00286928`, and seven detected controls. I inspected but did not independently rerun that executable evidence. The runner enumerates selectors 0–19, `0x80000000`, and `0xffffffff` on two seeds; it adds six raw case-6 words and all 32 case-12 masks. The seven source mutations are uniquely applied and must each differ (a mutant-only Unicorn fault counts as detection). The candidate retains the original callees. Its caller case uses the original `0x00286928` selector-11 path and asserts completion; it does not compose the other real caller sites.

I independently extracted both object symbols. `candidate-final.o` contains a 356-byte `candidate_002b8d24` body with no relocations (object SHA-256 `b3e97d3adbba27b0a3416bc4026d1827625190e4037a516844028e2a9fbdef8c`). The production-preview TU object contains a 356-byte `battle_func_002b8d24` body, also without relocations (object SHA-256 `b7ac3a905840200c86f4d5371e72aa35a7fb609e03c7e43ca9320de37722f032`); its function bytes are identical to the candidate. Thus it fits the 360-byte ledger slot with four bytes to spare. The production source and ledger remain unchanged.

## Real caller audit: `s0`, FPSCR/CPSR, and return use

I scanned pinned ARM direct branches to `0x002B8D24` and inspected each call window. Thirteen direct BL sites are present:

- `0x00114E34`, `0x00114E64`, `0x001157F4` in `Camp_DemonicaArchiveLoad` (`0x00114374` ledger range).
- `0x002016B0` in `camp_func_00201690`.
- `0x00235594` in `script_vm_func_0023554c`.
- `0x00286A18` in `engine_func_00286928`.
- `0x002899A8` in `script_vm_func_00289984`.
- `0x00297158` in `shop_func_00297128`.
- `0x0029D00C` and `0x0029D030` in `camp_func_0029cee4`.
- `0x002ED52C` in `func_002ed50c`.
- `0x002F6258` and `0x002F6280` in `camp_func_002f61c4`.

Each visible caller loads `r1` from a byte field before the BL. At all 13 return sites, the first instructions are unconditional stores, moves, or an unconditional branch; `r0` is ignored. No caller reads `s0` or executes `VMRS`/another FPSCR read after the call. The next conditional uses in the longer paths follow an explicit `CMP`. The case-6 difference in transient caller-clobbered `s0` and condition flags therefore has no observed dependency at these direct call sites. In `0x00286928`, the post-call code stores `sb` and `r8`; its later `VSTR` saves input `s16`, not `s0`. This is a static caller audit, not proof about unobserved indirect calls or runtime-only dispatch.

The earlier `docs/agent-work/h2-2b8d24-contract-review.md` incorrectly attributed `0x0029D00C/0x0029D030` to `script_vm_func_0029af60`. They belong to `camp_func_0029cee4`. `0x0029AF60` itself has no direct BL to `0x002B8D24`; it calls `0x002AEC80`, which calls `0x00144918`. I found no static evidence that this indirect/transitive path reaches `0x002B8D24`, so it is not counted as a proven caller. The function record's reference to two VM call sites “in `0x0029af60`” should be corrected before promotion. I found no direct ARM branch, Thumb BL/BLX, or literal word reference into `0x002B8E88`, the final four-byte `POP {r4-r6,pc}` left after a 356-byte replacement. This is a static reference scan; the integration patch should still explicitly pad or overwrite the four-byte remainder and audit the actual staged image.

## Limits and recommendation

The two fixtures cover null lists/empty manager and disjoint ordinary-RAM lists/eight all-marker records. They do not establish aliasing between list and object fields, arbitrary faults/MMIO/concurrent mutation, all manager table patterns, or the positive-record `0x00138934 -> 0x002BDAC0` service branch. Candidate semantics are supported only within the bounded domain in the contract and function record. The two `0x00286928` compositions do not establish behavior at the other direct callsites, a cumulative patched image, or the H2 runtime scenario.

No candidate defect was found in the reviewed fixtures and all tested selector branches are represented. **I do not recommend production placement yet.** Before placement, correct the function record's caller attribution, establish that the actual callers satisfy the disjoint ordinary-RAM/dependency domains (or characterize the uncovered service/alias cases), then verify final-image ARM interworking and the four-byte tail policy. After placement, update the ledger to `non_matching`, run the offline caller gate on the actual staged image, and continue the separately defined paired H2 runtime comparison. This review is read-only and does not promote the candidate.
