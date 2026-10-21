#include "engine/runtime_blocks.h"

#include <cstring>

#include "engine/asd_symbols.h"

/**
 * Reconstruction notes
 * ====================
 * The four blocks in this translation unit are reconstructed from the shipped
 * ARM listing.  Branches, observable calls and register stores are annotated
 * with the instruction addresses that prove them.  Helpers are used only for
 * code that the compiler inlined several times (vector growth, tree walks,
 * pointer-field copy); each helper documents the exact listing range it
 * replaces.
 */

namespace smt4::engine {
namespace {

// ---------------------------------------------------------------------------
// Literal-pool constants referenced below
// ---------------------------------------------------------------------------

constexpr u32 kEventAllocMessage = 0x003B178Cu;  // 0x003B1478 add r1,pc,#0x30C
constexpr u32 kEventVectorMessage = 0x0040FE40u; // 0x003B1DC4 / 0x003B1E2C
constexpr u32 kEventFailAddress = 0x0040FE80u;   // 0x003B184C

constexpr u32 kLcdCommandData = 0x000F008Eu;     // 0x00143278
constexpr u32 kLcdChannel0Reg = 0x81u;           // 0x00143254
constexpr u32 kLcdChannel0Count = 0x0Au;         // 0x00143250
constexpr u32 kLcdChannel1Reg = 0x91u;           // 0x001436FC
constexpr u32 kLcdChannel1Count = 0x06u;         // 0x001436F8
constexpr u32 kLcdChannel2Reg = 0x99u;           // 0x00143B78
constexpr u32 kLcdChannel2Count = 0x06u;         // 0x00143B74

constexpr f32 kLcdColorScale = 255.0f;           // 0x437F0000, 0x00142C7C
constexpr f32 kLcdAlphaBias = 16.0f;             // 0x41800000, 0x00142CA0
constexpr f32 kLcdAlphaScale = 256.0f;           // 0x43800000, 0x00142CA4
constexpr f32 kLcdAlphaMax = 8191.0f;            // 0x45FFF800, 0x00142CA8
constexpr f32 kLcdAlphaWrap = 4096.0f;           // 0x45800000, 0x00142CAC

} // namespace

// ---------------------------------------------------------------------------
// External call targets.  The declarations are local to this translation unit;
// names are the exact ledger names for each address.
// ---------------------------------------------------------------------------

extern "C" {

// 0x003B11A8 helpers -------------------------------------------------------
u32  func_003b03b0(const u8* data, u32* value, ScriptCursor* cursor, u32 end);
u32  func_003b01bc(void** allocator, u32 type, void* arg);
void func_00397158(void* tree, void* node);
void func_003af524(void* dest, u32 key, void* table);
void func_003fca6c(void* out, void* tree, void* key);
void func_0022c1cc(void* element);
void func_0022c6f8(void* vector, u32 first, u32 last);
u32  func_0022c198(u32 current, u32 requested);
void* func_00397314(void* node);

// 0x00101308 helpers -------------------------------------------------------
void engine_func_002c5fbc();
void engine_func_001076d8(u32 a, u32 b);
void* AsdMemory_func_0010376c(u32 size);
void func_00105e2c(u32 value);
void AsdFile_func_0010250c();
u32  engine_func_0010db6c();
void engine_func_00106db4(u32 value);
void func_00106d88();
void engine_func_00106bcc();
void engine_func_00106ce4();
s32  engine_func_00103e4c();
void func_00103c08();
void AsdNgc_func_00103aa0();
void battle_func_00105460(void* block);
void func_00105ddc(u32 value);
void engine_func_00105b38();

void func_00104298();
void func_00105db4(u32 index, f32 s0, f32 s1, f32 s2, f32 s3);
void* ui_func_002c5f58(void* dst, u32 table, u32 size, u32 count);
void engine_func_001059b4(void* object);
void engine_func_001051f8(void* object);
void engine_func_002c5e3c(const char* name, u32 a, u32 b, u32 c);
void engine_func_00105438();
void func_00105dcc(u32 value);
f32* func_00103760();
f32* func_001035d4();
f32* func_00103754();
f32* func_0010428c();
f32* func_00105c44();
void AsdModel_func_0010495c(u32 a, u32 b);
void script_vm_func_001041d8();
f32* script_vm_func_002c5e20();
void* func_00104db0();
void* script_vm_func_002c5e10();
void* AsdGxCommandList_func_002c5d90();
void ui_func_00102aa0();
void AsdPrim_func_001042c8(u32 value);
void AsdProcess_func_00102e80(u32 value);
void func_00103f70();
void AsdTMTexTable_func_00105080(const char* path);
void func_00103c70();
void IfTouch_Init();
void ui_func_00102848();
void engine_func_001058ec();
void engine_func_00107144();
void engine_func_00107050();
void engine_func_00107020();
void func_00104dcc(u32 value);
void func_00103ef8(u32 value);
void engine_func_00106b4c();
void AsdTMTexTable_func_002c5b04(u32 a, u32 b);
void engine_func_002c5ab8(u32 a, u32 b);
void GameData_func_00102cf0();
void func_00104de8(u32 value);
void func_00105df4(u32 value);
void engine_func_00106024();
void engine_func_00105e9c();
void engine_func_001065f4();
void soundEffect_func_0010368c();
void func_00105c1c();
void script_vm_func_002c5a6c();
void script_vm_func_00104e68();
u32  AsdSequence_func_002c59b8(u32 a, u32 b, u32 c);
void AsdCamera_func_00105c50(u32 value);
void AsdModelProcess_func_00103ff8(u32 a, u32 b, u32 c, u32 d);
void FrameTex_func_00104378(u32 value);
void engine_func_00102dc4(u32 value);
void engine_func_001069bc(u32 object, f32 s0, f32 s1, f32 s2, f32 s3);
void ui_func_002c5948(u32 value);
void camp_func_002c5918(u32 value);
void script_vm_func_002c58cc(u32 value);
u32  engine_func_002c586c(void* out);
void func_00103de4();
void func_00103cbc(u32 value);
void engine_func_0010b578();
u32  func_00103744();
u32  func_001076a0();
void func_002c584c(u32 opcode, u32 enable);
void func_00105e3c(u32 a, u32 b);
void crt_func_00102438();
void engine_func_00105914();
void func_00103fb0(u32 value);
u32  ui_func_001074dc(u32 value);
void camp_func_001071b4();
void engine_func_00107208();
void engine_func_00105338();
void engine_func_00102f18(u32 value);
void engine_func_001062e0();
void engine_func_00105f3c();
void engine_func_001066ac();
void func_00103f8c();
void engine_func_00105848(u32 value);

f32  func_00105da4();
void func_0010527c();
void func_00105bac();
u32  func_00103dd4();
void battle_func_00123858();
void func_002c5820(u32 value);
void func_0010753c();
u32  func_00104184();
void func_00103ccc();
u32  func_00104194();
void script_vm_func_00103c20();
u32  func_00105070();
void func_001041a4();
void engine_func_00104df8();
void engine_func_001034c8();
u32  func_00103df4();
void func_00103c54();
void script_vm_func_002c5810();
void engine_func_00104274();
void func_002c57fc(u32 value);
u32  engine_func_00105194();
void func_002c0ee0();
u32  func_0010541c();
void func_002c57c4(u32 value);
void func_00103484();
void func_00106f14();
void func_00103f14();
u32  func_002c57b4();
void func_00106e04();
u32  func_002c57a4();
void nn_sdk_func_002c5644(u32 a, u32 b, void* c);
void engine_func_002c5624(u32 value);

// 0x00142BF0 helpers -------------------------------------------------------
u32  func_00147994(u32 address);
void func_002aa938(u32 reg, u32 count);

// 0x002831F0 helpers -------------------------------------------------------
void* camp_func_002a0fac();
u32   camp_func_0029f0f4(void* slot);

} // extern "C"

// ---------------------------------------------------------------------------
// .data globals reproduced from the listing
// ---------------------------------------------------------------------------

void* g_RenderRegisterBase = nullptr;   // 0x0044EA00 (`ldr r4,[r7]`, 0x001013D0)
u8    g_CrtOverlayFlag = 0;             // 0x0044D048 (`ldrb r0,[r4]`, 0x00101E98)
void* g_CrtModeContext = nullptr;       // 0x0044E368 (`ldr r2,[r0]`, 0x00102268)
CrtMainState g_CrtMainState{};          // 0x00446DB0
void* g_LcdGpuState = nullptr;          // 0x004655C0 (`ldr r3,[r2]`, 0x00142BF8)
u32*  g_GpuCommandCursor = nullptr;     // 0x004652A0 (`ldr r1,[r2]`, 0x00143264)
u32*  g_GpuCommandEnd = nullptr;        // 0x004652A4 (`ldr r0,[r0]`, 0x00143268)
void* g_CampLayoutRoot = nullptr;       // 0x0043DA90 (`ldr r5,[r0]`, 0x002831FC)

namespace {

// ===========================================================================
// 0x003B11A8 helpers
// ===========================================================================

// 0x003B03B0: unsigned LEB128 reader.  Returns 1 on success, 0 when the
// cursor reaches `end` in the middle of a value.
u32 ReadLeb128(const u8* data, u32 index, u32* value, ScriptCursor* cursor,
               u32 end)
{
    return func_003b03b0(data + index, value, cursor, end);
}

// 0x003B1254..0x003B129C: tree lookup on the map at state+0x1444.  Nodes have
// the key at +0x10 and children at +0x00 / +0x04.
u8* FindTreeKey(void* tree, u32 key)
{
    u8* header = static_cast<u8*>(tree) + 0x08;
    u8* node = *reinterpret_cast<u8**>(static_cast<u8*>(tree) + 0x04);
    while (node != header) {
        u32 node_key = *reinterpret_cast<u32*>(node + 0x10);
        if (node_key < key) {
            node = *reinterpret_cast<u8**>(node + 0x04);
        } else {
            header = node;
            node = *reinterpret_cast<u8**>(node + 0x00);
        }
    }
    if (header != static_cast<u8*>(tree) + 0x08 &&
        *reinterpret_cast<u32*>(header + 0x10) == key) {
        return header;
    }
    return nullptr;
}

// 0x003B137C..0x003B1390: allocate one 0x24-byte tree node.  The allocator
// lives at tree+0x24 and exposes `vtable[0](allocator, size)`.
u8* AllocateTreeNode(void* tree)
{
    void* allocator = *reinterpret_cast<void**>(static_cast<u8*>(tree) + 0x24);
    void** vtable = *reinterpret_cast<void***>(allocator);
    using AllocFn = void* (*)(void*, u32);
    return static_cast<u8*>(
        reinterpret_cast<AllocFn>(vtable[0])(allocator, 0x24));
}

// 0x003B1468..0x003B1480 / 0x003B2038..0x003B2044: report an allocation
// failure through `vtable[2](allocator, message, size)` and release the
// already constructed temporary at +0x24.
void ReportNodeFailure(void* tree, u32 message, u32 size)
{
    void* allocator = *reinterpret_cast<void**>(static_cast<u8*>(tree) + 0x24);
    void** vtable = *reinterpret_cast<void***>(allocator);
    using FailFn = void (*)(void*, u32, u32);
    reinterpret_cast<FailFn>(vtable[2])(allocator, message, size);
}

// 0x003B1B08..0x003B1D64: append one 16-byte node to the vector at
// state+0x1434, growing it through func_0022c198 and destroying the moved
// range through func_0022c6f8.  The element links are copied with
// `ldr/str` pairs at 0x003B1B88..0x003B1BA8.
void AppendNode(ScriptRuntimeState* state, const ScriptNode16* source)
{
    ScriptNodeVector& vec = state->nodes;
    if (vec.capacity >= vec.size + 1) {
        // 0x003B1F60..0x003B1F90: append at begin + size*16.
        vec.begin[vec.size] = *source;
        vec.size += 1;                             // 0x003B1F54..0x003B1F58
        return;
    }

    // 0x003B1D68..0x003B1F50: grow to func_0022c198(capacity, size+1).
    u32 new_capacity = func_0022c198(vec.capacity, vec.size + 1);
    void* allocator = vec.owner;
    void** vtable = *reinterpret_cast<void***>(allocator);
    using AllocFn = void* (*)(void*, u32);
    u8* storage = static_cast<u8*>(
        reinterpret_cast<AllocFn>(vtable[0])(allocator, new_capacity * 0x10));
    if (storage == nullptr) {
        using FailFn = void (*)(void*, u32, u32);
        reinterpret_cast<FailFn>(vtable[2])(allocator, kEventVectorMessage,
                                            new_capacity * 0x10);
    }
    ScriptNode16* fresh = reinterpret_cast<ScriptNode16*>(storage);
    for (u32 i = 0; i < vec.size; ++i) {
        fresh[i] = vec.begin[i];
    }
    fresh[vec.size] = *source;
    func_0022c6f8(&vec, 0, vec.size);              // 0x003B1F30
    vec.begin = fresh;
    vec.capacity = new_capacity;
    vec.size += 1;
}

// The address of the command tree is state+0x1414; the helper below needs it
// as a void* without exposing the opaque field in every call.
void* tree_address(ScriptRuntimeState* state)
{
    return state->command_tree;
}

// 0x003B1578..0x003B17C8: create the 0x74-byte child record, initialise its
// two embedded lists and insert it through func_003b01bc.
u32 CreateChildRecord(ScriptRuntimeState* state, u32 index, u8* parent_payload)
{
    (void)index;
    void* allocator = state->allocator;
    void** vtable = *reinterpret_cast<void***>(allocator);
    using AllocFn = void* (*)(void*, u32);
    u8* record = static_cast<u8*>(
        reinterpret_cast<AllocFn>(vtable[0])(allocator, 0x74)); // 0x003B1608
    if (record == nullptr) {
        return 0x44u;
    }

    // 0x003B1620..0x003B1690: two intrusive lists at +0x4C and +0x58 and the
    // enable byte at +0x70.
    *reinterpret_cast<void**>(record + 0x00) = allocator;
    *reinterpret_cast<void**>(record + 0x04) = allocator;
    *reinterpret_cast<u32*>(record + 0x08) = 0;
    *reinterpret_cast<u32*>(record + 0x0C) = 0;
    *reinterpret_cast<u32*>(record + 0x10) = 0;
    *reinterpret_cast<u32*>(record + 0x14) = 0;
    *reinterpret_cast<u32*>(record + 0x18) = 0;
    *reinterpret_cast<u32*>(record + 0x1C) = 0;
    *reinterpret_cast<u32*>(record + 0x20) = 0;
    *reinterpret_cast<u32*>(record + 0x24) = 0;
    *reinterpret_cast<u32*>(record + 0x28) = 0;
    *reinterpret_cast<u32*>(record + 0x2C) = 0;
    *reinterpret_cast<u32*>(record + 0x30) = 0;
    *reinterpret_cast<u32*>(record + 0x34) = 0;
    *reinterpret_cast<u32*>(record + 0x38) = 0;
    *reinterpret_cast<u32*>(record + 0x3C) = 0;
    *reinterpret_cast<u32*>(record + 0x40) = 0;
    *reinterpret_cast<u32*>(record + 0x44) = 0;
    *reinterpret_cast<u32*>(record + 0x48) = 0;
    *reinterpret_cast<u32*>(record + 0x4C) = static_cast<u32>(reinterpret_cast<std::uintptr_t>(record + 0x4C));
    *reinterpret_cast<u32*>(record + 0x50) = 0;
    *reinterpret_cast<u32*>(record + 0x54) = static_cast<u32>(reinterpret_cast<std::uintptr_t>(record + 0x4C));
    *reinterpret_cast<u32*>(record + 0x58) = static_cast<u32>(reinterpret_cast<std::uintptr_t>(record + 0x4C));
    *reinterpret_cast<u32*>(record + 0x5C) =
        static_cast<u32>(reinterpret_cast<std::uintptr_t>(allocator));
    *reinterpret_cast<u32*>(record + 0x60) = 0;
    *reinterpret_cast<u32*>(record + 0x64) = 0;
    *reinterpret_cast<u32*>(record + 0x68) = 0;
    *reinterpret_cast<u32*>(record + 0x6C) = 0;
    *reinterpret_cast<u8*>(record + 0x70) = 1;
    *reinterpret_cast<u32*>(record + 0x14) =
        *reinterpret_cast<u32*>(parent_payload + 0x14); // 0x003B1694

    func_003af524(record, *reinterpret_cast<u32*>(parent_payload + 0x14),
                  state->channel_table);              // 0x003B16A0

    void* allocator_copy = allocator;
    u8* inserted = reinterpret_cast<u8*>(
        func_003b01bc(&allocator_copy, *reinterpret_cast<u32*>(parent_payload + 0x14),
                      record));                       // 0x003B16B0
    if (inserted == nullptr) {
        return 0x44u;
    }

    // 0x003B16C0..0x003B1788: payload slots 6 and 4, then the two temporary
    // trees are destroyed through func_003fca6c / func_0022c1cc.
    void** payload_vtable = *reinterpret_cast<void***>(inserted);
    using Slot6 = void (*)(void*, u8*);
    reinterpret_cast<Slot6>(payload_vtable[6])(inserted, parent_payload);
    using Slot4 = u32 (*)(void*);
    if (reinterpret_cast<Slot4>(payload_vtable[4])(inserted) != 0) {
        *reinterpret_cast<u32*>(inserted + 0x14) =
            *reinterpret_cast<u32*>(parent_payload + 0x14);
    }

    u8 temp_a[0x30] = {};
    u8 temp_b[0x30] = {};
    func_003fca6c(temp_a, tree_address(state), temp_b); // 0x003B1764
    func_0022c1cc(temp_b);                              // 0x003B1770
    func_0022c1cc(temp_a);                              // 0x003B177C
    return 0;
}

} // namespace

// ---------------------------------------------------------------------------
// 0x003B11A8 -- event command dispatch (4,548 B)
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x003b11a8, 4548)
u32 func_003b11a8(ScriptRuntimeState* state, u32 index, ScriptCursor* cursor,
                  u32 end)
{
    u32 key = 0;
    u32 value = 0;

    // 0x003B11B8..0x003B1204: first LEB128 from *cursor + index.
    {
        u32 stream = *reinterpret_cast<u32*>(
            reinterpret_cast<std::uintptr_t>(cursor));
        if (ReadLeb128(reinterpret_cast<const u8*>(
                           static_cast<std::uintptr_t>(stream)),
                       index, &key, cursor, end) == 0) {
            goto reset_43;
        }
    }

    // 0x003B1208..0x003B1224: second LEB128; the cursor was advanced by the
    // first read, so the stream base is reloaded (ldr r0,[r0]).
    {
        u32 stream = *reinterpret_cast<u32*>(
            reinterpret_cast<std::uintptr_t>(cursor));
        if (ReadLeb128(reinterpret_cast<const u8*>(
                           static_cast<std::uintptr_t>(stream)),
                       index, &value, cursor, end) == 0) {
            goto reset_43;
        }
    }

    if (key == 0) {
        // 0x003B1444..0x003B1464: cursor += value, return 0x100.
        *reinterpret_cast<u32*>(reinterpret_cast<std::uintptr_t>(cursor)) += value;
        return 0x100u;
    }

    {
        // 0x003B1228..0x003B1304: locate the command node for `key`.
        u8* tree = state->key_tree;
        u8* found = FindTreeKey(tree, key);
        u8* allocator = static_cast<u8*>(state->allocator);
        void* variant = nullptr;
        u8* node = nullptr;

        if (found != nullptr) {
            node = found;
            variant = *reinterpret_cast<void**>(found + 0x18);
        } else {
            // 0x003B12AC..0x003B12C0: func_003b01bc(&allocator, key, 0).
            void* allocator_copy = allocator;
            variant = reinterpret_cast<void*>(
                func_003b01bc(&allocator_copy, key, nullptr));
            if (variant == nullptr) {
                goto fail_44;
            }

            // 0x003B1310..0x003B13FC: allocate and link the 0x24-byte node.
            node = AllocateTreeNode(tree);
            if (node == nullptr) {
                ReportNodeFailure(tree, kEventAllocMessage, 0x24);
                goto fail_44;
            }
            *reinterpret_cast<u32*>(node + 0x10) = key;   // 0x003B13A0
            *reinterpret_cast<void**>(node + 0x18) = variant; // 0x003B13B0-B4
            *reinterpret_cast<void**>(node + 0x14) = nullptr;
            *reinterpret_cast<u8*>(node + 0x0C) = 1;      // 0x003B13F0
            func_00397158(tree, node);                    // 0x003B13EC
        }

        // 0x003B1520..0x003B1574: payload +0x08 must match the decoded value;
        // virtual slot 3 receives (payload, data + index).
        if (*reinterpret_cast<u32*>(static_cast<u8*>(variant) + 0x08) != value) {
            goto reset_45;
        }

        {
            void** vtable = *reinterpret_cast<void***>(variant);
            using Slot3 = u32 (*)(void*, u32);
            u32 stream_ptr = *reinterpret_cast<u32*>(
                                 reinterpret_cast<std::uintptr_t>(cursor)) +
                             index;
            if (reinterpret_cast<Slot3>(vtable[3])(variant, stream_ptr) == 0) {
                goto reset_45;
            }
            using Slot4 = u32 (*)(void*);
            if (reinterpret_cast<Slot4>(vtable[4])(variant) == 0) {
                // 0x003B1B08..0x003B1D64: append a 16-byte node.
                ScriptNode16 entry{};
                entry.link_00 = *reinterpret_cast<u32*>(node + 0x10);
                entry.link_04 = *reinterpret_cast<u32*>(node + 0x14);
                entry.link_08 = static_cast<u32>(
                    reinterpret_cast<std::uintptr_t>(node));
                entry.link_0c = static_cast<u32>(
                    reinterpret_cast<std::uintptr_t>(node));
                AppendNode(state, &entry);
                goto finish;
            }
        }

        // 0x003B1578..0x003B1814: nested command tree.
        if (CreateChildRecord(state, index, static_cast<u8*>(variant)) == 0x44u) {
            goto fail_44;
        }

        // 0x003B1818..0x003B18C0: walk the tree with the red-black successor
        // routine and notify the parent once.
        {
            u8* tree_bytes = static_cast<u8*>(tree);
            u8* header = tree_bytes + 0x08;
            u8* walk = *reinterpret_cast<u8**>(tree_bytes + 0x04);
            while (walk != header) {
                u8* child = *reinterpret_cast<u8**>(walk + 0x18);
                child = *reinterpret_cast<u8**>(child + 0x10); // 0x003B1828
                if (*reinterpret_cast<u8*>(child + 0x70) != 0) {
                    if (state->callback_1480 != nullptr) {
                        state->callback_1480(
                            kEventFailAddress,
                            *reinterpret_cast<u32*>(
                                static_cast<u8*>(variant) + 0x14));
                    }
                    return 0x53u;
                }
                walk = static_cast<u8*>(func_00397314(walk)); // 0x003B1864
            }
        }
    }

finish:
    // 0x003B22F0..0x003B2314: cursor += value; success only while <= end.
    *reinterpret_cast<u32*>(reinterpret_cast<std::uintptr_t>(cursor)) += value;
    if (*reinterpret_cast<u32*>(reinterpret_cast<std::uintptr_t>(cursor)) <= end) {
        return 0;
    }

reset_43:
    // 0x003B2318..0x003B2360.
    state->output_words[0] = 0;
    state->output_words[1] = 0;
    state->output_words[2] = 0;
    state->output_words[3] = 0;
    state->output_1478 = 0x40;
    state->output_147c = 0x10000;
    state->output_1487 = 0;
    state->output_1489 = 0;
    return 0x43u;

reset_45:
    // 0x003B17CC..0x003B1814.
    state->output_words[0] = 0;
    state->output_words[1] = 0;
    state->output_words[2] = 0;
    state->output_words[3] = 0;
    state->output_1478 = 0x40;
    state->output_147c = 0x10000;
    state->output_1487 = 0;
    state->output_1489 = 0;
    return 0x45u;

fail_44:
    // 0x003B2048..0x003B2050.
    return 0x44u;
}

