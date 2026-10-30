# H2 Draw cache-helper split probe

## Result

The production `leaf_batch43_a.cpp` now has one outlined, non-ledger helper
`title_config_draw_cached_render_update` for the repeated renderer-cache
sequence at `0x002CAFD0`. The focused production-TU object measures the main
symbol at 1,464 bytes and the helper at 124 bytes. The main fits the original
1,932-byte Draw span with 468 bytes to spare. The format literal is 3 bytes;
placing it after the 4-byte-aligned helper gives 127 bytes of payload, rounded
to 128 bytes. That fits the exact 428-byte Calc cave tail with 300 bytes left.

This is a **size and relocation probe**, not a patch. No cave bytes were
written, no combined image was built, and the Draw differential was not run at
the final guest address. The format string relocation and seven helper-call
relocations still need a placement-aware patch builder.

## Production source change

Only the `ui_func_002cafd0` production wrapper in
`src/engine/leaf_batch43_a.cpp` changed. The naked assembly was replaced by the
reviewed readable body and one static helper. `cached_render_update` had seven
source call sites and was previously inlined; those sites now call the helper
in the same order. Inside the helper, the original sequence remains: calculate
render value, read cache index/old slot, store the value, conditionally invoke
the callback with that value, then clear the dirty byte.

The unsigned guard remains `static_cast<draw_u32>(absolute_index) < 3u` and
matches the reviewed `CMP`/`BHS` condition. The callback accepts the ignored
pointer-sized argument and returns `u32` zero, preserving the observed normal
return `r0=0`. The original panel, sprite, cursor, layout, TBB, formatting,
font, touch, renderer-value, and indirect callback addresses/order remain in
use. The hard-float font call retains the reviewed argument order and VFP
coordinates/scales; the cache helper itself takes two integer arguments.

The format text remains exactly `%s\0`. The source now has a local `.rodata`
symbol `_ZL15kDrawTextFormat` rather than pointing at the original inline
literal at `0x002CB410` (Draw-relative offset `0x440`). The new main symbol has
an `R_ARM_ABS32` relocation to that local `.rodata` section. Under the proposed
tail layout, the literal address is `0x003FEED0` (helper start `0x003FEE54`
plus `0x7C` bytes). The existing builder does not yet support this mixed
in-place-main/cave-helper/data layout; this report records the relocation for
the later builder owner.

The callback's C++ definition is still local to the engine batch and does not
change the shared header or ledger. The shared declaration remains
`void TitleConfig_Draw(void*)`; the production symbol continues to return zero
in `r0` as observed. The exact registered callback type should be reconciled
before promotion rather than inferred from this object-size probe.

## Object and layout evidence

Fresh focused compile command:

```powershell
python tools/build_check.py --repo-root . --tu src/engine/leaf_batch43_a.cpp `
  --out-dir build/agent-work/H2-semantic/h2-draw-cache-split-probe/run-001/checks/production-tu `
  --jobs 1 --force
```

It exited 0 using Clang 23.1.3, target `armv6k-none-eabihf`,
`-mcpu=mpcore -mfpu=vfpv2 -mfloat-abi=hard -O2 -std=c++20 -ffreestanding
-fno-exceptions -fno-rtti -nostdinc -nostdinc++`.

| Symbol or placement | Bytes | Budget | Result |
|---|---:|---:|---|
| `ui_func_002cafd0` production main | 1,464 | original span 1,932 | fits, 468 spare |
| `_ZL38title_config_draw_cached_render_updatejj` | 124 | tail helper allowance 428 | fits |
| `_ZL15kDrawTextFormat` (`%s\0`) | 3 | counted with tail data | fits |
| Helper + string, rounded to four bytes | 128 | exact cave tail 428 | fits, 300 spare |

The pinned cave tail is `[0x003FEE54,0x003FF000)`. The tested placement
calculation starts the helper at `0x003FEE54`, puts the string at
`0x003FEED0`, and rounds the combined 127 payload bytes to 128. The helper has
no relocations. The main symbol has these relocations, all relative to its
first byte:

| Offset | Relocation | Target |
|---:|---|---|
| 332 | `R_ARM_CALL` | outlined cache helper |
| 400 | `R_ARM_CALL` | outlined cache helper |
| 440 | `R_ARM_CALL` | outlined cache helper |
| 480 | `R_ARM_CALL` | outlined cache helper |
| 524 | `R_ARM_CALL` | outlined cache helper |
| 804 | `R_ARM_CALL` | outlined cache helper |
| 840 | `R_ARM_CALL` | outlined cache helper |
| 1,460 | `R_ARM_ABS32` | local `.rodata` string symbol, section addend 0 |

When the main is placed at `0x002CAFD0` and the helper at `0x003FEE54`, the
helper calls are within ARM `BL` range. The linker/patcher must still resolve
all seven calls and retarget the absolute string reference; the standalone
object does not establish that the merged IPS or branch targets are correct.

Source SHA-256:
`e5c6414cd37d2d6fc9928ca85eb5466a8c07bcec224a887616cb383ac408d64c`.
Production object SHA-256:
`0513196e3d93398036feba0177fc92cadadba87589068dc0605da64b0658ede2`.
Detailed extraction and relocation record:
`build/agent-work/H2-semantic/h2-draw-cache-split-probe/run-001/checks/production-tu/split-report.json`.

## Limits and next action

The probe did not compare the rewritten production symbol with original ARM,
run the 46 directed Draw cases, verify caller-composed state, create a combined
Calc+Draw image, or test the helper at `0x003FEE54`. The original Draw helper
semantics remain HLE boundaries. The format-string relocation and local
`R_ARM_CALL` relocations require explicit support in a multi-symbol patcher.
The current Calc image and ledger were not changed; no emulator, RSP, profile,
keyboard, or mouse was used.

Freeze this source and independently review helper ordering, VFP call
preservation, return ABI, relocation handling, and exact symbol sizes. A later
placement task should link the helper and string into the cave tail, run the
production Draw differential from its final VMA, and rerun the Calc sequence
on the same merged image.
