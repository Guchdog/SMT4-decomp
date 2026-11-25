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
    UC_ARM_REG_SP,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from build_check import compile_tu_armv6k  # noqa: E402

CODE_BIN = REPO_ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = REPO_ROOT / "src" / "engine" / "leaf_batch45_c.cpp"

FUNC_ADDR = 0x003D2AFC
FUNC_SIZE = 1488

CALLEES = {
    "battle_func_003d33a8": (0x003D33A8, 2),
    "battle_func_003ca184": (0x003CA184, 2),
    "engine_func_003358e0": (0x003358E0, 1),
    "battle_func_002bf41c": (0x002BF41C, 1),
    "engine_func_002c4b30": (0x002C4B30, 2),
    "script_vm_func_00229ca4": (0x00229CA4, 2),
    "battle_func_003cfd8c": (0x003CFD8C, 2),
    "script_vm_func_0024c828": (0x0024C828, 2),
    "battle_func_003d30cc": (0x003D30CC, 2),
    "ui_func_003cc16c": (0x003CC16C, 2),
    "battle_func_003cb098": (0x003CB098, 2),
    "engine_func_0027e92c": (0x0027E92C, 2),
    "func_003ae9dc": (0x003AE9DC, 1),
    "engine_func_003cadc8": (0x003CADC8, 2),
    "engine_func_003d1e48": (0x003D1E48, 2),
    "battle_func_003d1968": (0x003D1968, 2),
    "engine_func_0027e5c0": (0x0027E5C0, 1),
    "func_003aed14": (0x003AED14, 1),
    "battle_func_003cf454": (0x003CF454, 2),
    "battle_func_003cbf10": (0x003CBF10, 2),
    "script_vm_func_0027e628": (0x0027E628, 1),
    "battle_func_002ae3f0": (0x002AE3F0, 1),
    "func_00229c68": (0x00229C68, 1),
    "func_003cb470": (0x003CB470, 2),
    "battle_func_003cb610": (0x003CB610, 2),
    "func_003cbda4": (0x003CBDA4, 2),
    "engine_func_003dd1f4": (0x003DD1F4, 1),
    "ui_func_003dce20": (0x003DCE20, 1),
    "battle_func_003dc6dc": (0x003DC6DC, 1),
    "script_vm_func_00229a34": (0x00229A34, 0),
    "script_vm_func_002298e8": (0x002298E8, 2),
}

STUB_RET = 0x00600000
STUB_BASE = 0x00600100
CAND_BASE = 0x00700000
STACK_TOP = 0x0080FFF0

CTX_ADDR = 0x00500000
UNIT_ADDR = 0x00501000  # size >= 0x5000
BASE_ARRAY = 0x00510000
P28_ADDR = 0x00520000
P20_ADDR = 0x00521000
SKILL_ADDR = 0x00522000

G_434260 = 0x00434260
G_43427C = 0x0043427C
G_434290 = 0x00434290
G_439CA8 = 0x00439CA8
G_435D48 = 0x00435D48
G_435D18 = 0x00435D18


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


STUB_MAP = {name: STUB_BASE + idx * 0x10 for idx, name in enumerate(CALLEES)}


