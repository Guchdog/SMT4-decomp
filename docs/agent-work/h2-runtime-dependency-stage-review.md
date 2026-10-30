# H2 runtime dependency staging — independent review

## Decision

The missing-runtime-package hypothesis for the prior launch failure is strongly supported. The failed run staged only the pinned private `azahar.exe`; that executable has direct imports of `Qt6Core.dll`, `Qt6Widgets.dll`, `Qt6Gui.dll`, `Qt6Multimedia.dll`, and `Qt6Concurrent.dll`, none of which were in that staged app directory. Windows returned `0xC0000135` before the GDB listener appeared. This status and the absent direct imports fit a missing-DLL startup failure, but the report does not identify the specific DLL or capture a loader diagnostic.

A fresh, separately packetized, original-only retry is justified after the updated runner, package pin, and disposable fixture are all frozen as inputs and the Qt/toolchain limitation below is retained. This review did not launch Azahar and establishes neither startup success nor guest behavior.

## What run-001 actually proves

The frozen run-001 runtime record (`261398eeb37cadc4a28d04ee4d32f74d763a9c63982dff2b8d1e692021d5f485`) says `launch_count=1`, `status=partial_failed`, and `TraceError: Azahar exited before listener: 3221225781`. The status is `0xC0000135`. It records staged executable hash `8e18aac0...`, a report trace of `{}`, and no listener-verification object or RSP-observed process ID. Its profile cleanup record is true. The CCI and supplied source-save before/after hashes agree with their expected values, and the report says the source save was not staged or loaded. The process exit was not a graceful-close observation. No dispatcher, handler, readiness, or persistence result was observed.

The run-001 task packet (`72d7fe1e...`) contains no `tools/h2_state2_dispatch_trace.py`, runtime package-pin, or disposable-fixture hash entry. The runtime JSON likewise has no runner hash, package-pin hash, or `runtime_dependency_assets` inventory. The contemporaneous review report records the then-intended runner hash `284c21bb...`, but the run packet did not freeze that source file and the runtime JSON does not bind itself to it. This prevents independent cryptographic attribution of the exact runner bytes that launched. The packet/run evidence does, however, show that the private executable was staged without a runtime-asset manifest. Current runner bytes are `fc642f6c...`; they must not be retroactively assigned to run-001.

## Runtime package pin and import closure

I recomputed all hashes declared in this review packet: **zero input mismatches**. The package pin is SHA-256 `bda8e1a43ac9e040e4a8165f1a9eec5a3656ff94d59d85cb50577959815428f9`. Its declared source executable is `E:\emulador3ds\azahar.exe`, SHA-256 `c248414eb5328cb8bb720775ace6959898e2f50a0a10221c3a1e7a14190183eb`. Against that distribution, its selected runtime set is exact: 59 of 59 files present, no missing or extra selected paths, all recorded byte counts and SHA-256 values match, and total bytes equal the pin's 112,727,315. The file selection covers top-level DLLs, the complete `plugins/` tree, and `scripting/AzaharRPC.py`; no `qt.conf` exists in that source package, and none is pinned.

I parsed the private PE import tables without loading the executable. Its direct non-system dependencies are the five Qt DLLs above. Their recursive package dependency closure resolves using the pinned distribution: Qt, ICU 74, zlib, PCRE2, zstd, Brotli, FreeType, HarfBuzz, GLib, libc++, and libunwind assets are present; the remaining imports in that executable closure resolve to Windows system/API-set DLLs. The selected `plugins/platforms/qwindows.dll` SHA-256 is `249546edd0eb8152e46f8d7ad8046578cfaf347605074fcaa30fe4e6ca580e21`; its imports resolve to the package's Qt Core/Gui and shared C++ runtime plus Windows system DLLs.

The entire pinned plugins tree is broader than the private executable's startup closure. Some included optional plugins have imports not supplied by the 59-file set: Qt Quick/QuickWidgets, Qt QML, Qt SVG, `libjpeg-10.dll`, FFmpeg libraries (`avcodec-61`, `avformat-61`, `avutil-59`, `swresample-5`, `swscale-8`), and SQL dependencies (`qt6sql`, SQLite, MariaDB). This does not show that Azahar loads those plugins during startup; it means the package is not a complete closure for every plugin it stages. Keep this distinction in any future runtime claim, and either restrict staging to needed plugins with their closure or pin their remaining dependencies if the scenario requires them.

## Qt/toolchain compatibility and updated staging review

