# H4 Navi trigger runtime route capture

## Scope and offline-first gate

A paired, passive run traced one naturally scheduled callback from `0x00399D60` through `0x0039C944`, `0x0039C968`, and `0x0039C9E8` using the original and patched images with isolated `C:\H4NaviProfile` profiles. Before launch, the task-pinned image, runner, four reusable offline H3/H4 reports, candidate and composition runners all matched their frozen SHA-256 values; see `checks/preflight.json`. H3 entry and caller, H4 direct reader and camera-composition evidence were reused, not rerun here.

The source save `E:\emulador3ds\sdds4game1.sav` was SHA-256 `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9` before the paired run and had the same hash in the postflight audit. Both staged saves also remained 151,088 bytes with that same hash before and after. No axis override, physical input, synthetic game-state change, or guest/register writes were used at the passive probes. The normal debugger-mediated title-load confirmation seam remained enabled.

## Paired trace

Command: `python tools/h3_autonomous_verify.py --output build/agent-work/H4-semantic/h4-navi-divisor-trigger-runtime-capture/001/checks/runtime-006 --profile-root C:\H4NaviProfile --callbacks 250 --confirm-load --post-callbacks 60 --field-ticks 250 --field-probe-address 0x00399D60 --field-probe-address 0x0039C944 --field-probe-address 0x0039C968 --field-probe-address 0x0039C9E8 --timeout 90`.

All four breakpoints hit in both runs in the requested order on GDB thread 1. The PC at each stop equals its requested address. Registers `(r0,r1,r2,r3)` were identical between profiles at each stop:

| Address | `(r0,r1,r2,r3)` | What this stop establishes |
|---|---|---|
| `0x00399D60` | `(0x086EB3C0, 0, 0x00399D60, 0)` | Callback entry; `r0` points to object `0x086EB3C0`. The validated global Navi slot `0x0044CDF0` contains host pointer `0x086EB380`. |
| `0x0039C944` | `(0x086EB3C0, 1, 6, 1)` | Same callback-object pointer reaches the helper entry. |
| `0x0039C968` | `(0, 1, 6, 1)` | Helper route check is reached with the entry bit clear (`r0=0`). |
| `0x0039C9E8` | `(0, 1, 6, 1)` | Clear-bit route reaches the threshold block in this invocation. |

The callback-entry 0x60-byte object snapshot decoded to word `+0x10=0` and floats `+0x3C=0.0`, `+0x40=0.0` in both profiles. The captured callback-table pair was `[0x00399D60, 0]` in both. These snapshots corroborate the same-object route through the threshold entry, but the probes do not capture the threshold comparison's outgoing branch or the later accessor/divide sites. They therefore do not directly prove the early exit, divisor reachability, or divisor value. In particular, do not interpret the clear-bit entry alone as proof of all behavior inside the helper.

The raw `0x00399D60` probe records also contain an auxiliary `navi_callback_call_return_trace` with status `unexpected_stop` and one event at the entry PC. The command above did **not** include `--navi-callback-return-trace`. Inspection of this runner version shows that it populates this auxiliary field unconditionally; the flag only clears the entry breakpoint before starting that nested trace. With the flag absent, the entry breakpoint remains armed and the nested continuation immediately stops there again. This is not callback-return evidence and is excluded from the route claims. The separate ordered probe records remain the evidence for the later helper and threshold PCs.

Both profiles acknowledged the load-complete step, reached the field manager, and recorded 250 tick snapshots (initial snapshot plus 249 subsequent successful tick returns). The runner's defined field-scene signature/tick comparison is equal. This is a bounded three-value signature comparison, not equality of all scene state. The overall report status is `observed`; unrelated optional negative-control comparisons are false because those controls were not requested.

## Integrity, cleanup, and limits

For both staged profiles, `save_before` and `save_after` match the external save hash, and `save_unchanged` and `non_mod_profile_unchanged` are true. The external source-save pre/post hashes and runtime cleanup are persisted in `checks/postflight.json`. After the run there was no Azahar process and no listening GDB port on 54342 or 54343; only a closed `TIME_WAIT` connection was visible.

This is one paired checkpoint observation. It confirms that one naturally scheduled callback takes the clear-entry-bit route to the threshold block in both builds and that the bounded scenario agrees. It does not establish movement, interaction, zone transition, a threshold branch outcome, accessor/divide reachability, a general divisor domain, or H4 completion. The next useful passive capture should include the threshold comparison's outgoing branch and the accessor/divide addresses in one invocation, still without synthetic input or state mutation.
