# Independent review — `0x0011C5EC` H2 input-state reader

## Recommendation

The production C++ is supported for the tested contract over valid, disjoint synthetic ordinary memory. The fresh final-VMA comparison and original caller compositions found no differences; all three mutation controls were detected. No semantic counterexample was found.

There is one promotion blocker: the frozen ledger row still says `matching`, although the fresh compiled 304-byte body differs from the pinned original 304-byte slot. Keep this review bounded and correct that classification to `non_matching` before promotion. The CSV is a frozen input for this task; I did not edit it.

## Frozen pins and implementation identity

I recomputed every one of the 17 declared packet input hashes; all match. The reference image SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Production source SHA-256 is `14e36c11b3f45da42ae14f870469d7cee9c665f7c78af24c35309a7686980d59`; harness SHA-256 is `c8c2d88a27f9bd128ed7e33ce9481b1174ae697f64f6f6d6cb6a746532cf4e1b`.

Independent extraction of the fresh object produced a 304-byte `func_0011c5ec` body with SHA-256 `a866215a27fb26bafe8d1a398e8921ab25cfc1e23b04d27dba8c3a1c4cf34edd`. The pinned original slot body SHA-256 is `2a35630875d322688ae72bc8c19e0c0c46e0f304ae3e1d8e271228662832e55f`; they differ. Current ledger row: `0x0011c5ec,304,matching,...`. This conflicts with the production note and record, which correctly say that the body differs and should be `non_matching`.

## Fresh differential and final-VMA evidence

Command:

`python tools/h2_11c5ec_experiment.py --out build/agent-work/H2-semantic/h2-input-state-reader-independent-review-0011c5ec/run001/checks/fresh-seed-20261112 --seed 20261112` — exit 0.

The output report SHA-256 is `2d38a8a505ac8d25b1750096791dd0872ab7eccb8f0dea58e6b25c44f6dc8fa6`; staged image SHA-256 is `68bd138851294c4abec31c7cf3d79f310ec2d3a91c50c7e311fa56be0e677c69`; slot-only IPS SHA-256 is `91c4444ab65da98f03312b150436a4e91cac71753085b8177364ec6dc4bdb220`.

The harness compiled the production TU, linked seven `R_ARM_CALL` relocations to even ARM entries, staged the 304-byte body at `0x0011C5EC` into the exact 304-byte span, and compared original versus staged at the final VMA. It reports 288 direct cases, 32 compositions through original caller `0x001078D8`, zero mismatches, all mutation controls detected, exact slot-IPS replay, and no changes outside the target slot.

The matrix covers mode bytes `0,3,4,255`; signed ring counts `-1,0,1`; selectors `0,1,2,3`; flag pairs `(0,0),(1,0),(1,1)`; and postprocess gate values `0,1`. It exercises early mode/count returns, calibration clamp cases, valid ring samples, all selector branches including invalid selector, context marker behavior, flag short-circuit behavior, output transformation and postprocess ordering. Each direct output compares return, output and context bytes, ordered writes, ring-call arguments, callee-saved register state, stack pointer, and relevant counters/global state.

The ring helper seam observed r0-r3 as source object, output buffer, request count 1, and count pointer. Caller stack words contain timestamp and index output pointers, both in the wrapper frame; the recorded SP is 8-byte aligned and the timestamp/index locals begin as all-ones sentinels. The helper return register is ignored; the signed local count controls the success path. The six remaining direct callees run from the pinned original image. The 32 caller compositions execute the original refresh wrapper with the final-VMA reader, comparing the wrapper-visible memory effects.

Seven relocations in the staged body resolve to `0x00128C2C`, `0x001285C4`, `0x0012A758`, `0x00128610`, `0x002BB978`, `0x002BC9C8`, and `0x0013BCAC`; every target is word-aligned ARM. The final body exactly fills its original slot. Exact-slot IPS replay is true and the image differs only within that slot.

## Contract audit

The ARM listing confirms a 40-byte frame and 0/1 return. It initializes timestamp/index sentinels before the mode-byte-4 early return. Otherwise it clamps five signed calibration halfwords, obtains the source object from `context[0]` then its handle at object `+4`, and calls the ring reader with `(handle, output, 1, &count, &timestamp, &index)` in AAPCS register/stack order. A nonpositive signed count returns zero after clamp effects. Positive count calls the selector-based normalizer with output halfword pointers and signed sample values; selector 0/1/2 dispatches while selector 3 reaches no normalizer helper.

