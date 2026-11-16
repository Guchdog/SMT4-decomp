#!/usr/bin/env python3
"""Differential test for script_vm_func_001e2af0 (0x001e2af0) using Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the reconstructed
script_vm_func_001e2af0 body, resolves its direct calls to deterministic stubs
at the pinned helper addresses, and runs the pinned original
(extracted/exefs/code.bin) against the candidate in separate Unicorn machines
with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11 and VFP s16-s31;
  * the ordered call log with every register argument, including the two float
    arguments in s0/s1 handed to 0x002BFDFC (all helpers take no stack args);
  * the 64 KiB engine-context page (only +0xD5B may change), the pending
    command page (words 2..4 must stay put) and the whole 5 MiB image, which
    must not be modified at all;
  * every emulated write must land in the private stack window, the context
    page or the command page.

Coverage: all three suppression gates (including gate ordering), every state
value 0..9 plus out-of-range and negative s8 indices, the case-1 populated-count
boundary (0/1/23/24 and a negative signed value), the unsigned 1800/3600 s
windows and the `elapsed >= 7200` test on their exact boundaries (with the
32-bit wrap of a negative elapsed), the signed s16 half-value comparison at
its equality and minimum/maximum boundaries, and the 9-entry index wrap.

Negative controls mutate the command kind, the first timing gate, the wrap
count and the half-value comparison; each mutant must be detected.
"""

from __future__ import annotations

import hashlib
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
SOURCE = ROOT / "src/engine/leaf_batch41_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_001e2af0"

FUNC_ADDR = 0x001E2AF0
FUNC_SIZE = 420
FUNC_SYMBOL = "script_vm_func_001e2af0"

IMAGE_ADDR = 0x00100000
IMAGE_MAP_SIZE = 0x00500000          # 0x00100000..0x00600000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
CTX_ADDR = 0x00700000
CTX_SIZE = 0x00010000
CMD_ADDR = 0x00710000
CMD_SIZE = 0x00001000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100
PRIVATE_STACK = 0x100                # scratch window either prologue may use
OVERLAY_SIZE = 0x200                 # image window replaced by each candidate

# Absolute fixture locations (inside the mapped image, like the real game).
UI_BLOCK_ADDR = 0x0049F91C
UI_BLOCK_HOLD = 0x18
COMMAND_POINTER_ADDR = 0x00447A98
ADVICE_TABLE_ADDR = 0x00447AB0
ADVICE_ENTRY_STRIDE = 0x60
ADVICE_TEXT_OFFSET = 4
ADVICE_ENTRY_COUNT = 9

STATE_OFFSET = 0xD5B

# Original direct-call targets; stubs sit at the pinned addresses.
STUB_CONTEXT = 0x002C2B1C            # engine_func_002c2b1c
STUB_PROFILE_BYTE = 0x002BFFAC       # script_vm_func_002bffac
STUB_COEFFICIENT_BYTE = 0x002BFF9C   # script_vm_func_002bff9c
STUB_EVENT_FLAG = 0x002C0BA8         # script_vm_func_002c0ba8
STUB_POPULATED_COUNT = 0x002A8A1C    # camp_func_002a8a1c
STUB_SAVE_ENTRY = 0x00290A38         # camp_func_00290a38
STUB_ELAPSED = 0x0025C1DC            # func_0025c1dc
STUB_HALF_VALUE = 0x0033426C         # script_vm_func_0033426c
STUB_CURRENT_VALUE = 0x0028D5B4      # camp_func_0028d5b4
STUB_MESSAGE = 0x002BFDFC            # script_vm_func_002bfdfc

STUB_NAMES = {
    STUB_CONTEXT: "engine_func_002c2b1c",
    STUB_PROFILE_BYTE: "script_vm_func_002bffac",
    STUB_COEFFICIENT_BYTE: "script_vm_func_002bff9c",
    STUB_EVENT_FLAG: "script_vm_func_002c0ba8",
    STUB_POPULATED_COUNT: "camp_func_002a8a1c",
    STUB_SAVE_ENTRY: "camp_func_00290a38",
    STUB_ELAPSED: "func_0025c1dc",
    STUB_HALF_VALUE: "script_vm_func_0033426c",
    STUB_CURRENT_VALUE: "camp_func_0028d5b4",
    STUB_MESSAGE: "script_vm_func_002bfdfc",
}
STUB_BY_SYMBOL = {name: address for address, name in STUB_NAMES.items()}

