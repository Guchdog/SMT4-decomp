import tempfile
import subprocess
import sys
import json
import unittest
from pathlib import Path
import struct

import capstone
from unicorn import UC_ARCH_ARM, UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE, UC_MODE_ARM, Uc
from unicorn import arm_const

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "experiments/semantic_equivalence/h18_002b5c2c_candidate.cpp"
IMAGE = ROOT / "extracted/exefs/code.bin"
ENTRY = 0x002B5C2C
DATA = 0x02000000
STACK = 0x08000000
SP = STACK + 0x1000
INJECT = 0x01000000
RETURN = 0x01001000


def execute_thumb(code_image, body, words):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(0x00100000, 0x00400000)
    uc.mem_write(0x00100000, code_image)
    uc.mem_map(DATA, 0x1000)
    uc.mem_map(STACK, 0x2000)
    uc.mem_map(INJECT, 0x2000)
    pointer = DATA + 0x100
    payload = struct.pack("<" + "H" * (len(words) + 1), *words, 0)
    uc.mem_write(pointer, payload)
    if body is not None:
        uc.mem_write(INJECT, body)
        start = INJECT | 1
    else:
        start = ENTRY | 1
    uc.reg_write(arm_const.UC_ARM_REG_CPSR, 0x10 | 0xF0000000)
    initial = [0x11110000 + i for i in range(13)]
    for i, value in enumerate(initial):
        uc.reg_write(getattr(arm_const, f"UC_ARM_REG_R{i}"), value)
    uc.reg_write(arm_const.UC_ARM_REG_R0, pointer)
    uc.reg_write(arm_const.UC_ARM_REG_SP, SP)
    uc.reg_write(arm_const.UC_ARM_REG_LR, RETURN)
    reads = set()
    writes = set()
    stopped = []

    def code_hook(machine, address, size, _):
        if address == RETURN:
            stopped.append(address)
            machine.emu_stop()

    def memory_hook(_machine, access, address, size, _value, _):
        target = reads if access == 16 else writes  # UC_MEM_READ
        for at in range(address, address + size):
            target.add(at)

    uc.hook_add(UC_HOOK_CODE, code_hook)
    uc.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, memory_hook)
    uc.emu_start(start, 0, count=256)
    return {
        "r0": uc.reg_read(arm_const.UC_ARM_REG_R0),
        "pc": uc.reg_read(arm_const.UC_ARM_REG_PC),
        "sp": uc.reg_read(arm_const.UC_ARM_REG_SP),
        "lr": uc.reg_read(arm_const.UC_ARM_REG_LR),
        "preserved": tuple(uc.reg_read(getattr(arm_const, f"UC_ARM_REG_R{i}")) for i in range(4, 12)),
        "nzcv": uc.reg_read(arm_const.UC_ARM_REG_CPSR) & 0xF0000000,
        "thumb_state": bool(uc.reg_read(arm_const.UC_ARM_REG_CPSR) & 0x20),
        "reads": reads,
        "writes": writes,
        "stopped": bool(stopped),
        "memory": bytes(uc.mem_read(pointer, len(payload))),
        "payload": payload,
    }


class TestThumbEmission(unittest.TestCase):
    def test_candidate_is_emitted_as_thumb(self):
        self.assertTrue(CANDIDATE.is_file(), "typed Thumb candidate has not been written")
        with tempfile.TemporaryDirectory(prefix="h18-2b5c2c-thumb-") as directory:
            obj = Path(directory) / "candidate.o"
            result = compile_tu_armv6k(CANDIDATE, obj, ROOT)
            self.assertEqual(result.returncode, 0, result.stderr)
            symbols = extract_elf_functions_detailed(obj)
        self.assertIn("candidate_002b5c2c", symbols)
        code, relocations = symbols["candidate_002b5c2c"]
        self.assertFalse(relocations)
        dis = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
        instructions = list(dis.disasm(code, 0))
        self.assertTrue(instructions)
        self.assertEqual(sum(item.size for item in instructions), len(code))
        self.assertEqual(instructions[-1].mnemonic, "bx")
        self.assertEqual(instructions[-1].op_str, "lr")


class TestHalfwordCountContract(unittest.TestCase):
    def test_original_and_candidate_match_count_reads_and_abi(self):
        image = IMAGE.read_bytes()
        with tempfile.TemporaryDirectory(prefix="h18-2b5c2c-diff-") as directory:
            obj = Path(directory) / "candidate.o"
            result = compile_tu_armv6k(CANDIDATE, obj, ROOT)
            self.assertEqual(result.returncode, 0, result.stderr)
            body, relocations = extract_elf_functions_detailed(obj)["candidate_002b5c2c"]
        self.assertFalse(relocations)
        for words in ([], [0x1234], [0x0001, 0x8000, 0xFFFF, 0x1234]):
            with self.subTest(words=words):
                original = execute_thumb(image, None, words)
                rebuilt = execute_thumb(image, body, words)
                expected_reads = set(range(DATA + 0x100, DATA + 0x100 + 2 * (len(words) + 1)))
                self.assertTrue(original["stopped"], original)
                self.assertTrue(rebuilt["stopped"], rebuilt)
                self.assertEqual(original["r0"], len(words))
                self.assertEqual(rebuilt["r0"], len(words))
                self.assertEqual(original["reads"], expected_reads)
                self.assertEqual(rebuilt["reads"], expected_reads)
                self.assertEqual(original["writes"], set())
                self.assertEqual(rebuilt["writes"], set())
                self.assertEqual(original["preserved"], rebuilt["preserved"])
                self.assertEqual(original["sp"], rebuilt["sp"])
                self.assertEqual(original["lr"], RETURN)
                self.assertEqual(rebuilt["lr"], RETURN)
                self.assertFalse(original["thumb_state"])
                self.assertFalse(rebuilt["thumb_state"])
                self.assertEqual(original["memory"], rebuilt["memory"])
                self.assertEqual(original["nzcv"], rebuilt["nzcv"])


class TestOfflineRunner(unittest.TestCase):
    def test_pinned_reference_has_all_fifteen_blx_callers(self):
        from tools.h18_002b5c2c_experiment import verify_reference
        evidence = verify_reference(IMAGE.read_bytes())
        self.assertEqual(len(evidence["direct_callers"]), 15)
        self.assertTrue(all(item["kind"] == "blx" for item in evidence["direct_callers"]))
        self.assertEqual(evidence["aligned_pointer_sites"], [])

    def test_seeded_runner_detects_negative_controls_and_composes_callers(self):
        for seed in (20261116, 17):
            with tempfile.TemporaryDirectory(prefix=f"h18-2b5c2c-{seed}-") as directory:
                output = Path(directory)
                completed = subprocess.run(
                    [sys.executable, str(ROOT / "tools/h18_002b5c2c_experiment.py"),
                     "--code", str(IMAGE), "--seed", str(seed), "--samples", "8",
                     "--output", str(output)], cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
                report = json.loads((output / "report.json").read_text(encoding="utf-8"))
            self.assertTrue(report["passed"], report)
            self.assertEqual(report["seed"], seed)
            self.assertEqual(report["cases"], 13)
            self.assertTrue(all(item["passed"] for item in report["caller_windows"]))
            self.assertEqual({item["kind"] for item in report["caller_windows"]},
                             {"count_times_2", "count_plus_terminator_times_2"})
            self.assertEqual({item["name"] for item in report["negative_controls"]},
                             {"byte_step", "inclusive_terminator", "wrong_count"})
            self.assertTrue(all(item["detected"] for item in report["negative_controls"]))


if __name__ == "__main__":
    unittest.main()
