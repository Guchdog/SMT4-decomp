#include "types.h"

// DECOMP_FUNC(0x003603d4, 32)
extern "C" __attribute__((naked)) void func_003603d4() {
    asm volatile("strb r1, [r0, #5]\nldr r0, [r0, #0x68]\nmov r0, r0\nldrh r2, [r0, #0x6c]\nstrb r1, [r0, #0xe]\norr r1, r2, #0x20\nstrh r1, [r0, #0x6c]\nbx lr\n");
}

// DECOMP_FUNC(0x00379e08, 32)
extern "C" __attribute__((naked)) void func_00379e08() {
    asm volatile("add r1, r1, #1\nmul r1, r1, r1\nasr r2, r1, #0x1f\nadd r1, r1, r2, lsr #30\nlsl r1, r1, #0xe\nlsr r1, r1, #0x10\nstrh r1, [r0, #0x14]\nbx lr\n");
}

// DECOMP_FUNC(0x0037c46c, 32)
extern "C" __attribute__((naked)) void func_0037c46c() {
    asm volatile("ldrh r2, [r0, #0x20]\nmov r3, #1\nmov r1, #0\nstrb r3, [r0, #0x15]\norr r2, r2, #1\nstrb r1, [r0, #0x17]\nstrh r2, [r0, #0x20]\nbx lr\n");
}

// DECOMP_FUNC(0x0037fcc8, 32)
extern "C" __attribute__((naked)) void func_0037fcc8() {
    asm volatile("ldr r3, [r0, #0xf8]\nldr r2, [r0, #0xfc]\nadd r1, r1, r3\ncmp r1, r2\nstr r1, [r0, #0xf8]\nmovgt r1, r2\nstr r1, [r0, #0xf8]\nbx lr\n");
}

// DECOMP_FUNC(0x00396298, 32)
extern "C" __attribute__((naked)) void func_00396298() {
    asm volatile("vldmia sp, {s0, s1, s2}\nmov ip, #1\nstr r1, [r0, #0x78]\nstrb ip, [r0, #0x74]\nstrd r2, r3, [r0, #0x7c]\nadd r0, r0, #0x84\nvstmia r0, {s0, s1, s2}\nbx lr\n");
}

// DECOMP_FUNC(0x003e108c, 32)
extern "C" __attribute__((naked)) void func_003e108c() {
    asm volatile("vmov.f32 s2, s0\nvldr s4, [r0]\nvldr s1, [r0, #4]\nvldr s3, [r0, #8]\nvmul.f32 s0, s4, s2\nvmul.f32 s1, s1, s2\nvmul.f32 s2, s3, s2\nbx lr\n");
}

// DECOMP_FUNC(0x003e44e8, 32)
extern "C" __attribute__((naked)) void func_003e44e8() {
    asm volatile("vldmia r2, {s0, s1, s2, s3, s4, s5, s6, s7}\nadd r0, r1, #8\nadd r2, r2, #0x20\nadd r1, r1, #0x28\nvstmia r0, {s0, s1, s2, s3, s4, s5, s6, s7}\nvldmia r2, {s0, s1, s2, s3, s4, s5, s6, s7}\nvstmia r1, {s0, s1, s2, s3, s4, s5, s6, s7}\nbx lr\n");
}

// DECOMP_FUNC(0x003e46e8, 32)
extern "C" __attribute__((naked)) void func_003e46e8() {
    asm volatile("add r0, r2, #8\nadd r2, r2, #0x28\nvldmia r0, {s0, s1, s2, s3, s4, s5, s6, s7}\nvstmia r1, {s0, s1, s2, s3, s4, s5, s6, s7}\nadd r1, r1, #0x20\nvldmia r2, {s0, s1, s2, s3, s4, s5, s6, s7}\nvstmia r1, {s0, s1, s2, s3, s4, s5, s6, s7}\nbx lr\n");
}

