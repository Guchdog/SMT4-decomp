# H4 Navi callback passive capture review

## Review result

The frozen inputs match the run-001 packet: all 19 declared SHA-256 pins verified with no mismatches. I independently inspected both raw paired reports, the runner branch that captures `0x00399D60`, the integration report, offline gate reports, and pinned ARM disassembly. The raw capture report SHA-256 is `13ad87a507acdcb4f45c5a2fda1057e269866ccd7d9b64fd7327a0d780f95467`; original and patched JSON hashes are `52b0affb03dcc3395749d4d7b59b0ba4d5840462a23369dfea16ffbb7111e71a` and `57888a3038a412c912ba76e654dd216086b12a786cfcc281c79ec7ef034bcb25`. The evidence supports that the installed `0x00399D60` callback was indirectly dispatched in this paired H3-derived H4 checkpoint. It does not establish callback behavior, input semantics, player movement, H4 interaction, transition, or broader equivalence.

## Runtime evidence and dispatch derivation

Both `original.json` and `patched.json` report the field manager reached and 250 recorded ticks. Each has exactly one probe at `0x00399D60`, with `hit=true`. The entry registers are `r0=0x086EB3C0`, `r1=0`, `r2=0x00399D60`, `r3=0`; `lr=0x001A95E8`. The global slot at `0x0044CDF0` contains host pointer `0x086EB380`, so entry `r0=host+0x40`. Both captures show the same registers, slot, pair bytes and relevant field checkpoint.

At `0x001A95B8`, the caller loads the current host pointer through slot `0x0044CDF0`; if `[host+0x30]` is zero, it adds `0x40` to `r0` and executes `BL 0x0039F1F0` at `0x001A95E4`. `0x001A95E8` is the next instruction and therefore the LR return address observed at callback entry. At `0x0039F1F0`, code reads the index from `[r0+4]`, computes `r0 + (index << 3)`, reads the pair at offsets `+0xB14/+0xB18`, then tail-dispatches with `BX r2` when the second word is zero.

The captured object prefix starts `00 00 00 00 02 00 00 00`, so `[r0+4]=2`. With `r0=host+0x40`, the selected pair is `host+0x40+(2*8)+0xB14 = host+0xB64`, with its second word at `host+0xB68`. Both raw reports identify the pair address as `0x086EBEE4` and return bytes `60 9d 39 00 00 00 00 00`, decoded little-endian as `(0x00399D60, 0)`. This matches captured `r2=0x00399D60`, `r1=0`, unchanged `r0`, and `lr=0x001A95E8`. Together the caller return address, index, live pair and callback entry provide dynamic support for this exact dispatch path.

The runner computes `pair_address=host+0xB64` and allows the read only when `0x10000 <= host` and `pair_address+8 <= 0xFFFFF000`; the reports record `range_valid=true` and the actual eight-byte RSP read succeeded. This is a numeric guard plus successful read in these runs, not a general memory-map proof. The callback-specific branch only reads registers, the slot, pair bytes and snapshots; it issues no guest-memory write there. The overall runner is not guest-write-free: checkpoint setup uses a temporary title-input stub and controlled title-work writes, then restores the stub. No axis output or physical input was injected.

## Paired integrity and gates

The paired comparison reports equal title entry/state, save-load callback snapshots, post-confirm events and progress, field-manager signature, and 250 ticks. `field_scene_semantics_equal` is a narrow recorded signature, not full scene-state equality. The staged original and patched saves each remain 151,088 bytes with SHA-256 `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9` before and after. The non-mod profile manifest is unchanged within each run; this does not establish that the original and patched profile baselines are identical.

The packet-pinned gate reports and handoff record successful pre-runtime checks: H3 final-image/IPS round trip, H3 entry differential and caller composition (with negative control detected and BL target low bit clear), H4 axis reader (119 cases, zero differences, mutation detected), H4 camera composition (six cases, mutation detected), plus runner AST parse and `--help`. These are bounded offline gates, not whole-game equivalence. I verified the recorded report hashes against the packet pins.

The runner's `finally` block terminates a live process, waits up to ten seconds, kills and waits if necessary, and restores any hidden save path. The integration report records both successful Azahar processes exited and loopback ports `54342/54343` left without listeners. The raw JSON contains save/profile snapshots but no process exit code or port-listener record, so those cleanup observations are supported by the integration record and runner logic rather than independently encoded in each raw report.

## Limits and recommendation

The preliminary 313-character profile-root attempt failed before the expected title-init breakpoint (`0x001EB02C`, observed PC `0x0`) and is not a valid sample. The short-root paired run completed. The root-length difference is correlated with the recovery; it does not isolate the cause. Only the first callback hit after the 250-tick settle was captured. The callback return and downstream effect were not observed. This closes the bounded question of whether this callback dispatch occurs in the captured checkpoint; it does not close claims about movement, live input handling, player ownership, H4 interaction, zone transition, or game-wide behavior. Continue with a bounded read-only trace of the callback's state effects if needed.
