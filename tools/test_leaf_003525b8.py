#!/usr/bin/env python3
"""Differential test for engine_func_003525b8 (0x003525b8) with Unicorn ARM.

Compiles src/engine/leaf_batch45_b.cpp, extracts the engine_func_003525b8 body,
resolves its direct calls to deterministic stubs, and runs the pinned original
(extracted/exefs/code.bin) against the candidate in separate Unicorn machines
with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log with every register argument, the 17 architected stack
    words of the 21-argument serializer call, the descriptor pair handed to
    func_0035382c, the parsed value string, and every key comparison;
  * the descriptor, header, item, pair, string and global fixture pages (they
    must be unmodified) and any emulated write outside the private stack.

Coverage: early negative open, negative serializer, negative put, positive and
zero helper results; header null, zero count, and present count; every lo8
selection ((w4>>14)==0x10 with low16 0x8C, 0x0D, other; and (w4>>14)!=0x10);
pair_count zero, key hit at k=0/k>0, and key miss; null and non-null descriptor
fallbacks; 1/2/3-item loop bounds; and both loop-exit returns (0 and the
0xC8A13908 sentinel). Negative controls mutate six distinct original decisions.
"""

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
OUT_DIR = ROOT / "build" / "test_leaf_003525b8"

FUNC_ADDR = 0x003525B8
FUNC_SIZE = 796

STUBS = {
    0x003538D4: "func_003538d4",
    0x003538B8: "func_003538b8",
    0x003538C4: "func_003538c4",
    0x0035334C: "func_0035334c",
    0x0023A3A4: "func_0023a3a4",
    0x003532A8: "func_003532a8",
    0x0035FA44: "func_0035fa44",
    0x002B45F8: "engine_func_002b45f8",
    0x002C607C: "script_vm_func_002c607c",
    0x0035382C: "func_0035382c",
}

# 0x2C607C is Thumb code in the pinned binary (the original reaches it with
# `blx`). A real linker turns the candidate's R_ARM_CALL into BLX as well; the
# two machines are separate, so the candidate can use an ARM stub.
THUMB_STUBS = {0x002C607C}

G_471A50 = 0x00471A50
G_471A54 = 0x00471A54
G_471A50_VALUE = 0xAAAA0001
G_471A54_VALUE = 0xAAAA0002

RODATA_BASE = 0x00450000
CAND_ADDR = 0x00400000

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000

SELF_ADDR = 0x20000000
HDR_ADDR = 0x20000100
ITEMS_ADDR = 0x20000200
PAIRS_ADDR = 0x20001000
STRS_ADDR = 0x20002000
A3_ADDR = 0x20004000
PTRS_ADDR = 0x20005000
FIXTURE_SIZE = 0x00100000
SNAPSHOT_BASE = 0x20000000
SNAPSHOT_SIZE = 0x00006000

STACK_BASE = 0x7F000000
STACK_SIZE = 0x00010000
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

SENTINEL = 0xC8A13908


def make_stub_bx_lr() -> bytes:
    return struct.pack("<I", 0xE12FFF1E)


