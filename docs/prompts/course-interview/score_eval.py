"""Offline grading of saved model outputs; no network, keys or application imports."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WEIGHTS = {"necessity": 35, "depth": 25, "knowledge": 25, "application": 15}
STATUSES = {"confirmed", "missing", "conflict", "not_applicable"}
VALUES = {"necessity": {"include", "exclude"}, "depth": {"brief", "standard", "deep"},
          "knowledge": {"junior", "middle", "senior"}, "application": {"concrete"}}
ACTIONS = {"ask", "next_module", "finish", "revise_goal"}


def confidence(signals):
    """Heuristic evidence coverage, NOT a calibrated probability of correctness."""
    necessity = signals.get("necessity", {})
    if necessity.get("status") == "confirmed" and necessity.get("value") == "exclude":
        if all(signals.get(k, {}).get("status") == "not_applicable"
               for k in ("depth", "knowledge", "application")):
            return 100
    return sum(weight for key, weight in WEIGHTS.items()
               if signals.get(key, {}).get("status") == "confirmed")


def validate(pred, case):
    errors = []
    if set(pred) != {"id", "signals", "action", "follow_up_question"}:
        errors.append("schema: unexpected or missing output keys")
    signals = pred.get("signals", {})
    if set(signals) != set(WEIGHTS):
        errors.append("schema: four signals required")
    if pred.get("action") not in ACTIONS:
        errors.append("schema: invalid action")
    question = pred.get("follow_up_question")
    if pred.get("action") in {"ask", "revise_goal"}:
        if not isinstance(question, str) or not question.strip() or len(question) > 300 or question.count("?") != 1:
            errors.append("question: exactly one short question required")
    elif question is not None:
        errors.append("question: must be null on transition")
    sources = [case["input"]["answer"].get("comment", "")]
    sources += [item["content"] for item in case["input"].get("history", []) if item["role"] == "user"]
    for name in WEIGHTS:
        sig = signals.get(name, {})
        if set(sig) != {"status", "value", "evidence"}:
            errors.append(f"schema: unexpected or missing keys in {name}")
        status, value, evidence = sig.get("status"), sig.get("value"), sig.get("evidence")
        if status not in STATUSES or not isinstance(evidence, list):
            errors.append(f"schema: {name}")
            continue
        if status == "confirmed" and value not in VALUES[name]:
            errors.append(f"value: {name}")
        if status != "confirmed" and value is not None:
            errors.append(f"value: {name} must be null")
        excluded = (signals.get("necessity", {}).get("status") == "confirmed"
                    and signals.get("necessity", {}).get("value") == "exclude")
        if status == "not_applicable" and (name == "necessity" or not excluded):
            errors.append(f"invalid not_applicable: {name}")
        if excluded and name != "necessity" and status != "not_applicable":
            errors.append(f"excluded module requires not_applicable: {name}")
        for quote in evidence:
            if not isinstance(quote, str) or not quote or not any(quote in text for text in sources):
                errors.append(f"ungrounded evidence: {name}")
        if status == "conflict" and not evidence:
            errors.append(f"missing conflict evidence: {name}")
        if status == "confirmed" and not evidence:
            answer = case["input"]["answer"]
            structured = ((name == "necessity" and (
                              (answer.get("depth") == "skip" and value == "exclude")
                              or (answer.get("depth") in {"brief", "standard", "deep"} and value == "include")))
                          or (name == "depth" and answer.get("depth") == value)
                          or (name == "knowledge" and answer.get("knowledge_level") == value))
            if not structured:
                errors.append(f"missing evidence: {name}")
    return errors


def grade(pred, case):
    errors = validate(pred, case)
    expected, signals = case["expected"], pred.get("signals", {})
    for key, value in expected.get("statuses", {}).items():
        if signals.get(key, {}).get("status") != value:
            errors.append(f"{key}: expected status {value}")
    for key, value in expected.get("values", {}).items():
        if signals.get(key, {}).get("value") != value:
            errors.append(f"{key}: expected value {value}")
    if pred.get("action") != expected["action"]:
        errors.append(f"action: expected {expected['action']}")
    score = confidence(signals)
    if "score" in expected and score != expected["score"]:
        errors.append(f"confidence: expected {expected['score']}, got {score}")
    if score > expected.get("max_score", 100):
        errors.append("confidence: excessive with unresolved conflict")
    return {"id": case["id"], "passed": not errors, "score": score,
            "action": pred.get("action"), "errors": errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("predictions", type=Path)
    parser.add_argument("--split", choices=["dev", "holdout", "all"], default="dev")
    parser.add_argument("--cases", type=Path, default=ROOT / "eval_cases.json")
    args = parser.parse_args()
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    cases = [c for c in cases if args.split == "all" or c["split"] == args.split]
    outputs = json.loads(args.predictions.read_text(encoding="utf-8"))
    if len({p["id"] for p in outputs}) != len(outputs):
        raise ValueError("Duplicate prediction IDs")
    by_id = {p["id"]: p for p in outputs}
    if set(by_id) - {c["id"] for c in cases}:
        raise ValueError("Unexpected prediction IDs for this split")
    results = [grade(by_id.get(c["id"], {}), c) for c in cases]
    report = {"predictions": args.predictions.name, "split": args.split,
              "passed": sum(r["passed"] for r in results), "total": len(results), "results": results}
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
