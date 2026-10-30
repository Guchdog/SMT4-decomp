# Independent review: H2 TitleConfig_Secondary candidate

## Decision

Accept the candidate as a supported experimental reconstruction of the isolated callback orchestration under the runner's explicit helper-entry models. Do not promote it as a production replacement or claim cleanup/task lifecycle equivalence yet. The callback’s scheduler timing, invocation count, task-state meaning, and workspace/resource lifetime remain unresolved; most cleanup and task helpers are trace-only in the differential. The production candidate is also 284 bytes versus the 224-byte original span, so an integrated patch requires explicit placement support.

## Instruction and candidate review

I compared the candidate with the pinned `0x002CAEF0` wrapper in `src/engine/leaf_batch32_c.cpp` and the instruction-level contract in `docs/agent-work/h2-secondary-contract.md`:

| Original behavior | Candidate review |
|---|---|
| Load `g_TitleConfigWork` from `0x0044E2D0`; no null guard; ignore callback `r0`. | Reads the absolute global at entry, does not dereference the incoming context, and keeps the invalid/null-global path outside its modeled domain. |
| Store byte 1 at work `+4`. | Performs the same unconditional byte store. |
| For signed halfword `+0x1A`, skip if nonpositive; otherwise call `0x002B9008`, reread the halfword, increment local count, and repeat while reread value is greater. Then do the same at `+0x24` with count reset. | Uses two independent loops, signed volatile halfword rereads, and count reset. For stable signed values in the tested domain, the call counts and sequence agree with the original. The second-loop count is not coupled to the first. |
| If `+0x154` is non-null, call `0x002A755C`, then clear it. Then conditionally release/clear `+0x14C`, followed by `+0x150`. | Keeps the same guards, helper order, and clear-after-call order. |
| Call `0x002BF41C(work->calc_task)`; when nonzero call `0x002C45B8(work->calc_task,0)`. | Uses the predicate’s return as the same gate and passes state zero to the task helper. It does not translate this into a presumed free/delete operation. |
| Reload the global; if non-null release its value with `0x002C4360`, then clear the global. | Reloads the global after the task helper and preserves release-before-clear ordering. |

The C++ ABI shim is `void candidate_002caef0(void*)`: it consumes no callback context and makes no return-value claim. The original saves/restores `r4-r6`, `lr`, uses no local stack, and returns via `pop {...,pc}`. The harness checks `r4-r11`, SP, and `d8-d15` preservation against the entry state; it also checks the caller-owned stack bytes at/above entry SP. It records final `r0` only diagnostically, which is appropriate for the declared void callback. The candidate has no unresolved ELF relocations in the reviewed object.

The `0x002B9008` call is retained even though it does not decrement either TitleConfig counter. The report and contract say its original body conditionally decrements a different manager halfword at `global+4 object+0x64A` only when the signed value is above 10. The runner models that direct side effect for 9/10/11/12 and the callback’s loop call; this matches the documented helper body. The candidate’s `s16` call signature sign-extends the reread counter in `r0`, as the original loop does at its direct call boundary. That incoming value is not part of the helper’s semantic effect, but it is included in normalized trace comparison.

## Differential and controls

The reviewed pre-existing report is `build/agent-work/H2-semantic/h2-secondary-candidate/run-001/checks/unittest-21092-1792986562456255900/report.json`, SHA-256 `97cc16474088a7a37eb45ea45cec489fbbd78b20c34634343e20136f2b707cce`. It uses the pinned image SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, candidate source SHA-256 `ce1d0376d136fd0d20c63bdc288d3535a06e91a36ca78ccb3a5aa88187877901`, compiler Clang 23.1.3 targeting ARMv6K hard-float, and object SHA-256 `2d4c59ec70b0d9686a031c2429e78c16e8cbc4a39a17979fba937d4ba4d87e25`. The object reports 284 bytes for `candidate_002caef0` and no relocations. These are experiment identities, not production-source or integrated-patch identities.

All 17 directed cases passed with no first counterexample:

- Both counters zero; each counter independently negative, one, and four; and both loops independently positive (`2` and `3`).
- Each nullable cleanup slot (`+0x154`, `+0x14C`, `+0x150`) independently zeroed; task-registration predicate false and true.
- Manager halfword values 9, 10, 11, and 12, with one first-loop helper call, to exercise below/at/above the helper threshold.

The runner compares fault/return-to-sentinel, preserved registers/SP/VFP, stack bytes at and above entry SP, full 0x158-byte work image, global pointer, manager halfword, normalized helper addresses/consumed arguments/order, and the set of watched write addresses. It detected both declared negative controls on `both-loops-distinct`: omitting the last first-loop call changed the helper trace; reversing the two resource-release calls changed the trace order.

## Evidence limits and follow-up

The positive differential supports the callback’s direct orchestration only under a valid, non-null synthetic work object, stable test fields, the exact modeled `0x002B9008` direct manager effect, a configurable task-registration return, and trace-only `0x002A755C`, `0x002C4360`, and `0x002C45B8` helpers. It does not execute their nested script-list cleanup, allocator/release internals, or task/scheduler state propagation. The write hook compares a watched-address set and final memory, not the sequence of stores relative to a helper’s internal observation; clear-after-call order is established by source/disassembly review, not by a helper model that observes work bytes during the call.

The matrix exercises ordinary signed values but not `INT16_MIN`/`INT16_MAX`, aliasing between work slots and helper-owned objects, work-null failure, counter mutation by another concurrent actor, or reentry. The source’s volatile rereads retain the original possibility of a changed counter; the current fixture’s helper does not mutate the title work, and scheduler/concurrent changes are not tested. Under a stable signed halfword, the loop terminates within the representable positive range. Treat races, invalid pointers, and callback overlap as outside this evidence.

The checked-in initializer registers this address as the secondary calculation callback, but that establishes tuple forwarding only. No caller/scheduler test proves whether it runs after the primary Calc returns `-1`, how many times it runs, or when task/work/resource memory becomes invalid. No edits, runtime, emulator, RSP, or user input were performed for this review. The CSV row `0x002caef0,224,matching,engine,engine_func_002caef0,src/engine/leaf_batch32_c.cpp` remains a truthful classification of the original checked-in body and was not changed.

Before any production promotion, independently establish secondary callback lifecycle and task/work lifetime in a caller-composed scenario. Then compile the actual production TU, resolve the candidate’s 60-byte excess over the original span with a reviewed placement map, verify final-address behavior alongside Calc/initializer/Draw using a reproducible merged patch, and keep runtime/persistence claims separate. Existing evidence does not warrant changing the ledger now.
