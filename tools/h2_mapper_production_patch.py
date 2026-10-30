#!/usr/bin/env python3
"""Install the three production H2 config mappers in their original slots."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import random
import struct
import sys
import time

import capstone
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, find_clang
from tools.h2_calc_code_patch import apply_ips, encode_ips
from tools.h2_config_mapper_experiment import (
    MAPPERS, make_case, mapper_access_violation, expected_index,
)

ORIGINAL_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
BASE_SHA256 = "7b2bc2983a890e1c4cf1ae71beca9f574260d98d6cfcdffb3bbb34bd3eb2b291"
BASE_MANIFEST_SHA256 = "e866f14b9c5bcf0936afa67aadabfcf58fff47e20e37ae51802dfd75745fc298"
BASE_IMAGE = ROOT / "build/agent-work/H2-semantic/h2-init-ready-final-image/run-013/combined-build-final/code.combined.bin"
BASE_MANIFEST = ROOT / "build/agent-work/H2-semantic/h2-init-ready-final-image/run-013/combined-build-final/manifest.json"
ORIGINAL_IMAGE = ROOT / "extracted/exefs/code.bin"
OBJECTS = {
    0x0021F39C: ("camp_func_0021f39c", "src/engine/leaf_batch32_b.cpp",
                 "build/agent-work/H2-semantic/h2-config-mapper-production-integration/run-001/checks/production-tu-b/engine/leaf_batch32_b.o"),
    0x002CAB70: ("camp_func_002cab70", "src/engine/leaf_batch32_c.cpp",
                 "build/agent-work/H2-semantic/h2-config-mapper-production-integration/run-001/checks/production-tu-c/engine/leaf_batch32_c.o"),
    0x002E0AF4: ("camp_func_002e0af4", "src/engine/leaf_batch32_c.cpp",
                 "build/agent-work/H2-semantic/h2-config-mapper-production-integration/run-001/checks/production-tu-c/engine/leaf_batch32_c.o"),
}
TABLES = {0x002CAB70: 0x004077EB, 0x0021F39C: 0x004077F6, 0x002E0AF4: 0x00407801}
TEXT_VMA = 0x00100000
SPAN = 92
NOP = struct.pack("<I", 0xE1A00000)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def vma_to_offset(address: int) -> int:
    return address - TEXT_VMA


def validate_mapper_blob(code: bytes, address: int, table_address: int) -> dict:
    """Accept local ARM branches and one in-blob literal for the pinned table."""
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    decoder.detail = True
    instructions = []
    return_offset = None
    for insn in decoder.disasm(code, address):
        if insn.address != address + sum(item.size for item in instructions):
            raise ValueError("Mapper body has an undecodable instruction prefix")
        instructions.append(insn)
        if insn.mnemonic == "bx" and insn.op_str == "lr":
            return_offset = insn.address - address
            break
    if return_offset is None:
        raise ValueError("Mapper body has no bx lr return")
    tail_start = return_offset + 4
    if tail_start >= len(code) or (len(code) - tail_start) % 4:
        raise ValueError("Mapper literal tail must contain complete words")
    literal_hits = []
    for insn in instructions[:-1]:
        if insn.group(capstone.CS_GRP_CALL):
            raise ValueError("Mapper body unexpectedly calls another function")
        if insn.group(capstone.CS_GRP_JUMP):
            if insn.mnemonic.startswith("bx") and insn.op_str == "lr":
                continue
            if insn.mnemonic in ("bx", "blx") or not insn.operands:
                raise ValueError("Mapper body has an indirect control transfer")
            target = insn.operands[0].imm
            if target < address or target >= address + tail_start or target % 4:
                raise ValueError("Mapper branch leaves its executable prefix")
        for operand in insn.operands:
            if operand.type == capstone.CS_OP_MEM and insn.reg_name(operand.mem.base) == "pc":
                if not insn.mnemonic.startswith("ldr"):
                    raise ValueError("Only PC-relative LDR literals are supported")
                target = (insn.address + 8 + operand.mem.disp) & ~3
                if not address + tail_start <= target <= address + len(code) - 4:
                    raise ValueError("Mapper literal reference leaves its data tail")
                literal_hits.append(target)
        if "pc" in insn.op_str and not any(
            operand.type == capstone.CS_OP_MEM and insn.reg_name(operand.mem.base) == "pc"
            for operand in insn.operands
        ):
            raise ValueError("Unsupported PC-relative instruction")
    if len(code) != 48 or literal_hits != [address + 44]:
        raise ValueError("Mapper executable/literal layout differs from reviewed 48-byte body")
    literal = struct.unpack_from("<I", code, 44)[0]
    if literal != table_address:
        raise ValueError(f"Mapper literal {literal:#x} does not select {table_address:#x}")
    return {"executable_bytes": tail_start, "return_vma": hex(address + return_offset),
            "literal_vma": hex(address + 44), "literal_value": hex(literal)}


def read_spans(functions_csv: Path) -> dict[int, tuple[int, str]]:
    spans = {}
    with functions_csv.open(newline="", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            address = int(row["address"], 16)
            spans[address] = (int(row["size"], 10), row["name"])
    return spans


def direct_branch_target(word: int, address: int) -> int | None:
    if (word >> 25) & 0x7 != 0b101:
        return None
    immediate = word & 0x00FFFFFF
    if immediate & 0x00800000:
        immediate -= 0x01000000
    if (word >> 28) == 0xF:
        h = (word >> 24) & 1
        return (address + 8 + (immediate << 2) + (h << 1)) | 1
    return address + 8 + (immediate << 2)


def audit_interior_references(image: bytes, functions_csv: Path) -> dict:
    spans = read_spans(functions_csv)
    targets = {address: (address + SPAN) for address in OBJECTS}
    branch_hits = []
    for start, (size, _name) in spans.items():
        if start in targets:
            continue
        start_off = vma_to_offset(start)
        if start_off < 0 or start_off + size > len(image):
            raise ValueError(f"function span out of image: {start:#x}")
        for off in range(start_off, start_off + size, 4):
            word = struct.unpack_from("<I", image, off)[0]
            target = direct_branch_target(word, TEXT_VMA + off)
            normalized = (target & ~1) if target is not None else None
            if normalized is not None and any(lo < normalized < hi for lo, hi in targets.items()):
                branch_hits.append({"source": hex(TEXT_VMA + off), "target": hex(normalized)})

    pointer_hits = []
    for off in range(0, len(image) - 3, 4):
        source_vma = TEXT_VMA + off if off < 0x002FF000 else None
        if source_vma is not None and any(lo <= source_vma < hi for lo, hi in targets.items()):
            continue
        value = struct.unpack_from("<I", image, off)[0] & ~1
        if any(lo < value < hi for lo, hi in targets.items()):
            pointer_hits.append({"source_file_offset": hex(off), "target": hex(value)})
    if branch_hits or pointer_hits:
        raise ValueError(f"external mapper interior references found: branches={branch_hits}, pointers={pointer_hits}")
    return {"ledger_functions_scanned": len(spans), "direct_branch_interior_hits": branch_hits,
            "aligned_absolute_pointer_interior_hits": pointer_hits,
            "scope": "direct ARM B/BL/BLX in ledgered text plus aligned words in full code.bin"}


def extract_bodies(object_paths: dict[int, Path]) -> tuple[dict[int, bytes], dict[int, dict]]:
    elf_cache = {}
    bodies, meta = {}, {}
    for address, (symbol, _source, _default_obj) in OBJECTS.items():
        path = object_paths[address]
        if path not in elf_cache:
            elf_cache[path] = extract_elf_functions_detailed(path)
        functions = elf_cache[path]
        if symbol not in functions:
            raise ValueError(f"missing production symbol {symbol} in {path}")
        body, relocations = functions[symbol]
        if relocations:
            raise ValueError(f"unsupported relocation in {symbol}: {relocations}")
        if len(body) > SPAN or len(body) % 4:
            raise ValueError(f"invalid in-place size for {symbol}: {len(body)}")
        layout = validate_mapper_blob(body, address, TABLES[address])
        bodies[address] = body
        meta[address] = {"symbol": symbol, "size": len(body), "sha256": sha256(body),
                         "object": str(path), "object_sha256": sha256(path.read_bytes()),
                         "source": str(ROOT / OBJECTS[address][1]),
                         "source_sha256": sha256((ROOT / OBJECTS[address][1]).read_bytes()),
                         "table_address": hex(TABLES[address]), **layout}
    return bodies, meta


def make_patch(base: bytes, original: bytes, bodies: dict[int, bytes],
               functions_csv: Path) -> tuple[bytes, bytes, list[dict]]:
    if sha256(base) != BASE_SHA256:
        raise ValueError("base image is not the reviewed run-013 H2 image")
    audit = audit_interior_references(original, functions_csv)
    # Also audit the five-function base so new production call sites cannot
    # silently target an overwritten mapper interior.
    audit["run013_base"] = audit_interior_references(base, functions_csv)
    patched = bytearray(base)
    records = []
    for address in sorted(OBJECTS):
        span, name = read_spans(functions_csv)[address]
        if span != SPAN:
            raise ValueError(f"unexpected ledger span for {name}: {span}")
        body = bodies[address]
        payload = body + NOP * ((span - len(body)) // 4)
        offset = vma_to_offset(address)
        patched[offset:offset + span] = payload
        records.append((offset, payload))
    ips = encode_ips(records, len(base))
    restored = apply_ips(base, ips)
    if restored != bytes(patched):
        raise ValueError("IPS round-trip differs from constructed mapper image")
    audit["patch_records"] = [{"address": hex(address), "offset": hex(offset),
                               "span": len(payload), "body_bytes": len(bodies[address]),
                               "sha256": sha256(payload)}
                              for address, (offset, payload) in zip(sorted(OBJECTS), records)]
    return bytes(patched), ips, audit


def compare_final_images(base: bytes, patched: bytes, address: int, table: int,
                         values: tuple[int, ...], seed: int, samples: int) -> dict:
    from tools.h2_config_mapper_experiment import MapperRunner
    rng = random.Random(seed ^ address)
    original = MapperRunner(base, address, table)
    rebuilt = MapperRunner(patched, address, table)
    cases = [(f"byte-{value}", value) for value in range(256)]
    cases += [(f"seeded-{i}", rng.randrange(256)) for i in range(samples)]
    reads_original: set[int] = set()
    reads_patched: set[int] = set()
    writes_original: set[int] = set()
    writes_patched: set[int] = set()
    for index, (label, value) in enumerate(cases, start=1):
        case = make_case(value, rng, label)
        left = original.run(case)
        right = rebuilt.run(case)
        reads_original.update(original.table_reads)
        reads_patched.update(rebuilt.table_reads)
        writes_original.update(original.writes)
        writes_patched.update(rebuilt.writes)
        violation = mapper_access_violation(original.table_reads, rebuilt.table_reads,
                                             original.writes, rebuilt.writes)
        if left.fault or right.fault or not left.stopped or not right.stopped:
            return {"passed": False, "cases": len(cases), "checked": index,
                    "first_counterexample": {"case": label, "input": value,
                                             "original_fault": left.fault, "patched_fault": right.fault}}
        if violation:
            return {"passed": False, "cases": len(cases), "checked": index,
                    "first_counterexample": {"case": label, "input": value,
                                             "reason": "mapper contract forbids data/stack writes",
                                             "write_violation": violation}}
        if left.result != right.result or left.result != expected_index(value, values):
            return {"passed": False, "cases": len(cases), "checked": index,
                    "first_counterexample": {"case": label, "input": value,
                                             "original_result": left.result,
                                             "patched_result": right.result,
                                             "expected_result": expected_index(value, values)}}
        if left.preserved != left.expected_preserved or right.preserved != right.expected_preserved:
            return {"passed": False, "cases": len(cases), "checked": index,
                    "first_counterexample": {"case": label, "input": value,
                                             "reason": "callee-saved register/SP/VFP preservation"}}
        if (left.data != right.data or left.live_stack != right.live_stack
                or left.pc != right.pc):
            return {"passed": False, "cases": len(cases), "checked": index,
                    "first_counterexample": {"case": label, "input": value,
                                             "reason": "continuation or memory differs"}}
    return {"passed": True, "cases": len(cases), "exhaustive_byte_cases": 256,
            "seeded_byte_cases": samples, "first_counterexample": None,
            "observed_accesses": {
                "original_table_read_addresses": [hex(x) for x in sorted(reads_original)],
                "patched_table_read_addresses": [hex(x) for x in sorted(reads_patched)],
                "original_data_stack_writes": [hex(x) for x in sorted(writes_original)],
                "patched_data_stack_writes": [hex(x) for x in sorted(writes_patched)]}}


def build_and_validate(base_path: Path, original_path: Path, object_b: Path,
                       object_c: Path, output: Path, seeds: list[int], samples: int) -> dict:
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    started = time.perf_counter()
    original = original_path.read_bytes()
    if sha256(original) != ORIGINAL_SHA256:
        raise ValueError("pinned original code.bin hash mismatch")
    base = base_path.read_bytes()
    if sha256(base) != BASE_SHA256:
        raise ValueError("reviewed five-function run-013 image hash mismatch")
    base_manifest = json.loads(BASE_MANIFEST.read_text(encoding="utf-8"))
    if sha256(BASE_MANIFEST.read_bytes()) != BASE_MANIFEST_SHA256:
        raise ValueError("reviewed run-013 manifest hash mismatch")
    if base_manifest.get("patched_sha256") != BASE_SHA256:
        raise ValueError("base manifest does not identify run-013 image")

    object_paths = {0x0021F39C: object_b, 0x002CAB70: object_c, 0x002E0AF4: object_c}
    bodies, symbols = extract_bodies(object_paths)
    build_b = json.loads(object_b.with_suffix(object_b.suffix + ".json").read_text(encoding="utf-8"))
    build_c = json.loads(object_c.with_suffix(object_c.suffix + ".json").read_text(encoding="utf-8"))
    for path, metadata in ((object_b, build_b), (object_c, build_c)):
        if metadata.get("object_hash") != sha256(path.read_bytes()):
            raise ValueError(f"build metadata does not identify {path}")
    if build_b["identity"]["compiler_version"] != build_c["identity"]["compiler_version"]:
        raise ValueError("affected TUs were built with different compiler versions")
    if build_b["identity"]["flags"] != build_c["identity"]["flags"]:
        raise ValueError("affected TUs were built with different compiler flags")
    compiler_metadata = {"compiler_version": build_b["identity"]["compiler_version"].strip(),
                         "flags": build_b["identity"]["flags"],
                         "objects": {str(object_b): build_b["object_hash"],
                                     str(object_c): build_c["object_hash"]}}
    patched, ips, audit = make_patch(base, original, bodies, ROOT / "config/functions.csv")
    final_hash = sha256(patched)
    manifest = dict(base_manifest)
    base_ips_hash = manifest.get("ips_sha256")
    manifest["base_patched_sha256"] = BASE_SHA256
    manifest["base_ips_sha256"] = base_ips_hash
    manifest["ips_sha256"] = sha256(ips)
    manifest["patch_chain"] = [
        {"base_sha256": ORIGINAL_SHA256, "ips_sha256": base_ips_hash,
         "result_sha256": BASE_SHA256, "kind": "reviewed run-013 five-function H2 image"},
        {"base_sha256": BASE_SHA256, "ips_sha256": sha256(ips),
         "result_sha256": final_hash, "kind": "three production mapper replacements"},
    ]
    manifest["patched_sha256"] = final_hash
    manifest["mapper_replacements"] = {
        "scope": "three H2 persisted-byte-to-index helpers, each padded within its original 92-byte slot",
        "patch_builder_sha256": sha256(Path(__file__).read_bytes()),
        "production_build": compiler_metadata,
        "functions": {hex(address): {**symbols[address], "vma": hex(address),
                                       "original_span": SPAN,
                                       "payload_sha256": audit["patch_records"][i]["sha256"]}
                      for i, address in enumerate(sorted(OBJECTS))},
        "incoming_reference_audit": audit,
        "changed_from_run013_bytes": sum(a != b for a, b in zip(base, patched)),
    }
    (output / "code.h2-mappers.bin").write_bytes(patched)
    (output / "code.h2-mappers.ips").write_bytes(ips)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    negative_source = ROOT / "experiments/semantic_equivalence/h2_config_mapper_candidates.cpp"
    negative_object = output / "negative-control-candidates.o"
    negative_build = compile_tu_armv6k(negative_source, negative_object, ROOT)
    if negative_build.returncode:
        raise RuntimeError(negative_build.stderr or "negative-control compile failed")
    negative_symbols = extract_elf_functions_detailed(negative_object)
    wrong_blob, wrong_relocations = negative_symbols["candidate_002cab70_wrong_map"]
    if wrong_relocations:
        raise ValueError(f"wrong-map control has unexpected relocations: {wrong_relocations}")
    from tools.h2_config_mapper_experiment import MapperRunner, validate_mapper_blob
    wrong_case = make_case(11, random.Random(7 ^ 0xC0FFEE), "wrong-map-at-11")
    correct_run = MapperRunner(base, 0x002CAB70, TABLES[0x002CAB70]).run(wrong_case)
    wrong_run = MapperRunner(base, 0x002CAB70, TABLES[0x002CAB70], wrong_blob).run(wrong_case)
    negative_control = {"name": "A threshold 10 changed to 11", "input": 11,
                        "original_result": correct_run.result, "wrong_candidate_result": wrong_run.result,
                        "detected": correct_run.result == 2 and wrong_run.result == 1,
                        "wrong_candidate_source_sha256": sha256(negative_source.read_bytes()),
                        "wrong_candidate_object_sha256": sha256(negative_object.read_bytes())}
    if not negative_control["detected"]:
        raise ValueError("wrong-map negative control was not detected")

    reports = []
    for seed in seeds:
        functions = []
        for address in sorted(OBJECTS):
            function = {"address": hex(address), "symbol": OBJECTS[address][0],
                        "table_address": hex(TABLES[address]),
                        "table_values": MAPPERS[address][1]}
            function.update(compare_final_images(base, patched, address, TABLES[address],
                                                 MAPPERS[address][1], seed, samples))
            functions.append(function)
        report = {"schema": 1, "seed": seed,
                  "passed": all(x["passed"] for x in functions) and negative_control["detected"],
                  "scope": "production mapper bodies at their final guest VMAs in the run-013 H2 image",
                  "original_sha256": sha256(original), "base_image_sha256": sha256(base),
                  "patched_image_sha256": final_hash, "manifest_sha256": sha256((output / "manifest.json").read_bytes()),
                  "source_sha256": {str(p): sha256(p.read_bytes()) for p in
                                    (ROOT / "src/engine/leaf_batch32_b.cpp", ROOT / "src/engine/leaf_batch32_c.cpp")},
                  "object_sha256": {str(p): sha256(p.read_bytes()) for p in (object_b, object_c)},
                  "production_build": compiler_metadata,
                  "patch_builder_sha256": sha256(Path(__file__).read_bytes()),
                  "functions": functions,
                  "negative_control": negative_control,
                  "limits": ["Only zero-extended byte callers are in the reviewed H2 contract.",
                             "Input table reads are compared by values, not identical access footprints.",
                             "No UI, scheduler, persistence, restart, or emulator behavior is established."]}
        report_path = output / f"report-seed-{seed}.json"
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        report["report_sha256"] = sha256(report_path.read_bytes())
        reports.append(report)
    summary = {"passed": all(r["passed"] for r in reports), "image_sha256": final_hash,
               "ips_sha256": sha256(ips), "manifest_sha256": sha256((output / "manifest.json").read_bytes()),
               "reports": [{"seed": r["seed"], "path": f"report-seed-{r['seed']}.json",
                            "sha256": r["report_sha256"], "passed": r["passed"]} for r in reports],
               "elapsed_seconds": round(time.perf_counter() - started, 3)}
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-image", type=Path, default=BASE_IMAGE)
    parser.add_argument("--original", type=Path, default=ORIGINAL_IMAGE)
    parser.add_argument("--object-b", type=Path, required=True)
    parser.add_argument("--object-c", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[7, 20261024])
    parser.add_argument("--samples", type=int, default=256)
    args = parser.parse_args()
    summary = build_and_validate(args.base_image, args.original, args.object_b,
                                 args.object_c, args.output, args.seeds, args.samples)
    print(json.dumps(summary, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
