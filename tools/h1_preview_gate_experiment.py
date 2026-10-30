#!/usr/bin/env python3
"""Differentially compare the H1 preview gate with a helper-entry-only stub."""
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
import capstone.arm as cap_arm
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, find_clang, get_armv6k_flags
from tools.semantic_experiment import INJECT, RETURN, STACK, STACK_SIZE, TEXT, require_unicorn, unicorn, arm

GATE = 0x0025A2BC
GATE_SIZE = 0x5C
GATE_INSTRUCTIONS_SIZE = 0x58
HELPER = 0x002BF9F0
HELPER_SIZE = 664
CALLER = 0x001E9D08
GLOBAL_SLOT = 0x0043E278
OBJECT = 0x02000100
OBJECT_SIZE = 0xFEC
DATA = 0x02000000
DATA_SIZE = 0x2000
SP = STACK + 0x1000
EXPECTED_IMAGE = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
PRIMARY_FLAG = 0xF2B
SECONDARY_FLAG = 0x1C
BUSY_BYTE = 0xD6D
SPRITE_OFFSET = 0xD74
SYMBOLS = (
    "h1_preview_gate_candidate",
    "negative_preview_gate_wrong_offset",
    "negative_preview_gate_wrong_branch",
    "negative_preview_gate_wrong_helper_polarity",
)


def verify_reference(image: bytes) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if digest != EXPECTED_IMAGE:
        raise ValueError("code.bin SHA-256 does not match the pinned game revision")
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    gate_bytes = image[GATE - TEXT:GATE - TEXT + GATE_SIZE]
    gate_insns = list(decoder.disasm(gate_bytes[:GATE_INSTRUCTIONS_SIZE], GATE))
    gate_expected = [
        ("ldr", "r0, [pc, #0x50]"), ("push", "{r4, lr}"),
        ("ldr", "r4, [r0]"), ("ldrb", "r0, [r4, #0xf2b]"),
        ("cmp", "r0, #0"), ("ldrbne", "r0, [r4, #0x1c]"),
        ("cmpne", "r0, #0"), ("beq", "#0x25a304"),
        ("add", "r0, r4, #0xc00"), ("add", "r0, r0, #0xe8"),
        ("ldrsb", "r0, [r0, #0x85]"), ("cmp", "r0, #0"),
        ("bne", "#0x25a30c"), ("add", "r0, r4, #0xc00"),
        ("add", "r0, r0, #0x174"), ("bl", "#0x2bf9f0"),
        ("cmp", "r0, #0"), ("beq", "#0x25a30c"),
        ("mov", "r0, #1"), ("pop", "{r4, pc}"),
        ("mov", "r0, #0"), ("pop", "{r4, pc}"),
    ]
    actual = [(i.mnemonic.lower(), i.op_str.lower()) for i in gate_insns]
    if actual != gate_expected:
        raise ValueError(f"pinned preview-gate instruction sequence changed: {actual}")
    if sum(i.size for i in gate_insns) != GATE_INSTRUCTIONS_SIZE:
        raise ValueError("preview-gate instruction-byte count changed")
    if gate_bytes[-4:] != struct.pack("<I", GLOBAL_SLOT):
        raise ValueError("preview-gate global pointer literal mismatch")

    helper_bytes = image[HELPER - TEXT:HELPER - TEXT + HELPER_SIZE]
    helper_insns = list(decoder.disasm(helper_bytes, HELPER))
    if (not helper_insns or sum(i.size for i in helper_insns) != HELPER_SIZE
            or helper_insns[0].mnemonic.lower() != "push"):
        raise ValueError("preview helper did not decode to its pinned full extent")
    helper_key = [(i.mnemonic.lower(), i.op_str.lower()) for i in helper_insns]
    required_helper = [
        ("push", "{r4, r5, r6, r7, r8, lr}"),
        ("movs", "r4, r0"), ("beq", "#0x2bfa10"),
    ]
    if helper_key[:3] != required_helper:
        raise ValueError("preview helper does not consume its sole pointer in r0")
    if not any(mnemonic == "ldrsb" and operands == "r0, [r4, #0x8a]"
               for mnemonic, operands in helper_key):
        raise ValueError("preview helper signed-byte result source +0x8A not found")
    if helper_key[-3:] != [("ldrsb", "r0, [r4, #0x8a]"),
                           ("strb", "r6, [r4, #0x85]"),
                           ("pop", "{r4, r5, r6, r7, r8, pc}")]:
        raise ValueError("preview helper terminal signed-byte result sequence changed")
    caller_bytes = image[CALLER - TEXT:CALLER - TEXT + 0x2C]
    caller_insns = list(decoder.disasm(caller_bytes, CALLER))
    caller_prefix = [(i.mnemonic.lower(), i.op_str.lower()) for i in caller_insns[:9]]
    if caller_prefix != [
        ("nop", ""), ("bl", "#0x289924"), ("cmp", "r0, #0"),
        ("nop", ""), ("beq", "#0x1ea62c"), ("bl", "#0x25a2bc"),
        ("cmp", "r0, #0"), ("nop", ""), ("beq", "#0x1ea62c"),
    ]:
        raise ValueError(f"H1 state-5 readiness call order changed: {caller_prefix}")
    caller_calls = [i for i in caller_insns if i.address == 0x001E9D1C]
    if len(caller_calls) != 1 or caller_calls[0].mnemonic.lower() != "bl" \
            or caller_calls[0].op_str.lower() != "#0x25a2bc":
        raise ValueError("H1 state-5 caller no-argument BL to Camp_IsPreviewReady changed")
    return {
        "sha256": digest,
        "gate": {"address": hex(GATE), "window_end": hex(GATE + GATE_SIZE),
                 "instruction_bytes": GATE_INSTRUCTIONS_SIZE, "size": len(gate_bytes),
                 "sha256": hashlib.sha256(gate_bytes).hexdigest(), "instruction_count": len(gate_insns)},
        "helper": {"address": hex(HELPER), "size": HELPER_SIZE,
                   "sha256": hashlib.sha256(helper_bytes).hexdigest(),
                   "entry": [f"{i.address:#x}: {i.mnemonic} {i.op_str}" for i in helper_insns[:4]],
                   "signed_result_loads": [f"{i.address:#x}" for i in helper_insns
                                            if i.mnemonic.lower() == "ldrsb" and "#0x8a" in i.op_str.lower()]},
        "caller": {"address": "0x1e9d1c", "callee": hex(GATE), "formal_arguments": 0},
        "global_slot": hex(GLOBAL_SLOT),
        "object_offsets": {"primary_flag_u8": hex(PRIMARY_FLAG),
                           "secondary_flag_u8": hex(SECONDARY_FLAG),
                           "busy_s8": hex(BUSY_BYTE), "helper_object": hex(SPRITE_OFFSET)},
    }


