# `0x002B85BC` typed profile-selector conversion

## Result

Replaced only the 472-byte raw ARM body in `src/engine/leaf_batch44_c.cpp` with
typed C++. The compiled candidate is 372 bytes and fits the original slot. It
preserves the full-width request, ordered old/new profile lookups, six-slot
address stride, the three old/new profile-state branches, the conditional
two-slot calls, the final manager-object reload, cleanup store order, and raw
return values. All five direct dependency addresses remain external calls.

### Status-call correction

The static contract note initially understated the status-8 branch. Pinned ARM
at `0x002B8644`, `0x002B8650`, and `0x002B8658` calls `0x002A8A8C` three times
when the reloaded status is 8. Status 7/9 calls the helper once at
`0x002B8634`, reloads the byte, and, if the new value is 8, then takes all three
status-8 calls (four total). With unchanged bytes, 7/9 produces two calls, 8
produces three, ordinary nonzero status produces one, and zero produces none.
The candidate and a helper-mutated 7-to-8 differential case preserve that
behavior. The coordinator corrected the shared static contract accordingly.

## Offline evidence

Run `build/agent-work/H2-semantic/h2-profile-selector-002b85bc-convert/run002/checks/final5/`:

- 9 direct comparisons passed: old lookup null, new lookup null, all three
  profile-flag branches, statuses 0/1/7/8/9/other, helper-mutation from status 7
  to 8, both two-slot modes, final manager pointer reload, and null-object fault.
- Both original caller slices passed: TitleConfig request `0x99` and nested
  callback request `0xDC`. These are explicit fixtures and deterministic hooks,
  not observations of natural callback reachability.
- All 5 negative controls were detected: altered slot stride/loop mapping,
  wrong status clear, wrong status-service multiplicity, changed two-slot
  service arguments, and changed cleanup value.
- Candidate body: 372/472 bytes; 11 ARM `BL` relocations to five distinct even
  ARM targets; IPS replay passed; no changed bytes outside the slot.
- The null-object case faults on the same unmapped byte read at `0x4C9` in both
  original and candidate. On normally returning cases the runner compares r0,
  SP, callee-saved registers, full fixture memory, ordered stores, and dependency
  calls/arguments. Call-boundary SP alignment is recorded in each event.
- The runner compiled the affected `leaf_batch44_c.cpp` TU with the project
  ARMv6K Clang configuration. This is a focused TU compile, not a full build.

The final machine report SHA-256 is
`5cd2e51783ff7d64ebf65e889c61e9996214cea94f2cb1fc04eca934b3f9a7f3`. The
staged image SHA-256 is
`1c90f45173a6847abf88f87ea2495de60c6ed2be64e3bbb571822c65b29e7904`; its
single-slot IPS SHA-256 is
`15ad28afb4e943e9adc9f1664c7c72bd811869f89746e0f6d453e74f5f73a676`. The
compiled object SHA-256 is
`ab280f5c40c573ae14a4b648a91a190608e5fbcd76967bff1340845fbb2aea91`.

## Evidence boundaries

Direct selector and caller tests use deterministic hooks for
`0x002AEA28`, `0x002BF030`, `0x002A8A8C`, `0x002BDAC0`, `0x002AA268`, and the
wrapper's remaining service calls. They validate the selector's call sequence,
arguments, raw returns, and fixture-visible stores in the modeled domain. They
do not validate the helpers' transitive effects, live TBB/profile data, manager
lifecycle, concurrent mutation, persistence, audible output, or natural runtime
reachability. The null-object read-fault fixture is one explicit fault case;
other invalid mappings and alias patterns remain unsupported. No emulator or
runtime test was run.

The production ledger was not edited. The typed source differs from the pinned
bytes, so the coordinator should reconcile the function's classification and
promotion status after independent review rather than infer a ledger update
from this experiment.

## Commands

```text
python -B tools/h2_profile_selector_experiment.py --out build/agent-work/H2-semantic/h2-profile-selector-002b85bc-convert/run002/checks/final5
exit: 0
```

The runner compiled the affected TU, resolved/rebased all final-VMA ARM branch
relocations, staged an IPS, and ran the direct/caller differentials and
mutations in sequence. It wrote the complete command and result details to
`build/agent-work/H2-semantic/h2-profile-selector-002b85bc-convert/run002/checks/final5/report.json`.
