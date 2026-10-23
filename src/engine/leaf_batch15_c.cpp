#include "types.h"

// DECOMP_FUNC(0x00376954, 52)
extern "C" __attribute__((naked)) void func_00376954() {
    asm volatile("push {r4, lr}\nsub sp, sp, #8\nstrb r3, [sp, #4]\nadd r3, sp, #4\nstr r3, [sp]\nldr r3, [r0]\nldr r4, [sp, #0x10]\nldr ip, [r3, #0x10]\nmov r3, r4\nblx ip\nadd sp, sp, #8\nand r0, r0, #0xff\npop {r4, pc}\n");
}

// DECOMP_FUNC(0x001db500, 56)
extern "C" __attribute__((naked)) void script_vm_func_001db500() {
    asm volatile("cmp r1, #3\nbls .L_001db500_001db534\nlsl r3, r1, #0x1d\nsub r0, r0, #4\ncmp r3, #0\nmov r2, #0\nstrlt r2, [r0, #4]!\nlsrs r1, r1, #3\nbeq .L_001db500_001db534\n.L_001db500_001db524:\nstr r2, [r0, #4]\nsubs r1, r1, #1\nstr r2, [r0, #8]!\nbne .L_001db500_001db524\n.L_001db500_001db534:\nbx lr\n");
}

// DECOMP_FUNC(0x0037734c, 56)
extern "C" __attribute__((naked)) void func_0037734c() {
    asm volatile("push {r3, r4, r5, lr}\nmov ip, r0\nldr r0, [r0, #0x18]\nmov r5, r2\nmov r2, r1\ncmp r0, #0\nbeq .L_0037734c_00377380\nstr r3, [sp]\nldr r1, [r0]\nmov r3, r5\nldr r4, [r1, #8]\nmov r1, ip\nblx r4\n.L_0037734c_00377380:\npop {r3, r4, r5, pc}\n");
}

// DECOMP_FUNC(0x00381398, 56)
extern "C" __attribute__((naked)) void func_00381398() {
    asm volatile("ldr r2, [r0]\nldrb r1, [r2]\nsub r3, r1, #0x81\ncmp r3, #0x1f\nblo .L_00381398_003813b8\ncmp r1, #0xe0\naddlo r2, r2, #1\nblo .L_00381398_003813c4\n.L_00381398_003813b8:\nldrb r3, [r2, #1]\nadd r2, r2, #2\norr r1, r3, r1, lsl #8\n.L_00381398_003813c4:\nstr r2, [r0]\nmov r0, r1\nbx lr\n");
}

// DECOMP_FUNC(0x00147994, 60)
extern "C" __attribute__((naked)) void func_00147994() {
    asm volatile("mov r0, r0\nadd r1, r0, #0xec000000\ncmp r1, #0x8000000\nmov r1, #0\naddlo r1, r0, #0xc000000\nblo .L_00147994_001479c8\nadd r2, r0, #0xe1000000\ncmp r2, #0x600000\nblo .L_00147994_001479c4\nadd r2, r0, #0xf0000000\nsubs r2, r2, #0xf600000\nbne .L_00147994_001479c8\n.L_00147994_001479c4:\nadd r1, r0, #0xf9000000\n.L_00147994_001479c8:\nmov r0, r1\nbx lr\n");
}

// DECOMP_FUNC(0x00157f44, 60)
extern "C" __attribute__((naked)) void func_00157f44() {
    asm volatile("mov r2, #0\nb .L_00157f44_00157f68\n.L_00157f44_00157f4c:\ntst r1, #1\nbeq .L_00157f44_00157f60\nadd r3, r0, r2, lsl #5\nadd r3, r3, #0x1800\nvstr s0, [r3, #0x2f0]\n.L_00157f44_00157f60:\nadd r2, r2, #1\nlsr r1, r1, #1\n.L_00157f44_00157f68:\nldr r3, [r0, #0xd4]\ncmp r3, r2\nbls .L_00157f44_00157f7c\ncmp r1, #0\nbne .L_00157f44_00157f4c\n.L_00157f44_00157f7c:\nbx lr\n");
}

