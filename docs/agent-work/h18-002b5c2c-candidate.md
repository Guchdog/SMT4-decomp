# Candidate report: H18 `0x002b5c2c`

## Result

Recovered and implemented the Thumb helper as a typed count over a zero-terminated 16-bit sequence. `compile_tu_armv6k` with `__attribute__((target("thumb")))` emitted a relocation-free Thumb function; Capstone decoded all candidate bytes as Thumb through `bx lr`. ARM BLX caller windows returned from Thumb into ARM correctly. The compiler path supports this candidate, so interworking was not a blocker.

The original returns the count of nonzero halfwords and reads the terminating zero without writing. Caller evidence includes 15 direct ARM BLX call sites. Representative exact caller windows passed for `count*2` at `0x002e0dd0` and `(count+1)*2` at `0x002a882c`.

## Test evidence

`python -m unittest tests.test_h18_002b5c2c_experiment -v` passed (4 tests). Two pinned-image offline runs passed 133 cases each (seeds `20261116`, `17`). Both runs matched return, exact read footprint, no writes, NZCV, SP/LR, callee-saved registers and Thumb-to-ARM continuation; both caller-window groups passed and all three controls were detected (byte-step, inclusive-terminator, wrong-count).

The first differential exposed a real flags discrepancy: optimized C++ retained `Z=1` after the zero sentinel for positive counts, while original `mov r0,r1` encoded as Thumb `LSLS #0` reflected the count in N/Z. Adding `cmp count,#0` corrected the observed flags. No runtime, emulator or wider regression was run.

## Evidence limits

Supported domain is an aligned, readable, zero-terminated `uint16_t` sequence; no null/bounds check exists in original. Random lengths were limited to 64. Caller tests exercise only two post-BLX windows, not full consumers. The candidate's 32 emitted bytes differ from the original 20-byte catalog span. The stock splitter labels raw halfwords `.arm` and produces invalid decoding for this Thumb helper; state was established from byte decoding plus direct BLX sites. Production wrapper and ledger are unchanged.

See `docs/function-records/0x002b5c2c.md` and the machine reports under `build/agent-work/batch-h18-001/h18-candidate-002b5c2c/run-001/checks/` for details.
