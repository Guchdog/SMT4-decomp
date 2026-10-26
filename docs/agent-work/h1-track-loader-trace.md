# H1 title BAM to runtime track source: static loader trace

## Result and evidence boundary

This read-only trace follows the two pinned title BAM requests through the
identified `Res_LoadBam` and model metadata helpers. The trace does **not** prove
that these title loads reach the separately identified mesh/draw track builders,
and it does not recover a write to the runtime track source object's byte at
`+0x10`. Therefore the actual callback binding at either H1 title gate remains
dynamic/unresolved; serialized CANM primitive types cannot be substituted for
that runtime byte.

**Review correction:** the independent review
[`h1-track-loader-trace-review.md`](h1-track-loader-trace-review.md) found that
the first version omitted the pinned `Res_LoadBam` body at `0x0029BDDC` and
treated calls in an uncompiled `#if 0` draft as if they described the pinned
`0x001FE470` constructor. They do not. The corrections below supersede those
earlier claims; the review file records the exact discrepancy and addresses.

The pinned `extracted/exefs/code.bin` identity is SHA-256
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, matching
`config/game_info.json`. The loader/track statements below use that image and
the preserved listings/drafts cited in the task packet and prior static audits.
The source drafts for several non-leaf functions are under `#if 0`; they are
readable reconstruction evidence, not proof of a fully built production path.

## Observed title resource requests

`Title` state 2 in `src/ui/ui_runtime2.cpp` requests:

| Address | Request | Stored handle |
| --- | --- | --- |
| `0x001E9B3C` | `Res_LoadBam("title/title_top1.bam", 7)` | title work `+0x8C` |
| `0x001E9B4C` | `Res_LoadBam("title/title_top2.bam", 7)` | title work `+0x90` |

State 3 checks `Res_IsLoadBusy` on both handles before advancing. The pinned
`Res_LoadBam` body at `0x0029BDDC` is retained in
`src/engine/leaf_batch30_c.cpp` (140 bytes). It creates a manager/model handle
through `0x002A135C`, issues and processes the BAM request through
`0x002B0434`, `0x002B0418`, `0x001181B0`, and `0x00138330`, builds an ATBC
metadata wrapper through `0x002B2B78`, initializes model metadata through
`0x002A9498`, then registers and lists the handle. The direct callees and limits
are cross-checked in the independent
[loader-trace review](h1-track-loader-trace-review.md). The relation from this
path to the separate `0x002A94E8` mesh/draw track builder remains unproven.
The local BAM range/hash observations are recorded in
`experiments/semantic_equivalence/title_real_callback_target_audit.md`:
`title_top1.bam` is 778,496 bytes (SHA-256
`109c1ce81f06bb90484dda4e685564028b593667a5f16493d44157efe7682e12`), and
`title_top2.bam` is 774,272 bytes (SHA-256
`eaa252616f8ba61ecda915cd1d381e2c4374fa78eb6289b86d6aa0358b5b904f`). Both
are ATBC wrappers with `MDLSIGN`/CGFX data; each contains CMDL and skeletal,
material and visibility CANM dictionaries.

## Serialized resource type versus runtime objects

The offline BAM audit observes CANM member type words at member `+0x08`:
skeletal transform type 5, material color type 6, and visibility boolean type
2. Those are serialized format values. The ATBC header's `+0x10` is also a
different field (zero in the observed wrappers). Neither field is evidence for
the byte loaded from a runtime target pointer at `target+0x10`.

The pinned title loading path and the separate track-builder path must remain
distinct until a caller edge connects them:

1. Title calls `Res_LoadBam` (`0x0029BDDC`), which calls `0x002A135C` to create
   a manager handle. That helper calls `AsdModel_func_001FE470` (`0x001FE470`)
   at `0x002A13AC` and stores its return at handle `+8`. The pinned 288-byte
   ARM body at `0x001FE470` allocates and clears `0xA8` bytes, initializes
   fields including `+0x0C/+0x10` to `-1`, links the object through
   `0x002B2814`, and increments its manager counter. Its direct calls are only
   `0x002C54F0`, `0x002C4B30`, and `0x002B2814`; it does **not** call
   `0x002B3CB0` or `0x002A94E8`.
2. The `src/engine/asd_model.cpp` `#if 0` draft around lines 936–994 includes
   `AsdGfx_CreateResource` and `AsdModel_func_002A94E8` calls that are absent
   from the pinned constructor. Do not use that draft as evidence for the title
   loader's call graph.
