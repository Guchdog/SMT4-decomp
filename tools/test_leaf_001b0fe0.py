import struct
import sys
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM
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

FUNC_ADDR = 0x001B0FE0
FUNC_SIZE = 1476

CALLEES = {
    "ui_func_002c0ac8": 0x002C0AC8,
    "script_vm_func_0029c660": 0x0029C660,
    "ui_func_002a0678": 0x002A0678,
    "script_vm_func_00289924": 0x00289924,
    "script_vm_func_002b8b78": 0x002B8B78,
    "script_vm_func_002971e4": 0x002971E4,
    "ui_func_0017f624": 0x0017F624,
    "Tbb_GetGlobalSubTable": 0x002C0EC4,
    "Tbb_GetPayloadData": 0x002C0E9C,
    "Tbb_GetRowCount": 0x002C0E4C,
    "camp_func_0029f10c": 0x0029F10C,
    "ui_func_002bffbc": 0x002BFFBC,
    "camp_func_002a8a1c": 0x002A8A1C,
    "camp_func_002a8a08": 0x002A8A08,
    "ui_func_002b902c": 0x002B902C,
    "script_vm_func_0019dfbc": 0x0019DFBC,
    "script_vm_func_00297674": 0x00297674,
    "script_vm_func_00291140": 0x00291140,
    "script_vm_func_001c35d8": 0x001C35D8,
    "script_vm_func_002899c4": 0x002899C4,
    "ui_func_0030aa1c": 0x0030AA1C,
    "ui_func_00282df8": 0x00282DF8,
    "engine_func_00215928": 0x00215928,
    "engine_func_00285f0c": 0x00285F0C,
    "ui_func_00282d98": 0x00282D98,
    "script_vm_func_00287990": 0x00287990,
    "battle_func_002c45b8": 0x002C45B8,
    "AsdSequence_func_002c59b8": 0x002C59B8,
}

STUB_RET = 0x00600000
STUB_BASE = 0x00600100
CAND_BASE = 0x00700000
STACK_TOP = 0x0080FFF0

SELF_ADDR = 0x00500000
ARR_ADDR = 0x00510000
TBB_SUB = 0x00520000
TBB_PAYLOAD = 0x00530000
G_43DE80 = 0x0043DE80
G_PTR1 = 0x00540000
G_PTR2 = 0x00540100


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

