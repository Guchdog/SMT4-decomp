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
    UC_ARM_REG_R3,
    UC_ARM_REG_S0,
    UC_ARM_REG_S1,
    UC_ARM_REG_S2,
    UC_ARM_REG_S3,
    UC_ARM_REG_S4,
    UC_ARM_REG_SP,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from build_check import compile_tu_armv6k  # noqa: E402

CODE_BIN = REPO_ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = REPO_ROOT / "src" / "engine" / "leaf_batch45_c.cpp"

FUNC_ADDR = 0x00203554
FUNC_SIZE = 1552

CALLEES = {
    "func_00262a44": (0x00262A44, 0, False),
    "func_002bf558": (0x002BF558, 6, False),
    "ui_func_002bf460": (0x002BF460, 6, False),
    "camp_func_0029f260": (0x0029F260, 1, False),
    "camp_func_0029d8e4": (0x0029D8E4, 1, False),
    "camp_func_0029f248": (0x0029F248, 1, False),
    "camp_func_002bf6d0": (0x002BF6D0, 2, False),
    "camp_func_00254298": (0x00254298, 1, False),
    "ui_func_002be7fc": (0x002BE7FC, 3, True),
    "ui_func_002be77c": (0x002BE77C, 3, False),
    "camp_func_00200410": (0x00200410, 1, False),
    "ui_func_002bf710": (0x002BF710, 0, False),
    "ui_func_0029d8fc": (0x0029D8FC, 1, False),
    "func_0029a418": (0x0029A418, 5, False),
    "shop_func_002bef70": (0x002BEF70, 1, False),
    "ui_func_002bef7c": (0x002BEF7C, 0, False),
    "camp_func_00290c38": (0x00290C38, 16, False),
}

STUB_RET = 0x00600000
STUB_BASE = 0x00600100
STUB_CB = 0x00600400
CAND_BASE = 0x00700000
STACK_TOP = 0x0080FFF0

R5_ADDR = 0x00500000
G_44EA00 = 0x0044EA00
G_OBJ = 0x00510000
LAYOUT_BASE = 0x00520000
ITEM_BASE = 0x00530000
BOX_ADDR = 0x00540000


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
                    addend16 = ((insn >> 4) & 0xF000) | (insn & 0x0FFF)
                    imm16 = (target + addend16) & 0xFFFF
                    insn = (insn & 0xFFF0F000) | ((imm16 & 0xF000) << 4) | (imm16 & 0x0FFF)
                    struct.pack_into("<I", text_bytes, r_offset, insn)
                elif r_type == 44:
                    insn = struct.unpack_from("<I", text_bytes, r_offset)[0]
                    addend_hi = (((insn >> 4) & 0xF000) | (insn & 0x0FFF)) << 16
                    imm16 = ((target + addend_hi) >> 16) & 0xFFFF
                    insn = (insn & 0xFFF0F000) | ((imm16 & 0xF000) << 4) | (imm16 & 0x0FFF)
                    struct.pack_into("<I", text_bytes, r_offset, insn)
            else:
                raise RuntimeError(f"Unhandled reloc type {r_type} for {sname}")

    return base_addr + func_val, bytes(text_bytes) + bytes(extra_blobs)


STUB_MAP = {name: STUB_BASE + idx * 0x10 for idx, name in enumerate(CALLEES)}


