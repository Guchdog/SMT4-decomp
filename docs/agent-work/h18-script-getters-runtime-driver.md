# Getter runtime driver: 0x002345f0 / 0x002345fc

## Result and safe invocation

`tools/h18_script_getters_runtime.py` prepares an isolated original/patched Azahar pair and collects getter entry/return events through the private loopback GDB stub. It does not invoke the emulator unless `--launch` is explicitly supplied. This task only ran syntax and offline patch/interworking checks; no emulator was launched.

Run the offline gate (choose a fresh output directory; the JSON check record is saved there):

```powershell
python -m py_compile tools/h18_script_getters_runtime.py
python tools/h18_script_getters_runtime.py --check-only --output-dir build/agent-work/batch-h18-001/h18-getters-runtime-driver/run-001/offline-check-next
```

For the coordinator's runtime run, use an unused output directory and two free adjacent loopback ports:

```powershell
python tools/h18_script_getters_runtime.py --launch --output-dir build/agent-work/batch-h18-001/h18-getters-runtime-driver/run-001/runtime --base-port 59962 --timeout 45
```

Default inputs resolve to the pinned original `code.bin`, the offline staged getter IPS, private loopback-bound Azahar, decrypted CCI, and pristine profile seed. Pass explicit paths if those defaults are not present in the coordinator's checkout. Output must be fresh. The script stages separate portable `original` and `patched` profiles, puts the IPS only in the patched profile, launches each sequentially on its own port, then terminates each process.

## Offline checks performed by the driver

The offline gate verifies the configured pinned original image through the existing reference scanner, applies the staged IPS, confirms the resulting whole-image hash is `d704a4c5550f60c894b4db26d48d9740ba75a560970a0835209f882aa4372552`, and rejects changes outside the two getter entry bodies. It verifies the expected 8-byte ARM bodies, checks the complete inventory of 16 direct ARM `BL` sites per getter, confirms all targets are exact even ARM entry addresses, and confirms the IPS leaves the call instructions unchanged. The staged IPS records are eight bytes each; 14 byte values differ from the original because two encoded instruction bytes were already equal.

The runtime launch is gated on both frozen staged differential reports: exact report SHA-256, pinned original/patched/IPS hashes, both getters at 80 cases each, four passing caller windows, and two detected negative controls for each seed. Those reports are summarized in `docs/agent-work/h18-script-getters-stage.md`; compiler budget was zero, so they were inspected and hash-checked rather than rerun here.

## Runtime observations and comparison

Each profile reaches the existing scripted boot/start gate using the same temporary `UiInput_Trigger2` return stub already used by the H2 harness; the original helper bytes are restored as soon as the Title Main initialization breakpoint is reached, including failure paths. Getter breakpoints are armed during this route. At each getter hit the driver removes that entry breakpoint temporarily, records `r0`, the four bytes at `p+0x48..0x4b`, LR-derived caller/continuation, CPSR and preserved registers, then breaks at the saved continuation and records returned `r0`, CPSR, callee-saved registers and the same field bytes before rearming the getter breakpoint.

Paired event sequences compare getter, caller and occurrence ordinal, observed field bytes, returned value, continuation, CPSR and preserved register state. Absolute heap pointers are recorded but normalized out of equality. Inputs (private Azahar, CCI and seed profile files) are hashed before/after; a mutation changes the report to `input_mutated`. `getter-runtime-report.json` stores events, per-getter hit counts and the comparison result.

A no-hit result is `inconclusive_no_hits`, never a pass. Failure to reach the scripted start gate is also inconclusive. The driver does not claim the H2 audio-settings route executes these script VM getters; it only reports actual observed hits from this scripted boot/title-idle route. A deterministic script VM trigger may still be needed.

## Limits

Runtime comparison covers only calls that actually occur in this route. It does not prove all 16 static callsites execute, actual application behavior for other script contexts, MMIO or read-width-sensitive memory, inaccessible/page-boundary faults, races, or unobserved callers. Original getters perform a halfword read while replacements perform byte reads; the offline evidence is restricted to ordinary side-effect-free RAM. A GDB RAM snapshot cannot close those read-width limitations. No runtime or whole-game equivalence is claimed by preparing this driver.
