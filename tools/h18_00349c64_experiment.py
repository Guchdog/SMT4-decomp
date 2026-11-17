#!/usr/bin/env python3
"""Offline differential check for the standalone ARM constant-return entry."""
from __future__ import annotations

import argparse
import capstone
import hashlib
import json
from pathlib import Path
import random
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.semantic_experiment import (  # noqa: E402
    DATA, DATA_SIZE, RETURN, SP, STACK, STACK_SIZE, TEXT, Case, Runner, difference,
    arm, unicorn,
)
from tools.semantic_experiment_support import compile_candidate_symbols  # noqa: E402

ADDRESS = 0x00349C64
SPAN_SIZE = 720
ADJACENT_ENTRY = 0x00349C70
EXPECTED = bytes.fromhex("0100a0e31eff2fe1")
MASK32 = 0xFFFFFFFF
CANDIDATE = ROOT / "experiments/semantic_equivalence/h18_00349c64_candidate.cpp"


def _static_text_xrefs(image: bytes) -> tuple[list[str], list[dict]]:
    """Find direct calls and recognized PC-relative refs to the pointer table."""
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    decoder.detail = True
    direct_callers = []
    table_references = []
    text_size = int(json.loads((ROOT / "config/game_info.json").read_text(
        encoding="utf-8"))["segments"]["text"]["size"], 16)
    for offset in range(0, text_size - 3, 4):
        insn = next(decoder.disasm(image[offset:offset + 4], TEXT + offset, count=1), None)
        if insn is None or not insn.operands:
            continue
        if insn.mnemonic in ("bl", "blx"):
            operand = insn.operands[0]
            if operand.type == capstone.CS_OP_IMM and (operand.imm & MASK32) == ADDRESS:
                direct_callers.append(f"0x{insn.address:08x}")
        target = None
        for operand in insn.operands:
            if operand.type == capstone.CS_OP_MEM and insn.reg_name(operand.mem.base) == "pc":
                target = ((insn.address + 8 + operand.mem.disp) & MASK32) & ~3
                break
        if (target is None and insn.mnemonic in ("add", "sub") and
                len(insn.operands) >= 3 and
                insn.reg_name(insn.operands[1].reg) == "pc" and
                insn.operands[2].type == capstone.CS_OP_IMM):
            immediate = insn.operands[2].imm
            target = (insn.address + 8 +
                      (immediate if insn.mnemonic == "add" else -immediate)) & MASK32
        if target is not None and 0x0047299C <= target < 0x004729B4:
            table_references.append({"site": f"0x{insn.address:08x}",
                                     "target": f"0x{target:08x}",
                                     "instruction": f"{insn.mnemonic} {insn.op_str}"})
    return direct_callers, table_references


def _aligned_function_pointers(image: bytes) -> list[str]:
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    segments = [game["segments"][name] for name in ("text", "rodata", "data")]
    hits = []
    for offset in range(0, len(image) - 3, 4):
        if struct.unpack_from("<I", image, offset)[0] not in (ADDRESS, ADDRESS | 1):
            continue
        for segment in segments:
            file_start = int(segment["file_offset"], 16)
            size = int(segment["size"], 16)
            if file_start <= offset < file_start + size:
                vaddr = int(segment["vaddr"], 16) + offset - file_start
                hits.append(f"0x{vaddr:08x}")
                break
    return hits


