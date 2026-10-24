#!/usr/bin/env python3
"""Trace a synthetic early-return path through the original title mutator."""
from __future__ import annotations

import hashlib
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.semantic_experiment import (  # noqa: E402
    DATA, DATA_SIZE, STACK, STACK_SIZE, SP, TEXT, Runner, arm, unicorn,
)
from tools.tbb_semantic_experiment import TITLE_TBB_SLOT_BASE, TITLE_TBB_SLOT_ID  # noqa: E402
from tools.title_help_presentation_experiment import (  # noqa: E402
    EXPECTED_HELP, extract_help_entries, verify_reference,
)

START = 0x001E9FD4
MUTATOR = 0x001EA070
HELP = 0x001EA12C
PRESENTATION_STOP = 0x001EA15C
PRESENTATION_CALLEE = 0x0029F10C
TBB_GLOBAL = 0x002C0EC4
TBB_SUBTABLE = 0x002AC2F4
TBB_PAYLOAD = 0x002C0E9C
READY_VISIBLE = 0x0025A274
READY_SECOND = 0x002D569C
FADE_A = 0x002872A4
FADE_A_BODY = 0x002872B0
FADE_B = 0x0020FFA0
FADE_B_BODY = 0x0020FFAC
CODE_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"

WORK, HANDLE_A, HANDLE_B = 0x100, 0x300, 0x340
CHILD_A, CHILD_B = 0x400, 0x600
NESTED_A, NESTED_B = 0x800, 0xA00
TBB_CONTAINER_OFFSET = 0x1000


