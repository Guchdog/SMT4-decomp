#!/usr/bin/env python3
"""Differential Unicorn test for engine_func_001a9970 (0x001a9970, 1096 B)."""

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
    UC_ARM_REG_R3,
    UC_ARM_REG_SP,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k

CODE_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = ROOT / "src" / "engine" / "leaf_batch45_c.cpp"

FUNC_ADDR = 0x001A9970
FUNC_SIZE = 1096
FUNC_NAME = "engine_func_001a9970"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x000F4000
STACK_BASE = 0x02000000
STACK_SIZE = 0x00100000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

G_STATE_ADDR = 0x0044DB88
TABLE_ADDR = 0x0044DBB0
G_SYS_PTR_ADDR = 0x0049F91C
G_SYS_OBJ_ADDR = 0x004A0000
STATE_OBJ_ADDR = 0x004A1000
VM_ADDR = 0x004A2000
HALT_ADDR = 0x004FFFF0

CALLEES = {
    0x002C0BA8: "script_vm_func_002c0ba8",
    0x0028796C: "engine_func_0028796c",
    0x00287958: "engine_func_00287958",
    0x00287790: "engine_func_00287790",
    0x002990BC: "script_vm_func_002990bc",
    0x002876D0: "ui_func_002876d0",
    0x00287590: "engine_func_00287590",
    0x00289B4C: "CommonBg_func_00289b4c",
    0x0028DC54: "camp_func_0028dc54",
    0x0028D974: "ButtonHelp_Init",
    0x00289AE8: "script_vm_func_00289ae8",
    0x002C23F8: "AsdMemory_func_002c23f8",
    0x0028757C: "engine_func_0028757c",
    0x00381D9C: "script_vm_func_00381d9c",
    0x00384304: "engine_func_00384304",
    0x002BF86C: "engine_func_002bf86c",
    0x002C59B8: "AsdSequence_func_002c59b8",
    0x00384AC8: "engine_func_00384ac8",
    0x002A72FC: "script_vm_func_002a72fc",
    0x002B2520: "engine_func_002b2520",
    0x00385488: "engine_func_00385488",
    0x0028756C: "engine_func_0028756c",
    0x0028753C: "engine_func_0028753c",
    0x00291BE8: "script_vm_func_00291be8",
    0x00291A5C: "script_vm_func_00291a5c",
    0x002874E4: "engine_func_002874e4",
    0x002A0678: "ui_func_002a0678",
    0x0032C8D0: "script_vm_func_0032c8d0",
}
STUB_BY_NAME = {name: STUB_BASE + i * 4 for i, name in enumerate(CALLEES.values())}
NAME_BY_STUB = {v: k for k, v in STUB_BY_NAME.items()}


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
            func_val = val
            func_size = struct.unpack_from("<I", elf, symtab[4] + idx * 16 + 8)[0]
            func_shndx = shndx
            break
    assert func_val is not None and func_size is not None and func_shndx is not None

    text_sh = sections[func_shndx]
    code = bytearray(elf[text_sh[4] + func_val : text_sh[4] + func_val + func_size])

    rodata_blob = bytearray()
    rodata_map: dict[int, int] = {}
    for idx, sh in enumerate(sections):
        if sec_name(idx).startswith(".rodata"):
            rodata_map[idx] = RODATA_BASE + len(rodata_blob)
            rodata_blob.extend(elf[sh[4] : sh[4] + sh[5]])
            while len(rodata_blob) % 4 != 0:
                rodata_blob.append(0)

    for sh in sections:
        if sh[1] == 9 and sh[7] == func_shndx:
            for pos in range(sh[4], sh[4] + sh[5], 8):
                r_off, r_info = struct.unpack_from("<II", elf, pos)
                if not (func_val <= r_off < func_val + func_size):
                    continue
                c_off = r_off - func_val
                r_type = r_info & 0xFF
                s_name, _, s_shndx = sym_info(r_info >> 8)
                if r_type in (28, 29):
                    insn = struct.unpack_from("<I", code, c_off)[0]
                    cond = (insn >> 28) & 0xF
                    op = (insn >> 24) & 0xF
                    link = op == 0xB
                    target = STUB_BY_NAME[s_name]
                    pc = FUNC_ADDR + c_off
                    imm24 = ((target - (pc + 8)) >> 2) & 0x00FFFFFF
                    struct.pack_into("<I", code, c_off, (cond << 28) | ((0xB if link else 0xA) << 24) | imm24)
                elif r_type == 2:
                    addend = struct.unpack_from("<I", code, c_off)[0]
                    if s_shndx == func_shndx:
                        struct.pack_into("<I", code, c_off, (FUNC_ADDR - func_val) + addend)
                    elif s_shndx in rodata_map:
                        struct.pack_into("<I", code, c_off, rodata_map[s_shndx] + addend)
                    else:
                        raise RuntimeError(f"Unexpected R_ARM_ABS32 section {s_shndx} ({s_name})")
                else:
                    raise RuntimeError(f"Unsupported reloc {r_type} for {s_name}")
    rodata_blobs = [(RODATA_BASE, bytes(rodata_blob))] if rodata_blob else []
    return bytes(code), rodata_blobs, func_size


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


