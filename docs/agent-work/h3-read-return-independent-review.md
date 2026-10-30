# Independent review: H3 read-return probe

## Review result

The paired evidence supports a bounded runtime observation: after a successful file open, truncating the disposable staged save to zero bytes changes the original `AsdSave_Read` return at `0x00210478` from `1` in the intact control to `0` in both original and patched error runs. In the error pair, the sampled result byte and downstream observations are consistent with the original state-7 failure path. This is not a reconstruction of the reader, parser, or filesystem, and it establishes no visible UI error.

## Frozen inputs and provenance

I recomputed every SHA-256 in the prepared `task.json`; all 16 declared inputs matched. This includes the report JSON, raw original/patched run JSON, runner copy, the two original source files, milestone/probe records, and workflow/config files. The packet's complete expected hashes are preserved in `build/agent-work/H3-semantic/h3-read-return-review/run-001/task.json`.

I inspected the frozen runner and its call path. It derives `save_path` from each disposable `profile_root/<kind>/app/user` tree, takes a backup of that staged file, truncates that path only after the `0x002D8E60` open-result breakpoint reports `r0=1`, and restores from the backup before the status-setter breakpoint. Its `finally` block also restores the staged file if execution exits earlier. The user fixture is the seed used to prepare the staged profiles, but it is not the runner's mutation target.

The two saved backup files are each 151,088 bytes with SHA-256 `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`. Each error-run record reports restoration before the status setter; the staged save's before and after snapshots also have that same size and hash. I independently hashed the current source fixture at `E:\emulador3ds\sdds4game1.sav`; it has the same size and hash. This corroborates byte identity by SHA-256, while the raw run artifacts do not contain a bytewise comparison log. The supplied evidence does not show the source fixture as a path opened for write.

## Paired observations

| Observation | Intact control (original and patched) | Truncated-after-open pair (original and patched) |
| --- | --- | --- |
| Open result at `0x002D8E60` | `r0=1` | `r0=1` |
| Requested size at `0x00210474` | `r3=0x24E30` | `r3=0x24E30` |
| `AsdSave_Read` return at `0x00210478` | `r0=1` | `r0=0` |
| Sampled `global_43e2f0` result bytes | `0100000100000000` | `0100000000000000` |
| Field manager / load-complete acknowledgement | reached / acknowledged | not reached / not acknowledged |

The intact control's original and patched progress samples both show `global_43e2f0=0100000100000000`; the error pair's corresponding samples both show `0100000000000000`. The original `SaveLoadProcess_Step` body at `0x002EF9AC` is retained as ARM words in `src/ui/save_load.cpp`. Its state-6 and state-7 terminal paths store the result byte at `global_43e2f0+3` as `1` and `0`, respectively. Thus the progress sample's byte `+3` decodes as the success/state-6 result for the intact run and failure/state-7 result for the truncated read. The setter-entry event itself captures the pre-write bytes; the result classification relies on the later progress sample and the original terminal writes. The setter's `r0=1` is a separate argument and is not the reader result.

Both error runs record the file as restored before entering the status setter, no field-manager entry, and no success acknowledgement. The error-run reports show no screen capture (`screen_result` and `post_read_screen` are null); they make no visible-error claim. The intact control reaches the field manager in both profiles and records the controlled load-complete acknowledgement.

## Raw paired differences and limits

The two error `post_confirm_events` arrays each contain 14 entries. Their only raw difference is the `r3` pointer at `save_load_process_start`: original `0x7c51`, patched `0x8265580`. The open result, requested read size, read return, sampled progress, status-setter inputs, and other event fields match. `post_confirm_progress` is equal in the paired report. This pointer difference remains unexplained and is not assigned semantic significance. The intact-control event arrays likewise differ in process-local pointers (including the save buffer), so full raw trace identity is not claimed.

The experiment shows that the original reader returns failure for this staged zero-byte save after a successful open in this title-load route. It does not prove general behavior for other devices, files, sizes, or callers. The original reader and surrounding I/O/parser remain dependencies. It does not establish a user-visible error message, whole-game equivalence, or any newly reconstructed C++ behavior.

## Commands and evidence level

- Read-only provenance and source inspection: PowerShell `Get-FileHash -Algorithm SHA256` over all declared packet inputs; `rg`/`Get-Content` for the runner and original source. Exit 0.
- Read-only JSON extraction: Python standard-library parsing of both reports and paired run files for event, progress, result, and snapshot comparisons. Exit 0.
- Read-only integrity check: PowerShell `Get-Item` and `Get-FileHash -Algorithm SHA256` on both staged-save backups and the source fixture. Exit 0; each was 151,088 bytes with the hash above.
- No emulator, build, differential runner, or code mutation was run as part of this review.

Evidence levels: runtime trace review **supported within the stated fixture/route and limits**; C++ reconstruction **not evaluated by this probe**; visible UI error **not observed**; whole-game equivalence **not established**.

Next action: the coordinator may accept this bounded read-return review after checking the report and its recorded source hashes; keep the visible UI error contract explicitly unresolved unless a separate captured observation establishes it.
