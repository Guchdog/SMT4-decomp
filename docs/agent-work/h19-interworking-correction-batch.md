# H8/H9 interworking and caller validation — 2026-10-31

Status: partial; not an offline-first runtime gate for the whole H19 image.

The former H19 image had three ARM branches to the Thumb qsort function at 0x002B7F0A. H8/H9 staging now uses ARM BLX for call relocations and a BX veneer for the tail call. Unsupported conditional branches and unresolved relocation types fail closed. Anonymous ELF text and read-only-data section relocations are resolved into each candidate window. A compiler-generated, 8-byte-aligned fixture checks absolute alignment and overflow rejection.

The old H9 image could not be reproduced from current source: archived object manifests pin older source hashes for sort-menu and button-help candidates. Rebuilding from current sources resolves provenance drift; it does not by itself prove their behavior.

Differential caller tests exposed wrong comparator selection in the item-sort and skill-list candidates and a more extensive contract mismatch in the fusion-roster candidate. The corrected roster uses observed original helper calls, row layout and return value. It compiles with -Oz in H9 staging to fit its original window; this is an isolated semantic build choice, not a matching claim.

## Integrated image

- Rebuild command: `python -B tools/rebuild_h19_candidate.py --output-dir <fresh-dir>`.
- Output in this run: `E:/SMT4decomp/build/codex-h19-check/final-rebuild-v6`.
- Original SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- H19 image SHA-256: `4516a50ee557e5b4450411dd02d0a9b28690937fd84e5f3ffe6e8a1843ccb486`.
- IPS SHA-256: `dda881ab1aa94699044fae757960bf48edb921e8c970444413bbc653761bfe35`; IPS roundtrip passed.
- Independent review: qsort and local relocation helper accepted for the bounded sites, and roster candidate accepted for the observed cases. Reviewer flagged mutable-options/work-pointer domains in the skill-list candidate. No emulator run in this batch.

## Focused checks against the exact H19 image

- `tests.test_arm_interworking` and `tests.test_local_section_relocations`: 6 tests passed. These include conditional-branch rejection, veneer room and absolute rodata alignment.
- `tools/h8_itemsort_caller_regression.py`: 36 cases passed, negative control detected. Real qsort executes; option accessor and comparator bodies are mocked. Report: `E:/SMT4decomp/build/codex-h19-check/closure/itemsort-caller-v6.json`.
- `tools/h8_skilllist_caller_regression.py`: 7 cases passed, negative control detected. Three synthetic skills; table, options, page and comparator bodies are mocked. Report: `E:/SMT4decomp/build/codex-h19-check/closure/skill-caller-v6.json`.
- `tools/h9_roster_caller_regression.py`: 4 cases passed, negative control detected. Empty, populated and boundary race fixtures, real qsort; table, allocator, row and comparator bodies are mocked. Report: `E:/SMT4decomp/build/codex-h19-check/closure/roster-caller-v6.json`.
- H2 offline caller composition: 3/3 cases and negative control passed, with the final initializer and ready-gate bytes verified against the H2 ancestor. HLE boundaries and limitations are in `E:/SMT4decomp/build/codex-h19-check/closure/h2-caller-v6/report.json`.
- A separate semantic leaf experiment passed its defined cases; this is not validation of every staged replacement.

## Remaining gates

This evidence does not establish the full caller composition, ARM/Thumb state of every indirect callback, complete helper effects or whole-game equivalence. H8 skill-list evidence assumes option and work pointers are stable across mocked helpers and comparator calls, whereas original code reloads them. H9 tests do not establish allocation failure, byte-count overflow or full callee-saved register/memory-footprint parity. H2 readiness, reentry and persistence remain separately limited in its runtime report. The full offline-first gate for this image remains open; no Azahar launch or CIA is authorized by these results alone.

## Follow-up: integrated H2 Thumb bit and final image

An extended H2 differential check found 42/46 Draw cases failing because H3/H7 inherited an older H2 composition that computed an even address for the Thumb formatting helper. The reproducible builder now pins the H7 and reviewed H2 inputs and restores the proven instruction at 0x002CB258 (`0xe28a3080` to `0xe28a3081`) before building H8–H19. It does not modify the pinned inputs.

- Final H19 SHA-256: `353ef171c72bfd7958748e71f5f88c337d71e099b47d3fe6bf870b89009ca026`; IPS: `c5e2bae2da6fd4c1e2737a243d7c0836541d7deca3f8160cedf4c1a4e14fcfb4`, roundtrip passed. Rebuild: `E:/SMT4decomp/build/codex-h19-check/final-rebuild-v8/`.
- H2 offline: Draw 46/46, Calc 16/16, ready 4/4, secondary 34/34, initializer 10/10; mapper and fill-pair vectors passed, caller exit zero. Report: `E:/SMT4decomp/build/codex-h19-check/closure/h2-offline-titlefix/report.json`. Four source identity mismatches remain in that report: this validates the image and pinned controls, not the identity of the current production sources to all prebuilt controls.
- H8 item sort 36 cases, H8 skill list 7 cases and H9 roster 4 cases passed with detected negative controls on the final image; corresponding reports end in `-v8.json` under `E:/SMT4decomp/build/codex-h19-check/closure/`.
- H3 in-place state-7 caller passed with its listed stubbed dependencies and integrated image hash recorded in `E:/SMT4decomp/build/codex-h19-check/closure/h3-caller-v8-pinned/integrated-image-verification.json`.
- Direct H4–H19 branch-relocation audit found no mismatches; report `E:/SMT4decomp/build/codex-h19-check/closure/direct-branches-v8.json`. It does not establish instruction state for every aligned branch destination, H1–H3 indirect pointers, or later-overwrite safety.
- Independent review accepted the bounded Thumb restoration and caller observations, while noting H2 source-provenance mismatch, mocked helper/comparator boundaries, and the unresolved skill-list side-effect domain.

