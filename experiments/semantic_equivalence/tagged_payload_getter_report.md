# Tagged relative-payload getter family

## Scope

This isolated experiment reconstructs two 24-byte ARM leaves as ordinary C++
helpers. It does not alter production sources or the exact-matching ledger.
The pinned image is checked by SHA-256 and by each function's original bytes,
ledger row, and direct `BL` site.

## Functions and observed behavior

- `0x003E6974`: if `*(u16*)base == 0x0300`, return the 32-bit sum
  `base + *(u32*)(base+4)`; otherwise return null.
- `0x003E69A8`: same contract for tag `0x4100`.

Both read the tag unconditionally and read the relative offset only when the tag
matches. Offset zero returns the original base. Direct callsites are pinned at
`0x003E71E4` and `0x003E7104`; those callers were not executed as full windows.

## Differential evidence

Reproduce with:

```powershell
python -m unittest tests.test_tagged_payload_getter_experiment -v
python tools/tagged_payload_getter_experiment.py --seed 20261024 --samples 1024 --output build/semantic-equivalence/tagged-payload-seed-20261024
python tools/tagged_payload_getter_experiment.py --seed 7 --samples 1024 --output build/semantic-equivalence/tagged-payload-seed-7
```

The focused module passed 4 tests. Each seed passed **2,064 function
comparisons** across both candidates; all four wrong-tag/wrong-offset controls
were detected. Valid and invalid tags, edge offsets including zero, and the
conditional memory-read footprint were checked. The ARM candidates are 28 bytes
each versus 24-byte originals, so they are not byte-identical.

Null-base probes faulted on the same read in Unicorn for both versions, but a
null base violates the valid contract and the emulator observation is not a
hardware/OS data-abort guarantee. Ordinary mapped RAM is the tested domain.
This is isolated differential evidence, not a title-track caller proof,
production integration, or game-level validation.
