import struct
import unittest

from tools.h2_copy_pair_experiment import (
    BASE,
    DATA,
    LAYOUTS,
    PATTERNS,
    cases,
    make_case,
)


class CopyPairContractTests(unittest.TestCase):
    def test_directed_layouts_are_aligned_and_cover_alias_shapes(self):
        generated = list(cases(seed=7, samples=0))
        self.assertEqual(len(generated), len(LAYOUTS) * len(PATTERNS))
        seen = {layout for _label, layout, _offsets, _words in generated}
        self.assertEqual(seen, set(LAYOUTS))
        rng_seed = __import__("random").Random(7)
        for label, _layout, offsets, words in generated:
            case = make_case(label, offsets, words, rng_seed)
            destination, source = case.registers[:2]
            self.assertEqual(destination % 4, 0)
            self.assertEqual(source % 4, 0)
            self.assertGreaterEqual(destination, DATA)
            self.assertGreaterEqual(source, DATA)
            self.assertLessEqual(destination + 8, DATA + len(case.data))
            self.assertLessEqual(source + 8, DATA + len(case.data))
            stored_words = struct.unpack_from("<8I", case.data, BASE - DATA)
            self.assertEqual(stored_words, words)

    def test_load_before_store_differs_from_forward_copy_on_dst_after_source(self):
        source_words = PATTERNS[2][:2]
        original = list(source_words + (0x99AABBCC,))
        correct_first, correct_second = original[0], original[1]
        original[1], original[2] = correct_first, correct_second

        forward = list(source_words + (0x99AABBCC,))
        forward[1] = forward[0]
        forward[2] = forward[1]
        self.assertEqual(original, [source_words[0], source_words[0], source_words[1]])
        self.assertEqual(forward, [source_words[0], source_words[0], source_words[0]])
        self.assertNotEqual(original, forward)

    def test_same_pointer_is_an_identity_copy(self):
        words = PATTERNS[2]
        before = list(words)
        first, second = before[0], before[1]
        before[0], before[1] = first, second
        self.assertEqual(before, list(words))


if __name__ == "__main__":
    unittest.main()
