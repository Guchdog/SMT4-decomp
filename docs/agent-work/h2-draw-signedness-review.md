# Independent review: TitleConfig_Draw unsigned guard

## Disposition

Accept the signedness correction and the two added guard cases as bounded isolated callback evidence. The candidate now preserves the original unsigned branch condition. This is not evidence that either test cursor state is reachable through the title initializer/caller, and the candidate remains unpromoted pending real-caller validation.

## Guard and fixture review

The recorded original disassembly at `0x002CB324` is `cmp r7,#3`, followed by `bhs 0x002CB3A8`. ARM `BHS` means unsigned higher-or-same, so the table path is taken only if the 32-bit index is unsigned `<3`. Candidate code uses `static_cast<u32>(absolute_index) < 3u`, which agrees: signed `-1` becomes `0xffffffff` and skips the table path; `3` also skips it.

The `negative-absolute-index` fixture returns scroll `-1` with one row, so row zero has absolute index `-1`. Its option read is `work + 0x28 + 4*(-1) == work+0x24`. The fixture explicitly seeds that word; it is within the `0x158`-byte allocated work object. The seeded option value 4 selects node `0x5F`, within the 0x80-node mapped fixture. The `absolute-index-three` fixture returns scroll 3 with one row, so its row-zero absolute index is 3. Its option read lands at `work+0x34`, explicitly seeded, and option value 7 selects mapped node `0x62`. These are valid mapped-memory cases for exercising the branch. Their mocked cursor return values are not proof of caller reachability or valid user state.

The runner makes the branch expectation independently observable: for each guard case it requires both original and candidate to have no TBB subtable/payload trace and no formatter trace. The report records zero counts and empty descriptor lists for both cases. Whole-trace differential equality, memory/fault checks, and ABI checks remain in the shared comparator.

## Report identity and controls

I verified report SHA-256 `40106e77c35d57230573b787e80f6cac089c814e5493f62d324e1cda96e2471a`; it identifies the pinned reference SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, candidate source SHA-256 `bef32aa76f533cb15d1372b9e4eace6b7a2c4dbfd7d95bd57877ab0f130fcc6e`, runner SHA-256 `43391efdd5efa790de0fd82d14ab32db317eb58ff7d06637eee2211a7a88c402`, and ARM object SHA-256 `000b4855164bfa7c8775ab32a4a02b936e9c878435c29f0ab8d95ebcffc9b9c2`. The report shows compile exits zero, 46/46 cases passing with no counterexample, and a compiled wrong-stride negative control detected as a trace difference. I did not rerun compilation or the differential.

## Evidence boundary and next action

Cursor, TBB, layout, format/font, panel/sprite, render, touch, and callback behavior are mocked. The run does not establish initialized-caller state, whether negative scroll or absolute index 3 occurs in-game, helper internals, scheduler/calc interaction, actual resources, user-visible meanings, persistence, Azahar behavior, or whole-menu equivalence. Keep the change as experimental; the next meaningful evidence is a bounded original-versus-patched draw invocation from initialized caller/resource state, with calc frozen and the same command/cache observations.
