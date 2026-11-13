#!/usr/bin/env python3
"""Differential test for ui_func_002392e0 (0x002392e0) using Unicorn ARM.

Compiles ``src/engine/leaf_batch45_a.cpp``, extracts ``ui_func_002392e0``,
resolves its direct calls to deterministic stubs at the pinned call targets,
and runs the original bytes from ``extracted/exefs/code.bin`` against the
candidate in separate Unicorn machines with identical fixtures.

The function owns a dispatch pointer at ``self + 0`` (slots +0x08/-0x28/-0x34)
and the record block at ``self + 0x55C`` (8-byte header: marker at +0, count at
+4; records at +0x564).  The stubs therefore exercise the table indirection,
the 0x320-byte staging allocation, the header copy, the derived count check,
the one retry, and the record copy loop.

Compared on every case:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * ordered call log with every register argument and the architected stack
    words of each helper, plus the copy-pair source/destination addresses;
  * the distinction between the open size-out pointer and the read flag-out
    pointer inside the private frame;
  * the full self page, staging-heap page and dispatch-table page;
  * any emulated write outside the private stack, self page or heap page.

Coverage: null handle; the 0x3F7 low-bit error word; size 0 and nonzero; every
accepted-kind / low-bound edge (0x63/0x64/0xB3/0xB4, kind 0x11 versus 0x12);
null allocation; first-attempt marker/count mismatches; reset/open/read
negative statuses on retry; retry success with written == 0; count 0/1/2/3;
carry/wrap sizes below 8; and status words with bit 31 set or clear.
Negative controls mutate the header marker, staging capacity, and accepted
kind; each mutant must be detected.
"""

from __future__ import annotations

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
SOURCE = ROOT / "src/engine/leaf_batch45_a.cpp"
OUT_DIR = ROOT / "build/test_leaf_002392e0"

FUNC_ADDR = 0x002392E0
FUNC_SIZE = 604

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers FUNC_ADDR and every stub below 0x2ADB40
SELF_ADDR = 0x00710000
SELF_SIZE = 0x00010000
HEAP_ADDR = 0x00720000
HEAP_SIZE = 0x00010000
TABLE_ADDR = 0x00730000
TABLE_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Pinned direct-call targets.
STUB_COPY = 0x002ADB40
STUB_ALLOC = 0x00239B54
STUB_FREE = 0x00239B84
# Indirect dispatch slots (private ARM stubs inside the mapped code page).
STUB_OPEN = 0x002AA000
STUB_RESET = 0x002AA010
STUB_READ = 0x002AA020

STUB_NAMES = {
    STUB_COPY: "ui_func_002adb40",
    STUB_ALLOC: "func_00239b54",
    STUB_FREE: "func_00239b84",
    STUB_OPEN: "dispatch_open",
    STUB_RESET: "dispatch_reset",
    STUB_READ: "dispatch_read",
}

STACK_ARGS = {
    STUB_COPY: 0,
    STUB_ALLOC: 0,
    STUB_FREE: 0,
    STUB_OPEN: 1,   # pointer to the size output
    STUB_RESET: 1,  # fifth argument is zero
    STUB_READ: 3,   # self handle, 5, 0x12
}

SELF_HANDLE = 0x04
SELF_HEADER = 0x55C
SELF_COUNT = 0x560
SELF_RECORDS = 0x564

TABLE_OPEN = 0x08
TABLE_RESET = 0x28
TABLE_READ = 0x34

HEAP_FILL_LEN = 0x400
HEADER_BYTES = 8
STAGING_CAPACITY = 0x320

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

BUFFER_FILL = bytes(((0x40 + 3 * index) & 0xFF) for index in range(HEAP_FILL_LEN))


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "002392e0" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"ui_func_002392e0 not found in {obj_file}: {sorted(funcs)}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (1, 28, 29):
            target = None
            for address, name in (
                (STUB_COPY, "002adb40"),
                (STUB_ALLOC, "00239b54"),
                (STUB_FREE, "00239b84"),
            ):
                if name in rel.symbol_name:
                    target = address
                    break
            if target is None:
                raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
            displacement = (target - (FUNC_ADDR + rel.offset + 8)) >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            struct.pack_into(
                "<I", code, rel.offset, (original & 0xFF000000) | (displacement & 0x00FFFFFF)
            )
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} for {rel.symbol_name}"
            )
    return bytes(code)


