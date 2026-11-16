#!/usr/bin/env python3
"""Differential test for engine_func_0037a8d8 (0x0037a8d8) using Unicorn ARM.

The routine initializes one engine object: it writes the header fields, copies
the 0x00420870 vtable-table entry into the embedded base subobject at +0x14
(including the MSVC virtual-base `vftable[-0x30]` fixup), resets the range and
flag fields, then queries the resource block through 0x002bb88c.  A negative
status either returns through the stored error callback or, when the resource's
+0x1C byte is zero, is reported through 0x002bbd10 before continuing.

Every direct call is replaced with a deterministic stub.  The original and the
compiled candidate run with identical fixtures; the test compares the ordered
call log, return value, continuation PC/SP, callee-saved integer and VFP
registers, the whole self block, the resource block, the vtable-table slot and
the fake-vftable window.

The stack output buffer of 0x002bb88c is a local whose address legitimately
differs between the two bodies, so the call log records it as "<stack out>";
the stub asserts it is aligned and inside the stack instead.
"""

import struct
import sys
from pathlib import Path

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
FUNC_ADDR = 0x0037A8D8
FUNC_SIZE = 400
TU_PATH = ROOT / "src/engine/leaf_batch44_b.cpp"
OUT_DIR = ROOT / "build/test_leaf_0037a8d8"

# ---------------------------------------------------------------------------
# Emulated address space
# ---------------------------------------------------------------------------
IMAGE_ADDR = 0x00100000
IMAGE_MAP_SIZE = 0x00500000          # 0x00100000..0x00600000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
RODATA_ADDR = 0x00600000
RODATA_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

SELF_ADDR = 0x00450000
SELF_WATCH = 0x60
RES_ADDR = 0x00451000
RES_WATCH = 0x30
FAKE_VFT_ADDR = 0x00452000
FAKE_VFT_WATCH = 0x40

TABLE_ADDR = 0x00420870              # g_AsdFileVTableTable slot
TABLE_WATCH = 0x10
VBASE_WORD_ADDR = TABLE_ADDR + 0x0C  # 0x0042087C, table+0x0C

CALLBACK_ADDR = 0x90000100

SELF_SENTINEL = 0xA5

# Direct-call stubs (original branch targets).
STUB_2BB88C = 0x002BB88C
STUB_2BBD10 = 0x002BBD10
STUB_235EEC = 0x00235EEC
STUB_2B93F0 = 0x002B93F0

STUB_BY_SYMBOL = {
    "engine_func_002bb88c": STUB_2BB88C,
    "nn_sdk_func_002bbd10": STUB_2BBD10,
    "func_00235eec": STUB_235EEC,
    "engine_func_002b93f0": STUB_2B93F0,
}
ABS32_TARGETS = {
    "g_AsdFileVTableTable": TABLE_ADDR,
}

BX_LR = 0xE12FFF1E

# 0x00420870 slot read from the pinned image.
EXPECTED_TABLE = (0x004208B0, 0x003FF29C, 0x003FF29C, 0x004208B0)
EXPECTED_VBASE_WORD = 0                    # [0x004208B0 - 0x30]

VFTABLE_INIT = 0x00421774                  # object vftable written to +0x00
STATUS_INIT = 0xE7E3FFFF                   # initial status written to +0x2C


# ---------------------------------------------------------------------------
# Candidate preparation
# ---------------------------------------------------------------------------
def get_orig_bytes():
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def image_bytes():
    return ORIG_BIN.read_bytes()


def table_bytes():
    image = image_bytes()
    offset = TABLE_ADDR - IMAGE_ADDR
    return image[offset:offset + TABLE_WATCH]


def vbase_word():
    image = image_bytes()
    offset = EXPECTED_TABLE[0] - 0x30 - IMAGE_ADDR
    return struct.unpack_from("<I", image, offset)[0]


