#include "engine/runtime_blocks.h"

#include <cstring>

#include "engine/asd_symbols.h"

// 0x00101B80 / 0x00101F08 execute `svc #0x28`, the nnSdk system-tick import.
// The host build leaves the import unresolved; callers must supply it when the
// reconstructed frame loop is linked into a runnable image.
namespace nn {
namespace os {
u64 GetSystemTick();
} // namespace os
} // namespace nn

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

// 0x00101308 helpers -------------------------------------------------------
void engine_func_002c5fbc();
void engine_func_001076d8(u32 a, u32 b);
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
void script_vm_func_001041d8();
f32* script_vm_func_002c5e20();
void* func_00104db0();
void* script_vm_func_002c5e10();
void* AsdGxCommandList_func_002c5d90();
void ui_func_00102aa0();
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
void AsdModelProcess_func_00103ff8(u32 a, u32 b, u32 c, u32 d);
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
// Note: func_002aa938 declared canonically in include/engine/runtime_blocks.h

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
CrtMainState g_CrtMainState{0, 1};      // 0x00446DB0, .word 0x00000100
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

// 0x003B1B08..0x003B1D64: append one 16-byte element to the vector at
// state+0x1434, growing it through func_0022c198 and destroying the moved
// range through func_0022c6f8.  `source` is the link record at node+0x14;
// 0x003B1F60..0x003B1F90 copies [source], [source+4] and [source+0xC], writes
// the self pointer at dest+8 and repairs both back-links.  A failed growth
// allocation returns 0x44 (0x003B1DC8..0x003B1D4C / 0x003B2038).
u32 AppendNode(ScriptRuntimeState* state, u8* source)
{
    ScriptNodeVector& vec = state->nodes;
    ScriptNode16* dest = nullptr;
    if (vec.capacity >= vec.size + 1) {
        // 0x003B1F54..0x003B1F60: append at begin + size*16.
        dest = vec.begin + vec.size;
        vec.size += 1;
    } else {
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
            return 0x44u;                           // 0x003B1E48 / 0x003B2038
        }
        ScriptNode16* fresh = reinterpret_cast<ScriptNode16*>(storage);
        for (u32 i = 0; i < vec.size; ++i) {
            fresh[i] = vec.begin[i];
        }
        dest = fresh + vec.size;
        func_0022c6f8(&vec, 0, vec.size);           // 0x003B1F30
        vec.begin = fresh;
        vec.capacity = new_capacity;
        vec.size += 1;
    }

    // 0x003B1F70..0x003B1F90: copy the three link words, then store the
    // self pointer and update the two neighbours.
    u32* const links = reinterpret_cast<u32*>(source);
    dest->link_00 = links[0];                       // node+0x14
    dest->link_04 = links[1];                       // node+0x18
    dest->link_0c = links[3];                       // node+0x20
    u8* const tail = reinterpret_cast<u8*>(
        static_cast<std::uintptr_t>(dest->link_0c));
    *reinterpret_cast<u32*>(tail + 0x08) =
        static_cast<u32>(reinterpret_cast<std::uintptr_t>(dest));
    dest->link_08 = static_cast<u32>(reinterpret_cast<std::uintptr_t>(source));
    links[3] = static_cast<u32>(reinterpret_cast<std::uintptr_t>(dest));
    return 0;
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

// 0x003B1864..0x003B18B4: in-order successor on the command tree.  Nodes use
// +0x04 parent, +0x08 left and +0x0C right; the caller stops when the returned
// node reaches the header computed at 0x003B15B8..0x003B15E0.
u8* CommandTreeSuccessor(u8* node)
{
    u8* right = *reinterpret_cast<u8**>(node + 0x0C);
    if (right != nullptr) {
        node = right;
        while (*reinterpret_cast<u8**>(node + 0x08) != nullptr) {
            node = *reinterpret_cast<u8**>(node + 0x08);
        }
        return node;
    }

    u8* parent = *reinterpret_cast<u8**>(node + 0x04);
    while (node == *reinterpret_cast<u8**>(parent + 0x0C)) {
        node = parent;
        parent = *reinterpret_cast<u8**>(parent + 0x04);
    }
    if (*reinterpret_cast<u8**>(node + 0x0C) != parent) {
        node = parent;
    }
    return node;
}

} // namespace

