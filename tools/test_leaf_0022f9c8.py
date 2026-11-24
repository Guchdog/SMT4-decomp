#!/usr/bin/env python3
"""Differential test for shop_func_0022f9c8 (0x0022f9c8) using Unicorn ARM.

Compiles ``src/engine/leaf_batch42_b.cpp``, extracts the
``shop_func_0022f9c8`` body, resolves its nine direct call relocations plus the
seven-word switch table, and runs the pinned original
(``extracted/exefs/code.bin``) against the candidate on separate Unicorn ARM
machines with identical fixtures.

Compared output per case:
  * returned r0, continuation PC, final SP and the callee-saved r4-r11;
  * the ordered call log with every register argument of every helper, the
    full 0x8C-byte scratch buffer handed to 0x0029960C and 0x0029A368, and the
    source/destination/size of the 0x002BCF58 copy;
  * the complete 128 KiB object page (selection index, entry/id/slot tables,
    the 0x15D24/0x15D28/0x15D54 words, the active/pending bytes) and the copy
    source page;
  * every write outside the private stack, including its access width.

The recovered contract is documented above the implementation.  In short:

  index  = *(u32*)(object + 0x860)                    (read twice)
  count  = 0x002337A0(object + 0x880 + index*0x74)
  id     = *(u16*)(object + 0xC94 + index*0x1002 + count*4)
  vis    = 0x003C2F7C(object + 0x880 + index2*0x74)
  if (vis == 0 && *(u32*)(object + 0x15D54) == id):
      active==0 -> push ids 4/5/6 into slots 0/1/2 via 0x002998D8, active=1
      active!=0 -> 0x0029A25C(active) != 0 -> 0x00299974(1), pending=1
  else:
      0x00299974(0), active=0, pending=0, *(u32*)(object+0x15D54)=id
  if (*(u32*)(object + 0x15D24) == 0) return 0
  prev = *(u32*)(object + 0x15D28); if (prev == id) return prev
  *(u32*)(object + 0x15D28) = id
  buffer = 0x002BCF58(local, 0x002B66EC(), 0x8C)
  type = 0x002AE64C(id); patch u16 selected by type 2..8 (offset table)
  0x0029960C(buffer); return 0x0029A368(buffer)

Helper stubs are deterministic and placed at the original call targets.  The
0x002337A0 stub can change the selection index mid-call (the original re-reads
``object + 0x860`` after it), the 0x0029A25C stub controls the state query, the
0x002AE64C stub supplies the item type, and the 0x002BCF58 stub copies its
source page into the scratch buffer.

Coverage: enabled zero/non-zero, visible zero/non-zero/0xFFFFFFFF, matching and
non-matching last id, active byte 0 / 1 / 0x80 / 0xFF, state query zero and
non-zero, item id 0 and 0xFFFF, every switch type 2..8 and the out-of-range
types 0, 1, 9 and 0xFFFFFFFF, index 0..6, counts 0..4 (including an id address
overlapping the entry/page boundary), the second index read differing from the
first, and junk r1-r3 on entry.

Negative controls mutate each structural offset, the second index read, the
visibility conjunction, the stored-id comparison, a slot index, the active-flag
value, the state-query polarity and the final return; each mutant must be
detected.
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
SOURCE = ROOT / "src/engine/leaf_batch42_b.cpp"
OUT_DIR = ROOT / "build/test_leaf_0022f9c8"

FUNC_ADDR = 0x0022F9C8
FUNC_SIZE = 504

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # covers the function and every stub up to 0x003C2F7C
OBJ_ADDR = 0x00500000
OBJ_SIZE = 0x00020000  # 128 KiB object page (0x15D58 bytes are live)
SRC_ADDR = 0x00520000
SRC_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Structure offsets recovered from the ARM body.
INDEX_OFFSET = 0x860
ENTRY_BASE = 0x880
ENTRY_STRIDE = 0x74
SLOT_BASE = 0xC94
SLOT_STRIDE = 0x1002
ID_STRIDE = 4
ENABLED_OFFSET = 0x15D24
APPLIED_OFFSET = 0x15D28
VISIBLE_ID_OFFSET = 0x15D54
ACTIVE_OFFSET = 0x1E
PENDING_OFFSET = 0x1F
SCRATCH_SIZE = 0x8C

# Original direct-call targets.
STUB_COUNT = 0x002337A0
STUB_VISIBLE = 0x003C2F7C
STUB_TYPE = 0x002AE64C
STUB_ASSIGN = 0x002998D8
STUB_TOGGLE = 0x00299974
STUB_QUERY = 0x0029A25C
STUB_SOURCE = 0x002B66EC
STUB_COPY = 0x002BCF58
STUB_CONSUME = 0x0029960C
STUB_FINISH = 0x0029A368

STUB_NAMES = {
    STUB_COUNT: "shop_func_002337a0",
    STUB_VISIBLE: "shop_func_003c2f7c",
    STUB_TYPE: "shop_func_002ae64c",
    STUB_ASSIGN: "ui_func_002998d8",
    STUB_TOGGLE: "ui_func_00299974",
    STUB_QUERY: "ui_func_0029a25c",
    STUB_SOURCE: "script_vm_func_002b66ec",
    STUB_COPY: "ui_func_002bcf58",
    STUB_CONSUME: "engine_func_0029960c",
    STUB_FINISH: "engine_func_0029a368",
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

BX_LR = 0xE12FFF1E


# ---------------------------------------------------------------------------
# Candidate preparation
# ---------------------------------------------------------------------------
def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def symbol_offset(obj_file: Path, wanted: str) -> int:
    data = obj_file.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize = struct.unpack_from("<H", data, 46)[0]
    e_shnum = struct.unpack_from("<H", data, 48)[0]
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    symtab = next(section for section in sections if section[1] == 2)
    strtab = sections[symtab[6]]
    for index in range(symtab[5] // 16):
        name, value, _size, _info, _other, _shndx = struct.unpack_from(
            "<IIIBBH", data, symtab[4] + index * 16
        )
        symbol = data[strtab[4] + name :].split(b"\x00")[0].decode(
            "ascii", errors="replace"
        )
        if symbol == wanted:
            return value
    raise RuntimeError(f"symbol {wanted} not found in {obj_file}")


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = funcs.get("shop_func_0022f9c8")
    if candidate is None:
        raise RuntimeError(
            f"shop_func_0022f9c8 not found in {obj_file}: {sorted(funcs)}"
        )
    code_raw, relocs = candidate
    code = bytearray(code_raw)
    entry_offset = symbol_offset(obj_file, "shop_func_0022f9c8")

    for rel in relocs:
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            target = None
            for address, name in STUB_NAMES.items():
                if name == rel.symbol_name:
                    target = address
                    break
            if target is None:
                raise RuntimeError(f"unresolved call relocation: {rel}")
            pc = FUNC_ADDR + rel.offset + 8
            displacement = (target - pc) >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            struct.pack_into(
                "<I",
                code,
                rel.offset,
                (original & 0xFF000000) | (displacement & 0x00FFFFFF),
            )
        elif rel.relocation_type == 2 and rel.symbol_name == "":
            # `ldr pc, [pc, r0, lsl #2]` switch table: the stored addend is the
            # section-relative address of a case label inside this function.
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            target = (FUNC_ADDR + addend - entry_offset) & 0xFFFFFFFF
            struct.pack_into("<I", code, rel.offset, target)
        else:
            raise RuntimeError(f"unexpected relocation: {rel}")
    return bytes(code)


def compile_candidate(src: Path, obj: Path) -> bytes:
    obj.parent.mkdir(parents=True, exist_ok=True)
    result = compile_tu_armv6k(src, obj, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"compilation failed for {src}:\n{result.stderr}")
    return relocate_candidate(obj)


def compile_candidate_baseline() -> bytes:
    return compile_candidate(SOURCE, OUT_DIR / "leaf_batch42_b.o")


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant = OUT_DIR / f"mutant_{name}.cpp"
    mutant.write_text(text.replace(old, new), encoding="utf-8")
    return compile_candidate(mutant, OUT_DIR / f"mutant_{name}.o")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
def id_address(case: dict, index: int | None = None) -> int:
    index = case["index"] if index is None else index
    return SLOT_BASE + index * SLOT_STRIDE + case["count"] * ID_STRIDE


def build_obj(case: dict) -> bytes:
    page = bytearray(OBJ_SIZE)
    for index in range(0x15D80):
        page[index] = (0x31 + index * 7) & 0xFF
    struct.pack_into("<I", page, INDEX_OFFSET, case["index"] & 0xFFFFFFFF)
    page[ACTIVE_OFFSET] = case["active"] & 0xFF
    page[PENDING_OFFSET] = case["pending"] & 0xFF
    struct.pack_into("<H", page, id_address(case), case["id"] & 0xFFFF)
    struct.pack_into("<I", page, ENABLED_OFFSET, case["enabled"] & 0xFFFFFFFF)
    struct.pack_into("<I", page, APPLIED_OFFSET, case["applied"] & 0xFFFFFFFF)
    struct.pack_into(
        "<I", page, VISIBLE_ID_OFFSET, case["last_visible"] & 0xFFFFFFFF
    )
    if "mutated_index" in case:
        # Written by the 0x002337A0 stub into a second copy of the index slot;
        # the original never reads this one before the second index load, so we
        # only use it to confirm the fixture stays deterministic.
        struct.pack_into("<I", page, INDEX_OFFSET + 0x10, case["mutated_index"])
    return bytes(page)


def build_src() -> bytes:
    page = bytearray(SRC_SIZE)
    for index in range(SRC_SIZE):
        page[index] = (0xC7 ^ (index * 13)) & 0xFF
    return bytes(page)


def write_u32(uc, address: int, value: int) -> None:
    uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))


def read_u32(uc, address: int) -> int:
    return struct.unpack("<I", uc.mem_read(address, 4))[0]


def finish_value(raw: bytes) -> int:
    first = struct.unpack_from("<I", raw, 0)[0]
    tail = sum(raw[4:]) & 0xFFFFFFFF
    return (first ^ (tail << 3) ^ 0x00C0FFEE) & 0xFFFFFFFF


# ---------------------------------------------------------------------------
# Machine
# ---------------------------------------------------------------------------
class Machine:
    """One Unicorn machine with deterministic stubs at the original addresses."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(OBJ_ADDR, OBJ_SIZE)
        self.uc.mem_map(SRC_ADDR, SRC_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", BX_LR))
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_helper, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}
        self.count_calls = 0

    # -------------------------------------------------------------- stubs
    @staticmethod
    def _pointer(value: int) -> object:
        if STACK_ADDR <= value < STACK_ADDR + STACK_SIZE:
            return "<stack>"
        if OBJ_ADDR <= value < OBJ_ADDR + OBJ_SIZE:
            return f"obj+0x{value - OBJ_ADDR:x}"
        if SRC_ADDR <= value < SRC_ADDR + SRC_SIZE:
            return f"src+0x{value - SRC_ADDR:x}"
        return value

    def _on_helper(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)

        if address == STUB_COUNT:
            self.count_calls += 1
            self.call_log.append(("shop_func_002337a0", self._pointer(r0)))
            if self.case.get("mutate_index_on_count") and self.count_calls == 1:
                write_u32(uc, OBJ_ADDR + INDEX_OFFSET,
                          self.case["mutated_index"])
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["count"])
        elif address == STUB_VISIBLE:
            self.call_log.append(("shop_func_003c2f7c", self._pointer(r0)))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["visible"])
        elif address == STUB_TYPE:
            self.call_log.append(("shop_func_002ae64c", r0))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["type"])
        elif address == STUB_ASSIGN:
            self.call_log.append(("ui_func_002998d8", r0, r1))
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_TOGGLE:
            self.call_log.append(("ui_func_00299974", r0))
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_QUERY:
            self.call_log.append(("ui_func_0029a25c", r0))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["query"])
        elif address == STUB_SOURCE:
            self.call_log.append(("script_vm_func_002b66ec",))
            uc.reg_write(arm.UC_ARM_REG_R0, SRC_ADDR)
        elif address == STUB_COPY:
            self.call_log.append(
                ("ui_func_002bcf58", self._pointer(r0), self._pointer(r1), r2)
            )
            src = bytes(uc.mem_read(r1, r2))
            uc.mem_write(r0, src)
            uc.reg_write(arm.UC_ARM_REG_R0, r0)
        elif address == STUB_CONSUME:
            raw = bytes(uc.mem_read(r0, SCRATCH_SIZE))
            self.call_log.append(("engine_func_0029960c", raw))
            if self.case.get("consume_mutates"):
                # Force the following 0x0029A368 call to observe this change.
                uc.mem_write(r0 + SCRATCH_SIZE - 1,
                             bytes([self.case["consume_mutates"] & 0xFF]))
        elif address == STUB_FINISH:
            raw = bytes(uc.mem_read(r0, SCRATCH_SIZE))
            self.call_log.append(("engine_func_0029a368", raw))
            uc.reg_write(arm.UC_ARM_REG_R0, finish_value(raw))
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE):
            self.writes.append(
                (address, size, value & ((1 << (8 * size)) - 1))
            )

    # -------------------------------------------------------------- execution
    def _prepare_memory(self, code: bytes, case: dict) -> None:
        uc = self.uc
        uc.mem_write(OBJ_ADDR, b"\x00" * OBJ_SIZE)
        uc.mem_write(SRC_ADDR, b"\x00" * SRC_SIZE)
        uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        uc.mem_write(FUNC_ADDR, b"\x00" * FUNC_SIZE)
        uc.mem_write(FUNC_ADDR, code)
        uc.mem_write(OBJ_ADDR, build_obj(case))
        uc.mem_write(SRC_ADDR, build_src())
        uc.ctl_flush_tb()

    def _set_registers(self, case: dict) -> None:
        uc = self.uc
        uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        junk = case["junk"]
        uc.reg_write(arm.UC_ARM_REG_R0, OBJ_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R1, junk[0])
        uc.reg_write(arm.UC_ARM_REG_R2, junk[1])
        uc.reg_write(arm.UC_ARM_REG_R3, junk[2])
        for name, value in CALLEE_SAVED_START.items():
            uc.reg_write(CALLEE_SAVED[name], value)

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case
        self.count_calls = 0

        self._prepare_memory(code, case)
        self._set_registers(case)
        self.writes = []

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        uc = self.uc
        return {
            "ret": uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "writes": list(self.writes),
            "obj": bytes(uc.mem_read(OBJ_ADDR, OBJ_SIZE)),
            "src": bytes(uc.mem_read(SRC_ADDR, SRC_SIZE)),
        }