// DECOMP_FUNC(0x001580ec, 60)
extern "C" __attribute__((naked)) void func_001580ec() {
    asm volatile("mov r2, #0\nb .L_001580ec_00158110\n.L_001580ec_001580f4:\ntst r1, #1\nbeq .L_001580ec_00158108\nadd r3, r0, r2, lsl #5\nadd r3, r3, #0x1800\nvstr s0, [r3, #0x2ec]\n.L_001580ec_00158108:\nadd r2, r2, #1\nlsr r1, r1, #1\n.L_001580ec_00158110:\nldr r3, [r0, #0xd4]\ncmp r3, r2\nbls .L_001580ec_00158124\ncmp r1, #0\nbne .L_001580ec_001580f4\n.L_001580ec_00158124:\nbx lr\n");
}

// DECOMP_FUNC(0x00158128, 60)
extern "C" __attribute__((naked)) void func_00158128() {
    asm volatile("mov r2, #0\nb .L_00158128_0015814c\n.L_00158128_00158130:\ntst r1, #1\nbeq .L_00158128_00158144\nadd r3, r0, r2, lsl #5\nadd r3, r3, #0x1800\nvstr s0, [r3, #0x2f4]\n.L_00158128_00158144:\nadd r2, r2, #1\nlsr r1, r1, #1\n.L_00158128_0015814c:\nldr r3, [r0, #0xd4]\ncmp r3, r2\nbls .L_00158128_00158160\ncmp r1, #0\nbne .L_00158128_00158130\n.L_00158128_00158160:\nbx lr\n");
}

// DECOMP_FUNC(0x0023d51c, 60)
extern "C" __attribute__((naked)) void engine_func_0023d51c() {
    asm volatile("push {r4, lr}\nldr r0, [r0, #0x258]\nmov r4, r1\nldr r1, [r0]\nldr r1, [r1, #0x10]\nblx r1\ncmp r0, #0\nbeq .L_0023d51c_0023d548\nldr r1, [r0]\ntst r1, #0x20000000\nmoveq r0, #0\n.L_0023d51c_0023d548:\nldm r4, {r1, r2, r3}\nadd r0, r0, #8\nstm r0, {r1, r2, r3}\npop {r4, pc}\n");
}

// DECOMP_FUNC(0x002de8fc, 60)
extern "C" __attribute__((naked)) void func_002de8fc() {
    asm volatile("ldr r1, [r0, #0x40]\nldrb r2, [r1, #0x54]\nldr r0, [r1, #0x34]\nldr r1, [r1, #0x4c]\ncmp r2, #0\nmovne r0, #0\nbne .L_002de8fc_002de934\ncmp r0, #0\nbeq .L_002de8fc_002de930\ncmp r1, #0\nmoveq r0, #1\ncmpne r0, r1\nble .L_002de8fc_002de934\n.L_002de8fc_002de930:\nmov r0, r1\n.L_002de8fc_002de934:\nbx lr\n");
}

// DECOMP_FUNC(0x0034244c, 60)
extern "C" __attribute__((naked)) void func_0034244c() {
    asm volatile("push {r4, r5, r6, lr}\nmov r4, r0\nldr r0, [r0, #8]\nmov r6, r1\nmov r5, r2\nldr r1, [r0, #4]\nldr r0, [r4, #4]\nblx r1\nstr r0, [r5]\nldr r0, [r4, #8]\nmov r1, r6\nldr r2, [r0, #8]\nldr r0, [r4, #4]\npop {r4, r5, r6, lr}\nbx r2\n");
}

