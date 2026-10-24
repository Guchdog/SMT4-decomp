# H1 title CANM-to-track source type trace (static)

## Question and boundary

This note traces the byte read by `AsdAnim_SetupTrack` (`0x002A5CA4`) and its
known direct callers, to test whether the type can be read straight from the
skeletal/material/visibility `CANM` records in `title_top1.bam` and
`title_top2.bam`. This is an offline static trace of the pinned `code.bin` and
existing readable drafts. It does not run the game, inspect live Azahar state,
or export/read additional ROM assets.

## What the setup function consumes

The exact ARM body is retained in `src/engine/leaf_batch43_a.cpp` under
`DECOMP_FUNC(0x002A5CA4, 1124)`. At `0x002A5CB8` it loads the first pointer in
the setup descriptor (`ldr r0,[r1]`); `0x002A5CEC` then reads
`ldrb r0,[r0,#0x10]`. The byte is compared with 0 and 1 at `0x002A5CF0` and
`0x002A5CFC`. The function stores a selected evaluator pointer into the
*destination track* at `+0x4C` (`0x002A5D08`): type 0 chooses the constructor's
default `0x0015555C`, type 1 chooses `0x00151404`; other values leave the
default intact. It marks destination track byte `+0x58` as 1 at
`0x002A5D10`.

So the type byte is **read**, not assigned, by `AsdAnim_SetupTrack`. The
callback/evaluator assignment at `0x002A5D08` is a different byte/field and
must not be confused with the source discriminator at `source+0x10`.
`AsdAnim_CreateTrack` (`0x002A6108`) initializes the destination track's
evaluator slot to `0x0015555C` at `0x002A6194`; it does not establish the
source object's `+0x10` value.

## Direct callers and source shapes

Scanning the pinned ARM image for direct `BL 0x002A5CA4` instructions found
these six PCs (the `code.bin` file offset is VA minus `0x00100000`):

| Call PC | Caller | What the readable draft / surrounding ARM establishes |
| --- | --- | --- |
| `0x002A97E8`, `0x002A99DC` | `AsdModel_func_002A94E8` (`src/engine/asd_model.cpp`) | Walks resolved model source-data tables and sets up mesh/controller tracks. Descriptor source is a resolved model element, not the outer BAM file header. |
| `0x0031033C` | `AsdCamera_func_00310124` (`src/engine/asd_scene.cpp`) | Descriptor source is a node resolved from the scene's relative node table (`scene+0x80`, entry `+0x28`); the clip/animation source is separately obtained through the typed owner at `+0x268` and later passed to the track's bind virtual. |
| `0x0031E3A8` | `AsdModel_func_0031DC4C` (`src/engine/asd_model.cpp`) | Descriptor source is a resolved draw handle; its associated list object is bound after setup. |
| `0x0034176C` | `engine_func_00341578` (`src/engine/leaf_batch45_a.cpp`) | The caller resolves a source node from a 16-byte scene entry through its relative pointer at `+0x28`; it gets the animation clip/source from a separate owner (`[owner+0x268]`). The two pointers have distinct roles. |
| `0x0034D574` | `engine_func_0034CCC0` (`src/engine/leaf_batch44_a.cpp`) | Sets up another model-node track from a descriptor built after resolving the node's `+0x148` list object and its linked info. This is runtime object plumbing, not a direct pointer to the BAM wrapper. |

The two previously documented model paths are therefore not the whole call
surface: the pinned binary has six direct call sites, including scene and
additional model-view paths. Their descriptors consistently pass a resolved
runtime source/target object as the first word; the animation object/list that
is bound to the resulting track is a separate argument or later bind call.

## Additional source-provenance checks

The scene-side caller at `0x0034176C` resolves its descriptor source through
the scene-relative node table (`scene+0x80`, 16-byte entries, relative pointer
at entry `+0x28`; `0x003416D8`–`0x00341704`). It does not write the resolved
object or its `+0x10` byte before setup. A second model path at `0x0034D574`
gets an object through `AsdRes_Find` (`0x002C31E8`) and resolves a relative
pointer at the found object's `+0x0C` (`0x0034D4D0`–`0x0034D4EC`); that resolved
pointer becomes descriptor source. Its nearby stack stores prepare the setup
descriptor, not the source object. Neither path identifies the earlier
constructor or a writer to source `+0x10`.

## Assignment site and relation to serialized CANM

Within this trace, the assignment site for the **source object's type byte**
remains unidentified. The proven site at `0x002A5CEC` is a load. The nearby
destination callback assignment (`0x002A5D08`) and constructor default
(`0x002A6194`) do not write `source+0x10`. The caller drafts also consume
already-resolved model/scene nodes; they do not show the code that constructs
those source records from serialized CGFX objects.

The existing read-only BAM inventory observes a `CANM` entry for each of the
three animation categories and records frame/channel counts. It does not
recover a field corresponding to the runtime source object's `+0x10`, nor a
loader instruction copying a serialized discriminator into that field. The
outer `ATBC` file-header word at `+0x10` is unrelated by address and structure.
Consequently, the byte is **not presently derivable from the inspected BAM
metadata alone**. It may be deterministically assigned by the missing
CGFX/Atlus loader based on animation category or target subtype; that is an
unverified possibility, not an established mapping. Naming a CANM category as
the runtime byte value would be unsupported.

## Result and next evidence needed

- **Observed:** `AsdAnim_SetupTrack` reads `source+0x10` and uses it to select
  the destination evaluator callback. Six direct call PCs are present in the
  pinned image.
- **Observed:** the additional scene and resource-lookup callers resolve
  descriptor sources through relative pointers and do not assign `+0x10` at
  the call site.
- **Strong inference:** the byte describes a property of a resolved runtime
  target/source object. It is not the track evaluator pointer and is not the
  ATBC header's `+0x10` word.
- **Unresolved:** the exact writer/constructor for each source object and any
  rule relating its byte to a serialized CANM category or channel.

Closing that gap needs the CGFX/Atlus resource-loader path from `CANM` and
CMDL target records to the runtime node object, or a bounded runtime snapshot
of the exact source pointer and bytes at a `0x002A5CEC` hit. Until then the
static candidates `0x0015555C` / `0x00151404` remain unselected for a live title
track.