def compile_candidate() -> tuple[bytes, list[tuple[str, int]], bytes, list[tuple[int, int]]]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_path = OUT_DIR / "leaf_batch45_b.o"
    res = compile_tu_armv6k(SOURCE, obj_path, ROOT)
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
        st_name, st_value, st_size, st_info, _, st_shndx = struct.unpack_from(
            "<IIIBBH", data, symtab[4] + i * 16
        )
        if st_shndx == tidx:
            name = data[strtab_off + st_name : data.index(b"\x00", strtab_off + st_name)].decode(
                "ascii", errors="replace"
            )
            if name == "engine_func_003525b8":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError("engine_func_003525b8 not found in object")

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
    abs_relocs: list[tuple[int, int]] = []
    for s in shdrs:
        if s[1] == 9 and s[7] == tidx:
            for k in range(s[5] // 8):
                r_off, r_info = struct.unpack_from("<II", data, s[4] + k * 8)
                sym_idx, r_type = r_info >> 8, r_info & 0xFF
                if fn_off <= r_off < fn_off + fn_size:
                    st_name, st_value, _, _, _, st_shndx = struct.unpack_from(
                        "<IIIBBH", data, symtab[4] + sym_idx * 16
                    )
                    sname = data[
                        strtab_off + st_name : data.index(b"\x00", strtab_off + st_name)
                    ].decode("ascii", errors="replace")
                    if r_type in (28, 29):
                        relocs.append((sname, r_off - fn_off))
                    elif r_type == 2 and st_shndx in sec_to_ro_off:
                        abs_relocs.append((r_off - fn_off, sec_to_ro_off[st_shndx] + st_value))

    return bytes(text_data[fn_off : fn_off + fn_size]), relocs, bytes(ro_blob), abs_relocs


def patch_call(code: bytearray, at_off: int, src_pc: int, dst_pc: int) -> None:
    delta = (dst_pc - (src_pc + 8)) >> 2
    top = code[at_off + 3]
    insn = (top << 24) | (delta & 0x00FFFFFF)
    struct.pack_into("<I", code, at_off, insn)


def read_cstr(uc: unicorn.Uc, addr: int) -> str:
    if addr == 0:
        return "<NULL>"
    raw = uc.mem_read(addr, 64)
    return raw.split(b"\x00", 1)[0].decode("ascii", errors="replace")


def build_fixture(
    mu: unicorn.Uc,
    *,
    a3_0: int,
    a3_8: int,
    a3_18: int,
    a3_1C: int,
    a3_byte28: int,
    use_hdr: bool,
    items: list[dict],
    hdr_word8: int,
) -> None:
    mu.mem_write(SELF_ADDR, struct.pack("<IIII", 0, HDR_ADDR if use_hdr else 0, 0x12, 0x34))

    if use_hdr:
        mu.mem_write(HDR_ADDR, struct.pack("<III", ITEMS_ADDR, len(items), hdr_word8))

    mu.mem_write(ITEMS_ADDR, b"\x00" * 0x400)
    mu.mem_write(PAIRS_ADDR, b"\x00" * 0x400)
    mu.mem_write(STRS_ADDR, b"\x00" * 0x1000)

    for i, item in enumerate(items):
        base = ITEMS_ADDR + i * 0x30
        mu.mem_write(base + 0x00, struct.pack("<II", item["w0"] & 0xFFFFFFFF, item["w4"] & 0xFFFFFFFF))
        keys = item["keys"]
        mu.mem_write(base + 0x18, struct.pack("<II", PAIRS_ADDR + i * 0x40, len(keys)))
        for k, key in enumerate(keys):
            key_addr = STRS_ADDR + i * 0x100 + k * 0x40
            val_addr = key_addr + 0x20
            mu.mem_write(key_addr, key.encode("ascii") + b"\x00")
            mu.mem_write(val_addr, f"val{i}_{k}".encode("ascii") + b"\x00")
            mu.mem_write(
                PAIRS_ADDR + i * 0x40 + k * 8,
                struct.pack("<II", key_addr, val_addr),
            )

    mu.mem_write(A3_ADDR, b"\x00" * 0x40)
    mu.mem_write(A3_ADDR + 0x00, struct.pack("<II", a3_0, 0x33333333))
    mu.mem_write(A3_ADDR + 0x08, struct.pack("<II", a3_8, 0x44444444))
    mu.mem_write(A3_ADDR + 0x10, struct.pack("<II", 0x55555555, 0x66666666))
    mu.mem_write(A3_ADDR + 0x18, struct.pack("<II", a3_18, a3_1C))
    mu.mem_write(A3_ADDR + 0x28, struct.pack("<B", a3_byte28 & 0xFF))
    mu.mem_write(A3_ADDR + 0x2C, struct.pack("<II", 0x88888888, 0x99999999))

    mu.mem_write(G_471A50, struct.pack("<I", G_471A50_VALUE))
    mu.mem_write(G_471A54, struct.pack("<I", G_471A54_VALUE))


def run_case(
    code_bytes: bytes,
    relocs: list[tuple[str, int]],
    ro_blob: bytes,
    abs_relocs: list[tuple[int, int]],
    *,
    is_orig: bool,
    ret_3538d4: int,
    ret_35fa44: int,
    ret_35382c: int,
    ret_38b8: int,
    ret_38c4: int,
    ret_2c607c: int,
    a3_0: int,
    a3_8: int,
    a3_18: int,
    a3_1C: int,
    a3_byte28: int,
    use_hdr: bool,
    items: list[dict],
    hdr_word8: int,
) -> dict:
    mu = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    mu.mem_map(CODE_BASE, CODE_SIZE)
    mu.mem_map(SELF_ADDR, FIXTURE_SIZE)
    mu.mem_map(STACK_BASE, STACK_SIZE)
    mu.mem_map(LR_SENTINEL, 0x1000)

    buf = bytearray(code_bytes)
    entry = FUNC_ADDR if is_orig else CAND_ADDR
    name_to_addr = {v: k for k, v in STUBS.items()}
    if not is_orig:
        if ro_blob:
            mu.mem_write(RODATA_BASE, ro_blob)
        for off, ro_off in abs_relocs:
            cur = struct.unpack_from("<I", buf, off)[0]
            struct.pack_into("<I", buf, off, cur + RODATA_BASE + ro_off)
        for sname, off in relocs:
            if sname not in name_to_addr:
                raise RuntimeError(f"Unexpected reloc target: {sname}")
            patch_call(buf, off, entry + off, name_to_addr[sname])

    mu.mem_write(entry, bytes(buf))
    for addr in STUBS:
        if addr in THUMB_STUBS and is_orig:
            mu.mem_write(addr, struct.pack("<H", 0x4770))
        else:
            mu.mem_write(addr, make_stub_bx_lr())

    calls: list[tuple[str, tuple]] = []
    writes: list[tuple[int, int]] = []

    def hook_stub(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
        sname = STUBS[addr]
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        if sname == "func_003538d4":
            calls.append((sname, (r0, r1, r2)))
            uc.reg_write(arm.UC_ARM_REG_R0, ret_3538d4 & 0xFFFFFFFF)
        elif sname == "func_003538b8":
            calls.append((sname, (r0,)))
            uc.reg_write(arm.UC_ARM_REG_R0, ret_38b8 & 0xFFFFFFFF)
        elif sname == "func_003538c4":
            calls.append((sname, (r0,)))
            uc.reg_write(arm.UC_ARM_REG_R0, ret_38c4 & 0xFFFFFFFF)
        elif sname == "func_0035334c":
            calls.append((sname, ()))
        elif sname == "func_0023a3a4":
            calls.append((sname, (read_cstr(uc, r0),)))
        elif sname == "func_003532a8":
            calls.append((sname, (r0,)))
        elif sname == "func_0035fa44":
            sp = uc.reg_read(arm.UC_ARM_REG_SP)
            stack_words = struct.unpack("<17I", uc.mem_read(sp, 68))
            calls.append((sname, (r0, r1, r2, r3, stack_words)))
            uc.reg_write(arm.UC_ARM_REG_R0, ret_35fa44 & 0xFFFFFFFF)
        elif sname == "engine_func_002b45f8":
            s0 = read_cstr(uc, r0)
            s1 = read_cstr(uc, r1)
            calls.append((sname, (s0, s1, r2)))
            uc.reg_write(arm.UC_ARM_REG_R0, 0 if s0 == s1 else 1)
        elif sname == "script_vm_func_002c607c":
            calls.append((sname, (read_cstr(uc, r0), r1, r2)))
            uc.reg_write(arm.UC_ARM_REG_R0, (ret_2c607c if r0 != 0 else 0) & 0xFFFFFFFF)
        elif sname == "func_0035382c":
            p0, p1 = struct.unpack("<II", uc.mem_read(r1, 8))
            calls.append((sname, (r0, p0, p1, r2)))
            uc.reg_write(arm.UC_ARM_REG_R0, ret_35382c & 0xFFFFFFFF)

    for addr in STUBS:
        mu.hook_add(unicorn.UC_HOOK_CODE, hook_stub, begin=addr, end=addr)

    def hook_write(uc: unicorn.Uc, access: int, address: int, size: int, value: int, user_data: object) -> None:
        if not (STACK_BASE <= address < STACK_BASE + STACK_SIZE):
            writes.append((address, size))

    mu.hook_add(unicorn.UC_HOOK_MEM_WRITE, hook_write)

    build_fixture(
        mu,
        a3_0=a3_0,
        a3_8=a3_8,
        a3_18=a3_18,
        a3_1C=a3_1C,
        a3_byte28=a3_byte28,
        use_hdr=use_hdr,
        items=items,
        hdr_word8=hdr_word8,
    )
    mu.mem_write(STACK_BASE, b"\x00" * STACK_SIZE)

    mu.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
    mu.reg_write(arm.UC_ARM_REG_R1, 0x11)
    mu.reg_write(arm.UC_ARM_REG_R2, 0x22)
    mu.reg_write(arm.UC_ARM_REG_R3, A3_ADDR)
    mu.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    mu.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for rname, cval in CALLEE_SAVED.items():
        mu.reg_write(getattr(arm, f"UC_ARM_REG_{rname.upper()}"), cval)

    mu.emu_start(entry, LR_SENTINEL, count=200000)

    ret = mu.reg_read(arm.UC_ARM_REG_R0)
    if ret & 0x80000000:
        ret -= 0x100000000
    regs = {"sp": mu.reg_read(arm.UC_ARM_REG_SP)}
    for rname in CALLEE_SAVED:
        regs[rname] = mu.reg_read(getattr(arm, f"UC_ARM_REG_{rname.upper()}"))
    snapshot = bytes(mu.mem_read(SNAPSHOT_BASE, SNAPSHOT_SIZE))
    globals_page = struct.pack(
        "<II",
        struct.unpack_from("<I", mu.mem_read(G_471A50, 4))[0],
        struct.unpack_from("<I", mu.mem_read(G_471A54, 4))[0],
    )
    return {
        "ret": ret,
        "pc": mu.reg_read(arm.UC_ARM_REG_PC),
        "regs": regs,
        "calls": calls,
        "writes": writes,
        "snapshot": snapshot,
        "globals": globals_page,
    }


BASE_CASE = dict(
    ret_3538d4=0,
    ret_35fa44=0,
    ret_35382c=0,
    ret_38b8=0x11112222,
    ret_38c4=0x33334444,
    ret_2c607c=0x12345678,
    a3_0=0,
    a3_8=0,
    a3_18=0,
    a3_1C=0,
    a3_byte28=0x77,
    use_hdr=True,
    items=[],
    hdr_word8=1,
)


def case(name: str, **overrides) -> dict:
    out = dict(BASE_CASE)
    out.update(overrides)
    out["name"] = name
    return out


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # Early open failure at three signed boundaries.
    for rc in (-1, -5, -0x80000000):
        cases.append(case(f"open_fail_{rc}", ret_3538d4=rc))

    # Open success variants.
    cases.append(case("open_ok_zero", ret_3538d4=0, use_hdr=False, hdr_word8=0))
    cases.append(case("open_ok_positive", ret_3538d4=0x7FFFFFFF, use_hdr=False, hdr_word8=0))

    # Serializer failure.
    cases.append(case("serializer_fail", ret_35fa44=-7))

    # Header absent: finish sentinel regardless of trailing word.
    cases.append(case("hdr_null_tail_zero", use_hdr=False, hdr_word8=0))
    cases.append(case("hdr_null_tail_nonzero", use_hdr=False, hdr_word8=0x5A))

    # Header present but empty.
    cases.append(case("hdr_empty_tail_zero", items=[], hdr_word8=0))
    cases.append(case("hdr_empty_tail_nonzero", items=[], hdr_word8=0x5A))

    # Descriptor fallbacks: all zero vs all distinct non-null pointers.
    cases.append(case("a3_all_zero", use_hdr=False, hdr_word8=0))
    cases.append(
        case(
            "a3_all_set",
            use_hdr=False,
            hdr_word8=0,
            a3_0=PTRS_ADDR + 0x00,
            a3_8=PTRS_ADDR + 0x10,
            a3_18=PTRS_ADDR + 0x20,
            a3_1C=PTRS_ADDR + 0x30,
        )
    )
    cases.append(
        case(
            "a3_mixed",
            use_hdr=False,
            hdr_word8=0,
            a3_0=0,
            a3_8=PTRS_ADDR + 0x40,
            a3_18=0,
            a3_1C=PTRS_ADDR + 0x50,
        )
    )

    # Full loop: 1, 2 and 3 items with every lo8 mode and key-hit shapes.
    cases.append(
        case(
            "one_item_8c_hit",
            items=[dict(w0=0x12345678, w4=(0x10 << 14) | 0x8C, keys=["TitleVersion"])],
            hdr_word8=1,
        )
    )
    cases.append(
        case(
            "two_items_8c_d_hit",
            items=[
                dict(w0=0x00000000, w4=(0x10 << 14) | 0x8C, keys=["TitleVersion"]),
                dict(w0=0xFFFFFFFF, w4=(0x10 << 14) | 0x0D, keys=["TitleVersion"]),
            ],
            hdr_word8=0x5A,
        )
    )
    cases.append(
        case(
            "three_items_all_modes",
            items=[
                dict(w0=0x12345678, w4=(0x10 << 14) | 0x8C, keys=["TitleVersion"]),
                dict(w0=0xABCDEF01, w4=(0x10 << 14) | 0x0D, keys=["TitleVersion"]),
                dict(w0=0x55667788, w4=(0x05 << 14) | 0x22, keys=["other.Key"]),
            ],
            hdr_word8=1,
        )
    )
    # (w4 >> 14) == 0x10 but low16 is neither 0x8C nor 0x0D.
    cases.append(
        case(
            "eq_mode_other_low16",
            items=[dict(w0=0xDEADBEEF, w4=(0x10 << 14) | 0x1234, keys=["TitleVersion"])],
            hdr_word8=1,
        )
    )
    # (w4 >> 14) != 0x10 with assorted high/low bits.
    for w4 in (0x00000000, 0xFFFFFFFF, 0x0003FFFF, 0x00040000, 0x7FFFFFFF, 0x80000000):
        cases.append(
            case(
                f"non_eq_w4_{w4:08x}",
                items=[dict(w0=0x01234567, w4=w4, keys=["TitleVersion"])],
                hdr_word8=1,
            )
        )

    # Key hit at k>0, and key miss with pair_count > 0.
    cases.append(
        case(
            "hit_at_second_pair",
            items=[
                dict(
                    w0=0x11111111,
                    w4=(0x10 << 14) | 0x8C,
                    keys=["other.Key", "TitleVersion"],
                )
            ],
            hdr_word8=1,
        )
    )
    cases.append(
        case(
            "pair_miss",
            items=[
                dict(
                    w0=0x22222222,
                    w4=(0x10 << 14) | 0x0D,
                    keys=["other.Key", "also.Key"],
                )
            ],
            hdr_word8=1,
        )
    )

    # Loop exits with the sentinel because [hdr+8] is zero.
    cases.append(
        case(
            "loop_then_tail_zero",
            items=[dict(w0=1, w4=(0x10 << 14) | 0x8C, keys=["TitleVersion"])],
            hdr_word8=0,
        )
    )

    # Put failure after the first item.
    cases.append(
        case(
            "put_fail",
            ret_35382c=-9,
            items=[dict(w0=0x33333333, w4=(0x10 << 14) | 0x8C, keys=["TitleVersion"])],
            hdr_word8=1,
        )
    )
    cases.append(
        case(
            "put_ok_positive",
            ret_35382c=0x7FFFFFFF,
            items=[dict(w0=0x44444444, w4=(0x10 << 14) | 0x8C, keys=["TitleVersion"])],
            hdr_word8=1,
        )
    )

    # w0/w4 signed boundaries feeding p0/p1 packing and the u16 code truncation.
    for w0, w4, code in (
        (0x000000FF, 0xFFFFFFFF, 0xFFFF0041),
        (0x7FFFFFFF, 0x80000000, 0x0000FFFF),
        (0x80000000, 0x7FFFFFFF, 0x12345678),
        (0xFFFFFFFF, 0x00000000, 0xFFFFFFFF),
    ):
        cases.append(
            case(
                f"pack_boundary_{w0:08x}_{w4:08x}",
                ret_2c607c=code,
                items=[dict(w0=w0, w4=w4, keys=["TitleVersion"])],
                hdr_word8=1,
            )
        )
        cases.append(
            case(
                f"pack_boundary_{w0:08x}_{w4:08x}_miss",
                ret_2c607c=code,
                items=[dict(w0=w0, w4=w4, keys=["other.Key"])],
                hdr_word8=1,
            )
        )

    # Header byte boundaries (only low 8 bits are passed to func_003532a8).
    for byte in (0x00, 0x7F, 0x80, 0xFF):
        cases.append(case(f"hdr_byte_{byte:02x}", a3_byte28=byte, use_hdr=False, hdr_word8=0))

    return cases


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "regs"):
        if orig[key] != cand[key]:
            problems.append(f"{key}: orig={orig[key]!r} cand={cand[key]!r}")
    if orig["calls"] != cand["calls"]:
        problems.append(f"calls:\n  orig={orig['calls']!r}\n  cand={cand['calls']!r}")
    if orig["snapshot"] != cand["snapshot"]:
        problems.append("fixture snapshot changed differently")
    if orig["globals"] != cand["globals"]:
        problems.append(
            f"globals: orig={orig['globals']!r} cand={cand['globals']!r}"
        )
    if orig["writes"] or cand["writes"]:
        problems.append(
            f"unexpected writes orig={orig['writes']} cand={cand['writes']}"
        )
    if cand["regs"]["sp"] != STACK_INIT:
        problems.append("candidate SP not restored")
    if orig["regs"]["sp"] != STACK_INIT:
        problems.append("original SP not restored")
    return problems


def run_pair(
    orig_bytes: bytes,
    cand_bytes: bytes,
    relocs: list[tuple[str, int]],
    ro_blob: bytes,
    abs_relocs: list[tuple[int, int]],
    *,
    cand_is_orig: bool = False,
    cases: list[dict] | None = None,
) -> tuple[bool, str]:
    for c in cases if cases is not None else make_cases():
        kw = {k: v for k, v in c.items() if k != "name"}
        o = run_case(orig_bytes, [], b"", [], is_orig=True, **kw)
        if cand_is_orig:
            k = run_case(cand_bytes, [], b"", [], is_orig=True, **kw)
        else:
            k = run_case(cand_bytes, relocs, ro_blob, abs_relocs, is_orig=False, **kw)
        problems = compare(o, k)
        if problems:
            return False, f"{c['name']}: " + "; ".join(problems)
    return True, "ok"


def mutate_bytes(orig_bytes: bytes) -> list[tuple[str, bytes]]:
    base = bytearray(orig_bytes)
    mutants: list[tuple[str, bytes]] = []

    def patch(addr: int, new_word: int, expected: int) -> None:
        m = bytearray(base)
        off = addr - FUNC_ADDR
        current = struct.unpack_from("<I", m, off)[0]
        if current != expected:
            raise RuntimeError(f"mutant anchor 0x{addr:08x}: 0x{current:08x} != 0x{expected:08x}")
        struct.pack_into("<I", m, off, new_word)
        mutants.append((f"mut_{addr:08x}", bytes(m)))

    # 1. Invert the negative open-return branch.
    patch(0x003525E0, 0x0A000092, 0x1A000092)
    # 2. Change the 0x8C mode constant.
    patch(0x003527D0, 0x035C008D, 0x035C008C)
    # 3. Change the 0x0D mode constant.
    patch(0x003527E8, 0x0350000E, 0x0350000D)
    # 4. Change the parse radix 10 -> 16.
    patch(0x003527A4, 0xE3A02010, 0xE3A0200A)
    # 5. Invert the key-match branch.
    patch(0x00352790, 0x1A000028, 0x0A000028)
    # 6. Change the loop-exit sentinel literal.
    m = bytearray(base)
    off = 0x003528D0 - FUNC_ADDR
    if struct.unpack_from("<I", m, off)[0] != 0xC8A13908:
        raise RuntimeError("sentinel literal anchor mismatch")
    struct.pack_into("<I", m, off, 0xC8A13909)
    mutants.append(("mut_sentinel", bytes(m)))
    # 7. Change the headline compare constant 0x10.
    patch(0x0035272C, 0x83A0A011, 0x83A0A010)
    return mutants


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    start = FUNC_ADDR - 0x00100000
    orig_bytes = orig_all[start : start + FUNC_SIZE]

    cand_bytes, relocs, ro_blob, abs_relocs = compile_candidate()
    print(
        f"engine_func_003525b8: original {FUNC_SIZE} B, candidate {len(cand_bytes)} B, "
        f"rodata {len(ro_blob)} B, {len(relocs)} call relocs, {len(abs_relocs)} abs relocs"
    )

    ok, msg = run_pair(orig_bytes, cand_bytes, relocs, ro_blob, abs_relocs)
    if not ok:
        print(f"FAIL: {msg}")
        return 1

    detected = 0
    mutants = mutate_bytes(orig_bytes)
    for mname, mbytes in mutants:
        mok, mmsg = run_pair(orig_bytes, mbytes, [], b"", [], cand_is_orig=True)
        if mok:
            print(f"FAIL: {mname} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: engine_func_003525b8 (0x{FUNC_ADDR:08x}) matched the pinned original "
        f"across {len(make_cases())} differential cases and detected {detected}/"
        f"{len(mutants)} mutants"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
