# Independent runtime review: `0x00286928`

**Task:** `h2-helper-00286928-runtime-review`, run002
**Recommendation:** Accept the dedicated runtime evidence as a bounded paired-scenario result. Keep H2 open. Correct the README’s overbroad cumulative-image wording before treating its summary as current.

## Identity and hash checks

All hashes declared by the frozen run002 packet match the current inputs. The runtime JSON hash is `7ea75a944d1f72c62ae76bbdc3f86c2d4c2a5d1f5fe0ded85b6c02110b3d3c76`. Its pinned original code hash matches the packet reference (`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).

The report’s cumulative image and IPS hashes match both the cumulative manifest and the bytes on disk:

- Image: `1616aa24873a72beafdc9ae12cf688f9d7575b11a3f9b3f366c77fddd1f4e703`
- IPS: `cc63c2fe655bdc38c3c017531cc429de6eb9c9a287f6f9c5ad31126a8e5a2252`
- Manifest records 629 IPS records, successful round-trip, and only the new helper slot changed relative to its stated base. It explicitly cautions that the prior H2 base has source-identity caveats; the runtime finding is therefore tied to these exact image bytes, not a source rebuild claim.

The report pins wrapper `tools/h2_86928_runtime_verify.py` at `3e8bf0b7a964c1fa4fcb82b2143a497ea562f966dc257672a37579c8e4255e46` and base runner `tools/h2_autonomous_gdb_verify.py` at `c68c357d36ed7ab6b45b7f63bfec0ebd8ae8578b68ab2f0d1588cd89c419a94e`. The stored helper-probe digest also recomputes to `89ff43a7d75b8a8b53b31ab7ce5adbc70a3e46becbe637f2840343b87c66697b`.

## Capture and parity

The wrapper installs an RSP software breakpoint at the even ARM address `0x00286928`. At each stop it captures `r0`–`r3` and the two words at entry `sp`, clears the breakpoint, single-steps the first ARM instruction and checks that PC advances to `0x0028692c`, then rearms it. It places a temporary breakpoint at the captured LR when needed and records the raw return `r0` at that return PC. The capture covers the six ABI argument words and raw return; it does not claim `sp` or `lr` parity.

The report has 129 original and 129 patched events, with a return captured for every event on both sides. Independently comparing the four register arguments, two stack arguments, and return `r0` for each ordered event yields exact parity. The stored `entry_arguments_and_raw_returns_matched` flag agrees. Three return PCs are represented (`0x001ecc04`, `0x002211f0`, and `0x0031e94c`); this supports helper reachability across the scenario without attributing every hit to one caller.

The paired scenario reports 51 scripted actions and 19/19 passing checkpoint comparisons. The image/IPS identity in this report is the cumulative image under review. This is evidence for this driven scenario and captured helper calls, not all caller domains, all callees, or whole-game equivalence.

## Boundaries and documentation

The runtime JSON and per-function record correctly say readiness did not complete on either side, same-session re-entry did not occur on either side, and full controlled lifecycle completion is false. Restart persistence outcome matches the original, but neither side’s restart matched confirmation. The driver substitutes a deterministic one-frame logical query response. Physical controller mapping and input scheduling are explicitly unproven. These limits support keeping H2 open; no blocker invalidates the bounded parity result.

One README statement needs narrower wording: the paragraph immediately above the H2 function table says this work “does not establish equivalence for one cumulative patched image.” The dedicated run now does compare a specific cumulative patched image and establishes parity for its defined 51-action scenario. Suggested replacement: “The paired runtime comparison establishes parity only for its defined scripted scenario on the recorded cumulative image; it does not establish whole-game or full H2 equivalence.” The H2 milestone summary should also identify this newer run as the latest bounded comparison (or explicitly label its existing 2026-11-01 run as an earlier run); its current summary names only the earlier 0x002B8D24 comparison. Keep readiness/re-entry and physical input limits in that summary.

## Review procedure and result

Read-only inspection only; no build, runner rerun, or emulator launch. Commands used were hash verification of the packet inputs and runtime artifacts, JSON extraction and independent event-signature comparison, `rg`/source inspection of the wrapper and base RSP runner, and review of the README, function record, implementation report, and H2 milestone summary. All completed with exit code 0. No runtime evidence was regenerated.

**Next action:** Narrow the README cumulative-image sentence and refresh the H2 milestone summary to point to this run while preserving its lifecycle limits. The dedicated runtime result itself is ready to be recorded as a bounded pass; it does not close H2.