// ---------------------------------------------------------------------------
// 0x003B11A8 -- event command dispatch (4,548 B)
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x003b11a8, 4548)
#if 0
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
                // 0x003B1B08..0x003B1D64: append the link record at node+0x14.
                if (AppendNode(state, node + 0x14) == 0x44u) {
                    goto fail_44;
                }
                goto finish;
            }
        }

        // 0x003B1578..0x003B1814: locate the insertion point in the command
        // tree at state+0x1414.  The sentinel is the word at command_tree+0x14;
        // nodes carry key +0x10, left +0x08, right +0x0C, parent +0x04 and a
        // payload pointer at +0x18.  `lower` is the first node whose key is
        // greater than or equal to payload+0x14.
        {
            u8* const command_tree = state->command_tree;
            u8* const sentinel = *reinterpret_cast<u8**>(command_tree + 0x14);
            const u32 payload_key =
                *reinterpret_cast<u32*>(static_cast<u8*>(variant) + 0x14);
            u8* lower = sentinel;
            u8* node_walk = *reinterpret_cast<u8**>(sentinel + 0x04);
            while (node_walk != nullptr) {
                if (*reinterpret_cast<u32*>(node_walk + 0x10) < payload_key) {
                    node_walk = *reinterpret_cast<u8**>(node_walk + 0x0C);
                } else {
                    lower = node_walk;
                    node_walk = *reinterpret_cast<u8**>(node_walk + 0x08);
                }
            }

            // 0x003B15B8..0x003B15E0: the walk terminator starts at the
            // sentinel and follows the last "key < node key" branch of a
            // second root-to-leaf descent.
            u8* header = sentinel;
            node_walk = *reinterpret_cast<u8**>(sentinel + 0x04);
            while (node_walk != nullptr) {
                if (payload_key <
                    *reinterpret_cast<u32*>(node_walk + 0x10)) {
                    header = node_walk;
                    node_walk = *reinterpret_cast<u8**>(node_walk + 0x08);
                } else {
                    node_walk = *reinterpret_cast<u8**>(node_walk + 0x0C);
                }
            }

            // 0x003B15F4: an empty lower bound takes the direct child-record
            // path; otherwise the command tree is walked first.
            if (lower == sentinel) {
                if (CreateChildRecord(state, index,
                                      static_cast<u8*>(variant)) == 0x44u) {
                    goto fail_44;
                }
                goto finish;
            }

            // 0x003B1818..0x003B18C0: reject when any pending child is
            // already enabled and notify the parent once.
            for (u8* walk = lower; walk != header;
                 walk = CommandTreeSuccessor(walk)) {
                u8* child =
                    *reinterpret_cast<u8**>(walk + 0x18);   // payload
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
            }

            // 0x003B18C0..0x003B1974: find the matching payload, let virtual
            // slot 5 bind it and flag the returned child as enabled.
            for (u8* walk = lower; walk != header;
                 walk = CommandTreeSuccessor(walk)) {
                u8* payload = *reinterpret_cast<u8**>(walk + 0x18);
                if (*reinterpret_cast<u32*>(payload + 0x04) !=
                    *reinterpret_cast<u32*>(
                        static_cast<u8*>(variant) + 0x04)) {
                    continue;
                }
                void** payload_vtable = *reinterpret_cast<void***>(payload);
                using Slot5 = u8* (*)(void*, void*);
                u8* matched = reinterpret_cast<Slot5>(
                    payload_vtable[5])(payload, variant);   // 0x003B18F0
                if (matched != nullptr) {
                    u8* child =
                        *reinterpret_cast<u8**>(matched + 0x10); // 0x003B1904
                    *reinterpret_cast<u8*>(child + 0x70) = 1;    // 0x003B1908
                    goto finish;
                }
            }
        }

        // 0x003B1978..0x003B1B04: no match, insert the child record.
        if (CreateChildRecord(state, index, static_cast<u8*>(variant)) == 0x44u) {
            goto fail_44;
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
#endif

// Readable script-runtime cursor operation draft above; exact ARM body retained pending codegen recovery.
__attribute__((naked)) u32 func_003b11a8(ScriptRuntimeState* state, u32 index, ScriptCursor* cursor,
                  u32 end) {
    asm volatile(
        ".word 0xe92d4fff, 0xe24dd08c, 0xe1a08001, 0xe1a09000\n"
        ".word 0xe28d101c, 0xe59d0094, 0xe5900000, 0xe1cd29d4\n"
        ".word 0xe0800008, 0xebfffc77, 0xe3500000, 0xe2890b05\n"
        ".word 0xe2800078, 0xe58d0060, 0xe2890b05, 0xe280007c\n"
        ".word 0xe58d0064, 0xe2890b05, 0xe2800087, 0xe58d0068\n"
        ".word 0xe2890b05, 0xe2800089, 0xe58d006c, 0x0a000443\n"
        ".word 0xe59d0094, 0xe28d1070, 0xe5900000, 0xe1cd29d4\n"
        ".word 0xe0800008, 0xebfffc63, 0xe3500000, 0x0a00043b\n"
        ".word 0xe59d301c, 0xe3530000, 0x0a000083, 0xe2896b05\n"
        ".word 0xe286606c, 0xe2891b05, 0xe5960000, 0xe2811044\n"
        ".word 0xe2894b05, 0xe58d0074, 0xe58d1038, 0xe5910004\n"
        ".word 0xe284404c, 0xe1a02004, 0xe1500002, 0xe1a01002\n"
        ".word 0x0a000006, 0xe590c010, 0xe15c0003, 0x35900004\n"
        ".word 0x21a01000, 0x25900000, 0xe1500002, 0x1afffff8\n"
        ".word 0xe1510004, 0x15910010, 0x11500003, 0xe59d0038\n"
        ".word 0x81a01004, 0xe2800008, 0xe1510000, 0x1a00009d\n"
        ".word 0xe3a02000, 0xe1a01003, 0xe28d0074, 0xebfffbc0\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000360, 0xe5963000\n"
        ".word 0xe58d002c, 0xe59d001c, 0xe58d3028, 0xe58d3040\n"
        ".word 0xe58d003c, 0xe28d0040, 0xe59d4038, 0xe59d202c\n"
        ".word 0xe58d0030, 0xe58d0034, 0xe28d1028, 0xe3a00000\n"
        ".word 0xe58d104c, 0xe58d2044, 0xe58d1048, 0xe5cd0054\n"
        ".word 0xe5943004, 0xe2847008, 0xe1a02007, 0xe1530002\n"
        ".word 0x159d303c, 0xe28db050, 0xe28da03c, 0xe2841004\n"
        ".word 0xe1a05002, 0xe1a00002, 0x0a000008, 0xe5911000\n"
        ".word 0xe1a05001, 0xe591c010, 0xe15c0003, 0x32851004\n"
        ".word 0x21a00005, 0xe591c000, 0xe15c0002, 0x1afffff6\n"
        ".word 0xe1500007, 0xe58d1014, 0x0a000005, 0xe5902010\n"
        ".word 0xe59d103c, 0xe1520001, 0x93a01000, 0x95cb1004\n"
        ".word 0x9a00001f, 0xe5940024, 0xe3a01024, 0xe5902000\n"
        ".word 0xe5922000, 0xe12fff32, 0xe1b07000, 0x0a000033\n"
        ".word 0xe2970010, 0x0a00000a, 0xe59d103c, 0xe4801004\n"
        ".word 0xe5ba1004, 0xe5801000, 0xe59a1004, 0xe5801004\n"
        ".word 0xe59a100c, 0xe580100c, 0xe5810008, 0xe580a008\n"
        ".word 0xe58a000c, 0xe5875008, 0xe3570000, 0x02840008\n"
        ".word 0x0a000007, 0xe59d0014, 0xe1a01007, 0xe5807000\n"
        ".word 0xe1a00004, 0xebff9759, 0xe3a00001, 0xe5cb0004\n"
        ".word 0xe1a00007, 0xe59d1048, 0xe58d0050, 0xe28d0040\n"
        ".word 0xe3510000, 0x11510000, 0x1a00001b, 0xe59d0044\n"
        ".word 0xe3500000, 0x0a000020, 0xe5901000, 0xe5911000\n"
        ".word 0xe12fff31, 0xe59d0040, 0xe59d1044, 0xe5902000\n"
        ".word 0xe5922004, 0xe12fff32, 0xea000017, 0xe59d0094\n"
        ".word 0xe59d1070, 0xe5900000, 0xe0811000, 0xe59d0094\n"
        ".word 0xe5801000, 0xe3a00c01, 0xe28dd09c, 0xe8bd8ff0\n"
        ".word 0xe5940024, 0xe3a02024, 0xe5901000, 0xe5913008\n"
        ".word 0xe28f1fc3, 0xe12fff33, 0xeaffffd2, 0xe1cd04d8\n"
        ".word 0xe28d3048, 0xe580100c, 0xe8930006, 0xe3a00000\n"
        ".word 0xe5821008, 0xe58d0048, 0xe58d004c, 0xe3a04000\n"
        ".word 0xe58d4044, 0xe59d1030, 0xe28d0028, 0xe3510000\n"
        ".word 0x11510000, 0x1a00000b, 0xe59d002c, 0xe3500000\n"
        ".word 0x0a00000e, 0xe5901000, 0xe5911000, 0xe12fff31\n"
        ".word 0xe59d0028, 0xe59d102c, 0xe5902000, 0xe5922004\n"
        ".word 0xe12fff32, 0xea000005, 0xe59d0034, 0xe581000c\n"
        ".word 0xe1cd03d0, 0xe5810008, 0xe58d4030, 0xe58d4034\n"
        ".word 0xe59d0038, 0xe59d1050, 0xe58d402c, 0xe2800008\n"
        ".word 0xe1510000, 0x0a0002c9, 0xe58d1034, 0xe5915018\n"
        ".word 0xe59d2070, 0xe2814010, 0xe5950008, 0xe1500002\n"
        ".word 0x1a0000a3, 0xe59d0094, 0xe5951000, 0xe5900000\n"
        ".word 0xe591300c, 0xe0801008, 0xe1a00005, 0xe12fff33\n"
        ".word 0xe3500000, 0x0a00009a, 0xe5950000, 0xe5901010\n"
        ".word 0xe1a00005, 0xe12fff31, 0xe3500000, 0x0a000163\n"
        ".word 0xe289cb05, 0xe28cc014, 0xe5952014, 0xe59c1014\n"
        ".word 0xe28d4058, 0xe1a0700c, 0xe5910004, 0xe3500000\n"
        ".word 0x0a000006, 0xe5903010, 0xe1530002, 0x21a01000\n"
        ".word 0x25900008, 0x3590000c, 0xe3500000, 0x1afffff8\n"
        ".word 0xe5973014, 0xe5930004, 0xe3500000, 0x0a000006\n"
        ".word 0xe590c010, 0xe152000c, 0x31a03000, 0x35900008\n"
        ".word 0x2590000c, 0xe3500000, 0x1afffff8, 0xe58d1058\n"
        ".word 0xe5843004, 0xe5970014, 0xe59d1058, 0xe1510000\n"
        ".word 0x1a000086, 0xe5960000, 0xe5901000, 0xe5912000\n"
        ".word 0xe3a01074, 0xe12fff32, 0xe3500000, 0x0a00028b\n"
        ".word 0xe5963000, 0xe3a02000, 0xe280104c, 0xe5803000\n"
        ".word 0xe5802008, 0xe5803004, 0xe580200c, 0xe5802010\n"
        ".word 0xe5802014, 0xe5802018, 0xe1c021fc, 0xe5802024\n"
        ".word 0xe5802028, 0xe1c022fc, 0xe5802034, 0xe5802038\n"
        ".word 0xe580203c, 0xe5802040, 0xe5802044, 0xe5802048\n"
        ".word 0xe5801058, 0xe5802050, 0xe580304c, 0xe5801054\n"
        ".word 0xe5802060, 0xe580305c, 0xe5802064, 0xe5802068\n"
        ".word 0xe580206c, 0xe3a03001, 0xe5c03070, 0xe5951014\n"
        ".word 0xe1a04000, 0xe2892010, 0xebfff79f, 0xe59d101c\n"
        ".word 0xe1a02004, 0xe28d0074, 0xebfffac1, 0xe1b04000\n"
        ".word 0xe320f000, 0x0a000261, 0xe5940000, 0xe1a08005\n"
        ".word 0xe1a01005, 0xe5902018, 0xe1a00004, 0xe12fff32\n"
        ".word 0xe5940000, 0xe5901010, 0xe1a00004, 0xe12fff31\n"
        ".word 0xe3500000, 0x15981014, 0xe28d0020, 0xe28d2030\n"
        ".word 0x15841014, 0xe5953014, 0xe596c000, 0xe58d0054\n"
        ".word 0xe58d0050, 0xe28d1048, 0xe28d0044, 0xe58d4024\n"
        ".word 0xe58dc020, 0xe58d404c, 0xe58d102c, 0xe8801008\n"
        ".word 0xe28d803c, 0xe59d3048, 0xe59d1044, 0xe28d0048\n"
        ".word 0xe58d3034, 0xe59d304c, 0xe58d1030, 0xe2821004\n"
        ".word 0xe58d3038, 0xe59d3054, 0xe58d1028, 0xe58d1054\n"
        ".word 0xe8880009, 0xe1a01007, 0xe28d0018, 0xeb012cc0\n"
        ".word 0xe28d0034, 0xe320f000, 0xebf9ea95, 0xe28d0048\n"
        ".word 0xe320f000, 0xebf9ea92, 0xe28d0020, 0xe320f000\n"
        ".word 0xea0000dc, 0x694c6f4d, 0x3a3a6576, 0x6f6c6c41\n"
        ".word 0x6f746163, 0x6e203a72, 0x6520746f, 0x67756f6e\n"
        ".word 0x656d2068, 0x79726f6d, 0x206f7420, 0x6f6c6c61\n"
        ".word 0x65746163, 0x20642520, 0x65747962, 0x21212073\n"
        ".word 0x00000a21, 0xe3a01000, 0xe1a02001, 0xe1a03001\n"
        ".word 0xe1a0c001, 0xe889100e, 0xe1a00001, 0xe3a04040\n"
        ".word 0xe59d1060, 0xe3a05801, 0xe5814000, 0xe59d1064\n"
        ".word 0xe5815000, 0xe59d1068, 0xe5c10000, 0xe59d106c\n"
        ".word 0xe5c10000, 0xe28dd09c, 0xe3a00045, 0xe8bd8ff0\n"
        ".word 0xe1a00001, 0xe59d105c, 0xe1500001, 0x0a000025\n"
        ".word 0xe5901018, 0xe5911010, 0xe5d11070, 0xe3510000\n"
        ".word 0x0a000009, 0xe2899d52, 0xe5992000, 0xe3520000\n"
        ".word 0x0a000002, 0xe59f0b10, 0xe5951014, 0xe12fff32\n"
        ".word 0xe28dd09c, 0xe3a00053, 0xe8bd8ff0, 0xe590100c\n"
        ".word 0xe3510000, 0x0a000004, 0xe1a00001, 0xe5911008\n"
        ".word 0xe3510000, 0x1afffffb, 0xea00000b, 0xe5901004\n"
        ".word 0xe591300c, 0xe1500003, 0x1a000004, 0xe1a00001\n"
        ".word 0xe5911004, 0xe591200c, 0xe1500002, 0x0afffffa\n"
        ".word 0xe590200c, 0xe1520001, 0x11a00001, 0xe59d105c\n"
        ".word 0xe1500001, 0x1affffd9, 0xe59d4058, 0xe3a08000\n"
        ".word 0xe1540001, 0x0a000029, 0xe5940018, 0xe5953004\n"
        ".word 0xe1a01005, 0xe5902004, 0xe1520003, 0x1a000009\n"
        ".word 0xe5902000, 0xe5922014, 0xe12fff32, 0xe3500000\n"
        ".word 0x0a000004, 0xe5940018, 0xe3a01001, 0xe5900010\n"
        ".word 0xe5c01070, 0xea000277, 0xe594000c, 0xe1a01004\n"
        ".word 0xe3500000, 0x0a000004, 0xe1a04000, 0xe5900008\n"
        ".word 0xe3500000, 0x1afffffb, 0xea00000b, 0xe5910004\n"
        ".word 0xe590200c, 0xe1540002, 0x1a000004, 0xe1a04000\n"
        ".word 0xe5900004, 0xe590100c, 0xe1540001, 0x0afffffa\n"
        ".word 0xe594100c, 0xe1510000, 0x11a04000, 0xe59d005c\n"
        ".word 0xe1540000, 0x1affffd7, 0xe3580000, 0x1a00025d\n"
        ".word 0xe5960000, 0xe5901000, 0xe5912000, 0xe3a01074\n"
        ".word 0xe12fff32, 0xe3500000, 0x0a0001ac, 0xe5963000\n"
        ".word 0xe3a02000, 0xe280104c, 0xe5803000, 0xe5802008\n"
        ".word 0xe5803004, 0xe580200c, 0xe5802010, 0xe5802014\n"
        ".word 0xe5802018, 0xe1c021fc, 0xe5802024, 0xe5802028\n"
        ".word 0xe1c022fc, 0xe5802034, 0xe5802038, 0xe580203c\n"
        ".word 0xe5802040, 0xe5802044, 0xe5802048, 0xe5801058\n"
        ".word 0xe5802050, 0xe580304c, 0xe5801054, 0xe5802060\n"
        ".word 0xe580305c, 0xe5802064, 0xe5802068, 0xe580206c\n"
        ".word 0xe3a03001, 0xe5c03070, 0xe5951014, 0xe1a04000\n"
        ".word 0xe2892010, 0xebfff6c0, 0xe59d101c, 0xe1a02004\n"
        ".word 0xe28d0074, 0xebfff9e2, 0xe1b04000, 0xe320f000\n"
        ".word 0x0a000182, 0xe5940000, 0xe1a08005, 0xe1a01005\n"
        ".word 0xe5902018, 0xe1a00004, 0xe12fff32, 0xe5940000\n"
        ".word 0xe5901010, 0xe1a00004, 0xe12fff31, 0xe3500000\n"
        ".word 0x15981014, 0xe28d0048, 0xe28d2020, 0x15841014\n"
        ".word 0xe5953014, 0xe596c000, 0xe58d0044, 0xe58d0040\n"
        ".word 0xe28d1038, 0xe28d0034, 0xe58d404c, 0xe58dc048\n"
        ".word 0xe58d403c, 0xe58d1054, 0xe8801008, 0xe2820004\n"
        ".word 0xe59d3038, 0xe59d1034, 0xe28d802c, 0xe58d3024\n"
        ".word 0xe59d303c, 0xe58d1020, 0xe28d1038, 0xe58d3028\n"
        ".word 0xe59d3044, 0xe58d0050, 0xe58d0044, 0xe888000a\n"
        ".word 0xe1a01007, 0xe28d0018, 0xeb012be1, 0xe28d0024\n"
        ".word 0xe320f000, 0xebf9e9b6, 0xe28d0038, 0xe320f000\n"
        ".word 0xebf9e9b3, 0xe28d0048, 0xebf9e9b1, 0xea0001f9\n"
        ".word 0xe289ab05, 0xe28aa034, 0xe2843004, 0xe59a100c\n"
        ".word 0xe59a0004, 0xe58d3030, 0xe281c001, 0xe0802201\n"
        ".word 0xe0423000, 0xe3a06001, 0xe1a0b243, 0xe58db040\n"
        ".word 0xe59a3008, 0xe58dc000, 0xe153000c, 0x3a000087\n"
        ".word 0xe041100b, 0xe3510001, 0x31a0c001, 0x21a0c006\n"
        ".word 0xe041400c, 0xe59d1000, 0xe35c0000, 0xe042220c\n"
        ".word 0xe041100c, 0x10800201, 0x0a00000f, 0xe1b01000\n"
        ".word 0xe1a03002, 0xe2810010, 0xe2822010, 0x0a000008\n"
        ".word 0xe5935000, 0xe5815000, 0xe5935004, 0xe5815004\n"
        ".word 0xe593500c, 0xe581500c, 0xe5851008, 0xe5813008\n"
        ".word 0xe583100c, 0xe25cc001, 0x1affffef, 0xe08b2006\n"
        ".word 0xe3540000, 0xe58d2044, 0x0a00005e, 0xe152000b\n"
        ".word 0x8a00002c, 0xe59a0004, 0xe0807202, 0xe080820b\n"
        ".word 0xe1570008, 0xe1a06007, 0xe1a05008, 0xe2877010\n"
        ".word 0xe2888010, 0x0a000020, 0xe5960008, 0xe3500000\n"
        ".word 0x11500006, 0x1a00000b, 0xe5960004, 0xe3500000\n"
        ".word 0x0a000010, 0xe5901000, 0xe5911000, 0xe12fff31\n"
        ".word 0xe8961001, 0xe5901000, 0xe5912004, 0xe1a0100c\n"
        ".word 0xe12fff32, 0xea000007, 0xe596100c, 0xe580100c\n"
        ".word 0xe2861008, 0xe3a00000, 0xe8910006, 0xe5821008\n"
        ".word 0xe5860008, 0xe586000c, 0xe3a00000, 0xe5860004\n"
        ".word 0xe5950004, 0xe5860004, 0xe595000c, 0xe586000c\n"
        ".word 0xe5806008, 0xe5865008, 0xe585600c, 0xe2544001\n"
        ".word 0x1affffd6, 0xea00002f, 0xe1a00202, 0xe0802204\n"
        ".word 0xe59a0004, 0xe1a0120b, 0xe0811204, 0xe0827000\n"
        ".word 0xe0818000, 0xe2476010, 0xe2485010, 0xe1560005\n"
        ".word 0xe1a07006, 0xe1a08005, 0x0a000020, 0xe5970008\n"
        ".word 0xe3500000, 0x11500006, 0x1a00000b, 0xe5960004\n"
        ".word 0xe3500000, 0x0a000010, 0xe5901000, 0xe5911000\n"
        ".word 0xe12fff31, 0xe8961001, 0xe5901000, 0xe5912004\n"
        ".word 0xe1a0100c, 0xe12fff32, 0xea000007, 0xe596100c\n"
        ".word 0xe580100c, 0xe2861008, 0xe3a00000, 0xe8910006\n"
        ".word 0xe5821008, 0xe5860008, 0xe586000c, 0xe3a00000\n"
        ".word 0xe5860004, 0xe5950004, 0xe5860004, 0xe595000c\n"
        ".word 0xe586000c, 0xe5806008, 0xe5865008, 0xe585600c\n"
        ".word 0xe2544001, 0x1affffd6, 0xe59d2044, 0xe59a000c\n"
        ".word 0xe1a0100b, 0xe1520000, 0x21a02000, 0xe1a0000a\n"
        ".word 0xebf9ea66, 0xe320f000, 0xe320f000, 0xea00007a\n"
        ".word 0xe1a0100c, 0xe1a00003, 0xebf9e908, 0xe1a08000\n"
        ".word 0xe59a0000, 0xe28d1024, 0xe3a07000, 0xe8810081\n"
        ".word 0xe1b04008, 0xe58d702c, 0x0a00002f, 0xe5900000\n"
        ".word 0xe1a05204, 0xe59d3024, 0xe58d5048, 0xe5902000\n"
        ".word 0xe1a01005, 0xe1a00003, 0xe12fff32, 0xe1b05000\n"
        ".word 0x1a000007, 0xe59d0024, 0xe59dc024, 0xe59f159c\n"
        ".word 0xe59d2048, 0xe5900000, 0xe5903008, 0xe1a0000c\n"
        ".word 0xe12fff33, 0xe3550000, 0xe58d5028, 0x1a000019\n"
        ".word 0xe59d0000, 0xe1500008, 0x0a000090, 0xe1b04000\n"
        ".word 0x0a000015, 0xe59d0024, 0xe59d3024, 0xe1a05204\n"
        ".word 0xe1a01005, 0xe5900000, 0xe5902000, 0xe1a00003\n"
        ".word 0xe12fff32, 0xe1b08000, 0x1a000007, 0xe59d0024\n"
        ".word 0xe59dc024, 0xe59f1534, 0xe1a02005, 0xe5900000\n"
        ".word 0xe5903008, 0xe1a0000c, 0xe12fff33, 0xe3580000\n"
        ".word 0xe58d8028, 0x0a000079, 0xe58d402c, 0xe1b0c00b\n"
        ".word 0xe59a2004, 0x159d0028, 0x0a00000f, 0xe1b01000\n"
        ".word 0xe1a03002, 0xe2810010, 0xe2822010, 0x0a000008\n"
        ".word 0xe5934000, 0xe5814000, 0xe5934004, 0xe5814004\n"
        ".word 0xe593400c, 0xe581400c, 0xe5841008, 0xe5813008\n"
        ".word 0xe583100c, 0xe25cc001, 0x1affffef, 0xe59a100c\n"
        ".word 0xe59a0004, 0xe08b3006, 0xe051c00b, 0xe080220b\n"
        ".word 0x159d0028, 0x10800203, 0x0a00000f, 0xe1b01000\n"
        ".word 0xe1a03002, 0xe2810010, 0xe2822010, 0x0a000008\n"
        ".word 0xe5934000, 0xe5814000, 0xe5934004, 0xe5814004\n"
        ".word 0xe593400c, 0xe581400c, 0xe5841008, 0xe5813008\n"
        ".word 0xe583100c, 0xe25cc001, 0x1affffef, 0xe59d2028\n"
        ".word 0xe59a1004, 0xe28d0024, 0xe58a2004, 0xe59d202c\n"
        ".word 0xe58d1028, 0xe59a1008, 0xe58a2008, 0xe58d102c\n"
        ".word 0xe59a200c, 0xe3a01000, 0xebf9e9f0, 0xe1cd02d4\n"
        ".word 0xe59d3024, 0xe5900000, 0xe5902004, 0xe1a00003\n"
        ".word 0xe12fff32, 0xe58d7028, 0xe58d702c, 0xe59d0000\n"
        ".word 0xe58a000c, 0xe59d0040, 0xe59a1004, 0xe0910200\n"
        ".word 0x0a000009, 0xe59d1030, 0xe5912000, 0xe5802000\n"
        ".word 0xe5912004, 0xe5802004, 0xe591200c, 0xe580200c\n"
        ".word 0xe5820008, 0xe5801008, 0xe581000c, 0xe28d0034\n"
        ".word 0xe8900110, 0xe1a00004, 0xebff94db, 0xe5941000\n"
        ".word 0xe2887008, 0xe1510007, 0x15942004, 0x11520007\n"
        ".word 0x1a000025, 0xe5981018, 0xe1510004, 0x05880018\n"
        ".word 0xe598001c, 0xe1500004, 0x1a000002, 0xe1a00004\n"
        ".word 0xebff94ee, 0xe588001c, 0xe5941008, 0xe1510007\n"
        ".word 0x02882004, 0x0a000003, 0xe5910000, 0xe1500004\n"
        ".word 0x01a02001, 0x12812004, 0xe5940000, 0xe1500007\n"
        ".word 0x05940004, 0xe5820000, 0xe5801008, 0xe5980000\n"
        ".word 0xe5926000, 0xe1a01004, 0xe5902000, 0xe1560007\n"
        ".word 0x05946008, 0xe1a00008, 0xe12fff32, 0xea000098\n"
        ".word 0xe1cd02d4, 0xe5902000, 0xe5922004, 0xe12fff32\n"
        ".word 0xe28dd09c, 0xe3a00044, 0xe8bd8ff0, 0xe5910004\n"
        ".word 0xe1a05004, 0xe1500007, 0x0a000004, 0xe5955000\n"
        ".word 0xe5b50004, 0xe5900004, 0xe1500007, 0x1afffffa\n"
        ".word 0xe2844010, 0xe1a06004, 0xe4941004, 0xe595b000\n"
        ".word 0xe58d1004, 0xe5940000, 0xe28d1008, 0xe28ba010\n"
        ".word 0xe58d0008, 0xe5940004, 0xe58d000c, 0xe594000c\n"
        ".word 0xe58d0014, 0xe5801008, 0xe58d4010, 0xe584100c\n"
        ".word 0xe59b0010, 0xe2864004, 0xe5860000, 0xe28a0004\n"
        ".word 0xe1540000, 0xe1a06004, 0xe58d0030, 0x0a000021\n"
        ".word 0xe5940008, 0xe3500000, 0x11500004, 0x1a00000b\n"
        ".word 0xe5940004, 0xe3500000, 0x0a000010, 0xe5901000\n"
        ".word 0xe5911000, 0xe12fff31, 0xe8940009, 0xe5901000\n"
        ".word 0xe5912004, 0xe1a01003, 0xe12fff32, 0xea000007\n"
        ".word 0xe594100c, 0xe580100c, 0xe2841008, 0xe3a00000\n"
        ".word 0xe8910006, 0xe5821008, 0xe5840008, 0xe584000c\n"
        ".word 0xe3a00000, 0xe5840004, 0xe59d0030, 0xe5901004\n"
        ".word 0xe5861004, 0xe590100c, 0xe586100c, 0xe5816008\n"
        ".word 0xe5860008, 0xe580600c, 0xe59d0004, 0xe28d4008\n"
        ".word 0xe28d6004, 0xe48a0004, 0xe15a0004, 0x0a000021\n"
        ".word 0xe59a0008, 0xe3500000, 0x1150000a, 0x1a00000c\n"
        ".word 0xe59a0004, 0xe3500000, 0x0a000011, 0xe5901000\n"
        ".word 0xe5911000, 0xe12fff31, 0xe59a3000, 0xe59a1004\n"
        ".word 0xe5930000, 0xe5902004, 0xe1a00003, 0xe12fff32\n"
        ".word 0xea000007, 0xe59a100c, 0xe580100c, 0xe28a1008\n"
        ".word 0xe3a00000, 0xe8910006, 0xe5821008, 0xe58a0008\n"
        ".word 0xe58a000c, 0xe3a00000, 0xe58a0004, 0xe59d000c\n"
        ".word 0xe58a0004, 0xe59d0014, 0xe58a000c, 0xe580a008\n"
        ".word 0xe58a4008, 0xe58da014, 0xe59d1010, 0xe2860004\n"
        ".word 0xe3510000, 0x11510000, 0x1a00000b, 0xe59d000c\n"
        ".word 0xe3500000, 0x0a000010, 0xe5901000, 0xe5911000\n"
        ".word 0xe12fff31, 0xe59d0008, 0xe59d100c, 0xe5902000\n"
        ".word 0xe5922004, 0xe12fff32, 0xea000007, 0xe59d0014\n"
        ".word 0xe28d3010, 0xe581000c, 0xe8930006, 0xe3a00000\n"
        ".word 0xe5821008, 0xe58d0010, 0xe58d0014, 0xe3a00000\n"
        ".word 0xe58d000c, 0xe59b1000, 0xe59b0008, 0xe5810008\n"
        ".word 0xe59b6000, 0xe1a0100b, 0xe5856000, 0xe5980000\n"
        ".word 0xe1560007, 0x059b6008, 0xe5902000, 0xe1a00008\n"
        ".word 0xe12fff32, 0xe5980020, 0xe2400001, 0xe5880020\n"
        ".word 0xe5980004, 0xe5880010, 0xe5964008, 0xe1540007\n"
        ".word 0x0a000008, 0xe5940000, 0xe1500006, 0x01a00004\n"
        ".word 0x12840004, 0xebff93cd, 0xe1a06004, 0xe5944008\n"
        ".word 0xe1540007, 0x1afffff6, 0xe2880004, 0xebff93c7\n"
        ".word 0xe5980004, 0xe5880010, 0xe59d0094, 0xe59d1070\n"
        ".word 0xe5900000, 0xe0800001, 0xe59d1094, 0xe5810000\n"
        ".word 0xe59d1098, 0xe1500001, 0x93a00000, 0x9afffc51\n"
        ".word 0xe3a01000, 0xe1a02001, 0xe1a03001, 0xe1a0c001\n"
        ".word 0xe889100e, 0xe1a00001, 0xe3a04040, 0xe59d1060\n"
        ".word 0xe3a05801, 0xe5814000, 0xe59d1064, 0xe5815000\n"
        ".word 0xe59d1068, 0xe5c10000, 0xe59d106c, 0xe5c10000\n"
        ".word 0xe28dd09c, 0xe3a00043, 0xe8bd8ff0, 0x0040fe80\n"
        ".word 0x0040fe40\n");
}

// ---------------------------------------------------------------------------
// 0x00101308 -- nnMain / application main loop (4,144 B)
// ---------------------------------------------------------------------------

namespace {

// `svc #0x28` at 0x00101B80 and 0x00101F08 (nn::os::GetSystemTick).  The
// import is declared above; the 64-bit fixed-point reduction below is
// independent of the clock source.
u64 SystemTick()
{
    return nn::os::GetSystemTick();
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
#if 0
void crt_func_00101308(void)
{
    // 0x00101310..0x00101358: system bring-up.
    engine_func_002c5fbc();
    engine_func_001076d8(0, 0x12345678u);
    AsdMemory_func_0010376c();                  // r0 = 0x100000 ignored
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
    AsdModel_func_0010495c();                  // r0/r1 = 0x100/0x30000 ignored
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
            f32 a = *reinterpret_cast<f32*>(rect + 0x0C);   // s18
            f32 b = *reinterpret_cast<f32*>(rect + 0x14);   // s16
            f32 c = *reinterpret_cast<f32*>(rect + 0x18);   // s17
            f32 value = *script_vm_func_002c5e20();         // V
            f32 half = 0.5f;                                // 0x3F000000
            f32 w = value * a;                              // s3 = V*A
            f32 ya = b - w * half;                          // s0  = B - 0.5W
            f32 yb = b + w * half;                          // s16 = B + 0.5W
            f32 h = c + value * half;                       // s17 = C + 0.5V
            f32 y1 = c - value * half;                      // s1  = C - 0.5V
            f32 height = h - y1;                            // s2  = H - Y1
            *reinterpret_cast<f32*>(rect + 0x10) = height;  // 0x001015B0
            *reinterpret_cast<f32*>(rect + 0x0C) =
                (yb - ya) / height;                         // 0x001015B8
            *reinterpret_cast<f32*>(rect + 0x14) =
                (yb + ya) * half;                           // 0x001015BC
            *reinterpret_cast<f32*>(rect + 0x18) =
                (h + y1) * half;                            // 0x001015C4
        }
    }

    // 0x001015CC..0x00101648: render/process bring-up.
    g_CrtMainState.gx_08 = AsdGxCommandList_func_002c5d90();
    g_CrtMainState.gx_0c = AsdGxCommandList_func_002c5d90();
    ui_func_00102aa0();
    AsdPrim_func_001042c8(reinterpret_cast<void*>(
        static_cast<std::uintptr_t>(0x100000u)));   // r0 = 0x100000
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
    AsdCamera_func_00105c50(reinterpret_cast<void*>(
        static_cast<std::uintptr_t>(3)));       // r0 = 3
    AsdModelProcess_func_00103ff8(0x67, 0x68, 0xE3, 0);
    FrameTex_func_00104378();                   // r0 = 1 ignored
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
#endif

// Readable CRT initialization draft above; exact ARM body retained for matcher coverage.
__attribute__((naked)) void crt_func_00101308(void) {
    asm volatile(
        ".word 0xed2d8b04, 0xe24dd0e0, 0xeb071329, 0xe59f1470\n"
        ".word 0xe3a00000, 0xeb0018ed, 0xe3a00601, 0xeb000910\n"
        ".word 0xe3a00001, 0xeb0012be, 0xeb000475, 0xeb00320c\n"
        ".word 0xe1a00000, 0xeb00169c, 0xeb001690, 0xeb001620\n"
        ".word 0xeb001665, 0xeb000abe, 0xe3500000, 0x0b000a2b\n"
        ".word 0xeb0009d0, 0xe3a05000, 0xe28d308c, 0xe3a00601\n"
        ".word 0xe3a08080, 0xe3a01b02, 0xe3a02702, 0xe58d50a0\n"
        ".word 0xe58d50a8, 0xe58d50ac, 0xe59f6410, 0xe8830107\n"
        ".word 0xe3a0b001, 0xe28b1c05, 0xe5c6b001, 0xe59fa3f8\n"
        ".word 0xe58d009c, 0xe59f93ec, 0xe28d008c, 0xe58d10a4\n"
        ".word 0xe58da0b0, 0xe58da0b4, 0xeb00102a, 0xe3a00001\n"
        ".word 0xeb001287, 0xeb0011dd, 0xe59f73d4, 0xe59f03d4\n"
        ".word 0xe3a02000, 0xe3a01007, 0xe5974000, 0xe7805004\n"
        ".word 0xe3a00006, 0xeb0712f0, 0xe59f13bc, 0xe7810004\n"
        ".word 0xe5974000, 0xe3a01001, 0xe3a00005, 0xeb0712e0\n"
        ".word 0xe59f13a8, 0xe7810004, 0xeb000ba4, 0xed9f8ae8\n"
        ".word 0xe3a00000, 0xeef01a48, 0xeeb01a48, 0xeef00a48\n"
        ".word 0xeeb00a48, 0xeb001264, 0xeef01a48, 0xeeb01a48\n"
        ".word 0xeef00a48, 0xeeb00a48, 0xe3a00001, 0xeb00125e\n"
        ".word 0xe59f1370, 0xe1a0000d, 0xe3a03002, 0xe3a0203c\n"
        ".word 0xfa0712c2, 0xe5805080, 0xe1c098b4, 0xe5805088\n"
        ".word 0xe3a00b01, 0xe3a09002, 0xe58d0088, 0xe1a0000d\n"
        ".word 0xe1cda8b4, 0xe58d9080, 0xeb00114f, 0xe3a01005\n"
        ".word 0xe28d30bc, 0xe58d10b8, 0xe8830102, 0xe3a00004\n"
        ".word 0xe28d10cc, 0xe3a02008, 0xe58d00c8, 0xe58d80c4\n"
        ".word 0xe8810005, 0xe3a01000, 0xe58d00d8, 0xe58d00dc\n"
        ".word 0xe28d00b8, 0xe58d20d4, 0xeb000f50, 0xe3a03080\n"
        ".word 0xe3a02001, 0xe3a01000, 0xe28f0fbb, 0xeb07125c\n"
        ".word 0xeb000fda, 0xe3a00001, 0xeb00123d, 0xeb0008a1\n"
        ".word 0xed9f0abc, 0xed800a00, 0xeb00083b, 0xed9f0aba\n"
        ".word 0xed800a00, 0xeb000898, 0xed9f0ab8, 0xed800a00\n"
        ".word 0xeb000b63, 0xeddf9ab6, 0xedc09a00, 0xeb0011ce\n"
        ".word 0xed9f0ab4, 0xe3a01803, 0xed800a00, 0xe3a00c01\n"
        ".word 0xeb000d0f, 0xeb000b2d, 0xeb07123e, 0xed9f0aae\n"
        ".word 0xed800a00, 0xeb000e1f, 0xe3500000, 0x0a000023\n"
        ".word 0xeb071234, 0xe5900260, 0xe5901000, 0xe5911010\n"
        ".word 0xe12fff31, 0xe3500000, 0x0a000002, 0xe5901000\n"
        ".word 0xe3110101, 0x03a00000, 0xe1b04000, 0x0a000017\n"
        ".word 0xedd40a06, 0xed949a03, 0xed948a05, 0xeef08a60\n"
        ".word 0xeb071228, 0xed901a00, 0xeef00a68, 0xeeb00a48\n"
        ".word 0xee611a09, 0xee418a29, 0xe2841014, 0xee410a69\n"
        ".word 0xee010ae9, 0xee018aa9, 0xee381ae0, 0xee780aa0\n"
        ".word 0xee781a40, 0xee380a00, 0xed841a04, 0xee600aa9\n"
        ".word 0xee812a81, 0xee200a29, 0xed842a03, 0xec810a02\n"
        ".word 0xe320f000, 0xeb0711ef, 0xe5860008, 0xe320f000\n"
        ".word 0xeb0711ec, 0xe586000c, 0xe320f000, 0xeb00052d\n"
        ".word 0xe3a00601, 0xe320f000, 0xeb000b34, 0xe59f01ec\n"
        ".word 0xe320f000, 0xeb00061f, 0xe320f000, 0xe320f000\n"
        ".word 0xeb000a58, 0xe28f0f76, 0xe320f000, 0xeb000e99\n"
        ".word 0xe320f000, 0xe320f000, 0xeb000992, 0xe320f000\n"
        ".word 0xe320f000, 0xeb0004da, 0xe320f000, 0xe320f000\n"
        ".word 0xeb000482, 0xe320f000, 0xe320f000, 0xeb0010a8\n"
        ".word 0xe320f000, 0xe320f000, 0xeb0016bb, 0xe320f000\n"
        ".word 0xe320f000, 0xeb00167b, 0xe320f000, 0xe320f000\n"
        ".word 0xeb00166c, 0xe3a00007, 0xe320f000, 0xeb000dd4\n"
        ".word 0xe3a00002, 0xe320f000, 0xeb000a1c, 0xe320f000\n"
        ".word 0xe320f000, 0xeb00152e, 0xe3a01000, 0xe3a0002c\n"
        ".word 0xeb071119, 0xe3a01000, 0xe3a0002c, 0xeb071103\n"
        ".word 0xe320f000, 0xe320f000, 0xeb00058e, 0xe3a00000\n"
        ".word 0xe320f000, 0xeb000dc9, 0xe3a00001, 0xe320f000\n"
        ".word 0xeb0011c9, 0xe320f000, 0xe320f000, 0xeb001252\n"
        ".word 0xe320f000, 0xe320f000, 0xeb0011ed, 0xe320f000\n"
        ".word 0xe320f000, 0xeb0013c0, 0xe320f000, 0xe320f000\n"
        ".word 0xeb0007e3, 0xe320f000, 0xe320f000, 0xeb001144\n"
        ".word 0xe320f000, 0xe320f000, 0xeb0710d5, 0xe320f000\n"
        ".word 0xe320f000, 0xeb000dd1, 0xe3a02000, 0xe1a01002\n"
        ".word 0xe3a00018, 0xeb0710a1, 0xe59f00c8, 0xe3a03000\n"
        ".word 0xe1a02003, 0xe88d0021, 0xe3a01065, 0xe28f00b8\n"
        ".word 0xe58d5008, 0xeb071089, 0xe59f00bc, 0xe3a03000\n"
        ".word 0xe1a02003, 0xe88d0021, 0xe3a01066, 0xe28f00ac\n"
        ".word 0xe58d5008, 0xeb071081, 0xe59f00b4, 0xe3a03000\n"
        ".word 0xe1a02003, 0xe88d0021, 0xe3a01069, 0xe28f00a4\n"
        ".word 0xea00002c, 0x12345678, 0x00008058, 0x00008d62\n"
        ".word 0x00446db0, 0x0044ea00, 0x0000136c, 0x00001384\n"
        ".word 0x00001378, 0x00000000, 0x0010716c, 0x6667776e\n"
        ".word 0x65445f78, 0x6c756166, 0x61685374, 0x2e726564\n"
        ".word 0x64736362, 0x00000072, 0x40400000, 0x469c4000\n"
        ".word 0x41400000, 0x3f000000, 0x3ecccccd, 0x447a0000\n"
        ".word 0x00000163, 0x2f786574, 0x73646473, 0x706f5434\n"
        ".word 0x2e726944, 0x00746164, 0x00103b58, 0x6f666542\n"
        ".word 0x72446572, 0x4c317761, 0x00000000, 0x00103d10\n"
        ".word 0x77617244, 0x74655331, 0x67726154, 0x72507465\n"
        ".word 0x0000636f, 0x001035e0, 0x77617244, 0x646f4d31\n"
        ".word 0x444c6c65, 0x00656e6f, 0xe58d5008, 0xeb07104b\n"
        ".word 0xe59f03c0, 0xe3a03000, 0xe1a02003, 0xe88d0021\n"
        ".word 0xe3a0106e, 0xe28f0e3b, 0xe58d5008, 0xeb071043\n"
        ".word 0xe59f03b0, 0xe3a03000, 0xe1a02003, 0xe88d0021\n"
        ".word 0xe3a01075, 0xe28f0e3a, 0xe58d5008, 0xeb07103b\n"
        ".word 0xe59f03a0, 0xe3a03000, 0xe1a02003, 0xe88d0021\n"
        ".word 0xe3a01072, 0xe28f0e39, 0xe58d5008, 0xeb071033\n"
        ".word 0xe59f0394, 0xe3a03000, 0xe1a02003, 0xe88d0021\n"
        ".word 0xe3a01074, 0xe28f0fe1, 0xe58d5008, 0xeb07102b\n"
        ".word 0xe59f0384, 0xe3a03000, 0xe1a02003, 0xe88d0021\n"
        ".word 0xe3a01083, 0xe28f0e33, 0xe58d5008, 0xeb071023\n"
        ".word 0xe59f0368, 0xe3a03000, 0xe1a02003, 0xe88d0021\n"
        ".word 0xe3a010cb, 0xe28f0fd6, 0xe58d5008, 0xeb07101b\n"
        ".word 0xe59f0358, 0xe3a03000, 0xe1a02003, 0xe88d0021\n"
        ".word 0xe3a010cc, 0xe28f0fd2, 0xe58d5008, 0xeb071013\n"
        ".word 0xe59f034c, 0xe3a03000, 0xe1a02003, 0xe88d0021\n"
        ".word 0xe3a010cd, 0xe28f0fcf, 0xe58d5008, 0xeb07100b\n"
        ".word 0xe59f033c, 0xe3a03000, 0xe1a02003, 0xe88d0021\n"
        ".word 0xe3a010d2, 0xe28f0fcb, 0xe58d5008, 0xeb071003\n"
        ".word 0xe59f032c, 0xe3a03000, 0xe1a02003, 0xe88d0021\n"
        ".word 0xe3a010d3, 0xe28f0fc7, 0xe58d5008, 0xeb070ffb\n"
        ".word 0xe59f031c, 0xe3a03000, 0xe1a02003, 0xe88d0021\n"
        ".word 0xe3a010e1, 0xe28f0fc3, 0xe58d5008, 0xeb070ff3\n"
        ".word 0xe59f430c, 0xe3a03000, 0xe1a02003, 0xe1cd40f0\n"
        ".word 0xe3a0107a, 0xe28f0fbf, 0xe58d5008, 0xeb070feb\n"
        ".word 0xe59f8304, 0xe3a03000, 0xe1a02003, 0xe3a010d8\n"
        ".word 0xe28f0fbe, 0xe58d5004, 0xe58d8000, 0xe58d5008\n"
        ".word 0xeb070fe2, 0xe3a03000, 0xe1cd40f0, 0xe1a02003\n"
        ".word 0xe3a01076, 0xe28f0fba, 0xe58d5008, 0xeb070fdb\n"
        ".word 0xe3a03000, 0xe1a02003, 0xe3a010d4, 0xe28f0fb9\n"
        ".word 0xe58d5004, 0xe58d8000, 0xe58d5008, 0xeb070fd3\n"
        ".word 0xe59f02e4, 0xe3a03000, 0xe1a02003, 0xe88d0021\n"
        ".word 0xe3a010e2, 0xe28f0fb5, 0xe58d5008, 0xeb070fcb\n"
        ".word 0xe59f02dc, 0xe3a03000, 0xe1a02003, 0xe88d0021\n"
        ".word 0xe3a010e4, 0xe28f0fb3, 0xe58d5008, 0xeb070fc3\n"
        ".word 0xe59f02d0, 0xe3a03000, 0xe59f12cc, 0xe88d0021\n"
        ".word 0xe1a02003, 0xe28f0fb1, 0xe58d5008, 0xeb070fbb\n"
        ".word 0xe59f02c4, 0xe3a03000, 0xe1a02003, 0xe88d0021\n"
        ".word 0xe3a01085, 0xe28f0fad, 0xe58d5008, 0xeb070fb3\n"
        ".word 0xe59f02b8, 0xe3a03000, 0xe1a02003, 0xe88d0021\n"
        ".word 0xe3a01e16, 0xe28f0faa, 0xe58d5008, 0xeb070fab\n"
        ".word 0xe3a00003, 0xe320f000, 0xeb00105e, 0xe3a03000\n"
        ".word 0xe3a020e3, 0xe3a01068, 0xe3a00067, 0xeb000943\n"
        ".word 0xe3a00001, 0xe320f000, 0xeb000a20, 0xe3a00003\n"
        ".word 0xe320f000, 0xe1a00000, 0xe3a00000, 0xe320f000\n"
        ".word 0xeb0004ad, 0xed9f1a9a, 0xe5970000, 0xeddf0a99\n"
        ".word 0xeef01a41, 0xed9f0a98, 0xeb0013a5, 0xe3a00007\n"
        ".word 0xe320f000, 0xeb070f85, 0xe3a00007, 0xe320f000\n"
        ".word 0xeb070f76, 0xe3a00001, 0xe320f000, 0xeb070f60\n"
        ".word 0xe1a0000d, 0xe5c65003, 0xeb070f45, 0xe59d0000\n"
        ".word 0xe59f1228, 0xe2500000, 0xe0810190, 0xe1a04000\n"
        ".word 0xeb00089d, 0xe1a00004, 0xe320f000, 0xeb000850\n"
        ".word 0xed9f8a83, 0xe320f000, 0xef000028, 0xe51f53f4\n"
        ".word 0xe1c502f0, 0xeb002679, 0xe320f000, 0xe320f000\n"
        ".word 0xeb0006e9, 0xe3500000, 0x13a00001, 0xe3a04001\n"
        ".word 0xe5c50000, 0xeb0016bb, 0xe3500000, 0xe320f000\n"
        ".word 0x0a000074, 0xe3a00001, 0xe1a01000, 0xe5c50001\n"
        ".word 0xe3a04000, 0xe3a000cc, 0xeb070f1d, 0xe3a01001\n"
        ".word 0xe3a000d8, 0xeb070f1a, 0xe3a01001, 0xe3a000db\n"
        ".word 0xeb070f17, 0xe3a01001, 0xe3a000de, 0xeb070f14\n"
        ".word 0xe3a01001, 0xe3a000df, 0xeb070f11, 0xe320f000\n"
        ".word 0xe320f000, 0xea000070, 0x001026c4, 0x77617244\n"
        ".word 0x73614331, 0x00315368, 0x00106130, 0x77617244\n"
        ".word 0x6c704531, 0x0000004c, 0x00103670, 0x77617244\n"
        ".word 0x44434c55, 0x65424432, 0x006e6967, 0x00102634\n"
        ".word 0x77617244, 0x73614331, 0x00314568, 0x00102724\n"
        ".word 0x00102678, 0x77617244, 0x73614331, 0x00324568\n"
        ".word 0x00103ba0, 0x6f666542, 0x72446572, 0x52317761\n"
        ".word 0x00000000, 0x00102810, 0x77617244, 0x646f4d31\n"
        ".word 0x00526c65, 0x00102760, 0x77617244, 0x6f725031\n"
        ".word 0x00003163, 0x00106160, 0x77617244, 0x6c704531\n"
        ".word 0x00000052, 0x001027c0, 0x77617244, 0x6f725031\n"
        ".word 0x00003263, 0x00103d9c, 0x77617244, 0x42443255\n"
        ".word 0x6e696765, 0x4c434e5f, 0x00000000, 0x00103db8\n"
        ".word 0x77617244, 0x42443255, 0x6e696765, 0x52434e5f\n"
        ".word 0x00000000, 0x77617244, 0x42443255, 0x6e696765\n"
        ".word 0x4c4c545f, 0x00000000, 0x77617244, 0x42443255\n"
        ".word 0x6e696765, 0x524c545f, 0x00000000, 0x00103d5c\n"
        ".word 0x77617244, 0x74655332, 0x67726154, 0x72507465\n"
        ".word 0x0000636f, 0x00103654, 0x77617244, 0x44434c44\n"
        ".word 0x65424432, 0x006e6967, 0x00106190, 0x00000162\n"
        ".word 0x77617244, 0x6f725032, 0x00000063, 0x00102cdc\n"
        ".word 0x77617244, 0x64614655, 0x6f725065, 0x00000063\n"
        ".word 0x00102cc8, 0x77617244, 0x64614644, 0x6f725065\n"
        ".word 0x00000063, 0x3f800000, 0x3e4ccccd, 0x3e800000\n"
        ".word 0x000f4240, 0x42c80000, 0xe3a00000, 0xe1a01000\n"
        ".word 0xe5c50001, 0xe3a000cc, 0xeb070ea9, 0xe3a01000\n"
        ".word 0xe3a000d8, 0xeb070ea6, 0xe3a01000, 0xe3a000db\n"
        ".word 0xeb070ea3, 0xe3a01000, 0xe3a000de, 0xeb070ea0\n"
        ".word 0xe3a01000, 0xe3a000df, 0xeb070e9d, 0xe1a01004\n"
        ".word 0xe3a00000, 0xeb001016, 0xe5d50001, 0xe3500000\n"
        ".word 0x0a000005, 0xe595001c, 0xe2800001, 0xe3500002\n"
        ".word 0xe585001c, 0xc3a00002, 0xda000000, 0xe585001c\n"
        ".word 0xe320f000, 0xeb000189, 0xe5d50004, 0xe3500000\n"
        ".word 0x0a000018, 0xeb000ebc, 0xe5d50004, 0xe3500000\n"
        ".word 0x0a000014, 0xe5950010, 0xe350001e, 0xba00000d\n"
        ".word 0xe240001e, 0xe5850010, 0xe3a00001, 0xeb000859\n"
        ".word 0xe3a00001, 0xe320f000, 0xeb0015a1, 0xe3500000\n"
        ".word 0xe320f000, 0x0a000003, 0xeb0014d3, 0xe320f000\n"
        ".word 0xe320f000, 0xeb0014e5, 0xe5950010, 0xe2800001\n"
        ".word 0xe5850010, 0xeb000d2d, 0xe3a00000, 0xeb000423\n"
        ".word 0xe5d50003, 0xe3500000, 0x1a00001b, 0xe59f4488\n"
        ".word 0xe5d40000, 0xe3500000, 0x1a000006, 0xeb00110d\n"
        ".word 0xe320f000, 0xe320f000, 0xeb001021, 0xe320f000\n"
        ".word 0xe320f000, 0xeb0011fa, 0xe320f000, 0xe1a00000\n"
        ".word 0xe320f000, 0xe320f000, 0xeb00082d, 0xe595001c\n"
        ".word 0xe3500002, 0xa3a00001, 0xb3a00000, 0xeb000e57\n"
        ".word 0xe3a00001, 0xe320f000, 0xeb070e51, 0xe3500000\n"
        ".word 0x05d40000, 0x03500000, 0x0b00055f, 0xe320f000\n"
        ".word 0xef000028, 0xe51f277c, 0xe3a04000, 0xe1c202f8\n"
        ".word 0xe2822020, 0xe8921008, 0xe0502003, 0xe59f33fc\n"
        ".word 0xe0c1000c, 0xe3a01003, 0xe08c7392, 0xe0898190\n"
        ".word 0xe094500c, 0xe0a86004, 0xe088c390, 0xe1a07fc0\n"
        ".word 0xe0238397, 0xe0233490, 0xe0a3c291, 0xe09c0005\n"
        ".word 0xe59fc3cc, 0xe0a31006, 0xe1a03004, 0xe3a05000\n"
        ".word 0xe0889c90, 0xe08b9c91, 0xe0288c93, 0xe1a02fc1\n"
        ".word 0xe0288590, 0xe02cbc92, 0xe1a0a005, 0xe1a07005\n"
        ".word 0xe1a06005, 0xe025c591, 0xe59f4398, 0xe099c008\n"
        ".word 0xe0a55007, 0xe0887490, 0xe0238493, 0xe09cc007\n"
        ".word 0xe0203a90, 0xe0883491, 0xe0a00006, 0xe0228492\n"
        ".word 0xe1a0cfc0, 0xe0242a91, 0xe0900005, 0xe0accfc5\n"
        ".word 0xe0932000, 0xe0a4000c, 0xe1a023a2, 0xe1a01fa1\n"
        ".word 0xe1820c80, 0xe0914000, 0xeb000f6f, 0xee004a90\n"
        ".word 0xe51f5858, 0xe59f4330, 0xeef80ae0, 0xee600a88\n"
        ".word 0xee801a80, 0xeebd0ac1, 0xee100a10, 0xe5850018\n"
        ".word 0xe5d41000, 0xe3510000, 0x1a000007, 0xe3500064\n"
        ".word 0xaa000003, 0xeb000c96, 0xe320f000, 0xe320f000\n"
        ".word 0xea000001, 0xe320f000, 0xeb000edd, 0xe5d50003\n"
        ".word 0xe3500000, 0x0a000026, 0xeb000763, 0xe3500000\n"
        ".word 0xe320f000, 0x0a000022, 0xeb008600, 0xe5d40000\n"
        ".word 0xe3500000, 0x13a00003, 0x1b070dee, 0xe320f000\n"
        ".word 0xe320f000, 0xeb001532, 0xe320f000, 0xe320f000\n"
        ".word 0xeb000841, 0xe3500000, 0xe320f000, 0x1b000710\n"
        ".word 0xe320f000, 0xe320f000, 0xeb00083f, 0xe3500000\n"
        ".word 0xe320f000, 0x1b0006df, 0xe320f000, 0xe320f000\n"
        ".word 0xeb000bf0, 0xe3500000, 0xe320f000, 0x1b00083a\n"
        ".word 0xe320f000, 0xe320f000, 0xeb000b4c, 0xe320f000\n"
        ".word 0xe320f000, 0xeb0004fd, 0xe320f000, 0xe320f000\n"
        ".word 0xeb0006ca, 0xe320f000, 0xeb000743, 0xe3500002\n"
        ".word 0xe320f000, 0x1a000010, 0xe5d40000, 0xe3500000\n"
        ".word 0x13a00002, 0x1b070dc7, 0xe320f000, 0xe320f000\n"
        ".word 0xeb0006d1, 0xe320f000, 0xe320f000, 0xeb070dbd\n"
        ".word 0xe320f000, 0xe320f000, 0xeb000853, 0xe5d40000\n"
        ".word 0xe3500000, 0x13a00002, 0x1b070db1, 0xe5d50003\n"
        ".word 0xe3500000, 0x1afffe8e, 0xeb000c13, 0xe3500001\n"
        ".word 0x13500002, 0x0a000002, 0xe3500003, 0x0a000007\n"
        ".word 0xea00000a, 0xe5d50002, 0xe3500000, 0x03a00058\n"
        ".word 0x05850014, 0xe3a00001, 0xe5c50002, 0xea000003\n"
        ".word 0xe5d50002, 0xe3500000, 0x0a00001d, 0xeb06fb55\n"
        ".word 0xe5d50003, 0xe3500000, 0x1afffe79, 0xeb000ca0\n"
        ".word 0xe3500000, 0xe320f000, 0x0afffe75, 0xe3a00001\n"
        ".word 0xeb070d85, 0xe5d40000, 0xe3500000, 0x13a00001\n"
        ".word 0x1b070d98, 0xe320f000, 0xe320f000, 0xeb0085a3\n"
        ".word 0xe320f000, 0xe320f000, 0xeb00134f, 0xe320f000\n"
        ".word 0xe320f000, 0xeb00074c, 0xe320f000, 0xe320f000\n"
        ".word 0xeb070d71, 0xe3500000, 0xe320f000, 0x1a000032\n"
        ".word 0xea00002c, 0xe5d40000, 0xe3500000, 0x13a00000\n"
        ".word 0x1b070d84, 0xe320f000, 0xe320f000, 0xeb00858f\n"
        ".word 0xe320f000, 0xe320f000, 0xeb0012f7, 0xe320f000\n"
        ".word 0xe320f000, 0xeb070d60, 0xe3500000, 0xe320f000\n"
        ".word 0x1a000003, 0xeb070d58, 0xe3500000, 0xe320f000\n"
        ".word 0x0a00000b, 0xe5d40000, 0xe3500000, 0x0a000006\n"
        ".word 0xe3a00003, 0xeb070d6f, 0xe59f00cc, 0xe3a01000\n"
        ".word 0xe5902000, 0xe1a00001, 0xeb070cf3, 0xe3a00001\n"
        ".word 0xe5c50003, 0xe5d50003, 0xe3500000, 0x1afffe3c\n"
        ".word 0xe5d40000, 0xe3500000, 0x13a00000, 0x1b070d58\n"
        ".word 0xe320f000, 0xe320f000, 0xeb070d5a, 0xe320f000\n"
        ".word 0xe320f000, 0xeaffffb5, 0xe320f000, 0xeb070d3a\n"
        ".word 0xe3500000, 0xe320f000, 0x0a00000b, 0xe5d40000\n"
        ".word 0xe3500000, 0x0a000006, 0xe3a00003, 0xeb070d51\n"
        ".word 0xe59f0054, 0xe3a01000, 0xe5902000, 0xe1a00001\n"
        ".word 0xeb070cd5, 0xe3a00001, 0xe5c50003, 0xe5d50003\n"
        ".word 0xe3500000, 0x1a000003, 0xe5d40000, 0xe3500000\n"
        ".word 0x13a00001, 0x1b070d3a, 0xe3a00001, 0xeb070cc2\n"
        ".word 0xe320f000, 0xe320f000, 0xeafffe15, 0x0044d048\n"
        ".word 0xbad34aee, 0xe353f7cf, 0x20c49ba5, 0x0044e368\n");
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
    } else if (selector == 0x8370u) {            // 0x00142EFC / 0x00142F98
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
#if 0
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

    // 0x00143324..0x0014332C / 0x0014379C..0x001437A4: screens 1 and 2 clear
    // the two fixed-2D control bits before the mode gate.
    if (screen != 0) {
        *control &= ~0xC0u;
    }

    // 0x00142E1C..0x00142E34: config +0x50 low nibble into channel +0x38.
    *extra = (*extra & ~0xFu) | (config->field_50 & 0xFu);

    // 0x00142E38..0x00142E7C (screen 0) and 0x00143330..0x00143384
    // (screens 1/2): accepted mode sets.  Screen 0 also accepts 0x6040 and
    // 0x6050; the 0x6040 body is screen-0 only.
    u32 mode = config->mode_48;
    u32 count_mask = 0;
    s32 nibble_source = 0;
    u32 nibble = 0;
    bool mode_ok = false;
    if (screen == 0) {
        mode_ok = (mode >= 0x1906u && mode <= 0x190Au) ||
                  mode == 0x6040u || mode == 0x6050u ||
                  mode == 0x6700u || mode == 0x675Au || mode == 0x675Bu;
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
    if (screen == 0 && mode == 0x6040u) {
        // 0x001431B8..0x001431F0.
        *control &= ~0x71000000u;
        *size &= ~0xF000000u;
        *size &= ~0xF0000u;
        *size &= ~0x1FFFu;                       // lsr #13 / lsl #13
        *control |= 0x20000006u;
        *control |= 0x100000u;
        *control = (*control & ~0x7000u & ~0x730u) | 0x1100u;
        goto submit;
    }
    if (screen == 0 && mode == 0x6050u) {
        // 0x001431F4..0x00143224.
        *control &= ~0x30u;
        *size &= ~0xF000000u;
        *size &= ~0xF0000u;
        *size &= ~0x1FFFu;                       // lsr #13 / lsl #13
        *control &= ~0x70000000u;
        *control &= ~6u;
        *control &= ~0x7700u;
        *color = 0;
        goto submit;
    }
    if (screen != 0 && mode == 0x6050u) {
        // 0x00143630..0x00143658 / 0x00143AA8..0x00143AD4.  This path falls
        // into the shared 0x0014365C tail rather than jumping to submit.
        *control = (*control & ~2u & ~4u & ~0x7700u);
        *size &= ~0xF000000u;
        *size &= ~0xF0000u;
        *size &= ~0x1FFFu;                       // lsr #13 / lsl #13
        *color = 0;
        goto tail;
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
        *size = (*size & ~0xF0000u) | count_mask;
        *size = (*size & ~0xF000000u) | (nibble << 24);
        *control &= ~0x1000000u;
        break;
    case 0x2701u:                               // 0x00143130
        *control |= 4u;
        *size = (*size & ~0xF0000u) | count_mask;
        *size = (*size & ~0xF000000u) | (nibble << 24);
        *control &= ~0x1000000u;
        break;
    case 0x2702u:                               // 0x00143098
        *control |= 4u;
        *size = (*size & ~0xF0000u) | count_mask;
        *size = (*size & ~0xF000000u) | (nibble << 24);
        *control |= 0x1000000u;
        break;
    case 0x2703u:                               // 0x00143170
        *control |= 4u;
        *size = (*size & ~0xF0000u) | count_mask;
        *size = (*size & ~0xF000000u) | (nibble << 24);
        *control |= 0x1000000u;
        break;
    default:
        break;
    }

    // 0x0014310C..0x0014312C / 0x0014365C..0x0014367C: bits 0x30 are always
    // cleared; mode 0x675A selects the 0x20 value.
tail:
    *control &= ~0x30u;
    if (mode == 0x675Au) {
        *control |= 0x20u;
    }

submit:
    SubmitChannel(screen, regs, config->address_34);
    return 0;                                    // 0x00143B80
}
#endif

// Readable LCD render/configuration draft above; exact ARM body retained pending codegen recovery.
__attribute__((naked)) u32 func_00142bf0(LcdRenderConfig* config, u32 screen) {
    asm volatile(
        ".word 0xe92d5ff0, 0xe59f235c, 0xe5923000, 0xe5902034\n"
        ".word 0xe283c058, 0xe2834e77, 0xe08c3001, 0xe3520000\n"
        ".word 0xe5d3e0ac, 0x059f2340, 0x13a02000, 0xe35e0000\n"
        ".word 0x0a000001, 0xe3520000, 0x0a000013, 0xe3510000\n"
        ".word 0x05940000, 0x03c00001, 0x0a00000a, 0xe3510001\n"
        ".word 0x05940000, 0x03c00002, 0x0a000006, 0xe3510002\n"
        ".word 0x05940000, 0x159f0304, 0x03c00004, 0x05840000\n"
        ".word 0x0a000001, 0xe8bd9ff0, 0xe5840000, 0xe5d300ac\n"
        ".word 0xe3500000, 0x11a00002, 0xe8bd9ff0, 0xed9f0ab8\n"
        ".word 0xedd03a07, 0xed904a06, 0xedd00a08, 0xed903a09\n"
        ".word 0xee633a80, 0xee244a00, 0xee604a80, 0xee235a00\n"
        ".word 0xed9f1ab0, 0xeddf2ab0, 0xeddf1ab0, 0xed9f2ab0\n"
        ".word 0xeddf0ab0, 0xe3510000, 0xeebc3ae3, 0xeebc0ac4\n"
        ".word 0xeefc3ae4, 0xeebc4ac5, 0xe3e0b33e, 0xe3a0e0ff\n"
        ".word 0xe3a0280f, 0xe3a0340f, 0xe3a06000, 0xee138a10\n"
        ".word 0xee107a10, 0xee139a90, 0xee14aa10, 0xe1877408\n"
        ".word 0xe2805034, 0xe1877809, 0xe1877c0a, 0x0a000005\n"
        ".word 0xe59fc274, 0xe3510001, 0x0a00015f, 0xe3510002\n"
        ".word 0x1a00039a, 0xea00027a, 0xe594100c, 0xe5847004\n"
        ".word 0xe3c18601, 0xe584800c, 0xe5941008, 0xe595700c\n"
        ".word 0xe3c11407, 0xe3c118ff, 0xe00b7807, 0xe1811007\n"
        ".word 0xe5841008, 0xe5957010, 0xe1a015a1, 0xe1a01581\n"
        ".word 0xe1a07a87, 0xe1a07aa7, 0xe1877001, 0xe5847008\n"
        ".word 0xed900a0a, 0xee101a10, 0xeeb40a60, 0xeef1fa10\n"
        ".word 0x0a000002, 0xe1a01081, 0xe15e0c21, 0x1a000003\n"
        ".word 0xe5941010, 0xe1a0e6a1, 0xe1a0e68e, 0xea000016\n"
        ".word 0xee300a01, 0xee200a22, 0xeef40ac0, 0xeef1fa10\n"
        ".word 0xceb00a60, 0xca000012, 0xee101a10, 0xe3510446\n"
        ".word 0xaeb00a61, 0xaa000003, 0xe59fe1c0, 0xee101a10\n"
        ".word 0xe151000e, 0xba00000a, 0xee300a42, 0xe594e010\n"
        ".word 0xe1a0e6ae, 0xe1a0e68e, 0xeebc0ac0, 0xee101a10\n"
        ".word 0xe1a01981, 0xe1a019a1, 0xe18ee001, 0xe584e010\n"
        ".word 0xea000009, 0xee300a02, 0xe594e010, 0xe1a0e6ae\n"
        ".word 0xe1a0e68e, 0xeebc0ac0, 0xee101a10, 0xe1a01981\n"
        ".word 0xe1a019a1, 0xe18ee001, 0xe584e010, 0xe5941038\n"
        ".word 0xe595701c, 0xe59fe158, 0xe3c1100f, 0xe207700f\n"
        ".word 0xe1877001, 0xe5847038, 0xe5951014, 0xe151000e\n"
        ".word 0xe041e00e, 0x0a0000db, 0xca000004, 0xe2411c19\n"
        ".word 0xe2411006, 0xe3510004, 0x8a000007, 0xea000008\n"
        ".word 0xe35e0010, 0x0a0000e2, 0xe35e0d1b, 0x124e1c07\n"
        ".word 0x1251101a, 0x13510001, 0x0a000001, 0xe59f00d8\n"
        ".word 0xe8bd9ff0, 0xe59c10a0, 0xe3510c6e, 0xe594100c\n"
        ".word 0x03c11207, 0x0381c203, 0x13c1c207, 0xe584c00c\n"
        ".word 0xe5901008, 0xe2411c29, 0xe2511001, 0x0a00000a\n"
        ".word 0xe2411b16, 0xe251102c, 0x0a00000b, 0xe3510002\n"
        ".word 0x0594100c, 0x03c1ca07, 0x0a00000e, 0xe2411c02\n"
        ".word 0xe2511043, 0x1a00000c, 0xea000007, 0xe594100c\n"
        ".word 0xe3c11a07, 0xe381ca02, 0xea000006, 0xe594100c\n"
        ".word 0xe3c11a07, 0xe381ca01, 0xea000002, 0xe594100c\n"
        ".word 0xe3c11a07, 0xe381ca03, 0xe584c00c, 0xe590100c\n"
        ".word 0xe2411c29, 0xe2511001, 0x0a00000a, 0xe2411b16\n"
        ".word 0xe251102c, 0x0a000017, 0xe3510002, 0x0594100c\n"
        ".word 0x03c1cc07, 0x0a00001a, 0xe2411c02, 0xe2511043\n"
        ".word 0x1a000018, 0xea000013, 0xe594100c, 0xe3c11c07\n"
        ".word 0xe381cc02, 0xea000012, 0x004655c0, 0x00000502\n"
        ".word 0x00000501, 0x437f0000, 0x41800000, 0x43800000\n"
        ".word 0x45fff800, 0x45800000, 0x00000000, 0x0000190a\n"
        ".word 0x45800000, 0x00006040, 0xe594100c, 0xe3c11c07\n"
        ".word 0xe381cc01, 0xea000002, 0xe594100c, 0xe3c11c07\n"
        ".word 0xe381cc03, 0xe584c00c, 0xe5901000, 0xe3510c26\n"
        ".word 0x0594100c, 0x03c1c002, 0x0a000004, 0xe2411c26\n"
        ".word 0xe2511001, 0x0594100c, 0x0381c002, 0x1a000000\n"
        ".word 0xe584c00c, 0xe590c004, 0xe59f1ba8, 0xe15c0001\n"
        ".word 0xe04c1001, 0x0a000051, 0xca000007, 0xe35c0c26\n"
        ".word 0x0a00000a, 0xe24c1c26, 0xe2511001, 0x0a00003a\n"
        ".word 0xe35100ff, 0x1a000040, 0xea00000d, 0xe3510001\n"
        ".word 0x0a000020, 0xe3510002, 0x1a00003b, 0xea000053\n"
        ".word 0xe5941010, 0xe594200c, 0xe3c1140f, 0xe3c22004\n"
        ".word 0xe3c1180f, 0xe3c22401, 0xe5841010, 0xe584200c\n"
        ".word 0xea000031, 0xe594100c, 0xe3c1c004, 0xe584c00c\n"
        ".word 0xe595c034, 0xe5941010, 0xe24cc001, 0xe3c1180f\n"
        ".word 0xe002280c, 0xe1811002, 0xe5841010, 0xe5900014\n"
        ".word 0xe3c1240f, 0xe3500000, 0xba00003a, 0xe594100c\n"
        ".word 0xe0030c00, 0xe284600c, 0xe1822000, 0xe3c11401\n"
        ".word 0xe8860006, 0xea00001c, 0xe594100c, 0xe3c1c004\n"
        ".word 0xe584c00c, 0xe595c034, 0xe5941010, 0xe24cc001\n"
        ".word 0xe3c1180f, 0xe002280c, 0xe1811002, 0xe5841010\n"
        ".word 0xe5900014, 0xe3c1240f, 0xe3500000, 0xba000035\n"
        ".word 0xe594100c, 0xe0030c00, 0xe284600c, 0xe1822000\n"
        ".word 0xe3811401, 0xe8860006, 0xea000007, 0xe5941010\n"
        ".word 0xe594200c, 0xe3c1140f, 0xe3822004, 0xe3c1180f\n"
        ".word 0xe3c22401, 0xe5841010, 0xe584200c, 0xe5952014\n"
        ".word 0xe594100c, 0xe2420c67, 0xe250005a, 0x03a00002\n"
        ".word 0x13a00000, 0xe3c11030, 0xe1811200, 0xea00001f\n"
        ".word 0xe594100c, 0xe381c004, 0xe584c00c, 0xe595c034\n"
        ".word 0xe5941010, 0xe24cc001, 0xe3c1180f, 0xe002280c\n"
        ".word 0xe1811002, 0xe5841010, 0xe5900014, 0xe3c1240f\n"
        ".word 0xe3500000, 0xaaffffc4, 0xe3a00000, 0xeaffffc2\n"
        ".word 0xe594100c, 0xe381c004, 0xe584c00c, 0xe595c034\n"
        ".word 0xe5941010, 0xe24cc001, 0xe3c1180f, 0xe002280c\n"
        ".word 0xe1811002, 0xe5841010, 0xe5900014, 0xe3c1240f\n"
        ".word 0xe3500000, 0xaaffffc9, 0xe3a00000, 0xeaffffc7\n"
        ".word 0xe584100c, 0xea00001b, 0xe5941010, 0xe594200c\n"
        ".word 0xe3c1140f, 0xe3c1180f, 0xe3c20471, 0xe1a026a1\n"
        ".word 0xe3801262, 0xe284000c, 0xe1a02682, 0xe3811601\n"
        ".word 0xe8800006, 0xe3c10a07, 0xe3c00e73, 0xe3801c11\n"
        ".word 0xeaffffee, 0xe284100c, 0xe8910006, 0xe3c10030\n"
        ".word 0xe3c2140f, 0xe3c1180f, 0xe3c00207, 0xe1a016a1\n"
        ".word 0xe3c02006, 0xe1a01681, 0xe5841010, 0xe3c21c77\n"
        ".word 0xe584100c, 0xe5846004, 0xe5950000, 0xeb0011d8\n"
        ".word 0xe5941014, 0xe2842004, 0xe2011103, 0xe18111a0\n"
        ".word 0xe5841014, 0xe5940000, 0xe3801001, 0xe5841000\n"
        ".word 0xe3a0100a, 0xe3a00081, 0xeb059db6, 0xe59f2928\n"
        ".word 0xe59f0928, 0xe5921000, 0xe5900000, 0xe1510000\n"
        ".word 0x2a000242, 0xe5943038, 0xe59fc914, 0xe281e008\n"
        ".word 0xe8811008, 0xe582e000, 0xea00023c, 0xed900a0a\n"
        ".word 0xee101a10, 0xeeb40a60, 0xeef1fa10, 0x0a000002\n"
        ".word 0xe1a01081, 0xe15e0c21, 0x1a000001, 0xe3a01000\n"
        ".word 0xea000014, 0xee300a01, 0xee200a22, 0xeef40ac0\n"
        ".word 0xeef1fa10, 0xceb00a60, 0xca00000b, 0xee101a10\n"
        ".word 0xe3510446, 0xaeb00a61, 0xaa000003, 0xe51fe364\n"
        ".word 0xee101a10, 0xe151000e, 0xba000003, 0xee300a42\n"
        ".word 0xeebc0ac0, 0xee101a10, 0xea000002, 0xee300a02\n"
        ".word 0xeebc0ac0, 0xee101a10, 0xe594e050, 0xe1a01981\n"
        ".word 0xe1a0e6ae, 0xe1a019a1, 0xe1a0e68e, 0xe18ee001\n"
        ".word 0xe584e050, 0xe594104c, 0xe3c110c0, 0xe584104c\n"
        ".word 0xe595e014, 0xe15e000c, 0xe24ecc19, 0xe24cc00a\n"
        ".word 0x0a000010, 0xaa000007, 0xe24ecc19, 0xe25cc006\n"
        ".word 0x135c0001, 0x0a00000b, 0xe35c0002, 0x135c0003\n"
        ".word 0x0a000008, 0xeafffec4, 0xe24ccc47, 0xe25cc046\n"
        ".word 0x0a0000ae, 0xe35c0e6b, 0x124ccc07, 0x125cc00a\n"
        ".word 0x135c0001, 0x1afffebc, 0xe590c008, 0xe24ccc29\n"
        ".word 0xe25cc001, 0x03c11a07, 0x0381ca02, 0x0a00000c\n"
        ".word 0xe24ccb16, 0xe25cc02c, 0x03c11a07, 0x0381ca01\n"
        ".word 0x0a000007, 0xe35c0002, 0x03c1ca07, 0x0a000004\n"
        ".word 0xe24ccc02, 0xe25cc043, 0x03c11a07, 0x0381ca03\n"
        ".word 0x1a000000, 0xe584c04c, 0xe590100c, 0xe2411c29\n"
        ".word 0xe2511001, 0x0a00000a, 0xe2411b16, 0xe251102c\n"
        ".word 0x0a00000b, 0xe3510002, 0x0594104c, 0x03c1cc07\n"
        ".word 0x0a00000e, 0xe2411c02, 0xe2511043, 0x1a00000c\n"
        ".word 0xea000007, 0xe594104c, 0xe3c11c07, 0xe381cc02\n"
        ".word 0xea000006, 0xe594104c, 0xe3c11c07, 0xe381cc01\n"
        ".word 0xea000002, 0xe594104c, 0xe3c11c07, 0xe381cc03\n"
        ".word 0xe584c04c, 0xe5901000, 0xe3510c26, 0x0594104c\n"
        ".word 0x03c1c002, 0x0a000004, 0xe2411c26, 0xe2511001\n"
        ".word 0x0594104c, 0x0381c002, 0x1a000000, 0xe584c04c\n"
        ".word 0xe590c004, 0xe59f170c, 0xe15c0001, 0xe04c1001\n"
        ".word 0x0a00004a, 0xca000007, 0xe35c0c26, 0x0a00000a\n"
        ".word 0xe24c1c26, 0xe2511001, 0x0a00003a, 0xe35100ff\n"
        ".word 0x1a000040, 0xea00000d, 0xe3510001, 0x0a000020\n"
        ".word 0xe3510002, 0x1a00003b, 0xea00004c, 0xe5941050\n"
        ".word 0xe594204c, 0xe3c1140f, 0xe3c22004, 0xe3c1180f\n"
        ".word 0xe3c22401, 0xe5841050, 0xe584204c, 0xea000031\n"
        ".word 0xe594104c, 0xe3c1c004, 0xe584c04c, 0xe595c034\n"
        ".word 0xe5941050, 0xe24cc001, 0xe3c1180f, 0xe002280c\n"
        ".word 0xe1811002, 0xe5841050, 0xe5900014, 0xe3c1140f\n"
        ".word 0xe3500000, 0xba000033, 0xe594204c, 0xe0030c00\n"
        ".word 0xe1811000, 0xe3c22401, 0xe5841050, 0xe584204c\n"
        ".word 0xea00001c, 0xe594104c, 0xe3c1c004, 0xe584c04c\n"
        ".word 0xe595c034, 0xe5941050, 0xe24cc001, 0xe3c1180f\n"
        ".word 0xe002280c, 0xe1811002, 0xe5841050, 0xe5900014\n"
        ".word 0xe3c1140f, 0xe3500000, 0xba00002e, 0xe594204c\n"
        ".word 0xe0030c00, 0xe1811000, 0xe3822401, 0xe5841050\n"
        ".word 0xe584204c, 0xea000007, 0xe5941050, 0xe594204c\n"
        ".word 0xe3c1140f, 0xe3822004, 0xe3c1180f, 0xe3c22401\n"
        ".word 0xe5841050, 0xe584204c, 0xe5847044, 0xea00002a\n"
        ".word 0xe594104c, 0xe381c004, 0xe584c04c, 0xe595c034\n"
        ".word 0xe5941050, 0xe24cc001, 0xe3c1180f, 0xe002280c\n"
        ".word 0xe1811002, 0xe5841050, 0xe5900014, 0xe3c1140f\n"
        ".word 0xe3500000, 0xaaffffcb, 0xe3a00000, 0xeaffffc9\n"
        ".word 0xe594104c, 0xe381c004, 0xe584c04c, 0xe595c034\n"
        ".word 0xe5941050, 0xe24cc001, 0xe3c1180f, 0xe002280c\n"
        ".word 0xe1811002, 0xe5841050, 0xe5900014, 0xe3c1140f\n"
        ".word 0xe3500000, 0xaaffffd0, 0xe3a00000, 0xeaffffce\n"
        ".word 0xe3c10002, 0xe5941050, 0xe3c02004, 0xe3c22c77\n"
        ".word 0xe3c1140f, 0xe3c1180f, 0xe1a016a1, 0xe1a01681\n"
        ".word 0xe5841050, 0xe584204c, 0xe5846044, 0xe5952014\n"
        ".word 0xe594104c, 0xe2420c67, 0xe250005a, 0x03a00002\n"
        ".word 0x13a00000, 0xe3c11030, 0xe1811200, 0xe584104c\n"
        ".word 0xe5940048, 0xe595100c, 0xe3c00407, 0xe3c008ff\n"
        ".word 0xe00b1801, 0xe1800001, 0xe5840048, 0xe5951010\n"
        ".word 0xe1a005a0, 0xe1a00580, 0xe1a01a81, 0xe1a01aa1\n"
        ".word 0xe1811000, 0xe5841048, 0xe5950000, 0xeb0010b4\n"
        ".word 0xe5941054, 0xe2842044, 0xe2011103, 0xe18111a0\n"
        ".word 0xe5841054, 0xe5940000, 0xe3801002, 0xe5841000\n"
        ".word 0xe595101c, 0xe5940058, 0xe201100f, 0xe3c0000f\n"
        ".word 0xe1811000, 0xe5841058, 0xe3a01006, 0xe3a00091\n"
        ".word 0xea00011d, 0xed900a0a, 0xee101a10, 0xeeb40a60\n"
        ".word 0xeef1fa10, 0x0a000002, 0xe1a01081, 0xe15e0c21\n"
        ".word 0x1a000001, 0xe3a01000, 0xea000014, 0xee300a01\n"
        ".word 0xee200a22, 0xeef40ac0, 0xeef1fa10, 0xceb00a60\n"
        ".word 0xca00000b, 0xee101a10, 0xe3510446, 0xaeb00a61\n"
        ".word 0xaa000003, 0xe51fe7dc, 0xee101a10, 0xe151000e\n"
        ".word 0xba000003, 0xee300a42, 0xeebc0ac0, 0xee101a10\n"
        ".word 0xea000002, 0xee300a02, 0xeebc0ac0, 0xee101a10\n"
        ".word 0xe594e070, 0xe1a01981, 0xe1a0e6ae, 0xe1a019a1\n"
        ".word 0xe1a0e68e, 0xe18ee001, 0xe584e070, 0xe594106c\n"
        ".word 0xe3c110c0, 0xe584106c, 0xe595e014, 0xe15e000c\n"
        ".word 0xe24ecc19, 0xe24cc00a, 0x0a000010, 0xaa000007\n"
        ".word 0xe24ecc19, 0xe25cc006, 0x135c0001, 0x0a00000b\n"
        ".word 0xe35c0002, 0x135c0003, 0x0a000008, 0xeafffda6\n"
        ".word 0xe24ccc47, 0xe25cc046, 0x0a0000ae, 0xe35c0e6b\n"
        ".word 0x124ccc07, 0x125cc00a, 0x135c0001, 0x1afffd9e\n"
        ".word 0xe590c008, 0xe24ccc29, 0xe25cc001, 0x03c11a07\n"
        ".word 0x0381ca02, 0x0a00000c, 0xe24ccb16, 0xe25cc02c\n"
        ".word 0x03c11a07, 0x0381ca01, 0x0a000007, 0xe35c0002\n"
        ".word 0x03c1ca07, 0x0a000004, 0xe24ccc02, 0xe25cc043\n"
        ".word 0x03c11a07, 0x0381ca03, 0x1a000000, 0xe584c06c\n"
        ".word 0xe590100c, 0xe2411c29, 0xe2511001, 0x0a00000a\n"
        ".word 0xe2411b16, 0xe251102c, 0x0a00000b, 0xe3510002\n"
        ".word 0x0594106c, 0x03c1cc07, 0x0a00000e, 0xe2411c02\n"
        ".word 0xe2511043, 0x1a00000c, 0xea000007, 0xe594106c\n"
        ".word 0xe3c11c07, 0xe381cc02, 0xea000006, 0xe594106c\n"
        ".word 0xe3c11c07, 0xe381cc01, 0xea000002, 0xe594106c\n"
        ".word 0xe3c11c07, 0xe381cc03, 0xe584c06c, 0xe5901000\n"
        ".word 0xe3510c26, 0x0594106c, 0x03c1c002, 0x0a000004\n"
        ".word 0xe2411c26, 0xe2511001, 0x0594106c, 0x0381c002\n"
        ".word 0x1a000000, 0xe584c06c, 0xe590c004, 0xe59f1294\n"
        ".word 0xe15c0001, 0xe04c1001, 0x0a00004a, 0xca000007\n"
        ".word 0xe35c0c26, 0x0a00000a, 0xe24c1c26, 0xe2511001\n"
        ".word 0x0a00003a, 0xe35100ff, 0x1a000040, 0xea00000d\n"
        ".word 0xe3510001, 0x0a000020, 0xe3510002, 0x1a00003b\n"
        ".word 0xea00004c, 0xe5941070, 0xe594206c, 0xe3c1140f\n"
        ".word 0xe3c22004, 0xe3c1180f, 0xe3c22401, 0xe5841070\n"
        ".word 0xe584206c, 0xea000031, 0xe594106c, 0xe3c1c004\n"
        ".word 0xe584c06c, 0xe595c034, 0xe5941070, 0xe24cc001\n"
        ".word 0xe3c1180f, 0xe002280c, 0xe1811002, 0xe5841070\n"
        ".word 0xe5900014, 0xe3c1140f, 0xe3500000, 0xba000033\n"
        ".word 0xe594206c, 0xe0030c00, 0xe1811000, 0xe3c22401\n"
        ".word 0xe5841070, 0xe584206c, 0xea00001c, 0xe594106c\n"
        ".word 0xe3c1c004, 0xe584c06c, 0xe595c034, 0xe5941070\n"
        ".word 0xe24cc001, 0xe3c1180f, 0xe002280c, 0xe1811002\n"
        ".word 0xe5841070, 0xe5900014, 0xe3c1140f, 0xe3500000\n"
        ".word 0xba00002e, 0xe594206c, 0xe0030c00, 0xe1811000\n"
        ".word 0xe3822401, 0xe5841070, 0xe584206c, 0xea000007\n"
        ".word 0xe5941070, 0xe594206c, 0xe3c1140f, 0xe3822004\n"
        ".word 0xe3c1180f, 0xe3c22401, 0xe5841070, 0xe584206c\n"
        ".word 0xe5847064, 0xea00002b, 0xe594106c, 0xe381c004\n"
        ".word 0xe584c06c, 0xe595c034, 0xe5941070, 0xe24cc001\n"
        ".word 0xe3c1180f, 0xe002280c, 0xe1811002, 0xe5841070\n"
        ".word 0xe5900014, 0xe3c1140f, 0xe3500000, 0xaaffffcb\n"
        ".word 0xe3a00000, 0xeaffffc9, 0xe594106c, 0xe381c004\n"
        ".word 0xe584c06c, 0xe595c034, 0xe5941070, 0xe24cc001\n"
        ".word 0xe3c1180f, 0xe002280c, 0xe1811002, 0xe5841070\n"
        ".word 0xe5900014, 0xe3c1140f, 0xe3500000, 0xaaffffd0\n"
        ".word 0xe3a00000, 0xeaffffce, 0xe3c10002, 0xe5941070\n"
        ".word 0xe3c02004, 0xe584206c, 0xe3c1080f, 0xe3c0040f\n"
        ".word 0xe3c21c77, 0xe1a026a0, 0xe284006c, 0xe1a02682\n"
        ".word 0xe5846064, 0xe8800006, 0xe5952014, 0xe594106c\n"
        ".word 0xe2420c67, 0xe250005a, 0x03a00002, 0x13a00000\n"
        ".word 0xe3c11030, 0xe1811200, 0xe584106c, 0xe5940068\n"
        ".word 0xe595100c, 0xe3c00407, 0xe3c008ff, 0xe00b1801\n"
        ".word 0xe1800001, 0xe5840068, 0xe5951010, 0xe1a005a0\n"
        ".word 0xe1a00580, 0xe1a01a81, 0xe1a01aa1, 0xe1811000\n"
        ".word 0xe5841068, 0xe5950000, 0xeb000f95, 0xe5941074\n"
        ".word 0xe2842064, 0xe2011103, 0xe18111a0, 0xe5841074\n"
        ".word 0xe5940000, 0xe3801004, 0xe5841000, 0xe595101c\n"
        ".word 0xe5940078, 0xe201100f, 0xe3c0000f, 0xe1811000\n"
        ".word 0xe5841078, 0xe3a01006, 0xe3a00099, 0xeb059b6d\n"
        ".word 0xe3a00000, 0xe8bd9ff0, 0x00002701, 0x004652a0\n"
        ".word 0x004652a4, 0x000f008e\n");
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
    // 0x002B7F30..0x002B7F88: insertion sort over [0, count).  The first pass
    // is a no-op, so the loop starts at element 1.
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

    // 0x002B7F1A..0x002B7F20 tail-branches into the shared insertion entry;
    // the listing has no separate count>0xA path, so every count uses the
    // same helper.
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
#if 0
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
        // 0x002834A0..0x00283678.  Pre-checked signed loop: the count is
        // re-read through camp_func_0029f0f4 before every iteration
        // (0x002834E4..0x002834F4 `cmp r0,r4` / `bgt`).
        u32 count_slot = reinterpret_cast<std::uintptr_t>(gpu + 0x240);
        u32 dest = reinterpret_cast<std::uintptr_t>(gpu + 0x1DB4);
        u32 cursor = stream + 2;
        u32 nonzero = 0;
        s32 count = static_cast<s32>(camp_func_0029f0f4(
            reinterpret_cast<void*>(count_slot)));
        for (s32 i = 0; count > i; ++i) {
            u16 value = *reinterpret_cast<u16*>(
                reinterpret_cast<std::uintptr_t>(gpu) + 0x1DB4u +
                static_cast<u32>(i) * 2u);
            if (value != 0) {
                nonzero += 1;
            }
            count = static_cast<s32>(camp_func_0029f0f4(
                reinterpret_cast<void*>(count_slot)));
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
#endif

// Readable camp menu routing draft above; exact ARM body retained pending codegen recovery.
__attribute__((naked)) void camp_func_002831f0(u32 layout_opcode) {
    asm volatile(
        ".word 0xe92d47f0, 0xe1a06000, 0xe59f0dbc, 0xe5905000\n"
        ".word 0xeb007769, 0xe1a07000, 0xe3a04000, 0xe2460009\n"
        ".word 0xe350000f, 0xe1a08004, 0xe1a09004, 0x379ff100\n"
        ".word 0xe8bd87f0, 0x00283260, 0x002834a0, 0x0028367c\n"
        ".word 0x00283220, 0x0028379c, 0x00283220, 0x00283220\n"
        ".word 0x00283220, 0x002838bc, 0x002838bc, 0x00283a68\n"
        ".word 0x00283bac, 0x00283bac, 0x00283bac, 0x00283ef8\n"
        ".word 0xe5f70001, 0xe2856b03, 0xe2866f8f, 0xe200107f\n"
        ".word 0xe351000b, 0xe2854f77, 0x1a000008, 0xe1b003a0\n"
        ".word 0xe1a00004, 0x0a00000a, 0xeb006f99, 0xe1a01000\n"
        ".word 0xe59f3d28, 0xe3a02008, 0xe1a00006, 0xfb00d319\n"
        ".word 0xe5d70000, 0xe200107f, 0xe3510020, 0x0a00000a\n"
        ".word 0xea000012, 0xe320f000, 0xeb006f8d, 0xe1a01000\n"
        ".word 0xe59f3cfc, 0xe3a02008, 0xe1a00006, 0xfb00d30d\n"
        ".word 0xe320f000, 0xe320f000, 0xeafffff0, 0xe1b003a0\n"
        ".word 0xe1a00004, 0x0a00000a, 0xeb006f81, 0xe1a01000\n"
        ".word 0xe59f3cd0, 0xe3a02008, 0xe1a00006, 0xfb00d301\n"
        ".word 0xe5d70000, 0xe200107f, 0xe351000d, 0x0a00000a\n"
        ".word 0xea000012, 0xe320f000, 0xeb006f75, 0xe1a01000\n"
        ".word 0xe59f3ca4, 0xe3a02008, 0xe1a00006, 0xfb00d2f5\n"
        ".word 0xe320f000, 0xe320f000, 0xeafffff0, 0xe1b003a0\n"
        ".word 0xe1a00004, 0x0a00000a, 0xeb006f69, 0xe1a01000\n"
        ".word 0xe59f3c78, 0xe3a02008, 0xe1a00006, 0xfb00d2e9\n"
        ".word 0xe5d70000, 0xe200107f, 0xe351000f, 0x0a00000a\n"
        ".word 0xea000012, 0xe320f000, 0xeb006f5d, 0xe1a01000\n"
        ".word 0xe59f3c4c, 0xe3a02008, 0xe1a00006, 0xfb00d2dd\n"
        ".word 0xe320f000, 0xe320f000, 0xeafffff0, 0xe1b003a0\n"
        ".word 0xe1a00004, 0x0a00000a, 0xeb006f51, 0xe1a01000\n"
        ".word 0xe59f3c20, 0xe3a02008, 0xe1a00006, 0xfb00d2d1\n"
        ".word 0xe5d70000, 0xe200107f, 0xe3510011, 0x0a00000a\n"
        ".word 0xea000012, 0xe320f000, 0xeb006f45, 0xe1a01000\n"
        ".word 0xe59f3bf4, 0xe3a02008, 0xe1a00006, 0xfb00d2c5\n"
        ".word 0xe320f000, 0xe320f000, 0xeafffff0, 0xe1b003a0\n"
        ".word 0xe1a00004, 0x0a000013, 0xeb006f39, 0xe1a01000\n"
        ".word 0xe59f3bc8, 0xe3a02008, 0xe1a00006, 0xfb00d2b9\n"
        ".word 0xe5d70000, 0xe200107f, 0xe3510003, 0x1affff7b\n"
        ".word 0xe1b003a0, 0xe1a00004, 0x0a000010, 0xeb006f2c\n"
        ".word 0xe1a01000, 0xe1a00006, 0xe8bd47f0, 0xe3a02008\n"
        ".word 0xe59f3b8c, 0xeaffefde, 0xe320f000, 0xeb006f24\n"
        ".word 0xe1a01000, 0xe59f3b7c, 0xe3a02008, 0xe1a00006\n"
        ".word 0xfb00d2a4, 0xe320f000, 0xe320f000, 0xeaffffe7\n"
        ".word 0xe320f000, 0xeb006f1a, 0xe1a01000, 0xe1a00006\n"
        ".word 0xe8bd47f0, 0xe3a02008, 0xe59f3b4c, 0xeaffefcc\n"
        ".word 0xe3a06000, 0xe2859b07, 0xe2858d09, 0xe2877002\n"
        ".word 0xe2899f6d, 0xe1a04006, 0xe1a00008, 0xeb006f0c\n"
        ".word 0xe3500000, 0xe320f000, 0xda00000a, 0xe0850084\n"
        ".word 0xe2800c1d, 0xe2844001, 0xe1d00bb4, 0xe3500000\n"
        ".word 0x12866001, 0xe1a00008, 0xeb006f01, 0xe1500004\n"
        ".word 0xe320f000, 0xcafffff4, 0xe5d70000, 0xe200107f\n"
        ".word 0xe351000b, 0x1a000006, 0xe1b003a0, 0x0a000009\n"
        ".word 0xe59f3ad8, 0xe3a02002, 0xe1a01006, 0xe1a00009\n"
        ".word 0xfb00d278, 0xe5d70000, 0xe200107f, 0xe351000e\n"
        ".word 0x0a000008, 0xea00000e, 0xe59f3ab4, 0xe3a02002\n"
        ".word 0xe1a01006, 0xe1a00009, 0xfb00d26e, 0xe320f000\n"
        ".word 0xe320f000, 0xeafffff2, 0xe1b003a0, 0x0a000009\n"
        ".word 0xe59f3a90, 0xe3a02002, 0xe1a01006, 0xe1a00009\n"
        ".word 0xfb00d264, 0xe5d70000, 0xe200107f, 0xe351000f\n"
        ".word 0x0a000008, 0xea00000e, 0xe59f3a6c, 0xe3a02002\n"
        ".word 0xe1a01006, 0xe1a00009, 0xfb00d25a, 0xe320f000\n"
        ".word 0xe320f000, 0xeafffff2, 0xe1b003a0, 0x0a000009\n"
        ".word 0xe59f3a48, 0xe3a02002, 0xe1a01006, 0xe1a00009\n"
        ".word 0xfb00d250, 0xe5d70000, 0xe200107f, 0xe3510011\n"
        ".word 0x0a000008, 0xea00000e, 0xe59f3a24, 0xe3a02002\n"
        ".word 0xe1a01006, 0xe1a00009, 0xfb00d246, 0xe320f000\n"
        ".word 0xe320f000, 0xeafffff2, 0xe1b003a0, 0x0a000010\n"
        ".word 0xe59f3a00, 0xe3a02002, 0xe1a01006, 0xe1a00009\n"
        ".word 0xfb00d23c, 0xe5d70000, 0xe200107f, 0xe3510003\n"
        ".word 0x1afffefe, 0xe1b003a0, 0x0a00000d, 0xe1a01006\n"
        ".word 0xe1a00009, 0xe8bd47f0, 0xe3a02002, 0xe59f39c8\n"
        ".word 0xeaffef63, 0xe59f39c4, 0xe3a02002, 0xe1a01006\n"
        ".word 0xe1a00009, 0xfb00d22b, 0xe320f000, 0xe320f000\n"
        ".word 0xeaffffeb, 0xe1a01006, 0xe1a00009, 0xe8bd47f0\n"
        ".word 0xe3a02002, 0xe59f3998, 0xeaffef55, 0xe5f70003\n"
        ".word 0xe2856b05, 0xe286607c, 0xe200107f, 0xe351000c\n"
        ".word 0xe28540b0, 0x1a000008, 0xe1b003a0, 0xe1a00004\n"
        ".word 0x0a00000a, 0xeb006e92, 0xe1a01000, 0xe59f3964\n"
        ".word 0xe3a02002, 0xe1a00006, 0xfb00d212, 0xe5d70000\n"
        ".word 0xe200107f, 0xe3510010, 0x0a00000a, 0xea000012\n"
        ".word 0xe320f000, 0xeb006e86, 0xe1a01000, 0xe59f3938\n"
        ".word 0xe3a02002, 0xe1a00006, 0xfb00d206, 0xe320f000\n"
        ".word 0xe320f000, 0xeafffff0, 0xe1b003a0, 0xe1a00004\n"
        ".word 0x0a000013, 0xeb006e7a, 0xe1a01000, 0xe59f390c\n"
        ".word 0xe3a02002, 0xe1a00006, 0xfb00d1fa, 0xe5d70000\n"
        ".word 0xe200107f, 0xe3510003, 0x1afffebc, 0xe1b003a0\n"
        ".word 0xe1a00004, 0x0a000010, 0xeb006e6d, 0xe1a01000\n"
        ".word 0xe1a00006, 0xe8bd47f0, 0xe3a02002, 0xe59f38d0\n"
        ".word 0xeaffef1f, 0xe320f000, 0xeb006e65, 0xe1a01000\n"
        ".word 0xe59f38c0, 0xe3a02002, 0xe1a00006, 0xfb00d1e5\n"
        ".word 0xe320f000, 0xe320f000, 0xeaffffe7, 0xe320f000\n"
        ".word 0xeb006e5b, 0xe1a01000, 0xe1a00006, 0xe8bd47f0\n"
        ".word 0xe3a02002, 0xe59f3890, 0xeaffef0d, 0xe5f70004\n"
        ".word 0xe2856b07, 0xe28660c4, 0xe200107f, 0xe3510021\n"
        ".word 0xe2854f5e, 0x1a000008, 0xe1b003a0, 0xe1a00004\n"
        ".word 0x0a00000a, 0xeb006e4a, 0xe1a01000, 0xe59f385c\n"
        ".word 0xe3a02002, 0xe1a00006, 0xfb00d1ca, 0xe5d70000\n"
        ".word 0xe200107f, 0xe3510010, 0x0a00000a, 0xea000012\n"
        ".word 0xe320f000, 0xeb006e3e, 0xe1a01000, 0xe59f3830\n"
        ".word 0xe3a02002, 0xe1a00006, 0xfb00d1be, 0xe320f000\n"
        ".word 0xe320f000, 0xeafffff0, 0xe1b003a0, 0xe1a00004\n"
        ".word 0x0a000013, 0xeb006e32, 0xe1a01000, 0xe59f3804\n"
        ".word 0xe3a02002, 0xe1a00006, 0xfb00d1b2, 0xe5d70000\n"
        ".word 0xe200107f, 0xe3510003, 0x1afffe74, 0xe1b003a0\n"
        ".word 0xe1a00004, 0x0a000010, 0xeb006e25, 0xe1a01000\n"
        ".word 0xe1a00006, 0xe8bd47f0, 0xe3a02002, 0xe59f37c8\n"
        ".word 0xeaffeed7, 0xe320f000, 0xeb006e1d, 0xe1a01000\n"
        ".word 0xe59f37b8, 0xe3a02002, 0xe1a00006, 0xfb00d19d\n"
        ".word 0xe320f000, 0xe320f000, 0xeaffffe7, 0xe320f000\n"
        ".word 0xeb006e13, 0xe1a01000, 0xe1a00006, 0xe8bd47f0\n"
        ".word 0xe3a02002, 0xe59f3788, 0xeaffeec5, 0xe3560011\n"
        ".word 0x0a000002, 0xe3560012, 0x0a000005, 0xea000008\n"
        ".word 0xe2859b07, 0xe2874005, 0xe2899f9f, 0xe2858fa9\n"
        ".word 0xea000003, 0xe2859b07, 0xe2874006, 0xe2899fdb\n"
        ".word 0xe2858fc2, 0xe5d40000, 0xe200107f, 0xe3510006\n"
        ".word 0x1a000008, 0xe1b003a0, 0xe1a00008, 0x0a00000a\n"
        ".word 0xeb006df7, 0xe1a01000, 0xe59f3728, 0xe3a02002\n"
        ".word 0xe1a00009, 0xfb00d177, 0xe5d40000, 0xe200107f\n"
        ".word 0xe3510011, 0x0a00000a, 0xea000012, 0xe320f000\n"
        ".word 0xeb006deb, 0xe1a01000, 0xe59f36fc, 0xe3a02002\n"
        ".word 0xe1a00009, 0xfb00d16b, 0xe320f000, 0xe320f000\n"
        ".word 0xeafffff0, 0xe1b003a0, 0xe1a00008, 0x0a00000a\n"
        ".word 0xeb006ddf, 0xe1a01000, 0xe59f36d0, 0xe3a02002\n"
        ".word 0xe1a00009, 0xfb00d15f, 0xe5d40000, 0xe200107f\n"
        ".word 0xe3510012, 0x0a00000a, 0xea000012, 0xe320f000\n"
        ".word 0xeb006dd3, 0xe1a01000, 0xe59f36a4, 0xe3a02002\n"
        ".word 0xe1a00009, 0xfb00d153, 0xe320f000, 0xe320f000\n"
        ".word 0xeafffff0, 0xe1b003a0, 0xe1a00008, 0x0a000013\n"
        ".word 0xeb006dc7, 0xe1a01000, 0xe59f3678, 0xe3a02002\n"
        ".word 0xe1a00009, 0xfb00d147, 0xe5d40000, 0xe200107f\n"
        ".word 0xe3510003, 0x1afffe09, 0xe1b003a0, 0xe1a00008\n"
        ".word 0x0a000010, 0xeb006dba, 0xe1a01000, 0xe1a00009\n"
        ".word 0xe8bd47f0, 0xe3a02002, 0xe59f363c, 0xeaffee6c\n"
        ".word 0xe320f000, 0xeb006db2, 0xe1a01000, 0xe59f362c\n"
        ".word 0xe3a02002, 0xe1a00009, 0xfb00d132, 0xe320f000\n"
        ".word 0xe320f000, 0xeaffffe7, 0xe320f000, 0xeb006da8\n"
        ".word 0xe1a01000, 0xe1a00009, 0xe8bd47f0, 0xe3a02002\n"
        ".word 0xe59f35fc, 0xeaffee5a, 0xe5f70007, 0xe2854a02\n"
        ".word 0xe284405c, 0xe200107f, 0xe3510006, 0xe2855fdb\n"
        ".word 0x1a000008, 0xe1b003a0, 0xe1a00005, 0x0a00000a\n"
        ".word 0xeb006d97, 0xe1a01000, 0xe59f35a8, 0xe3a02002\n"
        ".word 0xe1a00004, 0xfb00d117, 0xe5d70000, 0xe200107f\n"
        ".word 0xe351001f, 0x0a00000a, 0xea000012, 0xe320f000\n"
        ".word 0xeb006d8b, 0xe1a01000, 0xe59f357c, 0xe3a02002\n"
        ".word 0xe1a00004, 0xfb00d10b, 0xe320f000, 0xe320f000\n"
        ".word 0xeafffff0, 0xe1b003a0, 0xe1a00005, 0x0a00000a\n"
        ".word 0xeb006d7f, 0xe1a01000, 0xe59f3568, 0xe3a02002\n"
        ".word 0xe1a00004, 0xfb00d0ff, 0xe5d70000, 0xe200107f\n"
        ".word 0xe3510013, 0x0a00000a, 0xea000012, 0xe320f000\n"
        ".word 0xeb006d73, 0xe1a01000, 0xe59f353c, 0xe3a02002\n"
        ".word 0xe1a00004, 0xfb00d0f3, 0xe320f000, 0xe320f000\n"
        ".word 0xeafffff0, 0xe1b003a0, 0xe1a00005, 0x0a00000c\n"
        ".word 0xeb006d67, 0xe1a01000, 0xe59f3510, 0xe3a02002\n"
        ".word 0xe1a00004, 0xfb00d0e7, 0xe5d70000, 0xe200107f\n"
        ".word 0xe3510003, 0x1afffda9, 0xe1b003a0, 0x0a000106\n"
        ".word 0xea0000f3, 0xe320f000, 0xeb006d59, 0xe1a01000\n"
        ".word 0xe59f34dc, 0xe3a02002, 0xe1a00004, 0xfb00d0d9\n"
        ".word 0xe320f000, 0xe320f000, 0xeaffffee, 0xe3560014\n"
        ".word 0x0a000004, 0xe3560015, 0x0a000006, 0xe3560016\n"
        ".word 0x0a00000a, 0xea00000e, 0xe2874008, 0xe2859d83\n"
        ".word 0xe2858e3d, 0xea00000a, 0xe2859a02, 0xe2858b01\n"
        ".word 0xe2874009, 0xe2899e1b, 0xe2888034, 0xea000004\n"
        ".word 0xe2859a02, 0xe2858b01, 0xe287400a, 0xe2899e2a\n"
        ".word 0xe2888098, 0xe5d40000, 0xe200107f, 0xe3510004\n"
        ".word 0x1a000008, 0xe1b003a0, 0xe1a00008, 0x0a00000a\n"
        ".word 0xeb006d33, 0xe1a01000, 0xe59f3448, 0xe3a02002\n"
        ".word 0xe1a00009, 0xfb00d0b3, 0xe5d40000, 0xe200107f\n"
        ".word 0xe3510024, 0x0a00000a, 0xea000012, 0xe320f000\n"
        ".word 0xeb006d27, 0xe1a01000, 0xe59f341c, 0xe3a02002\n"
        ".word 0xe1a00009, 0xfb00d0a7, 0xe320f000, 0xe320f000\n"
        ".word 0xeafffff0, 0xe1b003a0, 0xe1a00008, 0x0a00000a\n"
        ".word 0xeb006d1b, 0xe1a01000, 0xe59f33f0, 0xe3a02002\n"
        ".word 0xe1a00009, 0xfb00d09b, 0xe5d40000, 0xe200107f\n"
        ".word 0xe3510025, 0x0a00000a, 0xea000012, 0xe320f000\n"
        ".word 0xeb006d0f, 0xe1a01000, 0xe59f33c4, 0xe3a02002\n"
        ".word 0xe1a00009, 0xfb00d08f, 0xe320f000, 0xe320f000\n"
        ".word 0xeafffff0, 0xe1b003a0, 0xe1a00008, 0x0a00000a\n"
        ".word 0xeb006d03, 0xe1a01000, 0xe59f3398, 0xe3a02002\n"
        ".word 0xe1a00009, 0xfb00d083, 0xe5d40000, 0xe200107f\n"
        ".word 0xe3510026, 0x0a00000a, 0xea000012, 0xe320f000\n"
        ".word 0xeb006cf7, 0xe1a01000, 0xe59f336c, 0xe3a02002\n"
        ".word 0xe1a00009, 0xfb00d077, 0xe320f000, 0xe320f000\n"
        ".word 0xeafffff0, 0xe1b003a0, 0xe1a00008, 0x0a00000a\n"
        ".word 0xeb006ceb, 0xe1a01000, 0xe59f3340, 0xe3a02002\n"
        ".word 0xe1a00009, 0xfb00d06b, 0xe5d40000, 0xe200107f\n"
        ".word 0xe3510027, 0x0a00000a, 0xea000012, 0xe320f000\n"
        ".word 0xeb006cdf, 0xe1a01000, 0xe59f3314, 0xe3a02002\n"
        ".word 0xe1a00009, 0xfb00d05f, 0xe320f000, 0xe320f000\n"
        ".word 0xeafffff0, 0xe1b003a0, 0xe1a00008, 0x0a00000a\n"
        ".word 0xeb006cd3, 0xe1a01000, 0xe59f32e8, 0xe3a02002\n"
        ".word 0xe1a00009, 0xfb00d053, 0xe5d40000, 0xe200107f\n"
        ".word 0xe3510028, 0x0a00000a, 0xea000012, 0xe320f000\n"
        ".word 0xeb006cc7, 0xe1a01000, 0xe59f32bc, 0xe3a02002\n"
        ".word 0xe1a00009, 0xfb00d047, 0xe320f000, 0xe320f000\n"
        ".word 0xeafffff0, 0xe1b003a0, 0xe1a00008, 0x0a00000a\n"
        ".word 0xeb006cbb, 0xe1a01000, 0xe59f3290, 0xe3a02002\n"
        ".word 0xe1a00009, 0xfb00d03b, 0xe5d40000, 0xe200107f\n"
        ".word 0xe3510003, 0x0a00000a, 0xea000012, 0xe320f000\n"
        ".word 0xeb006caf, 0xe1a01000, 0xe59f3264, 0xe3a02002\n"
        ".word 0xe1a00009, 0xfb00d02f, 0xe320f000, 0xe320f000\n"
        ".word 0xeafffff0, 0xe1b003a0, 0xe1a00008, 0x0a000013\n"
        ".word 0xeb006ca3, 0xe1a01000, 0xe59f31ec, 0xe3a02002\n"
        ".word 0xe1a00009, 0xfb00d023, 0xe5d40000, 0xe200107f\n"
        ".word 0xe3510032, 0x1afffce5, 0xe1b003a0, 0xe1a00008\n"
        ".word 0x0a000010, 0xeb006c96, 0xe1a01000, 0xe1a00009\n"
        ".word 0xe8bd47f0, 0xe3a02002, 0xe59f31f8, 0xeaffed48\n"
        ".word 0xe320f000, 0xeb006c8e, 0xe1a01000, 0xe59f31a0\n"
        ".word 0xe3a02002, 0xe1a00009, 0xfb00d00e, 0xe320f000\n"
        ".word 0xe320f000, 0xeaffffe7, 0xe320f000, 0xeb006c84\n"
        ".word 0xe1a01000, 0xe1a00009, 0xe8bd47f0, 0xe3a02002\n"
        ".word 0xe59f31b4, 0xeaffed36, 0xe5f7000b, 0xe2854a02\n"
        ".word 0xe2855b01, 0xe200107f, 0xe3510033, 0xe2844e39\n"
        ".word 0xe28550fc, 0x1a000008, 0xe1b003a0, 0xe1a00005\n"
        ".word 0x0a000013, 0xeb006c72, 0xe1a01000, 0xe59f317c\n"
        ".word 0xe3a02002, 0xe1a00004, 0xfb00cff2, 0xe5d70000\n"
        ".word 0xe200107f, 0xe3510003, 0x1afffcb4, 0xe1b003a0\n"
        ".word 0x0a000011, 0xe1a00005, 0xeb006c65, 0xe1a01000\n"
        ".word 0xe1a00004, 0xe8bd47f0, 0xe3a02002, 0xe59f30e8\n"
        ".word 0xeaffed17, 0xe320f000, 0xeb006c5d, 0xe1a01000\n"
        ".word 0xe59f312c, 0xe3a02002, 0xe1a00004, 0xfb00cfdd\n"
        ".word 0xe320f000, 0xe320f000, 0xeaffffe7, 0xe1a00005\n"
        ".word 0xeb006c53, 0xe1a01000, 0xe1a00004, 0xe8bd47f0\n"
        ".word 0xe3a02002, 0xe59f30a8, 0xeaffed05, 0x0043da90\n"
        ".word 0x00249950, 0x0025779c, 0x002f26f4, 0x0021910c\n"
        ".word 0x002dc6c4, 0x001f5e38, 0x002f80e4, 0x002c6ca4\n"
        ".word 0x002f25d0, 0x002f2634, 0x00218fe8, 0x0021904c\n"
        ".word 0x003132b0, 0x002e4684, 0x0030be4c, 0x002dcc78\n"
        ".word 0x003131e8, 0x002e446c, 0x0030bcb4, 0x0030bd54\n"
        ".word 0x002dc52c, 0x002dc5cc, 0x002f284c, 0x00219540\n"
        ".word 0x002e49ec, 0x002e4a38, 0x00206f30, 0x00206f7c\n"
        ".word 0x0031339c, 0x002e4968, 0x00313350, 0x003133c8\n"
        ".word 0x002e491c, 0x002e4998, 0x002e47b8, 0x00206dcc\n"
        ".word 0x003132fc, 0x002e4764, 0x0030bea4, 0x002f27a0\n"
        ".word 0x002dccd0, 0x002193e0, 0x002f27f4, 0x00219434\n"
        ".word 0x002e46d0, 0x00206d38, 0x002dce58, 0x001f6384\n"
        ".word 0x002e48dc, 0x00206ef0, 0x002e481c, 0x00206e30\n"
        ".word 0x002e489c, 0x00206eb0, 0x002e4724, 0x00206d8c\n"
        ".word 0x002e485c, 0x00206e70, 0x0030bf38, 0x002dcd68\n"
        ".word 0x0030bf0c, 0x002dcd38\n");
}

} // namespace smt4::engine
