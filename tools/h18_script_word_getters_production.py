"""Differentially test the production-source H18 script low-byte getters."""
from __future__ import annotations

import argparse
import csv
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import random
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.semantic_experiment import (
    DATA, DATA_SIZE, INJECT, RETURN, SP, STACK_SIZE, TEXT, Case, Runner,
    arm_branch, difference, validate_leaf,
)

EXPECTED_BYTE_OFFSETS = {0x002345F0: 0x48, 0x002345FC: 0x4A}
HALFWORDS = (
    0x0000, 0x0001, 0x007F, 0x0080, 0x00FF, 0x0100, 0x017F, 0x0180,
    0x01FF, 0x7FFF, 0x8000, 0x80FF, 0xFF00, 0xFF7F, 0xFF80, 0xFFFF,
)
CALLER_PAIRS = (
    {"caller": "0x0038c43c", "base_reg": 10, "halfword_call": 0x0038C5E8,
     "byte_call": 0x0038C5F4, "stop": 0x0038C600},
    {"caller": "0x0038cdf4", "base_reg": 4, "halfword_call": 0x0038CE60,
     "byte_call": 0x0038CE6C, "stop": 0x0038CE78},
    {"caller": "0x0038d7b0", "base_reg": 10, "halfword_call": 0x0038D8C0,
     "byte_call": 0x0038D8CC, "stop": 0x0038D8D8},
    {"caller": "0x0038de60", "base_reg": 4, "halfword_call": 0x0038DF78,
     "byte_call": 0x0038DF84, "stop": 0x0038DF90},
)


def verify_production_source(source_path: Path) -> dict[int, int]:
    """Require the two production symbols to be plain byte-index getters."""
    source = Path(source_path).read_text(encoding="utf-8")
    result: dict[int, int] = {}
    for address, offset in EXPECTED_BYTE_OFFSETS.items():
        name = f"script_vm_func_{address:08x}"
        pattern = re.compile(
            rf'extern\s+"C"\s+u32\s+{name}\s*\(\s*const\s+u8\s*\*\s*p\s*\)\s*\{{(?P<body>.*?)\}}',
            re.DOTALL,
        )
        match = pattern.search(source)
        if not match:
            raise ValueError(f"missing or incompatible production definition: {name}")
        body = match.group("body")
        if re.search(r"\basm\b|reinterpret_cast|uint16_t", body):
            raise ValueError(f"unsafe or assembly implementation in {name}")
        if not re.search(rf"return\s+p\s*\[\s*0x{offset:x}\s*\]\s*;", body):
            raise ValueError(f"{name} must return byte p[0x{offset:x}]")
        result[address] = offset
    return result


def verify_reference(code_path: Path, game_info_path: Path, ledger_path: Path) -> dict:
    import capstone

    image = Path(code_path).read_bytes()
    game = json.loads(Path(game_info_path).read_text(encoding="utf-8"))
    digest = hashlib.sha256(image).hexdigest()
    if len(image) != int(game["code_bin_size"]) or digest != game["code_sha256"]:
        raise ValueError("Pinned original image identity mismatch")
    with Path(ledger_path).open(encoding="utf-8", newline="") as stream:
        catalog = list(csv.DictReader(stream))
    rows = {int(row["address"], 16): row for row in catalog}
    expected = {
        0x002345F0: bytes.fromhex("b804d0e1ff0000e21eff2fe1"),
        0x002345FC: bytes.fromhex("ba04d0e1ff0000e21eff2fe1"),
    }
    references = {address: {"branches": [], "pointer_words": []} for address in expected}
    interior_branches = []
    code_size = 0x002FE624
    for address, code in expected.items():
        row = rows.get(address)
        if row is None or int(row["size"]) != 12 or row["status"] != "non_matching":
            raise ValueError(f"Expected promoted 12-byte non_matching ledger row at {address:#x}")
        actual = image[address - TEXT:address - TEXT + 12]
        if actual != code:
            raise ValueError(f"Original bytes changed at {address:#010x}")
    # Audit aligned ARM BL targets and aligned words across the complete image.
    for offset in range(0, code_size - 3, 4):
        word = struct.unpack_from("<I", image, offset)[0]
        site = TEXT + offset
        if (word & 0x0F000000) == 0x0B000000:
            displacement = word & 0x00FFFFFF
            if displacement & 0x00800000:
                displacement -= 0x01000000
            target = site + 8 + displacement * 4
            for address in expected:
                if address <= target < address + 12:
                    caller = next((row["name"] for row in catalog
                                   if int(row["address"], 16) <= site <
                                   int(row["address"], 16) + int(row["size"])), "unknown")
                    references[address]["branches"].append(
                        {"site": hex(site), "caller": caller, "target": hex(target)})
                    if target != address:
                        interior_branches.append({"site": hex(site), "target": hex(target)})
    for offset in range(0, len(image) - 3, 4):
        word = struct.unpack_from("<I", image, offset)[0]
        site = TEXT + offset
        for address in expected:
            if word == address:
                references[address]["pointer_words"].append(hex(site))
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    originals = {
        hex(address): {
            "bytes": code.hex(),
            "instructions": [f"{i.mnemonic} {i.op_str}" for i in cs.disasm(code, address)],
        }
        for address, code in expected.items()
    }
    return {"reference_sha256": digest, "originals": originals,
            "external_references": {hex(a): v for a, v in references.items()},
            "interior_branch_refs": interior_branches}


