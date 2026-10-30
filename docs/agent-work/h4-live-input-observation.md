# H4 live camera-input observation

## Result

The paired private Azahar runs reproduce the H3 Shinjuku checkpoint in both the original and H3-patched images. After 250 field callbacks, the camera task at `0x001FA840` calls the 320-byte reader at `0x0027FBC8` from `0x001FA948`. Its live arguments are mode 0, two adjacent stack output pointers, and a float in `r3`; the neutral reader returns 1 and writes two zero floats. The view slot `0x00447E88` points to `0x004BCCd0` in both runs. Its object is readable for 0x170 bytes.

At the helper's observed return boundary, a controlled GDB probe wrote only the two validated output slots and preserved the natural return value 1. The input buffers at `0x004E3C28` and `0x004E3C48` were not modified. The camera caller then updated the view state. The neutral control left all 0x170 bytes unchanged across the camera call. An X output of +0.5 changed selected anonymous floats at view offsets +0x24/+0x30/+0x4C/+0x50 from 250/250/270/270 to 261.666656/285/300/−0. An X output of −0.5 changed them to 238.333328/215/240/180. Both sign probes also set +0x15C to 65. Original and patched view prefixes were byte-identical for each probe.

This is causal evidence that the live analog-query result drives state in the active view object, with opposite responses for opposite X values. The offsets remain unnamed; this does not establish the character's movement, a visual camera change, the real Azahar/keyboard input path, interaction, or a zone transition. The `um win drive` focus attempt returned `focus -> fail` because Windows reported `foreground: Idle`; it was abandoned, and the runner now uses GDB-only probes.

## Runtime evidence

Each report and its `original.json` / `patched.json` are retained under:

`build/agent-work/H4-semantic/h4-live-input-observation/run-001/results/`

| Run | Controlled output | Output SHA-256 |
|---|---:|---|
| `runtime-field-call-probes-049` | Natural zero | `85FC0C848679761DD9B5B9CBA6ED22F1F4D293C24DB399245742387840D2DBAF` |
| `runtime-axis-x-positive-050` | `(0.5, 0.0)` | `13564193001545EB778872EF355AD23713BF0A30695D6AADA114F86E5C5FF1A5` |
| `runtime-axis-neutral-control-051` | Natural zero, view no-change control | `97F54D763CB4A7E67AC72BE0E99B4C02E92349F934FA15C2157DA6C54AC9962F` |
| `runtime-axis-x-negative-052` | `(-0.5, 0.0)` | `A066EA90979FC23E23A1548A42B5AE97522B05474BE070ACA72754A89C446235` |

The original save SHA-256 remained `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`; every successful paired report says both staged saves and non-mod profile files were unchanged. H3 offline differential, in-place placement/interworking, and caller composition passed immediately before the runtime sequence. Runtime probes did not change the on-disk code image.

## Retried probes and limits

- `runtime-field-call-probes-048` was an invalid breakpoint-order attempt: the already-stopped field-manager breakpoint remained armed, so both requested probes stopped at `0x00208CE8`. Its hit data is discarded.
- `runtime-circle-right-046` and `runtime-circle-right-047` did not apply keyboard input. The first did not focus the emulator; the second confirmed `focus -> fail` and `foreground: Idle`, then the runner closed Azahar. Neither run produced semantic input evidence. The keyboard hook was removed from the shared runner.
- Captures do not show a screenshot of the controlled camera response. The data above is memory-level evidence only.

## Exact paired commands

The common command used the private staged profiles at `E:/SMT4decomp/build/agent-work/H3-semantic/h3-runtime-isolated-run-042`, `--confirm-load --callbacks 100 --post-callbacks 60 --field-ticks 250`, and breakpoints `0x001FA840`, `0x0027FBC8`, `0x002767D4`. The positive and negative runs added `--field-axis-output 0.5,0.0` and `--field-axis-output=-0.5,0.0`, respectively. The neutral reports omitted that option. All output stayed under the ignored `build/` directory.