def verify_reference(code_path: Path) -> dict:
    image = Path(code_path).read_bytes()
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    actual_hash = hashlib.sha256(image).hexdigest()
    if actual_hash != game["code_sha256"] or len(image) != game["code_bin_size"]:
        raise ValueError("code.bin does not match the pinned game revision")
    with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
        import csv
        rows = list(csv.DictReader(stream))
    row = next((row for row in rows if int(row["address"], 16) == ADDRESS), None)
    if row is None or int(row["size"]) != SPAN_SIZE:
        raise ValueError("Function ledger no longer describes the 720-byte compound span")
    if int(row["address"], 16) + int(row["size"]) <= ADJACENT_ENTRY:
        raise ValueError("The adjacent 0x00349c70 routine is outside the recorded span")
    offset = ADDRESS - TEXT
    actual = image[offset:offset + len(EXPECTED)]
    if actual != EXPECTED:
        raise ValueError(f"8-byte entry changed: got {actual.hex()}")
    pointer_sites = _aligned_function_pointers(image)
    direct_callers, table_references = _static_text_xrefs(image)
    return {
        "image_sha256": actual_hash,
        "entry_bytes": actual.hex(),
        "entry_size": len(actual),
        "catalog_span_size": int(row["size"]),
        "adjacent_entry": f"0x{ADJACENT_ENTRY:08x}",
        "direct_callers": direct_callers,
        "aligned_function_pointer_sites": pointer_sites,
        "pointer_search_note": (
            "Aligned little-endian 32-bit scan found exact ARM/Thumb function-pointer "
            "values only; data around 0x0047299c..0x004729b0 contains six consecutive "
            "copies of 0x00349c64. Their owning table/consumer is unresolved."
            if pointer_sites else
            "No aligned little-endian exact function-pointer values found; unaligned or "
            "computed references are outside this scan."
        ),
        "recognized_table_reference_instructions": table_references,
        "caller_search_limits": (
            "Direct scan examines every 4-byte-aligned word in the declared ARM text "
            "range for immediate BL/BLX to the target. It is a static pattern scan and "
            "may see data as instructions; it cannot find indirect calls, computed targets, "
            "or unaligned/relocated references. Pointer scan covers aligned words only."
        ),
    }


def make_cases(seed: int, samples: int = 128):
    if samples < 0:
        raise ValueError("samples must be nonnegative")
    rng = random.Random(seed ^ ADDRESS)
    for index in range(samples):
        regs = tuple(rng.getrandbits(32) for _ in range(13))
        data = rng.randbytes(DATA_SIZE)
        stack = rng.randbytes(STACK_SIZE)
        nzcv = rng.getrandbits(4) << 28
        yield Case(f"seed-{seed}-case-{index}", regs, data, stack, nzcv)


def _state(runner: Runner) -> dict:
    uc = runner.uc
    regs = tuple(uc.reg_read(getattr(arm, f"UC_ARM_REG_R{index}")) for index in range(13))
    return {
        "regs": regs,
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        "lr": uc.reg_read(arm.UC_ARM_REG_LR),
        "nzcv": uc.reg_read(arm.UC_ARM_REG_CPSR) & 0xF0000000,
    }


