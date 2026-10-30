# H2 TitleConfig_Draw candidate

## Result

Implemented an editable experimental reconstruction at experiments/semantic_equivalence/h2_draw_candidate.cpp and an isolated ARM differential runner at tools/h2_draw_experiment.py. The function receives and ignores its task callback argument, returns zero, and preserves the observed callee-saved state. Direct state reads and cache writes are recorded in docs/function-records/0x002cafd0.md.

## Evidence

The final run is build/agent-work/H2-semantic/h2-draw-candidate/run-001/checks/final/report.json. The original and compiled candidate agreed in 44 of 44 controlled callback cases. Coverage includes zero and negative row bounds; three active selected rows; touch results 1, 2, and 6 on row/decrement/increment/special handle offsets; inactive rendering; dirty and matching render-cache paths. The deliberately incorrect TBB row stride was detected as a helper-trace difference.

The runner compares ordered helper and callback calls with arguments, work and config bytes, cache bytes, return and stop/fault/PC state, and preserved registers, SP, and d8-d15. Four focused Python unit tests pass. This is isolated differential evidence under explicit mocks; it is not caller or runtime evidence.

## Limits

Cursor, TBB, layout, formatting/font, panel/sprite, render-value, and touch helpers are deterministic mocks. The indirect cache callback is also a controlled hook. Visible label meanings, actual touch meanings, real resource contents, initializer-created state, scheduler/calc interaction, persistence, Azahar behavior, and whole-game equivalence are not established. Nonpositive row counts are controlled helper outputs, not claimed user-reachable states. Malformed cursor indices and arbitrary memory layouts are outside the tested domain.

## Next action

Request independent source/contract review. If accepted, use the real initialized caller and loaded resource/helper state to design a bounded draw-task original-versus-patched scenario before any production promotion.
