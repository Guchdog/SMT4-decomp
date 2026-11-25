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
    UC_ARM_REG_SP,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from build_check import compile_tu_armv6k  # noqa: E402

CODE_BIN = REPO_ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = REPO_ROOT / "src" / "engine" / "leaf_batch45_c.cpp"

FUNC_ADDR = 0x00357C48
FUNC_SIZE = 1500

CALLEES = {
    "engine_func_002c3aa8": (0x002C3AA8, 1),
    "engine_func_002c3a24": (0x002C3A24, 1),
    "engine_func_00263720": (0x00263720, 1),
    "func_00358b0c": (0x00358B0C, 1),
    "func_003e0c74": (0x003E0C74, 4),
    "ui_func_00238dd4": (0x00238DD4, 3),
    "func_003e0da8": (0x003E0DA8, 2),
    "func_002396f8": (0x002396F8, 1),
    "engine_func_002c586c": (0x002C586C, 1),
    "engine_func_002ad8f8": (0x002AD8F8, 2),
    "engine_func_003e07a4": (0x003E07A4, 3),
    "engine_func_0023963c": (0x0023963C, 3),
    "func_00239b54": (0x00239B54, 2),
    "engine_func_003e0cf0": (0x003E0CF0, 2),
    "engine_func_002c5ff4": (0x002C5FF4, 3),
    "func_003e0de8": (0x003E0DE8, 2),
    "func_00239564": (0x00239564, 4),
    "func_00239b84": (0x00239B84, 1),
    "ui_func_0023953c": (0x0023953C, 2),
    "ui_func_002adb40": (0x002ADB40, 2),
    "func_002392e0": (0x002392E0, 1),
}

STUB_RET = 0x00600000
STUB_BASE = 0x00600100
STUB_VTBL20 = 0x00600400
STUB_VTBL28 = 0x00600410
CAND_BASE = 0x00700000
STACK_TOP = 0x0080FFF0

