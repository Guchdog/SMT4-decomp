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
    UC_ARM_REG_S0,
    UC_ARM_REG_SP,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from build_check import compile_tu_armv6k  # noqa: E402

CODE_BIN = REPO_ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = REPO_ROOT / "src" / "engine" / "leaf_batch45_c.cpp"

FUNC_ADDR = 0x0021A610
FUNC_SIZE = 1492
FUNC_26959C = 0x0026959C
FUNC_2F9F54 = 0x002F9F54
FUNC_2C7420 = 0x002C7420

STUB_RET = 0x00600000
STUB_26959C = 0x00600100
STUB_2F9F54 = 0x00600110
STUB_2C7420 = 0x00600120
CAND_BASE = 0x00700000
STACK_TOP = 0x0080FFF0

SELF_ADDR = 0x00500000
P30_ADDR = 0x00500100
P28_ADDR = 0x00500200
P2C_ADDR = 0x00500300
P5_ARR = 0x00501000
IDX_ARR = 0x00502000
V10_HDR = 0x00503000
V14_HDR = 0x00503100
V10_DATA = 0x00504000
V14_DATA = 0x00505000
G_472560 = 0x00472560
G_4EA810 = 0x004EA810
G_4EA91C = 0x004EA91C


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


STUB_MAP = {
    "func_0026959c": STUB_26959C,
    "func_002f9f54": STUB_2F9F54,
    "ui_func_002c7420": STUB_2C7420,
}


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
        uc.mem_write(STUB_RET, bx_lr)
        addr_26959c = FUNC_26959C if is_orig else STUB_26959C
        addr_2f9f54 = FUNC_2F9F54 if is_orig else STUB_2F9F54
        addr_2c7420 = FUNC_2C7420 if is_orig else STUB_2C7420
        for a in (addr_26959c, addr_2f9f54, addr_2c7420):
            uc.mem_write(a, bx_lr)
        if is_orig:
            uc.mem_write(FUNC_ADDR, orig_bytes)
        else:
            uc.mem_write(CAND_BASE, cand_image)

        uc.mem_write(G_472560, bytes([0x11, 0x22, 0x33, 0x44]))
        uc.mem_write(G_4EA810, struct.pack("<3f", 1.0, 2.0, 3.0))
        uc.mem_write(G_4EA91C, b"\x00" * 0x30)

        items = case.get("items", [])
        uc.mem_write(SELF_ADDR, b"\x00" * 0x40)
        uc.mem_write(SELF_ADDR + 0x00, struct.pack("<i", case.get("count", len(items))))
        uc.mem_write(SELF_ADDR + 0x04, struct.pack("<I", case.get("base_col", 0x80C040FF)))
        uc.mem_write(SELF_ADDR + 0x10, struct.pack("<I", case.get("s10", 1)))
        uc.mem_write(SELF_ADDR + 0x24, struct.pack("<f", case.get("s24", 5.0)))
        uc.mem_write(SELF_ADDR + 0x28, struct.pack("<I", P28_ADDR))
        uc.mem_write(SELF_ADDR + 0x2C, struct.pack("<I", P2C_ADDR if case.get("has_p2c", True) else 0))
        uc.mem_write(SELF_ADDR + 0x30, struct.pack("<I", P30_ADDR))

        uc.mem_write(P30_ADDR + 0x10, struct.pack("<I", case.get("p30_cap", 2)))
        uc.mem_write(P30_ADDR + 0x18, struct.pack("<I", P5_ARR))

        uc.mem_write(P28_ADDR + 0x10, struct.pack("<I", V10_HDR))
        uc.mem_write(P28_ADDR + 0x14, struct.pack("<I", V14_HDR))
        uc.mem_write(P28_ADDR + 0x18, struct.pack("<I", IDX_ARR))
        uc.mem_write(V10_HDR + 0x04, struct.pack("<I", V10_DATA))
        uc.mem_write(V14_HDR + 0x04, struct.pack("<I", V14_DATA))
        uc.mem_write(V10_DATA, b"\x00" * 0x100)
        uc.mem_write(V14_DATA, b"\x00" * 0x100)
        uc.mem_write(IDX_ARR, b"\x00" * 0x40)
        uc.mem_write(P2C_ADDR, b"\x00" * 0x20)

        for idx, it in enumerate(items):
            uc.mem_write(IDX_ARR + idx * 2, struct.pack("<h", it.get("idx_val", 0)))
            uc.mem_write(
                P5_ARR + idx * 0x28,
                struct.pack(
                    "<3fIiIf",
                    it.get("x", 1.0),
                    it.get("y", 2.0),
                    it.get("z", 3.0),
                    0,
                    it.get("mode", 1),
                    it.get("col", 0xFFFFFFFF),
                    it.get("scale", 1.5),
                ),
            )

        calls = []

        def hook_code(uc_inst, address, size, user_data):
            if address == addr_26959c:
                calls.append(("26959c", uc_inst.reg_read(UC_ARM_REG_R0)))
            elif address == addr_2f9f54:
                r0 = uc_inst.reg_read(UC_ARM_REG_R0)
                r1 = uc_inst.reg_read(UC_ARM_REG_R1)
                r2 = uc_inst.reg_read(UC_ARM_REG_R2)
                s0 = uc_inst.reg_read(UC_ARM_REG_S0)
                pos_bytes = bytes(uc_inst.mem_read(r2, 12))
                calls.append(("2f9f54", r0, r1, pos_bytes, s0))
            elif address == addr_2c7420:
                r0 = uc_inst.reg_read(UC_ARM_REG_R0)
                s0 = uc_inst.reg_read(UC_ARM_REG_S0)
                calls.append(("2c7420", r0, s0))

        uc.hook_add(1 << 2, hook_code)
        uc.reg_write(UC_ARM_REG_CPSR, 0x10)
        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, STUB_RET)
        uc.reg_write(UC_ARM_REG_R0, SELF_ADDR)

        entry = FUNC_ADDR if is_orig else cand_entry
        uc.emu_start(entry, STUB_RET, timeout=5_000_000, count=200_000)

        n = max(len(items), 1)
        out_v10 = bytes(uc.mem_read(V10_DATA, n * 16))
        out_v14 = bytes(uc.mem_read(V14_DATA, n * 16))
        out_idx = bytes(uc.mem_read(IDX_ARR, n * 2))
        out_p2c = bytes(uc.mem_read(P2C_ADDR, 8))
        results.append((out_v10, out_v14, out_idx, out_p2c, calls))

    if results[0] != results[1]:
        return False, f"orig={results[0]} != cand={results[1]}"
    return True, "ok"


