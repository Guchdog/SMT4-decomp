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
    UC_ARM_REG_SP,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from build_check import compile_tu_armv6k  # noqa: E402

CODE_BIN = REPO_ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = REPO_ROOT / "src" / "engine" / "leaf_batch45_c.cpp"

FUNC_ADDR = 0x002283B4
FUNC_SIZE = 1512

CALLEES = {
    "ui_func_00293c98": (0x00293C98, 0),
    "battle_func_002ae3f0": (0x002AE3F0, 1),
    "ui_func_00282b94": (0x00282B94, 2),
    "camp_func_002475e4": (0x002475E4, 3),
    "ui_func_002462a0": (0x002462A0, 4),
    "func_0022ac9c": (0x0022AC9C, 2),
    "ui_func_0022abcc": (0x0022ABCC, 2),
    "engine_func_002c4b30": (0x002C4B30, 2),
    "func_00246554": (0x00246554, 1),
    "ui_func_0022aaac": (0x0022AAAC, 2),
    "ui_func_0022a824": (0x0022A824, 1),
    "camp_func_0023ebf0": (0x0023EBF0, 0),
    "script_vm_func_0023ec3c": (0x0023EC3C, 1),
}

STUB_RET = 0x00600000
STUB_BASE = 0x00600100
CAND_BASE = 0x00700000
STACK_TOP = 0x0080FFF0

