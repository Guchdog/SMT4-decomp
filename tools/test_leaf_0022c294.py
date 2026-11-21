#!/usr/bin/env python3
"""Differential Unicorn test for func_0022c294 (0x0022c294, 1124 B)."""

from __future__ import annotations

import struct
import sys
import tempfile
from pathlib import Path

from unicorn import UC_ARCH_ARM, UC_HOOK_CODE, UC_MODE_ARM, Uc
from unicorn.arm_const import (
    UC_ARM_REG_LR,
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_R2,
    UC_ARM_REG_SP,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k

CODE_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = ROOT / "src" / "engine" / "leaf_batch45_c.cpp"

FUNC_ADDR = 0x0022C294
FUNC_SIZE = 1124
FUNC_NAME = "func_0022c294"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STUB_BASE = 0x000F1000
STACK_BASE = 0x02000000
STACK_SIZE = 0x00100000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

SELF_ADDR = 0x004A0000
ALLOC_ADDR = 0x004A1000
ALLOC_VT = 0x004A1100
OLD_BUF_ADDR = 0x004A2000
NEW_BUF_ADDR = 0x004A3000
FILL_ADDR = 0x004A4000
OBJ_BASE = 0x004A5000
OBJ_VT = 0x004A5800
HALT_ADDR = 0x004FFFF0

CALLEES = {
    0x0022C198: "func_0022c198",
    0x0022C968: "func_0022c968",
}
STUB_BY_NAME = {name: STUB_BASE + i * 4 for i, name in enumerate(CALLEES.values())}
STUB_BY_NAME["alloc_fn"] = STUB_BASE + 0x20
STUB_BY_NAME["free_fn"] = STUB_BASE + 0x24
STUB_BY_NAME["oom_fn"] = STUB_BASE + 0x28
STUB_BY_NAME["obj_del"] = STUB_BASE + 0x2C
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


def write_node(uc: Uc, addr: int, ptr: int, ctrl: int, prev: int, nxt: int) -> None:
    uc.mem_write(addr, struct.pack("<IIII", ptr, ctrl, prev, nxt))


def run_one(code_bytes: bytes, case: dict) -> dict:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(0x000F0000, 0x00010000)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    uc.mem_write(FUNC_ADDR, code_bytes)
    for stub_addr in NAME_BY_STUB:
        uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))
    uc.mem_write(HALT_ADDR, struct.pack("<I", 0xE12FFF1E))

    uc.mem_write(ALLOC_ADDR, struct.pack("<I", ALLOC_VT))
    uc.mem_write(
        ALLOC_VT,
        struct.pack("<III", STUB_BY_NAME["alloc_fn"], STUB_BY_NAME["free_fn"], STUB_BY_NAME["oom_fn"]),
    )
    uc.mem_write(OBJ_VT, struct.pack("<II", 0, STUB_BY_NAME["obj_del"]))

    old_size = case["old_size"]
    old_cap = case["old_cap"]
    uc.mem_write(SELF_ADDR, struct.pack("<IIII", ALLOC_ADDR, OLD_BUF_ADDR, old_cap, old_size))

    # Create objects & nodes
    for i in range(4):
        uc.mem_write(OBJ_BASE + i * 0x20, struct.pack("<I", OBJ_VT))
    # Initialize old nodes as unique or linked
    for i in range(old_size):
        node_addr = OLD_BUF_ADDR + i * 16
        obj_addr = OBJ_BASE + i * 0x20
        if case.get("linked_idx") == i:
            # Self-contained 2-node ring with FILL_ADDR
            write_node(uc, node_addr, obj_addr, 1, FILL_ADDR, FILL_ADDR)
            write_node(uc, FILL_ADDR, obj_addr, 1, node_addr, node_addr)
        else:
            write_node(uc, node_addr, obj_addr, 1, node_addr, node_addr)

    if case.get("linked_idx") is None:
        # Standalone ring for fill_val
        write_node(uc, FILL_ADDR, OBJ_BASE + 0x60, 1, FILL_ADDR, FILL_ADDR)

    uc.mem_write(NEW_BUF_ADDR, b"\x00" * 0x100)

    trace: list[tuple] = []
    alloc_calls = [0]

    def hook_code(uc_inst, address, size, user_data):
        name = NAME_BY_STUB.get(address)
        if name is None:
            return
        r0 = uc_inst.reg_read(UC_ARM_REG_R0)
        r1 = uc_inst.reg_read(UC_ARM_REG_R1)
        r2 = uc_inst.reg_read(UC_ARM_REG_R2)
        if name == "func_0022c198":
            trace.append((name, r1))
            uc_inst.reg_write(UC_ARM_REG_R0, case.get("cap1", r1))
        elif name == "func_0022c968":
            trace.append((name, r1, r2))
        elif name == "alloc_fn":
            alloc_calls[0] += 1
            trace.append((name, r1))
            if alloc_calls[0] in case.get("fail_alloc_on", ()):
                uc_inst.reg_write(UC_ARM_REG_R0, 0)
            else:
                uc_inst.reg_write(UC_ARM_REG_R0, NEW_BUF_ADDR)
        elif name == "oom_fn":
            trace.append((name, r1, r2))
            if case.get("oom_ok"):
                uc_inst.reg_write(UC_ARM_REG_R0, NEW_BUF_ADDR)
            else:
                uc_inst.reg_write(UC_ARM_REG_R0, 0)
        elif name == "free_fn":
            trace.append((name, r0))
        elif name == "obj_del":
            trace.append((name, r0))

    uc.hook_add(UC_HOOK_CODE, hook_code)
    uc.reg_write(UC_ARM_REG_R0, SELF_ADDR)
    uc.reg_write(UC_ARM_REG_R1, case["new_size"])
    uc.reg_write(UC_ARM_REG_R2, FILL_ADDR)
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)
    uc.emu_start(FUNC_ADDR, HALT_ADDR, timeout=5_000_000, count=20_000)

    ret = uc.reg_read(UC_ARM_REG_R0)
    self_words = struct.unpack("<IIII", uc.mem_read(SELF_ADDR, 16))
    data_ptr = self_words[1]
    cur_sz = self_words[3]
    nodes = [struct.unpack("<IIII", uc.mem_read(data_ptr + i * 16, 16)) for i in range(cur_sz)]
    return {"ret": ret, "self": self_words, "nodes": nodes, "trace": trace}


