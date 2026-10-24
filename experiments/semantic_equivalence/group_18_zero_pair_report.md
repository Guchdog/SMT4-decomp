# Group 18: two-word zero initializers

## Result

The three candidates pass bounded, isolated ARM differential testing for the
verified ordinary-RAM contract. This is `probada_arm` evidence only; it does not
claim exact byte matching, fault/atomicity equivalence, callback behavior in the
game, or whole-program equivalence. The candidate source and runner are
`zero_pair_candidates.cpp` and `tools/zero_pair_experiment.py`.

## Individual evidence

The pinned image hash is
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
Each 16-byte entry in `config/functions.csv` is still marked `matching`; the
runner checks the exact ARM instruction sequence separately at each address:
`mov r1,#0; mov r2,r1; stm r0,{r1,r2}; bx lr`.

| Address | Address-specific evidence | Reconstructed contract |
|---|---|---|
| `0x0011B850` | Two verified direct `BL` references at `0x00110D94` and `0x0011109C`. Their caller code computes `r0 = object + 8` and `r0 = object + 0x20`, respectively. The first caller consumes returned `r0` in a post-call writeback byte store; the second immediately derives another address from returned `r0`. | Zero two adjacent 32-bit words at `r0` and `r0+4`; preserve and return `r0`. |
| `0x0017F5E8` | Callback pointer literal is loaded into `r1` at `0x0037E330` and `0x003F4154`; each setup sequence passes it to `ui_func_002C5F58` via `BLX` at `+0x10`. These are registration sites, not observed callback executions. | Same leaf memory operation and unchanged `r0`; downstream callback signature/consumer remains unverified. |
| `0x0017F5F8` | Callback pointer literal is loaded into `r1` at `0x003ED7F4`; the sequence passes it to `ui_func_002C5F58` via `BLX` at `+0x10`. This is registration evidence, not an observed callback execution. | Same leaf memory operation and unchanged `r0`; downstream callback signature/consumer remains unverified. |

The instruction operands establish an input address in `r0`, scratch values in
`r1/r2`, two zero word stores, no base writeback, and return through `lr` with
`r0` unchanged. The direct callers corroborate the base-pointer contract and
consume the returned base. The callback sites corroborate that the other two
addresses are passed as initializer callbacks, but do not establish how a later
callback invocation uses its return value. Callee-saved registers, stack
pointer, and NZCV are preserved by the observed leaf sequence. No caller window
is claimed for either callback target.

The C++ candidate uses two ordered `volatile uint32_t` stores and returns the
original pointer. Clang 23.1.3 emits 16 bytes per candidate. It is not byte
identical to the original: the original performs a single `STM`, while the
candidate performs two `STR`s. The experiment therefore excludes MMIO,
concurrency, unaligned pointers, exceptions, and partial-fault/atomicity
behavior. Its defined test domain is aligned, in-bounds ordinary RAM.

## Differential results

For each seed and each function: three fixed cases (distinct sentinels, all
ones, zero) plus 64 seeded cases passed. That is 67 cases per function, 201
function comparisons per seed, and 402 total across both seeds. Both verified
direct-caller windows passed per seed (four total). Three targeted controls per
seed were detected: wrong second offset, omitted second store, and wrong return
(six detections total).

| Seed | Per-function cases | Direct-caller windows | Negative controls |
|---:|---:|---:|---:|
| `20261024` | 67 × 3 pass | 2 pass | 3/3 detected |
| `7` | 67 × 3 pass | 2 pass | 3/3 detected |

Source SHA-256: `5bd8bf5268c5195df3aaefe99b13eda9b4fa4b198a53d24334ea027428e06e4a`.
Compiled object SHA-256: `c232b26c642cf14e62e908a7644ded3a162d2ef140124411b5fdad78c32de041`.

Reproduce from the repository root (the generated evidence stays under ignored
`build/`):

```powershell
python -m unittest tests.test_zero_pair_experiment -v
python tools/zero_pair_experiment.py --code extracted/exefs/code.bin --samples 64 --seed 20261024 --output build/semantic-equivalence/group-18-zero-pair/seed-20261024
python tools/zero_pair_experiment.py --code extracted/exefs/code.bin --samples 64 --seed 7 --output build/semantic-equivalence/group-18-zero-pair/seed-7
```

The direct-call verifier requires the branch destination to be exactly
`0x0011B850`. Callback evidence checks each literal-loaded function pointer is
in `r1` immediately before the expected registration `BLX`; neither check
substitutes for observing game-time execution.
