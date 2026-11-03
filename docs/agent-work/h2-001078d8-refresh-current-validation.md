# H2 `0x001078D8` refresher: current validation

Run `run009` rebuilt the current production translation unit and re-ran the
final-VMA offline comparison after correcting the unmapped return sentinel in
the harness. The pinned input image is
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.

## Results

- The typed production body is 160 bytes in the original 164-byte slot.
- Its sole code relocation is `R_ARM_CALL` to the even ARM entry `0x0011C5EC`;
  the entry bit is zero.
- 140 directed original-versus-staged cases passed with no mismatches. Every
  direct original/candidate invocation reached the mapped return sentinel with
  no fault; no completion failures were recorded.
- Four compositions through original caller `0x0010B578` passed with its
  unrelated `0x00108B10` follow-up service stubbed.
- The 31-to-30 loop-bound mutation was detected. The exact-slot IPS replay
  matched, and no bytes outside `[0x001078D8, 0x0010797C)` changed.
- The affected production TU compiled successfully in a dedicated run output.

The current detailed report is
`build/agent-work/H2-semantic/h2-titleconfig-001078d8-counter-refresh-cpp/run009/checks/direct/report.json`
(SHA-256 `c24b60e1d55df5f12a6f767f025b046a2095b217ab6214dc7bbec8cff31cc228`).
The staged image SHA-256 is
`4b6980079ff24bafa6a41812650166fa6a4dd34bc383fded805bb54608ca79cc`; the
slot IPS SHA-256 is
`6216f7fb1d001fcf1821d8eb241595a7f0e2c27f702eeced5952294b23c0bac6`. The
affected TU object SHA-256 is
`dd85dda953d3b7b90a1f802c690c034098a71e3f25f1d5661866b8053d185f5f`.

## Review finding

The independent reviewer found the previous `run006` runner accepted matching
`UC_ERR_FETCH_UNMAPPED` faults at its unmapped return sentinel. The runner now
maps the sentinel, records the stop address, and requires that address and
`fault is None` for each direct and caller invocation. The new run009 evidence
supersedes run006's invalidated direct-case claim. No runtime or full-build
claim follows.

## Limits

The reader is controlled to return a chosen value and state word in these
fixtures. The caller composition does not execute the unrelated follow-up
service. This run does not establish physical input mapping, buffer freshness,
refresh cadence, concurrent mutation, MMIO behavior, or whole-title runtime
behavior. A distinct two-function composition report covers the reader and
refresher together; neither report establishes H2 closure.