# No helper in this routine receives architected stack arguments.
STACK_ARGS = {address: 0 for address in STUB_NAMES}

BX_LR = 0xE12FFF1E

CALLEE_SAVED = {
    "r4": arm.UC_ARM_REG_R4,
    "r5": arm.UC_ARM_REG_R5,
    "r6": arm.UC_ARM_REG_R6,
    "r7": arm.UC_ARM_REG_R7,
    "r8": arm.UC_ARM_REG_R8,
    "r9": arm.UC_ARM_REG_R9,
    "r10": arm.UC_ARM_REG_R10,
    "r11": arm.UC_ARM_REG_R11,
}
CALLEE_SAVED_START = {
    "r4": 0x44444444,
    "r5": 0x55555555,
    "r6": 0x66666666,
    "r7": 0x77777777,
    "r8": 0x88888888,
    "r9": 0x99999999,
    "r10": 0xAAAAAAAA,
    "r11": 0xBBBBBBBB,
}
VFP_CALLEE_SAVED = [getattr(arm, f"UC_ARM_REG_S{i}") for i in range(16, 32)]

MESSAGE_COEFFICIENT_BITS = 0x3F34FDF4
COMMAND_SENTINEL = 0xCDCDCDCD


# ---------------------------------------------------------------------------
# Candidate preparation
# ---------------------------------------------------------------------------
def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - IMAGE_ADDR)
        return f.read(FUNC_SIZE)


def image_bytes() -> bytes:
    return ORIG_BIN.read_bytes()