SELF_ADDR = 0x00500000
VTBL_ADDR = 0x00501000
REQ_ADDR = 0x00502000
OUT_OBJ = 0x00503000
EXISTING_ADDR = 0x00504000
BUF_ADDR = 0x00510000
R353C_RET = 0x00505000


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
        uc.mem_write(STUB_VTBL20, bx_lr)
        uc.mem_write(STUB_VTBL28, bx_lr)
        if is_orig:
            uc.mem_write(FUNC_ADDR, orig_bytes)
            addr_to_info = {addr: (name, arity) for name, (addr, arity) in CALLEES.items()}
        else:
            uc.mem_write(CAND_BASE, cand_image)
            addr_to_info = {STUB_MAP[name]: (name, CALLEES[name][1]) for name in CALLEES}
        for addr in addr_to_info:
            uc.mem_write(addr, bx_lr)

        # Init self (0x900 bytes), vtable, req, existing
        uc.mem_write(SELF_ADDR, b"\x00" * 0x900)
        uc.mem_write(VTBL_ADDR + 0x20, struct.pack("<I", STUB_VTBL20))
        uc.mem_write(VTBL_ADDR + 0x28, struct.pack("<I", STUB_VTBL28))
        uc.mem_write(SELF_ADDR + 0x00, struct.pack("<I", VTBL_ADDR))
        uc.mem_write(SELF_ADDR + 0x04, struct.pack("<I", case.get("self_4", 0x10)))
        uc.mem_write(SELF_ADDR + 0x09, struct.pack("<BBB", case.get("b9", 1), case.get("bA", 0), case.get("bB", 0)))

        # Populate 0x1FC..0x21B and 0x3AC..0x3CB with distinct patterns
        uc.mem_write(SELF_ADDR + 0x1FC, bytes(range(1, 33)))
        uc.mem_write(SELF_ADDR + 0x3AC, bytes(range(101, 133)))

        for off, val in case.get("self_u32s", {}).items():
            uc.mem_write(SELF_ADDR + off, struct.pack("<I", val))

        uc.mem_write(REQ_ADDR, b"\x00" * 0x80)
        uc.mem_write(REQ_ADDR + 0x04, struct.pack("<I", case.get("req_sz", 0x80)))
        uc.mem_write(REQ_ADDR + 0x0C, struct.pack("<I", case.get("req_c", 1)))
        uc.mem_write(REQ_ADDR + 0x10, struct.pack("<I", case.get("req_10", 0x10)))
        uc.mem_write(REQ_ADDR + 0x6C, struct.pack("<BB", case.get("req_6c", 1), case.get("req_6d", 1)))

        uc.mem_write(EXISTING_ADDR + 0x04, struct.pack("<I", case.get("existing_4", 0x20)))

        calls = []
        rets = case.get("rets", {})

        def hook_code(uc_inst, address, size, user_data):
            if address == STUB_VTBL20:
                r0 = uc_inst.reg_read(UC_ARM_REG_R0)
                r1 = uc_inst.reg_read(UC_ARM_REG_R1)
                r2 = uc_inst.reg_read(UC_ARM_REG_R2)
                sp = uc_inst.reg_read(UC_ARM_REG_SP)
                s0, s1, s2, s3 = struct.unpack("<4I", uc_inst.mem_read(sp, 16))
                calls.append(("vtbl20", r0, r1, r2, s0, s1, s2, s3))
                uc_inst.reg_write(UC_ARM_REG_R0, rets.get("vtbl20", 0) & 0xFFFFFFFF)
                return
            if address == STUB_VTBL28:
                r0 = uc_inst.reg_read(UC_ARM_REG_R0)
                r1 = uc_inst.reg_read(UC_ARM_REG_R1)
                r3 = uc_inst.reg_read(UC_ARM_REG_R3)
                sp = uc_inst.reg_read(UC_ARM_REG_SP)
                s0 = struct.unpack("<I", uc_inst.mem_read(sp, 4))[0]
                calls.append(("vtbl28", r0, r1, r3, s0))
                uc_inst.reg_write(UC_ARM_REG_R0, rets.get("vtbl28", 0) & 0xFFFFFFFF)
                return
            info = addr_to_info.get(address)
            if info is None:
                return
            name, arity = info
            r0 = uc_inst.reg_read(UC_ARM_REG_R0)
            r1 = uc_inst.reg_read(UC_ARM_REG_R1)
            r2 = uc_inst.reg_read(UC_ARM_REG_R2)
            r3 = uc_inst.reg_read(UC_ARM_REG_R3)
            if name in ("engine_func_002c3aa8", "engine_func_002c3a24", "func_00239b54", "func_00239b84", "func_00358b0c", "func_00239564", "func_002392e0", "ui_func_002adb40"):
                calls.append((name,) + (r0, r1, r2, r3)[:arity])
            elif name == "engine_func_003e07a4":
                calls.append((name, r0, r1))

            if name == "func_00239b54":
                rv = 0 if case.get("oom", False) else BUF_ADDR
            elif name == "engine_func_0023963c":
                rv = EXISTING_ADDR
            elif name == "ui_func_0023953c":
                rv = R353C_RET
            else:
                rv = rets.get(name, 0)
            uc_inst.reg_write(UC_ARM_REG_R0, rv & 0xFFFFFFFF)

        uc.hook_add(1 << 2, hook_code)
        uc.reg_write(UC_ARM_REG_CPSR, 0x10)
        uc.reg_write(UC_ARM_REG_SP, STACK_TOP - 4)
        uc.mem_write(STACK_TOP - 4, struct.pack("<I", case.get("arg4", 0)))
        uc.reg_write(UC_ARM_REG_LR, STUB_RET)
        uc.reg_write(UC_ARM_REG_R0, SELF_ADDR)
        uc.reg_write(UC_ARM_REG_R1, REQ_ADDR)
        uc.reg_write(UC_ARM_REG_R2, case.get("mode", 0))
        uc.reg_write(UC_ARM_REG_R3, OUT_OBJ)

        entry = FUNC_ADDR if is_orig else cand_entry
        uc.emu_start(entry, STUB_RET, timeout=5_000_000, count=200_000)

        ret = uc.reg_read(UC_ARM_REG_R0)
        out_self = bytes(uc.mem_read(SELF_ADDR, 0x900))
        results.append((ret, out_self, calls))

    if results[0] != results[1]:
        return False, f"orig={results[0][0]:#x} cand={results[1][0]:#x} calls_diff={results[0][2] != results[1][2]}"
    return True, "ok"


