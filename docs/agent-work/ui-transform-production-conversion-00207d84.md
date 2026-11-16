# `0x00207D84` generic UI transform conversion (in-slot resolution)

## Result

Refactored `ui_func_00207d84` in `src/engine/leaf_batch30_c.cpp` to use a clean
4-word structure copy (`Vec4Words`) under `__attribute__((minsize))` instead of
volatile word-by-word loops. The ARMv6K body now compiles to **104 bytes**
(`0x68` bytes), fitting directly inside the original **128-byte** slot
`[0x00207D84, 0x00207E04)` with 24 bytes (six ARM NOP words `0xE320F000`) of
tail padding.

This completely eliminates the prior `0x003FEE54` code cave and resolves the
collision with Draw helper code/data (`[0x003FEE54, 0x003FEED4)`) and Secondary
(`0x003FEED4..0x003FEFF8`) in the cumulative H2 image.

The C++ calls the original `0x002C5218` and `0x0026330C`, copies the four global
vector words (`0x004EA91C`) to the fixed scratch (`0x00472550`) in ascending
word order via `ldm`/`stm`, passes the first three words as projection input,
writes x/y/z/zero back in ascending word order via `ldm`/`stm`, and returns
`r0=0x004EA91C` and `s0=projected z`.

## Fresh offline evidence

Command:

```text
python -B tools/ui_transform_00207d84_experiment.py --out build/agent-work/H2-semantic/h2-cave-reloc-00207d84/run-001/checks/direct --seed 20261102
```

Exit code: `0`. Report:
`build/agent-work/H2-semantic/h2-cave-reloc-00207d84/run-001/checks/direct/report.json`.

Recorded artifact hashes:
- `src/engine/leaf_batch30_c.cpp`: `405d0875fb66a8c86733135641fa3f5be1cb9c7572409406b0ec6dbcc03639ac`
- `leaf_batch30_c.o`: `d53ddd488b2f803c26be1936ad9f58fdd6bb1fe6f30316174c9d1ea514809b95`
- `candidate-body.bin` (104B): `1d25427eff5127ef8784cc68b16d2ecbe6bb745d33f6966b08eff91f797f7942`
- `slot-payload.bin` (128B, 24B ARM NOP tail): `88d044b4a20aca0b3f40bfc96601d4710d3abd3c162690f28cf5d556ce063005`
- `staged-image.bin`: `e6413616df11515c95a82cc1cf4964be2e3f4504bfaf436b744a1f61ade4177b`
- `staged.ips`: `11f2cd45f908e344194e1e462733bc332e63e0fa0a1c0f937e9703ceeaaeab4e`

Verification results:
- **Direct fixtures (`7/7`)**: `basis_x`, `basis_y`, `basis_z`, `negative`,
  `perspective`, `finite_near_denominator`, and `seeded` (`20261102`) matched
  on `r0=0x004EA91C`, `s0`, `fpscr`, `sp`, `r4-r11`, `s16-s31`, `0x004EA91C`
  vector bytes, `0x00472550` scratch bytes, ordered 4-byte global writes, and
  caller-owned stack.
- **FPSCR rounding modes (`4/4`)**: `RN`, `RP`, `RM`, and `RZ` matched.
- **Caller compositions (`2/2`)**: `same` and `distinct` executions of original
  `0x0024B874` exercised both callsites `0x0024B8E0` and `0x0024B908` under the
  `[r4+0x9C] == 2` path and matched output bytes, global state, and ordered
  global write traces (with unrelated UI services `0x002698F4`, `0x00269768`,
  and `0x0024C62C` stubbed as before).
- **Negative controls (`3/3`)**: comparator-injection controls detected
  `wrong_x_y_order`, `missing_zero_w_store`, and `scratch_word_mutated`.

## In-slot placement, relocation, and cumulative H2 collision audit

- **In-slot placement**: `[0x00207D84, 0x00207E04)` (`104`B body + `24`B ARM NOP
  tail, patch file offsets `0x107D84..0x107E03`, `changed_outside_slot=false`,
  `ips_replays=true`).
- **Relocations**: Two `R_ARM_CALL` relocations resolved at final in-slot VMAs
  `0x00207D8C -> 0x002C5218` and `0x00207DC0 -> 0x0026330C` (`thumb=false`).
- **Slot reference audit**: Static scan of `extracted/exefs/code.bin` found
  `0` aligned pointer words, `2` entry branch callsites (`0x0024B8E0` and
  `0x0024B908` targeting `0x00207D84`), and `0` interior references into
  `[0x00207D88, 0x00207E04)`.
- **Cumulative H2 collision audit**: Checked against
  `build/h2-86928-integration/cumulative-image/manifest.json` (`bfb7826d...`,
  image `1616aa24...`, IPS `cc63c2fe...`, `629` IPS records). Confirmed
  `slot_collision_count = 0`, `slot_overlapping_records = []`,
  `slot_bytes_unmodified_in_cumulative_image = true`, and
  `prior_cave_0x003fee54_eliminated = true`.

## Scope limits

The caller `0x0024B874` is a generic UI consumer. Neither it nor these synthetic
fixtures establish direct TitleConfig/Audio Settings reachability, natural H2
scheduling, or whole-screen behavior. Invalid pointer chains fault as the
original does; this run uses valid mapped pointers. Zero and nonfinite
homogeneous denominators are not asserted beyond the bounded finite
near-boundary sample. Runtime was not run.
