#!/usr/bin/env python3
"""Differential test for ui_func_0037dc24 (0x0037dc24) using Unicorn ARM.

Compiles src/engine/leaf_batch45_b.cpp, extracts the ui_func_0037dc24 body,
resolves its direct calls to deterministic stubs at the original addresses, and
runs the pinned original (extracted/exefs/code.bin) against the candidate in
separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log with every integer register argument (stack pointers
    normalised) and the descriptor words the allocator receives;
  * the implicit s0 float argument of func_0037fd70;
  * the self, owner, list-node, allocated-node and 0x00411xxx global images;
  * any emulated write outside the private stack and the fixture pages.

Coverage: both reuse/allocation decisions, the s27 == 0/!= 0 split, the
obj[0x90] == 4 teardown branch, the flag pre-update branch, allocation failure,
id-zero and id-matching list walks, the signed/unsigned 0x7F selector gates
(including 0x80..0xFF and s16 0x8000), both 0x37FD70 arms, the byte-lerp
bounds (elapsed < / == / > duration), signed b subtraction, s8 sign extension,
and a sweep of the fixed-point constant inputs that reaches negative scalars.
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
SOURCE = ROOT / "src/engine/leaf_batch45_b.cpp"
OUT_DIR = ROOT / "build/test_leaf_0037dc24"

FUNC_ADDR = 0x0037DC24
FUNC_SIZE = 800

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # 0x1311D8 .. 0x37FD70
GLOBAL_ADDR = 0x00411000
GLOBAL_SIZE = 0x00001000
SELF_ADDR = 0x00700000
SELF_SIZE = 0x00001000
OWNER_ADDR = 0x00710000
OWNER_SIZE = 0x00001000
NODE_ADDR = 0x00720000
NODE_SIZE = 0x00001000
ALLOC_ADDR = 0x00730000
ALLOC_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100
NODE_STRIDE = 0x200

# Original direct-call targets. Stubs live at the same addresses so the pinned
# original and the relocated candidate resolve to identical behaviour.
STUB_1311D8 = 0x001311D8
STUB_37F8E0 = 0x0037F8E0
STUB_235A4C = 0x00235A4C
STUB_235A08 = 0x00235A08
STUB_379EA0 = 0x00379EA0
STUB_379E28 = 0x00379E28
STUB_379E08 = 0x00379E08
STUB_37FD70 = 0x0037FD70
STUB_2C615C = 0x002C615C
STUB_2A2224 = 0x002A2224

STUB_NAMES = {
    STUB_1311D8: "func_001311d8",
    STUB_37F8E0: "func_0037f8e0",
    STUB_235A4C: "func_00235a4c",
    STUB_235A08: "func_00235a08",
    STUB_379EA0: "func_00379ea0",
    STUB_379E28: "func_00379e28",
    STUB_379E08: "func_00379e08",
    STUB_37FD70: "func_0037fd70",
    STUB_2C615C: "func_002c615c",
    STUB_2A2224: "func_002a2224",
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


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0037dc24" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"ui_func_0037dc24 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
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
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_b.o"
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
def build_global(case: dict) -> bytes:
    page = bytearray([0x11] * GLOBAL_SIZE)
    struct.pack_into("<I", page, 0x08, case.get("g08", 0xDEADBEEF))
    struct.pack_into("<I", page, 0x10, case.get("g10", 0x004119F8) & 0xFFFFFFFF)
    return bytes(page)


def build_self(case: dict) -> bytes:
    page = bytearray([0xA5] * SELF_SIZE)
    page[0x27] = case.get("s27", 0)
    page[0x41] = case.get("s41", 0x12)
    page[0x49] = case.get("s49", 0)
    page[0x4B] = case.get("s4b", 0)
    page[0x4D] = case.get("s4d", 0x33)
    struct.pack_into("<I", page, 0x50, case.get("s50", 0x12345678))
    struct.pack_into("<f", page, 0x68, case.get("s68", 12.5))
    page[0x85] = case.get("s85", 0x40)
    page[0x87] = case.get("s87", 0x00)
    page[0x89] = case.get("s89", 0x00)
    page[0x8A] = case.get("s8a", 0x10)
    page[0x8B] = case.get("s8b", 0x00)
    page[0x8C] = case.get("s8c", 0x00)
    page[0x8D] = case.get("s8d", 0x00)
    page[0x8E] = case.get("s8e", 0x00)
    page[0x8F] = case.get("s8f", 0x00)
    struct.pack_into("<H", page, 0x90, case.get("s90", 0x0000) & 0xFFFF)
    struct.pack_into("<I", page, 0xC0, OWNER_ADDR)
    struct.pack_into("<I", page, 0xC4, case.get("head", 0))
    return bytes(page)


def build_owner(case: dict) -> bytes:
    page = bytearray([0x77] * OWNER_SIZE)
    page[0x34] = case.get("own34", 0x21)
    page[0x35] = case.get("own35", 0x22)
    page[0x5C] = case.get("own5c", 0x23)
    page[0x75] = case.get("own75", 0x00)
    return bytes(page)


def build_nodes(case: dict) -> bytes:
    page = bytearray([0x66] * NODE_SIZE)
    for slot in range(NODE_SIZE // NODE_STRIDE):
        struct.pack_into("<I", page, slot * NODE_STRIDE + 0x138, 0)
    for index, chain in enumerate(case.get("chain", [])):
        base = index * NODE_STRIDE
        page[base + 0x90] = chain.get("slot", 0)
        page[base + 0x128] = chain.get("id", 0)
        nxt = chain.get("next", index + 1)
        pointer = 0 if nxt is None or nxt >= len(case.get("chain", [])) \
            else NODE_ADDR + nxt * NODE_STRIDE
        struct.pack_into("<I", page, base + 0x138, pointer)
        if "anim0" in chain:
            page[base + 0x110 + 0] = chain["anim0"]
            page[base + 0x110 + 1] = chain.get("anim1", 0)
            struct.pack_into("<H", page, base + 0x112, chain.get("anim2", 0))
            struct.pack_into("<H", page, base + 0x114, chain.get("anim4", 0))
        struct.pack_into("<I", page, base + 0x134, chain.get("w134", 0))
    # A standalone reused node (chain of one) is placed at node index 0 too.
    if "reuse" in case:
        node = case["reuse"]
        base = node.get("index", 0) * NODE_STRIDE
        page[base + 0x90] = node.get("slot", 0)
        page[base + 0x128] = node.get("id", 0)
        page[base + 0x110 + 0] = node.get("anim0", 0)
        page[base + 0x110 + 1] = node.get("anim1", 0)
        struct.pack_into("<H", page, base + 0x112, node.get("anim2", 0))
        struct.pack_into("<H", page, base + 0x114, node.get("anim4", 0))
        struct.pack_into("<I", page, base + 0x134, node.get("w134", 0))
    return bytes(page)


def build_alloc(case: dict) -> bytes:
    page = bytearray([0x5A] * ALLOC_SIZE)
    page[0x90] = case.get("alloc_slot", 0)
    page[0x128] = case.get("alloc_id", 0)
    page[0x110 + 0] = case.get("alloc_anim0", 0)
    page[0x110 + 1] = case.get("alloc_anim1", 0)
    struct.pack_into("<H", page, 0x112, case.get("alloc_anim2", 0))
    struct.pack_into("<H", page, 0x114, case.get("alloc_anim4", 0))
    struct.pack_into("<I", page, 0x134, case.get("alloc_w134", 0))
    return bytes(page)


def initial_head(case: dict) -> int:
    head = case.get("head", 0)
    if isinstance(head, str):
        raise AssertionError("head must be numeric")
    return head


def build_case_head(case: dict) -> int:
    if case.get("head_node", False):
        return NODE_ADDR
    return case.get("head", 0)


def read_word(uc, address: int) -> int:
    return struct.unpack("<I", uc.mem_read(address, 4))[0]


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(GLOBAL_ADDR, GLOBAL_SIZE)
        self.uc.mem_map(SELF_ADDR, SELF_SIZE)
        self.uc.mem_map(OWNER_ADDR, OWNER_SIZE)
        self.uc.mem_map(NODE_ADDR, NODE_SIZE)
        self.uc.mem_map(ALLOC_ADDR, ALLOC_SIZE)
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

    # ------------------------------------------------------------------ stubs
    @staticmethod
    def _is_stack(value: int) -> bool:
        return STACK_ADDR <= value < STACK_ADDR + STACK_SIZE

    def _log(self, address: int, *args) -> None:
        def norm(value):
            if isinstance(value, tuple):
                return tuple(norm(item) for item in value)
            if isinstance(value, int) and self._is_stack(value):
                return "<stack>"
            return value

        self.call_log.append((STUB_NAMES[address], norm(args)))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)

        if address == STUB_1311D8:
            self._log(address, r0)
        elif address == STUB_37F8E0:
            desc = struct.unpack("<8I", uc.mem_read(r2, 32))
            self._log(address, r0, r1, desc)
            if self.case.get("alloc_null", False):
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
            else:
                uc.reg_write(arm.UC_ARM_REG_R0, ALLOC_ADDR)
        elif address == STUB_235A4C:
            self._log(address, r0, r1)
        elif address == STUB_235A08:
            self._log(address, r0)
        elif address == STUB_379EA0:
            self._log(address, r0, r1)
        elif address == STUB_379E28:
            self._log(address, r0, r1)
        elif address == STUB_379E08:
            self._log(address, r0, r1)
        elif address == STUB_37FD70:
            s0 = uc.reg_read(arm.UC_ARM_REG_S0)
            self._log(address, r0, r1, r2, s0)
        elif address == STUB_2C615C:
            self._log(address, r0, r1)
            if "div" in self.case:
                result = self.case["div"]
            elif r1 != 0:
                result = (r0 // r1) & 0xFFFFFFFF
            else:
                result = 0xFFFFFFFF
            uc.reg_write(arm.UC_ARM_REG_R0, result)
        elif address == STUB_2A2224:
            self._log(address, r0, r1)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case
        head = build_case_head(case)

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(GLOBAL_ADDR, build_global(case))
        self.uc.mem_write(SELF_ADDR, build_self({**case, "head": head}))
        self.uc.mem_write(OWNER_ADDR, build_owner(case))
        self.uc.mem_write(NODE_ADDR, build_nodes(case))
        self.uc.mem_write(ALLOC_ADDR, build_alloc(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.uc.mem_write(ENTRY_SP, struct.pack(
            "<I", case.get("flag", 0) & 0xFFFFFFFF))
        self.writes = []

        # CPACR grants full access to CP10/11 and FPEXC.EN enables VFP.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case.get("b", 0) & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R2, case.get("c", 1) & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R3, case.get("sb", 0) & 0xFFFFFFFF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        allowed = (
            (STACK_ADDR, STACK_ADDR + STACK_SIZE),
            (SELF_ADDR, SELF_ADDR + SELF_SIZE),
            (NODE_ADDR, NODE_ADDR + NODE_SIZE),
            (ALLOC_ADDR, ALLOC_ADDR + ALLOC_SIZE),
        )
        unexpected_writes = []
        for address, size, _value in self.writes:
            if not any(lo <= address < hi for lo, hi in allowed):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "fixtures": {
                "global": bytes(self.uc.mem_read(GLOBAL_ADDR, GLOBAL_SIZE)),
                "self": bytes(self.uc.mem_read(SELF_ADDR, SELF_SIZE)),
                "owner": bytes(self.uc.mem_read(OWNER_ADDR, OWNER_SIZE)),
                "nodes": bytes(self.uc.mem_read(NODE_ADDR, NODE_SIZE)),
                "alloc": bytes(self.uc.mem_read(ALLOC_ADDR, ALLOC_SIZE)),
            },
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
    for key, value in orig["fixtures"].items():
        if value != cand["fixtures"][key]:
            problems.append(f"fixture {key} was modified differently")
    if orig["unexpected_writes"] != cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "flag": 0,
        "b": 0x0000_0010,
        "c": 1,
        "sb": 0x0000_0010,
    }
    case.update(overrides)
    return case


def chain(count: int, ids: list[int], slot: int = 0) -> list[dict]:
    return [{"id": ids[i] if i < len(ids) else 0, "slot": slot,
             "next": i + 1} for i in range(count)]


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- allocation and list insertion
    cases.append(base_case("alloc no list id 0"))
    cases.append(base_case("alloc list match middle", head_node=True,
                           chain=chain(3, [5, 7, 9]), alloc_id=7))
    cases.append(base_case("alloc list no match", head_node=True,
                           chain=chain(2, [5, 7]), alloc_id=4))
    cases.append(base_case("alloc list id zero skips walk", head_node=True,
                           chain=chain(2, [5, 7]), alloc_id=0))
    cases.append(base_case("alloc list single match", head_node=True,
                           chain=chain(1, [3]), alloc_id=3))
    cases.append(base_case("alloc fails", alloc_null=True))
    cases.append(base_case("alloc fails with list", alloc_null=True,
                           head_node=True, chain=chain(2, [5, 7]),
                           alloc_id=7))

    # --- s27 reuse / teardown / reallocation
    cases.append(base_case("s27 reuse node", s27=1, head_node=True,
                           reuse={"slot": 0, "id": 1, "w134": 0x11112222}))
    cases.append(base_case("s27 reuse node slot 4", s27=1, head_node=True,
                           reuse={"slot": 4, "id": 1}, alloc_id=1))
    cases.append(base_case("s27 head null", s27=1, head=0))
    cases.append(base_case("s27 head null slot ignored", s27=1, head=0,
                           alloc_id=2))

    # --- flag pre-update paths
    cases.append(base_case("flag 1 head node", flag=1, head_node=True,
                           reuse={"slot": 0, "id": 1}))
    cases.append(base_case("flag 1 head null", flag=1, head=0))
    cases.append(base_case("flag 2 head node", flag=2, head_node=True,
                           reuse={"slot": 9, "id": 2}))
    cases.append(base_case("flag -1 head null", flag=0xFFFFFFFF, head=0))
    cases.append(base_case("flag 1 s27 reuse", flag=1, s27=1, head_node=True,
                           reuse={"slot": 0, "id": 1}))
    cases.append(base_case("flag 1 s27 slot 4", flag=1, s27=1, head_node=True,
                           reuse={"slot": 4, "id": 1}, alloc_id=1))

    # --- selector gates: unsigned <= 0x7F on 0x8C..0x8F
    for offset in range(0x8C, 0x90):
        for value in (0x00, 0x01, 0x7E, 0x7F, 0x80, 0xFF):
            cases.append(base_case(
                f"selector {offset:02X}=0x{value:02X}",
                **{f"s{offset:02x}": value}))
    # --- signed <= 0x7F on the halfword at 0x90
    for value in (0x0000, 0x0001, 0x007F, 0x0080, 0x7FFF, 0x8000, 0xFFFF):
        cases.append(base_case(f"halfword 0x90=0x{value:04X}", s90=value))

    # --- fade source and slot step
    cases.append(base_case("s4b add positive", s4b=1, s8a=0x20, b=0x10, s68=3.0))
    cases.append(base_case("s4b add negative", s4b=1, s8a=0x00, b=0x01,
                           s68=3.0))
    cases.append(base_case("s4b add wraparound", s4b=1, s8a=0x00,
                           b=0xFFFFFFFF, s68=-2.5))
    cases.append(base_case("s4b off negative base", s4b=0, s68=-7.25))
    for step in (1, 2, 0x7F, 0x80, 0xFF):
        for base in (0.0, 0.5, -0.5, 100.0, -100.0):
            cases.append(base_case(f"step 0x{step:02X} base {base}",
                                   s8b=step, s68=base))
    cases.append(base_case("step 1 huge negative", s8b=1, s68=-1e6))

    # --- byte lerp at node+0x110
    lerp_pairs = [
        ("equal zero", 0, 0),
        ("less", 0, 5),
        ("equal nonzero", 5, 5),
        ("greater", 6, 5),
        ("max elapsed", 0xFFFF, 1),
        ("large duration", 1, 0xFFFF),
        ("full byte", 0xFFFF, 0xFFFF),
    ]
    for label, elapsed, duration in lerp_pairs:
        for s49 in (0, 1):
            cases.append(base_case(
                f"lerp {label} s49={s49}", s49=s49, s27=1, head_node=True,
                reuse={"slot": 0, "id": 1, "anim0": 0x10, "anim1": 0xFE,
                       "anim2": duration, "anim4": elapsed}))
    cases.append(base_case("lerp division override", s27=1, head_node=True,
                           reuse={"slot": 0, "id": 1, "anim0": 0xFF,
                                  "anim1": 0x00, "anim2": 9, "anim4": 4},
                           div=0xFFFFFFFF))
    cases.append(base_case("lerp division max delta", s27=1, head_node=True,
                           reuse={"slot": 0, "id": 1, "anim0": 0x00,
                                  "anim1": 0xFF, "anim2": 3, "anim4": 2}))

    # --- sign extension and byte-width copies
    for value in (0x00, 0x7F, 0x80, 0xFF):
        cases.append(base_case(f"s87 sign 0x{value:02X}", s87=value))
    for value in (0x00, 0x7F, 0x80, 0xFF):
        cases.append(base_case(f"s41 sign 0x{value:02X}", s41=value,
                               head_node=True,
                               reuse={"slot": 0, "id": 1,
                                      "w134": 0xCAFEBABE}))
    cases.append(base_case("f14 overflow", s89=0xFF, own75=0xFF))
    cases.append(base_case("owner bytes", own34=0x00, own35=0xFF, own5c=0x80,
                           head_node=True, reuse={"slot": 0, "id": 1}))
    cases.append(base_case("b full width", b=0x89ABCDEF))
    cases.append(base_case("b zero", b=0))
    cases.append(base_case("sb full width", sb=0xDEADBEEF, flag=1,
                           head_node=True, reuse={"slot": 0, "id": 1}))
    cases.append(base_case("s50 word", s50=0xFFFFFFFF, head_node=True,
                           reuse={"slot": 0, "id": 1}))
    cases.append(base_case("global field", g10=0xDEADBEEF, head_node=True,
                           reuse={"slot": 0, "id": 1}))
    cases.append(base_case("global field zero", g10=0, head_node=True,
                           reuse={"slot": 0, "id": 1}))

    # --- fixed-point scalar sweep (reaches negative / wrapping scalars)
    for s85 in (0x00, 0x01, 0x7F, 0x80, 0xFF):
        for c in (1, 2, 3, 0x100, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF,
                  0xFFFF0000, 0x00010000, 12345):
            cases.append(base_case(
                f"scalar s85=0x{s85:02X} c=0x{c:08X}",
                s85=s85, c=c, head_node=True,
                reuse={"slot": 0, "id": 1}))

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
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
    print("Testing ui_func_0037dc24 (0x0037dc24)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B.")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nCoverage sanity check:")
    seen = set()
    for case in cases:
        result = Runner().run(orig_code, case)
        for name, _args in result["call_log"]:
            seen.add(name)
    missing = sorted(set(STUB_NAMES.values()) - seen)
    if missing:
        raise SystemExit(f"coverage gap: {missing}")
    print(f"  all {len(STUB_NAMES)} helpers exercised")

    print("\nNegative controls:")
    for name, old, new in (
        ("desc_flag_word", "desc.f0C = (flag != 0u) ? 0xFFFFFFFFu : sb;",
         "desc.f0C = (flag != 0u) ? 0xFFFFFFFEu : sb;"),
        ("selector_8c_bound", "if (sel_8C <= 0x7Fu) {",
         "if (sel_8C < 0x7Fu) {"),
        ("slot_step_scale", "const u32 step = static_cast<u32>(converted >> 5) * 5u;",
         "const u32 step = static_cast<u32>(converted >> 5) * 4u;"),
        ("fade_target", "const u8 target = (self[0x49] != 0u) ? 0x00u : 0xFFu;",
         "const u8 target = (self[0x49] != 0u) ? 0xFFu : 0x00u;"),
        ("slot_teardown_compare", "} else if (obj[0x90] == 4u) {",
         "} else if (obj[0x90] == 5u) {"),
        ("fixed_point_constant",
         "static_cast<s64>(static_cast<s32>(mixed)) * 0x81020409LL;",
         "static_cast<s64>(static_cast<s32>(mixed)) * 0x81020408LL;"),
        ("lerp_bound", "if (elapsed >= duration) {",
         "if (elapsed > duration) {"),
        ("signed_s41", "static_cast<s32>(static_cast<s8>(self[0x41])));",
         "static_cast<s32>(self[0x41]));"),
    ):
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
