"""Tests of the offline rubric, not of the application or model reliability."""
import copy
import json
import unittest

from score_eval import ROOT, confidence, grade, validate


class RubricTests(unittest.TestCase):
    def setUp(self):
        self.cases = {c["id"]: c for c in json.loads((ROOT / "eval_cases.json").read_text(encoding="utf-8"))}
        self.outputs = {c["id"]: c for c in json.loads((ROOT / "results/v1-dev.json").read_text(encoding="utf-8"))}

    def test_complete_requirements(self):
        self.assertEqual(confidence(self.outputs["D1"]["signals"]), 100)

    def test_uncertainty_is_not_confirmation(self):
        self.assertEqual(confidence(self.outputs["D2"]["signals"]), 0)

    def test_exclusion_is_clear_decision_not_skill(self):
        self.assertEqual(confidence(self.outputs["D3"]["signals"]), 100)
        self.assertEqual(self.outputs["D3"]["signals"]["knowledge"]["status"], "not_applicable")

    def test_limit_does_not_inflate_confidence(self):
        self.assertEqual(confidence(self.outputs["D8"]["signals"]), 60)

    def test_conflict_loses_dimension_weight(self):
        signals = copy.deepcopy(self.outputs["D1"]["signals"])
        signals["knowledge"] = {"status": "conflict", "value": None, "evidence": ["conflict"]}
        self.assertEqual(confidence(signals), 75)

    def test_fabricated_quote_fails(self):
        pred = copy.deepcopy(self.outputs["D1"])
        pred["signals"]["application"]["evidence"] = ["несуществующая цитата"]
        self.assertIn("ungrounded evidence: application", validate(pred, self.cases["D1"]))

    def test_assistant_quote_is_not_learner_evidence(self):
        pred = copy.deepcopy(self.outputs["D6"])
        pred["signals"]["depth"]["evidence"] = ["Подтверждаете глубокий уровень?"]
        self.assertIn("ungrounded evidence: depth", validate(pred, self.cases["D6"]))

    def test_text_confirmation_requires_quote(self):
        pred = copy.deepcopy(self.outputs["D1"])
        pred["signals"]["depth"]["evidence"] = []
        self.assertIn("missing evidence: depth", validate(pred, self.cases["D1"]))

    def test_model_cannot_add_numeric_confidence(self):
        pred = copy.deepcopy(self.outputs["D1"])
        pred["confidence"] = 100
        self.assertIn("schema: unexpected or missing output keys", validate(pred, self.cases["D1"]))

    def test_not_applicable_requires_exclusion(self):
        pred = copy.deepcopy(self.outputs["D1"])
        pred["signals"]["knowledge"] = {"status": "not_applicable", "value": None, "evidence": []}
        self.assertIn("invalid not_applicable: knowledge", validate(pred, self.cases["D1"]))

    def test_all_skipped_must_not_finish(self):
        pred = copy.deepcopy(self.outputs["D7"])
        pred["action"], pred["follow_up_question"] = "finish", None
        self.assertFalse(grade(pred, self.cases["D7"])["passed"])


if __name__ == "__main__":
    unittest.main()