def compile_candidate(source: Path, obj_file: Path) -> bytes:
    obj_file.parent.mkdir(parents=True, exist_ok=True)
    result = compile_tu_armv6k(source, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_baseline() -> bytes:
    return compile_candidate(SOURCE, OUT_DIR / "leaf_batch45_a.o")


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    return compile_candidate(mutant_src, OUT_DIR / f"mutant_{name}.o")


# --------------------------------------------------------------------- fixtures
def make_read(marker=0x6767, count="auto", written=1, records=(), pad=0):
    return {
        "marker": marker,
        "pad": pad,
        "count": count,
        "written": written,
        "records": tuple(records),
    }


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "handle": 0x12345678,
        "status0": (2 << 10) | 0x80,
        "size0": 0x18,
        "status1": (2 << 10) | 0x80,
        "size1": 0x18,
        "reset_status": 0,
        "read_status0": 0,
        "read_status1": 0,
        "read0": make_read(
            records=((0x11111111, 0x22222222), (0x33333333, 0x44444444))
        ),
        "read1": make_read(
            records=((0x55555555, 0x66666666), (0x77777777, 0x88888888))
        ),
        "alloc_null": False,
        "pre_marker": 0,
        "pre_count": 0,
        "pre_records": (),
    }
    case.update(overrides)
    return case


def build_self(case: dict) -> bytes:
    page = bytearray(((0x5A ^ index) & 0xFF) for index in range(SELF_SIZE))
    struct.pack_into("<I", page, 0x00, TABLE_ADDR)
    struct.pack_into("<I", page, SELF_HANDLE, case["handle"] & 0xFFFFFFFF)
    struct.pack_into("<H", page, SELF_HEADER, case["pre_marker"] & 0xFFFF)
    struct.pack_into("<I", page, SELF_COUNT, case["pre_count"] & 0xFFFFFFFF)
    for index, (word0, word1) in enumerate(case["pre_records"]):
        struct.pack_into("<II", page, SELF_RECORDS + index * 8, word0, word1)
    return bytes(page)


def build_table() -> bytes:
    page = bytearray(((0xC3 ^ index) & 0xFF) for index in range(TABLE_SIZE))
    struct.pack_into("<I", page, TABLE_OPEN, STUB_OPEN)
    struct.pack_into("<I", page, TABLE_RESET, STUB_RESET)
    struct.pack_into("<I", page, TABLE_READ, STUB_READ)
    return bytes(page)