def build_cases() -> list[dict]:
    return [
        {"name": "same_size", "old_size": 2, "old_cap": 4, "new_size": 2},
        {"name": "shrink_unique_and_linked", "old_size": 3, "old_cap": 4, "new_size": 1, "linked_idx": 1},
        {"name": "grow_in_cap", "old_size": 1, "old_cap": 4, "new_size": 3},
        {"name": "grow_realloc_cap1_ok", "old_size": 2, "old_cap": 2, "new_size": 3, "cap1": 4},
        {"name": "grow_realloc_oom_retry", "old_size": 1, "old_cap": 1, "new_size": 2, "cap1": 4, "fail_alloc_on": (1,), "oom_ok": True},
        {"name": "grow_realloc_fallback_new_size", "old_size": 1, "old_cap": 1, "new_size": 3, "cap1": 4, "fail_alloc_on": (1,), "oom_ok": False},
        {"name": "grow_realloc_all_fail_same_cap1", "old_size": 1, "old_cap": 1, "new_size": 3, "cap1": 3, "fail_alloc_on": (1, 2)},
        {"name": "grow_realloc_all_fail_fallback", "old_size": 1, "old_cap": 1, "new_size": 3, "cap1": 4, "fail_alloc_on": (1, 2)},
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
        ("wrong_same_ret", "if (new_size == old_size) {\n            return 1;\n        }", "if (new_size == old_size) {\n            return 0;\n        }"),
        ("wrong_node_stride", "count * 16u);", "count * 12u);"),
        ("wrong_oom_str", "0x0040FE40u", "0x0040FE44u"),
        ("wrong_grow_size", "*reinterpret_cast<u32*>(self + 0x0Cu) = new_size;\n    } else {", "*reinterpret_cast<u32*>(self + 0x0Cu) = old_size;\n    } else {"),
        ("wrong_copy_ctrl", "dst->ctrl = src->ctrl;", "dst->ctrl = 0u;"),
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
