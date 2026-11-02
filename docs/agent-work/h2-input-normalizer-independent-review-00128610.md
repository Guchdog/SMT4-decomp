# Independent review: H2 input normalizer `0x00128610`

## Recommendation

**Ready for promotion review, within the validated domain.** I independently inspected the pinned ARM source and the typed dispatcher, reran the direct differential and original caller compositions with a fresh seed/output, and compiled the affected reader-consumer TU. No counterexample appeared in the exercised domain. The supported contract is the unsigned selector `0..255`, the three observed routes (`0`, `1`, `2`), and the no-call invalid-selector path, using valid disjoint ordinary-RAM fixtures. All three normalization callees remain original ARM and are dependencies, not reconstructed behavior.

This approves the dispatcher evidence only. It does not establish behavior for malformed pointers, aliasing/MMIO, callee arithmetic, device input provenance, live cadence, or whole-title behavior.

## Independent source and ABI audit

Pinned image identity is SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; all 14 declared task input hashes still match. I decoded all 37 ARM words in `[0x00128610,0x001286A4)` and the wrapper at `0x0011C5EC` directly from that image.

At dispatcher entry, r0 is the calibration pointer, r1/r2 are output-x/output-y pointers, r3 is full-width sample-x, and `[entry_sp]` is full-width sample-y. The helper reads an unsigned selector byte at `cal+0x0C`. Selector 0 uses signed halfwords at `cal+0` and `cal+6` and calls `0x0013B9FC`; selector 1 uses `cal+2` and `cal+8` and calls `0x0013B8F8`; selector 2 uses `cal+4` and `cal+0xA` and calls `0x0013BAE0`. The calls receive `(out_x,out_y,sample_x,sample_y)` in r0-r3 and the sign-extended calibration pair at `[sp]`/`[sp+4]`. Selector bytes 3 through 255 skip dispatch, preserve output, and return the original calibration pointer in raw r0. Valid paths return the selected callee's raw r0. The helper saves/restores r4 and returns with caller SP restored; the direct differential confirms r4-r11 preservation for exercised calls. The 16-byte total frame preserves 8-byte alignment.

The actual reader caller at `0x0011C5EC:0x0011C668` passes `context+0x0C`, `output+0x0C`, and `output+0x0E`; it loads both samples with `LDRSH`, puts sample-y at `[sp]`, and loads sample-x into r3. The call is an ARM `BL` to even address `0x00128610`. The wrapper clamps calibration before calling this helper and only reaches it for positive signed reader count. Its caller-visible wrapper return is 0/1 and it discards the normalizer return; therefore the dispatcher raw-return contract is evidenced by direct execution, while the composed scenario's equality is based on wrapper observables.

## Fresh validation

Command: `python tools/h2_input_normalizer_experiment.py --out build/agent-work/H2-semantic/h2-input-normalizer-review-00128610/run001/checks/review-seed-20261105 --seed 20261105` (exit 0).

- 254/254 direct original-versus-candidate cases matched; 0 call-contract mismatches. Coverage includes selectors 0/1/2 with every pair from `-32768,-1,0,1,32767`, selectors 3/127/128/255, full-width signed sample boundaries, and randomized full-width samples/calibration values.
- Direct call traces recorded exact target, r0-r3, both outgoing stack words, and alignment. The comparisons cover raw r0, r4-r11, SP, fault result, calibration/context and output bytes, and ordered in-fixture writes. Invalid selectors were checked for no normalizer call and raw r0 equal to calibration base.
- 12/12 original reader/counter-refresh compositions matched: all three valid routes, invalid selector, zero count, and negative count, over two seeds. The composition retains the controlled `0x0012A758` ring seam, and all three normalizer bodies are original ARM. It compares return, SP, callee-saved registers, full context/output, counters, availability, ring-call records, and global-write records.
- All four negative controls were detected: wrong selector callee, calibration sign-extension removal, reversed output pointers, and dropped fifth helper argument. No first counterexample in the candidate occurred.
- Candidate body: 144/148 bytes. Three `R_ARM_CALL` relocations resolve to even ARM entries `0x0013B9FC`, `0x0013B8F8`, `0x0013BAE0`; original wrapper call resolves to even ARM entry `0x00128610`. Slot-only IPS replay passed; only the original 148-byte slot changed. Candidate bytes differ from original.
- The runner compiled `leaf_batch29_a.cpp`; I separately compiled the actual affected consumer `leaf_batch30_a.cpp` through `compile_tu_armv6k` into the review-private output (exit 0, one compiler slot).
- No emulator/runtime check was run; offline evidence only.

Fresh report: `build/agent-work/H2-semantic/h2-input-normalizer-review-00128610/run001/checks/review-seed-20261105/report.json` (SHA-256 `a902f7f860254d0433551eb7200c8254e2c869efb023c32f5ef1e0eddec284fa`). Staged image: SHA-256 `0c9ede4a49c04bff01290037badd50d7d5a6db62257a306d6191d734552afc4d`; slot-only IPS: `179d0835bd8a04d1184046c0b10e68cff046abc2f2438e174f6b6b9bd9e722b0`. Consumer object: `bf2f8e3087a414133d18b3ddc3dd39e90a4822cc31f73846cc0f5d59dc0a5289`.

## Limits and next action

Fixtures use valid, distinct mapped ordinary RAM. Direct tests execute the original three normalizers; caller compositions use the controlled ring reader. No evidence covers malformed/unmapped pointers, aliases, concurrent mutation, MMIO, faults beyond those valid fixtures, internal normalizer arithmetic, physical input source/freshness, runtime cadence, or whole-title behavior. Preserve the `non_matching` byte classification. The coordinator can now consider this bounded candidate for promotion/integration; integration and any broader H2 scenario still require their own evidence.
