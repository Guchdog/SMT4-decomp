#!/usr/bin/env python3
"""Differential test for script_vm_func_0027d35c (0x0027d35c) with Unicorn ARM.

Compiles src/engine/leaf_batch45_b.cpp, extracts the script_vm_func_0027d35c
body, resolves its direct calls to deterministic stubs, and runs the pinned
original (extracted/exefs/code.bin) against the candidate in separate Unicorn
machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log with every meaningful register argument;
  * the full fixture memory: the two global pages (state pointer, 92-byte entry
    table, hud block, flag bytes), the state object and the lookup row;
  * any emulated write outside the fixture pages and the private stack.

Coverage: all three "busy" byte combinations, the 0x32839c row null/non-null and
signed row byte, 0x1fb434 zero/non-zero, the 0x275984 mode guard, the 0x18
shortcut (helper 1/non-1, flag 0x2C set/clear, report 0/1/3/other), the 0x255050
hit/miss path with entry +0x14 zero/non-zero and a -1 lookup index, the main
lookup's +0x10 override matrix with signed 16-bit flags, the 0x62C/0x648/0xB8
gates, the signed sub-mode <= 4 bound, the type 0x18 helper-5 path, type
0x29/0x2A/0x2B, all probe values (0, 0x15F..0x168 and misses), 0x287afc
0/1, and every report exit. Negative controls mutate six distinct decisions.
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
OUT_DIR = ROOT / "build" / "test_leaf_0027d35c"

FUNC_ADDR = 0x0027D35C
FUNC_SIZE = 800

CODE_BASE = 0x00100000
CODE_SIZE = 0x00340000  # ends at PAGE_A, covers every stub and the candidate
CAND_ADDR = 0x003E0000

STUB_32839C = 0x0032839C
STUB_26FC24 = 0x0026FC24
STUB_1FB434 = 0x001FB434
STUB_275984 = 0x00275984
STUB_255050 = 0x00255050
STUB_2857E4 = 0x002857E4
STUB_2C0BA8 = 0x002C0BA8
STUB_1B48C0 = 0x001B48C0
STUB_26FCB4 = 0x0026FCB4
STUB_2876D0 = 0x002876D0
STUB_290694 = 0x00290694
STUB_287AFC = 0x00287AFC
STUB_287590 = 0x00287590

STUB_NAMES = {
    STUB_32839C: "camp_func_0032839c",
    STUB_26FC24: "script_vm_func_0026fc24",
    STUB_1FB434: "script_vm_func_001fb434",
    STUB_275984: "script_vm_func_00275984",
    STUB_255050: "script_vm_func_00255050",
    STUB_2857E4: "script_vm_func_002857e4",
    STUB_2C0BA8: "script_vm_func_002c0ba8",
    STUB_1B48C0: "script_vm_func_001b48c0",
    STUB_26FCB4: "script_vm_func_0026fcb4",
    STUB_2876D0: "ui_func_002876d0",
    STUB_290694: "script_vm_func_00290694",
    STUB_287AFC: "script_vm_func_00287afc",
    STUB_287590: "engine_func_00287590",
}

# Globals read/written by the function.
G_STATE = 0x00447E28          # u32 pointer to the state object
G_TABLE = 0x00448E18          # 92-byte entry table
G_HUD = 0x0049F91C            # published descriptor block
G_STATUS = 0x0049FA1C         # flag bytes at +0x1D / +0x45

PAGE_A = 0x00440000
PAGE_A_SIZE = 0x00020000      # covers G_STATE and G_TABLE
PAGE_B = 0x00498000
PAGE_B_SIZE = 0x00020000      # covers G_HUD and G_STATUS

STATE_PAGE = 0x20000000
STATE_PAGE_SIZE = 0x00002000
STATE_ADDR = STATE_PAGE + 0x04  # keeps state+0x2C 8-byte aligned for LDRD

ROW_ADDR = STATE_PAGE + 0x1000

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

ENTRY_STRIDE = 92


def compile_candidate() -> tuple[bytes, list[tuple[str, int]]]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_path = OUT_DIR / "leaf_batch45_b.o"
    res = compile_tu_armv6k(SOURCE, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"compile failed:\n{res.stderr}")

    data = obj_path.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 46)
    shdrs = [
        struct.unpack_from("<10I", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
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
            name = data[
                strtab_off + st_name : data.index(b"\x00", strtab_off + st_name)
            ].decode("ascii", errors="replace")
            if name == "script_vm_func_0027d35c":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError("script_vm_func_0027d35c not found in object")

    relocs: list[tuple[str, int]] = []
    for s in shdrs:
        if s[1] == 9 and s[7] == tidx:
            for k in range(s[5] // 8):
                r_off, r_info = struct.unpack_from("<II", data, s[4] + k * 8)
                sym_idx, r_type = r_info >> 8, r_info & 0xFF
                if not (fn_off <= r_off < fn_off + fn_size):
                    continue
                st_name = struct.unpack_from(
                    "<I", data, symtab[4] + sym_idx * 16
                )[0]
                sname = data[
                    strtab_off + st_name : data.index(b"\x00", strtab_off + st_name)
                ].decode("ascii", errors="replace")
                if r_type in (28, 29):
                    relocs.append((sname, r_off - fn_off))
                else:
                    raise RuntimeError(
                        f"unhandled relocation type {r_type} for {sname}"
                    )

    return bytes(text_data[fn_off : fn_off + fn_size]), relocs


def patch_call(code: bytearray, at_off: int, src_pc: int, dst_pc: int) -> None:
    delta = (dst_pc - (src_pc + 8)) >> 2
    top = code[at_off + 3]
    struct.pack_into("<I", code, at_off, (top << 24) | (delta & 0x00FFFFFF))


def build_entry_fields(fields: dict) -> bytes:
    return struct.pack(
        "<IIhhII",
        fields.get("w8", 0) & 0xFFFFFFFF,
        fields.get("w10", 0) & 0xFFFFFFFF,
        fields.get("f0c", 0),
        fields.get("f0e", 0),
        fields.get("w14", 0) & 0xFFFFFFFF,
        fields.get("pad14", 0x5A5A5A5A) & 0xFFFFFFFF,
    )


def write_entry(fields: dict) -> dict:
    """Map raw field values onto a table entry image."""
    return {
        "w8": fields.get("w8", 0),
        "w10": fields.get("w10", 0),
        "f0c": fields.get("f0c", 0),
        "f0e": fields.get("f0e", 0),
        "w14": fields.get("w14", 0),
    }


def build_page_a(case: dict) -> bytes:
    page = bytearray(PAGE_A_SIZE)
    for i in range(len(page)):
        page[i] = (i * 37 + 11) & 0xFF
    struct.pack_into("<I", page, G_STATE - PAGE_A, STATE_ADDR)
    for index, fields in case.get("entries", {}).items():
        base = G_TABLE + index * ENTRY_STRIDE - PAGE_A
        if base < 0 or base + 0x18 > PAGE_A_SIZE:
            continue
        struct.pack_into("<IIhhI", page, base + 8,
                         fields["w8"] & 0xFFFFFFFF,
                         fields["w10"] & 0xFFFFFFFF,
                         fields["f0c"], fields["f0e"],
                         fields["w14"] & 0xFFFFFFFF)
    return bytes(page)


def build_page_b(case: dict) -> bytes:
    page = bytearray(PAGE_B_SIZE)
    for i in range(len(page)):
        page[i] = (i * 53 + 7) & 0xFF
    struct.pack_into("<I", page, G_HUD + 0x28 - PAGE_B, case["hud28"] & 0xFFFFFFFF)
    page[G_STATUS + 0x45 - PAGE_B] = case["status45"] & 0xFF
    page[G_STATUS + 0x1D - PAGE_B] = case["status1d"] & 0xFF
    return bytes(page)


def build_state(case: dict) -> bytes:
    page = bytearray(STATE_PAGE_SIZE)
    for i in range(len(page)):
        page[i] = (i * 29 + 3) & 0xFF
    off = STATE_ADDR - STATE_PAGE
    struct.pack_into("<I", page, off + 0x24, case["state_24"] & 0xFFFFFFFF)
    struct.pack_into("<I", page, off + 0x2C, case["state_2c"] & 0xFFFFFFFF)
    struct.pack_into("<I", page, off + 0x30, case["state_30"] & 0xFFFFFFFF)
    struct.pack_into("<I", page, off + 0x40, case["state_40"] & 0xFFFFFFFF)
    page[off + 0x45] = case["state_45"] & 0xFF
    row_off = ROW_ADDR - STATE_PAGE
    page[row_off + 0] = 0xAA
    page[row_off + 1] = 0xBB
    page[row_off + 2] = case["row_byte"] & 0xFF
    page[row_off + 3] = 0xCC
    return bytes(page)


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_BASE, CODE_SIZE)
        self.uc.mem_map(PAGE_A, PAGE_A_SIZE)
        self.uc.mem_map(PAGE_B, PAGE_B_SIZE)
        self.uc.mem_map(STATE_PAGE, STATE_PAGE_SIZE)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)
        for addr in STUB_NAMES:
            self.uc.mem_write(addr, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=addr, end=addr
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)
        self.calls: list = []
        self.writes: list = []
        self.cursor: dict[int, int] = {}
        self.case: dict = {}

    def _take(self, addr: int, default: int = 0) -> int:
        seq = self.case.get("seq", {}).get(addr)
        if not seq:
            return default
        i = self.cursor.get(addr, 0)
        self.cursor[addr] = i + 1
        return seq[min(i, len(seq) - 1)] & 0xFFFFFFFF

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        in_stack = STACK_BASE <= address < STACK_BASE + STACK_SIZE
        in_a = PAGE_A <= address < PAGE_A + PAGE_A_SIZE
        in_b = PAGE_B <= address < PAGE_B + PAGE_B_SIZE
        in_state = STATE_PAGE <= address < STATE_PAGE + STATE_PAGE_SIZE
        if not (in_stack or in_a or in_b or in_state):
            self.writes.append((address, size))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        name = STUB_NAMES[address]

        if address == STUB_32839C:
            self.calls.append((name, (r0, r1)))
            uc.reg_write(
                arm.UC_ARM_REG_R0,
                (ROW_ADDR if self.case["row_present"] else 0) & 0xFFFFFFFF,
            )
        elif address == STUB_26FC24:
            self.calls.append((name, ()))
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_1FB434:
            self.calls.append((name, ()))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["ret_1fb434"] & 0xFFFFFFFF)
        elif address == STUB_275984:
            self.calls.append((name, ()))
        elif address == STUB_255050:
            self.calls.append((name, (r0,)))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["ret_255050"] & 0xFFFFFFFF)
        elif address == STUB_2857E4:
            self.calls.append((name, ()))
            uc.reg_write(arm.UC_ARM_REG_R0, self._take(address))
        elif address == STUB_2C0BA8:
            self.calls.append((name, (r0,)))
            on = r0 in self.case["flags_on"]
            uc.reg_write(arm.UC_ARM_REG_R0, 1 if on else 0)
        elif address == STUB_1B48C0:
            self.calls.append((name, (r0, r1)))
        elif address == STUB_26FCB4:
            self.calls.append((name, (r0, r1)))
            uc.reg_write(arm.UC_ARM_REG_R0, self._take(address))
        elif address == STUB_2876D0:
            self.calls.append((name, (r0,)))
            uc.reg_write(arm.UC_ARM_REG_R0, self._take(address))
        elif address == STUB_290694:
            self.calls.append((name, ()))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["ret_290694"] & 0xFFFFFFFF)
        elif address == STUB_287AFC:
            self.calls.append((name, ()))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["ret_287afc"] & 0xFFFFFFFF)
        elif address == STUB_287590:
            self.calls.append((name, (r0,)))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["ret_287590"] & 0xFFFFFFFF)
        else:  # pragma: no cover
            raise AssertionError(f"unexpected stub 0x{address:08x}")

    def run(self, code: bytes, relocs, case: dict, *, is_orig: bool) -> dict:
        self.calls = []
        self.writes = []
        self.cursor = {}
        self.case = case

        buf = bytearray(code)
        entry = FUNC_ADDR if is_orig else CAND_ADDR
        if not is_orig:
            name_to_addr = {v: k for k, v in STUB_NAMES.items()}
            for sname, off in relocs:
                if sname not in name_to_addr:
                    raise RuntimeError(f"Unexpected reloc target: {sname}")
                patch_call(buf, off, entry + off, name_to_addr[sname])

        self.uc.mem_write(entry, bytes(buf))
        self.uc.mem_write(PAGE_A, build_page_a(case))
        self.uc.mem_write(PAGE_B, build_page_b(case))
        self.uc.mem_write(STATE_PAGE, build_state(case))
        self.uc.mem_write(STACK_BASE, b"\x00" * STACK_SIZE)

        self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        self.uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        self.uc.reg_write(arm.UC_ARM_REG_R0, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x33333333)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x44444444)
        for rname, value in CALLEE_SAVED.items():
            self.uc.reg_write(getattr(arm, f"UC_ARM_REG_{rname.upper()}"), value)

        self.uc.emu_start(entry, LR_SENTINEL, count=200000)

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                rname: self.uc.reg_read(getattr(arm, f"UC_ARM_REG_{rname.upper()}"))
                for rname in CALLEE_SAVED
            },
            "calls": list(self.calls),
            "page_a": bytes(self.uc.mem_read(PAGE_A, PAGE_A_SIZE)),
            "page_b": bytes(self.uc.mem_read(PAGE_B, PAGE_B_SIZE)),
            "state": bytes(self.uc.mem_read(STATE_PAGE, STATE_PAGE_SIZE)),
            "writes": list(self.writes),
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}: orig={orig[key]!r} cand={cand[key]!r}")
    if orig["calls"] != cand["calls"]:
        problems.append(f"calls:\n  orig={orig['calls']!r}\n  cand={cand['calls']!r}")
    for key in ("page_a", "page_b", "state"):
        if orig[key] != cand[key]:
            problems.append(f"{key} differs")
    if orig["writes"] or cand["writes"]:
        problems.append(
            f"writes outside fixtures orig={orig['writes']} cand={cand['writes']}"
        )
    return problems


DEFAULTS = dict(
    row_present=False,
    row_byte=0x80,
    status45=0,
    status1d=1,
    state_45=0,
    state_24=0,
    state_2c=0x13,
    state_30=0,
    state_40=0,
    hud28=0x11111111,
    ret_1fb434=1,
    ret_255050=0,
    ret_290694=0,
    ret_287afc=0,
    ret_287590=0xC0DE0001,
    flags_on=(),
    seq={},
    entries={},
)


def case(name: str, **overrides) -> dict:
    out = dict(DEFAULTS)
    out.update(overrides)
    out["name"] = name
    return out


def E(**fields) -> dict:
    return write_entry(fields)


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- busy path: each of the three byte conditions short-circuits.
    cases.append(case("busy_status45", status45=1, status1d=1, state_45=0))
    cases.append(case("busy_status45_ff", status45=0xFF, status1d=1))
    cases.append(case("busy_status1d_zero", status45=0, status1d=0))
    cases.append(case("busy_state45", status45=0, status1d=1, state_45=1))
    cases.append(case("busy_state45_ff", status45=0, status1d=1, state_45=0xFF))

    # --- proceed with the 0x32839c row null / non-null and signed byte.
    cases.append(case("row_null"))
    for byte in (0x00, 0x7F, 0x80, 0xFF):
        cases.append(case(f"row_byte_{byte:02x}", row_present=True, row_byte=byte))

    # --- 0x1fb434 branch and the 0x275984 mode guard.
    cases.append(case("helper_1fb_zero", ret_1fb434=0))
    for mode in (0x17, 0x18, 0x16, 0xFFFFFFFF):
        cases.append(case(f"mode_24_{mode:08x}", state_24=mode))

    # --- type 0x18 shortcut: helper/flag gates and every report exit.
    for helper, flag, rc in (
        (1, (), 0),
        (1, (), 3),
        (1, (), 1),
        (1, (), 2),
        (1, (0x2C,), 0),
        (0, (), 0),
        (5, (), 0),
    ):
        cases.append(
            case(
                f"shortcut_h{helper}_flag{len(flag)}_rc{rc}",
                state_2c=0x18,
                seq={STUB_2857E4: [helper, helper, helper],
                     STUB_2876D0: [rc]},
                flags_on=flag,
            )
        )

    # --- 0x255050 hit path: entry +0x14 selection and report exits.
    for idx, w14, rc in (
        (0, 0x22220000, 0),
        (0, 0x22220000, 3),
        (0, 0x22220000, 1),
        (0, 0x22220000, 2),
        (0, 0, 0),
        (-1, 0x33330000, 0),
        (1, 0x44440000, 0),
    ):
        cases.append(
            case(
                f"hit_idx{idx}_w14_{w14:08x}_rc{rc}",
                state_2c=0x13,
                state_30=0x55,
                ret_255050=1,
                seq={STUB_26FCB4: [idx, 0], STUB_2876D0: [rc]},
                entries={idx: E(w8=0x88880000, w10=0, w14=w14)},
            )
        )

    # --- main lookup +0x10 override matrix with signed 16-bit flags.
    for tag, fields, flags in (
        ("w10_zero", dict(w8=0x11110000, w10=0, w14=0x99990000), ()),
        ("f0c_zero_f0e_zero", dict(w8=1, w10=0xAB000001), ()),
        ("f0c_zero_f0e_on", dict(w8=1, w10=0xAB000002, f0e=7), (7,)),
        ("f0c_zero_f0e_off", dict(w8=1, w10=0xAB000003, f0e=8), ()),
        ("f0c_on_f0e_on", dict(w8=1, w10=0xAB000004, f0c=9, f0e=10), (9, 10)),
        ("f0c_on_f0e_off", dict(w8=1, w10=0xAB000005, f0c=11, f0e=12), (11,)),
        ("f0c_off", dict(w8=1, w10=0xAB000006, f0c=13, f0e=14), ()),
        ("f0c_off_f0e_off", dict(w8=1, w10=0xAB000007, f0c=15, f0e=16), ()),
        ("f0c_neg", dict(w8=1, w10=0xAB000008, f0c=-2), (0xFFFFFFFE,)),
        ("f0e_neg", dict(w8=1, w10=0xAB000009, f0e=-3), (0xFFFFFFFD,)),
        ("f0c_min", dict(w8=1, w10=0xAB00000A, f0c=-0x8000), (0xFFFF8000,)),
        ("f0e_max", dict(w8=1, w10=0xAB00000B, f0e=0x7FFF), (0x7FFF,)),
    ):
        cases.append(
            case(
                f"main_{tag}",
                seq={STUB_26FCB4: [0]},
                entries={0: E(**fields)},
                flags_on=flags,
            )
        )

    # --- step 8: 0x62C/0x648 gate, 0xB8 gate and the signed sub-mode bound.
    cases.append(case("gate_62c_only", seq={STUB_2C0BA8: []},
                      flags_on=(0x62C,)))
    cases.append(case("gate_62c_648", flags_on=(0x62C, 0x648)))
    cases.append(case("gate_648_only", flags_on=(0x648,)))
    for sub in (0, 4, 5, 6, 0xFFFFFFFF, 0x80000000):
        cases.append(case(f"sub_{sub:08x}_b8_off", state_30=sub, flags_on=()))
        cases.append(case(f"sub_{sub:08x}_b8_on", state_30=sub, flags_on=(0xB8,)))
    cases.append(case("type18_helper5_62c", state_2c=0x18,
                      seq={STUB_2857E4: [0, 5]}, flags_on=(0x62C,)))
    cases.append(case("type18_helper5_nogate", state_2c=0x18,
                      seq={STUB_2857E4: [0, 5]}, flags_on=()))
    cases.append(case("type18_helper4", state_2c=0x18,
                      seq={STUB_2857E4: [0, 4]}, flags_on=(0x62C,)))
    for t in (0x29, 0x2A, 0x2B):
        cases.append(case(f"type_{t:02x}", state_2c=t))

    # --- step 9: state +0x40 gate and the 0x290694 probe set.
    for mode in (1, 2, 0, 3):
        cases.append(case(f"state40_{mode}", state_40=mode))
    for probe in (0x0000, 0x015E, 0x015F, 0x0160, 0x0161, 0x0162, 0x0163,
                  0x0164, 0x0165, 0x0166, 0x0167, 0x0168, 0x0169, 0xFFFF):
        cases.append(case(f"probe_{probe:04x}", state_2c=0x01,
                          ret_290694=probe))
    for ret in (0, 1, 2, 0xFF):
        cases.append(case(f"afc_{ret}", state_2c=0x01, ret_290694=0x0162,
                          ret_287afc=ret))

    # --- observable tail return values.
    for ret in (0, 1, 0xFFFFFFFF, 0x80000000):
        cases.append(case(f"tail_ret_{ret:08x}", ret_287590=ret))
        cases.append(case(f"tail_ret_busy_{ret:08x}", ret_287590=ret,
                          status45=1))

    return cases


def mutate_bytes(orig_bytes: bytes) -> list[tuple[str, bytes]]:
    base = bytearray(orig_bytes)
    mutants: list[tuple[str, bytes]] = []

    def patch(addr: int, new_word: int, expected: int) -> None:
        m = bytearray(base)
        off = addr - FUNC_ADDR
        current = struct.unpack_from("<I", m, off)[0]
        if current != expected:
            raise RuntimeError(
                f"mutant anchor 0x{addr:08x}: 0x{current:08x} != 0x{expected:08x}"
            )
        struct.pack_into("<I", m, off, new_word)
        mutants.append((f"mut_{addr:08x}", bytes(m)))

    # 1. Type 0x18 constant in the shortcut gate.
    patch(0x0027D3F0, 0xE3500019, 0xE3500018)
    # 2. Early "busy" return constant.
    patch(0x0027D3B8, 0xE3A00002, 0xE3A00001)
    # 3. Flag id 0x62C in the literal pool.
    patch(0x0027D668, 0x0000062D, 0x0000062C)
    # 4. Published 0x0100007A constant for the 0x62C/0x648 gate.
    patch(0x0027D670, 0x0100007B, 0x0100007A)
    # 5. Flag id 0xB8 for the sub-mode gate.
    patch(0x0027D580, 0xE3A000B9, 0xE3A000B8)
    # 6. First probe constant 0x15F (0x100 + 0x5F).
    patch(0x0027D5C4, 0x12511060, 0x1251105F)
    return mutants


def run_pair(orig_bytes, cand_bytes, relocs, cases, *, cand_is_orig=False):
    for c in cases:
        o = Runner().run(orig_bytes, [], c, is_orig=True)
        if cand_is_orig:
            k = Runner().run(cand_bytes, [], c, is_orig=True)
        else:
            k = Runner().run(cand_bytes, relocs, c, is_orig=False)
        problems = compare(o, k)
        if problems:
            return False, f"{c['name']}: " + "; ".join(problems)
    return True, "ok"


def coverage_check(orig_bytes: bytes, cases: list[dict]) -> list[str]:
    """Require the case set to exercise every helper/decision signature."""
    needed_calls = {
        ("camp_func_0032839c", (0x13, 0)),
        ("script_vm_func_0026fc24", ()),
        ("script_vm_func_001fb434", ()),
        ("script_vm_func_00275984", ()),
        ("script_vm_func_00255050", (0x13,)),
        ("script_vm_func_002857e4", ()),
        ("script_vm_func_002c0ba8", (0x2C,)),
        ("script_vm_func_002c0ba8", (0xB8,)),
        ("script_vm_func_002c0ba8", (0x62C,)),
        ("script_vm_func_002c0ba8", (0x648,)),
        ("script_vm_func_001b48c0", (0x13, 0)),
        ("script_vm_func_0026fcb4", (0x13, 0)),
        ("script_vm_func_0026fcb4", (0x18, 1)),
        ("ui_func_002876d0", (0x01000086,)),
        ("ui_func_002876d0", (0x0100007A,)),
        ("ui_func_002876d0", (0x22220000,)),
        ("script_vm_func_00290694", ()),
        ("script_vm_func_00287afc", ()),
        ("engine_func_00287590", (0x01000086,)),
        ("engine_func_00287590", (0x01000037,)),
        ("engine_func_00287590", (0x01000038,)),
        ("engine_func_00287590", (0x0100007A,)),
        ("engine_func_00287590", (0x22220000,)),
    }
    seen_calls = set()
    seen_returns = set()
    for c in cases:
        out = Runner().run(orig_bytes, [], c, is_orig=True)
        seen_calls.update(out["calls"])
        seen_returns.add(out["ret"])
    problems = []
    missing = needed_calls - seen_calls
    if missing:
        problems.append(f"uncalled signatures: {sorted(missing)}")
    # 1 = busy/other report, 2 = unexpected report, 0xC0DE0001 = tail value.
    for value in (1, 2, 0xC0DE0001):
        if value not in seen_returns:
            problems.append(f"return value 0x{value:08x} never observed")
    return problems


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    start = FUNC_ADDR - 0x00100000
    orig_bytes = orig_all[start : start + FUNC_SIZE]

    cand_bytes, relocs = compile_candidate()
    print(
        f"script_vm_func_0027d35c: original {FUNC_SIZE} B, "
        f"candidate {len(cand_bytes)} B, {len(relocs)} call relocs"
    )

    cases = make_cases()
    ok, msg = run_pair(orig_bytes, cand_bytes, relocs, cases)
    if not ok:
        print(f"FAIL: {msg}")
        return 1

    coverage = coverage_check(orig_bytes, cases)
    if coverage:
        print("FAIL: coverage: " + "; ".join(coverage))
        return 1

    mutants = mutate_bytes(orig_bytes)
    detected = 0
    for mname, mbytes in mutants:
        mok, _ = run_pair(orig_bytes, mbytes, [], cases, cand_is_orig=True)
        if mok:
            print(f"FAIL: {mname} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: script_vm_func_0027d35c (0x{FUNC_ADDR:08x}) matched the pinned "
        f"original across {len(cases)} differential cases and detected "
        f"{detected}/{len(mutants)} mutants"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
