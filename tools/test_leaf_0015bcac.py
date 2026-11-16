#!/usr/bin/env python3
"""Differential test for engine_func_0015bcac (0x0015bcac) using Unicorn ARM.

Compiles src/engine/leaf_batch34_c.cpp, extracts the engine_func_0015bcac body,
resolves its three direct-call relocations (0x002C39A4, 0x002BC300 twice) and
its two R_ARM_ABS32 references (g_GpuCommandCursor / g_GpuCommandEnd), then runs
the pinned original (extracted/exefs/code.bin) and the candidate on separate
Unicorn ARM machines with identical fixtures.

The original reads its kind from the real word table at 0x0040B70C and the two
shared cursor globals at 0x004652A0 / 0x004652A4, so the whole code image is
mapped at its pinned address and the fixtures use those addresses directly.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log (helper name plus the single register argument);
  * the full 4 KiB packet page, arena page and draw-entry page;
  * both shared cursor globals.

Coverage: all four authentic table kinds and a 0..31 index sweep, synthetic
table values (4/5/6/0x6010/other/signed boundaries) through a per-case table
override, force-kind overrides, the 0x1403 flagged/halved variant against
signed value boundaries, direct [entry+0x20] and self-relative [entry+0x0C]
source resolution (including a zero offset and a wrapped offset), translation
helper results that make the emitted offset wrap, arena limit boundaries
exactly +0x70, -1 and below the cursor, and the shared-global fallback with the
same boundaries.  Negative controls mutate the special type, the forced kind,
the kind attribute store, the halving shift and the exact-fit comparison.
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
SOURCE = ROOT / "src/engine/leaf_batch34_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_0015bcac"

FUNC_ADDR = 0x0015BCAC
FUNC_SIZE = 520

# The whole pinned image: the function itself, both helper targets, the kind
# table at 0x0040B70C and the shared cursor globals at 0x004652A0/4.
CODE_ADDR = 0x00100000
CODE_SIZE = 0x00400000

ARENA_ADDR = 0x00700000
ARENA_SIZE = 0x00001000
ENTRY_ADDR = 0x00701000
ENTRY_SIZE = 0x00001000
PACKET_ADDR = 0x00710000
PACKET_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

KIND_TABLE = 0x0040B70C
GPU_CURSOR = 0x004652A0
GPU_END = 0x004652A4

STUB_2C39A4 = 0x002C39A4
STUB_2BC300 = 0x002BC300

STUB_NAMES = {
    STUB_2C39A4: "engine_func_002c39a4",
    STUB_2BC300: "engine_func_002bc300",
}

# Neither helper takes architected stack arguments.
STACK_ARGS = {
    STUB_2C39A4: 0,
    STUB_2BC300: 0,
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


def get_code_image() -> bytes:
    return ORIG_BIN.read_bytes()


CODE_IMAGE = get_code_image()
AUTHENTIC_KIND0 = struct.unpack_from(
    "<I", CODE_IMAGE, KIND_TABLE - 0x00100000
)[0]


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0015bcac" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_0015bcac not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (1, 28, 29):
            target = None
            for address, name in STUB_NAMES.items():
                if name == rel.symbol_name:
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
        elif rel.relocation_type == 2:  # R_ARM_ABS32
            if rel.symbol_name == "g_GpuCommandCursor":
                target = GPU_CURSOR
            elif rel.symbol_name == "g_GpuCommandEnd":
                target = GPU_END
            else:
                raise RuntimeError(f"unresolved data relocation: {rel.symbol_name}")
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            struct.pack_into("<I", code, rel.offset, (target + addend) & 0xFFFFFFFF)
        elif rel.relocation_type in (43, 44):  # R_ARM_MOVW_ABS_NC / R_ARM_MOVT_ABS
            if rel.symbol_name in ("g_GpuCommandCursor", "g_GpuCommandEnd"):
                target = GPU_CURSOR if rel.symbol_name == "g_GpuCommandCursor" else GPU_END
            else:
                raise RuntimeError(f"unresolved movw/movt relocation: {rel.symbol_name}")
            word = struct.unpack_from("<I", code, rel.offset)[0]
            if rel.relocation_type == 43:
                value = target & 0xFFFF
            else:
                value = (target >> 16) & 0xFFFF
            word = (word & ~0x000F0FFF) | ((value & 0xF000) << 4) | (value & 0x0FFF)
            struct.pack_into("<I", code, rel.offset, word)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch34_c.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
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
def build_arena(case: dict) -> bytes:
    page = bytearray(ARENA_SIZE)
    for offset in range(0, ARENA_SIZE, 4):
        struct.pack_into("<I", page, offset, 0xA0A00000 | (offset & 0xFFFC))
    struct.pack_into("<I", page, 0x00, 0xA0A00000)
    struct.pack_into("<I", page, 0x04, case["arena_limit"] & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x08, case["arena_cursor"] & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x0C, 0xC0C00000)
    return bytes(page)


def build_entry(case: dict) -> bytes:
    page = bytearray(ENTRY_SIZE)
    for offset in range(0, ENTRY_SIZE, 4):
        struct.pack_into("<I", page, offset, 0xE7E00000 | (offset & 0xFFFC))
    struct.pack_into("<I", page, 0x00, case["type"] & 0xFFFFFFFF)
    page[0x04] = case["kind"] & 0xFF
    struct.pack_into("<I", page, 0x08, case["value"] & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x0C, case["relative"] & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x20, case["address"] & 0xFFFFFFFF)
    return bytes(page)


def build_packet() -> bytes:
    page = bytearray(PACKET_SIZE)
    for offset in range(0, PACKET_SIZE, 4):
        struct.pack_into("<I", page, offset, 0xC1D00000 | (offset & 0xFFFC))
    return bytes(page)


def read_u32(uc, address: int) -> int:
    return struct.unpack("<I", uc.mem_read(address, 4))[0]


def write_u32(uc, address: int, value: int) -> None:
    uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))


class BCACRunner:
    """One Unicorn machine; the same code bytes are executed for every case."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        for address, size in (
            (CODE_ADDR, CODE_SIZE),
            (ARENA_ADDR, ARENA_SIZE),
            (ENTRY_ADDR, ENTRY_SIZE),
            (PACKET_ADDR, PACKET_SIZE),
            (STACK_ADDR, STACK_SIZE),
            (TRAP_ADDR, 0x1000),
        ):
            self.uc.mem_map(address, size)

        code_image = get_code_image()
        if len(code_image) > CODE_SIZE:
            raise RuntimeError("code.bin does not fit the mapped code region")
        self.uc.mem_write(CODE_ADDR, code_image)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )

        self.call_log: list = []
        self.case: dict = {}
        self.translate_index = 0
        self.code = b""

    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        return struct.unpack(f"<{count}I", self.uc.mem_read(sp, 4 * count))

    def _log(self, address: int, *args) -> None:
        self.call_log.append(
            (STUB_NAMES[address], args + self._stack_words(STACK_ARGS[address]))
        )

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)

        if address == STUB_2C39A4:
            self._log(address, r0)
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case["screen_address"] & 0xFFFFFFFF
            )
        elif address == STUB_2BC300:
            self._log(address, r0)
            explicit = self.case.get("translate_results")
            if explicit is not None:
                index = self.translate_index
                self.translate_index += 1
                value = explicit[index] if index < len(explicit) else explicit[-1]
            else:
                value = (r0 + self.case.get("translate_bias", 0)) & 0xFFFFFFFF
            uc.reg_write(arm.UC_ARM_REG_R0, value)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

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
        self.case = case
        self.translate_index = 0
        self.code = code

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(ARENA_ADDR, build_arena(case))
        self.uc.mem_write(ENTRY_ADDR, build_entry(case))
        self.uc.mem_write(PACKET_ADDR, build_packet())
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        override = case.get("table_override")
        write_u32(
            self.uc,
            KIND_TABLE,
            AUTHENTIC_KIND0 if override is None else override,
        )
        write_u32(self.uc, GPU_CURSOR, case["global_cursor"])
        write_u32(self.uc, GPU_END, case["global_end"])

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, ARENA_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, ENTRY_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R2, case["force"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R3, case.get("junk_r3", 0x33333333))
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self._normalise(self.call_log),
            "memory": {
                "packet": bytes(self.uc.mem_read(PACKET_ADDR, PACKET_SIZE)),
                "arena": bytes(self.uc.mem_read(ARENA_ADDR, ARENA_SIZE)),
                "entry": bytes(self.uc.mem_read(ENTRY_ADDR, ENTRY_SIZE)),
            },
            "globals": (
                read_u32(self.uc, GPU_CURSOR),
                read_u32(self.uc, GPU_END),
            ),
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig="
            + repr(orig["call_log"])
            + "\n    cand="
            + repr(cand["call_log"])
        )
    for name, value in orig["memory"].items():
        if value != cand["memory"][name]:
            first = next(
                index
                for index, (left, right) in enumerate(
                    zip(value, cand["memory"][name])
                )
                if left != right
            )
            problems.append(
                f"memory {name} differs first at +0x{first:04x}: "
                f"orig=0x{value[first]:02x} cand=0x{cand['memory'][name][first]:02x}"
            )
    if orig["globals"] != cand["globals"]:
        problems.append(
            f"globals:\n    orig={orig['globals']!r}\n    cand={cand['globals']!r}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "kind": 0,
        "type": 0,
        "value": 0x11223344,
        "relative": 0x40,
        "address": 0,
        "force": 0,
        "junk_r3": 0x33333333,
        "screen_address": 0x1F000000,
        "table_override": None,
        "translate_results": None,
        "translate_bias": 0,
        "arena_cursor": PACKET_ADDR + 0x200,
        "arena_limit": PACKET_ADDR + 0x200 + 0x100,
        "global_cursor": PACKET_ADDR + 0x800,
        "global_end": PACKET_ADDR + 0x900,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- authentic kind table entries 0..3 plus a short index sweep
    cases.append(base_case("authentic kind index 0 (-> 4)"))
    cases.append(base_case("authentic kind index 1 (-> 5)", kind=1))
    cases.append(base_case("authentic kind index 2 (-> 6)", kind=2))
    cases.append(base_case("authentic kind index 3 (untouched +0x20)", kind=3))
    for index in range(4, 32):
        cases.append(base_case(f"authentic kind index {index}", kind=index))

    # --- synthetic table values exercise every kind branch and its boundaries
    for value in (
        0,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        0x6010,
        0x6011,
        0x00010000,
        0x7FFFFFFF,
        0x80000000,
        0xFFFFFFFE,
        0xFFFFFFFF,
    ):
        cases.append(
            base_case(f"table override 0x{value:08x}", table_override=value)
        )

    # --- force-kind overrides win over every table value
    for force in (1, 2, 0xFFFFFFFF, 0x80000000):
        cases.append(base_case(f"force 0x{force:08x}", force=force))
        cases.append(
            base_case(f"force 0x{force:08x} kind 2", force=force, kind=2)
        )

    # --- 0x1403 variant: bit 31 and the value halved (signed boundaries)
    for value in (0, 1, 2, 3, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFE, 0xFFFFFFFF):
        cases.append(
            base_case(
                f"type 0x1403 value 0x{value:08x}",
                type=0x1403,
                value=value,
            )
        )
    for type_value in (0, 0x1402, 0x1404, 0xFFFFFFFF, 0x00001403 + 0x10000):
        cases.append(
            base_case(
                f"type 0x{type_value:08x} is not special",
                type=type_value,
                value=0xFFFFFFFF,
            )
        )

    # --- source address selection: [entry+0x20] wins over the self-relative
    cases.append(base_case("relative 0 -> address 0 translated", relative=0))
    cases.append(
        base_case("address 0, relative 1", relative=1)
    )
    cases.append(
        base_case("address 0, relative 0xFFFFFFF4 wraps", relative=0xFFFFFFF4)
    )
    cases.append(
        base_case(
            "address 0, relative 0x80000000",
            relative=0x80000000,
        )
    )
    cases.append(
        base_case(
            "address and relative both set",
            relative=0x4000,
            address=0x00480000,
        )
    )
    cases.append(
        base_case(
            "address 0xFFFFFFFF",
            relative=0x4000,
            address=0xFFFFFFFF,
        )
    )

    # --- translation results: offset wrapping in both directions
    cases.append(
        base_case(
            "translate results 0x1000/0x1200",
            translate_results=[0x1000, 0x1200],
        )
    )
    cases.append(
        base_case(
            "translate results 0x2000/0x1000 wraps to 0xFFFFF000",
            translate_results=[0x2000, 0x1000],
        )
    )
    cases.append(
        base_case(
            "translate results 0xFFFFFFFF/0",
            translate_results=[0xFFFFFFFF, 0],
        )
    )
    cases.append(
        base_case(
            "translate results 0/0",
            translate_results=[0, 0],
        )
    )
    cases.append(
        base_case(
            "translate results 0x80000000/0x80000000",
            translate_results=[0x80000000, 0x80000000],
        )
    )
    for bias in (0x40, 0x1000, 0xFFFFFF00, 0xFFFFFFFF):
        cases.append(base_case(f"translate bias 0x{bias:08x}", translate_bias=bias))

    # --- arena limit boundaries (unsigned compare of cursor + 0x70)
    for delta, label in (
        (0x70, "exactly fits"),
        (0x6F, "one byte short"),
        (0x71, "one byte spare"),
        (0x1000, "plenty of room"),
        (0x0, "limit below cursor"),
        (0xFFFFFFFF, "limit wraps below cursor"),
    ):
        cursor = PACKET_ADDR + 0x200
        cases.append(
            base_case(
                f"arena limit {label} (+0x{delta:x})",
                arena_cursor=cursor,
                arena_limit=(cursor + delta) & 0xFFFFFFFF,
            )
        )
    cases.append(
        base_case(
            "arena cursor at page start",
            arena_cursor=PACKET_ADDR,
            arena_limit=PACKET_ADDR + 0x70,
        )
    )
    cases.append(
        base_case(
            "arena cursor at last full packet",
            arena_cursor=PACKET_ADDR + PACKET_SIZE - 0x70,
            arena_limit=PACKET_ADDR + PACKET_SIZE,
        )
    )

    # --- shared-global fallback when the arena cursor is null
    for delta, label in (
        (0x70, "exactly fits"),
        (0x6F, "one byte short"),
        (0x71, "one byte spare"),
        (0x0, "end below cursor"),
        (0xFFFFFFFF, "end below cursor (wrapped)"),
    ):
        cursor = PACKET_ADDR + 0x400
        cases.append(
            base_case(
                f"global cursor {label} (+0x{delta:x})",
                arena_cursor=0,
                arena_limit=0xFFFFFFFF,
                global_cursor=cursor,
                global_end=(cursor + delta) & 0xFFFFFFFF,
            )
        )
    cases.append(
        base_case(
            "global cursor at page start",
            arena_cursor=0,
            arena_limit=0,
            global_cursor=PACKET_ADDR,
            global_end=PACKET_ADDR + 0x100,
        )
    )
    cases.append(
        base_case(
            "globals zero but arena cursor used",
            arena_cursor=PACKET_ADDR + 0x200,
            arena_limit=PACKET_ADDR + 0x400,
            global_cursor=0,
            global_end=0,
        )
    )

    # --- register junk and combined scenarios
    cases.append(
        base_case(
            "junk r3 ignored",
            junk_r3=0xFFFFFFFF,
            kind=2,
            type=0x1403,
            value=0xDEADBEEF,
            arena_cursor=PACKET_ADDR + 0x100,
            arena_limit=PACKET_ADDR + 0x170,
        )
    )
    cases.append(
        base_case(
            "combined forced kind, special type, global fallback",
            force=1,
            type=0x1403,
            value=0x7FFFFFFF,
            relative=0x800,
            arena_cursor=0,
            arena_limit=0,
            global_cursor=PACKET_ADDR + 0x300,
            global_end=PACKET_ADDR + 0x370 + 1,
        )
    )

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    orig_runner = BCACRunner()
    cand_runner = BCACRunner()
    passed = 0
    for case in cases:
        orig = orig_runner.run(orig_code, case)
        cand = cand_runner.run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        if orig["ret"] != 0x70:
            print(f"  [FAIL] {case['name']} original returned 0x{orig['ret']:x}")
            raise SystemExit(1)
        if len(orig["call_log"]) != 3:
            print(
                f"  [FAIL] {case['name']} unexpected call count "
                f"{len(orig['call_log'])}"
            )
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing engine_func_0015bcac (0x0015bcac)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        (
            "special_type",
            "constexpr u32 kSpecialType = 0x00001403;",
            "constexpr u32 kSpecialType = 0x00001402;",
        ),
        (
            "forced_kind",
            "constexpr u32 kForcedKind = 0x00006010;",
            "constexpr u32 kForcedKind = 0x00006011;",
        ),
        (
            "kind_attribute",
            "        out[8] = 0x300u;",
            "        out[8] = 0x301u;",
        ),
        (
            "halving_shift",
            "        second_value >>= 1;",
            "        second_value >>= 2;",
        ),
        (
            "exact_fit_compare",
            "static_cast<u32>(cursor + kPacketSize) <= arena->limit_04",
            "static_cast<u32>(cursor + kPacketSize) < arena->limit_04",
        ),
        (
            "command_word",
            "constexpr u32 kCmdVtx025E = 0x0008025E;",
            "constexpr u32 kCmdVtx025E = 0x0008025F;",
        ),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        orig_runner = BCACRunner()
        mutant_runner = BCACRunner()
        detected = False
        for case in cases:
            orig = orig_runner.run(orig_code, case)
            bad = mutant_runner.run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
