# Independent review: `script_vm_func_002b8b78` (`0x002B8B78`)

## Recommendation

Approve the typed C++ reconstruction as a bounded transition wrapper for valid mapped manager/object/profile fixtures and the two exercised caller slices. The fresh run passed all 23 direct final-VMA cases, both original caller call slices, and all four mutation controls. The candidate preserves the full-width request, direct state changes, dependency call order/arguments, raw service return, and ABI observations in that tested stubbed domain. No concrete candidate behavior counterexample was found.

One documentation mismatch should be corrected if README intends to count branch instructions: the compiled body contains six relocated branch instructions (`BL`s) to five distinct ARM targets, while README currently says “five ARM branches.” The relocation report itself and the other records accurately say there are five branch targets. This wording issue does not invalidate the differential, but the exact instruction count should be made consistent.

## Frozen inputs and fresh run

Recomputed all 18 SHA-256 pins in the task packet; all match. The pinned original image hash is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; pinned candidate source hash is `6837eb9eeabc93cfe89ca118f7f1e909102f2c11e1681c69c93af57bde339ea2`.

Ran the assigned experiment in the task-private output directory:

```text
python -B tools/h2_sound_playse_experiment.py --out build/agent-work/H2-semantic/h2-sound-playse-independent-review-002b8b78/run001/checks/fresh
exit: 0
```

The fresh `report.json` SHA-256 is `719b1e0ccf034a99cefafabccd1dabcce3bff30521229f81eee876f59e0a9105`. It identifies 23 fixtures (seeds 11–33), 23 direct comparisons, zero mismatches, two caller slices, four detected mutations, IPS replay success, and no changes outside the 340-byte entry slot. Compiled body size is 332 bytes and is not byte-identical to the original.

## ARM behavior and candidate audit

I independently decoded the pinned 340-byte ARM entry. It saves `r4-r8`, `sb`, and `lr`, reserves 12 local bytes, loads the manager object pointer from `0x0043DA2C`, and reads the selected profile byte at object+`0x4C9`. It compares that zero-extended byte with the full `r0` request. Equality returns immediately with the byte still in `r0`; there is no preceding null guard for the manager/object pointer.

On mismatch, the original reads a signed word latch at `0x0043DA38`. A negative latch scans six bytes at object+`0x4B8` through `+0x4BD`; a hit writes the full request to the latch and returns the found index. A miss or a nonnegative latch writes `0xFFFFFFFF` to the latch and continues. It calls `0x002B85BC(request)`, reads the old profile ID again from the original object, and calls `0x002AEA28(old_id)` then `0x002AEA28(request)`. It returns the second lookup's raw result if either pointer is null, after retaining prior effects.

When both profile pointers are valid, the body saves the old selected byte to object+`0x4CA`, stores the low byte of request to object+`0x4C9`, loads six priority bytes from ROM address `0x00402550`, and processes six halfwords in ascending slot order. Nonzero halfwords call `0x002B8794(slot, priority[slot], value & 0xFF, 0)`; zero halfwords call it with `(slot, 0x12, 0x51, 0)`. A value such as `0x0100` is nonzero and takes the former path with low byte zero. The final old/new profile flags select one of three direct outcomes: store 0 at current object+`0x4C5` then return `0x0013851C(0)`; store 1 then return `0x002AE874(1)`; or store 1 then return `0x0013851C(1)`. The object pointer is reloaded for these final stores, matching the possibility that a dependency changed manager+4.

The C++ body follows this branch order and preserves the typed load/store widths: byte profile fields, signed 32-bit latch, six byte occupancy reads, six unsigned halfword reads, and byte state stores. It performs all five original dependency functions through direct relocations, keeps the `0x0100` path distinct from zero, and returns the selected service's raw `u32`. The direct runner compares return, SP, callee-saved registers, mapped persistent memory, writes, and dependency call arguments/order. All direct cases matched.

## Caller slices, controls, and placement

Both tests start from the original caller setup and `BL`, then stop immediately after the helper call: TitleConfig initializer request `0x99` at `0x002F4DEC`, and the conditional `0x00286928` path request `0xDC` at `0x00286B7C`. Each trace matched original versus staged, had no fault, recorded ten dependency events, and reports 8-byte stack alignment at every call. The observed call arguments include the full request, both ordered profile lookups, all six slot calls in order, and the final service call. These establish the tested call slices; they do not demonstrate natural reachability of the callback's conditional branch.

All four negative controls were detected: truncating the profile comparison to a byte, changing the signed latch test, truncating the stored request, and changing the default slot argument. The fresh object body is 332 bytes in a 340-byte ARM slot. It has six branch relocations at offsets 60, 72, 84, 216, 300 and 320, resolving to five distinct even ARM entries: `0x002B85BC`, `0x002AEA28` (two calls), `0x002B8794`, `0x0013851C`, and `0x002AE874`. The data relocation at offset 328 resolves to `0x00402550`; its six bytes are `05 06 04 03 02 01`. The pinned interworking report confirms bit 0 is clear for every dependency entry and both caller BLs target the aligned ARM entry `0x002B8B78`. The fresh IPS replays, and independent whole-image comparison confirms only bytes in the helper slot changed.

The affected-TU report lists nine translation units and says all compiled with the ARMv6K Clang configuration. I verified the nine corresponding object files exist in its task-local output directory; this was a focused affected-TU result, not a full build.

## Classification, README, and milestone claims

The ledger row for `0x002B8B78` is `non_matching`, consistent with the fresh report's `exact_matching=false`. Ledger counts and byte totals reconcile: 10,909 matching functions / 3,120,864 bytes, 50 non-matching functions / 17,760 bytes, and 8 matching spans / 484 bytes, totaling 3,139,108 bytes over 10,959 functions plus 8 spans. README exact coverage arithmetic also reconciles: `(3,120,864 + 484) / 3,139,108 = 99.4342%` rounded to four decimal places. The milestone/README correctly state 23 direct cases, two caller slices, four controls, 332/340-byte body, original dependencies, and no runtime/audio verification. Their “five branches” phrasing should specify five distinct targets or be corrected to six branch instructions.

## Limits

The experiment compares the wrapper under explicit valid manager/object/profile fixtures and controlled dependency implementations; it does not validate the transitive memory/audio effects of `0x002B85BC`, `0x002AEA28`, `0x002B8794`, `0x0013851C`, or `0x002AE874`. Invalid/unmapped pointers, resource count/table validity, aliasing or concurrent manager mutation are outside the domain. The two call slices do not prove the callback branch is naturally reached. No actual audio output, profile persistence, broader caller state machine, or emulator/runtime behavior is established. Preserve the descriptive transition contract instead of claiming equivalence to a simple sound-play API.
