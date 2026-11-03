# Independent review: paired H2 signed-byte getters

## Finding

Both candidates match the pinned helpers' bounded contract. `0x002BB978` reads the signed byte at `0x0044E362`; `0x002BC9C8` reads the signed byte at `0x0044E381`. The source uses volatile `s8` reads and returns the sign-extended value. The pinned originals use `LDRSB` and `BX LR`, so the byte access width, signed return, and leaf return behavior agree. The two candidates each occupy their 16-byte slot and have no relocations. Their bodies differ from the original, so the `non_matching` ledger rows are correct.

The original reader has direct ARM `BL` instructions at `0x0011C6B0` and `0x0011C6C0`, targeting even ARM entries `0x002BB978` and `0x002BC9C8`. It compares the first signed result with zero before the second call; any nonzero signed byte, including high-bit values, takes that call. The second result feeds the reader's clear/retain path.

## Fresh validation

All 16 refreshed run003 input hashes matched. The frozen runner compiled the production TU to private output and passed 512 direct cases, exhaustively covering all byte values for both getters. It compared raw return, SP, and `r4-r11`; all direct results matched and both raw returns were correctly sign-extended. Its 25 compositions through original reader `0x0011C5EC` matched outputs, state writes, and helper traces across `(0, 1, 0x7f, 0x80, 0xff)` flag values. The unsigned-load mutation was detected.

The runner has no seed option; its direct cases are exhaustive and its 25 composition grid is deterministic. To add fresh seeded composition coverage, I separately compared original and patched images through the same original reader and controlled ring seam for 64 random byte pairs with seed `20261229`; all matched.

The 50-byte two-slot IPS replays exactly to the staged image. Independent scope inspection found only four differing bytes, all inside the two 16-byte getter slots. Caller branch targets have bit 0 clear. The staged image SHA matches the conversion packet's pinned `0e5d2ca7abf4b86f65a5ab022f76a69083973e926bff5aae5d6018ed0a58318e`. I also summed the current ledger's `non_matching` rows: 70 functions and 21,092 original bytes, consistent with the README arithmetic.

Fresh evidence:

- Exhaustive runner report SHA-256: `8f1f4ae0fa7ca7f1bfe7067bcbffa413feb5f9637dd8627b33849ba32fb32dd0`
- Seeded parent report SHA-256: `6c7a120865e7b467af2a837e1fb8ad19e194060b809ad5196c592dc346aa116a`
- Production source SHA-256: `e27e7edb6ec8fc8345d62672cfb4d481102c3aa476d29ab4f311ee2700019585`
- Production object SHA-256: `bfb967d4e79be964a9d0a2efc5190b5fa40a379db52943ff5a530379cbfcaf93`
- IPS SHA-256: `96ab363abd2d6771ab46db2a11678e1313f25c1c27e652b89fadd5146bae4158`

## Limits

Evidence covers ordinary mapped globals and synthetic RAM fixtures through a controlled ring-reader seam. It does not establish physical input provenance, timing, scheduling, MMIO semantics, concurrency-visible access width, or full H2 runtime equivalence. No emulator or canonical full build was run for this review.

## Reproduction

```powershell
python tools/h2_input_flag_getters_experiment.py --out build/agent-work/H2-semantic/h2-input-signed-flag-getters-review/run003/checks/fresh-exhaustive
```

The seeded supplemental caller check was run with Python seed `20261229` and wrote `seeded-parent-review.json` beside the runner report.
