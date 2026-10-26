# H1 title BAM loader trace: independent static review

## Review result

**Partial, with one material omission corrected.** The original trace correctly
separates serialized CANM member types from the runtime source discriminator
and correctly leaves the actual callback values unresolved. Its claim that the
`Res_LoadBam` implementation was not present in the inspected source was too
broad: the call target at `0x0029BDDC` is preserved as
`engine_func_0029bddc` in `src/engine/leaf_batch30_c.cpp`. Direct ARM decoding
shows a stronger title-resource-to-model path through this loader. That path
still does not identify a writer for the runtime target object's byte at
`+0x10`, nor demonstrate that the model track builders described in the prior
trace are invoked by this title load.

The pinned image is `extracted/exefs/code.bin`, SHA-256
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, matching
`config/game_info.json`.

## Independently verified addresses and fields

The title caller in `src/ui/ui_runtime2.cpp` invokes `Res_LoadBam` at
`0x001E9B3C` for `title/title_top1.bam` and at `0x001E9B4C` for
`title/title_top2.bam`, both with mode 7, storing returned handles at work
`+0x8C` and `+0x90`. State 3 polls both handles with `Res_IsLoadBusy`.
`Res_LoadBam` is declared at `0x0029BDDC`, and that address is listed in
`config/functions.csv` as a 140-byte matching ARM body.

Decoded ARM at `0x0029BDDC` shows this call sequence:

| Address | Observed operation |
| --- | --- |
| `0x0029BDE8` | calls `0x002A135C`, receives the manager/model handle |
| `0x0029BDF0`–`0x0029BDFC` | obtains the contained object at handle `+8` and stores the requested kind at object `+8` |
| `0x0029BE00` | calls `0x002B0434` with the BAM path to create/read a file request |
| `0x0029BE0C` | calls `0x002B0418` with mode 1 |
| `0x0029BE14`, `0x0029BE20` | calls `0x001181B0`, then `0x00138330` to obtain/process the loaded request data |
| `0x0029BE28` | calls `AsdModel_func_002B2B78` with the data pointer and owner argument; stores its returned animation-table handle into the contained object at `+4` |
| `0x0029BE40` | calls `0x002A9498` with the contained object and requested kind |
| `0x0029BE48`, `0x0029BE58` | registers the handle via `0x002B2928` and inserts it into a list via `0x002B2814` |

At `0x002A135C`, the manager helper allocates/zeros the handle and calls
`0x001FE470` at `0x002A13AC`, storing the resulting model object at handle
`+8`. The pinned 288-byte ARM body at `0x001FE470` allocates `0xA8` bytes
(`BL 0x002C54F0` at `0x001FE498`), zeroes that object (`BL 0x002C4B30` at
`0x001FE4A4`), initializes fields including `+0x0C/+0x10` to `-1`, and
appends it to a manager list (`BL 0x002B2814` at `0x001FE52C`) before
incrementing the manager counter at `+0x3C`. Its complete direct call set is
`0x002C54F0`, `0x002C4B30`, and `0x002B2814`; it has no call to
`0x002B3CB0` or `0x002A94E8`.

This conflicts with the readable `#if 0` draft at `src/engine/asd_model.cpp`
lines 936–994: lines 957 and 972 call `AsdGfx_CreateResource`, and line 994
calls `AsdModel_func_002a94e8` for mode 0. These operations are absent from
the pinned ARM body at `0x001FE470` and cannot be used as evidence for the
title loader path. The new evidence establishes that the title loader reaches
a model-object allocator/initializer, not that this constructor creates model
data or invokes the table-building function. `0x002A9498` then stores
the returned animation-table signature pointer at table `+0x18`, calls
`0x002A9ACC` at `0x002A94C8` with the flags and a zero source argument, and
calls `0x0014515C` at `0x002A94D8` to parse ATBC metadata. The source-less branch
in the readable `0x002A9ACC` draft uses name descriptors and `AsdRes_Create`;
it is distinct from the source-backed resource descriptor branch.