def get_symbol_value(obj_file, wanted):
    """Return st_value for `wanted` in the object's symbol table."""
    data = Path(obj_file).read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize = struct.unpack_from("<H", data, 46)[0]
    e_shnum = struct.unpack_from("<H", data, 48)[0]
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    symtab = [s for s in sections if s[1] == 2][0]
    strtab = sections[symtab[6]]
    for i in range(symtab[5] // 16):
        st = struct.unpack_from("<IIIBBH", data, symtab[4] + i * 16)
        name = data[strtab[4] + st[0]:].split(b"\x00")[0].decode(
            "ascii", "replace")
        if name == wanted:
            return st[1] & ~1
    raise RuntimeError(f"symbol {wanted} not found in {obj_file}")


def sign_extend_24(value):
    return value - 0x1000000 if value & 0x800000 else value


def read_object_section(obj_file, wanted):
    data = Path(obj_file).read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize = struct.unpack_from("<H", data, 46)[0]
    e_shnum = struct.unpack_from("<H", data, 48)[0]
    e_shstrndx = struct.unpack_from("<H", data, 50)[0]
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    shstrtab = sections[e_shstrndx]
    shstr = data[shstrtab[4]:shstrtab[4] + shstrtab[5]]
    for section in sections:
        name = shstr[section[0]:].split(b"\x00")[0].decode("ascii", "replace")
        if name.startswith(wanted):
            return data[section[4]:section[4] + section[5]]
    raise RuntimeError(f"section {wanted!r} not found in {obj_file}")


def compile_variant(src_file, obj_file):
    result = compile_tu_armv6k(Path(src_file), Path(obj_file), ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed for {src_file}: {result.stderr}")

    funcs = extract_elf_functions_detailed(Path(obj_file))
    entry = funcs.get("engine_func_0037a8d8")
    if entry is None:
        raise RuntimeError(
            "engine_func_0037a8d8 not found in object: "
            + ", ".join(sorted(funcs))
        )

    func_value = get_symbol_value(obj_file, "engine_func_0037a8d8")
    raw, relocs = entry
    code = bytearray(raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            target = STUB_BY_SYMBOL.get(rel.symbol_name)
            if target is None:
                raise RuntimeError(f"unexpected call relocation: {rel}")
            inst = struct.unpack_from("<I", code, rel.offset)[0]
            addend = sign_extend_24(inst & 0x00FFFFFF) << 2
            place = FUNC_ADDR + rel.offset
            disp = (target + addend - place) >> 2
            struct.pack_into(
                "<I", code, rel.offset, (inst & 0xFF000000) | (disp & 0x00FFFFFF)
            )
        elif rel.relocation_type == 2:  # R_ARM_ABS32
            literal = struct.unpack_from("<I", code, rel.offset)[0]
            if rel.symbol_name in ABS32_TARGETS:
                if literal != 0:
                    raise RuntimeError(f"unexpected addend in {rel}")
                value = ABS32_TARGETS[rel.symbol_name]
            elif rel.symbol_name == "":
                # Local label address (`&&report_site`): the in-place addend is
                # the .text offset of the label.  Rebase it into the candidate
                # body placed at FUNC_ADDR.
                value = FUNC_ADDR + literal - func_value
                if not (FUNC_ADDR <= value < FUNC_ADDR + len(code)):
                    raise RuntimeError(
                        f"label relocation outside the function: {rel} "
                        f"addend=0x{literal:x} value=0x{value:x}"
                    )
            else:
                raise RuntimeError(f"unexpected abs32 relocation: {rel}")
            struct.pack_into("<I", code, rel.offset, value)
        else:
            raise RuntimeError(f"unsupported relocation: {rel}")

    return bytes(code), read_object_section(obj_file, ".rodata")


def compile_candidate():
    return compile_variant(TU_PATH, OUT_DIR / "leaf_batch44_b.o")


def compile_mutant(name, old, new):
    text = TU_PATH.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    return compile_variant(mutant_src, OUT_DIR / f"mutant_{name}.o")


# ---------------------------------------------------------------------------
# Machine
# ---------------------------------------------------------------------------
class Machine:
    def __init__(self):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(IMAGE_ADDR, IMAGE_MAP_SIZE)
        self.uc.mem_map(RODATA_ADDR, RODATA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        # The original copies the two stack words with vldmia/vstmia, so the
        # VFP coprocessor CP10/CP11 must be enabled.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        self.original_image = image_bytes()
        self.uc.mem_write(IMAGE_ADDR, self.original_image)
        self.table = table_bytes()
        self.orig_code = get_orig_bytes()

        self.call_log = []
        self.case = None
        self.entry_sp = STACK_ADDR + STACK_SIZE - 0x100
        self._install_stubs()

    def _install_stubs(self):
        bx_lr = struct.pack("<I", BX_LR)
        stubs = [
            (STUB_2BB88C, self._on_2bb88c),
            (STUB_2BBD10, self._on_2bbd10),
            (STUB_235EEC, self._on_235eec),
            (STUB_2B93F0, self._on_2b93f0),
            (CALLBACK_ADDR, self._on_callback),
        ]
        for address, hook in stubs:
            self.uc.mem_write(address, bx_lr)
            self.uc.hook_add(unicorn.UC_HOOK_CODE, hook, begin=address, end=address)

    # -- stub bodies ------------------------------------------------------
    def _write_u32(self, address, value):
        self.uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))

    def _read_u32(self, address):
        return struct.unpack("<I", self.uc.mem_read(address, 4))[0]

    def _on_2bb88c(self, uc, address, size, user_data):
        handle_block = uc.reg_read(arm.UC_ARM_REG_R0)
        out = uc.reg_read(arm.UC_ARM_REG_R1)
        assert out & 3 == 0, f"unaligned output buffer 0x{out:08x}"
        assert STACK_ADDR <= out < STACK_ADDR + STACK_SIZE, (
            f"output buffer outside the stack: 0x{out:08x}"
        )
        handle = self._read_u32(handle_block)
        self.call_log.append(
            ("engine_func_002bb88c", handle_block, "<stack out>", handle)
        )
        status = self.case["status"]
        if status >= 0:
            lo = self.case["out_lo"]
            hi = self.case["out_hi"]
            self._write_u32(handle_block + 0x0C, lo)
            self._write_u32(handle_block + 0x10, hi)
            self._write_u32(out, lo)
            self._write_u32(out + 4, hi)
        else:
            # The real helper zeroes handle_block+0x0C/+0x10 and leaves the
            # caller's output buffer untouched on failure.
            self._write_u32(handle_block + 0x0C, 0)
            self._write_u32(handle_block + 0x10, 0)
        uc.reg_write(arm.UC_ARM_REG_R0, status & 0xFFFFFFFF)

    def _on_2bbd10(self, uc, address, size, user_data):
        status = uc.reg_read(arm.UC_ARM_REG_R0)
        site = uc.reg_read(arm.UC_ARM_REG_R1)
        kind = uc.reg_read(arm.UC_ARM_REG_R2)
        assert FUNC_ADDR <= site < FUNC_ADDR + 0x200, (
            f"report site is not a code address inside the routine: "
            f"0x{site:08x}"
        )
        self.call_log.append(("nn_sdk_func_002bbd10", status, "<code site>", kind))

    def _on_235eec(self, uc, address, size, user_data):
        range_addr = uc.reg_read(arm.UC_ARM_REG_R0)
        offset = uc.reg_read(arm.UC_ARM_REG_R1)
        mode = uc.reg_read(arm.UC_ARM_REG_R2)
        self.call_log.append(("func_00235eec", range_addr, offset, mode))
        if mode == 0:
            self._write_u32(range_addr + 4, 0)
        elif mode == 2:
            self._write_u32(range_addr + 4, self._read_u32(range_addr))
        if offset != 0:
            # The real helper clamps a nonzero offset into the range; the
            # routine under test always passes 0, so this stays unused.
            start = self._read_u32(range_addr)
            length = self._read_u32(range_addr + 4)
            target = start + offset
            self._write_u32(range_addr + 4, max(min(target, start + length), start)
                            - start)

    def _on_2b93f0(self, uc, address, size, user_data):
        self.call_log.append(("engine_func_002b93f0", uc.reg_read(arm.UC_ARM_REG_R0)))

    def _on_callback(self, uc, address, size, user_data):
        code = uc.reg_read(arm.UC_ARM_REG_R0)
        arg = uc.reg_read(arm.UC_ARM_REG_R1)
        self.call_log.append(("error_callback", code, arg))

    # -- fixtures ---------------------------------------------------------
    def _reset_fixtures(self, case):
        self.uc.mem_write(SELF_ADDR, bytes([SELF_SENTINEL]) * SELF_WATCH)
        self.uc.mem_write(SELF_ADDR + 0x52,
                          bytes([case["initialized_52"]]))

        self.uc.mem_write(RES_ADDR, bytes([SELF_SENTINEL]) * RES_WATCH)
        self._write_u32(RES_ADDR + 0x04, case["handle"])
        self.uc.mem_write(RES_ADDR + 0x1C, bytes([case["quiet"]]))

        self.uc.mem_write(TABLE_ADDR, self.table)
        self._write_u32(TABLE_ADDR + 0x00, case["vftable"])
        self._write_u32(TABLE_ADDR + 0x0C, case["self_ptr"])

        self.uc.mem_write(FAKE_VFT_ADDR - 0x30,
                          bytes([0x5A]) * FAKE_VFT_WATCH)
        self._write_u32(FAKE_VFT_ADDR - 0x30, case["vb_offset"])

    def run(self, candidate, case):
        """candidate = None runs the pinned original."""
        uc = self.uc
        self.case = case
        self.call_log = []

        self._reset_fixtures(case)
        if candidate is None:
            uc.mem_write(FUNC_ADDR, self.orig_code)
        else:
            code, rodata = candidate
            if rodata:
                uc.mem_write(RODATA_ADDR, rodata)
            uc.mem_write(FUNC_ADDR, code)
        uc.ctl_flush_tb()

        sp = self.entry_sp
        uc.mem_write(STACK_ADDR, bytes([SELF_SENTINEL]) * STACK_SIZE)
        self._write_u32(sp, case["callback"])
        self._write_u32(sp + 4, case["callback_arg"])
        uc.reg_write(arm.UC_ARM_REG_SP, sp)
        uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R1, RES_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R2, case["field_40"])
        uc.reg_write(arm.UC_ARM_REG_R3, case["field_44"])
        for index, reg in enumerate(
            [
                arm.UC_ARM_REG_R4, arm.UC_ARM_REG_R5, arm.UC_ARM_REG_R6,
                arm.UC_ARM_REG_R7, arm.UC_ARM_REG_R8, arm.UC_ARM_REG_R9,
                arm.UC_ARM_REG_R10, arm.UC_ARM_REG_R11,
            ]
        ):
            uc.reg_write(reg, 0x11110000 + index * 0x11)
        for index in range(16, 32):
            uc.reg_write(getattr(arm, f"UC_ARM_REG_S{index}"), 0x3F000000 + index)

        try:
            uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5000000)
        except unicorn.UcError as exc:
            raise RuntimeError(
                f"Crash at PC=0x{uc.reg_read(arm.UC_ARM_REG_PC):08x}: {exc}"
            ) from exc

        return {
            "call_log": list(self.call_log),
            "r0": uc.reg_read(arm.UC_ARM_REG_R0),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "callee_saved": [
                uc.reg_read(reg)
                for reg in [
                    arm.UC_ARM_REG_R4, arm.UC_ARM_REG_R5, arm.UC_ARM_REG_R6,
                    arm.UC_ARM_REG_R7, arm.UC_ARM_REG_R8, arm.UC_ARM_REG_R9,
                    arm.UC_ARM_REG_R10, arm.UC_ARM_REG_R11,
                ]
            ],
            "callee_saved_vfp": [
                uc.reg_read(getattr(arm, f"UC_ARM_REG_S{i}"))
                for i in range(16, 32)
            ],
            "self": bytes(uc.mem_read(SELF_ADDR, SELF_WATCH)),
            "resource": bytes(uc.mem_read(RES_ADDR, RES_WATCH)),
            "table": bytes(uc.mem_read(TABLE_ADDR, TABLE_WATCH)),
            "fake_vft": bytes(
                uc.mem_read(FAKE_VFT_ADDR - 0x30, FAKE_VFT_WATCH)),
        }


