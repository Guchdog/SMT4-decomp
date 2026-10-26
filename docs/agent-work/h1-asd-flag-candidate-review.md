# Independent review: `0x002C00D4` ASD flag candidate

## Review result

**Partial, bounded review.** The pinned Thumb body, candidate C++ and final private ARM differential report agree on the single-threaded ordinary-memory contract: load one 32-bit word at `r0`; for a zero value, store 1 and return 1; otherwise leave memory unchanged and return 0. The final report has 135 passing cases and detects the missing-store negative control. This supports the candidate only for the exercised valid, aligned ordinary-RAM domain. It is not evidence of atomicity, H1 execution, whole-caller behavior, or production integration.

All 21 frozen packet input hashes matched. The pinned image hash is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; candidate source `3f6ec2ff1fa6f9d968766498decacaf27221e61e04767528554033eae2887586`; runner `67b9fd6837b26d175d73d828c015b7783a8b8cb0ca6adba4bf56559a30d92b14`; final report `ea7218ab936f3ee5f334fdbfe0321fddfb254b00504c0fe5236056a3b9662c3c`.

## Pinned boundary and contract

At image offset `0x001C00D4` (`VMA 0x002C00D4`), the 18 executable bytes are:

`01 68 00 29 01 d0 00 20 70 47 01 21 01 60 08 00 70 47`

They decode in Thumb mode as:

| Address | Instruction | Effect |
|---|---|---|
| `0x002C00D4` | `ldr r1,[r0]` | One word load from the pointer in `r0`. |
| `0x002C00D6` | `cmp r1,#0` | Select zero/nonzero path. |
| `0x002C00D8` | `beq 0x002C00DE` | Zero goes to store path. |
| `0x002C00DA` | `movs r0,#0` | Nonzero return value. |
| `0x002C00DC` | `bx lr` | Nonzero early return. |
| `0x002C00DE` | `movs r1,#1` | Prepare stored/returned value. |
| `0x002C00E0` | `str r1,[r0]` | Store one word through original `r0`. |
| `0x002C00E2` | `movs r0,r1` | Zero-path return value 1. |
| `0x002C00E4` | `bx lr` | Return. |

The next halfword at `0x002C00E6` is `0xFFFF`. The 20-byte ledger span includes it, but both return instructions stop execution before it. The report’s `return_address`, executed address list and `trailing_halfword_executed=false` match the bytes. The source listing’s `.byte` sequence includes the padding, which is not part of the executable body.

The candidate signature `extern "C" u32 candidate_002c00d4(u32* flag)` is a 32-bit pointer and return under the reported ARM target. Its ordinary load, zero branch, conditional ordinary store and return match the decoded body. It does not use atomics or volatile, which is consistent with the instruction sequence and appropriately avoids claiming synchronization. ARM AAPCS preserves `r4-r11`, `sp`, and VFP callee-saved `d8-d15`; the original body touches only `r0/r1` and flags, while the compiled C++ ABI preserves the callee-saved state. The report compares `r0`, callee-saved state, SP, d8-d15, RAM, stack, and read/write address footprints. It intentionally does not compare caller-saved registers or NZCV.

The footprint hooks use sets of touched addresses, so they do not establish access multiplicity or ordering by themselves. The pinned instructions establish the relevant order here: one load precedes the branch, and at most one store follows it. The memory image comparison and missing-store negative control add useful independent checks for the store effect.

## Differential artifacts

The final report’s reference and source hashes match the packet. It records compiler Clang 23.1.3 and Unicorn 2.1.4, seed `20261025`, 128 seeded cases plus seven directed cases (`zero`, `one`, `positive`, `high-bit`, `negative-u32`, `signed-min`, `max-positive`), totaling 135. Every listed pointer offset is word-aligned, all cases passed, and the result/footprint fields agree between original and candidate. In zero input the report gives both return values as 1 and matching four-byte read/write footprints; nonzero inputs return 0 and show matching reads with no writes. The `missing-store` control on the zero case is detected as `data memory differs`.

The final run is distinct from the two documented superseded harness attempts: first attempt failed to enter Thumb state; second selected a banked LR=0 by changing CPSR after setting LR. Those are accurately marked expected failures in the handoff. They are not final-run evidence. The final `r3` run and focused report test are recorded as exit 0; this review did not rerun them, compile, or invoke an emulator.

## Caller cross-check

I independently decoded the three direct ARM callsites listed in the report:

- `0x001099B4`: `BLX 0x002C00D4`, followed by `CMP r0,#0` at `0x001099B8`; the sound path gates its one-shot mix-level initialization on nonzero.
- `0x001F6948`: `BLX 0x002C00D4`, followed by `CMP r0,#0` and a zero branch at `0x001F694C..0x001F6950`; the effect-matrix initialization is gated on nonzero.
- `0x0036C380`: `BLX 0x002C00D4`, followed by `CMP r0,#0` at `0x0036C384` and a zero branch at `0x0036C38C`; the UI command initialization is gated on nonzero.

The H1-related static path also merits explicit qualification. At `0x00155548`, wrapper code directly calls `0x002A2414`. In the pinned body of `0x002A2414`, `0x002A2428` loads literal `0x00473530` into `r0`; `0x002A242C` then `BLX`es `0x002C00D4`. Thus this nested helper receives a pointer to the global word at `0x00473530`, not its loaded value. The helper’s returned `r0` is compared to zero at `0x002A2430`; a nonzero result gates initialization stores. The wrapper subsequently adjusts an argument and calls `0x002A23FC`, then returns its context. This confirms a static call path and the return-polarity use. It does not establish that a live H1 object selects or reaches this wrapper at runtime.

The candidate report’s `caller_evidence` lists the three direct sites above but omits the statically encoded `0x00155548 -> 0x002A2414 -> 0x002A242C -> 0x002C00D4` path. That omission does not contradict the helper semantics or invalidate the three listed sites; it means its caller evidence is not an exhaustive H1 caller trace. The existing wrapper review likewise limits its claim to static code and leaves live H1 binding/reachability unresolved.

## Limits and recommendation

The evidence is finite differential testing over valid, word-aligned ordinary RAM. Invalid and unaligned pointers, MMIO, concurrent observers, interrupt races, exception behavior, timing, OS effects, and atomicity are unsupported. Caller analysis is static. No H1 boot/gameplay run, caller-level differential, production replacement, or integration was performed. The exact ledger label remains unchanged; this candidate is not byte-identical.

Keep the candidate as an experimental single-threaded helper. Any promotion should retain the ordinary-memory-only contract and separately validate its real caller/global lifecycle, especially H1 runtime binding, before making runtime claims.
