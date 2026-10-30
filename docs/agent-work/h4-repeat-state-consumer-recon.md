# H4 repeat-state consumers and writers

Static analysis of pinned `code.bin` SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` and `config/functions.csv`. Aligned ARM B/BL immediate scan covers text 0x00100000..0x003FE624; absolute-word scan covers that same extent. Embedded literals/data can create false branch hits, so listed sites were checked against local instructions. Computed, indirect, Thumb, dynamically generated and outside-image references are not exhausted. This is not runtime, player, device or H4 equivalence evidence.

## Absolute record references and boundaries

The 31 32-bit counters start at 0x004E3C58 and end at 0x004E3CD3 inclusive. The distinct 0x20-byte state block begins at 0x004E3CD4 and ends at 0x004E3CF3. Aligned in-text words within this latter range appear only as literal 0x004E3CD4 at 0x00108BFC (function 0x00108B10), 0x0010A744 (0x0010A70C), and 0x002C0288 (0x002C01B8). No other aligned absolute address into the range was found by this bounded scan; this is not exhaustive of address arithmetic or dynamic pointers.

- `0x0010A70C` (ledger `ComWin_SetState`, exact ARM wrapper in `src/ui/window.cpp`; readable sketch also exists) takes no observed input, clears words +0,+4,+8,+0xC,+0x10,+0x14, then writes words +0x18=15 and +0x1C=4, returns 1. A direct BL at 0x0010DB78 occurs after calls 0x0010FBE8 and 0x0010A1D4 in ledger function 0x0010DB6C. This is initialization/reset evidence, not an alternate active-input producer. The source name is not proof of runtime ownership.
- `0x00108B10` (ledger ARM wrapper) snapshots words +0/+4 to +8/+0xC, byte +0x10 to +0x11, updates +0x10/+0x12/+0x13 and counter +0x14 under byte +4 and signed thresholds +0x18/+0x1C, then calls 0x0011C380 with r0=stack descriptor and r1=base. After the call, if newly read byte +4 is zero, it copies halfwords +8/+0xA back to +0/+2 and returns 1. Word +4 includes byte +4; snapshot word +0xC includes previous byte +4. These overlaps matter. The full conditions and ordering are in the frozen update-transform review; the reader below sees bytes +0x10/+0x11/+0x12, not directly the newly sampled byte +4.
- `0x0011C380` receives descriptor r0 and destination r1; it follows `*(*r0)+4`, calls 0x0012A900 with r2=1, r3=local count and two stack cursor pointers. That helper writes destination halfwords +0/+2 and byte +4 from indexed source +0x20/+0x22/+0x24 (8-byte stride, at most one record for this caller), with snapshot consistency retry. If 0x002BB978 returns nonzero and 0x002BC9C8 returns zero, 0x0011C3DC..E8 clears those same destination fields. It returns 1 iff the local count is positive; 0x00108B10 ignores it. No proven relation connects this source to the separately captured 0x10000000 primary 16-byte-record object.

## Reader contract 0x002C01B8

ARM ABI: r0 and r1 are independently nullable output addresses, r2 mode, return r0=0/1; uses r3/ip and preserves r4-r6. It reads unsigned halfwords state +0/+2 and bytes current +0x10, prior +0x11 and repeat-like +0x12. On a successful mode it writes each nonnull output as a **32-bit** zero-extended halfword; on failure or unsupported mode it leaves both untouched. Conditions:

| r2 mode | Success condition |
|---|---|
| 0 | current byte +0x10 == 1 |
| 1 | current == 1 and prior byte +0x11 == 0 |
| 2 | current == 1 and byte +0x12 == 1 |
| 3 | current == 0 and prior == 1 |
| other | false |

This provides coordinate-like pairs and transition/repeat predicates at the ABI level only; the field values, physical mapping and event identity are not established. The `src/engine/leaf_batch32_c.cpp` body remains an exact ARM wrapper, not a validated high-level reconstruction.

## Direct branches and consumers

Direct ARM BLs into 0x002C01B8: 0x00107D2C/0x00107DFC/0x00107E5C/0x00107E8C in 0x0010797C; 0x001C185C in 0x001C0F14; 0x002C016C in 0x002C0144; and 0x00317464/0x00317684/0x00317760 in 0x003171F8. Mode is 1, 0, 3, 0 at the four 0x0010797C sites (first site output r0 is inherited from preceding branch; do not infer it from the local few instructions). At 0x00107E5C both outputs are null, mode 3; return controls writing work byte +8=6. The 0x001C185C and 0x00317760 sites use mode 0 and stack output slots; each continues to call 0x002BF6D0(0x39,0x41) and uses a stack coordinate with a signed-halfword result. The 0x00317464 call uses mode 1 and work +0x154/+0x158 outputs; 0x00317684 uses mode 3 with stack outputs. Their UI/window associations are ledger/name and local presentation-call evidence, not proof of a particular H4 field event.

0x002C0144 passes its fifth argument from stack as the reader mode, passes two local output pointers, then if successful compares outputs to an inclusive rectangle defined by its four register arguments; returns boolean. Its direct ARM BL sites are 0x00107D78, 0x00107EDC (0x0010797C); 0x001C14B8, 0x001C14FC, 0x001C153C, 0x001C158C (0x001C0F14); 0x00220C9C, 0x00220CD4 (0x00220C5C); 0x002315C0 (0x002315B4); 0x00231B6C (0x00231B54); 0x003174E8, 0x00317524, 0x00317560, 0x003175AC, 0x00317668 (0x003171F8); 0x00329664, 0x003296BC (0x00329404); 0x003C3050 (0x003C3044); 0x003C3064 (0x003C3058). These are static sites, not proof of dynamic reachability or correct rectangle arguments.

ARM tail branches 0x003C3038 and 0x003C3040 target 0x002C01B8 after setting mode 1 and 3 respectively; they inherit r0/r1. Direct BLs to those wrapper entries occur at 0x0039B69C and 0x0039D7FC (mode 1 wrapper) and 0x0039B5EC (mode 3 wrapper). Their surrounding functions are 0x0039B58C and 0x0039D758; exact scene ownership is unresolved. The scan into 0x00108B10/0x0011C380/0x0012A900 found 0x0010B580/0x00108BD0/0x0011C3C0 respectively. It found 0x0010DB78→0x0010A70C. The previous independent trace established 0x00101B8C→0x0010B578; this does not establish execution timing in the field.

## Conclusion and next evidence

The audited reader and rectangular hit predicate support a state-to-UI/window-like input path, but neither these calls nor the alternate update establish a verified player-work pointer, player movement, H4 interaction, physical input, or transition. Other callers and branches could have different consumers. The smallest useful next step is static review of 0x0039B58C/0x0039D758 context and the directly reachable object writes, plus confirmation of any runtime binding to the observed field before drawing a gameplay conclusion. A separately assigned passive breakpoint-based capture may compare reader entry/return, mode, output buffers and current state bytes in neutral and independently delivered verified input scenarios; avoid unverified guest writes or watchpoint-based methods. No build, tests, emulator, source-save access or guest writes were performed here.
