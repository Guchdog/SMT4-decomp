# H3 read-return probe — staged-file truncation after open

## Purpose and limits

This paired run distinguishes a real failure at the original file-read call from a failed file open. It is a runtime observation for the supplied save and the title-load route only. The user source file was never modified. The independent review for this packet is pending; do not treat the packet alone as milestone approval.

## Frozen setup and isolation

- Source input: `E:\emulador3ds\sdds4game1.sav`, 151,088 bytes, SHA-256 `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`.
- The original and patched profile trees were copied into the disposable directory `E:\SMT4decomp\build\agent-work\H3-semantic\h3-read-return-probe-20261028\profiles\`. Each staged save began with the same 151,088-byte hash as the source.
- Both profile executables were the private Azahar build, SHA-256 `8e18aac0df0be63b3351fb4b39b6d5f75fb23992ce3ad9d8ccd8cb671dc6f60a`; its GDB stub was owned by the launched child on loopback ports 54342 and 54343.
- Before launch, the fresh candidate differential passed, the final-image patcher passed the 120-byte-window/relocation/IPS round-trip checks, and the caller-composition runner passed. The pinned state-7 caller target low bit is zero; both candidate `BL` relocations remain ARM-aligned. Reports are preserved beside the runtime evidence.
- The autonomous runner copy adds breakpoints at `0x00210474` (read call) and `0x00210478` (return). In the error pair it truncates only the staged profile save to zero bytes after the original open call returns success at `0x002D8E60`, then restores its backup before the status setter and verifies the source hash.

## Paired result

| Observation | Original | Patched |
| --- | --- | --- |
| `0x002D8E60` open result `r0` | `1` | `1` |
| `0x00210474` requested read size (`r3`) | `0x24E30` | `0x24E30` |
| `0x00210478` `AsdSave_Read` result (`r0`) after truncation | `0` | `0` |
| `global_43e2f0` at the first post-read progress callback | `0100000000000000` | `0100000000000000` |
| Field manager reached / success acknowledgement | no / no | no / no |
| Staged save restored before status setter; unchanged after run | yes | yes |

The intact-save control returned `r0=1` at `0x00210478`, reached the field manager in both profiles, and produced `global_43e2f0=0100000100000000`. Comparing the two terminal writes in original `SaveLoadProcess_Step` (`0x002EF9AC`), byte `+3=0` identifies its state-7 failure result, while byte `+3=1` identifies state 6. The status setter's own `r0=1` is a separate input and is not the read result.

The only difference in the paired `post_confirm_events` arrays is `r3` at `save_load_process_start` (`0x7c51` original, `0x8265580` patched); the read call arguments/results and sampled progress bytes match. This is a raw pointer difference; no contract significance is inferred.

## Remaining limits

The runtime pair establishes the original reader's failure result and downstream internal state-7 marker after the file was opened but before bytes could be read. No screen capture was taken in this probe, so it does not establish a visible error message or the complete user-facing error contract. The parser, reader, and filesystem implementation remain original dependencies; this run validates their observed response but does not reconstruct them. It is not whole-game equivalence.

The first attempted runtime run used only 20 settling callbacks and correctly refused to confirm while the UI remained in state 1. The successful pair used 80 settling callbacks. No save file in the source path or original C checkout profile was modified.

## Evidence files

All machine reports, raw paired JSON, the runner copy, and offline gate reports are under ignored `build/agent-work/H3-semantic/h3-read-return-probe/evidence-run-001/`. The detailed runtime outputs were first written under the E: disposable profile root named above. The intact controls and truncated error pair are separate directories.
