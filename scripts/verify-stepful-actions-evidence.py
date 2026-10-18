#!/usr/bin/env python3
"""Classify GitHub Actions job evidence without inventing source verdicts."""

from __future__ import annotations
import argparse
import json
from pathlib import Path


def classify(payload: dict) -> dict:
    jobs = payload.get("jobs")
    if not isinstance(jobs, list) or not jobs:
        return {"classification": "NO_JOBS", "source_verdict": "NONE"}

    stepful = []
    zero_step = []
    for job in jobs:
        steps = job.get("steps")
        runner_id = job.get("runner_id")
        item = {
            "id": job.get("id"),
            "name": job.get("name"),
            "conclusion": job.get("conclusion"),
            "runner_id": runner_id,
        }
        if isinstance(steps, list) and len(steps) > 0:
            stepful.append(item)
        else:
            zero_step.append(item)

    if stepful:
        # This proves only runner admission. Source pass/fail is read from the
        # actual executed steps/job conclusion by the owning workflow.
        return {
            "classification": "STEPFUL",
            "source_verdict": "DEFER_TO_EXECUTED_JOB",
            "stepful_jobs": stepful,
            "zero_step_jobs": zero_step,
        }

    return {
        "classification": "NOT_EXECUTED",
        "source_verdict": "NONE",
        "reason": "every observed job has null/empty steps",
        "zero_step_jobs": zero_step,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("jobs_json", type=Path)
    args = parser.parse_args()
    result = classify(json.loads(args.jobs_json.read_text()))
    print(json.dumps(result, sort_keys=True))
    if result["classification"] == "NO_JOBS":
        raise SystemExit(3)
    if result["classification"] == "NOT_EXECUTED":
        raise SystemExit(4)


if __name__ == "__main__":
    main()