// ---------------------------------------------------------------------------
// 0x00101308 -- nnMain / application main loop (4,144 B)
// ---------------------------------------------------------------------------

namespace {

// `svc #0x28` at 0x00101B80 and 0x00101F08 (GetSystemTick).  The host build
// has no ARM SVC; the fixed-point arithmetic below is independent of the
// clock source.
u64 SystemTick()
{
    // The shipped ARM body executes `svc #0x28` and consumes the r0:r1 pair.
    // This host reconstruction keeps a platform-neutral stub; the 64-bit
    // fixed-point reduction below is independent of the clock source.
    return 0;
}

// 0x00101F20..0x00101FDC: the 64-bit tick delta is first multiplied by the
// packed magic 0x3BAD34AEE (0xBAD34AEE plus the `mov r1,#3` high term) and
// reduced by >>32, producing 999,999,999 for 268,111,856 ticks (one second in
// nanoseconds).  The second stage (0xE353F7CF, then 0x20C49BA5 with `>>7`)
// divides that value by 1000, so the frame-load input is microseconds.  The
// combined tick divisor is therefore ~268,111, not 1,000.
constexpr u64 kTickNanosecondsMagic = 0x3BAD34AEEULL; // 0x00101F24 + r1=3
constexpr u32 kTickMagic1 = 0xE353F7CFu;              // 0x00101F58
constexpr u64 kTickMicrosecondsMagic = 0x20C49BA5ULL; // 0x00101F90
constexpr u32 kTickMicrosecondsShift = 39u;           // 32 + the final >>7

u32 TickDeltaToMicroseconds(u64 delta)
{
    (void)kTickMagic1; // first-stage sign correction in the ARM sequence
    const u64 nanoseconds =
        (delta * kTickNanosecondsMagic) >> 32;
    return static_cast<u32>(
        (nanoseconds * kTickMicrosecondsMagic) >> kTickMicrosecondsShift);
}

void CreateDrawTask(const char* name, u32 priority, u32 callback)
{
    using Callback = void (*)(void*);
    AsdTask_CreateCalc(name, priority, 0, 0,
                       reinterpret_cast<Callback>(
                           static_cast<std::uintptr_t>(callback)),
                       0, 0);
}

} // namespace