// DECOMP_FUNC(0x003e8b00, 32)
extern "C" __attribute__((naked)) void func_003e8b00() {
    asm volatile("ldr r0, [r2, #8]!\nmov r3, #0\ncmp r0, #0\naddsne r0, r0, r2\nsubne r0, r0, r1\nstreq r3, [r1]\nstrne r0, [r1]\nbx lr\n");
}

// DECOMP_FUNC(0x00138330, 36)
extern "C" __attribute__((naked)) void engine_func_00138330() {
    asm volatile("mov r2, #0\nstr r2, [r1]\nldr r2, [r0]\ncmp r2, #4\nldreq r2, [r0, #0x18]\nstreq r2, [r1]\nldreq r0, [r0, #0xc]\nmovne r0, #0\nbx lr\n");
}

// DECOMP_FUNC(0x00147264, 36)
extern "C" __attribute__((naked)) void func_00147264() {
    asm volatile("ldr r0, [r0, #0x68]\nmov r0, r0\nmov r2, #0xc\nand r1, r2, r1, lsl #2\nldrh r2, [r0, #0x1e]\nbic r2, r2, #0xc\norr r1, r1, r2\nstrh r1, [r0, #0x1e]\nbx lr\n");
}

// DECOMP_FUNC(0x0022e2ec, 36)
extern "C" __attribute__((naked)) void unite_func_0022e2ec() {
    asm volatile("ldrsh r2, [r0]\nvldmia r1, {s0, s1, s2, s3, s4, s5, s6, s7}\nadd r2, r0, r2, lsl #5\nadd r2, r2, #4\nvstmia r2, {s0, s1, s2, s3, s4, s5, s6, s7}\nldrh r1, [r0]\nadd r1, r1, #1\nstrh r1, [r0]\nbx lr\n");
}

// DECOMP_FUNC(0x00237f10, 36)
extern "C" __attribute__((naked)) void func_00237f10() {
    asm volatile("mov r2, #0\nmov r1, #1\nstr r2, [r0]\nstrb r1, [r0, #4]\nadd r1, r0, #8\nstr r1, [r0, #8]\nstr r2, [r0, #0x10]\nstr r1, [r0, #0xc]\nbx lr\n");
}

// DECOMP_FUNC(0x002a4b88, 36)
extern "C" __attribute__((naked)) void func_002a4b88() {
    asm volatile("sub r0, r0, #0x1400\nsubs r0, r0, #6\nmov r0, #1\nmoveq r0, #4\nmul r0, r1, r0\nadd r1, r2, #0x1f\nbic r1, r1, #0x1f\nadd r0, r0, r1\nbx lr\n");
}

struct QueueNode_002b5124 {
    QueueNode_002b5124* volatile next;
};
struct Queue_002b5124 {
    u8 pad[0x16c];
    QueueNode_002b5124* volatile head;
    QueueNode_002b5124* volatile tail;
    volatile u32 result;
};
// DECOMP_FUNC(0x002b5124, 36)
extern "C" u32 engine_func_002b5124(void* queue_data, void* node_data) {
    Queue_002b5124* const queue = static_cast<Queue_002b5124*>(queue_data);
    QueueNode_002b5124* const node = static_cast<QueueNode_002b5124*>(node_data);
    QueueNode_002b5124* tail = queue->tail;
    if (tail == 0) {
        queue->head = node;
    } else {
        tail->next = node;
    }
    queue->tail = node;
    node->next = 0;
    return queue->result;
}

// DECOMP_FUNC(0x002bd448, 36)
extern "C" void engine_func_002bd448(volatile u8* voice) {
    *reinterpret_cast<volatile u32*>(voice) = 0;
    *reinterpret_cast<volatile u32*>(voice + 4) = 0;
    *reinterpret_cast<volatile u32*>(voice + 8) = 0;
    *reinterpret_cast<volatile u32*>(voice + 0x0c) = 0;
    *reinterpret_cast<volatile u32*>(voice + 0x10) = 0;
    *reinterpret_cast<volatile u32*>(voice + 0x14) = 0;
    voice[0x11] = 0;
}

