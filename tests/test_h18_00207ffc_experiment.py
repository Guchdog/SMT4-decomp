import tempfile
import unittest
from pathlib import Path
from tools.h18_00207ffc_experiment import ALLOC_RESOURCE, FUNC, RESOURCE_TARGET_A, ROOT, run

class TestH1800207ffcExperiment(unittest.TestCase):
    def test_handler_differential_and_controls(self):
        with tempfile.TemporaryDirectory() as temp:
            result=run(ROOT/"extracted/exefs/code.bin",Path(temp),seed=23)
        self.assertEqual(result["address"],hex(FUNC))
        self.assertTrue(result["passed"],result["direct"]["results"])
        self.assertEqual(result["direct"]["cases"],44)
        self.assertTrue(all(x["detected"] for x in result["negative_controls"]))
        reload_case=next(x for x in result["direct"]["results"]
                         if x["label"]=="state1-setup-mutates-context-resource")
        self.assertTrue(reload_case["passed"])
        self.assertEqual(reload_case["original_trace"],reload_case["candidate_trace"])
        self.assertEqual(reload_case["original_trace"][2]["args"][0],RESOURCE_TARGET_A)
        self.assertEqual(reload_case["original_trace"][3]["args"][0],RESOURCE_TARGET_A)
        models=result["helper_models"]
        self.assertEqual(models["default_side_effect_policy"]["context_or_resource_objects"],
                         "no_modelled_writes_by_default")
        self.assertFalse(models["post_call_fixture_mutation_policy"]["attributed_to_helper"])
        self.assertIn("applied_after_the_configured_helper_returns",
                      models["post_call_fixture_mutation_policy"]["mode"])
        described=next(x for x in models["configured_stimuli"]
                       if x["case"]=="state1-setup-mutates-context-resource")
        self.assertEqual(described["events"],[{"after":"setup","kind":"context_field_u32",
                           "offset":0x10,"value":ALLOC_RESOURCE}])
        self.assertEqual(reload_case["original_trace"][1]["mutations"][0]["stimulus"],
                         "post_call_fixture_mutation")

if __name__=="__main__": unittest.main()
