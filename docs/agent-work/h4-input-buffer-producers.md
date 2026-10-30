# H4 input-buffer producer reconnaissance

Reference `extracted/exefs/code.bin` SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Static ARM disassembly and aligned literal scan of text 0x00100000..0x003FE624; literal occurrences may include data and do not exhaust computed addresses, Thumb code, indirect pointers or code outside the image. No emulator, builds, save access or injection performed. Names below are ledger labels, not evidence of physical controls.

## Direct-address references

| Literal location/value | Containing function | Evidenced use |
|---|---|---|
| 0x0010796C / 0x004E3C28 | 0x001078D8 | passes as r1 to 0x0011C5EC; also loop source via base derived from 0x004E3C58 minus 0x30. |
| 0x00107974 / 0x004E3C58 | 0x001078D8 | 31 word counters, not 0x004E3C48 alternate record. |
| 0x0010A284 / 0x004E3C58; 0x0010A288 / 0x004E3C48 | 0x0010A1D4 | initializes counter region via 0x002C4B30(0x4E3C58,0x7C), then clears alternate record explicitly. |
| 0x001FF884 / 0x004E3C48; 0x001FF888 / 0x004E3C28 | 0x001FF830 | selects record by 0x004650A0+8 bit 0; reads selected word +8, masks with table value. |
| 0x0027FCFC / 0x004E3C48; 0x0027FD00 / 0x004E3C28 | 0x0027FBC8 | selects alternate or indexed 16-byte primary record and reads signed halfwords +0xC/+0xE. |
| 0x002B9090 and 0x002BFFF4 / 0x004E3C58 | 0x002B902C and 0x002BFFBC | query 31-word counter array. |
| 0x002C1828 / 0x004E3C48; 0x002C182C / 0x004E3C28 | 0x002C17D4 | selects same source and reads selected word +0 against table mask. |

0x004E3C28..47 spans two 16-byte records; alternate 0x004E3C48..57 is separate. Do not confuse its first 16 bytes with the counters starting at 0x004E3C58. The mode-0 reader uses 0x004E3C34/36; mode-1 uses 0x004E3C44/46. The alternate reader uses 0x004E3C54/56. Static constants do not establish writes at computed addresses not included in this scan.

## Initialization versus update

At 0x0010A21C the initializer loads 0x004E3C48 and stores that address at global 0x004650A0 +0; 0x0010A230 clears byte at alternate +0x18 (0x004E3C60), then 0x0010A244..4C calls zero helper on 0x004E3C58 for 0x7C bytes. At 0x0010A250..68 it clears alternate words +0/+4/+8 and halfwords +0xC/+0xE, then clears state word +8 at 0x004650A0. This is reset/initialization, not proof of refresh cadence or how primary buffer is filled. The 0x004E3C60 byte is inside the separate counter range subsequently zeroed. The global +0 initially points to alternate record; its lifetime/configuration role is not established here.

At 0x001078E4..E8 `func_001078D8` loads `*[0x004650A0]` into r0 and 0x004E3C28 into r1 and calls 0x0011C5EC; return !=0 sets global +4 to 1, otherwise 0. The remaining loop reads 31 mapping records at 0x004099C0 (8-byte stride), tests the same fixed 32-bit state word at 0x004E3C28 against each row mask when the first word is zero and availability >0, and updates the counter at 0x004E3C58+4*i. The state pointer is initialized once and does not advance; only the counter pointer and mapping-row pointers advance. Nonzero mapping first words reset the counter; when availability is zero for a zero-first-word row it advances without storing, so prior counters survive. This loop is counter production, not evidence of 31 fresh input-state words.

0x0011C5EC preserves r1 as output r4. Its precheck 0x00128C2C can fail; otherwise 0x0011C640 calls 0x0012A758 with r0=`*(*(root)+4)`, r1=output and r2=1, plus output-count/cursor stack pointers. If count <=0 it returns failure. The positive path uses output signed halfwords +0xC/+0xE as values and pointers passed to 0x00128610 at 0x0011C650..68. 0x00128610 selects 0x0013B9FC/0x0013B8F8/0x0013BAE0 based on calibration subobject byte +0xC; exact clamping/transformation and exception domain require independent contracts. 0x0011C688..AC modifies output +0, +4, +8 and may clear +0/+4/+8 and halfwords +0xC/+0xE at 0x0011C6D0..E0 following two helper tests; optional 0x0013BCAC modifies mask words further. This identifies conditional writers to the primary first record, not physical source identity.

In 0x0012A758 the copy loop at 0x0012A844..94 calculates destination `r1 + 16*i` and source `r0 + 16*ring_index`, copies source words +0x28/+0x2C/+0x30 and halfwords +0x34/+0x36 to destination +0/+4/+8/+0xC/+0xE. Caller requests count 1, so this call can update at most one record at 0x004E3C28; no evidence here that it refreshes primary record 1 or alternate record. The source r0 is an object/ring pointer; its producer and associated OS/device API are not resolved by this copy. Snapshot consistency loop compares object fields and retries; concurrent ordering still requires observation.

## Callers, source status and next observation

0x0010B57C directly calls 0x001078D8, then 0x0010B580 calls 0x00108B10. Prior independently reviewed `h2-input-logical-flag-refresh-review.md` reports one ledgered ARM direct caller for the refresh and none for 0x0010B578; this is bounded negative evidence, not scheduler proof. 0x002C43D4 toggles global 0x004650A0+8 bit 0 controlling source selection; it does not write either sample record. The relevant source spans in `leaf_batch27_a.cpp`, `leaf_batch30_a.cpp` and `leaf_batch45_b.cpp` are original ARM wrappers; no editable reconstruction or runtime behavior is established by these labels. 0x0012A758, 0x00128610 and 0x0013BCAC are also ledgered matching wrappers; no high-level API/physical mapping claim follows.

Narrow next observation: at the isolated H3/H4 settled checkpoint, capture, without modifying guest data, entry/return at 0x001078E8/0x001078EC and 0x0011C640/0x0011C644, root and source-object pointers, count and before/after 16-byte primary record, alternate record, selection bit, and camera reader call/return in timestamped execution order. Establish the scheduler entry and repeated cadence first; then correlate an independently delivered and verified input event with source object and copied halfwords. Avoid assuming address equality, a 31-row refresh, physical mapping, safe input injection, or player movement. Runtime observations require an exclusive assigned owner and offline-first gate; this report supplies no such observation.