def run_case(orig_bytes: bytes, cand_entry: int, cand_image: bytes, case: dict):
    results = []
    entry_idx = case.get("idx", 1)
    entry_off = entry_idx * 0xF1C + 4
    entry_addr = BASE_ARRAY + entry_off

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
        if is_orig:
            uc.mem_write(FUNC_ADDR, orig_bytes)
            addr_to_info = {addr: (name, arity) for name, (addr, arity) in CALLEES.items()}
        else:
            uc.mem_write(CAND_BASE, cand_image)
            addr_to_info = {STUB_MAP[name]: (name, CALLEES[name][1]) for name in CALLEES}
        for addr in addr_to_info:
            uc.mem_write(addr, bx_lr)

        # Globals & memory
        uc.mem_write(G_434260, struct.pack("<I", 0x1111))
        uc.mem_write(G_43427C, struct.pack("<I", BASE_ARRAY))
        uc.mem_write(G_434290, struct.pack("<I", 0x2222))
        uc.mem_write(G_439CA8, struct.pack("<I", 0x3333))
        uc.mem_write(G_435D48, struct.pack("<I", 0x4444))
        uc.mem_write(G_435D18, struct.pack("<I", 0x5555))

        uc.mem_write(CTX_ADDR, struct.pack("<I", UNIT_ADDR))
        uc.mem_write(UNIT_ADDR, b"\x00" * 0x5000)
        uc.mem_write(UNIT_ADDR + 0x20, struct.pack("<I", case.get("u20", 0)))
        uc.mem_write(UNIT_ADDR + 0x5C, struct.pack("<I", case.get("u5c", 0)))
        uc.mem_write(UNIT_ADDR + 0x7C, struct.pack("<I", case.get("u7c", 0)))
        uc.mem_write(UNIT_ADDR + 0x84, struct.pack("<I", entry_idx))
        uc.mem_write(UNIT_ADDR + 0x225C, struct.pack("<I", case.get("u225c", 0)))
        uc.mem_write(UNIT_ADDR + 0x44A0, struct.pack("<I", case.get("u44a0", 0)))
        uc.mem_write(UNIT_ADDR + 0x44A8, struct.pack("<I", case.get("u44a8", 0)))
        uc.mem_write(UNIT_ADDR + 0x496C, struct.pack("<HH", case.get("u496c", 0), case.get("u496e", 0)))
        uc.mem_write(UNIT_ADDR + 0x49C8, struct.pack("<I", case.get("u49c8", 0)))

        uc.mem_write(entry_addr, b"\x00" * 0xF20)
        uc.mem_write(entry_addr + 0x00, struct.pack("<I", case.get("e0", 0)))
        uc.mem_write(entry_addr + 0x08, struct.pack("<I", case.get("e8", 0)))
        uc.mem_write(entry_addr + 0x20, struct.pack("<I", P20_ADDR))
        uc.mem_write(entry_addr + 0x28, struct.pack("<I", P28_ADDR))
        uc.mem_write(entry_addr + 0xF18, struct.pack("<I", 0x99))

        uc.mem_write(P28_ADDR + 0x14C, struct.pack("<Hh", case.get("p28_type", 0), case.get("p28_id", 0)))
        uc.mem_write(P20_ADDR + 0xC0, struct.pack("<I", 0x77))
        uc.mem_write(SKILL_ADDR + 0x4B, struct.pack("<B", case.get("skill_4b", 0)))

        calls = []
        rets = case.get("rets", {})

        def hook_code(uc_inst, address, size, user_data):
            info = addr_to_info.get(address)
            if info is None:
                return
            name, arity = info
            r0 = uc_inst.reg_read(UC_ARM_REG_R0)
            r1 = uc_inst.reg_read(UC_ARM_REG_R1)
            calls.append((name,) + (r0, r1)[:arity])
            if name == "battle_func_002ae3f0":
                rv = SKILL_ADDR if case.get("skill_valid", True) else 0
            else:
                rv = rets.get(name, 0)
            uc_inst.reg_write(UC_ARM_REG_R0, rv & 0xFFFFFFFF)

        uc.hook_add(1 << 2, hook_code)
        uc.reg_write(UC_ARM_REG_CPSR, 0x10)
        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, STUB_RET)
        uc.reg_write(UC_ARM_REG_R0, CTX_ADDR)
        uc.reg_write(UC_ARM_REG_R1, case["cmd"])

        entry_pc = FUNC_ADDR if is_orig else cand_entry
        uc.emu_start(entry_pc, STUB_RET, timeout=5_000_000, count=100_000)

        ret = uc.reg_read(UC_ARM_REG_R0)
        out_entry_5 = uc.mem_read(entry_addr + 5, 1)[0]
        out_entry_8 = struct.unpack("<I", uc.mem_read(entry_addr + 8, 4))[0]
        out_entry_f18 = struct.unpack("<I", uc.mem_read(entry_addr + 0xF18, 4))[0]
        out_p28 = bytes(uc.mem_read(P28_ADDR + 0x14C, 4))
        out_p20_c0 = struct.unpack("<I", uc.mem_read(P20_ADDR + 0xC0, 4))[0]
        results.append((ret, out_entry_5, out_entry_8, out_entry_f18, out_p28, out_p20_c0, calls))

    if results[0] != results[1]:
        return False, f"orig={results[0]} != cand={results[1]}"
    return True, "ok"


