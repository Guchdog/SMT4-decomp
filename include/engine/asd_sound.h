#pragma once
#include <cstddef>
#include "types.h"

/**
 * AsdSoundSystem, the sound-effect unit and the sound-test front end.
 *
 * The nine functions reconstructed in `src/engine/asd_sound.cpp` come from
 * three original translation units:
 *
 *   soundEffect     c:\SMT4\XRD686\sdds4\program\sound\soundEffect.cpp
 *   AsdSoundSystem  c:\SMT4\XRD686\AsdSDK\Source\Snd\AsdSoundSystem.cpp
 *   soundTest       c:\SMT4\XRD686\sdds4\program\sound\soundTest.cpp
 *
 * Only the offsets actually touched by those nine functions are named.  Every
 * field carries the instruction that proves it; ranges that the reconstructed
 * code never addresses stay `pad_NN`.
 *
 * `AsdSoundSystem` is an observed prefix: the binary keeps using the same
 * object past +0x1220 (for example `0x00119B48` writes +0x1384), so no
 * `sizeof` assertion is made for the whole manager.
 */

namespace smt4::engine {

/** Three consecutive `f32` values (positions, mix levels, listener vectors). */
struct AsdSoundFloat3 {
    f32 x;
    f32 y;
    f32 z;
};
static_assert(sizeof(AsdSoundFloat3) == 0x0C);

/**
 * Recursive lock used around archive construction (`0x004E315C`).
 *
 * `engine_func_002c3aa8` stores the current thread id at +0x04 and increments
 * +0x08; `engine_func_002c3a24` decrements +0x08 and clears +0x04 at zero.
 */
struct AsdSoundLock {
    u32 field_00;                       // +0x00: tested by 0x002c3ab0 (thread id compare)
    u32 owner;                          // +0x04: `str r0,[r4,#4]` (0x002c3acc)
    u32 count;                          // +0x08: `add r0,r0,#1` (0x002c3ad4)
};
static_assert(offsetof(AsdSoundLock, owner) == 0x04);
static_assert(offsetof(AsdSoundLock, count) == 0x08);
static_assert(sizeof(AsdSoundLock) == 0x0C);

// ---------------------------------------------------------------------------
// Effect-unit configuration blocks (soundEffect.cpp)
// ---------------------------------------------------------------------------

/**
 * Configuration block of the first effect unit at `0x004C54E4`.
 *
 * `soundEffect_func_0010368c` fills +0x00..+0x0C and passes the block, together
 * with the unit base `0x004C5484`, to `engine_func_00110c60`.
 */
struct AsdSoundEffectConfigA {
    u32 field_00;                       // +0x00: `str r1,[r0]` = 0x96 (0x001036b0)
    f32 field_04;                       // +0x04: `vstmia r1,{s0,s1}` = 0.1f (0x001036bc)
    f32 field_08;                       // +0x08: second word of that `vstmia` = 0.7f
    u8  field_0c;                       // +0x0C: `strb r5,[r0,#0xc]` = 1 (0x001036c4)
    u8  pad_0d[0x03];                   // +0x0D..+0x10
};
static_assert(offsetof(AsdSoundEffectConfigA, field_04) == 0x04);
static_assert(offsetof(AsdSoundEffectConfigA, field_08) == 0x08);
static_assert(offsetof(AsdSoundEffectConfigA, field_0c) == 0x0C);
static_assert(sizeof(AsdSoundEffectConfigA) == 0x10);

/**
 * Configuration block of the second effect unit at `0x004C5604`.
 *
 * `soundEffect_func_00109524` fills it and passes it, together with the unit
 * base `0x004C54F4`, to `engine_func_00121208`.
 */
struct AsdSoundEffectConfigB {
    u32 field_00;                       // +0x00: `stm r0,{r6,r7,r8}` = 0x5A (0x00109548)
    u32 field_04;                       // +0x04: second word of that `stm` = 0x4B0
    u32 field_08;                       // +0x08: third word of that `stm` = 0x1E
    f32 field_0c;                       // +0x0C: `vstmia r6,{s1,s2}` = 0.5f (0x0010955c)
    f32 field_10;                       // +0x10: second word of that `vstmia` = 0.8f
    u32 field_14;                       // +0x14: `str r1,[r0,#0x14]` = block+0x24 (0x00109578)
    f32 field_18;                       // +0x18: `vstr s0,[r0,#0x18]` = 0.4f (0x0010957c)
    f32 field_1c;                       // +0x1C: `vstr s0,[r0,#0x1c]` = 0.4f (0x00109580)
    u8  field_20;                       // +0x20: `strb r2,[r0,#0x20]` = 0 (0x00109590)
    u8  field_21;                       // +0x21: `strb r5,[r0,#0x21]` = 1 (0x00109588)
    u8  pad_22[0x02];                   // +0x22..+0x24
    u32 field_24;                       // +0x24: `stm r1,{r3,r4,ip}` = 0xBE0 (0x0010956c)
    u32 field_28;                       // +0x28: second word of that `stm` = 0xE60
    u32 field_2c;                       // +0x2C: third word of that `stm` = 0x820
};
static_assert(offsetof(AsdSoundEffectConfigB, field_04) == 0x04);
static_assert(offsetof(AsdSoundEffectConfigB, field_08) == 0x08);
static_assert(offsetof(AsdSoundEffectConfigB, field_0c) == 0x0C);
static_assert(offsetof(AsdSoundEffectConfigB, field_10) == 0x10);
static_assert(offsetof(AsdSoundEffectConfigB, field_14) == 0x14);
static_assert(offsetof(AsdSoundEffectConfigB, field_18) == 0x18);
static_assert(offsetof(AsdSoundEffectConfigB, field_1c) == 0x1C);
static_assert(offsetof(AsdSoundEffectConfigB, field_20) == 0x20);
static_assert(offsetof(AsdSoundEffectConfigB, field_21) == 0x21);
static_assert(offsetof(AsdSoundEffectConfigB, field_24) == 0x24);
static_assert(offsetof(AsdSoundEffectConfigB, field_28) == 0x28);
static_assert(offsetof(AsdSoundEffectConfigB, field_2c) == 0x2C);
static_assert(sizeof(AsdSoundEffectConfigB) == 0x30);

// ---------------------------------------------------------------------------
// Stream records (AsdSoundSystem.cpp, 0x004E1F68 + 0x4BC, stride 0x50)
// ---------------------------------------------------------------------------

/**
 * One of the four 0x50-byte stream records starting at `0x004E2424`
 * (`0x004E1F68 + 0x4BC`).
 *
 * `AsdSoundSystem_func_002c1df4` addresses them as `system + 0x4BC + 0x50 * n`
 * (0x002c1e08: `add r0,r0,r0,lsl #2` / `lsl #4`) and only touches +0x10,
 * +0x40, +0x44, +0x48 and +0x4C; `AsdSoundSystem_func_0010d40c` clears the
 * +0x48 words of all four.
 */
struct AsdSoundStream {
    u8  pad_00[0x10];                   // +0x00..+0x10
    u32 field_10;                       // +0x10: `ldr r0,[r0,#0x4cc]` (0x002c1e14)
    u8  pad_14[0x2C];                   // +0x14..+0x40
    void* field_40;                     // +0x40: `str r0,[r5,#0x40]` (0x002c1e58)
    u32 field_44;                       // +0x44: `str r0,[r5,#0x44]` (0x002c1e78)
    u32 field_48;                       // +0x48: `str r0,[r5,#0x48]` = 0x40 (0x002c1e6c)
    u8  field_4c;                       // +0x4C: `strb r0,[r2,#0x4c]` (0x002c1ed4)
    u8  pad_4d[0x03];                   // +0x4D..+0x50
};
static_assert(offsetof(AsdSoundStream, field_10) == 0x10);
static_assert(offsetof(AsdSoundStream, field_40) == 0x40);
static_assert(offsetof(AsdSoundStream, field_44) == 0x44);
static_assert(offsetof(AsdSoundStream, field_48) == 0x48);
static_assert(offsetof(AsdSoundStream, field_4c) == 0x4C);
static_assert(sizeof(AsdSoundStream) == 0x50);

// ---------------------------------------------------------------------------
// Sequence records (AsdSoundSystem.cpp, 0x004E1F68 + 0x694, stride 0x3C)
// ---------------------------------------------------------------------------

/**
 * One of the four 0x3C-byte sequence records starting at `0x004E25FC`
 * (`0x004E1F68 + 0x694`).
 *
 * `AsdSoundSystem_func_0010c5d4` computes `system + 0x694 + 0x3C * n`
 * (0x0010c5ec: `rsb r0,r6,r6,lsl #4` = 15*n, then `lsl #2`) and uses the four
 * channel handles at +0x20..+0x2C, the stream buffer at +0x30, the stream
 * handle at +0x34 and the four state bytes at +0x38..+0x3B.
 */
struct AsdSoundSequenceSlot {
    u8  pad_00[0x20];                   // +0x00..+0x20
    void* field_20[4];                  // +0x20..+0x30: `ldr r0,[r0,#0x20]` in the
                                        // four-iteration loop at 0x0010c714
    void* field_30;                     // +0x30: `str r0,[r5,#0x30]` (0x0010c644)
    u32 field_34;                       // +0x34: `str r0,[r5,#0x34]` (0x0010c660)
    u8  field_38;                       // +0x38: `strb r8,[r5,#0x38]` = 0x40 (0x0010c678)
    u8  field_39;                       // +0x39: `strb r6,[r5,#0x39]` = index (0x0010c674)
    u8  field_3a;                       // +0x3A: `strb sb,[r5,#0x3a]` = 1 (0x0010c66c)
    u8  field_3b;                       // +0x3B: `strb sb,[r5,#0x3b]` = 1 (0x0010c664)
};
static_assert(offsetof(AsdSoundSequenceSlot, field_20) == 0x20);
static_assert(offsetof(AsdSoundSequenceSlot, field_30) == 0x30);
static_assert(offsetof(AsdSoundSequenceSlot, field_34) == 0x34);
static_assert(offsetof(AsdSoundSequenceSlot, field_38) == 0x38);
static_assert(offsetof(AsdSoundSequenceSlot, field_39) == 0x39);
static_assert(offsetof(AsdSoundSequenceSlot, field_3a) == 0x3A);
static_assert(offsetof(AsdSoundSequenceSlot, field_3b) == 0x3B);
static_assert(sizeof(AsdSoundSequenceSlot) == 0x3C);

// ---------------------------------------------------------------------------
// Streamed-sound object (AsdSoundSystem.cpp, 0x98 bytes, heap allocated)
// ---------------------------------------------------------------------------

/**
 * Object built by `AsdSoundSystem_func_0010c078` from a data block.
 *
 * The allocation size is 0x98 (`mov r3,#0x98` at 0x0010c0b0) and every field
 * below is written by that function; +0x04..+0x38 and +0x44..+0x6C are never
 * addressed by the reconstructed code.
 */
struct AsdSoundStreamObject {
    u32 field_00;                       // +0x00: `str r0,[r5]` = data base (0x0010c0dc)
    u8  pad_04[0x34];                   // +0x04..+0x38
    void* field_38;                     // +0x38: `str r0,[r5,#0x38]` = player (0x0010c154)
    f32 field_3c;                       // +0x3C: `vstr s0,[r5,#0x3c]` = 0.7071068f
    f32 field_40;                       // +0x40: `vstr s0,[r5,#0x40]` = 0.7071068f
    u8  pad_44[0x28];                   // +0x44..+0x6C
    void* field_6c;                     // +0x6C: `str r0,[r5,#0x6c]` = copy buffer
    u8  pad_70[0x0c];                   // +0x70..+0x7C
    u32 field_7c;                       // +0x7C: `str r0,[r5,#0x7c]` = -1 (0x0010c0cc)
    u32 field_80;                       // +0x80: `str r0,[r5,#0x80]` = entry offset
    u8  pad_84[0x04];                   // +0x84..+0x88
    u32 field_88;                       // +0x88: `str r1,[r5,#0x88]` = size - offset
    u32 field_8c;                       // +0x8C: `strd r8,sb,[r5,#0x8c]` = extra
    u32 field_90;                       // +0x90: second word of that `strd` = 1
    u8  pad_94[0x04];                   // +0x94..+0x98
};
static_assert(offsetof(AsdSoundStreamObject, field_38) == 0x38);
static_assert(offsetof(AsdSoundStreamObject, field_3c) == 0x3C);
static_assert(offsetof(AsdSoundStreamObject, field_40) == 0x40);
static_assert(offsetof(AsdSoundStreamObject, field_6c) == 0x6C);
static_assert(offsetof(AsdSoundStreamObject, field_7c) == 0x7C);
static_assert(offsetof(AsdSoundStreamObject, field_80) == 0x80);
static_assert(offsetof(AsdSoundStreamObject, field_88) == 0x88);
static_assert(offsetof(AsdSoundStreamObject, field_8c) == 0x8C);
static_assert(offsetof(AsdSoundStreamObject, field_90) == 0x90);
static_assert(sizeof(AsdSoundStreamObject) == 0x98);

/**
 * Sound-test front-end object (0x14 bytes) built by
 * `soundTest_func_001ea808` and published at `0x0044E110`.
 */
struct AsdSoundTestObject {
    void* ui;                           // +0x00: `str r0,[r4]` = AsdUi_Create result
    u8  field_04;                       // +0x04: `strb r5,[r0,#4]` = 0 (0x001ea858)
    u8  pad_05[0x03];                   // +0x05..+0x08
    u32 field_08;                       // +0x08: `str r5,[r0,#8]` = 0 (0x001ea84c)
    u32 field_0c;                       // +0x0C: `str r5,[r0,#0xc]` = 0 (0x001ea850)
    u32 field_10;                       // +0x10: `str r5,[r0,#0x10]` = 0 (0x001ea854)
};
static_assert(offsetof(AsdSoundTestObject, field_04) == 0x04);
static_assert(offsetof(AsdSoundTestObject, field_08) == 0x08);
static_assert(offsetof(AsdSoundTestObject, field_0c) == 0x0C);
static_assert(offsetof(AsdSoundTestObject, field_10) == 0x10);
static_assert(sizeof(AsdSoundTestObject) == 0x14);

// ---------------------------------------------------------------------------
// Voice bank (AsdSoundSystem.cpp, 0x004E1F68 + 0x784, 0xA44 bytes)
// ---------------------------------------------------------------------------

/** Opaque 132-byte voice slot (`AsdSoundSystem` + 0x784 + 0x3C + 0x84 * n). */
struct AsdSoundVoiceSlot {
    u8 raw[0x84];
};
static_assert(sizeof(AsdSoundVoiceSlot) == 0x84);

/**
 * Voice bank at `0x004E26EC` (`0x004E1F68 + 0x784`).
 *
 * `AsdSoundSystem_func_00109690` initialises it: the two list words and the
 * embedded node at +0x9E0 go through `engine_func_002bf774`, +0x1C/+0x24 carry
 * the 0x20 / 5.6666665f parameters, and the loop at 0x00109974 walks the 16
 * voice slots and their 16 mix vectors.  The structure ends exactly at
 * +0xA44, where `field_11c8` of the manager begins.
 */
struct AsdSoundVoice {
    u8  pad_000[0x0C];                  // +0x000..+0x00C
    u32 field_00c;                      // +0x00C: `add r3,r0,#0x790` list head (0x001098b8)
    u32 field_010;                      // +0x010: `add r1,r3,#4` list tail (0x001098cc)
    u8  pad_014[0x08];                  // +0x014..+0x01C
    u32 field_01c;                      // +0x01C: `str sb,[r6,#0x1c]` = 0x20 (0x001098ac)
    u8  pad_020[0x04];                  // +0x020..+0x024
    f32 field_024;                      // +0x024: `vstr s0,[r6,#0x24]` = 5.6666665f (0x001098b0)
    u8  pad_028[0x14];                  // +0x028..+0x03C
    AsdSoundVoiceSlot slots[16];        // +0x03C..+0x87C: `base + 0x3C + 0x84*n` (0x0010997c)
    u8  pad_87c[0x40];                  // +0x87C..+0x8BC
    AsdSoundFloat3 mix[16];             // +0x8BC..+0x97C: `base + 0x8BC + 12*n` (0x001099e8)
    u8  pad_97c[0x48];                  // +0x97C..+0x9C4
    f32 field_9c4;                      // +0x9C4: `vstr s0,[r0,#0x48]`, r0=voice+0x97C (0x0010995c)
    f32 field_9c8;                      // +0x9C8: `vstr s0,[r0,#0x4c]` (0x00109924)
    f32 field_9cc;                      // +0x9CC: `vstr s0,[r0,#0x50]` (0x00109940)
    u8  pad_9d0[0x10];                  // +0x9D0..+0x9E0
    u32 field_9e0;                      // +0x9E0: `add r2,r0,#0x1000` +0x164 (0x001098bc)
    u8  pad_9e4[0x40];                  // +0x9E4..+0xA24
    f32 field_a24;                      // +0xA24: `vstmia r1,{s16,s17}` = 0.0f (0x001098e8)
    f32 field_a28;                      // +0xA28: second word of that `vstmia` = 1.0f
    f32 field_a2c;                      // +0xA2C: `vstr s16,[r0,#0x22c]` = 0.0f (0x001098ec)
    u8  pad_a30[0x04];                  // +0xA30..+0xA34
    f32 field_a34;                      // +0xA34: `vstr s0,[r4,#0x234]` = 5.0f (0x0010991c)
    f32 field_a38;                      // +0xA38: `vstr s0,[r4,#0x238]` = 2.0f (0x00109938)
    f32 field_a3c;                      // +0xA3C: `vstr s17,[r4,#0x23c]` = 5.0f (0x00109954)
    u32 field_a40;                      // +0xA40: `str r1,[r6,#0xa40]` = 0 (0x00109970)
};
static_assert(offsetof(AsdSoundVoice, field_00c) == 0x00C);
static_assert(offsetof(AsdSoundVoice, field_010) == 0x010);
static_assert(offsetof(AsdSoundVoice, field_01c) == 0x01C);
static_assert(offsetof(AsdSoundVoice, field_024) == 0x024);
static_assert(offsetof(AsdSoundVoice, slots) == 0x03C);
static_assert(offsetof(AsdSoundVoice, mix) == 0x8BC);
static_assert(offsetof(AsdSoundVoice, field_9c4) == 0x9C4);
static_assert(offsetof(AsdSoundVoice, field_9c8) == 0x9C8);
static_assert(offsetof(AsdSoundVoice, field_9cc) == 0x9CC);
static_assert(offsetof(AsdSoundVoice, field_9e0) == 0x9E0);
static_assert(offsetof(AsdSoundVoice, field_a24) == 0xA24);
static_assert(offsetof(AsdSoundVoice, field_a28) == 0xA28);
static_assert(offsetof(AsdSoundVoice, field_a2c) == 0xA2C);
static_assert(offsetof(AsdSoundVoice, field_a34) == 0xA34);
static_assert(offsetof(AsdSoundVoice, field_a38) == 0xA38);
static_assert(offsetof(AsdSoundVoice, field_a3c) == 0xA3C);
static_assert(offsetof(AsdSoundVoice, field_a40) == 0xA40);
static_assert(sizeof(AsdSoundVoice) == 0xA44);

// ---------------------------------------------------------------------------
// Manager (AsdSoundSystem.cpp, 0x004E1F68)
// ---------------------------------------------------------------------------

/** Global AsdSoundSystem manager at `0x004E1F68` (observed prefix, 0x1220 B). */
struct AsdSoundSystem {
    u32 field_000;                      // +0x0000: never addressed by these functions
    u32 field_004;                      // +0x0004: `ldr r0,[r0,#4]` (0x002bf85c)
    u8  pad_008[0x124];                 // +0x0008..+0x012C
    u8  container_a[0x58];              // +0x012C..+0x0184: `add r0,r5,#0x12c` (0x001096f8)
    u8  container_b[0xC0];              // +0x0184..+0x0244: `add r0,r5,#0x184` (0x0010978c)
    u8  container_c[0x220];             // +0x0244..+0x0464: `add r0,r5,#0x244` (0x00109740)
    void* field_464;                    // +0x0464: `str r0,[r4,#0x464]` (0x0010d4e4)
    void* field_468;                    // +0x0468: `str r0,[r5,#0x468]` (0x0010972c)
    void* field_46c;                    // +0x046C: `str r0,[r5,#0x46c]` (0x00109774)
    void* field_470;                    // +0x0470: `str r0,[r5,#0x470]` (0x001097c8)
    void* field_474;                    // +0x0474: `str r0,[r5,#0x474]` (0x0010980c)
    void* field_478;                    // +0x0478: `ldr r0,[r4,#0x478]` (0x0010b98c)
    char path[0x40];                    // +0x047C: `add r0,r5,#0x47c` strcpy target
                                        // (0x001096a8).  No length clamp is emitted:
                                        // a longer name overruns into `streams`.
    AsdSoundStream streams[4];          // +0x04BC..+0x05FC
    u8  pad_5fc[0x34];                  // +0x05FC..+0x0630
    u32 field_630;                      // +0x0630: `str r6,[r4,#0x630]` (0x0010d508)
    u8  field_634;                      // +0x0634: `strb r6,[r4,#0x634]` (0x0010d50c)
    u8  field_635;                      // +0x0635: `strb r0,[r4,#0x635]` = 0x40 (0x0010d510)
    u8  pad_636[0x36];                  // +0x0636..+0x066C
    u32 field_66c;                      // +0x066C: `str r6,[r4,#0x66c]` (0x0010d514)
    u8  field_670;                      // +0x0670: `strb r6,[r4,#0x670]` (0x0010d518)
    u8  field_671;                      // +0x0671: `strb r0,[r4,#0x671]` = 0x40 (0x0010d51c)
    u8  pad_672[0x0A];                  // +0x0672..+0x067C
    u32 field_67c;                      // +0x067C: `str r6,[r4,#0x67c]` (0x0010d520)
    u8  field_680;                      // +0x0680: `strb r6,[r4,#0x680]` (0x0010d524)
    u8  field_681;                      // +0x0681: `strb r0,[r4,#0x681]` = 0x40 (0x0010d528)
    u8  field_682;                      // +0x0682: `strb r6,[r4,#0x682]` (0x0010d52c)
    u8  pad_683[0x09];                  // +0x0683..+0x068C
    u32 field_68c;                      // +0x068C: `str r6,[r4,#0x68c]` (0x0010d530)
    u8  field_690;                      // +0x0690: `strb r6,[r4,#0x690]` (0x0010d534)
    u8  field_691;                      // +0x0691: `strb r0,[r4,#0x691]` = 0x40 (0x0010d538)
    u8  field_692;                      // +0x0692: `strb r6,[r4,#0x692]` (0x0010d53c)
    u8  pad_693[0x01];                  // +0x0693..+0x0694
    AsdSoundSequenceSlot sequences[4];  // +0x0694..+0x0784
    AsdSoundVoice voice;                // +0x0784..+0x11C8
    void* field_11c8;                   // +0x11C8: `str r0,[r7]` r7=system+0x11c8 (0x0010988c)
    u8  field_11cc;                     // +0x11CC: `strb r8,[r0,r7]` = 1 (0x0010984c)
    u8  field_11cd;                     // +0x11CD: `strb r0,[r1,#0x1cd]` = 0x40 (0x0010d578)
    u8  pad_11ce[0x36];                 // +0x11CE..+0x1204
    void* field_1204;                   // +0x1204: `str r2,[r1,#0x204]` (0x002c1ed0)
    u8  pad_1208[0x10];                 // +0x1208..+0x1218
    void* field_1218;                   // +0x1218: `str r0,[r6,#0x218]` (0x0010c758)
    u8  field_121c;                     // +0x121C: `strbne r8,[r0,r5]` = 1 (0x001096d8)
    u8  pad_121d[0x03];                 // +0x121D..+0x1220
};
static_assert(offsetof(AsdSoundSystem, field_004) == 0x0004);
static_assert(offsetof(AsdSoundSystem, container_a) == 0x012C);
static_assert(offsetof(AsdSoundSystem, container_b) == 0x0184);
static_assert(offsetof(AsdSoundSystem, container_c) == 0x0244);
static_assert(offsetof(AsdSoundSystem, field_464) == 0x0464);
static_assert(offsetof(AsdSoundSystem, field_468) == 0x0468);
static_assert(offsetof(AsdSoundSystem, field_46c) == 0x046C);
static_assert(offsetof(AsdSoundSystem, field_470) == 0x0470);
static_assert(offsetof(AsdSoundSystem, field_474) == 0x0474);
static_assert(offsetof(AsdSoundSystem, field_478) == 0x0478);
static_assert(offsetof(AsdSoundSystem, path) == 0x047C);
static_assert(offsetof(AsdSoundSystem, streams) == 0x04BC);
static_assert(offsetof(AsdSoundSystem, field_630) == 0x0630);
static_assert(offsetof(AsdSoundSystem, field_66c) == 0x066C);
static_assert(offsetof(AsdSoundSystem, field_67c) == 0x067C);
static_assert(offsetof(AsdSoundSystem, field_68c) == 0x068C);
static_assert(offsetof(AsdSoundSystem, sequences) == 0x0694);
static_assert(offsetof(AsdSoundSystem, voice) == 0x0784);
static_assert(offsetof(AsdSoundSystem, field_11c8) == 0x11C8);
static_assert(offsetof(AsdSoundSystem, field_11cc) == 0x11CC);
static_assert(offsetof(AsdSoundSystem, field_11cd) == 0x11CD);
static_assert(offsetof(AsdSoundSystem, field_1204) == 0x1204);
static_assert(offsetof(AsdSoundSystem, field_1218) == 0x1218);
static_assert(offsetof(AsdSoundSystem, field_121c) == 0x121C);
static_assert(sizeof(AsdSoundSystem) == 0x1220);

// ---------------------------------------------------------------------------
// Stream settings (AsdSoundSystem.cpp, 0x004E3138) and system flags
// ---------------------------------------------------------------------------

/**
 * Sequencer/stream parameters at `0x004E3138`.
 *
 * `AsdSoundSystem_func_0010c5d4` sets tempo/track defaults and the flags byte,
 * `AsdSoundSystem_func_0010d40c` clears the whole block.
 */
struct AsdSoundStreamSettings {
    f32 field_00;                       // +0x00: `vstr s0,[r0]` = 0.5f (0x0010c68c)
    u32 field_04;                       // +0x04: `stm r6,{r1,r2,r3,ip}` = 0x1E (0x0010c6a4)
    u32 field_08;                       // +0x08: second word of that `stm` = 0x1E
    u32 field_0c;                       // +0x0C: third word of that `stm` = 0x0F
    u32 field_10;                       // +0x10: fourth word of that `stm` = 0x0F
    u32 field_14;                       // +0x14: `str r6,[r0,#0x14]` = 0 (0x0010d598)
    u8  field_18;                       // +0x18: `ldrb r5,[r0,#0x18]` (0x0010c67c)
    u8  field_19;                       // +0x19: `strb r6,[r0,#0x19]` (0x0010d59c)
    u8  field_1a;                       // +0x1A: `strbne sb,[r0,#0x1a]` (0x0010c6b4)
    u8  pad_1b[0x01];                   // +0x1B..+0x1C
    u32 field_1c;                       // +0x1C: `str r6,[r0]` after `add r0,#0x1c` (0x0010d5b4)
    u32 field_20;                       // +0x20: `str r6,[r0,#4]` (0x0010d5b8)
    u8  pad_24[0x0D];                   // +0x24..+0x31
    u8  field_31;                       // +0x31: `strb r6,[r0,#0x15]` (0x0010d5ac)
    u8  pad_32[0x01];                   // +0x32..+0x33
    u8  field_33;                       // +0x33: `ldrb r1,[r1,#0x17]` (0x0010c6ac)
};
static_assert(offsetof(AsdSoundStreamSettings, field_04) == 0x04);
static_assert(offsetof(AsdSoundStreamSettings, field_0c) == 0x0C);
static_assert(offsetof(AsdSoundStreamSettings, field_14) == 0x14);
static_assert(offsetof(AsdSoundStreamSettings, field_18) == 0x18);
static_assert(offsetof(AsdSoundStreamSettings, field_19) == 0x19);
static_assert(offsetof(AsdSoundStreamSettings, field_1a) == 0x1A);
static_assert(offsetof(AsdSoundStreamSettings, field_1c) == 0x1C);
static_assert(offsetof(AsdSoundStreamSettings, field_20) == 0x20);
static_assert(offsetof(AsdSoundStreamSettings, field_31) == 0x31);
static_assert(offsetof(AsdSoundStreamSettings, field_33) == 0x33);
static_assert(sizeof(AsdSoundStreamSettings) == 0x34);

/** Mixer flags at `0x004E30EC`; only the byte at +0x48 is read. */
struct AsdSoundSettings {
    u8 pad_00[0x48];                    // +0x00..+0x48
    u8 field_48;                        // +0x48: `ldrb r0,[r8,#0x48]` (0x0010990c)
};
static_assert(offsetof(AsdSoundSettings, field_48) == 0x48);

/**
 * Engine start-up descriptor built on the stack by
 * `AsdSoundSystem_func_0010d40c` and consumed by `engine_func_00120d44` /
 * `engine_func_00120ac8`.
 *
 * The descriptor base is `sp + 4` (0x0010d4a4 `add r0,sp,#4`), so the stack
 * word at `sp + 0x04` is +0x00 here and the word at `sp + 0x24` is +0x20.
 * `sp + 0x23` is never written and stays uninitialised.
 */
struct AsdSoundInitConfig {
    u32 field_00;                       // +0x00 (sp+0x04): `stm r0,{r1,r6}` = 4 (0x0010d48c)
    u32 field_04;                       // +0x04 (sp+0x08): second word of that `stm` = 0;
                                        // 0x0010d4b0 raises it to 1 when duration > 0
    u32 field_08;                       // +0x08 (sp+0x0C): `stm lr,{r0,r2,r3}` = 0x4000 (0x0010d470)
    u32 field_0c;                       // +0x0C (sp+0x10): second word of that `stm` = 0x20000
    u32 field_10;                       // +0x10 (sp+0x14): third word of that `stm` = 3
    u32 field_14;                       // +0x14 (sp+0x18): `stm r2,{r0,ip}` = 0x4000 (0x0010d47c)
    u32 field_18;                       // +0x18 (sp+0x1C): second word of that `stm` = 0x2000
    u8  field_1c;                       // +0x1C (sp+0x20): `strb r7,[sp,#0x20]` = 1 (0x0010d494)
    u8  field_1d;                       // +0x1D (sp+0x21): `strb r6,[sp,#0x21]` = 0 (0x0010d4a0)
    u8  field_1e;                       // +0x1E (sp+0x22): `strb r7,[sp,#0x22]` = 1 (0x0010d4a8)
    u8  pad_1f;                         // +0x1F (sp+0x23): never written
    u32 field_20;                       // +0x20 (sp+0x24): `str r8,[sp,#0x24]` = -1 (0x0010d4ac)
};
static_assert(offsetof(AsdSoundInitConfig, field_04) == 0x04);
static_assert(offsetof(AsdSoundInitConfig, field_08) == 0x08);
static_assert(offsetof(AsdSoundInitConfig, field_0c) == 0x0C);
static_assert(offsetof(AsdSoundInitConfig, field_10) == 0x10);
static_assert(offsetof(AsdSoundInitConfig, field_14) == 0x14);
static_assert(offsetof(AsdSoundInitConfig, field_18) == 0x18);
static_assert(offsetof(AsdSoundInitConfig, field_1c) == 0x1C);
static_assert(offsetof(AsdSoundInitConfig, field_1d) == 0x1D);
static_assert(offsetof(AsdSoundInitConfig, field_1e) == 0x1E);
static_assert(offsetof(AsdSoundInitConfig, field_20) == 0x20);
static_assert(sizeof(AsdSoundInitConfig) == 0x24);

// ---------------------------------------------------------------------------
// Globals
// ---------------------------------------------------------------------------

extern AsdSoundSystem g_AsdSoundSystem;                 // 0x004E1F68
extern AsdSoundStreamSettings g_AsdSoundStream;         // 0x004E3138
extern AsdSoundSettings g_AsdSoundSettings;             // 0x004E30EC
extern AsdSoundLock g_AsdSoundLock;                     // 0x004E315C

// Effect units and their configuration blocks.  Only the configuration blocks
// are written by the reconstructed code; the unit interiors are opaque.
extern u8 g_AsdSoundEffectUnitA;                        // 0x004C5484
extern AsdSoundEffectConfigA g_AsdSoundEffectConfigA;   // 0x004C54E4
extern u8 g_AsdSoundEffectUnitB;                        // 0x004C54F4
extern AsdSoundEffectConfigB g_AsdSoundEffectConfigB;   // 0x004C5604

// Two effect buffers: [0] for `soundEffect_func_0010368c`,
// [1] for `soundEffect_func_00109524` (`str r0,[r1]` / `str r0,[r1,#4]`).
extern void* g_AsdSoundEffectBuffers[2];                // 0x0044E0E0

// Sound-test front-end object created by `soundTest_func_001ea808`.
extern void* g_SoundTestObject;                         // 0x0044E110

// Word published by `AsdSoundSystem_func_0010b974` once the archive is loaded.
extern void* g_AsdSoundSystemHandle;                    // 0x004E23E0

// Bit 0 gates the one-shot `engine_func_002c00d4` latch in the voice loop.
extern u32 g_AsdSoundFlag;                              // 0x00476628

// Reference mix levels copied into every voice slot by
// `AsdSoundSystem_func_00109690` (0x001099e0).
extern AsdSoundFloat3 g_AsdSoundMixLevels;              // 0x004EFD2C

// ---------------------------------------------------------------------------
// Functions
// ---------------------------------------------------------------------------

// 0x0010368c (184 B): build the first effect unit, then chain into 0x00109524.
void soundEffect_func_0010368c();

// 0x00109524 (240 B): build the second effect unit and register it.
void soundEffect_func_00109524();

// 0x00109690 (1,040 B): load the sound archive and initialise its voices.
u32 AsdSoundSystem_func_00109690(const char* archive, u32 enable, u32 size);

// 0x0010b974 (176 B): lazily load the extra archive buffer.
void* AsdSoundSystem_func_0010b974();

// 0x0010c078 (380 B): build a streamed-sound object from a data block.
void* AsdSoundSystem_func_0010c078(void* data, u32 size, u32 extra);

// 0x0010c5d4 (480 B): open sequence slot `index` and publish the active one.
u32 AsdSoundSystem_func_0010c5d4(u32 index, u32 size);

// 0x0010d40c (516 B): start the DSP/mixer and reset the sound-system state.
void AsdSoundSystem_func_0010d40c(s32 duration);

// 0x002c1df4 (308 B): open stream slot `index` and publish the active one.
u32 AsdSoundSystem_func_002c1df4(u32 index, u32 size);

// 0x001ea808 (264 B): create the two sound-test UI widgets.
void soundTest_func_001ea808();

} // namespace smt4::engine