// DECOMP_FUNC(0x00101308, 4144)
void crt_func_00101308(void)
{
    // 0x00101310..0x00101358: system bring-up.
    engine_func_002c5fbc();
    engine_func_001076d8(0, 0x12345678u);
    AsdMemory_func_0010376c(0x100000u);
    func_00105e2c(1);
    AsdFile_func_0010250c();
    engine_func_00106db4(engine_func_0010db6c());
    func_00106d88();
    engine_func_00106bcc();
    engine_func_00106ce4();
    if (engine_func_00103e4c() <= 0) {          // 0x00101350 / bleq
        func_00103c08();
    }
    AsdNgc_func_00103aa0();

    // 0x0010138C..0x00101390: fp = 1, r6 = 0x00446DB0.
    g_CrtMainState.stereo_enabled = 1;

    // 0x0010135C..0x001013B0: the eleven-word initialiser passed to
    // battle_func_00105460.
    {
        alignas(8) u32 block[11] = {};
        block[0] = 0x100000u;                   // sp+0x8C
        block[1] = 0x800u;                      // sp+0x90
        block[2] = 0x80000u;                    // sp+0x94
        block[3] = 0x80u;                       // sp+0x98
        block[4] = 0x100000u;                   // sp+0x9C
        block[5] = 0;                           // sp+0xA0
        block[6] = 0x501u;                      // sp+0xA4
        block[7] = 0;                           // sp+0xA8
        block[8] = 0;                           // sp+0xAC
        block[9] = 0x8D62u;                     // sp+0xB0
        block[10] = 0x8D62u;                    // sp+0xB4
        battle_func_00105460(block);
    }

    func_00105ddc(1);
    engine_func_00105b38();

    // 0x001013C0..0x001013FC: three words in the render-register base.
    {
        u8* base = static_cast<u8*>(g_RenderRegisterBase);
        *reinterpret_cast<u32*>(base + 0x136C) = 0;
        *reinterpret_cast<u32*>(base + 0x1384) = static_cast<u32>(
            reinterpret_cast<std::uintptr_t>(UiGpu_SetRenderMode(6, 7, 0)));
        *reinterpret_cast<u32*>(base + 0x1378) = static_cast<u32>(
            reinterpret_cast<std::uintptr_t>(UiGpu_SetViewportParams(5, 1)));
    }

    func_00104298();
    func_00105db4(0, 0.0f, 0.0f, 0.0f, 0.0f);  // 0x0010141C
    func_00105db4(1, 0.0f, 0.0f, 0.0f, 0.0f);  // 0x00101434

    // 0x00101438..0x00101470: 0x8C-byte display-list descriptor; the helper
    // fills the first 0x80 bytes and the listing overwrites +0x80..+0x88.
    {
        alignas(8) u8 object[0x8C] = {};
        void* result = ui_func_002c5f58(object, 0x0010716Cu, 0x3Cu, 2);
        *reinterpret_cast<u32*>(static_cast<u8*>(result) + 0x80) = 0;
        *reinterpret_cast<u16*>(static_cast<u8*>(result) + 0x84) = 0x8058;
        *reinterpret_cast<u32*>(static_cast<u8*>(result) + 0x88) = 0;
        *reinterpret_cast<u32*>(object + 0x80) = 2;
        *reinterpret_cast<u16*>(object + 0x84) = 0x8D62;
        *reinterpret_cast<u32*>(object + 0x88) = 0x400;
        engine_func_001059b4(object);           // 0x00101470
    }

    // 0x00101474..0x001014B0: ten-word mode descriptor.
    {
        alignas(8) u32 desc[10] = {
            5, 5, 0x80, 0x80, 4, 4, 8, 8, 4, 4,
        };
        engine_func_001051f8(desc);
    }

    // 0x001014B4..0x001014C4: default shader.
    engine_func_002c5e3c("nwgfx_DefaultShader.bcsdr", 0, 1, 0x80);
    engine_func_00105438();
    func_00105dcc(1);

    // 0x001014D4..0x00101528: engine scalars.
    *func_00103760() = 3.0f;                    // 0x40400000
    *func_001035d4() = 20000.0f;               // 0x469C4000
    *func_00103754() = 12.0f;                  // 0x41400000
    *func_0010428c() = 0.5f;                   // 0x3F000000
    *func_00105c44() = 0.4f;                   // 0x3ECCCCCD
    AsdModel_func_0010495c(0x100, 0x30000);
    script_vm_func_001041d8();
    *script_vm_func_002c5e20() = 1000.0f;      // 0x447A0000

    // 0x0010152C..0x001015C4: project the loaded scene rectangle.
    if (func_00104db0() != nullptr) {
        u8* object = static_cast<u8*>(script_vm_func_002c5e10());
        u32* holder = *reinterpret_cast<u32**>(object + 0x260);
        void** vtable = *reinterpret_cast<void***>(holder);
        using GetFn = u8* (*)(void*);
        u8* rect = reinterpret_cast<GetFn>(vtable[4])(holder);
        if (rect != nullptr &&
            (*reinterpret_cast<u32*>(rect) & 0x40000000u) != 0) {
            f32 width = *reinterpret_cast<f32*>(rect + 0x0C);
            f32 x = *reinterpret_cast<f32*>(rect + 0x14);
            f32 height = *reinterpret_cast<f32*>(rect + 0x18);
            f32 value = *script_vm_func_002c5e20();
            f32 half = 0.5f;                   // 0x3F000000
            f32 h = height + value * half;
            f32 y0 = x - value * half;
            f32 y1 = height - value * half;
            f32 w = value * width;
            f32 new_w = h - y0;
            f32 new_h = (h + y0) * half;
            f32 y_a = y1 - 0.5f * w;
            f32 y_b = (y1 + 0.5f * w) * half;
            *reinterpret_cast<f32*>(rect + 0x10) = new_w;
            *reinterpret_cast<f32*>(rect + 0x0C) = (y_a - y_b) / new_w;
            *reinterpret_cast<f32*>(rect + 0x14) = y_b;
            *reinterpret_cast<f32*>(rect + 0x18) = new_h;
        }
    }

    // 0x001015CC..0x00101648: render/process bring-up.
    g_CrtMainState.gx_08 = AsdGxCommandList_func_002c5d90();
    g_CrtMainState.gx_0c = AsdGxCommandList_func_002c5d90();
    ui_func_00102aa0();
    AsdPrim_func_001042c8(0x100000);
    AsdProcess_func_00102e80(0x163);
    func_00103f70();
    AsdTMTexTable_func_00105080("tex/sdds4TopDir.dat");
    func_00103c70();
    IfTouch_Init();
    ui_func_00102848();
    engine_func_001058ec();
    engine_func_00107144();
    engine_func_00107050();
    engine_func_00107020();
    func_00104dcc(7);
    func_00103ef8(2);
    engine_func_00106b4c();
    AsdTMTexTable_func_002c5b04(0x2C, 0);
    engine_func_002c5ab8(0x2C, 0);
    GameData_func_00102cf0();
    func_00104de8(0);
    func_00105df4(1);
    engine_func_00106024();
    engine_func_00105e9c();
    engine_func_001065f4();
    soundEffect_func_0010368c();
    func_00105c1c();
    script_vm_func_002c5a6c();
    script_vm_func_00104e68();
    AsdSequence_func_002c59b8(0x18, 0, 0);

    // 0x00101730..0x00101AC8: twenty-three AsdProcess draw tasks.  The
    // argument order is (name, priority, 0, 0, callback, 0, 0); the callback
    // literals are the PC-relative words above each call.
    CreateDrawTask("BeforeDraw1L", 0x65, 0x00103B58);
    CreateDrawTask("Draw1SetTargetProc", 0x66, 0x00103D10);
    CreateDrawTask("Draw1ModelLDone", 0x69, 0x001035E0);
    CreateDrawTask("Draw1CashS1", 0x6E, 0x001026C4);
    CreateDrawTask("Draw1EplL", 0x75, 0x00106130);
    CreateDrawTask("DrawULCD2DBegin", 0x72, 0x00103670);
    CreateDrawTask("Draw1CashE1", 0x74, 0x00102634);
    CreateDrawTask("Draw1CashS1", 0x83, 0x00102724);
    CreateDrawTask("Draw1CashE2", 0xCB, 0x00102678);
    CreateDrawTask("BeforeDraw1R", 0xCC, 0x00103BA0);
    CreateDrawTask("Draw1ModelR", 0xCD, 0x00102810);
    CreateDrawTask("Draw1Proc1", 0xD2, 0x00102760);
    CreateDrawTask("Draw1EplR", 0xD3, 0x00106160);
    CreateDrawTask("Draw1Proc2", 0xE1, 0x001027C0);
    CreateDrawTask("DrawU2DBegin_NCL", 0x7A, 0x00103D9C);
    CreateDrawTask("DrawU2DBegin_NCR", 0xD8, 0x00103DB8);
    CreateDrawTask("DrawU2DBegin_TLL", 0x76, 0x00103D9C);
    CreateDrawTask("DrawU2DBegin_TLR", 0xD4, 0x00103DB8);
    CreateDrawTask("Draw2SetTargetProc", 0xE2, 0x00103D5C);
    CreateDrawTask("DrawDLCD2DBegin", 0xE4, 0x00103654);
    CreateDrawTask("Draw2Proc", 0x162, 0x00106190);
    CreateDrawTask("DrawUFadeProc", 0x85, 0x00102CDC);
    CreateDrawTask("DrawDFadeProc", 0x160, 0x00102CC8);

    // 0x00101AC8..0x00101B44.
    AsdCamera_func_00105c50(3);
    AsdModelProcess_func_00103ff8(0x67, 0x68, 0xE3, 0);
    FrameTex_func_00104378(1);
    engine_func_00102dc4(0);
    engine_func_001069bc(reinterpret_cast<std::uintptr_t>(g_RenderRegisterBase),
                         0.25f, 0.2f, 1.0f, 1.0f);
    ui_func_002c5948(7);
    camp_func_002c5918(7);
    script_vm_func_002c58cc(1);

    // 0x00101B48..0x00101B78: one-shot tick calibration.
    {
        g_CrtMainState.shutdown = 0;
        u8 tick_out[0x10] = {};
        u32 raw = engine_func_002c586c(tick_out);
        u32 scaled = raw * 1000000u;             // umull r0,r1,#0xF4240
        func_00103de4();
        func_00103cbc(scaled);
    }

    // Main frame loop starts at 0x00101B7C.  `stereo_disable` is the r4 value
    // at 0x00101BC8 / 0x00101DA8 (0 after enabling, 1 after disabling).
    u32 stereo_disable = 0;
    u32 mode = 0;
    u64 delta = 0;
    u32 elapsed = 0;
    f32 fps = 0.0f;
    const f32 frame_budget = 100.0f;             // 0x42C80000, 0x00101B78

main_loop:
    // 0x00101B80..0x00101B88.
    g_CrtMainState.tick_20 = SystemTick();
    engine_func_0010b578();
    g_CrtMainState.render_ready = func_00103744() != 0 ? 1 : 0;

    if (func_001076a0() != 0) {
        // 0x00101BBC..0x00101C0C: enable the five render switches.
        g_CrtMainState.stereo_enabled = 1;
        stereo_disable = 0;
        func_002c584c(0xCC, 1);
        func_002c584c(0xD8, 1);
        func_002c584c(0xDB, 1);
        func_002c584c(0xDE, 1);
        func_002c584c(0xDF, 1);
    } else {
        // 0x00101D90..0x00101DD0: disable them and pass r4 = 1.
        g_CrtMainState.stereo_enabled = 0;
        stereo_disable = 1;
        func_002c584c(0xCC, 0);
        func_002c584c(0xD8, 0);
        func_002c584c(0xDB, 0);
        func_002c584c(0xDE, 0);
        func_002c584c(0xDF, 0);
    }

    func_00105e3c(0, stereo_disable);            // 0x00101DDC
    if (g_CrtMainState.stereo_enabled != 0) {
        u32 next = g_CrtMainState.stereo_counter_1c + 1;
        g_CrtMainState.stereo_counter_1c = next;
        if (next > 2) {                           // movgt r0,#2
            g_CrtMainState.stereo_counter_1c = 2;
        }
    } else {
        g_CrtMainState.stereo_counter_1c = 0;
    }

    crt_func_00102438();                         // 0x00101E0C
    if (g_CrtMainState.timer_enabled != 0) {
        engine_func_00105914();
        if (g_CrtMainState.timer_enabled != 0) {
            if (g_CrtMainState.timer_10 >= 0x1E) {
                g_CrtMainState.timer_10 -= 0x1E;
                func_00103fb0(1);
                if (ui_func_001074dc(1) != 0) {
                    camp_func_001071b4();
                    engine_func_00107208();
                }
            }
            g_CrtMainState.timer_10 += 1;
            engine_func_00105338();
        }
    }

    engine_func_00102f18(0);
    if (g_CrtMainState.shutdown == 0) {
        if (g_CrtOverlayFlag == 0) {
            engine_func_001062e0();
            engine_func_00105f3c();
            engine_func_001066ac();
        }
        func_00103f8c();
        engine_func_00105848(g_CrtMainState.stereo_counter_1c >= 2 ? 1 : 0);
        if (AsdSound_GetTableEntry(1) == nullptr && g_CrtOverlayFlag == 0) {
            func_00103484();
        }
    }

    // 0x00101F04..0x00102034: frame timing.
    g_CrtMainState.tick_28 = SystemTick();
    delta = g_CrtMainState.tick_28 - g_CrtMainState.tick_20;
    elapsed = TickDeltaToMicroseconds(delta);
    fps = func_00105da4();
    g_CrtMainState.frame_load_18 =
        static_cast<u32>(static_cast<f32>(elapsed) * frame_budget / fps);

    if (g_CrtOverlayFlag == 0) {
        if (g_CrtMainState.frame_load_18 < 100) {
            func_0010527c();
        } else {
            func_00105bac();
        }
    }

    if (g_CrtMainState.shutdown != 0) {
        if (func_00103dd4() != 0) {
            battle_func_00123858();
            if (g_CrtOverlayFlag != 0) {
                func_002c5820(3);
            }
            func_0010753c();
            if (func_00104184() != 0) {
                func_00103ccc();
            }
            if (func_00104194() != 0) {
                script_vm_func_00103c20();
            }
            if (func_00105070() != 0) {
                func_001041a4();
            }
            engine_func_00104df8();
            engine_func_001034c8();
            func_00103c08();
        }
    }

    if (func_00103df4() == 2) {
        if (g_CrtOverlayFlag != 0) {
            func_002c5820(2);
        }
        func_00103c54();
        script_vm_func_002c5810();
        engine_func_00104274();
        if (g_CrtOverlayFlag != 0) {
            func_002c57fc(2);
        }
    }

    if (g_CrtMainState.shutdown != 0) {
        goto main_loop;
    }

    // 0x00102140..0x00102180: menu mode latch.
    mode = engine_func_00105194();
    if (mode == 1 || mode == 2) {
        if (g_CrtMainState.mode_latch == 0) {
            g_CrtMainState.fade_14 = 0x58;
            g_CrtMainState.mode_latch = 1;
        }
    } else if (mode == 3) {
        if (g_CrtMainState.mode_latch == 0) {
            goto label_1021fc;
        }
        func_002c0ee0();                         // 0x00102184
    }

label_102188:
    if (g_CrtMainState.shutdown != 0) {
        goto main_loop;
    }
    if (func_0010541c() == 0) {                  // 0x00102194..0x001021A0
        goto main_loop;
    }

    func_002c57c4(1);
    if (g_CrtOverlayFlag != 0) {
        func_002c5820(1);
    }
    battle_func_00123858();
    func_00106f14();
    func_00103f14();

    if (func_002c57b4() != 0) {
        goto label_1022c4;
    }
    if (func_002c57a4() == 0) {
        goto label_1022f4;
    }
    goto label_1022c4;

label_1021fc:
    // 0x001021FC..0x00102214: mode 3 shutdown path.
    if (g_CrtOverlayFlag != 0) {
        func_002c5820(0);
    }
    battle_func_00123858();
    func_00106e04();
    if (func_002c57b4() != 0) {
        goto label_10224c;
    }
    if (func_002c57a4() == 0) {
        goto label_10227c;
    }

label_10224c:
    if (g_CrtOverlayFlag != 0) {
        func_002c5820(3);
        nn_sdk_func_002c5644(0, 0, g_CrtModeContext);
    }
    g_CrtMainState.shutdown = 1;

label_10227c:
    if (g_CrtMainState.shutdown != 0) {
        goto main_loop;
    }
    if (g_CrtOverlayFlag != 0) {
        func_002c57fc(0);
    }
    script_vm_func_002c5810();
    goto label_102188;

label_1022c4:
    if (g_CrtOverlayFlag != 0) {
        func_002c5820(3);
        nn_sdk_func_002c5644(0, 0, g_CrtModeContext);
    }
    g_CrtMainState.shutdown = 1;

label_1022f4:
    if (g_CrtMainState.shutdown == 0 && g_CrtOverlayFlag != 0) {
        func_002c57fc(1);
    }

    engine_func_002c5624(1);
    goto main_loop;
}

