# H18 positive service composition: `0x002bf030` → `0x00138934` → `0x002bdac0`

## Recovered path and ABI

`0x002bf030` scans a manager's 28-byte records and tail-branches to `0x00138934` with `(object, selected_record)` in `r0/r1`. The service entry at `0x00138934` stores the selected pointer at `object+0x78`; a null selection returns immediately. A nonnull selection falls through to the body at `0x00138940`. At `0x00138964`, it loads the selected record's first word. `CMN r0,#1; BLE` bypasses the nested call for nonpositive values. The positive path reads a signed byte from `record+4`, sign-extends the first word to a halfword, sets `r0=object`, and calls `0x002bdac0` at `0x0013897c` with `(object, sxth(record[0]), ldrsb(record+4))` in `r0-r2`.

The selected record can be positive: the scan compares marker count before reading the current record's marker word, so a nonmarker positive record at table index zero is selected by selector zero. The focused fixture uses first word `1`, byte selector `0`, manager length `28`, and one record. It reaches the nested helper with arguments `(object,1,0)`. A second directed case uses selector byte `1` and reaches `(object,1,1)`, exercising the alternate table-pair selection in `0x002bdac0`.

## Composition evidence

`tools/h18_h2_positive_service_composition.py` compiles the production translation units into this run's private output directory and extracts the production bodies for `0x002bf030` and `0x002bdac0`. The image keeps the original service at `0x00138934`. It compares original execution against three variants: `0x002bf030` only, `0x002bdac0` only, and both replacements. Each is run from the real function entry under the same synthetic RAM fixture. A code hook records service and nested-call arguments, and execution stops at `0x00138980`, immediately after the nested helper returns. All four snapshots match, including object/table memory, `r0`, `sp`, and register state. The zero and nonzero nested selector cases both reach the expected ABI.

A compiled negative control swaps the zero/nonzero table-pair offsets in the nested candidate; the output mismatch is detected. The report pins source/object hashes and the original image SHA-256. The focused unittest and Python byte-compilation pass.

## Limits

This exercises the positive-record branch of the retained service and its nested helper, but deliberately stops before later service logic at `0x00138980`. The fixture is synthetic, aligned ordinary RAM. It does not establish natural H2 object setup, the runtime caller's record population, later service dependencies, startup ordering, or a complete title-config transition. This report supports the bounded composition only; it is not a whole-H2 runtime result.
