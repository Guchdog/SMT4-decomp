# H1 runtime callback binding observation contract

## Purpose and evidence boundary

This contract defines the smallest read-only runtime observation that can select the callback actually installed at each H1 transition gate. It records a plan, not a live result. No emulator session or runtime memory was inspected for this report.

The source image is the pinned `extracted/exefs/code.bin` (SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`). The relevant preserved listings are `src/engine/leaf_batch16_c.cpp` (`0x002872B0`), `src/engine/leaf_batch41_b.cpp` (`0x0020FFAC`), `src/engine/leaf_batch43_a.cpp` (`0x002A5CA4`), and `src/engine/leaf_batch44_a.cpp` / `src/engine/leaf_batch40_b.cpp` for render-node binding and track construction. The existing static audits are `experiments/semantic_equivalence/title_real_callback_target_audit.md`, `title_canm_source_type_trace.md`, and `title_bam_track_source_type_mapping_audit.md`.

Do not infer a runtime discriminator from serialized animation categories. The local BAM inventory reports CANM member primitive types 5 (transform), 6 (RGBA color), and 2 (boolean); CANM stores that 32-bit field at member `+0x08`. `AsdAnim_SetupTrack` reads a separate byte from the resolved source object at `source+0x10` (`0x002A5CEC`). Type 0 retains/selects evaluator `0x0015555C`; type 1 selects `0x00151404` (`0x002A5CF0..0x002A5D08`). Other values leave the initialized default. No static writer or mapping from CANM member type to this runtime byte is established.

## Gate A — alternate animation controller

- H1 caller gate/call: `0x001EA0CC` calls `0x002872A4` with the child reached through `work+0x90 -> handle+0x08`. Positive signed word `child+0x34` enters the adjacent callback body at `0x002872B0`.
- Callback object and registration: at `0x002872B4`, the body loads `object = [child+0x4C]`; at `0x002872C4`, it loads the callback pointer `[object+0x4C]`; it calls that pointer at `0x002872E4` with `[object+0x50]` as the callback argument. It also reads object fields `+0x38`, `+0x3C`, `+0x44`, `+0x48`, and `+0x58`.
- Static layout match: `AsdModel::node_count` is at `+0x34`; `AsdModel::anim_controller_alt` is at `+0x4C`. `AsdModel_func_002A94E8` stores `AsdAnim_BindController(...)` into model `+0x4C` at `0x002A95F0`; the bind path reaches `AsdRenderNode_Bind` (`0x00153F8C`), which allocates a `0x70`-byte object and initializes its callback-related `+0x38..+0x58` fields.
- What remains unknown: the live title child's pointer, whether its signed `+0x34` gate is positive, the actual `object` pointer and callback target, and which resolved source object's `+0x10` selected that target.

## Gate B — indexed model-data track

- H1 caller gate/call: `0x001EA0DC` calls `0x0020FFA0` with the same child. Positive signed word `child+0x58` enters `0x0020FFAC`.
- Selected record: the body follows `child+0x2C` to model data, checks model-data `+0x148`, uses the grid descriptor at `+0x28` and index at `+0x14C`, then selects a record pointer from that grid. The callback is loaded from `[record+0x4C]` at `0x0021000C`, called at `0x00210010`, and receives `[record+0x50]`. The body also uses record fields `+0x38`, `+0x3C`, `+0x44`, `+0x48`, and `+0x58`.
- Static layout match: these offsets match the `0x74`-byte animation-track prefix documented in `include/engine/asd_scene.h`. Model construction creates tracks and stores them in model-data grids; `AsdModel_func_0031DC4C` is another direct setup path.
- What remains unknown: the live gate value, which grid record is selected, the record's callback target and argument, and the exact resolved source object's `+0x10` associated with that record.

## Bounded capture procedure

Use the existing controlled, disposable H0/H1 emulator profile and the pinned image. Do not change options or enter New Game, save selection, or Add-On Content. This procedure is a future observation request; this worker did not control the emulator.

1. In one title boot, set read-only breakpoints at `0x001EA0CC` and `0x001EA0DC`. At each visit, record PC, parent work pointer, the resolved child pointer (`*(work+0x90)` then `*(handle+0x08)`), signed gate value (`child+0x34` for A, `child+0x58` for B), and whether control enters its callback body. Stop after the first positive visit to each gate; if a gate never becomes positive during the defined H1 transition, record that fact and the last observed value rather than forcing the branch.
2. At `0x002872B0` and `0x0020FFAC`, capture the exact runtime pointer chain and values described above. For both objects, preserve the raw callback address, callback argument pointer, fields `+0x38/+0x3C/+0x44/+0x48/+0x58`, and a small bounded memory window sufficient to verify the layout. Do not call or patch either callback as part of observation.
3. Capture the source discriminator at its producer/selection point to bind it to the gate object: on `AsdAnim_SetupTrack` entry/call path (`0x002A5CB8`, then read at `0x002A5CEC`), record the descriptor's first pointer, its byte at `+0x10`, and the destination track pointer. For the render-node path, observe the source pointer and byte at `0x001540C0` and the callback store at `0x001540DC`. Record any resulting object pointer so the `+0x4C` callback slot can be matched to Gate A or B by pointer identity. The six known direct `AsdAnim_SetupTrack` call PCs are `0x002A97E8`, `0x002A99DC`, `0x0031033C`, `0x0031E3A8`, `0x0034176C`, and `0x0034D574`; restrict collection to calls during this title boot and retain caller PC to distinguish unrelated scene/model work.
4. Treat pointers as valid only for the observed allocation lifetime. Record first and last observation time/frame, allocation/free or owner teardown if available, and whether the same pointer is reused. The title work area is `0xA0` bytes at `0x0044E300` for the registered title callback, but the static evidence does not establish lifetime or address stability for the child, model data, source records, tracks, or render-node objects. Do not correlate by address alone across a free/reallocation; require an owner chain and fresh capture within the same live interval.
5. Stop after one controlled transition interval with one positive observation per gate and the corresponding setup/bind records, or after a fixed cap of 120 emulated frames once the title is idle. Save a compact log with image hash, emulator version, profile identity, frame/PC, pointer chains, raw bytes/words, and breakpoint conditions. This proves only the observed instance and interval; it does not establish behavior for every model, animation category, or boot.

## Acceptance rule and unresolved assumptions

A gate's runtime target is established only by observing the pointer actually loaded from its callback slot at that gate (`object+0x4C` or `record+0x4C`). The source byte is corroborating provenance: it must be captured on the matching construction/setup path and correlated to the exact live object/track. Static initialization predicts `0x0015555C` as the default and `0x00151404` for source byte 1; neither prediction is a live observation.

If a slot target and producer byte disagree with the static rule, preserve the capture and stop interpretation pending source-object identity/initialization analysis. If no producer can be correlated, report the observed callback target and mark the source-byte mapping unresolved. A gate not reached positively is `not observed`, not evidence that its callback target is absent. No CANM member category, file-header `+0x10`, callback stub, or synthetic harness result may substitute for the live pointer read.

Outstanding facts are: the runtime writer/constructor for source `+0x10`; the mapping from a particular CANM target path to a resolved source object; whether either gate is positive in the selected H1 scenario; the identity and lifetime of the exact live object at each gate; and the invocation/effect of the observed callback beyond its pointer/argument registration. The report therefore specifies an observation contract only and makes no equivalence or runtime-completion claim.