// ---------------------------------------------------------------------------
// 0x00142BF0 -- LCD framebuffer register programming (4,008 B)
// ---------------------------------------------------------------------------

namespace {

// 0x00142E84..0x00142FA8 and repeats: map a pixel-format selector onto one
// three-bit field.  `shift` is 12 for the 0x7000 group and 8 for 0x700.
void ApplyFormatSelector(u32 selector, u32& field, u32 shift)
{
    if (selector == 0x2901u) {                   // 0x00142EDC / 0x00142F48
        field = (field & ~(7u << shift)) | (2u << shift);
    } else if (selector == 0x812Du) {            // 0x00142EEC / 0x00142F88
        field = (field & ~(7u << shift)) | (1u << shift);
    } else if (selector == 0x812Fu) {            // 0x00142EC4 / 0x00142F2C
        field &= ~(7u << shift);
    } else if (selector == 0x8130u) {            // 0x00142EFC / 0x00142F98
        field = (field & ~(7u << shift)) | (3u << shift);
    }
}

// 0x00142D60..0x00142E1C, repeated for channels 1 and 2: encode the alpha
// float into the 13-bit size field.
u32 PackAlphaSize(f32 alpha, u32 size)
{
    if (alpha == 0.0f) {                         // vcmp.f32 s0,s1 / beq
        return size & ~0x1FFFu;
    }
    u32 raw = 0;
    std::memcpy(&raw, &alpha, sizeof raw);
    if (((raw << 1) >> 24) == 0xFF) {            // lsl #1 / cmp lr,#0xff
        return size & ~0x1FFFu;
    }

    f32 scaled = (alpha + kLcdAlphaBias) * kLcdAlphaScale;
    if (0.0f > scaled) {                         // vcmpe s1,s0 / vmovgt
        scaled = 0.0f;
    }
    u32 scaled_raw = 0;
    std::memcpy(&scaled_raw, &scaled, sizeof scaled_raw);
    if (scaled_raw >= 0x46000000u) {             // vmovge.f32 s0,s3
        scaled = kLcdAlphaMax;
        scaled -= kLcdAlphaWrap;
    } else if (scaled_raw < 0x45800000u) {       // blt 0x00142DF4
        scaled += kLcdAlphaWrap;
    } else {
        scaled -= kLcdAlphaWrap;
    }
    return (size & ~0x1FFFu) | (static_cast<u32>(scaled) & 0x1FFFu);
}

// 0x00142C7C..0x00142CFC: pack config +0x18..+0x24 as R,G,B,A after scaling
// by 255.0f.  The order is [0x18] -> bits 0..7, [0x1C] -> 8..15,
// [0x20] -> 16..23 and [0x24] -> 24..31.
u32 PackColor(const LcdRenderConfig* config)
{
    u32 r = static_cast<u32>(config->color_18 * kLcdColorScale);
    u32 g = static_cast<u32>(config->color_1c * kLcdColorScale);
    u32 b = static_cast<u32>(config->color_20 * kLcdColorScale);
    u32 a = static_cast<u32>(config->color_24 * kLcdColorScale);
    return (r & 0xFFu) | ((g & 0xFFu) << 8) | ((b & 0xFFu) << 16) |
           ((a & 0xFFu) << 24);
}

// 0x00143228..0x00143288 and repeats: translate the framebuffer address,
// submit the register write and append the paired command word.
void SubmitChannel(u32 screen, LcdRegisterBlock* regs, u32 address)
{
    u32 physical = func_00147994(address);       // 0x00143228
    u32 base = *reinterpret_cast<u32*>(
        reinterpret_cast<std::uintptr_t>(regs) +
        (screen == 0 ? 0x14u : (screen == 1 ? 0x54u : 0x74u)));
    u32 value = (base & 0xC0000000u) | (physical >> 3);
    *reinterpret_cast<u32*>(
        reinterpret_cast<std::uintptr_t>(regs) +
        (screen == 0 ? 0x14u : (screen == 1 ? 0x54u : 0x74u))) = value;
    regs->flags_00 |= (screen == 0 ? 1u : (screen == 1 ? 2u : 4u));

    if (screen == 0) {
        func_002aa938(kLcdChannel0Reg, kLcdChannel0Count);
        // 0x0014325C..0x00143288: command ring slot is screen 0 only.
        // Screens 1/2 branch straight to 0x00143B7C after the register write.
        if (g_GpuCommandCursor < g_GpuCommandEnd) {
            u32* cursor = g_GpuCommandCursor;
            *cursor++ = regs->extra0_38;
            *cursor++ = kLcdCommandData;
            g_GpuCommandCursor = cursor;
        }
    } else if (screen == 1) {
        func_002aa938(kLcdChannel1Reg, kLcdChannel1Count);
    } else {
        func_002aa938(kLcdChannel2Reg, kLcdChannel2Count);
    }
}

} // namespace

