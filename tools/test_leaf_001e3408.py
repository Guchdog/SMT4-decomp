#!/usr/bin/env python3
"""Differential Unicorn test for engine_func_001e3408 (0x001e3408, 1132 B)."""

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
    UC_ARM_REG_S0,
    UC_ARM_REG_S1,
    UC_ARM_REG_S2,
    UC_ARM_REG_SP,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k

CODE_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = ROOT / "src" / "engine" / "leaf_batch45_c.cpp"

FUNC_ADDR = 0x001E3408
FUNC_SIZE = 1132
FUNC_NAME = "engine_func_001e3408"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x000F4000
STACK_BASE = 0x02000000
STACK_SIZE = 0x00100000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

G_MGR_PTR = 0x00447E58
G_SYS_PTR = 0x00433158
MGR_ADDR = 0x004A0000
SYS_ADDR = 0x004A2000
RECS_ADDR = 0x004A3000
INFOS_ADDR = 0x004A4000
OBJ_ADDR = 0x004A5000
SUB_OBJ_ADDR = 0x004A5100
CLONE_SRC_ADDR = 0x004A5200
HALT_ADDR = 0x004FFFF0

CALLEES = {
    0x0031B928: "engine_func_0031b928",
    0x002F4754: "engine_func_002f4754",
    0x002DFFD8: "engine_func_002dffd8",
    0x001E32F0: "engine_func_001e32f0",
    0x002FB468: "engine_func_002fb468",
    0x0026715C: "engine_func_0026715c",
    0x0025C110: "engine_func_0025c110",
    0x00316EAC: "engine_func_00316eac",
    0x002BE7FC: "ui_func_002be7fc",
    0x0028549C: "engine_func_0028549c",
    0x0029A2D0: "engine_func_0029a2d0",
    0x002AE16C: "engine_func_002ae16c",
    0x002A06C8: "engine_func_002a06c8",
    0x0025C0F0: "engine_func_0025c0f0",
    0x0021E070: "engine_func_0021e070",
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
        if top in (0xEA, 0xEB, 0xFA, 0xFB):
            imm24 = insn & 0x00FFFFFF
            if imm24 & 0x00800000:
                imm24 -= 0x01000000
            h_bit = (top & 1) if top >= 0xFA else 0
            pc = FUNC_ADDR + off
            target = (pc + 8 + imm24 * 4 + h_bit * 2) & ~3
            if target in CALLEES:
                stub = STUB_BY_NAME[CALLEES[target]]
                rel = ((stub - (pc + 8)) // 4) & 0x00FFFFFF
                op = 0xEA000000 if top == 0xEA else 0xEB000000
                struct.pack_into("<I", buf, off, op | rel)
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


def write_npc_info(uc: Uc, idx: int, a0: int, a1: int, t1: int, t2: int, npc_type: int, kind: int) -> None:
    buf = bytearray(0x38)
    struct.pack_into("<hhhh", buf, 0, a0, a1, t1, t2)
    struct.pack_into("<hhhhh", buf, 0x28, kind, 10, 20, 30, 40)
    buf[0x32] = 7
    buf[0x33] = npc_type
    uc.mem_write(INFOS_ADDR + idx * 0x40, bytes(buf))


def run_one(code_bytes: bytes, rodata_blobs: list[tuple[int, bytes]], case: dict) -> dict:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x000F0000, 0x00010000)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    uc.mem_write(FUNC_ADDR, code_bytes)
    for base, blob in rodata_blobs:
        uc.mem_write(base, blob)
    for stub_addr in NAME_BY_STUB:
        uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))
    uc.mem_write(HALT_ADDR, struct.pack("<I", 0xE12FFF1E))

    uc.mem_write(G_MGR_PTR, struct.pack("<I", MGR_ADDR))
    uc.mem_write(G_SYS_PTR, struct.pack("<I", SYS_ADDR))
    uc.mem_write(MGR_ADDR, b"\x00" * 0x1000)
    uc.mem_write(MGR_ADDR + 0x00, struct.pack("<iii", case["state"], case.get("idx", 0), case.get("slot_idx", 0)))
    uc.mem_write(MGR_ADDR + 0x3C, struct.pack("<I", CLONE_SRC_ADDR))

    if case.get("dup_slot1"):
        uc.mem_write(MGR_ADDR + 0x0C + 56, bytes([1]))
        uc.mem_write(MGR_ADDR + 0x0C + 56 + 8, struct.pack("<h", 0))

    slot_addr = MGR_ADDR + 0x0C + case.get("slot_idx", 0) * 56
    uc.mem_write(slot_addr + 0x30, struct.pack("<I", OBJ_ADDR))
    uc.mem_write(OBJ_ADDR + 8, struct.pack("<I", SUB_OBJ_ADDR))

    # State 0 records (4 records)
    recs = [(10, 20, 0), (1, 2, 3), (0x000F423E, 0, 0), (99, 99, 0)]
    for i, (x0, x1, x2) in enumerate(recs):
        uc.mem_write(RECS_ADDR + i * 16, struct.pack("<iii", x0, x1, x2))

    # NPC infos
    write_npc_info(uc, 0, case.get("i0_a", 10), 20, 1, 2, case.get("npc_type", 0x13), case.get("kind", 1))
    write_npc_info(uc, 1, 10, 20, 3, 4, 0x13, 2)
    write_npc_info(uc, 2, -1, 0, 0, 0, 0, 0)
    write_npc_info(uc, 3, -1, 0, 0, 0, 0, 0)

    trace: list[tuple] = []

    def hook_code(uc_inst, address, size, user_data):
        name = NAME_BY_STUB.get(address)
        if name is None:
            return
        r0 = uc_inst.reg_read(UC_ARM_REG_R0)
        r1 = uc_inst.reg_read(UC_ARM_REG_R1)
        if name == "engine_func_0031b928":
            uc_inst.reg_write(UC_ARM_REG_R0, 4)
        elif name == "engine_func_002f4754":
            uc_inst.reg_write(UC_ARM_REG_R0, RECS_ADDR + r0 * 16)
        elif name == "engine_func_002dffd8":
            s0 = struct.unpack("<f", struct.pack("<I", uc_inst.reg_read(UC_ARM_REG_S0)))[0]
            s1 = struct.unpack("<f", struct.pack("<I", uc_inst.reg_read(UC_ARM_REG_S1)))[0]
            s2 = struct.unpack("<f", struct.pack("<I", uc_inst.reg_read(UC_ARM_REG_S2)))[0]
            trace.append((name, s0, s1, s2))
        elif name == "engine_func_001e32f0":
            trace.append((name,))
        elif name == "engine_func_002fb468":
            uc_inst.reg_write(UC_ARM_REG_R0, case.get("npc_count", 4))
        elif name == "engine_func_0026715c":
            uc_inst.reg_write(UC_ARM_REG_R0, INFOS_ADDR + r0 * 0x40)
        elif name == "engine_func_0025c110":
            uc_inst.reg_write(UC_ARM_REG_R0, case.get("has_tail", 0))
        elif name == "engine_func_00316eac":
            trace.append((name, r0, r1))
            uc_inst.reg_write(UC_ARM_REG_R0, case.get("vis_ok", 1))
        elif name == "ui_func_002be7fc":
            fmt = uc_inst.mem_read(r1, 32).split(b"\x00", 1)[0].decode("ascii", errors="replace")
            r2 = uc_inst.reg_read(UC_ARM_REG_R2)
            s = fmt % r2
            uc_inst.mem_write(r0, s.encode("ascii") + b"\x00")
            trace.append((name, s))
        elif name == "engine_func_0028549c":
            trace.append((name, r0, r1))
            uc_inst.reg_write(UC_ARM_REG_R0, OBJ_ADDR)
        elif name == "engine_func_0029a2d0":
            s = uc_inst.mem_read(r0, 48).split(b"\x00", 1)[0].decode("ascii", errors="replace")
            trace.append((name, s, r1))
            uc_inst.reg_write(UC_ARM_REG_R0, OBJ_ADDR)
        elif name == "engine_func_002ae16c":
            trace.append((name, r0))
            uc_inst.reg_write(UC_ARM_REG_R0, case.get("loaded", 1))
        elif name == "engine_func_002a06c8":
            trace.append((name, r0, r1))
        elif name == "engine_func_0025c0f0":
            s0 = struct.unpack("<f", struct.pack("<I", uc_inst.reg_read(UC_ARM_REG_S0)))[0]
            s1 = struct.unpack("<f", struct.pack("<I", uc_inst.reg_read(UC_ARM_REG_S1)))[0]
            s2 = struct.unpack("<f", struct.pack("<I", uc_inst.reg_read(UC_ARM_REG_S2)))[0]
            trace.append((name, r0, r1, s0, s1, s2))
        elif name == "engine_func_0021e070":
            trace.append((name,))
            uc_inst.reg_write(UC_ARM_REG_R0, 0x77777777)

    uc.hook_add(UC_HOOK_CODE, hook_code)
    uc.reg_write(UC_ARM_REG_R0, case.get("target_a", 10) & 0xFFFFFFFF)
    uc.reg_write(UC_ARM_REG_R1, case.get("target_b", 20) & 0xFFFFFFFF)
    uc.reg_write(UC_ARM_REG_R2, case.get("mode", 0))
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)
    uc.emu_start(FUNC_ADDR, HALT_ADDR, timeout=5_000_000, count=20_000)

    ret = uc.reg_read(UC_ARM_REG_R0)
    hdr = struct.unpack("<iii", uc.mem_read(MGR_ADDR, 12))
    slot_mem = bytes(uc.mem_read(slot_addr, 56))
    return {"ret": ret, "hdr": hdr, "slot": slot_mem, "trace": trace}


