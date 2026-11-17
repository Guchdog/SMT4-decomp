# H18 getter table and caller reconstruction

## Result

The four pointer-like words are entries in four contiguous function-pointer tables, not isolated references. Exact aligned image references point only to these table entries. Constructor-like routines write each table base into an object's first word, providing positive evidence of dispatchable callback tables. Three table bases are selected by `func_0034fa10` from a mode field; the fourth has a constructor-like initializer but no identified external construction/call site in this bounded static pass. The table shape strongly resembles per-type virtual dispatch tables, but available evidence does not identify class names or the call sites that invoke each getter slot.

## Image and table entries

Pinned `extracted/exefs/code.bin` SHA256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. `config/game_info.json` maps it at `0x00100000`; rodata begins at `0x003ff000`.

| Getter | Table base | Slot offset | Getter entry site | Neighboring entries |
|---|---:|---:|---:|---|
| `0x003f5a68` | `0x004206d0` | `+0x18` | `0x004206e8` | `0x003f5980` at +8, `0x003f5ac4` at +0x10, `0x003f5a08` at +0x14 |
| `0x003f635c` | `0x004206f4` | `+0x18` | `0x0042070c` | `0x003f6268` at +8, `0x003f63a8` at +0x10, `0x003f62f0` at +0x14 |
| `0x003f6800` | `0x00420718` | `+0x28` | `0x00420740` | `0x003f64c8` at +8; `0x003f66f8`, `0x003f685c`, `0x003f6610`, `0x003f6784`, `0x003f6738` at +0x10..+0x20; `0x00351dc8` at +0x24 |
| `0x003f5e34` | `0x0042074c` | `+0x18` | `0x00420764` | `0x003f5cac` at +8, `0x003f5e8c` at +0x10, `0x003f5de0` at +0x14 |

The four getter targets each occur exactly once as an aligned 32-bit word in the image, at the entry site shown. Each surrounding table also contains zero/reserved words and other catalogued function addresses. This coherent grouping and the initializer evidence below supports table membership; slot semantics beyond the getters are not inferred.

## Table construction and consumers

`func_0034fa10` (catalog size 232 bytes) loads table addresses from its literal pool and stores `{table_pointer, 0}` to the returned object's first two words:

- `0x0034fa6c: ldr r1,[pc,#0x78]` reads literal `0x0034faec = 0x004206d0`; `0x0034fa70: stm r0,{r1,r6}` stores it.
- `0x0034fa94: ldr r1,[pc,#0x54]` reads `0x0034faf0 = 0x0042074c`; `0x0034fa98: stm r0,{r1,r6}` stores it.
- `0x0034fae0: ldr r1,[pc,#0xc]` reads `0x0034faf4 = 0x004206f4`; `0x0034fae4: stm r0,{r1,r6}` stores it.

The selected table varies with the field loaded at `0x0034fa18` (`[r2,#4]`, values 0, 1, or 4); other values take separate paths. After creation, the routine performs indirect calls through the first table entry and through offset `+8` of the table (`ldr r3,[r1]` / `blx r3` at `0x0034fa58–64` and related paths; `ldr r3,[r1,#8]` / `blx r3` at `0x0034fab0–b8`). It does not directly call the getter slots at `+0x18` in the inspected body. Thus this gives concrete construction and indirect-dispatch context for three table families, not proof that these particular getter slots are called here.

The four 36-byte routines `0x00351d80`, `0x00351da4`, `0x00351dd0`, and `0x00351df4` each load a literal table pointer, store it at `[this]`, invoke a helper on `[this+4]`, and return `this`. Their literal words are respectively at `0x00351da0` (`0x004206d0`), `0x00351dc4` (`0x004206f4`), `0x00351df0` (`0x00420718`), and `0x00351e14` (`0x0042074c`). The helpers called are respectively `0x003f5a74`, `0x003f6368`, `0x003f680c`, and `0x003f5e40`. The 8-byte `0x00351dc8` is also an entry in the third table and returns constant 2. These routines and the table layout are strong evidence of object-associated dispatch tables. Their exact source-level class/interface is unknown.

No static call site was tied conclusively to dispatch through `+0x18` or `+0x28` for these exact table instances. The table entries establish that the getter functions are address-taken callback targets and that indirect dispatch is a real design path in this family; they do not identify actual runtime invocations or the consumer of the returned word.

## Scan limits and promotion consequence

The read-only scan checked all aligned 32-bit words in the image for the four exact function pointers and for pointers into `0x004206c0..0x004207a0`. It decoded aligned ARM instructions over the declared text extent for PC-relative literal LDR/ADR targets in that data window; none directly addressed the table region. Instead, references resolve through literal pools inside code. A sweep for indirect `BLX` patterns found many unrelated calls and confirms indirect dispatch is common, but no global object/data-flow attribution was attempted. The sweep was ARM-state/aligned only and cannot exclude Thumb code, computed pointers, relocations applied at load, runtime-created objects, or dynamically selected interfaces.

The evidence changes the interpretation from “unreferenced leaves” to “address-taken methods in dispatch tables.” It still does not establish the concrete pointer/object layout contract or callers' treatment of the return value. Keep the candidates isolated; before production conversion, recover the interface and call sites for these table slots, especially the third table's distinct `+0x28` slot, then validate caller composition and source-level types. No compilation, execution, emulator, production-source, candidate, or ledger changes were made.