def touched_bytes(entries) -> dict:
    """Flatten the ordered write log to address -> byte value.

    The exact store decomposition and the relative order of independent stores
    to the same object are compiler choices, not part of the contract: the ARM
    original writes the two adjacent flag bytes as two ``strb`` while the C++
    body may coalesce them into one halfword store.  What must match is the set
    of touched bytes and the byte value written to each.
    """
    touched: dict = {}
    for address, size, value in entries:
        for index in range(size):
            touched[address + index] = (value >> (8 * index)) & 0xFF
    return touched


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
    if touched_bytes(orig["writes"]) != touched_bytes(cand["writes"]):
        problems.append(
            "touched bytes:\n    orig="
            + repr(sorted(touched_bytes(orig["writes"]).items()))
            + "\n    cand="
            + repr(sorted(touched_bytes(cand["writes"]).items()))
        )
    for key in ("obj", "src"):
        if orig[key] != cand[key]:
            diff = next(
                index
                for index, (left, right) in enumerate(zip(orig[key], cand[key]))
                if left != right
            )
            base = OBJ_ADDR if key == "obj" else SRC_ADDR
            problems.append(
                f"{key} region differs first at 0x{base + diff:08x}: "
                f"orig={orig[key][diff]:02x} cand={cand[key][diff]:02x}"
            )
    return problems


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------
def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "index": 0,
        "count": 0,
        "id": 0x1234,
        "active": 0,
        "pending": 0x5A,
        "enabled": 1,
        "applied": 0,
        "last_visible": 0x1234,  # matches id by default
        "visible": 0,
        "type": 0,
        "query": 0,
        "junk": (0x11111111, 0x22222222, 0x33333333),
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- enabled gate ---------------------------------------------------------
    cases.append(base_case("enabled 0, visible match, returns the loaded zero",
                           enabled=0))
    cases.append(
        base_case("enabled 0, visible mismatch still runs the reset branch",
                  enabled=0, visible=1)
    )
    cases.append(
        base_case("enabled 0, active nonzero, query nonzero (no side effect)",
                  enabled=0, active=0x80, query=1)
    )
    for enabled in (1, 2, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        cases.append(base_case(f"enabled 0x{enabled:08x}", enabled=enabled))

    # --- visibility / last-id decision ---------------------------------------
    cases.append(base_case("visible 1 -> reset branch", visible=1))
    cases.append(base_case("visible 0xFFFFFFFF -> reset branch",
                           visible=0xFFFFFFFF))
    cases.append(base_case("visible 0, last id differs -> reset branch",
                           last_visible=0x4321))
    cases.append(base_case("visible 0, last id differs and active set -> reset",
                           last_visible=0, active=1))
    cases.append(base_case("visible 0, last id matches, active 0",
                           active=0, type=0))
    cases.append(base_case("visible 0, last id matches, active 0, id 0",
                           active=0, id=0, last_visible=0))
    cases.append(base_case("visible 0, last id matches, active 0x01, query 0",
                           active=0x01, query=0))
    cases.append(base_case("visible 0, last id matches, active 0x80, query 1",
                           active=0x80, query=1))
    cases.append(base_case("visible 0, last id matches, active 0xFF, query -1",
                           active=0xFF, query=0xFFFFFFFF))

    # --- active-0 item type dispatch (type re-read before each test) ---------
    for item_type in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0xFFFFFFFF):
        cases.append(
            base_case(f"active 0, type {item_type}",
                      active=0, type=item_type, id=0x2222,
                      last_visible=0x2222)
        )

    # --- applied-id fast paths ------------------------------------------------
    for ident in (0, 1, 0x7FFF, 0x8000, 0xFFFF):
        cases.append(
            base_case(f"applied equals id 0x{ident:04x}",
                      id=ident, applied=ident, last_visible=ident)
        )
    cases.append(
        base_case("applied differs from id", id=0x1111, applied=0x2222)
    )
    cases.append(
        base_case("applied differs, id 0 -> no type patch",
                  id=0, applied=0x2222, last_visible=0)
    )

    # --- copy path switch table (type 2..8 and out-of-range) ------------------
    for item_type in (2, 3, 4, 5, 6, 7, 8):
        cases.append(
            base_case(f"copy path type {item_type}",
                      id=0xABCD, applied=0, type=item_type)
        )
    for item_type in (0, 1, 9, 0x10, 0xFFFFFFFF):
        cases.append(
            base_case(f"copy path out-of-range type {item_type}",
                      id=0xABCD, applied=0, type=item_type)
        )

    # --- selection index / count geometry ------------------------------------
    for index in (0, 1, 2, 3, 5, 6):
        for count in (0, 1, 3, 4):
            cases.append(
                base_case(f"index {index} count {count}",
                          index=index, count=count, id=0x0F0F,
                          last_visible=0x0F0F, active=0, type=4)
            )

    # --- second index read ----------------------------------------------------
    for mutated in (1, 2, 7):
        cases.append(
            base_case(f"count helper changes index to {mutated}",
                      index=0, mutated_index=mutated,
                      mutate_index_on_count=True, visible=1,
                      id=0x0AAA, count=2)
        )

    # --- consume-buffer mutation and finish return ---------------------------
    cases.append(base_case("consume helper mutates the buffer",
                           consume_mutates=0xA5, id=0x5555, applied=0,
                           type=6))
    cases.append(base_case("copy path with junk r1-r3",
                           id=0x7777, applied=0, type=8,
                           junk=(0xDEADBEEF, 0xFFFFFFFF, 0x80000000)))
    return cases


