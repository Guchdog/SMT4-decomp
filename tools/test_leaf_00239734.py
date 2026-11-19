#!/usr/bin/env python3
"""Differential Unicorn test for engine_func_00239734 (0x00239734, 1056 B)."""

from __future__ import annotations

import struct
import sys
import tempfile
from pathlib import Path

from unicorn import UC_ARCH_ARM, UC_HOOK_CODE, UC_MODE_ARM, Uc
from unicorn.arm_const import (
    UC_ARM_REG_LR,
    UC_ARM_REG_PC,
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

FUNC_ADDR = 0x00239734
FUNC_SIZE = 1056
FUNC_NAME = "engine_func_00239734"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STUB_BASE = 0x000F1000
STACK_BASE = 0x02000000
STACK_SIZE = 0x00100000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

SELF_ADDR = 0x004A0000
VTABLE_ADDR = 0x004A1000
OUT_HDR_ADDR = 0x004A2000
OUT_STATUS_ADDR = 0x004A3000
ALLOC_BUF_ADDR = 0x004B0000
OLD_PTR_ADDR = 0x004C0000
LOCK1_ADDR = 0x004E62A8
LOCK2_ADDR = 0x004E62B4
FLAGS_ADDR = 0x004656D0
HALT_ADDR = 0x004FFFF0

CALLEES = {
    0x002C3AA8: "engine_func_002c3aa8",
    0x002C3A24: "engine_func_002c3a24",
    0x00239B84: "func_00239b84",
    0x00239B54: "func_00239b54",
    0x002C5FF4: "engine_func_002c5ff4",
}
STUB_BY_NAME = {name: STUB_BASE + i * 4 for i, name in enumerate(CALLEES.values())}
VT_GET_SIZE_STUB = STUB_BASE + 0x40
VT_READ_STUB = STUB_BASE + 0x44
STUB_BY_NAME["vt_get_size"] = VT_GET_SIZE_STUB
STUB_BY_NAME["vt_read"] = VT_READ_STUB
NAME_BY_STUB = {v: k for k, v in STUB_BY_NAME.items()}


def patch_cand_elf(obj_path: Path) -> tuple[bytes, int]:
    elf = obj_path.read_bytes()
    e_shoff = struct.unpack_from("<I", elf, 0x20)[0]
    e_shentsize, e_shnum, _ = struct.unpack_from("<HHH", elf, 0x2E)
    sections = [struct.unpack_from("<10I", elf, e_shoff + i * e_shentsize) for i in range(e_shnum)]

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
            func_val = val
            func_size = struct.unpack_from("<I", elf, symtab[4] + idx * 16 + 8)[0]
            func_shndx = shndx
            break
    assert func_val is not None and func_size is not None and func_shndx is not None

    text_sh = sections[func_shndx]
    code = bytearray(elf[text_sh[4] + func_val : text_sh[4] + func_val + func_size])

    for sh in sections:
        if sh[1] == 9 and sh[7] == func_shndx:
            for pos in range(sh[4], sh[4] + sh[5], 8):
                r_off, r_info = struct.unpack_from("<II", elf, pos)
                if not (func_val <= r_off < func_val + func_size):
                    continue
                c_off = r_off - func_val
                r_type = r_info & 0xFF
                s_name, _, _ = sym_info(r_info >> 8)
                if r_type in (28, 29):
                    insn = struct.unpack_from("<I", code, c_off)[0]
                    cond = (insn >> 28) & 0xF
                    op = (insn >> 24) & 0xF
                    link = op == 0xB
                    target = STUB_BY_NAME[s_name]
                    pc = FUNC_ADDR + c_off
                    imm24 = ((target - (pc + 8)) >> 2) & 0x00FFFFFF
                    struct.pack_into("<I", code, c_off, (cond << 28) | ((0xB if link else 0xA) << 24) | imm24)
                else:
                    raise RuntimeError(f"Unsupported reloc {r_type} for {s_name}")
    return bytes(code), func_size


def patch_orig_bl(orig_code: bytes) -> bytes:
    buf = bytearray(orig_code)
    for off in range(0, len(buf), 4):
        insn = struct.unpack_from("<I", buf, off)[0]
        top = (insn >> 24) & 0xFF
        if top in (0xEA, 0xEB):
            imm24 = insn & 0x00FFFFFF
            if imm24 & 0x00800000:
                imm24 -= 0x01000000
            pc = FUNC_ADDR + off
            target = pc + 8 + imm24 * 4
            if target in CALLEES:
                stub = STUB_BY_NAME[CALLEES[target]]
                rel = ((stub - (pc + 8)) // 4) & 0x00FFFFFF
                struct.pack_into("<I", buf, off, (top << 24) | rel)
    return bytes(buf)


def compile_candidate(cpp_text: str) -> tuple[bytes, int]:
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        src = td_path / "cand.cpp"
        obj = td_path / "cand.o"
        src.write_text(cpp_text, encoding="utf-8")
        res = compile_tu_armv6k(src, obj)
        if res.returncode != 0:
            raise RuntimeError(f"compile failed:\n{res.stderr}")
        return patch_cand_elf(obj)


def run_one(code_bytes: bytes, case: dict) -> dict:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(0x000F0000, 0x00010000)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    uc.mem_write(FUNC_ADDR, code_bytes)
    for stub_addr in NAME_BY_STUB:
        uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))
    uc.mem_write(HALT_ADDR, struct.pack("<I", 0xE12FFF1E))

    # Setup self, vtable, flags, out_hdr, out_statuses
    uc.mem_write(SELF_ADDR, b"\x00" * 0x600)
    uc.mem_write(SELF_ADDR + 0x00, struct.pack("<I", VTABLE_ADDR))
    uc.mem_write(SELF_ADDR + 0x04, struct.pack("<I", case["ctx_id"]))
    uc.mem_write(SELF_ADDR + 0x3A8, struct.pack("<I", OLD_PTR_ADDR))
    uc.mem_write(SELF_ADDR + 0x558, struct.pack("<I", OLD_PTR_ADDR))

    uc.mem_write(VTABLE_ADDR + 0x08, struct.pack("<I", VT_GET_SIZE_STUB))
    uc.mem_write(VTABLE_ADDR + 0x34, struct.pack("<I", VT_READ_STUB))

    uc.mem_write(FLAGS_ADDR, bytes([0, 0, 0, case.get("flag3", 0), case.get("flag4", 0)]))
    uc.mem_write(OUT_HDR_ADDR, b"\xAA" * 0x20)
    uc.mem_write(OUT_STATUS_ADDR, struct.pack("<4I", 0x11111111, 0x22222222, 0x33333333, 0x44444444))

    trace: list[tuple] = []

    def hook_code(uc_inst, address, size, user_data):
        name = NAME_BY_STUB.get(address)
        if name is None:
            return
        r0 = uc_inst.reg_read(UC_ARM_REG_R0)
        r1 = uc_inst.reg_read(UC_ARM_REG_R1)
        r2 = uc_inst.reg_read(UC_ARM_REG_R2)
        r3 = uc_inst.reg_read(UC_ARM_REG_R3)
        sp = uc_inst.reg_read(UC_ARM_REG_SP)
        if name == "engine_func_002c3aa8":
            trace.append(("lock", r0))
        elif name == "engine_func_002c3a24":
            trace.append(("unlock", r0))
        elif name == "func_00239b84":
            trace.append(("free", r0))
        elif name == "func_00239b54":
            trace.append(("alloc", r0, r1))
            ret_ptr = ALLOC_BUF_ADDR if not case.get("alloc_fail") else 0
            uc_inst.reg_write(UC_ARM_REG_R0, ret_ptr)
        elif name == "engine_func_002c5ff4":
            data = bytes(uc_inst.mem_read(r1, r2))
            uc_inst.mem_write(r0, data)
            trace.append(("memcpy", r2))
        elif name == "vt_get_size":
            out_ptr = struct.unpack("<I", uc_inst.mem_read(sp, 4))[0]
            uc_inst.mem_write(out_ptr, struct.pack("<I", case.get("file_size", 0)))
            trace.append(("vt_get_size", r1, r2, r3))
        elif name == "vt_read":
            arg4, arg5, arg6 = struct.unpack("<III", uc_inst.mem_read(sp, 12))
            trace.append(("vt_read", r1, r2, arg4, arg5, arg6))
            payload = case.get("payload", b"")
            if payload:
                uc_inst.mem_write(r1, payload)
            uc_inst.mem_write(r3, struct.pack("<I", case.get("bytes_read", len(payload))))
            uc_inst.reg_write(UC_ARM_REG_R0, case.get("read_ret", 0))

    uc.hook_add(UC_HOOK_CODE, hook_code)

    uc.reg_write(UC_ARM_REG_R0, SELF_ADDR)
    uc.reg_write(UC_ARM_REG_R1, OUT_HDR_ADDR)
    uc.reg_write(UC_ARM_REG_R2, OUT_STATUS_ADDR)
    uc.reg_write(UC_ARM_REG_R3, 0)
    uc.mem_write(STACK_TOP, struct.pack("<I", case["mode"]))
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)

    uc.emu_start(FUNC_ADDR, HALT_ADDR, timeout=5_000_000, count=20_000)

    ret = uc.reg_read(UC_ARM_REG_R0)
    flags = bytes(uc.mem_read(FLAGS_ADDR + 3, 2))
    out_hdr5 = struct.unpack("<I", uc.mem_read(OUT_HDR_ADDR + 0x14, 4))[0]
    statuses = struct.unpack("<4I", uc.mem_read(OUT_STATUS_ADDR, 16))
    return {"ret": ret, "flags": flags, "out_hdr5": out_hdr5, "statuses": statuses, "trace": trace}


