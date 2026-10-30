# H2 secondary callback and cleanup contract

Status: static contract research against the pinned US v0.1.0 ARM image and the checked-in title workspace/caller. No candidate build, differential run, caller execution, emulator, or runtime test was performed.

## Identity and boundary

`TitleConfig_Secondary` is the ARM callback at `0x002CAEF0` (224 bytes; checked-in wrapper `src/engine/leaf_batch32_c.cpp:3578`). `include/camp/title_flow.h:241` declares it as the secondary calculation callback (`CreateCalc a5`). The initializer at `src/camp/title_flow.cpp:312` passes its address as the second calc callback and supplies `TitleConfigWork*` as the work argument. The callback body does not read incoming `r0`; it resolves `g_TitleConfigWork` through literal `0x0044E2D0`, so the global pointer, not its callback argument, is authoritative in this body.

It saves/restores `r4-r6` and `lr`, uses no local stack storage, and returns with `pop {r4,r5,r6,pc}`. It assigns no return value. Incoming `r0` and the callback context are not consumed; any returned `r0` is incidental. There is no null check before dereferencing the global work pointer. The valid entry precondition evidenced by accesses is a non-null pointer to a live `0x158`-byte `TitleConfigWork` with any pointer fields suitable for the called helpers. Reentry, concurrent mutation, and callback timing are not established.

## Direct instruction contract

Source of instruction-level facts: `python tools/split_asm.py --addr 0x002caef0`; checked-in instruction mirror is at `src/engine/leaf_batch32_c.cpp:3578`. Workspace offsets and size are in `include/camp/title_flow.h:61-94`.

1. Load `g_TitleConfigWork` into `r4`; store byte `1` at `work+4` unconditionally.
2. Read signed halfword `work+0x1A`. If nonpositive, skip the first loop. Otherwise, for local `r5=0` onward, call `0x002B9008` once per iteration, reread the signed halfword, increment `r5`, and repeat while the reread value is greater than `r5`. The helper receives whatever is in `r0` at call entry only as incidental call state; its body ignores `r0`. This wrapper does not write `work+0x1A`.
3. Repeat the same loop shape for signed halfword `work+0x24`, resetting local count to zero. The wrapper does not write `work+0x24`.
4. If `work+0x154` is non-null, call `0x002A755C(work+0x154)` and then clear `work+0x154` to zero.
5. If `work+0x14C` is non-null, call `0x002C4360(pointer)` and then clear that slot. Do the same for `work+0x150`.
6. Call `0x002BF41C(work->calc_task)`. Its boolean-like return gates the next operation. If nonzero, call `0x002C45B8(work->calc_task, 0)`.
7. Reload `g_TitleConfigWork`. If non-null, call `0x002C4360(global_pointer)` and then clear the global to zero. If null, skip both operations.

The two loops are not proven to “drain” the title work counters: direct helper evidence shows `0x002B9008` accesses a different global (`0x0043DCB0`), obtains its `+4` object, and conditionally decrements signed halfword at object `+0x64A` only when that value is greater than 10. It does not reference either title counter. With stable work fields, a positive initial title count yields that many helper calls; the callback rereads the field each iteration, so external/helper-induced mutations could alter the count. The checked-in helper has no apparent mechanism to mutate the title workspace. This makes exact count conditional on stable memory, not a general concurrency guarantee.

No callback-local indirect branch or call is present. All call targets above are direct `BL`s. Called helpers can of course make their own further calls.

## Direct helper effects that affect lifecycle interpretation

- `0x002BF41C` (`src/engine/leaf_batch32_c.cpp:1611`) looks up the task handle in a global indexed bucket/list and returns 1 on an exact handle match, otherwise 0. The callback uses it only as a gate. This is an active-registration lookup, not evidence of scheduler dispatch order or ownership.
- `0x002C45B8` is a short conditional entry: it returns immediately if `r0==0`; for nonzero `r0`, execution falls through to adjacent `0x002C45C0`. That routine looks up a task record and applies a signed-halfword state value from `r1` (here 0) at node `+0x36`, with propagation/linked-record handling and state-dependent branches. The neighboring routine is not a heap-free operation. Exact scheduler meaning and lifetime consequence of state 0 are unresolved; callers also name the API `AsdTask_DestroyPair`, so the source-level name should not be taken as proof of freeing.
- `0x002A755C` (`src/engine/leaf_batch42_c.cpp:62`) cleans three non-null internal pointers at offsets `+0xE8`, `+0xEC`, and `+0xD4` through `0x002C4360`, unlinking and clearing those fields as it goes. It unlinks the object from the global list at `0x0044DE78`, adjusts list endpoints/neighbor links and decrements the list count, clears its own link fields, then tail-calls `0x002C4360` on the object. This establishes callback-triggered nested cleanup; it does not establish when the script VM becomes eligible for this callback.
- `0x002C4360` is a heap/resource release path. Its body checks allocation-region bounds and dispatches to allocator internals (including `0x001245F0`, `0x001244E8`, and tail `0x002C3A24`). The callback uses it for the two async table slots and finally the workspace global. Exact allocator pool ownership, null tolerance at all deeper calls, and reclamation timing are outside this callback proof.
- `0x002B9008` decrements a separate shared halfword only above threshold 10; when at or below threshold it leaves that field unchanged. Therefore the callback's repeated helper calls can affect another subsystem field. Do not remove or replace these calls by assuming they are no-ops or that they decrement the title counters.

