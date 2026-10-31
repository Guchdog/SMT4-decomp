#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

typedef void (*VFunc0)(void*);
typedef void (*VFuncFree)(void*, void*);

struct TerminalContext {
    void* vptr;          // 0x00
    void* sub_objs[2];   // 0x04, 0x08
    u32 pad0c;           // 0x0C
    void* handle10;      // 0x10
    void* buffer14;      // 0x14
};

extern "C" {
    void sub_2A409C(void** p_handle);
    void sub_2C4360(void* ptr);
}

extern "C" u32 h11_terminal_releasecontext_candidate(TerminalContext* ctx) {
    if (!ctx) return 1;
    for (int i = 0; i < 2; ++i) {
        void* obj = ctx->sub_objs[i];
        if (obj) {
            VFunc0* vtbl = *reinterpret_cast<VFunc0**>(obj);
            vtbl[0](obj);
            void* mgr = *reinterpret_cast<void**>(reinterpret_cast<u8*>(obj) + 4);
            VFuncFree* mgr_vtbl = *reinterpret_cast<VFuncFree**>(mgr);
            mgr_vtbl[3](mgr, obj);
            ctx->sub_objs[i] = nullptr;
        }
    }
    if (ctx->handle10) {
        void* temp = ctx->handle10;
        sub_2A409C(&temp);
    }
    if (ctx->buffer14) {
        sub_2C4360(ctx->buffer14);
    }
    sub_2C4360(ctx);
    return 1;
}

extern "C" u32 h11_terminal_releasecontext_mutation(TerminalContext* ctx) {
    return 0;
}
