# Function records: adjacent initializers `0x003F32F4..0x003F3428`

## Identity and boundaries

These are eight separate no-argument ARM leaf initializers embedded in the catalog's 800-byte compound row beginning at `0x003F31D8`. Each entry spans `0x2C` bytes: nine instructions (`0x24` bytes) ending in `BX LR`, followed by two literal words (`0x08` bytes). The entries are consecutive at 0x2C-byte intervals. The next entry at `0x003F3454` is outside this task.

The pinned reference is `extracted/exefs/code.bin`, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.

## Recovered effects

Each entry writes two adjacent `0xFFFFFFFF` words and two adjacent zero words. All eight leave other memory untouched. The base literals and actual write ranges are:

| Entry | First literal | `-1` pair written | Zero literal / pair written |
|---|---:|---:|---:|
| `0x003F32F4` | `0x00464C68` | `0x00464C68..0x00464C6F` | `0x00464C70..0x00464C77` |
| `0x003F3320` | `0x00433E18` | `0x00433E20..0x00433E27` | `0x00433E28..0x00433E2F` |
| `0x003F334C` | `0x004719C8` | `0x004719C8..0x004719CF` | `0x004719D0..0x004719D7` |
| `0x003F3378` | `0x00471C30` | `0x00471C30..0x00471C37` | `0x00471C38..0x00471C3F` |
| `0x003F33A4` | `0x00433070` | `0x00433070..0x00433077` | `0x00433078..0x0043307F` |
| `0x003F33D0` | `0x004330C0` | `0x004330C0..0x004330C7` | `0x004330C8..0x004330CF` |
| `0x003F33FC` | `0x00433148` | `0x00433148..0x0043314F` | `0x00433150..0x00433157` |
| `0x003F3428` | `0x0044E598` | `0x0044E5A0..0x0044E5A7` | `0x0044E5A8..0x0044E5AF` |

For seven entries, `STRD` writes the first pair at the first literal address. Two entries differ: `0x003F3320` and `0x003F3428` encode `STRD [r2,#8]`, so the first pair starts eight bytes after the base literal. Their zero pairs start at the second literal's address. The `0x003F3320` offset is an intentional distinct behavior, not a typo or interchangeable form.

Each callable uses no input arguments, makes no calls, returns no value, and returns through LR. The observed originals preserve `r4-r11`, SP and NZCV. Candidate compilation is relocation-free; its 36-byte functions are ARM state. Caller-saved registers are not required to match. No aligned direct ARM `BL` or exact aligned pointer word to any of the eight entries was found in `code.bin`; any startup registration path is still unknown.

## Candidate and offline evidence

Candidate: `experiments/semantic_equivalence/h18_003f32f4_family.cpp`. Runner: `tools/h18_003f32f4_family.py`.

| Seed | Cases per entry | Entries | Negative controls |
|---:|---:|---:|---:|
| `7` | 20 | 8/8 passed | 8/8 detected (one mutated first sentinel per entry) |
| `20261024` | 32 | 8/8 passed | not rerun in this seed |

Each run cycles all 16 initial NZCV combinations and varies sentinel-area RAM patterns. Differential checks compare exact initialized words and byte write sets, untouched watched memory, callee-saved registers, SP, PC continuation and CPSR. Temporary stack scratch below input SP is allowed; writes outside expected global words or the bounded stack scratch fail the check.

- Seed 7 report: `build/agent-work/batch-h18-001/h18-003f32f4-family/run-001/checks/seed-7-attempt-2/report.json`, SHA-256 `97cbd706f3f8d6c107cae917f2c189ac200f23aaf6df4444328fcfed50d10033`.
- Seed 20261024 report: `build/agent-work/batch-h18-001/h18-003f32f4-family/run-001/checks/seed-20261024/report.json`, SHA-256 `d67394de24212547170454f76e697017f7f127c8b56f649742b8f885ab78287e`.
- Candidate translation unit SHA-256 `7615670e09986e1a7722f925a7be8aeec32adea1803e06baeac132461f258d08`.
- Candidate object SHA-256 `ab827aaf3487d63429dd369e4678143b309b9deef5795e6a8ac554dba08282ca`.

Commands:

```powershell
python -m unittest tests.test_h18_003f32f4_family -v
python -m py_compile tools/h18_003f32f4_family.py tests/test_h18_003f32f4_family.py
python tools/h18_003f32f4_family.py --output-dir build/agent-work/batch-h18-001/h18-003f32f4-family/run-001/checks/seed-7-attempt-2 --seed 7 --samples 20
python tools/h18_003f32f4_family.py --output-dir build/agent-work/batch-h18-001/h18-003f32f4-family/run-001/checks/seed-20261024 --seed 20261024 --samples 32 --no-negative-controls
```

The first boundary-validator attempt checked the STRD opcode at offset `0x10`; disassembly showed it is at `+0x0C`. The validator was corrected and all eight entries passed the subsequent reports. This was a harness offset error, not an original-versus-candidate counterexample.

## Limits and next action

This validates the eight bounded initializer contracts against the pinned original in Unicorn. It does not identify the owning globals' semantic names, prove startup registration or invocation order, establish full caller composition, or cover runtime behavior. No emulator run or production ledger/source promotion was performed. Review this family independently; trace startup dispatch only if integration requires provenance for when these initializers run.
