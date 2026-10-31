#include <cstdint>

typedef uint32_t u32;
typedef int32_t  s32;
typedef uint8_t  u8;

extern "C" {
    void* AsdMem_Alloc_002c54f0(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void  camp_func_00289b4c();
    void  camp_func_0028d974();
    void  camp_func_00289ae8();
    void  camp_func_002b8b78(u32 id);
    void* AsdRes_Load_002c5e2c(const char* path);
    void* FlowScript_Create_002972f8(void* bf, u32 flag);
    void  FlowScript_Helper_002971e4(void* proc, u32 flag);
    void  camp_func_00282e6c(u32 screen, u32 mode);
    void* AsdTask_Create_002c5978(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);

    extern void* g_OnesRoomManager_0044d1c8[];
}

extern "C" void h7_script_onesroom_init_candidate(void* arg0, s32 arg1) {
    u8* work = static_cast<u8*>(AsdMem_Alloc_002c54f0(0x100, 0x7D, 0, 0x14, 1));
    g_OnesRoomManager_0044d1c8[0] = work;

    if (!work) return;

    for (u32 i = 0; i < 5; ++i) {
        reinterpret_cast<u32*>(work)[i] = 0;
    }
    if (!arg0) {
        work[0x10] = 1;
    }

    camp_func_00289b4c();
    camp_func_0028d974();
    camp_func_00289ae8();
    camp_func_002b8b78(0xA2);

    void* bf = AsdRes_Load_002c5e2c("ones_room/onesRoom.bf");
    *reinterpret_cast<void**>(work + 4) = bf;

    void* bmd = AsdRes_Load_002c5e2c("ones_room/onesRoom.mbm");
    *reinterpret_cast<void**>(work + 0xC) = bmd;

    void* proc = FlowScript_Create_002972f8(bf, 2);
    *reinterpret_cast<void**>(work + 8) = proc;
    if (proc) {
        *reinterpret_cast<u32*>(static_cast<u8*>(proc) + 0x108) = 2;
        FlowScript_Helper_002971e4(proc, 0);
    }

    work[0x11] = 0;
    if (work[0x10]) {
        camp_func_00282e6c(0, 0xFF);
        camp_func_00282e6c(1, 0xFF);
    }

    void* task = AsdTask_Create_002c5978("onesRoom C", 2, 0, 0, reinterpret_cast<void*>(0x001FC4BC), work, 0);
    *reinterpret_cast<void**>(work) = task;
}

extern "C" void h7_script_onesroom_init_mutation(void* arg0, s32 arg1) {
    g_OnesRoomManager_0044d1c8[0] = reinterpret_cast<void*>(0xDEADBEEF);
}