If context marker `+0x30` is set, the pre-transition output word is saved to context `+8` before the marker is cleared. The function then clears state bit `0x2000`, writes forward-transition bits at output `+4`, reverse-transition bits at `+8`, and checks the two signed global-byte flags in order. If the first is nonzero and the second is zero, it clears outputs in order `+0`, `+8`, `+4`, `+0x0C`, `+0x0E`. It saves output word `+0` to context `+8` before optional postprocessing; byte `0x00471AD8 == 0` invokes `0x0013BCAC`. The function returns raw 0 or 1. The test matrix and ordered write comparisons cover these branches and ordering; the three mutation controls detect altered cleared bit, reversed marker condition, and omitted short-circuit clear.

## Seed behavior and scope limits

Although the fresh invocation records seed `20261112`, the harness does **not** use `args.seed` to generate case inputs. `make_case()` seeds each fixture from its fixed case index, and `args.seed` appears only in the report. Thus this is a fresh compile/execution of the same deterministic adversarial matrix, not a new randomized fixture set. I did not modify the runner to change that behavior.

The controlled ring seam does not establish actual source provenance, buffer freshness, physical input identity, aliasing, concurrency, malformed ring-state/fault behavior, MMIO, scheduling/cadence, or natural runtime reachability. The caller composition is limited to the original `0x001078D8` wrapper and its compared memory outputs. No emulator or full build was run.

## Next action

Correct the ledger classification to `non_matching` before promotion. The bounded ordinary-memory C++ behavior is otherwise supported by the reviewed source, pinned ARM listing, fresh final-VMA differential, caller compositions, slot/relocation checks, and mutation controls. Keep physical input mapping, source freshness, cadence, and runtime behavior open.

## Run003 follow-up — 2026-11-02

This follow-up uses the corrected frozen packet. All 19 packet hashes recomputed successfully. The ledger row now reads `0x0011c5ec,304,non_matching,...`, resolving the classification blocker noted in my earlier review. The production code, source record and stated ordinary-memory limits remain consistent.

The runner update also resolves the earlier seed caveat. It now derives each case's random context/output/ring-record bytes from `(seed, case index)` and records a SHA-256 digest of the serialized fixture set. I checked the three report fixture digests:

- Seed 20261110 (pinned implementation report): `918843cd4e6083359dfcefe5b5e31f3554734e0d3c6bcfc9ee5acedf2316f44e`
- Seed 20261113 (pinned seed-control report): `32bcee0c9ec27944d9d222d60a76b028172bd446f88deb7253cbb3156cbb25b9`
- Fresh seed 20261115: `28bf8e6898766791f97a329425898ae930a601f68005acb1b88d8dc1bc9b6831`

All three digests differ, so the corrected seed changes fixture bytes while preserving the same adversarial branch matrix.

I ran:

`python tools/h2_11c5ec_experiment.py --out build/agent-work/H2-semantic/h2-input-state-reader-independent-review-0011c5ec/run003/checks/fresh-seed-20261115 --seed 20261115` — exit 0. Its report SHA-256 is `6bfcc7e5e6798835a7decbcc7d266b0779de883f05e4c36e1e6d261eb36c1fdd`; staged image SHA-256 is `68bd138851294c4abec31c7cf3d79f310ec2d3a91c50c7e311fa56be0e677c69`; slot IPS SHA-256 is `91c4444ab65da98f03312b150436a4e91cac71753085b8177364ec6dc4bdb220`; compiled object SHA-256 is `bf2f8e3087a414133d18b3ddc3dd39e90a4822cc31f73846cc0f5d59dc0a5289`.

This fresh run passes all 288 direct cases and 32 compositions through original caller `0x001078D8`, reports zero differences, detects all three mutations, replays the exact slot IPS, and changes no bytes outside the 304-byte slot. It links all seven `R_ARM_CALL` sites to even ARM entries. The original/helper argument order, stack local pointers and alignment are explicitly captured; write order, context marker, selector, mode/count gates, global short-circuit and optional postprocess paths remain exercised by the full matrix. The fresh production object differs from the pinned original function body, consistent with the corrected non-matching ledger row.

**Updated recommendation:** approve the conversion only for its tested valid, disjoint synthetic ordinary-memory contract. The prior ledger blocker and seed-diversity caveat are resolved. The controlled ring seam still does not establish real input provenance, freshness, physical controls, scheduling/cadence, aliasing, concurrency, malformed ring state, MMIO, or natural runtime behavior; those remain open.