CALLEE_ARITY = {
    "ui_func_002c0ac8": 0,
    "script_vm_func_0029c660": 3,
    "ui_func_002a0678": 2,
    "script_vm_func_00289924": 0,
    "script_vm_func_002b8b78": 1,
    "script_vm_func_002971e4": 2,
    "ui_func_0017f624": 6,
    "Tbb_GetGlobalSubTable": 2,
    "Tbb_GetPayloadData": 1,
    "Tbb_GetRowCount": 1,
    "camp_func_0029f10c": 2,
    "ui_func_002bffbc": 1,
    "camp_func_002a8a1c": 0,
    "camp_func_002a8a08": 0,
    "ui_func_002b902c": 1,
    "script_vm_func_0019dfbc": 1,
    "script_vm_func_00297674": 0,
    "script_vm_func_00291140": 0,
    "script_vm_func_001c35d8": 1,
    "script_vm_func_002899c4": 3,
    "ui_func_0030aa1c": 1,
    "ui_func_00282df8": 0,
    "engine_func_00215928": 0,
    "engine_func_00285f0c": 0,
    "ui_func_00282d98": 0,
    "script_vm_func_00287990": 1,
    "battle_func_002c45b8": 2,
    "AsdSequence_func_002c59b8": 3,
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
        if is_orig:
            uc.mem_write(FUNC_ADDR, orig_bytes)
            addr_to_name = {addr: name for name, addr in CALLEES.items()}
            for addr in addr_to_name:
                uc.mem_write(addr, bx_lr)
        else:
            uc.mem_write(CAND_BASE, cand_image)
            addr_to_name = {STUB_MAP[name]: name for name in CALLEES}
            for addr in addr_to_name:
                uc.mem_write(addr, bx_lr)

        # Init self and globals
        uc.mem_write(SELF_ADDR, b"\x00" * 0xA0)
        uc.mem_write(SELF_ADDR + 0x08, struct.pack("<B", case.get("b8", 0)))
        uc.mem_write(SELF_ADDR + 0x0C, struct.pack("<I", case.get("state", 0)))
        for k, v in case.get("bytes", {}).items():
            uc.mem_write(SELF_ADDR + k, struct.pack("<B", v))
        uc.mem_write(SELF_ADDR + 0x18, struct.pack("<i", case.get("i18", 0)))
        uc.mem_write(SELF_ADDR + 0x1C, struct.pack("<I", case.get("sel", 0)))
        uc.mem_write(SELF_ADDR + 0x20, struct.pack("<i", case.get("cidx", 0)))
        uc.mem_write(SELF_ADDR + 0x84, struct.pack("<i", case.get("cnt", 0)))
        uc.mem_write(SELF_ADDR + 0x8C, struct.pack("<I", case.get("vm_handle", 0x1234)))

        uc.mem_write(ARR_ADDR + 0x90F0, bytes(case.get("arr", [10, 20, 30])))
        uc.mem_write(G_43DE80, struct.pack("<I", G_PTR1))
        uc.mem_write(G_PTR1, struct.pack("<I", G_PTR2))

        calls = []
        call_counts = {}
        rets = case.get("rets", {})

        def hook_code(uc_inst, address, size, user_data):
            name = addr_to_name.get(address)
            if name is None:
                return
            idx = call_counts.get(name, 0)
            call_counts[name] = idx + 1
            r0 = uc_inst.reg_read(UC_ARM_REG_R0)
            r1 = uc_inst.reg_read(UC_ARM_REG_R1)
            r2 = uc_inst.reg_read(UC_ARM_REG_R2)
            r3 = uc_inst.reg_read(UC_ARM_REG_R3)
            sp = uc_inst.reg_read(UC_ARM_REG_SP)
            sp0, sp1 = struct.unpack("<II", uc_inst.mem_read(sp, 8))

            if name == "ui_func_0017f624":
                # Optionally mutate *val if requested
                mut_val = case.get("mut_17f624")
                if mut_val is not None:
                    uc_inst.mem_write(r0, struct.pack("<i", mut_val))
            elif name == "ui_func_002c0ac8":
                uc_inst.reg_write(UC_ARM_REG_R0, SELF_ADDR)
                calls.append((name,))
                return
            elif name == "Tbb_GetGlobalSubTable":
                uc_inst.reg_write(UC_ARM_REG_R0, TBB_SUB)
                calls.append((name, r0, r1))
                return
            elif name == "Tbb_GetPayloadData":
                uc_inst.reg_write(UC_ARM_REG_R0, TBB_PAYLOAD)
                calls.append((name, r0))
                return
            elif name == "camp_func_002a8a08":
                uc_inst.reg_write(UC_ARM_REG_R0, ARR_ADDR)
                calls.append((name,))
                return

            all_args = (r0, r1, r2, r3, sp0, sp1)
            calls.append((name,) + all_args[: CALLEE_ARITY[name]])

            rv = rets.get(name, 0)
            if isinstance(rv, list):
                rv = rv[idx] if idx < len(rv) else rv[-1]
            uc_inst.reg_write(UC_ARM_REG_R0, rv & 0xFFFFFFFF)

        uc.hook_add(1 << 2, hook_code)
        uc.reg_write(UC_ARM_REG_CPSR, 0x10)
        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, STUB_RET)

        entry = FUNC_ADDR if is_orig else cand_entry
        uc.emu_start(entry, STUB_RET, timeout=5_000_000, count=100_000)

        ret_r0 = uc.reg_read(UC_ARM_REG_R0)
        out_self = bytes(uc.mem_read(SELF_ADDR, 0xA0))
        results.append((ret_r0, out_self, calls))

    if results[0] != results[1]:
        return False, f"orig={results[0]} != cand={results[1]}"
    return True, "ok"


