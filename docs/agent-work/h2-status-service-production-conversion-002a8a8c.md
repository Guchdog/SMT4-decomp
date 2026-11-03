# `ui_func_002a8a8c` (`0x002A8A8C`) status-service conversion

## Implementation

Replaced the raw 36-byte ARM block in `src/engine/leaf_batch23_b.cpp` with typed C++. It reads the global pointer at `0x0043DCB4`, returns `P+0x600` in `r0`, performs a signed `s16` load from `P+0x64C`, and decrements/stores only for values greater than zero. The counter write is a 16-bit volatile access. The incoming `r0` remains irrelevant, and the unguarded pointer/fault behavior is preserved.

The compiled ARMv6K function is 36/36 bytes with no relocations. It differs from the original bytes, so the production ledger should classify the function `non_matching`; ledger and README were outside this task's write lease and remain unchanged. The source contains an empty register constraint to keep the computed return base distinct from the counter access base under optimization; it emits no machine instruction and permits the typed body to fit the original slot.

## Final focused evidence

Command:

```text
python -B tools/h2_status_service_experiment.py --out build/agent-work/H2-semantic/h2-status-service-convert-002a8a8c/run001/checks/final4
exit: 0
```

Final report SHA-256: `7938e5f5b10dd890aec43a9ac67e0615ec5bc839ec4f33c8074a3b533c6b0885`.

Direct differential passed all 11 cases. The six signed boundary values are `0x8000`, `0xFFFF`, `0`, `1`, `2`, and `0x7FFF`; additional cases prove the incoming `r0` is ignored and adjacent bytes are preserved. `P=0` faults at `0x64C`; an unmapped counter read faults at the computed counter address; a read-only positive counter faults on its halfword store. All faults and pre-fault states match the original. The full mapped data and global snapshots, raw `r0`, sign-extended/decremented `r1`, preserved registers/SP, and ordered writes are compared.

The caller harness compiles/rebases the typed selector at `0x002B85BC` and installs this helper at final VMA. Each fixture runs the six spaced status bytes `[0,1,7,8,9,2]`, yielding nine service calls. Status bytes remain unchanged while the independent global counter decrements from 3 to 0 in three stores, or from 1 to 0 in one store. Both integrated original-versus-typed-selector compositions matched. The dependency services for profile lookup and `0x002BF030` are explicit hooks.

Four in-slot binary mutation controls were detected: decrementing zero, treating negative halfwords as unsigned positive, replacing the halfword store with a byte store, and loading the pointer from the wrong global offset. The status-only IPS replays exactly and changes no bytes outside the 36-byte slot. A two-slot status-plus-typed-selector composition image and IPS also replay exactly and modify only the two declared slots; that image is a validation fixture, not a production promotion claim.

Artifact SHA-256 values:

- status staged image: `5e91008bbe364b2dae41e617dbb746a61397ccce02dbddefe7efc7c7f5709b72`
- status IPS: `3308968297d57c9becbaafb27c7c9063d1e8293c20baa60541bda671ad8eca64`
- typed-selector composition image: `9fa2e50c0b9088b5536c513beb9ab2b1be9026c8323ec8e20793e674d2cceef9`
- typed-selector composition IPS: `03ecc2400ea29b75ac411b2e569ba32c042b93ffd7ec5498b3f2aa171027f3d1`
- status object: `8b4be8a9e2193fc9c11fcca7f3d66ec4d386403044255fc032a386ba19f12625`
- selector object: `ab280f5c40c573ae14a4b648a91a190608e5fbcd76967bff1340845fbb2aea91`
- status source: `718839e52ac638f0d9612ffcce047bcbcb874037e0f9a0051c31ff6000104f8f`
- typed selector source: `b3e09dd3cb90e8b9b4a21e113fbcf361dd8ee096675f2d22a48fee9d644578c1`

## Integration follow-up and limits

`leaf_batch44_c.cpp` currently declares `ui_func_002a8a8c()` as returning `void`, whereas this implementation returns `u32`. Since the caller discards the result, the ARM call ABI is compatible and the composed run passes, but the declaration should be aligned in the coordinator's integration changes. The helper's status pointer/counter is synthetic; selector profile lookup and manager-slot service calls are controlled hooks. This work does not establish counter lifecycle, live pointer validity, natural call reachability, the effects of other callees, or audio/runtime behavior. Only the affected translation unit was compiled; no full build or emulator run was performed.

The handoff contains the final-run command, artifact hashes and separate compiled, differential, caller and runtime evidence levels.