def _contract_failure(result, state: dict, case: Case) -> str | None:
    if result.fault:
        return f"fault: {result.fault}"
    if not result.stopped:
        return "no return to LR before instruction budget"
    if result.result != 1:
        return f"return r0 is {result.result:#x}, expected 1"
    if state["regs"][1:] != case.registers[1:]:
        return "a non-return general register changed"
    if state["sp"] != SP or state["lr"] != RETURN:
        return "SP or LR changed"
    if state["nzcv"] != case.nzcv:
        return "NZCV changed"
    stack_offset = SP - STACK
    if result.data != case.data or result.live_stack != case.stack[
            stack_offset:stack_offset + STACK_SIZE // 2]:
        return "memory changed"
    if result.reads or result.writes:
        return "memory access footprint is nonempty"
    if result.pc != RETURN:
        return f"returned to {result.pc:#x}, expected LR {RETURN:#x}"
    return None


def _negative_controls() -> dict[str, bytes]:
    word = lambda instruction: struct.pack("<I", instruction)
    bx_lr = word(0xE12FFF1E)
    return {
        "wrong_return": word(0xE3A00000) + bx_lr,
        "changed_flags": word(0xE3A00001) + word(0xE1500000) + bx_lr,
        "wrote_memory": word(0xE3A00001) + word(0xE5810000) + bx_lr,
    }


def run(code_path: Path, output: Path, seed: int = 20261024, samples: int = 128) -> dict:
    if unicorn is None or arm is None:
        raise RuntimeError("Unicorn is required for ARM differential execution")
    if samples <= 0:
        raise ValueError("samples must be positive")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    evidence = verify_reference(code_path)
    object_path = output / "h18_00349c64_candidate.o"
    compiled = compile_candidate_symbols(CANDIDATE, object_path, ROOT,
                                         ["candidate_00349c64"])
    candidate = compiled["candidate_00349c64"]
    original_runner = Runner(Path(code_path).read_bytes(), ADDRESS)
    candidate_runner = Runner(Path(code_path).read_bytes(), ADDRESS, candidate)
    case_results = []
    for case in make_cases(seed, samples):
        original = original_runner.run(case)
        original_state = _state(original_runner)
        rebuilt = candidate_runner.run(case)
        rebuilt_state = _state(candidate_runner)
        original_issue = _contract_failure(original, original_state, case)
        candidate_issue = _contract_failure(rebuilt, rebuilt_state, case)
        differential_issue = difference(original, rebuilt, returns_value=True,
                                         compare_flags=True)
        if original_issue or candidate_issue or differential_issue:
            case_results.append({
                "label": case.label, "passed": False,
                "original_issue": original_issue, "candidate_issue": candidate_issue,
                "differential_issue": differential_issue,
            })
            break
        case_results.append({"label": case.label, "passed": True})

    # Use distinct, deterministic states that make each control observable.
    base = next(make_cases(seed, 1))
    negative_controls = []
    for name, body in _negative_controls().items():
        control_case = base
        if name == "changed_flags":
            control_case = Case(base.label + "-flags", base.registers, base.data,
                                base.stack, 0)
        elif name == "wrote_memory":
            regs = list(base.registers)
            regs[1] = DATA + 0x100
            control_case = Case(base.label + "-memory", tuple(regs), base.data,
                                base.stack, base.nzcv)
        control = Runner(Path(code_path).read_bytes(), ADDRESS, body)
        actual = control.run(control_case)
        baseline = Runner(Path(code_path).read_bytes(), ADDRESS).run(control_case)
        # Compare flags explicitly: the shared comparison defaults to ignoring them
        # for isolated functions, while this contract requires exact preservation.
        reason = difference(baseline, actual, returns_value=True, compare_flags=True)
        if name == "wrong_return" and actual.result == baseline.result:
            reason = None
        negative_controls.append({"name": name, "detected": reason is not None,
                                  "reason": reason})

    report = {
        "schema_version": 1,
        "address": f"0x{ADDRESS:08x}",
        "seed": seed,
        "cases": len(case_results),
        "passed_cases": sum(result["passed"] for result in case_results),
        "passed": all(result["passed"] for result in case_results)
                  and all(item["detected"] for item in negative_controls),
        "reference": evidence,
        "candidate_source": str(CANDIDATE.relative_to(ROOT)).replace("\\", "/"),
        "candidate_source_sha256": hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(),
        "object": object_path.name,
        "object_sha256": hashlib.sha256(object_path.read_bytes()).hexdigest(),
        "candidate_bytes": candidate.hex(),
        "negative_controls": negative_controls,
        "first_failure": next((item for item in case_results if not item["passed"]), None),
        "limits": [
            "Seeded ARM-state register/flag/memory states are bounded differential evidence, not proof over all hardware contexts.",
            "This run validates only the 8-byte entry, not the adjacent routine or 720-byte catalogued span.",
            "No caller-composition or game-runtime comparison is performed.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n",
                                        encoding="utf-8")
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path, required=True,
                        help="new or existing output directory")
    parser.add_argument("--seed", type=int, default=20261024)
    parser.add_argument("--samples", type=int, default=128)
    args = parser.parse_args(argv)
    try:
        report = run(args.code, args.output, args.seed, args.samples)
    except (OSError, ValueError, RuntimeError) as error:
        parser.error(str(error))
    print(json.dumps({"passed": report["passed"], "seed": report["seed"],
                      "cases": report["cases"], "output": str(args.output / "report.json")}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
