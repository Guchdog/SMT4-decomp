# H1 title transition: static callback-target audit

## Scope and pinned image

This is a static trace of the two indirect callback slots reached by the H1
title transition. It identifies candidate targets from object construction and
registration code; it does not establish which target a live title instance
uses or claim that either callback ran in Azahar.

The preserved image is `extracted/exefs/code.bin`, SHA-256
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
Relevant exact ARM bodies are retained in `src/engine/leaf_batch16_c.cpp`
(`0x002872B0`), `src/engine/leaf_batch41_b.cpp` (`0x0020FFAC`),
`src/engine/leaf_batch28_a.cpp` (`0x0014EF80`),
`src/engine/leaf_batch44_a.cpp` (`0x00153F8C`),
`src/engine/leaf_batch40_b.cpp` (`0x002A6108`), and
`src/engine/leaf_batch43_a.cpp` (`0x002A5CA4`).

## Callback sites and object-layout match

At `0x001EA0CC`, the title callback passes the child reached through
`work+0x90 -> handle+8` to `0x002872A4`. If the signed word at child `+0x34`
is positive, execution falls through to the adjacent body at `0x002872B0`.
That body loads `object = [child+0x4C]` at `0x002872B4`, then loads
`r1 = [object+0x4C]` at `0x002872C4` and calls it with `BLX r1` at
`0x002872E4`. The callback argument is `[object+0x50]` (loaded at
`0x002872C8`); the body also uses object fields `+0x38`, `+0x3C`, `+0x44`,
`+0x48`, and `+0x58`.

The layout is consistent with the model controller path:

- `include/engine/asd_model.h` places `AsdModel::node_count` at `+0x34` and
  `AsdModel::anim_controller_alt` at `+0x4C`.
- `src/engine/asd_model.cpp` around `0x002A94E8` assigns
  `model->anim_controller_alt = AsdAnim_BindController(model_data,
  node_ptrs[0], max_index)`; the matching store to model `+0x4C` is at
  `0x002A95F0`.
- `AsdAnim_BindController` (`0x0014EF80`) calls
  `AsdRenderNode_Bind` (`0x00153F8C`). The latter allocates a 0x70-byte
  object and initializes the callback-related region, including fields
  `+0x38..+0x58`.

At `0x001EA0DC`, the title callback passes the same child to
`0x0020FFA0`. A positive signed child `+0x58` gate falls through to
`0x0020FFAC`. That body follows `child+0x2C`, checks model-data `+0x148`,
uses model-data `+0x28` as the grid descriptor and `+0x14C` as an index, then
loads a selected record pointer from the grid. It loads the callback from
`[record+0x4C]` at `0x0021000C` and calls it at `0x00210010`; the argument is
`[record+0x50]` (loaded at `0x0020FFF4`). It also uses record `+0x38`,
`+0x3C`, `+0x44`, `+0x48`, and `+0x58`.

The offsets match the model/track construction path:

- `include/engine/asd_model.h` places `AsdModel::model_data` at `+0x2C` and
  `mesh_count` at `+0x58`. `AsdModelData` has a grid-related field at `+0x28`,
  fields at `+0x148` and `+0x14C`, and related indexed-grid use in the model
  loader.
- `src/engine/asd_model.cpp` around `0x002A94E8` creates 0x74-byte animation
  tracks with `AsdAnim_CreateTrack` and `AsdAnim_SetupTrack`, then stores track
  pointers in model-data grids. The node-set path around `0x0031E38C` also
  creates and stores tracks in a model-data grid.
- `include/engine/asd_scene.h` documents the matching 0x74-byte track prefix:
  current/previous at `+0x38/+0x3C`, parameters at `+0x44/+0x48`, evaluator
  callback/argument at `+0x4C/+0x50`, and active byte at `+0x58`.

These field and construction matches make model render/animation track objects
the strongest static explanation for both callback slots. The addresses do
not, by themselves, prove that every H1 resource instance uses a particular
track subtype.

## Registered target candidates

The pinned image and preserved source establish two target values:

| Target | Construction/selection evidence | Selection condition |
| --- | --- | --- |
| `0x0015555C` | `AsdRenderNode_Bind` loads literal `0x0015555C` from `0x001543B0` and initializes `[object+0x4C]` at `0x00154054`. `AsdAnim_CreateTrack` loads the same value from `0x002A61E4` and stores it at `0x002A6194`. | Default. Type byte 0 explicitly keeps/selects this value; other values not handled by the conditional override retain the initialized default. |
| `0x00151404` | `AsdRenderNode_Bind` loads literal `0x00151404` from `0x001543C0`; `AsdAnim_SetupTrack` loads it from `0x002A5FB8`. | Selected when the source object's byte at `+0x10` is 1. |

`AsdRenderNode_Bind` reads the source byte at `+0x10` at `0x001540C0`.
Type 0 retains the initialized callback (`0x0015555C`); type 1 loads
`0x00151404` and stores it at object `+0x4C` at `0x001540DC`. Other values
skip the override and retain the default.

