# Independent post-differential review: `0x00286928`

## Verdict

I independently confirm all five facts in the contract's “Implementation differential corrections” against the pinned ARM. The complete candidate compiles to an 812-byte body with 22 resolved ARM call relocations, and the private rerun passed all 296 direct cases. I found no counterexample in those five corrections or the exercised candidate paths.

This is **candidate-level, stub-scoped evidence**, not production promotion. The runner does not compose the actual `0x00221168` caller and has no mutation-based negative controls; all direct callees are intercepted with contract-scoped stubs. Keep the candidate eligible for a next validation step, but require the real caller composition and negative controls before treating this as sufficient integration evidence.

## Provenance and independent rerun

All 13 hashes in run-001 `task.json` match current inputs, including pinned image `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, candidate source `dc7a1cc97a91bdf31dafac283ddfa90903fa77f5b7fd13caa24bcb3659ddb810`, and runner source `2ac19f8488336789fc64f1f7b221b621192a46baa953372274e413e25e0eaa66`.

I reran the focused runner with its output redirected to this task's private `build/agent-work/H2-semantic/h2-helper-00286928-post-diff-review/run001/checks/focused/` directory. The candidate object SHA-256 is `10bc610e6f180e54f380c415ba77baac573047cd6677103d259dd17b688f8280`; the extracted function body is 812 bytes (`a5b5f2546b9e2937ae90ba3756010fdd2cb785c9df9ae1a75467b4bb4d166db4`) with exactly 22 relocations. All are relocation type 28 (`R_ARM_CALL`), all target ledger-listed even ARM addresses, and the runner validates unconditional ARM BL opcode, alignment and range while resolving them. The resolved body hash is `cf49833b73ea58eeff3986af47a8c86d05c848123248a255f168bdb58e99c62c`; two ARM NOP words fill the 820-byte span. The focused command exited 0 and printed `PASS 296 direct cases ... body 812/820 bytes, 22 ARM calls relocated`.

The runner's 296 cases are 276 cases from 23 selectors × two `r2` values × six states, plus 20 targeted cases for selectors 11/12/13/15/19 over two seeds and both `r2` values. It compares raw return, SP, `r4-r11`, `d8`, ordered stub-call events/arguments (including the three stack words at `0x0028E974`), writes, selected mapped memories, fault and completion state. VFP is enabled and `d8` initialized. It does not compare transient stack contents or caller-saved registers, which is appropriate for the stated contract absent further caller requirements.

## Five correction checks against pinned ARM

| Contract correction | Pinned instruction evidence | Finding |
|---|---|---|
| Raw 11 mode 1; 13 mode 1; 14/15 mode 0 | Selector setup at `0x0028693C..0x00286998`; raw 13 path at `0x00286A28..0x00286A34` sets `r1=1`; raw 15 path at `0x00286A38..0x00286A40` explicitly sets `r1=0`; common `strb r1,[r5,#0x5E]` at `0x002869B4` | Confirmed. |
| Raw 19 selects special pointer `[0x0043E188+8]` and keeps selector 19 | `0x0028698C..0x00286998`: `cmp r6,#11`, then `cmpne r6,#19`, `movne r5,r0`, branch to `0x00286A44` for either 11 or 19; only selector 14/15/13 paths rewrite `r6` | Confirmed. |
| `P+0x2D=1` only for raw selectors 13 and 15 | Raw 13 setup sets internal `r2=1` at `0x00286A28`; raw 15 at `0x00286A3C`; other selector setup leaves it zero; unconditional `strb r2,[r5,#0x2D]` at `0x0028699C` precedes repurposing `r2` | Confirmed. |
| Incoming `r2==0` and initial `P+8!=0` sets `+0x2E`, calls `0x002B8D24(P,P[9])`, sets `P[8]=3`, `P[0x35]=0`, returns 0, and skips update loop | Initial-state compare/store at `0x00286A70..0x00286A7C` branches to `0x00286A10`; this loads `P[9]`, calls `0x002B8D24` at `0x00286A18`, performs the two stores at `0x00286A1C/20`, then branches to zero return at `0x00286BE4` | Confirmed. |
| Both `0x0028DF54` sites pass the raw word at `P+0x18` | `ldr r0,[r5,#0x18]` immediately precedes `bl 0x0028DF54` at `0x00286C18/1C` and `0x00286C40/44` | Confirmed: the value, not `P+0x18`, is passed. |

## Candidate and runner bounds

The candidate expresses the corrected selector setup and both `r2` path families, including the nonzero-state `r2==0` call to `0x002B8D24`. It retains original dependencies via 22 direct call relocations, fits in the original 820-byte slot with eight bytes available for the two NOPs, and models the `0x0028DF54` input as `uint32_t`.

The runner is direct-entry only: it initializes `r0-r3`/stack synthetically and invokes original versus candidate at `0x00286928`; it does not execute `0x00221168`, its getters, the nested callback table or handler `0x001A07CC`. Therefore there is no actual-caller composition in these 296 cases. The runner also defines no candidate mutants/negative controls, so there is no evidence that the harness detects representative wrong implementations. The test inputs cover relevant selector and state combinations, but they are not a substitute for those controls.

`TARGETS` intercepts every direct callee address used by this function. Some stubs model narrow local behavior (the two query helpers and `0x0028DF54` memory effects); the rest return fixed/simple values. In particular, `0x002B8D24` returns a synthetic value and does not run its body. Thus this differential isolates dispatcher code under the same controlled stubs; it does not establish equivalence with real dependencies, real caller state, or runtime behavior.

## Recommendation and next evidence

Accept the five corrected facts and the 296-case direct differential as reproducible bounded evidence. Before using the result for production integration, add mutation controls for selector remapping/`+0x2D`, default-versus-special pointer selection, the `r2==0/P+8!=0` helper-and-store path, and raw `0x0028DF54` argument; then compose the real `0x00221168` callback path with controlled valid getters/globals and check callback return/visible continuation. Keep any stub-only portions labeled as such; this review does not authorize runtime claims.

No production source, ledger, runner, build cache, or emulator was changed. The only authored repository file is the assigned review report.
