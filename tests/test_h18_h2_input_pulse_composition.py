import importlib.util
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "h18_h2_input_pulse_composition.py"


class InputPulseCompositionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = None
        if MODULE_PATH.exists():
            spec = importlib.util.spec_from_file_location("h18_h2_input_pulse_composition", MODULE_PATH)
            cls.runner = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cls.runner)

    def require_runner(self):
        self.assertIsNotNone(self.runner, f"required composition runner is missing: {MODULE_PATH}")

    def test_press_hold_release_retriggers_one_refresh_pulse(self):
        self.require_runner()
        model = self.runner.model_trace([
            {"label": "release", "available": 1, "state_word": 0, "flags": 0},
            {"label": "press", "available": 1, "state_word": 1, "flags": 0},
            {"label": "held", "available": 1, "state_word": 1, "flags": 0},
            {"label": "release_again", "available": 1, "state_word": 0, "flags": 0},
            {"label": "press_again", "available": 1, "state_word": 1, "flags": 0},
        ])
        self.assertEqual([(x["counter"], x["query"]) for x in model],
                         [(0, 0), (1, 1), (2, 0), (0, 0), (1, 1)])

    def test_unavailable_refresh_retains_counter_but_flag_blocks_query(self):
        self.require_runner()
        model = self.runner.model_trace([
            {"label": "press", "available": 1, "state_word": 1, "flags": 0},
            {"label": "unavailable", "available": 0, "state_word": 0, "flags": 0},
            {"label": "gated", "available": 0, "state_word": 0, "flags": 1},
            {"label": "ungated_stale", "available": 0, "state_word": 0, "flags": 0},
            {"label": "release", "available": 1, "state_word": 0, "flags": 0},
        ])
        self.assertEqual([(x["counter"], x["availability"], x["query"]) for x in model],
                         [(1, 1, 1), (1, 0, 1), (1, 0, 0), (1, 0, 1), (0, 1, 0)])

    def test_neighbor_bit_does_not_trigger_id0_and_gate_row_resets(self):
        self.require_runner()
        row_gate = self.runner.model_trace([
            {"label": "neighbor", "available": 1, "state_word": 2, "flags": 0},
        ], initial_counter=0)[0]
        gated_row = self.runner.model_trace([
            {"label": "gated_row", "available": 1, "state_word": 1,
             "flags": 0, "row_gate": 1},
        ], initial_counter=9)[0]
        self.assertEqual((row_gate["counter"], row_gate["query"]), (0, 0))
        self.assertEqual((gated_row["counter"], gated_row["query"]), (0, 0))

    def test_scratch_negative_control_has_distinct_reproducible_helper_artifacts(self):
        self.require_runner()
        good = b"candidate-mode1-helper"
        mutant = b"wrong-counter-mode1-helper"
        with tempfile.TemporaryDirectory() as temp:
            manifest = self.runner.write_scratch_helper_artifacts(
                pathlib.Path(temp), good, mutant)
            self.assertTrue(manifest["distinct_bytes"])
            self.assertNotEqual(manifest["candidate_helper_sha256"],
                                manifest["mutant_helper_sha256"])
            self.assertEqual((pathlib.Path(temp) / manifest["candidate_helper_file"]).read_bytes(), good)
            self.assertEqual((pathlib.Path(temp) / manifest["mutant_helper_file"]).read_bytes(), mutant)
            self.assertTrue((pathlib.Path(temp) / "scratch-helper-manifest.json").is_file())

    def test_scratch_negative_control_rejects_identical_helper_bytes(self):
        self.require_runner()
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                self.runner.write_scratch_helper_artifacts(
                    pathlib.Path(temp), b"same", b"same")


if __name__ == "__main__":
    unittest.main()
