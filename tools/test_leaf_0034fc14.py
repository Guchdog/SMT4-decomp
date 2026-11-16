#!/usr/bin/env python3
"""Differential test for engine_func_0034fc14 (0x0034fc14) using Unicorn ARM.

The routine is the wait/counter stage of the action-step object that is also
driven by camp_func_00351040 (0x00351040):

  * inspect the animation subobject at object+0x158 (0x0023A774 for the signed
    remaining count and 0x0023A690 for the completion test),
  * only service step states 3 and 6, move them to state 2 under the object lock
    and busy-wait with AsdThread_Sleep(0x0007A120, 0) until state 1, 7 or 8,
  * then, for the two slot indices at +0x46C, read a value through virtual slot
    +0x10 of the per-index object at +0x2EC, truncate it to a multiple of the
    granularity derived from the 40-byte entry at +0x30C, and advance virtual
    slot +0x1C once per frame while incrementing the +0x47C counter.

Every direct callee is replaced with a deterministic stub at its original
address.  Each case runs the pinned original and the compiled candidate with an
identical fixture and compares:
  - the ordered call log (with arguments and the step state seen by the lock
    helpers, so the state-store order is observable),
  - return value, continuation PC and SP,
  - callee-saved integer and VFP registers,
  - the full 0x500-byte object block, the slot objects, the vtables and the
    stub function area.
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
FUNC_ADDR = 0x0034FC14
FUNC_SIZE = 400
TU_PATH = ROOT / "src/engine/leaf_batch44_b.cpp"
OUT_DIR = ROOT / "build/test_leaf_0034fc14"

# ---------------------------------------------------------------------------
# Emulated address space
# ---------------------------------------------------------------------------
IMAGE_ADDR = 0x00100000
IMAGE_SIZE = 0x00500000              # 0x00100000..0x00600000 (pinned image)
FN_ADDR = 0x00600000                 # virtual-slot stub bodies
FN_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

OBJ_ADDR = 0x00450000                # action-step object
OBJ_WATCH = 0x500
SLOT_OBJ_ADDR = 0x00460000           # eight per-index objects
SLOT_OBJ_STRIDE = 0x20
SLOT_OBJ_COUNT = 8
VT_ADDR = 0x00470000                 # their virtual tables
VT_STRIDE = 0x40
SLOT_FN_STRIDE = 0x40
SLOT_FN_COUNT = 8

# Object offsets used by the function (see the C++ struct).
OFF_STATE = 0x00C
OFF_SYNC = 0x020
OFF_ANIM = 0x158
OFF_ANIM_END = 0x058
OFF_ANIM_POS = 0x05C
OFF_LIMIT = 0x2E8
OFF_OBJECTS = 0x2EC
OFF_ENTRIES = 0x30C
ENTRY_STRIDE = 40
OFF_INDEX = 0x46C
OFF_COUNTER = 0x47C

# Direct-call stubs (original branch targets).
STUB_23A774 = 0x0023A774
STUB_23A690 = 0x0023A690
STUB_351040 = 0x00351040
STUB_2C4244 = 0x002C4244
STUB_2C3AA8 = 0x002C3AA8
STUB_2C3A24 = 0x002C3A24
STUB_2BB490 = 0x002BB490
STUB_2C615C = 0x002C615C

STUB_BY_SYMBOL = {
    "_Z13func_0023a774Ph": STUB_23A774,
    "engine_func_0023a690": STUB_23A690,
    "camp_func_00351040": STUB_351040,
    "nn_sdk_func_002c4244": STUB_2C4244,
    "engine_func_002c3aa8": STUB_2C3AA8,
    "engine_func_002c3a24": STUB_2C3A24,
    "AsdThread_Sleep": STUB_2BB490,
    "ui_func_002c615c": STUB_2C615C,
}

BX_LR = 0xE12FFF1E
SLEEP_INTERVAL = 0x0007A120
MAX_SLEEPS = 64


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def s32(value):
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def u32(value):
    return value & 0xFFFFFFFF


def sign_extend_24(value):
    return value - 0x1000000 if value & 0x800000 else value


def get_orig_bytes():
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def compile_variant(src_file, obj_file):
    result = compile_tu_armv6k(Path(src_file), Path(obj_file), ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed for {src_file}: {result.stderr}")

    funcs = extract_elf_functions_detailed(Path(obj_file))
    entry = funcs.get("engine_func_0034fc14")
    if entry is None:
        raise RuntimeError(
            "engine_func_0034fc14 not found in object: " + ", ".join(sorted(funcs))
        )

    raw, relocs = entry
    code = bytearray(raw)
    for rel in relocs:
        if rel.relocation_type not in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            raise RuntimeError(f"unsupported relocation: {rel}")
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
        # Verify that the patched branch really lands on the requested stub.
        patched = struct.unpack_from("<I", code, rel.offset)[0]
        landed = place + 8 + (sign_extend_24(patched & 0x00FFFFFF) << 2)
        if landed != target:
            raise RuntimeError(
                f"patched call 0x{place:08x} lands on 0x{landed:08x}, "
                f"expected 0x{target:08x}"
            )
    return bytes(code)


def compile_candidate():
    return compile_variant(TU_PATH, OUT_DIR / "leaf_batch44_b.o")


def compile_mutant(name, old, new):
    text = TU_PATH.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    return compile_variant(mutant_src, OUT_DIR / f"mutant_{name}.o")


# ---------------------------------------------------------------------------
# Machine
# ---------------------------------------------------------------------------
class Machine:
    def __init__(self):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(IMAGE_ADDR, IMAGE_SIZE)
        self.uc.mem_map(FN_ADDR, FN_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        self.original_image = ORIG_BIN.read_bytes()
        self.uc.mem_write(IMAGE_ADDR, self.original_image)
        self.orig_code = get_orig_bytes()

        self.call_log = []
        self.case = None
        self.sleeps = 0
        self._install_stubs()

    # -- stub installation ------------------------------------------------
    def _install_stubs(self):
        bx_lr = struct.pack("<I", BX_LR)
        direct = [
            (STUB_23A774, self._on_23a774),
            (STUB_23A690, self._on_23a690),
            (STUB_351040, self._on_351040),
            (STUB_2C4244, self._on_2c4244),
            (STUB_2C3AA8, self._on_2c3aa8),
            (STUB_2C3A24, self._on_2c3a24),
            (STUB_2BB490, self._on_2bb490),
            (STUB_2C615C, self._on_2c615c),
        ]
        for address, hook in direct:
            self.uc.mem_write(address, bx_lr)
            self.uc.hook_add(unicorn.UC_HOOK_CODE, hook, begin=address, end=address)

        # Virtual-slot stubs: read at +0x10, advance at +0x1C of each vtable.
        slot_area = bytearray(b"\x00" * (SLOT_FN_STRIDE * SLOT_FN_COUNT))
        for index in range(SLOT_FN_COUNT):
            base = index * SLOT_FN_STRIDE
            slot_area[base:base + 4] = bx_lr
            slot_area[base + 0x20:base + 0x24] = bx_lr
        self.uc.mem_write(FN_ADDR, bytes(slot_area))
        self.uc.hook_add(
            unicorn.UC_HOOK_CODE,
            self._on_slot_call,
            begin=FN_ADDR,
            end=FN_ADDR + SLOT_FN_STRIDE * SLOT_FN_COUNT - 1,
        )

    # -- stub bodies ------------------------------------------------------
    def _write_u32(self, address, value):
        self.uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))

    def _read_u32(self, address):
        return struct.unpack("<I", self.uc.mem_read(address, 4))[0]

    def _on_23a774(self, uc, address, size, user_data):
        sub = uc.reg_read(arm.UC_ARM_REG_R0)
        end = s32(self._read_u32(sub + OFF_ANIM_END))
        pos = s32(self._read_u32(sub + OFF_ANIM_POS))
        remaining = s32(end - pos)
        self.call_log.append(("func_0023a774", sub, remaining))
        uc.reg_write(arm.UC_ARM_REG_R0, u32(remaining))

    def _on_23a690(self, uc, address, size, user_data):
        sub = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(("engine_func_0023a690", sub))
        uc.reg_write(arm.UC_ARM_REG_R0, u32(self.case["anim_ok"]))

    def _on_351040(self, uc, address, size, user_data):
        self.call_log.append(("camp_func_00351040", uc.reg_read(arm.UC_ARM_REG_R0)))

    def _on_2c4244(self, uc, address, size, user_data):
        self.call_log.append(("nn_sdk_func_002c4244", uc.reg_read(arm.UC_ARM_REG_R0)))

    def _on_2c3aa8(self, uc, address, size, user_data):
        obj = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(("lock", obj, self._read_u32(OBJ_ADDR + OFF_STATE)))

    def _on_2c3a24(self, uc, address, size, user_data):
        obj = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(("unlock", obj, self._read_u32(OBJ_ADDR + OFF_STATE)))

    def _on_2bb490(self, uc, address, size, user_data):
        lo = uc.reg_read(arm.UC_ARM_REG_R0)
        hi = uc.reg_read(arm.UC_ARM_REG_R1)
        self.call_log.append(("AsdThread_Sleep", lo, hi))
        self.sleeps += 1
        if self.sleeps > MAX_SLEEPS:
            raise RuntimeError("AsdThread_Sleep called too often (wait loop stuck)")
        script = self.case["sleep_script"]
        if script:
            next_state = script[min(self.sleeps - 1, len(script) - 1)]
            self._write_u32(OBJ_ADDR + OFF_STATE, next_state)

    def _on_2c615c(self, uc, address, size, user_data):
        numerator = s32(uc.reg_read(arm.UC_ARM_REG_R0))
        denominator = s32(uc.reg_read(arm.UC_ARM_REG_R1))
        self.call_log.append(("ui_func_002c615c", numerator, denominator))
        quotient, remainder = idivmod(numerator, denominator)
        uc.reg_write(arm.UC_ARM_REG_R0, quotient)
        uc.reg_write(arm.UC_ARM_REG_R1, remainder)

    def _on_slot_call(self, uc, address, size, user_data):
        offset = address - FN_ADDR
        index = offset // SLOT_FN_STRIDE
        step = offset % SLOT_FN_STRIDE
        self_obj = uc.reg_read(arm.UC_ARM_REG_R0)
        if step == 0x00:
            out = uc.reg_read(arm.UC_ARM_REG_R1)
            value = self.case["slot_values"].get(index, 0)
            self.call_log.append(("slot_read", index, self_obj, value))
            self._write_u32(out, value)
        elif step == 0x20:
            self.call_log.append(("slot_advance", index, self_obj))
            mutation = self.case["advance_writes_index"]
            if mutation is not None:
                trigger, slot, new_index = mutation
                if trigger == index:
                    self._write_u32(
                        OBJ_ADDR + OFF_INDEX + slot * 4, new_index
                    )
        else:
            raise RuntimeError(f"unexpected slot stub entry 0x{address:08x}")

    # -- fixtures ---------------------------------------------------------
    def _reset_fixtures(self, case):
        self.case = case
        self.sleeps = 0
        self.call_log = []

        self.uc.mem_write(OBJ_ADDR, b"\xA5" * OBJ_WATCH)
        self._write_u32(OBJ_ADDR + OFF_STATE, case["state"])
        self._write_u32(OBJ_ADDR + OFF_SYNC, 0x20202020)
        self._write_u32(OBJ_ADDR + OFF_ANIM + OFF_ANIM_END, case["anim_end"])
        self._write_u32(OBJ_ADDR + OFF_ANIM + OFF_ANIM_POS, case["anim_pos"])
        self._write_u32(OBJ_ADDR + OFF_LIMIT, case["limit"])
        for index in range(SLOT_OBJ_COUNT):
            self._write_u32(
                OBJ_ADDR + OFF_OBJECTS + index * 4,
                SLOT_OBJ_ADDR + index * SLOT_OBJ_STRIDE,
            )
            self._write_u32(
                OBJ_ADDR + OFF_ENTRIES + index * ENTRY_STRIDE + 8,
                case["modes"][index],
            )
        self._write_u32(OBJ_ADDR + OFF_INDEX + 0, case["indices"][0])
        self._write_u32(OBJ_ADDR + OFF_INDEX + 4, case["indices"][1])
        self._write_u32(OBJ_ADDR + OFF_COUNTER + 0, case["counters"][0])
        self._write_u32(OBJ_ADDR + OFF_COUNTER + 4, case["counters"][1])

        slot_objects = bytearray()
        vtables = bytearray()
        for index in range(SLOT_OBJ_COUNT):
            slot_objects += struct.pack(
                "<IIII", VT_ADDR + index * VT_STRIDE, 0x51000000 + index, 0, 0
            )
            slot_objects += b"\x00" * (SLOT_OBJ_STRIDE - 16)
            vtable = [
                0xDEAD0000 + index,
                0xDEAD0001 + index,
                0xDEAD0002 + index,
                0xDEAD0003 + index,
                FN_ADDR + index * SLOT_FN_STRIDE + 0x00,
                0xDEAD0005 + index,
                0xDEAD0006 + index,
                FN_ADDR + index * SLOT_FN_STRIDE + 0x20,
            ]
            vtables += struct.pack("<8I", *vtable)
            vtables += b"\x00" * (VT_STRIDE - 32)
        self.uc.mem_write(SLOT_OBJ_ADDR, bytes(slot_objects))
        self.uc.mem_write(VT_ADDR, bytes(vtables))

    def run(self, candidate, case):
        """candidate = None runs the pinned original."""
        uc = self.uc
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
        uc.reg_write(arm.UC_ARM_REG_R0, OBJ_ADDR)
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
            "object": bytes(uc.mem_read(OBJ_ADDR, OBJ_WATCH)),
            "slot_objects": bytes(
                uc.mem_read(SLOT_OBJ_ADDR, SLOT_OBJ_STRIDE * SLOT_OBJ_COUNT)
            ),
            "vtables": bytes(uc.mem_read(VT_ADDR, VT_STRIDE * SLOT_OBJ_COUNT)),
            "slot_code": bytes(
                uc.mem_read(FN_ADDR, SLOT_FN_STRIDE * SLOT_FN_COUNT)
            ),
        }


# ---------------------------------------------------------------------------
# Independent expected model
# ---------------------------------------------------------------------------
def idivmod(numerator, denominator):
    """__aeabi_idivmod: quotient in r0, remainder in r1."""
    n = s32(numerator)
    d = s32(denominator)
    if d == 0:
        # The divisor-zero path of 0x002C615C yields quotient 0xFFFFFFFF and
        # leaves the numerator as remainder; the caller multiplies by 0.
        return 0xFFFFFFFF, u32(numerator)
    quotient = abs(n) // abs(d)
    if (n < 0) != (d < 0):
        quotient = -quotient
    remainder = n - quotient * d
    return u32(quotient), u32(remainder)


def expected_case(case):
    """Return (call_log, return_value, final_state, [counter0, counter1])."""
    log = []
    state = u32(case["state"])
    counters = [u32(case["counters"][0]), u32(case["counters"][1])]

    remaining = s32(case["anim_end"] - case["anim_pos"])
    log.append(("func_0023a774", OBJ_ADDR + OFF_ANIM, remaining))
    if remaining != 0:
        log.append(("engine_func_0023a690", OBJ_ADDR + OFF_ANIM))
        if case["anim_ok"] == 0:
            state = 7
        log.append(("camp_func_00351040", OBJ_ADDR))

    if state not in (3, 6):
        return log, 0, state, counters

    if state != 1:
        if state == 6:
            log.append(("nn_sdk_func_002c4244", OBJ_ADDR + OFF_SYNC))
        log.append(("lock", OBJ_ADDR, state))
        state = 2
        log.append(("unlock", OBJ_ADDR, state))

    script = case["sleep_script"]
    sleeps = 0
    while state not in (1, 7, 8):
        log.append(("AsdThread_Sleep", SLEEP_INTERVAL, 0))
        if script:
            state = script[min(sleeps, len(script) - 1)]
        sleeps += 1
        if sleeps > MAX_SLEEPS:
            raise AssertionError("expected model wait loop did not terminate")

    indices = [case["indices"][0], case["indices"][1]]
    for slot in (0, 1):
        index = s32(indices[slot])
        if index < 0:
            continue
        granularity = 0
        if s32(case["limit"]) > index:
            mode = case["modes"][index]
            granularity = 2 if (mode == 0 or mode == 1) else 1
        self_ptr = SLOT_OBJ_ADDR + index * SLOT_OBJ_STRIDE
        value = case["slot_values"].get(index, 0)
        log.append(("slot_read", index, self_ptr, value))
        log.append(("ui_func_002c615c", s32(value), granularity))
        quotient, _remainder = idivmod(value, granularity)
        frames = s32(quotient * granularity)
        for _frame in range(frames if frames > 0 else 0):
            current = s32(indices[slot])
            log.append(
                ("slot_advance", current, SLOT_OBJ_ADDR + current * SLOT_OBJ_STRIDE)
            )
            mutation = case["advance_writes_index"]
            if mutation is not None and mutation[0] == current and mutation[1] == slot:
                indices[slot] = u32(mutation[2])
            counters[slot] = u32(counters[slot] + 1)

    return log, 1, state, counters


def make_case(name, state=3, **kwargs):
    case = {
        "name": name,
        "state": u32(state),
        "anim_end": 0,
        "anim_pos": 0,
        "anim_ok": 1,
        "limit": 8,
        "modes": [2, 2, 2, 2, 2, 2, 2, 2],
        "indices": (-1, -1),
        "counters": (0, 0),
        "slot_values": {},
        "sleep_script": [8],
        "advance_writes_index": None,
    }
    case.update(kwargs)
    return case


def build_cases():
    return [
        make_case("state 0 -> early return", state=0),
        make_case("state 1 -> early return", state=1),
        make_case("state 2 -> early return", state=2),
        make_case("state 7 -> early return", state=7),
        make_case("state 8 -> early return", state=8),
        make_case("state 0xffffffff -> early return", state=0xFFFFFFFF),
        make_case("state 0x7fffffff -> early return", state=0x7FFFFFFF),
        make_case("state 3, no animation, exit state 8", state=3),
        make_case("state 6, no animation, exit state 1", state=6, sleep_script=[1]),
        make_case(
            "state 6, no animation, exit state 7", state=6, sleep_script=[7]
        ),
        make_case(
            "state 3, remaining +5, complete -> finalize, exit 8",
            state=3,
            anim_end=5,
            anim_pos=0,
        ),
        make_case(
            "state 3, remaining -3, complete -> finalize, exit 8",
            state=3,
            anim_end=0,
            anim_pos=3,
        ),
        make_case(
            "state 3, remaining +1 (boundary), incomplete -> state 7",
            state=3,
            anim_end=1,
            anim_pos=0,
            anim_ok=0,
        ),
        make_case(
            "state 6, remaining +5, incomplete -> state 7",
            state=6,
            anim_end=5,
            anim_pos=0,
            anim_ok=0,
        ),
        make_case(
            "state 0, remaining +5, complete -> finalize then early return",
            state=0,
            anim_end=5,
            anim_ok=1,
        ),
        make_case(
            "wait loop: three sleeps before state 8",
            state=3,
            sleep_script=[2, 2, 8],
        ),
        make_case(
            "wait loop: two sleeps then state 7",
            state=3,
            sleep_script=[2, 7],
        ),
        make_case(
            "slot 0 mode 0, value 3, factor 2 -> two frames",
            state=3,
            indices=(0, -1),
            modes=[0, 2, 2, 2, 2, 2, 2, 2],
            slot_values={0: 3},
        ),
        make_case(
            "slot 0 mode 1, value 4, factor 2 -> four frames",
            state=3,
            indices=(0, -1),
            modes=[1, 2, 2, 2, 2, 2, 2, 2],
            slot_values={0: 4},
        ),
        make_case(
            "slot 0 mode 2, value 3, factor 1 -> three frames",
            state=3,
            indices=(0, -1),
            modes=[2, 2, 2, 2, 2, 2, 2, 2],
            slot_values={0: 3},
        ),
        make_case(
            "slot 0 index at limit-1 (2)",
            state=3,
            limit=3,
            indices=(2, -1),
            modes=[2, 2, 0, 2, 2, 2, 2, 2],
            slot_values={2: 2},
        ),
        make_case(
            "slot 0 index at limit (2 == 2) -> zero granularity",
            state=3,
            limit=2,
            indices=(2, -1),
            modes=[2, 2, 0, 2, 2, 2, 2, 2],
            slot_values={2: 7},
        ),
        make_case(
            "slot 0 index above limit with limit -1 (signed compare)",
            state=3,
            limit=-1,
            indices=(0, -1),
            slot_values={0: 7},
        ),
        make_case(
            "slot 0 index -1 -> skipped",
            state=3,
            indices=(-1, 0),
            slot_values={0: 3},
            counters=(0x100, 0x200),
        ),
        make_case(
            "slot 0 index 0x80000000 -> skipped",
            state=3,
            indices=(0x80000000, -1),
        ),
        make_case(
            "both slots active",
            state=3,
            indices=(0, 1),
            modes=[0, 2, 2, 2, 2, 2, 2, 2],
            slot_values={0: 3, 1: 2},
            counters=(0x10, 0x20),
        ),
        make_case(
            "counter wrap at 0xffffffff",
            state=3,
            indices=(0, -1),
            modes=[2, 2, 2, 2, 2, 2, 2, 2],
            slot_values={0: 3},
            counters=(0xFFFFFFFF, 0),
        ),
        make_case(
            "value 0x80000000, factor 2 -> negative frame count",
            state=3,
            indices=(0, -1),
            modes=[0, 2, 2, 2, 2, 2, 2, 2],
            slot_values={0: 0x80000000},
            counters=(5, 6),
        ),
        make_case(
            "value 0xfffffffb, factor 1 -> negative frame count",
            state=3,
            indices=(0, -1),
            modes=[2, 2, 2, 2, 2, 2, 2, 2],
            slot_values={0: 0xFFFFFFFB},
        ),
        make_case(
            "value 0 (empty read) -> no frames",
            state=3,
            indices=(0, 1),
            modes=[0, 0, 2, 2, 2, 2, 2, 2],
            slot_values={},
        ),
        make_case(
            "advance reloads the slot index (0 -> 2)",
            state=3,
            indices=(0, -1),
            modes=[2, 2, 0, 2, 2, 2, 2, 2],
            slot_values={0: 2, 2: 2},
            advance_writes_index=(0, 0, 2),
        ),
        make_case(
            "slot 0 index 7 at limit 8",
            state=3,
            limit=8,
            indices=(7, -1),
            modes=[2, 2, 2, 2, 2, 2, 2, 2],
            slot_values={7: 1},
        ),
    ]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def check_expectations(case, result):
    log, ret, state, counters = expected_case(case)
    assert result["call_log"] == log, (
        f"expected call log mismatch on {case['name']}:\n"
        f"  Expected: {log}\n  Actual:   {result['call_log']}"
    )
    assert result["r0"] == ret, (
        f"return mismatch on {case['name']}: "
        f"0x{result['r0']:08x} != 0x{ret:08x}"
    )
    actual_state = struct.unpack_from("<I", result["object"], OFF_STATE)[0]
    assert actual_state == state, (
        f"state mismatch on {case['name']}: "
        f"0x{actual_state:08x} != 0x{state:08x}"
    )
    for slot in (0, 1):
        actual = struct.unpack_from(
            "<I", result["object"], OFF_COUNTER + slot * 4
        )[0]
        assert actual == counters[slot], (
            f"counter {slot} mismatch on {case['name']}: "
            f"0x{actual:08x} != 0x{counters[slot]:08x}"
        )


def main():
    print("Testing engine_func_0034fc14 (0x0034fc14)...")
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
        assert res_orig["object"] == res_cand["object"], (
            f"object memory mismatch on {case['name']}"
        )
        assert res_orig["slot_objects"] == res_cand["slot_objects"], (
            f"slot object memory mismatch on {case['name']}"
        )
        assert res_orig["vtables"] == res_cand["vtables"], (
            f"vtable memory mismatch on {case['name']}"
        )
        assert res_orig["slot_code"] == res_cand["slot_code"], (
            f"stub memory mismatch on {case['name']}"
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
        check_expectations(case, res_cand)

        passed += 1
        print(f"  [PASS] {case['name']}")

    print("\nNegative controls:")
    mutants = [
        (
            "granularity_inverted",
            "(mode == 0u || mode == 1u) ? 2 : 1;",
            "(mode == 0u || mode == 1u) ? 1 : 2;",
        ),
        (
            "limit_unsigned_compare",
            "if (obj->entry_limit_2e8 > index) {",
            "if (static_cast<u32>(obj->entry_limit_2e8) >"
            " static_cast<u32>(index)) {",
        ),
        (
            "index_boundary_includes_zero",
            "if (index < 0) {",
            "if (index <= 0) {",
        ),
        (
            "state_filter_accepts_7",
            "if (obj->state_0c != 3 && obj->state_0c != 6) {",
            "if (obj->state_0c != 3 && obj->state_0c != 7) {",
        ),
        (
            "transition_state_wrong",
            "obj->state_0c = 2;",
            "obj->state_0c = 3;",
        ),
        (
            "counter_always_slot_zero",
            "++obj->slot_counter_47c[slot];",
            "++obj->slot_counter_47c[0];",
        ),
        (
            "index_not_reloaded",
            "const s32 current = obj->slot_index_46c[slot];",
            "const s32 current = index;",
        ),
        (
            "frame_loop_inclusive",
            "for (s32 frame = 0; frame < frames; ++frame) {",
            "for (s32 frame = 0; frame <= frames; ++frame) {",
        ),
        (
            "animation_failure_state_wrong",
            "obj->state_0c = 7;",
            "obj->state_0c = 8;",
        ),
        (
            "sleep_argument_wrong",
            "AsdThread_Sleep(0x0007A120, 0);",
            "AsdThread_Sleep(0x0007A120, 1);",
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
