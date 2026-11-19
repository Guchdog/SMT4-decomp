#!/usr/bin/env python3
"""Differential test for engine_func_002f5348 (0x002f5348) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_002f5348"

FUNC_ADDR = 0x002F5348
FUNC_SIZE = 572

STUBS = {
    0x0024ADA8: "engine_func_0024ada8",
    0x0024ACF0: "engine_func_0024acf0",
    0x002CBF38: "engine_func_002cbf38",
    0x001FF988: "engine_func_001ff988",
    0x00210188: "engine_func_00210188",
    0x001FF88C: "engine_func_001ff88c",
    0x001FFA08: "engine_func_001ffa08",
    0x0024AC80: "engine_func_0024ac80",
    0x0024AC48: "engine_func_0024ac48",
    0x0024AC10: "engine_func_0024ac10",
    0x0024ACB8: "engine_func_0024acb8",
    0x002BB9C8: "engine_func_002bb9c8",
}

ADDR_VTT = 0x00420768
VTBL0_ADDR = 0x20001000
RODATA_BASE = 0x18000000
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
            if name == "engine_func_002f5348":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None or fn_size is None:
        raise RuntimeError("candidate symbol engine_func_002f5348 not found")

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
                    addend = struct.unpack_from("<I", text_data, r_off)[0]
                    if st_shndx in sec_addr:
                        struct.pack_into("<I", text_data, r_off, sec_addr[st_shndx] + st_value + addend)
                    elif st_shndx == tidx:
                        struct.pack_into("<I", text_data, r_off, (0x00180000 - fn_off) + st_value + addend)

    return bytes(text_data[fn_off : fn_off + fn_size]), rodata, relocs


def patch_bl(code: bytearray, at_off: int, src_pc: int, dst_pc: int) -> None:
    delta = (dst_pc - (src_pc + 8)) >> 2
    hi = code[at_off + 3]
    insn = (hi << 24) | (delta & 0x00FFFFFF)
    struct.pack_into("<I", code, at_off, insn)


def run_one(
    code_bytes: bytes,
    base_addr: int,
    cand_rodata: bytes | None,
    relocs: list[tuple[str, int]] | None,
    kind: int,
    path_arg: int,
    off_arg: int,
    sz_arg: int,
    open_ret: int,
    act_ret: int,
    close_ret: int,
) -> tuple[int, list[tuple], dict[str, int]]:
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

    # VTT at 0x00420768, with vtbl0[-0x30] = 0x18 (offset 24 inside 28-byte object)
    vtt = bytearray(0x30)
    struct.pack_into("<I", vtt, 0x00, VTBL0_ADDR)
    struct.pack_into("<I", vtt, 0x20, 0xAAAA1111)
    struct.pack_into("<I", vtt, 0x24, 0xBBBB2222)
    uc.mem_write(ADDR_VTT, bytes(vtt))
    uc.mem_write(VTBL0_ADDR - 0x30, struct.pack("<i", 0x18))

    uc.reg_write(arm.UC_ARM_REG_R0, kind)
    uc.reg_write(arm.UC_ARM_REG_R1, path_arg)
    uc.reg_write(arm.UC_ARM_REG_R2, off_arg)
    uc.reg_write(arm.UC_ARM_REG_R3, sz_arg)
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for name, val in CALLEE_SAVED.items():
        uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), val)

    calls: list[tuple] = []

    def hook_code(uc_inst, address, size, user_data):
        tag = STUBS.get(address)
        if tag is None:
            return
        r0 = uc_inst.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc_inst.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc_inst.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc_inst.reg_read(arm.UC_ARM_REG_R3)
        obj_words = struct.unpack_from("<7I", uc_inst.mem_read(r0, 28))
        if tag in ("engine_func_0024ada8", "engine_func_0024acf0", "engine_func_002cbf38", "engine_func_001ff988"):
            calls.append((tag, obj_words, r1, r2))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, open_ret)
        elif tag in ("engine_func_00210188", "engine_func_001ff88c", "engine_func_001ffa08"):
            calls.append((tag, obj_words, r1, r2, r3))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, act_ret)
        elif tag in ("engine_func_0024ac80", "engine_func_0024ac48", "engine_func_0024ac10", "engine_func_0024acb8"):
            calls.append((tag, obj_words))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, close_ret)
        elif tag == "engine_func_002bb9c8":
            calls.append((tag, obj_words, r1))

    for addr in STUBS:
        uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=addr, end=addr)

    uc.emu_start(base_addr, LR_SENTINEL, count=50000)

    ret = uc.reg_read(arm.UC_ARM_REG_R0)
    regs = {
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        **{n: uc.reg_read(getattr(arm, f"UC_ARM_REG_{n.upper()}")) for n in CALLEE_SAVED},
    }
    return ret, calls, regs


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    orig_code = orig_all[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    cand_code, cand_rodata, cand_relocs = compile_candidate()

    cases = [
        ("k0_all_ok", 0, 0x20003000, 0x100, 0x200, 0, 0, 0),
        ("k0_open_fail", 0, 0x20003000, 0x100, 0x200, 0x80000001, 0, 0),
        ("k0_act_fail", 0, 0x20003000, 0x100, 0x200, 0, 0x80000001, 0),
        ("k0_close_fail", 0, 0x20003000, 0x100, 0x200, 0, 0, 0x80000001),
        ("k1_all_ok", 1, 0x20003000, 0x300, 0x400, 0, 0, 0),
        ("k1_act_fail", 1, 0x20003000, 0x300, 0x400, 0, 0x80000001, 0),
        ("k2_open_ok", 2, 0x20003000, 0x500, 0x600, 0, 0, 0),
        ("k3_all_ok", 3, 0x20003000, 0x700, 0x800, 0, 0, 0),
        ("k3_act_fail", 3, 0x20003000, 0x700, 0x800, 0, 0x80000001, 0),
        ("k4_invalid", 4, 0x20003000, 0x100, 0x200, 0, 0, 0),
    ]

    for name, *args in cases:
        o_ret, o_calls, o_regs = run_one(orig_code, FUNC_ADDR, None, None, *args)
        c_ret, c_calls, c_regs = run_one(cand_code, 0x00180000, cand_rodata, cand_relocs, *args)
        if o_ret != c_ret:
            print(f"FAIL {name}: ret orig={o_ret} cand={c_ret}")
            return 1
        if o_calls != c_calls:
            print(f"FAIL {name}: calls mismatch\n  orig={o_calls}\n  cand={c_calls}")
            return 1
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            print(f"FAIL {name}: regs mismatch")
            return 1

    # 5 negative / mutation controls
    ref = run_one(orig_code, FUNC_ADDR, None, None, *cases[0][1:])[:2]
    mutants = [
        ("mut_open_fail", cases[1][1:]),
        ("mut_act_fail", cases[2][1:]),
        ("mut_close_fail", cases[3][1:]),
        ("mut_k1", cases[4][1:]),
        ("mut_k2", cases[6][1:]),
    ]
    detected = 0
    for mname, margs in mutants:
        cur = run_one(cand_code, 0x00180000, cand_rodata, cand_relocs, *margs)[:2]
        if cur != ref:
            detected += 1
        else:
            print(f"FAIL mutant not detected: {mname}")
            return 1

    print(
        f"PASS: engine_func_002f5348 (0x002f5348) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
