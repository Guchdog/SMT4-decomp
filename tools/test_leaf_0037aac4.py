#!/usr/bin/env python3
"""Differential test for ui_func_0037aac4 (0x0037aac4) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the ui_func_0037aac4 body,
resolves its direct calls to deterministic stubs, and runs the pinned original
(extracted/exefs/code.bin) against the candidate in separate Unicorn machines
with identical fixtures.

The two indirect/SDK helpers stay real:
  * 0x002C5F58 is native Thumb code: it walks `count` records of `stride`
    bytes and calls the supplied initialiser for each one (BLX from ARM).
  * 0x0014C158 is the native ARM initialiser that stores {-1, 0} into an
    8-byte record.  Hooking it proves the candidate forwards the same
    initialiser address and record pointers.

Compared outputs:
  * return r0 (only when a callback is installed, see below), PC, SP and the
    callee-saved r4-r11;
  * the ordered call log with every register argument and the architected stack
    arguments of each helper (0x2AF648 and 0x37C034 take one stack word, the
    object callback takes two);
  * the object-callback snapshots: key word, raw id array, bound array and
    per-entry flag bytes as seen by the callback;
  * the full object page, the owner/extra pages and the stack-independent
    fixture pages (must match byte for byte);
  * every memory write outside the private stack page (must match).

Return-value caveat: the original is a void routine.  Every exit that has a
callback runs `blx <callback>` and therefore leaves the callback's r0 behind;
the exits guarded by `callback == null` fall through to the shared epilogue
with whatever r0 the previous helper left.  r0 is still compared on every case
(the candidate reproduces the same leftover on all current cases) but the
null-callback value is a compiler artefact, not part of the contract.

Coverage: key/key_handle gating (zero, -1, signed boundaries), request return
zero/non-zero with and without a callback on the primary key and on every loop
index, resolve returning zero and non-zero, handle cached vs. pending, id -1
with stale handle, bind results -1/0/1/2/3/0x7FFFFFFF/0x80000000, commit
success and failure with and without a callback, null and non-null `extra`,
null `owner`, contract-boundary parameter values, a fully idle entry set and
all-skipped loop completion.  Negative controls mutate the entry request mode,
the first bind's owner argument, the retry bind's owner argument, the
`result == 2` arm, the loop bound and the success callback's id pointer.
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
OUT_DIR = ROOT / "build/test_leaf_0037aac4"

FUNC_ADDR = 0x0037AAC4
FUNC_SIZE = 596

CODE_ADDR = 0x00100000          # image base of code.bin
CODE_SIZE = 0x00300000          # covers 0x14C158 .. 0x37AAC4 + body
OBJECT_ADDR = 0x00710000
OBJECT_SIZE = 0x00010000
OWNER_ADDR = 0x00720000
OWNER_SIZE = 0x00001000
EXTRA_ADDR = 0x00730000
EXTRA_SIZE = 0x00001000
CALLBACK_ADDR = 0x00740000
CALLBACK_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x200

# Object layout (see the C++ declaration above the function block).
OBJ_OWNER = 0x1C
OBJ_OWNER_PARAM = 0x20
OBJ_CALLBACK = 0x24
OBJ_CALLBACK_CTX = 0x28
OBJ_EXTRA = 0x2C
OBJ_AUX = 0x30
OBJ_KEY = 0x34
OBJ_KEY_HANDLE = 0x38
OBJ_ENTRIES = 0x3C
ENTRY_STRIDE = 8
ENTRY_COUNT = 4

# Original direct-call targets / native helpers.  Stubs are placed at the same
# addresses so both the original bytes and the relocated candidate resolve to
# them; the two helpers below stay real.
STUB_2AF648 = 0x002AF648        # request(id) -> nonzero when usable
STUB_235E08 = 0x00235E08        # resolve(id) -> handle
STUB_37C034 = 0x0037C034        # bind(entry, flag, handle, aux, extra)
STUB_37B82C = 0x0037B82C        # commit(handle, param) -> nonzero on success
REAL_2C5F58 = 0x002C5F58        # Thumb stride-callback loop (BLX)
REAL_14C158 = 0x0014C158        # ARM {-1, 0} record initialiser

THUMB_CALLS = {REAL_2C5F58}

STUB_NAMES = {
    STUB_2AF648: "engine_func_002af648",
    STUB_235E08: "engine_func_00235e08",
    STUB_37C034: "engine_func_0037c034",
    STUB_37B82C: "engine_func_0037b82c",
    REAL_2C5F58: "ui_func_002c5f58",
    REAL_14C158: "func_0014c158",
}

# Number of architected stack words each helper receives.
STACK_ARGS = {
    STUB_2AF648: 1,   # flags = 0
    STUB_235E08: 0,
    STUB_37C034: 1,   # extra owner (or 0)
    STUB_37B82C: 0,
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


def read_image(address: int, size: int) -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(address - CODE_ADDR)
        return handle.read(size)


def get_orig_bytes() -> bytes:
    return read_image(FUNC_ADDR, FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0037aac4" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"ui_func_0037aac4 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    seen = set()
    for rel in relocs:
        target = None
        for address, name in STUB_NAMES.items():
            if f"{address:08x}" in rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved relocation: {rel.symbol_name}")
        seen.add(target)
        if rel.relocation_type == 2:  # R_ARM_ABS32 (initialiser address)
            struct.pack_into("<I", code, rel.offset, target)
            continue
        if rel.relocation_type not in (1, 28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        pc = FUNC_ADDR + rel.offset + 8
        offset = target - pc
        if target in THUMB_CALLS:
            if offset & 3:
                raise RuntimeError(f"unaligned Thumb target 0x{target:08x}")
            instruction = (
                0xFA000000
                | ((offset >> 2) & 0x00FFFFFF)
                | ((offset & 2) << 23)
            )
            struct.pack_into("<I", code, rel.offset, instruction)
        else:
            displacement = offset >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
            )

    expected = set(STUB_NAMES)
    # The initialiser address is a data relocation, not a branch, but it must
    # still be present or the candidate is not the expected routine.
    if seen != expected:
        raise RuntimeError(
            f"relocation targets {sorted(seen)} != expected {sorted(expected)}"
        )
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
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
def fill_pattern(size: int, seed: int) -> bytearray:
    page = bytearray(size)
    for index in range(size):
        page[index] = (seed + index * 7) & 0xFF
    return page


def owner_pointer(case: dict) -> int:
    return OWNER_ADDR if case.get("owner", True) else 0


def extra_pointer(case: dict) -> int:
    return EXTRA_ADDR if case.get("extra", True) else 0


def build_object(case: dict) -> bytes:
    page = fill_pattern(OBJECT_SIZE, 0x31)
    struct.pack_into("<I", page, 0x00, 0xDEADBEEF)  # vtable word: never touched
    struct.pack_into("<I", page, OBJ_OWNER, owner_pointer(case))
    struct.pack_into("<I", page, OBJ_OWNER_PARAM,
                     case.get("owner_param", 0x11223344) & 0xFFFFFFFF)
    callback = CALLBACK_ADDR if case.get("callback", True) else 0
    struct.pack_into("<I", page, OBJ_CALLBACK, callback)
    struct.pack_into("<I", page, OBJ_CALLBACK_CTX,
                     case.get("callback_ctx", 0xCAFEBABE) & 0xFFFFFFFF)
    struct.pack_into("<I", page, OBJ_EXTRA, extra_pointer(case))
    struct.pack_into("<I", page, OBJ_AUX, case.get("aux", 0x55667788) & 0xFFFFFFFF)
    struct.pack_into("<I", page, OBJ_KEY, case.get("key", 0x1234) & 0xFFFFFFFF)
    struct.pack_into("<I", page, OBJ_KEY_HANDLE,
                     case.get("key_handle", 0) & 0xFFFFFFFF)
    entries = case.get("entries")
    if entries is None:
        entries = [(0x100, 0), (0x101, 0), (0x102, 0), (0x103, 0)]
    for index, (entry_id, handle) in enumerate(entries):
        base = OBJ_ENTRIES + index * ENTRY_STRIDE
        struct.pack_into("<I", page, base, entry_id & 0xFFFFFFFF)
        struct.pack_into("<I", page, base + 4, handle & 0xFFFFFFFF)
    return bytes(page)


def build_side_page(size: int, seed: int) -> bytes:
    page = fill_pattern(size, seed)
    struct.pack_into("<I", page, 0x0C, 0x0C0C0C0C)
    return bytes(page)


def read_bytes(uc, address: int, size: int) -> bytes:
    return bytes(uc.mem_read(address, size))


class AA_C4Runner:
    """One Unicorn machine with deterministic stubs and real 0x2C5F58."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(OBJECT_ADDR, OBJECT_SIZE)
        self.uc.mem_map(OWNER_ADDR, OWNER_SIZE)
        self.uc.mem_map(EXTRA_ADDR, EXTRA_SIZE)
        self.uc.mem_map(CALLBACK_ADDR, CALLBACK_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in (STUB_2AF648, STUB_235E08, STUB_37C034, STUB_37B82C):
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.mem_write(CALLBACK_ADDR, struct.pack("<I", 0xE12FFF1E))
        self.uc.hook_add(
            unicorn.UC_HOOK_CODE,
            self._on_callback,
            begin=CALLBACK_ADDR,
            end=CALLBACK_ADDR,
        )
        # Native helpers stay real; only log their entry arguments.
        self.uc.hook_add(
            unicorn.UC_HOOK_CODE,
            self._on_stride_helper,
            begin=REAL_2C5F58,
            end=REAL_2C5F58,
        )
        self.uc.hook_add(
            unicorn.UC_HOOK_CODE,
            self._on_init,
            begin=REAL_14C158,
            end=REAL_14C158,
        )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.counters: dict = {}
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        return struct.unpack(f"<{count}I", self.uc.mem_read(sp, 4 * count))

    def _log(self, address: int, *args) -> None:
        self.call_log.append(
            (
                STUB_NAMES[address],
                args + self._stack_words(STACK_ARGS.get(address, 0)),
            )
        )

    def _next(self, table: str, default: int) -> int:
        index = self.counters.get(table, 0)
        self.counters[table] = index + 1
        values = self.case.get(table, ())
        if index < len(values):
            return values[index] & 0xFFFFFFFF
        return default

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_2AF648:
            self._log(address, r0, r1, r2, r3)
            uc.reg_write(arm.UC_ARM_REG_R0, self._next("request_results", 1))
        elif address == STUB_235E08:
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0,
                         self._next("resolve_results", 0x70000000))
        elif address == STUB_37C034:
            self._log(address, r0, r1, r2, r3)
            index = self.counters.get("bind_calls", 0) + 1
            self.counters["bind_calls"] = index
            uc.mem_write(r0, struct.pack("<I", r2))
            uc.mem_write(r0 + 4, struct.pack("<I", 0xB0B00000 | index))
            uc.mem_write(r1, bytes([0x80 | index]))
            uc.reg_write(arm.UC_ARM_REG_R0, self._next("bind_results", 0))
        elif address == STUB_37B82C:
            self._log(address, r0, r1, r2)
            uc.reg_write(arm.UC_ARM_REG_R0, self._next("commit_results", 1))
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def _on_stride_helper(self, uc, address: int, size: int, user_data) -> None:
        self._log(
            address,
            uc.reg_read(arm.UC_ARM_REG_R0),
            uc.reg_read(arm.UC_ARM_REG_R1),
            uc.reg_read(arm.UC_ARM_REG_R2),
            uc.reg_read(arm.UC_ARM_REG_R3),
        )

    def _on_init(self, uc, address: int, size: int, user_data) -> None:
        self._log(address, uc.reg_read(arm.UC_ARM_REG_R0))

    def _on_callback(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        stack0, stack1 = struct.unpack(
            "<2I", uc.mem_read(uc.reg_read(arm.UC_ARM_REG_SP), 8)
        )
        snapshot = {
            "command": r0,
            "key": read_bytes(uc, r1, 4) if r1 else b"",
            "ids": read_bytes(uc, r2, ENTRY_COUNT * ENTRY_STRIDE)
            if r2 else b"",
            "bound": read_bytes(uc, r3, ENTRY_COUNT * ENTRY_STRIDE)
            if r3 else b"",
            "flags": read_bytes(uc, stack0, ENTRY_COUNT)
            if stack0 else b"",
            "context": stack1,
        }
        self.call_log.append(("object_callback", snapshot))
        uc.reg_write(
            arm.UC_ARM_REG_R0, self._next("callback_results", 0xC0DE0000)
        )

    # -------------------------------------------------------------- execution
    @staticmethod
    def _normalise(log) -> list:
        normalised = []
        for entry in log:
            name, args = entry
            if isinstance(args, dict):
                # Callback snapshots are byte images read through the argument
                # pointers; they are position independent and compared as-is.
                normalised.append((name, args))
                continue
            out = []
            for arg in args:
                if (
                    isinstance(arg, int)
                    and STACK_ADDR <= arg < STACK_ADDR + STACK_SIZE
                ):
                    out.append("<stack>")
                else:
                    out.append(arg)
            normalised.append((name, tuple(out)))
        return normalised

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.counters = {}
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(OBJECT_ADDR, build_object(case))
        self.uc.mem_write(OWNER_ADDR, build_side_page(OWNER_SIZE, 0x77))
        self.uc.mem_write(EXTRA_ADDR, build_side_page(EXTRA_SIZE, 0x99))
        self.uc.mem_write(CALLBACK_ADDR, struct.pack("<I", 0xE12FFF1E)
                          + b"\x00" * (CALLBACK_SIZE - 4))
        self.uc.mem_write(REAL_2C5F58, read_image(REAL_2C5F58, 36))
        self.uc.mem_write(REAL_14C158, read_image(REAL_14C158, 16))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, OBJECT_ADDR)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        # Object-page stores are expected; keep every write outside the private
        # stack page in address order so both runs must agree exactly.
        outside_stack_writes = []
        for address, size, _value in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            if not in_stack:
                outside_stack_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self._normalise(self.call_log),
            "fixtures": {
                "object": bytes(self.uc.mem_read(OBJECT_ADDR, OBJECT_SIZE)),
                "owner": bytes(self.uc.mem_read(OWNER_ADDR, OWNER_SIZE)),
                "extra": bytes(self.uc.mem_read(EXTRA_ADDR, EXTRA_SIZE)),
            },
            "outside_stack_writes": outside_stack_writes,
            "callback_present": bool(case.get("callback", True)),
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
    for key, value in orig["fixtures"].items():
        if value != cand["fixtures"][key]:
            problems.append(f"fixture {key} was modified differently")
    if orig["outside_stack_writes"] != cand["outside_stack_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['outside_stack_writes']} cand={cand['outside_stack_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "owner": True,
        "owner_param": 0x11223344,
        "callback": True,
        "callback_ctx": 0xCAFEBABE,
        "extra": True,
        "aux": 0x55667788,
        "key": 0x00001234,
        "key_handle": 0,
        "entries": [(0x100, 0), (0x101, 0), (0x102, 0), (0x103, 0)],
        # Per-call return sequences (short lists fall back to the default).
        "request_results": [],
        "resolve_results": [],
        "bind_results": [],
        "commit_results": [],
        "callback_results": [],
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- primary-key gating
    cases.append(base_case("baseline"))
    cases.append(base_case("key_handle cached", key_handle=0x5000))
    cases.append(base_case("key_handle 0xFFFFFFFF", key_handle=0xFFFFFFFF))
    for key in (0x00000000, 0x00000001, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFE,
                0xFFFFFFFF):
        cases.append(base_case(f"key 0x{key:08x}", key=key))
        cases.append(base_case(f"key 0x{key:08x} cached",
                               key=key, key_handle=0x70000001))
    cases.append(base_case("key -1 cached", key=0xFFFFFFFF, key_handle=1))

    # --- primary request: zero/non-zero x callback present/absent
    cases.append(base_case("primary request fails with callback",
                           request_results=[0]))
    cases.append(base_case("primary request fails without callback",
                           request_results=[0], callback=False))
    cases.append(base_case("primary request ok without callback",
                           callback=False))
    cases.append(base_case("primary request fails, callback, resolve 0",
                           request_results=[0], resolve_results=[0]))
    cases.append(base_case("primary request ok, resolve 0",
                           resolve_results=[0]))

    # --- per-entry request failures on each loop index, both callback states
    for index in range(ENTRY_COUNT):
        results = [1] * index + [0]
        cases.append(base_case(
            f"entry request fails at index {index}",
            request_results=results))
    for index in range(ENTRY_COUNT):
        results = [1] * (index + 1)
        cases.append(base_case(
            f"entry request fails at index {index}, no callback",
            request_results=results, callback=False))

    # --- pending vs cached handles and dead ids
    cases.append(base_case(
        "mixed handles",
        entries=[(0x100, 0x900), (0x101, 0), (0x102, 0x902), (0x103, 0)]))
    cases.append(base_case(
        "dead ids with pending handles",
        entries=[(-1, 0), (-1, 0), (-1, 0), (-1, 0)]))
    cases.append(base_case(
        "dead ids with stale handles",
        entries=[(-1, 0x900), (-1, 0x901), (-1, 0x902), (-1, 0x903)]))
    cases.append(base_case(
        "mixed dead ids",
        entries=[(0x100, 0), (-1, 0x901), (0x102, 0), (-1, 0)]))
    cases.append(base_case(
        "all cached",
        entries=[(0x100, 0x900), (0x101, 0x901), (0x102, 0x902),
                 (0x103, 0x903)]))
    cases.append(base_case(
        "all pending, no request",
        entries=[(0x100, 0), (0x101, 0), (0x102, 0), (0x103, 0)],
        request_results=[1, 1, 1, 1, 1], resolve_results=[0, 0, 0, 0, 0]))

    # --- bind return arms (-1 and 2 enter commit; 0/1/other continue)
    for value in (0xFFFFFFFF, 0x00000002, 0x00000000, 0x00000001,
                  0x00000003, 0x7FFFFFFF, 0x80000000):
        cases.append(base_case(
            f"bind returns 0x{value:08x}",
            bind_results=[value] * ENTRY_COUNT))
    for index in range(ENTRY_COUNT):
        values = [0] * ENTRY_COUNT
        values[index] = 0xFFFFFFFF
        cases.append(base_case(f"bind -1 at index {index}", bind_results=values))
        values = [0] * ENTRY_COUNT
        values[index] = 2
        cases.append(base_case(f"bind 2 at index {index}", bind_results=values))

    # --- commit outcome x callback presence
    for index in range(ENTRY_COUNT):
        values = [1] * ENTRY_COUNT
        values[index] = 0
        cases.append(base_case(
            f"commit fails at index {index}",
            bind_results=[0xFFFFFFFF] * ENTRY_COUNT,
            commit_results=values))
        cases.append(base_case(
            f"commit fails at index {index}, no callback",
            bind_results=[0xFFFFFFFF] * ENTRY_COUNT,
            commit_results=values, callback=False))
    cases.append(base_case(
        "commit retry then success",
        bind_results=[0xFFFFFFFF, 2, 2, 2, 2, 2, 2, 2],
        commit_results=[1, 1, 1, 1]))
    cases.append(base_case(
        "bind 2, commit fails immediately",
        bind_results=[2], commit_results=[0]))
    cases.append(base_case(
        "bind -1 at last index, commit ok",
        bind_results=[0, 0, 0, 0xFFFFFFFF], commit_results=[1]))

    # --- optional/absent owner pointers
    cases.append(base_case("extra null", extra=False))
    cases.append(base_case("extra null, bind -1",
                           extra=False, bind_results=[0xFFFFFFFF] * ENTRY_COUNT))
    cases.append(base_case("owner null", owner=False))
    cases.append(base_case("owner null, bind -1",
                           owner=False, bind_results=[0xFFFFFFFF] * ENTRY_COUNT))
    cases.append(base_case("owner null, entry request fails",
                           owner=False, request_results=[1, 0]))
    cases.append(base_case("owner and extra null, no callback",
                           owner=False, extra=False, callback=False))

    # --- parameter boundaries (all forwarded verbatim)
    for param in (0x00000000, 0x00000001, 0x7FFFFFFF, 0x80000000,
                  0xFFFFFFFF):
        cases.append(base_case(f"owner_param 0x{param:08x}",
                               owner_param=param))
        cases.append(base_case(f"aux 0x{param:08x}", aux=param))
        cases.append(base_case(f"context 0x{param:08x}", callback_ctx=param))

    # --- extreme ids/handles forwarded through the whole chain
    cases.append(base_case(
        "extreme entry values",
        entries=[(0x80000000, 0), (0x7FFFFFFF, 0x80000000),
                 (0x00000000, 0), (0xFFFFFFFE, 0)]))
    cases.append(base_case(
        "extreme entry values, bind -1",
        entries=[(0x80000000, 0), (0x7FFFFFFF, 0x80000000),
                 (0x00000000, 0), (0xFFFFFFFE, 0)],
        bind_results=[0xFFFFFFFF] * ENTRY_COUNT))

    # --- callback return values are propagated on callback exits
    for value in (0x00000000, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        cases.append(base_case(f"callback returns 0x{value:08x}",
                               callback_results=[value] * 8))

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = AA_C4Runner().run(orig_code, case)
        cand = AA_C4Runner().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(
            f"  [PASS] {case['name']}  ({len(orig['call_log'])} events, "
            f"r0=0x{orig['ret']:08x})"
        )
    return passed


def main() -> None:
    print("Testing ui_func_0037aac4 (0x0037aac4)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        f"(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("entry_request_mode", "kModeEntry = 4;", "kModeEntry = 1;"),
        ("first_bind_extra",
         "optional_owner_payload(obj->extra));",
         "optional_owner_payload(obj->owner));"),
        ("retry_bind_owner",
         "obj->aux, optional_owner_payload(obj->owner));",
         "obj->aux, optional_owner_payload(obj->extra));"),
        ("bind_commit_arm", "if (result == -1 || result == 2) {",
         "if (result == -1) {"),
        ("loop_bound", "i < kEntryCount; ++i", "i + 1 < kEntryCount; ++i"),
        ("success_callback_ids",
         "obj->callback(kCommandSuccess, &obj->key, obj->entries, bound, flags,",
         "obj->callback(kCommandSuccess, &obj->key, bound, bound, flags,"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = AA_C4Runner().run(orig_code, case)
            bad = AA_C4Runner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