def compile_candidate(cpp_text: str) -> tuple[bytes, list[tuple[int, bytes]], int]:
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        src = td_path / "cand.cpp"
        obj = td_path / "cand.o"
        src.write_text(cpp_text, encoding="utf-8")
        res = compile_tu_armv6k(src, obj)
        if res.returncode != 0:
            raise RuntimeError(f"compile failed:\n{res.stderr}")
        return patch_cand_elf(obj)


def write_rec(uc: Uc, idx: int, seq_id: int, f1: int, f2: int, scene_type: int, cond_id: int) -> None:
    base = TABLE_ADDR + idx * 26
    buf = bytearray(26)
    struct.pack_into("<HHHHh", buf, 0x10, seq_id, f1, f2, scene_type, cond_id)
    uc.mem_write(base, bytes(buf))


def run_one(code_bytes: bytes, rodata_blobs: list[tuple[int, bytes]], case: dict) -> dict:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(0x000F0000, 0x00010000)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    uc.mem_write(FUNC_ADDR, code_bytes)
    for base, blob in rodata_blobs:
        uc.mem_write(base, blob)
    for stub_addr in NAME_BY_STUB:
        uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))
    uc.mem_write(HALT_ADDR, struct.pack("<I", 0xE12FFF1E))

    uc.mem_write(G_STATE_ADDR, struct.pack("<BBHIIIII",
        0,
        case.get("g1", 0),
        0,
        STATE_OBJ_ADDR,
        case.get("scene_id", 1),
        case.get("scene_a2", 0xAA),
        case.get("quick_mode", 0),
        0,
    ))
    uc.mem_write(STATE_OBJ_ADDR, b"\x00" * 0x20)
    uc.mem_write(STATE_OBJ_ADDR + 0x19, bytes([case["state"]]))
    vm_init_ptr = 0 if case.get("vm_null") else VM_ADDR
    uc.mem_write(STATE_OBJ_ADDR + 0x1C, struct.pack("<I", vm_init_ptr))
    uc.mem_write(VM_ADDR, struct.pack("<I", case.get("vm_flags", 0)))

    uc.mem_write(G_SYS_PTR_ADDR + 0x2FC, struct.pack("<I", 0x1000))

    # 3 table records at 0x0044DBB0
    write_rec(uc, 0, 0x10, 0x0001, 0x0000, 0, 99)  # never matches unless scene_id==99
    write_rec(uc, 1, 0x20, 0xFFFF, 0x0000, 1, 2)   # matches scene_type==1, scene_id==2
    write_rec(uc, 2, 0x30, 0x0111, 0x0222, 3, -1)  # matches scene_type==3, any scene_id

    trace: list[tuple] = []
    vm_flags_map = case.get("flags", {})

    def hook_code(uc_inst, address, size, user_data):
        name = NAME_BY_STUB.get(address)
        if name is None:
            return
        r0 = uc_inst.reg_read(UC_ARM_REG_R0)
        r1 = uc_inst.reg_read(UC_ARM_REG_R1)
        r2 = uc_inst.reg_read(UC_ARM_REG_R2)
        r3 = uc_inst.reg_read(UC_ARM_REG_R3)
        if name == "script_vm_func_002c0ba8":
            trace.append((name, r0))
            uc_inst.reg_write(UC_ARM_REG_R0, vm_flags_map.get(r0, 0))
        elif name == "script_vm_func_002990bc":
            trace.append((name, r0))
            uc_inst.reg_write(UC_ARM_REG_R0, vm_flags_map.get(r0, 0))
        elif name == "engine_func_0028796c":
            trace.append((name, r0))
            uc_inst.reg_write(UC_ARM_REG_R0, 77)
        elif name == "engine_func_00287958":
            trace.append((name, r0, r1))
            uc_inst.reg_write(UC_ARM_REG_R0, case.get("bgm_check", 0))
        elif name == "ui_func_002876d0":
            trace.append((name, r0))
            uc_inst.reg_write(UC_ARM_REG_R0, case.get("bg_loaded", 0))
        elif name == "AsdMemory_func_002c23f8":
            trace.append((name, r0))
            uc_inst.reg_write(UC_ARM_REG_R0, 0 if case.get("alloc_null") else VM_ADDR)
        elif name == "engine_func_0028757c":
            trace.append((name, r0))
            uc_inst.reg_write(UC_ARM_REG_R0, r0)
        elif name == "engine_func_00384304":
            trace.append((name, r0, r1, r2, r3))
        elif name == "AsdSequence_func_002c59b8":
            data = bytes(uc_inst.mem_read(r1, r2)) if (r1 and r2) else b""
            trace.append((name, r0, r2, data))
        elif name == "engine_func_002bf86c":
            trace.append((name, r1))
            uc_inst.mem_write(r0, b"\x55" * 0x18)
        elif name == "engine_func_00385488":
            trace.append((name, r0))
            uc_inst.reg_write(UC_ARM_REG_R0, case.get("skip_seq", 0))
        elif name == "engine_func_0028756c":
            trace.append((name,))
            uc_inst.reg_write(UC_ARM_REG_R0, case.get("has_seq", 0))
        elif name == "engine_func_0028753c":
            trace.append((name,))
            uc_inst.reg_write(UC_ARM_REG_R0, case.get("seq_type", 0))
        elif name in ("ui_func_002a0678",):
            trace.append((name, r0, r1))
        elif name in ("engine_func_00287790", "engine_func_00287590", "engine_func_00384ac8", "script_vm_func_002a72fc", "engine_func_002b2520"):
            trace.append((name, r0))
        else:
            trace.append((name,))

    uc.hook_add(UC_HOOK_CODE, hook_code)
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)
    uc.emu_start(FUNC_ADDR, HALT_ADDR, timeout=5_000_000, count=20_000)

    ret = uc.reg_read(UC_ARM_REG_R0)
    st_after = uc.mem_read(STATE_OBJ_ADDR + 0x18, 2)
    vm_after = struct.unpack("<I", uc.mem_read(STATE_OBJ_ADDR + 0x1C, 4))[0]
    return {"ret": ret, "st": bytes(st_after), "vm": vm_after, "trace": trace}


