import argparse
import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import torch
from ultralytics import YOLO


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a person-named alias weight without touching the original best.pt.",
    )
    parser.add_argument("--source-weights", required=True, help="Original best.pt path.")
    parser.add_argument("--alias-weights", required=True, help="Output alias .pt path.")
    parser.add_argument("--metadata-path", required=True, help="Output alias metadata JSON path.")
    parser.add_argument(
        "--class-name",
        default="person",
        help="Class name to write into the alias checkpoint. Defaults to person.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting an existing alias file.",
    )
    return parser


def normalize_names(raw_value: Any) -> Dict[int, str]:
    if isinstance(raw_value, dict):
        return {int(key): str(value) for key, value in raw_value.items()}
    if isinstance(raw_value, (list, tuple)):
        return {index: str(value) for index, value in enumerate(raw_value)}
    return {}


def main() -> None:
    args = build_parser().parse_args()

    source_weights = Path(args.source_weights).expanduser().resolve()
    alias_weights = Path(args.alias_weights).expanduser().resolve()
    metadata_path = Path(args.metadata_path).expanduser().resolve()

    if not source_weights.exists():
        raise FileNotFoundError(f"Source checkpoint not found: {source_weights}")
    if alias_weights.exists() and not args.overwrite:
        raise FileExistsError(f"Alias checkpoint already exists: {alias_weights}")
    if metadata_path.exists() and not args.overwrite:
        raise FileExistsError(f"Alias metadata already exists: {metadata_path}")

    alias_weights.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)

    checkpoint = torch.load(source_weights, map_location="cpu", weights_only=False)
    alias_checkpoint = deepcopy(checkpoint)

    model = alias_checkpoint.get("model")
    if model is None:
        raise RuntimeError("Checkpoint does not contain a `model` entry.")

    original_names = normalize_names(getattr(model, "names", None))
    alias_names = {0: str(args.class_name)}

    model.names = alias_names
    model.nc = len(alias_names)

    model_yaml = getattr(model, "yaml", None)
    if isinstance(model_yaml, dict):
        model_yaml["names"] = alias_names
        model_yaml["nc"] = len(alias_names)

    train_args = alias_checkpoint.get("train_args") or {}
    alias_checkpoint["train_args"] = dict(train_args)
    alias_checkpoint["train_args"]["single_cls"] = len(alias_names) == 1

    torch.save(alias_checkpoint, alias_weights)

    verified_model = YOLO(str(alias_weights))
    verified_names = normalize_names(verified_model.names)
    if verified_names != alias_names:
        raise RuntimeError(
            f"Alias verification failed: expected {alias_names}, got {verified_names}"
        )

    metadata = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_weights": str(source_weights),
        "alias_weights": str(alias_weights),
        "original_model_names": original_names,
        "alias_model_names": alias_names,
        "verification_names": verified_names,
        "note": "Original best.pt was left untouched; this alias only normalizes class names.",
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    print("alias_weights", alias_weights)
    print("metadata_path", metadata_path)
    print("original_model_names", original_names)
    print("alias_model_names", alias_names)


if __name__ == "__main__":
    main()
