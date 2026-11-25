import struct
import sys
from pathlib import Path

from unicorn import UC_ARCH_ARM, UC_HOOK_CODE, UC_MODE_ARM, Uc
from unicorn.arm_const import (
    UC_ARM_REG_C1_C0_2,
    UC_ARM_REG_CPSR,
    UC_ARM_REG_FPEXC,
    UC_ARM_REG_LR,
    UC_ARM_REG_PC,
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_R2,
    UC_ARM_REG_R3,
    UC_ARM_REG_SP,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from build_check import compile_tu_armv6k  # noqa: E402

CODE_BIN = REPO_ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = REPO_ROOT / "src" / "engine" / "leaf_batch45_c.cpp"

FUNC_ADDR = 0x003EA54C
FUNC_SIZE = 1552

CALLEES = {
    "func_0022c198": 0x0022C198,
    "engine_func_002c5ff4": 0x002C5FF4,
}

STUB_RET = 0x00600000
STUB_BASE = 0x00600100
VTABLE_STUB_ALLOC = 0x00600200
VTABLE_STUB_FREE = 0x00600210
VTABLE_STUB_OOM = 0x00600220

CAND_BASE = 0x00700000
STACK_TOP = 0x0080FFF0

SELF_ADDR = 0x00500000
OUT_PTR_ADDR = 0x00500200
OUT_LEN_ADDR = 0x00500204
RING_BUF_ADDR = 0x00510000
Q_ARR_ADDR = 0x00520000
DESC_PAYLOAD_ADDR = 0x00521000
ALLOC_OBJ_ADDR = 0x00530000
VTABLE_ADDR = 0x00530100
INIT_VEC_BUF = 0x00540000
HEAP_BASE = 0x00550000


def parse_elf_symbols(elf_bytes: bytes):
    e_shoff = struct.unpack_from("<I", elf_bytes, 0x20)[0]
    e_shentsize = struct.unpack_from("<H", elf_bytes, 0x2E)[0]
    e_shnum = struct.unpack_from("<H", elf_bytes, 0x30)[0]
    e_shstrndx = struct.unpack_from("<H", elf_bytes, 0x32)[0]
    sh = [struct.unpack_from("<10I", elf_bytes, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr = elf_bytes[sh[e_shstrndx][4] : sh[e_shstrndx][4] + sh[e_shstrndx][5]]

    def sec_name(s):
        idx = s[0]
        return shstr[idx : shstr.index(0, idx)].decode("ascii", "replace")

    syms, sym_list = {}, []
    for s in sh:
        if s[1] == 2:
            strtab = elf_bytes[sh[s[6]][4] : sh[s[6]][4] + sh[s[6]][5]]
            ent_sz = s[9] or 16
            for idx in range(s[5] // ent_sz):
                st_name, st_value, st_size, st_info, _, st_shndx = struct.unpack_from(
                    "<IIIBBH", elf_bytes, s[4] + idx * ent_sz
                )
                name = strtab[st_name : strtab.index(0, st_name)].decode("ascii", "replace")
                sym_list.append((name, st_value, st_size, st_info, st_shndx))
                if name:
                    syms[name] = (st_value, st_size, st_shndx)
    return sh, sec_name, syms, sym_list


def patch_cand_elf(elf_bytes: bytes, base_addr: int, target_name: str, stub_map: dict):
    sh, sec_name, syms, sym_list = parse_elf_symbols(elf_bytes)
    func_val, func_size, func_shndx = syms[target_name]
    text_s = sh[func_shndx]
    text_name = sec_name(text_s)
    text_bytes = bytearray(elf_bytes[text_s[4] : text_s[4] + text_s[5]])

    sec_bases = {}
    pad0 = ((len(text_bytes) + 15) & ~15) - len(text_bytes)
    cursor = base_addr + len(text_bytes) + pad0
    extra_blobs = bytearray(b"\x00" * pad0)
    for i, s in enumerate(sh):
        if i == func_shndx:
            sec_bases[i] = base_addr
        elif s[1] == 1 and (s[2] & 2):
            blob = elf_bytes[s[4] : s[4] + s[5]]
            sec_bases[i] = cursor
            extra_blobs.extend(blob)
            pad = ((len(blob) + 15) & ~15) - len(blob)
            extra_blobs.extend(b"\x00" * pad)
            cursor += len(blob) + pad

    for s in sh:
        if s[1] == 9 and sec_name(s) == ".rel" + text_name:
            for off in range(0, s[5], 8):
                r_offset, r_info = struct.unpack_from("<II", elf_bytes, s[4] + off)
                if not (func_val <= r_offset < func_val + func_size):
                    continue
                r_type = r_info & 0xFF
                r_sym = r_info >> 8
                sym_name, sym_val, _, _, sym_shndx = sym_list[r_sym]
                if sym_name in stub_map:
                    target = stub_map[sym_name]
                elif sym_shndx == 0:
                    raise RuntimeError(f"Unresolved external symbol {sym_name!r} at 0x{r_offset:x}")
                else:
                    target = sec_bases[sym_shndx] + sym_val
                if r_type in (28, 29):
                    pc = base_addr + r_offset
                    insn = struct.unpack_from("<I", text_bytes, r_offset)[0]
                    imm24 = insn & 0xFFFFFF
                    if imm24 & 0x800000:
                        imm24 -= 0x1000000
                    rel = (target - pc + (imm24 << 2)) >> 2
                    struct.pack_into("<I", text_bytes, r_offset, (insn & 0xFF000000) | (rel & 0xFFFFFF))
                elif r_type == 2:
                    addend = struct.unpack_from("<i", text_bytes, r_offset)[0]
                    struct.pack_into("<I", text_bytes, r_offset, (target + addend) & 0xFFFFFFFF)
                elif r_type in (43, 44):
                    insn = struct.unpack_from("<I", text_bytes, r_offset)[0]
                    old_imm16 = ((insn >> 4) & 0xF000) | (insn & 0xFFF)
                    if old_imm16 & 0x8000:
                        old_imm16 -= 0x10000
                    val = (target + old_imm16) & 0xFFFFFFFF
                    imm16 = (val & 0xFFFF) if r_type == 43 else ((val >> 16) & 0xFFFF)
                    new_insn = (insn & 0xFFF0F000) | ((imm16 & 0xF000) << 4) | (imm16 & 0xFFF)
                    struct.pack_into("<I", text_bytes, r_offset, new_insn)
                else:
                    raise RuntimeError(f"Unsupported reloc type {r_type} at 0x{r_offset:x}")

    return bytes(text_bytes) + bytes(extra_blobs), base_addr + func_val


def run_one(code_bytes: bytes, load_addr: int, entry_addr: int, callee_addrs: dict, case: dict):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(UC_ARM_REG_CPSR, 0x10)

    uc.mem_map(0x00100000, 0x00400000)
    uc.mem_map(0x00500000, 0x00100000)
    uc.mem_map(0x00600000, 0x00100000)
    uc.mem_map(0x00700000, 0x00100000)
    uc.mem_map(0x00800000, 0x00020000)

    uc.mem_write(load_addr, code_bytes)

    # Sentinel / tag string at 0x0040FF98
    uc.mem_write(0x0040FF98, b"RingBufScratch\x00")

    # Stubs: BX LR
    bx_lr = struct.pack("<I", 0xE12FFF1E)
    uc.mem_write(STUB_RET, bx_lr)
    for addr in callee_addrs.values():
        uc.mem_write(addr, bx_lr)
    uc.mem_write(VTABLE_STUB_ALLOC, bx_lr)
    uc.mem_write(VTABLE_STUB_FREE, bx_lr)
    uc.mem_write(VTABLE_STUB_OOM, bx_lr)

    # Ring buffer pattern
    cap = case["cap"]
    ring_data = bytes((i * 17 + 3) & 0xFF for i in range(cap))
    uc.mem_write(RING_BUF_ADDR, ring_data)

    # Queue descriptor
    q_cap = case["q_cap"]
    q_idx = case["q_idx"]
    wrapped_q = q_idx - q_cap if q_idx >= q_cap else q_idx
    payload_addr = DESC_PAYLOAD_ADDR
    struct.pack_into("<I", uc.mem_read(payload_addr, 4), 0, 0)
    uc.mem_write(payload_addr + 8, struct.pack("<I", case["msg_len"]))
    desc_addr = Q_ARR_ADDR + wrapped_q * 16
    uc.mem_write(desc_addr + 4, struct.pack("<I", payload_addr))

    # Allocator vtable & object
    uc.mem_write(VTABLE_ADDR, struct.pack("<3I", VTABLE_STUB_ALLOC, VTABLE_STUB_FREE, VTABLE_STUB_OOM))
    uc.mem_write(ALLOC_OBJ_ADDR, struct.pack("<I", VTABLE_ADDR))

    # Initial vector buffer
    vec_cap = case["vec_cap"]
    vec_size = case["vec_size"]
    vec_data = INIT_VEC_BUF if vec_cap > 0 else 0
    if vec_data:
        uc.mem_write(vec_data, bytes((0xA0 + i) & 0xFF for i in range(max(vec_cap, vec_size, 64))))

    # Self struct
    self_bytes = bytearray(0x80)
    struct.pack_into("<I", self_bytes, 0x08, RING_BUF_ADDR)
    struct.pack_into("<I", self_bytes, 0x10, cap)
    struct.pack_into("<I", self_bytes, 0x14, case["read_pos"])
    struct.pack_into("<I", self_bytes, 0x34, Q_ARR_ADDR)
    struct.pack_into("<I", self_bytes, 0x3C, q_cap)
    struct.pack_into("<I", self_bytes, 0x40, q_idx)
    struct.pack_into("<4I", self_bytes, 0x5C, ALLOC_OBJ_ADDR, vec_data, vec_cap, vec_size)
    struct.pack_into("<I", self_bytes, 0x6C, case["max_len"])
    uc.mem_write(SELF_ADDR, bytes(self_bytes))

    uc.mem_write(OUT_PTR_ADDR, struct.pack("<I", 0xDEADBEEF))
    uc.mem_write(OUT_LEN_ADDR, struct.pack("<I", 0xCAFEBABE))

    events = []
    heap_cursor = [HEAP_BASE]
    alloc_count = [0]

    def hook_code(uc_inst, address, size, user_data):
        if address == callee_addrs["func_0022c198"]:
            min_cap = uc_inst.reg_read(UC_ARM_REG_R1)
            ret = case.get("grow_ret", min_cap + 16)
            events.append(("grow", min_cap, ret))
            uc_inst.reg_write(UC_ARM_REG_R0, ret)
        elif address == callee_addrs["engine_func_002c5ff4"]:
            dst = uc_inst.reg_read(UC_ARM_REG_R0)
            src = uc_inst.reg_read(UC_ARM_REG_R1)
            sz = uc_inst.reg_read(UC_ARM_REG_R2)
            events.append(("memcpy", dst, src, sz))
            if sz:
                uc_inst.mem_write(dst, bytes(uc_inst.mem_read(src, sz)))
        elif address == VTABLE_STUB_ALLOC:
            sz = uc_inst.reg_read(UC_ARM_REG_R1)
            idx = alloc_count[0]
            alloc_count[0] += 1
            if idx in case.get("fail_alloc_indices", set()):
                ptr = 0
            else:
                ptr = heap_cursor[0]
                heap_cursor[0] += (sz + 15) & ~15
            events.append(("alloc", sz, ptr))
            uc_inst.reg_write(UC_ARM_REG_R0, ptr)
        elif address == VTABLE_STUB_FREE:
            ptr = uc_inst.reg_read(UC_ARM_REG_R1)
            events.append(("free", ptr))
        elif address == VTABLE_STUB_OOM:
            tag = uc_inst.reg_read(UC_ARM_REG_R1)
            sz = uc_inst.reg_read(UC_ARM_REG_R2)
            events.append(("oom", tag, sz))

    for stub_addr in list(callee_addrs.values()) + [VTABLE_STUB_ALLOC, VTABLE_STUB_FREE, VTABLE_STUB_OOM]:
        uc.hook_add(UC_HOOK_CODE, hook_code, begin=stub_addr, end=stub_addr)

    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, STUB_RET)
    uc.reg_write(UC_ARM_REG_R0, SELF_ADDR)
    uc.reg_write(UC_ARM_REG_R1, OUT_PTR_ADDR)
    uc.reg_write(UC_ARM_REG_R2, OUT_LEN_ADDR)

    uc.emu_start(entry_addr, STUB_RET, count=500000)

    ret = uc.reg_read(UC_ARM_REG_R0)
    out_ptr = struct.unpack_from("<I", uc.mem_read(OUT_PTR_ADDR, 4), 0)[0]
    out_len = struct.unpack_from("<I", uc.mem_read(OUT_LEN_ADDR, 4), 0)[0]
    vec_data_out, vec_cap_out, vec_size_out = struct.unpack_from("<3I", uc.mem_read(SELF_ADDR + 0x60, 12), 0)
    max_len_out = struct.unpack_from("<I", uc.mem_read(SELF_ADDR + 0x6C, 4), 0)[0]
    out_buf_bytes = bytes(uc.mem_read(out_ptr, out_len)) if ret == 1 and out_len > 0 else b""
    return {
        "ret": ret,
        "out_ptr": out_ptr,
        "out_len": out_len,
        "vec_data": vec_data_out,
        "vec_cap": vec_cap_out,
        "vec_size": vec_size_out,
        "max_len": max_len_out,
        "out_bytes": out_buf_bytes,
        "events": events,
    }


def make_cases():
    return [
        # 1. Contiguous fast-path, updates max_len
        {"cap": 64, "read_pos": 4, "q_cap": 4, "q_idx": 1, "msg_len": 10, "vec_cap": 0, "vec_size": 0, "max_len": 5},
        # 2. Contiguous fast-path with read_pos >= cap and q_idx >= q_cap, max_len already larger
        {"cap": 64, "read_pos": 68, "q_cap": 4, "q_idx": 5, "msg_len": 10, "vec_cap": 0, "vec_size": 0, "max_len": 20},
        # 3. Contiguous fast-path reaching exact end of ring buffer
        {"cap": 64, "read_pos": 54, "q_cap": 4, "q_idx": 2, "msg_len": 10, "vec_cap": 0, "vec_size": 0, "max_len": 10},
        # 4. Wrap-around slow-path, shrink (msg_len < vec_size)
        {"cap": 64, "read_pos": 58, "q_cap": 4, "q_idx": 0, "msg_len": 12, "vec_cap": 32, "vec_size": 20, "max_len": 8},
        # 5. Wrap-around slow-path, grow within existing cap (vec_size < msg_len <= vec_cap)
        {"cap": 64, "read_pos": 58, "q_cap": 4, "q_idx": 3, "msg_len": 16, "vec_cap": 32, "vec_size": 6, "max_len": 16},
        # 6. Wrap-around slow-path, realloc via grow_ret succeeds
        {"cap": 64, "read_pos": 50, "q_cap": 4, "q_idx": 1, "msg_len": 24, "vec_cap": 8, "vec_size": 5, "max_len": 10, "grow_ret": 40},
        # 7. Wrap-around slow-path, grow_ret alloc fails (OOM), fallback msg_len alloc succeeds
        {"cap": 64, "read_pos": 50, "q_cap": 4, "q_idx": 1, "msg_len": 24, "vec_cap": 8, "vec_size": 5, "max_len": 10, "grow_ret": 40, "fail_alloc_indices": {0}},
        # 8. Wrap-around slow-path, both grow_ret and fallback msg_len alloc fail -> returns 0
        {"cap": 64, "read_pos": 50, "q_cap": 4, "q_idx": 1, "msg_len": 24, "vec_cap": 8, "vec_size": 5, "max_len": 10, "grow_ret": 40, "fail_alloc_indices": {0, 1}},
        # 9. Wrap-around slow-path, grow_ret == msg_len and alloc fails -> no second alloc, returns 0
        {"cap": 64, "read_pos": 50, "q_cap": 4, "q_idx": 1, "msg_len": 24, "vec_cap": 8, "vec_size": 5, "max_len": 10, "grow_ret": 24, "fail_alloc_indices": {0}},
    ]


def build_cand_from_source(src_text: str, tag: str = "cand"):
    tmp_dir = REPO_ROOT / "build" / "test_leaf_003ea54c_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    src_path = tmp_dir / f"{tag}.cpp"
    obj_path = tmp_dir / f"{tag}.o"
    src_path.write_text(src_text, encoding="utf-8")
    res = compile_tu_armv6k(src_path, obj_path)
    assert res.returncode == 0, f"Compile failed ({tag}):\n{res.stderr}"
    stub_map = {name: STUB_BASE + i * 8 for i, name in enumerate(CALLEES)}
    cand_bytes, cand_entry = patch_cand_elf(obj_path.read_bytes(), CAND_BASE, "engine_func_003ea54c", stub_map)
    return cand_bytes, cand_entry, stub_map


def main():
    code_bin = CODE_BIN.read_bytes()
    orig_off = FUNC_ADDR - 0x00100000
    orig_bytes = code_bin[orig_off : orig_off + FUNC_SIZE]
    orig_callees = {name: addr for name, addr in CALLEES.items()}

    src_text = SRC_CPP.read_text(encoding="utf-8")
    cand_bytes, cand_entry, cand_callees = build_cand_from_source(src_text, "cand")

    cases = make_cases()
    for i, c in enumerate(cases):
        r_orig = run_one(orig_bytes, FUNC_ADDR, FUNC_ADDR, orig_callees, c)
        r_cand = run_one(cand_bytes, CAND_BASE, cand_entry, cand_callees, c)
        assert r_orig == r_cand, f"Case {i} mismatch:\n  orig={r_orig}\n  cand={r_cand}"

    # 5 negative/mutation controls
    mutations = [
        ("invert_contiguous_cmp", "if (buf + start_off <= buf + end_off)", "if (buf + start_off > buf + end_off)"),
        ("invert_max_len_cmp", "if (msg_len > *max_len)", "if (msg_len < *max_len)"),
        ("omit_free_old_data", "(*alloc)->free(alloc, old_data);", "// omitted"),
        ("wrong_first_len", "u32 first_len = cap - read_pos;", "u32 first_len = cap - read_pos + 1;"),
        ("return_1_on_oom", "return 0;\n                }\n            }", "return 1;\n                }\n            }"),
    ]
    for name, old_s, new_s in mutations:
        assert old_s in src_text, f"Mutation target not found: {name}"
        m_bytes, m_entry, m_callees = build_cand_from_source(src_text.replace(old_s, new_s, 1), name)
        caught = False
        for c in cases:
            r_orig = run_one(orig_bytes, FUNC_ADDR, FUNC_ADDR, orig_callees, c)
            try:
                r_mut = run_one(m_bytes, CAND_BASE, m_entry, m_callees, c)
            except Exception:
                caught = True
                break
            if r_orig != r_mut:
                caught = True
                break
        assert caught, f"Mutation control not caught: {name}"
        print(f"NEG_CTRL PASS (caught): {name}")

    print(f"ALL PASS: {len(cases)} cases + {len(mutations)} negative controls")


if __name__ == "__main__":
    main()
