#include "types.h"

// Address-local leaf routines reconstructed from the original ARM code.
// DECOMP_FUNC(0x001ab894, 24)
extern "C" __attribute__((naked)) void engine_func_001ab894() {
    asm volatile(
        R"batch16(
cmp r0, #0
beq .Lbatch16a_001ab894_001ab8a8
ldr r1, [r0]
ldr r1, [r1, #4]
bx r1
.Lbatch16a_001ab894_001ab8a8:
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x00100c74, 28)
extern "C" __attribute__((naked, target("thumb"))) void crt_func_00100c74() {
    asm volatile(
        R"batch16(
push {r4, lr}
movs r3, r0
b .Lbatch16a_00100c74_00100c88
.Lbatch16a_00100c74_00100c7a:
ldrh r4, [r1]
strh r4, [r0]
ldrh r4, [r1]
adds r0, r0, #2
cmp r4, #0
beq .Lbatch16a_00100c74_00100c88
adds r1, r1, #2
.Lbatch16a_00100c74_00100c88:
subs r2, r2, #1
bhs .Lbatch16a_00100c74_00100c7a
movs r0, r3
pop {r4, pc}
        )batch16"
    );
}
// DECOMP_FUNC(0x001524e8, 36)
extern "C" __attribute__((naked)) void script_vm_func_001524e8() {
    asm volatile(
        R"batch16(
mov r0, r0
bx lr
mrc p15, #0, r0, c13, c0, #3
add r0, r0, #0x5c
bx lr
mov r2, r0
ldr r0, [r1]
bx r2
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x00379ba0, 40)
extern "C" __attribute__((naked)) void func_00379ba0() {
    asm volatile(
        R"batch16(
mov r3, r0
ldr r0, [r0]
mov r2, r1
cmp r0, #0
beq .Lbatch16a_00379ba0_00379bc4
ldr r1, [r0]
ldr ip, [r1, #0xc]
ldr r1, [r3, #0xc]
bx ip
.Lbatch16a_00379ba0_00379bc4:
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x002396f8, 60)
extern "C" __attribute__((naked)) void func_002396f8() {
    asm volatile(
        R"batch16(
mov r1, #0
.Lbatch16a_002396f8_002396fc:
ldrb r2, [r0, r1]
cmp r2, #0
bne .Lbatch16a_002396f8_00239718
add r2, r0, r1
ldrb r2, [r2, #1]
cmp r2, #0
beq .Lbatch16a_002396f8_00239720
.Lbatch16a_002396f8_00239718:
mov r0, #0
bx lr
.Lbatch16a_002396f8_00239720:
add r1, r1, #2
cmp r1, #8
blt .Lbatch16a_002396f8_002396fc
mov r0, #1
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x002c55e4, 64)
extern "C" __attribute__((naked)) void func_002c55e4() {
    asm volatile(
        R"batch16(
cmp r0, #0
ble .Lbatch16a_002c55e4_002c55fc
cmp r1, #0
ble .Lbatch16a_002c55e4_002c5600
cmp r0, r1
bgt .Lbatch16a_002c55e4_002c5604
.Lbatch16a_002c55e4_002c55fc:
vmov.f32 s0, s1
.Lbatch16a_002c55e4_002c5600:
bx lr
.Lbatch16a_002c55e4_002c5604:
vmov s2, r1
vmov s3, r0
vsub.f32 s4, s1, s0
vcvt.f32.s32 s2, s2
vcvt.f32.s32 s3, s3
vdiv.f32 s1, s2, s3
vmla.f32 s0, s4, s1
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x00339404, 64)
extern "C" __attribute__((naked)) void ui_func_00339404() {
    asm volatile(
        R"batch16(
mov r2, #0
.Lbatch16a_00339404_00339408:
add r3, r0, r2, lsl #2
add r3, r3, #0x2000
ldr r3, [r3, #0x134]
cmp r3, #0
beq .Lbatch16a_00339404_00339430
ldr r3, [r3, #4]
cmp r3, r1
bne .Lbatch16a_00339404_00339430
mov r0, #1
bx lr
.Lbatch16a_00339404_00339430:
add r2, r2, #1
cmp r2, #0x2a
blt .Lbatch16a_00339404_00339408
mov r0, #0
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x003b3564, 68)
extern "C" __attribute__((naked)) void func_003b3564() {
    asm volatile(
        R"batch16(
mov r2, #0
str r4, [sp, #-4]!
.Lbatch16a_003b3564_003b356c:
add r3, r1, r2
add ip, r0, r2
ldrb r4, [r3, #0xc]
add r2, r2, #2
cmp r2, #0x14
strb r4, [ip, #0xc]
ldrb r3, [r3, #0xd]
strb r3, [ip, #0xd]
blo .Lbatch16a_003b3564_003b356c
ldr r2, [r1, #4]
str r2, [r0, #4]
ldr r1, [r1, #8]
str r1, [r0, #8]
pop {r4}
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x0025a274, 72)
extern "C" __attribute__((naked)) void script_vm_func_0025a274() {
    asm volatile(
        R"batch16(
ldr r1, [r0, #0x34]
cmp r1, #0
ble .Lbatch16a_0025a274_0025a2ac
ldr r1, [r0, #0x4c]
cmp r1, #0
beq .Lbatch16a_0025a274_0025a2ac
ldr r0, [r0]
tst r0, #1
bne .Lbatch16a_0025a274_0025a2b4
vldr s0, [r1, #0x38]
vldr s1, [r1, #0x48]
vcmpe.f32 s0, s1
vmrs apsr_nzcv, fpscr
blt .Lbatch16a_0025a274_0025a2b4
.Lbatch16a_0025a274_0025a2ac:
mov r0, #1
bx lr
.Lbatch16a_0025a274_0025a2b4:
mov r0, #0
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x0033692c, 72)
extern "C" __attribute__((naked)) void func_0033692c() {
    asm volatile(
        R"batch16(
add r0, r0, #0x1fc0
mov r1, #4
ldr r3, [r0]
.Lbatch16a_0033692c_00336938:
add r0, r1, r1, lsl #4
add r0, r0, r1, lsl #6
add r0, r3, r0, lsl #3
ldr r2, [r0]
tst r2, #1
beq .Lbatch16a_0033692c_00336960
tst r2, #0x40
bne .Lbatch16a_0033692c_00336960
tst r2, #0x10
bne .Lbatch16a_0033692c_00336970
.Lbatch16a_0033692c_00336960:
add r1, r1, #1
cmp r1, #0x36
blt .Lbatch16a_0033692c_00336938
mov r0, #0
.Lbatch16a_0033692c_00336970:
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x00368588, 72)
extern "C" __attribute__((naked)) void func_00368588() {
    asm volatile(
        R"batch16(
push {r4, r5, r6, lr}
mov r6, r0
ldr r0, [r0, #8]
cmp r0, #0
beq .Lbatch16a_00368588_003685cc
add r1, r1, #0x164
ldm r1, {r4, r5}
cmp r4, r5
beq .Lbatch16a_00368588_003685cc
.Lbatch16a_00368588_003685ac:
ldr r0, [r6, #8]
ldr r1, [r4]
ldr r2, [r0]
ldr r2, [r2, #0xc]
blx r2
add r4, r4, #4
cmp r4, r5
bne .Lbatch16a_00368588_003685ac
.Lbatch16a_00368588_003685cc:
pop {r4, r5, r6, pc}
        )batch16"
    );
}
// DECOMP_FUNC(0x003e8884, 72)
extern "C" __attribute__((naked)) void func_003e8884() {
    asm volatile(
        R"batch16(
mov r3, #2
mov r0, r0
cmp r3, #0
mov ip, #1
add r0, r2, #8
str r4, [sp, #-4]!
ble .Lbatch16a_003e8884_003e88c4
.Lbatch16a_003e8884_003e88a0:
ldr r4, [r2, #4]
bics r4, ip, r4
ldreq r4, [r0]
lsl ip, ip, #1
add r0, r0, #4
streq r4, [r1]
subs r3, r3, #1
add r1, r1, #4
bne .Lbatch16a_003e8884_003e88a0
.Lbatch16a_003e8884_003e88c4:
pop {r4}
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x00153160, 76)
extern "C" __attribute__((naked)) void func_00153160() {
    asm volatile(
        R"batch16(
ldrb r1, [r0, #0xe]
cmp r1, #0
bne .Lbatch16a_00153160_0015319c
ldr r1, [pc, #0x30]
ldrb r2, [r1, #0x18]
cmp r2, #0
beq .Lbatch16a_00153160_00153194
ldrb r1, [r1, #0x19]
ldrb r0, [r0, #0xf]
sub r0, r1, r0
sxtb r0, r0
cmp r0, #2
ble .Lbatch16a_00153160_0015319c
.Lbatch16a_00153160_00153194:
mov r0, #0
bx lr
.Lbatch16a_00153160_0015319c:
mov r0, #1
bx lr
.word 0x004e8264
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x0033a7d4, 76)
extern "C" __attribute__((naked)) void script_vm_func_0033a7d4() {
    asm volatile(
        R"batch16(
add r0, r0, #0x1fc0
mov r3, #0
ldr r0, [r0]
mov r1, #4
.Lbatch16a_0033a7d4_0033a7e4:
add r2, r1, r1, lsl #4
add r2, r2, r1, lsl #6
ldr r2, [r0, r2, lsl #3]
tst r2, #1
beq .Lbatch16a_0033a7d4_0033a810
add r1, r1, #1
sxth r1, r1
cmp r1, #0x36
blt .Lbatch16a_0033a7d4_0033a7e4
mov r0, r3
bx lr
.Lbatch16a_0033a7d4_0033a810:
add r2, r1, r1, lsl #4
add r1, r2, r1, lsl #6
add r0, r0, r1, lsl #3
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x00381ad8, 76)
extern "C" __attribute__((naked)) void func_00381ad8() {
    asm volatile(
        R"batch16(
ldrb r2, [r0, #9]
mov ip, #1
tst r2, ip, lsl r1
mov r3, r0
mvn r0, #0
beq .Lbatch16a_00381ad8_00381b18
add r1, r1, r1, lsl #2
mov r2, #0
add r1, r3, r1, lsl #4
.Lbatch16a_00381ad8_00381afc:
add r3, r1, r2, lsl #2
ldr r3, [r3, #0x10]
cmn r3, #1
beq .Lbatch16a_00381ad8_00381b1c
add r2, r2, #1
cmp r2, #0x14
blt .Lbatch16a_00381ad8_00381afc
.Lbatch16a_00381ad8_00381b18:
bx lr
.Lbatch16a_00381ad8_00381b1c:
mov r0, r2
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x001408c0, 80)
extern "C" __attribute__((naked)) void func_001408c0() {
    asm volatile(
        R"batch16(
mov r1, #0
str r1, [r0, #0xc]
strb r1, [r0, #0x14]
strb r1, [r0, #0x15]
strb r1, [r0, #0x16]
strb r1, [r0, #0x17]
strh r1, [r0, #0x20]
str r1, [r0, #0x58]
str r1, [r0, #0x5c]
str r1, [r0]
str r1, [r0, #4]
bx lr
mov r1, r0
ldr r0, [r0, #0x1e8]
cmp r0, #0
beq .Lbatch16a_001408c0_0014090c
ldr r0, [r1, #0x1ec]
ldr r1, [r1, #0x1e8]
bx r1
.Lbatch16a_001408c0_0014090c:
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x0028c8d0, 80)
extern "C" __attribute__((naked)) void script_vm_func_0028c8d0() {
    asm volatile(
        R"batch16(
ldr r1, [r0, #0x58]
cmp r1, #0
ble .Lbatch16a_0028c8d0_0028c91c
vstr s0, [r0, #0x7c]
vldr s1, [r0, #0x74]
ldr r0, [r0, #0x2c]
mov r1, #0
vmul.f32 s0, s1, s0
ldr r2, [r0, #0x148]
cmp r2, #0
beq .Lbatch16a_0028c8d0_0028c91c
ldr r2, [r0, #0x28]
ldr r0, [r0, #0x14c]
ldr r3, [r2, #0x28]
ldr r2, [r2, #0x1c]
mla r0, r0, r3, r1
ldr r0, [r2, r0, lsl #2]
cmp r0, #0
vstrne s0, [r0, #0x40]
.Lbatch16a_0028c8d0_0028c91c:
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x00139f84, 84)
extern "C" __attribute__((naked)) void func_00139f84() {
    asm volatile(
        R"batch16(
mov ip, r0
mov r0, r1
str r4, [sp, #-4]!
rsb r4, r2, #0
sub r1, ip, r0
cmp r1, r4
bge .Lbatch16a_00139f84_00139fb8
add r1, r1, r2
mul r1, r1, r3
add r0, r0, r1, asr #7
sxth r0, r0
.Lbatch16a_00139f84_00139fb0:
pop {r4}
bx lr
.Lbatch16a_00139f84_00139fb8:
cmp r1, r2
ble .Lbatch16a_00139f84_00139fb0
sub r1, r1, r2
pop {r4}
mul r1, r1, r3
add r0, r0, r1, asr #7
sxth r0, r0
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x002befdc, 84)
extern "C" __attribute__((naked)) void func_002befdc() {
    asm volatile(
        R"batch16(
push {r4, lr}
add r4, r0, r1, lsl #5
add r4, r4, #0x1000
add r4, r4, #0x1ec
mov r0, r2
ldr r1, [r4]
add r2, r1, #1
add r3, r4, r1, lsl #2
ldr r1, [r3, #8]
add r3, r4, r2, lsl #2
str r2, [r4]
str r0, [r3, #8]
ldrb r2, [r4, #0x18]
cmp r2, #0
cmpeq r1, r0
beq .Lbatch16a_002befdc_002bf02c
ldr r1, [r4, #0x1c]
blx r1
mov r0, #0
strb r0, [r4, #0x18]
.Lbatch16a_002befdc_002bf02c:
pop {r4, pc}
        )batch16"
    );
}
// DECOMP_FUNC(0x00362f20, 84)
extern "C" __attribute__((naked)) void func_00362f20() {
    asm volatile(
        R"batch16(
push {r4, r5, r6, lr}
mov r5, r0
ldr r0, [r1]
mov r4, r1
mov r1, r5
ldr r2, [r0, #0x34]
mov r0, r4
blx r2
add r0, r5, #0x10
mov r6, r4
ldrd r4, r5, [r0, #8]
b .Lbatch16a_00362f20_00362f64
.Lbatch16a_00362f20_00362f50:
ldr r1, [r0]
ldr r2, [r1, #0x10]
mov r1, r6
blx r2
add r4, r4, #4
.Lbatch16a_00362f20_00362f64:
cmp r4, r5
ldrne r0, [r4]
bne .Lbatch16a_00362f20_00362f50
pop {r4, r5, r6, pc}
        )batch16"
    );
}
// DECOMP_FUNC(0x00365998, 84)
extern "C" __attribute__((naked)) void func_00365998() {
    asm volatile(
        R"batch16(
push {r4, r5, r6, lr}
mov r5, r0
ldr r0, [r1]
mov r4, r1
mov r1, r5
ldr r2, [r0, #0x1c]
mov r0, r4
blx r2
add r0, r5, #0x10
mov r6, r4
ldrd r4, r5, [r0, #8]
b .Lbatch16a_00365998_003659dc
.Lbatch16a_00365998_003659c8:
ldr r1, [r0]
ldr r2, [r1, #0x10]
mov r1, r6
blx r2
add r4, r4, #4
.Lbatch16a_00365998_003659dc:
cmp r4, r5
ldrne r0, [r4]
bne .Lbatch16a_00365998_003659c8
pop {r4, r5, r6, pc}
        )batch16"
    );
}
// DECOMP_FUNC(0x00367c14, 84)
extern "C" __attribute__((naked)) void func_00367c14() {
    asm volatile(
        R"batch16(
push {r4, r5, r6, lr}
mov r5, r0
ldr r0, [r1]
mov r4, r1
mov r1, r5
ldr r2, [r0, #0x38]
mov r0, r4
blx r2
add r0, r5, #0x10
mov r6, r4
ldrd r4, r5, [r0, #8]
b .Lbatch16a_00367c14_00367c58
.Lbatch16a_00367c14_00367c44:
ldr r1, [r0]
ldr r2, [r1, #0x10]
mov r1, r6
blx r2
add r4, r4, #4
.Lbatch16a_00367c14_00367c58:
cmp r4, r5
ldrne r0, [r4]
bne .Lbatch16a_00367c14_00367c44
pop {r4, r5, r6, pc}
        )batch16"
    );
}
// DECOMP_FUNC(0x00370550, 84)
extern "C" __attribute__((naked)) void func_00370550() {
    asm volatile(
        R"batch16(
push {r4, r5, r6, lr}
mov r5, r0
ldr r0, [r1]
mov r4, r1
mov r1, r5
ldr r2, [r0, #0x28]
mov r0, r4
blx r2
add r0, r5, #0x10
mov r6, r4
ldrd r4, r5, [r0, #8]
b .Lbatch16a_00370550_00370594
.Lbatch16a_00370550_00370580:
ldr r1, [r0]
ldr r2, [r1, #0x10]
mov r1, r6
blx r2
add r4, r4, #4
.Lbatch16a_00370550_00370594:
cmp r4, r5
ldrne r0, [r4]
bne .Lbatch16a_00370550_00370580
pop {r4, r5, r6, pc}
        )batch16"
    );
}
// DECOMP_FUNC(0x003766b8, 84)
extern "C" __attribute__((naked)) void func_003766b8() {
    asm volatile(
        R"batch16(
push {r4, r5, r6, lr}
mov r5, r0
ldr r0, [r1]
mov r4, r1
mov r1, r5
ldr r2, [r0, #0xc]
mov r0, r4
blx r2
add r0, r5, #0x10
mov r6, r4
ldrd r4, r5, [r0, #8]
b .Lbatch16a_003766b8_003766fc
.Lbatch16a_003766b8_003766e8:
ldr r1, [r0]
ldr r2, [r1, #0x10]
mov r1, r6
blx r2
add r4, r4, #4
.Lbatch16a_003766b8_003766fc:
cmp r4, r5
ldrne r0, [r4]
bne .Lbatch16a_003766b8_003766e8
pop {r4, r5, r6, pc}
        )batch16"
    );
}
// DECOMP_FUNC(0x00337020, 88)
extern "C" __attribute__((naked)) void func_00337020() {
    asm volatile(
        R"batch16(
mov r3, r0
add r3, r3, #0x1c00
add r3, r3, #0x298
push {r4, r5}
ldr ip, [r3]
mov r0, #0
mov r2, #4
.Lbatch16a_00337020_0033703c:
add r3, r2, r2, lsl #2
add r3, r3, r2, lsl #6
add r3, ip, r3, lsl #2
ldr r4, [r3, #0x50]
tst r4, #1
tstne r4, #0x80
beq .Lbatch16a_00337020_00337064
ldrsb r3, [r3, #0x44]
cmp r3, r1
addeq r0, r0, #1
.Lbatch16a_00337020_00337064:
add r2, r2, #1
cmp r2, #0x36
blt .Lbatch16a_00337020_0033703c
pop {r4, r5}
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x00396534, 88)
extern "C" __attribute__((naked)) void engine_func_00396534() {
    asm volatile(
        R"batch16(
mov r1, #0
str r4, [sp, #-4]!
str r1, [r0]
str r1, [r0, #0xc]
str r1, [r0, #0x10]
str r1, [r0, #0x14]
mov r3, r1
mov r2, r1
strh r1, [r0, #0xa0]
.Lbatch16a_00396534_00396558:
add ip, r0, r3, lsl #2
add r3, r3, #1
add r2, r2, #2
add r4, r0, r3, lsl #2
str r1, [ip, #0x18]
cmp r2, #0x20
add r3, r3, #1
str r1, [r4, #0x18]
blt .Lbatch16a_00396534_00396558
str r1, [r0, #0x98]
str r1, [r0, #0x9c]
pop {r4}
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x003a89ec, 88)
extern "C" __attribute__((naked)) void func_003a89ec() {
    asm volatile(
        R"batch16(
ldr r1, [r0, #0x14]
add r1, r0, r1, lsl #3
add r2, r1, #0xa400
add r2, r2, #0x1b8
add r1, r1, #0xa400
add r1, r1, #0x1bc
ldr r2, [r2]
ldr r1, [r1]
cmp r2, #0
bne .Lbatch16a_003a89ec_003a8a24
tst r1, #1
beq .Lbatch16a_003a89ec_003a8a40
cmp r1, #0
beq .Lbatch16a_003a89ec_003a8a40
.Lbatch16a_003a89ec_003a8a24:
tst r1, #1
add r0, r0, r1, asr #1
beq .Lbatch16a_003a89ec_003a8a38
ldr r1, [r0]
ldr r2, [r1, r2]
.Lbatch16a_003a89ec_003a8a38:
nop
bx r2
.Lbatch16a_003a89ec_003a8a40:
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x003ac42c, 88)
extern "C" __attribute__((naked)) void func_003ac42c() {
    asm volatile(
        R"batch16(
ldr r1, [r0, #0x14]
add r1, r0, r1, lsl #3
add r2, r1, #0xa400
add r2, r2, #0x1b8
add r1, r1, #0xa400
add r1, r1, #0x1bc
ldr r2, [r2]
ldr r1, [r1]
cmp r2, #0
bne .Lbatch16a_003ac42c_003ac464
tst r1, #1
beq .Lbatch16a_003ac42c_003ac480
cmp r1, #0
beq .Lbatch16a_003ac42c_003ac480
.Lbatch16a_003ac42c_003ac464:
tst r1, #1
add r0, r0, r1, asr #1
beq .Lbatch16a_003ac42c_003ac478
ldr r1, [r0]
ldr r2, [r1, r2]
.Lbatch16a_003ac42c_003ac478:
nop
bx r2
.Lbatch16a_003ac42c_003ac480:
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x002629a8, 92)
extern "C" __attribute__((naked)) void camp_func_002629a8() {
    asm volatile(
        R"batch16(
mov r1, #0
.Lbatch16a_002629a8_002629ac:
add r3, r2, r1, lsl #1
ldrh r3, [r3]
cmp r3, #0
beq .Lbatch16a_002629a8_002629d8
ldr ip, [r0, #0x178]
add ip, r0, ip, lsl #1
add ip, ip, #0x100
strh r3, [ip, #0x46]
ldr r3, [r0, #0x178]
add r3, r3, #1
str r3, [r0, #0x178]
.Lbatch16a_002629a8_002629d8:
add r1, r1, #1
cmp r1, #8
blt .Lbatch16a_002629a8_002629ac
ldr r1, [r0, #0x178]
cmp r1, #0x18
bge .Lbatch16a_002629a8_00262a00
add r1, r0, r1, lsl #1
add r1, r1, #0x100
mov r0, #0
strh r0, [r1, #0x46]
.Lbatch16a_002629a8_00262a00:
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x0039611c, 92)
extern "C" __attribute__((naked)) void func_0039611c() {
    asm volatile(
        R"batch16(
push {r4, lr}
mov r4, r0
ldr r0, [r0, #0x58]
cmp r0, #0
subgt r1, r0, #1
strgt r1, [r4, #0x58]
ldr r0, [r4, #0x58]
cmp r0, #0
bne .Lbatch16a_0039611c_0039614c
ldrb r1, [r4, #8]
bic r1, r1, #1
strb r1, [r4, #8]
.Lbatch16a_0039611c_0039614c:
ldr r0, [r4, #0x68]
cmp r0, #0
beq .Lbatch16a_0039611c_00396164
ldr r1, [r0]
ldr r1, [r1, #0xc]
blx r1
.Lbatch16a_0039611c_00396164:
ldr r0, [r4]
ldr r1, [r0, #0x18]
mov r0, r4
pop {r4, lr}
bx r1
        )batch16"
    );
}
// DECOMP_FUNC(0x00235eec, 96)
extern "C" __attribute__((naked)) void func_00235eec() {
    asm volatile(
        R"batch16(
cmp r2, #0
str r4, [sp, #-4]!
beq .Lbatch16a_00235eec_00235f0c
cmp r2, #1
beq .Lbatch16a_00235eec_00235f10
cmp r2, #2
ldreq r2, [r0]
bne .Lbatch16a_00235eec_00235f10
.Lbatch16a_00235eec_00235f0c:
str r2, [r0, #4]
.Lbatch16a_00235eec_00235f10:
cmp r1, #0
beq .Lbatch16a_00235eec_00235f44
ldr r3, [r0, #4]
mov r2, #0
add r3, r3, r1
ldr r1, [r0]
subs r4, r1, r3
sbcs ip, r2, r2
blt .Lbatch16a_00235eec_00235f40
cmp r2, #0
movlt r1, #0
movge r1, r3
.Lbatch16a_00235eec_00235f40:
str r1, [r0, #4]
.Lbatch16a_00235eec_00235f44:
pop {r4}
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x002d56fc, 96)
extern "C" __attribute__((naked)) void ui_func_002d56fc() {
    asm volatile(
        R"batch16(
ldr r1, [r0, #0x68]
cmp r1, #0
ble .Lbatch16a_002d56fc_002d5754
ldr r0, [r0, #0x2c]
mov r1, #0
ldr r2, [r0, #0x150]
cmp r2, #0
beq .Lbatch16a_002d56fc_002d5754
ldr r2, [r0, #0x28]
ldr r0, [r0, #0x154]
ldr r3, [r2, #0x28]
ldr r2, [r2, #0x1c]
mla r0, r0, r3, r1
ldr r0, [r2, r0, lsl #2]
cmp r0, #0
beq .Lbatch16a_002d56fc_002d5754
vldr s0, [r0, #0x38]
vldr s1, [r0, #0x48]
vcmpe.f32 s1, s0
vmrs apsr_nzcv, fpscr
movhi r0, #0
bhi .Lbatch16a_002d56fc_002d5758
.Lbatch16a_002d56fc_002d5754:
mov r0, #1
.Lbatch16a_002d56fc_002d5758:
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x003eaf4c, 96)
extern "C" __attribute__((naked)) void func_003eaf4c() {
    asm volatile(
        R"batch16(
sub r0, r0, #0xc
ldr r2, [r0, #0x218]
cmp r2, r1
ldreq r0, [r0, #0x21c]
movne r2, #1
beq .Lbatch16a_003eaf4c_003eaf7c
.Lbatch16a_003eaf4c_003eaf64:
add r3, r0, r2, lsl #3
ldr ip, [r3, #0x218]
cmp ip, r1
bne .Lbatch16a_003eaf4c_003eaf80
add r0, r0, r2, lsl #3
ldr r0, [r0, #0x21c]
.Lbatch16a_003eaf4c_003eaf7c:
bx lr
.Lbatch16a_003eaf4c_003eaf80:
ldr r3, [r3, #0x220]
cmp r3, r1
bne .Lbatch16a_003eaf4c_003eaf98
add r0, r0, r2, lsl #3
ldr r0, [r0, #0x224]
bx lr
.Lbatch16a_003eaf4c_003eaf98:
add r2, r2, #2
cmp r2, #9
blt .Lbatch16a_003eaf4c_003eaf64
mov r0, #0
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x00377270, 100)
extern "C" __attribute__((naked)) void func_00377270() {
    asm volatile(
        R"batch16(
push {r4, r5, lr}
mov ip, #0
ldr r4, [r2, #0x18]
sub sp, sp, #0xc
tst r4, #1
movne ip, #1
tst r4, #2
orrne ip, ip, #2
tst r4, #4
orrne ip, ip, #4
tst r4, #8
orrne ip, ip, #8
tst r4, #0x10
ldrb r4, [r2, #0x29]
orrne ip, ip, #0x10
vldr s0, [sp, #0x18]
cmp r4, #0
orrne ip, ip, #0x20
str ip, [sp]
vstr s0, [sp, #4]
ldr ip, [r0]
ldr ip, [ip, #0x10]
blx ip
add sp, sp, #0xc
pop {r4, r5, pc}
        )batch16"
    );
}
// DECOMP_FUNC(0x0014cfd4, 108)
extern "C" __attribute__((naked)) void func_0014cfd4() {
    asm volatile(
        R"batch16(
push {r4, r5}
ldrh ip, [r0, #0x10]
add r3, r0, #0x14
mov r5, r0
mov r0, #0
cmp ip, #0
mov r2, #0x6800
mov r1, r0
ble .Lbatch16a_0014cfd4_0014d024
.Lbatch16a_0014cfd4_0014cff8:
add r4, r1, r1, lsl #1
add r4, r3, r4, lsl #2
ldrh r4, [r4]
cmp r4, r2
bne .Lbatch16a_0014cfd4_0014d02c
add r1, r1, r1, lsl #1
adds r1, r3, r1, lsl #2
ldrne r1, [r1, #4]
cmpne r1, #0
addne r0, r1, r5
beq .Lbatch16a_0014cfd4_0014d024
.Lbatch16a_0014cfd4_0014d024:
pop {r4, r5}
bx lr
.Lbatch16a_0014cfd4_0014d02c:
add r1, r1, #1
cmp ip, r1
bgt .Lbatch16a_0014cfd4_0014cff8
pop {r4, r5}
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x00158e30, 108)
extern "C" __attribute__((naked)) void func_00158e30() {
    asm volatile(
        R"batch16(
push {r4, r5}
ldrh ip, [r0, #0x10]
add r3, r0, #0x14
mov r5, r0
mov r0, #0
cmp ip, #0
mov r2, #0x5800
mov r1, r0
ble .Lbatch16a_00158e30_00158e80
.Lbatch16a_00158e30_00158e54:
add r4, r1, r1, lsl #1
add r4, r3, r4, lsl #2
ldrh r4, [r4]
cmp r4, r2
bne .Lbatch16a_00158e30_00158e88
add r1, r1, r1, lsl #1
adds r1, r3, r1, lsl #2
ldrne r1, [r1, #4]
cmpne r1, #0
addne r0, r1, r5
beq .Lbatch16a_00158e30_00158e80
.Lbatch16a_00158e30_00158e80:
pop {r4, r5}
bx lr
.Lbatch16a_00158e30_00158e88:
add r1, r1, #1
cmp ip, r1
bgt .Lbatch16a_00158e30_00158e54
pop {r4, r5}
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x0027e964, 108)
extern "C" __attribute__((naked)) void engine_func_0027e964() {
    asm volatile(
        R"batch16(
add r0, r0, #0x1fc0
str r4, [sp, #-4]!
ldr r0, [r0]
mov ip, #0
mov r2, ip
.Lbatch16a_0027e964_0027e978:
add r3, r2, r2, lsl #4
add r3, r3, r2, lsl #6
ldr r3, [r0, r3, lsl #3]
tst r3, #1
tstne r3, #0x100
beq .Lbatch16a_0027e964_0027e9b8
add ip, ip, #1
cmp ip, r1
bne .Lbatch16a_0027e964_0027e9b8
add r3, r2, r2, lsl #4
add r2, r3, r2, lsl #6
mov r1, #0x6e
add r1, r1, r2, lsl #3
ldrsh r0, [r0, r1]
pop {r4}
bx lr
.Lbatch16a_0027e964_0027e9b8:
add r2, r2, #1
cmp r2, #0x6d
blt .Lbatch16a_0027e964_0027e978
pop {r4}
mvn r0, #0
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x003e87d4, 108)
extern "C" __attribute__((naked)) void func_003e87d4() {
    asm volatile(
        R"batch16(
push {r4, r5}
ldrh ip, [r0, #0x10]
add r3, r0, #0x14
mov r5, r0
mov r0, #0
cmp ip, #0
mov r2, #0x7000
mov r1, r0
ble .Lbatch16a_003e87d4_003e8824
.Lbatch16a_003e87d4_003e87f8:
add r4, r1, r1, lsl #1
add r4, r3, r4, lsl #2
ldrh r4, [r4]
cmp r4, r2
bne .Lbatch16a_003e87d4_003e882c
add r1, r1, r1, lsl #1
adds r1, r3, r1, lsl #2
ldrne r1, [r1, #4]
cmpne r1, #0
addne r0, r1, r5
beq .Lbatch16a_003e87d4_003e8824
.Lbatch16a_003e87d4_003e8824:
pop {r4, r5}
bx lr
.Lbatch16a_003e87d4_003e882c:
add r1, r1, #1
cmp ip, r1
bgt .Lbatch16a_003e87d4_003e87f8
pop {r4, r5}
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x002b780c, 112)
extern "C" __attribute__((naked)) void script_vm_func_002b780c() {
    asm volatile(
        R"batch16(
sub r1, r1, r0
str r4, [sp, #-4]!
asr ip, r1, #2
cmp ip, #0
ble .Lbatch16a_002b780c_002b7870
lsls ip, r1, #0x1d
bpl .Lbatch16a_002b780c_002b783c
ldr ip, [r0]
ldr r4, [r3]
add r0, r0, #4
cmp ip, r4
strne ip, [r2], #4
.Lbatch16a_002b780c_002b783c:
asrs r1, r1, #3
beq .Lbatch16a_002b780c_002b7870
.Lbatch16a_002b780c_002b7844:
ldr ip, [r0]
ldr r4, [r3]
cmp ip, r4
strne ip, [r2], #4
ldr r4, [r3]
ldr ip, [r0, #4]!
add r0, r0, #4
cmp ip, r4
strne ip, [r2], #4
subs r1, r1, #1
bne .Lbatch16a_002b780c_002b7844
.Lbatch16a_002b780c_002b7870:
pop {r4}
mov r0, r2
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x00138ac4, 116)
extern "C" __attribute__((naked)) void func_00138ac4() {
    asm volatile(
        R"batch16(
mov r3, #0
str r4, [sp, #-4]!
.Lbatch16a_00138ac4_00138acc:
add ip, r0, r3, lsl #1
ldrh ip, [ip]
cmp ip, #0
beq .Lbatch16a_00138ac4_00138b14
sub r4, ip, #0xff00
sub r4, r4, #1
cmp r4, #0x5d
addls ip, ip, #0x120
uxthls ip, ip
bls .Lbatch16a_00138ac4_00138afc
cmp ip, #0x3000
moveq ip, #0x20
.Lbatch16a_00138ac4_00138afc:
add r4, r1, r3, lsl #1
add r3, r3, #1
cmp r3, r2
strh ip, [r4]
blt .Lbatch16a_00138ac4_00138acc
sub r3, r3, #1
.Lbatch16a_00138ac4_00138b14:
mov r0, #0
add r1, r1, r3, lsl #1
strh r0, [r1]
pop {r4}
bx lr
ldrh r0, [r0]
ldrh r1, [r1]
sub r0, r0, r1
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x0028412c, 116)
extern "C" __attribute__((naked)) void func_0028412c() {
    asm volatile(
        R"batch16(
cmp r0, #0
push {r4, r5}
beq .Lbatch16a_0028412c_00284144
ldr r3, [r0, #0x38]
tst r3, #0x80000000
beq .Lbatch16a_0028412c_00284150
.Lbatch16a_0028412c_00284144:
pop {r4, r5}
mov r0, #0
bx lr
.Lbatch16a_0028412c_00284150:
sub r3, r1, #1
cmp r3, #8
movgt r3, #8
cmple r3, #0
mov r5, #0
mov r1, #0
ble .Lbatch16a_0028412c_00284194
.Lbatch16a_0028412c_0028416c:
add r4, r0, r1, lsl #1
ldrb ip, [r4, #0x58]
cmp ip, #0
beq .Lbatch16a_0028412c_00284194
cmp ip, r2
ldrbeq ip, [r4, #0x59]
add r1, r1, #1
addeq r5, r5, ip
cmp r1, r3
blt .Lbatch16a_0028412c_0028416c
.Lbatch16a_0028412c_00284194:
mov r0, r5
pop {r4, r5}
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x003ead9c, 116)
extern "C" __attribute__((naked)) void func_003ead9c() {
    asm volatile(
        R"batch16(
push {r4, r5}
ldr r2, [r1, #4]
ldr r3, [r0, #4]
cmp r2, r3
bne .Lbatch16a_003ead9c_003eae04
ldr r2, [r1, #8]
ldr r3, [r0, #8]
cmp r2, r3
moveq r2, #0
bne .Lbatch16a_003ead9c_003eae04
.Lbatch16a_003ead9c_003eadc4:
add ip, r0, r2
add r3, r1, r2
ldrb r4, [ip, #0xc]
ldrb r5, [r3, #0xc]
cmp r4, r5
bne .Lbatch16a_003ead9c_003eae04
ldrb ip, [ip, #0xd]
ldrb r3, [r3, #0xd]
cmp ip, r3
bne .Lbatch16a_003ead9c_003eae04
add r2, r2, #2
cmp r2, #0x14
blo .Lbatch16a_003ead9c_003eadc4
pop {r4, r5}
mov r0, #1
bx lr
.Lbatch16a_003ead9c_003eae04:
pop {r4, r5}
mov r0, #0
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x00339488, 120)
extern "C" __attribute__((naked)) void func_00339488() {
    asm volatile(
        R"batch16(
push {r4, r5, r6, r7, r8, sb}
add r4, r0, #0x1c00
mov r1, #0
mov r2, #0x6d
mov r7, #0x60
mov r6, #0x50
add ip, r0, #0x1fc0
add r4, r4, #0x298
.Lbatch16a_00339488_003394a8:
add r0, r1, r1, lsl #2
ldr r3, [r4]
add r5, r0, r1, lsl #6
add r0, r7, r5, lsl #2
ldrsh r0, [r3, r0]
cmp r0, #0
blt .Lbatch16a_00339488_003394ec
ldr r8, [ip]
add sb, r0, r0, lsl #4
add r0, sb, r0, lsl #6
ldr r0, [r8, r0, lsl #3]
tst r0, #0x10
beq .Lbatch16a_00339488_003394ec
add r0, r6, r5, lsl #2
ldr r5, [r3, r0]
bic r5, r5, #0x4000
str r5, [r3, r0]
.Lbatch16a_00339488_003394ec:
subs r2, r2, #1
add r1, r1, #1
bne .Lbatch16a_00339488_003394a8
pop {r4, r5, r6, r7, r8, sb}
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x002a213c, 124)
extern "C" __attribute__((naked)) void func_002a213c() {
    asm volatile(
        R"batch16(
push {r4, r5, r6, r7, r8, lr}
mov r6, r0
mov r4, r1
mov r8, r2
vpush {d8}
vmov.f32 s16, s0
mov r7, r3
mov r5, #0
.Lbatch16a_002a213c_002a215c:
cmp r4, #0
beq .Lbatch16a_002a213c_002a21b0
tst r4, #1
beq .Lbatch16a_002a213c_002a21a0
cmp r5, #0xf
bgt .Lbatch16a_002a213c_002a21a0
add r0, r6, r5, lsl #2
ldr r0, [r0, #0x8c]
cmp r0, #0
beq .Lbatch16a_002a213c_002a21a0
add r0, r0, r7, asr #1
tst r7, #1
ldrne r1, [r0]
vmov.f32 s0, s16
moveq r1, r8
ldrne r1, [r1, r8]
blx r1
.Lbatch16a_002a213c_002a21a0:
add r5, r5, #1
cmp r5, #0x10
lsr r4, r4, #1
blt .Lbatch16a_002a213c_002a215c
.Lbatch16a_002a213c_002a21b0:
vpop {d8}
pop {r4, r5, r6, r7, r8, pc}
        )batch16"
    );
}
// DECOMP_FUNC(0x0033faa4, 128)
extern "C" __attribute__((naked)) void func_0033faa4() {
    asm volatile(
        R"batch16(
mov r2, #0
mov ip, #1
push {r4, r5}
.Lbatch16a_0033faa4_0033fab0:
add r4, r2, #0x800
lsr r3, r4, #3
and r4, r4, #7
ldrb r5, [r1, r3]
lsl r4, ip, r4
tst r5, r4
beq .Lbatch16a_0033faa4_0033fad8
ldrb r5, [r0, r3]
orr r4, r4, r5
strb r4, [r0, r3]
.Lbatch16a_0033faa4_0033fad8:
add r2, r2, #1
cmp r2, #0x20
blt .Lbatch16a_0033faa4_0033fab0
mov r2, #0
.Lbatch16a_0033faa4_0033fae8:
add r4, r2, #0x820
lsr r3, r4, #3
and r4, r4, #7
ldrb r5, [r1, r3]
lsl r4, ip, r4
tst r5, r4
beq .Lbatch16a_0033faa4_0033fb10
ldrb r5, [r0, r3]
orr r4, r4, r5
strb r4, [r0, r3]
.Lbatch16a_0033faa4_0033fb10:
add r2, r2, #1
cmp r2, #0x200
blt .Lbatch16a_0033faa4_0033fae8
pop {r4, r5}
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x0022c6f8, 136)
extern "C" __attribute__((naked)) void func_0022c6f8() {
    asm volatile(
        R"batch16(
push {r4, r5, r6, r7, r8, lr}
ldr r0, [r0, #4]
add r5, r0, r1, lsl #4
add r6, r0, r2, lsl #4
cmp r5, r6
movlo r7, #0
bhs .Lbatch16a_0022c6f8_0022c77c
.Lbatch16a_0022c6f8_0022c714:
mov r4, r5
add r5, r5, #0x10
ldr r0, [r4, #8]
cmp r0, #0
cmpne r0, r4
bne .Lbatch16a_0022c6f8_0022c758
ldr r0, [r4, #4]
cmp r0, #0
beq .Lbatch16a_0022c6f8_0022c770
ldr r1, [r0]
ldr r1, [r1]
blx r1
ldrd r0, r1, [r4]
ldr r2, [r0]
ldr r2, [r2, #4]
blx r2
b .Lbatch16a_0022c6f8_0022c770
.Lbatch16a_0022c6f8_0022c758:
ldr r1, [r4, #0xc]
str r1, [r0, #0xc]
ldrd r0, r1, [r4, #8]
str r0, [r1, #8]
str r7, [r4, #8]
str r7, [r4, #0xc]
.Lbatch16a_0022c6f8_0022c770:
cmp r5, r6
str r7, [r4, #4]
blo .Lbatch16a_0022c6f8_0022c714
.Lbatch16a_0022c6f8_0022c77c:
pop {r4, r5, r6, r7, r8, pc}
        )batch16"
    );
}
// DECOMP_FUNC(0x003729e8, 140)
extern "C" __attribute__((naked)) void script_vm_func_003729e8() {
    asm volatile(
        R"batch16(
push {r4, r5, r6, lr}
mov r5, r0
ldr r0, [r0, #0x258]
mov r6, r1
ldr r1, [r0]
ldr r1, [r1, #0x10]
blx r1
cmp r0, #0
beq .Lbatch16a_003729e8_00372a1c
ldr r1, [r0]
tst r1, #0x80000000
movne r4, r0
bne .Lbatch16a_003729e8_00372a20
.Lbatch16a_003729e8_00372a1c:
mov r4, #0
.Lbatch16a_003729e8_00372a20:
ldr r0, [r5, #0x258]
ldr r1, [r0]
ldr r1, [r1, #0x10]
blx r1
cmp r0, #0
beq .Lbatch16a_003729e8_00372a44
ldr r1, [r0]
tst r1, #0x40000000
moveq r0, #0
.Lbatch16a_003729e8_00372a44:
cmp r4, #0
beq .Lbatch16a_003729e8_00372a5c
ldm r6, {r0, r1, r2}
add r4, r4, #8
stm r4, {r0, r1, r2}
.Lbatch16a_003729e8_00372a58:
pop {r4, r5, r6, pc}
.Lbatch16a_003729e8_00372a5c:
cmp r0, #0
beq .Lbatch16a_003729e8_00372a58
ldm r6, {r1, r2, r3}
add r0, r0, #8
stm r0, {r1, r2, r3}
pop {r4, r5, r6, pc}
        )batch16"
    );
}
// DECOMP_FUNC(0x001107f0, 148)
extern "C" __attribute__((naked)) void script_vm_func_001107f0() {
    asm volatile(
        R"batch16(
push {r4, r5, r6, r7, r8, lr}
mov r4, r0
mov r7, #0
ldr r0, [r0]
ldr r1, [r0, #0x38]!
cmp r1, #0
addne r0, r0, r1
moveq r0, r7
ldr r5, [r0, #0x10]
ldr r0, [r4]
ldr r1, [r0, #0x38]!
cmp r1, #0
addne r6, r1, r0
moveq r6, r7
cmp r6, #0
beq .Lbatch16a_001107f0_00110868
ldr r1, [r6, #0xc]
add r0, r6, #0xc
cmp r1, #0
addsne r1, r1, r0
movne r0, r5
beq .Lbatch16a_001107f0_00110854
ldr r2, [r0]
ldr r2, [r2, #0xc]
blx r2
.Lbatch16a_001107f0_00110854:
ldr r1, [r5]
mov r0, r5
ldr r2, [r1, #0xc]
mov r1, r6
blx r2
.Lbatch16a_001107f0_00110868:
ldr r0, [r5]
ldr r1, [r4]
ldr r2, [r0, #0xc]
mov r0, r5
blx r2
str r7, [r4]
pop {r4, r5, r6, r7, r8, pc}
        )batch16"
    );
}
// DECOMP_FUNC(0x003ad828, 152)
extern "C" __attribute__((naked)) void func_003ad828() {
    asm volatile(
        R"batch16(
push {r4, r5}
ldrsh r3, [r0]
cmp r3, #0
movle r2, #0
ble .Lbatch16a_003ad828_003ad86c
and r2, r3, #1
cmp r2, #0
ldrhgt r4, [r1]
mov ip, #0
ble .Lbatch16a_003ad828_003ad86c
.Lbatch16a_003ad828_003ad850:
add r5, r0, ip, lsl #5
ldrh r5, [r5, #4]
cmp r5, r4
beq .Lbatch16a_003ad828_003ad8b8
add ip, ip, #1
cmp r2, ip
bgt .Lbatch16a_003ad828_003ad850
.Lbatch16a_003ad828_003ad86c:
cmp r2, r3
ldrhlt ip, [r1]
bge .Lbatch16a_003ad828_003ad89c
.Lbatch16a_003ad828_003ad878:
add r4, r0, r2, lsl #5
ldrh r5, [r4, #4]
cmp r5, ip
ldrhne r4, [r4, #0x24]
cmpne r4, ip
beq .Lbatch16a_003ad828_003ad8b8
add r2, r2, #2
cmp r3, r2
bgt .Lbatch16a_003ad828_003ad878
.Lbatch16a_003ad828_003ad89c:
vldmia r1, {s0, s1, s2, s3, s4, s5, s6, s7}
add r1, r0, r3, lsl #5
add r1, r1, #4
vstmia r1, {s0, s1, s2, s3, s4, s5, s6, s7}
ldrh r1, [r0]
add r1, r1, #1
strh r1, [r0]
.Lbatch16a_003ad828_003ad8b8:
pop {r4, r5}
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x00370454, 156)
extern "C" __attribute__((naked)) void func_00370454() {
    asm volatile(
        R"batch16(
push {r4, r5, r6, lr}
mov r5, r1
mov r4, r0
ldr r1, [r0, #0xc]!
mov r6, #0
cmp r1, #0
addne r0, r0, r1
moveq r0, r6
cmp r0, #0
beq .Lbatch16a_00370454_0037049c
cmp r1, #0
mov r0, r5
add r2, r4, #0xc
addne r1, r1, r2
ldr r2, [r0]
moveq r1, r6
ldr r2, [r2, #0xc]
blx r2
.Lbatch16a_00370454_0037049c:
ldr r1, [r4, #8]
add r0, r4, #8
cmp r1, #0
addne r0, r0, r1
moveq r0, r6
cmp r0, #0
beq .Lbatch16a_00370454_003704d8
cmp r1, #0
mov r0, r5
add r2, r4, #8
addne r6, r1, r2
ldr r2, [r0]
mov r1, r6
ldr r2, [r2, #0xc]
blx r2
.Lbatch16a_00370454_003704d8:
ldr r0, [r5]
mov r1, r4
ldr r2, [r0, #0xc]
mov r0, r5
pop {r4, r5, r6, lr}
bx r2
        )batch16"
    );
}
// DECOMP_FUNC(0x0023fc3c, 164)
extern "C" __attribute__((naked)) void func_0023fc3c() {
    asm volatile(
        R"batch16(
mov r2, #0
cmp r1, #0
mov r3, r2
moveq r3, #4
str r4, [sp, #-4]!
beq .Lbatch16a_0023fc3c_0023fc80
cmp r1, #1
moveq r2, #4
moveq r3, #0x32
beq .Lbatch16a_0023fc3c_0023fc80
cmp r1, #2
moveq r2, #0x36
moveq r3, #1
beq .Lbatch16a_0023fc3c_0023fc80
cmp r1, #3
moveq r2, #0x43
moveq r3, #0x2a
.Lbatch16a_0023fc3c_0023fc80:
add r3, r3, r2
cmp r3, r2
addgt r0, r0, #0x1c00
addgt r0, r0, #0x298
ldrgt ip, [r0]
ble .Lbatch16a_0023fc3c_0023fcd4
.Lbatch16a_0023fc3c_0023fc98:
add r0, r2, r2, lsl #2
add r0, r0, r2, lsl #6
add r0, ip, r0, lsl #2
ldr r1, [r0, #0x50]
tst r1, #1
tstne r1, #0x80
beq .Lbatch16a_0023fc3c_0023fcc8
tst r1, #2
bne .Lbatch16a_0023fc3c_0023fcc8
ldr r0, [r0, #0x54]
ands r0, r0, #4
beq .Lbatch16a_0023fc3c_0023fcd8
.Lbatch16a_0023fc3c_0023fcc8:
add r2, r2, #1
cmp r3, r2
bgt .Lbatch16a_0023fc3c_0023fc98
.Lbatch16a_0023fc3c_0023fcd4:
mov r0, #1
.Lbatch16a_0023fc3c_0023fcd8:
pop {r4}
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x003f8f9c, 168)
extern "C" __attribute__((naked)) void func_003f8f9c() {
    asm volatile(
        R"batch16(
mov r1, r0
add r0, r0, #8
vldr s1, [r0]
vcmpe.f32 s1, s0
vmrs apsr_nzcv, fpscr
bgt .Lbatch16a_003f8f9c_003f903c
ldrh r2, [r1]
vmov.f32 s1, s0
add r0, r1, r2, lsl #3
vldr s2, [r0]
vcmpe.f32 s2, s1
vmrs apsr_nzcv, fpscr
bls .Lbatch16a_003f8f9c_003f903c
sub r0, r2, #1
vmov s1, r0
vldr s2, [r1, #4]
vcvt.f32.s32 s3, s1
vmov.f32 s1, s0
vmul.f32 s1, s3, s1
vmul.f32 s1, s2, s1
vcvt.u32.f32 s1, s1
vmov r0, s1
add r0, r1, r0, lsl #3
add r0, r0, #8
vldr s1, [r0]
vcmpe.f32 s1, s0
vmrs apsr_nzcv, fpscr
ble .Lbatch16a_003f8f9c_003f9024
.Lbatch16a_003f8f9c_003f900c:
sub r0, r0, #8
vldr s1, [r0]
vcmpe.f32 s1, s0
vmrs apsr_nzcv, fpscr
bgt .Lbatch16a_003f8f9c_003f900c
b .Lbatch16a_003f8f9c_003f903c
.Lbatch16a_003f8f9c_003f9024:
add r0, r0, #8
vldr s1, [r0]
vcmpe.f32 s1, s0
vmrs apsr_nzcv, fpscr
bls .Lbatch16a_003f8f9c_003f9024
sub r0, r0, #8
.Lbatch16a_003f8f9c_003f903c:
vldr s0, [r0, #4]
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x003f91ac, 172)
extern "C" __attribute__((naked)) void func_003f91ac() {
    asm volatile(
        R"batch16(
mov r1, r0
add r0, r0, #8
vldr s1, [r0]
vcmpe.f32 s1, s0
vmrs apsr_nzcv, fpscr
bgt .Lbatch16a_003f91ac_003f9250
ldrh r2, [r1]
vmov.f32 s1, s0
add r0, r1, r2, lsl #4
sub r0, r0, #8
vldr s2, [r0]
vcmpe.f32 s2, s1
vmrs apsr_nzcv, fpscr
bls .Lbatch16a_003f91ac_003f9250
sub r0, r2, #1
vmov s1, r0
vldr s2, [r1, #4]
vcvt.f32.s32 s3, s1
vmov.f32 s1, s0
vmul.f32 s1, s3, s1
vmul.f32 s1, s2, s1
vcvt.u32.f32 s1, s1
vmov r0, s1
add r0, r1, r0, lsl #4
add r0, r0, #8
vldr s1, [r0]
vcmpe.f32 s1, s0
vmrs apsr_nzcv, fpscr
ble .Lbatch16a_003f91ac_003f9238
.Lbatch16a_003f91ac_003f9220:
sub r0, r0, #0x10
vldr s1, [r0]
vcmpe.f32 s1, s0
vmrs apsr_nzcv, fpscr
bgt .Lbatch16a_003f91ac_003f9220
b .Lbatch16a_003f91ac_003f9250
.Lbatch16a_003f91ac_003f9238:
add r0, r0, #0x10
vldr s1, [r0]
vcmpe.f32 s1, s0
vmrs apsr_nzcv, fpscr
bls .Lbatch16a_003f91ac_003f9238
sub r0, r0, #0x10
.Lbatch16a_003f91ac_003f9250:
vldr s0, [r0, #4]
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x00372938, 176)
extern "C" __attribute__((naked)) void func_00372938() {
    asm volatile(
        R"batch16(
push {r4, r5, r6, lr}
movs r4, r1
mov r5, r0
beq .Lbatch16a_00372938_003729e4
add r0, r1, #0xc0
ldr r1, [r1, #0xc0]
mov r6, #0
cmp r1, #0
addne r0, r0, r1
moveq r0, r6
cmp r0, #0
beq .Lbatch16a_00372938_0037298c
cmp r1, #0
mov r0, r5
add r2, r4, #0xc0
addne r1, r1, r2
ldr r2, [r0]
moveq r1, r6
ldr r2, [r2, #0xc]
blx r2
str r6, [r4, #0xc0]
.Lbatch16a_00372938_0037298c:
ldr r1, [r4, #0xbc]
add r0, r4, #0xbc
cmp r1, #0
addne r0, r0, r1
moveq r0, r6
cmp r0, #0
beq .Lbatch16a_00372938_003729cc
cmp r1, #0
mov r0, r5
add r2, r4, #0xbc
addne r1, r1, r2
ldr r2, [r0]
moveq r1, r6
ldr r2, [r2, #0xc]
blx r2
str r6, [r4, #0xbc]
.Lbatch16a_00372938_003729cc:
ldr r0, [r5]
mov r1, r4
ldr r2, [r0, #0xc]
mov r0, r5
pop {r4, r5, r6, lr}
bx r2
.Lbatch16a_00372938_003729e4:
pop {r4, r5, r6, pc}
        )batch16"
    );
}
// DECOMP_FUNC(0x002abe74, 180)
extern "C" __attribute__((naked)) void engine_func_002abe74() {
    asm volatile(
        R"batch16(
add r3, r0, #8
str r4, [sp, #-4]!
ldm r3, {r3, ip}
mov r2, ip
.Lbatch16a_002abe74_002abe84:
cmp r3, r2
ldrne r4, [r3]
cmpne r4, r1
addne r3, r3, #4
bne .Lbatch16a_002abe74_002abe84
cmp r3, ip
mov r2, r3
beq .Lbatch16a_002abe74_002abefc
add r3, r2, #4
sub ip, ip, r3
asr r4, ip, #2
cmp r4, #0
ble .Lbatch16a_002abe74_002abefc
lsls r4, ip, #0x1d
bpl .Lbatch16a_002abe74_002abed0
ldr r4, [r3]
add r3, r3, #4
cmp r4, r1
strne r4, [r2], #4
.Lbatch16a_002abe74_002abed0:
asrs ip, ip, #3
beq .Lbatch16a_002abe74_002abefc
.Lbatch16a_002abe74_002abed8:
ldr r4, [r3]
cmp r4, r1
strne r4, [r2], #4
ldr r4, [r3, #4]!
add r3, r3, #4
cmp r4, r1
strne r4, [r2], #4
subs ip, ip, #1
bne .Lbatch16a_002abe74_002abed8
.Lbatch16a_002abe74_002abefc:
ldr r3, [r0, #0xc]
str r2, [r0, #0xc]
cmp r3, r2
movne r3, #1
moveq r3, #0
cmp r3, #0
movne r0, #0
strne r0, [r1, #0xc]
pop {r4}
mov r0, r3
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x003e8688, 180)
extern "C" __attribute__((naked)) void func_003e8688() {
    asm volatile(
        R"batch16(
ldr r3, [r0, #4]
ldrh ip, [r0]
mov r2, r0
add r2, r2, r3
cmp ip, #0x6000
mov r0, #0
ldreq r0, [r2, #4]
addeq r0, r0, r2
beq .Lbatch16a_003e8688_003e8724
sub r3, ip, #0x6000
subs r3, r3, #1
beq .Lbatch16a_003e8688_003e86d8
cmp r3, #1
bne .Lbatch16a_003e8688_003e8724
ldrb r0, [r2]
cmp r0, r1
ldrbls r3, [r2, #1]
cmpls r1, r3
bhi .Lbatch16a_003e8688_003e8720
b .Lbatch16a_003e8688_003e8728
.Lbatch16a_003e8688_003e86d8:
ldr ip, [r2]
mov r0, #0
cmp ip, #0
bls .Lbatch16a_003e8688_003e8720
.Lbatch16a_003e8688_003e86e8:
add r3, r2, r0
ldrb r3, [r3, #4]
cmp r3, r1
blo .Lbatch16a_003e8688_003e8714
add r1, ip, #3
bic r1, r1, #3
add r0, r1, r0, lsl #3
add r0, r0, #4
add r0, r0, r2
ldr r0, [r0, #4]
b .Lbatch16a_003e8688_003e8734
.Lbatch16a_003e8688_003e8714:
add r0, r0, #1
cmp r0, ip
blo .Lbatch16a_003e8688_003e86e8
.Lbatch16a_003e8688_003e8720:
mov r0, #0
.Lbatch16a_003e8688_003e8724:
bx lr
.Lbatch16a_003e8688_003e8728:
sub r0, r1, r0
add r0, r2, r0, lsl #3
ldr r0, [r0, #8]
.Lbatch16a_003e8688_003e8734:
add r0, r0, r2
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x001ee114, 188)
extern "C" __attribute__((naked)) void func_001ee114() {
    asm volatile(
        R"batch16(
add r3, r0, #0x200
mov r2, #1
ldrsb ip, [r3, #0xe4]
cmp ip, #3
movge ip, #4
strbge ip, [r0, #0x2e4]
ldrsb r3, [r3, #0xe4]
add ip, r3, #1
cmp ip, #4
bxge lr
push {r4, r5, r6}
add r5, r3, r3, lsl #4
add r4, r1, r5, lsl #2
.Lbatch16a_001ee114_001ee148:
add ip, r3, r2
ldr r6, [r4, #0x20]
add ip, ip, ip, lsl #4
add ip, r1, ip, lsl #2
ldr ip, [ip, #0x20]
sub ip, ip, r6
cmp ip, #0
str ip, [r0, #0x320]
ble .Lbatch16a_001ee114_001ee1b8
add r1, r3, r2
add r3, r0, r5, lsl #2
add r2, r1, r1, lsl #4
vldr s1, [r3, #0x40]
add r2, r0, r2, lsl #2
ldr ip, [r3, #0x20]
ldr r3, [r2, #0x20]
vldr s0, [r2, #0x40]
sub r3, r3, ip
vsub.f32 s2, s0, s1
vmov s0, r3
vcvt.f32.s32 s1, s0
vdiv.f32 s0, s2, s1
vstr s0, [r0, #0x224]
ldr r2, [r2, #0x40]
str r2, [r0, #0x250]
strb r1, [r0, #0x2e4]
pop {r4, r5, r6}
bx lr
.Lbatch16a_001ee114_001ee1b8:
add r2, r2, #1
add ip, r3, r2
cmp ip, #4
blt .Lbatch16a_001ee114_001ee148
pop {r4, r5, r6}
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x0012d8d4, 200)
extern "C" __attribute__((naked)) void engine_func_0012d8d4() {
    asm volatile(
        R"batch16(
push {r4, r5, r6, lr}
mov r4, r0
mov r5, r1
add r0, r1, #0xc
ldr r1, [r1, #0xc]
mov r6, #0
cmp r1, #0
addsne r1, r1, r0
movne r0, r4
beq .Lbatch16a_0012d8d4_0012d908
ldr r2, [r0]
ldr r2, [r2, #0xc]
blx r2
.Lbatch16a_0012d8d4_0012d908:
ldr r1, [r5, #0xc8]
add r0, r5, #0xc8
cmp r1, #0
addsne r1, r1, r0
movne r0, r4
beq .Lbatch16a_0012d8d4_0012d92c
ldr r2, [r0]
ldr r2, [r2, #0xc]
blx r2
.Lbatch16a_0012d8d4_0012d92c:
ldr r1, [r5, #0xc4]
add r0, r5, #0xc4
cmp r1, #0
addsne r0, r0, r1
beq .Lbatch16a_0012d8d4_0012d984
ldr r1, [r0, #0x10]!
cmp r1, #0
addsne r1, r1, r0
movne r0, r4
beq .Lbatch16a_0012d8d4_0012d960
ldr r2, [r0]
ldr r2, [r2, #0xc]
blx r2
.Lbatch16a_0012d8d4_0012d960:
ldr r2, [r5, #0xc4]
mov r0, r4
add r1, r5, #0xc4
cmp r2, #0
addne r6, r2, r1
ldr r2, [r0]
mov r1, r6
ldr r2, [r2, #0xc]
blx r2
.Lbatch16a_0012d8d4_0012d984:
ldr r0, [r4]
mov r1, r5
ldr r2, [r0, #0xc]
mov r0, r4
pop {r4, r5, r6, lr}
bx r2
        )batch16"
    );
}
// DECOMP_FUNC(0x003cfab0, 200)
extern "C" __attribute__((naked)) void func_003cfab0() {
    asm volatile(
        R"batch16(
push {r4, r5, r6, r7}
mov r3, #0
mov ip, #0x6d
mov r7, #0x50
.Lbatch16a_003cfab0_003cfac0:
ldr r4, [r0]
mov r5, r3
subs ip, ip, #1
add r4, r4, #0x1c00
add r6, r3, r5, lsl #2
add r4, r4, #0x298
add r5, r6, r5, lsl #6
ldr r6, [r4]
add r4, r7, r5, lsl #2
add r3, r3, #1
ldr r5, [r6, r4]
bic r5, r5, #4
str r5, [r6, r4]
bic r6, r5, #8
ldr r5, [r0]
add r5, r5, #0x1c00
add r5, r5, #0x298
ldr r5, [r5]
str r6, [r5, r4]
bne .Lbatch16a_003cfab0_003cfac0
ldr r0, [r0]
mov r3, #0
add r0, r0, #0x1fc0
ldr ip, [r0]
.Lbatch16a_003cfab0_003cfb20:
add r0, r3, r3, lsl #4
add r0, r0, r3, lsl #6
add r0, ip, r0, lsl #3
ldr r4, [r0]
tst r4, #1
beq .Lbatch16a_003cfab0_003cfb60
tst r4, #0x40
bne .Lbatch16a_003cfab0_003cfb60
ldrsh r0, [r0, #0x6e]
cmp r0, r2
bne .Lbatch16a_003cfab0_003cfb60
add r1, r1, r2
mov r0, #1
strb r0, [r1, #0x38]
pop {r4, r5, r6, r7}
bx lr
.Lbatch16a_003cfab0_003cfb60:
add r3, r3, #1
cmp r3, #0x6d
blt .Lbatch16a_003cfab0_003cfb20
pop {r4, r5, r6, r7}
mov r0, #0
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x001316ec, 208)
extern "C" __attribute__((naked)) void script_vm_func_001316ec() {
    asm volatile(
        R"batch16(
push {r4, r5, r6}
mov r4, #0x20
ldr ip, [r0, #0x3c0]
cmp ip, #0
movle r2, #0
ble .Lbatch16a_001316ec_00131748
and r2, ip, #1
cmp r2, #0
ldrgt r5, [r0, #0x3c4]
mov r3, #0
ble .Lbatch16a_001316ec_00131748
.Lbatch16a_001316ec_00131718:
rsb r6, r3, r3, lsl #4
add r6, r4, r6, lsl #2
ldrh r6, [r5, r6]
cmp r6, r1
bne .Lbatch16a_001316ec_0013173c
rsb r0, r3, r3, lsl #4
add r0, r5, r0, lsl #2
pop {r4, r5, r6}
bx lr
.Lbatch16a_001316ec_0013173c:
add r3, r3, #1
cmp r2, r3
bgt .Lbatch16a_001316ec_00131718
.Lbatch16a_001316ec_00131748:
cmp r2, ip
ldrlt r0, [r0, #0x3c4]
movlt r5, #0x5c
bge .Lbatch16a_001316ec_001317b0
.Lbatch16a_001316ec_00131758:
rsb r3, r2, r2, lsl #4
add r6, r4, r3, lsl #2
ldrh r6, [r0, r6]
cmp r6, r1
bne .Lbatch16a_001316ec_0013177c
rsb r1, r2, r2, lsl #4
pop {r4, r5, r6}
add r0, r0, r1, lsl #2
bx lr
.Lbatch16a_001316ec_0013177c:
add r3, r5, r3, lsl #2
ldrh r3, [r0, r3]
cmp r3, r1
bne .Lbatch16a_001316ec_001317a4
rsb r1, r2, r2, lsl #4
mov r2, #0x3c
add r1, r2, r1, lsl #2
pop {r4, r5, r6}
add r0, r0, r1
bx lr
.Lbatch16a_001316ec_001317a4:
add r2, r2, #2
cmp ip, r2
bgt .Lbatch16a_001316ec_00131758
.Lbatch16a_001316ec_001317b0:
pop {r4, r5, r6}
mov r0, #0
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x002915e4, 212)
extern "C" __attribute__((naked)) void func_002915e4() {
    asm volatile(
        R"batch16(
push {r4, r5, r6, r7}
mov ip, #1
ldr r4, [r1]
ldr r5, [sp, #0x10]
cmp r4, #3
addlt r4, r4, #1
cmplt r4, #4
bge .Lbatch16a_002915e4_00291694
.Lbatch16a_002915e4_00291604:
ldr r4, [r1]
add r6, r4, ip
add r7, r4, r4, lsl #1
add r4, r6, r6, lsl #1
add r6, r0, r7, lsl #3
add r4, r0, r4, lsl #3
ldr r6, [r6, #0x48]
ldr r4, [r4, #0x48]
sub r4, r4, r6
cmp r4, #0
str r4, [r2]
ble .Lbatch16a_002915e4_0029169c
ldr r2, [r1]
add r6, r2, ip
add r4, r2, r2, lsl #1
add r2, r6, r6, lsl #1
add r4, r0, r4, lsl #3
add r6, r0, r2, lsl #3
ldr r2, [r4, #0x48]
vldr s0, [r4, #0x44]
ldr r4, [r6, #0x48]
vcvt.f32.s32 s0, s0
sub r2, r4, r2
vmov s1, r2
vcvt.f32.s32 s1, s1
vdiv.f32 s2, s0, s1
vstr s2, [r3]
ldr r2, [r1]
add r2, r2, r2, lsl #1
add r0, r0, r2, lsl #3
vldr s0, [r0, #0x44]
vcvt.f32.s32 s0, s0
vstr s0, [r5]
ldr r0, [r1]
add r0, r0, ip
str r0, [r1]
.Lbatch16a_002915e4_00291694:
pop {r4, r5, r6, r7}
bx lr
.Lbatch16a_002915e4_0029169c:
ldr r4, [r1]
add ip, ip, #1
add r4, r4, ip
cmp r4, #4
blt .Lbatch16a_002915e4_00291604
pop {r4, r5, r6, r7}
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x002af528, 220)
extern "C" __attribute__((naked)) void engine_func_002af528() {
    asm volatile(
        R"batch16(
push {r4, r5, r6, r7, r8, lr}
mov r5, r1
mov r4, r0
ldr r1, [r0, #0xc]
bic r0, r1, #0xc0000000
cmp r0, r5
movge r0, #1
bge .Lbatch16a_002af528_002af564
ldr r0, [r4]
cmp r0, #0
beq .Lbatch16a_002af528_002af560
and r1, r1, #0xc0000000
cmp r1, #0x40000000
beq .Lbatch16a_002af528_002af568
.Lbatch16a_002af528_002af560:
mov r0, #0
.Lbatch16a_002af528_002af564:
pop {r4, r5, r6, r7, r8, pc}
.Lbatch16a_002af528_002af568:
ldr r1, [r0]
mov r2, #0x20
ldr r3, [r1, #8]
lsl r1, r5, #2
blx r3
add r2, r4, #4
mov r6, r0
ldm r2, {r0, r2}
mov r7, #0
cmp r0, r2
movne r1, r6
beq .Lbatch16a_002af528_002af5c4
.Lbatch16a_002af528_002af598:
cmp r1, #0
ldrne ip, [r0]
add r0, r0, #4
strne ip, [r1]
cmp r0, r2
add r1, r1, #4
bne .Lbatch16a_002af528_002af598
ldr r0, [r4, #8]
ldr r1, [r4, #4]
sub r0, r0, r1
asr r7, r0, #2
.Lbatch16a_002af528_002af5c4:
ldr r1, [r4, #4]
cmp r1, #0
beq .Lbatch16a_002af528_002af5e0
ldr r0, [r4]
ldr r2, [r0]
ldr r2, [r2, #0xc]
blx r2
.Lbatch16a_002af528_002af5e0:
add r0, r6, r7, lsl #2
str r0, [r4, #8]
str r6, [r4, #4]
ldr r0, [r4, #0xc]
and r0, r0, #0xc0000000
orr r0, r0, r5
str r0, [r4, #0xc]
mov r0, #1
pop {r4, r5, r6, r7, r8, pc}
        )batch16"
    );
}
// DECOMP_FUNC(0x00140eb8, 228)
extern "C" __attribute__((naked)) void engine_func_00140eb8() {
    asm volatile(
        R"batch16(
push {r4, r5, r6}
mov r4, #0x50
ldr ip, [r0, #0x3b4]
cmp ip, #0
movle r2, #0
ble .Lbatch16a_00140eb8_00140f1c
and r2, ip, #1
cmp r2, #0
ldrgt r5, [r0, #0x3b8]
mov r3, #0
ble .Lbatch16a_00140eb8_00140f1c
.Lbatch16a_00140eb8_00140ee4:
rsb r6, r3, r3, lsl #3
add r6, r6, r6, lsl #1
add r6, r4, r6, lsl #3
ldrh r6, [r5, r6]
cmp r6, r1
bne .Lbatch16a_00140eb8_00140f10
rsb r0, r3, r3, lsl #3
add r0, r0, r0, lsl #1
add r0, r5, r0, lsl #3
pop {r4, r5, r6}
bx lr
.Lbatch16a_00140eb8_00140f10:
add r3, r3, #1
cmp r2, r3
bgt .Lbatch16a_00140eb8_00140ee4
.Lbatch16a_00140eb8_00140f1c:
cmp r2, ip
ldrlt r0, [r0, #0x3b8]
movlt r6, #0xf8
bge .Lbatch16a_00140eb8_00140f90
.Lbatch16a_00140eb8_00140f2c:
rsb r3, r2, r2, lsl #3
add r3, r3, r3, lsl #1
add r5, r4, r3, lsl #3
ldrh r5, [r0, r5]
cmp r5, r1
bne .Lbatch16a_00140eb8_00140f58
rsb r1, r2, r2, lsl #3
pop {r4, r5, r6}
add r1, r1, r1, lsl #1
add r0, r0, r1, lsl #3
bx lr
.Lbatch16a_00140eb8_00140f58:
add r3, r6, r3, lsl #3
ldrh r3, [r0, r3]
cmp r3, r1
bne .Lbatch16a_00140eb8_00140f84
rsb r2, r2, r2, lsl #3
mov r1, #0xa8
add r2, r2, r2, lsl #1
pop {r4, r5, r6}
add r1, r1, r2, lsl #3
add r0, r0, r1
bx lr
.Lbatch16a_00140eb8_00140f84:
add r2, r2, #2
cmp ip, r2
bgt .Lbatch16a_00140eb8_00140f2c
.Lbatch16a_00140eb8_00140f90:
pop {r4, r5, r6}
mov r0, #0
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x0023b17c, 228)
extern "C" __attribute__((naked)) void engine_func_0023b17c() {
    asm volatile(
        R"batch16(
mov ip, r0
add r0, r1, r1, lsl #1
mov r3, #4
push {r4, r5}
mov r4, #6
add r1, r3, r0, lsl #2
cmp r2, #4
add r3, r4, r0, lsl #2
beq .Lbatch16a_0023b17c_0023b1b4
cmp r2, #5
beq .Lbatch16a_0023b17c_0023b20c
cmp r2, #6
movne r0, #0
bne .Lbatch16a_0023b17c_0023b228
.Lbatch16a_0023b17c_0023b1b4:
ldr r4, [ip, #0x30]
mov r5, #8
add r0, r5, r0, lsl #2
cmp r2, #5
ldrh r1, [r4, r1]
ldrh r3, [r4, r3]
ldrh r0, [r4, r0]
add r1, r1, r3
sub r3, r1, #1
add r3, r3, r0
beq .Lbatch16a_0023b17c_0023b220
cmp r1, r3
ldrle r4, [ip, #0x2c]
mov r0, #0
bgt .Lbatch16a_0023b17c_0023b228
.Lbatch16a_0023b17c_0023b1f0:
add ip, r1, r1, lsl #1
add ip, ip, r1, lsl #3
add ip, r4, ip, lsl #3
ldr ip, [ip, #0x50]
cmp ip, #0x3f800000
bne .Lbatch16a_0023b17c_0023b238
b .Lbatch16a_0023b17c_0023b230
.Lbatch16a_0023b17c_0023b20c:
ldr r0, [ip, #0x30]
ldrh r1, [r0, r1]
ldrh r0, [r0, r3]
sub r2, r1, #1
add r3, r0, r2
.Lbatch16a_0023b17c_0023b220:
sub r0, r3, r1
add r0, r0, #1
.Lbatch16a_0023b17c_0023b228:
pop {r4, r5}
bx lr
.Lbatch16a_0023b17c_0023b230:
cmp r2, #4
bne .Lbatch16a_0023b17c_0023b24c
.Lbatch16a_0023b17c_0023b238:
cmp ip, #0x3f800000
bge .Lbatch16a_0023b17c_0023b248
cmp r2, #6
bne .Lbatch16a_0023b17c_0023b24c
.Lbatch16a_0023b17c_0023b248:
add r0, r0, #1
.Lbatch16a_0023b17c_0023b24c:
add r1, r1, #1
cmp r1, r3
ble .Lbatch16a_0023b17c_0023b1f0
pop {r4, r5}
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x002a247c, 244)
extern "C" __attribute__((naked)) void func_002a247c() {
    asm volatile(
        R"batch16(
ldr r1, [r0]
mov ip, #0
ldr r1, [r1, #0x18]
cmp r1, #0
bxle lr
push {r4, r5}
mov r4, #0
.Lbatch16a_002a247c_002a2498:
ldr r1, [r0]
ldr r2, [r1, #0x1c]!
cmp r2, #0
addne r1, r1, r2
moveq r1, r4
cmp r1, #0
beq .Lbatch16a_002a247c_002a24c8
add r1, r1, ip, lsl #4
ldr r2, [r1, #0x28]!
cmp r2, #0
moveq r1, r4
addne r1, r1, r2
.Lbatch16a_002a247c_002a24c8:
ldr r2, [r1, #8]
cmp r2, #7
bne .Lbatch16a_002a247c_002a251c
ldr r2, [r1, #0x10]
mov r3, #0
cmp r2, #0
ble .Lbatch16a_002a247c_002a251c
.Lbatch16a_002a247c_002a24e4:
ldr r5, [r1, #0x14]
add r2, r1, #0x14
cmp r5, #0
addne r2, r2, r5
moveq r2, r4
ldr r5, [r2, r3, lsl #2]!
add r3, r3, #1
cmp r5, #0
addne r2, r2, r5
moveq r2, r4
str r4, [r2, #0x1c]
ldr r2, [r1, #0x10]
cmp r2, r3
bgt .Lbatch16a_002a247c_002a24e4
.Lbatch16a_002a247c_002a251c:
ldr r1, [r0]
add ip, ip, #1
ldr r1, [r1, #0x18]
cmp r1, ip
bgt .Lbatch16a_002a247c_002a2498
pop {r4, r5}
bx lr
push {r4, r5, sb, sl, fp}
ldm r1!, {r2}
ldm r1!, {r3}
stm r0!, {r2}
stm r0!, {r3}
pop {r4, r5, sb, sl, fp}
bx lr
push {r4, r5, sb, sl, fp}
ldm r1!, {r2, r3}
ldm r1!, {fp, ip}
stm r0!, {r2, r3}
stm r0!, {fp, ip}
pop {r4, r5, sb, sl, fp}
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x0014e648, 252)
extern "C" __attribute__((naked)) void engine_func_0014e648() {
    asm volatile(
        R"batch16(
cmp r0, #0
str r4, [sp, #-4]!
beq .Lbatch16a_0014e648_0014e73c
cmp r1, #0
moveq r0, #0
beq .Lbatch16a_0014e648_0014e73c
ldr r3, [r0, #8]
cmp r3, #0
strle r1, [r0]
ble .Lbatch16a_0014e648_0014e6b0
cmp r3, r2
ble .Lbatch16a_0014e648_0014e6a4
cmn r2, #1
beq .Lbatch16a_0014e648_0014e6a4
cmp r2, #0
rsbne ip, r3, #0
cmpne r2, ip
bgt .Lbatch16a_0014e648_0014e6b8
ldr r2, [r0]
str r1, [r2, #0x14]
str r2, [r1, #0x18]
str r1, [r0]
b .Lbatch16a_0014e648_0014e710
.Lbatch16a_0014e648_0014e6a4:
ldr r2, [r0, #4]
str r1, [r2, #0x18]
str r2, [r1, #0x14]
.Lbatch16a_0014e648_0014e6b0:
str r1, [r0, #4]
b .Lbatch16a_0014e648_0014e710
.Lbatch16a_0014e648_0014e6b8:
cmp r2, #0
addlt r2, r2, #1
addlt r2, r2, r3
ldr r3, [r0]
mov r4, #0
cmp r3, #0
beq .Lbatch16a_0014e648_0014e6ec
.Lbatch16a_0014e648_0014e6d4:
ldr ip, [r3]
cmp ip, r2
beq .Lbatch16a_0014e648_0014e6f0
ldr r3, [r3, #0x18]
cmp r3, #0
bne .Lbatch16a_0014e648_0014e6d4
.Lbatch16a_0014e648_0014e6ec:
mov r3, r4
.Lbatch16a_0014e648_0014e6f0:
ldr r2, [r3, #0x14]
cmp r2, #0
strne r2, [r1, #0x14]
strne r1, [r2, #0x18]
streq r4, [r1, #0x14]
streq r1, [r0]
str r3, [r1, #0x18]
str r1, [r3, #0x14]
.Lbatch16a_0014e648_0014e710:
ldr r1, [r0]
mov r2, #0
cmp r1, #0
beq .Lbatch16a_0014e648_0014e734
.Lbatch16a_0014e648_0014e720:
str r2, [r1]
ldr r1, [r1, #0x18]
add r2, r2, #1
cmp r1, #0
bne .Lbatch16a_0014e648_0014e720
.Lbatch16a_0014e648_0014e734:
str r2, [r0, #8]
mov r0, #1
.Lbatch16a_0014e648_0014e73c:
pop {r4}
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x00357190, 268)
extern "C" __attribute__((naked)) void engine_func_00357190() {
    asm volatile(
        R"batch16(
push {r4, r5, r6}
add r6, r0, r1
ldrb r2, [r6, #0x154]
cmp r2, #0
beq .Lbatch16a_00357190_00357274
add r2, r1, r1, lsl #2
mov r5, #0
add r2, r0, r2, lsl #2
str r5, [r0]
ldrb r3, [r2, #0x6a0]
cmp r3, #0
strbne r5, [r2, #0x6a0]
moveq ip, #0
strbne r5, [r6, #0x154]
bne .Lbatch16a_00357190_00357274
.Lbatch16a_00357190_003571cc:
rsb r2, ip, ip, lsl #3
add r2, r0, r2, lsl #4
ldr r3, [r2, #0x160]
cmp r3, #0
movne r3, #0
beq .Lbatch16a_00357190_00357288
.Lbatch16a_00357190_003571e4:
add r4, r2, r3, lsl #2
ldr r4, [r4, #0x1a0]
cmp r4, r1
bne .Lbatch16a_00357190_0035727c
rsb r1, ip, ip, lsl #3
add r1, r0, r1, lsl #4
add r1, r1, r3, lsl #2
mvn r0, #0
str r0, [r1, #0x1a0]
strb r5, [r6, #0x154]
ldr r0, [r2, #0x160]!
cmp r0, #0
movne r0, #0
beq .Lbatch16a_00357190_00357274
.Lbatch16a_00357190_0035721c:
add r1, r2, r0, lsl #2
ldr r3, [r1, #0x40]
cmn r3, #1
ldreq r1, [r1, #0x44]
cmneq r1, #1
bne .Lbatch16a_00357190_00357274
add r0, r0, #2
cmp r0, #0xc
blo .Lbatch16a_00357190_0035721c
str r5, [r2]
str r5, [r2, #0x10]
str r5, [r2, #0x14]
str r5, [r2, #0x18]
str r5, [r2, #0x1c]
str r5, [r2, #0x20]
str r5, [r2, #0x24]
str r5, [r2, #0x28]
str r5, [r2, #0x2c]
str r5, [r2, #0x30]
str r5, [r2, #0x34]
str r5, [r2, #0x38]
str r5, [r2, #0x3c]
.Lbatch16a_00357190_00357274:
pop {r4, r5, r6}
bx lr
.Lbatch16a_00357190_0035727c:
add r3, r3, #1
cmp r3, #0xc
blo .Lbatch16a_00357190_003571e4
.Lbatch16a_00357190_00357288:
add ip, ip, #1
cmp ip, #0xc
blo .Lbatch16a_00357190_003571cc
pop {r4, r5, r6}
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x0034c7e0, 284)
extern "C" __attribute__((naked)) void func_0034c7e0() {
    asm volatile(
        R"batch16(
push {r4, lr}
mov r4, r0
ldr r0, [r0, #0x14]
ldr r1, [r0]
ldr r1, [r1, #0xc]
blx r1
ldr r0, [r4, #0x1c]
ldr r1, [r4, #4]
ldr r0, [r0]
str r0, [r1, #0xc]
ldr r0, [r4, #0x1c]
ldr r1, [r4, #4]
ldr r0, [r0, #4]
str r0, [r1, #0x10]
ldr r0, [r4, #0x1c]
ldr r1, [r4, #4]
ldr r0, [r0]
str r0, [r1, #0x20]
ldr r0, [r4, #0x1c]
ldr r1, [r4, #4]
ldr r0, [r0, #0xc]
str r0, [r1, #0x24]
ldr r0, [r4, #0x1c]
ldr r1, [r4, #4]
ldr r0, [r0, #8]
str r0, [r1, #0x34]
ldr r0, [r4, #0x1c]
ldr r1, [r4, #4]
ldr r0, [r0, #4]
str r0, [r1, #0x38]
ldr r0, [r4, #0x1c]
ldr r1, [r4, #4]
ldr r0, [r0, #8]
str r0, [r1, #0x48]
ldr r0, [r4, #0x1c]
ldr r1, [r4, #4]
ldr r0, [r0, #0xc]
str r0, [r1, #0x4c]
ldr r0, [r4, #0x1c]
ldr r1, [r4, #4]
ldr r0, [r0, #0x28]
str r0, [r1, #0x5c]
ldr r0, [r4, #0x1c]
ldr r1, [r4, #4]
ldr r0, [r0, #0x2c]
str r0, [r1, #0x60]
ldr r0, [r4, #0x1c]
ldr r1, [r4, #4]
ldr r0, [r0, #0x28]
str r0, [r1, #0x70]
ldr r0, [r4, #0x1c]
ldr r1, [r4, #4]
ldr r0, [r0, #0x34]
str r0, [r1, #0x74]
ldr r0, [r4, #0x1c]
ldr r1, [r4, #4]
ldr r0, [r0, #0x30]
str r0, [r1, #0x84]
ldr r0, [r4, #0x1c]
ldr r1, [r4, #4]
ldr r0, [r0, #0x2c]
str r0, [r1, #0x88]
ldr r0, [r4, #0x1c]
ldr r1, [r4, #4]
ldr r0, [r0, #0x30]
str r0, [r1, #0x98]
ldr r1, [r4, #4]!
ldr r0, [r4, #0x18]
ldr r0, [r0, #0x34]
str r0, [r1, #0x9c]
pop {r4, pc}
        )batch16"
    );
}
// DECOMP_FUNC(0x0033a378, 288)
extern "C" __attribute__((naked)) void func_0033a378() {
    asm volatile(
        R"batch16(
push {r4, r5, r6, r7, r8, sb, sl, fp, lr}
add lr, r0, #0x1c00
add lr, lr, #0x3bc
ldr r1, [lr]
cmp r1, #0
beq .Lbatch16a_0033a378_0033a494
add sl, r0, #0x1c00
mov r7, #4
mov ip, #8
add sl, sl, #0x298
.Lbatch16a_0033a378_0033a3a0:
add r2, r7, r7, lsl #2
ldr r1, [sl]
add r2, r2, r7, lsl #6
add r8, r1, r2, lsl #2
ldr r1, [r8, #0x50]
tst r1, #1
tstne r1, #0x80
beq .Lbatch16a_0033a378_0033a488
mov r1, #0x1fc0
ldrsh r3, [r8, #0x62]
ldr r6, [r1, r0]
mov sb, #0
mov r2, sb
.Lbatch16a_0033a378_0033a3d4:
mov r1, #0
add r4, r2, r2, lsl #4
add r4, r4, r2, lsl #6
add r5, r6, r4, lsl #3
.Lbatch16a_0033a378_0033a3e4:
add r4, ip, r1, lsl #1
ldrsh r4, [r5, r4]
cmp r4, #0
blt .Lbatch16a_0033a378_0033a418
cmp r4, r3
bne .Lbatch16a_0033a378_0033a40c
add r1, r2, r2, lsl #4
add r1, r1, r2, lsl #6
add sb, r6, r1, lsl #3
b .Lbatch16a_0033a378_0033a424
.Lbatch16a_0033a378_0033a40c:
add r1, r1, #1
cmp r1, #0x32
blt .Lbatch16a_0033a378_0033a3e4
.Lbatch16a_0033a378_0033a418:
add r2, r2, #1
cmp r2, #0x6d
blt .Lbatch16a_0033a378_0033a3d4
.Lbatch16a_0033a378_0033a424:
ldr r5, [lr]
ldrsh r6, [sb, #0x6e]
add r4, sb, #0xcc
mov r2, #0
.Lbatch16a_0033a378_0033a434:
add r1, r2, r2, lsl #1
add r1, r5, r1, lsl #3
ldrsh sb, [r1]
cmp sb, r6
ldrsheq sb, [r1, #2]
cmpeq sb, r3
bne .Lbatch16a_0033a378_0033a47c
ldrh sb, [r1, #4]
ldrh fp, [r4, #2]
cmp sb, fp
bne .Lbatch16a_0033a378_0033a47c
ldr sb, [r1, #8]
ldr fp, [r4, #0xc]
cmp sb, fp
bne .Lbatch16a_0033a378_0033a47c
ldr r2, [r8, #0xc]
str r2, [r1, #0xc]
b .Lbatch16a_0033a378_0033a488
.Lbatch16a_0033a378_0033a47c:
add r2, r2, #1
cmp r2, #0x32
blt .Lbatch16a_0033a378_0033a434
.Lbatch16a_0033a378_0033a488:
add r7, r7, #1
cmp r7, #0x36
blt .Lbatch16a_0033a378_0033a3a0
.Lbatch16a_0033a378_0033a494:
pop {r4, r5, r6, r7, r8, sb, sl, fp, pc}
        )batch16"
    );
}
// DECOMP_FUNC(0x00236710, 292)
extern "C" __attribute__((naked)) void func_00236710() {
    asm volatile(
        R"batch16(
push {r4, r5, r6, r7, r8, sb, sl, lr}
mov r4, r0
mov r8, r1
add r1, r4, #8
ldr r3, [r0, #4]
ldm r1, {r1, r2}
mov r0, #1
sub r3, r1, r3
bic r1, r2, #0xc0000000
cmp r1, r3, asr #2
bgt .Lbatch16a_00236710_00236814
cmp r1, #0
lslne r5, r1, #1
moveq r5, #1
bic r1, r2, #0xc0000000
cmp r1, r5
mov sb, #1
bge .Lbatch16a_00236710_00236814
ldr r0, [r4]
mov r1, #0
cmp r0, #0
beq .Lbatch16a_00236710_00236774
and r2, r2, #0xc0000000
cmp r2, #0x40000000
beq .Lbatch16a_00236710_0023677c
.Lbatch16a_00236710_00236774:
mov r0, r1
pop {r4, r5, r6, r7, r8, sb, sl, pc}
.Lbatch16a_00236710_0023677c:
ldr r1, [r0]
mov r2, #0x20
ldr r3, [r1, #8]
lsl r1, r5, #2
blx r3
add r2, r4, #4
mov r6, r0
ldm r2, {r0, r2}
mov r7, #0
cmp r0, r2
movne r1, r6
beq .Lbatch16a_00236710_002367d8
.Lbatch16a_00236710_002367ac:
cmp r1, #0
ldrne ip, [r0]
add r0, r0, #4
strne ip, [r1]
cmp r0, r2
add r1, r1, #4
bne .Lbatch16a_00236710_002367ac
ldr r0, [r4, #8]
ldr r1, [r4, #4]
sub r0, r0, r1
asr r7, r0, #2
.Lbatch16a_00236710_002367d8:
ldr r1, [r4, #4]
cmp r1, #0
beq .Lbatch16a_00236710_002367f4
ldr r0, [r4]
ldr r2, [r0]
ldr r2, [r2, #0xc]
blx r2
.Lbatch16a_00236710_002367f4:
add r0, r6, r7, lsl #2
str r0, [r4, #8]
str r6, [r4, #4]
ldr r0, [r4, #0xc]
and r0, r0, #0xc0000000
orr r0, r0, r5
str r0, [r4, #0xc]
mov r0, sb
.Lbatch16a_00236710_00236814:
ldr r1, [r4, #8]
cmp r1, #0
ldrne r2, [r8]
strne r2, [r1]
ldr r1, [r4, #8]
add r1, r1, #4
str r1, [r4, #8]
pop {r4, r5, r6, r7, r8, sb, sl, pc}
        )batch16"
    );
}
// DECOMP_FUNC(0x001442ac, 296)
extern "C" __attribute__((naked)) void func_001442ac() {
    asm volatile(
        R"batch16(
cmp r0, r1
bxeq lr
push {r4, r5, r6, r7}
add r6, r0, #0x10
cmp r6, r1
sub sp, sp, #8
beq .Lbatch16a_001442ac_001443c8
.Lbatch16a_001442ac_001442c8:
ldr r5, [r6]
ldr ip, [r0]
ldr r3, [r6, #4]
ldr r4, [r0, #4]
subs ip, r5, ip
mov r2, r6
sbcs ip, r3, r4
add r4, r6, #8
vldmia r4, {s0, s1}
bhs .Lbatch16a_001442ac_0014436c
sub r4, r2, r0
add ip, r2, #0x10
asr r7, r4, #4
cmp r7, #0
ble .Lbatch16a_001442ac_00144358
lsls r7, r4, #0x1b
bpl .Lbatch16a_001442ac_0014431c
sub r2, r6, #0x10
sub ip, ip, #0x10
vldmia r2, {s2, s3, s4, s5}
vstmia ip, {s2, s3, s4, s5}
.Lbatch16a_001442ac_0014431c:
asrs r4, r4, #5
beq .Lbatch16a_001442ac_00144358
.Lbatch16a_001442ac_00144324:
mov r7, ip
vldr s2, [r2, #-0x10]
vldr s3, [r2, #-0xc]
vldr s4, [r2, #-8]
vldr s5, [r2, #-4]
sub r7, r7, #0x10
sub r2, r2, #0x20
vstmia r7, {s2, s3, s4, s5}
sub ip, ip, #0x20
subs r4, r4, #1
vldmia r2, {s2, s3, s4, s5}
vstmia ip, {s2, s3, s4, s5}
bne .Lbatch16a_001442ac_00144324
.Lbatch16a_001442ac_00144358:
str r3, [r0, #4]
str r5, [r0]
vstr s0, [r0, #8]
vstr s1, [r0, #0xc]
b .Lbatch16a_001442ac_001443bc
.Lbatch16a_001442ac_0014436c:
sub ip, r2, #0x10
ldm ip, {r4, r7}
subs r4, r5, r4
sbcs r4, r3, r7
bhs .Lbatch16a_001442ac_001443b0
.Lbatch16a_001442ac_00144380:
vmov s3, r7
vldr s2, [ip]
vldr s4, [ip, #8]
vldr s5, [ip, #0xc]
mov r4, r2
mov r2, ip
vstmia r4, {s2, s3, s4, s5}
sub ip, ip, #0x10
ldm ip, {r4, r7}
subs r4, r5, r4
sbcs r4, r3, r7
blo .Lbatch16a_001442ac_00144380
.Lbatch16a_001442ac_001443b0:
str r5, [r2], #4
str r3, [r2], #4
vstmia r2, {s0, s1}
.Lbatch16a_001442ac_001443bc:
add r6, r6, #0x10
cmp r6, r1
bne .Lbatch16a_001442ac_001442c8
.Lbatch16a_001442ac_001443c8:
add sp, sp, #8
pop {r4, r5, r6, r7}
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x00238c44, 320)
extern "C" __attribute__((naked)) void func_00238c44() {
    asm volatile(
        R"batch16(
push {r4, r5, r6, r7, r8}
mov ip, #0xa40
mov r7, r1
ldr r2, [r0, #8]
ldr r4, [r0]
mov r6, #0
cmp r2, #0xa40
mov r5, #1
bhs .Lbatch16a_00238c44_00238ce8
.Lbatch16a_00238c44_00238c68:
cmp r2, ip
mov r3, #0
bhs .Lbatch16a_00238c44_00238cd8
.Lbatch16a_00238c44_00238c74:
add r8, r2, r3
ldrb r8, [r4, r8]
cmp r8, #0
bne .Lbatch16a_00238c44_00238cd8
add r3, r3, #1
cmp r3, r1
bne .Lbatch16a_00238c44_00238ccc
mov r3, r2
add r1, r2, r7
cmp r1, r3
bls .Lbatch16a_00238c44_00238cb0
.Lbatch16a_00238c44_00238ca0:
strb r5, [r4, r3]
add r3, r3, #1
cmp r1, r3
bhi .Lbatch16a_00238c44_00238ca0
.Lbatch16a_00238c44_00238cb0:
ldr r3, [r0, #4]
str r1, [r0, #8]
adds r1, r3, r2, lsl #4
movne r0, r1
beq .Lbatch16a_00238c44_00238ce8
pop {r4, r5, r6, r7, r8}
bx lr
.Lbatch16a_00238c44_00238ccc:
add r8, r2, r3
cmp r8, ip
blo .Lbatch16a_00238c44_00238c74
.Lbatch16a_00238c44_00238cd8:
add r2, r2, r3
add r2, r2, #1
cmp r2, ip
blo .Lbatch16a_00238c44_00238c68
.Lbatch16a_00238c44_00238ce8:
ldr ip, [r0, #8]
ldr r4, [r0]
mov r1, r7
cmp ip, #0
mov r2, #0
bls .Lbatch16a_00238c44_00238d78
.Lbatch16a_00238c44_00238d00:
cmp r2, ip
mov r3, #0
bhs .Lbatch16a_00238c44_00238d68
.Lbatch16a_00238c44_00238d0c:
add r7, r2, r3
ldrb r7, [r4, r7]
cmp r7, #0
bne .Lbatch16a_00238c44_00238d68
add r3, r3, #1
cmp r3, r1
bne .Lbatch16a_00238c44_00238d5c
mov r3, r2
add r1, r1, r2
cmp r1, r3
bls .Lbatch16a_00238c44_00238d48
.Lbatch16a_00238c44_00238d38:
strb r5, [r4, r3]
add r3, r3, #1
cmp r1, r3
bhi .Lbatch16a_00238c44_00238d38
.Lbatch16a_00238c44_00238d48:
ldr r3, [r0, #4]
str r1, [r0, #8]
pop {r4, r5, r6, r7, r8}
add r0, r3, r2, lsl #4
bx lr
.Lbatch16a_00238c44_00238d5c:
add r7, r2, r3
cmp r7, ip
blo .Lbatch16a_00238c44_00238d0c
.Lbatch16a_00238c44_00238d68:
add r2, r2, r3
add r2, r2, #1
cmp r2, ip
blo .Lbatch16a_00238c44_00238d00
.Lbatch16a_00238c44_00238d78:
mov r0, r6
pop {r4, r5, r6, r7, r8}
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x00376130, 332)
extern "C" __attribute__((naked)) void func_00376130() {
    asm volatile(
        R"batch16(
push {r4, r5, r6, r7, r8, sb, sl, lr}
mov r4, r0
mov r7, #0
mov r5, r1
ldrb r0, [r0, #0x3c]
mov sb, r7
cmp r0, #0
beq .Lbatch16a_00376130_0037621c
ldr r0, [r5]
ldr r6, [r4, #0x40]
mov r2, #4
mov r1, #0x14
ldr r3, [r0, #8]
cmp r6, #0
mov r0, r5
beq .Lbatch16a_00376130_003761c8
blx r3
movs r8, r0
beq .Lbatch16a_00376130_00376268
ldr r0, [r5]
lsl r1, r6, #2
mov r2, #4
ldr r3, [r0, #8]
mov r0, r5
blx r3
movs r1, r0
beq .Lbatch16a_00376130_00376204
str r5, [r8]
str r1, [r8, #8]
str r5, [r8, #4]
str r1, [r8, #0xc]
ldr r1, [r8, #0x10]
mov sb, r8
and r1, r1, #0xc0000000
orr r1, r1, r6
bic r1, r1, #0xc0000000
str r1, [r8, #0x10]
b .Lbatch16a_00376130_00376268
.Lbatch16a_00376130_003761c8:
nop
blx r3
cmp r0, #0
beq .Lbatch16a_00376130_00376268
mov r2, #0
str r5, [r0]
str r2, [r0, #8]
str r5, [r0, #4]
str r2, [r0, #0xc]
ldr r2, [r0, #0x10]
add r1, r0, #4
and r2, r2, #0xc0000000
str r2, [r0, #0x10]
bic r2, r2, #0xc0000000
b .Lbatch16a_00376130_00376260
.Lbatch16a_00376130_00376204:
ldr r0, [r5]
mov r1, r8
ldr r2, [r0, #0xc]
mov r0, r5
blx r2
b .Lbatch16a_00376130_00376268
.Lbatch16a_00376130_0037621c:
ldr r0, [r5]
mov r2, #4
mov r1, #0x14
ldr r3, [r0, #8]
mov r0, r5
blx r3
cmp r0, #0
beq .Lbatch16a_00376130_00376268
add r1, r0, #4
str r5, [r0]
stm r1, {r5, sb}
str sb, [r0, #0xc]
ldr r2, [r0, #0x10]
and r2, r2, #0xc0000000
str r2, [r0, #0x10]
bic r2, r2, #0xc0000000
orr r2, r2, #0x40000000
.Lbatch16a_00376130_00376260:
mov sb, r0
str r2, [r1, #0xc]
.Lbatch16a_00376130_00376268:
cmp sb, #0
orreq r7, r7, #0x80000000
mov r0, r7
str sb, [r4, #0x34]
pop {r4, r5, r6, r7, r8, sb, sl, pc}
        )batch16"
    );
}
// DECOMP_FUNC(0x002b1c8c, 368)
extern "C" __attribute__((naked)) void ui_func_002b1c8c() {
    asm volatile(
        R"batch16(
push {r4, r5, r6, r7}
ldrb r1, [r0, #0x89]
cmp r1, #0
bne .Lbatch16a_002b1c8c_002b1d10
ldr r1, [r0, #0x70]
cmp r1, #0
beq .Lbatch16a_002b1c8c_002b1d10
ldrsh r2, [r0, #0x74]
ldrsh r3, [r0, #0x76]
add ip, r1, r2, lsl #2
ldrh ip, [ip, #2]
cmp ip, r3
addgt r1, r3, #1
strhgt r1, [r0, #0x76]
bgt .Lbatch16a_002b1c8c_002b1d10
add r2, r2, #1
mov ip, #0
sxth r3, r2
strh ip, [r0, #0x76]
add r2, r1, r3, lsl #2
strh r3, [r0, #0x74]
ldrsh r2, [r2]
mvn r4, #0
cmn r2, #1
beq .Lbatch16a_002b1c8c_002b1d18
cmn r2, #2
addne r0, r0, #4
stmne r0, {r2, r4}
bne .Lbatch16a_002b1c8c_002b1d10
strh ip, [r0, #0x74]
ldrsh r1, [r1]
add r0, r0, #4
stm r0, {r1, r4}
.Lbatch16a_002b1c8c_002b1d10:
pop {r4, r5, r6, r7}
bx lr
.Lbatch16a_002b1c8c_002b1d18:
ldrb r1, [r0, #0x84]
mov r2, #1
cmp r1, #0
ldrne r1, [r0, #0x78]
cmpne r1, #0
beq .Lbatch16a_002b1c8c_002b1df0
ldrsh r3, [r0, #0x82]
mov r5, #8
rsb r6, r3, r3, lsl #3
add r5, r5, r6, lsl #2
ldr r5, [r1, r5]
cmn r5, #1
beq .Lbatch16a_002b1c8c_002b1df0
add r3, r3, #1
sxth r3, r3
strh r3, [r0, #0x82]
rsb r5, r3, r3, lsl #3
add r1, r1, r5, lsl #2
ldr r1, [r1, #8]
cmn r1, #1
cmnne r1, #3
beq .Lbatch16a_002b1c8c_002b1df0
ldr r5, [r0, #0x48]
mov r3, #0
sxth r2, r1
mov r1, r3
ldrh r6, [r5, #6]
cmp r3, r6, lsr #2
ldrlo r5, [r5, #0x18]
bhs .Lbatch16a_002b1c8c_002b1dbc
.Lbatch16a_002b1c8c_002b1d90:
cmp r3, r2
bne .Lbatch16a_002b1c8c_002b1da0
add r1, r5, r1, lsl #2
b .Lbatch16a_002b1c8c_002b1dc0
.Lbatch16a_002b1c8c_002b1da0:
add r7, r5, r1, lsl #2
add r1, r1, #1
ldrsh r7, [r7]
cmn r7, #1
addeq r3, r3, #1
cmp r1, r6, lsr #2
blo .Lbatch16a_002b1c8c_002b1d90
.Lbatch16a_002b1c8c_002b1dbc:
mov r1, ip
.Lbatch16a_002b1c8c_002b1dc0:
cmp r1, #0
str r1, [r0, #0x70]
beq .Lbatch16a_002b1c8c_002b1d10
strh ip, [r0, #0x74]
strh ip, [r0, #0x76]
strb ip, [r0, #0x89]
strb ip, [r0, #0x8a]
ldrsh r1, [r1]
add r0, r0, #4
stm r0, {r1, r4}
pop {r4, r5, r6, r7}
bx lr
.Lbatch16a_002b1c8c_002b1df0:
strb r2, [r0, #0x89]
pop {r4, r5, r6, r7}
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x00123aac, 376)
extern "C" __attribute__((naked)) void func_00123aac() {
    asm volatile(
        R"batch16(
push {r4, r5, r6, r7, r8, lr}
mov r5, r0
ldr r4, [r5, #8]
ldr r6, [pc, #0xd4]
ldr r0, [pc, #0xcc]
ldr r7, [pc, #0xd0]
ldr r1, [r4, #0x18]
ldr ip, [r6]
cmp r1, r0
sub r0, r1, r0
beq .Lbatch16a_00123aac_00123b48
bgt .Lbatch16a_00123aac_00123af8
add r0, r1, #0xff000000
subs r0, r0, #0x10000
beq .Lbatch16a_00123aac_00123b24
cmp r0, #0x10000
cmpne r0, #0x20000
beq .Lbatch16a_00123aac_00123b58
b .Lbatch16a_00123aac_00123b48
.Lbatch16a_00123aac_00123af8:
cmp r0, #0x10000
cmpne r0, #0x20000
bne .Lbatch16a_00123aac_00123b48
ldr r3, [r4]
cmp r3, #0
cmpne ip, #0
beq .Lbatch16a_00123aac_00123b48
ldr r2, [r5]
ldr r0, [r4, #0x14]
mov r1, r7
b .Lbatch16a_00123aac_00123b44
.Lbatch16a_00123aac_00123b24:
ldr r3, [r4, #4]
cmp r3, #0
beq .Lbatch16a_00123aac_00123b48
cmp ip, #0
beq .Lbatch16a_00123aac_00123b48
.Lbatch16a_00123aac_00123b38:
ldr r2, [r5]
mov r1, r7
mov r0, #0x10000
.Lbatch16a_00123aac_00123b44:
blx ip
.Lbatch16a_00123aac_00123b48:
mov r0, #0
str r0, [r4]
str r0, [r4, #4]
pop {r4, r5, r6, r7, r8, pc}
.Lbatch16a_00123aac_00123b58:
ldr r3, [r4]
cmp r3, #0
cmpne ip, #0
beq .Lbatch16a_00123aac_00123b78
ldr r2, [r5]
ldr r0, [r4, #0x14]
mov r1, r7
blx ip
.Lbatch16a_00123aac_00123b78:
ldr r3, [r4, #4]
cmp r3, #0
ldrne ip, [r6]
cmpne ip, #0
beq .Lbatch16a_00123aac_00123b48
b .Lbatch16a_00123aac_00123b38
.word 0x02010000
.word 0x0044e334
.word 0x00000102
cmp r1, #0
ldrne r0, [r0]
strne r0, [r1]
bx lr
cmp r1, #0
ldrne r0, [r0]
strne r0, [r1]
bx lr
mov r2, r0
ldr r0, [r1]
bx r2
mov r2, r0
ldr r0, [r1]
bx r2
bx lr
bx lr
add r1, r0, #4
mov r2, #0
str r1, [r0, #4]
str r2, [r0]
str r1, [r0, #8]
bx lr
add r1, r0, #4
mov r2, #0
str r1, [r0, #4]
str r2, [r0]
str r1, [r0, #8]
bx lr
add r1, r0, #4
mov r2, #0
str r1, [r0, #4]
str r2, [r0]
str r1, [r0, #8]
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x0034c2fc, 412)
extern "C" __attribute__((naked)) void func_0034c2fc() {
    asm volatile(
        R"batch16(
push {r4, lr}
mov r4, r0
ldr r0, [r0, #0x14]
ldr r1, [r0]
ldr r1, [r1, #8]
blx r1
ldr r0, [r4, #4]
ldr r1, [r4, #0x1c]
vldr s0, [r0, #0xc]
vldr s1, [r1, #0x20]
vadd.f32 s0, s0, s1
vstr s0, [r0, #0xc]
ldr r0, [r4, #4]
ldr r1, [r4, #0x1c]
vldr s0, [r0, #0x10]
vldr s1, [r1, #0x24]
vadd.f32 s0, s0, s1
vstr s0, [r0, #0x10]
ldr r0, [r4, #4]
ldr r1, [r4, #0x1c]
vldr s0, [r0, #0x20]
vldr s1, [r1, #0x20]
vadd.f32 s0, s0, s1
vstr s0, [r0, #0x20]
ldr r0, [r4, #4]
ldr r1, [r4, #0x1c]
vldr s0, [r0, #0x24]
vldr s1, [r1, #0x24]
vadd.f32 s0, s0, s1
vstr s0, [r0, #0x24]
ldr r0, [r4, #4]
ldr r1, [r4, #0x1c]
vldr s0, [r0, #0x34]
vldr s1, [r1, #0x20]
vadd.f32 s0, s0, s1
vstr s0, [r0, #0x34]
ldr r0, [r4, #4]
ldr r1, [r4, #0x1c]
vldr s0, [r0, #0x38]
vldr s1, [r1, #0x24]
vadd.f32 s0, s0, s1
vstr s0, [r0, #0x38]
ldr r0, [r4, #4]
ldr r1, [r4, #0x1c]
vldr s0, [r0, #0x48]
vldr s1, [r1, #0x20]
vadd.f32 s0, s0, s1
vstr s0, [r0, #0x48]
ldr r0, [r4, #4]
ldr r1, [r4, #0x1c]
vldr s0, [r0, #0x4c]
vldr s1, [r1, #0x24]
vadd.f32 s0, s0, s1
vstr s0, [r0, #0x4c]
ldr r0, [r4, #4]
ldr r1, [r4, #0x1c]
vldr s0, [r0, #0x5c]
vldr s1, [r1, #0x48]
vadd.f32 s0, s0, s1
vstr s0, [r0, #0x5c]
ldr r0, [r4, #4]
ldr r1, [r4, #0x1c]
vldr s0, [r0, #0x60]
vldr s1, [r1, #0x4c]
vadd.f32 s0, s0, s1
vstr s0, [r0, #0x60]
ldr r0, [r4, #4]
ldr r1, [r4, #0x1c]
vldr s0, [r0, #0x70]
vldr s1, [r1, #0x48]
vadd.f32 s0, s0, s1
vstr s0, [r0, #0x70]
ldr r0, [r4, #4]
ldr r1, [r4, #0x1c]
vldr s0, [r0, #0x74]
vldr s1, [r1, #0x4c]
vadd.f32 s0, s0, s1
vstr s0, [r0, #0x74]
ldr r0, [r4, #4]
ldr r1, [r4, #0x1c]
vldr s0, [r0, #0x84]
vldr s1, [r1, #0x48]
vadd.f32 s0, s0, s1
vstr s0, [r0, #0x84]
ldr r0, [r4, #4]
ldr r1, [r4, #0x1c]
vldr s0, [r0, #0x88]
vldr s1, [r1, #0x4c]
vadd.f32 s0, s0, s1
vstr s0, [r0, #0x88]
ldr r0, [r4, #4]
ldr r1, [r4, #0x1c]
vldr s0, [r0, #0x98]
vldr s1, [r1, #0x48]
vadd.f32 s0, s0, s1
vstr s0, [r0, #0x98]
ldr r0, [r4, #4]!
ldr r1, [r4, #0x18]
vldr s0, [r0, #0x9c]
vldr s1, [r1, #0x4c]
vadd.f32 s0, s0, s1
vstr s0, [r0, #0x9c]
pop {r4, pc}
        )batch16"
    );
}
// DECOMP_FUNC(0x0026eb14, 440)
extern "C" __attribute__((naked)) void engine_func_0026eb14() {
    asm volatile(
        R"batch16(
str r4, [sp, #-4]!
sub sp, sp, #0x34
cmp r1, #4
vstmia sp, {s0, s1, s2, s3, s4, s5, s6, s7, s8}
addeq r4, sp, #0x24
mov ip, sp
vstmiaeq r4, {s9, s10, s11}
cmp r0, #0
sub r4, r1, #1
beq .Lbatch16a_0026eb14_0026ebcc
cmp r0, #1
beq .Lbatch16a_0026eb14_0026ec48
cmp r0, #2
bne .Lbatch16a_0026eb14_0026ebc0
vmov.f32 s1, s0
vldr s0, [sp, #4]
cmp r4, #0
vmov.f64 d1, d0
ble .Lbatch16a_0026eb14_0026ebb4
vmov.f32 s2, s0
add r0, ip, #0xc
add r1, ip, #0x10
.Lbatch16a_0026eb14_0026eb6c:
vldr s4, [r0]
add r0, r0, #0xc
vcmpe.f32 s4, s1
vmrs apsr_nzcv, fpscr
vldr s5, [r1]
add r1, r1, #0xc
vmovlo.f32 s1, s4
vcmpe.f32 s5, s2
vmrs apsr_nzcv, fpscr
vcmpe.f32 s4, s3
vmovlo.f32 s2, s5
vmrs apsr_nzcv, fpscr
vcmpe.f32 s5, s0
vmovgt.f32 s3, s4
vmrs apsr_nzcv, fpscr
vmovgt.f32 s0, s5
subs r4, r4, #1
bne .Lbatch16a_0026eb14_0026eb6c
.Lbatch16a_0026eb14_0026ebb4:
vstmia r2, {s1, s2}
vstr s3, [r3]
vstr s0, [r3, #4]
.Lbatch16a_0026eb14_0026ebc0:
add sp, sp, #0x34
pop {r4}
bx lr
.Lbatch16a_0026eb14_0026ebcc:
vmov.f32 s0, s2
vmov.f32 s2, s1
cmp r4, #0
addgt r0, ip, #0x10
addgt r1, ip, #0x14
vmov.f32 s3, s0
ble .Lbatch16a_0026eb14_0026ec30
.Lbatch16a_0026eb14_0026ebe8:
vldr s5, [r0]
add r0, r0, #0xc
vcmpe.f32 s5, s1
vmrs apsr_nzcv, fpscr
vldr s4, [r1]
add r1, r1, #0xc
vmovlo.f32 s1, s5
vcmpe.f32 s4, s0
vmrs apsr_nzcv, fpscr
vcmpe.f32 s5, s2
vmovlo.f32 s0, s4
vmrs apsr_nzcv, fpscr
vcmpe.f32 s4, s3
vmovgt.f32 s2, s5
vmrs apsr_nzcv, fpscr
vmovgt.f32 s3, s4
subs r4, r4, #1
bne .Lbatch16a_0026eb14_0026ebe8
.Lbatch16a_0026eb14_0026ec30:
vstr s1, [r2]
vstr s0, [r2, #4]
vstmia r3, {s2, s3}
add sp, sp, #0x34
pop {r4}
bx lr
.Lbatch16a_0026eb14_0026ec48:
vmov.f32 s3, s0
vmov.f32 s1, s2
cmp r4, #0
ble .Lbatch16a_0026eb14_0026ecb0
add r0, ip, #0xc
vmov.f32 s0, s3
vmov.f32 s2, s1
add r1, ip, #0x14
.Lbatch16a_0026eb14_0026ec68:
vldr s4, [r0]
add r0, r0, #0xc
vcmpe.f32 s4, s0
vmrs apsr_nzcv, fpscr
vldr s5, [r1]
add r1, r1, #0xc
vmovlo.f32 s0, s4
vcmpe.f32 s5, s2
vmrs apsr_nzcv, fpscr
vcmpe.f32 s4, s3
vmovlo.f32 s2, s5
vmrs apsr_nzcv, fpscr
vcmpe.f32 s5, s1
vmovgt.f32 s3, s4
vmrs apsr_nzcv, fpscr
vmovgt.f32 s1, s5
subs r4, r4, #1
bne .Lbatch16a_0026eb14_0026ec68
.Lbatch16a_0026eb14_0026ecb0:
vstr s0, [r2]
vstr s2, [r2, #4]
vstr s3, [r3]
vstr s1, [r3, #4]
add sp, sp, #0x34
pop {r4}
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x0022e9ac, 528)
extern "C" __attribute__((naked)) void shop_func_0022e9ac() {
    asm volatile(
        R"batch16(
push {r4, r5, r6}
add r2, r0, #0x15c00
add r2, r2, #0x13c
mov ip, #0
add r4, r0, #0x15c00
cmp r1, #0
mov r5, #2
mov r6, #3
mov r3, #1
add r4, r4, #0x12c
str ip, [r2]
beq .Lbatch16a_0022e9ac_0022ea94
cmp r1, #1
beq .Lbatch16a_0022e9ac_0022eb4c
cmp r1, #2
bne .Lbatch16a_0022e9ac_0022ea8c
ldr r1, [r0, #0x9e4]
cmp r1, #0
strgt r6, [r4]
strgt r3, [r2]
ldr r1, [r0, #0xa58]
cmp r1, #0
ble .Lbatch16a_0022e9ac_0022ea2c
ldr r1, [r2]
mov r3, #4
add r1, r0, r1, lsl #2
add r1, r1, #0x15c00
add r1, r1, #0x12c
str r3, [r1]
ldr r1, [r2]
add r1, r1, #1
str r1, [r2]
.Lbatch16a_0022e9ac_0022ea2c:
ldr r1, [r0, #0xacc]
cmp r1, #0
ble .Lbatch16a_0022e9ac_0022ea5c
ldr r1, [r2]
mov r3, #5
add r1, r0, r1, lsl #2
add r1, r1, #0x15c00
add r1, r1, #0x12c
str r3, [r1]
ldr r1, [r2]
add r1, r1, #1
str r1, [r2]
.Lbatch16a_0022e9ac_0022ea5c:
ldr r1, [r0, #0xb40]
cmp r1, #0
ble .Lbatch16a_0022e9ac_0022ea8c
ldr r3, [r2]
mov r1, #6
add r0, r0, r3, lsl #2
add r0, r0, #0x15c00
add r0, r0, #0x12c
str r1, [r0]
ldr r0, [r2]
add r0, r0, #1
str r0, [r2]
.Lbatch16a_0022e9ac_0022ea8c:
pop {r4, r5, r6}
bx lr
.Lbatch16a_0022e9ac_0022ea94:
ldr r1, [r0, #0x888]
cmp r1, #0
ldrle r1, [r0, #0x8fc]
cmple r1, #0
ldrle r1, [r0, #0x970]
cmple r1, #0
strgt ip, [r4]
strgt r3, [r2]
ldr r1, [r0, #0x9e4]
cmp r1, #0
ldrle r1, [r0, #0xa58]
cmple r1, #0
bgt .Lbatch16a_0022e9ac_0022eadc
ldr r1, [r0, #0xacc]
cmp r1, #0
ldrle r1, [r0, #0xb40]
cmple r1, #0
ble .Lbatch16a_0022e9ac_0022eafc
.Lbatch16a_0022e9ac_0022eadc:
ldr r1, [r2]
add r1, r0, r1, lsl #2
add r1, r1, #0x15c00
add r1, r1, #0x12c
str r3, [r1]
ldr r1, [r2]
add r1, r1, #1
str r1, [r2]
.Lbatch16a_0022e9ac_0022eafc:
ldr r1, [r0, #0xbb4]
cmp r1, #0
ldr r1, [r2]
ble .Lbatch16a_0022e9ac_0022eb28
add r1, r0, r1, lsl #2
add r1, r1, #0x15c00
add r1, r1, #0x12c
str r5, [r1]
ldr r1, [r2]
add r1, r1, #1
str r1, [r2]
.Lbatch16a_0022e9ac_0022eb28:
add r0, r0, r1, lsl #2
add r0, r0, #0x15c00
add r0, r0, #0x12c
str r6, [r0]
ldr r0, [r2]
add r0, r0, #1
str r0, [r2]
pop {r4, r5, r6}
bx lr
.Lbatch16a_0022e9ac_0022eb4c:
ldr r1, [r0, #0x888]
cmp r1, #0
strgt ip, [r4]
strgt r3, [r2]
ldr r1, [r0, #0x8fc]
cmp r1, #0
ble .Lbatch16a_0022e9ac_0022eb88
ldr r1, [r2]
add r1, r0, r1, lsl #2
add r1, r1, #0x15c00
add r1, r1, #0x12c
str r3, [r1]
ldr r1, [r2]
add r1, r1, #1
str r1, [r2]
.Lbatch16a_0022e9ac_0022eb88:
ldr r1, [r0, #0x970]
cmp r1, #0
ble .Lbatch16a_0022e9ac_0022ea8c
ldr r1, [r2]
add r0, r0, r1, lsl #2
add r0, r0, #0x15c00
add r0, r0, #0x12c
str r5, [r0]
ldr r0, [r2]
add r0, r0, #1
str r0, [r2]
pop {r4, r5, r6}
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x0012ce8c, 604)
extern "C" __attribute__((naked)) void func_0012ce8c() {
    asm volatile(
        R"batch16(
mov r3, #0
str r3, [r0]
str r3, [r0, #4]
ldr ip, [r1, #0x30]
str ip, [r0, #8]
ldr ip, [r1, #0x34]
str ip, [r0, #0xc]
ldr ip, [r1, #0x38]
str ip, [r0, #0x10]
ldr ip, [r1, #0x3c]
str ip, [r0, #0x14]
str r3, [r1, #0x34]
str r3, [r1, #0x38]
ldr r2, [r1, #0x3c]
add ip, r0, #0x40
and r2, r2, #0xc0000000
str r2, [r1, #0x3c]
add r2, r0, #0x20
stm r2, {r3, ip}
str ip, [r0, #0x28]
ldr ip, [r0, #0x2c]
str r3, [r0, #0x60]
and ip, ip, #0xc0000000
orr ip, ip, #8
bic ip, ip, #0xc0000000
orr ip, ip, #0x80000000
str ip, [r0, #0x2c]
str r3, [r0, #0x64]
ldr ip, [r1]
str ip, [r0, #0x68]
ldr ip, [r1, #4]
str ip, [r0, #0x6c]
ldr ip, [r1, #8]
str ip, [r0, #0x70]
ldr ip, [r1, #0xc]
str ip, [r0, #0x74]
str r3, [r1, #4]
str r3, [r1, #8]
ldr r2, [r1, #0xc]
mvn ip, #0
and r2, r2, #0xc0000000
str r2, [r1, #0xc]
str ip, [r0, #0x78]
vldr s0, [r1, #0x10]
vstr s0, [r0, #0x7c]
vldr s0, [r1, #0x14]
vstr s0, [r0, #0x80]
vldr s0, [r1, #0x18]
vstr s0, [r0, #0x84]
vldr s0, [r1, #0x1c]
vstr s0, [r0, #0x88]
str r3, [r1, #0x14]
str r3, [r1, #0x18]
ldr r2, [r1, #0x1c]
and r2, r2, #0xc0000000
str r2, [r1, #0x1c]
vldr s0, [r1, #0x20]
vstr s0, [r0, #0x8c]
vldr s0, [r1, #0x24]
vstr s0, [r0, #0x90]
vldr s0, [r1, #0x28]
vstr s0, [r0, #0x94]
vldr s0, [r1, #0x2c]
vstr s0, [r0, #0x98]
str r3, [r1, #0x24]
str r3, [r1, #0x28]
ldr r2, [r1, #0x2c]
and r2, r2, #0xc0000000
str r2, [r1, #0x2c]
str r3, [r0, #0xa0]
str ip, [r0, #0x9c]
mov r1, #1
str r3, [r0, #0xa4]
strb r1, [r0, #0xa8]
strb r1, [r0, #0xa9]
strb r1, [r0, #0xaa]
strb r1, [r0, #0xab]
strb r1, [r0, #0xac]
ldr r1, [r0, #0x2c]
ldrd r2, r3, [r0, #0x24]
bic r1, r1, #0xc0000000
sub r3, r3, r2
add r1, r2, r1, lsl #2
str r1, [r0, #0x28]
ldr r1, [r0, #0x14]
ldrd r2, r3, [r0, #0xc]
bic r1, r1, #0xc0000000
sub r3, r3, r2
add r1, r2, r1, lsl #2
str r1, [r0, #0x10]
ldr r1, [r0, #0x74]
bic r2, r1, #0xc0000000
add r1, r0, #0x6c
ldm r1, {r1, r3}
mov r3, #0
add r2, r1, r2, lsl #2
str r2, [r0, #0x70]
sub r2, r2, r1
asr ip, r2, #2
cmp ip, #0
ble .Lbatch16a_0012ce8c_0012d044
lsl ip, r2, #0x1d
cmp ip, #0
strlt r3, [r1], #4
asrs r2, r2, #3
beq .Lbatch16a_0012ce8c_0012d044
.Lbatch16a_0012ce8c_0012d034:
str r3, [r1], #4
subs r2, r2, #1
str r3, [r1], #4
bne .Lbatch16a_0012ce8c_0012d034
.Lbatch16a_0012ce8c_0012d044:
ldr r1, [r0, #0x88]
bic r2, r1, #0xc0000000
add r1, r0, #0x80
ldm r1, {r1, r3}
mov r3, #0
add r2, r1, r2, lsl #2
str r2, [r0, #0x84]
sub r2, r2, r1
asr ip, r2, #2
cmp ip, #0
ble .Lbatch16a_0012ce8c_0012d094
lsl ip, r2, #0x1d
cmp ip, #0
strlt r3, [r1], #4
asrs r2, r2, #3
beq .Lbatch16a_0012ce8c_0012d094
.Lbatch16a_0012ce8c_0012d084:
str r3, [r1], #4
subs r2, r2, #1
str r3, [r1], #4
bne .Lbatch16a_0012ce8c_0012d084
.Lbatch16a_0012ce8c_0012d094:
ldr r1, [r0, #0x98]
bic r2, r1, #0xc0000000
add r1, r0, #0x90
ldm r1, {r1, r3}
mov r3, #0
add r2, r1, r2, lsl #2
str r2, [r0, #0x94]
sub r2, r2, r1
asr ip, r2, #2
cmp ip, #0
ble .Lbatch16a_0012ce8c_0012d0e4
lsl ip, r2, #0x1d
cmp ip, #0
strlt r3, [r1], #4
asrs r2, r2, #3
beq .Lbatch16a_0012ce8c_0012d0e4
.Lbatch16a_0012ce8c_0012d0d4:
str r3, [r1], #4
subs r2, r2, #1
str r3, [r1], #4
bne .Lbatch16a_0012ce8c_0012d0d4
.Lbatch16a_0012ce8c_0012d0e4:
bx lr
        )batch16"
    );
}
// DECOMP_FUNC(0x003791c0, 624)
extern "C" __attribute__((naked)) void func_003791c0() {
    asm volatile(
        R"batch16(
push {r0, r1, r2, r3, r4, r5, r6, r7, r8, sb, sl, fp, lr}
vpush {d0}
sub sp, sp, #0x5c
ldrb r1, [r0, #0x10e]
cmp r1, #0
beq .Lbatch16a_003791c0_00379428
ldr r1, [r2]
mov ip, #0
mov r4, ip
str r1, [sp, #0x30]
ldr r1, [r2, #4]
mov r5, ip
mov r6, ip
str r1, [sp, #0x34]
ldr r1, [r2, #8]
mov r7, ip
str r1, [sp, #0x38]
ldr r1, [r2, #0xc]
str r1, [sp, #0x3c]
ldrb r2, [r0, #0x10d]
mov r1, ip
str ip, [sp, #0x54]
cmp r2, #0
ble .Lbatch16a_003791c0_003793d4
.Lbatch16a_003791c0_00379220:
ldr r2, [sp, #0x70]
add r1, r0, r1, lsl #2
str r1, [sp, #0x4c]
cmp r2, #0
ldr r2, [r1, #0x44]
add r5, r0, #0xbc
mov r8, #0
str r2, [sp, #0x48]
ldr fp, [r1, #0x54]!
ldm r5, {r5, r6}
ldr r4, [r0, #0xb0]
ldr r7, [r0, #0xd0]
ldr ip, [r0, #0xa8]
ldr r2, [r1, #0x84]
ble .Lbatch16a_003791c0_003793b4
ldr r3, [sp, #0x54]
ldr sb, [sp, #0x54]
add r1, sp, #0x30
add r3, r0, r3, lsl #3
str r3, [sp, #0x58]
ldr r1, [r1, sb, lsl #2]
str r1, [sp, #0x20]
.Lbatch16a_003791c0_00379278:
ldr sl, [r1, r8, lsl #2]
ldr r1, [sp, #0x48]
ldr r3, [r0, #0xe8]
ldr lr, [r1, ip, lsl #2]
str sl, [r1, ip, lsl #2]
ldr sb, [fp, r4, lsl #2]
str sl, [fp, r4, lsl #2]
ldr r1, [sp, #0x58]
mul r3, lr, r3
ldr sl, [r1, #0x64]
ldr r1, [sl, r5, lsl #2]
str r3, [sp, #0x50]
ldr r3, [r0, #0xc4]
cmp r1, #0
rsblt lr, r1, #0
str r1, [sp, #0x24]
mullt lr, r3, lr
mulge lr, r3, r1
asr lr, lr, #7
rsblt lr, lr, #0
add lr, lr, sb
str lr, [sl, r5, lsl #2]
ldr r1, [sp, #0x58]
ldr lr, [r1, #0x68]
ldr r1, [r0, #0xc8]
ldr sl, [lr, r6, lsl #2]
cmp sl, #0
mulge r1, r1, sl
asrge r1, r1, #7
bge .Lbatch16a_003791c0_00379300
rsb r3, sl, #0
mul r1, r1, r3
asr r1, r1, #7
rsb r1, r1, #0
.Lbatch16a_003791c0_00379300:
add sb, sb, r1
ldr r1, [sp, #0x24]
str sb, [lr, r6, lsl #2]
ldr lr, [r0, #0xd4]
sub r3, r1, sl
ldr r1, [sp, #0x4c]
add ip, ip, #1
add r4, r4, #1
add r5, r5, #1
ldr r1, [r1, #0x84]
add r6, r6, #1
ldr sb, [r1, r7, lsl #2]
cmp sb, #0
rsblt sl, sb, #0
mullt sl, sl, lr
mulge sl, sb, lr
asr sl, sl, #7
rsblt sl, sl, #0
add sl, sl, r3
cmp sl, #0
str sl, [r1, r7, lsl #2]
rsblt r1, sl, #0
add r7, r7, #1
mullt r1, r1, lr
mulge r1, sl, lr
ldr sl, [r0, #0xf0]
asr r1, r1, #7
rsblt r1, r1, #0
sub r1, sb, r1
ldr sb, [r0, #0xf4]
mul r1, sl, r1
ldr sl, [r0, #0xec]
mla r1, r2, sb, r1
ldr sb, [sp, #0x50]
asr r2, r1, #7
mul r1, sl, r2
add r1, r1, sb
ldr sb, [sp, #0x20]
asr r1, r1, #7
str r1, [sb, r8, lsl #2]
ldr r3, [sp, #0x70]
add r8, r8, #1
cmp r8, r3
ldrlt r1, [sp, #0x20]
blt .Lbatch16a_003791c0_00379278
.Lbatch16a_003791c0_003793b4:
ldr r1, [sp, #0x4c]
str r2, [r1, #0xd8]
ldr r1, [sp, #0x54]
add r1, r1, #1
str r1, [sp, #0x54]
ldrb r2, [r0, #0x10d]
cmp r1, r2
blt .Lbatch16a_003791c0_00379220
.Lbatch16a_003791c0_003793d4:
ldr r2, [r0, #0xa4]
mov r1, #0
cmp r2, ip
strls r1, [r0, #0xa8]
strhi ip, [r0, #0xa8]
ldr r2, [r0, #0xac]
cmp r2, r4
strls r1, [r0, #0xb0]
strhi r4, [r0, #0xb0]
ldr r2, [r0, #0xb4]
cmp r2, r5
strls r1, [r0, #0xbc]
strhi r5, [r0, #0xbc]
ldr r2, [r0, #0xb8]
cmp r2, r6
strls r1, [r0, #0xc0]
strhi r6, [r0, #0xc0]
ldr r2, [r0, #0xcc]
cmp r2, r7
strls r1, [r0, #0xd0]
strhi r7, [r0, #0xd0]
.Lbatch16a_003791c0_00379428:
add sp, sp, #0x74
pop {r4, r5, r6, r7, r8, sb, sl, fp, pc}
        )batch16"
    );
}
// DECOMP_FUNC(0x002406ac, 76)
extern "C" __attribute__((naked)) void func_002406ac() {
    asm volatile(
        R"batch16(
mov r0, #0
str r0, [r1, #0x7c]
and r3, r3, #0xff
str r2, [r1, #0x78]
str r3, [r1, #0x84]
cmp r2, #0
ldr r2, [r1, #0x64]
ldr r0, [r1, #0x50]
and ip, r2, #0xff
orrne r0, r0, #0x2000
str ip, [r1, #0x88]
beq .Lbatch16a_002406ac_002406e4
.Lbatch16a_002406ac_002406dc:
str r0, [r1, #0x50]
bx lr
.Lbatch16a_002406ac_002406e4:
bic r2, r2, #0xff
orr r2, r2, r3
bic r0, r0, #0x2000
str r2, [r1, #0x64]
b .Lbatch16a_002406ac_002406dc
        )batch16"
    );
}
// DECOMP_FUNC(0x003e8a88, 76)
extern "C" __attribute__((naked)) void func_003e8a88() {
    asm volatile(
        R"batch16(
ldr r0, [sp]
vldr s1, [r3, #8]
ldr r3, [r1, #4]
mov r2, #1
vldr s0, [r0]
bics r2, r2, r3
add r0, r1, #8
vmul.f32 s0, s0, s1
beq .Lbatch16a_003e8a88_003e8ac4
vstr s0, [r0]
ldr r0, [r1, #4]
orr r0, r0, #1
str r0, [r1, #4]
.Lbatch16a_003e8a88_003e8abc:
mov r0, #1
bx lr
.Lbatch16a_003e8a88_003e8ac4:
vldr s1, [r0]
vadd.f32 s0, s1, s0
vstr s0, [r0]
b .Lbatch16a_003e8a88_003e8abc
        )batch16"
    );
}
// DECOMP_FUNC(0x003fc9a4, 100)
extern "C" __attribute__((naked)) void func_003fc9a4() {
    asm volatile(
        R"batch16(
ldrb r2, [r0, #4]
cmp r2, #2
beq .Lbatch16a_003fc9a4_003fc9c0
cmp r2, #3
ldreq r2, [r0, #0xc]
bne .Lbatch16a_003fc9a4_003fc9d4
b .Lbatch16a_003fc9a4_003fc9f8
.Lbatch16a_003fc9a4_003fc9c0:
ldrh r0, [r0, #6]
cmp r0, r1
bne .Lbatch16a_003fc9a4_003fc9d4
.Lbatch16a_003fc9a4_003fc9cc:
mov r0, #1
bx lr
.Lbatch16a_003fc9a4_003fc9d4:
mov r0, #0
bx lr
.Lbatch16a_003fc9a4_003fc9dc:
ldrh ip, [r2, #8]
add r3, r2, #8
cmp ip, r1
ldrhls ip, [r3, #2]
cmpls r1, ip
ldrhi r2, [r2, #4]
bls .Lbatch16a_003fc9a4_003fc9cc
.Lbatch16a_003fc9a4_003fc9f8:
add r3, r0, #8
cmp r2, r3
bne .Lbatch16a_003fc9a4_003fc9dc
b .Lbatch16a_003fc9a4_003fc9d4
        )batch16"
    );
}
// DECOMP_FUNC(0x003813d0, 108)
extern "C" __attribute__((naked)) void func_003813d0() {
    asm volatile(
        R"batch16(
ldr r1, [r0]
ldrb r2, [r1]
tst r2, #0x80
addeq r1, r1, #1
streq r1, [r0]
beq .Lbatch16a_003813d0_0038141c
and r3, r2, #0xe0
cmp r3, #0xc0
beq .Lbatch16a_003813d0_00381424
lsl r3, r2, #0xc
ldrb r2, [r1, #1]
and r2, r2, #0x3f
orr r3, r3, r2, lsl #6
ldrb r2, [r1, #2]
add r1, r1, #3
and r2, r2, #0x3f
orr r2, r2, r3
uxth r2, r2
.Lbatch16a_003813d0_00381418:
str r1, [r0]
.Lbatch16a_003813d0_0038141c:
mov r0, r2
bx lr
.Lbatch16a_003813d0_00381424:
ldrb r3, [r1, #1]
and r2, r2, #0x1f
add r1, r1, #2
and r3, r3, #0x3f
orr r2, r3, r2, lsl #6
b .Lbatch16a_003813d0_00381418
        )batch16"
    );
}
// DECOMP_FUNC(0x00237b34, 132)
extern "C" __attribute__((naked)) void func_00237b34() {
    asm volatile(
        R"batch16(
push {r4, r5, r6, r7}
mov r6, #1
.Lbatch16a_00237b34_00237b3c:
ldr r5, [r0, #0x10]
mov ip, #0
cmp r5, #0
bls .Lbatch16a_00237b34_00237ba8
.Lbatch16a_00237b34_00237b4c:
ldrb r2, [r1, ip]
cmp r2, #0
beq .Lbatch16a_00237b34_00237b9c
ldr r2, [r0, #0x14]
ldr r2, [r2, ip, lsl #2]
add r2, r2, #8
ldr r3, [r2, #4]
cmp r3, r2
beq .Lbatch16a_00237b34_00237b9c
.Lbatch16a_00237b34_00237b70:
ldrb r4, [r3, #0xc]
cmp r4, #1
bne .Lbatch16a_00237b34_00237b90
ldr r4, [r3, #8]
ldr r4, [r4, #0x14]
ldrb r7, [r1, r4]
cmp r7, #0
beq .Lbatch16a_00237b34_00237bb0
.Lbatch16a_00237b34_00237b90:
ldr r3, [r3, #4]
cmp r3, r2
bne .Lbatch16a_00237b34_00237b70
.Lbatch16a_00237b34_00237b9c:
add ip, ip, #1
cmp r5, ip
bhi .Lbatch16a_00237b34_00237b4c
.Lbatch16a_00237b34_00237ba8:
pop {r4, r5, r6, r7}
bx lr
.Lbatch16a_00237b34_00237bb0:
strb r6, [r1, r4]
b .Lbatch16a_00237b34_00237b3c
        )batch16"
    );
}
// DECOMP_FUNC(0x002c38d4, 148)
extern "C" __attribute__((naked)) void engine_func_002c38d4() {
    asm volatile(
        R"batch16(
str r4, [sp, #-4]!
ldr r2, [r0, #4]
mov r4, #0
cmp r2, #0
streq r1, [r0]
ldrne r3, [r1]
streq r1, [r0, #4]
streq r4, [r1, #8]
streq r4, [r1, #0xc]
beq .Lbatch16a_002c38d4_002c3938
.Lbatch16a_002c38d4_002c38fc:
ldr ip, [r2]
cmp r3, ip
bhi .Lbatch16a_002c38d4_002c3918
ldr r2, [r2, #8]
cmp r2, #0
bne .Lbatch16a_002c38d4_002c38fc
b .Lbatch16a_002c38d4_002c394c
.Lbatch16a_002c38d4_002c3918:
cmp r2, #0
beq .Lbatch16a_002c38d4_002c394c
ldr r3, [r2, #0xc]
str r1, [r2, #0xc]
cmp r3, #0
strd r2, r3, [r1, #8]
streq r1, [r0, #4]
strne r1, [r3, #8]
.Lbatch16a_002c38d4_002c3938:
ldr r1, [r0, #8]
add r1, r1, #1
str r1, [r0, #8]
pop {r4}
bx lr
.Lbatch16a_002c38d4_002c394c:
str r4, [r1, #8]
ldr r2, [r0]
str r2, [r1, #0xc]
str r1, [r0]
ldr r2, [r1, #0xc]
str r1, [r2, #8]
b .Lbatch16a_002c38d4_002c3938
        )batch16"
    );
}
// DECOMP_FUNC(0x003e4450, 152)
extern "C" __attribute__((naked)) void func_003e4450() {
    asm volatile(
        R"batch16(
vmov r0, s0
add r3, r0, #0x40000000
adds r3, r3, #0x800000
beq .Lbatch16a_003e4450_003e44c0
ldr ip, [r1, #0x3c]
mov r3, #8
add r0, r1, #0x30
bics r3, r3, ip
beq .Lbatch16a_003e4450_003e44c4
vldr s2, [r2, #0x30]
vldr s1, [r2, #0x34]
vldr s3, [r2, #0x38]
vmul.f32 s2, s2, s0
vmul.f32 s1, s1, s0
vmul.f32 s0, s3, s0
vldr s3, [r0]
vadd.f32 s2, s3, s2
vstr s2, [r0]
vldr s2, [r0, #4]
vadd.f32 s1, s2, s1
vstr s1, [r0, #4]
vldr s1, [r0, #8]
vadd.f32 s0, s1, s0
.Lbatch16a_003e4450_003e44ac:
vstr s0, [r0, #8]
ldr r0, [r1, #0x3c]
bic r0, r0, #8
orr r0, r0, #0x800
str r0, [r1, #0x3c]
.Lbatch16a_003e4450_003e44c0:
bx lr
.Lbatch16a_003e4450_003e44c4:
vldr s1, [r2, #0x30]
vmul.f32 s1, s1, s0
vstr s1, [r0]
vldr s1, [r2, #0x34]
vmul.f32 s1, s1, s0
vstr s1, [r0, #4]
vldr s1, [r2, #0x38]
vmul.f32 s0, s1, s0
b .Lbatch16a_003e4450_003e44ac
        )batch16"
    );
}
// DECOMP_FUNC(0x00159370, 220)
extern "C" __attribute__((naked)) void engine_func_00159370() {
    asm volatile(
        R"batch16(
cmp r3, #0
bmi .Lbatch16a_00159370_001593d4
.Lbatch16a_00159370_00159378:
lsls r7, r6, #1
beq .Lbatch16a_00159370_001593c8
.Lbatch16a_00159370_00159380:
push {r2, r3, r4, lr}
rrx r7, r7
push {r0, r1}
mov r0, #0x10
mov r1, #0x10
mov r0, #0
pop {r0, r1, r2, r3}
add fp, fp, #1
cmp fp, #1
lsrseq r7, r7, #0x20
pop {r4, lr}
addshs r2, r2, #1
addshs r1, r1, #1
movhs r1, #0x80000000
adc r3, r3, #0
.Lbatch16a_00159370_001593bc:
and r0, r0, #0x80000000
orr r0, r3, r0
bx lr
.Lbatch16a_00159370_001593c8:
blo .Lbatch16a_00159370_001593bc
lsrs r7, r2, #1
b .Lbatch16a_00159370_00159380
.Lbatch16a_00159370_001593d4:
orr r6, r6, r6, lsl #16
cmn r3, #0x40
lsr r6, r6, #0x10
ble .Lbatch16a_00159370_00159424
cmn r3, #0x20
orrle r6, r6, r2
movle r2, r1
movle r1, #0
addle r3, r3, #0x20
rsbs r3, r3, #0
beq .Lbatch16a_00159370_00159378
orr r6, r6, r6, lsl #16
rsb r7, r3, #0x20
lsr r6, r6, #0x10
orr r6, r6, r2, lsl r7
lsr r2, r2, r3
orr r2, r2, r1, lsl r7
lsr r1, r1, r3
mov r3, #0
b .Lbatch16a_00159370_00159378
.Lbatch16a_00159370_00159424:
orr r6, r6, r2
mov r3, #0
mov r2, #0
orr r6, r6, r6, lsl #16
lsr r6, r6, #0x10
orr r6, r6, r1
mov r1, #0
orrlt r6, r6, r6, lsl #16
lsrlt r6, r6, #0x10
b .Lbatch16a_00159370_00159378
        )batch16"
    );
}
// DECOMP_FUNC(0x00337b34, 268)
extern "C" __attribute__((naked)) void func_00337b34() {
    asm volatile(
        R"batch16(
push {r4, r5, r6}
mov ip, #0
ldr r4, [r1]
.Lbatch16a_00337b34_00337b40:
add r5, r0, ip, lsl #3
add r3, r5, #0x4400
tst r4, #2
add r3, r3, #0xb8
beq .Lbatch16a_00337b34_00337b64
ldrsh r5, [r3, #4]
cmn r5, #1
beq .Lbatch16a_00337b34_00337b8c
b .Lbatch16a_00337b34_00337b7c
.Lbatch16a_00337b34_00337b64:
tst r4, #0x38
beq .Lbatch16a_00337b34_00337b7c
ldrsh r5, [r3, #4]
ldrh r6, [r1, #0xce]
cmp r5, r6
beq .Lbatch16a_00337b34_00337b8c
.Lbatch16a_00337b34_00337b7c:
add ip, ip, #1
cmp ip, #0x80
blt .Lbatch16a_00337b34_00337b40
b .Lbatch16a_00337b34_00337b94
.Lbatch16a_00337b34_00337b8c:
cmp r3, #0
bne .Lbatch16a_00337b34_00337bec
.Lbatch16a_00337b34_00337b94:
mov ip, #0
.Lbatch16a_00337b34_00337b98:
add r3, r0, ip, lsl #3
add r3, r3, #0x4400
add r3, r3, #0xb8
ldrsh r5, [r3, #4]
cmp r5, #0
ldreq r5, [r3]
cmpeq r5, #0
beq .Lbatch16a_00337b34_00337bcc
add ip, ip, #1
cmp ip, #0x80
blt .Lbatch16a_00337b34_00337b98
.Lbatch16a_00337b34_00337bc4:
pop {r4, r5, r6}
bx lr
.Lbatch16a_00337b34_00337bcc:
tst r4, #2
beq .Lbatch16a_00337b34_00337c0c
mvn r1, #0
mov r0, #2
strh r1, [r3, #4]
.Lbatch16a_00337b34_00337be0:
str r0, [r3]
.Lbatch16a_00337b34_00337be4:
cmp r3, #0
beq .Lbatch16a_00337b34_00337bc4
.Lbatch16a_00337b34_00337bec:
cmp r2, #1
mov r0, #1
strbeq r0, [r3, #6]
beq .Lbatch16a_00337b34_00337bc4
cmp r2, #2
strbeq r0, [r3, #7]
pop {r4, r5, r6}
bx lr
.Lbatch16a_00337b34_00337c0c:
ldrh r0, [r1, #0xce]
strh r0, [r3, #4]
ldr r0, [r1]
tst r0, #8
movne r0, #8
bne .Lbatch16a_00337b34_00337be0
tst r0, #0x10
movne r0, #0x10
bne .Lbatch16a_00337b34_00337be0
tst r0, #0x20
movne r0, #0x20
bne .Lbatch16a_00337b34_00337be0
b .Lbatch16a_00337b34_00337be4
        )batch16"
    );
}
// DECOMP_FUNC(0x002b4454, 420)
extern "C" __attribute__((naked)) void func_002b4454() {
    asm volatile(
        R"batch16(
push {r4, r5, r6, r7, r8}
and r6, r2, #0xff
lsl r7, r2, #0x10
bic r5, r5, #0xff
ldr ip, [sp, #0x14]
asr r2, r7, #0x18
orr r5, r5, r6
lsl r2, r2, #8
and r2, r2, #0xff00
bic r5, r5, #0xff00
orr r5, r5, r2
lsl r6, ip, #2
ldr r4, [sp, #0x18]
ldr r2, [r0, #4]
mov ip, #0x20
str ip, [r0, #4]
ldr r7, [r0, #8]
cmp r7, #0x20
movlo r7, ip
str r7, [r0, #8]
ldr r7, [r0]
str r2, [r0, #4]
add r7, r7, #0x1f
bic r7, r7, #0x1f
add r6, r6, r7
str r6, [r0]
ldr ip, [r0, #8]
cmp ip, r2
movhs r2, ip
str r2, [r0, #8]
ldr r6, [r0, #4]
ldr r7, [r0]
cmp r3, #0
lsl ip, r3, #2
mov r2, r0
beq .Lbatch16a_002b4454_002b45e0
add r8, r7, r6
sub r7, r6, #1
sub r6, r8, #1
bic r6, r6, r7
add r6, r6, #0x14
str r6, [r2]
ldr r8, [r2, #4]
add r6, r6, r8
sub r6, r6, #1
bic r6, r6, r7
add r6, r6, ip
.Lbatch16a_002b4454_002b4510:
lsl r2, r5, #0x10
str r6, [r0]
asrs r2, r2, #0x18
cmpne r1, #0
ldrne r2, [r1, #0x28]
cmpne r2, #0
beq .Lbatch16a_002b4454_002b4594
ldr r5, [r0, #4]
ldr r6, [r0]
mul r4, r2, r4
add r6, r6, r5
sub r5, r5, #1
sub r6, r6, #1
bic r5, r6, r5
add r5, r5, #0x2c
lsl r6, r2, #2
str r5, [r0]
ldr r2, [r0, #4]
mov r1, r0
add r5, r5, r2
sub r2, r2, #1
sub r5, r5, #1
bic r2, r5, r2
add r2, r2, r6
lsl r5, r4, #2
str r2, [r1]
ldr r4, [r1, #4]
add r2, r2, r4
sub r4, r4, #1
sub r2, r2, #1
bic r2, r2, r4
add r2, r2, r5
str r2, [r0]
.Lbatch16a_002b4454_002b4594:
ldr r1, [r0, #4]
ldr r2, [r0]
cmp r3, #0
add r2, r2, r1
sub r1, r1, #1
sub r2, r2, #1
bic r1, r2, r1
add r1, r1, #0x14
beq .Lbatch16a_002b4454_002b45d4
str r1, [r0]
ldr r2, [r0, #4]
add r1, r1, r2
sub r2, r2, #1
sub r1, r1, #1
bic r1, r1, r2
add r1, r1, ip
.Lbatch16a_002b4454_002b45d4:
str r1, [r0]
pop {r4, r5, r6, r7, r8}
bx lr
.Lbatch16a_002b4454_002b45e0:
add r7, r7, r6
sub r6, r6, #1
sub r7, r7, #1
bic r6, r7, r6
add r6, r6, #0x14
b .Lbatch16a_002b4454_002b4510
        )batch16"
    );
}
// DECOMP_FUNC(0x00370a18, 652)
extern "C" __attribute__((naked)) void func_00370a18() {
    asm volatile(
        R"batch16(
push {r4, r5, r6, r7, r8, sb, sl, lr}
mov r4, r0
mov r5, r1
mov r8, #0
ldr r0, [r0, #0x218]
mov r7, r8
ldrb r1, [r0]
cmp r1, #0
beq .Lbatch16a_00370a18_00370c04
ldr r6, [r0, #4]
ldr r0, [r5]
mov r2, #4
cmp r6, #0
mov r1, #0x14
ldr r3, [r0, #8]
mov r0, r5
beq .Lbatch16a_00370a18_00370ab4
blx r3
movs sb, r0
moveq sb, r7
beq .Lbatch16a_00370a18_00370b74
ldr r0, [r5]
lsl r1, r6, #2
mov r2, #4
ldr r3, [r0, #8]
mov r0, r5
blx r3
movs r1, r0
beq .Lbatch16a_00370a18_00370b5c
str r5, [sb]
str r1, [sb, #8]
str r5, [sb, #4]
str r1, [sb, #0xc]
ldr r1, [sb, #0x10]
and r1, r1, #0xc0000000
orr r1, r1, r6
bic r1, r1, #0xc0000000
str r1, [sb, #0x10]
b .Lbatch16a_00370a18_00370b74
.Lbatch16a_00370a18_00370ab4:
nop
blx r3
cmp r0, #0
moveq r1, r7
beq .Lbatch16a_00370a18_00370af0
mov r1, r0
str r5, [r0], #4
mov r2, r5
mov r3, #0
strd r2, r3, [r0]
str r3, [r0, #8]
ldr r2, [r0, #0xc]
and r2, r2, #0xc0000000
bic r2, r2, #0xc0000000
str r2, [r0, #0xc]
.Lbatch16a_00370a18_00370af0:
str r1, [r4, #0x158]
ldr r0, [r5]
mov r2, #4
mov r1, #0x14
ldr r3, [r0, #8]
mov r0, r5
blx r3
cmp r0, #0
beq .Lbatch16a_00370a18_00370b40
mov r2, #0
str r5, [r0]
str r2, [r0, #8]
str r5, [r0, #4]
str r2, [r0, #0xc]
ldr r2, [r0, #0x10]
add r1, r0, #4
and r2, r2, #0xc0000000
str r2, [r0, #0x10]
bic r2, r2, #0xc0000000
b .Lbatch16a_00370a18_00370c98
.Lbatch16a_00370a18_00370b40:
str r7, [r4, #0x15c]
ldr r0, [r4, #0x158]
cmp r0, #0
cmpne r7, #0
orreq r8, r8, #0x80000000
mov r0, r8
pop {r4, r5, r6, r7, r8, sb, sl, pc}
.Lbatch16a_00370a18_00370b5c:
ldr r0, [r5]
mov r1, sb
ldr r2, [r0, #0xc]
mov r0, r5
blx r2
mov sb, r7
.Lbatch16a_00370a18_00370b74:
str sb, [r4, #0x158]
ldr r0, [r4, #0x218]
mov r2, #4
mov r1, #0x14
ldr r6, [r0, #4]
ldr r0, [r5]
ldr r3, [r0, #8]
mov r0, r5
blx r3
movs sb, r0
beq .Lbatch16a_00370a18_00370b40
ldr r0, [r5]
lsl r1, r6, #2
mov r2, #4
ldr r3, [r0, #8]
mov r0, r5
blx r3
movs r1, r0
beq .Lbatch16a_00370a18_00370bec
str r5, [sb]
str r1, [sb, #8]
str r5, [sb, #4]
str r1, [sb, #0xc]
ldr r1, [sb, #0x10]
mov r7, sb
and r1, r1, #0xc0000000
orr r1, r1, r6
bic r1, r1, #0xc0000000
str r1, [sb, #0x10]
b .Lbatch16a_00370a18_00370b40
.Lbatch16a_00370a18_00370bec:
ldr r0, [r5]
mov r1, sb
ldr r2, [r0, #0xc]
mov r0, r5
blx r2
b .Lbatch16a_00370a18_00370b40
.Lbatch16a_00370a18_00370c04:
ldr r0, [r5]
mov r2, #4
mov r1, #0x14
ldr r3, [r0, #8]
mov r0, r5
blx r3
cmp r0, #0
moveq r1, r7
beq .Lbatch16a_00370a18_00370c50
mov r1, r0
str r5, [r0], #4
mov r2, r5
stm r0, {r2, r7}
str r7, [r0, #8]
ldr r2, [r0, #0xc]
and r2, r2, #0xc0000000
bic r2, r2, #0xc0000000
orr r2, r2, #0x40000000
str r2, [r0, #0xc]
.Lbatch16a_00370a18_00370c50:
str r1, [r4, #0x158]
ldr r0, [r5]
mov r2, #4
mov r1, #0x14
ldr r3, [r0, #8]
mov r0, r5
blx r3
cmp r0, #0
beq .Lbatch16a_00370a18_00370b40
add r1, r0, #4
str r5, [r0]
stm r1, {r5, r7}
str r7, [r0, #0xc]
ldr r2, [r0, #0x10]
and r2, r2, #0xc0000000
str r2, [r0, #0x10]
bic r2, r2, #0xc0000000
orr r2, r2, #0x40000000
.Lbatch16a_00370a18_00370c98:
mov r7, r0
str r2, [r1, #0xc]
b .Lbatch16a_00370a18_00370b40
        )batch16"
    );
}
// DECOMP_FUNC(0x00375d28, 1032)
extern "C" __attribute__((naked)) void func_00375d28() {
    asm volatile(
        R"batch16(
push {r4, r5, r6, r7, r8, lr}
mov r4, r0
mov r5, #0
ldrb r0, [r0, #0x3c]
sub sp, sp, #0x28
mov r6, r1
cmp r0, #0
mov r8, #1
mov r7, r5
beq .Lbatch16a_00375d28_00376008
ldr r0, [r4, #0x44]
cmp r0, #0
beq .Lbatch16a_00375d28_00375ecc
ldr r1, [r6]
mov r2, #0x20
ldr r3, [r1, #8]
lsl r1, r0, #2
mov r0, r6
blx r3
movs r2, r0
orreq r5, r5, #0x80000000
ands r1, r5, #0x80000000
mov r0, r5
bmi .Lbatch16a_00375d28_00375ec4
ldr r1, [r4, #0x44]
add ip, sp, #0x10
mov r3, #0
str r2, [sp, #0x18]
str r2, [sp, #0x1c]
stm ip, {r3, r6}
add r0, r4, #0x14
ldr r2, [sp, #0x20]
and r2, r2, #0xc0000000
orr r1, r1, r2
bic r1, r1, #0xc0000000
str r1, [sp, #0x20]
str r3, [r4, #0x10]
ldr r2, [sp, #0x14]
mov r1, sp
cmp r0, r1
str r2, [sp]
ldr r2, [sp, #0x18]
str r2, [sp, #4]
ldr r2, [sp, #0x1c]
str r7, [sp, #0x18]
str r2, [sp, #8]
ldr r2, [sp, #0x20]
str r7, [sp, #0x1c]
str r2, [sp, #0xc]
and r2, r2, #0xc0000000
str r2, [sp, #0x20]
beq .Lbatch16a_00375d28_00375e20
vldmia sp, {s0, s1, s2, s3}
vldr s4, [r0, #4]
vstr s4, [sp, #4]
vldr s4, [r0, #8]
vstr s4, [sp, #8]
vldr s4, [r0, #0xc]
vstr s4, [sp, #0xc]
vldr s4, [r0]
vstr s4, [sp]
vstmia r0, {s0, s1, s2, s3}
.Lbatch16a_00375d28_00375e20:
ldr r0, [sp, #4]
str r0, [sp, #8]
ldr r0, [sp]
cmp r0, #0
ldrne r0, [sp, #4]
cmpne r0, #0
beq .Lbatch16a_00375d28_00375e50
ldr r0, [sp]
ldr r1, [sp, #4]
ldr r2, [r0]
ldr r2, [r2, #0xc]
blx r2
.Lbatch16a_00375d28_00375e50:
add r3, sp, #0x18
add ip, sp, #0x10
ldm r3, {r0, r2}
mov r1, #1
sub r2, r2, r0
add r3, r8, r2, asr #2
cmp r3, #1
addgt r3, r8, r2, asr #2
ble .Lbatch16a_00375d28_00375e90
.Lbatch16a_00375d28_00375e74:
ldr r2, [r0]
add r1, r1, #1
add r0, r0, #4
cmp r2, #0
strne r7, [r2, #0xc]
cmp r3, r1
bgt .Lbatch16a_00375d28_00375e74
.Lbatch16a_00375d28_00375e90:
ldr r1, [ip, #8]
add r0, ip, #4
str r1, [ip, #0xc]
ldr r2, [ip, #4]
cmp r2, #0
ldrne r1, [r0, #4]
cmpne r1, #0
beq .Lbatch16a_00375d28_00375ec0
.Lbatch16a_00375d28_00375eb0:
ldr r0, [r2]
ldr r3, [r0, #0xc]
mov r0, r2
blx r3
.Lbatch16a_00375d28_00375ec0:
mov r0, r5
.Lbatch16a_00375d28_00375ec4:
add sp, sp, #0x28
pop {r4, r5, r6, r7, r8, pc}
.Lbatch16a_00375d28_00375ecc:
ldr r0, [sp, #0x20]
mov r2, #0
str r2, [sp, #0x10]
and r0, r0, #0xc0000000
bic r0, r0, #0xc0000000
str r2, [sp, #0x14]
str r2, [sp, #0x18]
str r2, [sp, #0x1c]
str r0, [sp, #0x20]
str r7, [r4, #0x10]!
ldr r1, [sp, #0x14]
add r4, r4, #4
mov r0, sp
str r1, [sp]
ldr r1, [sp, #0x18]
cmp r4, r0
str r1, [sp, #4]
ldr r1, [sp, #0x1c]
str r7, [sp, #0x18]
str r1, [sp, #8]
ldr r1, [sp, #0x20]
str r7, [sp, #0x1c]
str r1, [sp, #0xc]
and r1, r1, #0xc0000000
str r1, [sp, #0x20]
beq .Lbatch16a_00375d28_00375f74
add r0, sp, #4
vldr s3, [r4, #4]
vldr s0, [sp]
add r1, r4, #4
vldmia r0, {s1, s2}
ldr r0, [sp, #0xc]
vstr s3, [sp, #4]
vldr s3, [r4, #8]
vstr s3, [sp, #8]
vldr s3, [r4, #0xc]
vstr s3, [sp, #0xc]
vldr s3, [r4]
vstr s3, [sp]
vstmia r1, {s1, s2}
str r0, [r4, #0xc]
vstr s0, [r4]
.Lbatch16a_00375d28_00375f74:
ldr r0, [sp, #4]
str r0, [sp, #8]
ldr r0, [sp]
cmp r0, #0
ldrne r0, [sp, #4]
cmpne r0, #0
beq .Lbatch16a_00375d28_00375fa4
ldr r0, [sp]
ldr r1, [sp, #4]
ldr r2, [r0]
ldr r2, [r2, #0xc]
blx r2
.Lbatch16a_00375d28_00375fa4:
add r3, sp, #0x18
add ip, sp, #0x10
ldm r3, {r0, r2}
mov r1, #1
sub r2, r2, r0
add r3, r8, r2, asr #2
cmp r3, #1
addgt r3, r8, r2, asr #2
ble .Lbatch16a_00375d28_00375fe4
.Lbatch16a_00375d28_00375fc8:
ldr r2, [r0]
add r1, r1, #1
add r0, r0, #4
cmp r2, #0
strne r7, [r2, #0xc]
cmp r3, r1
bgt .Lbatch16a_00375d28_00375fc8
.Lbatch16a_00375d28_00375fe4:
ldr r1, [ip, #8]
add r0, ip, #4
str r1, [ip, #0xc]
ldr r2, [ip, #4]
cmp r2, #0
ldrne r1, [r0, #4]
cmpne r1, #0
beq .Lbatch16a_00375d28_00375ec0
b .Lbatch16a_00375d28_00375eb0
.Lbatch16a_00375d28_00376008:
add r2, sp, #0x10
mov r0, #0
stm r2, {r0, r1, r7}
ldr r0, [sp, #0x20]
str r7, [sp, #0x1c]
and r0, r0, #0xc0000000
bic r0, r0, #0xc0000000
orr r0, r0, #0x40000000
str r0, [sp, #0x20]
ldr r0, [sp, #0x10]
str r0, [r4, #0x10]!
ldr r1, [sp, #0x14]
add r4, r4, #4
mov r0, sp
str r1, [sp]
ldr r1, [sp, #0x18]
cmp r4, r0
str r1, [sp, #4]
ldr r1, [sp, #0x1c]
str r7, [sp, #0x18]
str r1, [sp, #8]
ldr r1, [sp, #0x20]
str r7, [sp, #0x1c]
str r1, [sp, #0xc]
and r1, r1, #0xc0000000
str r1, [sp, #0x20]
beq .Lbatch16a_00375d28_0037609c
vldmia sp, {s0, s1, s2, s3}
vldr s4, [r4, #4]
vstr s4, [sp, #4]
vldr s4, [r4, #8]
vstr s4, [sp, #8]
vldr s4, [r4, #0xc]
vstr s4, [sp, #0xc]
vldr s4, [r4]
vstr s4, [sp]
vstmia r4, {s0, s1, s2, s3}
.Lbatch16a_00375d28_0037609c:
ldr r0, [sp, #4]
str r0, [sp, #8]
ldr r0, [sp]
cmp r0, #0
ldrne r0, [sp, #4]
cmpne r0, #0
beq .Lbatch16a_00375d28_003760cc
ldr r0, [sp]
ldr r1, [sp, #4]
ldr r2, [r0]
ldr r2, [r2, #0xc]
blx r2
.Lbatch16a_00375d28_003760cc:
add r3, sp, #0x18
add ip, sp, #0x10
ldm r3, {r0, r2}
mov r1, #1
sub r2, r2, r0
add r3, r8, r2, asr #2
cmp r3, #1
addgt r3, r8, r2, asr #2
ble .Lbatch16a_00375d28_0037610c
.Lbatch16a_00375d28_003760f0:
ldr r2, [r0]
add r1, r1, #1
add r0, r0, #4
cmp r2, #0
strne r7, [r2, #0xc]
cmp r3, r1
bgt .Lbatch16a_00375d28_003760f0
.Lbatch16a_00375d28_0037610c:
ldr r1, [ip, #8]
add r0, ip, #4
str r1, [ip, #0xc]
ldr r2, [ip, #4]
cmp r2, #0
ldrne r1, [r0, #4]
cmpne r1, #0
beq .Lbatch16a_00375d28_00375ec0
b .Lbatch16a_00375d28_00375eb0
        )batch16"
    );
}
