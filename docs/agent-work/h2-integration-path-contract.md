# H2 integration path: candidate placement and evidence boundary

Status: read-only integration-path research. No compiler, patch construction, source/ledger edit, Azahar launch, GDB session, or input control was performed.

## Findings

### Production and experimental build/patch routes

- `tools/build_check.py` compiles individual translation units for ARMv6K and writes object/dependency metadata. It does not itself place a C++ symbol at a game guest address or produce an installable game patch. `tools/verify_decomp.py` uses compiled size and exact-byte checks for ledger entries; its `compiled` classification for `non_matching` is a size threshold, not behavioral acceptance.
- `tools/semantic_experiment.py` has an experimental `patch_image` route. It places relocation-free leaf blobs in zero-filled `.text` page padding, writes a branch at each original entry, and creates an IPS. Its present `CANDIDATES` and `validate_leaf` restrict it to that leaf set; it does not currently accept the H2 non-leaf callback candidate or its relocation records. The common utility is not a general production linker.
- `tools/h1_menu_slice_integration_experiment.py` compiles actual production TUs, extracts individual symbols, manually resolves a limited known relocation (branch from the original callback body to a helper cave), and validates an in-memory patched image in Unicorn. It does not write the H1 runtime IPS. The reviewed H1 runtime report records installed IPS SHA-256 `9b5f7c8f261743a2805d356153232f445c02f00c2f7938e7550505bc4b6317f9`, cave `0x003FE720`, and a live hit there, but cites an external script under a user scratch directory; that runtime patch-construction script is not reproducible from the checked-in H1 runner alone.
- H0 proves Azahar applied a previous IPS and reached title → Audio Settings → title; it does not reconstruct a general patch writer. Its earlier patch was kept separately and the observed FLAG hits prove entry reachability only.

### H2 candidate placement facts

Pinned US v0.1.0 code image SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. `config/game_info.json` maps `.text` VMA `0x00100000`, file offset `0`, size `0x002FE624`, aligned size `0x002FF000`. Therefore the current zero-padded page tail is `0x003FE624..0x003FEFFF`, also file offsets `0x002FE624..0x002FEFFF`, capacity `0x9DC` (2,524 bytes). H1 runtime has already observed the loader executing a replacement from that same page at `0x003FE720`; this supports loader/cave feasibility for that exact title/build, not every possible padding/candidate placement.

The independently reviewed `TitleConfig_Calc` experiment compiles to 2,096 bytes. Its run report lists four `R_ARM_ABS32 .text` in-symbol relocations at blob offsets `0x3C, 0x40, 0x44, 0x48`, with local addends `0x4C, 0x1C0, 0x16C, 0x1A4`; the experiment rebases them to `0x0100004C`, `0x010001C0`, `0x0100016C`, and `0x010001A4`. These are local blob references in the report, not addresses that can be copied unchanged into a cave. At a prospective cave base `0x003FE624`, a patch builder would need to encode the corresponding values `0x003FE670`, `0x003FE7E4`, `0x003FE790`, and `0x003FE7C8`, after independently confirming object relocation semantics and that the symbol extraction includes their targets. Reject any unrecognized relocation. The reviewed initializer candidate is 552 bytes with no relocations; the reviewed secondary candidate is 284 bytes with no relocations. These candidate sizes are evidence from their experiment reports, not proof that they are safe to place or runtime-equivalent.

### Recommended smallest integration batch

Start with **only `TitleConfig_Calc` (`0x001EA928`)** after the coordinator accepts its independent review. Keep the original initializer (`0x002F4CA0`), secondary callback (`0x002CAEF0`), draw callback (`0x002CAFD0`), readiness path, and engine helpers. This leaves original task creation/work initialization and secondary cleanup in control while changing one callback that the original initializer registers. It occupies 2,096 of 2,524 cave bytes and leaves 428 bytes for alignment/branch support. Secondary integration could later fit too (`2,096 + 284 = 2,380`, 144 bytes remain), but its partial helper models and unresolved task-state/free meaning make it a worse first runtime patch. Including the initializer candidate would take `2,096 + 284 + 552 = 2,932` bytes if kept in the cave, exceeding capacity; overwriting the initializer's original span in place also risks destroying literal strings/data it currently reads by absolute address, so do not assume a short in-place C++ body is safe.

Prospective exact placement for the calc-only patch is:

| Item | Guest address | `code.bin` file offset | Size / operation |
|---|---:|---:|---|
| Calc entry redirect | `0x001EA928` | `0x000EA928` | Replace exactly one ARM word with unconditional branch to cave |
| C++ callback blob | `0x003FE624` | `0x002FE624` | 2,096 bytes, with the four verified local absolute relocations rebased |

The ARM branch is within range. The entry is already passed to the calc task factory as `0x001EA928`; retaining the original initializer means the registered function pointer still reaches the patched entry. Preserve all other bytes. This placement is a design proposal, not a patch already produced or tested. Confirm no unusual interior/alternate entry dependencies before building it.

