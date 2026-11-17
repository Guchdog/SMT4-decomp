# Runtime plan: paired script getters `0x002345f0` / `0x002345fc`

## Concrete patch and launch path

These replacements can be patched in place without a code cave: the original entries each occupy 12 bytes, the production ARMv6K C++ symbols are 8-byte `LDRB r0,[r0,#imm]; BX lr` leaves, and the text segment maps `vaddr 0x00100000` to `code.bin` file offset `0`. Write each 8-byte leaf at file offset `address - 0x00100000` (`0x001345f0` and `0x001345fc`) and retain the untouched trailing original four bytes, which are unreachable after `BX LR`. Build a final image from the pinned `extracted/exefs/code.bin`, generate a standalone IPS from original/final using `tools.h2_manual_final_image_stage.compose` (or `tools.h2_calc_code_patch.encode_ips`), and require `apply_ips(original, ips) == final_image` before staging.

The source of the exact production object is already exercised by `tools/h18_script_word_getters_production.py::compile_production_symbols`; its current frozen reports show 8-byte ARM code. The existing `tools/h2_autonomous_gdb_verify.py::stage_portable_dir` stages a private Azahar executable and runtime DLL/plugin set into separate portable user profiles, seeds both from `build/h2-runtime/profile-pristine-user`, and installs supplied `ips_bytes` only into the patched profile at `user/load/mods/00040000000E5C00/exefs/code.ips`. `execute_h2_scenario` launches with `azahar.exe -g PORT CCI` and attaches via loopback GDB RSP. A focused getter driver should reuse those staging/RSP primitives, running original and patched profiles sequentially on separate ports with the same CCI and seed. Current private Azahar, CCI, pristine profile, and helper paths exist in this checkout; their identities still need pinning in the runtime run manifest.

The shipped `h2_autonomous_gdb_verify.py` is not itself a getter verifier: it drives the TitleConfig/audio-settings lifecycle and does not set getter breakpoints or assert that either getter executes. It can provide a launch/staging base, but a small separate getter-specific driver is needed. Do not claim that the H2 audio-settings scenario reaches these script VM functions until breakpoint evidence confirms it.

## Offline gate before any launch

1. Run the existing production-source runner twice with fresh output children and the already evidenced seeds:

   ```powershell
   python tools/h18_script_word_getters_production.py --code extracted/exefs/code.bin --seed 7 --samples 64 --output build/agent-work/batch-h18-001/h18-runtime-getters-plan/run-001/checks/offline-seed-7
   python tools/h18_script_word_getters_production.py --code extracted/exefs/code.bin --seed 20261024 --samples 64 --output build/agent-work/batch-h18-001/h18-runtime-getters-plan/run-001/checks/offline-seed-20261024
   ```

   Existing integration reports for both seeds already pass 80 cases per getter, four paired caller windows, two negative controls, full register/flags/continuation/data/write checks and original/candidate read-set reporting. Read-width identity is intentionally excluded under the ordinary-RAM contract.

2. Before building the IPS, assert the production source/object hashes and decoded ARM leaf bytes, then statically verify that the 16 direct `BL` call sites to each address are ARM-state calls to even addresses. The candidate emits ARM instructions, so no Thumb bit or interworking veneer is needed. Ensure no patch entry or return address is mis-tagged as Thumb. The production runner's Unicorn caller compositions are the offline caller gate; rerun them against the final IPS-applied `code.bin` (not just an in-memory replacement) and confirm the two original `BL` instructions still target the exact entry addresses.

3. Apply the generated IPS back to the pinned original and verify both the whole-image hash and the changed-byte set. Verify only the two expected 8-byte entry regions changed and that each branch/call target remains ARM. Do not reuse any existing H2 IPS as the getter patch; its code image is a separate composition.

## Getter observation and paired comparison

In the new RSP driver, set entry breakpoints at both getter addresses for each staged run. At every hit, record `LR` (callsite is `LR - 4` for these ARM `BL`s), caller address, occurrence ordinal, `r0` pointer, the input bytes at `p+0x48..0x4b`, CPSR/NZCV and `r4-r11`/SP. To observe the return, clear the entry breakpoint while stopped, set a temporary breakpoint at the saved LR continuation, continue, then record returned `r0`, PC/CPSR, preserved state, and relevant record bytes. Re-arm the entry breakpoint and continue through the same deterministic scenario. Compare normalized event sequences by callsite and ordinal, input field bytes, returned low byte, caller continuation/ARM state, flags, callee-saved state and relevant memory. Normalize absolute heap pointers if separate runs allocate them differently; do not require pointer equality unless startup proves deterministic allocation.

Start with the existing scripted boot/title/audio-settings route and instrument all four observed script VM callers (`0x0038c43c`, `0x0038cdf4`, `0x0038d7b0`, `0x0038de60`). If the scenario produces no getter hits, it is not a getter runtime test: first identify a deterministic game/script trigger from caller behavior and captured original execution, then repeat both profiles. The static inventory has 16 aligned ARM `BL` sites per getter, but the offline evidence only executes one paired window in each caller; runtime should report exactly which sites were observed. A no-hit result is inconclusive, not a pass.

Keep the access-width limitation explicit even after runtime comparison. The original reads two bytes and the candidate reads one. An ordinary RAM capture can show both bytes readable at observed inputs, but the GDB scenario does not establish equivalence for MMIO, read-width-sensitive memory, page-boundary faults, races or unobserved callers. No canonical project build, IPS package, runtime run, or caller trigger for these getters has yet been demonstrated by this planning task.

## Prepared environment and next action

Read-only checks confirmed paths exist for the private loopback build `build/agent-work/H2-semantic/h2-private-azahar-source/build-clang64/bin/Release/azahar.exe`, its package source `E:/emulador3ds/azahar.exe`, the decrypted US v0.1.0 CCI, the pristine profile seed, and the existing H2 RSP/staging tools. No emulator was launched. Next action: have the integrator authorize a bounded runtime driver/package task that emits the two-record IPS, verifies it against the final image, stages isolated profiles, and records getter hit/return pairs in original and patched execution. If the titleConfig scenario has no hits, resolve a real script trigger before claiming runtime evidence.
