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

FUNC_ADDR = 0x0033445C
FUNC_SIZE = 1552

CALLEES = {
    "ui_func_002fe358": (0x002FE358, 5, False),
    "engine_func_0027e964": (0x0027E964, 2, False),
    "battle_func_002b087c": (0x002B087C, 1, False),
    "engine_func_00288424": (0x00288424, 0, False),
    "engine_func_00240650": (0x00240650, 2, False),
    "ui_func_0027dd20": (0x0027DD20, 2, False),
    "ui_func_002bcf58": (0x002BCF58, 3, False),
    "func_003381cc": (0x003381CC, 2, False),
    "func_002b7f0a": (0x002B7F0A, 4, True),
    "func_002409dc": (0x002409DC, 2, False),
}

STUB_RET = 0x00600000
STUB_BASE = 0x00600100
CAND_BASE = 0x00700000
STACK_TOP = 0x0080FFF0

ARG_ADDR = 0x00500000
CTX_ADDR = 0x00501000
R4_ARR = 0x00510000
R5_ARR = 0x00520000
B087C_ADDR = 0x00505000
G_439CF8 = 0x00439CF8


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
        if is_orig:
            uc.mem_write(FUNC_ADDR, orig_bytes)
            addr_to_info = {addr: (name, arity, is_thumb) for name, (addr, arity, is_thumb) in CALLEES.items()}
        else:
            uc.mem_write(CAND_BASE, cand_image)
            addr_to_info = {STUB_MAP[name]: (name, CALLEES[name][1], False) for name in CALLEES}
        for addr, (_, _, is_thumb) in addr_to_info.items():
            uc.mem_write(addr, thumb_bx_lr if is_thumb else bx_lr)

        uc.mem_write(G_439CF8, struct.pack("<I", 0x4080C0FF))
        uc.mem_write(ARG_ADDR, struct.pack("<3I", 0, 0, 0x77))
        uc.mem_write(B087C_ADDR + 0x9E, struct.pack("<B", case.get("b9e", 0)))

        uc.mem_write(CTX_ADDR, b"\x00" * 0x2000)
        uc.mem_write(CTX_ADDR + 0x1E88, struct.pack("<I", 0x33))
        uc.mem_write(CTX_ADDR + 0x1E98, struct.pack("<I", R4_ARR))
        uc.mem_write(CTX_ADDR + 0x1FC0, struct.pack("<I", R5_ARR))

        # Populate ctx + 0x3F4 (n entries of 32 bytes)
        for i in range(4):
            base = CTX_ADDR + 0x3F4 + i * 32
            uc.mem_write(
                base,
                struct.pack("<fHIIfffI", 10.0 + i, 0x10 + i, 0x20406080, 0x1111 + i, 5.0 - i, 2.0, 1.0, 20 - i),
            )

        # Populate R4_ARR (54 entries of 276 bytes)
        uc.mem_write(R4_ARR, b"\x00" * (54 * 276))
        for i in range(54):
            e = R4_ARR + i * 276
            uc.mem_write(e + 0x60, struct.pack("<h", -1))
            uc.mem_write(e + 0x62, struct.pack("<h", i))
        for i, cfg in case.get("r4_cfg", {}).items():
            e = R4_ARR + i * 276
            uc.mem_write(e + 0x50, struct.pack("<I", cfg.get("p50", 0)))
            uc.mem_write(e + 0x60, struct.pack("<h", cfg.get("e60", -1)))
            uc.mem_write(e + 0xFC, struct.pack("<I", cfg.get("fc", 0)))
            uc.mem_write(e + 0x0C, struct.pack("<f", cfg.get("d0c", 1.0)))

        # Populate R5_ARR (4 entries of 648 bytes)
        uc.mem_write(R5_ARR, b"\x00" * (4 * 648))
        for i in range(4):
            p = R5_ARR + i * 648
            uc.mem_write(p + 0x00, struct.pack("<I", 0x100 if i == 1 else 0))
            uc.mem_write(p + 0x08, struct.pack("<50h", *([-1] * 50)))
            uc.mem_write(p + 0x6E, struct.pack("<h", case.get("r7_out", 1)))
            uc.mem_write(p + 0xCE, struct.pack("<H", 0x55))
        for pidx, slots in case.get("p5_slots", {}).items():
            p = R5_ARR + pidx * 648
            for s_i, val in enumerate(slots):
                uc.mem_write(p + 8 + s_i * 2, struct.pack("<h", val))

        calls = []

        def hook_code(uc_inst, address, size, user_data):
            info = addr_to_info.get(address)
            if info is None:
                return
            name, arity, _ = info
            r0 = uc_inst.reg_read(UC_ARM_REG_R0)
            r1 = uc_inst.reg_read(UC_ARM_REG_R1)
            r2 = uc_inst.reg_read(UC_ARM_REG_R2)
            r3 = uc_inst.reg_read(UC_ARM_REG_R3)
            sp = uc_inst.reg_read(UC_ARM_REG_SP)

            if name == "ui_func_002fe358":
                s0 = struct.unpack("<I", uc_inst.mem_read(sp, 4))[0]
                calls.append((name, r0, r1, r2, r3, s0))
                uc_inst.reg_write(UC_ARM_REG_R0, case.get("n", 2))
            elif name == "engine_func_0027e964":
                calls.append((name, r0, r1))
                uc_inst.reg_write(UC_ARM_REG_R0, 1)
            elif name == "battle_func_002b087c":
                calls.append((name, r0))
                uc_inst.reg_write(UC_ARM_REG_R0, B087C_ADDR)
            elif name == "engine_func_00288424":
                calls.append((name, uc_inst.reg_read(UC_ARM_REG_S0)))
            elif name == "ui_func_0027dd20":
                uc_inst.reg_write(UC_ARM_REG_R0, (r1 - R4_ARR) // 276)
            elif name == "ui_func_002bcf58":
                data = bytes(uc_inst.mem_read(r1, r2))
                uc_inst.mem_write(r0, data)
            elif name == "func_002b7f0a":
                # Sort u32 array by *ptr + 0x0C descending? Keep deterministic reverse-order for test
                cnt = r1
                ptrs = list(struct.unpack(f"<{cnt}I", uc_inst.mem_read(r0, cnt * 4)))
                ptrs.reverse()
                uc_inst.mem_write(r0, struct.pack(f"<{cnt}I", *ptrs))
                calls.append((name, cnt, r2, r3))
            elif name == "func_002409dc":
                calls.append((name, r0, r1))
                uc_inst.reg_write(UC_ARM_REG_R0, 0x999)
            else:
                calls.append((name,) + (r0, r1, r2, r3)[:arity])

        uc.hook_add(1 << 2, hook_code)
        uc.reg_write(UC_ARM_REG_CPSR, 0x10)
        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, STUB_RET)
        uc.reg_write(UC_ARM_REG_R0, ARG_ADDR)
        uc.reg_write(UC_ARM_REG_R1, CTX_ADDR)

        entry = FUNC_ADDR if is_orig else cand_entry
        uc.emu_start(entry, STUB_RET, timeout=5_000_000, count=300_000)

        ret = uc.reg_read(UC_ARM_REG_R0)
        out_arg = bytes(uc.mem_read(ARG_ADDR, 12))
        out_r4 = bytes(uc.mem_read(R4_ARR, 12 * 276))
        out_r5 = bytes(uc.mem_read(R5_ARR, 2 * 648))
        out_ctx = bytes(uc.mem_read(CTX_ADDR + 0xA34, 64))
        results.append((ret, out_arg, out_r4, out_r5, out_ctx, calls))

    if results[0] != results[1]:
        return False, f"orig=({results[0][0]}, {results[0][5]}) != cand=({results[1][0]}, {results[1][5]})"
    return True, "ok"