The candidate currently lives at `experiments/semantic_equivalence/h2_calc_candidate.cpp`; a future production promotion should move/reconcile the implementation into the production source for address `0x001EA928` (currently the ARM wrapper in `src/engine/leaf_batch46_b.cpp`) and update only that function's ledger status from `matching` to `non_matching`, with a semantic record. Do not change the ledger to `matching`, and do not treat `verify_decomp.py` size coverage as semantic proof. For a later initializer replacement the production source is `src/camp/title_flow.cpp`; for secondary, `src/engine/leaf_batch32_c.cpp`. This task made no such edits.

### Required reproducible patch/check sequence

A separately assigned integrator task should create an H2-specific patch builder (or explicitly extend integration tooling with tests) that:

1. Verifies pinned image size/hash and `.text` VMA/file-size/alignment bounds; rejects non-zero cave bytes, overlap, out-of-range branches, over-capacity blobs, and any unsupported relocation.
2. Compiles the production calc candidate from a frozen tree, records compiler/object/source hashes, extracts exactly `candidate_001ea928`, and resolves only its audited four `R_ARM_ABS32 .text` local references against the final cave VMA. Verify every local target remains inside the extracted blob. Add a branch at the exact original entry and preserve the function's original full span except that first word.
3. Emits a deterministic patched `code.bin`, IPS, placement/relocation manifest, original/patched/IPS hashes, and an independent IPS-application check whose resulting bytes hash exactly equals the tested patched image. Keep outputs in ignored `build/` and never alter the pinned `extracted/exefs/code.bin`.
4. Runs a patched-image ARM differential/caller check at the *final guest cave address*, not only the candidate at a synthetic `INJECT` address. The current H2 calc reports use mocked service boundaries, so preserve their partial status and separately validate original-helper effects/caller setup. Include a deliberate wrong branch target or patched candidate control to prove the patch application/check detects a mismatch.
5. Only after patch bytes and original/candidate provenance are reviewed, use the reviewed Azahar CLI/GDB route with separate staged installs and matching disposable user/profile seeds. Log executable/game/patch hashes and effective user paths; observe entry at `0x001EA928`, candidate cave hit at `0x003FE624`, `g_TitleConfigWork`, callback state, work bytes, config bytes and return path in original and patched runs. Capture state before the callback can invalidate/free work. An entry hit proves installation/reachability, not behavior equivalence.

The exact runtime command proposed by the CLI contract is an example (`azahar.exe --windowed --gdbport 24690 <CCI>`), not executed. Use separate staged app directories with an adjacent isolated `user\\` directory and verify Azahar's effective path from logs. The checked-in `experiments/semantic_equivalence/azahar_hit_flag.py` is a minimal monitor for its historical fixed port/PID and breakpoint/read subset; it does not implement H2 snapshots or validated memory/register writes.

## H1 precedent and evidence caution

H1 demonstrates a working production pattern: preserve the enclosing callback extent, replace a bounded original instruction window with a branch/call shim, place compiled C++ into `.text` padding, run differential/caller composition, install an IPS, and observe a live cave PC. Its State-5 C++ functions were fitted via manual extraction/linking and a specific patch script outside the repository. H1's full path is more than a candidate file or unit test; it also does not provide a reusable H2 patch constructor.

One detail warrants narrower wording when using H1 as a comparison benchmark: the H1 Azahar report marks `initial_ready_at_001e9de0` as `matched: true`, but the stored raw snapshots differ at that step (`timer_64` 1.0 vs 2.0, `blend_68` 0 vs 0.0667, `fade_98` 0 vs 19.0). This is a fact from the report; why those values differ or which observations its `matched` flag compares is not explained in the row. Thus the 11/11 label is evidence for the report's selected scenario observables, not proof that every listed runtime field or whole state matched. The H2 runtime comparator must state a field-by-field comparison policy and synchronise equivalent stop points.

## Runtime blockers and H2 acceptance gap

The reviewed CLI/GDB route is static research only. Its future design requires staged executable/game/patch identity, a new loopback port, PID/path verification, and separate disposable `user` profiles. No RSP `M`/`P` support or H2 event-injection path is validated. A later static audit found the `IfTouch_Init` manager producer and its `TOUCH CALC` update callback, but the relation between its state/index and Calc's `work+0x1C..+0x22` sentinels remains unresolved; `0x001EABE0` is only a proposed return-register seam. The checked-in monitor cannot drive the menu or snapshot all H2 state. See [the manager-state audit](h2-input-manager-touch-state-producer-audit.md).

The reviewed Calc candidate's differential uses shared deterministic mocks for input, touch, task/script decisions, rendering, audio and animation; state 1 and state 2 are tested as separate callback cases rather than one actual caller sequence. The initializer candidate similarly uses HLEs for allocator, process factory, sprite/cursor setup, async file loads, sound and UI reset. Existing H0/H1 runtime only covers no-change entry/cancel; it does not prove an edited cancel, confirmation, persistence, re-entry or restart. The milestone acceptance therefore remains open even if a calc entry patch and live cave hit are achieved. No keyboard/mouse automation should be used to paper over the unresolved input seam.

Next action: after independent candidate/source review, assign one integrator-owned implementation task for a calc-only cave/IPS builder and final-address ARM/caller validation. Separately resolve a valid logical input seam and validate RSP/profile isolation before attempting the original-versus-patched edit/cancel/confirm/re-entry/persistence/restart scenarios. Do not mark the H2 scenario complete from the patch or a cave hit.
