# H1 title BAM tracks vs. runtime callback source type

## Question and scope

Can a serialized animation member from the local `title_top1.bam` or
`title_top2.bam` be identified as the runtime object whose byte at `+0x10`
selects callback `0x0015555C` versus `0x00151404`?

The decrypted CCI was read by bounded file ranges only. No ROM data was
extracted or written. The CCI and BAM identities/layout are cross-checked in
`title_real_callback_target_audit.md`; this audit adds animation-member
metadata and compares it with the callback setup path.

## Observed serialized members

`tools/title_bam_inventory.py` confirmed one CMDL and one CANM in each of the
skeletal, material, and visibility DATA dictionaries for both BAMs. A bounded
read of the CANM member dictionaries exposed these target paths and the
serialized member primitive types:

| BAM | CANM group | Members | Serialized primitive type |
| --- | --- | ---: | --- |
| `title_top1` | `SkeletalAnimation` | 18 | 5 (`TransformAnimation`) |
| `title_top1` | `MaterialAnimation` | 14 | 6 (`RgbaColorAnimation`) |
| `title_top1` | `VisibilityAnimation` | 18 | 2 (`BoolAnimation`) |
| `title_top2` | `SkeletalAnimation` | 11 | 5 (`TransformAnimation`) |
| `title_top2` | `MaterialAnimation` | 14 | 6 (`RgbaColorAnimation`) |
| `title_top2` | `VisibilityAnimation` | 18 | 2 (`BoolAnimation`) |

Examples of the actual dictionary paths are skeletal targets `Dummy_title_d`,
`title_d1`, and `title_u1`; material targets such as
`Materials["black_title"].MaterialColor.Diffuse`; and visibility targets
`Meshes[3].IsVisible` through `Meshes[20].IsVisible`. These are member/path
identifiers, not callback registrations.

The CGFX `CMDL` resource in each BAM is named after the BAM. Its standard
header begins with type word `0x40000092`; the eight bytes at CMDL `+0x10` are
zero in both local resources. This is a serialized CMDL-header observation,
not evidence that the runtime callback source pointer points at the CMDL
header.

## Why this does not select either callback

The primary format parser [EveryFileExplorer `CANM.cs`](https://github.com/Gericom/EveryFileExplorer/blob/master/3DS/NintendoWare/GFX/CANM.cs)
defines each CANM member record as flags at `+0x00`, relative path at `+0x04`,
primitive type at `+0x08`, followed by type/flag-dependent constant or curve
references. The animation member's primitive type is therefore a 32-bit
serialized format field at `+0x08`; it is not the byte read by the game at
runtime source-object `+0x10`.

In the pinned ARM at `0x002A5CA4`, `AsdAnim_SetupTrack` takes the first pointer
from its caller-built descriptor (`ldr r0,[r1]` at `0x002A5CB8`) and reads
`[source+0x10]` at `0x002A5CEC`. It stores the default evaluator for byte 0,
the alternate evaluator for byte 1, and leaves the constructor default for
other values. The statically reconstructed model callers build descriptors
from resolved model mesh/draw/node records (see
`src/engine/asd_model.cpp` around `0x002A94E8` and `0x0031DC4C`); the CANM
member dictionary parser alone does not establish which such resolved record
feeds a particular H1 callback slot.

Thus, the asset data now identifies concrete animation targets and their
standard CGFX primitive types, but it does **not** prove a mapping from any
target to runtime `source+0x10`, nor does it choose `0x0015555C` or
`0x00151404` for a live slot. That requires the Atlus loader's mapping from
CANM/CMDL target paths to its resolved source records, or a read-only runtime
snapshot of the exact title model objects and callback slots. Neither is
available in this static file-only pass. Treating primitive type 2/5/6 as
the runtime byte would be unsupported.

## Evidence sources

- Local decrypted CCI ranges for `/title/title_top1.bam` and
  `/title/title_top2.bam`, validated by the read-only range/hash procedure in
  `tools/title_bam_inventory.py` and `tests/test_title_bam_inventory.py`.
- Pinned `extracted/exefs/code.bin` and the existing callback-target audit in
  `title_real_callback_target_audit.md`.
- Primary format structures: [CANM](https://github.com/Gericom/EveryFileExplorer/blob/master/3DS/NintendoWare/GFX/CANM.cs),
  [DICT](https://github.com/Gericom/EveryFileExplorer/blob/master/3DS/NintendoWare/GFX/DICT.cs),
  [CGFX DATA](https://github.com/Gericom/EveryFileExplorer/blob/master/3DS/NintendoWare/GFX/CGFX.cs),
  and [CMDL](https://github.com/Gericom/EveryFileExplorer/blob/master/3DS/NintendoWare/GFX/CMDL.cs).

No parser, test, production source, shared progress document, or ROM was
modified for this audit.
