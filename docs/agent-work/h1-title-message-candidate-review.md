# Independent review: H1 title/message candidates

## Verdict

**Supported within the stated safe domain; overall evidence remains partial.** I matched all 13 frozen packet input hashes; independently decoded the pinned helper and copy bodies, rehashed all three reported original spans from the pinned image, inspected the candidate preconditions and final run-02 report, and verified its counts, projections, control failures, and artifact hashes. The report supports 9 helper fixtures plus 176 direct copy cases, 185 total. I did not compile, rerun tests, or use a game runtime.

The candidate is experimental and should remain unintegrated until actual localized row data, caller behavior, and runtime rendering are tested. The source's bounds are materially narrower than the original routine's unchecked behavior.

## Pinned helper `0x0029F10C`

The 316-byte span `[0x0029F10C, 0x0029F248)` hashes to `9e432ddfb9a774f0665383f3d790f83fb7b79b44121a8e96806a114e37314873`. It loads the manager structure address from its literal at `0x0029F244` (`0x0043DA28`) and loads the work pointer from manager `+4`. It does not null-check either pointer. The ABI is `r0=optional message pointer`, `r1=color`.

Both modes store color to work `+0x4CC`, clear `+0x550`, and store `0xFF` at `+0x554`. If `r0` is null, it clears byte `+0x4CB`, leaves `+0x55C` unchanged, and returns `0xFF`. Otherwise it clears `[+0x4D0,+0x550)`, then scans at most 128 bytes using signed-byte loads. It treats NUL and LF as delimiters; high-bit bytes remain non-delimiter content. It copies bytes before the delimiter to `+0x4D0 + line*0x40`, excluding LF/NUL. A second LF ends processing after the second line. If no delimiter appears within the scanned 128 bytes, it does not copy the incomplete trailing line. The non-null tail clears `+0x55C`, sets `+0x4CB`, and returns `1`.

The C++ candidate implements that scan and those state writes under an explicit safe domain: initialized, valid manager/work pointers; a non-null input with at least 128 readable bytes; and each copied line no longer than 64 bytes. The original has no line-length guard. A first copied line longer than 64 bytes crosses into the nominal second slot; a second line longer than 64 overwrites adjacent work fields; second-line lengths above 84 exceed the modeled `0x564`-byte work object. These inputs are excluded from the C++ safe domain rather than claimed as supported. The synthetic helper cases cover null reset, empty input, ordinary/max-size line, high-bit bytes, leading LF, two lines, the scan-boundary case, and a two-line NUL-at-index-127 case.

## Pinned copy `0x002C5FF4`

The 136-byte span `[0x002C5FF4, 0x002C607C)` hashes to `644501596cdc02773609b59f6b01e737be96c516e4546919af3c259c1b64746e`. Its ABI is `r0=destination`, `r1=source`, `r2=length`; it returns the advanced destination. It uses byte tails and aligned word operations, and can branch to optimized copy body `0x002BCF58` when the adjusted source is aligned. That 116-byte body hashes to `d4e075de5405e2393514369688bf643d3d2064f5386b321b2b9f0ee3d511e0fe`.

The editable copy candidate is a forward byte loop returning `destination+length`. Its explicit precondition is valid, non-overlapping source/destination ranges in ordinary memory. This is not `memmove`; overlap, invalid/null pointers, and MMIO access ordering are not supported. The direct matrix spans every source and destination alignment modulo four and lengths `{0,1,2,3,4,7,8,9,31,32,33}` (176 cases). The report also records that the pinned optimized body was entered in 28 direct cases and five helper copy calls. Those counts characterize original ARM path coverage; the comparison code does not require the C++ loop to reproduce that internal optimization branch.

## Run-02 differential and controls

The run-02 report hash is `90bcc2f28a02858abbd12c93f3b6167ccadf0dec7a0565f511605a07310d4d35`; the candidate ELF hash independently recomputes to `05059c43b7a1a55312c3c44556bf8386588005cc34e4e79f0f09b5769b6e041f`. The source hash matches the packet: `68c91fe472a631d9435daa0596161ddcbea70dba011abcecfe1be8df6422305e`. The run report records zero undefined symbols and successful compile/link commands (exit 0).

All nine helper cases and 176 direct-copy cases report pass, with no final mismatch. The comparison projection checks fault/return sentinel, `r0`, preservation/equality of `r4-r11` and SP, `d8-d15`, FPSCR, all `0x20000` mapped bytes, the `0x564` work slice, caller-owned stack, and ordered copy call arguments. `optimized_copy_entries` is reported as an original path-coverage diagnostic, not compared as a candidate equivalence field.

All three mutation controls are detected:

- `wrong_null_mode_return` produces an `r0` mismatch (`0xFF` versus mutant `0`).
- `omitted_color_store` produces a data mismatch at `0x020014CC` (original byte `0xFF`, mutant `0xA7`).
- `corrupt_forward_copy_bytes` produces a data mismatch at `0x020014D0` (original byte `0x54`, mutant `0xAB`).

The producer handoff records run-02 exit 0, five focused tests passing (exit 0), and its handoff-provenance check passing (exit 0). I inspected those records and the test assertions; none were rerun for this read-only review. The tests assert the reported case counts, safe boundary examples, full candidate source set, three detected controls, and evidence limits.

## Evidence limits and next action

The message strings and work memory are synthetic. The frozen packet contains no localized slot-`0x3A` TBB bytes, so actual H1 row contents and line lengths are unknown. The run does not execute the caller to construct the input pointer, test title initialization order, render text, or exercise a production build, emulator, Azahar, or game runtime. It also does not prove arbitrary pointers, inputs outside the scan/line domain, overlapping copy behavior, MMIO semantics, or behavior beyond the declared projection.

Keep this as bounded offline ARM differential evidence, not caller/runtime equivalence. Freeze and inspect the actual localized TBB data before claiming these line-length preconditions hold for game rows, then test the caller and rendered output before promotion.
