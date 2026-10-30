# H2 production integration: `UiConfig_FillPair`

## Result

Prepared a readable production implementation of `camp_func_0027edf8` at its
original VMA `0x0027EDF8`, preserving the 24-byte slot and patching it into the
reviewed mapper-extended H2 image. The C++ performs defined unsigned low-byte
replication; empty register constraints keep Clang from replacing the shift/OR
steps with a larger literal multiply. Two target-specific ARM `str` instructions
preserve the original eight-byte store footprint and support the halfword-aligned
caller found at `g_ConfigWork+0x76` without a misaligned `u32*` dereference.

This is an offline integration package awaiting independent review. It does not
establish allocation success, complete game behavior, or Azahar/runtime acceptance.

## Caller and implementation contract

The pinned-image caller audit found seven direct ARM `BL` callers. Six pass
offsets divisible by four when their object base is word-aligned; one passes
`g_ConfigWork+0x76`, which is halfword-aligned under that base assumption. The
H2 initializer and later titleConfig reset use `TitleConfigWork+0x1C`, with an
eight-byte span inside the declared `0x158`-byte workspace. The allocator's
success/alignment behavior and dynamic object extents remain assumptions to
record. See [the caller audit](h2-pair-fill-caller-audit.md).

The candidate accepts a `u8*` and `u32`, masks the low byte, replicates it with
unsigned shifts and ORs, then writes the same replicated word twice. Register
constraints are compiler barriers only; the inline ARM stores deliberately
retain the original machine access width. The domain is eight writable bytes of
ordinary target memory. Fault, MMIO, and concurrent-observer behavior are not
claimed. The helper does not read memory and does not call out.

## Build and image evidence

Production source SHA-256:
`b5e511d0bae599ac38a13b6df68918444c00aece51ebcb760e0817897c18adf8`.
Production TU object SHA-256:
`b59d0fa7d71b58be50b08ef10a9c0061816c5b37c3f23c5318a39313869bd3e3`.
The extracted function is 24 bytes, relocation-free, with body
`7110efe6011481e1011881e1001080e5041080e51eff2fe1`. Relative to the pinned
original, only the first instruction changes from `and r1,r1,#0xff` to the
semantically equivalent `uxtb r1,r1`; the two ORRs, stores, and return are
unchanged.

Reproducible patch command:

```powershell
python tools/h2_pair_fill_production_patch.py --output build/agent-work/H2-semantic/h2-pair-fill-production-integration/run-003/checks/production-fill-patch
```

Patch manifest SHA-256 is
`1969152fd1215c901883c5cadcf3b19314255df7bab418e501809342e8728a35`.
The incremental IPS SHA-256 is
`5b0a75a1526aec8db88b0f02cf0f9eef98e657a51a5b2bb5e1993932b9d5a4c2`.
The resulting image SHA-256 is
`5e9aa08b449985f012e24400c45b4b037e4a0d5d069723b6cfa7ccf83300d8fa`.
The patcher verified its IPS round trip and scanned all 10,967 ledger spans plus
aligned words in the full code image; it found no covered direct branch or
absolute pointer into the function interior. Computed/indirect targets and
non-ledger interpretations are outside that scan.

## Differential and caller results

`python tools/h2_pair_fill_production_experiment.py --output build/agent-work/H2-semantic/h2-pair-fill-production-integration/run-004/checks/helper-differential`
passed 4,096 cases: every low-byte value under four high-bit patterns, crossed
with destination byte offsets 0 through 3. Original and candidate write sets
matched, and a wrong high-byte mask was detected as a data-memory mismatch.
Report SHA-256:
`208a4df775ec281a9467538acab60c6f6c6b99685c075f9376368d4d63a98d6b`.

The focused patcher tests passed 4/4. The extended final image passed the
combined offline suites: Calc 16/16 sequences and 54/54 ticks, Draw 46/46,
Secondary 34/34, initializer 10/10, and ready gate 4/4. Report SHA-256:
`8cc19997ae04b54791fb383c711859fbfa5d7a27288b2c30c15ba7b711263f7a`.
The State-9/10 caller composition using the same final image passed 3/3 and
detected the wrong Calc callback control. Report SHA-256:
`6369612ea7d681cd43f99d107ad1f7db60c2ae69a522185efe4450a457d35cb4`.

These caller and combined runs execute the production initializer, ready gate,
and mapper bodies where specified, while retaining HLE boundaries for task
scheduling, allocator/factories, rendering/resource setup, input delivery,
asynchronous assets, sound, and reset services. They are offline ARM simulation
evidence, not a running Azahar scenario.

## Review and next step

Independent production review is in progress. After review, update the function
record and ledger to `non_matching` if the promoted source remains non-identical,
and synchronize the H2 milestone. Keep H2 open until Azahar input, editing,
cancel/confirm, persistence, and restart behavior are compared against the
original under the authorized CLI-only workflow.