def validate_blob(code: bytes, name: str) -> dict:
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    decoder.detail = True
    instructions = list(decoder.disasm(code, INJECT))
    if not instructions:
        raise ValueError(f"no ARM instructions in {name}")
    if any(i.mnemonic.lower() == "bl" for i in instructions):
        raise ValueError(f"{name} contains an unexpected direct call")
    if not any(i.mnemonic.lower() == "blx" for i in instructions):
        raise ValueError(f"{name} does not call helper through the pinned function pointer")
    loaded_literals = set()
    for insn in instructions:
        for operand in insn.operands:
            if operand.type == cap_arm.ARM_OP_MEM and operand.mem.base == cap_arm.ARM_REG_PC:
                target = (insn.address + 8 + operand.mem.disp) & 0xFFFFFFFF
                if not INJECT <= target < INJECT + len(code):
                    raise ValueError(f"{name} has an external PC-relative read to {target:#x}")
                offset = target - INJECT
                if offset + 4 <= len(code):
                    loaded_literals.add(struct.unpack_from("<I", code, offset)[0])
    if {GLOBAL_SLOT, HELPER} - loaded_literals:
        raise ValueError(f"{name} is missing a pinned global/helper pointer literal")
    decoded_bytes = sum(i.size for i in instructions)
    if decoded_bytes != len(code):
        undecoded = len(code) - decoded_bytes
        if undecoded > 16 or undecoded % 4 or decoded_bytes == 0:
            raise ValueError(f"{name} has unvalidated undecoded tail ({undecoded} bytes)")
    return {"symbol": name, "size": len(code), "decoded_instruction_bytes": decoded_bytes,
            "undecoded_tail_bytes": len(code) - decoded_bytes}