# ---------------------------------------------------------------------------
# Independent expected model
# ---------------------------------------------------------------------------
def expected_case(case):
    """Return (call_log, self_bytes, resource_bytes)."""
    log = []
    selfmem = bytearray([SELF_SENTINEL]) * SELF_WATCH
    selfmem[0x52] = case["initialized_52"]

    def self_w32(off, value):
        struct.pack_into("<I", selfmem, off, value & 0xFFFFFFFF)

    def self_w8(off, value):
        selfmem[off] = value & 0xFF

    # Object initialisation.
    self_w8(0x04, 0)
    self_w32(0x0C, 0)
    self_w32(0x00, VFTABLE_INIT)
    self_w32(0x10, 0)
    for off in (0x18, 0x1C, 0x20, 0x24, 0x28):
        self_w32(off, 0)
    self_w32(0x14, case["vftable"])
    base_target = 0x14 + case["vb_offset"]
    if 0 <= base_target <= SELF_WATCH - 4:
        self_w32(base_target, case["self_ptr"])
    self_w32(0x2C, STATUS_INIT)
    self_w32(0x34, RES_ADDR)
    self_w32(0x38, 0)
    self_w32(0x3C, 0)
    self_w32(0x40, case["field_40"])
    self_w32(0x44, case["field_44"])
    self_w32(0x48, case["callback"])
    self_w32(0x4C, case["callback_arg"])
    self_w8(0x50, 0)
    self_w8(0x51, 0)

    # Resource query.
    res = bytearray([SELF_SENTINEL]) * RES_WATCH
    struct.pack_into("<I", res, 0x04, case["handle"] & 0xFFFFFFFF)
    res[0x1C] = case["quiet"]

    log.append(("engine_func_002bb88c", RES_ADDR + 0x04, "<stack out>",
                case["handle"] & 0xFFFFFFFF))
    status = case["status"]
    if status >= 0:
        struct.pack_into("<I", res, 0x10, case["out_lo"] & 0xFFFFFFFF)
        struct.pack_into("<I", res, 0x14, case["out_hi"] & 0xFFFFFFFF)
        output = case["out_lo"] & 0xFFFFFFFF
    else:
        struct.pack_into("<I", res, 0x10, 0)
        struct.pack_into("<I", res, 0x14, 0)
        # Quiet path pre-clears the output buffer; the reporting path does not,
        # so the stale stack sentinel is forwarded.
        output = 0 if case["quiet"] else 0xA5A5A5A5

    if case["quiet"]:
        struct.pack_into("<I", res, 0x18, status & 0xFFFFFFFF)
        if status < 0:
            if case["callback"]:
                log.append(("error_callback", status & 0xFFFFFFFF,
                            case["callback_arg"] & 0xFFFFFFFF))
            return log, bytes(selfmem), bytes(res)
    elif status < 0:
        log.append(("nn_sdk_func_002bbd10", status & 0xFFFFFFFF,
                    "<code site>", 1))

    if case["field_44"] == 0:
        self_w32(0x44, output)
    self_w32(0x38, output)
    log.append(("func_00235eec", SELF_ADDR + 0x38, 0, 0))
    self_w8(0x52, 0)
    self_w8(0x50, 1)
    return log, bytes(selfmem), bytes(res)