def make_payload(hdr_size: int, count: int, entries: list[tuple[int, int]]) -> bytes:
    buf = bytearray(0x20 + len(entries) * 0x70)
    struct.pack_into("<I", buf, 0x04, hdr_size)
    struct.pack_into("<I", buf, 0x14, count)
    for i, (magic, cid) in enumerate(entries):
        off = 0x20 + i * 0x70
        struct.pack_into("<H", buf, off + 0x00, magic)
        struct.pack_into("<I", buf, off + 0x10, cid)
    return bytes(buf)


def build_cases() -> list[dict]:
    return [
        {"name": "ctx_id_zero", "ctx_id": 0, "mode": 0},
        {"name": "file_size_zero", "ctx_id": 0x123, "mode": 0, "file_size": 0},
        {"name": "mode0_alloc_fail", "ctx_id": 0x123, "mode": 0, "file_size": 0x90, "flag3": 1, "alloc_fail": True},
        {"name": "mode1_read_neg", "ctx_id": 0x123, "mode": 1, "file_size": 0x90, "flag4": 1, "read_ret": 0x80000001, "bytes_read": 0x90},
        {"name": "mode2_bytes_read_zero", "ctx_id": 0x123, "mode": 2, "file_size": 0x90, "flag4": 1, "read_ret": 0, "bytes_read": 0},
        {"name": "bytes_read_lt_32", "ctx_id": 0x123, "mode": 0, "file_size": 0x1F, "bytes_read": 0x1F, "payload": b"\x00" * 0x1F},
        {"name": "hdr_size_mismatch", "ctx_id": 0x123, "mode": 0, "file_size": 0x90, "bytes_read": 0x90, "payload": make_payload(0x80, 1, [(0x6060, 0x123)])},
        {"name": "count_overflow_bytes", "ctx_id": 0x123, "mode": 0, "file_size": 0xF0, "bytes_read": 0xF0, "payload": make_payload(0xF0, 2, [(0x6060, 0x123), (0x6060, 0x123)])[:0xF0]},
        {"name": "entry_magic_bad", "ctx_id": 0x123, "mode": 0, "file_size": 0x90, "bytes_read": 0x90, "payload": make_payload(0x90, 1, [(0x6061, 0x123)])},
        {"name": "entry_ctx_id_bad", "ctx_id": 0x123, "mode": 0, "file_size": 0x90, "bytes_read": 0x90, "payload": make_payload(0x90, 1, [(0x6060, 0x999)])},
        {"name": "mode0_ok_two_entries", "ctx_id": 0x123, "mode": 0, "file_size": 0x100, "bytes_read": 0x100, "payload": make_payload(0x100, 2, [(0x6060, 0x123), (0x6060, 0x123)])},
        {"name": "mode1_ok_zero_entries", "ctx_id": 0x456, "mode": 1, "file_size": 0x20, "bytes_read": 0x20, "payload": make_payload(0x20, 0, [])},
        {"name": "mode2_ok_one_entry", "ctx_id": 0x789, "mode": 2, "flag4": 1, "file_size": 0x90, "bytes_read": 0x90, "payload": make_payload(0x90, 1, [(0x6060, 0x789)])},
    ]


