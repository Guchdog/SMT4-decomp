# `0x002AF854` expanded alias & `0x002B8D24` cross-alias review

**Verdict: ACCEPT expanded alias and `0x002B8D24` cross-alias evidence. This closes the alias limitation for the H2 `0x002B8D24` helper caller within its documented ordinary-RAM domain.**

## 1. Frozen pins & recorded output

- Read-only audit (`compiler_slots: 0`); no canonical build or emulator was run.
- Recomputed all `13/13` `input_sha256` entries in `build/agent-work/H2-semantic/h2-helper-002af854-alias-review-002/run-001/task.json`: `13/13` matched (`reference_sha256` = `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- Recorded output `build/agent-work/H2-semantic/h2-helper-002af854-alias-caller-coverage/001/offline-output.txt` (SHA-256 `a9fac9b90ea7daf807cd53904132549293f1dfa2d1192a30cac1f800c306f029`) reports `PASS 503/503` direct cases (`132` alias overlaps), `32/32` disjoint + `32/32` cross-alias `0x002B8D24` compositions, `4/4` negative controls + selected-word alias ordering control, `64/64/64` bytes (`candidate == production`, `production != original`).

## 2. Verified alias indices, object-relative addresses, and cross-call order

- **132 direct alias overlaps (`tools/h2_af854_experiment.py:141-149`):**
  - `60` index-0 cases: `seed in {0, 17, 4729}` × `offset in {+0x20, +0x58, +0x5c, +0x60, +0x84}` × `mode in {0, 1, 0x100, 0xffffffff}`.
  - `72` index-2 and index-5 cases: `seed in {0, 17, 4729}` × `index in {2, 5}` × `selected in {+0x5c, +0x60, +0x84}` × `mode in {0, 1, 0x100, 0xffffffff}` with `list = object + (selected - index * 12)`.
- **`0x002B8D24` helper index-2 cross-alias composition (`tools/h2_af854_experiment.py:79-128`, `188-196`):**
  - Exercises `0x002B8D24` with `r1 = 2`, asserting exact call order and arguments `[(obj+0xc4, 2, 0), (obj+0x1dc, 2, 0)]` across 32 disjoint + 32 cross-alias seeds.
  - In cross-alias mode: `*(obj + 0xc4 + 0x58) = obj + 0x1dc + 0x5c - 24` and `*(obj + 0x1dc + 0x58) = obj + 0xc4 + 0x5c - 24`, with `*(obj + 0xc4 + 0x5c)` pre-seeded to `0x89898989`. Call 1 writes `index=2, 0` into `obj+0xc4+0x5c`; call 2 reads that updated word (`2`) rather than `0x89898989` and stores `*(obj + 0x1dc + 0x20) == 2`. Full `r0`, `SP`, `r4..r11`, `0x500`-byte `obj`, `list1`, `list2`, and ordered `writes` match original.

## 3. Closure of alias limitation & retained untested-domain limits

- **Closed:** The alias limitation for `0x002AF854` under the H2 `0x002B8D24` helper caller (including self-aliasing at indices `0, 2, 5` and cross-subobject aliasing between `obj+0xc4` and `obj+0x1dc`) is closed by `volatile` ordering and verified differential/composition parity.
- **Retained untested-domain limits:** Unmapped/misaligned/wrapping pointers, concurrent/MMIO observers, `d8..d15` VFP sampling (absent from disassembly), legacy `void` declarations in other TUs, and live Azahar runtime behavior remain outside scope.
