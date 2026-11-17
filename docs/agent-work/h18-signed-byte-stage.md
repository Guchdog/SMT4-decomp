# H18 0x00121d70 offline staging

## Placement and patch layout

The pinned text segment starts at `0x00100000`, has size `0x002fe624`, and aligned size `0x002ff000`. Its text extent ends at `0x003fe624`; the aligned executable page ends at `0x003ff000`. The `2,524` bytes in `[0x003fe624,0x003ff000)` are zero in the pinned image and contain no catalogued function span. The exact production object for `func_00121d70` is 28 bytes and fits at `0x003fe624` without overwriting adjacent code or data.

The 12-byte original slot at `0x00121d70` receives an ARM unconditional `B` to the cave (`2b720bea`), followed by two ARM NOP words to fill the original span. The branch resolves to `0x003fe624`. Both source and destination addresses have bit 0 clear, so the veneer remains in ARM state; it preserves LR and the candidate returns through its `bx lr`.

The pinned-image reference scan finds the one immediate direct BL to the entry at `0x00110f44`, with no branch into the entry interior. It finds no aligned pointer words to the entry span and no direct/aligned-pointer references into the selected cave prefix. The catalog overlap check finds no function span overlapping the candidate cave. These are static aligned ARM/image scans; they cannot prove the absence of indirect, computed, relocated, Thumb, unaligned, or runtime-generated references.

IPS contains two non-overlapping records: the entry veneer at file offset `0x00021d70` and the body at file offset `0x002fe624`. The stage runner parses the IPS back over the original and requires byte-for-byte equality with `code.staged.bin`.

## Offline differential evidence

The runner compiles the exact production `src/engine/leaf_matching.cpp`, extracts the relocation-free `func_00121d70` symbol, stages those bytes, and runs original versus the resulting patched image under Unicorn ARM11 MPCore. Both seeds produce identical staged output:

- Staged image SHA-256: `a0a00341aff58b407490cedd281d220a3a83ed7161a02372bbd30f99664b53d5`.
- IPS SHA-256: `73169f032f95ba8637f64b473c489ca900790dd3dd7c1645e384a5d8e984f97d`.
- Candidate bytes: `331ea0e3ff20e0e3d11090e1000051e37100efe6020080411eff2fe1` (28 bytes).
- Seed 7 report hash: `c2d3ff899e1eb81f4ffb13c6980f7c9b11b3d6b51c471a193d62f65a4bbcb461`.
- Seed 20261024 report hash: `9754a4b424ceb9c0b2416fbac915e45eb7706659e027453639b0cf3df21a2144`.

Each seed passes 512 direct-entry cases: all 256 byte values plus 256 randomized values. Each also passes 512 caller-composition cases, with all byte values plus random values. Caller execution begins at `0x00110f3c`, performs the real literal load and global pointer load at `0x00110f40`, calls the patched entry, and exercises both continuations (`0x00110f50` for nonzero, `0x00111008` for zero). The comparison includes the signed result, relevant preserved state, memory/access footprint, continuation and caller-consumed flags.

## Limits

The caller fixture seeds global `0x00433158` with a synthetic readable object; it does not execute the runtime producer or identify the actual pointee type, lifetime, or extent. The reported executable placement follows configured text size/alignment and the pinned image's zero padding; no live loader mapping, emulator, title boot, or game runtime was tested. No production source, function ledger, or emulator state was changed.

Artifacts and reports are under `build/agent-work/batch-h18-001/h18-signed-stage/run-001/seed-7/` and `.../seed-20261024/`. The next action is independent review of placement, IPS, and patched-image caller evidence before any runtime-stage assignment.
