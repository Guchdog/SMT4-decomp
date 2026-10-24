#!/usr/bin/env python3
"""Run the pinned title help-text ARM call window against the real TitleTable."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.inspect_assets import parse_tbb_header
from tools.semantic_experiment import DATA, DATA_SIZE, STACK_SIZE, Case, Runner, arm, unicorn
from tools.tbb_semantic_experiment import TITLE_TBB_SLOT_BASE, TITLE_TBB_SLOT_ID


WINDOW_START = 0x001EA12C
WINDOW_STOP = 0x001EA15C  # stop immediately before Camp_SetSlotMessage(0x0029F10C)
HELP_OFFSET = 0x16
HELP_STRIDE = 0x56
HELP_RGBA = 0x323232FF
EXPECTED_HELP = (
    "Start a new game from the beginning.",
    "Load a saved game and continue playing.",
    "Configure audio settings.",
    "Download additional content.",
)


def verify_reference(image: bytes) -> str:
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(image).hexdigest()
    if len(image) != game["code_bin_size"] or digest != game["code_sha256"]:
        raise ValueError("code.bin does not match the configured pinned revision")
    return digest


def extract_help_entries(raw_tbb: bytes) -> dict:
    parsed = parse_tbb_header(raw_tbb)
    if parsed["table_count"] <= 0:
        raise ValueError("TitleTable.tbb contains no subtable 0")
    table = parsed["tables"][0]
    if table["magic"] != "TBL1":
        raise ValueError("TitleTable subtable 0 is not TBL1")
    if table["payload_size"] < HELP_OFFSET + (len(EXPECTED_HELP) - 1) * HELP_STRIDE + 1:
        raise ValueError("TitleTable subtable 0 is too short for four help entries")
    subtable_offset = table["offset"]
    payload_offset = subtable_offset + 0x10
    entries = []
    for index in range(len(EXPECTED_HELP)):
        relative = HELP_OFFSET + HELP_STRIDE * index
        start = payload_offset + relative
        limit = min(payload_offset + table["payload_size"], start + HELP_STRIDE)
        end = raw_tbb.find(b"\0", start, limit)
        if end < 0:
            raise ValueError(f"Help string {index} is not NUL-terminated within its slot")
        text = raw_tbb[start:end].decode("ascii")
        entries.append({"index": index, "relative_payload_offset": relative,
                        "file_offset": start, "text": text})
    actual = tuple(entry["text"] for entry in entries)
    if actual != EXPECTED_HELP:
        raise ValueError(f"Unexpected title help strings: {actual!r}")
    return {"container_magic": parsed["magic"], "subtable_magic": table["magic"],
            "subtable_index": 0, "subtable_file_offset": subtable_offset,
            "payload_file_offset": payload_offset, "payload_size": table["payload_size"],
            "entries": entries}


def make_case(raw_tbb: bytes, selection: int, seed: int) -> Case:
    if selection not in range(len(EXPECTED_HELP)):
        raise ValueError("Title menu selection must be 0..3")
    if len(raw_tbb) > DATA_SIZE - 0x100:
        raise ValueError("TitleTable.tbb does not fit in the experiment DATA region")
    rng = random.Random(seed ^ selection)
    data = bytearray(rng.randbytes(DATA_SIZE))
    data[0x100:0x100 + len(raw_tbb)] = raw_tbb
    work_offset = 0x800
    struct.pack_into("<I", data, work_offset + 8, selection)
    registers = [rng.getrandbits(32) for _ in range(13)]
    registers[5] = DATA + work_offset  # r5 = title work block
    return Case(f"title-help-selection-{selection}", tuple(registers), bytes(data),
                rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)


def install_title_table_slot(runner: Runner, container_pointer: int) -> None:
    slot_pointer_address = TITLE_TBB_SLOT_BASE + TITLE_TBB_SLOT_ID * 0x10 + 4
    page = slot_pointer_address & ~0xFFF
    runner.uc.mem_protect(page, 0x1000,
                          unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
    runner.uc.mem_write(slot_pointer_address, struct.pack("<I", container_pointer))


def run_presentation_window(code_path: Path, tbb_path: Path, seed: int = 20261024) -> dict:
    image = code_path.read_bytes()
    code_sha256 = verify_reference(image)
    raw_tbb = tbb_path.read_bytes()
    asset_sha256 = hashlib.sha256(raw_tbb).hexdigest()
    asset = extract_help_entries(raw_tbb)
    runner = Runner(image, 0x002C0EC4)
    install_title_table_slot(runner, DATA + 0x100)
    parsed = parse_tbb_header(raw_tbb)
    expected_payload = DATA + 0x100 + parsed["tables"][0]["offset"] + 0x10

    results = []
    for index, entry in enumerate(asset["entries"]):
        case = make_case(raw_tbb, index, seed)
        execution = runner.run(case, start=WINDOW_START, stops=(WINDOW_STOP,), budget=512)
        if execution.fault:
            raise RuntimeError(f"ARM window faulted for selection {index}: {execution.fault}")
        if not execution.stopped or execution.pc != WINDOW_STOP:
            raise RuntimeError(f"ARM window did not stop before the presentation call for {index}")
        expected_pointer = expected_payload + entry["relative_payload_offset"]
        if execution.result != expected_pointer:
            raise AssertionError(f"selection {index}: ARM produced {execution.result:#x}, expected {expected_pointer:#x}")
        if runner.uc.reg_read(arm.UC_ARM_REG_R1) != HELP_RGBA:
            raise AssertionError(f"selection {index}: unexpected presentation color argument")
        data = execution.data
        text_offset = execution.result - DATA
        end = data.find(b"\0", text_offset, min(text_offset + HELP_STRIDE, len(data)))
        if end < 0:
            raise AssertionError(f"selection {index}: selected ARM pointer is not NUL-terminated")
        selected_text = data[text_offset:end].decode("ascii")
        if selected_text != entry["text"]:
            raise AssertionError(f"selection {index}: ARM-selected text differs from the asset")
        results.append({"index": index, "arm_pointer": hex(execution.result),
                        "expected_pointer": hex(expected_pointer),
                        "rgba_argument": hex(runner.uc.reg_read(arm.UC_ARM_REG_R1)),
                        "text": selected_text, "passed": True})

    return {"passed": True, "evidence_type": "pinned original ARM caller-window execution in Unicorn; no emulator/runtime observation",
            "code_sha256": code_sha256, "asset_sha256": asset_sha256,
            "window_start": hex(WINDOW_START), "stop_before_call": hex(WINDOW_STOP),
            "presentation_callee": "Camp_SetSlotMessage at 0x0029F10C (not executed)",
            "tbb_getters": "original Tbb_GetGlobalSubTable/Tbb_GetSubTable/Tbb_GetPayloadData executed; their candidate integration was separately checked in the existing TBB experiment",
            "asset_layout": asset, "selections": results,
            "limits": ["does not execute Camp_SetSlotMessage or render graphics",
                       "does not establish visible text in Azahar or physical input bindings"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--tbb", type=Path,
                        default=ROOT / "build/semantic-equivalence/real-assets/romfs/title/TitleTable.tbb")
    parser.add_argument("--seed", type=int, default=20261024)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run_presentation_window(args.code, args.tbb, args.seed)
    encoded = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
