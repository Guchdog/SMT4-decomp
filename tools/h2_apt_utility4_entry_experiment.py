#!/usr/bin/env python3
"""Offline isolated ARM comparison of entry 0x002c0efc; controlled wrapper."""
import argparse
import hashlib
import json
import random
import struct
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import unicorn as u
from unicorn.arm_const import *
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.semantic_experiment_support import load_pinned_reference

ADDRESS, WRAPPER = 0x002c0efc, 0x002b5a1c
TEXT, STACK, DATA, END = 0x00100000, 0x08000000, 0x02000000, 0x01000000
SP = STACK + 0x1000
REGS = [UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
        UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
        UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11, UC_ARM_REG_R12]
SOURCE = ROOT / "experiments/semantic_equivalence/h2_apt_utility4_entry_candidate.cpp"

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def execute(image, replacement, case):
    uc = u.Uc(u.UC_ARCH_ARM, u.UC_MODE_ARM)
    uc.mem_map(TEXT, (len(image) + 0xfff) & ~0xfff)
    uc.mem_write(TEXT, image)
    if replacement is not None:
        uc.mem_write(ADDRESS, replacement)
    uc.mem_map(STACK, 0x2000)
    uc.mem_write(STACK, case["stack"])
    uc.mem_map(DATA, 0x1000)
    uc.mem_write(DATA, case["data"])
    uc.mem_map(END, 0x1000)
    uc.reg_write(UC_ARM_REG_CPSR, 0x10 | case["flags"])
    for reg, value in zip(REGS, case["regs"]):
        uc.reg_write(reg, value)
    uc.reg_write(UC_ARM_REG_SP, SP)
    uc.reg_write(UC_ARM_REG_LR, END)
    uc.reg_write(UC_ARM_REG_CPSR, 0x10 | case["flags"])
    calls = []
    def hook(machine, address, size, _):
        if address == WRAPPER:
            sp = machine.reg_read(UC_ARM_REG_SP)
            stack_words = struct.unpack("<2I", machine.mem_read(sp, 8))
            args = [machine.reg_read(r) for r in REGS[:4]] + list(stack_words)
            calls.append({"args": args, "sp_align": sp % 8, "thumb": bool(machine.reg_read(UC_ARM_REG_CPSR) & 0x20)})
            machine.reg_write(UC_ARM_REG_R0, case["ret"])
            machine.reg_write(UC_ARM_REG_PC, machine.reg_read(UC_ARM_REG_LR))
    uc.hook_add(u.UC_HOOK_CODE, hook)
    uc.emu_start(ADDRESS, END, count=200)
    return {"pc": uc.reg_read(UC_ARM_REG_PC), "sp": uc.reg_read(UC_ARM_REG_SP),
            "r0": uc.reg_read(UC_ARM_REG_R0),
            "preserved": [uc.reg_read(r) for r in REGS[4:12]],
            "data": bytes(uc.mem_read(DATA, 0x1000)).hex(),
            "live_stack": bytes(uc.mem_read(SP, 0x1000)).hex(), "calls": calls}

def differences(left, right, case):
    errors = []
    for label, got in (("original", left), ("candidate", right)):
        if got["pc"] != END: errors.append(label + ": return PC")
        if got["sp"] != SP: errors.append(label + ": stack restoration")
        if got["preserved"] != case["regs"][4:12]: errors.append(label + ": callee saves")
        if len(got["calls"]) != 1: errors.append(label + ": wrapper count")
        elif got["calls"][0] != {"args": [4,0,0,0,0,0], "sp_align": 0, "thumb": False}:
            errors.append(label + ": wrapper arguments/ABI")
        if got["r0"] != case["ret"]: errors.append(label + ": return")
        if got["data"] != case["data"].hex(): errors.append(label + ": external data")
        if got["live_stack"] != case["stack"][0x1000:].hex(): errors.append(label + ": live stack")
    for key in ("pc", "sp", "r0", "preserved", "data", "live_stack", "calls"):
        if left[key] != right[key]: errors.append("differential: " + key)
    return errors

def make_case(rng, result):
    return {"regs": [rng.getrandbits(32) for _ in range(13)],
            "flags": rng.getrandbits(4) << 28, "ret": result,
            "stack": rng.randbytes(0x2000), "data": rng.randbytes(0x1000)}

def run(code, output, seed):
    output.mkdir(parents=True, exist_ok=False)
    pinned = load_pinned_reference(code, ROOT / "config/game_info.json", ROOT / "config/functions.csv")
    source_hash = sha(SOURCE)
    obj = output / "candidate.o"
    compilation = compile_tu_armv6k(SOURCE, obj, ROOT)
    if compilation.returncode: raise RuntimeError(compilation.stderr)
    symbols = extract_elf_functions_detailed(obj)
    names = ("candidate_002c0efc", "wrong_command", "wrong_argument", "discarded_return")
    blobs = {}
    for name in names:
        blob, relocations = symbols[name]
        if relocations: raise ValueError("unexpected relocation " + name)
        blobs[name] = blob
    rng = random.Random(seed)
    results = [0, 1, 0x7fffffff, 0x80000000, 0xffffffff] + [rng.getrandbits(32) for _ in range(59)]
    failures = []
    for number, result in enumerate(results):
        case = make_case(rng, result)
        errors = differences(execute(pinned.image, None, case), execute(pinned.image, blobs[names[0]], case), case)
        if errors: failures.append({"case": number, "errors": errors})
    case = make_case(rng, 0x80000000)
    baseline = execute(pinned.image, None, case)
    negatives = {name: differences(baseline, execute(pinned.image, blobs[name], case), case) for name in names[1:]}
    expected = {"wrong_command": "candidate: wrapper arguments/ABI",
                "wrong_argument": "candidate: wrapper arguments/ABI",
                "discarded_return": "candidate: return"}
    passed = not failures and all(expected[k] in negatives[k] for k in expected)
    if sha(SOURCE) != source_hash: raise RuntimeError("source changed during run")
    report = {"passed": passed, "seed": seed, "cases": len(results), "failures": failures,
              "negative_controls": negatives, "reference_sha256": sha(code), "source_sha256": source_hash,
              "object_sha256": sha(obj), "compile_command": compilation.args,
              "limits": ["controlled wrapper only", "ARM entry only; no Thumb callers", "no real IPC, runtime, caller composition or integration"]}
    (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"passed": passed, "cases": len(results), "failures": failures, "negative_controls": negatives}))
    return passed

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if run(args.code, args.output, args.seed) else 1)
