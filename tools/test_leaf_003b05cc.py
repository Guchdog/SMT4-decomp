#!/usr/bin/env python3
"""Differential Unicorn test for func_003b05cc (0x003b05cc, 1464 B)."""

from __future__ import annotations

import struct
import sys
import tempfile
from pathlib import Path

from unicorn import UC_ARCH_ARM, UC_HOOK_CODE, UC_MODE_ARM, Uc
from unicorn.arm_const import (
    UC_ARM_REG_C1_C0_2,
    UC_ARM_REG_FPEXC,
    UC_ARM_REG_LR,
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_R2,
    UC_ARM_REG_R3,
    UC_ARM_REG_SP,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k

CODE_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = ROOT / "src" / "engine" / "leaf_batch45_c.cpp"

FUNC_ADDR = 0x003B05CC
FUNC_SIZE = 1464
FUNC_NAME = "func_003b05cc"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x00510000
STACK_BASE = 0x02000000
STACK_SIZE = 0x00100000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

DATA_BASE = 0x00600000
DATA_SIZE = 0x00040000
HALT_ADDR = 0x006FFFF0

CALLEES = {
    0x003B0C30: "func_003b0c30",
    0x003B0B84: "func_003b0b84",
    0x001ED7C0: "func_001ed7c0",
    0x003B0F14: "func_003b0f14",
    0x0022C6F8: "func_0022c6f8",
    0x003B11A8: "func_003b11a8",
    0x003B0FD8: "func_003b0fd8",
    0x003B2538: "func_003b2538",
}
STUB_BY_NAME = {name: STUB_BASE + i * 4 for i, name in enumerate(CALLEES.values())}
STUB_READ = STUB_BASE + 0x100
STUB_ACK = STUB_BASE + 0x104
STUB_CHK = STUB_BASE + 0x108
STUB_SETSZ = STUB_BASE + 0x10C
STUB_LOG = STUB_BASE + 0x110
STUB_BY_NAME["vtbl_read"] = STUB_READ
STUB_BY_NAME["vtbl_ack"] = STUB_ACK
STUB_BY_NAME["vtbl_chk"] = STUB_CHK
STUB_BY_NAME["vtbl_setsz"] = STUB_SETSZ
STUB_BY_NAME["log_fn"] = STUB_LOG
STUB_BY_NAME["__aeabi_memclr4"] = STUB_BASE + 0x114
NAME_BY_STUB = {v: k for k, v in STUB_BY_NAME.items()}

SELF_ADDR = DATA_BASE + 0x1000
READER_ADDR = DATA_BASE + 0x3000
VTBL_ADDR = DATA_BASE + 0x3200
BUF_ADDR = DATA_BASE + 0x4000


def patch_cand_elf(obj_path: Path) -> tuple[bytes, list[tuple[int, bytes]], int]:
    elf = obj_path.read_bytes()
    e_shoff = struct.unpack_from("<I", elf, 0x20)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", elf, 0x2E)
    sections = [struct.unpack_from("<10I", elf, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr_off = sections[e_shstrndx][4]

    def sec_name(idx: int) -> str:
        n_off = shstr_off + sections[idx][0]
        return elf[n_off : elf.find(b"\x00", n_off)].decode("ascii", errors="replace")

    symtab = next(sh for sh in sections if sh[1] == 2)
    strtab = sections[symtab[6]]
    str_off = strtab[4]

    def sym_info(sym_idx: int) -> tuple[str, int, int]:
        s_off = symtab[4] + sym_idx * 16
        st_name, st_value, _, _, _, st_shndx = struct.unpack_from("<IIIBBH", elf, s_off)
        end = elf.find(b"\x00", str_off + st_name)
        return elf[str_off + st_name : end].decode("ascii", errors="replace"), st_value, st_shndx

    func_val = func_size = func_shndx = None
    for idx in range(symtab[5] // 16):
        name, val, shndx = sym_info(idx)
        if name == FUNC_NAME:
            s_off = symtab[4] + idx * 16
            func_size = struct.unpack_from("<I", elf, s_off + 8)[0]
            func_val, func_shndx = val, shndx
            break
    if func_val is None or func_shndx is None:
        raise RuntimeError(f"Symbol {FUNC_NAME} not found")

    text_sh = sections[func_shndx]
    text_bytes = bytearray(elf[text_sh[4] : text_sh[4] + text_sh[5]])
    text_name = sec_name(func_shndx)

    rodata_blobs: list[tuple[int, bytes]] = []
    rodata_map: dict[int, int] = {}
    next_ro = RODATA_BASE
    for idx, sh in enumerate(sections):
        sname = sec_name(idx)
        if sname.startswith(".rodata"):
            blob = elf[sh[4] : sh[4] + sh[5]]
            rodata_map[idx] = next_ro
            rodata_blobs.append((next_ro, blob))
            next_ro += (len(blob) + 0x1F) & ~0x1F

    for idx, sh in enumerate(sections):
        if sh[1] != 9:
            continue
        if sec_name(sh[7]) != text_name:
            continue
        for pos in range(0, sh[5], 8):
            r_off, r_info = struct.unpack_from("<II", elf, sh[4] + pos)
            r_type = r_info & 0xFF
            sym_idx = r_info >> 8
            sname, sval, sshndx = sym_info(sym_idx)

            is_in_func = func_val <= r_off < func_val + func_size
            if not is_in_func and not (r_type in (28, 29) and sname in STUB_BY_NAME):
                continue

            if sname in STUB_BY_NAME:
                target = STUB_BY_NAME[sname]
            elif sshndx in rodata_map:
                target = rodata_map[sshndx] + sval
            elif sshndx == func_shndx:
                target = CODE_BASE + sval
            else:
                raise RuntimeError(f"Unhandled reloc {sname!r} type={r_type} at 0x{r_off:x}")

            if r_type in (28, 29):
                insn = struct.unpack_from("<I", text_bytes, r_off)[0]
                rel = ((target - (CODE_BASE + r_off + 8)) >> 2) & 0x00FFFFFF
                struct.pack_into("<I", text_bytes, r_off, (insn & 0xFF000000) | rel)
            elif r_type == 2:
                addend = struct.unpack_from("<i", text_bytes, r_off)[0]
                struct.pack_into("<I", text_bytes, r_off, target + addend)
            elif r_type == 43:
                insn = struct.unpack_from("<I", text_bytes, r_off)[0]
                imm16 = target & 0xFFFF
                struct.pack_into("<I", text_bytes, r_off, (insn & 0xFFF0F000) | ((imm16 >> 12) << 16) | (imm16 & 0xFFF))
            elif r_type == 44:
                insn = struct.unpack_from("<I", text_bytes, r_off)[0]
                imm16 = (target >> 16) & 0xFFFF
                struct.pack_into("<I", text_bytes, r_off, (insn & 0xFFF0F000) | ((imm16 >> 12) << 16) | (imm16 & 0xFFF))
            else:
                raise RuntimeError(f"Unsupported r_type={r_type} for {sname!r}")

    return bytes(text_bytes), rodata_blobs, CODE_BASE + func_val


def patch_orig_bl(code: bytearray) -> None:
    for off in range(FUNC_ADDR - CODE_BASE, FUNC_ADDR - CODE_BASE + FUNC_SIZE, 4):
        insn = struct.unpack_from("<I", code, off)[0]
        top = (insn >> 24) & 0xFF
        if ((top & 0x0E) == 0x0A and top < 0xF0) or top in (0xFA, 0xFB):
            imm24 = insn & 0x00FFFFFF
            if imm24 & 0x00800000:
                imm24 -= 0x01000000
            pc = CODE_BASE + off + 8
            target = pc + (imm24 << 2)
            if target in CALLEES:
                stub = STUB_BY_NAME[CALLEES[target]]
                rel = ((stub - pc) >> 2) & 0x00FFFFFF
                op = 0xEB000000 if top in (0xFA, 0xFB) else (insn & 0xFF000000)
                struct.pack_into("<I", code, off, op | rel)


def run_side(
    code_bytes: bytes,
    rodata_blobs: list[tuple[int, bytes]],
    entry: int,
    cfg: dict,
) -> tuple[int, list, bytes]:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_write(CODE_BASE, code_bytes)

    uc.mem_map(STUB_BASE, 0x2000)
    for addr in NAME_BY_STUB:
        uc.mem_write(addr, struct.pack("<I", 0xE12FFF1E))

    uc.mem_map(RODATA_BASE, 0x20000)
    for addr, blob in rodata_blobs:
        uc.mem_write(addr, blob)

    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.mem_map(DATA_BASE, DATA_SIZE)
    uc.mem_map(0x006F0000, 0x10000)
    uc.mem_write(HALT_ADDR, struct.pack("<I", 0xE320F000))

    uc.mem_write(VTBL_ADDR + 0x08, struct.pack("<I", STUB_SETSZ))
    uc.mem_write(VTBL_ADDR + 0x14, struct.pack("<I", STUB_READ))
    uc.mem_write(VTBL_ADDR + 0x18, struct.pack("<I", STUB_ACK))
    uc.mem_write(VTBL_ADDR + 0x28, struct.pack("<I", STUB_CHK))
    uc.mem_write(READER_ADDR, struct.pack("<I", VTBL_ADDR))

    uc.mem_write(SELF_ADDR, b"\x00" * 0x1490)
    uc.mem_write(SELF_ADDR + 0x00, struct.pack("<QQ", cfg.get("self_q0", 0), cfg.get("self_q8", 0)))
    uc.mem_write(SELF_ADDR + 0x1440, struct.pack("<I", cfg.get("f1440", 0x12)))
    uc.mem_write(SELF_ADDR + 0x1470, struct.pack("<I", READER_ADDR))
    uc.mem_write(SELF_ADDR + 0x1474, struct.pack("<I", cfg.get("pkt_rem", 0)))
    uc.mem_write(SELF_ADDR + 0x1478, struct.pack("<I", 0x20))
    uc.mem_write(SELF_ADDR + 0x147C, struct.pack("<I", 0x999))
    uc.mem_write(SELF_ADDR + 0x1480, struct.pack("<I", STUB_LOG))
    uc.mem_write(SELF_ADDR + 0x1485, bytes([cfg.get("f1485", 0)]))
    uc.mem_write(SELF_ADDR + 0x1487, bytes([cfg.get("f1487", 0)]))
    uc.mem_write(SELF_ADDR + 0x1488, bytes([cfg.get("f1488", 0)]))
    uc.mem_write(SELF_ADDR + 0x1489, bytes([1]))

    uc.reg_write(UC_ARM_REG_R0, SELF_ADDR)
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)

    trace: list = []
    hdr_calls = [0]
    r11a8_calls = [0]
    r2538_calls = [0]

    def u32(a: int) -> int:
        return struct.unpack("<I", uc.mem_read(a, 4))[0]

    def hook(uc_inst, address, size, user_data):
        name = NAME_BY_STUB.get(address)
        if name is None:
            return
        a0 = uc_inst.reg_read(UC_ARM_REG_R0)
        a1 = uc_inst.reg_read(UC_ARM_REG_R1)
        a2 = uc_inst.reg_read(UC_ARM_REG_R2)
        a3 = uc_inst.reg_read(UC_ARM_REG_R3)

        if name == "__aeabi_memclr4":
            uc_inst.mem_write(a0, b"\x00" * a1)
        elif name == "vtbl_read":
            ok = cfg.get("read_ok", 1)
            if ok:
                buf_p = 0 if cfg.get("read_null", False) else BUF_ADDR
                uc_inst.mem_write(a1, struct.pack("<I", buf_p))
                uc_inst.mem_write(a2, struct.pack("<I", cfg.get("read_len", 0)))
            uc_inst.reg_write(UC_ARM_REG_R0, ok)
            trace.append((name, ok))
        elif name == "vtbl_ack":
            ret = cfg.get("ack_ret", 1)
            uc_inst.reg_write(UC_ARM_REG_R0, ret)
            trace.append((name, a1, ret))
        elif name == "vtbl_chk":
            ret = cfg.get("chk_ret", 0)
            uc_inst.reg_write(UC_ARM_REG_R0, ret)
            trace.append((name, ret))
        elif name == "vtbl_setsz":
            ret = cfg.get("setsz_ret", 1)
            uc_inst.reg_write(UC_ARM_REG_R0, ret)
            trace.append((name, a1, ret))
        elif name == "log_fn":
            if a0 in (0x0040FF30, 0x0040FECC):
                tag = f"0x{a0:08x}"
            else:
                raw_s = bytes(uc_inst.mem_read(a0, 64))
                tag = raw_s.split(b"\x00", 1)[0].decode("ascii", errors="replace")
            trace.append((name, tag))
        elif name == "func_003b0c30":
            ret = cfg.get("ret_0c30", 1)
            uc_inst.reg_write(UC_ARM_REG_R0, ret)
            trace.append((name, ret))
        elif name == "func_003b0b84":
            ret = cfg.get("ret_0b84", 1)
            uc_inst.reg_write(UC_ARM_REG_R0, ret)
            trace.append((name, ret))
        elif name == "func_001ed7c0":
            hdr_calls[0] += 1
            hit_at = cfg.get("hdr_hit_at", 1)
            if hdr_calls[0] == hit_at:
                uc_inst.mem_write(a1, struct.pack("<Q", cfg.get("hdr_val", 0x100)))
                uc_inst.mem_write(a2, struct.pack("<H", cfg.get("hdr_sz", 0x20)))
                ret = 1
            else:
                ret = 0
            uc_inst.reg_write(UC_ARM_REG_R0, ret)
            trace.append((name, a0 - BUF_ADDR, ret))
        elif name == "func_003b0f14":
            trace.append((name,))
        elif name == "func_0022c6f8":
            trace.append((name, a0 - SELF_ADDR, a1, a2))
        elif name == "func_003b11a8":
            r11a8_calls[0] += 1
            seq = cfg.get("seq_11a8", [0x100])
            ret = seq[min(r11a8_calls[0] - 1, len(seq) - 1)]
            if cfg.get("inc_consumed_11a8"):
                uc_inst.mem_write(a2, struct.pack("<I", u32(a2) + cfg["inc_consumed_11a8"]))
            uc_inst.reg_write(UC_ARM_REG_R0, ret)
            trace.append((name, u32(a2), a3, ret))
        elif name == "func_003b0fd8":
            ret = cfg.get("ret_0fd8", 0)
            if cfg.get("clear_1487_in_0fd8"):
                uc_inst.mem_write(SELF_ADDR + 0x1487, b"\x00")
            uc_inst.reg_write(UC_ARM_REG_R0, ret)
            trace.append((name, u32(a2), a3, ret))
        elif name == "func_003b2538":
            r2538_calls[0] += 1
            seq = cfg.get("seq_2538", [0x101])
            ret = seq[min(r2538_calls[0] - 1, len(seq) - 1)]
            if cfg.get("inc_consumed_2538"):
                uc_inst.mem_write(a2, struct.pack("<I", u32(a2) + cfg["inc_consumed_2538"]))
            uc_inst.reg_write(UC_ARM_REG_R0, ret)
            trace.append((name, u32(a2), a3, ret))

    uc.hook_add(UC_HOOK_CODE, hook, begin=STUB_BASE, end=STUB_BASE + 0x1000)
    uc.emu_start(entry, HALT_ADDR, timeout=5_000_000, count=200_000)

    state_snap = bytes(uc.mem_read(SELF_ADDR, 0x10)) + bytes(uc.mem_read(SELF_ADDR + 0x1440, 0x4C))
    return uc.reg_read(UC_ARM_REG_R0), trace, state_snap


def make_cases() -> list[tuple[str, dict]]:
    return [
        ("read_fail_chk0", {"read_ok": 0, "chk_ret": 0}),
        ("read_fail_chk1_ok", {"read_ok": 0, "chk_ret": 1, "ret_0c30": 1}),
        ("read_fail_chk1_err", {"read_ok": 0, "chk_ret": 1, "ret_0c30": 0}),
        ("empty_1488_0", {"read_len": 0, "f1488": 0}),
        ("empty_1488_1_0b84_fail", {"read_len": 0, "f1488": 1, "ret_0b84": 0}),
        ("empty_1488_1_ok_1487_1", {"read_len": 0, "f1488": 1, "ret_0b84": 1, "f1487": 1}),
        ("empty_1488_1_ok_1487_0", {"read_len": 0, "f1488": 1, "ret_0b84": 1, "f1487": 0}),
        ("f1487_1_pkt_rem_mismatch_1485_0", {"f1487": 1, "pkt_rem": 0x20, "f1485": 0, "read_len": 0x10}),
        ("f1487_1_pkt_rem_mismatch_1485_1", {"f1487": 1, "pkt_rem": 0x20, "f1485": 1, "read_len": 0x24}),
        ("f1487_0_short_len", {"f1487": 0, "read_len": 0x0D}),
        ("f1487_0_scan_hit_neg_sz_ok", {"f1487": 0, "read_len": 0x12, "hdr_hit_at": 3, "hdr_val": 0x8000000000000001, "hdr_sz": 0x10}),
        ("f1487_0_scan_hit_bad_sz", {"f1487": 0, "read_len": 0x12, "hdr_hit_at": 1, "hdr_val": 0x10, "hdr_sz": 0x0F}),
        ("f1487_0_scan_miss_1488_1", {"f1487": 0, "read_len": 0x12, "hdr_hit_at": 99, "f1488": 1}),
        ("f1487_0_scan_miss_1488_0", {"f1487": 0, "read_len": 0x10, "hdr_hit_at": 99, "f1488": 0}),
        ("hdr_body_full_success", {
            "f1487": 1, "pkt_rem": 0x20, "read_len": 0x20,
            "self_q0": 0x50, "self_q8": 0,
            "hdr_val": 0x8000000000000120, "hdr_sz": 0x20,
            "seq_11a8": [0, 0x100], "seq_2538": [0, 0x101],
        }),
        ("hdr_resize_grow_ok", {
            "f1487": 1, "pkt_rem": 0x18, "f1485": 1, "read_len": 0x18,
            "hdr_val": 0, "hdr_sz": 0x24, "setsz_ret": 1,
        }),
        ("hdr_resize_fail", {
            "f1487": 1, "pkt_rem": 0x18, "f1485": 1, "read_len": 0x18,
            "hdr_val": 0, "hdr_sz": 0x24, "setsz_ret": 0,
        }),
        ("hdr_consumed_overflow", {
            "f1487": 1, "pkt_rem": 0x20, "read_len": 0x20,
            "hdr_val": 0, "hdr_sz": 0x20,
            "seq_11a8": [0x100], "inc_consumed_11a8": 0x20,
        }),
        ("body_1487_cleared", {
            "f1487": 1, "read_len": 0x0C, "clear_1487_in_0fd8": True,
        }),
        ("body_2538_overflow", {
            "f1487": 1, "read_len": 0x0C,
            "seq_2538": [0x101], "inc_consumed_2538": 0x10,
        }),
    ]


def main() -> int:
    raw = bytearray(CODE_BIN.read_bytes())
    patch_orig_bl(raw)
    orig_code = bytes(raw)

    with tempfile.TemporaryDirectory() as tmpdir:
        obj_path = Path(tmpdir) / "leaf_batch45_c.o"
        res = compile_tu_armv6k(SRC_CPP, obj_path)
        if res.returncode != 0:
            print(f"COMPILE ERROR:\n{res.stderr}")
            return 1
        cand_code, rodata_blobs, cand_entry = patch_cand_elf(obj_path)

    cases = make_cases()
    for name, cfg in cases:
        o_res = run_side(orig_code, [], FUNC_ADDR, cfg)
        c_res = run_side(cand_code, rodata_blobs, cand_entry, cfg)
        if o_res != c_res:
            print(f"FAIL {name}:\n  orig=({o_res[0]}, {o_res[1]})\n  cand=({c_res[0]}, {c_res[1]})")
            return 1
        print(f"PASS {name}")

    # 5 negative controls
    src_text = SRC_CPP.read_text(encoding="utf-8")
    mutations = [
        ("neg_read_fail", "return (func_003b0c30(self) != 0u) ? 3u : 0x44u;", "return 0x44u;"),
        ("neg_empty_1488", "if (self[0x1488u] != 0u) {\n            *reinterpret_cast<u32*>(self + 0x147Cu)", "if (self[0x1488u] == 0u) {\n            *reinterpret_cast<u32*>(self + 0x147Cu)"),
        ("neg_hdr_sz_10", "if (hdr_sz < 0x10u) {\n                    reset_reader_3b05cc(self);", "if (hdr_sz < 0x0Fu) {\n                    reset_reader_3b05cc(self);"),
        ("neg_prev_pkt", "if (prev_pkt < hdr_sz) {\n                return 0u;\n            }", "if (prev_pkt > hdr_sz) {\n                return 0u;\n            }"),
        ("neg_2538_101", "if (r2 == 0x101u) {", "if (r2 == 0x102u) {"),
    ]
    for mname, old, new in mutations:
        assert old in src_text, f"Mutation target not found: {old}"
        mut_src = src_text.replace(old, new, 1)
        with tempfile.TemporaryDirectory() as tmpdir:
            mut_cpp = Path(tmpdir) / "mut.cpp"
            mut_obj = Path(tmpdir) / "mut.o"
            mut_cpp.write_text(mut_src, encoding="utf-8")
            res = compile_tu_armv6k(mut_cpp, mut_obj)
            if res.returncode != 0:
                print(f"MUT COMPILE ERR {mname}: {res.stderr}")
                return 1
            m_code, m_ro, m_entry = patch_cand_elf(mut_obj)
        detected = False
        for _, cfg in cases:
            o_res = run_side(orig_code, [], FUNC_ADDR, cfg)
            m_res = run_side(m_code, m_ro, m_entry, cfg)
            if o_res != m_res:
                detected = True
                break
        if not detected:
            print(f"FAIL negative control {mname} was not detected!")
            return 1
        print(f"PASS {mname} (detected)")

    print(f"ALL PASS: {len(cases)} cases + {len(mutations)} negative controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
