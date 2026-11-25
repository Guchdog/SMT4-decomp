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
    UC_ARM_REG_SP,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from build_check import compile_tu_armv6k  # noqa: E402

CODE_BIN = REPO_ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = REPO_ROOT / "src" / "engine" / "leaf_batch45_c.cpp"

FUNC_ADDR = 0x00143B98
FUNC_SIZE = 1604

CALLEES = {
    "func_00147994": 0x00147994,
    "func_002aa938": 0x002AA938,
}

STUB_RET = 0x00600000
STUB_BASE = 0x00600100
CAND_BASE = 0x00700000
STACK_TOP = 0x0080FFF0

G_PTR_ADDR = 0x004655C0
G_OBJ_ADDR = 0x00500000
CFG_ADDR = 0x00510000
CMD_CUR_PTR = 0x004652A0
CMD_END_PTR = 0x004652A4
CMD_BUF_ADDR = 0x00520000


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

    uc.mem_write(G_PTR_ADDR, struct.pack("<I", G_OBJ_ADDR))
    g_buf = bytearray(0x800)
    g_buf[0x107] = case.get("g107", 1)
    init_state = case.get("init_state", [0xFFFFFFFF] * 16)
    for idx, val in enumerate(init_state):
        struct.pack_into("<I", g_buf, 0x770 + idx * 4, val)
    uc.mem_write(G_OBJ_ADDR, bytes(g_buf))

    cmd_room = case.get("cmd_room", 16)
    uc.mem_write(CMD_CUR_PTR, struct.pack("<I", CMD_BUF_ADDR))
    uc.mem_write(CMD_END_PTR, struct.pack("<I", CMD_BUF_ADDR + cmd_room))
    uc.mem_write(CMD_BUF_ADDR, b"\x00" * 32)

    cfg = bytearray(0x200)
    struct.pack_into("<I", cfg, 0x00, case.get("cfg0", 0x2600))
    struct.pack_into("<I", cfg, 0x04, case.get("cfg4", 0x2600))
    struct.pack_into("<I", cfg, 0x08, case.get("cfg8", 0x2901))
    struct.pack_into("<I", cfg, 0x0C, case.get("cfgc", 0x812D))
    struct.pack_into("<i", cfg, 0x14, case.get("cfg14", 3))
    r, g, b, a = case.get("rgba", (0.5, 0.25, 0.75, 1.0))
    struct.pack_into("<4f", cfg, 0x18, r, g, b, a)

    for i in range(6):
        off = 0x34 + i * 0x44
        st = case.get("stages", [{}] * 6)[i]
        struct.pack_into("<I", cfg, off + 0x00, st.get("s00", 0x01000000 + i * 0x1000))
        struct.pack_into("<I", cfg, off + 0x0C, st.get("s0c", 64))
        struct.pack_into("<I", cfg, off + 0x10, st.get("s10", 128))
        struct.pack_into("<I", cfg, off + 0x14, st.get("s14", 0x190A))
        struct.pack_into("<I", cfg, off + 0x1C, st.get("s1c", 5))
        struct.pack_into("<I", cfg, off + 0x20, st.get("s20", 0x1000))
        struct.pack_into("<I", cfg, off + 0x34, st.get("s34", 2))
    uc.mem_write(CFG_ADDR, bytes(cfg))

    events = []
    addr_to_name = {v: k for k, v in callee_addrs.items()}

    def hook_code(uc_inst, address, size, user_data):
        name = addr_to_name.get(address)
        r0 = uc_inst.reg_read(UC_ARM_REG_R0)
        r1 = uc_inst.reg_read(UC_ARM_REG_R1)
        if name == "func_00147994":
            events.append(("147994", r0))
            uc_inst.reg_write(UC_ARM_REG_R0, (r0 ^ 0xA5A50000) & 0xFFFFFFFF)
        elif name == "func_002aa938":
            events.append(("2aa938", r0, r1))

    for stub_addr in callee_addrs.values():
        uc.hook_add(UC_HOOK_CODE, hook_code, begin=stub_addr, end=stub_addr)

    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, STUB_RET)
    uc.reg_write(UC_ARM_REG_R0, CFG_ADDR)
    uc.reg_write(UC_ARM_REG_R1, case.get("idx", 0))

    uc.emu_start(entry_addr, STUB_RET, count=500000)

    ret = uc.reg_read(UC_ARM_REG_R0)
    state_out = struct.unpack_from("<16I", uc.mem_read(G_OBJ_ADDR + 0x770, 64), 0)
    cmd_cur_out = struct.unpack_from("<I", uc.mem_read(CMD_CUR_PTR, 4), 0)[0]
    cmd_words = struct.unpack_from("<2I", uc.mem_read(CMD_BUF_ADDR, 8), 0)
    return {
        "ret": ret,
        "state": state_out,
        "cmd_cur": cmd_cur_out,
        "cmd_words": cmd_words,
        "events": events,
    }