`AsdAnim_CreateTrack` initializes the track callback to `0x0015555C` at
`0x002A6194`. `AsdAnim_SetupTrack` obtains a source pointer from the setup
descriptor, reads its byte at `+0x10` (`0x002A5CEC`), and stores
`0x0015555C` for type 0 or `0x00151404` for type 1 at `0x002A5D08`.
Other values skip that store, leaving the constructor default.

The generic setter `0x00254C6C` is additional corroboration: it selects the
same two literal targets from its selector argument and stores one at the
selected object's `+0x4C`, while setting byte `+0x58`. Its direct callers
are outside the title setup path identified here, so it is not used as proof
of the H1 instance's registration route.

`0x0015555C` is an executable ARM entry immediately following the epilogue of
the neighboring routine at `0x00155540`; it is not represented as a separate
function start in the function ledger. `0x00151404` is a listed function
entry. Their inclusion as candidates is based on literal pointer values and
the registered callback slots, not on inferred semantic names.

## Certainty and unresolved runtime facts

**Observed statically:** both H1 call sites load callback pointers from
`+0x4C` in objects with the same parameter, argument, value, and state offsets
used by the preserved model render/animation-track builders. The builders
register `0x0015555C` by default and select `0x00151404` for source type byte
1.

**Strong inference:** the two H1 callbacks are instances of those model
render/animation-track callbacks. The first path matches
`AsdModel::anim_controller_alt` construction; the second matches model-data
track-grid construction and its record layout.

**Unknown:** the loaded title model/source bytes at the relevant `+0x10` type
fields, the selected record's exact source object, and therefore which of the
two targets is present in either live callback slot. The callback targets'
actual runtime invocation and effects in Azahar are also unobserved. A runtime
snapshot or inspection of the exact loaded title model data is needed to pick
the target for each slot. No synthetic callback stub should be relabeled as
one of these real callbacks without that evidence.

## Title resource files located in the local CCI

The H1 caller at `0x001E9B3C` and `0x001E9B4C` loads
`title/title_top1.bam` and `title/title_top2.bam`, respectively. Both files
were read by range from the user's decrypted CCI without writing or modifying
the ROM. The CCI RomFS base calculation was cross-checked against the existing
`TitleTable.tbb` extraction hash before reading these ranges. The local
`extracted/romfs_index.json` hash is
`dc9e2d1b6daef9b6c7e7b573ed080fcd8dd8499e96fcc6a5b3cc398be2792aad`.

| Resource | RomFS offset | Size | SHA-256 |
| --- | ---: | ---: | --- |
| `/title/title_top1.bam` | `0x6EA46080` | 778,496 | `109c1ce81f06bb90484dda4e685564028b593667a5f16493d44157efe7682e12` |
| `/title/title_top2.bam` | `0x6EB04180` | 774,272 | `eaa252616f8ba61ecda915cd1d381e2c4374fa78eb6289b86d6aa0358b5b904f` |

Both resources begin with `ATBC`; their declared file size at `+4` matches the
indexed size, and their header has zero entries at `+8`, `+0x0C`, and `+0x10`,
with `0x80` at `+0x14`. `MDLSIGN` begins at `+0x80`; a `CGFX` chunk begins at
`+0x100` and contains `DATA` at `+0x114`, followed by aligned `DICT`/`SOBJ`/
`CMDL` structures. The existing `AsdFindEplEntry` parser only resolves an
`EPLSIGN` table when its ATBC count is nonzero, and the current asset inspector
does not parse BAM/CGFX.

The file-header byte at `+0x10` is not the track source object's type byte
used by callback setup. `AsdModelData` describes an already-resolved runtime
object graph, not the serialized CGFX/BAM layout. Mapping the models' source
records and callback tracks requires decoding this Atlus CGFX variant (DICT,
CMDL, offsets/relocations) and understanding how the loader constructs the
type-bearing source object. Therefore the two candidate callback addresses
remain unselected for the live title.

A bounded read-only walk of the CGFX `DATA` dictionaries was also completed.
Each file has one `CMDL`, seven textures, and one entry each for skeletal,
material, and visibility animation. `title_top1` has 150-frame animations
with 18 transform, 14 material-color, and 18 visibility channels;
`title_top2` has 1200-frame animations with 11 transform, 14 material-color,
and 18 visibility channels. This confirms the assets contain the model and
animation structures implicated by the code, but it does not map the runtime
callback slot to a serialized member or reveal the source object's `+0x10`
type. The parsed record/category mapping follows the open-source structures in
[CGFX DATA](https://github.com/Gericom/EveryFileExplorer/blob/master/3DS/NintendoWare/GFX/CGFX.cs),
[DICT](https://github.com/Gericom/EveryFileExplorer/blob/master/3DS/NintendoWare/GFX/DICT.cs),
and [CANM](https://github.com/Gericom/EveryFileExplorer/blob/master/3DS/NintendoWare/GFX/CANM.cs);
the format's use in this Atlus wrapper is still under validation.
