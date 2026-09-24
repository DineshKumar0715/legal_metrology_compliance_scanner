"""Measure the current OCR pipeline against the labeled evaluation set."""

from __future__ import annotations

import argparse
import json
import re
import sys
import subprocess
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ocr_engine import OCREngine


FIELD_NAMES = (
    "mrp",
    "net_quantity",
    "date_of_packing",
    "consumer_care",
    "manufacturer_details",
    "country_of_origin",
)


def normalize_text(text: str) -> str:
    """Normalize case, punctuation, and whitespace for comparable scoring."""
    normalized = text.lower()
    normalized = "".join(
        " " if unicodedata.category(character).startswith("P") else character
        for character in normalized
    )
    return re.sub(r"\s+", " ", normalized).strip()


def levenshtein(left: list[str], right: list[str]) -> int:
    """Return edit distance using a memory-efficient dynamic-programming pass."""
    if len(left) < len(right):
        left, right = right, left
    previous = list(range(len(right) + 1))
    for left_index, left_value in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_value in enumerate(right, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[right_index] + 1,
                    previous[right_index - 1] + (left_value != right_value),
                )
            )
        previous = current
    return previous[-1]


def score_text(expected: str, actual: str) -> dict[str, Any]:
    normalized_expected = normalize_text(expected)
    normalized_actual = normalize_text(actual)
    expected_characters = list(normalized_expected)
    actual_characters = list(normalized_actual)
    expected_words = normalized_expected.split()
    actual_words = normalized_actual.split()
    character_errors = levenshtein(expected_characters, actual_characters)
    word_errors = levenshtein(expected_words, actual_words)
    return {
        "expected_text": expected,
        "ocr_text": actual,
        "normalized_expected_text": normalized_expected,
        "normalized_ocr_text": normalized_actual,
        "cer": character_errors / len(expected_characters)
        if expected_characters
        else (0.0 if not actual_characters else 1.0),
        "wer": word_errors / len(expected_words)
        if expected_words
        else (0.0 if not actual_words else 1.0),
        "character_errors": character_errors,
        "reference_characters": len(expected_characters),
        "word_errors": word_errors,
        "reference_words": len(expected_words),
    }


def jsonable(value: Any) -> Any:
    """Convert EasyOCR/Numpy values into JSON-compatible Python values."""
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    return value


def summarize_scores(scores: Iterable[dict[str, Any]]) -> dict[str, Any]:
    scores = list(scores)
    character_errors = sum(item["character_errors"] for item in scores)
    reference_characters = sum(item["reference_characters"] for item in scores)
    word_errors = sum(item["word_errors"] for item in scores)
    reference_words = sum(item["reference_words"] for item in scores)
    return {
        "documents": len(scores),
        "cer": character_errors / reference_characters
        if reference_characters
        else 0.0,
        "wer": word_errors / reference_words if reference_words else 0.0,
        "character_errors": character_errors,
        "reference_characters": reference_characters,
        "word_errors": word_errors,
        "reference_words": reference_words,
    }


def confidence_summary(confidences: list[float]) -> dict[str, Any]:
    return {
        "tokens": len(confidences),
        "min": min(confidences) if confidences else None,
        "median": median(confidences) if confidences else None,
        "max": max(confidences) if confidences else None,
        "below_0_5": sum(confidence < 0.5 for confidence in confidences),
    }


