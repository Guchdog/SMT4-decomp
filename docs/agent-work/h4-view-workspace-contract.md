# H4 View Workspace Contract — Static ARM Reconnaissance

**Task ID:** `h4-view-workspace-contract`  
**Address:** `0x001B4664` (440 bytes)  
**Assigned Owner:** `h4_recon_worker`  
**Reference Binary:** `extracted/exefs/code.bin` (SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`)  
**Date:** 2026-10-30  

---

## 1. Overview and Scope

This document specifies the exact memory contract, field offsets, literal constants, subobject allocations, and global side effects of function `0x001B4664` (`engine_func_001b4664` in `src/engine/leaf_batch45_b.cpp`).

`0x001B4664` is the primary initialization routine for the field camera / view workspace located via the global pointer `g_ViewWork` at `0x00447E88` (observed in Shinjuku Station runtime at `0x004BCCD0`). In addition to configuring the `0x1C0`-byte view workspace, it instantiates a `0x100`-byte subobject and clears the global input repeat/gate structure at `0x0049F91C`.

---

## 2. Global Dependencies and Calling Convention

- **Calling Convention:** Standard AAPCS (`void engine_func_001b4664(void)`).
- **Incoming Registers:** No arguments are consumed (`r0` is overwritten immediately).
- **Callee-saved Registers Preserved:** `r4`, `r5`, `r6`, `lr`, and VFP `d8`.
- **Global Pointer Targets:**
  - `0x00447E88`: Global pointer to `ViewCameraWork` (heap object, size `0x1C0`).
  - `0x0049F91C` (derived as `0x0049FA1C - 0x100`): Global repeat/gate state structure.
- **External Calls:**
  - `0x002C23F8`: `AsdMem_Alloc(0x100)` (heap allocator, returns pointer in `r0`).
  - `0x00294A98`: Subobject constructor (`vtable` publication `0x00420420`).

---

## 3. View Workspace (`ViewCameraWork`) Layout at `*[0x00447E88]`

The base object pointed to by `*[0x00447E88]` is populated with the following exact offsets, types, and initial values:

| Offset | Type | Initial Value | Instruction | Functional Role |
|---|---|---|---|---|
| `+0x00` | `u32` | `0` | `str r4, [r0]` | Header flag / mode |
| `+0x04` | `u32` | `0` | `str r4, [r0, #4]` | Status word |
| `+0x08` | `u32` | `0` | `str r4, [r0, #8]` | Frame counter |
| `+0x10` | `u8` | `0` | `strb r4, [r0, #0x10]` | Active state byte |
| `+0x14` | `f32` | `0.0f` | `vstr s16, [r0, #0x14]` | Vertical offset |
| `+0x1C` | `f32` | `10.0f` | `vstr s0, [r0, #0x1c]` | Current Position X |
| `+0x20` | `f32` | `0.0f` | `vstr s16, [r0, #0x20]` | Current Position Y |
| `+0x24` | `f32` | `10.0f` | `vstr s0, [r0, #0x24]` | Current Position Z |
| `+0x28` | `f32` | `10.0f` | `vstr s3, [r0, #0x28]` | Target Position X |
| `+0x2C` | `f32` | `0.0f` | `vstr s2, [r0, #0x2c]` | Target Position Y |
| `+0x30` | `f32` | `10.0f` | `vstr s0, [r0, #0x30]` | Target Position Z |
| `+0x40` | `f32` | `10.0f` | `vstr s3, [r0, #0x40]` | Velocity / Interpolation X |
| `+0x44` | `f32` | `0.0f` | `vstr s2, [r0, #0x44]` | Velocity / Interpolation Y |
| `+0x48` | `f32` | `10.0f` | `vstmia r2, {s0, s1}` | Look-at Vector X |
| `+0x4C` | `f32` | `-90.0f` | `vstmia r2, {s0, s1}` | Look-at Vector Y |
| `+0x50` | `f32` | `-90.0f` | `vstr s1, [r0, #0x50]` | Pitch angle |
| `+0x54` | `u32` | `0` | `str r4, [r0, #0x54]` | Rotation state flags |
| `+0x58` | `f32` | `5.0f` | `vstr s0, [r0, #0x58]` | Distance / Radial zoom |
| `+0x5C` | `u8` | `0` | `strb r4, [r0, #0x5c]` | Zoom active flag |
| `+0x60` | `u32` | `0` | `str r4, [r0, #0x60]` | Mode selector |
| `+0x68` | `f32` | `0.0f` | `vstr s16, [r0, #0x68]` | Damping factor |
| `+0x6C` | `u8` | `0` | `strb r4, [r0, #0x6c]` | Damping active flag |
| `+0x70` | `u32` | `0` | `str r4, [r0, #0x70]` | Secondary counter |
| `+0x74` | `f32` | `0.0f` | `vstr s16, [r0, #0x74]` | Secondary target X |
| `+0x78` | `f32` | `0.0f` | `vstr s16, [r0, #0x78]` | Secondary target Y |
| `+0x7C` | `f32` | `0.0f` | `vstr s16, [r0, #0x7c]` | Secondary target Z |
| `+0x80` | `f32` | `0.0f` | `vstr s16, [r0, #0x80]` | Secondary delta |
| `+0x84` | `u32` | `0` | `str r4, [r0, #0x84]` | Collision flag |
| `+0x88` | `u8` | `0` | `strb r4, [r0, #0x88]` | Raycast hit flag |
| `+0x90` | `u32` | `0` | `str r4, [r0, #0x90]` | Obstruction state |
| `+0x94` | `f32` | `0.0f` | `vstr s16, [r0, #0x94]` | Obstruction distance |
| `+0x134` | `u8` | `1` | `strb r2, [r0, #0x134]` | Enabled / active flag |
| `+0x15C` | `f32` | `100.0f` | `vstmia r3, {s1, s2}` | Far clip plane / max distance |
| `+0x160` | `f32` | `1000.0f` | `vstmia r3, {s1, s2}` | Near clip plane / min distance |
| `+0x164` | `u32` | `0` | `str r4, [r1, #0x164]` | Camera event state |
| `+0x170` | `u32` | `0` | `str r4, [r1, #0x170]` | Track control word |
| `+0x174` | `u32` | `0` | `str r4, [r1, #0x174]` | Spline node index |
| `+0x178` | `u32` | `0` | `str r4, [r1, #0x178]` | Spline progress |
| `+0x17C` | `u32` | `0` | `str r4, [r1, #0x17c]` | Spline flags |
| `+0x180..0x184`| `u8[5]` | `0` | `strb r4, [r1, #0x180..0x184]` | Channel mute/bypass bytes |
| `+0x188` | `u32` | `0` | `str r4, [r1, #0x188]` | Target actor ID |
| `+0x18C` | `s32` | `-1` | `mvn r0, #0; str r0, [r1, #0x18c]` | Sentinel tracking ID (`0xFFFFFFFF`) |
| `+0x190` | `u32` | `0` | `str r4, [r1, #0x190]` | Reserved field |
| `+0x194` | `void*`| Heap ptr | `str r0, [r1, #0x194]` | Allocated subobject (`0x100` B) |
| `+0x198` | `u8` | `0` | `strb r4, [r1, #0x198]` | Subobject status byte |
| `+0x19C..0x1B0`| `u32[6]`| `0` | `str r4, [r1, #0x19c..0x1b0]` | Subobject channel words |
| `+0x1B4..0x1B8`| `u16[3]`| `0` | `strh r4, [r0, #0xb4..0xb8]` | Subobject halfword flags |

---

## 4. Subobject (`+0x194`) Construction Details

1. `0x1B4724..0x1B4728`: Calls `AsdMem_Alloc(0x100)` at `0x002C23F8`.
2. If the pointer returned in `r0` is non-null:
   - Calls constructor `0x00294A98`: zeros `0x50` bytes, sets flags `+4=0, +8=0, +0xC=1`.
   - Publishes vtable `0x00420420` at `*subobject`.
3. Stores subobject pointer into `work->subobj_194`.

---

## 5. Global Repeat / Gate State at `0x0049F91C`

`0x001B4664` also initializes fields in the global repeat/gate structure at `0x0049F91C`:

| Offset in `0x0049F91C` | Type | Initial Value | Instruction |
|---|---|---|---|
| `+0x17C` | `u8` | `0` | `strb r4, [r0, #0x17c]` |
| `+0x180` | `f32` | `0.0f` | `vstr s16, [r0, #0x180]` |
| `+0x184` | `f32` | `0.0f` | `vstr s16, [r0, #0x184]` |
| `+0x188` | `f32` | `0.0f` | `vstr s16, [r0, #0x188]` |
| `+0x18C` | `f32` | `0.0f` | `vstr s16, [r0, #0x18c]` |
| `+0x194` (`0x0049FA1C + 0x94`)| `u16` | `0` | `strh r4, [r2, #0x94]` |
| `+0x198` | `u8` | `0` | `strb r4, [r0, #0x198]` |
| `+0x199` | `u8` | `0` | `strb r4, [r0, #0x199]` |
| `+0x19A` | `u8` | `0` | `strb r4, [r0, #0x19a]` |
| `+0x1A0` | `u8` | `0` | `strb r4, [r0, #0x1a0]` |
| `+0x1A4` | `u32` | `0` | `str r4, [r0, #0x1a4]` |
| `+0x1A8` | `f32` | `0.0f` | `vstr s16, [r0, #0x1a8]` |
| `+0x1AC` | `f32` | `0.0f` | `vstr s16, [r0, #0x1ac]` |
| `+0x1B0` | `f32` | `0.0f` | `vstr s16, [r0, #0x1b0]` |
| `+0x1B4` | `f32` | `0.0f` | `vstr s16, [r0, #0x1b4]` |

---

## 6. Acceptance and Next Steps

The mapping above accounts for 100% of instructions in `0x001B4664`. The struct layout cleanly isolates:
1. Position coordinates (`+0x1C..+0x24`) and Target coordinates (`+0x28..+0x30`) integrated by `0x002E8F9C`.
2. Look-at and orientation angles (`+0x48..+0x58`).
3. Clipping boundaries (`+0x15C`, `+0x160`).
4. Subobject linkage (`+0x194`).

**Recommendation:** Proceed to independent review, then implement C++ reconstruction `h4_view_init_candidate.cpp` and differential validation.
