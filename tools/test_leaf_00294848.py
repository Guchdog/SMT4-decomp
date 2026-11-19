#!/usr/bin/env python3
"""Differential test for engine_func_00294848 (0x00294848) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_00294848"

FUNC_ADDR = 0x00294848
FUNC_SIZE = 540

STUBS = {
    0x002B47CC: "engine_func_002b47cc",
    0x0023D04C: "engine_func_0023d04c",
    0x002BE7FC: "ui_func_002be7fc",
    0x0023F440: "engine_func_0023f440",
    0x002B66EC: "script_vm_func_002b66ec",
}

RODATA_BASE = 0x18000000
OBJ_ADDR = 0x20000000
ITEM_BASE = 0x20001000
DEFAULTS_ADDR = 0x20002000
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


def make_stub_thumb_bx_lr() -> bytes:
    return struct.pack("<HH", 0x4770, 0x46C0)


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
            if name == "engine_func_00294848":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None or fn_size is None:
        raise RuntimeError("candidate symbol engine_func_00294848 not found")

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


def read_cstr(uc: unicorn.Uc, ptr: int, max_len: int = 64) -> bytes:
    raw = bytes(uc.mem_read(ptr, max_len))
    nul = raw.find(b"\x00")
    return raw[:nul] if nul >= 0 else raw


def run_one(
    code_bytes: bytes,
    base_addr: int,
    cand_rodata: bytes | None,
    relocs: list[tuple[str, int]] | None,
    slot: int,
    item_id: int,
    arg3: int,
    item_types: dict[int, tuple[int, int, int]],
) -> tuple[list[tuple], dict[str, int]]:
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
        if addr == 0x002BE7FC and relocs is None:
            uc.mem_write(addr, make_stub_thumb_bx_lr())
        else:
            uc.mem_write(addr, make_stub_bx_lr())

    defs = bytearray(0x20)
    struct.pack_into("<HHH", defs, 6, 10, 0, 12)
    uc.mem_write(DEFAULTS_ADDR, bytes(defs))

    uc.reg_write(arm.UC_ARM_REG_R0, OBJ_ADDR)
    uc.reg_write(arm.UC_ARM_REG_R1, slot)
    uc.reg_write(arm.UC_ARM_REG_R2, item_id)
    uc.reg_write(arm.UC_ARM_REG_R3, arg3)
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
        if tag == "engine_func_002b47cc":
            calls.append((tag, r0))
            tp, v70, v72 = item_types[r0]
            iaddr = ITEM_BASE + r0 * 0x80
            ibuf = bytearray(0x80)
            ibuf[0x52] = tp
            struct.pack_into("<HH", ibuf, 0x70, v70, v72)
            uc_inst.mem_write(iaddr, bytes(ibuf))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, iaddr)
        elif tag == "engine_func_0023d04c":
            sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
            s0 = struct.unpack_from("<I", uc_inst.mem_read(sp, 4))[0]
            calls.append((tag, r0, r1, r2, r3, s0))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, 7)
        elif tag == "ui_func_002be7fc":
            fmt = read_cstr(uc_inst, r1).decode("ascii")
            sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
            if fmt.count("%") == 3:
                s0 = struct.unpack_from("<I", uc_inst.mem_read(sp, 4))[0]
                text = (fmt % (r2, r3, s0)).encode("ascii")
            else:
                text = (fmt % (r2, r3)).encode("ascii")
            uc_inst.mem_write(r0, text + b"\x00")
            calls.append((tag, text))
        elif tag == "engine_func_0023f440":
            calls.append((tag, r0, r1, read_cstr(uc_inst, r2), r3))
        elif tag == "script_vm_func_002b66ec":
            calls.append((tag,))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, DEFAULTS_ADDR)

    for addr in STUBS:
        uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=addr, end=addr)

    uc.emu_start(base_addr, LR_SENTINEL, count=50000)

    regs = {
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        **{n: uc.reg_read(getattr(arm, f"UC_ARM_REG_{n.upper()}")) for n in CALLEE_SAVED},
    }
    return calls, regs


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    orig_code = orig_all[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    cand_code, cand_rodata, cand_relocs = compile_candidate()

    items = {
        1: (4, 1, 20),
        2: (5, 2, 30),
        3: (6, 3, 40),
        4: (9, 4, 50),
        10: (4, 5, 60),
        12: (6, 6, 70),
    }

    cases = [
        ("slot0_ok", 0, 1, 0x111, items),
        ("slot0_bad_type", 0, 2, 0x111, items),
        ("slot1_ok", 1, 2, 0x222, items),
        ("slot1_bad_type", 1, 1, 0x222, items),
        ("slot2_ok", 2, 3, 0x333, items),
        ("slot2_bad_type", 2, 1, 0x333, items),
    ]

    for name, *args in cases:
        o_calls, o_regs = run_one(orig_code, FUNC_ADDR, None, None, *args)
        c_calls, c_regs = run_one(cand_code, 0x00180000, cand_rodata, cand_relocs, *args)
        if o_calls != c_calls:
            print(f"FAIL {name}: calls mismatch\n  orig={o_calls}\n  cand={c_calls}")
            return 1
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            print(f"FAIL {name}: regs mismatch")
            return 1

    # 5 negative / mutation controls
    ref_calls, _ = run_one(orig_code, FUNC_ADDR, None, None, 1, 2, 0x222, items)
    mutants = [
        ("mut_slot0", (0, 1, 0x222, items)),
        ("mut_slot2", (2, 3, 0x222, items)),
        ("mut_bad_type", (1, 1, 0x222, items)),
        ("mut_arg3", (1, 2, 0x999, items)),
        ("mut_item_vals", (1, 2, 0x222, {**items, 2: (5, 9, 99)})),
    ]
    detected = 0
    for mname, margs in mutants:
        m_calls, _ = run_one(cand_code, 0x00180000, cand_rodata, cand_relocs, *margs)
        if m_calls != ref_calls:
            detected += 1
        else:
            print(f"FAIL mutant not detected: {mname}")
            return 1

    print(
        f"PASS: engine_func_00294848 (0x00294848) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