// DECOMP_FUNC(0x00377310, 60)
extern "C" __attribute__((naked)) void func_00377310() {
    asm volatile("mov ip, r0\npush {r4, lr}\nldr r0, [r0, #0x18]\nmov r3, r2\nmov r2, r1\ncmp r0, #0\nmov r1, #0\nbeq .L_00377310_00377344\nldr r1, [r0]\nldr r4, [r1, #0xc]\nmov r1, ip\nblx r4\nmov r1, r0\n.L_00377310_00377344:\nmov r0, r1\npop {r4, pc}\n");
}

// DECOMP_FUNC(0x003b3524, 60)
extern "C" __attribute__((naked)) void func_003b3524() {
    asm volatile("cmp r2, #0x14\nmvnlo r0, #0\nblo .L_003b3524_003b355c\nldr r2, [r1]\nstr r2, [r0, #0xc]\nldr r2, [r1, #4]\nstr r2, [r0, #0x10]\nldr r2, [r1, #8]\nstr r2, [r0, #0x14]\nldr r2, [r1, #0xc]\nstr r2, [r0, #0x18]\nldr r1, [r1, #0x10]\nstr r1, [r0, #0x1c]\nmov r0, #0x14\n.L_003b3524_003b355c:\nbx lr\n");
}

// DECOMP_FUNC(0x0022cac4, 64)
extern "C" __attribute__((naked)) void script_vm_func_0022cac4() {
    asm volatile("mov r3, r0\nmvn r0, #0\nmov r2, #0\n.L_0022cac4_0022cad0:\nadd ip, r3, r2, lsl #1\nadd ip, ip, #0x2f00\nldrsh ip, [ip, #6]\ncmp ip, #0\naddge r0, r0, #1\nsxthge r0, r0\ncmp ip, r1\nbeq .L_0022cac4_0022cb00\nadd r2, r2, #1\ncmp r2, #0xc\nblt .L_0022cac4_0022cad0\nmvn r0, #0\n.L_0022cac4_0022cb00:\nbx lr\n");
}

// DECOMP_FUNC(0x002f9820, 64)
extern "C" __attribute__((naked)) void func_002f9820() {
    asm volatile("ldrd r0, r1, [r0, #0x3c]\nldr r2, [r1, #0x38]\nldr r0, [r0]\ncmp r2, #0\nble .L_002f9820_002f985c\nsub r0, r0, #0x2c\ntst r2, #1\nmvn r1, #0\nstrne r1, [r0, #0x2c]!\nasrs r2, r2, #1\nbeq .L_002f9820_002f985c\n.L_002f9820_002f984c:\nstr r1, [r0, #0x2c]\nsubs r2, r2, #1\nstr r1, [r0, #0x58]!\nbne .L_002f9820_002f984c\n.L_002f9820_002f985c:\nbx lr\n");
}

// DECOMP_FUNC(0x0030348c, 64)
extern "C" __attribute__((naked)) void func_0030348c() {
    asm volatile("ldrd r0, r1, [r0, #0x3c]\nldr r2, [r1, #0x38]\nldr r0, [r0]\ncmp r2, #0\nble .L_0030348c_003034c8\nsub r0, r0, #0x1c\ntst r2, #1\nmvn r1, #0\nstrne r1, [r0, #0x1c]!\nasrs r2, r2, #1\nbeq .L_0030348c_003034c8\n.L_0030348c_003034b8:\nstr r1, [r0, #0x1c]\nsubs r2, r2, #1\nstr r1, [r0, #0x38]!\nbne .L_0030348c_003034b8\n.L_0030348c_003034c8:\nbx lr\n");
}

// DECOMP_FUNC(0x00314640, 64)
extern "C" __attribute__((naked)) void func_00314640() {
    asm volatile("ldrd r0, r1, [r0, #0x3c]\nldr r2, [r1, #0x38]\nldr r0, [r0]\ncmp r2, #0\nble .L_00314640_0031467c\nsub r0, r0, #0x18\ntst r2, #1\nmvn r1, #0\nstrne r1, [r0, #0x18]!\nasrs r2, r2, #1\nbeq .L_00314640_0031467c\n.L_00314640_0031466c:\nstr r1, [r0, #0x18]\nsubs r2, r2, #1\nstr r1, [r0, #0x30]!\nbne .L_00314640_0031466c\n.L_00314640_0031467c:\nbx lr\n");
}