def make_case(name, **kwargs):
    case = {
        "name": name,
        "quiet": 0,
        "status": 0,
        "out_lo": 0x11111111,
        "out_hi": 0x22222222,
        "handle": 0x00465001,
        "field_40": 0x40404040,
        "field_44": 0,
        "callback": 0,
        "callback_arg": 0,
        "initialized_52": 0,
        "vftable": EXPECTED_TABLE[0],
        "self_ptr": EXPECTED_TABLE[3],
        "vb_offset": EXPECTED_VBASE_WORD,
    }
    case.update(kwargs)
    return case


def build_cases():
    return [
        make_case("quiet, status 0, zero field_44 -> output copied",
                  quiet=1, status=0),
        make_case("quiet, status 1, nonzero field_44 preserved",
                  quiet=1, status=1, field_44=0x33333333,
                  out_lo=0, out_hi=0xFFFFFFFF),
        make_case("quiet, status 0x7fffffff (positive boundary)",
                  quiet=1, status=0x7FFFFFFF, out_lo=0x01020304,
                  out_hi=0x05060708),
        make_case("quiet, status -1, null callback",
                  quiet=1, status=-1),
        make_case("quiet, status -1, error callback invoked",
                  quiet=1, status=-1, callback=CALLBACK_ADDR,
                  callback_arg=0xDEADBEEF),
        make_case("quiet, status 0x80000000 (signed negative boundary)",
                  quiet=1, status=-0x80000000, callback=CALLBACK_ADDR,
                  callback_arg=0, out_lo=0xCAFEBABE),
        make_case("quiet, negative status keeps initialized_52",
                  quiet=1, status=-2, callback=CALLBACK_ADDR,
                  initialized_52=0xFF),
        make_case("reporting, status 0, no report",
                  quiet=0, status=0, out_lo=0x0BADF00D),
        make_case("reporting, status 7, zero field_44",
                  quiet=0, status=7, field_44=0, out_lo=0x76543210,
                  out_hi=0xFEDCBA98),
        make_case("reporting, negative status reported, stale output used",
                  quiet=0, status=-1, callback=CALLBACK_ADDR,
                  callback_arg=0x12345678),
        make_case("reporting, 0x80000000, stale output fills field_44",
                  quiet=0, status=-0x80000000, field_44=0,
                  callback=CALLBACK_ADDR),
        make_case("nonzero virtual-base offset 4 rewrites +0x18",
                  quiet=1, status=0, vftable=FAKE_VFT_ADDR,
                  self_ptr=0x12345678, vb_offset=4),
        make_case("virtual-base offset 0x18 targets +0x2c, sentinel wins",
                  quiet=1, status=0, vftable=FAKE_VFT_ADDR,
                  self_ptr=0x99999999, vb_offset=0x18),
        make_case("virtual-base offset 0x1c reaches untouched +0x30",
                  quiet=1, status=0, vftable=FAKE_VFT_ADDR,
                  self_ptr=0xABCDEF01, vb_offset=0x1C),
        make_case("success clears initialized_52",
                  quiet=1, status=0, initialized_52=0xA5),
        make_case("tagged handle with reporting negative status",
                  quiet=0, status=-1, handle=0x00465001,
                  out_lo=0xFFFFFFFF),
        make_case("quiet negative with initialized_52 0xff and null callback",
                  quiet=1, status=-1, initialized_52=0xFF),
    ]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def check_expectations(case, result):
    log, expected_self, expected_res = expected_case(case)
    assert result["call_log"] == log, (
        f"expected call log mismatch on {case['name']}:\n"
        f"  Expected: {log}\n  Actual:   {result['call_log']}"
    )
    assert result["r0"] == SELF_ADDR, (
        f"return mismatch on {case['name']}: 0x{result['r0']:08x}"
    )
    if result["self"] != expected_self:
        for i in range(0, SELF_WATCH, 4):
            exp = expected_self[i:i + 4]
            act = result["self"][i:i + 4]
            if exp != act:
                print(f"    self+0x{i:02x}: exp {exp.hex()} act {act.hex()}")
        raise AssertionError(f"self block mismatch on {case['name']}")
    if result["resource"] != expected_res:
        for i in range(0, RES_WATCH, 4):
            exp = expected_res[i:i + 4]
            act = result["resource"][i:i + 4]
            if exp != act:
                print(f"    res+0x{i:02x}: exp {exp.hex()} act {act.hex()}")
        raise AssertionError(f"resource block mismatch on {case['name']}")