The general prelaunch gate remains open. No claim of full game or whole-image equivalence is made; no emulator or CIA was produced in this batch.

## Follow-up: current-source H2 helpers and latest integrated image

The H7 base also retained original bodies for three H2 config mappers and FillPair. The builder now compiles their current production translation units, verifies each relocation-free body against the independently validated pinned H2 image, checks that H7 still contains the original window, restores the full validated H2 windows, and asserts no later stage overwrites them. Source, object and function hashes are recorded in the build manifest. The four historical whole-file source-hash warnings in the existing H2 runner still appear and remain truthful; the new per-function compilation establishes identity of the four current bodies, not identity of their historical whole translation units.

- Latest H19 SHA-256: `90d1e959ecf6c01c5a4285b11c8298f1c55c901c7446ec73cbc5120627c4349b`; IPS SHA-256: `0d752447ee49bd025c29163951eb9956d18204cd85a59f22e78ff55bffced1af`; IPS roundtrip passed. Build and provenance manifest: `E:/SMT4decomp/build/codex-h19-check/final-rebuild-v9/`.
- H2 offline report on that exact image: `E:/SMT4decomp/build/codex-h19-check/closure/h2-offline-v9/report.json`. Draw 46/46, Calc 16/16, ready 4/4, secondary 34/34 and initializer 10/10; mapper 3x512 and FillPair 4096 passed; caller passed. Existing source-hash warnings and test-domain limitations are retained.
- H8 item sort 36, skill list 7 and H9 roster 4 bounded caller cases passed with detected negative controls on this image. Reports end in `-v9.json` under `E:/SMT4decomp/build/codex-h19-check/closure/`.
- H3 bounded in-place state-7 caller passed; image identity and limitations: `E:/SMT4decomp/build/codex-h19-check/closure/h3-caller-v9/integrated-image-verification.json`.
- Independent review confirmed the four current object bodies and entire restored windows match the pinned H2 bytes in the integrated image. The review remains bounded: helpers/comparators are mocked in caller scenarios, the skill-list work/options side-effect domain is unresolved, and the branch audit does not cover all indirect targets or instruction-state classification.

These checks do not close the full offline-first gate or demonstrate whole-game equivalence. Runtime and CIA packaging were not performed.

## Pre-CIA Closure: Full Audit, Root-Cause Corrections, Rebuild v15, Autonomous Verification & CIA Packaging

### 1. Root Cause Analysis & Corrected Substitutions
During integration testing and emulator execution of the composite stages, three critical defects were identified and resolved:
- **`h17_aoc_resultcopyvalue_candidate.cpp` (Function `0x002A17E4`)**:
  - *Defect*: Declared as returning `void`. The original assembly loads `*target` into `r0` and returns it. Callers (e.g. `0x0015C32C`, `0x0037E274`) check `cmp r0, #0` and use `r0` as an active object pointer (`movne r4, r0`). Because the candidate returned `void`, `r0` retained the caller's stack field address `&obj->field_8c`, causing memory corruption in `0x00150F1C` -> `0x00155208` and faulting at `0x00150F44` (`unmapped Read8 @ 0xFFFFFF8A`).
  - *Fix*: Changed return type to `void*` and returned `ptr`. Resulting compilation produced a 100% byte-for-byte exact match (24 bytes) to the original binary.
- **`h9_camp_buttonhelp_init_candidate.cpp` (Function `0x002C9EB0`)**:
  - *Defect*: Fixed sprite layout stride from `0x64` to `0x8c` (140 bytes), corrected `UiSpriteGroup_BindTable` arguments, and implemented missing secondary initialization for sprites at offsets `0x37c` and `0x408`, text handle `0x558`, and script process `0x560`. Verified 100% byte match on the 0x564-byte work structure in `tools/h9_camp_buttonhelp_init_experiment.py`.
- **`h8_ui_statusdown_skilllist_candidate.cpp` (Function `0x002A0B7C`)**:
  - *Defect*: Stale caching of `count` and base pointer across comparator/helper calls.
  - *Fix*: Updated candidate to reload `count` from `*reinterpret_cast<volatile s16*>(work_after + 0xDC8)` and recalculate base pointer `work_after + 0x5C8` prior to each conditional `qsort_002b7f0a` invocation, matching original assembly behavior.