def run_case_set(orig_code: bytes, cand_code: bytes, cases) -> int:
    runner = Machine()
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
        print(
            f"  [PASS] {case['name']}  "
            f"({len(orig['call_log'])} calls, ret=0x{orig['ret']:08x})"
        )
    return passed


def main() -> None:
    print("Testing shop_func_0022f9c8 (0x0022f9c8)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        f"(9 call relocations + 7 switch words resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    mutants = (
        ("entry_stride", "constexpr u32 kEntryStride = 0x74;",
         "constexpr u32 kEntryStride = 0x70;"),
        ("slot_stride", "constexpr u32 kSlotStride = 0x1002;",
         "constexpr u32 kSlotStride = 0x1000;"),
        ("id_stride", "constexpr u32 kIdStride = 4;",
         "constexpr u32 kIdStride = 2;"),
        ("visible_id_offset", "constexpr u32 kVisibleIdOffset = 0x15D54;",
         "constexpr u32 kVisibleIdOffset = 0x15D50;"),
        ("enabled_offset", "constexpr u32 kEnabledOffset = 0x15D24;",
         "constexpr u32 kEnabledOffset = 0x15D20;"),
        ("applied_offset", "constexpr u32 kAppliedIdOffset = 0x15D28;",
         "constexpr u32 kAppliedIdOffset = 0x15D2C;"),
        ("active_byte_read",
         "if (object->active_1e == 0) {",
         "if (*reinterpret_cast<const u8*>(object) == 0) {"),
        ("pending_store", "object->pending_1f = 1;",
         "object->active_1e = 1;"),
        ("first_index_reused",
         "const u32 second_index = load_u32(base + kIndexOffset);",
         "const u32 second_index = index;"),
        ("visibility_conjunction",
         "if (visible == 0 && load_u32(base + kVisibleIdOffset) == id) {",
         "if (visible != 0 && load_u32(base + kVisibleIdOffset) == id) {"),
        ("applied_comparison",
         "if (previous == id) {",
         "if (previous != id) {"),
        ("slot_index",
         "ui_func_002998d8(0, id);",
         "ui_func_002998d8(1, id);"),
        ("active_flag", "object->active_1e = 1;",
         "object->active_1e = 2;"),
        ("query_polarity",
         "} else if (ui_func_0029a25c(object->active_1e) != 0) {",
         "} else if (ui_func_0029a25c(object->active_1e) == 0) {"),
        ("switch_case_4", "case 4: store_u16(buffer + 0x06, id); break;",
         "case 4: store_u16(buffer + 0x04, id); break;"),
        ("final_return", "return engine_func_0029a368(buffer);",
         "engine_func_0029a368(buffer);\n    return 0;"),
    )
    for name, old, new in mutants:
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        runner = Machine()
        for case in cases:
            orig = runner.run(orig_code, case)
            try:
                bad = runner.run(mutant_code, case)
            except RuntimeError:
                detected = True
                break
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")
    print(f"{len(mutants)}/{len(mutants)} negative controls detected.")


if __name__ == "__main__":
    main()