def build_cases() -> list[dict]:
    return [
        {"name": "st0_quick_mode", "state": 0, "scene_id": 1, "quick_mode": 1},
        {"name": "st0_scene1_bg_loaded", "state": 0, "scene_id": 1, "bg_loaded": 1},
        {"name": "st0_scene9_alloc_null", "state": 0, "scene_id": 9, "bg_loaded": 0, "alloc_null": True},
        {"name": "st0_scene2_bgm_rec_ffff", "state": 0, "scene_id": 2, "bgm_check": 1, "flags": {0x235: 1, 0x1C0: 1, 0x424: 1, 0x65: 1, 0x66: 1, 0x67: 1}},
        {"name": "st0_scene12_rec_flag", "state": 0, "scene_id": 12, "flags": {0x111: 1, 0x222: 0}},
        {"name": "st1_wait", "state": 1, "vm_flags": 0},
        {"name": "st1_done", "state": 1, "vm_flags": 1},
        {"name": "st2_nonnull", "state": 2, "vm_null": False},
        {"name": "st2_null", "state": 2, "vm_null": True},
        {"name": "st3_skip_seq", "state": 3, "skip_seq": 1, "has_seq": 1},
        {"name": "st3_seq_e", "state": 3, "skip_seq": 0, "has_seq": 1, "seq_type": 1},
        {"name": "st3_seq_6", "state": 3, "skip_seq": 0, "has_seq": 1, "seq_type": 0},
        {"name": "st4_flag1", "state": 4, "g1": 1},
        {"name": "st4_flag0", "state": 4, "g1": 0},
        {"name": "st5_default", "state": 5},
    ]


def verify(cpp_text: str) -> tuple[bool, int, str]:
    cand_code, rodata_blobs, cand_size = compile_candidate(cpp_text)
    with open(CODE_BIN, "rb") as f:
        f.seek(FUNC_ADDR - CODE_BASE)
        orig_code = patch_orig_bl(f.read(FUNC_SIZE))

    for case in build_cases():
        orig_res = run_one(orig_code, [], case)
        cand_res = run_one(cand_code, rodata_blobs, case)
        if orig_res != cand_res:
            return False, cand_size, f"FAIL {case['name']}:\n  orig={orig_res}\n  cand={cand_res}"
    return True, cand_size, "OK"


def run_negative_controls(cpp_text: str) -> None:
    mutations = [
        ("wrong_scene_map_12", "case 12:\n        case 13:", "case 14:\n        case 13:"),
        ("wrong_rec_stride", "table + i * 26u;", "table + i * 24u;"),
        ("wrong_vm_offset", "vm + 0x658u) - 0x658u;", "vm + 0x650u) - 0x650u;"),
        ("wrong_seq_sub", "0x2FCu) - 0xC8u;", "0x2FCu) - 0xC0u;"),
        ("wrong_st4_ret", "return -1;\n        }\n        default:", "return 0;\n        }\n        default:"),
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
