# H4 input update transform — static ARM trace

Reference `code.bin` SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. ARM-state disassembly and aligned ARM BL-immediate scan cover text 0x00100000..0x003FE624; embedded data, Thumb, indirect/computed calls and execution reachability are outside the scan. The code spans at 0x0010B578, 0x001078D8 and 0x00108B10 start with ARM instructions and use ARM direct BL and ARM return sequences. No blanket Thumb scan or runtime execution was performed. The ledger marks these bodies `matching` wrappers, not semantic verification.

## Direct callers and observed refresh

| Call site | ARM target | Context |
|---|---|---|
| 0x00101B8C | 0x0010B578 | `crt_func_00101308` (ledger extent 0x00101308 + 4144). Actual instructions at 0x00101B80..98 include SVC 0x28, load global, store pair at +0x20, BL, then BL 0x00103744. This is an actual code-context hit; no runtime cadence or scheduler identity inferred. |
| 0x0010B57C | 0x001078D8 | First call in `0x0010B578`, no explicit argument setup; callee overwrites its arguments. |
| 0x0010B580 | 0x00108B10 | Second call after refresh, no explicit argument setup; callee overwrites r0/r1. |
| 0x00108BD0 | 0x0011C380 | Call inside second update, with r0=SP and r1=0x004E3CD4. |
| 0x0011C3C0 | 0x0012A900 | Subordinate record-copy helper, r2=1. |

The earlier H2 report said its bounded scan found no direct caller of 0x0010B578. The current image-wide aligned scan finds 0x00101B8C, and its surrounding instructions verify it is not merely a literal hit. The earlier negative finding is superseded for this site; indirect/Thumb callers and actual dynamic invocation remain unresolved. The wrapper starts `push {r4,lr}`, calls both functions, then `pop {r4,lr}` at 0x0010B584; its executable body continues at 0x0010B588. Ledger size alone does not imply 0x0010B584 is a return. Further continuation belongs to the containing original body; no player-state conclusion follows from the two calls.

Prior paired neutral H4 capture saw 0x001078E8/EC and 0x0011C640/644 with primary/alternate records zero; it did not trace 0x00101B8C or 0x00108B10, active input, or frame cadence. That observation is not repeated or extended by this task.

## First update: 0x001078D8

Loads global 0x004650A0, r0=its word +0, r1=0x004E3C28, BL 0x0011C5EC at 0x001078E8. Return nonzero writes 1 to global +4; zero writes 0. A 31-row loop uses table at 0x004099C0 (two words, 8-byte stride), tests each row mask against the same fixed state dword at 0x004E3C28, and updates 32-bit counters at 0x004E3C58+4*i. The state pointer is initialized to 0x004E3C28 and stays fixed while the counter and mapping-row pointers advance. A nonzero first table word resets its counter; for a zero first table word and availability >0, an absent mask bit resets the counter and a present bit increments it modulo 2^32. When availability is zero for such a row, the counter is left unchanged. No player pointer or map-coordinate write is visible in this body. The helper copies at most one 16-byte input record and can transform it; see frozen producer and independent review for exact offsets and limitations.

## Second update: 0x00108B10

Prologue preserves r4/lr and allocates 16 stack bytes. 0x00108B18 calls 0x0011C368, whose literal return is address 0x004E6C7C; it stores this in `[sp]` and fills three stack words `[sp+4,+8,+0xC]` with 0xFFFFFFFF. It loads r4=0x004E3CD4. The 31-word counter table ends at 0x004E3CD3, so this is a distinct following record. At 0x00108B34..48 it copies existing words +0/+4 to +8/+0xC and byte +0x10 to +0x11. Byte +4 is the first byte of the dword at +4; byte-level/word-level aliases must be respected. The rest of this state logic uses the pre-existing byte +4, before the later helper overwrites the current record.

- If byte +4 !=1, word +0x14 is cleared, bytes +0x12/+0x13 cleared; when byte +4 ==0, byte +0x10 also clears. Other nonzero values leave +0x10 unchanged.
- If byte +4 ==1, byte +0x10 becomes 1, +0x12 becomes 0 and word +0x14 increments modulo 2^32. If byte +0x13 is nonzero and signed comparison `[+0x1C] <= counter` holds, counter becomes 0 and byte +0x12 becomes 1. If byte +0x13 is zero, counter==1 sets byte +0x12; signed comparison counter >= word +0x18 sets +0x13=1, counter=0, and +0x12=1. Signed ARM branch conditions must be preserved for high-bit values. These are state/repeat-like mechanics; names and meaning remain hypotheses.
- At 0x00108BC8..D0, r0=SP and r1=0x004E3CD4, BL 0x0011C380. On return byte +4 is read afresh; when zero, 0x00108BE0..EC copies halfwords +8/+0xA back to +0/+2. 0x00108BF4 returns r0=1 unconditionally. The helper return is ignored; writes and its possible failure therefore matter. This routine does not directly read 0x004E3C28/48 or the 31-counter table and does not show a direct sample-to-player transform.

0x0011C380 dereferences `*[SP]` then its object +4, calls 0x0012A900 with output r1=0x004E3CD4, r2=1, count r3 and two cursor pointers on stack. At 0x0012A9DC..18 a ring-indexed source copies halfwords source +0x20/+0x22 and byte +0x24 into destination +0/+2/+4 (8-byte destination stride); request 1 limits the call to at most one record. A consistency loop compares source snapshot fields and retries. Afterward, if 0x002BB978 returns nonzero and 0x002BC9C8 returns zero, 0x0011C3DC..E8 clears those same halfwords and byte. Helper returns count>0 as 1 otherwise 0. Source object, producer and physical type remain unknown. These effects update the `0x004E3CD4` record, not the `0x004E3C28` first record.

## Conclusion and next bounded observation

The verified local dataflow prepares logical/counter state and a separate sampled record with previous-state and repeat-like bytes. No verified player-work pointer, field position, orientation, or map update is reached in the inspected routines. This does not prove the wider program lacks a downstream route. The concrete next step is to trace consumers and producers of 0x004E3CD4 (including +0x12/+0x13/+0x14), then in a separately assigned exclusive runtime observation capture 0x00101B8C, both call returns and records before/after under neutral conditions; only after identifying an independently delivered input should active change be correlated with an established player object. No frontend event, input injection, build, save access or emulator was performed here.
