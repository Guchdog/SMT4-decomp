# H2 synchronized query capture design

## Decision

No existing callback in the pinned Azahar/Dynarmic code is a supported, low-overhead synchronization point for recording the H2 logical query and its returns. Do not use `AddTicks`, `CallSVC`, `ExceptionRaised`, or `PreCodeTranslationHook` as a generic sampler. A viable future design is a narrowly scoped **dispatcher-yield observer**: when enabled for the H2 query's known entry and return PCs, end the generated JIT invocation at those addresses, return normally through `Jit::Run()` to the emulation thread, and capture only after the JIT call has returned. This design is conditional on a source-level proof/test that the selected yield path commits all architectural state to `jit_state` before returning. The assigned source slice does not establish that commit guarantee for a new observer terminal, so this is a design recommendation, not a validated capture route.

If that guarantee cannot be added and demonstrated, keep only the existing RunLoop-owned manual snapshot as coarse diagnostic context. It cannot prove query entry/return ordering or scheduling.

## Pinned-source trace

- Azahar `ARM_Dynarmic::Run()` calls `jit->Run()` and returns after it does (`arm_dynarmic.cpp:192-200`). `Step()` similarly returns after `jit->Step()` (`202-208`). The wrapper does not itself add a callback after those calls.
- Dynarmic `Jit::Impl::Run()` first processes pending cache invalidation, marks itself executing, calls `block_of_code.RunCode()`, then processes requested invalidation using the returned halt reason, and returns it (`a32_interface.cpp:72-97`). `Step()` has the same outer shape around `StepCode()` (`99-112`). This host return is the clearest public synchronization boundary in the inspected path; reading registers at that point is materially different from sampling an arbitrary generated-code callback. Whether every architectural component is materialized at this boundary for a newly introduced terminal still requires explicit verification.
- `BlockOfCode::GenRunCode()` obtains the cycle budget through `GetTicksRemaining` before entering generated execution (`block_of_code.cpp:308-336`). Its dispatcher checks the halt reason/cycle budget and looks up another block (`364-370`). On return it restores host MXCSR, calls `AddTicks` for the elapsed amount, atomically clears/returns the halt reason, restores callee-saved registers, and returns to C++ (`388-408`). `UpdateTicks()` separately calls `AddTicks` and reloads the remaining budget (`433-446`). Thus `AddTicks` is a timing/accounting callback that can occur during a larger `Run()`; the API does not define it as a guest-PC boundary.
- The generated SVC path explicitly switches MXCSR out, calls `AddTicks` before `CallSVC`, then queries ticks and switches back (`a32_emit_x64.cpp:739-760`). The exception path similarly calls `AddTicks` before `ExceptionRaised` (`762-788`). Azahar's implementations forward those methods to the timer and SVC/error handling (`arm_dynarmic.cpp:89-169`). A callback being invoked from translated code does not establish a stable whole-CPU snapshot point.
- `UserCallbacks` documents `PreCodeTranslationHook` as translation-time IR emission before translation of the instruction, not a runtime callback (`config.h:68-76`). `a32_interface.cpp:204-230` shows the block cache miss path translates, optimizes, verifies, and emits IR. The earlier private-build investigation also records that inserting a `CallHostFunction` in this hook froze startup even when the call was a no-op; that report is historical evidence, not a fresh runtime reproduction.
- `Step()` is a public instruction-step interface (`a32.h:25-35`); the inspected backend sets a one-cycle budget and `HaltReason::Step` before entering its generated step code (`block_of_code.cpp:338-357`). It can serve as a high-overhead fallback for a short bounded diagnostic window only if the caller is already positioned at the query. It does not by itself provide a low-overhead way to discover the query entry during normal execution.

## Recommended observer contract

