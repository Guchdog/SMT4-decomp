#!/usr/bin/env python3
"""Differentially execute the readable 0x00151404 callback against pinned ARM."""
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
from tools.semantic_experiment import (
    DATA, DATA_SIZE, INJECT, RETURN, SP, STACK, STACK_SIZE, TEXT, arm, unicorn,
)
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ENTRY = 0x00151404
ENTRY_END = 0x00151468
DIV_HELPER = 0x002A337C
DIFF_HELPER = 0x0014D608
NESTED_HELPER = 0x0015258C
SPECIAL_HELPER = 0x002A464E
REFERENCE_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
SYMBOLS = ("candidate_00151404", "wrong_ordered_nan_branch_00151404",
           "wrong_skip_integral_helper_00151404")


def bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def f32(value: int) -> float:
    return struct.unpack("<f", struct.pack("<I", value & 0xffffffff))[0]


def _verify_image(image: bytes) -> None:
    if hashlib.sha256(image).hexdigest() != REFERENCE_SHA256:
        raise ValueError("code.bin is not the pinned US reference image")
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    decoded = list(cs.disasm(image[ENTRY-TEXT:ENTRY_END-TEXT], ENTRY))
    if not decoded or decoded[-1].address != ENTRY_END - 4 or decoded[-1].mnemonic != "pop":
        raise ValueError("callback instruction boundary no longer matches pinned map")
    if sum(i.size for i in decoded) != ENTRY_END - ENTRY:
        raise ValueError("callback boundary is not fully disassembled")


