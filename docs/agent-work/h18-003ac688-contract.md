# H18 contract report: `0x003AC688`

Owner: `h18_recon_a`
Scope: read-only contract reconstruction for the first entry point in the compound CSV span `0x003AC688` (680 bytes).
Status: `investigada`; no compile or runtime work performed.

## Bounded behavior

The first entry is a standalone ARM routine at `0x003AC688`, 20 instruction bytes followed by a literal pool word at `0x003AC69C`. Disassembly from `python tools/split_asm.py --addr 0x003ac688` shows:

```text
ldr r0, [pc, #0xc]   ; literal 0x0043d9e0
mov r1, #5
ldr r0, [r0, #4]    ; *(u32*)0x0043d9e4
strb r1, [r0, #0x1d]
bx lr
```

Observed contract: no input registers are consumed; read a 32-bit pointer from global address `0x0043D9E4`, store byte value `5` at object offset `0x1D`, and return to the caller. The object pointer remains in `r0` at return. There are no helper calls, stack accesses, conditional branches, or callee-saved register writes. The operation has one global pointer read and one byte store. The reachable-object validity and lifetime requirements are not established; a null/invalid pointer would fault, and the routine contains no guard.

A bounded editable C++ form already present in `src/engine/leaf_batch45_a.cpp` is:

```cpp
extern "C" u32 ui_func_003ac688() {
    u8* const object = *reinterpret_cast<u8**>(0x0043D9E4u);
    object[0x1D] = 5;
    return reinterpret_cast<u32>(object);
}
```

This captures the observed residual `r0` as an explicit return. Whether any real caller consumes that value is unknown. If the integration interface later uses `void`, the original `r0` behavior should still be accounted for in caller evidence before being discarded.

## Callers and neighboring entries

- A read-only aligned ARM `BL` immediate scan of `extracted/exefs/code.bin` found **zero** direct `BL` references to `0x003AC688`.
- No references to `ui_func_003ac688` or `0x003AC688` appear elsewhere in reconstructed `src/` C++ outside its definition/comments.
- This does not rule out indirect calls, function-pointer tables, Thumb/BLX calls, references encoded in data, or entries into an interior address. No real caller/composition contract is established.
- The CSV row spans 680 bytes but contains three independently reachable routines: this setter, state updater at `0x003AC6A0`, and indirect dispatch helper at `0x003AC908`. They must not be treated as one linear function. The existing source reconstructs those separately. Their dependencies/caller behavior are outside this address's bounded proposal; the state updater calls helpers at `0x002A63F8`, `0x002941B4`, `0x002BF9F0`, `0x002AF854`, `0x00294568`, and `0x00295B9C`; the last entry performs a vtable slot `+0x0C` call through the manager/object chain rooted at `0x0043D990`.

## Evidence: facts and inferences

**Observed from original disassembly and pinned image inspection**

- Instruction sequence, literal value, global pointer location, byte offset/value, and `bx lr` return are as transcribed above.
- `r0` contains the loaded object pointer at the branch-to-link-register instruction.
- The code has no null test or direct calls.
- The ledger classification is `non_matching`; no byte-identity claim is relevant to semantic acceptance.

**Existing project artifacts (secondary evidence, not a new run)**

- `docs/function-records/003ac688.md` records the three-entry compound span and reports a prior Unicorn differential run of 65 cases, with eight negative controls detected. The record explicitly limits that evidence to synthetic fixtures and says no caller-composition or runtime game comparison was done.
- `tools/test_leaf_003ac688.py` includes baseline, preexisting-byte overwrite, and unrelated-field preservation cases for the setter. I did not execute it.
- The candidate currently lives in `src/engine/leaf_batch45_a.cpp` and is already readable C++ matching the observed operation.

**Inference / unresolved**

- The global at `0x0043D9E4` is named as the active UI object pointer in existing comments/records, but the owning class, initialization/lifetime, and valid object shape remain unknown.
- No evidence proves that the returned pointer is consumed by any real caller.
- Since this is ordinary game memory in the inspected code, a normal byte store is the natural C++ expression; concurrent observers/MMIO behavior is not established.

## Validation needed for promotion or stronger claims

1. Keep the object pointer and target byte in valid mapped RAM; vary initial byte values and non-target object bytes. Compare original and compiled candidate for the byte write, pointer residual `r0` if the test treats it as observable, continuation, and ABI preservation.
2. Include a negative control changing the stored value or offset and confirm the relevant comparison detects it.
3. Identify real call sites, including indirect/table-based and Thumb references, then test the actual caller continuation and whether it consumes the residual `r0`. The aligned ARM `BL` scan alone cannot establish absence of callers.
4. For any whole-program claim, capture the actual global pointer/object state and compare an original-versus-patched scenario where this entry executes. Existing synthetic helper stubs and entry-only testing do not supply that evidence.

No validation commands beyond the read-only disassembly and read-only BL scan were run. No compiler, canonical build, emulator, or runtime was used.
