#!/usr/bin/env python3
"""Differential test for camp_func_0035532c (0x0035532c) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the camp_func_0035532c body,
resolves its four direct calls to deterministic stubs at their original
addresses, and runs the pinned 640-byte original against the candidate in
separate Unicorn machines with identical fixtures.

The routine is a service-request submit:
  * 0x002adb84 submits command 3 with the {&buffer, 1} block and returns the
    two response words (or a negative SVC status);
  * 0x0035654c (request vtable slot 0) builds the operation object from the
    {2, &{2, "icon", 0}, 0x0c} descriptor;
  * the operation's vtable slot 0 (0x00356454) starts it with the caller's
    argument plus the stack constant 0x36c0;
  * the operation's vtable slot 0x2c (0x003563e4) releases it;
  * 0x00239f84 reads the request handle and 0x002adb54 sends the release
    command with the two response words.

Compared outputs:
  * return r0, continuation PC, final SP and every callee-saved r4-r11;
  * the ordered call log: every used register argument, the architected stack
    words, the submit block {self, 1}, the descriptor and "icon" block, the
    request object words and the getter result;
  * the full 0x20000-byte service page and 0x10000-byte fake operation page;
  * every emulated write outside the private stack and those fixture pages.

Coverage: negative submit statuses; create failure with zero, one and both
response words set (signed boundaries included); the getter returning a
sentinel and mutating the response words; start success at 0 and positive
maxima and start failure at signed minima; a session handle changed by
0x002adb84 between the two loads; argument and handle boundaries.  Negative
controls mutate each forwarded constant and two data-flow steps.

The original leaves both request response words undefined when 0x002adb84
fails and still tests them in the inlined destructor.  This reconstruction
zero-initializes them, and every case runs with a zero-filled stack so the
original's uninitialized read observes the same zero (see the record).
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
OUT_DIR = ROOT / "build/test_leaf_0035532c"

FUNC_ADDR = 0x0035532C
FUNC_SIZE = 640

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00210000  # covers 0x35532c, the four stubs and the fake slots
SERVICE_ADDR = 0x00440000
SERVICE_SIZE = 0x00020000
FAKE_ADDR = 0x00750000
FAKE_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Original direct-call targets.  The candidate's R_ARM_CALL relocations are
# patched to these addresses, so both binaries use the same hooks.
STUB_SUBMIT = 0x002ADB84
STUB_CREATE = 0x0035654C
STUB_GET_HANDLE = 0x00239F84
STUB_RELEASE = 0x002ADB54

STUB_NAMES = {
    STUB_SUBMIT: "func_002adb84",
    STUB_CREATE: "func_0035654c",
    STUB_GET_HANDLE: "nn_sdk_func_00239f84",
    STUB_RELEASE: "func_002adb54",
}

# Stack-word counts for the architected arguments of every stub.
STACK_ARGS = {
    STUB_SUBMIT: 2,       # submit buffer pointer, count
    STUB_CREATE: 0,
    STUB_GET_HANDLE: 0,
    STUB_RELEASE: 0,
}

# Operation-vtable slots invoked indirectly.  They live in the free tail of the
# mapped code page.
STUB_OPERATION_START = 0x00380000
STUB_OPERATION_RELEASE = 0x00380010
INDIRECT_NAMES = {
    STUB_OPERATION_START: "operation_start",
    STUB_OPERATION_RELEASE: "operation_release",
}

SERVICE_HANDLE_ADDR = 0x0044E650 + 0x10  # 0x0044E660
FAKE_OBJECT = FAKE_ADDR + 0x0100
FAKE_VTABLE = FAKE_ADDR + 0x0200
FAKE_OBJECT_HANDLE = 0x5A5A5A5A

# Layout of the request object (0x004209F8 vtable) and the operation object
# (0x00420998 vtable), both taken from the ARM disassembly.
REQUEST_VTABLE = 0x004209F8
OPERATION_VTABLE = 0x00420998
OPERATION_START_SLOT = 0x00
OPERATION_RELEASE_SLOT = 0x2C
REQUEST_HANDLE_OFFSET = 0x04
REQUEST_RESPONSE0_OFFSET = 0x08
REQUEST_RESPONSE1_OFFSET = 0x0C

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


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0035532c" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"camp_func_0035532c not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type != 28:  # only R_ARM_CALL is expected
            raise RuntimeError(
                f"unhandled relocation {rel.relocation_type} {rel.symbol_name}"
            )
        target = None
        for address, name in STUB_NAMES.items():
            if rel.symbol_name == name:
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        cond = original & 0xFF000000
        struct.pack_into("<I", code, rel.offset, cond | (displacement & 0x00FFFFFF))
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
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {count} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    res = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


def read_c_string(uc, address: int, limit: int = 32) -> bytes:
    out = bytearray()
    for index in range(limit):
        byte = uc.mem_read(address + index, 1)[0]
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(SERVICE_ADDR, SERVICE_SIZE)
        self.uc.mem_map(FAKE_ADDR, FAKE_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_direct_stub,
                begin=address, end=address,
            )
        for address in INDIRECT_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_indirect_stub,
                begin=address, end=address,
            )

        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)
        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    @staticmethod
    def _norm(value: int):
        if STACK_ADDR <= value < STACK_ADDR + STACK_SIZE:
            return "<stack>"
        return value

    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        raw = self.uc.mem_read(sp, 4 * count)
        return struct.unpack(f"<{count}I", raw)

    def _request_words(self, address: int) -> tuple:
        return struct.unpack("<4I", self.uc.mem_read(address, 16))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _log(self, name: str, *args) -> None:
        self.call_log.append((name, args))

    def _on_direct_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        stack = self._stack_words(STACK_ARGS[address])

        if address == STUB_SUBMIT:
            handle = struct.unpack("<I", uc.mem_read(r0, 4))[0]
            block = struct.unpack(
                "<II", uc.mem_read(stack[0], 8)
            )
            self._log(
                "submit", handle, self._norm(r1), r2, r3,
                self._norm(stack[0]), stack[1],
                self._norm(block[0]), block[1],
            )
            if self.case.get("submit_mutates_session"):
                uc.mem_write(
                    SERVICE_HANDLE_ADDR,
                    struct.pack("<I", self.case["session_after_submit"]),
                )
            if self.case.get("submit_ok", True):
                uc.mem_write(
                    r1,
                    struct.pack("<II", *self.case["response"]),
                )
                uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("submit_status", 3))
            else:
                uc.reg_write(
                    arm.UC_ARM_REG_R0,
                    self.case["submit_status"] & 0xFFFFFFFF,
                )

        elif address == STUB_CREATE:
            request = self._request_words(r0)
            desc = struct.unpack("<3I", uc.mem_read(r2, 12))
            icon = struct.unpack("<3I", uc.mem_read(desc[1], 12))
            self._log(
                "create", self._norm(r0), self._norm(r1), self._norm(r2), r3,
                request[0], request[1], request[2], request[3],
                desc[0], self._norm(desc[1]), desc[2],
                icon[0], icon[1], icon[2],
            )
            if self.case.get("create_ok", True):
                uc.mem_write(r1, struct.pack("<I", FAKE_OBJECT))
                uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("create_status", 0))
            else:
                uc.reg_write(
                    arm.UC_ARM_REG_R0,
                    self.case["create_status"] & 0xFFFFFFFF,
                )

        elif address == STUB_GET_HANDLE:
            request = self._request_words(r0)
            self._log("get_handle", self._norm(r0), *request)
            if self.case.get("getter_mutates"):
                uc.mem_write(
                    r0 + REQUEST_RESPONSE0_OFFSET,
                    struct.pack(
                        "<II",
                        self.case["mutated_response"][0],
                        self.case["mutated_response"][1],
                    ),
                )
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["getter_result"])

        elif address == STUB_RELEASE:
            handle = struct.unpack("<I", uc.mem_read(r0, 4))[0]
            # r1 (the second argument) is not read by the callee; it is
            # deliberately omitted from the log.
            self._log("release", handle, r2, r3)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("release_result", 0))

        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected direct stub 0x{address:08x}")

    def _on_indirect_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_OPERATION_START:
            stack = self._stack_words(2)
            self._log(
                "operation_start", r0, self._norm(r1), r2, r3,
                stack[0], stack[1],
            )
            if self.case.get("start_writes_output"):
                uc.mem_write(r1, struct.pack("<I", 0xCAFEF00D))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("start_status", 0))
        elif address == STUB_OPERATION_RELEASE:
            self._log("operation_release", r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("release_return", 0))
        else:  # pragma: no cover
            raise AssertionError(f"unexpected indirect stub 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)

        service = bytearray([0xA5] * SERVICE_SIZE)
        struct.pack_into("<I", service, SERVICE_HANDLE_ADDR - SERVICE_ADDR,
                         case.get("session", 0x0000CAFE))
        self.uc.mem_write(SERVICE_ADDR, bytes(service))

        fake = bytearray([0xA5] * FAKE_SIZE)
        struct.pack_into("<I", fake, FAKE_OBJECT - FAKE_ADDR, FAKE_VTABLE)
        struct.pack_into("<I", fake, FAKE_OBJECT + 4 - FAKE_ADDR,
                         FAKE_OBJECT_HANDLE)
        struct.pack_into("<I", fake, FAKE_VTABLE - FAKE_ADDR,
                         STUB_OPERATION_START)
        struct.pack_into("<I", fake,
                         FAKE_VTABLE + OPERATION_RELEASE_SLOT - FAKE_ADDR,
                         STUB_OPERATION_RELEASE)
        self.uc.mem_write(FAKE_ADDR, bytes(fake))

        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0,
                          case.get("argument", 0x12345678) & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
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
            in_service = SERVICE_ADDR <= address < SERVICE_ADDR + SERVICE_SIZE
            in_fake = FAKE_ADDR <= address < FAKE_ADDR + FAKE_SIZE
            if not (in_stack or in_service or in_fake):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "service": bytes(self.uc.mem_read(SERVICE_ADDR, SERVICE_SIZE)),
            "fake": bytes(self.uc.mem_read(FAKE_ADDR, FAKE_SIZE)),
            "unexpected_writes": unexpected_writes,
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
    for key in ("service", "fake"):
        if orig[key] != cand[key]:
            first = next(
                (i for i, (a, b) in enumerate(zip(orig[key], cand[key])) if a != b),
                None,
            )
            problems.append(f"{key} page differs at offset {first!r}")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "argument": 0x12345678,
        "session": 0x0000CAFE,
        "submit_ok": True,
        "submit_status": 3,
        "response": (0x00000001, 0x00000002),
        "create_ok": True,
        "create_status": 0,
        "getter_result": None,
        "release_result": 0,
        "start_status": 0,
        "release_return": 0,
    }
    case.update(overrides)
    if case["getter_result"] is None:
        # The real getter returns request->handle, i.e. the session value read
        # after 0x002adb84 returned.
        case["getter_result"] = (
            case.get("session_after_submit")
            if case.get("submit_mutates_session")
            else case["session"]
        )
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- 0x002adb84 failure: no create, no release command.
    for status in (0xFFFFFFFF, 0x80000000, 0xFFFFFF00, 0x80000001):
        cases.append(
            base_case(f"submit fails 0x{status:08x}", submit_ok=False,
                      submit_status=status, session=0x0000CAFE)
        )
    cases.append(
        base_case("submit fails with zero session", submit_ok=False,
                  submit_status=0x80000000, session=0)
    )

    # --- create failure: response-word OR gate and the release command.
    for status in (0xFFFFFFFF, 0x80000000, 0xDEADBEEF):
        cases.append(
            base_case(f"create fails 0x{status:08x}, response 0/0",
                      create_ok=False, create_status=status,
                      response=(0, 0))
        )
    cases.append(
        base_case("create fails, response 1/2", create_ok=False,
                  create_status=0xFFFFFFFF, response=(1, 2))
    )
    for response in (
        (0x80000000, 0),
        (0, 0x80000000),
        (0, 0xFFFFFFFF),
        (0xFFFFFFFF, 0),
        (0xFFFFFFFF, 0xFFFFFFFF),
        (0x7FFFFFFF, 0x80000000),
        (0xFFFFFFFF, 0x7FFFFFFF),
    ):
        cases.append(
            base_case(f"create fails, response {response[0]:08x}/"
                      f"{response[1]:08x}",
                      create_ok=False, create_status=0xFFFFFFFE,
                      response=response)
        )

    # --- start success: 0x00356454 returns >= 0, 0x003563e4 is released.
    for status in (0, 1, 0x7FFFFFFF, 0x40000000):
        cases.append(
            base_case(f"start succeeds 0x{status:08x}", start_status=status)
        )
    cases.append(
        base_case("start succeeds, response 0/0", start_status=0,
                  response=(0, 0))
    )

    # --- start failure: its negative status is returned unchanged.
    for status in (0x80000000, 0xFFFFFFFF, 0xC0000000, 0x80000001, 0xDEADBEEF):
        cases.append(
            base_case(f"start fails 0x{status:08x}", start_status=status)
        )
    cases.append(
        base_case("start fails, response 0/80000000", start_status=0x80000000,
                  response=(0, 0x80000000))
    )

    # --- getter data flow: distinct result, and mutation before the reload.
    cases.append(
        base_case("getter returns sentinel", start_status=0,
                  response=(3, 4), getter_result=0xDEADBEEF)
    )
    cases.append(
        base_case("getter mutates response", start_status=0,
                  response=(1, 2),
                  getter_mutates=True,
                  mutated_response=(0x11111111, 0x22222222))
    )
    cases.append(
        base_case("getter mutates response on create failure",
                  create_ok=False, create_status=0xFFFFFFFF,
                  response=(1, 2),
                  getter_mutates=True,
                  mutated_response=(0, 0x80000000))
    )
    cases.append(
        base_case("getter mutates response to zero", start_status=0xFFFFFFFF,
                  response=(5, 6),
                  getter_mutates=True,
                  mutated_response=(0, 0))
    )

    # --- session handle: second load after 0x002adb84 vs. first load.
    cases.append(
        base_case("session changes during submit", start_status=0,
                  session=0x0000CAFE,
                  submit_mutates_session=True,
                  session_after_submit=0x0000BEEF)
    )
    cases.append(
        base_case("session changes to zero during submit",
                  create_ok=False, create_status=0xFFFFFFFF,
                  session=0xFFFFFFFF,
                  submit_mutates_session=True,
                  session_after_submit=0)
    )
    cases.append(
        base_case("session changes during submit, start fails",
                  start_status=0x80000000,
                  session=0x80000000,
                  submit_mutates_session=True,
                  session_after_submit=0x7FFFFFFF)
    )

    # --- caller argument / handle boundaries.
    for argument, session in (
        (0x00000000, 0x00000000),
        (0xFFFFFFFF, 0xFFFFFFFF),
        (0x80000000, 0x80000000),
        (0x7FFFFFFF, 0x7FFFFFFF),
        (0x0000FFFF, 0x00010000),
    ):
        cases.append(
            base_case(f"argument 0x{argument:08x} session 0x{session:08x}",
                      argument=argument, session=session)
        )

    # --- start writes its output word (never read back).
    cases.append(
        base_case("start writes output word", start_status=0,
                  start_writes_output=True)
    )

    # --- boundary return values of the release helper (ignored).
    cases.append(
        base_case("release helper returns negative", start_status=0,
                  release_return=0x80000000, release_result=0xFFFFFFFF)
    )

    return cases


def run_case_set(orig_code: bytes, cand_code: bytes, cases) -> int:
    passed = 0
    for case in cases:
        orig = Runner().run(orig_code, case)
        cand = Runner().run(cand_code, case)
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
    print("Testing camp_func_0035532c (0x0035532c)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(direct calls relocated)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    mutants = (
        ("submit_command",
         "constexpr u32 kSubmitCommand = 3;",
         "constexpr u32 kSubmitCommand = 4;"),
        ("submit_argument",
         "constexpr u32 kSubmitArgument = 1;",
         "constexpr u32 kSubmitArgument = 2;"),
        ("submit_buffer_count",
         "constexpr u32 kSubmitBufferCount = 1;",
         "constexpr u32 kSubmitBufferCount = 2;"),
        ("descriptor_type",
         "constexpr u32 kDescriptorType = 2;",
         "constexpr u32 kDescriptorType = 3;"),
        ("icon_tag",
         "constexpr u32 kIconTag = 0x6e6f6369;  // \"icon\"",
         "constexpr u32 kIconTag = 0x6e6f6368;  // \"icon\""),
        ("descriptor_size",
         "constexpr u32 kDescriptorSize = 0x0c;",
         "constexpr u32 kDescriptorSize = 0x10;"),
        ("create_flag",
         "constexpr u32 kCreateFlag = 1;",
         "constexpr u32 kCreateFlag = 0;"),
        ("start_stack_argument",
         "constexpr u32 kStartStackArgument = 0x36c0;",
         "constexpr u32 kStartStackArgument = 0x36c1;"),
        ("response_swap",
         "    request.response0 = response[0];",
         "    request.response0 = response[1];"),
        ("cached_session",
         "    // The original reloads the global handle after the command succeeds.\n"
         "    request.handle = *reinterpret_cast<u32*>(kServiceStateAddress +\n"
         "                                             kSessionHandleOffset);",
         "    // The original reloads the global handle after the command succeeds.\n"
         "    request.handle = handle;"),
        ("success_return",
         "    release_request_cached(&request);\n"
         "    return 0;",
         "    release_request_cached(&request);\n"
         "    return start_status;"),
        ("success_reload",
         "    release_request_cached(&request);\n"
         "    return 0;",
         "    release_request_reloaded(&request);\n"
         "    return 0;"),
        ("missing_release",
         "    operation->vtable->release(operation);",
         "    (void)operation;"),
        ("release_second_word",
         "        func_002adb54(&handle, 0, request->response0, request->response1);",
         "        func_002adb54(&handle, 0, request->response0, request->response0);"),
    )
    for name, old, new in mutants:
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, case)
            bad = Runner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
