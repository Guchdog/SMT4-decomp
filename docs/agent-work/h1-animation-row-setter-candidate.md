# H1 animation row setter candidate handoff

The experimental C++ candidate models pinned entry `0x002BDAC0` as a
row-driven state initializer for an opaque object. It does not assign a
stronger engine object type. Original entry extent is 108 bytes through
`0x002BDB2B`; it returns at `0x002BDB0C` for a null table and at `0x002BDB28`
after row initialization. H1's caller in `0x002BF9F0` calls this target at
`0x002BFB48` and `0x002BFB78` with object, animation word, and signed entry
byte arguments.

The final private original-versus-candidate run passed 9/9 fixtures: null table,
two row modes, full-width mode `0x100`, 12-byte row stride, negative row index
with valid preceding row storage, signed coordinate extremes, and the observed
null-object fault. A compiled mutant omitting the `+0x86` clear was detected by
synthetic memory mismatch. The final report's `first_mismatch` is `null`.

First development run `run-01` reported a stack mismatch on otherwise matching
valid-pointer cases because it compared temporary bytes below SP, which the
candidate compiler used for private spills. This was a harness projection
issue, not a caller-visible difference. `run-02` compares SP and caller-owned
stack at/above the entry SP, while still comparing all object memory and
callee-saved registers; all cases then pass. The runner, candidate source, and
final test preserve explicit valid-pointer limits. First-run report SHA-256:
`26a4aa963662591d095a1c620a33875a349bf66d02aa651762b365008716f1f9`; runner
exit 1, first report mismatch `nonnull object with null table returns
unchanged` / `stack differs`. The first direct-entry null-object case matched
the observed invalid-pointer fault on both executions.

The function body is not integrated and the `matching` ledger status is
unchanged. Caller support is static only. Null-object execution is undefined
for the C++ candidate and is recorded only as both implementations faulting in
Unicorn. Aliasing between row/table memory and the object, invalid pointers,
arbitrary indices, real H1 object initialization, and runtime behavior are
unsupported. The original helper's call argument flow does not establish live
asset selection or object lifecycle.

Final private report and linked candidate:
`build/agent-work/H1-semantic/h1-animation-row-setter-candidate/overnight-20261025-animation-row-setter/run-02/`.
Runner and focused test commands, exits, hashes, and explicit limits are in the
structured handoff for this task.
