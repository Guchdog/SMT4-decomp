#!/usr/bin/env python3
"""Differential test for engine_func_002350f4 (0x002350f4) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_002350f4"

FUNC_ADDR = 0x002350F4
FUNC_SIZE = 756

STUBS = {
    0x002C4B30: "engine_func_002c4b30",
    0x002BE7FC: "ui_func_002be7fc",
    0x0029BDDC: "engine_func_0029bddc",
    0x002A06C8: "engine_func_002a06c8",
    0x00341578: "engine_func_00341578",
    0x002A0C54: "engine_func_002a0c54",
    0x002A0790: "script_vm_func_002a0790",
    0x002A8948: "engine_func_002a8948",
    0x00100C4C: "crt_func_00100c4c",
    0x0028C8A8: "engine_func_0028c8a8",
}

SELF_ADDR = 0x20000000
NAME1_ADDR = 0x20002000
NAME2_ADDR = 0x20002100
P56C_ADDR = 0x20003000
P2A8_ADDR = 0x20003100
MOD1C_ADDR = 0x20004000
MOD20_ADDR = 0x20004100
MOD24_ADDR = 0x20004200
SUB8_ADDR = 0x20004300
SUB2C_ADDR = 0x20004400
NODE_ADDR = 0x20005000
GRP_ADDR = 0x20005200
ARR_ADDR = 0x20005400
ENTRY0_ADDR = 0x20006000
ENTRY1_ADDR = 0x20006100
RODATA_BASE = 0x00450000

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


def compile_candidate() -> tuple[bytes, list[tuple[str, int]], bytes, list[tuple[int, int, int]]]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_path = OUT_DIR / "leaf_batch45_b.o"
    res = compile_tu_armv6k(SOURCE, obj_path)
    if res.returncode != 0:
        raise RuntimeError(f"compile failed:\n{res.stderr}")

    data = obj_path.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 46)
    shdrs = [struct.unpack_from("<10I", data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr_off = shdrs[e_shstrndx][4]

    def sh_name(idx: int) -> str:
        off = shstr_off + shdrs[idx][0]
        return data[off : data.index(b"\x00", off)].decode("ascii", errors="replace")

    tidx = next(i for i in range(e_shnum) if sh_name(i) == ".text")
    text_data = data[shdrs[tidx][4] : shdrs[tidx][4] + shdrs[tidx][5]]
    symtab = next(s for s in shdrs if s[1] == 2)
    strtab_off = shdrs[symtab[6]][4]

    fn_off = fn_size = None
    for i in range(symtab[5] // 16):
        st_name, st_value, st_size, st_info, _, st_shndx = struct.unpack_from("<IIIBBH", data, symtab[4] + i * 16)
        if st_shndx == tidx:
            name = data[strtab_off + st_name : data.index(b"\x00", strtab_off + st_name)].decode("ascii", errors="replace")
            if name == "engine_func_002350f4":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError("engine_func_002350f4 not found in object")

    ro_blob = bytearray()
    sec_to_ro_off: dict[int, int] = {}
    for idx, s in enumerate(shdrs):
        nm = sh_name(idx)
        if nm.startswith(".rodata"):
            sec_to_ro_off[idx] = len(ro_blob)
            ro_blob.extend(data[s[4] : s[4] + s[5]])
            while len(ro_blob) % 4:
                ro_blob.append(0)

    relocs: list[tuple[str, int]] = []
    abs_relocs: list[tuple[int, int, int]] = []
    for s in shdrs:
        if s[1] == 9 and s[7] == tidx:
            for k in range(s[5] // 8):
                r_off, r_info = struct.unpack_from("<II", data, s[4] + k * 8)
                sym_idx, r_type = r_info >> 8, r_info & 0xFF
                if fn_off <= r_off < fn_off + fn_size:
                    st_name, st_value, _, _, _, st_shndx = struct.unpack_from("<IIIBBH", data, symtab[4] + sym_idx * 16)
                    sname = data[strtab_off + st_name : data.index(b"\x00", strtab_off + st_name)].decode("ascii", errors="replace")
                    if r_type in (28, 29):
                        relocs.append((sname, r_off - fn_off))
                    elif r_type == 2 and st_shndx in sec_to_ro_off:
                        abs_relocs.append((r_off - fn_off, sec_to_ro_off[st_shndx] + st_value, r_type))

    return bytes(text_data[fn_off : fn_off + fn_size]), relocs, bytes(ro_blob), abs_relocs


def patch_bl(code: bytearray, at_off: int, src_pc: int, dst_pc: int) -> None:
    delta = (dst_pc - (src_pc + 8)) >> 2
    hi = code[at_off + 3]
    insn = (hi << 24) | (delta & 0x00FFFFFF)
    struct.pack_into("<I", code, at_off, insn)


def read_cstr(uc: unicorn.Uc, addr: int) -> str:
    if addr == 0:
        return "<NULL>"
    raw = uc.mem_read(addr, 64)
    return raw.split(b"\x00", 1)[0].decode("ascii", errors="replace")


def run_case(
    code_bytes: bytes,
    relocs: list[tuple[str, int]],
    ro_blob: bytes,
    abs_relocs: list[tuple[int, int, int]],
    *,
    is_orig: bool,
    use_name2: bool,
    dum_names: list[str],
) -> tuple[bytes, bytes, list[tuple[str, tuple[object, ...]]], dict[str, int]]:
    mu = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    cpacr = mu.reg_read(arm.UC_ARM_REG_C1_C0_2)
    mu.reg_write(arm.UC_ARM_REG_C1_C0_2, cpacr | (0xF << 20))
    mu.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

    mu.mem_map(0x00100000, 0x00400000)
    mu.mem_map(0x20000000, 0x00100000)
    mu.mem_map(STACK_BASE, STACK_SIZE)
    mu.mem_map(LR_SENTINEL, 0x1000)

    buf = bytearray(code_bytes)
    entry = FUNC_ADDR if is_orig else 0x00400000
    name_to_addr = {v: k for k, v in STUBS.items()}
    if not is_orig:
        if ro_blob:
            mu.mem_write(RODATA_BASE, ro_blob)
        for off, ro_off, _ in abs_relocs:
            cur = struct.unpack_from("<I", buf, off)[0]
            struct.pack_into("<I", buf, off, cur + RODATA_BASE + ro_off)
        for sname, off in relocs:
            if sname not in name_to_addr:
                raise RuntimeError(f"Unexpected reloc target: {sname}")
            patch_bl(buf, off, entry + off, name_to_addr[sname])

    mu.mem_write(entry, bytes(buf))
    for addr in STUBS:
        if is_orig and addr in (0x002BE7FC, 0x00100C4C):
            mu.mem_write(addr, struct.pack("<H", 0x4770))
        else:
            mu.mem_write(addr, make_stub_bx_lr())

    calls: list[tuple[str, tuple[object, ...]]] = []
    load_idx = [0]

    def hook_stub(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
        sname = STUBS[addr]
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        if sname == "engine_func_002c4b30":
            calls.append((sname, (r0, r1)))
            uc.mem_write(r0, struct.pack("<I", P56C_ADDR))
        elif sname == "ui_func_002be7fc":
            fmt = read_cstr(uc, r1)
            arg = read_cstr(uc, r2) if "%s" in fmt else ""
            formatted = (fmt % arg) if "%s" in fmt else fmt
            uc.mem_write(r0, formatted.encode("ascii") + b"\x00")
            calls.append((sname, (formatted,)))
        elif sname == "engine_func_0029bddc":
            calls.append((sname, (read_cstr(uc, r0), r1)))
            idx = load_idx[0]
            load_idx[0] += 1
            uc.reg_write(arm.UC_ARM_REG_R0, [MOD1C_ADDR, MOD24_ADDR, MOD20_ADDR][idx])
        elif sname == "engine_func_002a06c8":
            calls.append((sname, (r0, r1)))
        elif sname == "engine_func_00341578":
            calls.append((sname, (r0, read_cstr(uc, r1))))
        elif sname == "engine_func_002a0c54":
            calls.append((sname, (read_cstr(uc, r0), r1)))
        elif sname == "script_vm_func_002a0790":
            calls.append((sname, (r0,)))
        elif sname == "engine_func_002a8948":
            calls.append((sname, (r0,)))
            uc.reg_write(arm.UC_ARM_REG_R0, P2A8_ADDR)
        elif sname == "crt_func_00100c4c":
            s0 = read_cstr(uc, r0)
            s1 = read_cstr(uc, r1)
            calls.append((sname, (s0, s1)))
            uc.reg_write(arm.UC_ARM_REG_R0, 1 if s1 in s0 else 0)
        elif sname == "engine_func_0028c8a8":
            vec = struct.unpack("<3I", uc.mem_read(r2, 12))
            calls.append((sname, (r0, r1, vec)))

    for addr in STUBS:
        mu.hook_add(unicorn.UC_HOOK_CODE, hook_stub, begin=addr, end=addr)

    mu.mem_write(NAME1_ADDR, b"field01\x00")
    mu.mem_write(NAME2_ADDR, b"field02\x00")

    mu.mem_write(SELF_ADDR, b"\x00" * 0x1700)
    mu.mem_write(P56C_ADDR, b"\x00" * 0x80)
    mu.mem_write(P56C_ADDR + 0x58, struct.pack("<I", 0x1111))
    mu.mem_write(P56C_ADDR + 0x68, struct.pack("<I", 0x2222))
    mu.mem_write(P56C_ADDR + 0x78, struct.pack("<I", 0x3333))
    mu.mem_write(P2A8_ADDR, struct.pack("<3I", 0x4444, 0x5555, 0x6666))

    mu.mem_write(MOD1C_ADDR + 8, struct.pack("<I", SUB8_ADDR))
    mu.mem_write(SUB8_ADDR + 0x2C, struct.pack("<I", SUB2C_ADDR))
    mu.mem_write(SUB2C_ADDR + 8, struct.pack("<I", NODE_ADDR))

    mu.mem_write(MOD20_ADDR + 8, struct.pack("<I", 0x20009000))

    mu.mem_write(NODE_ADDR, struct.pack("<I", 0x40000092))
    mu.mem_write(NODE_ADDR + 0xE0, struct.pack("<I", GRP_ADDR - (NODE_ADDR + 0xE0)))

    mu.mem_write(GRP_ADDR + 0x18, struct.pack("<iI", len(dum_names), ARR_ADDR - (GRP_ADDR + 0x1C)))

    entries = [ENTRY0_ADDR, ENTRY1_ADDR]
    for i, nm in enumerate(dum_names):
        ent = entries[i]
        slot_ptr = ARR_ADDR + i * 0x10 + 0x28
        mu.mem_write(slot_ptr, struct.pack("<I", ent - slot_ptr))
        mu.mem_write(ent, struct.pack("<I", 0x40))
        mu.mem_write(ent + 0x38, struct.pack("<3I", 0xA0 + i, 0xB0 + i, 0xC0 + i))
        mu.mem_write(ent + 0x40, nm.encode("ascii") + b"\x00")

    mu.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
    mu.reg_write(arm.UC_ARM_REG_R1, NAME1_ADDR)
    mu.reg_write(arm.UC_ARM_REG_R2, NAME2_ADDR if use_name2 else 0)
    mu.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    mu.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for rname, cval in CALLEE_SAVED.items():
        mu.reg_write(getattr(arm, f"UC_ARM_REG_{rname.upper()}"), cval)

    mu.emu_start(entry, LR_SENTINEL, count=200000)

    self_head = bytes(mu.mem_read(SELF_ADDR, 0x28))
    self_tail = bytes(mu.mem_read(SELF_ADDR + 0x1604, 0x88))
    regs = {
        "sp": mu.reg_read(arm.UC_ARM_REG_SP),
        **{r: mu.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
    }
    return self_head, self_tail, calls, regs


CASES = [
    dict(name="name2_with_2_dums", use_name2=True, dum_names=["Other_0", "Dum_0"]),
    dict(name="null_name2_no_dums", use_name2=False, dum_names=["Foo", "Bar"]),
    dict(name="null_name2_empty_grp", use_name2=False, dum_names=[]),
]


def check_pair(
    orig_bytes: bytes,
    cand_bytes: bytes,
    relocs: list[tuple[str, int]],
    ro_blob: bytes,
    abs_relocs: list[tuple[int, int, int]],
    *,
    cand_is_orig: bool = False,
) -> tuple[bool, str]:
    for c in CASES:
        kw = {k: v for k, v in c.items() if k != "name"}
        o_h, o_t, o_calls, o_regs = run_case(orig_bytes, [], b"", [], is_orig=True, **kw)
        c_h, c_t, c_calls, c_regs = run_case(cand_bytes, relocs, ro_blob, abs_relocs, is_orig=cand_is_orig, **kw)
        if o_h != c_h or o_t != c_t:
            return False, f"{c['name']}: memory mismatch"
        if o_calls != c_calls:
            return False, f"{c['name']}: calls mismatch\norig={o_calls}\ncand={c_calls}"
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            return False, f"{c['name']}: regs mismatch"
    return True, "ok"


def mutate_bytes(orig_bytes: bytes) -> list[tuple[str, bytes]]:
    b = bytearray(orig_bytes)

    # 1. Flip name2 == NULL branch beq -> bne (at 0x00235140)
    m1 = bytearray(b)
    off1 = 0x00235140 - FUNC_ADDR
    insn1 = struct.unpack_from("<I", m1, off1)[0]
    assert (insn1 >> 28) == 0x0
    struct.pack_into("<I", m1, off1, (insn1 & 0x0FFFFFFF) | 0x10000000)

    # 2. Flip count <= 0 branch ble -> bgt (at 0x00235254)
    m2 = bytearray(b)
    off2 = 0x00235254 - FUNC_ADDR
    insn2 = struct.unpack_from("<I", m2, off2)[0]
    assert (insn2 >> 28) == 0xD
    struct.pack_into("<I", m2, off2, (insn2 & 0x0FFFFFFF) | 0xC0000000)

    # 3. Flip strstr == NULL branch beq -> bne (at 0x002352ac)
    m3 = bytearray(b)
    off3 = 0x002352AC - FUNC_ADDR
    insn3 = struct.unpack_from("<I", m3, off3)[0]
    assert (insn3 >> 28) == 0x0
    struct.pack_into("<I", m3, off3, (insn3 & 0x0FFFFFFF) | 0x10000000)

    # 4. Flip self[0xC] <= 0 branch ble -> bgt (at 0x00235314)
    m4 = bytearray(b)
    off4 = 0x00235314 - FUNC_ADDR
    insn4 = struct.unpack_from("<I", m4, off4)[0]
    assert (insn4 >> 28) == 0xD
    struct.pack_into("<I", m4, off4, (insn4 & 0x0FFFFFFF) | 0xC0000000)

    # 5. Flip self[0x15] = 1 -> 0 (at 0x00235318)
    m5 = bytearray(b)
    off5 = 0x00235318 - FUNC_ADDR
    assert struct.unpack_from("<I", m5, off5)[0] == 0xE3A00001
    struct.pack_into("<I", m5, off5, 0xE3A00000)

    return [
        ("name2_bne", bytes(m1)),
        ("count_bgt", bytes(m2)),
        ("strstr_bne", bytes(m3)),
        ("dum_cnt_bgt", bytes(m4)),
        ("flag15_0", bytes(m5)),
    ]


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    start = FUNC_ADDR - 0x00100000
    orig_bytes = orig_all[start : start + FUNC_SIZE]

    cand_bytes, relocs, ro_blob, abs_relocs = compile_candidate()
    ok, msg = check_pair(orig_bytes, cand_bytes, relocs, ro_blob, abs_relocs)
    if not ok:
        print(f"FAIL: {msg}")
        return 1

    detected = 0
    for mname, mbytes in mutate_bytes(orig_bytes):
        mok, _ = check_pair(orig_bytes, mbytes, [], b"", [], cand_is_orig=True)
        if not mok:
            detected += 1
        else:
            print(f"FAIL: mutant {mname} was not detected")
            return 1

    print(
        f"PASS: engine_func_002350f4 (0x{FUNC_ADDR:08x}) matched original across {len(CASES)} cases "
        f"and detected {detected}/5 mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
