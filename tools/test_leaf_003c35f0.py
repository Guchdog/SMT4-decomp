import struct
import sys
from pathlib import Path

from unicorn import UC_ARCH_ARM, UC_HOOK_CODE, UC_MODE_ARM, Uc
from unicorn.arm_const import (
    UC_ARM_REG_C1_C0_2,
    UC_ARM_REG_CPSR,
    UC_ARM_REG_FPEXC,
    UC_ARM_REG_LR,
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

FUNC_ADDR = 0x003C35F0
FUNC_SIZE = 1588

CALLEES = {
    "battle_func_002564cc": 0x002564CC,
    "battle_func_0022a5f8": 0x0022A5F8,
    "battle_func_0022a5d8": 0x0022A5D8,
    "ui_func_002c17d4": 0x002C17D4,
    "battle_func_00256418": 0x00256418,
    "script_vm_func_0027eb98": 0x0027EB98,
    "battle_func_00246f90": 0x00246F90,
    "battle_func_00246ea4": 0x00246EA4,
    "camp_func_002a8a08": 0x002A8A08,
    "camp_func_002a89e4": 0x002A89E4,
    "script_vm_func_00296020": 0x00296020,
    "battle_func_0026e88c": 0x0026E88C,
    "camp_func_00263194": 0x00263194,
}

STUB_RET = 0x00600000
STUB_BASE = 0x00600100
CAND_BASE = 0x00700000
STACK_TOP = 0x0080FFF0

SELF_ADDR = 0x00500000
SUB_ADDR = 0x00501000
A5F8_VAL_ADDR = 0x00501100
MGR_ADDR = 0x00510000
ITEM_TABLE_ADDR = 0x00520000
UNITS_BASE = 0x00530000
PARTY_ADDR = 0x00540000
DEMONS_BASE = 0x00550000
G_43427C = 0x0043427C


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

    bx_lr = struct.pack("<I", 0xE12FFF1E)
    uc.mem_write(STUB_RET, bx_lr)
    for addr in callee_addrs.values():
        uc.mem_write(addr, bx_lr)

    uc.mem_write(G_43427C, struct.pack("<I", 0x12345678))
    uc.mem_write(A5F8_VAL_ADDR, struct.pack("<I", case.get("a5f8_val", 7)))

    self_bytes = bytearray(0x28)
    struct.pack_into("<I", self_bytes, 0x10, SUB_ADDR)
    self_bytes[0x14] = case.get("f14", 0)
    self_bytes[0x15] = case.get("f15", 0)
    self_bytes[0x16] = case.get("f16", 0)
    struct.pack_into("<I", self_bytes, 0x18, case.get("flags", 0))
    struct.pack_into("<i", self_bytes, 0x1C, case.get("sel", -1))
    uc.mem_write(SELF_ADDR, bytes(self_bytes))

    uc.mem_write(MGR_ADDR + 0x1E98, struct.pack("<I", ITEM_TABLE_ADDR))

    # Units (each 0x80 bytes)
    units_cfg = case.get("units", {})
    for idx, (u_flags, slots) in units_cfg.items():
        ubuf = bytearray(0x80)
        struct.pack_into("<I", ubuf, 0x00, u_flags)
        for j in range(0x32):
            struct.pack_into("<h", ubuf, 8 + j * 2, slots.get(j, -1))
        uc.mem_write(UNITS_BASE + idx * 0x80, bytes(ubuf))

    # Party
    party = case.get("party", [])
    uc.mem_write(PARTY_ADDR + 0x910B, struct.pack("<B", len(party)))
    for k, idx in enumerate(party):
        uc.mem_write(PARTY_ADDR + 0x90F0 + k, struct.pack("<b", idx))

    events = []
    addr_to_name = {v: k for k, v in callee_addrs.items()}

    def hook_code(uc_inst, address, size, user_data):
        name = addr_to_name.get(address)
        r0 = uc_inst.reg_read(UC_ARM_REG_R0)
        r1 = uc_inst.reg_read(UC_ARM_REG_R1)
        r2 = uc_inst.reg_read(UC_ARM_REG_R2)
        r3 = uc_inst.reg_read(UC_ARM_REG_R3)
        sp = uc_inst.reg_read(UC_ARM_REG_SP)
        if name == "battle_func_002564cc":
            uc_inst.reg_write(UC_ARM_REG_R0, case["cmd"])
        elif name == "battle_func_0022a5f8":
            events.append(("a5f8", r0, r1))
            uc_inst.reg_write(UC_ARM_REG_R0, A5F8_VAL_ADDR)
        elif name == "battle_func_0022a5d8":
            events.append(("a5d8", r0, r1))
            uc_inst.reg_write(UC_ARM_REG_R0, case.get("a5d8_ret", 0))
        elif name == "ui_func_002c17d4":
            uc_inst.reg_write(UC_ARM_REG_R0, case.get("c17d4_ret", 1))
        elif name == "battle_func_00256418":
            u_addr = (UNITS_BASE + r1 * 0x80) if r1 in units_cfg else 0
            uc_inst.reg_write(UC_ARM_REG_R0, u_addr)
        elif name == "script_vm_func_0027eb98":
            uc_inst.reg_write(UC_ARM_REG_R0, r0 ^ 0x1111)
        elif name == "battle_func_00246f90":
            arg4 = struct.unpack_from("<I", uc_inst.mem_read(sp, 4), 0)[0]
            events.append(("f90", r0, r1, r2, r3, arg4))
        elif name == "battle_func_00246ea4":
            events.append(("ea4", r0, r1, r2, r3))
        elif name == "camp_func_002a8a08":
            uc_inst.reg_write(UC_ARM_REG_R0, PARTY_ADDR)
        elif name == "camp_func_002a89e4":
            d_addr = (DEMONS_BASE + r0 * 0x40) if r0 in case.get("demons", set()) else 0
            uc_inst.reg_write(UC_ARM_REG_R0, d_addr)
        elif name == "script_vm_func_00296020":
            d_idx = (r0 - DEMONS_BASE) // 0x40
            uc_inst.reg_write(UC_ARM_REG_R0, 1 if d_idx in case.get("skip_demons", set()) else 0)
        elif name == "battle_func_0026e88c":
            events.append(("e88c", r0, r1))
        elif name == "camp_func_00263194":
            events.append(("3194", r0, r1))

    for stub_addr in callee_addrs.values():
        uc.hook_add(UC_HOOK_CODE, hook_code, begin=stub_addr, end=stub_addr)

    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, STUB_RET)
    uc.reg_write(UC_ARM_REG_R0, SELF_ADDR)
    uc.reg_write(UC_ARM_REG_R1, MGR_ADDR)

    uc.emu_start(entry_addr, STUB_RET, count=1000000)

    out_self = bytes(uc.mem_read(SELF_ADDR, 0x20))
    return {
        "f14": out_self[0x14],
        "f15": out_self[0x15],
        "f16": out_self[0x16],
        "flags": struct.unpack_from("<I", out_self, 0x18)[0],
        "sel": struct.unpack_from("<i", out_self, 0x1C)[0],
        "events": events,
    }


