# Independent Review: `0x002BF6D0` (`camp_func_002bf6d0`) Manager-Node Resolver

## Verdict

**Disposition:** **Accept** `camp_func_002bf6d0` (`src/engine/leaf_batch27_b.cpp:1270-1281`, `non_matching`, `60/64` bytes, `2` even ARM `R_ARM_CALL` relocations to `0x002B0188` and `0x002C615C`) for bounded promotion within its tested synthetic ordinary-RAM domain and `0x002B88C4` caller composition.

This review does not claim temporary stack-residue parity below `SP`, arbitrary pointer aliasing, malformed-pointer fault parity, or live Azahar runtime equivalence.

## 1. Independent Disassembly & Contract Audit (`0x002BF6D0`, 64 bytes)

Inspected `extracted/exefs/code.bin` (`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`) at `0x002BF6D0..0x002BF710` (literal `0x10624DD3` at `0x002BF70C`) and verified all 15 `input_sha256` pins:

- **Both resolver arguments**: `mov r4, r1; bl 0x2b0188` forwards both `(group, node_index)` in `(r0, r1)` to `ui_func_002b0188`.
- **Pointer chain**: Dereferences `indirect_nodes = *(u8**)(manager + 4)`, then `node_base = *(u8**)indirect_nodes`.
- **Signed divide-by-1000 & remainder**:
  - Original uses magic `0x10624DD3` (`ceil(2^38 / 1000)`): `smull r3, r1, r1, r4; asr r3, r1, #6; sub r1, r3, r1, asr #31`, computing signed truncating-toward-zero quotient `q = (s32)node_index / 1000`, then `mul r1, r1, r2` (`r2 = -125`) and `add r1, r4, r1, lsl #3` (`r = (s32)node_index - 1000 * q`).
  - Candidate calls original signed divider `ui_func_002c615c(node_index, 1000)` (`q`), computes `r = signed_index - q * 1000`, and returns `reinterpret_cast<void*>(reinterpret_cast<u32>(node_base) + static_cast<u32>(r * 20))` (matching `add r1, r1, r1, lsl #2; add r0, r0, r1, lsl #2`).
- **Stack-residue boundary**: Calling `0x002C615C` spills temporary bytes below `SP` before restoring `SP`; non-stack writes, `SP`, and `r4-r11` match.

## 2. Fresh Offline Rerun (Distinct Seed `20261130`) & Affected TUs

- `python tools/h2_bf6d0_experiment.py --out build/agent-work/H2-semantic/h2-bf6d0-independent-review-conversion/run-001/checks/fresh --seed 20261130` (exit `0`, `report.json` SHA-256 `f4f95472769470b351640ccd4da0c3cd7c559251d2404e42565c556d8522d4f3`):
  - `2,269/2,269` direct cases (`direct_mismatches=0`, covering `[-1000, 1000]`, signed 32-bit endpoints, block boundaries, and `256` seeded indices).
  - `42/42` original `0x002B88C4` caller compositions (`caller_mismatches=0`, with original `0x002B0188` executing).
  - `3/3` negative controls detected (`wrong_block_divisor`, `resolver_index_forwarding`, `node_stride`).
  - `60/64` bytes, `2` even ARM `R_ARM_CALL` relocations (`ui_func_002b0188` at `+8`, `ui_func_002c615c` at `+28`; both `entry_bit0=0`), `ips_replay=true`, `only_original_slot_changed=true`.
- `python tools/build_check.py --tu src/engine/leaf_batch27_b.cpp` & `src/engine/leaf_batch32_c.cpp` (`--out-dir .../run-001/tu-compile -j 1`, both exit `0`; `.o` SHA-256s `fe18ff64...` and `9f98ea6a...`).

## 3. Limits

- Temporary stack residue below `SP` from `0x002C615C` is excluded from comparison; valid aligned synthetic ordinary RAM; no invalid-pointer fault parity, MMIO, or live Azahar runtime claimed.
