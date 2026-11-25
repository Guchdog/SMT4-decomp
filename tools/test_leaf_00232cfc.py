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

FUNC_ADDR = 0x00232CFC
FUNC_SIZE = 1624

CALLEES = {
    "script_vm_func_002b66ec": 0x002B66EC,
    "camp_func_002a89e4": 0x002A89E4,
    "camp_func_0029ee4c": 0x0029EE4C,
    "ui_func_00293c98": 0x00293C98,
    "func_00262664": 0x00262664,
    "func_00269e54": 0x00269E54,
    "script_vm_func_00295fac": 0x00295FAC,
    "script_vm_func_00262648": 0x00262648,
    "camp_func_00263194": 0x00263194,
    "script_vm_func_0031c494": 0x0031C494,
    "func_0032b3e8": 0x0032B3E8,
    "script_vm_func_002e3380": 0x002E3380,
}

STUB_RET = 0x00600000
STUB_BASE = 0x00600100
CAND_BASE = 0x00700000
STACK_TOP = 0x0080FFF0

SKILL_ADDR = 0x00500000
MC_ADDR = 0x00501000
DEMON_ADDR = 0x00502000
OUT_HP_ADDR = 0x00503000
OUT_MP_ADDR = 0x00503004


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

    skill = bytearray(0x80)
    struct.pack_into("<H", skill, 0x62, case.get("s62", 0))
    struct.pack_into("<H", skill, 0x64, case.get("hp_flat", 0))
    struct.pack_into("<H", skill, 0x66, case.get("mp_flat", 0))
    skill[0x68] = case.get("hp_pct", 0)
    skill[0x69] = case.get("mp_pct", 0)
    skill[0x6A] = case.get("kind", 0)
    skill[0x6E] = case.get("s6e", 0)
    uc.mem_write(SKILL_ADDR, bytes(skill))

    mc = bytearray(0x80)
    struct.pack_into("<h", mc, 0x1C, case.get("mc_max_hp", 200))
    struct.pack_into("<h", mc, 0x1E, case.get("mc_max_mp", 100))
    struct.pack_into("<h", mc, 0x2A, case.get("mc_hp", 50))
    struct.pack_into("<h", mc, 0x2C, case.get("mc_mp", 20))
    struct.pack_into("<H", mc, 0x72, case.get("mc_status", 0))
    uc.mem_write(MC_ADDR, bytes(mc))

    demon = bytearray(0x80)
    struct.pack_into("<h", demon, 0x0E, case.get("d_max_hp", 300))
    struct.pack_into("<h", demon, 0x10, case.get("d_max_mp", 120))
    struct.pack_into("<h", demon, 0x2A, case.get("d_hp", 40))
    struct.pack_into("<h", demon, 0x2C, case.get("d_mp", 10))
    struct.pack_into("<H", demon, 0x44, case.get("d_status", 0))
    uc.mem_write(DEMON_ADDR, bytes(demon))

    uc.mem_write(OUT_HP_ADDR, struct.pack("<i", -999))
    uc.mem_write(OUT_MP_ADDR, struct.pack("<i", -999))

    events = []
    addr_to_name = {v: k for k, v in callee_addrs.items()}

    def hook_code(uc_inst, address, size, user_data):
        name = addr_to_name.get(address)
        r0 = uc_inst.reg_read(UC_ARM_REG_R0)
        r1 = uc_inst.reg_read(UC_ARM_REG_R1)
        r2 = uc_inst.reg_read(UC_ARM_REG_R2)
        r3 = uc_inst.reg_read(UC_ARM_REG_R3)
        if name == "script_vm_func_002b66ec":
            uc_inst.reg_write(UC_ARM_REG_R0, MC_ADDR)
        elif name == "camp_func_002a89e4":
            uc_inst.reg_write(UC_ARM_REG_R0, 0 if case.get("null_demon") else DEMON_ADDR)
        elif name == "camp_func_0029ee4c":
            uc_inst.reg_write(UC_ARM_REG_R0, 1 if r1 in case.get("d_bits", set()) else 0)
        elif name == "ui_func_00293c98":
            uc_inst.reg_write(UC_ARM_REG_R0, case.get("ui_ctx", 0))
        elif name == "func_00262664":
            uc_inst.reg_write(UC_ARM_REG_R0, case.get("mc_max_hp_fn", 250))
        elif name == "func_00269e54":
            uc_inst.reg_write(UC_ARM_REG_R0, case.get("d_max_hp_fn", 350))
        elif name == "script_vm_func_00295fac":
            uc_inst.reg_write(UC_ARM_REG_R0, 1 if r0 in case.get("mc_bits", set()) else 0)
        elif name == "script_vm_func_00262648":
            events.append(("262648", r0))
        elif name == "camp_func_00263194":
            events.append(("263194", r0, r1))
        elif name == "script_vm_func_0031c494":
            events.append(("31c494", r0, r1, r2))
            uc_inst.reg_write(UC_ARM_REG_R0, case.get("c494_ret", 0))
        elif name == "func_0032b3e8":
            uc_inst.reg_write(UC_ARM_REG_R0, 1 if (r1 & 1) else 0)
        elif name == "script_vm_func_002e3380":
            events.append(("2e3380", r0, r1, r2, r3))
            uc_inst.reg_write(UC_ARM_REG_R0, r2)

    for stub_addr in callee_addrs.values():
        uc.hook_add(UC_HOOK_CODE, hook_code, begin=stub_addr, end=stub_addr)

    sp = STACK_TOP - 8
    uc.reg_write(UC_ARM_REG_SP, sp)
    uc.mem_write(sp, struct.pack("<I", OUT_MP_ADDR if case.get("use_out_mp", True) else 0))
    uc.reg_write(UC_ARM_REG_LR, STUB_RET)
    uc.reg_write(UC_ARM_REG_R0, case.get("unit_idx", -1) & 0xFFFFFFFF)
    uc.reg_write(UC_ARM_REG_R1, SKILL_ADDR)
    uc.reg_write(UC_ARM_REG_R2, case.get("dry_run", 0))
    uc.reg_write(UC_ARM_REG_R3, OUT_HP_ADDR if case.get("use_out_hp", True) else 0)

    uc.emu_start(entry_addr, STUB_RET, count=500000)

    ret = uc.reg_read(UC_ARM_REG_R0)
    mc_hp, mc_mp = struct.unpack_from("<2h", uc.mem_read(MC_ADDR + 0x2A, 4), 0)
    d_hp, d_mp = struct.unpack_from("<2h", uc.mem_read(DEMON_ADDR + 0x2A, 4), 0)
    out_hp = struct.unpack_from("<i", uc.mem_read(OUT_HP_ADDR, 4), 0)[0]
    out_mp = struct.unpack_from("<i", uc.mem_read(OUT_MP_ADDR, 4), 0)[0]
    return {
        "ret": ret,
        "mc_hp": mc_hp,
        "mc_mp": mc_mp,
        "d_hp": d_hp,
        "d_mp": d_mp,
        "out_hp": out_hp,
        "out_mp": out_mp,
        "events": events,
    }


