# Independent review: `ui_func_002b85bc` (`0x002B85BC`)

## Recommendation

Approve the typed selector for the bounded fixture and caller contract. The fresh differential passed all nine direct cases and both original caller slices; all five mutation controls were detected. The corrected status behavior is represented correctly: unchanged status 8 causes three service calls; unchanged 7/9 causes two total; when the first 7/9 call changes status to 8, it causes four calls total (the initial call plus the three-call status-8 block). Hook calls, arguments, and order match the original in the observed cases.

There is a separate exact-classification issue to fix during integration: the fresh body is 372/472 bytes, uses 11 relocated calls, and `exact_matching=false`, while the current CSV row remains `matching` and README omits `0x002B85BC` from the non-matching list. The behavior review approves the candidate, but its production classification must become `non_matching` before promotion. I did not edit the ledger or README.

## Frozen inputs and fresh run

Recomputed all 16 SHA-256 pins from the run001 packet; all matched. Pinned original image SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; candidate source SHA-256 is `b3e09dd3cb90e8b9b4a21e113fbcf361dd8ee096675f2d22a48fee9d644578c1`.

Ran the assigned fresh final-VMA experiment:

```text
python -B tools/h2_profile_selector_experiment.py --out build/agent-work/H2-semantic/h2-profile-selector-review-002b85bc/run001/checks/fresh
exit: 0
```

Fresh `report.json` SHA-256 is `a6a9d9a8bb2d61a85a3cf206b596c13c1dffb51385c0e4f391a88c24d768f645`.

## Contract and branch audit

The candidate accepts the full 32-bit request in `r0`, loads the selected old ID from object byte `+0x4C9`, and calls the original `camp_func_002aea28` first with that old ID and then with the request. The lookup order is preserved even if the old lookup returns null. If either result is null it returns the new lookup's raw result without entering profile loops or cleanup. The null-object case faults on the same unmapped read at `0x4C9` as the original; this is an explicit fault case, not a supported valid-object path.

For non-null profiles, the candidate preserves the old/new profile `+0x0C` branches, six slot iterations at stride `0x8C`, service arguments, status-byte accesses, cleanup reload, ordered stores of 0 then 3 at the reloaded object's `+0x0C/+0x10`, and raw return pointer. Each six-slot iteration calls `camp_func_002bf030(object+0x34+0x8C*i, 1)` before status handling. In the clear-status branch, nonzero status is cleared before one `ui_func_002a8a8c()` call; the two extra records call either `camp_func_002bdac0(record,3,0)` for object byte `+0x4C8 == 1`, or `camp_func_002aa268(record,0,1)` otherwise.

The status matrix covers 0, 1, 7, 8, 9 and another nonzero value. Its `ui_func_002a8a8c` counts are respectively 0, 1, 2, 3, 2 and 1, totaling nine calls. The dedicated service-mutated fixture starts at status 7; the first no-argument hook changes it to 8, then the reloaded 8 executes three additional calls. The trace therefore contains four ordered service calls for that slot. This confirms the correction to the prior static contract's 7/9→8 accounting.

## Fresh differential, hooks, callers and controls

Fresh report: nine direct cases, two caller cases, zero mismatches. Direct cases include both lookup-null paths, the old-active status matrix, the status-7 mutation to 8, both new-active two-slot modes, both profile flags zero, manager-pointer reload before cleanup, and the null-object read fault. The normal-return comparisons include `r0`, SP, callee-saved state, fixture memory, ordered writes, dependency events/arguments and fault state.

Both original caller slices match: TitleConfig initializer request `0x99` and nested callback request `0xDC`. Each reaches the selector dependencies with aligned SP. The traces show ordered old/request lookups `(3, request)`; six manager-service calls `(object+0x34+0x8C*i,1)` in index order; status helper calls interleaved according to each fixture; and in the clear-status cases two final calls with exact argument tuples `(record,3,0)` or `(record,0,1)`. Both caller slices report final raw `r0=0xAE874001`. Other wrapper services are controlled hooks, so the tests establish the modeled call slice rather than those callees' transitive effects or natural runtime reachability.

All five controls were detected: loop-bound/slot mapping, wrong status clear, status-service multiplicity, altered two-slot arguments, and cleanup value. The fresh output records 11 `R_ARM_CALL`-class relocations (type 28) at offsets 24, 36, 116, 144, 208, 216, 228, 268, 284, 316 and 332. Every rebased target is an even ARM address: `0x002AEA28`, `0x002A8A8C`, `0x002BF030`, `0x002BDAC0`, and `0x002AA268`. Each observed dependency call reports aligned SP.

The candidate body is 372 bytes in the 472-byte slot. Staging preserves the original slot suffix, IPS replay succeeds, and `changed_outside_slot=false`. Fresh staged image SHA-256 is `1c90f45173a6847abf88f87ea2495de60c6ed2be64e3bbb571822c65b29e7904`; IPS SHA-256 is `15ad28afb4e943e9adc9f1664c7c72bd811869f89746e0f6d453e74f5f73a676`; object SHA-256 is `ab280f5c40c573ae14a4b648a91a190608e5fbcd76967bff1340845fbb2aea91`. The object identity agrees with the pinned focused ARMv6K compile report. This is a focused TU compile, not a full build.

## Ledger arithmetic and classification correction

The current ledger says `0x002B85BC` is `matching`, despite the candidate's different 372-byte body and `exact_matching=false`; the conversion note also records that ledger reconciliation was deferred. Current totals are 10,907 matching functions / 3,120,504 bytes, 52 non-matching functions / 18,120 bytes, and 8 matching spans / 484 bytes. The totals are 10,959 functions plus 8 spans and 3,139,108 bytes. README currently reports 3,120,988 exact bytes including spans (99.4228%) and 18,120 non-matching bytes.

After coordinator changes the 472-byte function row to `non_matching`, expected totals become 10,906 matching functions / 3,120,032 bytes; 53 non-matching functions / 18,592 bytes; and 8 matching spans / 484 bytes. Exact matching coverage including spans becomes 3,120,516 / 3,139,108 = 99.4077%. README must add `0x002B85BC` to its non-matching reconstruction list. These are arithmetic consequences of the current ledger and the pinned 472-byte function size; no accounting file was modified in this review.

## Limits

The scenarios use explicit mapped profile/manager fixtures and deterministic hooks for the selector's service callees and remaining wrapper helpers. They do not validate those dependencies' transitive state changes, live TBB/profile population, manager lifecycle/concurrency, persistence, audible output, or natural callback reachability. Only the documented direct cases and two caller slices are covered. The null-object fault matches, but arbitrary invalid mappings, pointer aliasing and concurrent mutation remain outside the supported domain. No emulator or runtime test was run.