class FunctionRunner:
    """One Unicorn machine with deterministic stubs at the pinned targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(SELF_ADDR, SELF_SIZE)
        self.uc.mem_map(HEAP_ADDR, HEAP_SIZE)
        self.uc.mem_map(TABLE_ADDR, TABLE_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log = []
        self.writes = []
        self.open_index = 0
        self.read_index = 0
        self.open_out_ptrs = []
        self.read_out_ptrs = []
        self.case = {}

    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        return struct.unpack(f"<{count}I", self.uc.mem_read(sp, 4 * count))

    def _log(self, address: int, registers: tuple, stack_count: int) -> None:
        self.call_log.append(
            (STUB_NAMES[address], registers + self._stack_words(stack_count))
        )

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _write_u32(self, address: int, value: int) -> None:
        self.uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_COPY:
            self._log(address, (r0, r1), 0)
            source = struct.unpack("<II", uc.mem_read(r1, 8))
            uc.mem_write(r0, struct.pack("<II", *source))
        elif address == STUB_ALLOC:
            self._log(address, (r0, r1), 0)
            uc.mem_write(HEAP_ADDR, BUFFER_FILL)
            uc.reg_write(
                arm.UC_ARM_REG_R0, 0 if self.case["alloc_null"] else HEAP_ADDR
            )
        elif address == STUB_FREE:
            self._log(address, (r0,), 0)
        elif address == STUB_OPEN:
            stack = self._stack_words(1)
            self._log(address, (r0, r1, r2, r3), 1)
            self.open_out_ptrs.append(stack[0])
            index = 0 if self.open_index == 0 else 1
            self.open_index += 1
            self._write_u32(stack[0], self.case[f"size{index}"])
            uc.reg_write(arm.UC_ARM_REG_R0, self.case[f"status{index}"])
        elif address == STUB_RESET:
            self._log(address, (r0, r1, r2, r3), 1)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["reset_status"])
        elif address == STUB_READ:
            self._log(address, (r0, r1, r2, r3), 3)
            self.read_out_ptrs.append(r3)
            index = 0 if self.read_index == 0 else 1
            self.read_index += 1
            config = self.case[f"read{index}"]
            buffer = bytearray(BUFFER_FILL)
            if config["marker"] is not None:
                struct.pack_into("<H", buffer, 0, config["marker"] & 0xFFFF)
            if config["pad"] is not None:
                struct.pack_into("<H", buffer, 2, config["pad"] & 0xFFFF)
            if config["count"] == "auto":
                count = ((r2 - HEADER_BYTES) & 0xFFFFFFFF) >> 3
                struct.pack_into("<I", buffer, 4, count)
            elif config["count"] is not None:
                struct.pack_into("<I", buffer, 4, config["count"] & 0xFFFFFFFF)
            for record_index, (word0, word1) in enumerate(config["records"]):
                struct.pack_into(
                    "<II", buffer, HEADER_BYTES + record_index * 8, word0, word1
                )
            uc.mem_write(HEAP_ADDR, bytes(buffer))
            if config["written"] is not None:
                self._write_u32(r3, config["written"])
            uc.reg_write(arm.UC_ARM_REG_R0, self.case[f"read_status{index}"])
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    @staticmethod
    def _normalise(log) -> list:
        normalised = []
        for name, args in log:
            out = []
            for arg in args:
                if isinstance(arg, int) and STACK_ADDR <= arg < STACK_ADDR + STACK_SIZE:
                    out.append("<stack>")
                else:
                    out.append(arg)
            normalised.append((name, tuple(out)))
        return normalised

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.open_index = 0
        self.read_index = 0
        self.open_out_ptrs = []
        self.read_out_ptrs = []
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(SELF_ADDR, build_self(case))
        self.uc.mem_write(TABLE_ADDR, build_table())
        self.uc.mem_write(HEAP_ADDR, b"\x00" * HEAP_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []
        # The same machine is reused for original and candidate bodies; drop
        # translated blocks so the freshly written bytes are the ones executed.
        self.uc.ctl_flush_tb()

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, _value in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            in_self = SELF_ADDR <= address < SELF_ADDR + SELF_SIZE
            in_heap = HEAP_ADDR <= address < HEAP_ADDR + HEAP_SIZE
            if not (in_stack or in_self or in_heap):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self._normalise(self.call_log),
            "out_ptrs_distinct": all(
                open_ptr != read_ptr
                for open_ptr in self.open_out_ptrs
                for read_ptr in self.read_out_ptrs
            ),
            "self": bytes(self.uc.mem_read(SELF_ADDR, SELF_SIZE)),
            "heap": bytes(self.uc.mem_read(HEAP_ADDR, HEAP_SIZE)),
            "table": bytes(self.uc.mem_read(TABLE_ADDR, TABLE_SIZE)),
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "out_ptrs_distinct"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig="
            + repr(orig["call_log"])
            + "\n    cand="
            + repr(cand["call_log"])
        )
    for key in ("self", "heap", "table"):
        if orig[key] != cand[key]:
            problems.append(f"{key} memory was modified differently")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def make_cases() -> list[dict]:
    cases: list[dict] = []

    cases.append(base_case("null handle returns early", handle=0))

    # open-status error word (low ten bits 0x3F7); high bits and kind ignored.
    for status in (0x000003F7, 0x123403F7, 0x800003F7, 0xFFFFFBF7):
        cases.append(
            base_case(f"open error word 0x{status:08x}", status0=status)
        )

    # baseline success and record-count bounds.
    cases.append(base_case("success two records"))
    cases.append(
        base_case(
            "success zero records",
            size0=HEADER_BYTES,
            read0=make_read(records=()),
        )
    )
    cases.append(
        base_case(
            "success one record",
            size0=HEADER_BYTES + 8,
            read0=make_read(records=((0xDEADBEEF, 0x0BADF00D),)),
        )
    )
    cases.append(
        base_case(
            "success three records",
            size0=HEADER_BYTES + 24,
            read0=make_read(
                records=(
                    (0x01010101, 0x02020202),
                    (0x03030303, 0x04040404),
                    (0x05050505, 0x06060606),
                )
            ),
        )
    )

    # written == 0 uses the pre-existing header; the final loop still copies.
    cases.append(
        base_case(
            "written 0 keeps pre-existing valid header",
            pre_marker=0x6767,
            pre_count=2,
            read0=make_read(written=0),
        )
    )
    cases.append(
        base_case(
            "written 0 with stale header retries",
            pre_marker=0x1234,
            pre_count=2,
            read0=make_read(written=0),
        )
    )
    cases.append(
        base_case(
            "written 0xFFFFFFFF is non-zero",
            read0=make_read(written=0xFFFFFFFF),
        )
    )

    # accepted-kind / low-bound selection of the reset slot.
    for low in (0x63, 0x64, 0xB3, 0xB4, 0x00, 0x3FF):
        cases.append(
            base_case(
                f"kind 0x11 low 0x{low:03x}",
                status0=(0x11 << 10) | low,
            )
        )
    for kind in (0x10, 0x12, 0x00, 0x3FF):
        cases.append(
            base_case(
                f"kind 0x{kind:03x} low 0x064 ignored",
                status0=(kind << 10) | 0x64,
            )
        )
    cases.append(
        base_case(
            "status bit 31 with accepted kind still reads",
            status0=0x80004464,
        )
    )

    # size == 0 forces the reset slot even when kind/low would not.
    cases.append(
        base_case(
            "size 0 forces reset then retry succeeds",
            size0=0,
            status0=(0x12 << 10) | 0x64,
            size1=HEADER_BYTES + 8,
            read0=make_read(written=1, count=0),
            read1=make_read(records=((0x13572468, 0x24681357),)),
        )
    )

    # allocation failure/null helper result.
    cases.append(
        base_case(
            "pre-allocation reset negative returns early",
            status0=(0x11 << 10) | 0x64,
            reset_status=0x80000000,
            pre_marker=0x6767,
            pre_count=9,
        )
    )
    cases.append(
        base_case(
            "null allocation zeroes count",
            pre_count=5,
            pre_marker=0x6767,
            alloc_null=True,
        )
    )
    cases.append(
        base_case(
            "null allocation after reset",
            status0=(0x11 << 10) | 0x64,
            alloc_null=True,
        )
    )

    # first-attempt validation failures and retry outcomes.
    cases.append(
        base_case(
            "first read negative frees without zeroing count",
            pre_marker=0x6767,
            pre_count=7,
            read_status0=0xFFFFFFFF,
        )
    )
    cases.append(
        base_case(
            "retry reset negative",
            size0=0x18,
            read0=make_read(marker=0x1234),
            reset_status=0xFFFFFFFF,
        )
    )
    cases.append(
        base_case(
            "retry open negative",
            read0=make_read(marker=0x1234),
            status1=0x80000000,
        )
    )
    cases.append(
        base_case(
            "retry read negative",
            read0=make_read(marker=0x1234),
            read_status1=0xFFFFFFFF,
        )
    )
    cases.append(
        base_case(
            "retry marker invalid",
            read0=make_read(marker=0x1234),
            read1=make_read(marker=0x0000),
        )
    )
    cases.append(
        base_case(
            "retry count invalid",
            read0=make_read(marker=0x1234),
            read1=make_read(count=0),
        )
    )
    cases.append(
        base_case(
            "retry copies header when written is 0",
            pre_marker=0x1234,
            pre_count=2,
            read0=make_read(marker=0x1234, written=0),
            read1=make_read(written=0),
        )
    )
    cases.append(
        base_case(
            "retry open ignores low error bits",
            read0=make_read(marker=0x1234),
            status1=0x000003F7,
            size1=HEADER_BYTES + 8,
            read1=make_read(records=((0x0F0F0F0F, 0xF0F0F0F0),)),
        )
    )
    cases.append(
        base_case(
            "first marker valid count mismatch",
            read0=make_read(count=1),
        )
    )
    cases.append(
        base_case(
            "first marker invalid count valid",
            read0=make_read(marker=0xBEEF),
        )
    )

    # carry/wrap: size below the 8-byte header makes the derived count huge.
    cases.append(
        base_case(
            "size 4 wraps derived count",
            size0=4,
            read0=make_read(count=0),
            size1=HEADER_BYTES + 16,
            read1=make_read(records=((0xA1A1A1A1, 0xB2B2B2B2),
                                     (0xC3C3C3C3, 0xD4D4D4D4))),
        )
    )

    # header pad bytes still travel through the 8-byte copy.
    cases.append(
        base_case(
            "header pad bytes copied",
            read0=make_read(pad=0xA5C3),
        )
    )

    return cases


def run_case_set(original: bytes, candidate: bytes, cases: list[dict]) -> int:
    runner = FunctionRunner()
    passed = 0
    for case in cases:
        orig = runner.run(original, case)
        cand = runner.run(candidate, case)
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
    print("Testing ui_func_002392e0 (0x002392e0)...")
    original = get_orig_bytes()
    candidate = compile_candidate_baseline()
    print(f"Original {len(original)} B, candidate {len(candidate)} B (relocations resolved).")

    cases = make_cases()
    passed = run_case_set(original, candidate, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("header_marker", "constexpr u16 kHeaderMarker = 0x6767;",
         "constexpr u16 kHeaderMarker = 0x6766;"),
        ("staging_capacity", "constexpr u32 kStagingCapacity = 0x320;",
         "constexpr u32 kStagingCapacity = 0x31C;"),
        ("accepted_kind", "constexpr u32 kAcceptedKind = 0x11;",
         "constexpr u32 kAcceptedKind = 0x10;"),
    ):
        mutant = compile_candidate_mutant(name, old, new)
        detected = False
        runner = FunctionRunner()
        for case in cases:
            orig = runner.run(original, case)
            bad = runner.run(mutant, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
