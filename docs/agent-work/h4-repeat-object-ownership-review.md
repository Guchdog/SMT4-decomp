# H4 repeat-object ownership: independent review

## Result

The pinned ARM and source-level layout evidence support the recon’s static arithmetic: the `0x00291CAC` initialization path allocates a `0x12344`-byte host object, stores its pointer in global slot `0x0044CDF0`, and passes `host+0x40` to `0x00399594`. That routine forwards the same pointer to `0x00399E20`; the latter copies the table pair at `0x00404A8C/0x00404A90` (`0x00399D60, 0`) to input-object `+0xB24`, which is host allocation `+0xB64`. This is static initialization evidence for a callback-like pair in a Navi-associated host object. It does not prove indirect dispatch, what `r0` the eventual dispatch supplies, or that dispatch occurs at the H4 checkpoint.

The scheduled “NAVI PROC” callback is a separate registration: `0x00291CAC` passes `0x001A95B8` as the task callback to `0x002C5978`, with the host pointer in its stack arguments. The table-installed `0x00399D60` pair is not the same callback address or proven to be the registered task callback. The draw task callbacks at `0x001FC480` and `0x001FC454` are also separate. Keeping these identities distinct is important.

## Allocation and table-copy audit

The packet’s 13 declared input hashes matched; reference `code.bin` SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Ledger bounds and disassembly agree:

- At `0x00291CCC..0x00291CDC`, allocator arguments are aligned to `0x100`, size `0x12344`, with other register/stack arguments visible in the call setup. The result in `r0` is stored through the literal slot `0x0044CDF0` at `0x00291CF0`.
- `r4` retains the returned host pointer. `0x00291D28` computes `r0=r4+0x40` and `0x00291D2C` calls `0x00399594`.
- `0x00399594` copies input `r0` to `r4` and at `0x003995AC..B0` passes that same pointer to `0x00399E20`.
- `0x00399E20` loads table base `0x00404A74`; the pair at `+0x18` is the aligned pair `0x00399D60, 0`. Its instructions at `0x00399EA4..B0` store that pair at input-object `+0xB24`. Since this input is host `+0x40`, the destination is host `+0xB64`.
- `0x00291CAC` also creates the named “NAVI PROC” task with callback value `0x001A95B8` (stack argument), user value `0x001A959C`, and host userdata; it separately creates “NAVI DOWN” with `0x001FC480` and “NAVI FADE DRAW” with `0x001FC454`. The code statically sets up those tasks but cannot show task execution or the `0x00399D60` pair’s dispatch.

`src/engine/map_runtime.cpp`/`map_runtime.h` label the global pointer `g_NaviMainWork` and preserve an exact wrapper plus a disabled readable draft; the ARM allocation/copy arithmetic is independently checked above. Names/layout notes support that this initialization route is Navi-associated, but do not resolve dynamic ownership of every `r0` object passed to `0x00399D60`.

## Helper global accesses and the `+0x162` correction

The two helper bodies are short and decisive:

- `0x00231F58` loads the literal address `0x0044CDF0` into `r0`, loads `*[0x0044CDF0]`, adds `0x38`, and returns that address. The caller’s incoming `r0` (including `r4+0x162`) is overwritten before use; the helper does not dereference it.
- `0x00231B38` likewise replaces incoming `r0` with `0x0044CDF0`. It loads two words from `r1` and stores them at `*[0x0044CDF0]+0x38` and `+0x3C`; it returns without using the caller’s incoming `r0`. It does not dereference `r4+0x162`.

Therefore the earlier inference that these helper calls operate on the `+0x162` subobject is unsupported. Their actual global target is the current pointer in `0x0044CDF0`. This also means that a stale or changed global slot could direct helper effects away from the object whose `+0x162` value was passed; no runtime slot identity or null/fault domain is established here. Other consumers of `+0x162` are outside this pair’s demonstrated behavior.

## H4 checkpoint and ownership limits

The H4 report records `*[0x00447E88] == 0x004BCCd0` for its view object and describes the camera helper/callback checkpoint. The Navi global slot `0x0044CDF0` is a different slot; the H4 evidence cited does not read it, compare its value to `0x004BCCd0`, observe the table pair at host `+0xB64`, or record entry `r0` at `0x00399D60`. Thus the capture does not prove that the Navi host was the same object, that the callback was entered/dispatched, or that a particular entry argument was passed. It also does not tie the chain to player work, movement, physical input, interaction, or transition.

The recon’s next bounded observation is reasonable as a future, separately assigned passive task: at an established checkpoint, record entry `r0` and return address at `0x00399D60`, read the current global slot and pair only after validating the pointer/ranges, and record ordering/absence or timeout across neutral paired runs. That would test one bounded runtime link; a hit alone would still not prove player ownership or H4 behavior. No guest writes or watchpoints are warranted by this static evidence.

## Read-only checks and disposition

- Verified all 13 packet hashes; zero mismatches.
- Disassembled `0x00291CAC`, `0x00399594`, `0x00399E20`, `0x00231F58`, `0x00231B38`, and `0x00399D60` from the pinned image; each `tools/split_asm.py --addr ...` command exited 0.
- Read the declared `map_runtime.cpp`/header declarations and H4 field-control report; no source edits.
- No build, tests, emulator, save access, guest writes, runner changes, or board edits.

**Recommendation:** accept the bounded static table-copy and global-helper findings. Keep callback dispatch, actual `r0`, checkpoint ownership, and all player/H4 behavior claims unresolved pending separately assigned direct evidence.