def run_case(orig_bytes: bytes, cand_entry: int, cand_image: bytes, case: dict):
    results = []
    for is_orig in (True, False):
        uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        uc.mem_map(0x00100000, 0x00300000)
        uc.mem_map(0x00400000, 0x00200000)
        uc.mem_map(STUB_RET, 0x00010000)
        uc.mem_map(CAND_BASE, 0x00100000)
        uc.mem_map(0x00800000, 0x00020000)

        uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
        uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

        bx_lr = struct.pack("<I", 0xE12FFF1E)
        thumb_bx_lr = struct.pack("<H", 0x4770)
        uc.mem_write(STUB_RET, bx_lr)
        uc.mem_write(STUB_CB, bx_lr)
        if is_orig:
            uc.mem_write(FUNC_ADDR, orig_bytes)
            addr_to_info = {addr: (name, arity, is_thumb) for name, (addr, arity, is_thumb) in CALLEES.items()}
        else:
            uc.mem_write(CAND_BASE, cand_image)
            addr_to_info = {STUB_MAP[name]: (name, CALLEES[name][1], False) for name in CALLEES}
        for addr, (_, _, is_thumb) in addr_to_info.items():
            uc.mem_write(addr, thumb_bx_lr if is_thumb else bx_lr)

        # Init R5 (0x9600 bytes)
        uc.mem_write(R5_ADDR, b"\x00" * 0x9600)
        uc.mem_write(R5_ADDR + 0x44, struct.pack("<f", 0.75))
        uc.mem_write(R5_ADDR + 0x252, struct.pack("<b", case.get("b252", 1)))
        uc.mem_write(R5_ADDR + 0x438, struct.pack("<3h", 1, 5, 6))
        uc.mem_write(R5_ADDR + 0x472, struct.pack("<3h", 11, 22, 33))
        for i in range(4):
            uc.mem_write(R5_ADDR + 0x9468 + i * 2, struct.pack("<H", 10 + i))

        uc.mem_write(G_44EA00, struct.pack("<I", G_OBJ))
        g_draw = G_OBJ + 0x130C
        uc.mem_write(g_draw, b"\x00" * 0x20)
        uc.mem_write(g_draw + 0x18, struct.pack("<B", case.get("g18", 0)))
        uc.mem_write(g_draw + 0x1C, struct.pack("<I", STUB_CB))

        uc.mem_write(BOX_ADDR, struct.pack("<hh", 40, 50))
        for i in range(0x200):
            la = LAYOUT_BASE + i * 0x10
            uc.mem_write(la + 8, struct.pack("<hhI", (i % 10) + 1, (i % 7) + 2, BOX_ADDR))

        for i in range(4):
            ia = ITEM_BASE + i * 0x20
            uc.mem_write(ia + 8, f"Item{i}\x00".encode("ascii"))

        calls = []

        def hook_code(uc_inst, address, size, user_data):
            if address == STUB_CB:
                calls.append(("cb", uc_inst.reg_read(UC_ARM_REG_R0)))
                return
            info = addr_to_info.get(address)
            if info is None:
                return
            name, arity, _ = info
            r0 = uc_inst.reg_read(UC_ARM_REG_R0)
            r1 = uc_inst.reg_read(UC_ARM_REG_R1)
            r2 = uc_inst.reg_read(UC_ARM_REG_R2)
            r3 = uc_inst.reg_read(UC_ARM_REG_R3)
            sp = uc_inst.reg_read(UC_ARM_REG_SP)

            if name == "func_00262a44":
                uc_inst.reg_write(UC_ARM_REG_R0, 0 if case.get("null_r5", False) else R5_ADDR)
                calls.append((name,))
            elif name == "camp_func_0029f260":
                uc_inst.reg_write(UC_ARM_REG_R0, 0)
            elif name == "camp_func_0029d8e4":
                uc_inst.reg_write(UC_ARM_REG_R0, case.get("count", 3))
            elif name == "camp_func_0029f248":
                uc_inst.reg_write(UC_ARM_REG_R0, case.get("cur_idx", 1))
            elif name == "camp_func_002bf6d0":
                uc_inst.reg_write(UC_ARM_REG_R0, LAYOUT_BASE + r1 * 0x10)
            elif name == "camp_func_00254298":
                if r0 == 12:
                    uc_inst.reg_write(UC_ARM_REG_R0, 0)
                else:
                    uc_inst.reg_write(UC_ARM_REG_R0, ITEM_BASE + (r0 - 10) * 0x20)
            elif name == "camp_func_00200410":
                uc_inst.reg_write(UC_ARM_REG_R0, 1 if (r0 & 1) == 0 else 0)
            elif name == "ui_func_0029d8fc":
                uc_inst.reg_write(UC_ARM_REG_R0, case.get("kind", 1))
            elif name == "shop_func_002bef70":
                uc_inst.reg_write(UC_ARM_REG_R0, 12)
            elif name == "ui_func_002bef7c":
                uc_inst.reg_write(UC_ARM_REG_R0, 8)
            elif name == "ui_func_002be7fc":
                fmt = uc_inst.mem_read(r1, 2).decode("ascii", "replace")
                src = uc_inst.mem_read(r2, 6).decode("ascii", "replace")
                uc_inst.mem_write(r0, src.encode("ascii"))
                calls.append((name, fmt, src))
            elif name == "ui_func_002be77c":
                s = uc_inst.mem_read(r2, 5)
                s0 = uc_inst.reg_read(UC_ARM_REG_S0)
                s1 = uc_inst.reg_read(UC_ARM_REG_S1)
                s2 = uc_inst.reg_read(UC_ARM_REG_S2)
                s3 = uc_inst.reg_read(UC_ARM_REG_S3)
                s4 = uc_inst.reg_read(UC_ARM_REG_S4)
                calls.append((name, r0, r1, bytes(s), s0, s1, s2, s3, s4))
            elif name == "ui_func_002bf710":
                calls.append((name, uc_inst.reg_read(UC_ARM_REG_S0)))
            elif name in ("func_002bf558", "ui_func_002bf460"):
                s0, s1 = struct.unpack("<II", uc_inst.mem_read(sp, 8))
                calls.append((name, r0, r1, r2, r3, s0, s1))
            elif name == "func_0029a418":
                s0 = struct.unpack("<I", uc_inst.mem_read(sp, 4))[0]
                calls.append((name, r0, r1, r2, r3, s0))
            elif name == "camp_func_00290c38":
                stk = struct.unpack("<8I3iI", uc_inst.mem_read(sp, 48))
                calls.append((name, r0, r1, r2, r3, stk))

        uc.hook_add(1 << 2, hook_code)
        uc.reg_write(UC_ARM_REG_CPSR, 0x10)
        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, STUB_RET)
        uc.reg_write(UC_ARM_REG_R0, 100)
        uc.reg_write(UC_ARM_REG_R1, 200)

        entry = FUNC_ADDR if is_orig else cand_entry
        uc.emu_start(entry, STUB_RET, timeout=5_000_000, count=300_000)

        out_g = bytes(uc.mem_read(g_draw, 0x20))
        results.append((out_g, calls))

    if results[0] != results[1]:
        return False, f"orig={results[0]} != cand={results[1]}"
    return True, "ok"