CASES = [
    {"name": "cmd0_tail", "cmd": 0, "rets": {"battle_func_003d33a8": 0x100}},
    {"name": "cmd1_tail", "cmd": 1, "rets": {"battle_func_003ca184": 0x101}},
    {"name": "cmd2_clear_and_call", "cmd": 2, "u44a0": 4, "rets": {"engine_func_003358e0": 1, "battle_func_002bf41c": 0}},
    {"name": "cmd2_fail_3358e0", "cmd": 2, "rets": {"engine_func_003358e0": 0}},
    {"name": "cmd3_ok", "cmd": 3, "u49c8": 0x55, "rets": {"battle_func_002bf41c": 0}},
    {"name": "cmd4_tail", "cmd": 4, "rets": {"battle_func_003d30cc": 0x104}},
    {"name": "cmd5_tail", "cmd": 5, "rets": {"ui_func_003cc16c": 0x105}},
    {"name": "cmd6_noop", "cmd": 6},
    {"name": "cmd7_tail", "cmd": 7, "rets": {"battle_func_003cb098": 0x107}},
    {"name": "cmd8_set9", "cmd": 8},
    {"name": "cmd9_ok", "cmd": 9, "rets": {"engine_func_0027e92c": 0}},
    {"name": "cmd10_even", "cmd": 10, "u7c": 2},
    {"name": "cmd10_odd", "cmd": 10, "u7c": 1},
    {"name": "cmd14_set1b", "cmd": 14},
    {"name": "cmd15_ok", "cmd": 15, "rets": {"battle_func_002bf41c": 0, "engine_func_0027e5c0": 1}},
    {"name": "cmd16_v3", "cmd": 16, "u225c": 3, "rets": {"func_003aed14": 1}},
    {"name": "cmd16_v1", "cmd": 16, "u225c": 1, "rets": {"func_003aed14": 1}},
    {"name": "cmd22_set1b", "cmd": 22},
    {"name": "cmd24_set0c", "cmd": 24, "p28_type": 3, "p28_id": 10, "skill_4b": 1, "u44a8": 0},
    {"name": "cmd24_fallback", "cmd": 24, "p28_type": 3, "p28_id": 10, "skill_4b": 1, "u44a8": 0x800},
    {"name": "cmd29_tail", "cmd": 29, "rets": {"battle_func_003cb610": 0x11D}},
    {"name": "cmd31_s0", "cmd": 31, "e8": 0, "rets": {"ui_func_003dce20": 1}},
    {"name": "cmd31_s1", "cmd": 31, "e8": 1, "rets": {"engine_func_003dd1f4": 1}},
    {"name": "cmd32_ok", "cmd": 32, "e0": 0, "rets": {"engine_func_0027e92c": 0, "script_vm_func_00229a34": 0}},
    {"name": "cmd33_ok", "cmd": 33, "rets": {"script_vm_func_0027e628": 0}},
    {"name": "cmd34_set23", "cmd": 34},
    {"name": "cmd35_reset7", "cmd": 35, "p28_type": 7, "p28_id": 12},
    {"name": "cmd36_oob", "cmd": 36},
]


def run_negative_controls(orig_bytes: bytes):
    mutants = [
        ("mut1_wrong_stride", "idx * 0xF1Cu + 4u", "idx * 0xF10u + 4u"),
        ("mut2_wrong_cmd16_else", "(v == 3u) ? 0x0Bu : 0x1Bu;", "(v == 3u) ? 0x0Bu : 0x10u;"),
        ("mut3_wrong_cmd24_mask", "& 0x800u", "& 0x400u"),
        ("mut4_wrong_cmd35_type", "== 7u", "== 6u"),
        ("mut5_missing_cmd31_inc", "*reinterpret_cast<u32*>(entry + 8) = st + 1u;", ""),
    ]
    src_text = SRC_CPP.read_text(encoding="utf-8")
    tmp_dir = REPO_ROOT / "build" / "test_leaf_003d2afc_mut"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    for mname, old, new in mutants:
        assert old in src_text, f"Mutant target missing: {old}"
        mut_src = tmp_dir / f"{mname}.cpp"
        mut_obj = tmp_dir / f"{mname}.o"
        pos = src_text.rfind(old) if mname == "mut4_wrong_cmd35_type" else src_text.find(old)
        mut_text = src_text[:pos] + new + src_text[pos + len(old) :]
        mut_src.write_text(mut_text, encoding="utf-8")
        res = compile_tu_armv6k(mut_src, mut_obj)
        if res.returncode != 0:
            raise RuntimeError(f"Mutant {mname} failed to compile: {res.stderr}")
        m_entry, m_img = patch_cand_elf(mut_obj.read_bytes(), CAND_BASE, "battle_func_003d2afc", STUB_MAP)
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

    obj_out = REPO_ROOT / "build" / "test_leaf_003d2afc.o"
    obj_out.parent.mkdir(parents=True, exist_ok=True)
    res = compile_tu_armv6k(SRC_CPP, obj_out)
    if res.returncode != 0:
        print("COMPILE FAIL:\n", res.stderr)
        sys.exit(1)

    cand_entry, cand_image = patch_cand_elf(obj_out.read_bytes(), CAND_BASE, "battle_func_003d2afc", STUB_MAP)

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
