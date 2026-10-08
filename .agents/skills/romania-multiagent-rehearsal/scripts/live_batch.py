"""Execute three internal model-backed rehearsals, never publish to WhatsApp."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import engine


def run_three(topic: str, output_dir: Path, *, consent: bool = False,
              size: int = 5, steps: int = 2, readiness=None, generate=None) -> dict:
    """Save every successful iteration as a private JSON; fail closed on errors.

    readiness and generate are injectable only for deterministic offline unit tests.
    """
    if not consent:
        raise PermissionError("Explicit --ack-internal required.")
    if not topic.strip() or not 1 <= size <= 8 or not 1 <= steps <= 4:
        raise ValueError("Valid topic; participant count 1..8; steps 1..4 required.")
    status = readiness() if readiness is not None else engine.preflight()
    if not status.get("real_llm_test_possible"):
        raise RuntimeError("NOT RUN: model credentials or required packages unavailable.")
    writer = generate if generate is not None else engine.run_tinytroupe
    out = Path(output_dir).resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("Output directory must be empty to avoid overwriting or mixing runs.")
    out.mkdir(parents=True, exist_ok=True)
    outcome = {
        "kind": "INTERNAL_MODEL_REHEARSAL_RUNS",
        "publication_allowed": False,
        "automatic_whatsapp_send": False,
        "source_role_count": 65,
        "editorial_role_count": 2,
        "review_status": "HOLD_FOR_HUMAN_REVIEW",
        "actual_runs_completed": 0,
        "rounds": []
    }
    for i in range(3):
        blueprint = engine.panel(topic, session=i, size=size)
        try:
            response = writer(blueprint, acknowledged=True, steps=steps)
            if response.get("status") != "internal_only" or response.get("publication_allowed") is not False:
                raise ValueError("External adapter returned unsafe output status")
            record = {
                "round": i + 1, "selected_persona_ids": [p["id"] for p in blueprint["participants"]],
                "kind": "INTERNAL_SIMULATION_ONLY",
                "publication_allowed": False,
                "source_topic": topic,
                "result": response
            }
            path = out / f"rehearsal_round_{i+1}.json"
            with path.open("x", encoding="utf-8") as stream:
                os.chmod(path, 0o600)
                json.dump(record, stream, ensure_ascii=False, indent=2, default=str)
            outcome["actual_runs_completed"] += 1
            outcome["rounds"].append({"round": i + 1, "status": "saved", "file": path.name})
        except Exception as exc:
            # Never include provider exception text; it may contain secrets or user data.
            outcome["rounds"].append({"round": i + 1, "status": "failed",
                                      "error_type": type(exc).__name__})
            outcome["review_status"] = "INCOMPLETE_DO_NOT_USE"
            break
    outcome["all_three_completed"] = outcome["actual_runs_completed"] == 3
    report = out / "run_summary.json"
    with report.open("x", encoding="utf-8") as stream:
        os.chmod(report, 0o600)
        json.dump(outcome, stream, ensure_ascii=False, indent=2)
    return outcome


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", default="diversificarea portofoliului")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--size", default=5, type=int)
    parser.add_argument("--steps", default=2, type=int)
    parser.add_argument("--ack-internal", action="store_true")
    args = parser.parse_args()
    try:
        summary = run_three(args.topic,args.output_dir,consent=args.ack_internal,
                            size=args.size,steps=args.steps)
    except (PermissionError, ValueError, RuntimeError, FileExistsError) as err:
        print(f"NOT_RUN: {type(err).__name__}: {err}")
        raise SystemExit(2)
    print(json.dumps({k:v for k,v in summary.items() if k != "rounds"},ensure_ascii=False,indent=2))
    if not summary["all_three_completed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