These facts distinguish local cleanup stores and helper invocation from framework guarantees. The body clears the global only after its final release call returns. It does not itself prove that the scheduler will stop referencing the callback/work afterward, that it runs once, that task state 0 destroys a task, or that cleanup is reentrant/idempotent.

## Registration and independent call evidence

The checked-in initializer at `src/camp/title_flow.cpp` registers callback word `0x002CAEF0` in the calc factory tuple alongside primary callback `0x001EA928`; the task user context is the allocated work. `AsdTask_CreateCalc` forwards those callback words to generic process creation. This proves registration/argument forwarding only, not callback order, exact invocation time, invocation count, or context lifetime.

Repository-wide text search found the literal callback address only in that initializer and its declaration/definition. That is evidence that no other checked-in source explicitly registers it, not proof that runtime code cannot reach it indirectly. The H1/init contract reports a live menu scenario reached initializer and primary calc, then returned via cancel; it did not instrument this secondary callback or demonstrate cleanup execution. `TitleConfig_Calc` reaches terminal state 4 and returns `-1`, but the scheduler relation between that return and the secondary callback remains unproven. `TitleConfig_IsReady` checks task activity separately; it does not itself call this callback.

Other `AsdTask_DestroyPair(...,0)` call sites exist (e.g. `src/ui/ui_runtime2.cpp` and `src/ui/status_down.cpp`), but they are not independent callback invocations and do not resolve the state/lifetime meaning. Treat their naming/comments as corroboration of an API label only.

## Smallest safe candidate and validation seam

A candidate may replace only the callback's own orchestration while retaining calls to the pinned helper entries at their observed ABI boundaries. Keep the global lookup, unconditional flag store, loop rereads/call counts, pointer checks, clear-after-call ordering, active-task predicate, state call arguments, final global reload, free, and clear order exactly explicit. Do not substitute callback argument for the global, silently omit the secondary global mutation made by `0x002B9008`, or translate task-state call into a presumed delete/free.

The bounded standalone differential should compare original vs candidate with a valid synthetic `TitleConfigWork`, stable global/helper fixtures, poisoned unrelated bytes, and controlled helper spies/original helpers. Cover each counter as negative/zero/positive (including 1 and a larger value); verify `0x002B9008` call count and separate global-halfword effect above, at, and below threshold; independently vary nullable `+0x154`, `+0x14C`, and `+0x150`; and vary task-active predicate false/true. Record exact helper order/arguments, work/global writes, callee-saved registers and stack restoration. Add edit-then-cancel only at the actual primary-calc/caller integration layer; this isolated callback test cannot establish setting semantics or persistence.

A separate caller/scheduler test is required to observe whether/when this callback executes after primary callback terminal return, whether it is called exactly once, whether the task remains registered, and when the workspace/script/resource pointers become invalid or freed. Use a private disposable runtime profile only after runtime owner verifies isolation. Existing H0/H1 traversal evidence does not supply those observations. Semantic/runtime acceptance remains open.

## Evidence and limitations

Pinned original identity is the US v0.1.0 image SHA-256 in `config/game_info.json` and the task packet. Disassembly commands used: `python tools/split_asm.py --addr 0x002caef0`, `--addr 0x002c4360`, `--addr 0x002a755c`, `--addr 0x002c45b8`, `--addr 0x002bf41c`, and `--addr 0x002c45c0`. Static source searches/readbacks were limited to the listed implementation/caller/layout/contracts. No build, candidate, test, debugger, or emulator evidence was generated.

Unresolved: scheduler callback order and lifetime; whether secondary cleanup is called after `TitleConfig_Calc` returns `-1`; whether task state 0 implies stop, remove, or another scheduler transition; valid runtime invariants for global and embedded pointers; allocator/resource ownership; reentry/race behavior; actual edit/cancel/confirm persistence. Next action: runtime owner instruments one isolated title-settings scenario to capture secondary callback entry/exit and task/work lifetime, while candidate validation remains bounded to the described differential seam.

