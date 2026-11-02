# 0x002C17D4: logical input bit query

## Recommendation

This 92-byte leaf is a bounded C++ conversion with a direct H2 cursor dependency and indirect mode-2 dispatcher use. Implement its full unsigned ID guard, gate, exact state addresses and boolean return. Avoid inventing physical-button meanings or treating logical state writes as a supported input injection method. Check generated code/slot placement, ABI and ARM interworking, and validate both callers before promotion.

## Exact pinned ARM behavior

Argument r0 is a full 32-bit unsigned ID. `cmp r0,#0x1F; bhs 0x002C17EC` rejects ID >=31 (including high-bit values) and returns r0=0. For 0..30, `ldr r1,[pc,#0x3C]` at 0x002C17DC reads literal 0x004099C0 at 0x002C1820, then `ldr r0,[r1,r0,lsl #3]!` reads gate from row 0x004099C0+8*ID and leaves r1 at that row. A nonzero gate returns 0 before loading mask, mode or state.

For a zero gate, at 0x002C17F4 `ldr r0,[pc,#0x28]` loads literal 0x004650A0 at 0x002C1824; 0x002C17F8 reads the 32-bit mask at row+4; 0x002C17FC then reads the 32-bit mode word at 0x004650A8 (literal base+8). The low mode bit selects literal `0x004E3C48` at 0x002C1828 when set, or `0x004E3C28` at 0x002C182C when clear. These are **addresses of state words**, not global pointers to dereference twice. `cmp r0,#0; ldrne r0,[r0]` tests the selected literal address; with this pinned image both constants are nonzero, so it reads exactly the selected state word. `ands r0,r0,r1; movne r0,#1` returns exactly 0 or 1. No ID-dependent increment applies to the selected state word.

The helper is leaf ARM, uses no stack, writes no data memory, makes no calls and uses no VFP. It preserves r2-r12, SP, LR and callee-saved registers, clobbers r0/r1 and CPSR, and returns through `bx lr`. For valid ID, the row must be readable; nonzero gate avoids other data reads. For zero gate, mask, mode and selected state word must be readable. The code does not handle mapping faults; the compare checks the nonzero literal address, not the selected word's contents or a nullable object pointer. Alignment, page permissions, concurrent mutation, MMIO and faults are not established beyond the observed instruction order.

The fixed pinned image table (31 rows, first word gate and second word mask):

| ID | gate | mask |
| --- | --- | --- |
| 0 | `0x00000000` | `0x00000001` |
| 1 | `0x00000000` | `0x00000002` |
| 2 | `0x00000000` | `0x00000008` |
| 3 | `0x00000000` | `0x00000010` |
| 4 | `0x00000000` | `0x00000020` |
| 5 | `0x00000000` | `0x00000040` |
| 6 | `0x00000000` | `0x00000080` |
| 7 | `0x00000000` | `0x00000100` |
| 8 | `0x00000000` | `0x00000200` |
| 9 | `0x00000000` | `0x00000400` |
| 10 | `0x00000000` | `0x00000800` |
| 11 | `0x00000000` | `0x00001000` |
| 12 | `0x00000000` | `0x10000000` |
| 13 | `0x00000000` | `0x20000000` |
| 14 | `0x00000000` | `0x40000000` |
| 15 | `0x00000000` | `0x80000000` |
| 16 | `0x00000001` | `0x00000001` |
| 17 | `0x00000001` | `0x00000002` |
| 18 | `0x00000001` | `0x00000004` |
| 19 | `0x00000001` | `0x00000008` |
| 20 | `0x00000001` | `0x00000010` |
| 21 | `0x00000001` | `0x00000020` |
| 22 | `0x00000001` | `0x00000040` |
| 23 | `0x00000001` | `0x00000080` |
| 24 | `0x00000001` | `0x00000200` |
| 25 | `0x00000001` | `0x00000400` |
| 26 | `0x00000001` | `0x00000800` |
| 27 | `0x00000001` | `0x00001000` |
| 28 | `0x00000001` | `0x00002000` |
| 29 | `0x00000001` | `0x00004000` |
| 30 | `0x00000001` | `0x00008000` |

