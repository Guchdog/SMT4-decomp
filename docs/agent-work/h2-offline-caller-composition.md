# H2 offline caller-composition evidence

This task-local runner composes the pinned MainTitle State-9/10 code with the
H2 initializer candidate. It starts independent Unicorn machines from the same
pinned `code.bin`; the patched machine changes only the initializer entry
`0x002F4CA0` to branch into the compiled candidate. Both sides execute the
original readiness body at `0x002FC0EC` and the original MainTitle callback.

The directed cases cover the baseline config bytes, a second distinct eight
byte config block, and the `flag_7c` transition gate. For each transition case,
the task-active boundary returns active then inactive, so the real State-10
caller remains pending once and then runs its reset path. The runner records
raw helper arguments, stack words, call sites and VFP scratch values. Its
differential compares caller state and work/config bytes, return/PC/SP,
callee-saved `r4-r11` and `d8-d15`, ordered observed boundary calls, and the
meaningful process-factory tuple words. Candidate instruction layout changes
some call-site addresses and caller-saved scratch registers; those remain in
the report as diagnostics rather than equivalence requirements. The factory
tuple assertions check Calc's primary and secondary callbacks plus work
context, and Draw's callback, reserved words and Calc task handle.

The reset assertion pass checks consumed arguments at each observed reset HLE
call site. `Sound_PlaySE(s32 se_id)` at `0x002B8B78` consumes `r0` only; the
pinned initializer call sets `r0=0x99`, and State-10 reset sets `r0=0x9f`.
The original callee body saves `r0` in `r5` and uses that value; its `r1`
register is not an incoming parameter and is loaded/overwritten before later
use. Raw `r1-r3` remain in the trace, including the original/candidate `r1`
scratch discrepancy. Touch registration, cursor mode, environment load, and
model visibility assertions check their consumed caller arguments as recorded
at their pinned MainTitle call sites.

The wrong-primary-callback negative control mutates the candidate's unique
Calc callback literal from `0x001EA928` to `0x001EA92C`. It fails both the
explicit expected-tuple assertion and original-versus-mutant tuple comparison.

The generated evidence is in the task-local ignored output root:
`build/agent-work/H2-semantic/h2-offline-caller-composition/run-001/checks/final-5/report.json`.
It records three passing directed cases and a detected negative control.

## Scope limits

Allocator, process factory, task-active lookup, sprite/resource/cursor setup,
Sound_PlaySE internals, transition, touch registration, cursor mode, environment load
and model visibility are explicit matched HLE boundaries. The runner compares
registration and handle linkage but does not execute either registered Calc
callback. It covers only State 9, State-10 pending, ready/reset and the
`flag_7c` gate. State-1 input/cursor behavior, editing, persistence, profile
behavior, mapper behavior, Azahar/RSP execution and whole-game equivalence are
not established. Reset HLE consumed-argument assertions do not establish those
helpers' internal behavior.