def make_cases():
    return [
        {"s62": 1},
        {"unit_idx": 0, "null_demon": True},
        {"unit_idx": 0, "d_bits": {10}},
        {"unit_idx": 0, "d_bits": {2}},
        # Revive MC
        {"unit_idx": -1, "kind": 0x0E, "mc_bits": set()},
        {"unit_idx": -1, "kind": 0x0E, "mc_bits": {1}, "dry_run": 1, "hp_pct": 50},
        {"unit_idx": -1, "kind": 0x01, "mc_bits": {1, 3}, "dry_run": 1, "hp_flat": 99},
        {"unit_idx": -1, "kind": 0x0E, "mc_bits": {1}, "dry_run": 0, "mc_hp": 0, "hp_pct": 1, "mc_max_hp": 10},
        {"unit_idx": -1, "kind": 0x01, "mc_bits": {1, 3}, "dry_run": 0, "mc_hp": -5, "s6e": 2},
        # Revive Demon
        {"unit_idx": 0, "kind": 0x0E, "d_bits": set()},
        {"unit_idx": 0, "kind": 0x0E, "d_bits": {1}, "dry_run": 1, "hp_pct": 50, "ui_ctx": 1, "d_max_hp_fn": 400},
        {"unit_idx": 0, "kind": 0x01, "d_bits": {1, 3}, "dry_run": 1, "hp_flat": 50},
        {"unit_idx": 0, "kind": 0x0E, "d_bits": {1}, "dry_run": 0, "d_hp": 0, "hp_flat": 80, "s6e": 2},
        {"unit_idx": 0, "kind": 0x01, "d_bits": {1, 3}, "dry_run": 0, "d_hp": -2},
        # Normal heal MC
        {"unit_idx": -1, "mc_bits": {1}},
        {"unit_idx": -1, "kind": 0x4E, "mc_bits": {1}, "hp_flat": 10},
        {"unit_idx": -1, "hp_flat": 60, "mp_pct": 25, "mc_status": 1, "s6e": 2, "c494_ret": 1},
        {"unit_idx": -1, "hp_pct": 50, "mp_flat": 200, "dry_run": 1, "mc_hp": 180, "mc_mp": 90, "ui_ctx": 1},
        {"unit_idx": -1, "hp_flat": 30, "mp_flat": 30, "mc_bits": {3}, "dry_run": 0, "mc_hp": 50, "mc_mp": 20},
        # Normal heal Demon
        {"unit_idx": 0, "d_bits": {1}},
        {"unit_idx": 0, "hp_flat": 60, "mp_pct": 25, "d_status": 1, "s6e": 2},
        {"unit_idx": 0, "hp_pct": 50, "mp_flat": 200, "dry_run": 1, "d_hp": 290, "d_mp": 115, "ui_ctx": 1},
        {"unit_idx": 0, "hp_flat": 30, "mp_flat": 30, "d_bits": {3}, "dry_run": 0, "d_hp": 40, "d_mp": 10},
    ]


