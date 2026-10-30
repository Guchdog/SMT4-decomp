# H2 script-step dispatcher source integration

## Result

Replaced `script_vm_func_0019dfbc` with typed C++ in
`src/engine/leaf_batch29_a.cpp` and updated the six assembly-caller declarations
to `(void*) -> s32`. The dispatcher reads the current method ID, resolves the
handler through the table at `0x0044DED0`, and calls it with the work pointer.
Callback results 0, 1, 2, and all other values follow the recorded branches in
the [function record](../function-records/0x0019dfbc.md).

## Source/object provenance

- Candidate source SHA-256:
  `b82456afa384ae14e75d1caa63c6443cad589e1383ab49844a7985d2241a71b8`.
- Runner SHA-256:
  `a658617e828525be916d0c58fcbd3490b3d656c98b375009418619b21bf959f0`.
- Focused test source SHA-256:
  `02554c8d393c2f0854b2cf340706b019e31b54f71619e5c44f00455e1a876def`.
- Production TU SHA-256:
  `eda60a6e0a3830bf187021ec0f3d0cbf69d5b3fb0ea32ed14a1650c68282ad46`.
- Production object:
  `build/agent-work/H2-semantic/h2-script-vm-step-runner/run-002/checks/compile-consumers/leaf_batch29_a_0/leaf_batch29_a.o`,
  SHA-256 `0dc95e41b5cb062ea9d30d15f6b70766565956f575d0b51fb20b887a910f8956`.
  Its extracted function is 128 bytes, relocation-free, and byte-identical to
  the candidate body (SHA-256
  `c0cbad2f317c22e16ea12159e32e8b13180ca5ad4df12af8d994f53f8508cd48`).
- The six caller TUs also compiled successfully. Their object SHA-256 values
  are in the private `compile-report.json` (SHA-256
  `02ea661f57c288a28ac93aae4ed654f4d687b040078061f9bb18b3c792982dbd`).
- Original span: 120 bytes. Production C++ body: 128 bytes. Ledger is
  `non_matching`; no IPS/code.bin patch was created for this helper.

## Validation

- `python -m unittest tests.test_h2_script_step_experiment -v` — 6/6 passed.
- Command:

  ```powershell
  python tools/h2_script_step_experiment.py --output build/agent-work/H2-semantic/h2-script-vm-step-runner/run-001/checks/final-differential-20261026
  ```

  Exit 0; report file SHA-256
  `ebb2f58ad9f659234c20d8dd96df26ea7118bd245536d10ebc03831e1174da91`.
  Five finite original-vs-C++ callback sequences matched in full work bytes,
  return values, PC, SP, callee-saved registers and callback counts. Directed
  expected-state checks cover result 0 terminal return 2, result 2 counter
  increments/return 1, result 1 loop/clear, other-result loop, and mixed
  sequences. The deliberately incorrect always-return-2 control is detected.
- The non-advancing callback returning 1 was stopped at the eighth callback
  entry on both implementations. Both remained in the dispatcher with equal
  state; this is an explicit bounded nontermination guard.
- The seven separate production/caller TUs compiled in the private compile
  report. No canonical build was run.
- Two preliminary harness attempts failed before the final run: first, the
  candidate object did not yet include the deliberately wrong control symbol;
  then the non-advancing-loop check used an equal instruction limit, which
  stopped the two differently-sized functions after different callback
  counts. The final runner includes the control symbol and stops at the same
  callback entry count on both sides; the final report was generated after
  these harness corrections.

## Limits and next action

Handlers and operation tables were synthetic. The experiment does not establish
real script contents, callback behavior, valid IDs for every caller, meaning of
state-2 results, UI cancel/confirm semantics, persistence, scheduler behavior,
or Azahar runtime equivalence. The C++ function is source-integrated but not in
the H2 IPS image because its body exceeds the original span. Independent review
is required before accepting the bounded source promotion; H2 remains open.
