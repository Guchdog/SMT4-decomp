#!/usr/bin/env python3
"""Differential test for script_vm_func_0028f15c (0x0028f15c) using Unicorn ARM.

The routine releases a script-VM actor `id`.  It indexes a four-byte flag
record at [actor_work + 0x200 + id*4] and a shared work block (both returned by
0x002ADF14), applies two early-return gates, rewrites the flag record, and then
either claims a 14-byte slot of the four-entry table at work+0x842 or records
the id as the active id at work+0x840 and clears command bits 0x500..0x51F.

Every direct call is replaced by a deterministic stub that logs its arguments.
0x002ADF14 returns a scripted sequence of work-block pointers so that the two
role bases (flag record, shared work block) and the per-bit refetch can be
told apart. 0x003EB280 is stubbed with its real 12-byte zero-fill body.

Each case runs the pinned original and the compiled candidate with identical
fixtures and compares:
  - the ordered call log,
  - return value, continuation PC and SP,
  - callee-saved integer and VFP registers,
  - the four 0x920-byte fixture windows (all of the memory this function can
    address for the tested ids) and the stack regions outside the dead push
    frame,
  - the same values against an independent Python model of the recovered
    behavior.
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
FUNC_ADDR = 0x0028F15C
FUNC_SIZE = 400
TU_PATH = ROOT / "src/engine/leaf_batch33_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_0028f15c"

# ---------------------------------------------------------------------------
# Emulated address space
# ---------------------------------------------------------------------------
IMAGE_ADDR = 0x00100000
IMAGE_MAP_SIZE = 0x00500000          # 0x00100000..0x00600000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

BASE_A = 0x00400000                  # first getter result (flag record)
BASE_B = 0x00410000                  # second getter result (shared work block)
BASE_C = 0x00420000                  # per-bit refetch base
BASE_D = 0x00430000                  # alternate per-bit refetch base
ALL_BASES = (BASE_A, BASE_B, BASE_C, BASE_D)

WORK_SIZE = 0x920

# Work-block field offsets (ARM evidence only).
ACTIVE_ID = 0x840
SLOT_TABLE = 0x842
SLOT_STRIDE = 14
SLOT_COUNT = 4
SLOT_PAYLOAD = 2
TAIL_RECORD = 0x87A
TAIL_FIELD = 0x886
COMMAND_FIRST_BIT = 0x500
COMMAND_BIT_COUNT = 0x20

# Direct-call stubs (original branch targets).
STUB_2ADF14 = 0x002ADF14
STUB_287AFC = 0x00287AFC
STUB_299224 = 0x00299224
STUB_3EB280 = 0x003EB280
STUB_23DF18 = 0x0023DF18

STUB_BY_SYMBOL = {
    "engine_func_002adf14": STUB_2ADF14,
    "script_vm_func_00287afc": STUB_287AFC,
    "script_vm_func_00299224": STUB_299224,
    "camp_func_003eb280": STUB_3EB280,
    "script_vm_func_0023df18": STUB_23DF18,
}

BX_LR = 0xE12FFF1E

# The pool literal at 0x0028F2E8 read by the original's `ldr r0,[pc,#0x160]`.
ID_LIMIT = 0x15E


# ---------------------------------------------------------------------------
# Candidate preparation
# ---------------------------------------------------------------------------
def get_orig_bytes():
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def image_bytes():
    return ORIG_BIN.read_bytes()


def sign_extend_24(value):
    return value - 0x1000000 if value & 0x800000 else value


def compile_variant(src_file, obj_file):
    result = compile_tu_armv6k(Path(src_file), Path(obj_file), ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed for {src_file}: {result.stderr}")

    funcs = extract_elf_functions_detailed(Path(obj_file))
    entry = funcs.get("script_vm_func_0028f15c")
    if entry is None:
        raise RuntimeError(
            "script_vm_func_0028f15c not found in object: "
            + ", ".join(sorted(funcs))
        )

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
        else:
            raise RuntimeError(f"unsupported relocation: {rel}")

    return bytes(code)


def compile_candidate():
    return compile_variant(TU_PATH, OUT_DIR / "leaf_batch33_c.o")


def compile_mutant(name, old, new):
    text = TU_PATH.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    return compile_variant(mutant_src, OUT_DIR / f"mutant_{name}.o")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
def flag_offset(case):
    """Byte offset of the 4-byte flag record inside the actor work block."""
    return (0x200 + ((case["id"] << 2) & 0xFFFFFFFF)) & 0xFFFFFFFF


def make_images(case):
    """Deterministic 0x920-byte images for every potential work-block base."""
    images = {}
    for index, base in enumerate(ALL_BASES):
        data = bytearray(WORK_SIZE)
        for i in range(WORK_SIZE):
            data[i] = (i * 37 + 11 + index * 53) & 0xFF
        struct.pack_into("<H", data, ACTIVE_ID, case["active_id"])
        for slot in range(SLOT_COUNT):
            off = SLOT_TABLE + slot * SLOT_STRIDE
            struct.pack_into("<H", data, off, case["slots"][slot])
            data[off + SLOT_PAYLOAD:off + SLOT_STRIDE] = b"\xaa" * 12
        data[TAIL_RECORD:TAIL_RECORD + 12] = b"\x55" * 12
        struct.pack_into("<H", data, TAIL_FIELD, case["tail_field"])
        data[0x9F] = 0x5A
        data[0xA0:0xA4] = case["command_bytes"]
        data[0xA4] = 0xA5
        images[base] = data
    offset = flag_offset(case)
    for data in images.values():
        data[offset:offset + 3] = case["flags"]
    return images


class Machine:
    def __init__(self):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(IMAGE_ADDR, IMAGE_MAP_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        self.original_image = image_bytes()
        self.uc.mem_write(IMAGE_ADDR, self.original_image)
        self.orig_code = get_orig_bytes()

        self.call_log = []
        self.case = None
        self.getter_calls = 0
        self.gate_calls = 0
        self._install_stubs()

    def _install_stubs(self):
        bx_lr = struct.pack("<I", BX_LR)
        stubs = [
            (STUB_2ADF14, self._on_getter),
            (STUB_287AFC, self._on_kind),
            (STUB_299224, self._on_gate),
            (STUB_3EB280, self._on_clear_slot),
            (STUB_23DF18, self._on_command),
        ]
        for address, hook in stubs:
            self.uc.mem_write(address, bx_lr)
            self.uc.hook_add(unicorn.UC_HOOK_CODE, hook, begin=address, end=address)

    # -- stub bodies ------------------------------------------------------
    def _on_getter(self, uc, address, size, user_data):
        bases = self.case["bases"]
        base = bases[min(self.getter_calls, len(bases) - 1)]
        self.call_log.append(("EngineWorkBlock", base))
        effect = self.case["getter_writes"].get(self.getter_calls)
        if effect is not None:
            offset, payload = effect
            uc.mem_write((base + offset) & 0xFFFFFFFF, payload)
        self.getter_calls += 1
        self.case["_active_block"] = base
        uc.reg_write(arm.UC_ARM_REG_R0, base)

    def _on_kind(self, uc, address, size, user_data):
        actor_id = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(("ScriptVmActorKind", actor_id))
        uc.reg_write(arm.UC_ARM_REG_R0, self.case["kind"] & 0xFFFFFFFF)

    def _on_gate(self, uc, address, size, user_data):
        actor_id = uc.reg_read(arm.UC_ARM_REG_R0)
        values = self.case["gate_calls"]
        value = values[min(self.gate_calls, len(values) - 1)]
        self.call_log.append(("ScriptVmActorGate", actor_id))
        self.gate_calls += 1
        uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)

    def _on_clear_slot(self, uc, address, size, user_data):
        payload = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(("CampClearSlot", payload))
        # Real body of 0x003EB280: three word stores.
        uc.mem_write(payload, b"\x00" * 12)

    def _on_command(self, uc, address, size, user_data):
        bit = uc.reg_read(arm.UC_ARM_REG_R0)
        flag = uc.reg_read(arm.UC_ARM_REG_R1)
        self.call_log.append(("ScriptVmCommand", bit, flag))
        effect = self.case["command_effects"].get(bit)
        if effect is not None:
            offset, payload = effect
            # Applies to the block the candidate/original is about to update.
            block = self.case["_active_block"]
            uc.mem_write((block + offset) & 0xFFFFFFFF, payload)

    # -- helpers ----------------------------------------------------------
    def _reset_fixtures(self, case):
        images = make_images(case)
        case["_images"] = images
        for base, data in images.items():
            self.uc.mem_write(base, bytes(data))

    def run(self, candidate, case):
        """candidate = None runs the pinned original."""
        uc = self.uc
        self.case = case
        self.call_log = []
        self.getter_calls = 0
        self.gate_calls = 0
        case["_active_block"] = None

        self._reset_fixtures(case)
        if candidate is None:
            uc.mem_write(FUNC_ADDR, self.orig_code)
        else:
            uc.mem_write(FUNC_ADDR, candidate)
        # Unicorn keeps translated blocks across mem_write; drop them.
        uc.ctl_flush_tb()

        sp = STACK_ADDR + STACK_SIZE - 0x100
        uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        uc.reg_write(arm.UC_ARM_REG_SP, sp)
        uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R0, case["id"])
        uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
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
        finally:
            uc.ctl_flush_tb()

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
            "images": {
                base: bytes(uc.mem_read(base, WORK_SIZE)) for base in ALL_BASES
            },
            "stack_guard": (
                bytes(uc.mem_read(STACK_ADDR, sp - 0x40 - STACK_ADDR)),
                bytes(uc.mem_read(sp, STACK_ADDR + STACK_SIZE - sp)),
            ),
        }


# ---------------------------------------------------------------------------
# Independent expected model
# ---------------------------------------------------------------------------
def read_u16(data, offset):
    return struct.unpack_from("<H", data, offset)[0]


def write_u16(data, offset, value):
    struct.pack_into("<H", data, offset, value & 0xFFFF)


def expected_case(case):
    """Return (call_log, return_value, images) for the recovered behavior."""
    images = {base: bytearray(data) for base, data in case["_images"].items()}
    bases = case["bases"]
    log = []
    index = 0

    def getter():
        nonlocal index
        base = bases[min(index, len(bases) - 1)]
        log.append(("EngineWorkBlock", base))
        effect = case["getter_writes"].get(index)
        if effect is not None:
            offset, payload = effect
            images[base][offset:offset + len(payload)] = payload
        index += 1
        return base

    actor = getter()
    work = getter()
    offset = flag_offset(case)
    flags = images[actor]

    if (flags[offset] & 1) == 0 and case["id"] < ID_LIMIT:
        return log, 0, images

    kind = case["kind"]
    log.append(("ScriptVmActorKind", case["id"]))
    first_gate = case["gate_calls"][0]
    log.append(("ScriptVmActorGate", case["id"]))
    if first_gate == 0 and kind != 0 and read_u16(images[work], ACTIVE_ID) != 0:
        return log, 0, images

    follow = flags[offset + 1]
    value = ((flags[offset] & ~4) | 2) & 0xFF
    flags[offset] = value
    value = (value | 0x40) if follow else (value & ~0x40 & 0xFF)
    flags[offset] = value
    flags[offset] = value & ~0x80 & 0xFF
    flags[offset + 2] = flags[offset + 2] & ~5 & 0xFF

    second_gate = case["gate_calls"][1]
    log.append(("ScriptVmActorGate", case["id"]))
    block = images[work]

    if second_gate != 0:
        if kind == 1:
            for slot in range(SLOT_COUNT):
                slot_offset = SLOT_TABLE + slot * SLOT_STRIDE
                if read_u16(block, slot_offset) == 0:
                    write_u16(block, slot_offset, case["id"])
                    log.append(
                        ("CampClearSlot", (work + slot_offset + SLOT_PAYLOAD) & 0xFFFFFFFF)
                    )
                    block[slot_offset + SLOT_PAYLOAD:slot_offset + SLOT_STRIDE] = (
                        b"\x00" * 12
                    )
                    break
        return log, 1, images

    if kind == 0:
        return log, 1, images

    write_u16(block, ACTIVE_ID, case["id"])
    block[TAIL_RECORD:TAIL_RECORD + 12] = b"\x00" * 12
    write_u16(block, TAIL_FIELD, 0)

    for bit in range(COMMAND_FIRST_BIT, COMMAND_FIRST_BIT + COMMAND_BIT_COUNT):
        current = getter()
        target = images[current]
        log.append(("ScriptVmCommand", bit, 0))
        effect = case["command_effects"].get(bit)
        if effect is not None:
            effect_offset, payload = effect
            target[effect_offset:effect_offset + len(payload)] = payload
        target[bit >> 3] = target[bit >> 3] & ~(1 << (bit & 7)) & 0xFF

    return log, 1, images


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------
def make_case(name, actor_id, **kwargs):
    case = {
        "name": name,
        "id": actor_id & 0xFFFFFFFF,
        "kind": 0,
        "gate_calls": (1, 0),
        "flags": bytes((0x01, 0x00, 0x00)),
        "active_id": 0,
        "slots": [0x0000, 0x0000, 0x0000, 0x0000],
        "tail_field": 0x1234,
        "command_bytes": b"\xff\xff\xff\xff",
        "bases": [BASE_A, BASE_B, BASE_C],
        "getter_writes": {},
        "command_effects": {},
    }
    case.update(kwargs)
    return case


def build_cases():
    return [
        # --- first gate: flag bit 0 and the unsigned 0x15E limit ----------
        make_case("bit0 clear, id 0 -> early 0", 0,
                  flags=b"\x00\x00\x00"),
        make_case("bit0 clear, id 1 -> early 0", 1,
                  flags=b"\xfe\x00\x00"),
        make_case("bit0 clear, id 0x15d -> early 0", 0x15D,
                  flags=b"\x00\x00\x00"),
        make_case("bit0 clear, id 0x15e -> runs (activation)", 0x15E,
                  flags=b"\x00\x00\x00", kind=2, gate_calls=(1, 0)),
        make_case("bit0 set, id 0x15d -> runs (slot 0)", 0x15D,
                  flags=b"\x01\x00\x00", kind=1, gate_calls=(1, 1)),
        make_case("bit0 clear, id 0x15f -> runs (slot 3)", 0x15F,
                  flags=b"\x04\x01\x05", kind=1, gate_calls=(1, 1),
                  slots=[5, 6, 7, 0]),
        make_case("bit0 set high bits, id 0x18f -> all slots busy", 0x18F,
                  flags=b"\x80\x00\x00", kind=1, gate_calls=(1, 1),
                  slots=[1, 2, 3, 4]),
        # --- unsigned/wrapped id boundaries ------------------------------
        make_case("id 0x40000000 wraps to +0x200 (activation)", 0x40000000,
                  flags=b"\x00\x00\x00", kind=2, gate_calls=(1, 0)),
        make_case("id 0x7fffffff wraps to +0x1fc (free slot 3)", 0x7FFFFFFF,
                  flags=b"\x01\x00\x00", kind=1, gate_calls=(1, 1),
                  slots=[7, 8, 9, 0], active_id=0x1357),
        make_case("id 0x80000000 wraps to +0x200 (kind 0)", 0x80000000,
                  flags=b"\x00\x00\x00", kind=0, gate_calls=(1, 0)),
        make_case("id 0xffffffff wraps to +0x1fc (gate 2 passes)", 0xFFFFFFFF,
                  flags=b"\x01\x00\x00", kind=-1, gate_calls=(0, 0),
                  active_id=0),
        # --- second gate --------------------------------------------------
        make_case("gate2: first read 0, kind 2, active 7 -> 0", 0x20,
                  kind=2, gate_calls=(0, 0), active_id=7, flags=b"\x01\x00\x00"),
        make_case("gate2: first read 0, kind 2, active 0 -> activation", 0x20,
                  kind=2, gate_calls=(0, 0), active_id=0, flags=b"\x01\x00\x00"),
        make_case("gate2: first read 0, kind 0, active 9 -> return 1", 0x21,
                  kind=0, gate_calls=(0, 1), active_id=9, flags=b"\x01\x00\x00"),
        make_case("gate2: first read 1, kind 2, active 0 -> activation", 0x22,
                  kind=2, gate_calls=(1, 0), active_id=0),
        make_case("gate2: first read 0, kind 1, active 0 -> slot", 0x23,
                  kind=1, gate_calls=(0, 1), active_id=0,
                  slots=[0, 0, 0, 0]),
        # --- second entity-flag read set ---------------------------------
        make_case("gate2 set, kind 1, slot 0 free", 0x30,
                  kind=1, gate_calls=(1, 1)),
        make_case("gate2 set, kind 1, slot 1 free", 0x31,
                  kind=1, gate_calls=(1, 1), slots=[0xAA, 0, 0xCC, 0xDD]),
        make_case("gate2 set, kind 1, only slot 3 free", 0x32,
                  kind=1, gate_calls=(1, 1), slots=[1, 2, 3, 0]),
        make_case("gate2 set, kind 1, no free slot", 0x33,
                  kind=1, gate_calls=(1, 1), slots=[5, 6, 7, 8],
                  active_id=0x4242),
        make_case("gate2 set, kind 0 -> return 1", 0x34,
                  kind=0, gate_calls=(1, 1)),
        make_case("gate2 set, kind 2 -> return 1", 0x35,
                  kind=2, gate_calls=(1, 1)),
        make_case("gate2 set, kind -1 -> return 1", 0x36,
                  kind=-1, gate_calls=(1, 1)),
        # --- second entity-flag read clear -------------------------------
        make_case("gate2 clear, kind 0 -> return 1, no work", 0x40,
                  kind=0, gate_calls=(1, 0)),
        make_case("gate2 clear, kind 1 -> activation", 0x41,
                  kind=1, gate_calls=(1, 0)),
        make_case("gate2 clear, kind 3 -> activation", 0x42,
                  kind=3, gate_calls=(1, 0), active_id=0xBEEF),
        make_case("gate2 clear, kind -1 -> activation", 0x43,
                  kind=-1, gate_calls=(1, 0)),
        # --- flag record rewrite combinations ----------------------------
        make_case("flags 00/00/ff -> 02/00/fa", 0x15E,
                  flags=b"\x00\x00\xff", kind=0, gate_calls=(1, 0)),
        make_case("flags ff/01/ff -> 7e/01/fa", 0x50,
                  flags=b"\xff\x01\xff", kind=0, gate_calls=(1, 0)),
        make_case("flags 01/00/05 -> 03/00/00", 0x51,
                  flags=b"\x01\x00\x05", kind=0, gate_calls=(1, 0)),
        make_case("flags 24/ff/fa -> 66/ff/fa? (follow sets bit 6)", 0x52,
                  flags=b"\x24\xff\xfa", kind=2, gate_calls=(1, 0)),
        # --- work-block roles -------------------------------------------
        make_case("role base swap: flags C, work A, bits B", 0x60,
                  kind=2, gate_calls=(1, 0),
                  bases=[BASE_C, BASE_A, BASE_B]),
        make_case("same base for every getter call (slot)", 0x61,
                  kind=1, gate_calls=(1, 1), bases=[BASE_A]),
        make_case("same base for every getter call (gate 2 -> 0)", 0x62,
                  kind=2, gate_calls=(0, 0), active_id=5, bases=[BASE_A]),
        make_case("same base for every getter call (activation)", 0x63,
                  kind=2, gate_calls=(1, 0), bases=[BASE_A]),
        make_case("alternating refetch bases C/D", 0x64,
                  kind=2, gate_calls=(1, 0),
                  bases=[BASE_A, BASE_B] + [BASE_C, BASE_D] * 32),
        # --- ordering-sensitive helper side effects ---------------------
        make_case("first getter rewrites the flag record before the gate", 0x70,
                  kind=2, gate_calls=(1, 0),
                  flags=b"\x00\x00\x00",
                  getter_writes={0: (0x200 + 0x70 * 4, b"\x01\x00\x00")}),
        make_case("loop getter rewrites command byte 0xa0", 0x71,
                  kind=2, gate_calls=(1, 0),
                  getter_writes={5: (0xA0, b"\xff")}),
        make_case("command call rewrites command byte 0xa1", 0x72,
                  kind=2, gate_calls=(1, 0),
                  command_effects={0x503: (0xA1, b"\xff")}),
    ]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def check_against_model(case, result):
    log, ret, images = expected_case(case)
    assert result["call_log"] == log, (
        f"model call log mismatch on {case['name']}:\n"
        f"  Expected: {log}\n  Actual:   {result['call_log']}"
    )
    assert result["r0"] == ret, (
        f"model return mismatch on {case['name']}: "
        f"0x{result['r0']:08x} != 0x{ret:08x}"
    )
    for base in ALL_BASES:
        assert result["images"][base] == bytes(images[base]), (
            f"model memory mismatch on {case['name']} at 0x{base:08x}"
        )


def main():
    print("Testing script_vm_func_0028f15c (0x0028f15c)...")
    with open(ORIG_BIN, "rb") as f:
        f.seek(0x0028F2E8 - 0x00100000)
        assert struct.unpack("<I", f.read(4))[0] == ID_LIMIT, (
            "pool literal at 0x0028f2e8 is not 0x15e"
        )
    cand = compile_candidate()
    print(f"  original: {FUNC_SIZE} B, candidate: {len(cand)} B")

    machine = Machine()
    cases = build_cases()
    entry_sp = STACK_ADDR + STACK_SIZE - 0x100

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
        assert res_orig["images"] == res_cand["images"], (
            f"fixture memory mismatch on {case['name']}: "
            + ", ".join(
                base_name
                for base_name, base in zip("ABCD", ALL_BASES)
                if res_orig["images"][base] != res_cand["images"][base]
            )
        )
        assert res_orig["stack_guard"] == res_cand["stack_guard"], (
            f"stack guard mismatch on {case['name']}"
        )
        assert res_orig["sp"] == res_cand["sp"] == entry_sp, (
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
        check_against_model(case, res_cand)

        passed += 1
        print(f"  [PASS] {case['name']}")

    print("\nNegative controls:")
    mutants = [
        (
            "gate_limit_le_instead_of_lt",
            "id < kActorIdLimit",
            "id <= kActorIdLimit",
        ),
        (
            "gate_inverts_flag_bit0",
            "(flags[0] & 1u) == 0",
            "(flags[0] & 1u) != 0",
        ),
        (
            "gate2_inverted",
            "if (gate == 0 && kind != 0 && LoadHalf(work, kActiveId) != 0) {",
            "if (gate != 0 && kind != 0 && LoadHalf(work, kActiveId) != 0) {",
        ),
        (
            "gate2_ignores_kind",
            "if (gate == 0 && kind != 0 && LoadHalf(work, kActiveId) != 0) {",
            "if (gate == 0 && kind == 0 && LoadHalf(work, kActiveId) != 0) {",
        ),
        (
            "gate2_halfword_inverted",
            "LoadHalf(work, kActiveId) != 0",
            "LoadHalf(work, kActiveId) == 0",
        ),
        (
            "slot_scan_misses_last_slot",
            "for (u32 index = 0; index < kSlotCount; ++index) {",
            "for (u32 index = 0; index < kSlotCount - 1; ++index) {",
        ),
        (
            "command_loop_clears_one_extra_bit",
            "bit < kCommandFirstBit + kCommandBitCount; ++bit",
            "bit <= kCommandFirstBit + kCommandBitCount; ++bit",
        ),
        (
            "active_id_stored_at_wrong_offset",
            "StoreHalf(work, kActiveId, static_cast<u16>(id));",
            "StoreHalf(work, kActiveId + 2, static_cast<u16>(id));",
        ),
        (
            "flag_bit6_follow_inverted",
            "follow != 0 ? (value | 0x40u) : (value & ~0x40u)",
            "follow == 0 ? (value | 0x40u) : (value & ~0x40u)",
        ),
        (
            "slot_kind_test_inverted",
            "if (kind != 1) {",
            "if (kind == 1) {",
        ),
    ]
    for name, old, new in mutants:
        mutant = compile_mutant(name, old, new)
        detected = False
        for case in cases:
            res_orig = machine.run(None, case)
            res_mut = machine.run(mutant, case)
            if res_orig != res_mut:
                detected = True
                break
        assert detected, f"negative control not detected: {name}"
        print(f"  [PASS] mutant detected: {name}")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
