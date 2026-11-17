# Recon contract: `0x002a34a4`

## Identity and boundaries

**Observed facts.** `config/functions.csv` records `0x002a34a4,740,matching,engine,engine_func_002a34a4,src/engine/leaf_batch45_a.cpp`. The entry is ARM state. The 740 bytes decode completely as ARM instructions plus a 16-byte literal tail at `0x002a3778..0x002a3787`. The source is one naked assembly wrapper; it does not provide a typed C++ contract.

The prologue at `0x002a34a4` saves r4-r8/LR, d8-d9, and allocates 0x18 stack bytes. The epilogue at `0x002a3554..0x002a355c` adds back the local stack, restores d8-d9, and returns via `pop {r4-r8,pc}`. Loop/branch paths converge on this epilogue when their list/count conditions terminate. The literal tail supplies `1.0f`, `0x00464b70`, `0x00464af0`, and `0.0f`.

## Proposed ABI contract (facts separated from inference)

**Observed register inputs:** r0 is an object/entry pointer; r1 is a mode selector (the two real callers pass only 0 or 1); s0 is a float copied to saved s16. No other incoming integer/VFP argument is read before being overwritten. The function uses saved d8-d9 and restores them. It modifies caller-saved integer/VFP temporaries, NZCV and memory. It returns through saved LR. Its r0 value is not read by the two identified callers, so a C++ `void` interface is a reasonable provisional surface; the machine can leave the last helper-produced value in r0 on some paths, and indirect callers are not ruled out.

**Direct caller evidence:** aligned ARM BL scan found four references, all in two functions:

| Caller and call sites | Values passed | Observed condition and post-call use |
|---|---|---|
| `engine_func_0014e9f4`, `0x0014eba4`, `0x0014ec18` | r0=r6 entry, r1=0; s0=`[0x00464af0+0x64]` or `[...+0x60]` | Called only when byte `[0x00464af0+1]` is nonzero and the resolved entry field at `+0x10` is 2 or nonpositive, respectively. Immediately after BL, caller writes a constant 1 status; it does not consume returned r0 or flags. |
| `engine_func_002fb5c8`, `0x002fb6fc`, `0x002fb764` | r0=r6 entry, r1=1; s0=`[0x00464af0+0x64]` or `[...+0x60]` | Same global guard and field-value split. Immediately after the call it proceeds to another lookup / loop; it does not consume returned r0 or flags. |

No direct C++ call expression was found; the call instructions are inside byte-preserved naked caller wrappers. No aligned exact pointer value equal to `0x002a34a4` or Thumb-tagged `0x002a34a5` was found in code.bin. This does not exclude indirect/computed or relocated calls, Thumb callsites, or references through tables not represented as literal function pointers.

**Likely meaning (inference only):** the function configures/render-initializes an engine object for two “shadow” related call modes. Both callers embed the string `shadow` and query a per-entry property at `+0x10`; the actual caller-level feature name and object layout are not established.

## Memory behavior and branches

- `r5 = *(u32*)(r0+8)` is the main work/state base. Unconditionally writes zero to `r5+0x2a8`, `+0x2b0`, `+0x2c8`, `+0x2b4`, `+0x2ac`; writes 2 to `+0x174` and 4 to `+0x170`.
- Reads relative-pointer/vector fields including `r0+0x10/+0x14`, `r0+0x24`, `r5+0x274`, `r5+0x288`, and later state/table records. The `r1==1` path walks the `[r0+0x10, r0+0x14)` 32-bit vector, chooses a record, writes four floats at record `+0xa0..+0xac`, calls the float packer, stores its result at `+0xd8`, and clears a field at `+0x2b4` on one branch.
- The `r1==0` path resolves relative pointers and tagged objects, tests sentinel words such as `0x20000004`, dispatches through metadata, and updates object flags at `+0x14` (masking/setting `0x1000` and `0x100`). It consults globals `0x00464b70` and `0x00464af0`; byte `0x00464af5` selects a zero versus saved scalar component. It packs a four-float vector, writes a returned word into an object at `+8`, then iterates records under `r5+0x288`, modifying record type/flag fields.
- Meaningful control decisions include selector `r1==0`, null/relative-pointer resolution, tagged type values, a high-bit test on an object word, global option bytes, entry property values `<=0`, `==2`, or other positive values, vector counts, and per-record low-nibble/type checks. Invalid/null memory is not guarded on all paths.

These field names and higher-level meanings are not proven. Treat offsets/tags as the observed layout for this bounded binary revision, not a reusable engine schema.

## Dependencies and open calls

