# H4 Navi callback contract review

## Result

All 18 declared input hashes match the run-001 packet. I independently checked the full pinned ARM body at `0x00399D60` (192 bytes, `0x00399D60..0x00399E1F`), its direct helper bodies and the related recon/runtime evidence. The recon report's main branch and return description is supported, with the direct/transitive and runtime limits below. This is static contract evidence, not a reconstruction or proof of interaction.

## Direct branch and return flow

The function pushes `{r4,r5,r6,lr}`, keeps entry `r0` in `r4`, and returns through `pop {r4,r5,r6,pc}` at `0x00399DE0`. It does not explicitly consume incoming `r1-r3`. It has no local null/range check before reading the object.

1. It loads **signed** byte `[r4+0x0C]`. Only the value `-1` takes the immediate exit, returning `r0=-1` (sign-extended `0xFFFFFFFF`). This is not a generic “negative byte” test.
2. Otherwise it loads `[r4+0x10]`, extracts bit `0x1000` to saved `r5` as 0/1, and calls `0x002C0BA8(0x400)`. If that returns nonzero it calls `0x002931CC(0x76)`. Only when this second result is nonzero does `LDRB` read `[r4+0x0C]` as **unsigned**; if nonzero it calls `0x0039C944(r4)`. Thus values `0x80..0xFE` are not the signed `-1` sentinel, and can pass this nonzero check. The `0x400` and `0x76` callees query indexed flag data through other helpers; their transitive effects remain dependencies.
3. Only after those checks/call does it test saved bit `0x1000`. If set, it returns the then-current residual `r0` without calling `0x00220888` or entering the later branches. The residual can be from the first flag query, second query, or `0x0039C944`; it is not a proven boolean or fixed value. Therefore bit `0x1000` is a later gate, not an early exit around the initial helpers.
4. If bit `0x1000` is clear, it calls `0x00220888` without preparing explicit arguments. That callee starts by loading a global and reading its `+4` pointer, so the callback's residual `r0` is not an explicit object argument. It then reloads `[r4+0x0C]` with `LDRB`. If nonzero, it calls `0x0039AF30(r4)`: zero returns immediately with `r0=0`; nonzero reaches the only direct object store, `[r4+0x10] |= 1`, then returns the modified word in `r0`.
5. If the reloaded byte is zero, it repeats `0x002C0BA8(0x400)` and, only on nonzero, `0x002931CC(0x76)`. A zero from either returns `r0=0`. If both return nonzero it calls `0x0039B58C(r4)`, compares its return, returns zero on zero, or sets bit 0 of `[r4+0x10]` and returns that modified word on nonzero.

Static inspection of the pinned `0x0039AF30` and `0x0039B58C` bodies shows their visible return paths set `r0=0`. Consequently the callback's conditional bit-0 store exists in the direct body but is not shown reachable through those current helper bodies' visible returns. Keep the condition in the contract; do not report the store as an observed or established effect.

## Direct versus transitive effects

Within its own 192-byte body, the only explicit store through the `r4` object is the conditional word update at `+0x10`. It also reads object `+0x0C` and `+0x10`. This direct-store description must not be mistaken for the full call-tree write set:

- `0x0039C944` is a non-leaf stateful helper. Its body reads and writes object fields/flags and calls reader and Navi-host helpers; its complete transitive effects and predicate meaning are not established.
- `0x00220888` immediately loads a pointer from global `0x0043DA28+4`, calls input-related helpers including `0x002B9094` and `0x002B90A8`, and has conditional stores to that pointed-to object's fields (including offsets in the `+0x4B8..+0x4BE` range). It is not a no-op or a callback-object-only operation. Its complete semantics, pointed-object type/lifetime and effects through its helpers remain unresolved.
- `0x0039AF30` and `0x0039B58C` themselves mutate fields relative to `r4` and call further helpers. Their visible zero returns do not make their side effects pure or establish the full transitive effect set.

No source or static evidence here maps the callback object to player work. The prior runtime entry capture gives `r0=host+0x40`, initial signed `+0x0C=1` and word `+0x10=0` in both processes, while its live dispatch pair and LR support callback entry. It stops at entry: the two flag results, whether `0x0039C944` runs, any later object mutations, callback return, and view/player consequences were not captured. Since `0x0039C944` may mutate the object before later reloads, the entry snapshot alone cannot settle subsequent `+0x0C` branch conditions.

## Next evidence and limits

A bounded passive call/return trace is a suitable next step: record callback entry, the actual returns of the two flag helpers and any `0x0039C944` call, the `0x00220888`/later-helper path, and callback return before the dispatcher continues at `0x001A95E8`. Pair that with validated before/after reads of the callback object and only validated spans for the global-pointer object used by `0x00220888`; preserve execution order and a neutral paired control. The return breakpoint at the known callback LR can observe the callback's value before the caller's next instruction overwrites `r0`. This is a narrow way to resolve path selection and the direct return; complete transitive semantics still need separate work. Do not use unvalidated reads, writes, watchpoints, or infer behavior from entry alone.

No evidence in this review establishes physical or logical input meaning, player movement/ownership, view changes, H4 interaction, zone transition, or whole-game equivalence. No build, tests, emulator, save access, or guest writes were used.
