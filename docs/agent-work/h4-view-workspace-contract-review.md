# Independent Review: H4 View Workspace Contract

**Task ID:** `h4-view-workspace-contract-review`  
**Reviewer:** `h4_recon_reviewer`  
**Target:** `docs/agent-work/h4-view-workspace-contract.md`  
**Date:** 2026-10-30  

---

## 1. Scope and Objective

This review independently evaluates the static ARM contract report for `0x001B4664` (440 bytes), verifying all instruction-level field writes, literal constants, heap allocation boundaries, and global side effects in `*[0x00447E88]` and `0x0049F91C`.

---

## 2. Integrity and Instruction Audit

All 110 ARM instructions of `0x001B4664` and the literal pool at `0x001B47F8..0x001B481C` were independently disassembled from `extracted/exefs/code.bin` (SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`):

1. **Floating Point Literals:**  
   - `0x1B47FC`: `0x00000000` -> `0.0f` (`s16`)
   - `0x1B4800`: `0x41200000` -> `10.0f` (`s0`)
   - `0x1B4804`: `0xC2B40000` -> `-90.0f` (`s1`)
   - `0x1B4808`: `0x40A00000` -> `5.0f` (`s2`)
   - `0x1B480C`: `0x42C80000` -> `100.0f` (`s0`)
   - `0x1B4810`: `0x447A0000` -> `1000.0f` (`s1`)
   All IEEE-754 single-precision float representations are verified correct.

2. **Workspace Offsets (`*[0x00447E88]`):**  
   - Position coordinates initialized to `(10.0f, 0.0f, 10.0f)` at offsets `+0x1C`, `+0x20`, `+0x24`.
   - Target coordinates initialized to `(10.0f, 0.0f, 10.0f)` at offsets `+0x28`, `+0x2C`, `+0x30`.
   - Look-at vectors initialized to `(10.0f, -90.0f)` at `+0x48`, `+0x4C` and `-90.0f` at `+0x50`.
   - Distance / radial parameter set to `100.0f` at `+0x58`.
   - Near/far clip distances set to `5.0f` (`+0x160`) and `1000.0f` (`+0x15C`).
   - Active state flag byte set to `1` at `+0x134`.
   - Sentinel word `-1` (`0xFFFFFFFF`) set at `+0x18C`.

3. **Subobject Allocation (`+0x194`):**  
   - `AsdMem_Alloc(0x100)` at `0x002C23F8` allocates `256` bytes.
   - Constructor `0x00294A98` clears `0x50` bytes and publishes vtable `0x00420420`.
   - Pointer safely stored at `work+0x194`.

4. **Global Repeat / Gate State (`0x0049F91C`):**  
   - Computed base `0x0049FA1C - 0x100 = 0x0049F91C`.
   - Offsets `+0x17C..+0x1B4` initialized to zero (bytes, floats, and halfwords).

---

## 3. Recommendation

**ACCEPT.** The contract is complete, fully verified against retail machine code, and ready to guide C++ reconstruction.