def verify(cpp_text: str) -> tuple[bool, int, str]:
    cand_code, cand_size = compile_candidate(cpp_text)
    with open(CODE_BIN, "rb") as f:
        f.seek(FUNC_ADDR - CODE_BASE)
        orig_code = patch_orig_bl(f.read(FUNC_SIZE))

    for case in build_cases():
        orig_res = run_one(orig_code, case)
        cand_res = run_one(cand_code, case)
        if orig_res != cand_res:
            return False, cand_size, f"FAIL {case['name']}:\n  orig={orig_res}\n  cand={cand_res}"
    return True, cand_size, "OK"


def run_negative_controls(cpp_text: str) -> None:
    mutations = [
        ("wrong_zero_ctx_ret", "return 0xC8810BEAu;", "return 0xC8810BEFu;"),
        ("wrong_alloc_fail_ret", "return 0xC8610BF3u;", "return 0xC8810BEFu;"),
        ("wrong_entry_stride", "0x20u + count * 0x70u", "0x20u + count * 0x60u"),
        ("wrong_magic_const", "!= 0x6060u", "!= 0x6061u"),
        ("skip_entry_ptr_write", "out_entries[i] = entry;", "out_entries[i] = nullptr;"),
    ]
    for name, old, new in mutations:
        assert old in cpp_text, f"Mutation anchor missing: {name}"
        mutated = cpp_text.replace(old, new, 1)
        ok, _, _ = verify(mutated)
        if ok:
            raise AssertionError(f"Negative control {name} unexpectedly passed!")


def main() -> int:
    cpp_text = SRC_CPP.read_text(encoding="utf-8")
    ok, cand_size, msg = verify(cpp_text)
    if not ok:
        print(msg)
        return 1
    run_negative_controls(cpp_text)
    print(f"ALL PASS: {len(build_cases())} cases + 5 negative controls (cand_size={cand_size}B)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