def compile_production_symbols(output: Path) -> tuple[dict[int, bytes], str, str]:
    source = ROOT / "src/engine/leaf_matching.cpp"
    obj = output / "leaf_matching.production.o"
    build = compile_tu_armv6k(source, obj, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr or "Production translation unit compilation failed")
    extracted = extract_elf_functions_detailed(obj)
    compiled: dict[int, bytes] = {}
    for address in EXPECTED_BYTE_OFFSETS:
        name = f"script_vm_func_{address:08x}"
        if name not in extracted:
            raise ValueError(f"production symbol not extracted: {name}")
        code, relocations = extracted[name]
        if relocations:
            raise ValueError(f"Unexpected relocation in {name}: {relocations}")
        validate_leaf(code)
        compiled[address] = code
    return compiled, hashlib.sha256(source.read_bytes()).hexdigest(), hashlib.sha256(obj.read_bytes()).hexdigest()


def _case(address: int, seed: int, index: int, value: int) -> Case:
    rng = random.Random((seed ^ address) + index * 0x9E3779B1)
    registers = [rng.getrandbits(32) for _ in range(13)]
    registers[0] = DATA + 0x100 + (index % 8) * 4
    offset = EXPECTED_BYTE_OFFSETS[address]
    data = bytearray(rng.randbytes(DATA_SIZE))
    struct.pack_into("<H", data, registers[0] - DATA + offset, value)
    other = 0x4A if offset == 0x48 else 0x48
    struct.pack_into("<H", data, registers[0] - DATA + other, value ^ 0x5AA5)
    return Case(f"case-{index}-halfword-{value:#06x}", tuple(registers), bytes(data),
                rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)


def _run_full(runner: Runner, case: Case, *, start=None, stops=(RETURN,)):
    result = runner.run(case, start=start, stops=stops)
    import unicorn
    from unicorn import arm_const as arm
    state = {
        "r0_r12": tuple(runner.uc.reg_read(r) for r in runner.reg_ids),
        "sp": runner.uc.reg_read(arm.UC_ARM_REG_SP),
        "lr": runner.uc.reg_read(arm.UC_ARM_REG_LR),
        "pc": result.pc,
        "nzcv": result.nzcv,
    }
    return result, state


def _ordinary_ram_difference(original, candidate, original_state, candidate_state, **kwargs):
    # Preserve and report read sets separately; the ordinary-RAM contract does
    # not expose access width, while state, writes, flags, and continuation do.
    result = difference(replace(original, reads=candidate.reads), candidate,
                        compare_flags=True, **kwargs)
    if result is None and original_state != candidate_state:
        result = "full GPR/LR/SP/NZCV/PC state differs"
    return result


def _caller_runner(image: bytes, compiled: dict[int, bytes], patched: bool) -> Runner:
    if not patched:
        return Runner(image, 0x002345FC)
    halfword = compiled[0x002345FC]
    byte = compiled[0x002345F0]
    runner = Runner(image, 0x002345FC, replacement=halfword + byte,
                    replacement_validator=lambda _code: None)
    runner.uc.mem_write(0x002345F0, arm_branch(0x002345F0, INJECT + len(halfword)))
    return runner