def build_cand_from_source(src_text: str, tag: str = "cand"):
    tmp_dir = REPO_ROOT / "build" / "test_leaf_00232cfc_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    src_path = tmp_dir / f"{tag}.cpp"
    obj_path = tmp_dir / f"{tag}.o"
    src_path.write_text(src_text, encoding="utf-8")
    res = compile_tu_armv6k(src_path, obj_path)
    assert res.returncode == 0, f"Compile failed ({tag}):\n{res.stderr}"
    stub_map = {name: STUB_BASE + i * 8 for i, name in enumerate(CALLEES)}
    cand_bytes, cand_entry = patch_cand_elf(obj_path.read_bytes(), CAND_BASE, "camp_func_00232cfc", stub_map)
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
        ("wrong_s62_ret", "if (*reinterpret_cast<const u16*>(skill + 0x62u) != 0u) {\n        return 1;", "if (*reinterpret_cast<const u16*>(skill + 0x62u) != 0u) {\n        return 0;"),
        ("wrong_pct_div", "/ 100;", "/ 99;"),
        ("skip_mc_status3_cap", "if (script_vm_func_00295fac(3) != 0 && hp_gain > 1) {\n                hp_gain = 1;\n            }", "// skipped"),
        ("wrong_kind_mask", "u8 kind = skill[0x6Au] & 0x7Fu;", "u8 kind = skill[0x6Au] & 0x3Fu;"),
        ("skip_2e3380", "res = script_vm_func_002e3380(unit_idx, skill, res, dry_run);", "// skipped"),
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