These are pinned bytes, not a proof that the table cannot be mutated at runtime; test controlled altered gates/masks where writable and within the harness model. IDs 0..15 have zero gate; IDs 16..30 have nonzero gate in the pinned initial image.

## H2 callers and prior producer scope

`camp_func_0029F278` has BL at 0x0029F454 and 0x0029F46C for IDs read as bytes from cursor subrecord +4/+8, and at 0x0029F540 and 0x0029F558 for the second subrecord +0x2C/+0x30. A byte equal to 0x20 skips each respective call. The caller compares each returned word to zero and combines the two logical queries as its control flow dictates; these are internal cursor fields, not established physical controls. `TitleConfig_Calc` state 1 calls this mutating cursor helper with work+0xE8 and mode 1, consuming its result to decide a refresh.

Original 0x002C1830 mode 2 calls this helper first at 0x002C18F0 with its ID, and for IDs 3..6, if first return is zero, again at 0x002C19B0 with ID+9. Its other fallback paths and full mode contract are recorded in the frozen dispatcher record. Its C++ reconstruction currently uses typed `u32(u32)` for this helper; dispatcher record evidence uses original helper and does not establish this helper's conversion or a natural H2 mode-2 runtime event.

The frozen producer audit says its refresh loop tests each row's mask against a shared state word 0x004E3C28 without advancing the state pointer. The frozen independent review instead lists 0x004E3C28+4*ID and explicitly describes 31 indexed state words. These claims disagree on refresh-source stride; this report does not resolve the producer loop. The query function analyzed here unambiguously reads **one of the two fixed addresses** 0x004E3C28/0x004E3C48, independent of ID. Neither prior report proves physical mappings, actual refresh cadence, safe guest writes or runtime delivery.

## Direct caller census

Word-aligned raw ARM scan of the pinned image found 132 BL candidates, no B or aligned absolute pointer. It can match data and misses Thumb, register-indirect or dynamic calls. Ledger ownership is not runtime proof.