def compile_candidates(output: Path) -> tuple[dict[str, bytes], Path, dict]:
    output.mkdir(parents=True, exist_ok=True)
    source = ROOT / "experiments/semantic_equivalence/h1_preview_gate_candidate.cpp"
    obj = output / "h1_preview_gate_candidate.o"
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "ARMv6K candidate compilation failed")
    extracted = extract_elf_functions_detailed(obj)
    compiled: dict[str, bytes] = {}
    validations = []
    for name in SYMBOLS:
        if name not in extracted:
            raise ValueError(f"missing candidate symbol {name}")
        code, relocations = extracted[name]
        if relocations:
            raise ValueError(f"unsupported relocation in {name}: {relocations}")
        validations.append(validate_blob(code, name))
        compiled[name] = code
    meta = {"source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "object_sha256": hashlib.sha256(obj.read_bytes()).hexdigest(),
            "object_path": str(obj), "compiler": str(find_clang()),
            "compiler_flags": get_armv6k_flags(ROOT, find_clang()),
            "symbol_validation": validations}
    return compiled, obj, meta


class GateMachine:
    def __init__(self, image: bytes, candidate: bytes | None = None):
        require_unicorn()
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.arm = arm
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.mem_map(TEXT, 0x400000, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
        self.uc.mem_write(TEXT, image)
        self.uc.mem_map(INJECT, 0x4000, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
        self.uc.mem_map(DATA, DATA_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.uc.mem_map(STACK, STACK_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.uc.mem_protect(GLOBAL_SLOT & ~0xFFF, 0x1000,
                            unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.candidate = candidate
        if candidate is not None:
            self.uc.mem_write(INJECT, candidate)
        self.response = 0
        self.calls: list[dict] = []
        self.fault: str | None = None
        self.stopped = False
        self.stop_pc = RETURN
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._hook)

    def _hook(self, uc, address, _size, _user):
        if address == RETURN:
            self.stopped = True
            uc.emu_stop()
        elif address == HELPER:
            arg = uc.reg_read(self.arm.UC_ARM_REG_R0)
            self.calls.append({"entry": hex(address), "arg": hex(arg), "response": self.response})
            uc.reg_write(self.arm.UC_ARM_REG_R0, self.response & 0xFFFFFFFF)
            uc.reg_write(self.arm.UC_ARM_REG_PC, uc.reg_read(self.arm.UC_ARM_REG_LR))

    def execute(self, primary: int, secondary: int, busy: int, response: int) -> dict:
        obj = bytearray([0xA5]) * OBJECT_SIZE
        obj[PRIMARY_FLAG] = primary & 0xFF
        obj[SECONDARY_FLAG] = secondary & 0xFF
        obj[BUSY_BYTE] = busy & 0xFF
        self.uc.mem_write(OBJECT, bytes(obj))
        self.uc.mem_write(GLOBAL_SLOT, struct.pack("<I", OBJECT))
        self.uc.mem_write(STACK, bytes([0x5A]) * STACK_SIZE)
        self.response = int(response)
        self.calls.clear()
        self.fault = None
        self.stopped = False

        a = self.arm
        initial = {f"r{i}": 0xA5A50000 | i for i in range(4, 12)}
        initial.update({"sp": SP, "d8": 0x1122334455667708, "d9": 0x1122334455667709,
                        "d10": 0x112233445566770A, "d11": 0x112233445566770B,
                        "d12": 0x112233445566770C, "d13": 0x112233445566770D,
                        "d14": 0x112233445566770E, "d15": 0x112233445566770F,
                        "fpscr": 0x01000000})
        for i in range(13):
            self.uc.reg_write(getattr(a, f"UC_ARM_REG_R{i}"), (0xA5A50000 | i) & 0xFFFFFFFF)
        self.uc.reg_write(a.UC_ARM_REG_CPSR, 0x10)
        self.uc.reg_write(a.UC_ARM_REG_SP, SP)
        self.uc.reg_write(a.UC_ARM_REG_LR, RETURN)
        for name, value in initial.items():
            reg_name = "UC_ARM_REG_" + name.upper()
            if name.startswith("d"):
                self.uc.reg_write(getattr(a, reg_name), value)
        self.uc.reg_write(a.UC_ARM_REG_FPSCR, initial["fpscr"])
        before = bytes(self.uc.mem_read(OBJECT, OBJECT_SIZE))
        start = INJECT if self.candidate is not None else GATE
        try:
            self.uc.emu_start(start, 0, count=256)
        except unicorn.UcError as error:
            self.fault = f"{self.uc.reg_read(a.UC_ARM_REG_PC):#x}: {error}"
        final = bytes(self.uc.mem_read(OBJECT, OBJECT_SIZE))
        state = {f"r{i}": self.uc.reg_read(getattr(a, f"UC_ARM_REG_R{i}")) for i in range(4, 12)}
        state.update({"sp": self.uc.reg_read(a.UC_ARM_REG_SP),
                      "d8": self.uc.reg_read(a.UC_ARM_REG_D8),
                      "d9": self.uc.reg_read(a.UC_ARM_REG_D9),
                      "d10": self.uc.reg_read(a.UC_ARM_REG_D10),
                      "d11": self.uc.reg_read(a.UC_ARM_REG_D11),
                      "d12": self.uc.reg_read(a.UC_ARM_REG_D12),
                      "d13": self.uc.reg_read(a.UC_ARM_REG_D13),
                      "d14": self.uc.reg_read(a.UC_ARM_REG_D14),
                      "d15": self.uc.reg_read(a.UC_ARM_REG_D15),
                      "fpscr": self.uc.reg_read(a.UC_ARM_REG_FPSCR)})
        return {"fault": self.fault, "stopped": self.stopped,
                "pc": hex(self.uc.reg_read(a.UC_ARM_REG_PC)),
                "result": self.uc.reg_read(a.UC_ARM_REG_R0),
                "calls": self.calls.copy(), "object_before": before.hex(),
                "object_after": final.hex(), "state": state, "initial_state": initial}


def expected_result(primary: int, secondary: int, busy: int, response: int) -> int:
    if (primary & 0xFF) == 0 or (secondary & 0xFF) == 0:
        return 1
    if ((busy & 0xFF) ^ 0x80) - 0x80 != 0:
        return 0
    return int(response != 0)


def compare_case(image: bytes, code: bytes, primary: int, secondary: int,
                 busy: int, response: int, label: str) -> dict:
    original = GateMachine(image).execute(primary, secondary, busy, response)
    candidate = GateMachine(image, code).execute(primary, secondary, busy, response)
    errors = []
    for name, result, expected_pc in (("original", original, RETURN),
                                      ("candidate", candidate, RETURN)):
        if result["fault"] is not None or not result["stopped"] or result["pc"] != hex(expected_pc):
            errors.append(f"{name} did not complete normally")
        if result["object_before"] != result["object_after"]:
            errors.append(f"{name} changed object memory")
        for reg, value in result["initial_state"].items():
            if result["state"].get(reg) != value:
                errors.append(f"{name} failed to preserve {reg}")
    if original["result"] != candidate["result"]:
        errors.append("r0 result differs")
    if original["result"] != expected_result(primary, secondary, busy, response):
        errors.append("original result differs from branch contract")
    if original["calls"] != candidate["calls"]:
        errors.append("helper call order/argument/result differs")
    if len(original["calls"]) > 1:
        errors.append("unexpected repeated helper call")
    return {"name": label, "inputs": {"primary": primary & 0xFF, "secondary": secondary & 0xFF,
                                      "busy": busy & 0xFF, "helper_result": response},
            "passed": not errors, "errors": errors,
            "expected_result": expected_result(primary, secondary, busy, response),
            "original": original, "candidate": candidate}


def run_experiment(code_path: Path, output: Path) -> dict:
    image = code_path.read_bytes()
    reference = verify_reference(image)
    blobs, object_path, metadata = compile_candidates(output)
    cases = []
    # Every boolean branch combination is exercised for helper outputs on both
    # sides of zero. Outputs are scripted even when short-circuiting makes them unused.
    for primary in (0, 1):
        for secondary in (0, 1):
            for busy in (0, 1):
                for response in (-7, 0, 1, 9):
                    cases.append(compare_case(image, blobs[SYMBOLS[0]], primary,
                                              secondary, busy, response,
                                              f"boolean branch matrix p={primary} s={secondary} b={busy} h={response}"))
    boundaries = (0, 1, 0x7F, 0x80, 0xFF)
    for value in boundaries:
        cases.append(compare_case(image, blobs[SYMBOLS[0]], value, 1, 1, -1,
                                  f"primary byte boundary {value:#04x}"))
        cases.append(compare_case(image, blobs[SYMBOLS[0]], 1, value, 1, -1,
                                  f"secondary byte boundary {value:#04x}"))
        cases.append(compare_case(image, blobs[SYMBOLS[0]], 1, 1, value, 1,
                                  f"signed busy byte boundary {value:#04x}"))
    for response in (-2147483648, -1, 0, 1, 2147483647):
        cases.append(compare_case(image, blobs[SYMBOLS[0]], 1, 1, 0, response,
                                  f"helper signed result boundary {response}"))

    negative = []
    # Wrong sprite offset is caught at the actual external helper entry even
    # though a stub can return the same status for both addresses.
    orig = GateMachine(image).execute(1, 1, 0, 1)
    wrong_offset = GateMachine(image, blobs[SYMBOLS[1]]).execute(1, 1, 0, 1)
    offset_detected = (orig["result"] == wrong_offset["result"] == 1
                       and orig["calls"][0]["arg"] == hex(OBJECT + SPRITE_OFFSET)
                       and wrong_offset["calls"][0]["arg"] == hex(OBJECT + SPRITE_OFFSET + 1))
    negative.append({"name": "wrong_helper_object_offset", "detected": offset_detected,
                     "original_arg": orig["calls"][0]["arg"],
                     "negative_arg": wrong_offset["calls"][0]["arg"]})

    orig = GateMachine(image).execute(0, 1, 0, 0)
    wrong_branch = GateMachine(image, blobs[SYMBOLS[2]]).execute(0, 1, 0, 0)
    branch_detected = (orig["result"] == 1 and wrong_branch["result"] == 0
                       and len(orig["calls"]) == 0 and len(wrong_branch["calls"]) == 1)
    negative.append({"name": "wrong_primary_branch_polarity", "detected": branch_detected,
                     "original_result": orig["result"], "negative_result": wrong_branch["result"],
                     "original_helper_calls": orig["calls"], "negative_helper_calls": wrong_branch["calls"]})

    orig = GateMachine(image).execute(1, 1, 0, -1)
    wrong_helper = GateMachine(image, blobs[SYMBOLS[3]]).execute(1, 1, 0, -1)
    helper_detected = (orig["result"] == 1 and wrong_helper["result"] == 0
                       and orig["calls"] == wrong_helper["calls"])
    negative.append({"name": "wrong_helper_result_polarity", "detected": helper_detected,
                     "original_result": orig["result"], "negative_result": wrong_helper["result"],
                     "calls": orig["calls"]})

    source = ROOT / "experiments/semantic_equivalence/h1_preview_gate_candidate.cpp"
    report = {
        "task_id": "h1-preview-readiness-candidate",
        "passed": all(item["passed"] for item in cases) and all(item["detected"] for item in negative),
        "reference": reference, "candidate": metadata,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "object_sha256": hashlib.sha256(object_path.read_bytes()).hexdigest(),
        "cases": cases, "case_count": len(cases), "negative_controls": negative,
        "evidence": {"compiled": "passed", "arm_differential": "passed",
                     "caller": "partial", "runtime": "not_run"},
        "limitations": [
            "The original gate and candidate run with a scripted stub only at 0x002BF9F0; the helper body, callbacks and animation side effects are not executed.",
            "The H1 state-5 caller calls 0x0025A2BC with no formal arguments and branches on r0, but this gate-only experiment does not execute the surrounding callback.",
            "g_FrameTex is null-initialized and its constructor allocates/publishes and zeroes a 0xFEC scene; detailed lifecycle/readiness of the raw object at scene+0xD74 is not established by this slice. No physical/runtime behavior is claimed."
        ],
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"H1 preview gate experiment {'PASS' if report['passed'] else 'FAIL'}; "
          f"{sum(item['passed'] for item in cases)}/{len(cases)} cases, "
          f"{sum(item['detected'] for item in negative)}/{len(negative)} controls; report: {output / 'report.json'}")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "build/azahar-validation/exefs/code.bin")
    parser.add_argument("--output", type=Path, required=True, help="fresh private output directory")
    args = parser.parse_args()
    report = run_experiment(args.code, args.output)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
