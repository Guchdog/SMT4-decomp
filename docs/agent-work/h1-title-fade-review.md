# Independent review — 0x00210030 title fade front gate

## Verdict

**Partial; do not promote as a complete replacement.** The pinned ARM entry sequence, VFP forwarding, signed final boundary, and continuation tail path agree with the compiled candidate. The experiment gives useful branch evidence for the front gate. It does not establish all behavior for a changing `object+8` pointer or cover the deeper positive callees and live caller object graphs.

## Independently checked

- Pinned entry `0x00210030` is 68 bytes, ARM state. Its verified sequence saves `r4/lr` and `d8`, copies incoming `s0` to `s16`, loads `object+8` and calls `0x002872A4`, restores `s0`, reloads `object+8` and calls `0x0020FFA0`, reloads `object+8` again, restores `s0`, restores saved state, and checks signed `child+0x68 <= 0` before returning or falling through at `0x00210074`.
- The two 12-byte front gates are confirmed in pinned bytes and source wrappers: `0x002872A4` checks signed `child+0x34` and `0x0020FFA0` checks signed `child+0x58`. Positive inputs fall through to `0x002872B0` and `0x0020FFAC` respectively.
- Compiled object SHA-256 is `77da36838869facd950b48a7f0b769702f7b01d3235f95523894688ab990724d`. Its instructions save `s0` in callee-saved `s16`/`d8`, restore `s0` before the second gate and before the positive tail branch, and call the original gate entries using `blx`. The source `FadeGate(void*, f32)` therefore forwards the float in hard-float `s0` under the recorded ARM hard-float build flags.
- Candidate signed `<= 0` compiles to `cmp r0,#1; blt`, which is signed `< 1`; it matches the original signed `cmp #0; bxle`. The negative control compiles to `< 0` and the report shows zero incorrectly reaches `0x00210074`.
- The positive candidate path restores its frame and tail-branches (`bx r1`) to `0x00210074`; the object calculation resolves to that address. The tail branch passes the child pointer and fade value while retaining the caller LR, matching the original fallthrough shape rather than adding an extra return frame.

## Concrete gaps and limits

1. **Child pointer reloads are elided.** The original has loads at `0x00210040`, `0x0021004C`, and `0x00210054`; the compiled candidate has one load at object offset `+8`, keeps the value in `r4`, and reuses it for both callees and the final test. In the tested positive first-gate case, this mutation is *not reached*: the fixture uses a separate synthetic record and callback object, and the counted callback stub is only `bx lr`; the original first positive body writes to its record, not the parent object's `+8`. No counterexample is claimed from the executed cases. A real callback or aliased object graph could change the parent's `+8`, after which original and candidate would pass/test different children. The allowed runtime aliasing and callback effects are not established. Either reload from the parent at the three original points or provide caller/object evidence that `object+8` stays invariant across these calls and exercise that constraint.
2. **Early-return `r0` differs, but observed direct callers discard it.** For the report's object (`object = 0x02000100`, `object+8 = 0x02000400`) and final gate zero, original reaches `bxle lr` with `r0 = 0x02000400` because it compares through `r1`. Candidate's early path loads `child+0x68` into `r0` before its signed comparison, so it returns with `r0 = 0`. For a negative final word `0xFFFFFFFF`, candidate returns that word instead. `r0` is caller-saved and the C++ API is `void`; this is not by itself an AAPCS callee-save violation. A read-only scan of aligned ARM BL-shaped references found nine direct references (including one conditional BL); each inspected continuation reloads `r0` before subsequent use. This supports that the known direct callers do not consume the difference. It is not a complete audit of indirect/Thumb call sites, so keep the return contract documented as caller-dependent until those are ruled out.
3. **Coverage stops at distinct boundaries.** The report has 15 directed values, but positive values do not all exercise full bodies. The first positive body at `0x002872B0` does execute in two cases and reaches one synthetic callback (`bx lr`); it does not establish the game's callback target. The second positive body at `0x0020FFAC` executes only to its first early return because the fixture sets the `+0x148` guard word to zero; its deeper table and callback path is not tested. The positive fallthrough body at `0x00210074` is reached, but exits at its initial `+0x150` zero guard; its deeper callback path is also untested. Negative/zero values test the 12-byte gates and do not enter those bodies.
4. The runner compares memory, callback count, SP, `d8-d15`, and a single continuation-path bit. It returns `r0` and `s0` snapshots but `_check` does not compare them, and it does not compare `r4-r11`. The object disassembly supports preservation of the registers it explicitly saves; the report should not describe unasserted integer callee-saved state as differential coverage. The first positive synthetic body exercises some float-dependent memory effects, but the callback stub does not assert the incoming `s0/s2` values.

## Evidence identity and commands

- Source SHA-256: `8f2f8363fc4d56fb5231d5b128c4ad9f78cdb47d891adddeb85acf6e873ab67e`.
- Original image SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- Original 68-byte entry SHA-256: `3f8d4d694b6de74559c6e2fc3ea7bf85e35ddc3e6d5cb13766501d16aa270161`.
- Run-2 report SHA-256: `ca532da99a74e6e27ba0ef1d3cc8327dd31a892b1512a9f48d4fafb02650c7b6`.
- Candidate object SHA-256: `77da36838869facd950b48a7f0b769702f7b01d3235f95523894688ab990724d`.
- Read-only object inspection: `& 'C:\msys64\clang64\bin\llvm-objdump.exe' -d build/agent-work/H1-semantic/h1-title-fade-candidate/sleep-20261025-title-fade/checks/run-2/h1_title_fade_candidate.o` — exit 0.
- Original entry/body and caller inspection used read-only Capstone decoding of the pinned `extracted/exefs/code.bin`; no compile, test, emulator, source, or candidate changes were made for this review. The implementer's recorded test run is not an independent rerun.

## Next action

Keep this as a bounded partial front-gate candidate. Resolve the parent `+8` invariant or update the candidate to reload, add an adversarial mutation/alias case if the domain permits it, and have the integrator decide whether the return-register audit needs indirect/Thumb callers. Assign separate contracts for the deeper `0x0020FFAC` and `0x00210074` paths before any full promotion; do not infer runtime equivalence from the 15 synthetic cases.