CASES = [
    {"name": "count_0", "count": 0},
    {"name": "count_neg", "count": -1, "has_p2c": False},
    {
        "name": "all_modes_mix",
        "base_col": 0x80C040FF,
        "s10": 2,
        "p30_cap": 2,
        "items": [
            {"idx_val": -1, "mode": 1},
            {"idx_val": 0, "mode": -2},
            {"idx_val": 1, "mode": -1},
            {"idx_val": 2, "mode": 0},
            {"idx_val": 3, "mode": 1, "col": 0x4080C0FF, "x": 4.0, "y": 5.0, "z": 6.0, "scale": 2.5},
        ],
    },
    {
        "name": "p2c_skipped_over_cap",
        "s10": 5,
        "p30_cap": 2,
        "items": [{"idx_val": 0, "mode": 2, "col": 0xFF112233}],
    },
]


def run_negative_controls(orig_bytes: bytes):
    mutants = [
        ("mut1_wrong_mode_minus2_idx", "(mode == -2) ? static_cast<u16>(0xFFFFu) : static_cast<u16>(0u)", "static_cast<u16>(0u)"),
        ("mut2_wrong_v10_lane_order", "write_color_vecs_0021a610(r6, idx, c3, c2, c1, c0);", "write_color_vecs_0021a610(r6, idx, c0, c1, c2, c3);"),
        ("mut3_wrong_scale_0_1", "*reinterpret_cast<f32*>(self + 0x24) * 0.10000000149011612f", "*reinterpret_cast<f32*>(self + 0x24) * 0.25f"),
        ("mut4_missing_skip_neg1", "if (idx_arr[idx] == 0xFFFFu) {\n            continue;\n        }", ""),
        ("mut5_wrong_cap_cmp", "*reinterpret_cast<u32*>(self + 0x10) <= cap", "*reinterpret_cast<u32*>(self + 0x10) < cap"),
    ]
    src_text = SRC_CPP.read_text(encoding="utf-8")
    tmp_dir = REPO_ROOT / "build" / "test_leaf_0021a610_mut"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    for mname, old, new in mutants:
        assert old in src_text, f"Mutant target missing: {old}"
        mut_src = tmp_dir / f"{mname}.cpp"
        mut_obj = tmp_dir / f"{mname}.o"
        mut_src.write_text(src_text.replace(old, new, 1), encoding="utf-8")
        res = compile_tu_armv6k(mut_src, mut_obj)
        if res.returncode != 0:
            raise RuntimeError(f"Mutant {mname} failed to compile: {res.stderr}")
        m_entry, m_img = patch_cand_elf(mut_obj.read_bytes(), CAND_BASE, "func_0021a610", STUB_MAP)
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

    obj_out = REPO_ROOT / "build" / "test_leaf_0021a610.o"
    obj_out.parent.mkdir(parents=True, exist_ok=True)
    res = compile_tu_armv6k(SRC_CPP, obj_out)
    if res.returncode != 0:
        print("COMPILE FAIL:\n", res.stderr)
        sys.exit(1)

    cand_entry, cand_image = patch_cand_elf(obj_out.read_bytes(), CAND_BASE, "func_0021a610", STUB_MAP)

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