// DECOMP_FUNC(0x00142bf0, 4008)
u32 func_00142bf0(LcdRenderConfig* config, u32 screen)
{
    if (config == nullptr) {
        return 0x502u;
    }

    u8* gpu = static_cast<u8*>(g_LcdGpuState);
    u8 present = gpu[0x104u + screen];           // 0x00142C10
    u32 invalid = config->address_34 == 0 ? 0x502u : 0u;

    if (present == 0 || config->address_34 == 0) {
        // 0x00142C2C..0x00142C78: disable one screen bit and return.
        LcdRegisterBlock* regs =
            reinterpret_cast<LcdRegisterBlock*>(gpu + 0x770);
        if (screen == 0) {
            regs->flags_00 &= ~1u;
        } else if (screen == 1) {
            regs->flags_00 &= ~2u;
        } else if (screen == 2) {
            regs->flags_00 &= ~4u;
        } else {
            return 0x501u;                       // 0x00142C54 / 0x00142C64
        }
        return present != 0 ? invalid : 0u;      // 0x00142C6C..0x00142C78
    }

    // 0x00142C7C..0x00142D14: packed colour and channel selection.
    u32 packed = PackColor(config);
    if (screen > 2) {
        return 0;                                // 0x00142D10 / 0x00143B80
    }

    LcdRegisterBlock* regs =
        reinterpret_cast<LcdRegisterBlock*>(gpu + 0x770);
    u32* color = nullptr;
    u32* format = nullptr;
    u32* control = nullptr;
    u32* size = nullptr;
    u32* extra = nullptr;
    if (screen == 0) {
        color = &regs->color0_04;
        format = &regs->format0_08;
        control = &regs->control0_0c;
        size = &regs->size0_10;
        extra = &regs->extra0_38;
    } else if (screen == 1) {
        color = &regs->color1_44;
        format = &regs->format1_48;
        control = &regs->control1_4c;
        size = &regs->size1_50;
        extra = &regs->extra1_58;
    } else {
        color = &regs->color2_64;
        format = &regs->format2_68;
        control = &regs->control2_6c;
        size = &regs->size2_70;
        extra = &regs->extra2_78;
    }

    *color = packed;                              // 0x00142D1C / 0x001435A8

    // 0x00142D28..0x00142D5C: geometry fields from config +0x40/+0x44.
    *format = (*format & ~0x7FF07FFu) |
              ((config->field_40 << 16) & 0x07FF0000u) |
              (config->field_44 & 0x7FFu);

    // 0x00142D60..0x00142E1C: alpha-derived size field.
    *size = PackAlphaSize(config->alpha_28, *size);

    // 0x00142E1C..0x00142E34: config +0x50 low nibble into channel +0x38.
    *extra = (*extra & ~0xFu) | (config->field_50 & 0xFu);

    // 0x00142E38..0x00142E7C (screen 0) and 0x00143330..0x00143384
    // (screens 1/2): the accepted mode sets differ per screen.
    u32 mode = config->mode_48;
    u32 count_mask = 0;
    s32 nibble_source = 0;
    u32 nibble = 0;
    bool mode_ok = false;
    if (screen == 0) {
        mode_ok = (mode >= 0x1906u && mode <= 0x190Au) ||
                  mode == 0x191Au || mode == 0x1FCAu || mode == 0x2025u;
    } else {
        mode_ok = (mode >= 0x1906u && mode <= 0x190Au) ||
                  mode == 0x6050u || mode == 0x6700u ||
                  mode == 0x675Au || mode == 0x675Bu;
    }
    if (!mode_ok) {
        return 0x502u;                           // 0x00142E7C
    }

    // 0x00142E44 / 0x00142E64 and 0x00143340..0x00143368: the fixed 2D
    // modes branch to their own path and never run the 0x6E00/format/
    // mode_04 sequence below.  The channel 1/2 form is at 0x00143630 /
    // 0x00143AA8.
    if (screen == 0 && mode == 0x190Au) {
        // 0x001431B8..0x001431F0.
        *control &= ~0x71000000u;
        *size &= ~0xF000000u;
        *size &= ~0xF0000u;
        *control |= 0x20000006u;
        *control |= 0x100000u;
        *control = (*control & ~0x7000u & ~0x730u) | 0x1100u;
        goto submit;
    }
    if (screen == 0 && mode == 0x191Au) {
        // 0x001431F4..0x00143224.
        *control &= ~0x30u;
        *size &= ~0xF000000u;
        *size &= ~0xF0000u;
        *control &= ~0x70000000u;
        *control &= ~6u;
        *control &= ~0x7700u;
        *color = 0;
        goto submit;
    }
    if (screen != 0 && mode == 0x6050u) {
        // 0x00143630..0x00143658 / 0x00143AA8..0x00143AD4.
        *control = (*control & ~2u & ~4u & ~0x7700u);
        *size &= ~0xF000000u;
        *size &= ~0xF0000u;
        *color = 0;
        goto submit;
    }

    // 0x00142E84..0x00142E9C: set the 0x30000000 field from gpu+0xF8.
    {
        u32 mode_flag = *reinterpret_cast<u32*>(gpu + 0xF8);
        if (mode_flag == 0x6E00u) {
            *control = (*control & ~0x70000000u) | 0x30000000u;
        } else {
            *control &= ~0x70000000u;
        }
    }

    // 0x00142EA0..0x00142FA4: two pixel-format selectors.
    ApplyFormatSelector(config->format_08, *control, 12);
    ApplyFormatSelector(config->format_0c, *control, 8);

    // 0x00142FA8..0x00142FD0: mode_00 bit 1.
    if (config->mode_00 == 0x2600u) {
        *control &= ~2u;
    } else if (config->mode_00 == 0x2601u) {
        *control |= 2u;
    }

    // 0x00142FD4..0x001431B0: mode_04 branches.
    count_mask = ((config->count_68 - 1u) & 0xFu) << 16;
    nibble_source = static_cast<s32>(config->field_14);
    nibble = nibble_source < 0 ? 0u
                               : (static_cast<u32>(nibble_source) & 0xFu);
    switch (config->mode_04) {
    case 0x2600u:                               // 0x00143020
        *size &= ~0xF000000u;
        *control &= ~4u;
        *size &= ~0xF0000u;
        *control &= ~0x1000000u;
        break;
    case 0x2601u:                               // 0x001430EC
        *size &= ~0xF000000u;
        *control |= 4u;
        *size &= ~0xF0000u;
        *control &= ~0x1000000u;
        break;
    case 0x2700u:                               // 0x00143044
        *control &= ~4u;
        *size = (*size & ~0xF0000u) | (*control & count_mask);
        *size = (*size & ~0xF000000u) | (nibble << 24);
        *control &= ~0x1000000u;
        break;
    case 0x2701u:                               // 0x00143130
        *control |= 4u;
        *size = (*size & ~0xF0000u) | (*control & count_mask);
        *size = (*size & ~0xF000000u) | (nibble << 24);
        *control &= ~0x1000000u;
        break;
    case 0x2702u:                               // 0x00143098
        *control |= 4u;
        *size = (*size & ~0xF0000u) | (*control & count_mask);
        *size = (*size & ~0xF000000u) | (nibble << 24);
        *control |= 0x1000000u;
        break;
    case 0x2703u:                               // 0x00143170
        *control |= 4u;
        *size = (*size & ~0xF0000u) | (*control & count_mask);
        *size = (*size & ~0xF000000u) | (nibble << 24);
        *control |= 0x1000000u;
        break;
    default:
        break;
    }

    // 0x0014310C..0x0014312C: 0x675A selects control bits 0x30 = 2.
    if (mode == 0x675Au) {
        *control = (*control & ~0x30u) | 0x20u;
    }

submit:
    SubmitChannel(screen, regs, config->address_34);
    return 0;                                    // 0x00143B80
}