def put32(data: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<I", data, offset, value & 0xFFFFFFFF)


def initial_memory() -> bytes:
    data = bytearray([0xCD]) * DATA_SIZE
    # Both readiness callees return 1 through their signed <= 0 early exits.
    # Thus the outer gates are positive while both children remain minimal.
    put32(data, WORK + 0x8C, DATA + HANDLE_A)
    put32(data, WORK + 0x90, DATA + HANDLE_B)
    put32(data, WORK + 8, 0)
    data[WORK + 0x94] = 0
    put32(data, HANDLE_A, 4)  # Skip conditional 0x29bdb4 call on resource A.
    put32(data, HANDLE_B, 0)  # Skip conditional 0x29bdb4 call on resource B.
    put32(data, HANDLE_A + 8, DATA + CHILD_A)
    put32(data, HANDLE_B + 8, DATA + CHILD_B)
    for child, nested in ((CHILD_A, NESTED_A), (CHILD_B, NESTED_B)):
        put32(data, child + 0x34, 0)
        put32(data, child + 0x58, 0)
        put32(data, child + 0x2C, DATA + nested)
    return bytes(data)


def run_mutator(image: bytes, raw_tbb: bytes) -> dict:
    if hashlib.sha256(image).hexdigest() != CODE_SHA256:
        raise ValueError("code.bin is not the pinned US reference image")
    verify_reference(image)
    runner = Runner(image, START)
    uc = runner.uc
    if len(raw_tbb) > 0x1000:
        raise ValueError("TitleTable.tbb does not fit the additional experiment page")
    uc.mem_map(DATA + 0x1000, 0x1000,
               unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
    table_pointer_address = (TITLE_TBB_SLOT_BASE + TITLE_TBB_SLOT_ID * 0x10 + 4)
    uc.mem_protect(table_pointer_address & ~0xFFF, 0x1000,
                   unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
    uc.mem_write(table_pointer_address,
                 struct.pack("<I", DATA + TBB_CONTAINER_OFFSET))
    uc.mem_write(DATA + TBB_CONTAINER_OFFSET, raw_tbb)
    trace: list[int] = []
    reads: list[dict] = []
    writes: list[dict] = []
    calls: list[dict] = []
    stopped = {"at_help": False, "presentation_args": None}

    def code_hook(machine, address, _size, _user):
        trace.append(address)
        if address in (READY_VISIBLE, READY_SECOND, FADE_A, FADE_B,
                       TBB_GLOBAL, TBB_SUBTABLE, TBB_PAYLOAD):
            calls.append({"target": hex(address),
                          "r0": hex(machine.reg_read(arm.UC_ARM_REG_R0)),
                          "lr": hex(machine.reg_read(arm.UC_ARM_REG_LR))})
        if address in (FADE_A_BODY, FADE_B_BODY):
            raise AssertionError(f"early-return helper unexpectedly entered body {address:#x}")
        if address == PRESENTATION_STOP:
            stopped["at_help"] = True
            stopped["presentation_args"] = {
                "r0": hex(machine.reg_read(arm.UC_ARM_REG_R0)),
                "r1": hex(machine.reg_read(arm.UC_ARM_REG_R1)),
                "lr": hex(machine.reg_read(arm.UC_ARM_REG_LR)),
            }
            machine.emu_stop()

    def memory_hook(machine, access, address, size, value, _user):
        pc = machine.reg_read(arm.UC_ARM_REG_PC)
        if access == unicorn.UC_MEM_READ:
            reads.append({"pc": hex(pc), "address": hex(address), "size": size})
        elif access == unicorn.UC_MEM_WRITE:
            writes.append({"pc": hex(pc), "address": hex(address), "size": size,
                           "value": hex(value & ((1 << (size * 8)) - 1))})

    uc.hook_add(unicorn.UC_HOOK_CODE, code_hook)
    uc.hook_add(unicorn.UC_HOOK_MEM_READ | unicorn.UC_HOOK_MEM_WRITE, memory_hook)
    uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
    registers = [0xA5A50000 | i for i in range(13)]
    registers[4] = DATA + WORK
    registers[5] = DATA + WORK
    registers[7] = 1  # This caller-saved register is the final flag value.
    for i, value in enumerate(registers):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"), value)
    for i in range(8, 16):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_D{i}"), 0)
    uc.reg_write(arm.UC_ARM_REG_S16,
                 struct.unpack("<I", struct.pack("<f", 0.75))[0])
    uc.reg_write(arm.UC_ARM_REG_S17,
                 struct.unpack("<I", struct.pack("<f", 0.25))[0])
    uc.reg_write(arm.UC_ARM_REG_SP, SP)
    uc.reg_write(arm.UC_ARM_REG_LR, PRESENTATION_STOP)
    uc.mem_write(DATA, initial_memory())
    uc.mem_write(STACK, bytes([0xCD]) * STACK_SIZE)
    try:
        uc.emu_start(START, 0, count=4096)
    except unicorn.UcError as exc:
        raise RuntimeError(f"ARM fault at {uc.reg_read(arm.UC_ARM_REG_PC):#x}: {exc}") from exc
    if not stopped["at_help"] or uc.reg_read(arm.UC_ARM_REG_PC) != PRESENTATION_STOP:
        raise RuntimeError(f"did not reach presentation boundary; PC={uc.reg_read(arm.UC_ARM_REG_PC):#x}")

    final = bytes(uc.mem_read(DATA, DATA_SIZE))
    def u32(offset: int) -> int:
        return struct.unpack_from("<I", final, offset)[0]
    def f32(offset: int) -> float:
        return struct.unpack_from("<f", final, offset)[0]
    def u8(offset: int) -> int:
        return final[offset]

    expected_calls = [READY_VISIBLE, READY_SECOND, FADE_A, FADE_B,
                      TBB_GLOBAL, TBB_SUBTABLE, TBB_PAYLOAD]
    if [int(call["target"], 16) for call in calls] != expected_calls:
        raise AssertionError(f"unexpected call order: {calls}")
    if not all(address in trace for address in
               (START, MUTATOR, FADE_A_BODY - 4, FADE_B_BODY - 4, HELP,
                PRESENTATION_STOP)):
        raise AssertionError("continuous original ARM path did not cover required boundaries")
    expected_writes = [
        (0x001EA0B0, DATA + HANDLE_A, 4, 6),
        (0x001EA0BC, DATA + NESTED_A + 0x1F6, 1, 0),
        (0x001EA0C0, DATA + WORK + 0x98, 4, 0x3F400000),
        (0x001EA0EC, DATA + HANDLE_B, 4, 0),
        (0x001EA0F8, DATA + NESTED_B + 0x1F6, 1, 1),
        (0x001EA128, DATA + WORK + 0x94, 1, 1),
    ]
    observed_writes = [(int(row["pc"], 16), int(row["address"], 16),
                        row["size"], int(row["value"], 16)) for row in writes]
    if observed_writes != expected_writes:
        raise AssertionError(f"write sequence differs: {writes}")

    allowed_read_ranges = [
        (DATA + WORK, DATA + WORK + 0x9C),
        (DATA + HANDLE_A, DATA + HANDLE_A + 0x0C),
        (DATA + HANDLE_B, DATA + HANDLE_B + 0x0C),
        (DATA + CHILD_A, DATA + CHILD_A + 0x5C),
        (DATA + CHILD_B, DATA + CHILD_B + 0x5C),
        (DATA + NESTED_A, DATA + NESTED_A + 0x1F7),
        (DATA + NESTED_B, DATA + NESTED_B + 0x1F7),
        (DATA + TBB_CONTAINER_OFFSET, DATA + TBB_CONTAINER_OFFSET + len(raw_tbb)),
        (table_pointer_address, table_pointer_address + 4),
    ]
    code_literal_reads = {0x001E9EC4, 0x002C0EDC, 0x002AC348,
                          0x002AC34C, 0x002C0EC0}
    escaped_reads = [row for row in reads
                     if int(row["address"], 16) not in code_literal_reads
                     and not any(start <= int(row["address"], 16)
                                 and int(row["address"], 16) + row["size"] <= end
                                 for start, end in allowed_read_ranges)]
    if escaped_reads:
        raise AssertionError(f"read outside explicit synthetic graph/TBB/literals: {escaped_reads}")
    if u32(HANDLE_A) != 6 or u32(HANDLE_B) != 0 or u8(WORK + 0x94) != 1:
        raise AssertionError("final transition flags do not match the original stores")
    if f32(WORK + 0x98) != 0.75:
        raise AssertionError("S16 did not propagate to work+0x98")
    table = extract_help_entries(raw_tbb)
    entry = table["entries"][0]
    expected_pointer = (DATA + TBB_CONTAINER_OFFSET + table["payload_file_offset"] +
                        entry["relative_payload_offset"])
    args = stopped["presentation_args"]
    if int(args["r0"], 16) != expected_pointer or int(args["r1"], 16) != 0x323232FF:
        raise AssertionError(f"unexpected help caller arguments: {args}")
    if entry["text"] != EXPECTED_HELP[0] or PRESENTATION_CALLEE in trace:
        raise AssertionError("help text differs or presentation callee was entered")

    return {
        "passed": True,
        "evidence_type": "continuous pinned original ARM through the title mutator and real TBB help caller on a synthetic early-return path",
        "code_sha256": CODE_SHA256,
        "start": hex(START), "mutator": hex(MUTATOR),
        "help_entry": hex(HELP), "stop_before_presentation": hex(PRESENTATION_STOP),
        "presentation_callee_not_entered": hex(PRESENTATION_CALLEE),
        "tbb_sha256": hashlib.sha256(raw_tbb).hexdigest(),
        "reached": {"readiness_visible": READY_VISIBLE in trace,
                    "readiness_second": READY_SECOND in trace,
                    "mutator": MUTATOR in trace,
                    "fade_a_entry_early_return": FADE_A in trace and FADE_A_BODY not in trace,
                    "fade_b_entry_early_return": FADE_B in trace and FADE_B_BODY not in trace,
                    "help_boundary": HELP in trace},
        "call_entries": calls,
        "pre_presentation_call_args": args,
        "help_text": entry["text"],
        "executed_pc_count": len(trace),
        "read_count": len(reads), "reads": reads,
        "write_count": len(writes), "writes": writes,
        "final_state": {"handle_a_flags": u32(HANDLE_A),
                        "handle_b_flags": u32(HANDLE_B),
                        "work_0x94": u8(WORK + 0x94),
                        "work_0x98": f32(WORK + 0x98),
                        "nested_a_0x1f6": u8(NESTED_A + 0x1F6),
                        "nested_b_0x1f6": u8(NESTED_B + 0x1F6)},
        "limits": [
            "Synthetic object graph, work+0x94=0, and finite S16/S17 values; not captured from Azahar or claimed runtime-normal.",
            "Both readiness functions return nonzero through signed-field <=0 early exits; both transition fade helpers also return early.",
            "The two conditional 0x0029BDB4 calls are skipped by explicit handle bit-4 setup; no indirect callback is reached on this path.",
            "All exercised instructions are original ARM through the real TBB getters; execution stops before Camp_SetSlotMessage and does not verify rendered UI.",
        ],
    }
