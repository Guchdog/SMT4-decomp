# H4 repeat-state context: independent review

## Recommendation

The recon report’s core static dataflow is supported: `0x00399D60` saves its incoming `r0` object as `r4`; on distinct branches it passes that same value to `0x0039AF30` and `0x0039B58C`. `0x0039AF30` retains it in `r4`, passes it to `0x0039B864`, and then to `0x0039D758`. The reader wrappers access the separate state at `0x004E3CD4`, return a boolean and, on success, write 32-bit results to the supplied output addresses. The code also mutates fields and flag bits relative to the incoming object pointer. This confirms common per-call pointer flow, not object ownership or a player/H4 contract.

Three wording/interpretation limits should accompany acceptance:

1. The literal `0x0049F91C` and tests of its word/byte fields are directly supported, but the task’s read sources do not independently identify it as a “map/script block.” The field-control contract does not mention this address. Describe it as a shared global gate unless another pinned source establishes its type.
2. In `0x0039D758`, `ldrsb r0,[r4,#0x55]` is compared with the literal dword `0x0000FFFF` using signed `cmp`, followed by `addlt` and `strblt`. Every possible signed-byte value is less than positive 65535, so the branch is not a meaningful saturation bound; on this path the byte increments with truncation/wrap. Do not describe `+0x55` as incrementing “up to” an effective bound.
3. Both mode-1 sites ignore the reader’s boolean return and then consume their stack outputs. The mode-1 reader leaves output memory untouched on failure. Therefore the output values on that failure path are not established as zero or fresh; they depend on caller stack contents. The recon report says the returns are unchecked, but the risk should be retained when summarizing the resulting object writes.

## Independent ARM audit

The reference image hash is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, matching the run-002 packet; all 12 declared input hashes matched. Ledger extents agree with the disassembly: `0x00399D60` is `0xC0`, `0x0039AF30` is `0x124`, `0x0039B58C` is `0x2D8`, and `0x0039D758` is `0x160`. The former two caller sites are within those extents; the two target function ends are `0x0039B864` and `0x0039D8B8`.

A bounded aligned ARM B/BL scan over `[0x00100000,0x003FE624)` and local instruction decode confirmed `0x00399E10 -> 0x0039B58C`, `0x0039B03C -> 0x0039D758`, `0x0039B5EC -> 0x003C303C`, and `0x0039B69C` / `0x0039D7FC -> 0x003C3034`. `0x00399DC8` directly calls `0x0039AF30`. At the `0x0039B03C` site, `r0` is explicitly reloaded from saved `r4` before the call. The scan and local context do not prove runtime execution; indirect/computed calls, registration, Thumb and references outside the declared interval remain open.

### Caller and shared object flow

At `0x00399D60`, the incoming object in `r0` is copied to `r4`. A signed byte load at `r4+0x0C` equal to -1 exits; bit `0x1000` from dword `r4+0x10` can also short-circuit. In the nonzero-`+0x0C` branch, `r4` is passed to `0x0039AF30`. In the alternate zero-byte branch, successful checks at `0x002C0BA8(0x400)` and `0x002931CC(0x76)` lead to a call of `0x0039B58C` with `r0=r4`. The return from `0x0039AF30` is checked; a nonzero value would set bit 0 of `[r4+0x10]`. `0x0039B58C`’s visible exits set `r0=0`, and that call’s return is also checked by the caller. This is a caller relationship and an object-local branch effect; it does not validate the object type.

`0x0039AF30` tests `[r4+0x10]` bits `0x1000` and `0x10`, reads global words at `0x0049F91C` and `+4`, reads/tests its byte `+0x18`, and accesses object words/floats at `+0x18..+0x28`. If the interpolation path is entered, the helper `0x0039B864` receives `r4`; its return is ignored before `r0` is reloaded from `r4` and `0x0039D758` is called. The routine returns 0 on its visible paths. The `script_vm` ledger label on `0x00399D60` and `unknown` labels on the other routines are metadata, not type or scene proof.

### Reader modes, output slots and state writes