def main():
    print("Testing engine_func_0037a8d8 (0x0037a8d8)...")
    assert table_bytes() == struct.pack("<4I", *EXPECTED_TABLE), (
        "0x00420870 slot does not match the recorded values: "
        + table_bytes().hex()
    )
    assert vbase_word() == EXPECTED_VBASE_WORD, (
        "[0x004208B0 - 0x30] does not match the recorded value"
    )

    cand = compile_candidate()
    print(f"  original: {FUNC_SIZE} B, candidate: {len(cand[0])} B")

    machine = Machine()
    cases = build_cases()

    passed = 0
    for case in cases:
        res_orig = machine.run(None, case)
        res_cand = machine.run(cand, case)

        assert res_orig["call_log"] == res_cand["call_log"], (
            f"call log mismatch on {case['name']}:\n"
            f"  Orig: {res_orig['call_log']}\n  Cand: {res_cand['call_log']}"
        )
        assert res_orig["r0"] == res_cand["r0"], (
            f"return mismatch on {case['name']}: "
            f"0x{res_orig['r0']:08x} != 0x{res_cand['r0']:08x}"
        )
        assert res_orig["self"] == res_cand["self"], (
            f"object memory mismatch on {case['name']}"
        )
        assert res_orig["resource"] == res_cand["resource"], (
            f"resource memory mismatch on {case['name']}"
        )
        assert res_orig["table"] == res_cand["table"], (
            f"vtable-table mismatch on {case['name']}"
        )
        assert res_orig["fake_vft"] == res_cand["fake_vft"], (
            f"fake-vftable mismatch on {case['name']}"
        )
        assert res_orig["sp"] == res_cand["sp"] == machine.entry_sp, (
            f"SP mismatch on {case['name']}: "
            f"0x{res_orig['sp']:08x} / 0x{res_cand['sp']:08x}"
        )
        assert res_orig["pc"] == res_cand["pc"] == TRAP_ADDR, (
            f"PC mismatch on {case['name']}: "
            f"0x{res_orig['pc']:08x} / 0x{res_cand['pc']:08x}"
        )
        assert res_orig["callee_saved"] == res_cand["callee_saved"], (
            f"callee-saved register mismatch on {case['name']}"
        )
        assert res_orig["callee_saved_vfp"] == res_cand["callee_saved_vfp"], (
            f"callee-saved VFP register mismatch on {case['name']}"
        )
        check_expectations(case, res_cand)

        passed += 1
        print(f"  [PASS] {case['name']}")

    print("\nNegative controls:")
    mutants = [
        (
            "quiet_flag_inverted",
            "    if (resource->quiet_1c == 0) {",
            "    if (resource->quiet_1c != 0) {",
        ),
        (
            "field_44_condition_inverted",
            "    if (field_44 == 0) {",
            "    if (field_44 != 0) {",
        ),
        (
            "initial_status_wrong",
            "    self->status_2c = 0xE7E3FFFFu;",
            "    self->status_2c = 0xE7E3FFFEu;",
        ),
        (
            "virtual_base_offset_shifted",
            "static_cast<const u8*>(base_vftable) - 0x30);",
            "static_cast<const u8*>(base_vftable) - 0x2c);",
        ),
        (
            "callback_arguments_swapped",
            "                error_callback(code, self->callback_arg_4c);",
            "                error_callback(self->callback_arg_4c, code);",
        ),
        (
            "negative_test_uses_le",
            "        const s32 status = engine_func_002bb88c(&resource->handle_04, result);\n"
            "        if (status < 0) {",
            "        const s32 status = engine_func_002bb88c(&resource->handle_04, result);\n"
            "        if (status <= 0) {",
        ),
    ]
    for name, old, new in mutants:
        mutant = compile_mutant(name, old, new)
        detected = False
        fault = None
        for case in cases:
            res_orig = machine.run(None, case)
            try:
                res_mut = machine.run(mutant, case)
            except RuntimeError as exc:
                # A fault (e.g. a shifted virtual-base offset writing outside
                # the mapped object) is itself a detected difference.
                detected = True
                fault = exc
                break
            if res_orig != res_mut:
                detected = True
                break
        assert detected, f"negative control not detected: {name}"
        if fault is None:
            print(f"  [PASS] mutant detected: {name}")
        else:
            print(f"  [PASS] mutant detected: {name} (fault: {fault})")
    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
