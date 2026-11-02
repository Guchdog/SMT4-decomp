# Independent review: `0x002AE6B0` control-code predicate

## Decision

The typed predicate is supported for semantic promotion as a bounded, stateless helper. Keep its ledger class `non_matching`: the candidate is the same 24-byte span but has different bytes. The exhaustive halfword differential, selected 32-bit probes, and boundary mutations strongly establish the unsigned interval rule. Caller evidence is useful but partial: it composes through original `0x00286928` and `0x002B787C` bodies with deterministic hooks for the dispatcher’s unrelated services, and its imported harnesses are not included in the run001 packet hashes. This does not establish runtime call frequency or natural H2 reachability.

## Identity and contract

The packet pins the original image at SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; all 12 declared input hashes match. The 24 bytes at `0x002AE6B0` hash to `39132c786b4f14598c98e9a6c68661fbc2a16fd0d449099dc040eafd2f88b29f`. Their ARM instructions subtract `0xF800`, subtract one, compare against `0x8F`, and return 1 below the unsigned bound or 0 otherwise. Modular subtraction means the result is 1 exactly for unsigned inputs `[0xF801, 0xF88F]`, inclusive, over the full 32-bit domain.

The current C++ is:

```cpp
extern "C" __attribute__((minsize)) uint32_t engine_func_002ae6b0(
    uint32_t code) {
    return static_cast<uint32_t>(code - 0xf801u) < 0x8fu ? 1u : 0u;
}
```

It returns the boolean word in `r0`; it has no memory accesses, stack use, or callee-saved register writes. The declaration is `uint32_t engine_func_002ae6b0(uint32_t code)`. The candidate hex in the report hashes to `d6476e69b5213740930513337c57f5caec10b08cb9d54e59fc6c51e485332d58`, has length 24, and differs from the pinned original. The source hash matches the report and packet value `2a59d7aeba7fa2f9f70046b2e9dea87a2e65471a0069886e3b84e1ce2daf58d3`.

## Differential and mutation evidence

The report claims 66,057 distinct direct inputs: all 65,536 halfwords, 18 directed 32-bit values, and 512 deterministic 32-bit draws from seed `20261102`. I inspected the runner’s construction and independently reproduced the set cardinality; the 512 generated random values are unique and outside the halfword domain. Return values are compared between pinned ARM and the compiled body, then checked against the interval formula. The runner also records no guest writes, unchanged SP, and unchanged `r4-r11`; it seeds `r1-r11`, correctly checks the callee-saved subset, and allows caller-saved `r1-r3` to differ. The original and candidate snippets use no VFP instructions. These observations support the stated ABI/memory claim for the tested calls.

Both mutation controls are well targeted: changing the upper test from `< 0x8F` to `< 0x90` makes `0xF890` incorrectly true; changing the subtraction base from `0xF801` to `0xF800` makes `0xF800` incorrectly true. The report records each expected original 0 versus mutant 1 and `detected: true`. This review did not compile, run the experiment, or independently execute the mutants.

## Caller composition and provenance limit

For selectors 11 and 19, the runner places only the predicate’s compiled body at `0x002AE6B0` in the pinned image, then executes original `0x00286928` and original `0x002B787C` with an initialized four-record line table. The line-count path reaches the predicate and the parent consumes count 2 at `object+0x20`. The harness compares the full collected caller state, event trace, writes, return state, and completion flag for original versus converted image before the report emits the concise `done`, helper-event, and count fields. The fixture has deterministic hooks for other services called by `0x00286928`; it is a controlled composition, not a natural runtime trace.

One reproducibility limit: `h2_ae6b0_experiment.py` imports `tools/h2_2b787c_experiment.py`, which in turn imports `tools/h2_86928_experiment.py`. The run001 packet pins the top-level predicate runner and report but not those transitive caller harnesses. I inspected the current harness code and verified that it patches only the predicate for these two compositions; the exact caller-harness versions used to generate the report are not established by this packet. Their current SHA-256 values are `1409ba1d0e1784ee6cc6e547c55cf04a40cddb5bc599fcd84a4b8b6a7272e8c6` and `e41a245675dd1ad8282f83733d8deaa3d0aabb2d3858b0e6a9ce782bff43c040`, respectively. Treat the caller result as reported and code-path corroborated, with transitive provenance incomplete; pin those dependencies if this specific caller result must serve as a reproducible promotion gate.

## Evidence status and next action

- Compiled body: **reported passed**, 24 bytes, no relocations, no build rerun by this reviewer.
- ARM differential: **reported passed**, 66,057 direct inputs and two boundary mutants; strong exhaustive coverage of the 16-bit input domain plus the sampled 32-bit domain.
- Caller: **partial**, two controlled selector compositions through original caller/line-count bodies; other dispatcher services are stubbed and transitive harness versions are not packet-pinned.
- Runtime: **not run** for this helper. The caller composition does not establish natural game runtime reachability.

Recommendation: proceed with the bounded semantic replacement and preserve `non_matching`; do not claim byte identity, runtime reachability, or whole-H2 equivalence. The direct helper evidence is self-contained enough for its simple unsigned predicate. Keep caller composition marked partial until its imported harness inputs are frozen in a future reproduction. The runner report is `build/agent-work/H2-semantic/h2-ae6b0-convert/run001/report.json`, SHA-256 `9452fb6065ec05bb21a025fabf78ce87d01ba19179e53dbea34fa124ca104b75`.

## Review actions

- Recomputed SHA-256 for all packet-declared inputs, the original 24-byte function slice, and candidate hex; verified the pinned ARM instructions and interval arithmetic.
- Read the C++ declaration/body and differential runner, including input generation, register/memory observation, negative controls, and composition setup/return assertions.
- Read the JSON report, current predicate function record, line-count function record, and ledger row.
- No compiler, build, test runner, or emulator was run.
