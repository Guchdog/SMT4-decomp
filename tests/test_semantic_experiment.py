"""Synthetic controls for the oracle: no proprietary game image required."""
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest

from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed
from tools.semantic_experiment import (
    ROOT, TEXT, DATA, DATA_SIZE, STACK_SIZE, Candidate, Case, CANDIDATES,
    Runner, arm_branch, cases, difference, patch_image, validate_leaf,
)


def instructions(*words):
    return struct.pack("<" + "I" * len(words), *words)


@unittest.skipUnless(importlib.util.find_spec("unicorn"), "Optional Unicorn experiment dependency")
class TestSemanticOracle(unittest.TestCase):
    def case(self, r0=7):
        return Case("synthetic", (r0,) + tuple(range(1, 13)),
                    bytes(DATA_SIZE), bytes(STACK_SIZE), 0)

    def runner(self, code):
        return Runner(code, TEXT)

    def test_distinct_code_with_same_result_passes(self):
        # mov r0,#1; bx lr versus mov r1,#1; mov r0,r1; bx lr.
        a = self.runner(instructions(0xE3A00001, 0xE12FFF1E)).run(self.case())
        b = self.runner(instructions(0xE3A01001, 0xE1A00001, 0xE12FFF1E)).run(self.case())
        self.assertIsNone(difference(a, b))

    def test_wrong_return_and_wrong_memory_are_detected(self):
        a = self.runner(instructions(0xE3A00001, 0xE12FFF1E)).run(self.case())
        b = self.runner(instructions(0xE3A00002, 0xE12FFF1E)).run(self.case())
        self.assertIn("return value", difference(a, b))
        # str r1,[r0] with different immediate data; void return contract.
        a = self.runner(instructions(0xE3A01001, 0xE5801000, 0xE12FFF1E)).run(self.case(DATA))
        b = self.runner(instructions(0xE3A01002, 0xE5801000, 0xE12FFF1E)).run(self.case(DATA))
        self.assertIn("data memory", difference(a, b, returns_value=False))

    def test_void_result_is_ignored_but_abi_violation_is_not(self):
        a = self.runner(instructions(0xE12FFF1E)).run(self.case())
        b = self.runner(instructions(0xE3A00001, 0xE12FFF1E)).run(self.case())
        self.assertIsNone(difference(a, b, returns_value=False))
        b = self.runner(instructions(0xE3A04000, 0xE12FFF1E)).run(self.case())
        self.assertIn("callee-saved", difference(a, b, returns_value=False))

    def test_faults_and_instruction_exhaustion_never_pass(self):
        # Both read an unmapped address: equality of failures is not equivalence.
        a = self.runner(instructions(0xE5900000, 0xE12FFF1E)).run(self.case())
        self.assertIn("fault", difference(a, a))
        # b . loops forever; bounded execution must fail closed.
        a = self.runner(instructions(0xEAFFFFFE)).run(self.case(), budget=16)
        self.assertIn("budget", difference(a, a))

    def test_same_final_memory_with_extra_access_is_detected(self):
        # str r1,[r0] writes the same existing zero but changes access footprint.
        case = self.case(DATA)
        case = Case(case.label, (DATA, 0) + case.registers[2:], case.data, case.stack, case.nzcv)
        a = self.runner(instructions(0xE12FFF1E)).run(case)
        b = self.runner(instructions(0xE5801000, 0xE12FFF1E)).run(case)
        self.assertIn("write footprint", difference(a, b, returns_value=False))

    def test_original_call_to_relocated_replacement_returns_to_caller(self):
        # BL original leaf, then a continuation at TEXT+4.
        image = instructions(0xEB000002, 0xE12FFF1E, 0, 0, 0xE3A00001, 0xE12FFF1E)
        original = Runner(image, TEXT + 16)
        replacement = Runner(image, TEXT + 16, instructions(0xE3A01001, 0xE1A00001, 0xE12FFF1E))
        a = original.run(self.case(), start=TEXT, stops=(TEXT + 4,))
        b = replacement.run(self.case(), start=TEXT, stops=(TEXT + 4,))
        self.assertIsNone(difference(a, b, caller_window=True))
        self.assertEqual(b.pc, TEXT + 4)

    def test_leaf_validation_rejects_unhandled_relocation_shapes(self):
        validate_leaf(instructions(0xE3A00001, 0xE12FFF1E))
        for code in (instructions(0xEB000000, 0xE12FFF1E),
                     instructions(0xE59F0000, 0xE12FFF1E), b"\x00"):
            with self.assertRaises(ValueError):
                validate_leaf(code)
        with self.assertRaises(ValueError):
            arm_branch(TEXT, TEXT + 1)
        with self.assertRaises(ValueError):
            arm_branch(TEXT, 0x80000000)

    def test_patch_artifact_stays_in_existing_padding_and_ips_roundtrips(self):
        text_size = 0x300000
        game = {"segments": {"text": {"vaddr": hex(TEXT), "file_offset": "0x0",
                                     "size": hex(text_size), "aligned_size": hex(text_size + 0x1000)}}}
        image = bytes(text_size + 0x2000)
        leaf = instructions(0xE3A00001, 0xE12FFF1E)
        compiled = {c.symbol: leaf for c in CANDIDATES}
        patched, ips, manifest = patch_image(image, compiled, game)
        self.assertEqual(len(patched), len(image))
        self.assertEqual(patched[text_size + 0x1000:], image[text_size + 0x1000:])
        self.assertEqual(len(manifest), len(CANDIDATES))
        allowed = set(range(text_size, text_size + 0x1000))
        for candidate in CANDIDATES:
            allowed.update(range(candidate.address - TEXT, candidate.address - TEXT + 4))
        self.assertTrue(all(i in allowed for i, (a, b) in enumerate(zip(image, patched)) if a != b))
        # Independent basic IPS reader checks that the actual artifact regenerates
        # exactly the tested patched image, not just a matching patch manifest.
        rebuilt = bytearray(image)
        cursor = 5
        self.assertEqual(ips[:5], b"PATCH")
        while ips[cursor:cursor + 3] != b"EOF":
            offset = int.from_bytes(ips[cursor:cursor + 3], "big")
            length = int.from_bytes(ips[cursor + 3:cursor + 5], "big")
            self.assertGreater(length, 0)
            cursor += 5
            rebuilt[offset:offset + length] = ips[cursor:cursor + length]
            cursor += length
        self.assertEqual(cursor + 3, len(ips))
        self.assertEqual(bytes(rebuilt), patched)
        dirty = bytearray(image)
        dirty[text_size] = 1
        with self.assertRaises(ValueError):
            patch_image(bytes(dirty), compiled, game)
        too_small = {"segments": {"text": dict(game["segments"]["text"], aligned_size=hex(text_size + 4))}}
        with self.assertRaises(ValueError):
            patch_image(image, compiled, too_small)

    def test_generators_cover_byte_domain_and_valid_cursor_alias(self):
        byte = Candidate(0x00394614, "byte_equality")
        values = {c.data[c.registers[0] - DATA] for c in cases(byte, 0, 7)}
        self.assertEqual(values, set(range(256)))
        cursor = Candidate(0x00381450, "byte_cursor")
        aliased = [c for c in cases(cursor, 0, 7) if "cursor-alias" in c.label]
        self.assertEqual(len(aliased), 4)

    def test_new_generators_cover_signed_bytes_null_and_store_inputs(self):
        signed = Candidate(0x00121D70, "signed_byte_field")
        values = {c.data[c.registers[0] - DATA + 0x330] for c in cases(signed, 0, 7)}
        self.assertEqual(values, set(range(256)))
        nullable = Candidate(0x0014EC5C, "nullable_pointer_field")
        inputs = list(cases(nullable, 32, 7))
        self.assertTrue(any(c.registers[0] == 0 for c in inputs))
        self.assertTrue(any(c.registers[0] != 0 for c in inputs))
        stores = Candidate(0x00131414, "paired_word_store")
        self.assertTrue(all(c.registers[2] == (c.registers[1] ^ 0xFFFFFFFF)
                            for c in cases(stores, 16, 7)))

    def test_compiled_deliberate_bugs_are_detected(self):
        # Use synthetic originals here; private-image controls are also in the CLI.
        with tempfile.TemporaryDirectory(prefix="smt4-semantic-") as directory:
            obj = Path(directory) / "candidates.o"
            build = compile_tu_armv6k(ROOT / "experiments/semantic_equivalence/candidates.cpp", obj, ROOT)
            self.assertEqual(build.returncode, 0, build.stderr)
            functions = extract_elf_functions_detailed(obj)
            # Correct unsigned >400 predicate in a synthetic ARM fixture.
            image = instructions(0xE3500E19, 0x83A00001, 0x93A00000, 0xE12FFF1E)
            self.assertEqual(len(image), 16)
            candidate = Candidate(0x002AE464, "unsigned_threshold")
            # Runner can place this fixture at TEXT, independent of its ledger address.
            inputs = list(cases(candidate, 0, 42))
            good_code, relocations = functions[candidate.symbol]
            self.assertFalse(relocations)
            oracle, good = Runner(image, TEXT), Runner(image, TEXT, good_code)
            self.assertTrue(all(difference(oracle.run(c), good.run(c)) is None for c in inputs))
            for symbol in ("wrong_threshold", "wrong_abi"):
                code, relocations = functions[symbol]
                self.assertFalse(relocations)
                oracle, mutant = Runner(image, TEXT), Runner(image, TEXT, code)
                reasons = [difference(oracle.run(c), mutant.run(c)) for c in inputs]
                self.assertTrue(any(reasons), symbol)
                expected = "return value" if symbol == "wrong_threshold" else "callee-saved"
                self.assertTrue(any(expected in r for r in reasons if r), symbol)
            # For non-aliasing buffers these two functions agree. The alias case
            # must expose the mutation, rather than relying on random detection.
            cursor = Candidate(0x00381450, "byte_cursor")
            good_code, _ = functions[cursor.symbol]
            bad_code, _ = functions["wrong_cursor_order"]
            good, bad = Runner(good_code, TEXT), Runner(bad_code, TEXT)
            inputs = list(cases(cursor, 16, 42))
            differences = [(c.label, difference(good.run(c), bad.run(c))) for c in inputs]
            self.assertTrue(any("cursor-alias" in label and reason == "return value differs"
                                for label, reason in differences))
            self.assertTrue(all(reason is None for label, reason in differences if "cursor-alias" not in label))


if __name__ == "__main__":
    unittest.main()
