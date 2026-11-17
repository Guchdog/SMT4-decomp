# H18 MOV r0,r0 stub experiment

Prepared a quarantined instruction-effect fixture containing 21 typed empty C++ stubs (not valid function candidates) in `experiments/semantic_equivalence/h18_nop_stub_candidates.cpp`, plus a dedicated Unicorn runner and focused test. No production source or shared ledger was changed.

The runner pins each ledger row and revision, verifies the original is exactly the single ARM instruction `mov r0, r0`, and compares all GPRs (including SP/LR), NZCV, RAM/stack bytes, read/write footprint, and continuation. Since the original has no return branch, it stops at `address+4`; the candidate's LR is set to the same sequential continuation. The TU also includes four intentionally incorrect controls: clobber r0, clobber r1, alter flags, and write memory.

Validation: 68 cases/address/seed, 1,428 comparisons per run, seeds 7 and 20261024. Both instruction-effect reports passed with all negative controls detected; they do not prove whole-function equivalence. Candidate output bytes differ; no matching claim. Test command: `python -m unittest tests.test_h18_nop_stub_experiment -v` (passed).

Critical finding: all 21 entries are followed at address+4 by meaningful ARM instructions (including prologues, stores and calls), so they are not standalone no-op callbacks. The harness uses a synthetic continuation solely to isolate the MOV effect. Empty stubs would return where the original sequence falls through, changing behavior. Caller argument/return types and actual function boundaries remain unresolved. The fixture must not be promoted; the task needs re-scoping to whole functions or a proven call-through contract.
