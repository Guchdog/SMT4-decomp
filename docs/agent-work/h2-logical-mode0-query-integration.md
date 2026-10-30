# H2 logical mode-0 query integration

`ui_func_002b902c` (`0x002B902C`) now has typed production C++ in
`src/engine/leaf_batch30_b.cpp`. It validates unsigned IDs `<31`, reads the
mode flag at `0x004650A8`, checks for the first-pulse counter value one, then
uses the threshold `0x004650AC` and selector `0x004650B0` for the repeat path.
The fallback invokes the pinned original quotient/remainder service at
`0x002C6C10`; the candidate preserves that service as an explicit dependency.

The offline differential passed 140,884 calls. The complete valid-ID matrix
covered 31 IDs, four mode-flag values, four thresholds, four nonzero selector
values, and 71 counter values. Twenty invalid-ID cases also passed. The test
compared the return, fault, PC, SP, r4-r11 and every fallback service's `(r0,r1)`
arguments, found no data writes, and detected wrong counter, threshold and
selector controls. Original and candidate fallback argument trace hashes match.
Stack writes differ as scratch below entry SP; the runner verifies their range
and SP restoration. Selector zero is excluded because the original divide
service enters its zero-divisor error path.

The candidate and production bodies are byte-identical at 136 bytes with no
relocations, versus the original 104-byte body. The ledger is therefore
`non_matching`; no IPS image or runtime test includes the change. Seven
production/caller TUs compiled. The original service at `0x002C6C10`, input
producer freshness/cadence, physical control mapping and runtime event delivery
remain unresolved.

Focused tests: `python -m unittest tests.test_h2_logical_mode0_query_experiment -v`

Differential:
`python -m tools.h2_logical_mode0_query_experiment --output build/agent-work/H2-semantic/h2-logical-mode0-service-args/run-002/checks/differential-20261026`
