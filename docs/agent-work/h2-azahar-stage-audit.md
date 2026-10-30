# H2 Azahar staged-startup audit

Status: read-only startup-path diagnosis. No emulator launch, GDB/RSP exchange, game/profile write, or keyboard/mouse control was performed by this audit.

## Pinned executable and matching source

The installed and run-005 staged executable both hash to `c248414eb5328cb8bb720775ace6959898e2f50a0a10221c3a1e7a14190183eb`. Its embedded build strings identify Azahar `2126.2`, MXE, build commit `219d743a1e698101fe1ab8bef43e6563126c3c27`, and timestamp `2026-10-08T22:19:01Z`.

The official source at that exact commit parses `-g`/`--gdbport` followed by a decimal/base-0 port and accepts a final positional game path in [`citra_qt.cpp`](https://github.com/azahar-emu/azahar/blob/219d743a1e698101fe1ab8bef43e6563126c3c27/src/citra_qt/citra_qt.cpp). Its `-v`/`--version` implementation calls `QMessageBox::information` on Windows before exiting, so it is not a silent headless version check. The same commit's [`core.cpp`](https://github.com/azahar-emu/azahar/blob/219d743a1e698101fe1ab8bef43e6563126c3c27/src/core/core.cpp) applies a GDB port override and turns the server on when an override is supplied. Thus the run-005 command spelling is supported by the source; this does not prove the runtime reached the code that enables the stub.

## Runtime staging facts

Run-005 copied `azahar.exe`, every top-level `.dll`, and the complete `plugins/` tree into `app/`. The installed package at `E:\emulador3ds` also contains `scripting/AzaharRPC.py`, which was omitted. The official installer at the same source commit bundles the binary output tree verbatim, so `scripting/` is part of that package layout. Its relevance to ordinary startup is unproven; treat this as a packaging mismatch and testable hypothesis, not an established root cause. Do not copy the installed directory wholesale: it also contains unrelated tools, the original CIA/CCI, a save, and logs.

The run-005 record says Azahar exited with code 1 before opening port 58573; stdout/stderr were empty and no RSP connection occurred. A later, separate parent diagnostic used `-v` on the staged executable and timed out; matching source explains that Windows `-v` opens a modal information dialog. That diagnostic created `app/user/config/qt-config.ini` and empty user log files. The generated config records default `use_gdbstub=false`, port `24689`, and stage-local NAND/SDMC paths. Because this config was generated during the separate `-v` invocation, it does not show what configuration existed during run-005. It also does not prove whether run-005's `-g 58573` override reached core startup.

The local-profile assumption is supported: matching Windows `file_util.cpp` chooses `<executable-directory>\\user\\` when that directory exists; otherwise it falls back to roaming AppData. Run-005 created `app/user` before launch, and the later generated config resides there with stage-local paths. The effective runtime path should still be verified from the new process's own log in any future run. No shared profile needs to be read or used.

## Diagnosis and next bounded run

The cause of the exit remains unresolved. Evidence rules out a simple `-g` spelling mismatch and supports the intended adjacent local-profile selection. The most actionable testable hypothesis is that the curated stage omitted a bundled runtime component: add only the pinned build's required runtime files, including a verified `scripting/` directory (and `qt.conf` only if present in the exact package), while continuing to exclude unrelated tools, ROMs, saves, and logs. The exact-package identity of the installed `scripting/AzaharRPC.py` has not been established, so verify it against the pinned distribution before reuse or acquire the corresponding clean 2126.2 package. This hypothesis is not proven to explain exit code 1.

If authorized by a fresh packet, make one isolated diagnostic run in a new E: stage using the exact 2126.2 runtime package and the existing permitted two-file profile seed. Use one verified free loopback port and only `-g PORT <pinned CCI>`; do not add `-v`, `-h`, long-flag retries, or UI interaction. Capture process exit code, listener owner, Windows application error events, `user/log/azahar_log.txt`, generated config, and hashes for every staged executable/runtime file and the CCI. Stop at the first failure and do not connect RSP until the listener PID and effective local user path are verified. If the complete package still exits, inspect captured error/log evidence before changing the seed or adding files.

## Scope limits

This audit establishes build identity, source-level option behavior, a package-layout difference, and a conditional local-profile path. It does not prove the missing scripting folder causes the crash, prove GDB opens under `-g`, verify `M`/`P`, or establish any H2 behavior. No game inputs or profile files were changed by this audit.