3. Back in `Res_LoadBam`, the returned request data is processed by
   `0x001181B0`, `0x00138330`, and `AsdModel_func_002B2B78`; the wrapper stores
   ATBC/signature metadata in its own table object. It then calls
   `0x002A9498`, which calls `0x002A9ACC` and `0x0014515C`. The `+0x10` store
   in `0x002B2B78` belongs to that table wrapper, not a proven track source.
   The title call path contains no established edge to `0x002A94E8`.
4. Separately, `AsdModel_func_002A94E8` obtains source tables through
   `*(model->source + 0x18)`. Its mesh table at `+0x70` and draw/controller
   table at `+0x78` contain 16-byte entries whose relative target at entry
   `+0x28` is resolved and stored in the model's pointer arrays. Track setup at
   `0x002A97E8` and `0x002A99DC` places the resolved mesh/draw target in
   descriptor word zero. This is a separate, statically understood path; the
   title BAM loader reaching it is not established.
5. The related model-view path `AsdModel_func_0031DC4C` also resolves mesh and
   draw targets from its `+0x68` / `+0x78` relative tables and passes the
   selected draw target to setup at `0x0031E3A8`. It separately creates node
   name handles with `AsdRes_Create` at `0x0031E204`; those handles are not the
   draw descriptor source.

The separate `AsdAnim_SetupTrack` (`0x002A5CA4`) loads descriptor word zero at
`0x002A5CB8`, reads byte `[source+0x10]` at `0x002A5CEC`, and selects a
destination callback at `+0x4C`: type 0/default is `0x0015555C`, type 1 is
`0x00151404`. `AsdAnim_CreateTrack` initializes the destination callback to
`0x0015555C` at `0x002A6194`. This establishes what that separate setup path
does, not that the title's `Res_LoadBam` requests call it. `AsdRenderNode_Bind`
(`0x00153F8C`) is a related 0x70-byte object constructor: it initializes a
callback at object `+0x4C` and reads its input source `+0x10` at `0x001540C0`,
overriding to `0x00151404` for value 1.

`AsdGfx_CreateResource` is retained as an ARM body (1,792 bytes) in
`src/engine/leaf_batch43_a.cpp`, but the title loader path above does not call it
directly. The independent static review found no identified writer for the
resolved track source's `+0x10` byte in the inspected body. This does not rule
out writes in indirect helpers, virtual targets, or another unindexed path.

## H1 callback slots and static resolution

Both H1 transition gates load callback slots from objects matching these
runtime layouts, but static constructors only give candidate registrations:

- Gate A (`0x001EA0CC` to `0x002872A4`, positive child `+0x34` falls through to
  `0x002872B0`) loads the controller object from `[child+0x4C]`, then callback
  `[object+0x4C]` and argument `[object+0x50]`. Constructor/layout evidence
  matches `AsdModel::anim_controller_alt`; callback candidates are the
  default `0x0015555C` and type-1 override `0x00151404`.
- Gate B (`0x001EA0DC` to `0x0020FFA0`, positive child `+0x58` falls through to
  `0x0020FFAC`) walks to model data and an indexed grid record, then loads
  callback `[record+0x4C]` and argument `[record+0x50]`. Track construction
  and layout evidence again show the same two candidates.

Neither constructor evidence nor the title BAM dictionaries chooses the
callback in a live slot. To establish actual bindings, the minimum useful
read-only observation is a snapshot at each gate of the child pointer and
gate value, followed by the resolved object/record pointer, its `+0x4C` callback
and `+0x50` argument. To also explain why a track setup chose that callback,
capture the exact descriptor source pointer and `[source+0x10]` at
`AsdAnim_SetupTrack` (or the analogous `AsdRenderNode_Bind` hit), with the
loaded title resource/model identity. Without such a snapshot or a recovered
loader writer, both H1 callback bindings remain dynamic.

## Evidence level and next action

- **Static caller/dataflow:** partial. The BAM names/mode/handles and the path
  through `0x0029BDDC`, `0x002A135C`, `0x001FE470`, and `0x002A9498` are
  supported. The link from these title objects to the separate `0x002A94E8` /
  `0x0031DC4C` track builders and the target-object materialization/type writer
  are unresolved.
- **Serialized/runtime mapping:** not established. CANM categories/types cannot
  be mapped to runtime `source+0x10` from evidence here.
- **Live binding/runtime:** not observed. Do not select either callback for
  either H1 slot based solely on static candidates.

Next action: obtain a bounded live capture of the two exact callback slots and
source `+0x10` values after both title BAM loads complete, or assign a separate
static loader/relocation trace that identifies the target object's type-byte
writer and proves the title resource path reaches it.
