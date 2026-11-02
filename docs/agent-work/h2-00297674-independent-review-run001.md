# Independent review: raw global word getter `0x00297674` — run001

## Recommendation

The frozen evidence supports the bounded raw-word getter reconstruction and the exact-slot caller comparison. The 20-byte compiled body has no relocations, returns through `BX LR`, and retains the original two dependent data reads and full 32-bit field value. In the caller harness, each candidate run uses the staged image created from the pinned original with only the getter slot replaced. The four prior-helper outcomes gate the getter as expected; when the gate opens, all seven getter values are covered. I found no concrete counterexample in the frozen report/source.

Proceed with bounded semantic integration/review. This does not establish real global-object lifetime, production value distribution, or emulator behavior.

## Frozen provenance and patch scope

All 22 input hashes in the packet recompute exactly. Key identities:

- Original image: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`
- Candidate source: `9d58cde6be83f61fac61601db72696f9defa591f93439349b4e4924dae9dd9e3`
- Production source: `e60a3333cb10f70784fcabdb753e218e534ffb7f3cee0160df442d24696acc71`
- Candidate object / production object: `1f72685b67b9d420da4bad2467e18d65b7fee7775f5165286de8b3ad922b8dd4` / `857958e88c81502be6bbcb17686b7dfd94964d2f4c7ca96ce8ee19b3ab8cb34b`
- Conversion report: `7253188e26361ecdc25df55800fc8970ce3628c17b5d238c3dcb9c3e43a190c1`

The original and reconstructed slots are both 20 bytes. The report records two changed bytes in that slot; its IPS SHA-256 is `15687233cc7d529337e4e9ecdbbe99a1694cbd6490f87bf3723c7ca2c3e36564`, staged image SHA-256 is `296a4f314a1f9efc923958d28a5300ed17dcad31e491eb0b2cd107f31b8beb3a`, and IPS roundtrip passes. The changed instruction/literal pair removes the original `+8` from the second load and changes the literal from `0x0043E188` to `0x0043E190`; together these preserve the effective pointer-slot read at `0x0043E190` while making the access direct. The ledger marks the byte-different implementation `non_matching`.

The original caller `BL` at `0x001EAFAC` resolves to the even ARM entry `0x00297674`. The compiled getter has no call relocations, enters in ARM state and returns with `BX LR`. Focused object hashes match the packet: production `leaf_batch21_b.o` is `857958e8…cb34b`, and the other focused dependent object `leaf_batch22_c.o` is `8460b770…17751`.

## Getter contract and direct cases

The candidate source reads the 32-bit pointer stored at `0x0043E190`, then reads the 32-bit word at pointer `+0x1C` and returns that word unchanged. It takes no arguments and makes no writes. There is no null guard or byte/boolean normalization. The report’s seven direct inputs are `0`, `1`, `2`, `0xFF`, `0x100`, `0x80000000`, and `0xFFFFFFFF`; all return the full input word, with identical pointer-slot/field read order, no writes, and matching register, stack, ABI and flag observations. The null-pointer fixture faults on both original and candidate after reading the pointer slot; this supports preserving the faulting dereference for this mapped fixture, not a universal host/OS fault guarantee.

All three mutation controls are caught: wrong pointer slot, wrong field offset, and byte-width return. Direct and caller reports both pass. The aligned synthetic pointer and selected field values do not establish actual object ownership, lifetime, concurrent mutation behavior, MMIO semantics, or every aliasing/alignment condition.

## Exact `TitleConfig_Calc` caller path

The runner builds `staged_image` from the pinned original image and replaces exactly the 20-byte getter slot with the compiled production body. For each caller case, `caller_run(image, ...)` is the original and `caller_run(staged_image, ...)` is the patched profile. Thus the state-2 caller remains the original `TitleConfig_Calc`; only the getter implementation changes. This is the key composition check, and it is correctly scoped.

The report contains 28 cases: four prior `0x0019DFBC` results (`0`, `1`, `2`, `0xFFFFFFFF`) crossed with the seven getter values. For prior results other than exactly `2`, all 21 runs skip the getter and keep configuration/call traces unchanged. For prior result `2`, each of the seven runs records getter entry at `0x001EAFAC` and the two data reads. Getter result `0` follows the original `0x002BDAC0(work+0x5C,1,0)` path, records its call, sets config byte `+4` to 1 and state to 3. Result `1` stores state 1; all other tested full-width values leave those state/config writes and call absent. Original and patched profiles match return, stopped/fault status, preserved registers, work/config bytes, service trace, getter reads and `0x002BDAC0` argument trace in every case.

The runner executes the original `0x002BDAC0` body on the zero path. Nested service dependencies remain Calc-harness boundaries. The prior `0x0019DFBC` result is scripted, not produced by executing that helper, and global/object pointers and values are synthetic. Therefore the tests prove the caller’s conditional composition under these supplied inputs, not natural reachability, live object lifetime, physical user decision semantics, or scheduler/runtime behavior.

## Limits and next action

No emulator run was performed; runtime is unverified. The report and static code establish a bounded getter and patched caller path only. Proceed with the semantic integration step while retaining the modeled prior-helper result, synthetic global/object setup, and nested `0x002BDAC0` service boundaries as explicit evidence limits.
