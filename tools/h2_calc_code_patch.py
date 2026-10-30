#!/usr/bin/env python3
"""Build and differentially exercise the Calc-only H2 code-cave patch."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.asm_diff import ElfRelocation, extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, find_clang
from tools.h2_calc_experiment import (
    ADDRESS,
    CalcMachine,
    Scenario,
    compare,
    directed_scenarios,
)
from tools.semantic_experiment import arm_branch

CODE_DEFAULT = ROOT / "extracted/exefs/code.bin"
SOURCE = ROOT / "experiments/semantic_equivalence/h2_calc_candidate.cpp"
SYMBOL = "candidate_001ea928"
U32 = 0xFFFFFFFF


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rebase_local_text_relocations(
    code: bytes,
    relocations: tuple[ElfRelocation, ...],
    cave_vma: int,
) -> tuple[bytes, list[dict]]:
    """Resolve only audited R_ARM_ABS32 references into this extracted body."""
    fixed = bytearray(code)
    rows: list[dict] = []
    seen: set[int] = set()
    for relocation in relocations:
        if relocation.relocation_type != 2 or relocation.symbol_name:
            raise ValueError(f"unsupported candidate relocation: {relocation}")
        if relocation.explicit_addend is not None:
            raise ValueError(f"unexpected explicit addend: {relocation}")
        if relocation.offset in seen or relocation.offset < 0 or relocation.offset + 4 > len(fixed):
            raise ValueError(f"invalid or duplicate relocation offset: {relocation}")
        seen.add(relocation.offset)
        local_addend = struct.unpack_from("<I", fixed, relocation.offset)[0]
        if local_addend >= len(fixed):
            raise ValueError(
                f"local relocation target {local_addend:#x} is outside {len(fixed):#x}-byte body"
            )
        target = cave_vma + local_addend
        if target > U32:
            raise ValueError("rebased local target overflows the ARM address space")
        struct.pack_into("<I", fixed, relocation.offset, target)
        rows.append({
            "offset": relocation.offset,
            "type": "R_ARM_ABS32",
            "local_addend": hex(local_addend),
            "guest_target": hex(target),
        })
    if len(rows) != 4:
        raise ValueError(f"expected exactly four audited local references; got {len(rows)}")
    return bytes(fixed), rows


def elf_function_section_offset(obj_path: Path, function_name: str) -> int:
    """Return the section-relative address of an ELF32 function symbol."""
    data = Path(obj_path).read_bytes()
    if len(data) < 52 or data[:4] != b"\x7fELF" or data[4] != 1 or data[5] != 1:
        raise ValueError("expected a little-endian ELF32 object")
    header = struct.unpack_from("<16sHHIIIIIHHHHHH", data, 0)
    section_offset, section_entry_size, section_count = header[6], header[11], header[12]
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, section_offset + i * section_entry_size)
        for i in range(section_count)
    ]
    for section in sections:
        if section[1] != 2:  # SHT_SYMTAB
            continue
        string_section = sections[section[6]]
        strings = data[string_section[4]:string_section[4] + string_section[5]]
        entry_size = section[9] or 16
        for index in range(section[5] // entry_size):
            name_offset, value, _size, _info, _other, _section_index = struct.unpack_from(
                "<IIIBBH", data, section[4] + index * entry_size
            )
            end = strings.find(b"\x00", name_offset)
            name = strings[name_offset:end].decode("utf-8", errors="replace")
            if name == function_name:
                return value & ~1
    raise ValueError(f"function symbol not found in ELF symbol table: {function_name}")


def normalize_local_text_addends(
    code: bytes, relocations: tuple[ElfRelocation, ...], section_offset: int
) -> bytes:
    """Convert local ABS32 addends from TU section coordinates to function offsets."""
    normalized = bytearray(code)
    for relocation in relocations:
        if relocation.relocation_type != 2 or relocation.symbol_name:
            continue
        if relocation.explicit_addend is not None:
            raise ValueError(f"unexpected explicit addend: {relocation}")
        target = struct.unpack_from("<I", normalized, relocation.offset)[0]
        if target >= len(normalized):
            if target < section_offset:
                raise ValueError(f"local relocation target precedes function: {target:#x}")
            target -= section_offset
            if target >= len(normalized):
                raise ValueError(f"local relocation target is outside function: {target:#x}")
            struct.pack_into("<I", normalized, relocation.offset, target)
    return bytes(normalized)


def encode_ips(records: list[tuple[int, bytes]], image_size: int) -> bytes:
    output = bytearray(b"PATCH")
    previous_end = -1
    for offset, payload in sorted(records):
        if offset < 0 or len(payload) <= 0 or len(payload) >= 0x10000:
            raise ValueError("IPS record has an invalid offset or length")
        end = offset + len(payload)
        if end > image_size or offset < previous_end:
            raise ValueError("IPS records overlap or exceed the original image")
        if offset >= 0x1000000:
            raise ValueError("IPS record offset exceeds the 24-bit format")
        output.extend(offset.to_bytes(3, "big"))
        output.extend(len(payload).to_bytes(2, "big"))
        output.extend(payload)
        previous_end = end
    output.extend(b"EOF")
    return bytes(output)


def apply_ips(image: bytes, patch: bytes) -> bytes:
    if not patch.startswith(b"PATCH"):
        raise ValueError("invalid IPS header")
    source = memoryview(patch)
    cursor = 5
    result = bytearray(image)
    while True:
        if cursor + 3 > len(source):
            raise ValueError("truncated IPS record or missing EOF")
        if bytes(source[cursor:cursor + 3]) == b"EOF":
            cursor += 3
            if cursor != len(source):
                raise ValueError("unsupported trailing IPS truncate/extension data")
            return bytes(result)
        offset = int.from_bytes(source[cursor:cursor + 3], "big")
        cursor += 3
        if cursor + 2 > len(source):
            raise ValueError("truncated IPS length")
        size = int.from_bytes(source[cursor:cursor + 2], "big")
        cursor += 2
        if size == 0:
            if cursor + 3 > len(source):
                raise ValueError("truncated IPS RLE record")
            size = int.from_bytes(source[cursor:cursor + 2], "big")
            value = source[cursor + 2]
            cursor += 3
            data = bytes((value,)) * size
        else:
            if cursor + size > len(source):
                raise ValueError("truncated IPS payload")
            data = bytes(source[cursor:cursor + size])
            cursor += size
        if size == 0 or offset + size > len(result):
            raise ValueError("IPS record is empty or outside the original image")
        result[offset:offset + size] = data


def build_patch(
    image: bytes,
    code: bytes,
    relocations: tuple[ElfRelocation, ...],
    game: dict,
) -> tuple[bytes, bytes, dict]:
    """Build the pinned Calc patch; original image bytes are never modified."""
    if len(image) != int(game["code_bin_size"]):
        raise ValueError("pinned code.bin size mismatch")
    expected_hash = str(game["code_sha256"]).lower()
    if sha256(image) != expected_hash:
        raise ValueError("pinned code.bin SHA-256 mismatch")
    text = game["segments"]["text"]
    text_base = int(text["vaddr"], 16)
    text_size = int(text["size"], 16)
    aligned_size = int(text["aligned_size"], 16)
    text_offset = int(text["file_offset"], 16)
    text_end = text_base + text_size
    padded_end = text_base + aligned_size
    if text_base != 0x00100000 or text_offset != 0 or text_end != 0x003FE624:
        raise ValueError("pinned .text layout differs from the reviewed H2 cave contract")
    if aligned_size < text_size or text_offset + aligned_size > len(image):
        raise ValueError("invalid .text page-padding bounds")
    cave_vma = text_end
    cave_offset = text_offset + (cave_vma - text_base)
    cave_capacity = padded_end - cave_vma
    if cave_capacity != 0x9DC or cave_offset + len(code) > text_offset + aligned_size:
        raise ValueError("candidate exceeds the reviewed .text cave capacity")
    if any(image[cave_offset:text_offset + aligned_size]):
        raise ValueError(".text page padding is not all zero")
    entry_offset = text_offset + (ADDRESS - text_base)
    if ADDRESS < text_base or ADDRESS + 4 > text_end:
        raise ValueError("Calc entry lies outside original .text")
    if entry_offset < cave_offset + len(code) and cave_offset < entry_offset + 4:
        raise ValueError("Calc entry word overlaps the cave body")

    relocated, relocation_rows = rebase_local_text_relocations(code, relocations, cave_vma)
    branch = arm_branch(ADDRESS, cave_vma)
    branch_word = struct.unpack("<I", branch)[0]
    branch_displacement = (branch_word & 0x00FFFFFF) << 2
    if branch_displacement & 0x02000000:
        branch_displacement -= 0x04000000
    branch_target = ADDRESS + 8 + branch_displacement
    if branch_target != cave_vma:
        raise ValueError("ARM branch encoding does not target the candidate cave")

    patched = bytearray(image)
    patched[entry_offset:entry_offset + 4] = branch
    patched[cave_offset:cave_offset + len(relocated)] = relocated
    ips = encode_ips([(entry_offset, branch), (cave_offset, relocated)], len(image))
    manifest = {
        "schema": 1,
        "function": "TitleConfig_Calc",
        "entry_vma": hex(ADDRESS),
        "entry_file_offset": hex(entry_offset),
        "cave_vma": hex(cave_vma),
        "cave_file_offset": hex(cave_offset),
        "cave_capacity": cave_capacity,
        "candidate_bytes": len(relocated),
        "branch_bytes": branch.hex(),
        "branch_target": hex(branch_target),
        "relocations": relocation_rows,
        "original_sha256": sha256(image),
        "patched_sha256": sha256(bytes(patched)),
        "ips_sha256": sha256(ips),
        "ips_records": [
            {"offset": hex(offset), "length": len(payload), "sha256": sha256(payload)}
            for offset, payload in sorted([(entry_offset, branch), (cave_offset, relocated)])
        ],
    }
    reapplied = apply_ips(image, ips)
    if reapplied != bytes(patched):
        raise ValueError("independent IPS application does not reproduce patched image")
    return bytes(patched), ips, manifest


def run_final_address_differential(
    image: bytes,
    patched_image: bytes,
    seed: int,
    samples: int,
) -> tuple[list[dict], dict]:
    rows: list[dict] = []
    first_error = None
    cases = directed_scenarios(seed, samples)
    for scenario in cases:
        original = CalcMachine(image, scenario=scenario).run()
        replacement = CalcMachine(patched_image, scenario=scenario).run()
        error = compare(original, replacement)
        row = {"case": scenario.label, "passed": error is None, "difference": error}
        rows.append(row)
        if error and first_error is None:
            first_error = {
                "case": scenario.label,
                "difference": error,
                "original_return": hex(original["return"]),
                "patched_return": hex(replacement["return"]),
                "original_work_sha256": sha256(original["work"]),
                "patched_work_sha256": sha256(replacement["work"]),
                "original_config": original["config"].hex(),
                "patched_config": replacement["config"].hex(),
            }

    negative_case = Scenario("wrong-branch-target-control", 4)
    bad = bytearray(patched_image)
    text = 0x00100000
    bad_offset = ADDRESS - text
    bad[bad_offset:bad_offset + 4] = arm_branch(ADDRESS, 0x003FE628)
    original = CalcMachine(image, scenario=negative_case).run()
    wrong = CalcMachine(bytes(bad), scenario=negative_case).run()
    negative_error = compare(original, wrong)
    negative = {
        "name": "branch-to-cave-plus-four",
        "detected": negative_error is not None,
        "difference": negative_error,
    }
    return rows, {"first_counterexample": first_error, "negative_control": negative}


def build_experiment(
    code_path: Path,
    output: Path,
    seed: int,
    samples: int,
    source_path: Path = SOURCE,
    symbol: str = SYMBOL,
    expected_size: int | None = None,
) -> dict:
    if output.exists():
        raise FileExistsError(f"output directory already exists: {output}")
    output.mkdir(parents=True)
    started = time.perf_counter()
    image = code_path.read_bytes()
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    source_path = source_path.resolve()
    source_hash = sha256(source_path.read_bytes())
    object_path = output / f"{source_path.stem}.o"
    build = compile_tu_armv6k(source_path, object_path, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr or "ARMv6K compile failed")
    functions = extract_elf_functions_detailed(object_path)
    if symbol not in functions:
        raise ValueError(f"Calc symbol missing from compiled object: {symbol}")
    code, relocations = functions[symbol]
    symbol_section_offset = elf_function_section_offset(object_path, symbol)
    code = normalize_local_text_addends(code, relocations, symbol_section_offset)
    if expected_size is not None and len(code) != expected_size:
        raise ValueError(
            f"Calc symbol size changed: expected {expected_size}, got {len(code)}"
        )
    patched_image, ips, manifest = build_patch(image, code, relocations, game)
    if sha256(source_path.read_bytes()) != source_hash:
        raise RuntimeError("Calc source changed during patch construction")

    rows, controls = run_final_address_differential(image, patched_image, seed, samples)
    passed = (
        all(row["passed"] for row in rows)
        and controls["first_counterexample"] is None
        and controls["negative_control"]["detected"]
    )
    rebuilt = apply_ips(image, ips)
    if rebuilt != patched_image:
        raise RuntimeError("IPS application drifted after differential run")
    (output / "code.experimental.bin").write_bytes(patched_image)
    (output / "code.ips").write_bytes(ips)
    manifest.update({
        "compiled_source_path": str(source_path),
        "compiled_symbol": symbol,
        "compiled_source_sha256": source_hash,
        "compiled_object_sha256": sha256(object_path.read_bytes()),
        "compiler": subprocess.run(
            [str(find_clang()), "--version"], capture_output=True, text=True, check=True
        ).stdout.splitlines()[0],
        "compile_command": build.args,
    })
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    report = {
        "schema": 1,
        "passed": passed,
        "scope": "pinned code image with Calc replacement installed at its final guest VMA; explicit shared external service mocks",
        "original_sha256": sha256(image),
        "patched_sha256": sha256(patched_image),
        "ips_sha256": sha256(ips),
        "source_sha256": source_hash,
        "source_path": str(source_path),
        "object_sha256": sha256(object_path.read_bytes()),
        "symbol": symbol,
        "symbol_size": len(code),
        "symbol_section_offset": hex(symbol_section_offset),
        "runner_sha256": sha256(Path(__file__).read_bytes()),
        "case_count": len(rows),
        "cases_passed": sum(row["passed"] for row in rows),
        "cases": rows,
        **controls,
        "evidence": {"compiled": "passed", "arm_differential": "passed" if passed else "failed", "caller": "not_run", "runtime": "not_run"},
        "limits": [
            "The same deterministic service hooks are used for original and patched callback executions; this validates patched image placement and Calc logic only at those boundaries.",
            "No original title caller, helper internals beyond current mocked/original boundaries, user input, persistence, Azahar runtime, or OS input was tested.",
            "A wrong-branch control detects the patch-entry redirect error; it does not independently mutate and test each relocation.",
        ],
        "elapsed_seconds": round(time.perf_counter() - started, 3),
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=CODE_DEFAULT)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--symbol", default=SYMBOL)
    parser.add_argument("--expected-size", type=int)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--samples", type=int, default=32)
    args = parser.parse_args()
    report = build_experiment(
        args.code, args.output, args.seed, args.samples,
        args.source, args.symbol, args.expected_size,
    )
    print(json.dumps({"passed": report["passed"], "cases": report["cases_passed"],
                      "report": str(args.output / "report.json"),
                      "patched_sha256": report["patched_sha256"]}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
