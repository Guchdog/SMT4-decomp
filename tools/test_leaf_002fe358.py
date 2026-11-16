#!/usr/bin/env python3
"""Differential test for ui_func_002fe358 (0x002fe358) using Unicorn ARM.

Compiles ``src/engine/leaf_batch45_a.cpp``, extracts the ``ui_func_002fe358``
body, resolves its six direct-call relocations to deterministic stubs and runs
the pinned original (``extracted/exefs/code.bin``) against the candidate on
separate Unicorn ARM machines with identical fixtures.

Recovered contract (see ``docs/function-records/002fe358.md``)::

    s32 ui_func_002fe358(OutputRecord* out, s32 capacity,
                         const u8* descriptor, const CatalogSlot* catalog,
                         s32 catalog_count);

Compared per case:
  * return r0, continuation PC, final SP, callee-saved r4-r11 and s16-s31;
  * the ordered call log, including register arguments and the architected
    stack word of 0x002FE600;
  * the full source bytes handed to 0x002FE600 (stack-local descriptor below
    1300 units, forwarded descriptor at or above it);
  * the full output, descriptor and catalog pages (byte for byte);
  * every emulated write outside the private stack and the output page.

Coverage: type 0 local/forward paths, type 1 copy path, unknown types; time
boundaries 1099/1100/1199/1200/1201/1299/1300/1301 and negative/extreme digit
bytes; all three block bases (0xD8/0xDC/0xF4); count 0, partial, exact and
capped-at-capacity; wrapped span; capacity 0/1/8; catalog_count 0/negative;
catalog matches at index 0/5/200/256, misses, duplicate keys and the
0xFFFFFFFF/-1 key; sentinel fill; exact-1200 +0x14 clearing; and the
0x002FE600 return value propagated to the caller.

Negative controls mutate the time threshold, block base, catalog stride and
sub-block group offset of the candidate; each mutant must be detected.
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed  # noqa: E402
from tools.build_check import compile_tu_armv6k  # noqa: E402

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
SOURCE_FILE = ROOT / "src/engine/leaf_batch45_a.cpp"
OUT_DIR = ROOT / "build/test_leaf_002fe358"

FUNC_ADDR = 0x002FE358
FUNC_SIZE = 680

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000
DESC_ADDR = 0x00700000
DESC_SIZE = 0x00020000
CATALOG_ADDR = 0x00730000
CATALOG_SIZE = 0x00020000
OUT_ADDR = 0x00750000
OUT_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_2BCF58 = 0x002BCF58
STUB_2C5F58 = 0x002C5F58
STUB_2FE600 = 0x002FE600
STUB_2E2750 = 0x002E2750

STUB_NAMES = {
    STUB_2BCF58: "ui_func_002bcf58",
    STUB_2C5F58: "ui_func_002c5f58",
    STUB_2FE600: "ui_func_002fe600",
    STUB_2E2750: "ui_func_002e2750",
}

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
VFP_CALLEE_SAVED = {
    f"s{index}": getattr(arm, f"UC_ARM_REG_S{index}") for index in range(16, 32)
}
VFP_CALLEE_SAVED_START = {
    f"s{index}": 0x3E800000 | index for index in range(16, 32)
}

RECORD_STRIDE = 0x20
CATALOG_STRIDE = 0x48
GROUP_STRIDE = 0x14
GROUP_COUNT = 10
GROUP_BYTES = GROUP_STRIDE * GROUP_COUNT

# Reference time encoding: (s8@+4 - 0x30)*1000 + (s8@+5)*100 + (s8@+6)*10 +
# (s8@+7) - 0x12C0 - 0x210.
TIME_BASE = 0x12C0 + 0x210


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        data = handle.read(FUNC_SIZE)
    if len(data) != FUNC_SIZE:
        raise RuntimeError("could not read the pinned original function")
    return data


def normalise_original_calls(code: bytes) -> bytes:
    """Rewrite the BLX to 0x002C5F58 as an ARM BL for the shared ARM stubs."""
    out = bytearray(code)
    seen = set()
    for offset in range(0, len(out) - 3, 4):
        word = struct.unpack_from("<I", out, offset)[0]
        pc = FUNC_ADDR + offset + 8
        if (word & 0xFE000000) == 0xFA000000:  # BLX (immediate)
            immediate = word & 0x00FFFFFF
            if immediate & 0x00800000:
                immediate -= 0x01000000
            half = (word >> 24) & 1
            target = (pc & ~3) + (immediate << 2) + (half << 1)
        elif (word & 0x0F000000) == 0x0B000000:  # BL
            immediate = word & 0x00FFFFFF
            if immediate & 0x00800000:
                immediate -= 0x01000000
            target = pc + immediate * 4
        else:
            continue
        if target not in STUB_NAMES:
            continue
        displacement = (target - pc) >> 2
        struct.pack_into(
            "<I", out, offset, 0xEB000000 | (displacement & 0x00FFFFFF)
        )
        seen.add(target)
    if seen != set(STUB_NAMES):
        raise RuntimeError(f"original call sites not understood: {sorted(seen)}")
    return bytes(out)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = funcs.get("ui_func_002fe358")
    if candidate is None:
        for name, value in funcs.items():
            if "002fe358" in name:
                candidate = value
                break
    if candidate is None:
        raise RuntimeError(
            f"ui_func_002fe358 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    resolved = []
    for rel in relocs:
        if rel.relocation_type in (1, 28, 29):
            target = None
            for address, name in STUB_NAMES.items():
                if name in rel.symbol_name:
                    target = address
                    break
            if target is None:
                raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
            pc = FUNC_ADDR + rel.offset + 8
            displacement = (target - pc) >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
            )
            resolved.append((rel.symbol_name, rel.relocation_type, target))
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
    return bytes(code), resolved


def compile_candidate_baseline():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
    result = compile_tu_armv6k(SOURCE_FILE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str):
    text = SOURCE_FILE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    result = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


# --------------------------------------------------------------------- fixtures
def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def encode_time(time: int) -> bytes:
    """Encode a time value into the four descriptor digit bytes."""
    total = time + TIME_BASE
    if not 0 <= total <= 79999:
        raise ValueError(f"time {time} is outside the digit-encoding domain")
    return bytes(
        (
            0x30 + total // 1000,
            (total // 100) % 10,
            (total // 10) % 10,
            total % 10,
        )
    )


def reference_time(digits: bytes) -> int:
    def s8(value: int) -> int:
        return value - 0x100 if value & 0x80 else value

    return (
        (s8(digits[0]) - 0x30) * 1000
        + s8(digits[1]) * 100
        + s8(digits[2]) * 10
        + s8(digits[3])
        - 0x12C0
        - 0x210
    )


def block_base_for(time: int) -> int:
    if time >= 1300:
        return 0xF4
    if time >= 1100:
        return 0xDC
    return 0xD8


def build_descriptor(case: dict) -> bytes:
    page = bytearray(((index * 7 + 0x13) & 0xFF) for index in range(DESC_SIZE))
    digits = case.get("digits")
    if digits is None:
        digits = encode_time(case["time"])
    page[4:8] = digits
    struct.pack_into("<H", page, 0x08, case.get("sub_offset", 0x100))
    page[0x0A] = case.get("type", 0) & 0xFF
    struct.pack_into("<I", page, 0x0C, case.get("span", 0) & 0xFFFFFFFF)

    sub = case.get("sub_offset", 0x100)
    struct.pack_into("<i", page, sub + 0x00, case.get("key", 0x1234))
    struct.pack_into("<i", page, sub + 0x04, case.get("group_count", 1))
    struct.pack_into("<i", page, sub + 0x08, case.get("mode", 0))
    struct.pack_into("<i", page, sub + 0x0C, case.get("extra", 0x55AA55AA))
    groups = case.get("groups")
    if groups is None:
        groups = tuple(
            (
                index - 2,
                0x1000 + index,
                f32_bits(0.25 * index),
                f32_bits(1.0 - 0.05 * index),
                f32_bits(2.0 + index),
            )
            for index in range(GROUP_COUNT)
        )
    for index, (repeat, step, f08, f0c, f10) in enumerate(groups):
        base = sub + 0x10 + index * GROUP_STRIDE
        struct.pack_into("<i", page, base + 0x00, repeat)
        struct.pack_into("<i", page, base + 0x04, step)
        struct.pack_into("<I", page, base + 0x08, f08 & 0xFFFFFFFF)
        struct.pack_into("<I", page, base + 0x0C, f0c & 0xFFFFFFFF)
        struct.pack_into("<I", page, base + 0x10, f10 & 0xFFFFFFFF)

    if "mode_20" in case:
        struct.pack_into("<i", page, sub + 0x20, case["mode_20"])

    # Pre-baked record block used by type 1. The selected base follows the
    # recovered time thresholds; every record gets an explicit key and a
    # non-zero +0x14 word so the exact-1200 clearing is observable.
    base = block_base_for(reference_time(digits))
    record_keys = case.get("record_keys")
    if record_keys is None:
        record_keys = [0x3000 + index for index in range(16)]
    for index in range(32):
        record = sub + base + index * RECORD_STRIDE
        if record + RECORD_STRIDE > DESC_SIZE:
            break
        key = record_keys[index] if index < len(record_keys) else 0x3000 + index
        struct.pack_into("<I", page, record + 0x00, key & 0xFFFFFFFF)
        struct.pack_into("<H", page, record + 0x04, (index * 3 + 1) & 0xFFFF)
        page[record + 0x06] = (0x70 + index) & 0xFF
        page[record + 0x07] = (0xF0 - index) & 0xFF
        struct.pack_into("<I", page, record + 0x08, 0x11110000 + index)
        struct.pack_into("<I", page, record + 0x0C, 0x22220000 + index)
        struct.pack_into("<I", page, record + 0x10, 0x33330000 + index)
        struct.pack_into("<I", page, record + 0x14, 0x44440000 + index)
        struct.pack_into("<I", page, record + 0x18, 0x55550000 + index)
        struct.pack_into("<I", page, record + 0x1C, 0x66660000 + index)
    return bytes(page)


def build_catalog(case: dict) -> bytes:
    page = bytearray(CATALOG_SIZE)
    entry_count = case.get("catalog_entries", 0)
    for index in range(entry_count):
        struct.pack_into("<i", page, index * CATALOG_STRIDE + 4, 0x2000 + index * 3)
    for index, key in case.get("catalog_keys", {}).items():
        struct.pack_into("<i", page, index * CATALOG_STRIDE + 4, key)
    return bytes(page)


def build_out(case: dict) -> bytes:
    return bytes([case.get("out_fill", 0xCC)]) * OUT_SIZE


class FE358Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DESC_ADDR, DESC_SIZE)
        self.uc.mem_map(CATALOG_ADDR, CATALOG_SIZE)
        self.uc.mem_map(OUT_ADDR, OUT_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        # VFP is used for the plain float stores; grant CP10/CP11 and FPEXC.EN.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.reg_write(arm.UC_ARM_REG_FPSCR, 0)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _addr(self, address: int):
        if STACK_ADDR <= address < STACK_ADDR + STACK_SIZE:
            return "<stack>"
        return address

    def _stack_word(self, index: int = 0) -> int:
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        return struct.unpack("<I", self.uc.mem_read(sp + 4 * index, 4))[0]

    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], args))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_2BCF58:
            self._log(address, self._addr(r0), self._addr(r1), r2)
            if r2:
                uc.mem_write(r0, bytes(uc.mem_read(r1, r2)))
        elif address == STUB_2C5F58:
            self._log(address, self._addr(r0), r1, r2, r3)
            # Model the initialiser at 0x00333FEC: {1, 0, 0.0f, 1.0f, 1.0f}.
            entry = struct.pack("<IIIII", 1, 0, 0, 0x3F800000, 0x3F800000)
            for index in range(r3):
                uc.mem_write(r0 + index * r2, entry[:r2])
        elif address == STUB_2FE600:
            source = r2
            source_bytes = bytes(uc.mem_read(source, 0xF0))
            stack_arg = self._stack_word(0)
            self._log(
                address,
                self._addr(r0),
                r1,
                self._addr(source),
                source_bytes,
                self._addr(r3),
                stack_arg,
            )
            # The helper's return value is the caller's return value.
            uc.mem_write(r0, struct.pack("<I", 0xFE600000 | (r1 & 0xFFFF)))
            uc.reg_write(
                arm.UC_ARM_REG_R0,
                self.case.get("fe600_ret", 0) & 0xFFFFFFFF,
            )
        elif address == STUB_2E2750:
            self._log(address, self._addr(r0), r1, r2, self._addr(r3))
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub 0x{address:08x}")

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(DESC_ADDR, build_descriptor(case))
        self.uc.mem_write(CATALOG_ADDR, build_catalog(case))
        self.uc.mem_write(OUT_ADDR, build_out(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        # The original and candidate share the entry address; drop translated
        # blocks from the previous image.
        self.uc.ctl_remove_cache(CODE_ADDR, CODE_ADDR + CODE_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, OUT_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case.get("capacity", 8) & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R2, DESC_ADDR)
        self.uc.reg_write(
            arm.UC_ARM_REG_R3,
            case.get("catalog_addr", CATALOG_ADDR) & 0xFFFFFFFF,
        )
        self.uc.mem_write(
            ENTRY_SP, struct.pack("<I", case.get("catalog_count", 4) & 0xFFFFFFFF)
        )
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)
        for name, bits in VFP_CALLEE_SAVED_START.items():
            self.uc.reg_write(VFP_CALLEE_SAVED[name], bits)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, _value in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            in_out = OUT_ADDR <= address < OUT_ADDR + OUT_SIZE
            if not (in_stack or in_out):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "vfp_callee_saved": {
                name: self.uc.reg_read(reg)
                for name, reg in VFP_CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "fixtures": {
                "descriptor": bytes(self.uc.mem_read(DESC_ADDR, DESC_SIZE)),
                "catalog": bytes(self.uc.mem_read(CATALOG_ADDR, CATALOG_SIZE)),
                "out": bytes(self.uc.mem_read(OUT_ADDR, OUT_SIZE)),
            },
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "vfp_callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig="
            + repr(orig["call_log"])
            + "\n    cand="
            + repr(cand["call_log"])
        )
    for key, value in orig["fixtures"].items():
        if value != cand["fixtures"][key]:
            first = next(
                (
                    index
                    for index, (left, right) in enumerate(
                        zip(value, cand["fixtures"][key])
                    )
                    if left != right
                ),
                None,
            )
            problems.append(f"fixture {key} differs (first byte {first})")
    if orig["unexpected_writes"] != cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    if orig["unexpected_writes"]:
        problems.append(
            f"original wrote outside allowed regions: {orig['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "time": 0,
        "type": 0,
        "sub_offset": 0x100,
        "span": 0,
        "capacity": 8,
        "catalog_count": 4,
        "key": 0x1234,
        "group_count": 1,
        "mode": 0,
        "extra": 0x55AA55AA,
        "catalog_entries": 8,
        "fe600_ret": 3,
        "out_fill": 0xCC,
    }
    case.update(overrides)
    if "time" in overrides and "digits" not in overrides:
        case["digits"] = encode_time(overrides["time"])
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- type 0: local source below 1300 ---------------------------------
    cases.append(base_case("type 0 local time 0", time=0))
    cases.append(base_case("type 0 local time -1", time=-1))
    cases.append(base_case("type 0 local time -5328", time=-5328))
    cases.append(base_case("type 0 local time 1099", time=1099))
    cases.append(base_case("type 0 local time 1299", time=1299))
    cases.append(
        base_case(
            "type 0 local group_count 0 mode 1",
            time=1299,
            key=0,
            group_count=0,
            mode=1,
            extra=0,
        )
    )
    cases.append(
        base_case(
            "type 0 local negative key and mode -1",
            time=100,
            key=-1,
            group_count=4,
            mode=-1,
            sub_offset=0x20,
        )
    )
    cases.append(
        base_case(
            "type 0 local capacity 0",
            time=0,
            capacity=0,
            group_count=3,
        )
    )

    # --- type 0: forwarded descriptor at or above 1300 -------------------
    cases.append(base_case("type 0 forward time 1300", time=1300))
    cases.append(base_case("type 0 forward time 1301", time=1301))
    cases.append(
        base_case(
            "type 0 forward time 4672 (b4 above '9')",
            time=4672,
            key=0x7FFFFFFF,
            group_count=2,
            mode=2,
        )
    )
    cases.append(
        base_case(
            "type 0 local signed digit bytes",
            digits=bytes((0x80, 0xFF, 0x80, 0x7F)),
            time=reference_time(bytes((0x80, 0xFF, 0x80, 0x7F))),
            sub_offset=0x40,
            key=-7,
        )
    )
    cases.append(
        base_case(
            "type 0 forward largest positive digit bytes",
            digits=bytes((0x7F, 0x7F, 0x7F, 0x7F)),
            time=reference_time(bytes((0x7F, 0x7F, 0x7F, 0x7F))),
            sub_offset=0x180,
        )
    )
    cases.append(
        base_case(
            "type 0 forward fe600 return -1",
            time=1300,
            fe600_ret=-1,
        )
    )

    # --- type 1: time block selection ------------------------------------
    def type1(name: str, time: int, count: int, **overrides) -> dict:
        base = block_base_for(time)
        span = (base + count * RECORD_STRIDE) & 0xFFFFFFFF
        return base_case(
            name,
            time=time,
            type=1,
            span=span,
            block_count=count,
            **overrides,
        )

    cases.append(type1("type 1 time 0 base D8 count 3", 0, 3))
    cases.append(type1("type 1 time 1099 base D8 count 3", 1099, 3))
    cases.append(type1("type 1 time 1100 base DC count 3", 1100, 3))
    cases.append(type1("type 1 time 1199 base DC count 3", 1199, 3))
    cases.append(type1("type 1 time 1201 base DC count 3", 1201, 3))
    cases.append(type1("type 1 time 1299 base DC count 3", 1299, 3))
    cases.append(type1("type 1 time 1300 base F4 count 4", 1300, 4))
    cases.append(type1("type 1 time 1301 base F4 count 4", 1301, 4))

    # Exact 1200 zeroes +0x14 of every copied record.
    cases.append(type1("type 1 exact 1200 clears +0x14", 1200, 4))
    cases.append(
        type1(
            "type 1 exact 1200 count 0",
            1200,
            0,
            capacity=4,
        )
    )

    # --- type 1: count boundaries ----------------------------------------
    cases.append(
        base_case(
            "type 1 span equals base => count 0 sentinel fill",
            time=0,
            type=1,
            span=0xD8,
            capacity=4,
        )
    )
    cases.append(
        base_case(
            "type 1 span base+31 => count 0",
            time=0,
            type=1,
            span=0xD8 + 31,
            capacity=4,
        )
    )
    cases.append(
        base_case(
            "type 1 span base+32 => count 1",
            time=0,
            type=1,
            span=0xD8 + 32,
            capacity=4,
        )
    )
    cases.append(
        base_case(
            "type 1 count capped at capacity 2",
            time=0,
            type=1,
            span=0xD8 + 6 * RECORD_STRIDE,
            capacity=2,
        )
    )
    cases.append(
        base_case(
            "type 1 wrapped span => capped count",
            time=0,
            type=1,
            span=0,
            capacity=2,
        )
    )
    cases.append(
        base_case(
            "type 1 capacity 0",
            time=0,
            type=1,
            span=0xD8 + 3 * RECORD_STRIDE,
            capacity=0,
        )
    )
    cases.append(
        base_case(
            "type 1 capacity 1",
            time=0,
            type=1,
            span=0xD8 + 3 * RECORD_STRIDE,
            capacity=1,
        )
    )
    cases.append(
        base_case(
            "type 1 exact capacity",
            time=0,
            type=1,
            span=0xD8 + 3 * RECORD_STRIDE,
            capacity=3,
        )
    )

    # --- type 1: catalog re-index ----------------------------------------
    record_keys = [0x1111, 0x2222, 0x3333, 0x4444]
    cases.append(
        base_case(
            "type 1 catalog match at index 0",
            time=0,
            type=1,
            span=0xD8 + 3 * RECORD_STRIDE,
            capacity=8,
            record_keys=record_keys,
            catalog_keys={0: 0x1111},
        )
    )
    cases.append(
        base_case(
            "type 1 catalog match at index 5",
            time=0,
            type=1,
            span=0xD8 + 3 * RECORD_STRIDE,
            capacity=8,
            record_keys=record_keys,
            catalog_keys={5: 0x3333},
        )
    )
    cases.append(
        base_case(
            "type 1 catalog miss leaves byte +6",
            time=0,
            type=1,
            span=0xD8 + 3 * RECORD_STRIDE,
            capacity=8,
            record_keys=record_keys,
            catalog_keys={},
        )
    )
    cases.append(
        base_case(
            "type 1 catalog_count 0 skips re-index",
            time=0,
            type=1,
            span=0xD8 + 3 * RECORD_STRIDE,
            capacity=8,
            catalog_count=0,
            record_keys=record_keys,
        )
    )
    cases.append(
        base_case(
            "type 1 catalog_count negative skips re-index",
            time=0,
            type=1,
            span=0xD8 + 3 * RECORD_STRIDE,
            capacity=8,
            catalog_count=-4,
            record_keys=record_keys,
        )
    )
    cases.append(
        base_case(
            "type 1 duplicate keys use the first slot",
            time=0,
            type=1,
            span=0xD8 + 2 * RECORD_STRIDE,
            capacity=4,
            record_keys=[0x7000, 0x7000],
            catalog_keys={1: 0x7000, 4: 0x7000},
        )
    )
    cases.append(
        base_case(
            "type 1 match at catalog index 200",
            time=0,
            type=1,
            span=0xD8 + 1 * RECORD_STRIDE,
            capacity=2,
            catalog_entries=201,
            record_keys=[0x5151],
            catalog_keys={200: 0x5151},
        )
    )
    cases.append(
        base_case(
            "type 1 match at catalog index 256 truncates",
            time=0,
            type=1,
            span=0xD8 + 1 * RECORD_STRIDE,
            capacity=2,
            catalog_entries=257,
            record_keys=[0x6262],
            catalog_keys={256: 0x6262},
        )
    )
    cases.append(
        base_case(
            "type 1 copied key 0xFFFFFFFF matches catalog -1",
            time=0,
            type=1,
            span=0xD8 + 1 * RECORD_STRIDE,
            capacity=3,
            catalog_entries=3,
            record_keys=[0xFFFFFFFF],
            catalog_keys={2: -1},
        )
    )
    cases.append(
        base_case(
            "type 1 mode loaded from sub +8",
            time=1299,
            type=1,
            span=0xDC + 1 * RECORD_STRIDE,
            mode=2,
            capacity=2,
        )
    )
    cases.append(
        base_case(
            "type 1 mode loaded from sub +0x20",
            time=1300,
            type=1,
            span=0xF4 + 1 * RECORD_STRIDE,
            mode=7,
            mode_20=0x12345678,
            capacity=2,
        )
    )

    # --- unknown types ---------------------------------------------------
    cases.append(base_case("type 2 returns 0", time=0, type=2))
    cases.append(base_case("type 0x63 returns 0", time=1300, type=0x63))
    cases.append(
        base_case(
            "type 0xFF returns 0 with sentinel prefilled output",
            time=0,
            type=0xFF,
            out_fill=0xA5,
        )
    )

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    runner = FE358Runner()
    passed = 0
    for case in cases:
        orig = runner.run(orig_code, case)
        cand = runner.run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing ui_func_002fe358 (0x002fe358)...")
    orig_code = normalise_original_calls(get_orig_bytes())
    cand_code, resolved = compile_candidate_baseline()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B")
    for symbol, rel_type, target in resolved:
        print(f"  relocation {symbol} (type {rel_type}) -> 0x{target:08x}")

    cases = make_cases()

    # Sanity-check the digit encoding used to place time at the thresholds.
    for case in cases:
        if "time" in case and case.get("digits") is not None:
            actual = reference_time(case["digits"])
            if actual != case["time"]:
                raise RuntimeError(
                    f"{case['name']}: digits encode {actual}, expected {case['time']}"
                )

    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    mutants = (
        ("time_threshold", "constexpr s32 kTimeForward = 1300;",
         "constexpr s32 kTimeForward = 1299;"),
        ("block_base", "constexpr u32 kBlockBaseShort = 0xD8;",
         "constexpr u32 kBlockBaseShort = 0xD7;"),
        ("catalog_stride",
         "constexpr u32 kCatalogStride = 0x48;\n"
         "constexpr u32 kCatalogKeyOffset = 0x04;",
         "constexpr u32 kCatalogStride = 0x47;\n"
         "constexpr u32 kCatalogKeyOffset = 0x04;"),
        ("sub_groups", "constexpr u32 kSubGroupsOffset = 0x10;",
         "constexpr u32 kSubGroupsOffset = 0x14;"),
        ("sentinel_index", "constexpr u8 kSentinelIndex = 0xFF;",
         "constexpr u8 kSentinelIndex = 0xFE;"),
    )
    runner = FE358Runner()
    detected_controls = 0
    for name, old, new in mutants:
        mutant_code, _ = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            baseline = runner.run(orig_code, case)
            broken = runner.run(mutant_code, case)
            if compare(baseline, broken):
                detected = True
                break
        if detected:
            detected_controls += 1
            print(f"  [PASS] {name} mutant is detected")
        else:
            print(f"  [FAIL] {name} mutant was not detected")
            raise SystemExit(1)

    total = passed + detected_controls
    print(f"\nAll {total}/{total} differential checks PASSED.")
    print(f"  {passed} cases, {detected_controls} negative controls")


if __name__ == "__main__":
    main()
