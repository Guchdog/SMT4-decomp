import struct
import sys
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM
from unicorn.arm_const import (
    UC_ARM_REG_C1_C0_2,
    UC_ARM_REG_CPSR,
    UC_ARM_REG_FPEXC,
    UC_ARM_REG_LR,
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_R2,
    UC_ARM_REG_SP,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from build_check import compile_tu_armv6k  # noqa: E402

CODE_BIN = REPO_ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = REPO_ROOT / "src" / "engine" / "leaf_batch45_c.cpp"

FUNC_ADDR = 0x003AF524
FUNC_SIZE = 1484
FUNC_3FBE64 = 0x003FBE64

STUB_RET = 0x00600000
STUB_ALLOC = 0x00600100
STUB_FREE = 0x00600110
STUB_OOM = 0x00600120
STUB_3FBE64 = 0x00600130
CAND_BASE = 0x00700000
STACK_TOP = 0x0080FFF0

ALLOC_VTBL = 0x00500000
ALLOC_OBJ = 0x00500020
SELF_ADDR = 0x00500100
TBL_ADDR = 0x00500200
HEAP_BASE = 0x00510000
EXT_NODE = 0x00500400
OLD_BUF_BASE = 0x00501000


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
    cursor = (base_addr + len(text_bytes) + 15) & ~15
    extra_blobs = bytearray()
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
        if s[1] != 9 or sec_name(sh[s[7]]) != text_name:
            continue
        ent_sz = s[9] or 8
        for idx in range(s[5] // ent_sz):
            r_offset, r_info = struct.unpack_from("<II", elf_bytes, s[4] + idx * ent_sz)
            r_sym = r_info >> 8
            r_type = r_info & 0xFF
            sname, sval, _, _, sshndx = sym_list[r_sym]
            in_func = func_val <= r_offset < func_val + func_size
            if not in_func and not (r_type in (28, 29) and sname in stub_map):
                continue
            if r_type in (28, 29):
                if sname in stub_map:
                    target = stub_map[sname]
                elif sshndx == func_shndx:
                    target = base_addr + sval
                else:
                    raise RuntimeError(f"Unresolved branch target {sname}")
                pc = base_addr + r_offset + 8
                disp = (target - pc) >> 2
                insn = struct.unpack_from("<I", text_bytes, r_offset)[0]
                insn = (insn & 0xFF000000) | (disp & 0x00FFFFFF)
                struct.pack_into("<I", text_bytes, r_offset, insn)
            elif r_type in (2, 43, 44):
                target = sec_bases[sshndx] + sval
                if r_type == 2:
                    addend = struct.unpack_from("<i", text_bytes, r_offset)[0]
                    struct.pack_into("<I", text_bytes, r_offset, (target + addend) & 0xFFFFFFFF)
                elif r_type == 43:
                    insn = struct.unpack_from("<I", text_bytes, r_offset)[0]
                    imm16 = target & 0xFFFF
                    insn = (insn & 0xFFF0F000) | ((imm16 & 0xF000) << 4) | (imm16 & 0x0FFF)
                    struct.pack_into("<I", text_bytes, r_offset, insn)
                elif r_type == 44:
                    insn = struct.unpack_from("<I", text_bytes, r_offset)[0]
                    imm16 = (target >> 16) & 0xFFFF
                    insn = (insn & 0xFFF0F000) | ((imm16 & 0xF000) << 4) | (imm16 & 0x0FFF)
                    struct.pack_into("<I", text_bytes, r_offset, insn)
            else:
                raise RuntimeError(f"Unhandled reloc type {r_type} for {sname}")

    return base_addr + func_val, bytes(text_bytes) + bytes(extra_blobs)


STUB_MAP = {"func_003fbe64": STUB_3FBE64}


def run_case(orig_bytes: bytes, cand_entry: int, cand_image: bytes, case: dict):
    results = []
    for is_orig in (True, False):
        uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        uc.mem_map(0x00100000, 0x00320000)
        uc.mem_map(0x00500000, 0x00100000)
        uc.mem_map(STUB_RET, 0x00010000)
        uc.mem_map(CAND_BASE, 0x00100000)
        uc.mem_map(0x00800000, 0x00020000)

        uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
        uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

        bx_lr = struct.pack("<I", 0xE12FFF1E)
        uc.mem_write(STUB_RET, bx_lr)
        uc.mem_write(STUB_ALLOC, bx_lr)
        uc.mem_write(STUB_FREE, bx_lr)
        uc.mem_write(STUB_OOM, bx_lr)
        addr_3fbe64 = FUNC_3FBE64 if is_orig else STUB_3FBE64
        uc.mem_write(addr_3fbe64, bx_lr)

        if is_orig:
            uc.mem_write(FUNC_ADDR, orig_bytes)
        else:
            uc.mem_write(CAND_BASE, cand_image)

        uc.mem_write(ALLOC_VTBL, struct.pack("<3I", STUB_ALLOC, STUB_FREE, STUB_OOM))
        uc.mem_write(ALLOC_OBJ, struct.pack("<I", ALLOC_VTBL))

        # Init self (0x70 bytes)
        uc.mem_write(SELF_ADDR, b"\x00" * 0x70)
        uc.mem_write(SELF_ADDR + 0x00, struct.pack("<I", ALLOC_OBJ))
        # Vec offsets: 0x04 (byte), 0x20 (ref), 0x30 (ref), 0x5C (byte)
        for voff in (0x04, 0x20, 0x30, 0x5C):
            uc.mem_write(SELF_ADDR + voff, struct.pack("<I", ALLOC_OBJ))

        if case.get("prepopulate", False):
            # ByteVec 0: cap=2, size=3
            b0 = OLD_BUF_BASE
            uc.mem_write(b0, b"\x11\x22\x33")
            uc.mem_write(SELF_ADDR + 0x04, struct.pack("<4I", ALLOC_OBJ, b0, 2, 3))
            # RefVec 1: cap=2, size=2
            r1 = OLD_BUF_BASE + 0x100
            obj_sole = OLD_BUF_BASE + 0x200
            uc.mem_write(r1 + 0x00, struct.pack("<4I", ALLOC_OBJ, obj_sole, r1, r1))
            uc.mem_write(r1 + 0x10, struct.pack("<4I", ALLOC_OBJ, 0, EXT_NODE, EXT_NODE))
            uc.mem_write(EXT_NODE, struct.pack("<4I", ALLOC_OBJ, 0, r1 + 0x10, r1 + 0x10))
            uc.mem_write(SELF_ADDR + 0x20, struct.pack("<4I", ALLOC_OBJ, r1, 2, 2))
            # RefVec 2: cap=1, size=1
            r2 = OLD_BUF_BASE + 0x300
            uc.mem_write(r2, struct.pack("<4I", ALLOC_OBJ, 0, r2, r2))
            uc.mem_write(SELF_ADDR + 0x30, struct.pack("<4I", ALLOC_OBJ, r2, 1, 1))
            # ByteVec 3: cap=2, size=2
            b3 = OLD_BUF_BASE + 0x400
            uc.mem_write(b3, b"\xAA\xBB")
            uc.mem_write(SELF_ADDR + 0x5C, struct.pack("<4I", ALLOC_OBJ, b3, 2, 2))
        else:
            for voff, cap in zip((0x04, 0x20, 0x30, 0x5C), case.get("init_caps", (0, 0, 0, 0))):
                uc.mem_write(SELF_ADDR + voff + 8, struct.pack("<I", cap))

        # Table at TBL_ADDR
        entries = case.get("entries", [])
        uc.mem_write(TBL_ADDR, struct.pack("<I", len(entries)))
        for idx, (k, c0, c1, c2, c3) in enumerate(entries):
            uc.mem_write(TBL_ADDR + 4 + idx * 20, struct.pack("<5I", k, c0, c1, c2, c3))

        heap_cursor = [HEAP_BASE]
        alloc_count = [0]
        fail_alloc_on = case.get("fail_alloc_on")
        events = []

        def hook_code(uc_inst, address, size, user_data):
            if address == STUB_ALLOC:
                alloc_count[0] += 1
                sz = uc_inst.reg_read(UC_ARM_REG_R1)
                if fail_alloc_on == alloc_count[0]:
                    events.append(("alloc_fail", sz))
                    uc_inst.reg_write(UC_ARM_REG_R0, 0)
                else:
                    ptr = heap_cursor[0]
                    heap_cursor[0] += (sz + 15) & ~15
                    uc_inst.mem_write(ptr, b"\x00" * sz)
                    events.append(("alloc", sz, ptr))
                    uc_inst.reg_write(UC_ARM_REG_R0, ptr)
            elif address == STUB_FREE:
                ptr = uc_inst.reg_read(UC_ARM_REG_R1)
                events.append(("free", ptr))
            elif address == STUB_OOM:
                msg = uc_inst.reg_read(UC_ARM_REG_R1)
                sz = uc_inst.reg_read(UC_ARM_REG_R2)
                events.append(("oom", msg, sz))
            elif address == addr_3fbe64:
                vec_ptr = uc_inst.reg_read(UC_ARM_REG_R0)
                item_ptr = uc_inst.reg_read(UC_ARM_REG_R1)
                events.append(("3fbe64", vec_ptr))
                if case.get("fail_3fbe64", False):
                    uc_inst.reg_write(UC_ARM_REG_R0, 0)
                else:
                    data_ptr, cap, sz = struct.unpack("<3I", uc_inst.mem_read(vec_ptr + 4, 12))
                    if sz < cap:
                        dst = data_ptr + sz * 16
                        i_alloc, i_obj, i_prev, i_next = struct.unpack("<4I", uc_inst.mem_read(item_ptr, 16))
                        uc_inst.mem_write(dst, struct.pack("<4I", i_alloc, i_obj, item_ptr, i_next))
                        uc_inst.mem_write(i_next + 8, struct.pack("<I", dst))
                        uc_inst.mem_write(item_ptr + 12, struct.pack("<I", dst))
                        uc_inst.mem_write(vec_ptr + 12, struct.pack("<I", sz + 1))
                    uc_inst.reg_write(UC_ARM_REG_R0, 1)

        uc.hook_add(1 << 2, hook_code)
        uc.reg_write(UC_ARM_REG_CPSR, 0x10)
        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, STUB_RET)
        uc.reg_write(UC_ARM_REG_R0, SELF_ADDR)
        uc.reg_write(UC_ARM_REG_R1, case.get("key", 0x42))
        uc.reg_write(UC_ARM_REG_R2, TBL_ADDR)

        entry = FUNC_ADDR if is_orig else cand_entry
        uc.emu_start(entry, STUB_RET, timeout=5_000_000, count=200_000)

        ret = uc.reg_read(UC_ARM_REG_R0)
        out_self = bytes(uc.mem_read(SELF_ADDR, 0x70))
        b0_ptr = struct.unpack("<I", out_self[0x08:0x0C])[0]
        b3_ptr = struct.unpack("<I", out_self[0x60:0x64])[0]
        b0_data = bytes(uc.mem_read(b0_ptr, 4)) if b0_ptr else b""
        b3_data = bytes(uc.mem_read(b3_ptr, 4)) if b3_ptr else b""
        results.append((ret, out_self, b0_data, b3_data, events))

    if results[0] != results[1]:
        return False, f"orig={results[0]} != cand={results[1]}"
    return True, "ok"


CASES = [
    {"name": "tbl_count_0", "entries": []},
    {"name": "key_not_found", "key": 0x99, "entries": [(0x10, 1, 1, 1, 1), (0x20, 2, 2, 2, 2)]},
    {
        "name": "all_caps_already_sufficient",
        "key": 0x20,
        "init_caps": (5, 3, 4, 6),
        "entries": [(0x10, 1, 1, 1, 1), (0x20, 4, 0, 4, 5)],
    },
    {
        "name": "grow_all_empty_vecs",
        "key": 0x42,
        "entries": [(0x42, 4, 2, 3, 5)],
    },
    {
        "name": "key_at_index_1",
        "key": 0x42,
        "entries": [(0x10, 1, 1, 1, 1), (0x42, 3, 1, 2, 4)],
    },
    {
        "name": "grow_prepopulated_copy_and_unlink",
        "key": 0x42,
        "prepopulate": True,
        "entries": [(0x42, 4, 3, 2, 5)],
    },
    {"name": "oom_byte_vec0", "key": 0x42, "fail_alloc_on": 1, "entries": [(0x42, 4, 2, 3, 5)]},
    {"name": "oom_ref_vec1", "key": 0x42, "fail_alloc_on": 2, "entries": [(0x42, 4, 2, 3, 5)]},
    {"name": "oom_ref_vec2", "key": 0x42, "fail_alloc_on": 5, "entries": [(0x42, 4, 2, 3, 5)]},
    {"name": "oom_byte_vec3", "key": 0x42, "fail_alloc_on": 6, "entries": [(0x42, 4, 2, 3, 5)]},
    {"name": "fail_3fbe64", "key": 0x42, "fail_3fbe64": True, "entries": [(0x42, 4, 2, 3, 5)]},
]


def run_negative_controls(orig_bytes: bytes):
    mutants = [
        ("mut1_wrong_table_stride", "tbl + i * 20u", "tbl + i * 16u"),
        ("mut2_wrong_ref_byte_sz", "u32 byte_sz = new_cap << 4;", "u32 byte_sz = new_cap << 3;"),
        ("mut3_wrong_node_size", "alloc->vtbl->alloc(alloc, 0x18u)", "alloc->vtbl->alloc(alloc, 0x10u)"),
        ("mut4_missing_byte_copy", "new_buf[i] = old_buf[i];", "new_buf[i] = 0;"),
        ("mut5_wrong_3fbe64_fail_ret", "if (ok == 0u) {\n            return 0;", "if (ok == 0u) {\n            return 1;"),
    ]
    src_text = SRC_CPP.read_text(encoding="utf-8")
    tmp_dir = REPO_ROOT / "build" / "test_leaf_003af524_mut"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    for mname, old, new in mutants:
        assert old in src_text, f"Mutant target missing: {old}"
        mut_src = tmp_dir / f"{mname}.cpp"
        mut_obj = tmp_dir / f"{mname}.o"
        mut_src.write_text(src_text.replace(old, new, 1), encoding="utf-8")
        res = compile_tu_armv6k(mut_src, mut_obj)
        if res.returncode != 0:
            raise RuntimeError(f"Mutant {mname} failed to compile: {res.stderr}")
        m_entry, m_img = patch_cand_elf(mut_obj.read_bytes(), CAND_BASE, "func_003af524", STUB_MAP)
        caught = False
        for c in CASES:
            ok, _ = run_case(orig_bytes, m_entry, m_img, c)
            if not ok:
                caught = True
                break
        if not caught:
            raise RuntimeError(f"Negative control {mname} was NOT caught!")
        print(f"NEG_CTRL PASS (caught): {mname}")


def main():
    code_all = CODE_BIN.read_bytes()
    off = FUNC_ADDR - 0x00100000
    orig_bytes = code_all[off : off + FUNC_SIZE]

    obj_out = REPO_ROOT / "build" / "test_leaf_003af524.o"
    obj_out.parent.mkdir(parents=True, exist_ok=True)
    res = compile_tu_armv6k(SRC_CPP, obj_out)
    if res.returncode != 0:
        print("COMPILE FAIL:\n", res.stderr)
        sys.exit(1)

    cand_entry, cand_image = patch_cand_elf(obj_out.read_bytes(), CAND_BASE, "func_003af524", STUB_MAP)

    for c in CASES:
        ok, msg = run_case(orig_bytes, cand_entry, cand_image, c)
        if not ok:
            print(f"FAIL {c['name']}: {msg}")
            sys.exit(1)
        print(f"PASS: {c['name']}")

    run_negative_controls(orig_bytes)
    print(f"ALL PASS: {len(CASES)} cases + 5 negative controls")


if __name__ == "__main__":
    main()
