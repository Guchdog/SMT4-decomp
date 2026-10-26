# H1 state-5 title-message caller composition

## Result

The private offline Unicorn composition executes pinned code from `0x001EA12C`
through the state-5 TBB lookup and address arithmetic, then returns from the
original `0x0029F10C` helper at `0x001EA160`. In the candidate image, only the
BL instruction at `0x001EA15C` is retargeted to the linked editable helper at
`0x01000030`; its forward-copy dependency is linked candidate code at
`0x01000000`. The four valid asset rows pass the defined projection (4/4), and
the selection-1 candidate-entry wrong-row mutation is detected.

The pinned call word is `ead302eb`; the candidate word is `b35738eb`. The patch
span is four bytes, with three byte values differing. No other image byte was
changed. Both images execute the original pinned TBB getters and caller
arithmetic. At the call site, the selected row pointer and color
`0x323232FF` match the frozen TitleTable asset. For rows 0..3, the payload
strings are respectively 36, 39, 25, and 28 bytes, with file offsets
`0x46`, `0x9C`, `0xF2`, and `0x148`; mapped caller pointers are
`0x02000146`, `0x0200019C`, `0x020001F2`, and `0x02000248`.

The comparison covers helper-entry pointer/LR, return `r0`, resume PC, SP,
`r4-r11`, `d8-d15`, FPSCR, full mapped data, separate title-main and
`0x564`-byte ButtonHelp work blocks, the caller-owned stack, and normalized
copy-call arguments/order. LR after the helper returns is volatile and is
reported rather than treated as required equality. Caller-saved registers and
condition flags are diagnostics. The candidate's bounded safe domain is valid
manager/work pointers, these bounded single-line strings, and non-overlapping
forward-copy spans.

The wrong-row control changes selection 1's candidate entry pointer from
`0x0200019C` to row 0 at `0x02000146`; it is rejected and produces a different
ButtonHelp text output. The frozen asset SHA-256 is
`edd6bc1de5388e5689f797861ae6947c7c339f9b6bdb63d6c35951d72020fa41`.

## Validation

Final fresh runner command:

```text
python tools/h1_title_message_caller_experiment.py --output build/agent-work/H1-semantic/h1-title-message-caller-composition/overnight-20261025-caller-compose-v1/run-05
```

It exited 0 and wrote `run-05/report.json`. The candidate compiled and linked
with one ARM compiler slot (`clang++ --target=armv6k-none-eabihf`, hard-float
VFPv2, `-O2`); compile and link both exited 0. The focused test command
`python -m unittest tests.test_h1_title_message_caller_experiment -v` exited 0
(4 tests).

## Limits

This is partial state-5 caller-window evidence, not full callback or lifecycle
coverage. Execution uses a synthetic active-state caller frame, stops at the
helper return, and uses a single frozen 880-byte TitleTable asset. It does not
exercise readiness/input behavior, resource-manager lifecycle, object
construction, rendering, other locales, malformed or overlong strings, invalid
pointers, or runtime/Azahar behavior. It demonstrates the selected private
composition boundary, not production integration or placement. Pinned copier
alignment can differ, so memory read/write footprints are not compared.