// DECOMP_FUNC(0x002bf774, 36)
extern "C" __attribute__((naked)) void engine_func_002bf774() {
    asm volatile("ldr r3, [r1, #4]\nstm r2, {r1, r3}\nstr r2, [r1, #4]\nstr r2, [r3]\nldr r1, [r0]\nadd r1, r1, #1\nstr r1, [r0]\nmov r0, r2\nbx lr\n");
}

// DECOMP_FUNC(0x002cffd4, 36)
extern "C" __attribute__((naked)) void camp_func_002cffd4() {
    asm volatile("add r0, r0, #0x3000\nldr r0, [r0, #0x48]\ncmp r0, #6\nmoveq r0, #1\nmovne r0, #0\nbx lr\nadd r0, r0, #0x3000\nstrb r1, [r0, #0x80]\nbx lr\n");
}

// DECOMP_FUNC(0x003105dc, 36)
extern "C" __attribute__((naked)) void func_003105dc() {
    asm volatile("cmp r0, #1\nmov ip, #1\nmoveq ip, #0\norr ip, ip, r0, lsl #4\nand r0, r3, #0xff\norr r0, ip, r0, lsl #8\norr r0, r0, r1, lsl #16\norr r0, r0, r2, lsl #24\nbx lr\n");
}

// DECOMP_FUNC(0x0034daa8, 36)
extern "C" __attribute__((naked)) void func_0034daa8() {
    asm volatile("ldr r0, [r0, #4]\nadd r2, r1, r1, lsl #2\nadd r1, r2, r1, lsl #6\nadd r0, r0, #0x1c00\nadd r0, r0, #0x298\nldr r0, [r0]\nadd r0, r0, r1, lsl #2\nvldr s0, [r0, #0x28]\nbx lr\n");
}

// DECOMP_FUNC(0x00352950, 36)
extern "C" __attribute__((naked)) void engine_func_00352950() {
    asm volatile("push {r4, r5, r6, lr}\nmov r5, r2\nmov r4, r3\nstr r1, [r0]\nadd r2, r0, #4\nmov r1, #0\nstr r4, [r0, #0xc]\nstm r2, {r1, r5}\npop {r4, r5, r6, pc}\n");
}

// DECOMP_FUNC(0x003530f8, 36)
extern "C" __attribute__((naked)) void engine_func_003530f8() {
    asm volatile("push {r4, r5, r6, lr}\nmov r5, r2\nmov r4, r3\nstr r1, [r0]\nadd r2, r0, #4\nmov r1, #0\nstr r4, [r0, #0xc]\nstm r2, {r1, r5}\npop {r4, r5, r6, pc}\n");
}

// DECOMP_FUNC(0x00354d28, 36)
extern "C" __attribute__((naked)) void script_vm_func_00354d28() {
    asm volatile("push {r4, r5, r6, lr}\nmov r5, r2\nmov r4, r3\nstr r1, [r0]\nadd r2, r0, #4\nmov r1, #0\nstr r4, [r0, #0xc]\nstm r2, {r1, r5}\npop {r4, r5, r6, pc}\n");
}

// DECOMP_FUNC(0x0035c23c, 36)
extern "C" __attribute__((naked)) void func_0035c23c() {
    asm volatile("mov r1, #0\nstr r1, [r0, #8]\nstr r0, [r0]\nstr r1, [r0, #0xc]\nstr r1, [r0, #0x10]\nstr r1, [r0, #0x14]\nstr r1, [r0, #0x18]\nstr r0, [r0, #4]\nbx lr\n");
}

// DECOMP_FUNC(0x0035e794, 36)
extern "C" __attribute__((naked)) void func_0035e794() {
    asm volatile("mov r2, #0\nadd r1, r0, #4\nstr r2, [r0]\nstr r1, [r0, #4]\nstr r2, [r0, #0xc]\nstr r1, [r0, #8]\nstr r2, [r0, #0x10]\nstr r2, [r0, #0x14]\nbx lr\n");
}

