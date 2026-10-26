# Independent review: H1 title initializer

Task: `h1-title-init-independent-review`; candidate `0x001EB02C`.

## Review result

**PASS for the isolated constructor contract and reported ARM differential.** I
found no concrete mismatch in the candidate's work layout, nullable argument
handling, allocation arguments, or task registration protocol when checked
against the pinned original listing and the report. **Integration remains
partial:** the allocator and task-factory implementations are hooks, and no
real H1 caller or game runtime was exercised.

## Independent checks

- Pinned `code.bin` SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- Original `0x001EB02C` slice: 524 bytes, SHA-256
  `ec9c7b1d6e1c59d3db88187f2b573cfea1dc96467057700720122a2f7be5a1e1`.
- Candidate source SHA-256:
  `a632f1d5ac1456b335eee208eea01fe653b056badc2fae4defc39dc28780a4ea`.
- Candidate object SHA-256:
  `53bdecdacc6fc14a5365647754e3785b9153ce7e1a19109070bb823345a2572a`.
- Final experiment report SHA-256:
  `b16f9b3648552143903d6d9b466a5b92bf8f0ec5e3365a2bddccf5c558802a08`.

I decoded the pinned initializer and compared it with
`experiments/semantic_equivalence/h1_title_main_init.cpp` and
`include/camp/title_flow.h`. The constructor calls allocation unconditionally
with `r0-r3 = 0x10000, 0x100, 0, 0xA0` and stack word `1`; stores the returned
work pointer at `0x0044E300`; initializes the candidate's declared offsets;
and clears `+0x10` only when the input pointer is non-null. Its fixed-size work
structure is `0xA0` bytes. The candidate leaves the same untouched allocator
bytes untouched.

The task-registration arguments match the original's AAPCS layout:

- CreateCalc: name `TITLE C`, priority `2`, zero `r2/r3`, stack words
  `[0x001E989C, 0x002CA6F4, 0]`; the returned task handle is stored at work
  `+0`.
- CreateDraw: names `TITLE UDrawLeft`, `TITLE UDrawRight`, `TITLE D`, priorities
  `0x76`, `0xD4`, `0xE7`, callbacks `0x0020FD5C`, `0x0021F36C`, `0x002CA7A8`,
  and stack words `[callback, 0, 0, task_handle]`.

The final report covers null and all 256 byte values, then three cases with a
preexisting global pointer. It compares the entire `0xA0` work region, the
global pointer and recorded service-call arguments, and the callee-saved
register/SP/VFP state. Its wrong `+0x10` control is detected at the expected
byte. I inspected those comparison paths; I did not rerun compilation or the
ARM suite because this review packet assigns zero compiler slots.

## Limits and next action

The differential hooks record the allocation/task-factory call protocol and
return deterministic pointers; they do not validate heap behavior, scheduler
internals, or task execution. Allocation failure is unchecked in the original
and assumed absent in the candidate domain. No actual caller-window, patched
image, or runtime scenario was compared. Keep the candidate's status scoped to
the isolated constructor; before integration, verify the task-factory address
bindings in the production build and run the assigned H1 caller/runtime
scenario.

The implementation packet's provenance checker was also queried read-only, but
now reports `Task assignment or scope changed since dispatch`, consistent with
the coordinator having closed that task. This is a workflow-state result, not
a candidate discrepancy.

## Structured review payload

```json
{
  "task_id": "h1-title-init-independent-review",
  "review_result": "pass",
  "scope": "isolated 0x001EB02C constructor and pinned ARM differential",
  "integration_status": "partial",
  "reference_image_sha256": "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558",
  "original_function_sha256": "ec9c7b1d6e1c59d3db88187f2b573cfea1dc96467057700720122a2f7be5a1e1",
  "candidate_source_sha256": "a632f1d5ac1456b335eee208eea01fe653b056badc2fae4defc39dc28780a4ea",
  "candidate_object_sha256": "53bdecdacc6fc14a5365647754e3785b9153ce7e1a19109070bb823345a2572a",
  "candidate_report_sha256": "b16f9b3648552143903d6d9b466a5b92bf8f0ec5e3365a2bddccf5c558802a08",
  "checks": [
    {"argv": ["python", "tools/split_asm.py", "--addr", "0x001eb02c"], "exit_code": 0},
    {"argv": ["python", "-c", "hash pinned image and 0x001EB02C slice"], "exit_code": 0},
    {"argv": ["Get-FileHash", "experiments/semantic_equivalence/h1_title_main_init.cpp,tools/h1_title_init_experiment.py,tests/test_h1_title_init_experiment.py,build/agent-work/H1-semantic/h1-title-init-candidate/sleep-20261025-title-init/checks/final/report.json,build/agent-work/H1-semantic/h1-title-init-candidate/sleep-20261025-title-init/checks/final/title_init.o", "-Algorithm", "SHA256"], "exit_code": 0},
    {"argv": ["python", "tools/agent_workflow.py", "check-handoff", "--packet", "<h1-title-init-candidate>/task.json", "--handoff", "<h1-title-init-candidate>/agent-handoff.json"], "exit_code": 1, "reason": "Task assignment or scope changed since dispatch"},
    {"argv": ["python", "-c", "verify review packet input hashes"], "exit_code": 0}
  ],
  "evidence": {"compiled": "passed_by_implementer_and_independently_inspected", "arm_differential": "passed_by_implementer_and_independently_inspected", "caller": "not_run", "runtime": "not_run"},
  "concrete_defects": [],
  "limitations": ["Deterministic allocator/task-factory hooks only", "Allocator failure is outside tested domain", "No live caller or game runtime"],
  "next_action": "Keep candidate bounded to isolated constructor semantics; verify production service bindings and add real H1 caller/runtime evidence before integration approval."
}
```