// DECOMP_FUNC(0x003153fc, 64)
extern "C" __attribute__((naked)) void func_003153fc() {
    asm volatile("ldrd r0, r1, [r0, #0x3c]\nldr r2, [r1, #0x38]\nldr r0, [r0]\ncmp r2, #0\nble .L_003153fc_00315438\nsub r0, r0, #0x28\ntst r2, #1\nmvn r1, #0\nstrne r1, [r0, #0x28]!\nasrs r2, r2, #1\nbeq .L_003153fc_00315438\n.L_003153fc_00315428:\nstr r1, [r0, #0x28]\nsubs r2, r2, #1\nstr r1, [r0, #0x50]!\nbne .L_003153fc_00315428\n.L_003153fc_00315438:\nbx lr\n");
}

// DECOMP_FUNC(0x00319b7c, 64)
extern "C" __attribute__((naked)) void func_00319b7c() {
    asm volatile("ldrd r0, r1, [r0, #0x3c]\nldr r2, [r1, #0x38]\nldr r0, [r0]\ncmp r2, #0\nble .L_00319b7c_00319bb8\nsub r0, r0, #0x2c\ntst r2, #1\nmvn r1, #0\nstrne r1, [r0, #0x2c]!\nasrs r2, r2, #1\nbeq .L_00319b7c_00319bb8\n.L_00319b7c_00319ba8:\nstr r1, [r0, #0x2c]\nsubs r2, r2, #1\nstr r1, [r0, #0x58]!\nbne .L_00319b7c_00319ba8\n.L_00319b7c_00319bb8:\nbx lr\n");
}

// DECOMP_FUNC(0x0031a968, 64)
extern "C" __attribute__((naked)) void func_0031a968() {
    asm volatile("ldrd r0, r1, [r0, #0x3c]\nldr r2, [r1, #0x38]\nldr r0, [r0]\ncmp r2, #0\nble .L_0031a968_0031a9a4\nsub r0, r0, #0x18\ntst r2, #1\nmvn r1, #0\nstrne r1, [r0, #0x18]!\nasrs r2, r2, #1\nbeq .L_0031a968_0031a9a4\n.L_0031a968_0031a994:\nstr r1, [r0, #0x18]\nsubs r2, r2, #1\nstr r1, [r0, #0x30]!\nbne .L_0031a968_0031a994\n.L_0031a968_0031a9a4:\nbx lr\n");
}

// DECOMP_FUNC(0x003205cc, 64)
extern "C" __attribute__((naked)) void func_003205cc() {
    asm volatile("ldrd r0, r1, [r0, #0x3c]\nldr r2, [r1, #0x38]\nldr r0, [r0]\ncmp r2, #0\nble .L_003205cc_00320608\nsub r0, r0, #0x18\ntst r2, #1\nmvn r1, #0\nstrne r1, [r0, #0x18]!\nasrs r2, r2, #1\nbeq .L_003205cc_00320608\n.L_003205cc_003205f8:\nstr r1, [r0, #0x18]\nsubs r2, r2, #1\nstr r1, [r0, #0x30]!\nbne .L_003205cc_003205f8\n.L_003205cc_00320608:\nbx lr\n");
}

// DECOMP_FUNC(0x00321550, 64)
extern "C" __attribute__((naked)) void func_00321550() {
    asm volatile("ldrd r0, r1, [r0, #0x3c]\nldr r2, [r1, #0x38]\nldr r0, [r0]\ncmp r2, #0\nble .L_00321550_0032158c\nsub r0, r0, #0x20\ntst r2, #1\nmvn r1, #0\nstrne r1, [r0, #0x20]!\nasrs r2, r2, #1\nbeq .L_00321550_0032158c\n.L_00321550_0032157c:\nstr r1, [r0, #0x20]\nsubs r2, r2, #1\nstr r1, [r0, #0x40]!\nbne .L_00321550_0032157c\n.L_00321550_0032158c:\nbx lr\n");
}