CTX_ADDR = 0x00500000
SKILL_ADDR = 0x00506000
ACTOR_ADDR = 0x00507000
TARGET_ADDR = 0x00508000
EBF0_ADDR = 0x00509000
OUT_FLAG_ADDR = 0x0050A000


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

        uc.mem_write(CTX_ADDR, b"\x00" * 0x5000)
        uc.mem_write(CTX_ADDR + 0xE0, struct.pack("<I", case.get("ctx_e0", 0)))
        uc.mem_write(CTX_ADDR + 0x44A0, struct.pack("<I", case.get("ctx_44a0", 0)))
        uc.mem_write(CTX_ADDR + 0x44A8, struct.pack("<I", case.get("ctx_44a8", 0)))

        uc.mem_write(SKILL_ADDR, b"\x00" * 0x80)
        uc.mem_write(SKILL_ADDR + 0x23, struct.pack("<B", case.get("sk_23", 1)))
        uc.mem_write(SKILL_ADDR + 0x28, struct.pack("<I", case.get("sk_28", 0)))
        uc.mem_write(SKILL_ADDR + 0x2F, struct.pack("<B", case.get("sk_2f", 1)))
        uc.mem_write(SKILL_ADDR + 0x36, struct.pack("<H", case.get("sk_36", 0)))
        uc.mem_write(SKILL_ADDR + 0x38, struct.pack("<I", case.get("sk_38", 0)))
        uc.mem_write(SKILL_ADDR + 0x4A, struct.pack("<B", case.get("sk_4a", 0)))
        uc.mem_write(SKILL_ADDR + 0x56, struct.pack("<B", case.get("sk_56", 0)))

        uc.mem_write(ACTOR_ADDR, b"\x00" * 0x200)
        uc.mem_write(ACTOR_ADDR + 0x00, struct.pack("<I", case.get("act_0", 0x10)))
        uc.mem_write(ACTOR_ADDR + 0x1C2, struct.pack("<hh", case.get("act_1c2", 20), case.get("act_1c4", 20)))
        uc.mem_write(ACTOR_ADDR + 0x1C6, struct.pack("<H", case.get("act_1c6", 0)))

        uc.mem_write(TARGET_ADDR, b"\x00" * 0x200)
        uc.mem_write(TARGET_ADDR + 0x1C2, struct.pack("<hh", case.get("tgt_1c2", 10), case.get("tgt_1c4", 10)))
        uc.mem_write(TARGET_ADDR + 0x1C6, struct.pack("<H", case.get("tgt_1c6", 0)))

        uc.mem_write(EBF0_ADDR + 0x04, struct.pack("<f", case.get("ebf0_mul", 1.0)))
        uc.mem_write(OUT_FLAG_ADDR, b"\x00")

        calls = []
        rets = case.get("rets", {})
        call_idx = {}

        def hook_code(uc_inst, address, size, user_data):
            info = addr_to_info.get(address)
            if info is None:
                return
            name, arity = info
            idx = call_idx.get(name, 0)
            call_idx[name] = idx + 1
            r0 = uc_inst.reg_read(UC_ARM_REG_R0)
            r1 = uc_inst.reg_read(UC_ARM_REG_R1)
            r2 = uc_inst.reg_read(UC_ARM_REG_R2)
            r3 = uc_inst.reg_read(UC_ARM_REG_R3)
            if name in ("ui_func_002462a0", "ui_func_0022aaac", "script_vm_func_0023ec3c"):
                calls.append((name,) + (r0, r1, r2, r3)[:arity])

            if name == "ui_func_00293c98":
                uc_inst.reg_write(UC_ARM_REG_R0, CTX_ADDR)
            elif name == "battle_func_002ae3f0":
                uc_inst.reg_write(UC_ARM_REG_R0, SKILL_ADDR)
            elif name == "ui_func_00282b94":
                uc_inst.reg_write(UC_ARM_REG_R0, ACTOR_ADDR if r1 == case.get("actor_idx", 0) else TARGET_ADDR)
            elif name == "camp_func_002475e4":
                # sp9a=+2, sp9c=+4, sp9e=+6
                uc_inst.mem_write(r0 + 2, struct.pack("<Hhh", 0x33, case.get("s9c", 0), case.get("s9e", 100)))
            elif name == "func_0022ac9c":
                uc_inst.mem_write(r1, struct.pack("<I", 0x55))
            elif name == "camp_func_0023ebf0":
                uc_inst.reg_write(UC_ARM_REG_R0, EBF0_ADDR)
            elif name == "ui_func_0022a824":
                val = 1.0 if r0 == 11 else case.get("s0_9", 1.0)
                uc_inst.reg_write(UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", val))[0])
            elif name == "engine_func_002c4b30":
                uc_inst.mem_write(r0, b"\x00" * r1)
            elif name == "func_00246554":
                uc_inst.reg_write(UC_ARM_REG_R0, 100 + r0)
            else:
                rv = rets.get(name, 0)
                if isinstance(rv, list):
                    rv = rv[idx] if idx < len(rv) else rv[-1]
                uc_inst.reg_write(UC_ARM_REG_R0, rv & 0xFFFFFFFF)

        uc.hook_add(1 << 2, hook_code)
        uc.reg_write(UC_ARM_REG_CPSR, 0x10)
        sp = STACK_TOP - 16
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.mem_write(
            sp,
            struct.pack(
                "<4I",
                case.get("target_idx", 1) & 0xFFFFFFFF,
                case.get("flag5", 0) & 0xFFFFFFFF,
                case.get("flag6", 0) & 0xFFFFFFFF,
                OUT_FLAG_ADDR,
            ),
        )
        uc.reg_write(UC_ARM_REG_LR, STUB_RET)
        uc.reg_write(UC_ARM_REG_R0, case.get("skill_id", 10) & 0xFFFFFFFF)
        uc.reg_write(UC_ARM_REG_R1, 0)
        uc.reg_write(UC_ARM_REG_R2, case.get("action_type", 1))
        uc.reg_write(UC_ARM_REG_R3, case.get("actor_idx", 0) & 0xFFFFFFFF)

        entry = FUNC_ADDR if is_orig else cand_entry
        uc.emu_start(entry, STUB_RET, timeout=5_000_000, count=200_000)

        ret = uc.reg_read(UC_ARM_REG_R0)
        out_flag = uc.mem_read(OUT_FLAG_ADDR, 1)[0]
        out_48b8 = struct.unpack("<I", uc.mem_read(CTX_ADDR + 0x48B8, 4))[0]
        out_tgt0 = struct.unpack("<I", uc.mem_read(TARGET_ADDR, 4))[0]
        results.append((ret, out_flag, out_48b8, out_tgt0, calls))

    if results[0] != results[1]:
        return False, f"orig={results[0]} != cand={results[1]}"
    return True, "ok"


CASES = [
    {"name": "act_9_ret6", "action_type": 9},
    {"name": "act_11_ret11", "action_type": 11},
    {"name": "act_14_ret8", "action_type": 14},
    {"name": "skill_ffff_ret6", "skill_id": 0xFFFF},
    {"name": "flag5_sk23_7", "flag5": 1, "sk_23": 7},
    {"name": "flag5_bits_8", "flag5": 1, "sk_28": 8 << 5},
    {"name": "sk23_11_ret16", "sk_23": 11},
    {"name": "sk36_1000_ret9", "sk_36": 0x1000},
    {"name": "sk4a_ret7", "sk_4a": 1},
    {"name": "sk56_ret12", "sk_56": 1},
    {"name": "sk36_4000_ret14", "sk_36": 0x4000},
    {"name": "ctx44a8_100_ret1", "ctx_44a8": 0x100},
    {"name": "ctx44a8_80_r4_1", "ctx_44a8": 0x80, "sk_38": 0x10000},
    {"name": "s9c_3_ret0", "s9c": 3},
    {"name": "abcc_1_d0000_20000", "rets": {"ui_func_0022abcc": 1, "ui_func_002462a0": 0x260000}},
    {"name": "abcc_0_40000_ret2", "rets": {"ui_func_0022abcc": 0, "ui_func_002462a0": 0x40000}},
    {"name": "abcc_0_10000_ret3", "rets": {"ui_func_0022abcc": 0, "ui_func_002462a0": 0x10000}},
    {"name": "sk23_2_b2f_13_ok", "sk_23": 2, "sk_2f": 0x13},
    {"name": "sk23_2_b2f_16_blocked", "sk_23": 2, "sk_2f": 0x16, "rets": {"ui_func_0022aaac": [0, 0, 0x10000]}},
    {"name": "tgt_1c6_200_r4_1", "tgt_1c6": 0x200, "sk_38": 0x10000},
    {"name": "chance_100_roll_99_ok", "act_1c6": 0x10, "rets": {"script_vm_func_0023ec3c": 99}},
    {"name": "chance_15_roll_20_miss", "tgt_1c6": 0x10, "rets": {"script_vm_func_0023ec3c": 20}},
    {"name": "chance_normal_hit_r4_1", "sk_38": 0x10000, "act_0": 0, "ebf0_mul": 0.9, "rets": {"script_vm_func_0023ec3c": 50}},
]


def run_negative_controls(orig_bytes: bytes):
    mutants = [
        ("mut1_wrong_act11_ret", "return 0x0B;", "return 0x0A;"),
        ("mut2_wrong_bits_shift", "(*reinterpret_cast<const u32*>(skill + 0x28) >> 5) & 0x0Fu", "(*reinterpret_cast<const u32*>(skill + 0x28) >> 4) & 0x0Fu"),
        ("mut3_wrong_abcc_40000", "if ((r6_flags & 0x40000u) != 0u) {\n            return 2;", "if ((r6_flags & 0x40000u) != 0u) {\n            return 3;"),
        ("mut4_wrong_chance_15", "chance = 15.0f;", "chance = 50.0f;"),
        ("mut5_wrong_b2f_16_count", "cnt = 6;", "cnt = 2;"),
    ]
    src_text = SRC_CPP.read_text(encoding="utf-8")
    tmp_dir = REPO_ROOT / "build" / "test_leaf_002283b4_mut"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    for mname, old, new in mutants:
        assert old in src_text, f"Mutant target missing: {old}"
        mut_src = tmp_dir / f"{mname}.cpp"
        mut_obj = tmp_dir / f"{mname}.o"
        mut_src.write_text(src_text.replace(old, new, 1), encoding="utf-8")
        res = compile_tu_armv6k(mut_src, mut_obj)
        if res.returncode != 0:
            raise RuntimeError(f"Mutant {mname} failed to compile: {res.stderr}")
        m_entry, m_img = patch_cand_elf(mut_obj.read_bytes(), CAND_BASE, "ui_func_002283b4", STUB_MAP)
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

    obj_out = REPO_ROOT / "build" / "test_leaf_002283b4.o"
    obj_out.parent.mkdir(parents=True, exist_ok=True)
    res = compile_tu_armv6k(SRC_CPP, obj_out)
    if res.returncode != 0:
        print("COMPILE FAIL:\n", res.stderr)
        sys.exit(1)

    cand_entry, cand_image = patch_cand_elf(obj_out.read_bytes(), CAND_BASE, "ui_func_002283b4", STUB_MAP)

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
