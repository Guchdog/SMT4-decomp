# Independent review: TitleConfig sprite setup `0x002BDB2C`

## Result

The candidate matches the pinned helper's final sprite bytes, group state, raw return value, tested register state, and zero-helper arguments over the fresh direct cases and exact TitleConfig caller slice. The fresh run used seed `20261217` and 48 random cases: all 52 direct cases passed, the caller slice passed, and the wrong-zero-helper target control detected a sprite difference. The candidate fits the original 152-byte slot at 148 bytes with one even ARM call relocation. The current `config/functions.csv` row is truthfully `non_matching` for this semantically reconstructed, non-identical body. The refreshed run002 packet pins that corrected classification. This is bounded offline evidence for ordinary aligned, disjoint RAM, not resource/rendering or runtime equivalence.

## Independent pinned-code and ABI inspection

I disassembled the pinned 152-byte range at `0x002BDB2C` from image `extracted/exefs/code.bin` (SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`). The span hash matches the contract: `250f01439d7532fe72009449a21f82c0b808ec72984da4a004fbe87f9d8456e4`.

The original saves `r4-r8`, `r9`, `r10`, LR and `d8`, copies scale from `s0` into `s16`, reads the panel word from entry `[sp]`, then calls `0x002C4B30(sprite,0x8C)` before writing sprite fields. It copies the group pointer and words at `+0x0C,+0x10,+0x14,+0x18,+0x1C`, stores scale/panel and fixed values, sets bytes `+0x86..+0x8A`, restores `d8` and saved GPRs, and returns the zero helper's end pointer `sprite+0x8C` in `r0`. The `0x002F4D6C` caller supplies `r0=sprite`, `r1=0x2F`, `r2=0`, `r3=group`, stack `[sp]=0xC9`, and `s0=1.0f`.

The C++ candidate expresses the same mixed ABI: four integer register arguments, one integer stack argument, and hard-float `scale` in `s0`. It preserves the zero-helper dependency and returns `sprite+0x8C`. In the extracted candidate body, the prologue saves `r4-r7`, `r11`/FP and LR plus `d8`; the epilogue restores them. It does not use `r8-r10` or `d9-d15`. The runner checks `r4-r10`, SP, and `d8-d15`; it does not check `r11`, which I verified directly in the candidate push/pop instructions.

The only relocation is `R_ARM_CALL` at body offset 32 to `engine_func_002c4b30`, ledger entry `0x002C4B30` (bit 0 clear; first target word `0xE3A02000`). The candidate body is 148 bytes in the 152-byte span. One-slot staging pads the remaining word with ARM NOP; independent IPS application reproduces the staged image exactly and the 125 changed bytes are confined to `[0x002BDB2C,0x002BDBC4)`.

## Fresh differential and caller-slice evidence

Command:

```text
python tools/h2_2bdb2c_sprite_setup_experiment.py --out build/agent-work/H2-semantic/h2-titleconfig-sprite-setup-review-002bdb2c/run002/checks/review-seed-20261217 --seed 20261217 --random-cases 48
```

Exit code: 0. Report: `build/agent-work/H2-semantic/h2-titleconfig-sprite-setup-review-002bdb2c/run002/checks/review-seed-20261217/report.json`, SHA-256 `7d590b9a9dad21ae0217095d341c9c1d367ec4d4da829dd53ee167f6ec77ec8b`. It records 52/52 direct cases, the `0x002F4D6C..0x002F4D8C` caller slice, zero failures, body size 148/152, and the expected return pointer. The caller summary confirms type `0x2F`, index 0, sentinel `0xFFFFFFFF`, scale bits `0x3F800000`, panel `0xC9`, group `sprite-0x20`, copied descriptor words, and five enabled flag bytes. The negative control redirects the zero call to `0x002C3344`; the runner detects the poisoned sprite left uncleared.

The inputs include four directed cases and 48 seeded cases; scale bit patterns include 1.0, zero, negative one, a NaN payload, and random values. The runner compares final sprite and group bytes, raw `r0`, SP, `r4-r10`, `d8-d15`, faults, and zero-helper argument pairs.

## Review limitation: write trace

The harness captures guest `write_events` but does not compare them. Candidate disassembly confirms a concrete access-pattern difference: it writes the flag tail using a byte store at `+0x8A`, then halfword stores at `+0x88` and `+0x86` (each halfword encodes two adjacent `1` bytes). The original uses five byte stores in increasing order from `+0x86` through `+0x8A`. Final bytes match, and the assigned domain is ordinary non-MMIO memory without concurrent observers, but the evidence does not establish write-width/order parity. The harness also compares helper arguments, not the call's SP; its state checks do not include flags. These are not claims of tested equivalence.

## Limits and recommendation

Accept this as independent bounded evidence for the TitleConfig sprite setup projection. The group is an ordinary readable 0x20-byte descriptor ending immediately before the writable 0x8C-byte sprite; aliasing, invalid pointers, MMIO, concurrent observation, helper fault paths, table contents, resource loading, rendering, scheduler/lifetime behavior, and runtime title reachability are outside the tested domain. No emulator or full build was run.

No counterexample was found in the exercised domain. Retain the original `AsdMem_Zero` dependency and exact return value; use the report's explicit write-trace limitation if later requirements include byte-access ordering or concurrent/MMIO observability.