def build_cases() -> list[dict]:
    return [
        {"name": "st0_mode1", "state": 0, "mode": 1},
        {"name": "st0_mode0_match", "state": 0, "mode": 0},
        {"name": "st1_end_sentinel_no_tail", "state": 1, "i0_a": -1, "has_tail": 0},
        {"name": "st1_end_sentinel_tail_ok", "state": 1, "idx": 3, "has_tail": 2, "npc_count": 5},
        {"name": "st1_match_mode0_clone", "state": 1, "target_a": 0x65, "i0_a": 0x65, "slot_idx": 1, "mode": 0},
        {"name": "st1_dup_skip_then_match", "state": 1, "mode": 1, "dup_slot1": True, "slot_idx": 2},
        {"name": "st2_wait_load", "state": 2, "loaded": 0},
        {"name": "st2_ready_type1_npc19", "state": 2, "loaded": 1, "kind": 1, "npc_type": 0x13},
        {"name": "st2_clone_type2_non19", "state": 2, "target_a": 0x65, "slot_idx": 1, "kind": 2, "npc_type": 0x12},
        {"name": "st3_default", "state": 3},
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
        ("wrong_sentinel_val", "if (sub_id == 0x000F423E) {", "if (sub_id == 0x000F423D) {"),
        ("wrong_slot_stride", "mgr + 0x0Cu + k * 56;", "mgr + 0x0Cu + k * 52;"),
        ("wrong_bam_fmt", '"character/npc/npc_%02d.bam"', '"character/npc/npc_%03d.bam"'),
        ("wrong_scale_50", "50.0f, 50.0f, 50.0f", "60.0f, 50.0f, 50.0f"),
        ("wrong_type_eq1", "if (type_val == 1) {", "if (type_val == 2) {"),
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
