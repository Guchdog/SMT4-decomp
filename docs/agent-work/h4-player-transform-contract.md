# Contract Recon: 0x001B4A54 (PlayerActor_UpdateVisibilityTransform)

- **Target Address:** `0x001B4A54`
- **Binary Size:** 276 bytes (including 12-byte literal pool: `0x001B4A54..0x001B4B64` code, `0x001B4B68..0x001B4B70` pool)
- **Role:** Map player 3D actor model visibility and coordinate transform synchronization
- **Module:** `program/map/player/playerActor.cpp`

## 1. Disassembly Analysis

```arm
0x001B4A54: push     {r4, r5, r6, lr}
0x001B4A58: ldr      r0, [pc, #0x108]       ; 0x0044CDA0 (g_PlayerActorWork)
0x001B4A5C: vpush    {d8}
0x001B4A60: ldr      r0, [r0]               ; dereference player actor work pointer
0x001B4A64: adds     r5, r0, #0x10          ; r5 = &work->state_10
0x001B4A68: ldrne    r4, [r5, #0x1c]        ; r4 = work->model_subobj (+0x2C)
0x001B4A6C: cmpne    r4, #0
0x001B4A70: beq      #0x1b4aa8              ; exit if work or model is NULL

0x001B4A74: ldr      r0, [pc, #0xf0]        ; 0x0049F91C (g_RepeatGate)
0x001B4A78: mov      r6, #0
0x001B4A7C: ldrb     r0, [r0, #0x22]        ; g_RepeatGate->menu_pause_flag
0x001B4A80: cmp      r0, #0
0x001B4A84: beq      #0x1b4ab0              ; branch if not paused

; Paused state handling:
0x001B4A88: ldr      r0, [r4]               ; model flags
0x001B4A8C: tst      r0, #2                 ; check hidden bit (bit 1)
0x001B4A90: bne      #0x1b4aa8              ; already hidden -> exit
0x001B4A94: orr      r0, r0, #2             ; set hidden bit
0x001B4A98: str      r0, [r4]
0x001B4A9C: ldr      r0, [r4, #8]           ; model backend object
0x001B4AA0: ldr      r0, [r0, #0x2c]        ; visual node
0x001B4AA4: strb     r6, [r0, #0x1f6]       ; visual_node->visible_1f6 = 0
0x001B4AA8: vpop     {d8}
0x001B4AAC: pop      {r4, r5, r6, pc}

; Unpaused state handling:
0x001B4AB0: ldrb     r0, [r5]               ; work->state_10.active
0x001B4AB4: cmp      r0, #0
0x001B4AB8: ldr      r0, [r4]
0x001B4ABC: and      r1, r0, #2
0x001B4AC0: beq      #0x1b4ae8              ; branch if active == 0
0x001B4AC4: cmp      r1, #0                 ; if active != 0 and hidden
0x001B4AC8: beq      #0x1b4b04
0x001B4ACC: bic      r0, r0, #2             ; clear hidden bit
0x001B4AD0: str      r0, [r4]
0x001B4AD4: ldr      r0, [r4, #8]
0x001B4AD8: mov      r1, #1
0x001B4ADC: ldr      r0, [r0, #0x2c]
0x001B4AE0: strb     r1, [r0, #0x1f6]       ; visual_node->visible_1f6 = 1 (show)
0x001B4AE4: b        #0x1b4b04

0x001B4AE8: cmp      r1, #0                 ; if active == 0 and visible
0x001B4AEC: bne      #0x1b4b04
0x001B4AF0: orr      r0, r0, #2             ; set hidden bit
0x001B4AF4: str      r0, [r4]
0x001B4AF8: ldr      r0, [r4, #8]
0x001B4AFC: ldr      r0, [r0, #0x2c]
0x001B4B00: strb     r6, [r0, #0x1f6]       ; visual_node->visible_1f6 = 0 (hide)

; Transform synchronization:
0x001B4B04: ldrb     r0, [r5, #0x18]        ; work->state_10.dirty_flag (+0x28)
0x001B4B08: cmp      r0, #0
0x001B4B0C: beq      #0x1b4aa8              ; exit if not dirty
0x001B4B10: ldr      r0, [r4, #8]           ; model backend
0x001B4B14: add      r2, r5, #4             ; Vec3 pos (work->state_10.pos +0x14)
0x001B4B18: mov      r1, #0
0x001B4B1C: bl       #0x28c8a8              ; Model_SetTranslation(backend, 0, &pos)
0x001B4B20: vldr     s16, [pc, #0x48]       ; 0.0f
0x001B4B24: ldr      r0, [r4, #8]
0x001B4B28: vldr     s1, [r5, #0x10]        ; yaw rotation float
0x001B4B2C: vmov.f32 s2, s16                ; 0.0f
0x001B4B30: vmov.f32 s0, s16                ; 0.0f
0x001B4B34: mov      r1, #0
0x001B4B38: bl       #0x28c880              ; Model_SetRotation(backend, 0, 0.0f, yaw, 0.0f)
0x001B4B3C: vmov.f32 s0, s16                ; 0.0f
0x001B4B40: ldr      r1, [r5, #0x14]        ; scale factor
0x001B4B44: ldr      r0, [r4, #8]
0x001B4B48: bl       #0x2a5a54              ; Model_SetScale(backend, scale, 0.0f)
0x001B4B4C: vmov.f32 s0, s16                ; 0.0f
0x001B4B50: ldr      r0, [r4, #8]
0x001B4B54: ldr      r1, [r5, #0x14]
0x001B4B58: bl       #0x287300              ; Model_CommitTransform(backend, scale, 0.0f)
0x001B4B5C: strb     r6, [r5, #0x18]        ; clear dirty flag
0x001B4B60: vpop     {d8}
0x001B4B64: pop      {r4, r5, r6, pc}
```

## 2. Structural & Field Mapping

```cpp
struct PlayerActorVisualNode {
    u8 pad[0x1F6];
    u8 visible_1f6;       // +0x1F6: 1 = visible, 0 = hidden
};

struct PlayerActorModelBackend {
    u8 pad[0x2C];
    PlayerActorVisualNode* visual_node; // +0x2C
};

struct PlayerActorModel {
    u32 flags;                          // +0x00: bit 1 (0x2) = hidden
    u8 pad[4];
    PlayerActorModelBackend* backend;   // +0x08
};

struct PlayerActorTransformState {
    u8 active;                          // +0x00 (+0x10 in work): 1 = active, 0 = inactive
    u8 pad_01[3];
    float pos[3];                       // +0x04 (+0x14 in work): X, Y, Z
    float yaw;                          // +0x10 (+0x20 in work): yaw angle in radians/degrees
    u32 scale;                          // +0x14 (+0x24 in work): scale parameter
    u8 dirty_flag;                      // +0x18 (+0x28 in work): 1 = transform modified
    u8 pad_19[3];
    PlayerActorModel* model;            // +0x1C (+0x2C in work): pointer to model
};

struct PlayerActorWork {
    u8 pad[0x10];
    PlayerActorTransformState transform; // +0x10..+0x2F
};
```

## 3. Callee Dependencies

- `0x0028C8A8`: `Model_SetTranslation(backend, channel=0, const float* pos)`
- `0x0028C880`: `Model_SetRotation(backend, channel=0, pitch=0.0f, yaw, roll=0.0f)`
- `0x002A5A54`: `Model_SetScale(backend, scale, 0.0f)`
- `0x00287300`: `Model_CommitTransform(backend, scale, 0.0f)`