def run(code_path: Path, output: Path, *, seed: int = 7, samples: int = 64,
        game_info_path: Path | None = None, ledger_path: Path | None = None) -> dict:
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    game_info_path = game_info_path or ROOT / "config/game_info.json"
    ledger_path = ledger_path or ROOT / "config/functions.csv"
    source_path = ROOT / "src/engine/leaf_matching.cpp"
    verify_production_source(source_path)
    refs = verify_reference(code_path, game_info_path, ledger_path)
    image = Path(code_path).read_bytes()
    compiled, source_hash, object_hash = compile_production_symbols(output)
    functions = []
    for address, offset in EXPECTED_BYTE_OFFSETS.items():
        cases = [_case(address, seed, i, value) for i, value in enumerate(HALFWORDS)]
        start_index = len(cases)
        for i in range(samples):
            value = random.Random(seed ^ address ^ i).getrandbits(16)
            cases.append(_case(address, seed, start_index + i, value))
        outcomes = []
        for case in cases:
            original, original_state = _run_full(Runner(image, address), case)
            candidate, candidate_state = _run_full(Runner(image, address, compiled[address]), case)
            reason = _ordinary_ram_difference(original, candidate, original_state, candidate_state)
            outcomes.append({"case": case.label, "passed": reason is None, "reason": reason})
        sample_reads = _case(address, seed, 0, 0x80FF)
        original_read = _run_full(Runner(image, address), sample_reads)[0].reads
        candidate_read = _run_full(Runner(image, address, compiled[address]), sample_reads)[0].reads
        functions.append({"address": hex(address), "offset": hex(offset), "cases": len(outcomes),
                          "passed": all(x["passed"] for x in outcomes), "results": outcomes,
                          "candidate_bytes": len(compiled[address]),
                          "candidate_sha256": hashlib.sha256(compiled[address]).hexdigest(),
                          "candidate_disassembly": _disassemble(compiled[address], address),
                          "original_read_footprint": sorted(hex(x) for x in original_read),
                          "candidate_read_footprint": sorted(hex(x) for x in candidate_read)})
    # Sensitivity checks use directed bytes: wrong offset sees a distinct byte;
    # omitted mask returns 0x80ff rather than 0xff.
    controls = []
    control_case = _case(0x002345F0, seed, 0, 0x80FF)
    control_data = bytearray(control_case.data)
    struct.pack_into("<H", control_data, control_case.registers[0] - DATA + 0x4A, 0x0011)
    control_case = replace(control_case, data=bytes(control_data))
    control_codes = {
        "wrong_offset": bytes.fromhex("4a00d0e51eff2fe1"),
        "omitted_mask": bytes.fromhex("b804d0e11eff2fe1"),
    }
    for name, code in control_codes.items():
        wrong, wrong_state = _run_full(Runner(image, 0x002345F0, code), control_case)
        ref, ref_state = _run_full(Runner(image, 0x002345F0), control_case)
        reason = _ordinary_ram_difference(ref, wrong, ref_state, wrong_state)
        controls.append({"name": name, "detected": reason is not None, "reason": reason})
    # One paired composition per each of the four statically observed caller
    # functions; every window includes both getter calls and both result uses.
    caller_results = []
    for index, window in enumerate(CALLER_PAIRS):
        case = _case(0x002345FC, seed, 100 + index, 0x005E)
        registers = list(case.registers)
        registers[window["base_reg"]] = DATA + 0x100
        data = bytearray(case.data)
        base = DATA + 0x100 + 0x28
        struct.pack_into("<H", data, base - DATA + 0x48, 0x00D3)
        struct.pack_into("<H", data, base - DATA + 0x4A, 0x005E)
        caller_case = replace(case, registers=tuple(registers), data=bytes(data))
        start = window["halfword_call"] - 4
        stops = (window["stop"],)
        original_runner = _caller_runner(image, compiled, False)
        candidate_runner = _caller_runner(image, compiled, True)
        original, original_state = _run_full(original_runner, caller_case, start=start, stops=stops)
        candidate, candidate_state = _run_full(candidate_runner, caller_case, start=start, stops=stops)
        reason = _ordinary_ram_difference(original, candidate, original_state, candidate_state,
                                          returns_value=False, caller_window=True)
        caller_results.append({"caller": window["caller"],
                               "calls": [hex(window["halfword_call"]), hex(window["byte_call"])],
                               "start": hex(start), "stop": hex(window["stop"]),
                               "passed": reason is None, "reason": reason, "cases": 1,
                               "original_reads": sorted(hex(x) for x in original.reads),
                               "candidate_reads": sorted(hex(x) for x in candidate.reads),
                               "consumed_values": {"r4_or_r7": "0x5e", "r2": "0xd3"}})
    report = {
        "schema": 1, "seed": seed, "samples_per_function": samples,
        "passed": all(x["passed"] for x in functions)
                  and all(x["detected"] for x in controls)
                  and all(x["passed"] for x in caller_results),
        "reference_sha256": refs["reference_sha256"],
        "source_sha256": source_hash, "object_sha256": object_hash,
        "originals": refs["originals"], "external_references": refs["external_references"],
        "interior_branch_refs": refs["interior_branch_refs"],
        "functions": functions, "negative_controls": controls,
        "caller_windows": caller_results,
        "limitations": [
            "Candidate reads one byte while original LDRH reads two; evidence is limited to aligned ordinary RAM with both bytes readable and no read-width-visible side effects.",
            "Caller composition covers one paired representative window in each of four direct-call functions; remaining direct call sites and full callers are not executed.",
            "Aligned ARM BL and aligned pointer-word reference scan excludes Thumb, computed/indirect, relocated and runtime-generated references.",
            "No MMIO, unaligned or invalid pointers, concurrent observation, exception behavior, or game runtime was tested."
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def _disassemble(code: bytes, address: int) -> list[str]:
    import capstone
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    return [f"{i.mnemonic} {i.op_str}" for i in cs.disasm(code, address)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--samples", type=int, default=64)
    args = parser.parse_args()
    report = run(args.code, args.output, seed=args.seed, samples=args.samples)
    print(json.dumps({"passed": report["passed"], "report": str(args.output / "report.json")}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