CASES = [
    {"name": "n0_r7_neg1", "n": 0, "r7_out": -1, "b9e": 1},
    {"name": "b9e_0_fill_and_swap", "n": 2, "b9e": 0, "r4_cfg": {4: {"p50": 0x81, "e60": -1}, 5: {"e60": 1}}},
    {
        "name": "b9e_2_swap_head",
        "n": 2,
        "b9e": 2,
        "p5_slots": {1: [7, 8, -1]},
        "r4_cfg": {7: {"p50": 0x81, "fc": 19, "d0c": 9.0}, 8: {"p50": 0x81, "fc": 19, "d0c": 2.0}},
    },
]


def run_negative_controls(orig_bytes: bytes):
    mutants = [
        ("mut1_wrong_b9e_2_val", "s16 = -20.0f;", "s16 = 20.0f;"),
        ("mut2_wrong_p50_flag", "*reinterpret_cast<u32*>(e + 0x50u) = 0x491u;", "*reinterpret_cast<u32*>(e + 0x50u) = 0x490u;"),
        ("mut3_wrong_slot_start", "for (s32 slot_idx = 4; slot_idx < 0x36; ++slot_idx)", "for (s32 slot_idx = 5; slot_idx < 0x36; ++slot_idx)"),
        ("mut4_missing_swap_preserve_h8", "*reinterpret_cast<u16*>(r8_p + 0x62u) = h8;", ""),
        ("mut5_wrong_arg_ret7", "*reinterpret_cast<u32*>(r0_arg) = 7u;", "*reinterpret_cast<u32*>(r0_arg) = 6u;"),
    ]
    src_text = SRC_CPP.read_text(encoding="utf-8")
    tmp_dir = REPO_ROOT / "build" / "test_leaf_0033445c_mut"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    for mname, old, new in mutants:
        assert old in src_text, f"Mutant target missing: {old}"
        mut_src = tmp_dir / f"{mname}.cpp"
        mut_obj = tmp_dir / f"{mname}.o"
        mut_src.write_text(src_text.replace(old, new, 1), encoding="utf-8")
        res = compile_tu_armv6k(mut_src, mut_obj)
        if res.returncode != 0:
            raise RuntimeError(f"Mutant {mname} failed to compile: {res.stderr}")
        m_entry, m_img = patch_cand_elf(mut_obj.read_bytes(), CAND_BASE, "ui_func_0033445c", STUB_MAP)
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

    obj_out = REPO_ROOT / "build" / "test_leaf_0033445c.o"
    obj_out.parent.mkdir(parents=True, exist_ok=True)
    res = compile_tu_armv6k(SRC_CPP, obj_out)
    if res.returncode != 0:
        print("COMPILE FAIL:\n", res.stderr)
        sys.exit(1)

    cand_entry, cand_image = patch_cand_elf(obj_out.read_bytes(), CAND_BASE, "ui_func_0033445c", STUB_MAP)

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