| Ledger function | BL PCs |
| --- | --- |
| `engine_func_001066ac` / `0x001066AC` | `0x001069A4` |
| `camp_func_0010edd4` / `0x0010EDD4` | `0x0010EE20`, `0x0010EE7C`, `0x0010EEEC` |
| `camp_func_0010efb4` / `0x0010EFB4` | `0x0010EFE8` |
| `Camp_DemonicaArchiveLoad` / `0x00114374` | `0x001148A8`, `0x00114AFC`, `0x00114B10`, `0x00114B38`, `0x00114B70`, `0x00115088` |
| `ui_func_00115bd0` / `0x00115BD0` | `0x00115C28`, `0x00115CBC`, `0x00115CEC`, `0x00115D1C`, `0x00115D4C`, `0x00115DBC`, `0x00115E34` |
| `Status_CalcTaskCallback` / `0x0018F560` | `0x0018FEE0`, `0x0018FF4C`, `0x0018FFB8`, `0x0018FFF0` |
| `ui_func_001c0f14` / `0x001C0F14` | `0x001C128C`, `0x001C12A0`, `0x001C12B4`, `0x001C12DC`, `0x001C1328`, `0x001C133C`, `0x001C168C`, `0x001C16A0`, `0x001C16B4`, `0x001C16C8`, `0x001C16E8`, `0x001C1738`, `0x001C174C`, `0x001C1760`, `0x001C1780`, `0x001C17EC`, `0x001C1800`, `0x001C1814`, `0x001C1830`, `0x001C18F0`, `0x001C1904`, `0x001C1918` |
| `engine_func_001dcb5c` / `0x001DCB5C` | `0x001DCC20`, `0x001DCCD0` |
| `engine_func_001dd178` / `0x001DD178` | `0x001DD5BC`, `0x001DD6A8` |
| `engine_func_001fc4f4` / `0x001FC4F4` | `0x001FC504` |
| `ui_func_001fe590` / `0x001FE590` | `0x001FE600`, `0x001FE614` |
| `ui_func_0021980c` / `0x0021980C` | `0x00219890`, `0x002198C8`, `0x002198E8` |
| `ui_func_00243e8c` / `0x00243E8C` | `0x002440A0`, `0x002440D0`, `0x002440F0`, `0x00244104`, `0x00244148`, `0x0024415C`, `0x002441C4`, `0x002441D8`, `0x002442F4`, `0x00244324`, `0x00244358`, `0x0024436C`, `0x002443E0`, `0x00244410`, `0x00244440`, `0x00244454` |
| `ui_func_0024dfa4` / `0x0024DFA4` | `0x0024E264`, `0x0024E278`, `0x0024E2BC`, `0x0024E2D0`, `0x0024E320`, `0x0024E334`, `0x0024E394`, `0x0024E3A8`, `0x0024E3FC`, `0x0024E410`, `0x0024E468`, `0x0024E47C` |
| `ui_func_00254ca8` / `0x00254CA8` | `0x00254D20`, `0x00254D34`, `0x00254D4C`, `0x00254D58`, `0x00254DB8`, `0x00254DCC`, `0x00254DE0`, `0x00254DF4`, `0x00254E5C`, `0x00254ED4`, `0x00254F24`, `0x00254F74` |
| `script_vm_func_00264368` / `0x00264368` | `0x0026441C`, `0x00264430`, `0x00264454`, `0x00264464`, `0x00264494`, `0x002644A8` |
| `ui_func_00297850` / `0x00297850` | `0x0029785C`, `0x00297878`, `0x00297898`, `0x002978B8` |
| `camp_func_0029f278` / `0x0029F278` | `0x0029F454`, `0x0029F46C`, `0x0029F540`, `0x0029F558` |
| `camp_func_002c1830` / `0x002C1830` | `0x002C18F0`, `0x002C19B0` |
| `ui_func_002d1da0` / `0x002D1DA0` | `0x002D1E50`, `0x002D1E60`, `0x002D1E94`, `0x002D1EA8`, `0x002D1ECC`, `0x002D1EDC`, `0x002D1F44`, `0x002D1F58` |
| `EffectEditor_func_002fcd20` / `0x002FCD20` | `0x002FCED4`, `0x002FCEE8`, `0x002FCF0C`, `0x002FCF20`, `0x002FCF80`, `0x002FCF94`, `0x002FCFB0`, `0x002FCFC4` |
| `ui_func_0030947c` / `0x0030947C` | `0x003094F0`, `0x00309504` |
| `ui_func_0031e500` / `0x0031E500` | `0x0031E57C`, `0x0031E590` |
| `battle_func_003c35f0` / `0x003C35F0` | `0x003C3814`, `0x003C3A30` |

## Required validation

Direct original-versus-compiled ARM cases should cover all IDs 0..30 using pinned rows, 31/32/0xFFFFFFFF/high-bit IDs, gate nonzero short-circuit, controlled zero/nonzero gates and masks, zero mask, no overlap/one bit/multiple bit overlap, both mode bit values including unrelated higher mode bits, and conflicting words at the two state addresses to prove selection. Track ordered reads and absence of writes, r0, r2-r11/SP and return/interworking; test fault-aware unreadable rows/mode/state only under explicit mapping assumptions. Mutants should detect signed/out-of-range guard, 8-byte stride, gate polarity, wrong mask, wrong mode bit/address and non-normalized result. Compose original cursor caller at all four sites with equal fixtures including 0x20 skip, and original dispatcher mode 2 with primary/secondary and fallback traces; preserve real surrounding dependencies and use controlled stubs only where explicitly bounded. Then independent review and integrated original-versus-patched runtime are needed. No compilation, ARM execution, emulator, input injection or runtime testing occurred here.

## Provenance

All frozen packet input hashes were recomputed and matched. Pinned image SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; `src/engine/leaf_batch32_c.cpp` `5f92de7c0940bfdb1f47e53580aecc233b60ad5b4878879ea942ed07501924ff`; `src/engine/leaf_batch40_a.cpp` `3ebf6bb17e01ac9eb9b678f85307e7d4fcf09c83417e752b09b1dfa475dfbfe3`; `src/engine/leaf_batch46_b.cpp` `12d5e4a07d522a592df43a522b4004121b1c2ec7ff0131a940ac26db2f5c99cc`. Read-only Capstone, table dump, aligned image scan and hash verification exited 0.
