# Independent review: type-1 callback `0x00151404`

## Verdict

**Partial pass for the isolated callback contract and the stated synthetic test
domain.** The candidate preserves the two pinned helper boundaries, represents
the original unordered `VCMPE`/`BLE` behavior explicitly, and the compiled
candidate matches the pinned ARM callback in the ten completed directed cases
on return `s0`, FPSCR, `r4-r11`, `d8-d15`, SP, data-change status, and captured
direct-helper arguments. Both deliberate mutations are detected. The positive
infinity case reaches the same exceptional path and faults at the same PC; it
does not return and is not a successful equivalence case.

This review does not support integration or runtime/H1 equivalence. The helper
implementations remain pinned originals; caller selection and production
placement are unproved; the tests use synthetic state; and the exception is
limited by the emulator's read-only text map.

## Independent checks

- The frozen review packet's hashes match the reviewed candidate, runner,
  function record, producer report, and pinned image digest. The report's
  compiled object is 144 bytes for the candidate symbol, with 128 executable
  bytes, 16 bytes of bounded literal tail, no relocations, and an ordinary
  `pop {fp, pc}` return.
- The ARM body contract is consistent with the code: save start; zero interval
  returns start; otherwise compute sample-relative delta; unordered `BLE`
  takes the no-wrap path; the other path uses the original integral-float
  helper; both converging paths call the original two-argument float-difference
  helper and add start.
- The inline VFP comparison in the source is necessary: using C++ ordered `<=`
  would diverge for NaN. The negative control demonstrates this divergence.
  The skip-integral-helper control also diverges as intended.
- Direct helper boundaries are consistent with observed arguments:
  `0x002A337C` receives the quotient in `s0`; `0x0014D608` receives adjusted
  delta and interval in `s0/s1`. No claim is made that either helper is
  reconstructed.
- All ten completed candidate cases list no mismatches and the exceptional
  positive-infinity case lists the same fault at `0x002A4656` for both runs.
  The four synthetic boundary/interval classes plus NaN and the positive
  infinity limit are represented in the case list. Static caller evidence
  supports the stated float inputs/returned `s0` use, but does not prove the
  runtime callback is selected.

## Evidence boundaries

The runner checks equality of the final stack pointer and records only a
boolean `stack_changed`; it does not compare stack bytes or exact stack
read/write sequences. Likewise, for ordinary cases it compares whether the
data region changed rather than byte-level memory effects. Thus this evidence
supports the callback result/register/helper-argument contract under its
synthetic harness, but is not a complete memory-trace differential. The
positive-infinity fault occurs before return, so post-return ABI preservation
is not observable there. The runner records incidental `r0` but correctly
excludes it from the callback contract.

**Review classification:** partial pass; retain as an experimental candidate
only. Next useful evidence is independent review of the original float helper
contracts and a justified caller scenario; do not promote on this isolated
differential alone.

## Reviewed hashes

- Reference `code.bin`: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`
- Candidate source: `837f79c6d65d00450050e1b79354b6d534b26fc8026fd576f19d92e1fb80a358`
- Runner: `d248baf3b1a4a31b0368039fdea5d0227ff866c7cc39f708c9f932242dc62bb8`
- Producer report: `50147c654ee47d5751ec6548a0ca1b79dc591b83c72130661ac97458d4d71e8b`
- Candidate object: `3af66ebca4a88664e0063cbf3f35fa17bb99211f03cf8de6e6987f7a2e9ba008`