`0x003C3034` sets `r2=1` and tail-branches from `0x003C3038` to `0x002C01B8`; `0x003C303C` sets `r2=3` and tail-branches from `0x003C3040`. Their branches preserve/inherit `r0` and `r1`. The mode-0 entry `0x002C01B0` sets `r2=0` before reaching the same reader.

In `0x0039B58C`, the tested object flag is `[r4+0x10] & 0x20000`:

- With the bit set, `0x0039B5CC` calls mode 0 at `0x002C01B0` with `r0=sp+0x0C`, `r1=sp+8`. If return is nonzero and `[0x0049F91C+0x18]==0`, those results feed the update path. Otherwise `0x0039B5EC` calls mode 3 with the same pointers. The mode-3 result and global byte gate whether the release/reset path runs. That path clears bit `0x20000`; it either zeros floats `+0x3C/+0x40` when signed byte `+0x54>2` or stores differences based on `+0x44/+0x48/+0x4C/+0x50`.
- With the bit clear, a query/setup through `0x002315C8` and `0x002315B4` gates the mode-1 call at `0x0039B69C`, with `r0=sp`, `r1=sp+4`. The returned boolean is not checked. The stack words are then read and converted to floats; fields around `+0x2C/+0x30`, `+0x34..+0x3C`, `+0x44..+0x50`, and byte `+0x54` are written, and bit `0x20000` is set. If the reader fails, mode 1 leaves outputs untouched and this caller still consumes them.

In `0x0039D758`, entry bit `[r4+0x10] & 0x02000000` returns 0. Otherwise a `0x002315C8`/`0x002315B4` gate checks four stack-produced values. A nonzero helper result plus global byte `[0x0049F91C+0x18]==0` calls mode 1 at `0x0039D7FC` with `r0=sp+0x18`, `r1=sp+0x1C`; its return is not checked. The subsequent stores consume both stack words and update fields around `+0x2C..+0x50`, bytes `+0x54/+0x55`, and bit `0x10000`. Again, a reader failure does not prove those stack values are zero/current. On the alternate branch, bit `0x10000`, `0x00231B54`, and the global byte determine whether the code clears bit `0x20000` or enters the `+0x55` progression. At `0x0039D880..8C`, the signed byte is compared against literal `0x0000FFFF`, so this code does not cap the signed-byte value at 255 or any reachable maximum.

The object/subobject access `r4+0x162` is passed to `0x00231F58`/`0x00231B38`, with helper results subsequently loaded/stored. These instructions establish a nested address/use pattern, but do not supply a type, allocation site, player-work offset, or H4 interaction contract.

## Evidence limits and next step

The recon report correctly avoids claiming a validated player object, active H4 reachability, physical input, or a specific interaction. The run-003 recon now also resolves the wording concern: it calls `0x0049F91C` only an untyped shared global gate, describes the signed-byte `+0x55` comparison with `0x0000FFFF` as ineffective (with byte wrap), and preserves the unchecked mode-1 output caveat. Its proposed next static trace remains appropriate: trace the `0x00399D60` object allocation/ownership and the `+0x162` helper object through direct loads/stores and consumers. Keep later runtime work separately assigned and read-only until the pointer and consumer are validated. No build, tests, emulator, save access, or guest writes were performed.

## Read-only checks

- Recomputed hashes for the 12 packet inputs: zero mismatches.
- Disassembled `0x00399D60`, `0x0039AF30`, `0x0039B58C`, `0x0039D758`, `0x003C3034`, `0x002C01B0` with `tools/split_asm.py`; each command exited 0.
- Recomputed the aligned ARM direct-branch sites and decoded their local instructions with Capstone; matched the sites listed above, exit 0.
- No source, recon, runner, board, build, test, runtime, save, or guest-memory changes.

## Run-003 focused recheck

The run-003 packet pins the corrected recon at the declared hash, and all 12 input hashes match. Its three requested statements now agree with the pinned evidence and prior review: `0x0049F91C` is described only as a shared gate with no assigned type; `ldrsb` of `+0x55` compared signed against positive `0x0000FFFF` is not an effective bound and the byte store can wrap; both mode-1 callers still consume output slots without checking the reader return, so failure-path contents remain unknown. No broader static reanalysis or runtime/build activity was performed for this recheck.