// DECOMP_FUNC(0x0035b294, 64)
extern "C" __attribute__((naked)) void func_0035b294() {
    asm volatile("ldr r3, [r0, #0x18]\nldr r2, [r1]\ncmp r3, #0\nmovle r1, #0xd\nstrble r1, [r2, #8]\nble .L_0035b294_0035b2c0\nmov ip, #0\nstrb ip, [r2, #8]\nldr r1, [r1]\nmov r3, #0x2b\nstrh r3, [r1, #0xa]\n.L_0035b294_0035b2c0:\nldr r1, [r0, #0x10]\nadd r1, r1, #1\nstr r1, [r0, #0x10]\nmov r0, #0\nbx lr\n");
}

// DECOMP_FUNC(0x0035bbf8, 64)
extern "C" __attribute__((naked)) void func_0035bbf8() {
    asm volatile("ldr r3, [r0, #0x18]\nldr r2, [r1]\ncmp r3, #0\nmovle r1, #0xc\nstrble r1, [r2, #8]\nble .L_0035bbf8_0035bc24\nmov ip, #0\nstrb ip, [r2, #8]\nldr r1, [r1]\nmov r3, #0x2a\nstrh r3, [r1, #0xa]\n.L_0035bbf8_0035bc24:\nldr r1, [r0, #0x10]\nadd r1, r1, #1\nstr r1, [r0, #0x10]\nmov r0, #0\nbx lr\n");
}

// DECOMP_FUNC(0x0035bc38, 64)
extern "C" __attribute__((naked)) void func_0035bc38() {
    asm volatile("ldr r3, [r0, #0x18]\nldr r2, [r1]\ncmp r3, #0\nmovle r1, #0xb\nstrble r1, [r2, #8]\nble .L_0035bc38_0035bc64\nmov ip, #0\nstrb ip, [r2, #8]\nldr r1, [r1]\nmov r3, #0x3f\nstrh r3, [r1, #0xa]\n.L_0035bc38_0035bc64:\nldr r1, [r0, #0x10]\nadd r1, r1, #1\nstr r1, [r0, #0x10]\nmov r0, #0\nbx lr\n");
}

// DECOMP_FUNC(0x0035bfcc, 64)
extern "C" __attribute__((naked)) void func_0035bfcc() {
    asm volatile("ldr r3, [r0, #0x18]\nldr r2, [r1]\ncmp r3, #0\nmovle r1, #1\nstrble r1, [r2, #8]\nble .L_0035bfcc_0035bff8\nmov ip, #0\nstrb ip, [r2, #8]\nldr r1, [r1]\nmov r3, #0x7c\nstrh r3, [r1, #0xa]\n.L_0035bfcc_0035bff8:\nldr r1, [r0, #0x10]\nadd r1, r1, #1\nstr r1, [r0, #0x10]\nmov r0, #0\nbx lr\n");
}

// DECOMP_FUNC(0x0035c128, 64)
extern "C" __attribute__((naked)) void func_0035c128() {
    asm volatile("ldr r3, [r0, #0x18]\nldr r2, [r1]\ncmp r3, #0\nmovle r1, #9\nstrble r1, [r2, #8]\nble .L_0035c128_0035c154\nmov ip, #0\nstrb ip, [r2, #8]\nldr r1, [r1]\nmov r3, #0x28\nstrh r3, [r1, #0xa]\n.L_0035c128_0035c154:\nldr r1, [r0, #0x10]\nadd r1, r1, #1\nstr r1, [r0, #0x10]\nmov r0, #0\nbx lr\n");
}

