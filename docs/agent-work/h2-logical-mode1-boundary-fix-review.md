# Independent review — logical mode-1 ID-boundary correction

## Finding

The boundary sensitivity correction is effective. In the refreshed differential, ID `31` is paired with the adjacent counter word set to `1`; the pinned original and correct candidate return `0`, while the deliberate off-by-one mutant (`id > 31`) accepts the ID and returns `1`. The earlier sensitivity gap is resolved for the upper boundary. The valid-ID matrix, prior wrong-flag and wrong-counter controls, write observation, and ABI observations remain present and passing.

This supports isolated helper behavior only. The source-level production implementation remains the previously compiled body; no production source or object change is needed for this test-only correction. It remains `non_matching` against the 60-byte image span and does not establish producer cadence, physical input mapping, or H2 runtime behavior.

## Boundary mutant review

The runner appends a 32nd word to its seeded counter array and writes it at `0x004E3C58 + 31*4` (`0x004E3CD4`). For ordinary invalid ID 31 differential cases the candidate receives `boundary_counter=1`; the original receives its default sentinel but rejects the ID before reading either global. The dedicated negative control invokes both original and `candidate_002bffbc_bad_bound` with ID 31, flag bit clear, and the same boundary word value `1`. The mutant uses `id > 0x1f`, so ID 31 reaches the counter read; recorded returns are original `0`, mutant `1`, and the runner requires that mismatch to be detected. This correctly exercises the off-by-one hypothesis rather than merely observing a zero result from default memory.

## Refreshed evidence and production identity

The refreshed differential report is `build/agent-work/H2-semantic/h2-logical-mode1-boundary-fix/run-002/reports/final-differential.json`, SHA-256 `97268d810f2cbb95cb84c6fe9b18987971e0967b27eb6f0d2c28a5d92a352b27`; that matches the current file and packet manifest. It records 496 valid matrix calls plus 10 invalid-ID cases, three detected negative controls (wrong flag bit, wrong counter index, and off-by-one bound), no original/candidate guest writes, comparison of return/fault/PC/SP and `r4-r11`, and no first mismatch.

The production compile report is `build/agent-work/H2-semantic/h2-logical-mode1-boundary-fix/run-002/reports/production-compile-report.json`, SHA-256 `0bc49ccbfe7101a86c03329330316ff8bb4c9f0a5ffd8b242d346bc9a15dd1d4`, matching the report manifest and the earlier compile report. The production TU remains at SHA-256 `4a5494cadfcaadfd7af0fcd1e2c9255ebe7e72d1fedd000971ebb97a30b528e1`. I independently extracted the existing production and refreshed candidate objects: production object SHA-256 `681e67ee676c636d756e50f668101913ce344d7626b0efc31c9bd4888315e164`; refreshed candidate object SHA-256 `ffb8fc873c507e7d30161743c289bc5653a54cbfc27f57747e09a20f7a1fff5a`. Both good symbols are 68 bytes, relocation-free, and have identical body hash `0dfb38ba0a2c8384b0557230def99f875ad18866bc21a6eb5851b1ebf9f7fd8f`. The recorded eight-TU production compile remains successful; its object hashes are unchanged.

The updated integration note now points at the refreshed run-002 differential and explicitly calls out the ID 31 sentinel/mutant. The function record likewise retains the valid/invalid cases, unchanged `non_matching` ledger class, and producer/runtime limitations. I reviewed the frozen reports and objects; I ran no builds, tests, emulator, or guest interaction.

## Limits and recommendation

The helper checks the shared mode flag at `0x004650A8` and its counter at `0x004E3C58 + 4*id`; the availability flag used by the producer is a distinct address. This differential does not show that producer counter values are fresh or scheduled before the H2 caller, name physical controls, show safe input injection, include an IPS patch, or compare original and patched H2 runtime behavior. Recommend accepting this boundary correction and isolated helper evidence with those limits retained; keep the ledger label `non_matching`.
