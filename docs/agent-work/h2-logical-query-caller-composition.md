# H2 logical query caller composition

The runner composes the pinned `TitleConfig_Calc` (`0x001EA928`) and its real
`camp_func_002C1830` dispatcher with the original helper bodies or the typed
mode-0/mode-1 C++ helper bodies. It compares original Calc/original helpers,
candidate Calc/original helpers, original Calc/typed helpers, and candidate
Calc/typed helpers. It does not mock `logical_query` as a return-value service.

The corrected run passed 43 scenarios and 172 absolute execution gates. Every
baseline and candidate execution had no Unicorn fault, reached the return
sentinel, and preserved `r4-r11`, SP, and `d8-d15` at their seeded values. The
real Calc caller reached mode-0 query IDs
`4`, `3`, `0xD`, and `0xC`, and mode-1 IDs `9`, `0`, and `1`. These include both
fallback branches, a positive primary mode-0 pulse, the mode-1 ID-9 branch,
and positive ID-0/ID-1 transitions. The runner records wrapper argument pairs
and helper entry `(mode,id)` pairs, and compares return, fault/stop, PC, SP,
callee-saved GPR/VFP state, work/config bytes, and deterministic service traces.
The three candidate variants matched the pinned Calc plus original query
helpers. The wrong-counter mode-0 helper in the fallback-D case was detected
through a work-state difference. The output report records the absolute gates
per scenario and the negative-control difference.

The mode-0 and mode-1 C++ bodies extracted from the freshly compiled candidate
objects are byte-identical to the existing compiled production symbols:
136 bytes for `ui_func_002b902c` and 68 bytes for `ui_func_002bffbc`, both without
relocations. The Calc candidate was compiled and its local text relocations
were rebased into the runner's injection page. Original `0x002C6C10` remains a
mode-0 dependency.

The inputs to the helper tests are seeded counter words derived from each
scenario's requested logical outcomes. This establishes dispatch and caller
composition for those values; it does not exercise the counter producer,
scheduling, physical button meanings, keyboard/mouse event delivery, profile
state, IPS placement, or Azahar. Non-input Calc service boundaries retain the
same deterministic HLE models as the existing Calc runner. Runtime evidence is
`not_run`.

Focused tests:

```powershell
python -m unittest tests.test_h2_logical_query_caller_composition -v
```

Differential command:

```powershell
python tools/h2_logical_query_caller_composition.py --output build/agent-work/H2-semantic/h2-logical-query-caller-composition/run-004/checks/caller-composition --code extracted/exefs/code.bin
```

Final report SHA-256: `f7a2f37419620b26951f36cc7fa367d30031b0fdf43786b5e0b7a495ea40475f`.
The report and structured handoff are under
`build/agent-work/H2-semantic/h2-logical-query-caller-composition-fix/run-001/`.
