# H2 staging record-overlap fix

## Result

Updated `_verify_declared_record_coverage` to reject a record when its start is before the previous record's end. This check runs after bounds/order validation and before hashing the current record payload. Sorted disjoint records remain accepted; sorted touching records remain accepted and are merged into one interval for the single-pass image coverage sweep. The coverage work remains O(record count + image bytes).

Added an overlap fixture whose second, overlapping span deliberately carries a wrong payload hash. The expected overlap error proves the structural check precedes payload hashing. Added a touching-span acceptance fixture. The existing 1,024-record fixture remains intact.

## Validation

Command: `python -m unittest tests.test_h2_manual_final_image_stage`

Result: **12 tests passed**, exit 0. The suite used temporary test fixtures only. No real CCI/profile was staged and no wrapper, emulator, debugger, network, or input automation was used.

The preceding stage-tool update recorded a read-only pass of the pinned composed image's 533 declared records. This change preserves that ordered-record contract and adds overlap rejection; the current task's validation was restricted to the requested fixture suite, so the composed artifact was not staged or rerun here.

## File identities

The selected task inputs matched their run-001 packet hashes before editing. Final hashes are recorded in `build/agent-work/H2-semantic/h2-final-image-stage-overlap-fix/001/handoff.json` and the in-run copy of this report. No board, image, or profile files were changed.