CASES = [
    {"name": "state0", "state": 0},
    {"name": "state1", "state": 1},
    {"name": "state2_no_input", "state": 2, "rets": {"script_vm_func_00289924": 0}},
    {"name": "state2_triggered", "state": 2, "rets": {"script_vm_func_00289924": 1}},
    {
        "name": "state3_move_in_bounds",
        "state": 3,
        "sel": 2,
        "mut_17f624": 3,
        "rets": {"ui_func_0017f624": 1, "Tbb_GetRowCount": 5},
    },
    {
        "name": "state3_move_oob",
        "state": 3,
        "sel": 5,
        "mut_17f624": 6,
        "rets": {"ui_func_0017f624": 1, "Tbb_GetRowCount": 4},
    },
    {"name": "state3_sel7", "state": 3, "sel": 7, "rets": {"ui_func_002bffbc": 1}},
    {"name": "state3_sel8", "state": 3, "sel": 8, "rets": {"ui_func_002bffbc": 1}},
    {
        "name": "state3_sel6_enabled",
        "state": 3,
        "sel": 6,
        "bytes": {0x16: 1},
        "i18": 20,
        "arr": [10, 20, 30],
        "rets": {"ui_func_002bffbc": 1, "camp_func_002a8a1c": 3},
    },
    {
        "name": "state3_sel6_not_found",
        "state": 3,
        "sel": 6,
        "bytes": {0x16: 1},
        "i18": 99,
        "arr": [10, 20, 30],
        "rets": {"ui_func_002bffbc": 1, "camp_func_002a8a1c": 3},
    },
    {
        "name": "state3_toggle_byte",
        "state": 3,
        "sel": 4,
        "bytes": {0x14: 1},
        "rets": {"ui_func_002bffbc": 0, "ui_func_002b902c": [0, 1]},
    },
    {"name": "state4_noop", "state": 4},
    {"name": "state5_noop", "state": 5},
    {"name": "state6_r0", "state": 6, "rets": {"script_vm_func_0019dfbc": 2, "script_vm_func_00297674": 0}},
    {"name": "state6_r1", "state": 6, "rets": {"script_vm_func_0019dfbc": 2, "script_vm_func_00297674": 1}},
    {"name": "state7_cancel", "state": 7, "cnt": 3, "rets": {"ui_func_002bffbc": [1]}},
    {"name": "state7_confirm", "state": 7, "cnt": 3, "cidx": 1, "rets": {"ui_func_002bffbc": [0, 1]}},
    {
        "name": "state8_not_done",
        "state": 8,
        "rets": {"script_vm_func_0019dfbc": 1, "script_vm_func_00291140": 2, "Tbb_GetRowCount": 5},
    },
    {"name": "state8_r0", "state": 8, "rets": {"script_vm_func_0019dfbc": 2, "script_vm_func_00297674": 0}},
    {"name": "state8_r1", "state": 8, "rets": {"script_vm_func_0019dfbc": 2, "script_vm_func_00297674": 1}},
    {"name": "state9_busy", "state": 9, "rets": {"ui_func_00282df8": 1}},
    {"name": "state9_exit_215928", "state": 9, "rets": {"ui_func_00282df8": 0, "engine_func_00215928": 1}},
    {"name": "state9_proceed", "state": 9, "rets": {"ui_func_00282df8": 0, "engine_func_00215928": 0}},
    {"name": "state10_r0", "state": 10, "rets": {"script_vm_func_0019dfbc": 2, "script_vm_func_00297674": 0}},
    {"name": "state10_r1", "state": 10, "rets": {"script_vm_func_0019dfbc": 2, "script_vm_func_00297674": 1}},
    {"name": "state11_busy", "state": 11, "rets": {"ui_func_00282d98": 1}},
    {"name": "state11_b8_set", "state": 11, "b8": 1, "rets": {"ui_func_00282d98": 0}},
    {"name": "state11_b8_clear", "state": 11, "b8": 0, "rets": {"ui_func_00282d98": 0}},
    {"name": "state12_oob", "state": 12},
]


def run_negative_controls(orig_bytes: bytes):
    mutants = [
        ("mut1_wrong_stride_80", "payload + idx * 82u", "payload + idx * 80u"),
        ("mut2_wrong_case11_ret", "return -1;", "return 0;"),
        ("mut3_wrong_toggle_bound", "if (sel <= 6u)", "if (sel < 4u)"),
        ("mut4_missing_case8_556", "script_vm_func_002899c4(0x556u, 1u, 1u);", ""),
        ("mut5_wrong_case10_r1_next", "*reinterpret_cast<u32*>(self + 0x0C) = 2u;", "*reinterpret_cast<u32*>(self + 0x0C) = 3u;"),
    ]
    src_text = SRC_CPP.read_text(encoding="utf-8")
    tmp_dir = REPO_ROOT / "build" / "test_leaf_001b0fe0_mut"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    for mname, old, new in mutants:
        assert old in src_text, f"Mutant target missing: {old}"
        mut_src = tmp_dir / f"{mname}.cpp"
        mut_obj = tmp_dir / f"{mname}.o"
        # Replace in engine_func_001b0fe0 region (last occurrence for shared strings)
        if mname in ("mut2_wrong_case11_ret", "mut5_wrong_case10_r1_next"):
            pos = src_text.rfind(old)
            mut_text = src_text[:pos] + new + src_text[pos + len(old) :]
        else:
            mut_text = src_text.replace(old, new, 1)
        mut_src.write_text(mut_text, encoding="utf-8")
        res = compile_tu_armv6k(mut_src, mut_obj)
        if res.returncode != 0:
            raise RuntimeError(f"Mutant {mname} failed to compile: {res.stderr}")
        m_entry, m_img = patch_cand_elf(mut_obj.read_bytes(), CAND_BASE, "engine_func_001b0fe0", STUB_MAP)
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

    obj_out = REPO_ROOT / "build" / "test_leaf_001b0fe0.o"
    obj_out.parent.mkdir(parents=True, exist_ok=True)
    res = compile_tu_armv6k(SRC_CPP, obj_out)
    if res.returncode != 0:
        print("COMPILE FAIL:\n", res.stderr)
        sys.exit(1)

    cand_entry, cand_image = patch_cand_elf(obj_out.read_bytes(), CAND_BASE, "engine_func_001b0fe0", STUB_MAP)

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
