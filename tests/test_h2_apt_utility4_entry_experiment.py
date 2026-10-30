import unittest
from tools.h2_apt_utility4_entry_experiment import differences, make_case, SP, END
import random

class ComparatorTests(unittest.TestCase):
    def test_rejects_missing_wrapper_and_wrong_return(self):
        case = make_case(random.Random(1), 5)
        good = {"pc": END, "sp": SP, "r0": 5, "preserved": case["regs"][4:12],
                "data": case["data"].hex(), "live_stack": case["stack"][0x1000:].hex(),
                "calls": [{"args": [4,0,0,0,0,0], "sp_align": 0, "thumb": False}]}
        self.assertEqual(differences(good, good, case), [])
        bad = dict(good, calls=[], r0=0)
        errors = differences(good, bad, case)
        self.assertIn("candidate: wrapper count", errors)
        self.assertIn("candidate: return", errors)

if __name__ == "__main__":
    unittest.main()
