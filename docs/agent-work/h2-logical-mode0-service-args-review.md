# Independent review — mode-0 service argument trace

## Finding

The added service trace closes the prior argument-observability gap for the bounded mode-0 matrix. The runner's Unicorn code hook at `0x002C6C10` reads the live ARM `r0` and `r1` registers at service entry. Each case captures its original and candidate trace slices, compares them pairwise, and checks the candidate trace against the independently computed branch contract: `[(counter-threshold, selector)]` only when the ID is valid, bit 0 is clear, counter is not the early-pulse value 1, and counter exceeds threshold; otherwise the trace is empty.

The trace digest and count are consistent. The report records 43,896 entries and matching original/candidate SHA-256 `4711cd958c8beb5ccd5a4cc8e6ef819e72f338b10aa17ceb7531895f6fdcc801`. I independently regenerated the expected trace in runner loop order from the documented matrix and obtained the same count and digest. This is still isolated-helper evidence: the service at `0x002C6C10` remains original code, selector zero is omitted, and producer/runtime behavior is not established.

## Trace and control review

- The hook is an entry hook (`begin=end=DIVMOD`) and reads the emulator registers before the service executes. It appends `(r0,r1)` pairs, not modeled values.
- `invoke_recorded` slices the helper-call list at each invocation's start/end, so `compare` checks the per-case original/candidate call count and exact pair sequence. The candidate is additionally compared against expected arguments for each valid matrix case.
- Matrix size is 140,864: IDs 0..30 × flags 0..3 × thresholds `{0,7,31,64}` × nonzero selectors `{1,2,3,7}` × 71 counter values. Another 20 calls cover invalid IDs. Total is 140,884; the 43,896 service entries match the branch predicate.
- The controls remain sensitive and their captured traces show the changed arguments: bad-threshold original `[3,2]` vs mutant `[2,2]`; bad-selector original `[2,2]` vs mutant `[2,3]`. The bad-counter mutant is also detected (return 0 vs 1) and, correctly, does not enter the service on that directed case.

The pinned original at `0x002B902C` loads selector into `r1`, subtracts threshold from counter into `r0`, calls `0x002C6C10`, then checks the returned remainder in `r1`. The C++ helper's inline ARM assembly explicitly places dividend and selector in those registers, calls the same address, and copies returned `r1` as remainder. The observed trace therefore validates the exact service ABI arguments as well as its branch placement.

## Stack and caller-visible effects

The refreshed report records no non-stack guest writes and confirms every observed stack write lies below the fixed entry SP (`0x08004000`). Stack-write counts remain different (original `281,774`, candidate `175,584`), and temporary stack contents are not compared. The runner compares original and candidate SP on every case and callee-saved `r4-r11`; the recorded mutant examples return at `0x08004000`. Source disassembly also shows the original's push/pop balance and the candidate's conditional push/pop on its service path, with fast paths returning without changing SP. This supports restored caller-visible stack state, not equality of scratch bytes.

## Provenance and production identity

The final differential file SHA-256 is `185a8d8697184603a0b5dea0683e78c062d9e31b286165eeaaa1313c95e715ec`, matching the packet manifest. The compile report SHA-256 is `2703853e94dd720426fee728edd839a699f1d52cdd020a7abbcb9b18b4f08b66`. All seven recorded production/caller objects exist, match their report hashes, and have successful exits.

The production TU source hash remains `42829c03786f8675adc5e5b8ca64ded5d7d23a9923f2adaa9ac4b97f6020dbeb`. The current production and candidate symbols are 136 bytes, relocation-free, and byte-identical with body SHA-256 `6d375730a5326520f907ac12c3928dafdcfb2d85dc1fefcc86f727ef1c662538`; the production object hash is `0596cea541cb609cb60f0ee43b66a62071c0f2050509cd4dad3a909de77b7605`. This is unchanged from the earlier production compile evidence. The original span is 104 bytes; the ledger remains truthfully `non_matching` and no image patch/runtime acceptance follows.

One metadata note: the report's embedded `report_sha256` is `4c40ce917964e4b45f4377f812dbcbe542ac7c136472d2152ee61183bd06ba56`, which is the digest captured before that field was serialized back into the JSON. It does not equal the final file's SHA-256 above. The packet's input hash and integration note use the actual final file hash; use those for artifact identity.

## Limits and recommendation

Accept the argument-trace correction as stronger, per-case service-call evidence for the isolated helper. It does not reconstruct the division service, cover selector zero's divide-by-zero path, prove freshness/scheduling of logical counters, map IDs to physical controls, or establish an IPS image and H2 runtime behavior. Keep those limits and the `non_matching` ledger status explicit.

No build, test, emulator, debugger, or guest-state action was run for this review.