`AsdModel_func_002B2B78` (`src/engine/asd_model.cpp`) is an animation-table
wrapper: it stores the input data/owner and examines ATBC offsets to retain
MDLSIGN/signature and chunk pointers. Its observed `+0x10` store is into the
newly allocated table wrapper (`table+0x10`), not into the resolved model
target later passed to `AsdAnim_SetupTrack`. This is a concrete nearby field
that must not be mistaken for the target discriminator.

The previous trace's model table path remains supported as a path within the
ARM body at `0x002A94E8`: it resolves 16-byte entries through relative pointer
field `entry+0x28` from the node table at model source-data `+0x68`, mesh table
`+0x70`, and draw table `+0x78`. Setup calls at `0x002A97E8` and
`0x002A99DC` pass resolved targets as descriptor word zero. The separate
model-view path at `0x0031DC4C` resolves draw targets from its `+0x78` table
and calls setup at `0x0031E3A8`. However, I found no direct `0x002A94E8` call
in the 140-byte `0x0029BDDC` loader, and the exact `0x001FE470` body does not
provide the draft's link to it. `0x002A9498` is a different, neighboring
function. The static evidence does not establish that these track builders
execute for the title BAM instances.

At `AsdAnim_SetupTrack` (`0x002A5CA4`), descriptor source is loaded at
`0x002A5CB8`, and the source byte is read at `0x002A5CEC`. The destination
callback slot is written at `0x002A5D08`: type 0 chooses/retains
`0x0015555C`, type 1 selects `0x00151404`; the track constructor initializes
`0x0015555C` at `0x002A6194`. Separately, the serialized CANM member's 32-bit
primitive type is at member `+0x08` (observed values 5/6/2 in the asset audit).
These are distinct objects, offsets and widths. This review found no basis to
map those serialized values to runtime byte `[source+0x10]`.

## Search for a missed materializer or discriminator writer

I searched assigned source/listings for `Res_LoadBam`, its target address,
`AsdGfx_CreateResource`, `AsdModel_func_001FE470`, and the track setup/read.
This found and verified the omitted `0x0029BDDC` implementation and its call
to `0x002A9498`. The search is limited to the declared source/listing corpus;
it is not a proof that no other indirect or unindexed loader exists.

The `0x002B3CB0` body is a 1,792-byte non-streaming resource builder retained
in `src/engine/leaf_batch43_a.cpp`. Its disassembly initializes a large
model-data object and fields including `+0x148` through `+0x178`, `+0x188`,
and later `+0x1F4` through `+0x231`; it includes dynamic virtual calls. In the
inspected span I found no direct `STRB [reg,#0x10]` that can be identified as
the resolved track source's discriminator assignment. This does not rule out
a write by one of its helpers/virtual targets, another constructor, or a
different source base. The `0x0029BDDC` title load calls `0x002A9498` and its
visible `0x002A9ACC` path, not `0x002B3CB0` directly; the mapping from serialized
CGFX targets to the runtime track source is still missing. The earlier trace's
separate assertion that `0x001FE470` calls `0x002B3CB0` and then
`0x002A94E8` is specifically contradicted by the pinned ARM body. Those calls
occur only in the readable `#if 0` draft and are not proven edges.

## Actual H1 gate bindings and minimum next observation

Static constructor evidence still gives only two candidates, not live values.
Gate A (`0x001EA0CC`) reads callback `[object+0x4C]` after resolving
`[child+0x4C]`; Gate B (`0x001EA0DC`) resolves a model-data grid record and
reads its callback at record `+0x4C`. To choose the actual values, capture the
resolved object/record pointer, callback `+0x4C`, argument `+0x50`, and gate
value at each gate after both title loads complete. To explain why a track
setup selected that callback, also capture the exact setup source pointer and
its byte `+0x10` on entry to `0x002A5CA4` (or the corresponding source on
`0x00153F8C`). Correlate the captures with the loaded title resource identity.

No candidate, integration, or runtime evidence is reviewed here. The static
trace is **partial**: title requests reach a concrete model loader and its
resource initialization calls, but the CGFX relocation/materialization and
runtime discriminator write remain untraced. Neither live H1 gate binding is
statically selected by this evidence.