def elf_symbol_value(obj_file: Path, symbol: str) -> int:
    data = Path(obj_file).read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize = struct.unpack_from("<H", data, 46)[0]
    e_shnum = struct.unpack_from("<H", data, 48)[0]
    e_shstrndx = struct.unpack_from("<H", data, 50)[0]
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    symtab = [s for s in sections if s[1] == 2][0]
    strtab = sections[symtab[6]]
    strings = data[strtab[4] : strtab[4] + strtab[5]]
    for index in range(symtab[5] // 16):
        st_name, st_value, _size, _info, _other, _shndx = struct.unpack_from(
            "<IIIBBH", data, symtab[4] + index * 16
        )
        name = strings[st_name:].split(b"\x00")[0].decode("ascii", "replace")
        if name == symbol:
            return st_value
    raise RuntimeError(f"symbol {symbol} not found in {obj_file}")


def sign_extend_24(value: int) -> int:
    return value - 0x1000000 if value & 0x800000 else value


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(Path(obj_file))
    entry = funcs.get(FUNC_SYMBOL)
    if entry is None:
        raise RuntimeError(
            f"{FUNC_SYMBOL} not found in object: " + ", ".join(sorted(funcs))
        )

    raw, relocs = entry
    code = bytearray(raw)
    function_offset = elf_symbol_value(obj_file, FUNC_SYMBOL)

    for rel in relocs:
        if rel.relocation_type in (1, 28, 29):  # R_ARM_PC24 / CALL / JUMP24
            target = STUB_BY_SYMBOL.get(rel.symbol_name)
            if target is None:
                raise RuntimeError(f"unexpected call relocation: {rel}")
            inst = struct.unpack_from("<I", code, rel.offset)[0]
            addend = sign_extend_24(inst & 0x00FFFFFF) << 2
            place = FUNC_ADDR + rel.offset
            displacement = (target + addend - place) >> 2
            struct.pack_into(
                "<I", code, rel.offset,
                (inst & 0xFF000000) | (displacement & 0x00FFFFFF),
            )
        elif rel.relocation_type == 2:  # R_ARM_ABS32 (switch table, .text)
            if rel.symbol_name not in ("", ".text"):
                raise RuntimeError(f"unexpected abs32 relocation: {rel}")
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            struct.pack_into(
                "<I", code, rel.offset, FUNC_ADDR + addend - function_offset
            )
        else:
            raise RuntimeError(f"unhandled relocation type {rel.relocation_type}")
    return bytes(code)


def compile_variant(src_file: Path, obj_file: Path) -> bytes:
    result = compile_tu_armv6k(Path(src_file), Path(obj_file), ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed for {src_file}: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return compile_variant(SOURCE, OUT_DIR / "leaf_batch41_c.o")


def compile_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    return compile_variant(mutant_src, OUT_DIR / f"mutant_{name}.o")


# ---------------------------------------------------------------------------
# Pinned accessor bodies used as deterministic stubs
# ---------------------------------------------------------------------------
def verify_pinned_profile_accessors() -> None:
    """0x002BFF9C/0x002BFFAC are 16-byte byte loads at 0x004C5634+0x1E5/0x1E4."""
    machine = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    machine.mem_map(IMAGE_ADDR, IMAGE_MAP_SIZE)
    machine.mem_map(STACK_ADDR, 0x1000)
    machine.mem_map(TRAP_ADDR, 0x1000)
    machine.mem_write(IMAGE_ADDR, image_bytes())

    fixture = bytes(range(0x00, 0x100)) * 8
    machine.mem_write(0x004C5600, fixture)
    for address, offset in ((STUB_PROFILE_BYTE, 0x1E4),
                            (STUB_COEFFICIENT_BYTE, 0x1E5)):
        machine.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        machine.emu_start(address, TRAP_ADDR, timeout=1_000_000)
        expected = fixture[0x5634 - 0x5600 + offset]
        actual = machine.reg_read(arm.UC_ARM_REG_R0)
        assert actual == expected, (
            f"pinned 0x{address:08x} returned {actual:#x}, expected {expected:#x}"
        )
        machine.ctl_flush_tb()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
def build_advice_table(case: dict) -> bytes:
    page = bytearray(ADVICE_ENTRY_COUNT * ADVICE_ENTRY_STRIDE)
    for index in range(ADVICE_ENTRY_COUNT):
        base = index * ADVICE_ENTRY_STRIDE
        struct.pack_into("<I", page, base, 0x000C3929 + index)
        for byte_index in range(ADVICE_ENTRY_STRIDE - ADVICE_TEXT_OFFSET):
            page[base + ADVICE_TEXT_OFFSET + byte_index] = (
                0x82 if byte_index % 2 == 0 else 0x40 + index
            )
    return bytes(page)


class Machine:
    """One Unicorn machine with deterministic stubs at the pinned addresses."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(IMAGE_ADDR, IMAGE_MAP_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(CTX_ADDR, CTX_SIZE)
        self.uc.mem_map(CMD_ADDR, CMD_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.image = image_bytes()
        self.uc.mem_write(IMAGE_ADDR, self.image)
        # VFP needs CPACR/FPEXC enabled in Unicorn's ARM model.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0xF00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        self.orig_code = get_orig_bytes()
        self._stack_pattern = bytes(
            (index * 37 + 0x5A) & 0xFF for index in range(STACK_SIZE)
        )
        self.call_log: list[tuple] = []
        self.writes: list[tuple[int, int]] = []
        self.case: dict = {}
        self._install_stubs()

    def _install_stubs(self) -> None:
        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", BX_LR))
            self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_stub,
                             begin=address, end=address)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

    # -- stubs ----------------------------------------------------------
    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        return struct.unpack(f"<{count}I", self.uc.mem_read(sp, 4 * count))

    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address],) + args
                             + self._stack_words(STACK_ARGS[address]))

    def _on_stub(self, uc, address, size, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        case = self.case

        if address == STUB_CONTEXT:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, CTX_ADDR)
        elif address == STUB_PROFILE_BYTE:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, case["profile_byte"])
        elif address == STUB_COEFFICIENT_BYTE:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, case["coefficient_byte"])
        elif address == STUB_EVENT_FLAG:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, case["flag"])
        elif address == STUB_POPULATED_COUNT:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, case["populated"])
        elif address == STUB_SAVE_ENTRY:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, case["save_entry"])
        elif address == STUB_ELAPSED:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, case["elapsed"] & 0xFFFFFFFF)
        elif address == STUB_HALF_VALUE:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, case["half_value"] & 0xFFFFFFFF)
        elif address == STUB_CURRENT_VALUE:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, case["current_value"] & 0xFFFFFFFF)
        elif address == STUB_MESSAGE:
            s0 = uc.reg_read(arm.UC_ARM_REG_S0)
            s1 = uc.reg_read(arm.UC_ARM_REG_S1)
            self._log(address, r0, r1, r2, r3, s0, s1)
            uc.reg_write(arm.UC_ARM_REG_R0, 0xA5A50000)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    # -- execution ------------------------------------------------------
    def run(self, candidate: bytes | None, case: dict) -> dict:
        uc = self.uc
        self.case = case
        self.call_log = []
        self.writes = []

        uc.mem_write(FUNC_ADDR, self.image[FUNC_ADDR - IMAGE_ADDR:
                                             FUNC_ADDR - IMAGE_ADDR + OVERLAY_SIZE])
        uc.mem_write(FUNC_ADDR, self.orig_code if candidate is None else candidate)

        # Context page: only the advice index is meaningful.
        uc.mem_write(CTX_ADDR, b"\x00" * CTX_SIZE)
        uc.mem_write(CTX_ADDR + STATE_OFFSET, struct.pack("<B", case["state"] & 0xFF))

        # Pending command page.  Word 0 is both the "pending command" gate that
        # the routine tests through 0x00447A98 and the word it overwrites with
        # kind 2; words 2..4 must stay at the sentinel.
        command_page = bytearray(CMD_SIZE)
        struct.pack_into("<6I", command_page, 0,
                         case["pending"] & 0xFFFFFFFF, COMMAND_SENTINEL,
                         COMMAND_SENTINEL, COMMAND_SENTINEL,
                         COMMAND_SENTINEL, COMMAND_SENTINEL)
        uc.mem_write(CMD_ADDR, bytes(command_page))

        # Absolute globals.
        ui_block = bytearray(0x20)
        ui_block[UI_BLOCK_HOLD] = case["ui_hold"] & 0xFF
        uc.mem_write(UI_BLOCK_ADDR, bytes(ui_block))
        uc.mem_write(COMMAND_POINTER_ADDR, struct.pack("<I", CMD_ADDR))
        uc.mem_write(ADVICE_TABLE_ADDR, build_advice_table(case))

        uc.ctl_flush_tb()
        uc.mem_write(STACK_ADDR, self._stack_pattern)
        image_before = hashlib.sha256(bytes(
            uc.mem_read(IMAGE_ADDR, IMAGE_MAP_SIZE))).digest()

        uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        for name, value in CALLEE_SAVED_START.items():
            uc.reg_write(CALLEE_SAVED[name], value)
        for index, reg in enumerate(VFP_CALLEE_SAVED):
            uc.reg_write(reg, 0x3F000000 + index)

        try:
            uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except unicorn.UcError as error:
            pc = uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(
                f"Crash at PC=0x{pc:08x} on {case['name']}: {error}"
            ) from error
        finally:
            uc.ctl_flush_tb()

        image_after = hashlib.sha256(bytes(
            uc.mem_read(IMAGE_ADDR, IMAGE_MAP_SIZE))).digest()

        allowed_writes = (
            (STACK_ADDR, STACK_ADDR + STACK_SIZE),
            (CTX_ADDR, CTX_ADDR + CTX_SIZE),
            (CMD_ADDR, CMD_ADDR + CMD_SIZE),
        )
        outside = []
        for address, size in self.writes:
            if not any(lo <= address and address + size <= hi
                       for lo, hi in allowed_writes):
                outside.append((address, size))
        stack_writes_inside = sorted({
            (address, size) for address, size in self.writes
            if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
        })

        return {
            "ret": uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "callee_saved_vfp": [uc.reg_read(reg) for reg in VFP_CALLEE_SAVED],
            "call_log": list(self.call_log),
            "context": bytes(uc.mem_read(CTX_ADDR, CTX_SIZE)),
            "commands": bytes(uc.mem_read(CMD_ADDR, CMD_SIZE)),
            "stack_guard": (
                bytes(uc.mem_read(STACK_ADDR, ENTRY_SP - PRIVATE_STACK - STACK_ADDR)),
                bytes(uc.mem_read(ENTRY_SP, STACK_ADDR + STACK_SIZE - ENTRY_SP)),
            ),
            "image_unchanged": image_before == image_after,
            "writes_outside": outside,
            "non_stack_writes": stack_writes_inside,
        }


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------
def make_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "state": 0,
        "ui_hold": 0,
        "pending": 0,
        "profile_byte": 0x12,
        "coefficient_byte": 0x34,
        "flag": 1,
        "populated": 0,
        "save_entry": 0,
        "elapsed": 0,
        "half_value": 100,
        "current_value": 50,
    }
    case.update(overrides)
    return case


def build_cases() -> list[dict]:
    cases: list[dict] = []

    # --- suppression gates and their order
    cases.append(make_case("ui hold set returns profile byte 0x00",
                           ui_hold=1, profile_byte=0x00, pending=0x12345678))
    cases.append(make_case("ui hold set returns profile byte 0xFF",
                           ui_hold=1, profile_byte=0xFF, state=5))
    cases.append(make_case("ui hold clear, pending returns its word",
                           ui_hold=0, profile_byte=0x80, pending=0xDEADBEEF))
    cases.append(make_case("ui hold set wins over pending word",
                           ui_hold=1, profile_byte=0x5A, pending=0x11111111))
    cases.append(make_case("pending word 0xFFFFFFFF",
                           pending=0xFFFFFFFF, profile_byte=0x00))
    cases.append(make_case("event flag clear returns 0",
                           flag=0, state=5, pending=0))
    cases.append(make_case("event flag clear leaves state untouched",
                           flag=0, state=8, half_value=1000, current_value=0))

    # --- default entries: 0, 2, 3, 4 and out-of-range indices
    for state in (0, 2, 3, 4):
        cases.append(make_case(f"state {state} default entry", state=state))
    for state in (9, 10, 0x7F):
        cases.append(make_case(f"state {state} out-of-range entry", state=state))
    for state in (0xFF, 0x80):
        cases.append(make_case(f"state 0x{state:02x} negative entry", state=state))

    # --- state 1: populated-count boundary (`movlt r4, #2`)
    for populated in (0, 1, 23, 24):
        cases.append(make_case(f"state 1 populated {populated}", state=1,
                               populated=populated))
    cases.append(make_case("state 1 populated 0x80000000 (s32 negative)",
                           state=1, populated=0x80000000))

    # --- state 5..7 timing gates (unsigned windows)
    cases.append(make_case("state 5 no save entry chains to 8 (healthy)",
                           state=5, save_entry=0, half_value=100,
                           current_value=50))
    cases.append(make_case("state 5 no save entry chains to 8 (low)",
                           state=5, save_entry=0, half_value=100,
                           current_value=49))
    for elapsed in (0, 1, 1799, 1800, 1801, 3599, 3600, 3601, 7199, 7200,
                    7201, 0x7FFFFFFF, 0xFFFFFFFF):
        cases.append(make_case(
            f"state 5 elapsed 0x{elapsed & 0xFFFFFFFF:08x}", state=5,
            save_entry=1, elapsed=elapsed & 0xFFFFFFFF, half_value=100,
            current_value=50))
    for elapsed in (0, 1799, 1800, 3599, 3600, 3601, 7200, 7201, 0xFFFFFFFF):
        cases.append(make_case(
            f"state 6 elapsed 0x{elapsed & 0xFFFFFFFF:08x}", state=6,
            save_entry=1, elapsed=elapsed & 0xFFFFFFFF))
        cases.append(make_case(
            f"state 7 elapsed 0x{elapsed & 0xFFFFFFFF:08x}", state=7,
            save_entry=1, elapsed=elapsed & 0xFFFFFFFF))
    cases.append(make_case("state 6 no save entry", state=6, save_entry=0))
    cases.append(make_case("state 7 no save entry", state=7, save_entry=0))

    # --- state 8: signed half-value comparison
    for half, current, label in (
        (100, 50, "equal halves reset"),
        (100, 49, "one below half stays"),
        (100, 51, "above half resets"),
        (0, 0, "zero/zero resets"),
        (1, 0, "half of one truncates to zero"),
        (1, 1, "one at half resets"),
        (-1, -1, "negative one truncates to zero"),
        (-1, 0, "zero against negative half"),
        (-3, -1, "negative three truncates to minus one"),
        (-3, -2, "minus two below negative half"),
        (0x7FFF, 0x3FFF, "s16 maximum equal half"),
        (0x7FFF, 0x3FFE, "s16 maximum one below half"),
        (-0x8000, -0x4000, "s16 minimum equal half"),
        (-0x8000, -0x3FFF, "s16 minimum above half"),
    ):
        cases.append(make_case(f"state 8 {label}", state=8,
                               half_value=half & 0xFFFFFFFF,
                               current_value=current & 0xFFFFFFFF))

    # --- forward-argument coverage through the message call
    for profile, coefficient in ((0x00, 0x00), (0x08, 0xFF), (0xFF, 0x01),
                                 (0x04, 0x80)):
        cases.append(make_case(
            f"message args profile 0x{profile:02x} coefficient 0x{coefficient:02x}",
            state=3, profile_byte=profile, coefficient_byte=coefficient))

    return cases


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------
def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "callee_saved_vfp",
                "call_log", "context", "commands", "stack_guard",
                "image_unchanged", "writes_outside", "non_stack_writes"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["sp"] != ENTRY_SP:
        problems.append(f"SP not restored: 0x{orig['sp']:08x}")
    if orig["pc"] != TRAP_ADDR:
        problems.append(f"PC not at trap: 0x{orig['pc']:08x}")
    if not orig["image_unchanged"] or not cand["image_unchanged"]:
        problems.append("pinned image was modified by the call")
    return problems


def main() -> None:
    print("Testing script_vm_func_001e2af0 (0x001e2af0)...")
    verify_pinned_profile_accessors()
    print("  [PASS] pinned 0x002bff9c/0x002bffac byte loads match the stubs")

    cand_code = compile_candidate()
    orig_code = get_orig_bytes()
    print(f"  original: {len(orig_code)} B, candidate: {len(cand_code)} B")

    machine = Machine()
    cases = build_cases()
    passed = 0
    for case_data in cases:
        res_orig = machine.run(None, case_data)
        res_cand = machine.run(cand_code, case_data)
        problems = compare(res_orig, res_cand)
        if problems:
            print(f"  [FAIL] {case_data['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case_data['name']}  "
              f"(r0=0x{res_cand['ret']:08x}, {len(res_cand['call_log'])} calls)")

    print("\nNegative controls:")
    mutants = [
        ("command_kind",
         "constexpr u32 kCommandKind = 2;",
         "constexpr u32 kCommandKind = 3;"),
        ("first_gate",
         "constexpr u32 kSaveGateWindow = 0x0708;   // 1800 s",
         "constexpr u32 kSaveGateWindow = 0x0709;   // 1800 s"),
        ("wrap_count",
         "constexpr u32 kAdviceEntryCount = 9;",
         "constexpr u32 kAdviceEntryCount = 8;"),
        ("half_comparison",
         "        if (current_value >= half_value / 2) {",
         "        if (current_value > half_value / 2) {"),
        ("forwarded_flags",
         "constexpr u32 kAdviceFlagsOr = 4;",
         "constexpr u32 kAdviceFlagsOr = 5;"),
    ]
    for name, old, new in mutants:
        mutant_code = compile_mutant(name, old, new)
        detected = False
        for case_data in cases:
            res_orig = machine.run(None, case_data)
            res_mut = machine.run(mutant_code, case_data)
            if compare(res_orig, res_mut):
                detected = True
                break
        assert detected, f"negative control not detected: {name}"
        print(f"  [PASS] mutant detected: {name}")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
