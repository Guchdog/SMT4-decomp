# Independent review: `camp_func_002bdac0`

## Recommendation

The frozen C++ reconstruction is supported by the pinned offline evidence for the tested raw 32-bit mode/selector domain, null-table return, ordered alias case, and two real `TitleConfig_Calc` call slices. The compiled body is 80 bytes in the 108-byte slot with no relocations. The one-slot IPS round-trips and changes only `0x002BDAC0`. I recommend proceeding to integration review as a bounded nonmatching implementation; runtime and full state-transition behavior remain unverified.

## Provenance and patch scope

All 21 run003 packet input hashes match. Key identities are: original image `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; source `src/engine/leaf_batch13_c.cpp` `52220f75e242ea3f9a9d19d08dc49839896c482c655b7be63803f45e64594085`; report `b3ae3603ff33879de8ccc2436510bf7ce750da97a7339db4cc847387bfbdfc99`; staged image `3afbd263381b66d18f8ac680529fb27e4291899b70cb74401c8b812552df8774`; IPS `af194f9646402bd6dd7e421d1fe3478e7ad50f4c3dabcbcba7db4eb5d0c2b3ec`.

The existing compiled object `candidate.o` hashes to `dde2e061ea545dd3ad11365c40afec600b47c4106105e6bc8cf075abb3e0a0ef`. I extracted its `camp_func_002bdac0` body: 80 bytes, SHA-256 `b9638dacf59be4454222ea5b133e9ec5043dc36a6d850f6d0739cd9ae561bfd6`, no relocations. The staged 108-byte slot begins with those exact 80 bytes and contains seven ARM NOP words afterward.

The cumulative base image hash is `b71fece339cc135393f03a4e806bcf5a2d158cfe1ed8402df249c3613d933140`. Applying the pinned IPS reproduces the staged image exactly. It changes 77 bytes, all within file offsets for VA `0x002BDAC0..0x002BDB2B`; manifest and report both say the only declared slot changed. The CSV row marks this differing implementation `non_matching`, which is consistent with the report’s `final_slot_matches_original:false`.

## Contract and ordering

The implementation accepts `(void* object, u32 mode, u32 selector)` and returns the original object pointer in `r0`. It first reads the table pointer at `object + 0x4C`; a null pointer returns immediately with no writes or table reads. For a nonnull table it stores low 16 bits of `mode` at `+0x50`, clears `+0x52`, `+0x86`, and `+0x8A`, and stores low 8 bits of `selector` at `+0x54`. Addressing uses the full 32-bit mode in `table + mode*12` with unsigned wrap. The full 32-bit selector selects signed halfwords at row offsets `0/2` only when selector is exactly zero; every other value selects `4/6`. Each signed halfword is converted to unsigned and shifted left 12, giving the ARM 32-bit wrap result, then stored at object `+0x0C` and `+0x10`.

The order of later reads/stores is significant: read x, store scaled x to `+0x0C`, then read y and store scaled y to `+0x10`. The alias fixture makes the table row begin at `object + 0x0C` and seeds halfwords `0x1234, 0x2345`. The first output word becomes `0x01234000`, overwriting the second source halfword with `0x0123`; the later y read consequently produces `0x00123000`. The report’s final aliased bytes (`0040230100301200`) and write sequence match across original, temporary, final and staged profiles. This exercises the store/read dependency rather than assuming disjoint table/object memory.

## Differential and caller evidence

The harness compares original, temporary, final-VMA and staged execution for 72 direct cases: 24 directed combinations (six modes including `0x10000` and `0x80000001`, each with selectors `0`, `1`, `0x100`, and `0xFFFFFFFF`) plus 48 seeded cases. It checks full object/row state, ordered read/write traces, return pointer, saved registers and stack. Three null-table fixtures verify return and no writes. Three negative controls are detected: wrong stride (`12` to `8`), byte-only selector comparison, and wrong second-field offset.

Two actual `TitleConfig_Calc` slices (`0x001EAF2C..0x001EAF3C` and `0x001EAFC8..0x001EAFD8`) compare original code with the cumulative staged image. Both set `(object=work+0x5C, mode=1, selector=0)` and compare the post-call object. The harness creates a readable table fixture with the selected mode-1 row. The cumulative staged base carries the earlier predicate/getter changes; I independently confirmed the caller-slice bytes and the candidate’s table/object/helper path used in these tests are unchanged between that base and the pinned original except for the declared staged slot.

## Limits

The report’s compile and offline results are pinned evidence; I inspected the existing object and harness but did not compile, rerun the runner, or launch the emulator. No table bounds are checked or inferred. Unmapped/invalid pointers, arbitrary wraparound address mappings, unaligned access behavior, concurrent mutation, table lifetime/length, initialization caller behavior and a natural TitleConfig runtime scenario remain unproven. The two tested caller slices do not establish complete TitleConfig state transitions.
