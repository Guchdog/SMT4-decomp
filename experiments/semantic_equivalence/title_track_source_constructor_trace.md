# H1 model track source: static constructor trace

## Scope

Read-only follow-up to `title_canm_source_type_trace.md`. This distinguishes
the model-data objects passed as `AsdAnim_SetupTrack`'s descriptor source from
objects created with `AsdRes_Create`. It uses the pinned ARM image and the
readable drafts in `src/engine/asd_model.cpp`; it does not inspect live
emulator state or modify ROM assets.

## `AsdModel_func_002A94E8`

At `0x002A94E8`, the function obtains `source_data = *(model->source + 0x18)`.
For mesh entries, it resolves the relative list at `source_data + 0x70`, steps
through 16-byte entries, and resolves each target pointer from `entry + 0x28`.
That pointer is stored in `model->mesh_ptrs`; the mesh-track setup at
`0x002A97E8` uses `model->mesh_ptrs[0]` as the first word of its stack
descriptor. The draw/controller table repeats this pattern using
`source_data + 0x78`; its track setup is at `0x002A99DC` and also passes the
resolved table target as descriptor word zero.

The same model construction path assigns `model->model_data` from
`AsdGfx_CreateResource` (`0x002B3CB0`) in `AsdModel_func_001FE470` before
calling `AsdModel_func_002A94E8` for mode 0. This is the resource-construction
boundary visible in the current code. However, `AsdModel_func_002A94E8`
follows `model->source + 0x18` for its source tables, while the model-data
handle is used for runtime binding/grids. The exact loader/copy/relocation
step that materializes the `+0x70` / `+0x78` target objects is not recovered
here. Therefore the trace identifies their table provenance, not a specific
constructor that writes their contents.

## Model-view path (`0x0031DC4C` / `0x0031E3A8`)

`AsdModel_func_0031DC4C` receives a view whose first word is a resolved model
data block. Its mesh and draw targets are likewise obtained by resolving
relative `+0x28` pointers from 16-byte entries in the `+0x68` and `+0x78`
tables. The draw-track setup at `0x0031E3A8` passes the selected draw target
as descriptor word zero.

The same function separately iterates the node-name table (`+0x20`) and calls
`AsdRes_Create` at `0x0031E204`, then type-matches those returned node handles.
Those created handles are used for name matching and node-associated grids;
they are not the draw-target pointer supplied to the track descriptor. This
distinction is visible in the control/data flow and rules out `AsdRes_Create`
as the direct creator of the `0x0031E3A8` descriptor source.

## Conclusions and limits

- **Observed:** the `0x002A97E8`, `0x002A99DC`, and `0x0031E3A8` descriptor
  sources are pointers resolved directly from mesh/draw relative tables.
- **Observed:** `AsdRes_Create` at `0x0031E204` creates separately stored node
  handles from the node-name table; those handles are not the track source in
  the draw-track path.
- **Observed:** the regular model constructor calls `AsdGfx_CreateResource`
  (`0x002B3CB0`) before entering `0x002A94E8`; the ARM routine at
  `0x002B3CB0` is retained as a 1,792-byte body in
  `src/engine/leaf_batch43_a.cpp`.
- **Not established:** which loader routine allocates or populates each
  relative-table target, whether it copies a serialized CGFX object or builds
  a distinct runtime wrapper, and whether it writes byte `target + 0x10`.
- **Not established:** a mapping from that byte to the serialized skeletal,
  material, or visibility CANM categories. The table provenance does not
  justify assigning any category a runtime discriminator value.

Relevant readable drafts: `src/engine/asd_model.cpp` around
`0x001FE470`, `0x002A94E8`, and `0x0031DC4C`; pinned ARM bodies are in
`src/engine/leaf_batch43_a.cpp` and `src/engine/leaf_batch19_c.cpp`.
