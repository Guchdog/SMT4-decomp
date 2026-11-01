# Independent review: expanded `0x002AF854` alias evidence

## Frozen evidence and object identity

All input hashes in run-002 `task.json` match. The pinned reference image hash is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; the preserved runner output hash is `a9fac9b90ea7daf807cd53904132549293f1dfa2d1192a30cac1f800c306f029`. I reviewed the frozen runner/output and independently extracted the candidate and production symbols from the recorded objects. Both remain 64 bytes, have no function relocations, and match byte-for-byte (candidate object `516c5aed72c5738989545c9a83a9897be7c4358fa907df34954c81e76326d19d`; production object `06a038ddcec0acffbf0b49de94125217bb06eb0ed9256ebeb8e6a3127021e162`). I did not rerun the compiler, differential, or emulator.

## Address and order checks

The 132 direct alias cases comprise the original 60 cases at index 0 plus 72 cases at indices 2 and 5. For each index and three seeds, the runner uses base offsets derived as `list = object + selected_offset - index*12`, where `selected_offset` is `0x5C`, `0x60`, or `0x84`, and modes are 0, 1, `0x100`, and `0xffffffff`. With mode zero the selected word is at the target offset; nonzero mode selects the following word. This includes representative overlaps with the index store at `+0x5C`, mode-byte store at `+0x60`, and byte clear at `+0x87` (the selected word beginning at `+0x84`). The fixtures use aligned, mapped ordinary RAM and non-wrapping addresses.

The actual original `0x002B8D24` index-2 caller composition checks the two calls and their exact arguments: `(object+0xC4,2,0)` followed by `(object+0x1DC,2,0)`. The cross-alias fixture points the first call's list into the second subobject at `+0x44` and the second call's list into the first subobject at `+0x44`. Each index-2 selection then reads at that subobject's `+0x5C`. The fixture initializes the first subobject's selected word to `0x89898989`; the first call writes index 2 there, and the second call must read that updated word. The runner asserts that the final selected word in the second subobject is exactly 2, compares the original, candidate and production runs, and retains ordered guest write checks. It runs 32 disjoint-list and 32 cross-alias seeds.

The runner reports 503/503 direct cases, 32/32 disjoint and 32/32 cross-alias original caller compositions, four ordinary mutants detected, and the nonvolatile ordering control detected. The control is specifically list=`object+0x5C`, index 0, mode 0 and requires the selected word to differ after volatile is removed. The volatile source ordering remains limited to the five stores before the selected read plus that read; source/production behavior is consistent with the original memory-event order in these fixtures.

## Does this close the `0x002B8D24` alias limitation?

It closes the previously identified **index-2 caller alias gap** for the concrete two-subobject cross-alias pattern: the relevant caller, helper indices, argument order, first-to-second mutation dependency and final value are exercised against the pinned original. The 72 additional direct cases also support selected-word overlaps for helper indices 2 and 5 at the three listed target offsets.

It does not establish every possible `0x002B8D24` alias arrangement. In particular, the wrapper's selector-12 loop passes index 5 to up to five separate subobjects, but this run tests index 5 only as a direct helper call and does not compose selector 12 or cross-aliases among those five calls. Arbitrary list/object overlap, other alias offsets, pointer wrap, invalid memory, MMIO, concurrency and C++ object-lifetime/type-alias assumptions remain outside the tested domain. Keep those limits explicit; the alias limitation may be narrowed to the tested index-2 and direct index-5 cases, but must not be removed globally from the `0x002B8D24` record.

The updated function record also retains a stale earlier sentence saying only index-0 overlaps were exercised, immediately before the run-002 extension that adds indices 2 and 5. Correct that sentence in the coordinator's next documentation edit so the evidence summary is internally consistent.

Conclusion: the concrete index-2 cross-alias case that blocked the prior `0x002B8D24` support claim is now covered. Broader selector-12/cross-call alias behavior is still unverified, so full arbitrary-alias support is not established.