def make_cases():
    cases = [
        {"cmd": 0, "a5f8_val": 42},
        {"cmd": 1, "a5d8_ret": 1},
        {"cmd": 2, "a5d8_ret": 1},
        {"cmd": 3, "a5d8_ret": 1},
        {"cmd": 15},
    ]
    for cmd in range(4, 13):
        cases.append({"cmd": cmd, "a5d8_ret": 1, "flags": 0})
        cases.append({"cmd": cmd, "a5d8_ret": 0, "flags": 0xFFFF})
    cases.extend([
        # cmd 13 early exit
        {"cmd": 13, "c17d4_ret": 0, "f14": 1, "units": {0: (0, {0: 1})}},
        # cmd 13 f14=1 + f16=1
        {
            "cmd": 13,
            "f14": 1,
            "f16": 1,
            "flags": 0x405,
            "units": {0: (0x00, {0: 2, 49: 0}), 1: (0x10, {0: 3})},
            "party": [-1, 0, 1, 2],
            "demons": {0, 2},
            "skip_demons": {2},
        },
        # cmd 13 f15=1
        {"cmd": 13, "f15": 1, "flags": 0x10, "units": {0: (0x00, {0: 1}), 2: (0x10, {1: 4})}},
        # cmd 13 single sel >= 0
        {"cmd": 13, "sel": 5, "flags": 0x20, "units": {5: (0x00, {3: 7})}},
        # cmd 13 single sel < 0
        {"cmd": 13, "sel": -1, "flags": 0x20, "units": {0: (0x00, {0: 1})}},
        # cmd 14 f14=1 + f16=1
        {
            "cmd": 14,
            "f14": 1,
            "f16": 1,
            "flags": 0x10405,
            "units": {0: (0x00, {0: 2}), 1: (0x10, {0: 3})},
            "party": [0, 1],
            "demons": {0},
        },
        # cmd 14 single sel >= 0
        {"cmd": 14, "sel": 5, "flags": 0x80, "units": {5: (0x00, {2: 6})}},
    ])
    return cases


def build_cand_from_source(src_text: str, tag: str = "cand"):
    tmp_dir = REPO_ROOT / "build" / "test_leaf_003c35f0_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    src_path = tmp_dir / f"{tag}.cpp"
    obj_path = tmp_dir / f"{tag}.o"
    src_path.write_text(src_text, encoding="utf-8")
    res = compile_tu_armv6k(src_path, obj_path)
    assert res.returncode == 0, f"Compile failed ({tag}):\n{res.stderr}"
    stub_map = {name: STUB_BASE + i * 8 for i, name in enumerate(CALLEES)}
    cand_bytes, cand_entry = patch_cand_elf(obj_path.read_bytes(), CAND_BASE, "battle_func_003c35f0", stub_map)
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
        assert r_orig == r_cand, f"Case {i} ({c}) mismatch:\n  orig={r_orig}\n  cand={r_cand}"

    mutations = [
        ("wrong_kFlagBits", "0x10u, 0x02u, 0x20u,", "0x04u, 0x02u, 0x20u,"),
        ("invert_f14_unit_check", "if (f14 != 0 && (unit_flags & 0x10u) != 0)", "if (f14 != 0 && (unit_flags & 0x10u) == 0)"),
        ("wrong_item_stride", "static_cast<u32>(slot) * 276u;", "static_cast<u32>(slot) * 272u;"),
        ("wrong_bit_limit", "for (u32 bit = 0; bit < 11u; ++bit)", "for (u32 bit = 0; bit < 10u; ++bit)"),
        ("skip_3194", "camp_func_00263194(demon, static_cast<u16>(flags));", "// skipped"),
    ]
    for name, old_s, new_s in mutations:
        assert old_s in src_text, f"Mutation target not found: {name}"
        m_bytes, m_entry, m_callees = build_cand_from_source(src_text.replace(old_s, new_s, 1), name)
        caught = any(
            run_one(orig_bytes, FUNC_ADDR, FUNC_ADDR, orig_callees, c)
            != run_one(m_bytes, CAND_BASE, m_entry, m_callees, c)
            for c in cases
        )
        assert caught, f"Mutation control not caught: {name}"
        print(f"NEG_CTRL PASS (caught): {name}")

    print(f"ALL PASS: {len(cases)} cases + {len(mutations)} negative controls")


if __name__ == "__main__":
    main()
