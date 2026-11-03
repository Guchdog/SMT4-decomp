# Function Record: `engine_func_002baacc` (0x002BAACC)

## 1. Summary
- **Address:** `0x002BAACC`
- **Size:** 144 bytes
- **File:** `src/engine/leaf_batch30_c.cpp`
- **Classification:** `non_matching`
- **Role:** Subsystem context initializer: clears header state, activates state flags at offsets `0x414`/`0x415`, resets offsets `0x418`/`0x41C`, and initializes nested sub-context at offset `0x420` via `camp_func_002c3344` and table descriptors via `camp_func_002c32f8`.

## 2. Contract & ABI
- **Inputs:** `u8* obj` (`r0`).
- **Returns:** `void`.
- **Effects:**
  - Zeroes `obj[0..0x10]`.
  - Sets `obj[0x414] = 1`, `obj[0x415] = 1`.
  - Zeroes `*(u32*)(obj + 0x418)` and `*(u32*)(obj + 0x41C)`.
  - Calls `camp_func_002c3344(obj + 0x420)`.
  - Calls `camp_func_002c32f8` with table base `0x003FF3F4` and structured stride parameters.

## 3. Verification
- Offline differential verification with Unicorn against original ARM binary (`tools/batch30_batch5_experiment.py`):
  - Verified full 0x500-byte object memory layout, register preservation, and stack frames.
  - Result: PASS.