def make_base_stages():
    return [{} for _ in range(6)]


def make_cases():
    cases = [
        # 1. idx != 0
        {"idx": 1},
        # 2. g[0x107] == 0
        {"g107": 0},
        # 3. stage mismatch cases
        {"stages": [{}] + [{"s00": 0}] + [{}] * 4},
        {"stages": [{}] + [{"s34": 3}] + [{}] * 4},
        {"stages": [{}] + [{"s20": 0x2000}] + [{}] * 4},
        {"stages": [{}] + [{"s0c": 65}] + [{}] * 4},
        {"stages": [{}] + [{"s10": 129}] + [{}] * 4},
        {"stages": [{}] + [{"s14": 0x1909}] + [{}] * 4},
        {"stages": [{"s00": 0x02000000}] + [{"s00": 0x01000000}] + [{}] * 4},
        {"stages": [{"s00": 0x01001000}] + [{"s00": 0x01000000}] + [{}] * 4},
        # 4. fmt == 0x6040
        {"stages": [{"s14": 0x6040} for _ in range(6)]},
        # 5. fmt in 0x1906..0x190A, 0x675A, 0x675B, invalid
        {"stages": [{"s14": 0x1906} for _ in range(6)]},
        {"stages": [{"s14": 0x675A} for _ in range(6)]},
        {"stages": [{"s14": 0x675B} for _ in range(6)]},
        {"stages": [{"s14": 0x1234} for _ in range(6)]},
        # 6. cfg8 / cfgc / cfg0 / cfg4 variants
        {"cfg8": 0x812F, "cfgc": 0x8370, "cfg0": 0x2601, "cfg4": 0x2601, "rgba": (1.0, 0.5, 0.25, 1.0)},
        {"cfg8": 0x8370, "cfgc": 0x2901, "cfg0": 0x2600, "cfg4": 0x2700, "cfg14": 9},
        {"cfg8": 0x812D, "cfgc": 0x812F, "cfg0": 0x2601, "cfg4": 0x2701, "cfg14": -1},
        {"cfg4": 0x2702, "cfg14": 5},
        {"cfg4": 0x2703, "cfg14": 12},
        # 7. cmd_room == 0 (no emit)
        {"cmd_room": 0},
    ]
    return cases


def build_cand_from_source(src_text: str, tag: str = "cand"):
    tmp_dir = REPO_ROOT / "build" / "test_leaf_00143b98_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    src_path = tmp_dir / f"{tag}.cpp"
    obj_path = tmp_dir / f"{tag}.o"
    src_path.write_text(src_text, encoding="utf-8")
    res = compile_tu_armv6k(src_path, obj_path)
    assert res.returncode == 0, f"Compile failed ({tag}):\n{res.stderr}"
    stub_map = {name: STUB_BASE + i * 8 for i, name in enumerate(CALLEES)}
    cand_bytes, cand_entry = patch_cand_elf(obj_path.read_bytes(), CAND_BASE, "func_00143b98", stub_map)
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
        ("wrong_idx_ret", "if (idx != 0u) {\n        return 0x0502u;", "if (idx != 0u) {\n        return 0u;"),
        ("wrong_rgba_scale", "255.0f);", "254.0f);"),
        ("wrong_fmt_675a", "u32 fmt_bits = (fmt == 0x675Au) ? 2u : 0u;", "u32 fmt_bits = (fmt == 0x675Au) ? 1u : 0u;"),
        ("skip_2aa938", "func_002aa938(0x81u, 0x0Au);", "// skipped"),
        ("wrong_cmd_magic", "cmd_cur[1] = 0x000F008Eu;", "cmd_cur[1] = 0x000F008Fu;"),
    ]
    for name, old_s, new_s in mutations:
        if old_s not in src_text and "0x675Au" in old_s:
            old_s = old_s.replace("0x675Au", "0x675A")
            new_s = new_s.replace("0x675Au", "0x675A")
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