Direct calls inside this function:

- `0x002c2be8` (`engine_func_002c2be8`) consumes four floats, clamps channels to [0,1], quantizes them to bytes and packs the four results into r0. A typed use exists in `leaf_batch45_a.cpp` as a color/rgba packer; higher-level format naming remains partly inferential.
- `0x002c3568` (`script_vm_func_002c3568`) dispatches according to tagged words (`0x20000002`, `0x20000004`, `0x20000009`, and a related range) through the table rooted at `0x0044e8c4`; it tail-branches to indirect entries. Exact target behavior/data is unresolved.
- `0x002a2ddc` (`camp_func_002a2ddc`) receives local pointer storage and a key from `0x00464b70`; for several tags it tail-branches to `0x0015b5b8`, `0x0015b79c`, or `0x0015b8f8`. Its higher-level lookup contract and target contracts remain unresolved.
- `0x002a2db4` (`func_002a2db4`) fills a two-word local record from a relative pointer path, including a value at resolved base `+0x48` and a pointer at `+0x10`.

The first three helper source bodies are still raw/naked ARM wrappers; `script_vm_func_002c3568` and `camp_func_002a2ddc` contain dynamic tail-dispatch. This is a concrete blocker to an honest whole-function C++ candidate without more layout/dispatch evidence.

## Reconstruction recommendation and validation plan

**Recommendation:** do not replace the 740-byte wrapper with a partial initialization fragment. A bounded semantic implementation should first recover the entry/work-state layouts and dynamic helper contracts, then implement the complete `void`-like entry for both observed selector values while preserving existing call dependencies. The smallest useful prerequisite is to characterize the four direct helpers and the tag/relative-pointer objects; the `r1==1` vector path may be the first isolated branch only after its vector and element layout are confirmed. No compile, differential run, caller-composition run, or runtime run was performed in this recon-only task.

For the later offline runner, pin the original image and exercise both actual call shapes: r1=0 and r1=1, with s0 sourced from both global float offsets; valid/null relative pointers and tagged sentinel/type variants; empty, one-element and multi-element ranges; property values below zero, zero, 2, and other positive values; global option bytes 0/nonzero; and record low-nibble branches. Compare state fields, all reached writes, return/continuation, ABI-preserved GPR/VFP and memory, and negative controls that alter selector, color scalar, a state offset, or a bit mask. Once these pass, execute each caller window at the four callsites and check its post-call status/loop state. Do not infer runtime behavior from static caller xrefs.

## Provenance and limitations

Pinned code.bin SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Read-only source/input hashes (including helper/caller files consulted beyond the packet’s minimum declared reads):

```text
e2a863ff5ba7818fa76c5257357d6de29f73804d710236933c2bdd050189da8d  config/functions.csv
5b9f1fa5114e9a460c9e2d7ca045d882c17ff8f93d70e358b1834141a0d4dbdd  config/game_info.json
1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558  extracted/exefs/code.bin
8a7aacd39a3170ce25677e03977650c73ef1a1da58827ac2b0f16b9112df35a9  src/engine/leaf_batch45_a.cpp
ba84b9c8310f610cafaa8f624c661cf9cefc877eb1c579867c40e048ef6aa7d7  src/engine/leaf_batch42_b.cpp
92f809cb8f1bf188519071c906656fce2ce0ed462ebb154a95849f7affa4362f  src/engine/leaf_batch41_c.cpp
8c042d859ea2412f06f31ed21b13576c699a3d8ead744a790f5da09f4898afc9  src/engine/leaf_batch10_c.cpp
3199e5a1eb3e7b46e2273bb3eb6696b0556ea9d8da9ad6259fa26eb2a785a717  src/engine/leaf_batch37_c.cpp
3327f196471908368a1099626df60ab70841a12d669f77ff4b06204367c175d0  src/engine/leaf_batch38_b.cpp
10a8f416f16330faa1e3b6345e616c419c82e99ae77fcc2912298d6c7b4763cb  src/engine/leaf_batch40_a.cpp
c534ca4a414ec59561c9add48e244cedfdabde99d844144a622ed32a15af7504  include/engine/leaf_matching.h
5a59bdeed14404e4e8ea2ef6679af51aa870c2f02566d9e129256355a54ed421  tools/split_asm.py
```

Static direct-call scan decoded each 4-byte-aligned word of the configured ARM text segment; code/data words can be misdecoded as instructions. It does not cover Thumb decoding, indirect BLX-register calls, computed branches, relocated addresses, or dynamically selected table entries. No compilation or mutation was performed.