The private build cache is pinned at SHA-256 `2b1585a3...`. It identifies the C++ compiler as `C:/msys64/clang64/bin/c++.exe` and its Qt package configuration as 6.11.2. The local Qt config version file also says 6.11.2; the candidate distribution's Qt DLLs and `qwindows.dll` report file version 6.11.1.0. Their SHA-256 values differ from the corresponding 6.11.2 DLLs in the private build environment. Both sets share Qt 6.11 major/minor, but this metadata does not prove their exact build/compiler ABI compatibility. The candidate runtime imports `libc++.dll` and `libunwind.dll`, matching dependency names in the private executable's build family, but those DLL hashes also differ from the local build environment. Treat compatibility as plausible and supported by the pin's referenced prior successful run for this exact private executable (`e370da857f1738409decc468bee81859eb84cfc9278bacf3d0c9d0b460d045b8`), not as byte-identical or independently runtime-reverified here. That prior record has `passed: true` and the same private executable hash, but does not inventory the runtime files it loaded.

The current unpacketized runner (`fc642f6cef0613138785fcde97f2b2c36eefccf091df4ca3689fc8e3545185cb`) adds meaningful provenance checks: it pins the private executable, checks the package-pin document against a task input hash, checks the distribution executable hash and source relationship, requires exact selected runtime-path set equality, verifies every asset hash before copy and after staging, and places the assets adjacent to the private executable under the disposable app root. It stages `plugins/` and the pinned scripting file at their relative paths; it copies `qt.conf` only when present and in the pinned set. It also records asset hashes. Profile configuration is copied into a task-specific user tree, validated within the seed root, and cleanup removes only that staged `user` tree after preserving its log. The runner statically references a separate disposable fixture and stages it under the staged profile; this review did not access that fixture or any profile/save contents.

There are two provenance corrections required before retry. First, do not reuse run-001: its task input map lacks the runtime package pin, current runner, and fixture entries, so the updated runner's pin lookups cannot be validated from that packet (and a direct package-pin key lookup would fail). Prepare a fresh packet that pins the exact current runner, package-pin JSON, source executable, private executable, CCI/code and fixture inputs. Second, preserve the Qt 6.11.2 versus 6.11.1 and differing runtime-DLL hash caveat in the prelaunch review. The manifest's full plugin tree contains optional unresolved imports described above.

## Scope and limits

This was a read-only review. I did not build, launch Azahar, connect a debugger, create/stage a profile, or access a save. The PE inspection covers static imports of the private executable and the pinned Qt platform plugin; it does not inspect delay-load or runtime `LoadLibrary` behavior, Qt plugin selection, app logs after a new run, or Windows loader resolution on a new launch. File-version metadata and hashes establish package identity differences, not ABI acceptance. No semantic, caller, ARM-differential, or runtime evidence was generated by this review.

## Inspected identities

- Review task packet: `build/agent-work/H2-semantic/h2-runtime-dependency-stage-review/run-001/task.json`, SHA-256 `f423bfb3021171bad9e323fd78f921d128e186d30d20440f175ba5dd16b54eae`.
- Current runner: `tools/h2_state2_dispatch_trace.py`, SHA-256 `fc642f6cef0613138785fcde97f2b2c36eefccf091df4ca3689fc8e3545185cb`.
- Private executable: SHA-256 `8e18aac0df0be63b3351fb4b39b6d5f75fb23992ce3ad9d8ccd8cb671dc6f60a`.
- Delivery manifest: SHA-256 `0d93e2cda5724e386c927230fbceaa198daa43dc3ee4917d01ea22fa5bc6a4e8`.
- CMake cache: SHA-256 `2b1585a3bb36ebbc10a15c15be21e69c2612f28dd3b0502220578336ad0b8f66`.
- Failed run packet / runtime JSON: `72d7fe1e1be10647077bba90ddff35e8eb5310124891951faded7d891a2cf4a1` / `261398eeb37cadc4a28d04ee4d32f74d763a9c63982dff2b8d1e692021d5f485`.
- Prior runtime summary report named by the pin: SHA-256 `e370da857f1738409decc468bee81859eb84cfc9278bacf3d0c9d0b460d045b8`.
- No source, package, profile, save, or runtime file was modified.

## Recommendation

Coordinator may accept this bounded dependency/provenance review and prepare a distinct retry packet. Before any future launch, freeze current runner and package-pin inputs, verify the exact staged dependency set and the selected plugin closure, retain the Qt/toolchain caveat, then perform the offline gates and a single original-only startup attempt. A fresh start/listener result is still required before any RSP connection; no launch is authorized by this review.
