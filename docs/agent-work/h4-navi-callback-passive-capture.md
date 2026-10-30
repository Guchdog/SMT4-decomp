# H4 Navi callback passive capture

## Scope and setup

This paired observation tests whether the callback-like entry `0x00399D60` is reached after the known H3 save has entered Shinjuku Station — Underground and both field-manager callbacks have advanced for 250 ticks. It is a bounded runtime observation, not a movement or interaction test. The callback probe uses software breakpoint `Z0` and read-only register/memory reads. The existing harness writes a temporary title input stub and controlled title-work fields to reach the known save route; it restores the stub before loading. No axis output, physical input, source-save edit, or guest write occurred at the callback probe.

Pinned `code.bin` SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The modified runner is recorded in the structured handoff. Both staged save files were 151,088 bytes with SHA-256 `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9` before and after the successful paired run. The source file at `E:\emulador3ds\sdds4game1.sav` was not opened by this capture.

## Offline-first gates

All gates passed before the successful Azahar run:

- `h3_title_entry_patch.py` passed final H3 image placement and IPS round-trip checks; final image SHA-256 is `af2bc749364703ac11d1b663527a1ea339c571e14f89e0aa4e919c58f71436d8`.
- `h3_title_load_entry_experiment.py` passed its directed differential and detected the negative control that shifts the X halfword read from `+8` to `+6`.
- `h3_title_caller_composition.py` passed the real caller composition; the ARM BL target low bit is zero.
- `h4_axis_reader_experiment.py` passed 119 cases with zero differences and detected its invalid-mode mutation.
- `h4_axis_camera_composition.py` passed six cases and detected the same-input candidate mutation.
- Runner AST parsing and `--help` passed after the runner change.

## Paired observation

After the controlled load route, each process reached the field manager and advanced 250 recorded ticks. The first subsequent breakpoint at `0x00399D60` hit in both runs. At entry, `r0=0x086EB3C0`, `r1=0`, `r2=0x00399D60`, `r3=0`, and `lr=0x001A95E8` in both. The current global slot `0x0044CDF0` held host pointer `0x086EB380`; the entry object in `r0` was exactly `host+0x40`. After validating the eight-byte read range, the probe read the pair at `host+0xB64 = 0x086EBEE4`: `60 9d 39 00 00 00 00 00`, decoded as `(0x00399D60, 0)`. It matched the statically installed pair in both processes.

| Observation | Original | Patched |
|---|---:|---:|
| Field-manager ticks | 250 | 250 |
| `0x00399D60` hit | yes | yes |
| Entry `r0` | `0x086EB3C0` | `0x086EB3C0` |
| Global host `*[0x0044CDF0]` | `0x086EB380` | `0x086EB380` |
| `r0 - host` | `0x40` | `0x40` |
| Pair at `host+0xB64` | `(0x00399D60, 0)` | `(0x00399D60, 0)` |
| Save unchanged; non-mod profile manifest unchanged | yes; yes | yes; yes |

The `lr` value also matches the return address after `BL 0x0039F1F0` at `0x001A95E4` in `0x001A95B8`. Pinned ARM at `0x0039F1F0` reads the object index from `[r0+4]`, selects the callback/user pair at object-relative `+0xB14/+0xB18`, and dispatches through `bx r2`. The entry object snapshot has index 2, so its selected pair is `host+0xB64/+0xB68`; the live `r2`, `r1`, and preserved `lr` agree with that indirect-dispatch path. This dynamically confirms that the table-installed `0x00399D60` callback runs in the paired H3-derived H4 checkpoint through the Navi callback path.

## Limits and diagnostic attempt

The successful runner comparison reports equal title state, save-load callback snapshots, post-confirm event/progress streams, field-manager signature and 250 ticks. This is evidence for this one controlled checkpoint only. It does not establish that `0x00399D60` moves the player, handles a particular physical or logical input, performs the H4 target interaction, or transitions zones. The callback return value and its downstream visual effect were not captured. The previously inspected helpers `0x00231F58`/`0x00231B38` use the current global host slot and do not dereference the `+0x162` argument; this capture does not change that contract.

A preliminary attempt used a copied profile path of 313 characters and failed before the title-init breakpoint (`expected 0x001EB02C`, observed PC `0x0`); it produced no accepted runtime sample. The paired run was repeated with short profile root `C:\H4NaviProfile` and completed. The path-length difference is correlated with recovery, but the failure cause was not independently isolated. Both successful-run Azahar processes exited; ports `54342/54343` were left without listeners.

Artifacts are in `build/agent-work/H4-semantic/h4-navi-callback-passive-capture/run-001/checks/`: offline gate reports and `runtime-navi-entry-002/{report.json,original.json,patched.json}`. This is not H4 movement, interaction, transition, or whole-game equivalence.