// ---------------------------------------------------------------------------
// 0x002831F0 -- camp layout byte-stream interpreter (3,784 B)
// ---------------------------------------------------------------------------

namespace {

// The byte code is (bit 7 = variant, bits 0..6 = field opcode).  The two
// variants are the two literals immediately below the branch in the listing.
// 0x002B7F0A..0x002B7F90: Thumb sorted insertion.  r0 is the destination
// array, r1 is a **count** (not a slot), r2 the element size and r3 a
// comparator callback (invoked as `blx r2` with (previous, new) pointers).
// 0x002B7F24..0x002B7F2C computes dest + (count-1)*size, and the loop covers
// [0, count), so the new element is the last slot.
using CampCompareFn = s32 (*)(const void*, const void*);

void CampInsertionSort(u8* base, u32 count, u32 size, CampCompareFn compare,
                       u32 copy_size)
{
    // 0x002B7F30..0x002B7F88 (and the stack-buffered 0x002B7D0C form):
    // insertion sort over [0, count).  The first pass is a no-op, so the
    // loop starts at element 1.
    for (u32 i = 1; i < count; ++i) {
        u8 temp[16] = {};
        u8* element = base + i * size;
        std::memcpy(temp, element, copy_size);
        u32 position = i;
        while (position > 0) {
            u8* previous = base + (position - 1) * size;
            if (compare(previous, temp) <= 0) {  // 0x002B7F44 `cmp r0,#0`
                break;
            }
            std::memmove(base + position * size, previous, copy_size);
            --position;
        }
        std::memcpy(base + position * size, temp, copy_size);
    }
}

void CampInsert(void* dest, u32 count, u32 size, u32 callback)
{
    if (count == 0 || size == 0 || callback == 0) {
        return;
    }
    u8* base = static_cast<u8*>(dest);
    const u32 copy_size = size < 16u ? size : 16u;
    CampCompareFn compare =
        reinterpret_cast<CampCompareFn>(static_cast<std::uintptr_t>(callback));

    // 0x002B7F1A..0x002B7F20: counts above 0xA use the stack-buffered
    // insertion helper at 0x002B7D0C, which has the same ordering contract.
    if (count > 0xA) {
        CampInsertionSort(base, count, size, compare, copy_size);
        return;
    }
    CampInsertionSort(base, count, size, compare, copy_size);
}

struct CampRule {
    u32 dest;       // r0 at the 0x002B7F0A call
    u32 source;     // r0 passed to camp_func_0029f0f4 / stream pointer
    u32 size;       // r2 (8 for the first eight bytes, 2 afterwards)
    u32 variant0;   // callback when bit 7 is clear (`lsrs r0,r0,#7` == 0)
    u32 variant1;   // callback when bit 7 is set
    u8  opcode;     // low seven bits
    bool from_source; // false when r1 is the precomputed counter
    u32 value;      // precomputed r1 for the counter rule
};

void InvokeCamp(const CampRule& rule, u32 stream)
{
    u8* dest = reinterpret_cast<u8*>(static_cast<std::uintptr_t>(rule.dest));
    u8* source =
        reinterpret_cast<u8*>(static_cast<std::uintptr_t>(rule.source));
    u8 current = *reinterpret_cast<u8*>(static_cast<std::uintptr_t>(stream));
    if ((current & 0x7Fu) != rule.opcode) {
        return;
    }
    u32 resolved = rule.value;
    if (rule.from_source) {
        resolved = camp_func_0029f0f4(source);   // 0x00283288 and repeats
    }
    u32 target = (current & 0x80u) ? rule.variant1 : rule.variant0;
    CampInsert(dest, resolved, rule.size, target); // 0x002B7F0A
}

bool CampRuleMatches(u32 stream, u8 opcode)
{
    return (*reinterpret_cast<u8*>(static_cast<std::uintptr_t>(stream)) &
            0x7Fu) == opcode;
}

} // namespace

