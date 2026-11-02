# Independent review: `0x002A8A8C` status counter service

## Recommendation

The typed helper passes the reviewed direct cases and bounded selector
compositions. I found no counter-semantics, raw-return, fault, slot, or
interworking counterexample. Approval is limited to the mapped global-pointer
fixtures and exercised selector states. Before wider integration, the
coordinator should align the caller declaration from `void` to `u32` and
reclassify the non-identical function from `matching` to `non_matching`.

## Frozen input and ARM audit

All 16 packet input hashes matched. The pinned 36-byte function consists of
eight ARM instructions followed by a literal at `0x002A8AAC`; the literal is
`0x0043DCB0`. The first instruction loads that word using PC=`0x002A8A94` plus
`0x18`. The next instruction loads the pointer stored at `0x0043DCB4`; call
this value `P`. The helper forms `P+0x600`, reads the signed halfword at
`P+0x64C`, decrements/stores a halfword only when that signed value is
positive, and returns `P+0x600` unchanged in `r0` on all non-faulting paths.
The incoming `r0` is ignored. This is not a counter-value return and not a
success flag.

The candidate uses a PC-relative literal containing `0x0043DCB4` directly,
then performs `LDRSH`, `CMP #1`, conditional subtract/store, and `BX LR`. The
`CMP #1`/`GE` condition is equivalent to the original signed `CMP #0`/`GT`
condition. The body touches only `r0/r1`, flags, and the counter halfword; it
has no stack accesses, calls, or callee-saved register writes. The direct
runner compares raw `r0`, `r1/r2`, SP, preserved-register status, full mapped
data/global snapshots, ordered writes, and fault details.

## Fresh differential and faults

Fresh command and exit:

```text
python -B tools/h2_status_service_experiment.py --out build/agent-work/H2-semantic/h2-status-service-review-002a8a8c/run001/checks/review-001
exit: 0
```

The report matched all 11 direct cases: signed values `-32768`, `-1`, `0`,
`1`, `2`, and `32767`; ignored incoming `r0`; adjacent-byte preservation; null
`P`; an unmapped counter read; and a read-only positive counter store. All
cases matched, including raw return `P+0x600` and exact writes. Faults were:

- `P=0`: halfword read fault at `0x0000064C`, with no prior write.
- Unmapped counter: read fault at `0x00800000`, with no prior write.
- Read-only positive counter: halfword store fault at `0x0061164C`, with no
  earlier write.

All four in-slot controls were detected: changing the zero threshold,
unsigned comparison, byte-width store, and global pointer offset. There were
zero differential mismatches.

## Selector call multiplicity and raw-register boundary

The original `0x002B85BC` image contains nine service-call instructions across
mutually exclusive paths: conditional calls at `0x002B8634` and `0x002B8758`,
plus calls at `0x002B8644`, `0x002B8650`, `0x002B8658`, `0x002B86C4`,
`0x002B8768`, `0x002B8774`, and `0x002B877C`. The two six-slot status loops
have these per-slot counts after `0x002BF030`:

- Status 0: zero calls.
- Ordinary nonzero status: one call.
- Status 8: three calls.
- Status 7 or 9: one conditional call, status reload, then one call unless
  the reload is 8; a reload of 8 takes three more calls, four total.

In the new-profile route, each nonzero status is cleared and causes one call;
zero skips it. That route also uses two later record helpers, which are
separate from `0x002A8A8C`.

The fresh standard composition compiles and installs the typed selector with
the candidate service. For status bytes `[0,1,7,8,9,2]`, it produces nine
service calls and matches the original selector/service image for initial
counter values 3 and 1. The global counter reaches zero after three or one
stores respectively; all six selector status bytes remain unchanged. This
keeps the helper's global halfword distinct from selector status storage in
that fixture.

The selector declaration still says `extern "C" void ui_func_002a8a8c()`
while the definition returns `u32`. The selector discards the result, so the
call ABI and tested effects remain compatible, but the interface should be
corrected before integration. The runner intentionally normalizes away
service-entry `r0` in its caller-event comparison. That is appropriate for
behavioral comparison because this helper ignores incoming `r0`, but it does
not claim raw callsite-register parity. In particular the compiled C++ caller
can pass the preceding returned pointer on later calls where the pinned
assembly reloads a status byte.

I also exercised the duplicate status loop with both profile flags zero and
the new-profile clear-status path. Both original/staged caller comparisons
matched: the duplicate loop made nine calls; the clear-status route made five
calls for five nonzero statuses and cleared those bytes. A controlled alias
fixture makes the global signed halfword coincide with the first slot's status
byte; `9` is decremented to `8` by the first service call, then the caller's
reload selects the three-call block (four total calls). Both images agree on
this path. The alias is a directed control for the reload logic, not evidence
that live state uses this layout. The extra `0x002BDAC0` calls in the
new-profile route were intercepted to verify their arguments; that hook does
not validate that neighboring helper.

## Compile, interworking, patch, and accounting

The fresh run compiled the status TU and typed selector TU for ARMv6K. The
status body is exactly 36 bytes with no relocations and differs from the
original. The status IPS contains one 36-byte record at file offset
`0x001A8A8C`; replay succeeds and no byte outside the slot changes. The
two-slot composition IPS also replays and changes only the declared
`0x002A8A8C` and `0x002B85BC` slots. The selector has 11 ARM call relocations,
all targeting even addresses (`target_bit0_clear=true`), including the status
helper. The status function has no function-pointer writes or interworking
relocations.

The current ledger still says:

```text
0x002a8a8c,36,matching,ui,ui_func_002a8a8c,src/engine/leaf_batch23_b.cpp
```

This label is inconsistent with the fresh `exact_matching=false` result.
Current ledger counts are 10,905 `matching`, 54 `non_matching`, and 8
`matching_span`; changing this row yields 10,904, 55, and 8 respectively,
without changing row count or text coverage. The ledger and reporting files
were not edited in this review.

## Limits and evidence identity

These are offline Unicorn tests over controlled pointers, counters, profiles,
and manager slots. The selector lookup and `0x002BF030` are deterministic
hooks; the counter's lifecycle, live pointer validity, service transitive
effects, natural H2 reachability, and runtime/audio behavior are unverified.
The alternate selector helper in the added branch test was also hooked. No
full build or emulator was run.

- Fresh report SHA-256: `c82066eef11006aaad4058e0b08c13d6e2bbf9c9a9e2c27d44733d632abe02b3`.
- Candidate source SHA-256: `718839e52ac638f0d9612ffcce047bcbcb874037e0f9a0051c31ff6000104f8f`.
- Candidate object SHA-256: `8b4be8a9e2193fc9c11fcca7f3d66ec4d386403044255fc032a386ba19f12625`.
- Status image SHA-256: `5e91008bbe364b2dae41e617dbb746a61397ccce02dbddefe7efc7c7f5709b72`.
- Status IPS SHA-256: `3308968297d57c9becbaafb27c7c9063d1e8293c20baa60541bda671ad8eca64`.
- Supplemental caller paths SHA-256: recorded in the handoff.
