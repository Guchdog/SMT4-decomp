# Contract Recon: `0x002A8A8C` (`ui_func_002a8a8c`) Status-Counter Service

## 1. Pinned Identity & Disassembly (`0x002A8A8C`, 36 bytes)

All 11 `input_sha256` pins in `task.json` matched (`extracted/exefs/code.bin` `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`). `config/functions.csv` classifies `0x002a8a8c` as `non_matching` (`ui_func_002a8a8c` in `src/engine/leaf_batch23_b.cpp:259-273`).

Exact 36-byte disassembly (`0x002A8A8C..0x002A8AB0`):

```arm
0x002a8a8c: ldr   r0, [pc, #0x18]    @ 0x002A8AAC -> 0x0043DCB0
0x002a8a90: ldr   r0, [r0, #4]       @ manager = *(u32*)0x0043DCB4
0x002a8a94: add   r0, r0, #0x600     @ object = manager + 0x600
0x002a8a98: ldrsh r1, [r0, #0x4c]    @ value = *(s16*)(object + 0x4c)
0x002a8a9c: cmp   r1, #0
0x002a8aa0: subgt r1, r1, #1
0x002a8aa4: strhgt r1, [r0, #0x4c]   @ if (value > 0) *(s16*)(object + 0x4c) = value - 1
0x002a8aa8: bx    lr                 @ returns r0 = manager + 0x600
0x002a8aac: .word 0x0043dcb0
```

## 2. Recovered Contract & ABI

- **Global pointer loads**: Loads literal `0x0043DCB0` from `0x002A8AAC`, then reads `manager = *(const u32*)0x0043DCB4`.
- **Signed-halfword boundary & write**: Sign-extends `*(const s16*)(manager + 0x64C)` (`ldrsh`). Iff `value > 0` (signed, i.e. `[1, 32767]`), writes `(s16)(value - 1)` via `strh` to `manager + 0x64C`. For `value <= 0` (`0`, `-1`, `-32768`), performs **no memory write**.
- **Raw `r0` return**: Unconditionally returns `manager + 0x600` (`u32`) in `r0`, regardless of whether a write occurred.
- **ABI**: Zero explicit arguments; no stack frame, no VFP/NEON instructions, no callees; clobbers only `r0-r1` and `CPSR`; preserves `r2-r11` and `SP`.
- **Fault domain**: Unchecked dereference of `*(u32*)0x0043DCB4` and `manager + 0x64C`; null/unmapped `manager` faults at `0x002A8A98`.

## 3. H2 Callsite Multiplicity (`0x002B85BC`)

- `extracted/exefs/code.bin` has `16` unconditional `BL` sites plus `2` conditional `BLEQ` sites (`0x002B8634`, `0x002B8758`) targeting `0x002A8A8C`.
- Inside `0x002B85BC` (`ui_func_002b85bc`), `0x002A8A8C` is called across `9` sites (`7` `BL` + `2` `BLEQ`):
  - `clear_status` branch: `1` call per nonzero slot (`0` if `0`).
  - Non-clear branch: `0` calls if `status == 0`; `1` call for ordinary nonzero; `2` calls for unchanged `7` or `9`; `3` calls for `8`; `4` calls if `7`/`9` mutates to `8`.
  - All `0x002B85BC` calls ignore `r0` and rely on the side-effect at `manager + 0x64C`.

## 4. Bounded Test Plan & Limits

- **Direct cases**: Signed-halfword boundaries `{-32768, -1, 0, 1, 2, 32767}`, repeated decrement `3 -> 2 -> 1 -> 0 -> 0` (verifying no write at `0`), distinct `manager` bases, `r0 == manager + 0x600`, `r4-r11`/`SP` preservation, and zero writes outside `manager + 0x64C`.
- **Caller composition**: Compose `0x002A8A8C` with `0x002B85BC` across statuses `0`, `1`, `7`, `8`, `9` and `clear_status`, verifying cumulative decrements at `manager + 0x64C`.
- **Limits**: Valid mapped ordinary RAM for `0x0043DCB4` and `manager + 0x64C`; concurrency, MMIO, and live Azahar runtime remain outside scope.
