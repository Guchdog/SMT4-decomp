# Independent review: H2 cursor setup `0x0029FAE8`

## Recommendation

The readable candidate has no counterexample in the audited aligned ordinary-RAM domain. I recommend accepting the bounded semantic conversion for its tested direct wrapper behavior and the exact original H2 setup path. This does not establish the complete TitleConfig lifecycle, scheduler/input timing, audio behavior, or runtime equivalence. The ledger currently labels this changed body `matching`; that label is not truthful for a 392-byte compiled body replacing the pinned 452-byte body. Coordinator promotion must set `0x0029FAE8` to the appropriate non-matching classification before treating it as promoted.

## Frozen inputs and independent run

All hashes declared in the run003 packet recomputed exactly, including the pinned image, candidate source, corrected runner, accepted contract, coordinator report, and ledger. The pinned image SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; original 452-byte slice SHA-256 is `775855685fc946151107ff9a787cce85eee1ef29b839e558628ddcc3429e58b9`.

I ran:

```text
python -B tools/h2_29fae8_cursor_setup_experiment.py --out build/agent-work/H2-semantic/h2-titleconfig-0029fae8-review/run003/checks/fresh-seed-20261119 --seed 20261119 --random-cases 48
```

Exit code: 0. The fresh report is [report.json](../../build/agent-work/H2-semantic/h2-titleconfig-0029fae8-review/run003/checks/fresh-seed-20261119/report.json), SHA-256 `9afce600666e95de46ba0acd5cf86ccda9235ea1365c5ed19f6929f5d535042f`. It records 60/60 passing cases (12 fixed plus 48 seeded), zero mismatches, and a detected wrong-helper-target negative control. Source SHA-256 `10a8f416f16330faa1e3b6345e616c419c82e99ae77fcc2912298d6c7b4763cb`; compiled object SHA-256 `b67d10cb10ba11c76e4a9028e5f376a775bb399280e8f0d1858b8ec832e3794e`; body SHA-256 `61f40c89bfc4ba6f6f0e35150c54de65fa5114bc287b097e5869d787a57ae9b0`.

The body is 392 bytes in a 452-byte slot. The runner resolved all seven ARM `BL` relocations, to `0x002C615C`, two calls each to `0x00296F18` and `0x00296EF8`, and two calls to `0x003170A0`. All targets are even, word-aligned original ARM entries with nonzero entry words; each branch is in range. The staged image/IPS path is checked by the runner to replay exactly and replace only the original slot. The independent IPS SHA-256 is `9ebc9c4de860c32f72aee9ef9dc85e7e6c9a15b4990e603fa99d83a414382497`; staged-image SHA-256 is `2d0676d5ef27714288507e3ae91e60ccecfca26920c5e3948a4896f2d1b9258f`.

## ABI, branches, writes, and helper order

The candidate matches the pinned contract's six-word ABI: cursor in `r0`, signed total/visible/columns in `r1-r3`, and `wrap_row`/`repeat` as the first two stack words. The corrected runner maps the five scalar case values to `r1-r3` and stack `[sp]`/`[sp+4]`; its random cases now truly exercise `wrap_row=0/1` and `repeat=0/1`. This fixes the earlier runner defect where the wrap value was discarded. The fresh run therefore covers both axis-0 ID branches and the repeat-enabled/disabled branches.

The original signed gate for `total<=0` sets byte `cursor+0x62=1`, returns `r0=1`, and makes no helper calls. Active paths clamp visible to total only for `columns==1 && visible>total`, store total at `+0x50`, and clear disabled byte `+0x62`. The divider call yields quotient in `r0` and signed remainder in `r1`; the caller rounds rows upward only when remainder is positive. The candidate preserves these branches and direct writes.

Active helper order and arguments match the pinned original: divide `(total,columns)`; axis0 initializer `(cursor,visible,rows)`; axis0 ID writer; optional axis0 extended ID writer when repeat is nonzero; axis1 initializer with the conditional `(columns,total)` clamp path; axis1 ID writer; optional axis1 extended IDs; then final cursor stores and tail behavior. The H2 check asserts the complete expected helper trace, including fifth stack words, and both final ten-word axis records. In the H2 fixture `(cursor,3,3,1,0,1)`, the calls are `0x0029FBC4(cursor,3,3)` and `0x0029FC44(cursor+0x28,1,1)`, with the expected logical ID bytes. Both records end with start=1: the initializer helper's intermediate 2 is overwritten for axis0 by this wrapper, and the tail leaf at `0x002FC20C` writes 1 to axis1 `+0x14`.

For every direct case, the differential compares fault state, raw `r0`, the cursor bytes, ordered writes, exact helper call/argument trace, `r4-r11`, and SP. The fixed corpus covers `total=0,-1,1,3,8,INT32_MAX`, visible clamping, columns/visible branch combinations, wrap route, repeat suppression, and the H2 fixture. The randomized domain uses positive total `1..100`, visible `1..total+10`, columns `1..8`, and independent wrap/repeat bits. The negative control changes an axis-ID call target from `0x00296EF8` to `0x00296F18` and is detected by cursor mismatch.

## Limits and next action

The runner does not cover negative/zero columns, negative visible values, arbitrary non-boolean wrap/repeat words, malformed cursor pointers, aliasing, concurrent observers, or helper fault behavior. The candidate and runner retain pinned original helpers, so this result validates orchestration against those dependencies rather than independently reconstructing their full behavior. The helper/task/input/audio lifecycle and actual runtime screen reachability remain outside this review.

Before promotion, reconcile the `config/functions.csv` row from `matching` to a truthful non-matching classification. Then include the candidate in the coordinator-owned integrated batch/build and the explicitly scoped original-versus-patched runtime scenario; this focused differential alone does not establish whole-H2 equivalence. No source, runner, ledger, README, milestone, board, or emulator changes were made by this review.
