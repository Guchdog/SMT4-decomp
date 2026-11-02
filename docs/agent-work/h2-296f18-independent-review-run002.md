## Run002 follow-up: refreshed caller assertions (2026-11-02)

I reviewed the refreshed offline report at
`E:\SMT4decomp-evidence\h2-296f18-run005\report.json` (SHA-256
`FEC753EF426355DFA8D39C2E09DD0A1D6DDB49381F9F92298FEEE02F3C986E58`). The
same runner and seed were reproduced inside the repository at
`build/agent-work/H2-semantic/h2-cursor-axis-setup-00296f18-convert/run002/checks/coordinator-seed-20261130/report.json`
(SHA-256 `2084459247d927b20f8b9b43c93f68c2568ccb5ed15ee05ea7eb897d0458b681`).
All compared semantic/result fields match; only output-path/compiler-argument
metadata differs. The report records 61 direct cases, three detected mutation controls, a matched first-store
boundary fault, a 68-byte body in the 72-byte slot, zero relocations, and the
four even ARM call targets. No counterexample appears in the reported direct
or actual-caller comparisons.

The previous caller-coverage objection is closed. The runner now requires the
exact dynamic calls in both original and staged setup executions:
`(0x0029FBC4, cursor, 3, 3)` and
`(0x0029FC44, cursor+0x28, 1, 1)`. It also asserts all ten words in each final
0x28-byte axis record against explicit values. The expected packed words encode
the pinned ID sequences: axis0 `(6,5,32,32,15,14,32,32)` and axis1
`(3,4,32,32,12,13,32,32)`; remaining words cover zeroed fields, dimensions,
threshold/count, and index/offset. The report's final records have axis0
`(width,start,threshold,count)=(3,1,3,3)` and axis1 `(1,1,1,1)`, with both
index/offset pairs zero. The caller run also compares the full block, ordered
writes, preserved registers, stack pointer, return, and fault between original
and one-slot staged images.

Correct the conceptual/documentary distinction in
`docs/agent-work/h2-001ff3c4-contract.md`: `0x00296F18` itself initially writes
constant 2 at axis `+0x14`, but the complete pinned `0x0029FAE8` setup path
later overwrites axis0 `+0x14` with 1. Thus the final state produced by that
caller has `axis0.start=1`, as does axis1. The contract's `start=2` is an
intermediate helper output, not the final setup state. The run005 expected words
match the final pinned caller output; the earlier run001 static review text
above that describes start 2 as the resulting state is superseded by this
addendum.

Recommendation: the refreshed runner now supports bounded semantic approval
for `0x00296F18` over its direct cases and the exercised original H2 setup
path. This does not establish the rest of the TitleConfig lifecycle, other
setup helpers, runtime reachability, input scheduling, or behavior outside
aligned mapped ordinary RAM. Promotion still requires the coordinator-owned
truthful ledger classification for non-identical compiled bytes; no source,
runner, ledger, or board files were edited for this follow-up.
