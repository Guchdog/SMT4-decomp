# H18 paired script word getters: implementation handoff

Implemented isolated typed C++ candidates for `0x002345f0` and `0x002345fc`, with focused tests and family-specific original-vs-candidate ARM/Unicorn evidence. The originals are complete 12-byte leaves. Contracts, limitations, run paths, and caller addresses are recorded in the per-function records and structured handoff.

TDD evidence: before writing the candidate TU, `python -m unittest tests.test_h18_script_word_getters_experiment` failed at import with `ModuleNotFoundError: No module named 'tools.h18_script_word_getters_experiment'`, the expected missing experiment module. After implementation, that exact focused test command passed (3 tests). Fresh differential runs passed at seeds 7 and 20261024 (24 cases per address per seed, two caller windows, four detected controls).

Important limitation: generated C++ loads can narrow the original halfword access to a byte access after masking. In aligned ordinary RAM the compared full machine state, memory image and writes agree, while read footprints differ. This work does not establish MMIO/read-width equivalence and must not be promoted outside the stated domain without review. Game runtime and full caller composition were not run.
