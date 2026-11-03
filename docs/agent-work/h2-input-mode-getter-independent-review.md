# Independent review: H2 input mode getter `0x00138F34`

## Finding

The candidate matches the pinned getter contract for ordinary mapped memory: load the unsigned byte at `0x0047388B` and return its zero-extended value in `r0`. The original ARM body loads the literal-backed pointer, executes `LDRB [r0,#3]`, and returns via `BX LR`; the candidate uses a volatile `u8` read. The compiled body is 16 bytes in the 16-byte slot with no relocations. The entry target is even ARM.

The original wrapper at `0x00128C2C` calls the getter at `0x00128C30`, compares the raw result with 4, and returns true only for byte value 4. The original reader at `0x0011C60C` calls that wrapper and branches to its early return when the wrapper result is nonzero. Thus modes other than 4 continue through the ring-reader path, including high-bit byte values.

## Fresh validation

All 13 frozen run001 input hashes matched. The fresh final-VMA runner compiled the production TU to private output and passed all 256 byte values with no differences in raw return, SP, or `r4-r11`. Its 14 compositions through the original reader covered modes `0, 3, 4, 5, 0x7f, 0x80, 0xff` and ring results 0/1. The mode-four path skipped the ring call; the other modes continued. A signed-load mutation was detected on a high-bit value.

The runner has no seed option; its direct coverage is exhaustive and its directed composition matrix includes the signed-byte boundary values. I added a seeded supplemental comparison with 64 random mode-byte/ring-count pairs using seed `20261229`; all matched between original and staged images through the original reader and controlled ring-reader seam.

The wrapper call at `0x00128C30` resolves to even ARM target `0x00138F34`; the reader call at `0x0011C60C` resolves to wrapper `0x00128C2C`. The one-slot IPS replay exactly matched the staged image and changed bytes only inside the 16-byte getter slot. The converted bytes differ from the original; the ledger classifies the function `non_matching`.

Fresh artifacts:

- Runner report SHA-256: `65680e7c7901ec6702208a7ccb189e8418b47067dc1e8db427e6c3905f27503d`
- Seeded reader report SHA-256: `b70ae43835bb0efc438193e28e4fb720b3fecb624ee91558f9c56d6394dbf535`
- Production source SHA-256: `6e0ca93d7dd7bc0739aa84c95b38cb9b13d7f4526eaf33b83142467319f2c564`
- Production object SHA-256: `ea700dd2c60de00664e60320fcc574cb632371bc2946aa9d85aeba895cc3d196`
- Candidate body SHA-256: `fd59decda82c2f0b3896f1c41334aa00cd56601cb6b57ec881611470fc427bd6`
- IPS SHA-256: `198bacf6aa8c7e6a4b0934f61fe1bf0925f4596f2c30cc79c712954a3bf5d916`

## Limits

Tests cover an ordinary mapped global byte and synthetic reader memory through a controlled ring-reader seam. The physical purpose and provenance of the mode byte, MMIO behavior, timing/scheduling, and full H2 runtime behavior are unproven. No emulator or canonical full build was run.

## Reproduction

```powershell
python tools/h2_input_mode_getter_experiment.py --out build/agent-work/H2-semantic/h2-input-mode-byte-getter-review/run001/checks/fresh-exhaustive
```

The supplemental original-reader comparison used Python seed `20261229` and wrote `seeded-reader-review.json` beside the runner report.