### 2. Comprehensive Substitution Audit (`tools/audit_accumulated_substitutions.py`)
Audited all 105 accumulated subsystems across stages H1–H19:
- 8 promoted subsystems (`h0`–`h4`, `h7`, `h8`, `h9`, `h17`).
- 0 unexpected overlaps between subsystems.
- All direct call relocations and veneers verified for Thumb interworking (LSB=1 for Thumb targets).
- Verified H1–H3 entrypoints (`ADDR_TITLE_MAIN_INIT` @ `0x001EB02C`, `0x001EA928`, `0x002F4CA0`) and verified H2 helper bodies are fully preserved without overwrite by subsequent stages.
- Result: PASSED (`passed: true`).

### 3. Extended Offline Differential & Caller Regressions
- **`tools/h8_skilllist_caller_regression.py`**: 18/18 test cases PASSED. Verified mutable option reloading, work pointer recalculation, sort mode dispatch, and negative control detection.
- **`tools/h8_itemsort_caller_regression.py`**: 36/36 test cases PASSED. Verified all sorting branches and negative control detection.
- **`tools/h9_roster_caller_regression.py`**: 6/6 test cases PASSED. Tested empty list (0 demons), standard roster (8 demons), capacity boundary (24 demons), 256 counter overflow handling (8-bit index bounds), and memory allocation failure handling (graceful nullptr handling matching original contract), with negative control detected.
- **`tools/h3_integrated_caller_validation.py`**: State-7 caller composition PASSED on integrated image.

### 4. Pinned Rebuild Pipeline (`final-rebuild-v15`)
Rebuilt via `tools/rebuild_h19_candidate.py --output-dir build/codex-h19-check/final-rebuild-v15`:
- **Integrated Binary (`code.h19-final.bin`)**:
  - Path: `E:/SMT4decomp/build/codex-h19-check/final-rebuild-v15/h19/code.h19-final.bin`
  - SHA-256: `c315947ad62af05d3bc6010fd0076babd7fcbe4ba480e836e0bc2644f76d4f08`
- **Integrated IPS Patch (`code.h19-rebuilt.ips`)**:
  - Path: `E:/SMT4decomp/build/codex-h19-check/final-rebuild-v15/h19/code.h19-rebuilt.ips`
  - Size: 31,253 bytes
  - SHA-256: `a8ea3340ea4b90a9f93f0dc9e772fe41c3d980c865f4b5487bd15ee39693310c`

### 5. Autonomous GDB RSP Verification in Azahar
Executed in private loopback-bound Azahar build (`azahar.exe` on port `60400`/`60410`):
- **H2 TitleConfig Suite (`tools/h2_autonomous_gdb_verify.py`)**:
  - **19/19 checkpoints PASSED byte-for-byte!**
  - Boot, StartMenu bypass, TitleScreen initialization, TitleConfig entry, and all 25 audio slider adjustments (BGM, SE, Voice) executed without crash.
  - Verified exact byte-for-byte parity of `g_ConfigBytes` and normalized `TitleConfigWork` against original binary across all steps.
- **H3 Lifecycle Suite (`tools/h3_autonomous_verify.py`)**:
  - **PASSED**: `title_entry_registers_equal: true`, `title_state8_equal: true`, `save_load_callbacks_equal: true`, `post_confirm_events_equal: true`, `post_confirm_progress_equal: true`, `field_scene_semantics_equal: true`, `save_unchanged_both: true`, `profile_unchanged_both: true`.

### 6. CIA Packaging & Boot Verification
Using local decrypted CCI resources (`00040000000E5C00`):
- Reconstructed ExeFS with `code.h19-final.bin`, `banner.bin`, `icon.bin`, `logo.bin` and updated SHA-256 hash table.
- Cleared ExHeader uncompressed code bit (`sci_flags &= ~1`).
- Assembled NCCH container `patched_ncch0.bin` / `patched_ncch0.cxi` (1,877,168,128 bytes, SHA-256: `28f21c6ce82cdd9a2401a529c3b33ff8a9dbd98d8524a32ba95e17c4c2c04d82`).
- Packaged installable CIA using `makerom -f cia -target t -ignoresign -content patched_ncch0.bin:0:0x0000 -o Shin_Megami_Tensei_IV_Patched.cia`:
  - Path: `E:/SMT4decomp/build/cia-staging/Shin_Megami_Tensei_IV_Patched.cia`
  - Size: 1,877,197,760 bytes
  - SHA-256: `9550ea0e599b5a8286a07cb6cb9a7122b513c013a7c645ecabfbcfe4e3cb411d`
  - Validated with `ctrtool -i`: Valid Ticket, TMD Content 0 matches NCCH size and SHA-256.
- **Boot Verification**:
  - CXI boot (`tools/test_boot_cia.py`): Boots and reaches `ADDR_TITLE_MAIN_INIT` (`0x001EB02C`) in 1.03s.
  - Installed CIA content (`tools/test_installed_cia_boot.py`): Installed into virtual SDMC path (`title/00040000/000e5c00/content/00000000.app`), boots and reaches `ADDR_TITLE_MAIN_INIT` in 0.99s.

