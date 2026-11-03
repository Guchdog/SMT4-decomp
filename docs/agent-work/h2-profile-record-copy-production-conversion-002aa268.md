# `camp_func_002aa268` (`0x002AA268`) profile-record copy conversion

## Implementation

Replaced the raw 72-byte ARM body in `src/engine/leaf_batch13_b.cpp` with typed C++. The C++ function has three explicit `u32` arguments and returns the incoming record pointer. It loads the table pointer before writes, returns immediately on null, writes the truncated index/cleared metadata/selector byte in observed order, loads the selected full-width word after those writes, and copies it to the three original destinations in order. Address computation is unsigned modulo `2^32`; the source uses `index*3 + (selector != 0)` followed by a four-byte scale, equivalent modulo `2^32` to `index*12 + (selector != 0 ? 4 : 0)`.

The compiled function body is 68/72 bytes, has no relocations, and differs from the original. It is slot-fitting but remains a byte-level `non_matching` reconstruction; the CSV/README were outside this task's write lease and were not updated. The coordinator should correct the ledger row before promotion.

## Final focused differential

Command:

```text
python -B tools/h2_profile_record_copy_experiment.py --out build/agent-work/H2-semantic/h2-profile-record-copy-convert-002aa268/run001/checks/final3
exit: 0
```

The final report records 12/12 direct cases equal, an equal original `0x002B85BC` composition, zero mismatches, four detected controls, no relocations, successful IPS replay, and no out-of-slot changes. Direct cases cover null table; selector 0/1/0x100/0x10000/0xFFFFFFFF; index 0/1/0xFFFF/0x10000/0xFFFFFFFF; record/table alias at `+0x68` and `+0x6C`; invalid record; and a mapped record with invalid selected table entry. Both fault fixtures match the original fault address and pre-fault writes.

The original selector fixture sets its two profile results through deterministic lookup hooks, uses object mode byte 0, and lets the actual original selector and candidate helper execute. It records two aligned helper entries: `(object+0x37C, 0, 1)` then `(object+0x408, 0, 1)`. The other selector dependency at `0x002BF030` is a no-op hook; this does not validate its transitive effects. The four controls target wrong index stride, byte-truncated selector branch, wrong third output offset, and loading before metadata writes.

Final evidence SHA-256:

- `report.json`: `668a8e3c81f18fd00979c5d054cd3b6653c452fd936386077cf8ea785e6ab477`
- staged image: `e1c0e48ebe64908ed5b545991c3d44d1ae2b6e38b6c8acd4b96ed8761a4b3d29`
- slot IPS: `b80f240f38f4ecae13a18108b785d114accc987465dfd2877309898e9b03dc05`
- affected TU object: `1f00f1eba9a07d0be62ff287a951229fb0b577da43c2ab4a9e11d32a4b72870f`
- candidate source: `5b53c640a0c75f58d58a13b161792a886419eade52ce4880e06e828edf9356af`
- experiment source: recorded in the report; the final runner is owned by this task.

## Iteration notes and limits

The first compiled candidate exceeded the slot at 80 bytes. Adding the `minsize` attribute reduced it to 76 bytes; expressing the selected word index as `index*3 + selector_word` reduced the final body to 68 bytes while preserving the ARM modulo arithmetic. Early harness iterations exposed insufficient map coverage for high indices and an attempted fixture write to the intentionally invalid table pointer; both fixture issues were corrected before the final run. A source-level wrong-stride mutant exceeded the 72-byte slot, so that negative control changes the compiled `add r1,r1,r1,lsl #1` shift immediate in a copy of the in-slot body. It still detects incorrect stride behavior without altering the candidate or weakening the slot validator.

Only the assigned translation unit was compiled. There was no full build or emulator run. Fixtures cover valid aligned mapped records/tables plus two explicit unmapped fault cases; table length, live pointer lifetime, natural H2 runtime reachability, concurrency, and full selector-service effects remain unproven.