1. Resolve and pin the exact logical-query entry and the observed return continuation(s) from the original caller/ABI evidence before enabling capture. Treat ARM/Thumb mode and the return address convention explicitly; a single expected return PC must not be assumed if the caller has multiple continuations.
2. Add an opt-in observer mode that is disabled by default. The generated path should only yield at the allowlisted entry/return PCs, then return through the ordinary JIT `Run()`/`Step()` boundary. Capture must execute on the emulation thread after the JIT call has returned. Do not invoke an arbitrary host sampler from `AddTicks`, memory callbacks, SVC/exception callbacks, or translation hooks.
3. Before relying on captured values, prove that the observer yield commits R0-R15, CPSR/FPSCR and relevant memory effects into the public JIT state before C++ reads them. Add a focused backend test using a known register/memory pattern immediately before each yield and compare the returned `Regs()`, CPSR/FPSCR and memory with the expected state. If the emitter cannot prove this property, the observer must fail closed and emit no evidence.
4. Assign a monotonically increasing capture sequence and query invocation ID. Record process/title identity, CPU/thread identity, entry PC/mode, LR, SP, relevant registers, query inputs, result registers/flags, completion PC, tick count, and explicitly bounded guest-memory fields. Keep entry and return records paired by invocation ID; reject missing, duplicate, out-of-order, wrong-mode, wrong-return, or truncated records. No remote listener or host input is part of this design.
5. Bound overhead by enabling yields only for the H2 scenario and the allowlisted PCs, with a hard cap on invocation count/records and a watchdog on host wall time. The normal dispatcher path must be unchanged when disabled. Record the number of yields and elapsed time; if any cap or watchdog fires, mark the trace incomplete and do not interpret it as a pass.
6. Failure to reach entry, return, or capture state is an explicit incomplete result. Preserve the last valid record and failure reason, stop observation without changing guest memory or logical inputs, and do not convert an optional observer failure into a generic guest/core fatal error.

This avoids reliance on undocumented callback timing, but it requires a narrowly assigned Dynarmic implementation and review before it becomes an available route. The current public `Step()` fallback is synchronized only at its documented call boundary and is useful for a very short trace after the caller has reached the target; its per-instruction cost and target-discovery gap prevent calling it a low-overhead solution.

## No-host-input validation sequence

1. Offline, unit-test the observer's state-materialization and entry/return pairing with synthetic JIT state; include ARM and Thumb targets, multiple returns, zero invocations, duplicate events, and a deliberately omitted return.
2. Run the backend's focused test with cycle counting both enabled and disabled, confirming the observer is independent of `AddTicks` scheduling and the disabled path has no observer events. Do not infer production correctness from a unit test alone.
3. Before any runtime work in a separately assigned task, confirm the offline ARM interworking/differential/caller gates for the unchanged H2 candidate and validate the exact observer build and private runtime boundary. This task did not run those checks or authorize an emulator/debugger/network session.
4. In a future isolated original/patched capture task, use a deterministic already-approved guest event source (or a no-input scenario that naturally reaches the query), start capture before entry, and require paired records for the same invocation. Compare query arguments, results, relevant state and persistence across both images. Do not synthesize keyboard/mouse input, directly write guest state, or count manual UI observations as a logical-query trace.
5. Require clean observer shutdown, bounded output, process identity, and a complete terminal record. Keep H2 open if no valid entry/return pair is produced or if the input/scheduling source is not independently established.

## Evidence boundary and limitations

This is a read-only design review. The 15 task-declared input hashes matched the packet. Source facts above are limited to the pinned files listed in `task.json`; the recommendation to add a dispatcher-yield observer is an inference/design proposal and has not been implemented or tested. The assigned source slice does not prove full register allocator flush behavior for a newly introduced yield terminal, exact H2 caller entry/return addresses, a deterministic guest input seam, runtime overhead, or persistence behavior. No build, test, emulator, profile, debugger, network, or host input was used. H2 remains open.

## Reviewed pinned source hashes

- `arm_dynarmic.cpp`: `025745b534b2c0321078ed5a67fe9cb71bcb04fd8cc34b17349bced19709642f`
- `a32_interface.cpp`: `9bf76851ad87141fe1822d155c570964a10b7c59152ff3f509bebda8973b8977`
- `block_of_code.cpp`: `324d269ac4f41a9a6d63ef15d118d3ef8f14404fbedc0d47b9241a8e366bb957`
- `a32_emit_x64.cpp`: `30b5230b2d21819a95fa2e7288e88cc8a94cdc310222f31d6b6033a96448325a`
- `config.h`: `5da62b5b4954476e76b2e0e3bbc16cfe1d52c864ada729174fc2e46db6859f69`
- `a32.h`: `fee5f0fedb0fadaaaeebcf12479283bb6f1e77d91a8433b8fd55440a8d8fdafe`