def git_commit(project_root: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return completed.stdout.strip() or None


def resolve_image(eval_root: Path, image_path: str) -> Path:
    candidate = eval_root / image_path
    if candidate.exists():
        return candidate
    project_candidate = eval_root.parent / image_path
    if project_candidate.exists():
        return project_candidate
    raise FileNotFoundError(f"Image not found for evaluation record: {image_path}")


def run_evaluation(ground_truth_path: Path, output_path: Path) -> dict[str, Any]:
    eval_root = ground_truth_path.parent
    records = json.loads(ground_truth_path.read_text(encoding="utf-8"))
    if not isinstance(records, list) or not records:
        raise ValueError("ground_truth.json must contain a non-empty JSON array")

    engine = OCREngine(languages=["en"])
    document_scores: list[dict[str, Any]] = []
    condition_scores: dict[str, list[dict[str, Any]]] = defaultdict(list)
    all_confidences: list[float] = []

    for record in records:
        image_path = resolve_image(eval_root, record["image"])
        image_bytes = image_path.read_bytes()
        actual_text, ocr_results = engine.extract_text(image_bytes)
        score = score_text(record["text"], actual_text)
        confidences = [float(result[2]) for result in ocr_results]
        score.update(
            {
                "id": record["id"],
                "image": record["image"],
                "capture_conditions": record.get("capture_conditions", []),
                "field_expectations": record.get("fields", {}),
                "expected_compliance": record.get("expected_compliance", {}),
                "confidence": confidence_summary(confidences),
                "easyocr_results": [
                    {
                        "bounding_box": jsonable(result[0]),
                        "text": result[1],
                        "confidence": float(result[2]),
                    }
                    for result in ocr_results
                ],
            }
        )
        document_scores.append(score)
        all_confidences.extend(confidences)
        for condition in score["capture_conditions"]:
            condition_scores[condition].append(score)

    metrics = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_commit(output_path.parent.parent),
        "ground_truth": str(ground_truth_path),
        "normalization": {
            "lowercase": True,
            "punctuation": "Unicode punctuation replaced with spaces",
            "whitespace": "Runs of whitespace collapsed and surrounding whitespace stripped",
            "word_tokenization": "Whitespace-separated tokens after normalization",
        },
        "easyocr_config": {
            "engine": "EasyOCR",
            "version": "1.7.1",
            "languages": ["en"],
            "gpu": False,
            "preprocessing": "OpenCV decode, grayscale, bilateral filter, adaptive Gaussian threshold",
            "readtext_arguments": "Default EasyOCR readtext() arguments",
        },
        "aggregates": summarize_scores(document_scores),
        "confidence_distribution": confidence_summary(all_confidences),
        "per_condition": {
            condition: summarize_scores(scores)
            for condition, scores in sorted(condition_scores.items())
        },
        "documents": document_scores,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def print_summary(metrics: dict[str, Any]) -> None:
    aggregates = metrics["aggregates"]
    print(f"Documents: {aggregates['documents']}")
    print(f"Aggregate CER: {aggregates['cer']:.4f}")
    print(f"Aggregate WER: {aggregates['wer']:.4f}")
    print("\nPer-document scores:")
    print(f"{'ID':<20} {'CER':>10} {'WER':>10} {'Tokens':>10}")
    for document in metrics["documents"]:
        print(
            f"{document['id']:<20} {document['cer']:>10.4f} "
            f"{document['wer']:>10.4f} {document['confidence']['tokens']:>10}"
        )
    print("\nPer-condition scores:")
    print(f"{'Condition':<20} {'Docs':>6} {'CER':>10} {'WER':>10}")
    for condition, summary in metrics["per_condition"].items():
        print(
            f"{condition:<20} {summary['documents']:>6} "
            f"{summary['cer']:>10.4f} {summary['wer']:>10.4f}"
        )
    confidence = metrics["confidence_distribution"]
    print(
        "\nConfidence distribution: "
        f"min={confidence['min']}, median={confidence['median']}, "
        f"max={confidence['max']}, below_0.5={confidence['below_0_5']}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ground-truth",
        type=Path,
        default=Path(__file__).with_name("ground_truth.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("baseline_metrics.json"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.ground_truth.exists():
        raise SystemExit(
            f"Ground-truth file not found: {args.ground_truth}. "
            "Create it from ground_truth.example.json before running the baseline."
        )
    metrics = run_evaluation(args.ground_truth, args.output)
    print_summary(metrics)
    print(f"\nSaved metrics to {args.output}")


if __name__ == "__main__":
    main()
