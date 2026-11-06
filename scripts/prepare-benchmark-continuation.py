#!/usr/bin/env python3
"""Copy a stopped benchmark's game profile and active checkpoint for continuation."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


def prepare(source: Path, destination: Path, objective_file: Path, model: dict,
            think: str, context: int, temperature: float, seed: int) -> dict:
    source = source.resolve(strict=True)
    destination = destination.resolve()
    objective_file = objective_file.resolve(strict=True)
    if destination.exists():
        raise ValueError("destination already exists")
    if source == destination or source in destination.parents or destination in source.parents:
        raise ValueError("source and destination must be separate directories")

    checkpoints = source / "checkpoints"
    profile = source / "profile"
    required = [profile, checkpoints / "latest.json", checkpoints / "runtime.json",
                checkpoints / "objective.json", source / "logs" / "trial-config.json"]
    if any(not path.exists() for path in required):
        raise ValueError("source is missing its profile, checkpoint, or trial configuration")

    def load(path: Path) -> dict:
        value = json.loads(path.read_text())
        if not isinstance(value, dict):
            raise ValueError(f"{path.name} must contain a JSON object")
        return value

    latest = load(checkpoints / "latest.json")
    runtime = load(checkpoints / "runtime.json")
    objective_checkpoint = load(checkpoints / "objective.json")
    config = load(source / "logs" / "trial-config.json")
    objective = objective_file.read_text()
    objective_hash = hashlib.sha256(objective.encode()).hexdigest()
    if latest.get("state") != "active" or runtime.get("state") != "active":
        raise ValueError("only an interrupted active checkpoint can be continued")
    if (latest.get("objective") != objective or objective_checkpoint.get("objective") != objective
            or runtime.get("objective") != objective):
        raise ValueError("source checkpoint objective does not match the current benchmark objective")
    if config.get("objective_sha256") != objective_hash:
        raise ValueError("source trial objective digest does not match")

    expected = {
        "model_tag": model.get("model_tag"),
        "model_digest": model.get("digest"),
        "think_setting": think,
        "context_size": context,
        "temperature": temperature,
        "seed": seed,
    }
    actual = {
        "model_tag": (config.get("model") or {}).get("model_tag"),
        "model_digest": (config.get("model") or {}).get("digest"),
        "think_setting": config.get("think_setting"),
        "context_size": config.get("context_size"),
        "temperature": config.get("temperature"),
        "seed": config.get("seed"),
    }
    mismatches = [key for key in expected if expected[key] != actual[key]]
    if mismatches:
        raise ValueError("continuation settings differ from source: " + ", ".join(mismatches))

    destination.mkdir(parents=True)
    try:
        # Chromium leaves process-specific singleton links behind after a
        # container exits; never carry these links into the next browser.
        ignore_browser_locks = shutil.ignore_patterns("SingletonLock", "SingletonSocket",
                                                     "SingletonCookie")
        shutil.copytree(profile, destination / "profile", ignore=ignore_browser_locks)
        shutil.copytree(checkpoints, destination / "checkpoints",
                        ignore=shutil.ignore_patterns("*.tmp"))
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise
    return {
        "source_trial_id": config.get("trial_id", source.name),
        "source_checkpoint_time": latest.get("time"),
        "source_session": latest.get("session"),
        "source_steps": latest.get("steps"),
        "objective_sha256": objective_hash,
        "model_tag": expected["model_tag"],
        "model_digest": expected["model_digest"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--objective", type=Path, required=True)
    parser.add_argument("--model-json", required=True)
    parser.add_argument("--think", required=True)
    parser.add_argument("--context", type=int, required=True)
    parser.add_argument("--temperature", type=float, required=True)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    try:
        model = json.loads(args.model_json)
        print(json.dumps(prepare(args.source, args.destination, args.objective, model,
                                 args.think, args.context, args.temperature, args.seed)))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
