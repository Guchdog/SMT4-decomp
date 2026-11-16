#!/usr/bin/env python3
"""Differential test for engine_func_0015e600 (0x0015e600) using Unicorn ARM.

Compiles src/engine/leaf_batch34_c.cpp, extracts the engine_func_0015e600 body,
resolves its thirteen direct calls plus the one tail branch to deterministic
stubs at the original target addresses, and runs the pinned original
(extracted/exefs/code.bin) against the candidate in separate Unicorn machines
with identical fixtures.

Compared outputs:
  * continuation PC, final SP and the callee-saved r4-r11 (all must be restored);
  * the ordered call log: helper name, every register argument, the four
    architected stack words of 0x0015E7D0, the mount name both strings seen by
    the 0x002AA7F4 comparison, and the status argument of every 0x002A13D0;
  * the full contents of the out, context, mount-name, applet1, applet2 and
    global pages (JSON-style byte equality), so the 16-byte name copy, the
    +0x330 flag, the 0x64/0xC8 status stores and the 0x754 flag clear are all
    pinned;
  * every emulated write outside the private stack is bucketed by fixture page,
    so a stray write is reported without depending on store width or order;
  * r0 at return is recorded for both sides (see the note below) but is not a
    contract of this function.

r0 at return is leftover register state in the original: `out` on the
string-equal and request-success paths, 0 on the release-failure path and
0x64/0xC8 on the failure path.  The sole caller (0x0015DB38) ignores it, so the
test records it for both runs and asserts it against those documented leftovers
instead of comparing candidate garbage with original garbage.

Coverage: string equal, string equal with a mounted flag, first-byte difference,
difference inside the 16-byte field, difference only after the 16-byte field,
and a self-overlapping mount pointer; mounted 0/1 with release codes 0,
0x7FFFFFFF, 0x80000000 and 0xFFFFFFFF; request codes 0, 0x7FFFFFFF, 0x80000000
and 0xFFFFFFFF; the applet lock refusing and accepting, with the 0x10000 bit
alone and among other flag bits; a stub-only [negative, non-negative] result
sequence that exercises the second `>= 0` test; the applet global rewritten by
the lock stub to prove the second global load; and mount/index/value sentinels.

Negative controls mutate the pending/retry status bytes, the cleared applet bit,
the content id, the request mode, the lock offset, the trailing request word,
the success test and the 16-byte copy count; each mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_0015e600"

FUNC_ADDR = 0x0015E600
FUNC_SIZE = 448

# The candidate body (548 B) is wider than the original span and would overlap
# the 0x0015E7D0 stub, so it is relocated to a free address in the same code
# region.  ARM branches are PC-relative and the only literal in the body is the
# absolute 0x00432FC8 slot, so the body is position independent.
CAND_ADDR = 0x00200000

# Every stub target lives below 0x00300000.
CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000
OUT_ADDR = 0x00710000
OUT_SIZE = 0x00001000
CTX_ADDR = 0x00711000
CTX_SIZE = 0x00001000
NAME_ADDR = 0x00712000
NAME_SIZE = 0x00001000
APP1_ADDR = 0x00713000
APP1_SIZE = 0x00001000
APP2_ADDR = 0x00714000
APP2_SIZE = 0x00001000
GLOBAL_ADDR = 0x00432000
GLOBAL_SIZE = 0x00002000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100
NAME_PTR = NAME_ADDR + 0x100
APPLET_SLOT = 0x00432FC8

STUB_2AA7F4 = 0x002AA7F4
STUB_2C4000 = 0x002C4000
STUB_2A13D0 = 0x002A13D0
STUB_2BB09C = 0x002BB09C
STUB_15E7D0 = 0x0015E7D0
STUB_2BAD80 = 0x002BAD80
STUB_2A1578 = 0x002A1578
STUB_2C583C = 0x002C583C
STUB_2AD46C = 0x002AD46C

STUB_NAMES = {
    STUB_2AA7F4: "engine_func_002aa7f4",
    STUB_2C4000: "engine_func_002c4000",
    STUB_2A13D0: "engine_func_002a13d0",
    STUB_2BB09C: "engine_func_002bb09c",
    STUB_15E7D0: "func_0015e7d0",
    STUB_2BAD80: "engine_func_002bad80",
    STUB_2A1578: "engine_func_002a1578",
    STUB_2C583C: "engine_func_002c583c",
    STUB_2AD46C: "engine_func_002ad46c",
}

# Number of architected stack words each helper receives.
STACK_ARGS = {
    STUB_2AA7F4: 0,
    STUB_2C4000: 0,
    STUB_2A13D0: 0,
    STUB_2BB09C: 0,
    STUB_15E7D0: 4,   # mode_b=2, word20, value34, 0
    STUB_2BAD80: 0,
    STUB_2A1578: 0,
    STUB_2C583C: 0,
    STUB_2AD46C: 0,
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

# Documented leftover r0 values of the original per exit path.
LEFTOVER_R0 = {OUT_ADDR, 0x00000000, 0x00000064, 0x000000C8}

EMPTY_STATUS = 0x00
PENDING_STATUS = 0x64
RETRY_STATUS = 0xC8


def module_for(code: int) -> int:
    """Deterministic stand-in for the 0x002BAD80 module-descriptor lookup."""
    return (0x51000000 ^ code) & 0xFFFFFFFF


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0015e600" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_0015e600 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        # R_ARM_CALL for the thirteen calls, R_ARM_JUMP24 for the tail branch
        # to 0x002A13D0.
        if rel.relocation_type not in (28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = None
        for address, name in STUB_NAMES.items():
            if name == rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")

        pc = CAND_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        cond = original & 0xFF000000
        struct.pack_into(
            "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
        )
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch34_c.o"
    res = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    res = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


# --------------------------------------------------------------------- fixtures
def pattern_page(size: int, salt: int) -> bytes:
    return bytes(((index * 7 + salt) & 0xFF) for index in range(size))


def name_bytes(value: str) -> bytes:
    raw = value.encode("ascii")
    if len(raw) > 16:
        raise ValueError("mount name fixtures are at most 16 bytes")
    return raw + b"\x00" * (16 - len(raw))


def build_out() -> bytes:
    return pattern_page(OUT_SIZE, 0x03)


def build_ctx(case: dict) -> bytes:
    page = bytearray(pattern_page(CTX_SIZE, 0x11))
    page[0x330] = case.get("mounted", 0) & 0xFF
    page[0x331:0x341] = case.get("ctx_name", name_bytes("aoc:0000"))
    return bytes(page)


def build_name_page(case: dict) -> bytes:
    page = bytearray(pattern_page(NAME_SIZE, 0x22))
    page[0x100:0x110] = case.get("mount_name", name_bytes("aoc:0001"))
    # Byte immediately after the 16-byte field, used by the over-read case.
    page[0x110] = case.get("name_byte_after", 0x5A) & 0xFF
    # Byte immediately before the field.
    page[0x0FF] = case.get("name_byte_before", 0xA5) & 0xFF
    return bytes(page)


def build_applet(salt: int, flags: int) -> bytes:
    page = bytearray(pattern_page(0x1000, salt))
    page[0x98] = 0x3C
    struct.pack_into("<I", page, 0x754, flags & 0xFFFFFFFF)
    return bytes(page)


def build_global(applet: int) -> bytes:
    page = bytearray(pattern_page(GLOBAL_SIZE, 0x55))
    struct.pack_into("<I", page, APPLET_SLOT - GLOBAL_ADDR, applet & 0xFFFFFFFF)
    return bytes(page)


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        # The original body opens with `vpush {d8}`; the 3DS OS leaves the VFP
        # unit enabled, so model that state before running either side.
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(GLOBAL_ADDR, GLOBAL_SIZE)
        self.uc.mem_map(OUT_ADDR, OUT_SIZE)
        self.uc.mem_map(CTX_ADDR, CTX_SIZE)
        self.uc.mem_map(NAME_ADDR, NAME_SIZE)
        self.uc.mem_map(APP1_ADDR, APP1_SIZE)
        self.uc.mem_map(APP2_ADDR, APP2_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}
        self.result_calls = 0

    # ------------------------------------------------------------------ helpers
    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        raw = self.uc.mem_read(sp, 4 * count)
        return struct.unpack(f"<{count}I", raw)

    def _read_cstr(self, address: int, limit: int = 64) -> bytes:
        raw = bytes(self.uc.mem_read(address, limit))
        end = raw.find(b"\x00")
        return raw[:end] if end >= 0 else raw

    def _log(self, address: int, args: tuple) -> None:
        self.call_log.append(
            (STUB_NAMES[address], args + self._stack_words(STACK_ARGS[address]))
        )

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    @staticmethod
    def _pick(sequence, index: int, default: int) -> int:
        if not sequence:
            return default
        return sequence[index] if index < len(sequence) else sequence[-1]

    # -------------------------------------------------------------------- stubs
    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        case = self.case

        if address == STUB_2AA7F4:
            left = self._read_cstr(r0)
            right = self._read_cstr(r1)
            outcome = 0 if left == right else (1 if left > right else -1)
            self._log(address, (r0, r1, left, right, outcome))
            uc.reg_write(arm.UC_ARM_REG_R0, outcome & 0xFFFFFFFF)
        elif address == STUB_2C4000:
            name = self._read_cstr(r0)
            self._log(address, (r0, name))
            uc.reg_write(
                arm.UC_ARM_REG_R0, case.get("release_code", 0) & 0xFFFFFFFF
            )
        elif address == STUB_2A13D0:
            status = r1 & 0xFF
            self._log(address, (r0, r1))
            uc.mem_write(r0, bytes((status,)))
            uc.mem_write(
                r0 + 4,
                struct.pack("<3I", 0, module_for(0), 0) + struct.pack("<I", 0),
            )
            uc.reg_write(arm.UC_ARM_REG_R0, r0)
        elif address == STUB_2BB09C:
            self._log(address, (r0,))
            uc.mem_write(r0, struct.pack("<2I", 0x2BB0B0C0, 0))
            uc.reg_write(arm.UC_ARM_REG_R0, r0)
        elif address == STUB_15E7D0:
            self._log(address, (r0, r1, r2, r3))
            uc.reg_write(
                arm.UC_ARM_REG_R0, case.get("request_code", 0) & 0xFFFFFFFF
            )
        elif address == STUB_2BAD80:
            self._log(address, (r0, r1))
            uc.mem_write(
                r0, struct.pack("<2I", r1 & 0xFFFFFFFF, module_for(r1))
            )
            uc.reg_write(arm.UC_ARM_REG_R0, r0)
        elif address == STUB_2A1578:
            stored = struct.unpack("<I", uc.mem_read(r0, 4))[0]
            self._log(address, (r0, stored))
            override = self._pick(
                case.get("result_values"), self.result_calls, stored
            )
            self.result_calls += 1
            uc.reg_write(arm.UC_ARM_REG_R0, override & 0xFFFFFFFF)
        elif address == STUB_2C583C:
            self._log(address, (r0,))
            uc.reg_write(
                arm.UC_ARM_REG_R0, case.get("table_entry", 0x51510000) & 0xFFFFFFFF
            )
        elif address == STUB_2AD46C:
            self._log(address, (r0,))
            if case.get("rewrite_applet"):
                self.uc.mem_write(
                    APPLET_SLOT, struct.pack("<I", case["rewrite_applet"])
                )
            uc.reg_write(
                arm.UC_ARM_REG_R0, case.get("lock_result", 0) & 0xFFFFFFFF
            )
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict, addr: int = FUNC_ADDR) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case
        self.result_calls = 0

        self.uc.mem_write(addr, code)
        self.uc.mem_write(OUT_ADDR, build_out())
        self.uc.mem_write(CTX_ADDR, build_ctx(case))
        self.uc.mem_write(NAME_ADDR, build_name_page(case))
        self.uc.mem_write(
            APP1_ADDR, build_applet(0x66, case.get("applet1_flags", 0))
        )
        self.uc.mem_write(
            APP2_ADDR, build_applet(0x77, case.get("applet2_flags", 0))
        )
        self.uc.mem_write(
            GLOBAL_ADDR, build_global(case.get("applet", APP1_ADDR))
        )
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        # Fifth and sixth arguments sit at the caller's SP.
        self.uc.mem_write(
            ENTRY_SP,
            struct.pack(
                "<II",
                case.get("value34", 0x3F800000) & 0xFFFFFFFF,
                case.get("index", 0) & 0xFFFFFFFF,
            ),
        )
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, OUT_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, CTX_ADDR)
        self.uc.reg_write(
            arm.UC_ARM_REG_R2, case.get("mount_ptr", NAME_PTR)
        )
        self.uc.reg_write(
            arm.UC_ARM_REG_R3, case.get("word20", 0x2000BEEF) & 0xFFFFFFFF
        )
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(
                addr, TRAP_ADDR, timeout=5_000_000, count=1_000_000
            )
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        regions = sorted(
            {
                self._region(address)
                for address, _size in self.writes
                if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
            }
        )

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self._normalise(self.call_log),
            "write_regions": regions,
            "fixtures": {
                "out": bytes(self.uc.mem_read(OUT_ADDR, OUT_SIZE)),
                "ctx": bytes(self.uc.mem_read(CTX_ADDR, CTX_SIZE)),
                "name": bytes(self.uc.mem_read(NAME_ADDR, NAME_SIZE)),
                "applet1": bytes(self.uc.mem_read(APP1_ADDR, APP1_SIZE)),
                "applet2": bytes(self.uc.mem_read(APP2_ADDR, APP2_SIZE)),
                "global": bytes(self.uc.mem_read(GLOBAL_ADDR, GLOBAL_SIZE)),
            },
        }

    @staticmethod
    def _region(address: int) -> str:
        for name, base, size in (
            ("out", OUT_ADDR, OUT_SIZE),
            ("ctx", CTX_ADDR, CTX_SIZE),
            ("name", NAME_ADDR, NAME_SIZE),
            ("applet1", APP1_ADDR, APP1_SIZE),
            ("applet2", APP2_ADDR, APP2_SIZE),
            ("global", GLOBAL_ADDR, GLOBAL_SIZE),
        ):
            if base <= address < base + size:
                return name
        return "unmapped"

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


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("pc", "sp", "callee_saved", "write_regions"):
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
            for index, (left, right) in enumerate(zip(value, cand["fixtures"][key])):
                if left != right:
                    problems.append(
                        f"fixture {key} first differs at +0x{index:03x}: "
                        f"orig=0x{left:02x} cand=0x{right:02x}"
                    )
                    break
            else:
                problems.append(f"fixture {key} length differs")
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "ctx_name": name_bytes("aoc:0000"),
        "mount_name": name_bytes("aoc:0001"),
        "mounted": 0,
        "mount_ptr": NAME_PTR,
        "word20": 0x2000BEEF,
        "value34": 0x3F800000,
        "index": 0,
        "release_code": 0,
        "request_code": 0,
        "lock_result": 0,
        "applet": APP1_ADDR,
        "applet1_flags": 0x00010000,
        "applet2_flags": 0x00010000,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- string comparison branch
    cases.append(
        base_case("names equal, no mount", ctx_name=name_bytes("aoc:0000"),
                  mount_name=name_bytes("aoc:0000"), mounted=0)
    )
    cases.append(
        base_case("names equal, mounted, applet flags cleared by request path",
                  ctx_name=name_bytes("aoc:0000"),
                  mount_name=name_bytes("aoc:0000"), mounted=1,
                  applet1_flags=0xFFFFFFFF)
    )
    cases.append(base_case("first byte differs"))
    cases.append(base_case("last in-field byte differs",
                           ctx_name=name_bytes("aoc:0000"),
                           mount_name=name_bytes("aoc:0001")))
    cases.append(
        base_case("byte after the 16-byte field differs",
                  ctx_name=b"aoc:0000aaaaaaaa", mount_name=b"aoc:0000aaaaaaaa",
                  name_byte_after=0xA6)
    )
    cases.append(
        base_case("no NUL inside either field",
                  ctx_name=b"0123456789abcdef", mount_name=b"0123456789abcdeF")
    )
    cases.append(
        base_case("mount pointer overlaps the stored name",
                  mount_ptr=CTX_ADDR + 0x335)
    )
    cases.append(
        base_case("mount pointer equals the stored name", mount_ptr=CTX_ADDR + 0x331)
    )

    # --- release branch (mounted != 0, names differ)
    for code in (0, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        cases.append(
            base_case(f"release returns 0x{code:08x}", mounted=1,
                      release_code=code)
        )
    cases.append(
        base_case("release negative with lock accepting", mounted=1,
                  release_code=0x80000001, lock_result=1,
                  applet1_flags=0x00010000)
    )
    cases.append(
        base_case("mounted flag 0xFF is non-zero", mounted=0xFF)
    )

    # --- request-result branch
    for code in (0, 0x00000001, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        cases.append(
            base_case(f"request returns 0x{code:08x}", request_code=code)
        )

    # --- failure path and the applet lock
    cases.append(
        base_case("request fails, lock refuses", request_code=0x80000000,
                  lock_result=0, applet1_flags=0x00010000)
    )
    cases.append(
        base_case("request fails, lock accepts, only bit 16 set",
                  request_code=0xFFFFFFFF, lock_result=1,
                  applet1_flags=0x00010000)
    )
    cases.append(
        base_case("request fails, lock accepts, bit 16 among others",
                  request_code=0xD9001234, lock_result=1,
                  applet1_flags=0xFFFFFFFF)
    )
    cases.append(
        base_case("request fails, lock accepts, bit 16 already clear",
                  request_code=0xD9001234, lock_result=1, applet1_flags=0x60)
    )
    cases.append(
        base_case("request fails, lock returns 2", request_code=0x80000000,
                  lock_result=2, applet1_flags=0x00010010)
    )
    cases.append(
        base_case("request fails on the second applet", request_code=0x80000000,
                  lock_result=1, applet1_flags=0x00010000,
                  applet2_flags=0x00030000, applet=APP2_ADDR)
    )
    cases.append(
        base_case("lock stub rewrites the applet global",
                  request_code=0x80000000, lock_result=1,
                  applet1_flags=0x00010000, applet2_flags=0x00030000,
                  rewrite_applet=APP2_ADDR)
    )

    # --- the repeated result test: second call reports success (stub-only)
    cases.append(
        base_case("second result test non-negative",
                  request_code=0x80000000, lock_result=1,
                  result_values=[0x80000000, 0x00000000])
    )
    cases.append(
        base_case("second result test non-negative, flags untouched",
                  request_code=0xFFFFFFFF, lock_result=1,
                  applet1_flags=0x00010000,
                  result_values=[0xFFFFFFFF, 0x7FFFFFFF])
    )
    cases.append(
        base_case("second result test negative again",
                  request_code=0x80000000, lock_result=1,
                  result_values=[0x80000000, 0x80000001])
    )

    # --- forwarded argument sentinels
    for word20 in (0x00000000, 0xFFFFFFFF, 0xDEADBEEF):
        cases.append(base_case(f"word20 0x{word20:08x}", word20=word20))
    for value34 in (0x00000000, 0x7FC00000, 0xFFFFFFFF):
        cases.append(base_case(f"value34 0x{value34:08x}", value34=value34))
    for index in (0x00000000, 0x0000FFFF, 0xFFFFFFFF):
        cases.append(base_case(f"index 0x{index:08x}", index=index))
    cases.append(
        base_case("all sentinels with a failing request", word20=0,
                  value34=0xFFFFFFFF, index=0xFFFFFFFF,
                  request_code=0x80000000, lock_result=1)
    )

    # --- full release + failure combination
    cases.append(
        base_case("release success then failing request", mounted=1,
                  release_code=0, request_code=0x80000000, lock_result=1,
                  applet1_flags=0x00010000)
    )
    cases.append(
        base_case("release success then successful request", mounted=1,
                  release_code=0, request_code=0)
    )

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    orig_runner = Runner()
    cand_runner = Runner()
    passed = 0
    for case in cases:
        orig = orig_runner.run(orig_code, case)
        cand = cand_runner.run(cand_code, case, CAND_ADDR)
        if orig["ret"] not in LEFTOVER_R0:
            raise SystemExit(
                f"  [FAIL] {case['name']}: unexpected original r0 "
                f"0x{orig['ret']:08x}"
            )
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(
            f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls, "
            f"r0=0x{orig['ret']:08x}, writes={orig['write_regions']})"
        )
    return passed


def main() -> None:
    print("Testing engine_func_0015e600 (0x0015e600)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        f"(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("pending_status", "constexpr u32 kStatusPending = 0x64;",
         "constexpr u32 kStatusPending = 0x65;"),
        ("retry_status", "constexpr u32 kStatusRetry = 0xC8;",
         "constexpr u32 kStatusRetry = 0xC9;"),
        ("applet_flag_mask", "constexpr u32 kAppletFlagMask = 0x00010000;",
         "constexpr u32 kAppletFlagMask = 0x00020000;"),
        ("content_id", "constexpr u32 kContentId = 0x00000E5C;",
         "constexpr u32 kContentId = 0x00000E5D;"),
        ("request_mode", "constexpr u32 kRequestMode = 2;",
         "constexpr u32 kRequestMode = 3;"),
        ("applet_lock_offset", "constexpr u32 kAppletLockOffset = 0x98;",
         "constexpr u32 kAppletLockOffset = 0x99;"),
        ("request_zero", "constexpr u32 kRequestZero = 0;",
         "constexpr u32 kRequestZero = 1;"),
        ("success_test",
         "    if (static_cast<s32>(result_value(&result)) >= 0) {",
         "    if (static_cast<s32>(result_value(&result)) > 0) {"),
        ("name_copy_words", "    for (u32 word = 0; word < 4; ++word) {",
         "    for (u32 word = 0; word < 3; ++word) {"),
        ("release_sign_test",
         "        if (static_cast<s32>(release_code) < 0) {",
         "        if (static_cast<s32>(release_code) <= 0) {"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, case)
            bad = Runner().run(mutant_code, case, CAND_ADDR)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
