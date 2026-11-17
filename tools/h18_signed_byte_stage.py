#!/usr/bin/env python3
"""Stage and offline-validate the production 0x00121d70 getter replacement."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import random
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.h18_signed_byte_production as semantic
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.semantic_experiment import arm_branch, validate_leaf

FUNC = semantic.FUNC
FUNC_SIZE = semantic.FUNC_SIZE
TEXT = semantic.TEXT
CALL_START = semantic.CALL_START
CALL_STOPS = semantic.CALL_STOPS
GLOBAL_PTR = semantic.GLOBAL_PTR
TEXT_PAD_START = 0x003FE624
TEXT_PAD_END = 0x003FF000
CAVE = TEXT_PAD_START
NOP = 0xE1A00000


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _compile_production(output: Path) -> tuple[bytes, dict]:
    source = ROOT / "src/engine/leaf_matching.cpp"
    obj = output / "leaf_matching.production.o"
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "production ARMv6K compile failed")
    functions = extract_elf_functions_detailed(obj)
    if "func_00121d70" not in functions:
        raise ValueError("compiled production object lacks func_00121d70")
    code, relocations = functions["func_00121d70"]
    if relocations:
        raise ValueError(f"unexpected candidate relocations: {relocations}")
    validate_leaf(code)
    return code, {
        "source_sha256": _sha(source.read_bytes()),
        "object_sha256": _sha(obj.read_bytes()),
        "candidate_sha256": _sha(code),
        "candidate_bytes": len(code),
    }


def _static_refs(image: bytes) -> dict:
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    text_start = int(game["segments"]["text"]["vaddr"], 16)
    text_size = int(game["segments"]["text"]["size"], 16)
    destinations = ((FUNC, FUNC + FUNC_SIZE, "entry_span"),
                    (CAVE, CAVE + 0x100, "cave_prefix"))
    branches = []
    for off in range(0, text_size - 3, 4):
        word = struct.unpack_from("<I", image, off)[0]
        site = text_start + off
        target = None
        kind = None
        if word & 0x0F000000 == 0x0B000000:
            imm = word & 0xFFFFFF
            if imm & 0x800000:
                imm -= 1 << 24
            target, kind = site + 8 + imm * 4, "BL"
        elif word & 0xFE000000 == 0xFA000000:
            imm = word & 0xFFFFFF
            if imm & 0x800000:
                imm -= 1 << 24
            target, kind = site + 8 + imm * 4 + ((word >> 23) & 2), "BLX"
        if target is not None:
            for start, end, label in destinations:
                if start <= target < end:
                    branches.append({"site": hex(site), "target": hex(target),
                                     "kind": kind, "region": label})
    pointer_words = []
    for off in range(0, len(image) - 3, 4):
        word = struct.unpack_from("<I", image, off)[0]
        for start, end, label in destinations:
            if start <= word < end:
                pointer_words.append({"site": hex(text_start + off),
                                      "value": hex(word), "region": label})
    return {"branch_refs": branches, "aligned_pointer_words": pointer_words}


def _occupancy(image: bytes, candidate_size: int) -> dict:
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    text_start = int(game["segments"]["text"]["vaddr"], 16)
    text_size = int(game["segments"]["text"]["size"], 16)
    aligned_size = int(game["segments"]["text"]["aligned_size"], 16)
    expected_cave = text_start + text_size
    aligned_end = text_start + aligned_size
    if CAVE != expected_cave or aligned_end != TEXT_PAD_END or expected_cave != TEXT_PAD_START:
        raise ValueError("configured text padding does not match the pinned staging window")
    padding = image[CAVE - TEXT:CAVE - TEXT + (aligned_end - expected_cave)]
    if len(padding) != aligned_end - expected_cave or any(padding):
        raise ValueError("executable text-page padding is not entirely zero")
    if candidate_size <= 0 or candidate_size > len(padding) or CAVE % 4:
        raise ValueError("candidate does not fit aligned executable padding")
    with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    conflicts = []
    for row in rows:
        start = int(row["address"], 16)
        end = start + int(row["size"])
        if start < CAVE + candidate_size and end > CAVE:
            conflicts.append({"address": row["address"], "size": row["size"],
                              "name": row["name"], "region": "candidate_cave"})
        if start < FUNC + FUNC_SIZE and end > FUNC:
            if start != FUNC or end != FUNC + FUNC_SIZE:
                conflicts.append({"address": row["address"], "size": row["size"],
                                  "name": row["name"], "region": "entry_span"})
    if conflicts:
        raise ValueError(f"catalog span collision(s): {conflicts}")
    return {"text_vaddr": hex(text_start), "text_size": hex(text_size),
            "aligned_text_end": hex(aligned_end), "padding_start": hex(expected_cave),
            "padding_end": hex(aligned_end), "padding_bytes": len(padding),
            "padding_all_zero": True, "candidate_vaddr": hex(CAVE),
            "candidate_size": candidate_size, "catalog_conflicts": conflicts}


def _ips(patches: list[tuple[int, bytes]]) -> bytes:
    result = bytearray(b"PATCH")
    for offset, payload in sorted(patches):
        if not 0 <= offset < (1 << 24) or not 0 < len(payload) <= 0xFFFF:
            raise ValueError("IPS patch record is outside format limits")
        result.extend(offset.to_bytes(3, "big"))
        result.extend(len(payload).to_bytes(2, "big"))
        result.extend(payload)
    result.extend(b"EOF")
    return bytes(result)


def _apply_ips(image: bytes, patch: bytes) -> bytes:
    if not patch.startswith(b"PATCH"):
        raise ValueError("IPS magic missing")
    output = bytearray(image)
    cursor = 5
    while patch[cursor:cursor + 3] != b"EOF":
        if cursor + 5 > len(patch):
            raise ValueError("truncated IPS record")
        offset = int.from_bytes(patch[cursor:cursor + 3], "big")
        length = int.from_bytes(patch[cursor + 3:cursor + 5], "big")
        cursor += 5
        if length == 0:
            raise ValueError("unexpected unsupported IPS RLE record")
        payload = patch[cursor:cursor + length]
        if len(payload) != length or offset + length > len(output):
            raise ValueError("truncated/out-of-image IPS record")
        output[offset:offset + length] = payload
        cursor += length
    if cursor + 3 != len(patch):
        raise ValueError("trailing data after IPS EOF")
    return bytes(output)


def _branch_target(site: int, encoded: bytes) -> int:
    word = struct.unpack("<I", encoded)[0]
    if word & 0xFF000000 != 0xEA000000:
        raise ValueError("entry veneer is not an unconditional ARM B")
    imm = word & 0xFFFFFF
    if imm & 0x800000:
        imm -= 1 << 24
    return site + 8 + imm * 4


def _direct_and_caller(original: bytes, patched: bytes, seed: int,
                       samples: int, caller_samples: int) -> tuple[dict, dict]:
    cases = list(range(256)) + [random.Random(seed ^ n).getrandbits(8) for n in range(samples)]
    direct_results = []
    for index, value in enumerate(cases):
        regs, data, stack, _ptr = semantic._data(seed, index, value)
        old = semantic._execute(original, code=None, registers=regs, data=data,
                                stack=stack, start=FUNC, stops=(semantic.RETURN,))
        new = semantic._execute(patched, code=None, registers=regs, data=data,
                                stack=stack, start=FUNC, stops=(semantic.RETURN,))
        reason = semantic._compare(old, new)
        direct_results.append({"index": index, "input_byte": value,
                               "passed": reason is None, "reason": reason})

    caller_cases = list(range(256)) + [random.Random((seed << 1) ^ n).getrandbits(8)
                                       for n in range(caller_samples)]
    caller_results = []
    observed = set()
    for index, value in enumerate(caller_cases):
        regs, data, stack, pointer = semantic._data(seed, 1200 + index, value)
        old = semantic._execute(original, code=None, registers=regs, data=data,
                                stack=stack, start=CALL_START, stops=CALL_STOPS,
                                global_pointer=pointer)
        new = semantic._execute(patched, code=None, registers=regs, data=data,
                                stack=stack, start=CALL_START, stops=CALL_STOPS,
                                global_pointer=pointer)
        reason = semantic._compare(old, new, caller_window=True)
        if old["stopped_at"] is not None:
            observed.add(hex(old["stopped_at"]))
        caller_results.append({"index": index, "input_byte": value,
                               "continuation": None if old["stopped_at"] is None else hex(old["stopped_at"]),
                               "passed": reason is None, "reason": reason})
    direct = {"passed": all(row["passed"] for row in direct_results),
              "directed_cases": 256, "randomized_cases": samples,
              "cases": len(direct_results), "results": direct_results}
    caller = {"passed": all(row["passed"] for row in caller_results)
                        and observed == {hex(x) for x in CALL_STOPS},
              "start": hex(CALL_START), "global_pointer_word": hex(GLOBAL_PTR),
              "cases": len(caller_results), "randomized_cases": caller_samples,
              "continuations": sorted(observed), "results": caller_results,
              "injection_note": "Global pointer word is seeded to a synthetic RAM object; the runtime producer is not executed."}
    return direct, caller


def run(code_path: Path, output: Path, *, seed: int = 7, samples: int = 256,
        caller_samples: int = 256) -> dict:
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    semantic.verify_source(ROOT)
    original = Path(code_path).read_bytes()
    reference_hash = _sha(original)
    if reference_hash != semantic.REFERENCE_SHA256:
        raise ValueError("reference code.bin does not match the pinned image")
    code, build_identity = _compile_production(output)
    occupancy = _occupancy(original, len(code))
    static_refs = _static_refs(original)
    entry_refs = [r for r in static_refs["branch_refs"] if r["region"] == "entry_span"]
    interior = [r for r in entry_refs if r["target"] != hex(FUNC)]
    cave_refs = [r for r in static_refs["branch_refs"] + static_refs["aligned_pointer_words"]
                 if r.get("region") == "cave_prefix"]
    if interior or cave_refs:
        raise ValueError(f"entry/cave reference conflict: interior={interior}, cave={cave_refs}")
    if len(entry_refs) != 1 or entry_refs[0]["site"] != "0x110f44":
        raise ValueError(f"unexpected direct callers to staged entry: {entry_refs}")

    branch = arm_branch(FUNC, CAVE)
    if _branch_target(FUNC, branch) != CAVE or CAVE & 1 or FUNC & 1:
        raise ValueError("branch veneer target or ARM/Thumb state is invalid")
    veneer = branch + struct.pack("<II", NOP, NOP)
    if len(veneer) != FUNC_SIZE:
        raise AssertionError("entry veneer must occupy exactly the 12-byte original span")
    patches = [(FUNC - TEXT, veneer), (CAVE - TEXT, code)]
    for i, (off_a, bytes_a) in enumerate(patches):
        for off_b, bytes_b in patches[i + 1:]:
            if off_a < off_b + len(bytes_b) and off_b < off_a + len(bytes_a):
                raise ValueError("IPS patch hunks overlap")
    patched, ips = _apply_ips(original, _ips(patches)), _ips(patches)
    if _apply_ips(original, ips) != patched:
        raise AssertionError("IPS roundtrip did not reproduce staged image")
    if patched[CAVE - TEXT:CAVE - TEXT + len(code)] != code:
        raise AssertionError("staged production symbol bytes missing at cave")
    if _branch_target(FUNC, patched[FUNC - TEXT:FUNC - TEXT + 4]) != CAVE:
        raise AssertionError("staged entry veneer does not target the cave")
    ips_path, image_path = output / "code.staged.ips", output / "code.staged.bin"
    ips_path.write_bytes(ips)
    image_path.write_bytes(patched)
    direct, caller = _direct_and_caller(original, patched, seed, samples, caller_samples)
    report = {
        "schema": 1, "passed": direct["passed"] and caller["passed"],
        "seed": seed, "samples": samples, "caller_samples": caller_samples,
        "reference_sha256": reference_hash, "source_sha256": build_identity["source_sha256"],
        "object_sha256": build_identity["object_sha256"],
        "candidate_sha256": build_identity["candidate_sha256"],
        "candidate_bytes": len(code), "candidate_bytes_hex": code.hex(),
        "staged_image_sha256": _sha(patched), "ips_sha256": _sha(ips),
        "ips_roundtrip": _apply_ips(original, ips) == patched,
        "placement": occupancy,
        "entry_patch": {"address": hex(FUNC), "original_size": FUNC_SIZE,
                        "veneer_bytes": veneer.hex(), "branch_bytes": branch.hex(),
                        "target": hex(_branch_target(FUNC, branch)),
                        "source_pointer_bit0": FUNC & 1, "target_pointer_bit0": CAVE & 1,
                        "arm_state": True, "direct_branch_refs": entry_refs,
                        "interior_branch_refs": interior},
        "reference_scan": static_refs,
        "direct_differential": direct, "caller_composition": caller,
        "artifacts": {"image": str(image_path), "ips": str(ips_path)},
        "limitations": [
            "Placement uses the pinned executable text segment's all-zero page padding from 0x003fe624 to 0x003ff000; this is an offline image-layout fact, not loader/runtime verification.",
            "Caller composition seeds global 0x00433158 to a synthetic readable object and does not run its runtime producer or establish the real pointee's type/lifetime/extent.",
            "Static scans cover aligned ARM BL/BLX and aligned image words only; indirect, computed, Thumb, relocated, unaligned, or runtime-generated references are not excluded.",
            "No emulator, loader, live title, or whole-game runtime verification was performed."
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--samples", type=int, default=256)
    parser.add_argument("--caller-samples", type=int, default=256)
    args = parser.parse_args()
    report = run(args.code, args.output, seed=args.seed,
                 samples=args.samples, caller_samples=args.caller_samples)
    print(json.dumps({"passed": report["passed"], "report": str(args.output / "report.json")}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
