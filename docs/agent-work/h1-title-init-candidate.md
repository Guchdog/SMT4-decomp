# H1 title initializer candidate handoff

Task `h1-title-init-candidate` reconstructed `0x001EB02C` as an isolated, readable C++ candidate and validated it against the pinned original ARM function with deterministic allocator and task-factory hooks.

- Candidate: [experiments/semantic_equivalence/h1_title_main_init.cpp](/C:/Users/altair/.codex/worktrees/semantic-equivalence-experiment/SMT4decomp/experiments/semantic_equivalence/h1_title_main_init.cpp)
- Runner: [tools/h1_title_init_experiment.py](/C:/Users/altair/.codex/worktrees/semantic-equivalence-experiment/SMT4decomp/tools/h1_title_init_experiment.py)
- Focused tests: [tests/test_h1_title_init_experiment.py](/C:/Users/altair/.codex/worktrees/semantic-equivalence-experiment/SMT4decomp/tests/test_h1_title_init_experiment.py)
- Function record: [0x001eb02c.md](/C:/Users/altair/.codex/worktrees/semantic-equivalence-experiment/SMT4decomp/docs/function-records/0x001eb02c.md)
- Final report: `build/agent-work/H1-semantic/h1-title-init-candidate/sleep-20261025-title-init/checks/final/report.json`
- Tested null and all 256 possible argument bytes; also seeded a nonzero existing global in three cases. All candidate/original comparisons passed, including allocation arguments, callback registration arguments, exact work bytes, and callee-saved state.
- Negative control changes only `+0x10` for non-null argument `0xA5`; checker caught the expected differing byte.
- Original image SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; original function slice SHA-256: `ec9c7b1d6e1c59d3db88187f2b573cfea1dc96467057700720122a2f7be5a1e1`.
- Source SHA-256: `a632f1d5ac1456b335eee208eea01fe653b056badc2fae4defc39dc28780a4ea`; object SHA-256: `53bdecdacc6fc14a5365647754e3785b9153ce7e1a19109070bb823345a2572a`; report SHA-256: `b16f9b3648552143903d6d9b466a5b92bf8f0ec5e3365a2bddccf5c558802a08`.
- Limitations: allocator/task factory are deterministic hooks; allocator success is assumed; no live H1 caller or game runtime was exercised. The first development counterexample was a reversed pair of CreateCalc stack callback words, fixed before final validation.
- Next: independent review, then integrator-owned caller/integration evidence if promoted.