def _machine(image: bytes, candidates: dict[str, bytes], candidate_name: str,
             values: tuple[int, int, int]) -> dict:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
    uc.mem_map(TEXT, 0x400000, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
    uc.mem_write(TEXT, image)
    uc.mem_map(INJECT, 0x2000, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
    uc.mem_map(DATA, DATA_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
    uc.mem_map(STACK, STACK_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
    addresses = {}
    cursor = INJECT
    for name, code in candidates.items():
        addresses[name] = cursor
        uc.mem_write(cursor, code)
        cursor = (cursor + len(code) + 0x1f) & ~0x1f
    target = ENTRY if candidate_name == "original" else addresses[candidate_name]
    trace: list[int] = []
    helper_entries: list[dict] = []
    reads: list[dict] = []
    writes: list[dict] = []
    helper_targets = {DIV_HELPER, DIFF_HELPER, NESTED_HELPER, SPECIAL_HELPER}

    def code_hook(machine, address, _size, _user):
        if address == RETURN:
            machine.emu_stop()
            return
        trace.append(address)
        if address in helper_targets:
            helper_entries.append({
                "target": hex(address),
                "r0": hex(machine.reg_read(arm.UC_ARM_REG_R0)),
                "r1": hex(machine.reg_read(arm.UC_ARM_REG_R1)),
                "s0": hex(machine.reg_read(arm.UC_ARM_REG_S0)),
                "s1": hex(machine.reg_read(arm.UC_ARM_REG_S1)),
                "fpscr": hex(machine.reg_read(arm.UC_ARM_REG_FPSCR)),
            })

    def mem_hook(machine, access, address, size, value, _user):
        row = {"address": hex(address), "size": size, "pc": hex(machine.reg_read(arm.UC_ARM_REG_PC))}
        if access == unicorn.UC_MEM_READ:
            reads.append(row)
        elif access == unicorn.UC_MEM_WRITE:
            row["value"] = hex(value & ((1 << (size * 8)) - 1))
            writes.append(row)

    uc.hook_add(unicorn.UC_HOOK_CODE, code_hook)
    uc.hook_add(unicorn.UC_HOOK_MEM_READ | unicorn.UC_HOOK_MEM_WRITE, mem_hook)
    uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
    for i in range(13):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"), 0xA5A50000 | i)
    uc.reg_write(arm.UC_ARM_REG_R0, DATA + 0x80)
    uc.reg_write(arm.UC_ARM_REG_SP, SP)
    uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
    for i in range(8, 16):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_D{i}"), 0x1122334400000000 | i)
    uc.reg_write(arm.UC_ARM_REG_S0, values[0])
    uc.reg_write(arm.UC_ARM_REG_S1, values[1])
    uc.reg_write(arm.UC_ARM_REG_S2, values[2])
    uc.mem_write(DATA, bytes(i & 0xff for i in range(DATA_SIZE)))
    uc.mem_write(STACK, b"\xcd" * STACK_SIZE)
    initial_data = bytes(uc.mem_read(DATA, DATA_SIZE))
    initial_stack = bytes(uc.mem_read(SP - 0x100, 0x100))
    fault = None
    try:
        uc.emu_start(target, 0, count=4096)
    except unicorn.UcError as error:
        fault = f"{error}; pc={uc.reg_read(arm.UC_ARM_REG_PC):#x}"
    ended = uc.reg_read(arm.UC_ARM_REG_PC) == RETURN
    final_data = bytes(uc.mem_read(DATA, DATA_SIZE))
    final_stack = bytes(uc.mem_read(SP - 0x100, 0x100))
    return {
        "stopped": ended, "fault": fault,
        "s0": hex(uc.reg_read(arm.UC_ARM_REG_S0)),
        "r0": hex(uc.reg_read(arm.UC_ARM_REG_R0)),
        "sp": hex(uc.reg_read(arm.UC_ARM_REG_SP)),
        "fpscr": hex(uc.reg_read(arm.UC_ARM_REG_FPSCR)),
        "callee_saved": {f"r{i}": hex(uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}"))) for i in range(4, 12)},
        "d8_d15": [hex(uc.reg_read(getattr(arm, f"UC_ARM_REG_D{i}"))) for i in range(8, 16)],
        "trace": [hex(pc) for pc in trace], "helpers": helper_entries,
        "data_changed": final_data != initial_data,
        "stack_changed": final_stack != initial_stack,
        "reads": reads, "writes": writes,
    }


def _differential(image: bytes, candidates: dict[str, bytes], name: str,
                  values: tuple[int, int, int]) -> dict:
    original = _machine(image, candidates, "original", values)
    rebuilt = _machine(image, candidates, name, values)
    fields = ("s0", "sp", "fpscr", "callee_saved", "d8_d15", "data_changed")
    mismatches = [field for field in fields if original[field] != rebuilt[field]]
    same_fault = bool(original["fault"] and rebuilt["fault"]
                      and original["fault"] == rebuilt["fault"])
    if same_fault:
        # No callback return occurred, so post-fault SP/VFP preservation is not
        # an ABI observation. The matched fault site is retained as a domain limit.
        mismatches = [field for field in mismatches if field not in ("sp", "d8_d15")]
    def abi_args(rows):
        normalized = []
        for row in rows:
            target = int(row["target"], 16)
            args = {"target": row["target"], "fpscr": row["fpscr"]}
            if target == DIV_HELPER:
                args["s0"] = row["s0"]
            elif target == DIFF_HELPER:
                args.update({"s0": row["s0"], "s1": row["s1"]})
            elif target == NESTED_HELPER:
                args.update({"r0": row["r0"], "r1": row["r1"]})
            normalized.append(args)
        return normalized
    if abi_args(original["helpers"]) != abi_args(rebuilt["helpers"]):
        mismatches.append("helper_ABI_arguments")
    # r0 is caller-saved: record it, but it is not part of callback's return contract.
    if ((original["fault"] or rebuilt["fault"] or not original["stopped"] or not rebuilt["stopped"])
            and not same_fault):
        mismatches.append("execution/fault")
    return {"candidate": name, "input_bits": [hex(x) for x in values],
            "original": original, "rebuilt": rebuilt,
            "same_fault_domain_limit": same_fault,
            "helper_ABI_args_equal": abi_args(original["helpers"]) == abi_args(rebuilt["helpers"]),
            "mismatches": mismatches,
            "r0_equal": original["r0"] == rebuilt["r0"]}


def run_experiment(code_path: Path, source_path: Path, output_dir: Path) -> dict:
    image = code_path.read_bytes()
    _verify_image(image)
    output_dir.mkdir(parents=True, exist_ok=True)
    object_path = output_dir / "h1_type1_callback_candidate.o"
    build = compile_tu_armv6k(source_path, object_path, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr or "ARMv6K candidate compilation failed")
    extracted = extract_elf_functions_detailed(object_path)
    compiled = {}
    binary_validation = []
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    cs.detail = True
    for symbol, (code, relocations) in extracted.items():
        if relocations:
            raise ValueError(f"Unsupported relocation in {symbol}: {relocations}")
        decoded_all = list(cs.disasm(code, 0))
        returns = [index for index, item in enumerate(decoded_all)
                   if ((item.mnemonic == "pop" and "pc" in item.op_str)
                       or (item.mnemonic == "bx" and item.op_str == "lr"))]
        if not returns:
            raise ValueError(f"Candidate lacks ordinary ABI return: {symbol}")
        last_return = returns[-1]
        decoded = decoded_all[:last_return + 1]
        end = decoded[-1].address + decoded[-1].size
        if end > len(code) or (len(code) - end) % 4:
            raise ValueError(f"Candidate literal tail has invalid boundary: {symbol}")
        for item in decoded[:-1]:
            for operand in item.operands:
                if operand.type == capstone.CS_OP_MEM and item.reg_name(operand.mem.base) == "pc":
                    if not item.mnemonic.startswith(("ldr", "vldr")):
                        raise ValueError(f"Unsupported PC-relative access in {symbol}: {item.mnemonic}")
                    literal = (item.address + 8 + operand.mem.disp) & ~3
                    if literal < end or literal + 4 > len(code):
                        raise ValueError(f"Literal is not bounded internal data in {symbol}: {item}")
            if item.group(capstone.CS_GRP_JUMP) and item.operands and item.operands[0].type == capstone.CS_OP_IMM:
                if not 0 <= item.operands[0].imm < end:
                    raise ValueError(f"Branch escapes candidate in {symbol}: {item}")
        compiled[symbol] = code
        binary_validation.append({"symbol": symbol, "symbol_bytes": len(code),
                                 "executable_bytes": end, "bounded_literal_tail_bytes": len(code) - end,
                                 "relocations": 0, "return": f"{decoded[-1].mnemonic} {decoded[-1].op_str}"})
    missing = set(SYMBOLS) - compiled.keys()
    if missing:
        raise ValueError(f"Missing candidate symbols: {sorted(missing)}")
    cases = [
        ("zero_interval", (bits(.5), bits(.5), bits(.5))),
        ("equal_sample", (bits(.5), bits(1.0), bits(.5))),
        ("below_start", (bits(.5), bits(1.0), bits(.25))),
        ("inside_positive", (bits(.5), bits(1.0), bits(.75))),
        ("at_upper", (bits(.5), bits(1.0), bits(1.0))),
        ("above_upper", (bits(.5), bits(1.0), bits(1.25))),
        ("negative_interval", (bits(1.0), bits(.5), bits(.75))),
        ("negative_interval_below", (bits(1.0), bits(.5), bits(.25))),
        ("rounding_near_half", (bits(.25), bits(1.0), bits(.625))),
        ("positive_infinity_sample", (bits(.5), bits(1.0), 0x7f800000)),
        ("qnan_sample", (bits(.5), bits(1.0), 0x7fc00000)),
    ]
    reports = []
    for label, vals in cases:
        row = _differential(image, compiled, "candidate_00151404", vals)
        row["label"] = label
        reports.append(row)
    # Controls are deliberately required to diverge on inputs targeting their mutation.
    wrong_branch = _differential(image, compiled, "wrong_ordered_nan_branch_00151404",
                                 (bits(.5), bits(1.0), 0x7fc00000))
    wrong_helper = _differential(image, compiled, "wrong_skip_integral_helper_00151404",
                                 (bits(.5), bits(1.0), bits(.375)))
    if any(row["mismatches"] for row in reports):
        status = "partial_mismatch"
    elif any(row["same_fault_domain_limit"] for row in reports):
        status = "passed_with_exceptional_domain_limit"
    else:
        status = "candidate_cases_passed"
    if not wrong_branch["mismatches"] or "0x2a337c" not in [x["target"] for x in wrong_helper["original"]["helpers"]]:
        raise AssertionError("negative control did not exercise the intended branch/helper mutation")
    report = {
        "schema_version": 1, "task_id": "h1-type1-callback-candidate",
        "outcome": status, "evidence_type": "synthetic Unicorn differential: pinned original ARM callback/helpers versus compiled C++ candidate",
        "reference_sha256": REFERENCE_SHA256,
        "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "object_sha256": hashlib.sha256(object_path.read_bytes()).hexdigest(),
        "object": str(object_path), "cases": reports,
        "binary_validation": binary_validation,
        "original_callback_pcs": [hex(pc) for pc in range(ENTRY, ENTRY_END, 4)],
        "negative_controls": {"ordered_nan_branch": wrong_branch, "skip_integral_helper": wrong_helper},
        "coverage": ["zero interval", "sample equal/below/inside/at/above", "positive and negative interval",
                     "boundary quotient", "positive infinity", "quiet NaN", "both control-flow paths"],
        "direct_helpers": [hex(DIV_HELPER), hex(DIFF_HELPER)],
        "limitations": ["Inputs are synthetic; no live runtime state was sampled.",
                        "Callback selection remains unproven; static registration is not runtime selection.",
                        "The callback relies on original helper bodies at 0x2A337C and 0x14D608; their behavior is not reconstructed.",
                        "Exceptional indirect helper target 0x2A464E may fault or remain outside exercised FP domain.",
                        "This isolates callback entry/return and does not establish caller, menu, visible UI, or runtime equivalence.",
                        "r0 is caller-saved and may differ; the known caller overwrites it immediately after return."],
    }
    report_path = output_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "build/semantic-equivalence/real-assets/exefs/code.bin")
    parser.add_argument("--source", type=Path, default=ROOT / "experiments/semantic_equivalence/h1_type1_callback_candidate.cpp")
    parser.add_argument("--output", type=Path, default=ROOT / "build/agent-work/H1-semantic/h1-type1-callback-candidate/sleep-20261025-type1-callback")
    args = parser.parse_args()
    report = run_experiment(args.code, args.source, args.output)
    print(f"{report['outcome']}: {args.output / 'report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
