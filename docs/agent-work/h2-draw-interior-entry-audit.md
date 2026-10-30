# H2 Draw interior-entry and format-literal audit

## Result

Static inspection found no supported direct ARM branch/call from a different ledger function and no aligned absolute code pointer into the requested overwrite interval `[0x002CAFD4,0x002CB59C)`. The decoded direct branches targeting that interval are all self-references from the original Draw function. One of them originates in the original Draw suffix beyond the proposed in-place main body: `0x002CB748: bgt 0x002CB0B0`. That edge is not an external caller, but it remains in unmodified suffix bytes if a patch overwrites only the new 1,464-byte main. Therefore the static result supports removing the main body from other functions' direct reachability, but does not alone certify the patch layout: the final builder must prove the new body returns without falling into the retained suffix, establish that the suffix has no independent entry, and reconcile the exact write interval.

The old inline `%s\0` at `0x002CB410` has one decoded reference: an ADR-form `add r1, pc, #0xb8` at `0x002CB350`, inside Draw and inside the overwritten main. No other ledger-function PC-relative literal load whose pool word contains `0x002CB410`, no ADR to that address, and no aligned absolute pointer to it was found. The Draw split probe moves the `%s\0` object into the tail cave and emits a relocation for the production main's pointer to the new local string. The audited old ADR is thus an internal reference that the replacement must retarget; no external static reader of the old inline literal was found.

## Pinned identities and ranges

- Reference image: pinned US v0.1.0 `extracted/exefs/code.bin`, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- Ledger input: `config/functions.csv`, SHA-256 `d293c3b0a8a53eaf3cf3750ece6ce0d7886fac3eda8293462cd4aa07ba2f38a1`.
- Original ledger row remains `0x002cafd0,1932,matching,ui,ui_func_002cafd0,src/engine/leaf_batch43_a.cpp`; this audit does not change it.
- Original Draw range: `[0x002CAFD0,0x002CB75C)`.
- Requested interior audit range: `[0x002CAFD4,0x002CB59C)` (1,480 bytes).
- Cache-split probe's production main size is 1,464 bytes (0x5B8). A 1,464-byte body starting at 0x002CAFD4 ends at 0x002CB58C, 16 bytes before the requested 0x002CB59C end. If it starts at the original entry 0x002CAFD0, it ends at 0x002CB588; the requested interval then begins four bytes into that body and extends 20 bytes beyond its end. The patch manifest must state the actual main write start/length and which bytes at the boundary are deliberately replaced or retained.
- The cache-split source/object identities recorded in `docs/agent-work/h2-draw-cache-split-probe.md` are source SHA-256 `e5c6414cd37d2d6fc9928ca85eb5466a8c07bcec224a887616cb383ac408d64c` and object SHA-256 `0513196e3d93398036feba0177fc92cadadba87589068dc0605da64b0658ede2`. These identify the size probe, not a final patched image.

## Method

This was a read-only static scan of the configured image and ledger. It parsed 10,967 ledger function extents and used `.text` VMA 0x00100000, file offset 0, and size 0x002FE624 from `config/game_info.json`. A word-aligned sweep checked ARM B/BL/BLX immediate encodings (signed imm24 displacement from PC+8, including BLX H bit), excluding the known Thumb CRT interval `[0x00100048,0x00101300)`. Candidate branch targets were then decoded against ledger-owned function spans with Capstone 5.0.7 in ARM mode. A separate every-four-byte sweep over the complete code image checked absolute word values into the interior, including values with bit 0 cleared for possible Thumb-tagged pointers. For the format string, the scan checked PC-relative LDR/VLDR literal-pool loads and ADR-shaped ADD/SUB from PC, then scanned all aligned words for an absolute pointer to 0x002CB410.

The raw branch-encoding sweep and Capstone decode produced the same 17 target hits. All are attributed to `ui_func_002cafd0`; 16 source instructions are within the requested interval and one is the preserved-suffix back-edge at 0x002CB748. There are zero aligned absolute code-pointer hits into the requested interval, including when bit 0 is masked. The whole-file absolute-pointer sweep found zero references to 0x002CB410.

The branch hits, shown as source → target, are:

- Within the proposed main interval: `0x002CB108→0x002CB130`, `0x002CB120→0x002CB130`, `0x002CB190→0x002CB1A4`, `0x002CB1B8→0x002CB414`, `0x002CB208→0x002CB21C`, `0x002CB244→0x002CB308`, `0x002CB284→0x002CB298`, `0x002CB2F4→0x002CB308`, `0x002CB328→0x002CB3A8`, `0x002CB3B0→0x002CB4F8`, `0x002CB3F0→0x002CB430`, `0x002CB3F4→0x002CB51C`, `0x002CB42C→0x002CB1CC`, `0x002CB46C→0x002CB480`, `0x002CB4E0→0x002CB51C`, and `0x002CB4F4→0x002CB51C`.
- From preserved original Draw suffix into the main interval: `0x002CB748→0x002CB0B0` (`bgt`, the original row-loop back-edge).

The 0x002CB1B8 target is executable code at 0x002CB414 (`mov r2,#0x0c`), immediately after the `%s\0` bytes and alignment padding; it is not a branch into the string itself. The string is at function-relative offset 0x440. The single ADR reference at 0x002CB350 targets 0x002CB410, and both instruction and literal lie inside the proposed main replacement. This report records that the reviewed split object has a local `.rodata` `%s` relocation to its cave string; the future patcher must resolve it to 0x003FEED0 under the proposed layout and prove the resulting format argument at the final address.

## Placement conclusion and limits

No cross-function direct entry or aligned static pointer into the requested main interval was observed, so there is no static evidence here that a different ledger function calls into the middle of Draw. The original Draw body contains several cross-edges between its main and suffix: in particular, main instruction `0x002CB0AC` branches to suffix `0x002CB74C`, and suffix instruction `0x002CB748` loops back to main `0x002CB0B0`. Those original instructions are replaced only if their source addresses fall within the exact write interval; otherwise they remain stale. A valid in-place main replacement must return through its own epilogue and must not fall through into retained original bytes. Because the exact write window in the task is 16 bytes longer than the measured 1,464-byte production main under either natural start convention, resolve this before building the patch.

The scan is not a proof of absence for indirect callback/task tables that contain unaligned or transformed addresses, runtime-generated references, non-ledger/data-code ambiguities outside the known Thumb interval, Thumb branches outside the excluded CRT interval, computed branches, or pointers encoded in formats other than one aligned word. The `.text` sweep can decode inline data as candidate instructions; the 17 matches were individually checked as aligned conditional/unconditional ARM branch instructions belonging to the Draw ledger extent. The absolute-pointer sweep intentionally covers aligned words only. No code was compiled, no image was changed, and no emulator, RSP, profile, or host input was used.

## Next action

Have the placement-builder owner use this audit alongside a final-address control-flow check. The builder should pin the exact replacement range, preserve or retarget the format argument, prove that the new Draw body returns before any retained original suffix, and include the `0x002CB748→0x002CB0B0` old back-edge in its overwrite/reachability assertions. Then compare the production Draw symbol and the combined Calc/Draw patched image at final addresses; this static audit is not semantic or runtime approval.
