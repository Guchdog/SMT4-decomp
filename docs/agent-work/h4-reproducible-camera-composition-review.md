# Independent review: reproducible H4 camera composition

## Result and frozen provenance

Reviewed packet `build/agent-work/H4-semantic/h4-reproducible-camera-composition-review/run-001`. All 16 SHA-256 entries declared in `task.json` matched the current files. The pinned image is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; candidate C++ is `108b45003ec4908630514b615be7ebe6911fddb83c7448e4a8dacc403dd85aca`; composition runner is `0ee119776d70c070de1c02b06b1adb578fb5501e2f21af5d735e6a9bfa56494a`; report is `0fbb05901d7c27feddb401623c13f23225746b6dfe14a3ff224de8d1bc73521b`; mutant is `94b671373d64e2e3e4d875e0b351d103956c88527eade3985198cf834af9ff44`.

The report's candidate object is present at `build/agent-work/H4-semantic/h4-reproducible-camera-composition/run-001/checks/camera-002/candidate.o` (1288 bytes); its independently calculated SHA-256, `82c0589a66d61818c9a99776d2e6a208beeedd4c574ace6fbc272253d59cf039`, matches the report. `candidate.o.json` pins the candidate source hash and records ARMv6K/ARM-state hard-float compiler flags. I did not rebuild it.

## Independent branch and relocation calculation

The pinned instruction at `0x001FA948` is little-endian word `0xEB02149E`. ARM BL uses `PC=site+8`; sign-extending its 24-bit immediate and multiplying by four yields target `0x0027FBC8`, as reported. With candidate mapped at `0x01000000`, the displacement is `0x01000000 - (0x001FA948+8) = 14,702,256` bytes. It is word-aligned and within the signed ARM BL range. Encoding the displacement gives replacement word `0xEB3815AC`, which decodes back to `0x01000000`. The call's return address is `0x001FA94C`, where the runner records the reader return and stack outputs.

I parsed the supplied object ELF function bytes and independently encoded the two R_ARM_CALL (type 28) relocations to the original helper. Both raw words are `0xEBFFFFFE` before linking:

| Candidate call site | Offset | Manually linked word | Decoded target |
|---|---:|---:|---:|
| `0x010000B8` | `0xB8` | `0xEBC67F63` | `0x0019FE4C` |
| `0x010000C4` | `0xC4` | `0xEBC67F60` | `0x0019FE4C` |

The report's words and targets match these calculations. This confirms the candidate calls the original deadzone helper at the expected even ARM address.

## Fixture, cases, and observed comparison

The runner initializes a synthetic context: `SP=0x08002000`; `r0=SP+4` (X), `r1=SP` (Y), `r2=0`, `r3=0x437A0000` (250.0f), `r8=0x02013000` (slot containing view pointer `0x02012000`), `r9=0x02014000`, `r10=0x5A`, and `r6=0`. It seeds the two stack output words with `0xA5`, the view region with `0x11`, context offset `+0x368` with 2, reader state at `0x004650A0` with calibration pointer `0x02010000`, max 1, flags 0 and case threshold, and calibration bounds 0/100 with default selector 0. It writes test samples at `0x004E3C28`. This is explicit fixture setup, not captured live object state.

All six original/candidate rows compare equal across the returned reader record, deadzone-entry observations, `r6`, the captured `0x170`-byte view prefix, and stop at `0x001FAA84`. Stack bytes are serialized Y then X because the report reads from `SP`; the pointer contract is X at `SP+4`, Y at `SP`.

| Case | Input X/Y | Y then X bytes | Return / `r6` | Helper calls |
|---|---|---|---|---:|
| neutral | 0/0, threshold 0 | `00000000 00000000` | 1 / 1 | 0 |
| positive | 60/0, threshold 0 | `00000000 9a99193f` (+0.6 X) | 1 / 0 | 0 |
| negative | -60/0, threshold 0 | `00000000 9a9919bf` (-0.6 X) | 1 / 0 | 0 |
| plus-half | 50/0, threshold 0 | `00000000 0000003f` | 1 / 0 | 0 |
| minus-half | -50/0, threshold 0 | `00000000 000000bf` | 1 / 0 | 0 |
| deadzone-zero | 10/0, threshold 0.25 | `a5a5a5a5 a5a5a5a5` (untouched) | 0 / 1 | 2 |

For the deadzone case the report records the two original-helper entry values (`0.1` and `0.0`) and threshold bits `0x3e800000` for each, with equal observations on the candidate path. The outputs remain sentinels when reader returns zero. No evidence is claimed for helper return values beyond effects reflected in this bounded window.

The comparison is a bounded instruction-window check: the original path executes the pinned original reader; the patched path retargets only the private copy's call at `0x001FA948` to the candidate. The code hook stops at `0x001FAA84`, after the window. It is not a whole `0x001FA840` task execution. The equality predicate does not track full memory, preserved general/VFP registers, FPSCR, faults, or writes outside the captured stack words and 0x170-byte view prefix. It checks no physical input or rendered camera output.

## Mutation control

The 300-byte `mutant.bin` differs from the candidate blob only at offset `0x30`: instruction bytes change from `01 00 52 E3` (`0xE3520001`) to `00 00 52 E3` (`0xE3520000`). Restoring the four original bytes in the mutant reconstructs a blob with SHA-256 `68bff63e771d574e2ef1bfec4fddecc1fd6c08518424bddc58fcb87e40d34dd6`, the report's candidate hash. The mutation's reported hash matches both the packet pin and independently calculated digest.

The mutation report compares original and mutant using the same direct-reader mode-1 control input: original returns 1 and writes X=0.25/Y=-0.5; mutant returns 0 and leaves output sentinels. This is a useful same-input negative control for the candidate's upper-bound branch. It is run through `direct_run`, not injected into the six caller-composition cases; thus it shows direct semantic sensitivity, not that the composition predicate would detect every caller-level mutant.

## Assessment and remaining scope

The runner and report are reproducible and internally consistent for the stated synthetic `0x001FA948` to `0x001FAA84` window. The exact caller BL, candidate mapping, both links to the original helper, fixture, six equal cases, stop address, captured view bytes, and mutation artifact all check out. This is meaningful bounded caller-composition evidence and addresses the previous lack of serialized patch/relocation provenance.

Keep the candidate experimental. This review does not establish the full camera task, all ABI effects, fault/FPSCR equivalence, runtime/physical control behavior, or rendered-camera response. The function record `docs/function-records/0x0027fbc8.md` still says that composition at the observed `0x001FA948` caller is outstanding; that historical statement should be reconciled by the integrator in a separately owned update. Do not infer H4 completion or promote from this bounded report alone.

## Read-only checks performed

- Read `AGENTS.md`, `docs/agent-workflow.md`, the frozen brief/task, candidate, both runners, function record, prior review, producer handoff, report, object metadata, object, mutant and pinned image.
- Compared all 16 `task.json` input hashes.
- Independently decoded the original and replacement caller BL words and computed/decoded both object R_ARM_CALL links.
- Reconstructed candidate bytes from `mutant.bin`, verified candidate/mutant hashes, and checked the report's six rows and mutation outputs.
- No build, runner/test rerun, source edit, or emulator launch.
