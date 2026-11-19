#!/usr/bin/env python3
"""Differential test for engine_func_00111090 (0x00111090) with Unicorn ARM."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SOURCE = ROOT / "src" / "engine" / "leaf_batch45_b.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_00111090"

FUNC_ADDR = 0x00111090
FUNC_SIZE = 556

STUBS = {
    0x0011B850: "engine_func_0011b850",
    0x0011B838: "engine_func_0011b838",
    0x002BAC24: "engine_func_002bac24",
    0x002BAC28: "engine_func_002bac28",
    0x00121EC4: "engine_func_00121ec4",
    0x002C541C: "engine_func_002c541c",
    0x00121ED8: "engine_func_00121ed8",
    0x002BB09C: "engine_func_002bb09c",
    0x002BAD80: "engine_func_002bad80",
    0x00126EDC: "script_vm_func_00126edc",
    0x002C4B30: "engine_func_002c4b30",
    0x002BAB5C: "engine_func_002bab5c",
    0x00121E08: "aocThread_func_00121e08",
    0x0012701C: "engine_func_0012701c",
    0x002BAACC: "engine_func_002baacc",
    0x002C5978: "engine_func_002c5978",
}

RODATA_BASE = 0x18000000
OBJ_ADDR = 0x20000000
STACK_BASE = 0x7F000000
STACK_SIZE = 0x10000
STACK_INIT = STACK_BASE + STACK_SIZE - 0x200
LR_SENTINEL = 0x90000000

CALLEE_SAVED = {
    "r4": 0x44444444,
    "r5": 0x55555555,
    "r6": 0x66666666,
    "r7": 0x77777777,
    "r8": 0x88888888,
    "r9": 0x99999999,
    "r10": 0xAAAAAAAA,
    "r11": 0xBBBBBBBB,
}


def make_stub_bx_lr() -> bytes:
    return struct.pack("<I", 0xE12FFF1E)


def _layout_rodata(obj_file: Path) -> tuple[bytes, dict[int, int]]:
    data = obj_file.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 46)
    raw_secs = [struct.unpack_from("<10I", data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr_off = raw_secs[e_shstrndx][4]
    names = [data[shstr_off + s[0] : data.index(b"\x00", shstr_off + s[0])].decode("ascii", errors="replace") for s in raw_secs]

    image = bytearray()
    sec_addr: dict[int, int] = {}
    for i, s in enumerate(raw_secs):
        if s[1] == 1 and (s[2] & 2) and not names[i].startswith(".text"):
            align = max(s[8], 1)
            while len(image) % align:
                image.append(0)
            sec_addr[i] = RODATA_BASE + len(image)
            image.extend(data[s[4] : s[4] + s[5]])

    for i, s in enumerate(raw_secs):
        if s[1] == 9 and s[7] in sec_addr:
            target_off = sec_addr[s[7]] - RODATA_BASE
            symtab = raw_secs[s[6]]
            for k in range(s[5] // 8):
                r_off, r_info = struct.unpack_from("<II", data, s[4] + k * 8)
                sym_idx, r_type = r_info >> 8, r_info & 0xFF
                if r_type == 2:
                    st_shndx = struct.unpack_from("<H", data, symtab[4] + sym_idx * 16 + 14)[0]
                    if st_shndx in sec_addr:
                        val = struct.unpack_from("<I", image, target_off + r_off)[0]
                        struct.pack_into("<I", image, target_off + r_off, sec_addr[st_shndx] + val)

    return bytes(image), sec_addr


def compile_candidate() -> tuple[bytes, bytes, list[tuple[str, int]]]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_path = OUT_DIR / "leaf_batch45_b.o"
    res = compile_tu_armv6k(SOURCE, obj_path)
    if res.returncode != 0:
        raise RuntimeError(f"compile failed:\n{res.stderr}\n{res.stdout}")

    rodata, sec_addr = _layout_rodata(obj_path)
    data = obj_path.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 46)
    secs = [struct.unpack_from("<10I", data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr_off = secs[e_shstrndx][4]
    sec_names = [data[shstr_off + s[0] : data.index(b"\x00", shstr_off + s[0])].decode("ascii", errors="replace") for s in secs]
    tidx = sec_names.index(".text")
    text_data = bytearray(data[secs[tidx][4] : secs[tidx][4] + secs[tidx][5]])

    symtab = next(s for s in secs if s[1] == 2)
    strtab_off = secs[symtab[6]][4]
    fn_off = fn_size = None
    for idx in range(symtab[5] // 16):
        st_name, st_value, st_size, _st_info, _st_other, st_shndx = struct.unpack_from("<IIIbbH", data, symtab[4] + idx * 16)
        if st_shndx == tidx:
            name = data[strtab_off + st_name : data.index(b"\x00", strtab_off + st_name)].decode("ascii", errors="replace")
            if name == "engine_func_00111090":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None or fn_size is None:
        raise RuntimeError("candidate symbol engine_func_00111090 not found")

    relocs: list[tuple[str, int]] = []
    for s in secs:
        if s[1] == 9 and s[7] == tidx:
            for k in range(s[5] // 8):
                r_off, r_info = struct.unpack_from("<II", data, s[4] + k * 8)
                sym_idx, r_type = r_info >> 8, r_info & 0xFF
                if not (fn_off <= r_off < fn_off + fn_size):
                    continue
                if r_type in (28, 29):
                    st_name = struct.unpack_from("<I", data, symtab[4] + sym_idx * 16)[0]
                    sname = data[strtab_off + st_name : data.index(b"\x00", strtab_off + st_name)].decode("ascii", errors="replace")
                    relocs.append((sname, r_off - fn_off))
                elif r_type == 2:
                    st_value, _, _, _, st_shndx = struct.unpack_from("<IIbbH", data, symtab[4] + sym_idx * 16 + 4)
                    if st_shndx in sec_addr:
                        addend = struct.unpack_from("<I", text_data, r_off)[0]
                        struct.pack_into("<I", text_data, r_off, sec_addr[st_shndx] + st_value + addend)

    return bytes(text_data[fn_off : fn_off + fn_size]), rodata, relocs


def patch_bl(code: bytearray, at_off: int, src_pc: int, dst_pc: int) -> None:
    delta = (dst_pc - (src_pc + 8)) >> 2
    hi = code[at_off + 3]
    insn = (hi << 24) | (delta & 0x00FFFFFF)
    struct.pack_into("<I", code, at_off, insn)


def read_cstr(uc: unicorn.Uc, ptr: int, max_len: int = 32) -> bytes:
    raw = bytes(uc.mem_read(ptr, max_len))
    nul = raw.find(b"\x00")
    return raw[:nul] if nul >= 0 else raw


def run_one(
    code_bytes: bytes,
    base_addr: int,
    cand_rodata: bytes | None,
    relocs: list[tuple[str, int]] | None,
    v1_lo: int,
    v1_hi: int,
    v2_lo: int,
    v2_hi: int,
    task_id: int,
    ts_lo: int,
) -> tuple[int, bytes, list[tuple], dict[str, int]]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.mem_map(0x00100000, 0x00400000)
    uc.mem_map(RODATA_BASE, 0x00100000)
    uc.mem_map(0x20000000, 0x00010000)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    if cand_rodata is not None:
        uc.mem_write(RODATA_BASE, cand_rodata)

    buf = bytearray(code_bytes)
    if relocs is not None:
        name_to_addr = {v: k for k, v in STUBS.items()}
        for sym_name, off in relocs:
            target = name_to_addr.get(sym_name)
            if target is None:
                raise RuntimeError(f"unexpected relocation: {sym_name}")
            patch_bl(buf, off, base_addr + off, target)

    uc.mem_write(base_addr, bytes(buf))
    for addr in STUBS:
        uc.mem_write(addr, make_stub_bx_lr())

    uc.mem_write(OBJ_ADDR, b"\x5A" * 0xE00)

    uc.reg_write(arm.UC_ARM_REG_R0, OBJ_ADDR)
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for name, val in CALLEE_SAVED.items():
        uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), val)

    calls: list[tuple] = []
    edc_idx = 0

    def hook_code(uc_inst, address, size, user_data):
        nonlocal edc_idx
        tag = STUBS.get(address)
        if tag is None:
            return
        r0 = uc_inst.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc_inst.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc_inst.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc_inst.reg_read(arm.UC_ARM_REG_R3)
        if tag in (
            "engine_func_0011b850",
            "engine_func_0011b838",
            "engine_func_002bac24",
            "engine_func_002bac28",
            "engine_func_00121ec4",
            "engine_func_00121ed8",
            "engine_func_002bb09c",
            "engine_func_0012701c",
            "engine_func_002baacc",
        ):
            calls.append((tag, r0))
        elif tag in ("engine_func_002c541c", "engine_func_002c4b30", "aocThread_func_00121e08"):
            calls.append((tag, r0, r1))
        elif tag == "engine_func_002bad80":
            calls.append((tag, r1))
            uc_inst.mem_write(r0, struct.pack("<II", ts_lo, 0xCAFEBABE))
        elif tag == "script_vm_func_00126edc":
            calls.append((tag, r0))
            if edc_idx == 0:
                uc_inst.reg_write(arm.UC_ARM_REG_R0, v1_lo)
                uc_inst.reg_write(arm.UC_ARM_REG_R1, v1_hi)
            elif edc_idx == 1:
                uc_inst.reg_write(arm.UC_ARM_REG_R0, v2_lo)
                uc_inst.reg_write(arm.UC_ARM_REG_R1, v2_hi)
            else:
                uc_inst.reg_write(arm.UC_ARM_REG_R0, 0)
                uc_inst.reg_write(arm.UC_ARM_REG_R1, 0)
            edc_idx += 1
        elif tag == "engine_func_002bab5c":
            calls.append((tag, r0, read_cstr(uc_inst, r1), r2))
        elif tag == "engine_func_002c5978":
            sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
            s0, s1, s2 = struct.unpack_from("<III", uc_inst.mem_read(sp, 12))
            calls.append((tag, read_cstr(uc_inst, r0), r1, r2, r3, s0, s1, s2))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, task_id)

    for addr in STUBS:
        uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=addr, end=addr)

    uc.emu_start(base_addr, LR_SENTINEL, count=50000)

    ret = uc.reg_read(arm.UC_ARM_REG_R0)
    out_obj = bytes(uc.mem_read(OBJ_ADDR, 0xE00))
    regs = {
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        **{n: uc.reg_read(getattr(arm, f"UC_ARM_REG_{n.upper()}")) for n in CALLEE_SAVED},
    }
    return ret, out_obj, calls, regs


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    orig_code = orig_all[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    cand_code, cand_rodata, cand_relocs = compile_candidate()

    cases = [
        ("case_a", 0x11112222, 0xABCD9999, 0x12345678, 0x77778888, 0x501, 0x11223344),
        ("case_b", 0x00000000, 0x0000FFFF, 0xFFFF0000, 0xFFFFFFFF, 0x502, 0x99887766),
        ("case_c", 0xFFFFFFFF, 0x80010000, 0x0001FFFF, 0x00000000, 0x503, 0xDEADBEEF),
    ]

    for name, *args in cases:
        o_ret, o_obj, o_calls, o_regs = run_one(orig_code, FUNC_ADDR, None, None, *args)
        c_ret, c_obj, c_calls, c_regs = run_one(cand_code, 0x00180000, cand_rodata, cand_relocs, *args)
        if o_ret != c_ret or o_obj != c_obj:
            print(f"FAIL {name}: ret/obj mismatch")
            return 1
        if o_calls != c_calls:
            print(f"FAIL {name}: calls mismatch\n  orig={o_calls}\n  cand={c_calls}")
            return 1
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            print(f"FAIL {name}: regs mismatch")
            return 1

    # 5 negative / mutation controls
    ref = run_one(orig_code, FUNC_ADDR, None, None, *cases[0][1:])[:3]
    mutants = [
        ("mut_v1_hi", (0x11112222, 0xABCE9999, 0x12345678, 0x77778888, 0x501, 0x11223344)),
        ("mut_v2_lo", (0x11112222, 0xABCD9999, 0x12355678, 0x77778888, 0x501, 0x11223344)),
        ("mut_task_id", (0x11112222, 0xABCD9999, 0x12345678, 0x77778888, 0x509, 0x11223344)),
        ("mut_ts_lo", (0x11112222, 0xABCD9999, 0x12345678, 0x77778888, 0x501, 0x11223345)),
        ("mut_case_b", cases[1][1:]),
    ]
    detected = 0
    for mname, margs in mutants:
        cur = run_one(cand_code, 0x00180000, cand_rodata, cand_relocs, *margs)[:3]
        if cur != ref:
            detected += 1
        else:
            print(f"FAIL mutant not detected: {mname}")
            return 1

    print(
        f"PASS: engine_func_00111090 (0x00111090) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
