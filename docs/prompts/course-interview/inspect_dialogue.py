"""Validate a saved sequential model trial and compute confidence/progress offline."""
import argparse
import json
from pathlib import Path

from score_eval import confidence, validate


def required_action(signals, state):
    included = (signals["necessity"]["status"] == "confirmed"
                and signals["necessity"]["value"] == "include")
    excluded = (signals["necessity"]["status"] == "confirmed"
                and signals["necessity"]["value"] == "exclude")
    unresolved = any(signals[k]["status"] in {"missing", "conflict"}
                     for k in ("necessity", "depth", "knowledge"))
    if not excluded and unresolved and state["followup_count"] < min(state["max_followups"], 2):
        return "ask"
    if state["completed_modules"] + 1 < state["module_count"]:
        return "next_module"
    return "finish" if state["included_modules"] > 0 or included else "revise_goal"


def inspect(turns):
    completed, included, followups = 0, 0, 0
    history, scores, rows, errors = [], {}, [], []
    seen_modules = set()
    current_module = None
    total = turns[0]["input"]["module_count"]
    finished = False
    for turn in turns:
        state, output = turn["input"], turn["output"]
        module_id = state["module"]["id"]
        local_errors = validate({"id": turn["id"], **output}, {"input": state})
        if finished:
            local_errors.append("turn after terminal action")
        if current_module is None:
            if module_id in seen_modules:
                local_errors.append("revisited completed module")
            current_module = module_id
            seen_modules.add(module_id)
        elif current_module != module_id:
            local_errors.append("module changed before transition")
        if state["module_count"] != total or not 0 <= completed < total:
            local_errors.append("invalid module counters")
        if state["completed_modules"] != completed or state["included_modules"] != included:
            local_errors.append("incorrect completed/included counters")
        if state["followup_count"] != followups or state["history"] != history:
            local_errors.append("incorrect followup count/history")
        if output["action"] != required_action(output["signals"], state):
            local_errors.append("illegal transition for signals and budget")
        scores[module_id] = confidence(output["signals"])
        if output["action"] == "ask":
            history.extend([{"role": "user", "content": state["answer"].get("comment", "")},
                            {"role": "assistant", "content": output["follow_up_question"]}])
            followups += 1
        else:
            completed += 1
            necessity = output["signals"]["necessity"]
            included += int(necessity["status"] == "confirmed" and necessity["value"] == "include")
            current_module, followups, history = None, 0, []
            finished = output["action"] in {"finish", "revise_goal"}
        rows.append({"id": turn["id"], "module": module_id, "action": output["action"],
                     "module_confidence": scores[module_id],
                     "course_confidence": round(sum(scores.values()) / total, 1),
                     "progress": round(100 * completed / total, 1),
                     "remaining_modules": total - completed})
        errors.extend(f"{turn['id']}: {error}" for error in local_errors)
    if not finished or completed != total:
        errors.append("trajectory did not finish all modules")
    return {"passed": not errors, "turns": len(turns), "errors": errors, "rows": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("transcript", type=Path)
    args = parser.parse_args()
    report = inspect(json.loads(args.transcript.read_text(encoding="utf-8")))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["passed"] else 1)
