# battle_func_002cfbfc (0x002CFBFC)

## Summary
- **Address:** 0x002CFBFC (with companion entry at 0x002CFC38)
- **Size:** 100 bytes
- **Domain:** Battle / Command Trigger & UI Link
- **Status:** Semantically verified (non_matching in ledger)
- **Source File:** src/engine/leaf_batch32_c.cpp
- **Differential Suite:** tools/batch32_c_part4_experiment.py

## Role and Behavior
- **Role:** Dual entry point function:
  1. Entry 1 (`battle_func_002cfbfc`, 0x002CFBFC): Builds an 8-word argument frame on the stack `(0, 0, 0, 0, 8, 0, 6, 0)` and invokes battle setup function `battle_func_00282a90`. Returns 1.
  2. Entry 2 (`battle_func_002cfc38`, 0x002CFC38): Traverses global context pointer `*0x00439B58`, extracts entity pointer at offset `0x14`, calls UI helper `ui_func_0024bb80()`, and forwards both to `ui_func_0024bb18(obj, res)`.
- **Differential Coverage:** Verified in Unicorn across both entry points, confirming parameter staging on the stack and context pointer dereferencing against original binary code.