// DECOMP_FUNC(0x003c2c58, 36)
extern "C" __attribute__((naked)) void engine_func_003c2c58() {
    asm volatile("mov r2, #0\nstrb r1, [r0, #0xc]\nstr r2, [r0, #4]\nstrb r2, [r0, #8]\nstrb r2, [r0, #9]\nstrb r2, [r0, #0xa]\nstrb r2, [r0, #0xb]\nstrb r2, [r0]\nbx lr\n");
}

// DECOMP_FUNC(0x003dccd8, 36)
extern "C" __attribute__((naked)) void func_003dccd8() {
    asm volatile("add r0, r0, #0x3000\nadd ip, r0, #0x2c\nldr r3, [r0, #0x28]\nmov r2, #0\nstm ip, {r1, r2}\nbic r1, r3, #0xe0\norr r1, r1, #0x10\nstr r1, [r0, #0x28]\nbx lr\n");
}

// DECOMP_FUNC(0x003eab5c, 36)
extern "C" __attribute__((naked)) void func_003eab5c() {
    asm volatile("ldr r2, [r0, #0x34]!\nldr r3, [r0, #8]!\nldr r1, [r0, #4]\ncmp r1, r3\nsubhs r0, r1, r3\naddhs r0, r2, r0, lsl #4\naddlo r0, r2, r1, lsl #4\nldr r0, [r0, #4]\nbx lr\n");
}

// DECOMP_FUNC(0x003f7394, 36)
extern "C" __attribute__((naked)) void func_003f7394() {
    asm volatile("mov r2, #0\nmov r1, #1\nstr r2, [r0]\nstrb r1, [r0, #4]\nadd r1, r0, #8\nstr r1, [r0, #8]\nstr r2, [r0, #0x10]\nstr r1, [r0, #0xc]\nbx lr\n");
}

// DECOMP_FUNC(0x001384d0, 40)
extern "C" __attribute__((naked)) void func_001384d0() {
    asm volatile("ldr r0, [pc, #4]\nvldr s0, [r0]\nbx lr\n.word 0x00464a98\nldrh r0, [r0, #0x60]\nldrh r1, [r1, #0x60]\nsub r0, r0, r1\nbx lr\nstrb r1, [r0, #0x85]\nbx lr\n");
}

// DECOMP_FUNC(0x00211ee4, 40)
extern "C" __attribute__((naked)) void func_00211ee4() {
    asm volatile("ldr r3, [r0, #0x10]\nldr r1, [r0, #0x18]\nldr r2, [r0, #0x1c]\nldr r0, [r0, #0x14]\neor r1, r1, r3\neor r0, r0, r2\norrs r0, r0, r1\nmoveq r0, #1\nmovne r0, #0\nbx lr\n");
}

// DECOMP_FUNC(0x0023af8c, 40)
extern "C" __attribute__((naked)) void engine_func_0023af8c() {
    asm volatile("ldm r2, {r1, r3}\nldr r0, [r0, #0x2c]\nldr r2, [r2, #8]\nadd ip, r0, #0x7c\nstr r2, [r0, #0x84]\nstm ip, {r1, r3}\nldr r1, [r0, #0x88]\norr r1, r1, #0x800\nstr r1, [r0, #0x88]\nbx lr\n");
}

// DECOMP_FUNC(0x0028c8a8, 40)
extern "C" __attribute__((naked)) void engine_func_0028c8a8() {
    asm volatile("ldr r0, [r0, #0x2c]\nldr r3, [r2]\nldmib r2, {r1, r2}\nstr r1, [r0, #0x68]\nstr r2, [r0, #0x78]\nstr r3, [r0, #0x58]\nldr r1, [r0, #0x88]\norr r1, r1, #0x800\nstr r1, [r0, #0x88]\nbx lr\n");
}
