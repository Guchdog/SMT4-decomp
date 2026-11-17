# H18 paired script getter offline stage

## Result

`tools/h18_script_getters_stage.py` compiled the current production translation unit, extracted both actual production getter symbols, verified their ARM `LDRB; BX LR` bodies fit inside the original 12-byte slots, and wrote a direct in-place IPS plus a patched `code.bin` under the assigned `build/` run. The IPS changes exactly eight bytes at each entry and retains the original four-byte `BX LR` tail. Original and patched images were round-trip checked. No emulator was launched.

| Artifact | Path | SHA-256 |
|---|---|---|
| Original `code.bin` | `extracted/exefs/code.bin` | `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` |
| Patched `code.bin` | `build/agent-work/batch-h18-001/h18-getters-stage/run-001/checks/staged-validation/stage/getters-patched.code.bin` | `d704a4c5550f60c894b4db26d48d9740ba75a560970a0835209f882aa4372552` |
| IPS | `build/agent-work/batch-h18-001/h18-getters-stage/run-001/checks/staged-validation/stage/getters-patched.code.ips` | `474718ecbb74db66b5f682fef626d29cea1237eb5604a93e38d92d40f406e520` |
| Stage manifest | `build/agent-work/batch-h18-001/h18-getters-stage/run-001/checks/staged-validation/stage/manifest.json` | `3098043b90da2aab8b911cf0e5596c03a2b181fffff5b11e9d186218af895fb3` |

Text maps `0x00100000` to file offset 0. The two IPS records patch file offsets `0x001345f0` and `0x001345fc`, each with 8 bytes. Entries remain even ARM addresses and each candidate returns using `BX LR`; all 16 direct ARM `BL` sites per getter target the exact entry, with no direct branch into either 12-byte function interior. The original ledger rows remain `non_matching` and unchanged by this task.

## Offline evidence

The runner executes the actual patched image at the original entry addresses, not an entry trampoline or an injected replacement. It compares full `r0-r12`, SP/LR/PC/NZCV, mapped data and stack, writes, and continuation against the pinned original. It deliberately permits only the already declared read-width difference: original `LDRH` observes two bytes; candidate `LDRB` observes one. Evidence is therefore for aligned, side-effect-free ordinary RAM with both original bytes accessible.

| Seed | Cases per getter | Four paired caller windows | Controls |
|---|---:|---|---|
| 7 | 80, passed | all passed | wrong offset and omitted mask detected |
| 20261024 | 80, passed | all passed | wrong offset and omitted mask detected |

Each caller window is one representative paired sequence in `0x0038c43c`, `0x0038cdf4`, `0x0038d7b0`, or `0x0038de60`. Both getters execute from the staged image, and the caller consumes the expected values in `r2/r3`. Each stops before the following external helper; full callers and runtime pointers were not exercised.

Reports:

- `build/agent-work/batch-h18-001/h18-getters-stage/run-001/checks/staged-validation/seed-7/report.json` — SHA-256 `409406c385178aea44a3454d54fea462995805e109a9a55093f33c855010f735`.
- `build/agent-work/batch-h18-001/h18-getters-stage/run-001/checks/staged-validation/seed-20261024/report.json` — SHA-256 `e6c7d359085fa3c08aef89bf748fea1b280a85ebec299e4f5e72c826af24b88a`.

## Limits and next action

The staged image proves offline patch placement, ARM entry/return mode, round trip, and the bounded Unicorn differential. It does not demonstrate Azahar patch-loader acceptance, live heap pointer values, a deterministic in-game trigger, full script VM behavior, or runtime equivalence. No canonical full build was run. The read-width limitation remains explicit; no MMIO, fault-boundary, unaligned, concurrency or invalid-pointer behavior is claimed.

Next, use the staged IPS with the previously identified isolated original/patched profile and loopback GDB route, after a getter-specific driver is available. First establish an actual deterministic scenario that hits these functions; a no-hit result is inconclusive.
