#!/usr/bin/env python3
"""Verify the production H1 main-menu State-5 slice integration in src/ui/ui_runtime2.cpp.

This runner compiles the actual production translation unit `src/ui/ui_runtime2.cpp`
(plus `src/ui/tbb_loader.cpp` and the reviewed `h1_alpha_candidates.cpp` /
`h1_type1_callback_candidate.cpp`), links the compiled `ui_func_001e989c` and
`H1_TitleMain_UpdateNavigationSlice` symbols, and runs:

1. The full 258-case State-5 navigation/continuation differential matrix
   (256 cursor x cached x trigger-mask combinations + 2 false readiness gates),
   plus the adversarial post-capture global-pointer mutation case and the
   wrong-signed-modulo negative control, comparing original `code.bin`
   `ui_func_001e989c` against the production-integrated `ui_func_001e989c` +
   `H1_TitleMain_UpdateNavigationSlice`.
2. The State-5 transition/fade/help-lookup composition (`0x001E9FD4..0x001EA15C`)
   consuming:
   - the observed runtime callback binding (`0x00151404` on `child_b`, duration
     `1200.0f` = `0x44960000`, `callback_arg = 0x00000000`) from `h1-track-runtime`,
   - the reviewed alpha helper candidate (`0x0029BDB4`) from `h1-alpha-caller-review`,
   - the promoted production TBB accessors (`Tbb_GetSubTable` `0x002AC2F4` and
     `Tbb_GetPayloadData` `0x002C0E9C`) from `h1-tbb-promotion` with the real
     `TitleTable.tbb` asset across all four menu selections `0..3`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import capstone
from tools import h1_navigation_adapter_experiment as nav_base
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, find_clang, get_armv6k_flags
from tools.semantic_experiment import (
    DATA, DATA_SIZE, INJECT, RETURN, SP, STACK, STACK_SIZE, TEXT, Runner, arm,
    arm_branch, unicorn,
)
from tools.tbb_semantic_experiment import TITLE_TBB_SLOT_BASE, TITLE_TBB_SLOT_ID
from tools.title_help_presentation_experiment import EXPECTED_HELP, extract_help_entries
from tools.title_transition_positive_gate_experiment import (
    CHILD_A, CHILD_B, FADE_A, FADE_A_CONTINUATION, FADE_B, HANDLE_A, HANDLE_B,
    NESTED_A, NESTED_B, READY_SECOND, READY_VISIBLE, START as TRANSITION_START,
    STOP as PRESENTATION_STOP, TBB_CONTAINER_OFFSET, TBB_GLOBAL, TBB_PAYLOAD,
    TBB_SUBTABLE, WORK as TRANSITION_WORK, initial_memory,
)

CODE_PATH = ROOT / "extracted/exefs/code.bin"
TBB_PATH = ROOT / "build/semantic-equivalence/real-assets/romfs/title/TitleTable.tbb"
UI_RUNTIME2_CPP = ROOT / "src/ui/ui_runtime2.cpp"
TITLE_FLOW_H = ROOT / "include/camp/title_flow.h"
TBB_LOADER_CPP = ROOT / "src/ui/tbb_loader.cpp"
ALPHA_CANDIDATE_CPP = ROOT / "experiments/semantic_equivalence/h1_alpha_candidates.cpp"
TYPE1_CALLBACK_CPP = ROOT / "experiments/semantic_equivalence/h1_type1_callback_candidate.cpp"

EXPECTED_CODE_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
EXPECTED_TBB_SHA256 = "edd6bc1de5388e5689f797861ae6947c7c339f9b6bdb63d6c35951d72020fa41"

CALLBACK_ADDR = 0x001E989C
CALLBACK_SIZE = 3924
STATE5_ENTRY = 0x001E9D08
STATE5_BL_ADDR = 0x001E9D10
STATE5_CONTINUE = 0x001E9DE0
STATE5_GATE_EXIT = 0x001EA62C
STATE5_TOUCH_STOP = 0x001E9E50

SLICE_HELPER_ADDR = INJECT + 0x2000
CONFIRM_HELPER_ADDR = INJECT + 0x3000
STATE5_CONFIRM_BL_ADDR = 0x001EA164
STATE5_CONFIRM_ENTRY = 0x001EA160
STATE5_CONFIRM_END = 0x001EA32C
ALPHA_HELPER_ADDR = 0x0029BDB4
ALPHA_CANDIDATE_INJECT = INJECT + 0x0200
TBB_SUBTABLE_INJECT = INJECT + 0x0400
TBB_PAYLOAD_INJECT = INJECT + 0x0600
OBSERVED_TRACK_CALLBACK = 0x00151404
TYPE1_CANDIDATE_INJECT = INJECT + 0x0800

TRIGGER_IDS = nav_base.TRIGGER_IDS
MASK_BIT_FOR_TRIGGER = {logical_id: index for index, logical_id in enumerate(TRIGGER_IDS)}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encode_bl(source: int, target: int) -> bytes:
    displacement = target - (source + 8)
    if displacement & 3 or not -(1 << 25) <= displacement < (1 << 25):
        raise ValueError(f"ARM BL out of range: {source:#x} -> {target:#x}")
    word = 0xEB000000 | ((displacement >> 2) & 0xFFFFFF)
    return struct.pack("<I", word)


def compile_production_symbols(output_dir: Path) -> tuple[dict[str, bytes], dict]:
    build_dir = output_dir / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    clang = find_clang()
    flags = get_armv6k_flags(ROOT, clang)

    ui_obj = build_dir / "ui_runtime2.o"
    ui_res = compile_tu_armv6k(UI_RUNTIME2_CPP, ui_obj, ROOT)
    if ui_res.returncode != 0:
        raise RuntimeError(ui_res.stderr or "Failed to compile src/ui/ui_runtime2.cpp")
    ui_funcs = extract_elf_functions_detailed(ui_obj)

    callback_sym = "_ZN4smt42ui16ui_func_001e989cEPv"
    slice_sym = "H1_TitleMain_UpdateNavigationSlice"
    confirm_sym = "H1_TitleMain_ProcessConfirmationSlice"
    if callback_sym not in ui_funcs or slice_sym not in ui_funcs or confirm_sym not in ui_funcs:
        raise ValueError(f"Missing expected symbols in {ui_obj}")

    callback_raw, callback_relocs = ui_funcs[callback_sym]
    slice_code, slice_relocs = ui_funcs[slice_sym]
    confirm_code, confirm_relocs = ui_funcs[confirm_sym]
    if len(callback_raw) != CALLBACK_SIZE:
        raise ValueError(f"ui_func_001e989c size {len(callback_raw)} != {CALLBACK_SIZE}")
    if slice_relocs:
        raise ValueError(f"Unexpected relocations in {slice_sym}: {slice_relocs}")

    # Link relocations in ui_func_001e989c
    callback_linked = bytearray(callback_raw)
    for reloc in callback_relocs:
        if reloc.symbol_name == slice_sym:
            callback_linked[reloc.offset:reloc.offset + 4] = encode_bl(
                CALLBACK_ADDR + reloc.offset, SLICE_HELPER_ADDR
            )
        elif reloc.symbol_name == confirm_sym:
            callback_linked[reloc.offset:reloc.offset + 4] = encode_bl(
                CALLBACK_ADDR + reloc.offset, CONFIRM_HELPER_ADDR
            )

    tbb_obj = build_dir / "tbb_loader.o"
    tbb_res = compile_tu_armv6k(TBB_LOADER_CPP, tbb_obj, ROOT)
    if tbb_res.returncode != 0:
        raise RuntimeError(tbb_res.stderr or "Failed to compile src/ui/tbb_loader.cpp")
    tbb_funcs = extract_elf_functions_detailed(tbb_obj)
    subtable_sym = "_ZN4smt42ui15Tbb_GetSubTableEPKNS0_10TbcrHeaderEj"
    payload_sym = "_ZN4smt42ui18Tbb_GetPayloadDataEPKNS0_10Tbl1HeaderE"
    subtable_code, subtable_relocs = tbb_funcs[subtable_sym]
    payload_code, payload_relocs = tbb_funcs[payload_sym]
    if subtable_relocs or payload_relocs:
        raise ValueError("Unexpected relocations in TBB production symbols")

    alpha_obj = build_dir / "h1_alpha_candidates.o"
    alpha_res = compile_tu_armv6k(ALPHA_CANDIDATE_CPP, alpha_obj, ROOT)
    if alpha_res.returncode != 0:
        raise RuntimeError(alpha_res.stderr or "Failed to compile h1_alpha_candidates.cpp")
    alpha_funcs = extract_elf_functions_detailed(alpha_obj)
    alpha_code, alpha_relocs = alpha_funcs["candidate_0029bdb4"]
    if alpha_relocs:
        raise ValueError(f"Unexpected relocations in candidate_0029bdb4: {alpha_relocs}")

    type1_obj = build_dir / "h1_type1_callback_candidate.o"
    type1_res = compile_tu_armv6k(TYPE1_CALLBACK_CPP, type1_obj, ROOT)
    if type1_res.returncode != 0:
        raise RuntimeError(type1_res.stderr or "Failed to compile h1_type1_callback_candidate.cpp")
    type1_funcs = extract_elf_functions_detailed(type1_obj)
    type1_code, type1_relocs = type1_funcs["candidate_00151404"]
    if type1_relocs:
        raise ValueError(f"Unexpected relocations in candidate_00151404: {type1_relocs}")

    blobs = {
        "ui_func_001e989c_linked": bytes(callback_linked),
        "ui_func_001e989c_raw": callback_raw,
        "H1_TitleMain_UpdateNavigationSlice": slice_code,
        "H1_TitleMain_ProcessConfirmationSlice": confirm_code,
        "Tbb_GetSubTable": subtable_code,
        "Tbb_GetPayloadData": payload_code,
        "candidate_0029bdb4": alpha_code,
        "candidate_00151404": type1_code,
    }
    meta = {
        "clang": str(clang),
        "flags": flags,
        "ui_runtime2": {
            "source_path": str(UI_RUNTIME2_CPP.relative_to(ROOT)),
            "source_sha256": sha256_bytes(UI_RUNTIME2_CPP.read_bytes()),
            "header_path": str(TITLE_FLOW_H.relative_to(ROOT)),
            "header_sha256": sha256_bytes(TITLE_FLOW_H.read_bytes()),
            "object_path": str(ui_obj.resolve()),
            "object_sha256": sha256_bytes(ui_obj.read_bytes()),
            "callback_size": len(callback_raw),
            "callback_relocation": {
                "offset": reloc.offset,
                "address": hex(CALLBACK_ADDR + reloc.offset),
                "type": reloc.relocation_type,
                "symbol": reloc.symbol_name,
            },
            "slice_helper_size": len(slice_code),
            "slice_helper_sha256": sha256_bytes(slice_code),
        },
        "tbb_loader": {
            "source_path": str(TBB_LOADER_CPP.relative_to(ROOT)),
            "source_sha256": sha256_bytes(TBB_LOADER_CPP.read_bytes()),
            "object_path": str(tbb_obj.resolve()),
            "object_sha256": sha256_bytes(tbb_obj.read_bytes()),
            "subtable_size": len(subtable_code),
            "subtable_sha256": sha256_bytes(subtable_code),
            "payload_size": len(payload_code),
            "payload_sha256": sha256_bytes(payload_code),
        },
        "alpha_helper": {
            "source_path": str(ALPHA_CANDIDATE_CPP.relative_to(ROOT)),
            "source_sha256": sha256_bytes(ALPHA_CANDIDATE_CPP.read_bytes()),
            "object_sha256": sha256_bytes(alpha_obj.read_bytes()),
            "size": len(alpha_code),
            "sha256": sha256_bytes(alpha_code),
        },
        "type1_callback": {
            "source_path": str(TYPE1_CALLBACK_CPP.relative_to(ROOT)),
            "source_sha256": sha256_bytes(TYPE1_CALLBACK_CPP.read_bytes()),
            "object_sha256": sha256_bytes(type1_obj.read_bytes()),
            "size": len(type1_code),
            "sha256": sha256_bytes(type1_code),
        },
    }
    return blobs, meta


def compile_wrong_normalizer_mutant(output_dir: Path) -> tuple[bytes, dict]:
    mutant_dir = output_dir / "negative-control"
    mutant_dir.mkdir(parents=True, exist_ok=True)
    src_text = UI_RUNTIME2_CPP.read_text(encoding="utf-8")
    anchor = "return adjusted - multiple;"
    if src_text.count(anchor) != 1:
        raise ValueError("Expected exactly one NormalizeSignedRemainderByFour return anchor")
    mutant_cpp = mutant_dir / "ui_runtime2_wrong_modulo.cpp"
    mutant_cpp.write_text(
        src_text.replace(
            anchor,
            "return static_cast<u32>(static_cast<s32>(provisional) % 4);",
        ),
        encoding="utf-8",
    )
    # Fix relative include "../camp/title_message.h" when compiling from mutant_dir
    fixed_text = mutant_cpp.read_text(encoding="utf-8").replace(
        '#include "../camp/title_message.h"',
        f'#include "{(ROOT / "src/camp/title_message.h").as_posix()}"',
    )
    mutant_cpp.write_text(fixed_text, encoding="utf-8")
    mutant_obj = mutant_dir / "ui_runtime2_wrong_modulo.o"
    res = compile_tu_armv6k(mutant_cpp, mutant_obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(res.stderr or "Failed to compile mutant ui_runtime2.cpp")
    funcs = extract_elf_functions_detailed(mutant_obj)
    code, relocs = funcs["H1_TitleMain_UpdateNavigationSlice"]
    if relocs:
        raise ValueError(f"Unexpected relocations in mutant slice: {relocs}")
    return code, {
        "source_sha256": sha256_bytes(mutant_cpp.read_bytes()),
        "object_sha256": sha256_bytes(mutant_obj.read_bytes()),
        "slice_sha256": sha256_bytes(code),
        "size": len(code),
    }


def make_production_machine(image: bytes, blobs: dict[str, bytes], *, patched: bool,
                            slice_override: bytes | None = None) -> nav_base.AdapterMachine:
    shim_blobs = {
        nav_base.SHIM_VARIANTS["good"]: blobs["H1_TitleMain_UpdateNavigationSlice"],
        "h1_navigation_adapter_candidate": slice_override or blobs["H1_TitleMain_UpdateNavigationSlice"],
    }
    machine = nav_base.AdapterMachine(image, shim_blobs, "good")
    if patched:
        # Install the entire 3,924-byte compiled production ui_func_001e989c at 0x001E989C
        # and the compiled H1_TitleMain_UpdateNavigationSlice at SLICE_HELPER_ADDR.
        machine.uc.mem_write(CALLBACK_ADDR, blobs["ui_func_001e989c_linked"])
        machine.uc.mem_write(
            SLICE_HELPER_ADDR,
            slice_override or blobs["H1_TitleMain_UpdateNavigationSlice"],
        )
        if "H1_TitleMain_ProcessConfirmationSlice" in blobs:
            machine.uc.mem_write(
                CONFIRM_HELPER_ADDR,
                blobs["H1_TitleMain_ProcessConfirmationSlice"],
            )
    return machine


def run_full_callback_state5(machine: nav_base.AdapterMachine, cursor: int, cached: int,
                             ready=(1, 1), responses=None, *, patched: bool,
                             mutate_global: bool = False, blend: float = 1.5) -> dict:
    """Execute from the function entry 0x001E989C with state_9C = 5."""
    initial = machine.initialize(
        cursor, cached, ready, responses, mutate_global=mutate_global, blend=blend
    )
    # Set state_9C (+0x9C) = 5 so the jump table at 0x001E98C4 dispatches to 0x001E9D08.
    nav_base.write_u32(machine.uc, nav_base.WORK + 0x9C, 5)
    nav_base.write_u32(machine.uc, nav_base.MUTATED_WORK + 0x9C, 5)
    initial_work = bytes(machine.uc.mem_read(nav_base.WORK, nav_base.WORK_SIZE))
    initial_mutated = bytes(machine.uc.mem_read(nav_base.MUTATED_WORK, nav_base.WORK_SIZE))

    machine.stop_addresses = (STATE5_GATE_EXIT, STATE5_TOUCH_STOP)
    try:
        machine.uc.emu_start(CALLBACK_ADDR, 0, count=5000)
        fault = None
    except machine.unicorn.UcError as error:
        fault = str(error)
    work = bytes(machine.uc.mem_read(nav_base.WORK, nav_base.WORK_SIZE))
    mutated_work = bytes(machine.uc.mem_read(nav_base.MUTATED_WORK, nav_base.WORK_SIZE))
    # Restore caller SP (+0x20 from callback prologue) in the snapshot comparison or
    # compare directly at the interior stop with the active callback frame.
    state = machine.snapshot()
    return {
        "fault": fault,
        "mode": "production_patched" if patched else "original",
        "stop": machine.uc.reg_read(machine.arm.UC_ARM_REG_PC),
        "state": state,
        "mailbox": nav_base.WORK if all(ready) else nav_base.read_u32(machine.uc, nav_base.MAILBOX),
        "work_hex": work.hex(),
        "mutated_work_hex": mutated_work.hex(),
        "initial_work_hex": initial_work.hex(),
        "initial_mutated_work_hex": initial_mutated.hex(),
        "work_sha256": sha256_bytes(work),
        "mutated_work_sha256": sha256_bytes(mutated_work),
        "slot": hex(nav_base.read_u32(machine.uc, nav_base.WORK_SLOT)),
        "ready_calls": list(machine.ready_calls),
        "trigger_calls": list(machine.trigger_calls),
        "event_calls": list(machine.event_calls),
        "timeline": list(machine.timeline),
        "hook_error": machine.hook_error,
    }


def run_transition_fade_help_slice(image: bytes, raw_tbb: bytes, blobs: dict[str, bytes],
                                   selection: int, *, patched: bool) -> dict:
    """Run 0x001E9FD4..0x001EA15C with observed runtime callback 0x00151404 (duration 1200.0f),
    reviewed alpha helper 0x0029BDB4, and promoted TBB getters across selections 0..3."""
    runner = Runner(image, TRANSITION_START)
    uc = runner.uc
    uc.mem_map(DATA + 0x1000, 0x1000, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
    slot_ptr = TITLE_TBB_SLOT_BASE + TITLE_TBB_SLOT_ID * 0x10 + 4
    uc.mem_protect(slot_ptr & ~0xFFF, 0x1000, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
    uc.mem_write(slot_ptr, struct.pack("<I", DATA + TBB_CONTAINER_OFFSET))
    uc.mem_write(DATA + TBB_CONTAINER_OFFSET, raw_tbb)

    data = bytearray(initial_memory())
    # Set selection in TitleMainWork (+0x08) and enable both alpha helper calls:
    # Handle A bit 2 clear (0), Handle B bit 2 set (4) initially so after bit 1 is cleared,
    # both 0x001EA098 and 0x001EA124 execute.
    struct.pack_into("<I", data, TRANSITION_WORK + 8, selection)
    struct.pack_into("<I", data, HANDLE_A, 0)
    struct.pack_into("<I", data, HANDLE_B, 4)
    struct.pack_into("<f", data, CHILD_A + 0x78, 0.75)
    struct.pack_into("<f", data, CHILD_B + 0x78, 0.5)
    # Observed runtime binding from h1-track-runtime:
    # callback = 0x00151404, callback_arg = 0x00000000, duration (+0x48) = 1200.0f (0x44960000),
    # start (+0x44) = 0.0f, sample (+0x38/+0x3C) = 300.0f so relative sample is 300.0f / 1200.0f.
    struct.pack_into("<I", data, NESTED_B + 0x4C, OBSERVED_TRACK_CALLBACK)
    struct.pack_into("<I", data, NESTED_B + 0x50, 0)
    struct.pack_into("<f", data, NESTED_B + 0x44, 0.0)
    struct.pack_into("<f", data, NESTED_B + 0x48, 1200.0)

    if patched:
        # Install promoted production TBB accessors + reviewed alpha helper + reviewed type-1 callback.
        uc.mem_write(TBB_SUBTABLE_INJECT, blobs["Tbb_GetSubTable"])
        uc.mem_write(TBB_SUBTABLE, arm_branch(TBB_SUBTABLE, TBB_SUBTABLE_INJECT))
        uc.mem_write(TBB_PAYLOAD_INJECT, blobs["Tbb_GetPayloadData"])
        uc.mem_write(TBB_PAYLOAD, arm_branch(TBB_PAYLOAD, TBB_PAYLOAD_INJECT))
        uc.mem_write(ALPHA_CANDIDATE_INJECT, blobs["candidate_0029bdb4"])
        uc.mem_write(ALPHA_HELPER_ADDR, arm_branch(ALPHA_HELPER_ADDR, ALPHA_CANDIDATE_INJECT))
        uc.mem_write(TYPE1_CANDIDATE_INJECT, blobs["candidate_00151404"])
        uc.mem_write(OBSERVED_TRACK_CALLBACK, arm_branch(OBSERVED_TRACK_CALLBACK, TYPE1_CANDIDATE_INJECT))

    calls: list[str] = []
    stopped = {"reached": False, "r0": 0, "r1": 0}

    def code_hook(machine, address, _size, _user):
        if address in (
            READY_VISIBLE, READY_SECOND, FADE_A, OBSERVED_TRACK_CALLBACK,
            ALPHA_HELPER_ADDR, FADE_B, TBB_GLOBAL, TBB_SUBTABLE, TBB_PAYLOAD,
        ):
            calls.append(hex(address))
        if address == PRESENTATION_STOP:
            stopped["reached"] = True
            stopped["r0"] = machine.reg_read(arm.UC_ARM_REG_R0)
            stopped["r1"] = machine.reg_read(arm.UC_ARM_REG_R1)
            machine.emu_stop()

    uc.hook_add(unicorn.UC_HOOK_CODE, code_hook)
    uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
    for i in range(13):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"), 0xA5A50000 | i)
    uc.reg_write(arm.UC_ARM_REG_R4, DATA + TRANSITION_WORK)
    uc.reg_write(arm.UC_ARM_REG_R5, DATA + TRANSITION_WORK)
    uc.reg_write(arm.UC_ARM_REG_R7, 1)
    for i in range(8, 16):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_D{i}"), 0)
    uc.reg_write(arm.UC_ARM_REG_S16, struct.unpack("<I", struct.pack("<f", 0.75))[0])
    uc.reg_write(arm.UC_ARM_REG_S17, struct.unpack("<I", struct.pack("<f", 0.25))[0])
    uc.reg_write(arm.UC_ARM_REG_SP, SP)
    uc.reg_write(arm.UC_ARM_REG_LR, PRESENTATION_STOP)
    uc.mem_write(DATA, bytes(data))
    uc.mem_write(STACK, bytes([0xCD]) * STACK_SIZE)
    uc.emu_start(TRANSITION_START, 0, count=8192)
    if not stopped["reached"]:
        raise RuntimeError(f"Transition slice did not reach {PRESENTATION_STOP:#x}")

    final = bytes(uc.mem_read(DATA, DATA_SIZE))
    r0 = stopped["r0"]
    help_bytes = bytes(uc.mem_read(r0, 64)).split(b"\x00", 1)[0].decode("ascii")
    return {
        "selection": selection,
        "mode": "patched" if patched else "original",
        "stop_pc": hex(uc.reg_read(arm.UC_ARM_REG_PC)),
        "r0_help_ptr": hex(r0),
        "r1_color": hex(stopped["r1"]),
        "help_text": help_bytes,
        "calls": calls,
        "work_fade_98": struct.unpack_from("<f", final, TRANSITION_WORK + 0x98)[0],
        "work_flag_94": final[TRANSITION_WORK + 0x94],
        "handle_a_flags": struct.unpack_from("<I", final, HANDLE_A)[0],
        "handle_b_flags": struct.unpack_from("<I", final, HANDLE_B)[0],
        "nested_a_alpha_40": struct.unpack_from("<f", final, NESTED_A + 0x40)[0],
        "nested_b_alpha_40": struct.unpack_from("<f", final, NESTED_B + 0x40)[0],
        "data_sha256": sha256_bytes(final),
    }


def run_experiment(output_dir: Path) -> dict:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError(f"Output directory is not fresh: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    image = CODE_PATH.read_bytes()
    raw_tbb = TBB_PATH.read_bytes()
    if sha256_bytes(image) != EXPECTED_CODE_SHA256:
        raise ValueError("Pinned code.bin SHA-256 mismatch")
    if sha256_bytes(raw_tbb) != EXPECTED_TBB_SHA256:
        raise ValueError("Pinned TitleTable.tbb SHA-256 mismatch")

    reference = nav_base.verify_image(image)
    blobs, build_meta = compile_production_symbols(output_dir)

    # Verify byte identity of ui_func_001e989c outside the two State-5 slice windows.
    orig_callback = image[CALLBACK_ADDR - TEXT : CALLBACK_ADDR - TEXT + CALLBACK_SIZE]
    comp_callback = blobs["ui_func_001e989c_raw"]
    # Slice 1: 0x001E9D08..0x001E9DDC (0..1132 identical)
    # Intermediate: 0x001E9DE0..0x001EA160 (1348..2244 identical)
    # Slice 2: 0x001EA160..0x001EA32C (2704..3924 identical)
    if orig_callback[:1132] != comp_callback[:1132]:
        raise ValueError("ui_func_001e989c prefix bytes before 0x001E9D08 changed!")
    if orig_callback[1348:2244] != comp_callback[1348:2244]:
        raise ValueError("ui_func_001e989c intermediate bytes 0x001E9DE0..0x001EA160 changed!")
    if orig_callback[2704:] != comp_callback[2704:]:
        raise ValueError("ui_func_001e989c suffix bytes from 0x001EA32C changed!")

    orig_machine = make_production_machine(image, blobs, patched=False)
    patched_machine = make_production_machine(image, blobs, patched=True)

    gate_rows = []
    for label, ready in (("script_not_ready", (0, 1)), ("preview_not_ready", (1, 0))):
        orig_run = run_full_callback_state5(orig_machine, 1, 0, ready, {}, patched=False)
        patch_run = run_full_callback_state5(patched_machine, 1, 0, ready, {}, patched=True)
        gate_rows.append(nav_base.compare(orig_run, patch_run, label, ready))

    matrix_rows = []
    key_orig_for_control = None
    for cursor in range(4):
        for cached in range(4):
            for mask in range(16):
                responses = {
                    logical_id: int(bool(mask & (1 << bit)))
                    for logical_id, bit in MASK_BIT_FOR_TRIGGER.items()
                }
                orig_run = run_full_callback_state5(
                    orig_machine, cursor, cached, (1, 1), responses, patched=False
                )
                patch_run = run_full_callback_state5(
                    patched_machine, cursor, cached, (1, 1), responses, patched=True
                )
                label = f"cursor{cursor}-cache{cached}-mask{mask:02x}"
                row = nav_base.compare(orig_run, patch_run, label, (1, 1))
                matrix_rows.append(row)
                if cursor == 0 and cached == 0 and mask == 1:
                    key_orig_for_control = orig_run

    # Adversarial global-pointer mutation after readiness capture:
    mut_orig = run_full_callback_state5(
        orig_machine, 1, 0, (1, 1), {6: 1}, patched=False, mutate_global=True
    )
    mut_patch = run_full_callback_state5(
        patched_machine, 1, 0, (1, 1), {6: 1}, patched=True, mutate_global=True
    )
    pointer_mutation_case = nav_base.compare(
        mut_orig, mut_patch, "captured-work-survives-global-slot-mutation", (1, 1)
    )

    # Negative control: wrong signed modulo normalizer in production TU:
    mutant_slice, mutant_meta = compile_wrong_normalizer_mutant(output_dir)
    mutant_machine = make_production_machine(
        image, blobs, patched=True, slice_override=mutant_slice
    )
    mutant_run = run_full_callback_state5(
        mutant_machine, 0, 0, (1, 1), {5: 1}, patched=True
    )
    negative_control_cmp = nav_base.compare(
        key_orig_for_control, mutant_run, "negative-wrong-signed-modulo", (1, 1)
    )
    negative_control = {
        "name": "wrong_raw_signed_remainder_for_minus_one",
        "mutant": mutant_meta,
        "detected": not negative_control_cmp["passed"],
        "comparison": negative_control_cmp,
    }

    # Transition/fade/help-lookup composition across selections 0..3:
    transition_cases = []
    for sel in range(4):
        orig_t = run_transition_fade_help_slice(image, raw_tbb, blobs, sel, patched=False)
        patch_t = run_transition_fade_help_slice(image, raw_tbb, blobs, sel, patched=True)
        matched = (
            orig_t["stop_pc"] == patch_t["stop_pc"]
            and orig_t["r0_help_ptr"] == patch_t["r0_help_ptr"]
            and orig_t["r1_color"] == patch_t["r1_color"] == "0x323232ff"
            and orig_t["help_text"] == patch_t["help_text"] == EXPECTED_HELP[sel]
            and orig_t["calls"] == patch_t["calls"]
            and orig_t["data_sha256"] == patch_t["data_sha256"]
        )
        transition_cases.append({
            "selection": sel,
            "passed": matched,
            "help_text": patch_t["help_text"],
            "expected_help_text": EXPECTED_HELP[sel],
            "r0_help_ptr": patch_t["r0_help_ptr"],
            "r1_color": patch_t["r1_color"],
            "work_fade_98": patch_t["work_fade_98"],
            "work_flag_94": patch_t["work_flag_94"],
            "nested_a_alpha_40": patch_t["nested_a_alpha_40"],
            "nested_b_alpha_40": patch_t["nested_b_alpha_40"],
            "calls": patch_t["calls"],
            "original_data_sha256": orig_t["data_sha256"],
            "patched_data_sha256": patch_t["data_sha256"],
        })

    all_passed = (
        len(matrix_rows) == 256
        and all(r["passed"] for r in gate_rows)
        and all(r["passed"] for r in matrix_rows)
        and pointer_mutation_case["passed"]
        and negative_control["detected"]
        and len(transition_cases) == 4
        and all(c["passed"] for c in transition_cases)
    )

    report = {
        "task_id": "h1-menu-slice-integration",
        "address": hex(CALLBACK_ADDR),
        "slice_window": {
            "entry": hex(STATE5_ENTRY),
            "continuation_ready": hex(STATE5_CONTINUE),
            "continuation_not_ready": hex(STATE5_GATE_EXIT),
            "replaced_words": 54,
            "replaced_bytes": 216,
            "callback_total_bytes": CALLBACK_SIZE,
            "prefix_bytes_identical": True,
            "suffix_bytes_identical": True,
        },
        "passed": all_passed,
        "reference": reference,
        "build": build_meta,
        "navigation_matrix_summary": {
            "gate_false_cases": len(gate_rows),
            "gate_false_passed": sum(bool(r["passed"]) for r in gate_rows),
            "matrix_cases": len(matrix_rows),
            "matrix_passed": sum(bool(r["passed"]) for r in matrix_rows),
            "pointer_mutation_passed": pointer_mutation_case["passed"],
            "negative_control_detected": negative_control["detected"],
        },
        "gate_false_cases": gate_rows,
        "pointer_mutation_case": pointer_mutation_case,
        "negative_control": negative_control,
        "transition_fade_help_cases": transition_cases,
        "matrix_cases": matrix_rows,
    }
    report_path = output_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run_experiment(args.output)
    print(f"H1 menu slice integration {'PASS' if report['passed'] else 'FAIL'}: {args.output / 'report.json'}")
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