// DECOMP_FUNC(0x0035c168, 64)
extern "C" __attribute__((naked)) void func_0035c168() {
    asm volatile("ldr r3, [r0, #0x18]\nldr r2, [r1]\ncmp r3, #0\nmovle r1, #0xa\nstrble r1, [r2, #8]\nble .L_0035c168_0035c194\nmov ip, #0\nstrb ip, [r2, #8]\nldr r1, [r1]\nmov r3, #0x29\nstrh r3, [r1, #0xa]\n.L_0035c168_0035c194:\nldr r1, [r0, #0x10]\nadd r1, r1, #1\nstr r1, [r0, #0x10]\nmov r0, #0\nbx lr\n");
}

// DECOMP_FUNC(0x00360394, 64)
extern "C" __attribute__((naked)) void func_00360394() {
    asm volatile("push {r4, r5, r6, lr}\nmov r4, r0\nadd r5, r0, #4\nldr r0, [r0, #4]\nmov r6, #0\ncmp r0, #0\nbeq .L_00360394_003603b8\nsvc #0x23\nstr r6, [r5]\n.L_00360394_003603b8:\nldr r0, [r4]\ncmp r0, #0\nbeq .L_00360394_003603cc\nsvc #0x23\nstr r6, [r4]\n.L_00360394_003603cc:\nmov r0, r4\npop {r4, r5, r6, pc}\n");
}

// DECOMP_FUNC(0x003715e4, 64)
extern "C" __attribute__((naked)) void func_003715e4() {
    asm volatile("push {r4, r5, r6, lr}\nmov r5, r1\nmov r0, r1\nldr r1, [r2]\nmov r4, r2\nldr r2, [r0]\ncmp r1, #0\naddne r1, r1, r4\nldr r2, [r2, #0xc]\nblx r2\nldr r2, [r5]\nmov r0, r5\nmov r1, r4\nldr r2, [r2, #0xc]\npop {r4, r5, r6, lr}\nbx r2\n");
}

// DECOMP_FUNC(0x002b7af0, 68)
extern "C" __attribute__((naked)) void engine_func_002b7af0() {
    asm volatile("cmp r2, #3\nbls .L_002b7af0_002b7b30\nlsls r3, r2, #0x1d\nsub r0, r0, #4\nsub r1, r1, #4\nbpl .L_002b7af0_002b7b10\nldr r3, [r0, #4]!\nstr r3, [r1, #4]!\n.L_002b7af0_002b7b10:\nlsrs r2, r2, #3\nbeq .L_002b7af0_002b7b30\n.L_002b7af0_002b7b18:\nldr r3, [r0, #4]\nsubs r2, r2, #1\nstr r3, [r1, #4]\nldr r3, [r0, #8]!\nstr r3, [r1, #8]!\nbne .L_002b7af0_002b7b18\n.L_002b7af0_002b7b30:\nbx lr\n");
}

// DECOMP_FUNC(0x00361bac, 68)
extern "C" __attribute__((naked)) void func_00361bac() {
    asm volatile("cmp r1, #0\nstr r4, [sp, #-4]!\nbeq .L_00361bac_00361be4\nldr r3, [r0, #4]\nmov r2, #0\nadd r1, r1, r3\nldr r3, [r0]\nsubs r4, r3, r1\nsbcs ip, r2, r2\nmovlt r1, r3\nblt .L_00361bac_00361be0\ncmp r2, #0\nmovlt r1, #0\n.L_00361bac_00361be0:\nstr r1, [r0, #4]\n.L_00361bac_00361be4:\nldr r0, [r0, #4]\npop {r4}\nbx lr\n");
}

// DECOMP_FUNC(0x0015f714, 52)
extern "C" __attribute__((naked)) void func_0015f714() {
    asm volatile("str lr, [sp, #-4]!\nbics r3, r1, #1\naddne r1, r1, #1\nlsl r3, r1, #2\nsub sp, sp, r3\nmov r1, sp\nstr r3, [sp, #-4]!\nblx r2\npop {r3}\nadd sp, sp, r3\npop {pc}\nsvc #0x23\nbx lr\n");
}