// DECOMP_FUNC(0x002831f0, 3784)
void camp_func_002831f0(u32 layout_opcode)
{
    u8* gpu = static_cast<u8*>(g_CampLayoutRoot);
    void* table = camp_func_002a0fac();          // 0x00283200
    u32 stream = reinterpret_cast<std::uintptr_t>(table);

    switch (layout_opcode) {
    case 9: {
        // 0x00283260..0x0028349C.
        u32 dest = reinterpret_cast<std::uintptr_t>(gpu + 0xC23C);
        u32 source = reinterpret_cast<std::uintptr_t>(gpu + 0x1DC);
        u32 cursor = stream + 1;
        CampRule rules[] = {
            {dest, source, 8, 0x0025779C, 0x00249950, 0x0B, true, 0},
            {dest, source, 8, 0x0021910C, 0x002F26F4, 0x20, true, 0},
            {dest, source, 8, 0x001F5E38, 0x002DC6C4, 0x0D, true, 0},
            {dest, source, 8, 0x002C6CA4, 0x002F80E4, 0x0F, true, 0},
            {dest, source, 8, 0x00218FE8, 0x002F25D0, 0x11, true, 0},
            {dest, source, 8, 0x0021904C, 0x002F2634, 0x03, true, 0},
        };
        for (const CampRule& rule : rules) {
            if (CampRuleMatches(cursor, rule.opcode)) {
                InvokeCamp(rule, cursor);
                return;
            }
        }
        return;
    }
    case 10: {
        // 0x002834A0..0x00283678.  The counter loop re-evaluates
        // camp_func_0029f0f4 on every iteration.
        u32 count_slot = reinterpret_cast<std::uintptr_t>(gpu + 0x240);
        u32 dest = reinterpret_cast<std::uintptr_t>(gpu + 0x1DB4);
        u32 cursor = stream + 2;
        u32 nonzero = 0;
        u32 count = camp_func_0029f0f4(
            reinterpret_cast<void*>(count_slot));
        for (u32 i = 0; i != count; ++i) {
            u16 value = *reinterpret_cast<u16*>(
                reinterpret_cast<std::uintptr_t>(gpu) + 0x1DB4u + i * 2u);
            if (value != 0) {
                nonzero += 1;
            }
            count = camp_func_0029f0f4(
                reinterpret_cast<void*>(count_slot));
        }
        CampRule rules[] = {
            {dest, cursor, 2, 0x002E4684, 0x003132B0, 0x0B, false, nonzero},
            {dest, cursor, 2, 0x002DCC78, 0x0030BE4C, 0x0E, false, nonzero},
            {dest, cursor, 2, 0x002E446C, 0x003131E8, 0x0F, false, nonzero},
            {dest, cursor, 2, 0x002DC52C, 0x0030BCB4, 0x11, false, nonzero},
            {dest, cursor, 2, 0x002DC5CC, 0x0030BD54, 0x03, false, nonzero},
        };
        for (const CampRule& rule : rules) {
            if (CampRuleMatches(cursor, rule.opcode)) {
                InvokeCamp(rule, cursor);
                return;
            }
        }
        return;
    }
    case 11: {
        // 0x0028367C..0x00283798.
        u32 dest = reinterpret_cast<std::uintptr_t>(gpu + 0x147C);
        u32 source = reinterpret_cast<std::uintptr_t>(gpu + 0x0B0);
        u32 cursor = stream + 3;
        CampRule rules[] = {
            {dest, source, 2, 0x00219540, 0x002F284C, 0x0C, true, 0},
            {dest, source, 2, 0x00206F30, 0x002E49EC, 0x10, true, 0},
            {dest, source, 2, 0x00206F7C, 0x002E4A38, 0x03, true, 0},
        };
        for (const CampRule& rule : rules) {
            if (CampRuleMatches(cursor, rule.opcode)) {
                InvokeCamp(rule, cursor);
                return;
            }
        }
        return;
    }
    case 12:
    case 14:
    case 15:
    case 16:
    case 24:
        return;                                   // 0x00283220
    case 13: {
        // 0x0028379C..0x002838B8.
        u32 dest = reinterpret_cast<std::uintptr_t>(gpu + 0x1CC4);
        u32 source = reinterpret_cast<std::uintptr_t>(gpu + 0x178);
        u32 cursor = stream + 4;
        CampRule rules[] = {
            {dest, source, 2, 0x002E4968, 0x0031339C, 0x21, true, 0},
            {dest, source, 2, 0x002E491C, 0x00313350, 0x10, true, 0},
            {dest, source, 2, 0x002E4998, 0x003133C8, 0x03, true, 0},
        };
        for (const CampRule& rule : rules) {
            if (CampRuleMatches(cursor, rule.opcode)) {
                InvokeCamp(rule, cursor);
                return;
            }
        }
        return;
    }
    case 17:
    case 18: {
        // 0x002838BC..0x00283A64.  The original opcode selects both the
        // destination and the stream offset (r7+5 or r7+6).
        u32 dest = 0;
        u32 source = 0;
        u32 cursor = 0;
        // 0x002838BC compares the incoming opcode with 0x11 and 0x12:
        // 17 (0x11) -> 0x002838D0, 18 (0x12) -> 0x002838E4.
        if (layout_opcode == 0x11) {              // case 17
            dest = reinterpret_cast<std::uintptr_t>(gpu + 0x1C27C);
            source = reinterpret_cast<std::uintptr_t>(gpu + 0x2A4);
            cursor = stream + 5;
        } else if (layout_opcode == 0x12) {       // case 18
            dest = reinterpret_cast<std::uintptr_t>(gpu + 0x1C36C);
            source = reinterpret_cast<std::uintptr_t>(gpu + 0x308);
            cursor = stream + 6;
        } else {
            return;                               // 0x002838F4 with no match
        }
        CampRule rules[] = {
            {dest, source, 2, 0x00206DCC, 0x002E47B8, 0x06, true, 0},
            {dest, source, 2, 0x002E4764, 0x003132FC, 0x11, true, 0},
            {dest, source, 2, 0x002DCCD0, 0x0030BEA4, 0x12, true, 0},
            {dest, source, 2, 0x002193E0, 0x002F27A0, 0x03, true, 0},
        };
        for (const CampRule& rule : rules) {
            if (CampRuleMatches(cursor, rule.opcode)) {
                InvokeCamp(rule, cursor);
                return;
            }
        }
        return;
    }
    case 19: {
        // 0x00283A68..0x00283BA8.
        u32 dest = reinterpret_cast<std::uintptr_t>(gpu + 0x205C);
        u32 source = reinterpret_cast<std::uintptr_t>(gpu + 0x36C);
        u32 cursor = stream + 7;
        CampRule rules[] = {
            {dest, source, 2, 0x00206DCC, 0x002E47B8, 0x06, true, 0},
            {dest, source, 2, 0x00219434, 0x002F27F4, 0x1F, true, 0},
            {dest, source, 2, 0x00206D38, 0x002E46D0, 0x13, true, 0},
            {dest, source, 2, 0x002193E0, 0x002F27A0, 0x03, true, 0},
        };
        for (const CampRule& rule : rules) {
            if (CampRuleMatches(cursor, rule.opcode)) {
                InvokeCamp(rule, cursor);
                return;
            }
        }
        return;
    }
    case 20:
    case 21:
    case 22: {
        // 0x00283BAC..0x00283EF4.
        u32 dest = 0;
        u32 source = 0;
        u32 cursor = 0;
        if (layout_opcode == 0x14) {              // case 20
            dest = reinterpret_cast<std::uintptr_t>(gpu + 0x20C0);
            source = reinterpret_cast<std::uintptr_t>(gpu + 0x3D0);
            cursor = stream + 8;
        } else if (layout_opcode == 0x15) {       // case 21
            dest = reinterpret_cast<std::uintptr_t>(gpu + 0x21B0);
            source = reinterpret_cast<std::uintptr_t>(gpu + 0x434);
            cursor = stream + 9;
        } else if (layout_opcode == 0x16) {       // case 22
            dest = reinterpret_cast<std::uintptr_t>(gpu + 0x22A0);
            source = reinterpret_cast<std::uintptr_t>(gpu + 0x498);
            cursor = stream + 10;
        } else {
            return;                               // no matching arm
        }
        CampRule rules[] = {
            {dest, source, 2, 0x001F6384, 0x002DCE58, 0x04, true, 0},
            {dest, source, 2, 0x00206EF0, 0x002E48DC, 0x24, true, 0},
            {dest, source, 2, 0x00206E30, 0x002E481C, 0x25, true, 0},
            {dest, source, 2, 0x00206EB0, 0x002E489C, 0x26, true, 0},
            {dest, source, 2, 0x00206D8C, 0x002E4724, 0x27, true, 0},
            {dest, source, 2, 0x00206E70, 0x002E485C, 0x28, true, 0},
            {dest, source, 2, 0x002193E0, 0x002F27A0, 0x03, true, 0},
            {dest, source, 2, 0x002DCD68, 0x0030BF38, 0x32, true, 0},
        };
        for (const CampRule& rule : rules) {
            if (CampRuleMatches(cursor, rule.opcode)) {
                InvokeCamp(rule, cursor);
                return;
            }
        }
        return;
    }
    case 23: {
        // 0x00283EF8..0x00283FB8.
        u32 dest = reinterpret_cast<std::uintptr_t>(gpu + 0x2390);
        u32 source = reinterpret_cast<std::uintptr_t>(gpu + 0x4FC);
        u32 cursor = stream + 0x0B;
        CampRule rules[] = {
            {dest, source, 2, 0x002DCD38, 0x0030BF0C, 0x33, true, 0},
            {dest, source, 2, 0x002193E0, 0x002F27A0, 0x03, true, 0},
        };
        for (const CampRule& rule : rules) {
            if (CampRuleMatches(cursor, rule.opcode)) {
                InvokeCamp(rule, cursor);
                return;
            }
        }
        return;
    }
    default:
        return;                                   // 0x00283220
    }
}

} // namespace smt4::engine
