# Independent review: `0x002AA268` profile-record copy

## Recommendation

The candidate passes the reviewed bounded offline domain. I found no semantic,
ABI, relocation, slot-fit, or caller-composition counterexample. The code is a
supported non-identical reconstruction for aligned mapped records and readable
table entries. **Do not promote it while the production ledger still labels the
function `matching`;** the final candidate differs from the pinned bytes. Correct
that classification to `non_matching` at integration, then include the helper
in the coordinator-owned integration closure. Runtime profile lifecycle and
natural H2 reachability remain outside this review.

## Inputs and original contract audit

All 14 `input_sha256` entries in the prepared review packet matched. I decoded
the complete pinned 72-byte body at `0x002AA268` and independently checked the
actual original caller at `0x002B85BC`.

The original confirms the report's main semantics: `r1` remains a full-width
index for `T + 12*index`, while `STRH` stores its low halfword; `r2` is compared
as a full-width selector, while `STRB` stores its low byte. It reads the table
pointer from record `+0x64`, returns unchanged if it is zero, and otherwise
writes index metadata at `+0x68/+0x6A`, clears bytes `+0x88/+0x8A`, and stores
selector byte at `+0x6C`. The selected full word is loaded from table-entry
offset 0 for selector zero or 4 for any nonzero selector, then copied in order
to `+0x24`, `+0x28`, `+0x2C`. The selected table read follows the metadata
writes, so both alias-order fixtures are material. It returns the incoming
record pointer in `r0`; the function has no stack frame, calls, or callee-saved
register writes.

At the original caller's `0x002B86D8` branch, mode byte `object+0x4C8 != 1`
selects the two-iteration `0x002AA268` path at `0x002B86FC`, with
`r0=object+0x37C+i*0x8C`, `r1=0`, `r2=1`. The separate `mode == 1` path calls
`0x002BDAC0` with the same record progression but `(index,selector)=(3,0)`;
that helper uses a different table pointer and writes scaled coordinates, so it
is not interchangeable with this pointer-copy routine.

## Fresh differential and caller evidence

I ran the frozen experiment into the independent review output directory:

```text
python -B tools/h2_profile_record_copy_experiment.py --out build/agent-work/H2-semantic/h2-profile-record-copy-review-002aa268/run001/checks/review-001
exit: 0
```

The fresh report matches the candidate and original source hashes pinned by the
conversion packet. All 12 direct cases pass, with zero mismatches. Coverage
includes null table; indices 0, 1, `0xFFFF`, `0x10000`, and `0xFFFFFFFF`;
selectors 0, 1, `0x100`, `0x10000`, and `0xFFFFFFFF`; two table/record aliases;
invalid record; and invalid selected entry. The invalid-record fault is the
initial `record+0x64` word read at `0x800024`; the invalid selected-entry case
faults at `0x80000C` after the metadata stores. Both fault cases match original
fault detail and pre-fault writes.

The runner compares full mapped memory, ordered writes/events, return `r0`,
preserved `r2`, SP, and callee-save preservation. An additional 12-case review
compared exact `r4-r11`, SP, `r0`, `r2`, memory/write events, and fault details;
all pass. Candidate `r1/r3` differences occur in caller-saved registers and
are permitted by the ABI. The candidate leaves the callee-saved set unchanged.

The original `0x002B85BC` composition uses a controlled new-profile fixture
(old profile byte 0, requested profile byte 1) and reaches the real two
`0x002AA268` calls with aligned SP and arguments `(object+0x37C,0,1)` then
`(object+0x408,0,1)`. Original and staged images match for all compared state.
The `0x002BF030` dependency is a deterministic hook, so its effects are not
validated.

The standard runner does not exercise mode byte 1. I separately ran the same
original caller and staged image with `object+0x4C8=1` and controlled valid
`0x002BDAC0` table entries. The images match on full mapped data, writes,
register/stack checks, and caller events; the alternate branch makes exactly
two aligned calls `(object+0x37C,3,0)` and `(object+0x408,3,0)` and makes zero
calls to `0x002AA268`. This checks branch separation, not live mode selection.
The result is saved at
`build/agent-work/H2-semantic/h2-profile-record-copy-review-002aa268/run001/checks/review-001/mode1-caller.json`.

All four mutation controls were detected: wrong stride, byte-truncated
selector condition, wrong third destination, and selected load moved before
metadata stores. The 32-bit arithmetic is sound: unsigned `index*3 + branch`
followed by a four-byte scale is equivalent modulo `2^32` to
`index*12 + (selector != 0 ? 4 : 0)`.

## Object, interworking, IPS, and ledger

The fresh candidate compiles to 68 bytes in the 72-byte slot, has no
relocations, and decodes as ARM instructions ending in `BX LR`. The caller's
direct `BL` target is the even ARM address `0x002AA268`; the helper has no
function-pointer writes or interworking relocation to repair. IPS contains one
record at file offset `0x001AA268`, length 72; replay reproduces the staged
image and changes no byte outside the function slot. The candidate differs
from the original (`exact_matching=false`).

The current CSV row is still:

```text
0x002aa268,72,matching,camp,camp_func_002aa268,src/engine/leaf_batch13_b.cpp
```

This is a concrete ledger blocker to promotion. Current counts are 10,906
`matching`, 53 `non_matching`, and 8 `matching_span` rows across 10,967 ledger
rows. Reclassifying this one function makes the counts 10,905, 54, and 8; text
coverage and total row count do not change. The byte difference must not remain
classified as `matching`.

## Boundaries

This evidence covers synthetic aligned mapped records and tables, explicit
full-width arithmetic and selector cases, two alias patterns, and two matching
faults. It does not establish a valid table length, natural profile table
population, pointer lifetime, concurrency, effects of the hooked `0x002BF030`
service, natural runtime reachability, or game-level profile behavior. Only
the affected translation unit was compiled; no full build or emulator was run.

Fresh evidence:

- Differential report SHA-256: `26f6f58f42da76a32efa2f5bdc7a4542cb2589a3a5b8d5449f85ffe27b38667f`.
- Candidate source SHA-256: `5b53c640a0c75f58d58a13b161792a886419eade52ce4880e06e828edf9356af`.
- Staged image SHA-256: `e1c0e48ebe64908ed5b545991c3d44d1ae2b6e38b6c8acd4b96ed8761a4b3d29`.
- IPS SHA-256: `b80f240f38f4ecae13a18108b785d114accc987465dfd2877309898e9b03dc05`.
- Mode-1 caller result SHA-256: `adc3ed0c0735dbfa403eb4f9c2d238a2b720cb584619cc8c295f6ae2fc0c0af3`.
- ABI register result SHA-256: recorded in the structured handoff.