CASES = [
    {"name": "init_358b0c_fail", "b9": 0, "rets": {"func_00358b0c": -0x1234}},
    {"name": "self_4_zero", "self_4": 0},
    {"name": "req_c_zero", "req_c": 0},
    {"name": "3e0c74_fail", "rets": {"func_003e0c74": -1}},
    {"name": "handle_mismatch", "self_4": 0x10, "req_10": 0x20},
    {"name": "req_6c_6d_invalid", "req_6c": 2, "req_6d": 2, "rets": {"func_002396f8": 1}},
    {"name": "mode0_lim_exceeded", "mode": 0, "req_sz": 0x100, "self_u32s": {0x218: 0x80}},
    {"name": "mode1_cap_exceeded_new", "mode": 1, "req_sz": 0x100, "self_u32s": {0x3B4: 0x120, 0x3B8: 0x50}, "rets": {"engine_func_003e07a4": -1}},
    {
        "name": "mode1_cap_exceeded_existing",
        "mode": 1,
        "req_sz": 0x100,
        "existing_4": 0x20,
        "self_u32s": {0x3B4: 0x120, 0x3B8: 0x50},
        "rets": {"engine_func_003e07a4": 2},
    },
    {"name": "mode0_count_exceeded", "mode": 0, "req_sz": 0x80, "self_u32s": {0x20C: 3, 0x210: 3}, "rets": {"engine_func_003e07a4": -1}},
    {"name": "oom_239b54", "oom": True, "rets": {"engine_func_003e07a4": -1}},
    {"name": "arg4_nonzero_239564_fail", "arg4": 1, "mode": 1, "rets": {"engine_func_003e07a4": -1, "func_00239564": -0x55}},
    {"name": "mode0_ok_copy_and_2396f8", "mode": 0, "req_sz": 0x80, "rets": {"func_002396f8": 1}},
    {"name": "mode1_new_vtbl28_ok", "mode": 1, "req_sz": 0x80, "self_u32s": {0x3B8: 0, 0x3BC: 5, 0x3C0: 1}, "rets": {"engine_func_003e07a4": -1}},
    {"name": "mode1_existing_vtbl20_fail", "mode": 1, "req_sz": 0x80, "bB": 1, "rets": {"engine_func_003e07a4": 1, "vtbl20": -1}},
    {"name": "mode1_existing_ok", "mode": 1, "req_sz": 0x80, "bB": 1, "existing_4": 0x20, "rets": {"engine_func_003e07a4": 1, "vtbl20": 0}},
]


def run_negative_controls(orig_bytes: bytes):
    mutants = [
        ("mut1_wrong_err_6c_6d", "return static_cast<s32>(0xE0E10BEEu);", "return static_cast<s32>(0xC8810BEFu);"),
        ("mut2_wrong_mode1_flag_off", "self[0x0B] = 1u;", "self[0x0B] = 0u;"),
        ("mut3_wrong_sp98_zero", "sp98 = 1u;", "sp98 = 0u;"),
        ("mut4_missing_vtbl28_call", "if (mode == 1u && sb == 0u) {", "if (false) {"),
        ("mut5_wrong_existing_sub", "sp9c = req_sz - e4;", "sp9c = req_sz;"),
    ]
    src_text = SRC_CPP.read_text(encoding="utf-8")
    tmp_dir = REPO_ROOT / "build" / "test_leaf_00357c48_mut"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    for mname, old, new in mutants:
        assert old in src_text, f"Mutant target missing: {old}"
        mut_src = tmp_dir / f"{mname}.cpp"
        mut_obj = tmp_dir / f"{mname}.o"
        mut_src.write_text(src_text.replace(old, new, 1), encoding="utf-8")
        res = compile_tu_armv6k(mut_src, mut_obj)
        if res.returncode != 0:
            raise RuntimeError(f"Mutant {mname} failed to compile: {res.stderr}")
        m_entry, m_img = patch_cand_elf(mut_obj.read_bytes(), CAND_BASE, "engine_func_00357c48", STUB_MAP)
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

    obj_out = REPO_ROOT / "build" / "test_leaf_00357c48.o"
    obj_out.parent.mkdir(parents=True, exist_ok=True)
    res = compile_tu_armv6k(SRC_CPP, obj_out)
    if res.returncode != 0:
        print("COMPILE FAIL:\n", res.stderr)
        sys.exit(1)

    cand_entry, cand_image = patch_cand_elf(obj_out.read_bytes(), CAND_BASE, "engine_func_00357c48", STUB_MAP)

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