CASES = [
    {"name": "null_r5", "null_r5": True},
    {"name": "count0_b252_0", "count": 0, "b252": 0},
    {"name": "full_draw_kind1", "count": 3, "b252": 1, "cur_idx": 0, "kind": 1},
    {"name": "full_draw_kind5_cb", "count": 3, "b252": 1, "cur_idx": 1, "kind": 5, "g18": 1},
]


def run_negative_controls(orig_bytes: bytes):
    mutants = [
        ("mut1_wrong_sel_spr", "? 0x3Du : 0x3Cu;", "? 0x3Cu : 0x3Cu;"),
        ("mut2_wrong_alpha_0_58", "0.5859375f", "0.5f"),
        ("mut3_wrong_draw_mode3", "set_draw_mode_00203554(3u);", "set_draw_mode_00203554(2u);"),
        ("mut4_missing_290c38_arg_35", "0x23u, 0x24u, 0x25u, 0x1Fu,", "0x23u, 0x24u, 0x00u, 0x1Fu,"),
        ("mut5_wrong_skip_cur", "if (static_cast<s8>(r5[0x252u]) != 0 && camp_func_0029f248(list) == i)", "if (false)"),
    ]
    src_text = SRC_CPP.read_text(encoding="utf-8")
    tmp_dir = REPO_ROOT / "build" / "test_leaf_00203554_mut"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    for mname, old, new in mutants:
        assert old in src_text, f"Mutant target missing: {old}"
        mut_src = tmp_dir / f"{mname}.cpp"
        mut_obj = tmp_dir / f"{mname}.o"
        mut_src.write_text(src_text.replace(old, new, 1), encoding="utf-8")
        res = compile_tu_armv6k(mut_src, mut_obj)
        if res.returncode != 0:
            raise RuntimeError(f"Mutant {mname} failed to compile: {res.stderr}")
        m_entry, m_img = patch_cand_elf(mut_obj.read_bytes(), CAND_BASE, "ui_func_00203554", STUB_MAP)
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

    obj_out = REPO_ROOT / "build" / "test_leaf_00203554.o"
    obj_out.parent.mkdir(parents=True, exist_ok=True)
    res = compile_tu_armv6k(SRC_CPP, obj_out)
    if res.returncode != 0:
        print("COMPILE FAIL:\n", res.stderr)
        sys.exit(1)

    cand_entry, cand_image = patch_cand_elf(obj_out.read_bytes(), CAND_BASE, "ui_func_00203554", STUB_MAP)

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
