from __future__ import annotations

import argparse
import hashlib
import json
import os
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv

from .budget import CostLedger, Pricing
from .corpus import corpus_counts, iter_customer_messages, load_corpus
from .evaluation import prepare_evaluation, score_evaluation
from .pipeline import classify_messages, write_jsonl
from .prompt import build_prompt, prompt_hash
from .provider import GeminiProvider
from .rules import rule_gate

DEFAULT_INPUT = Path("inputs/dm_message_corpus_10k.json")
DEFAULT_OUTPUT = Path("outputs/classifications.jsonl")
DEFAULT_LEDGER = Path("outputs/cost-ledger.jsonl")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Budget-guarded customer message triage")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="validate and count the corpus")
    inspect_parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)

    forecast = subparsers.add_parser("forecast", help="estimate conservative request reservations")
    forecast.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    forecast.add_argument("--batch-size", type=int, default=50)
    forecast.add_argument("--max-output-tokens", type=int, default=2048)

    run = subparsers.add_parser("run", help="run the full hybrid classifier")
    run.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    run.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    run.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    run.add_argument("--batch-size", type=int, default=50)
    run.add_argument("--max-output-tokens", type=int, default=2048)
    run.add_argument("--budget-usd", type=Decimal, default=Decimal("0.80"))
    run.add_argument("--allow-paid-api", action="store_true")
    run.add_argument("--resume", action="store_true")
    run.add_argument("--accept-config-change", action="store_true")

    prepare = subparsers.add_parser(
        "prepare-evaluation", help="create blinded calibration and held-out review queues"
    )
    prepare.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    prepare.add_argument("--classifications", type=Path, default=DEFAULT_OUTPUT)
    prepare.add_argument(
        "--state", type=Path, default=Path("outputs/classifications.jsonl.state.json")
    )
    prepare.add_argument("--output-dir", type=Path, default=Path("outputs/evaluation"))
    prepare.add_argument("--seed", type=int, default=20260806)

    score = subparsers.add_parser("score-evaluation", help="score completed human gold labels")
    score.add_argument("--review-csv", type=Path, required=True)
    score.add_argument(
        "--manifest", type=Path, default=Path("outputs/evaluation/evaluation-manifest.csv")
    )
    score.add_argument("--split", choices=["calibration", "heldout"], required=True)
    score.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "score-evaluation":
        try:
            report = score_evaluation(
                args.review_csv, args.manifest, args.output, split=args.split
            )
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    conversations = load_corpus(args.input)
    messages = list(iter_customer_messages(conversations))

    if args.command == "inspect":
        report = corpus_counts(conversations)
        report["unique_message_ids"] = len({message.message_id for message in messages})
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    if args.command == "forecast":
        report = _forecast(messages, args.batch_size, args.max_output_tokens)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    if args.command == "prepare-evaluation":
        try:
            metadata = prepare_evaluation(
                conversations,
                args.classifications,
                args.state,
                args.output_dir,
                seed=args.seed,
            )
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        print(json.dumps(metadata, indent=2, sort_keys=True))
        return 0

    if not args.allow_paid_api:
        raise SystemExit("refusing paid API calls without explicit --allow-paid-api")
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("GEMINI_API_KEY is required and must not be stored in the repository")

    pricing = Pricing()
    config_hash = _configuration_hash(args, pricing)
    state_path = args.output.with_name(f"{args.output.name}.state.json")
    ledger = CostLedger(args.ledger, pricing, args.budget_usd)
    _prepare_run_state(args, state_path, config_hash)
    provider = GeminiProvider(api_key, pricing.model)
    results = classify_messages(
        messages,
        provider,
        ledger,
        batch_size=args.batch_size,
        max_output_tokens=args.max_output_tokens,
        checkpoint_path=args.output,
    )
    write_jsonl(results, args.output)
    _write_state(
        state_path,
        {
            "status": "completed",
            "configuration_hash": config_hash,
            "classified": len(results),
            "actual_usd": f"{ledger.actual_usd():.6f}",
            "committed_usd": f"{ledger.committed_usd():.6f}",
        },
    )
    print(
        json.dumps(
            {
                "classified": len(results),
                "output": str(args.output),
                "actual_usd": f"{ledger.actual_usd():.6f}",
                "committed_usd": f"{ledger.committed_usd():.6f}",
                "budget_usd": f"{args.budget_usd:.2f}",
                "prompt_hash": prompt_hash(),
                "configuration_hash": config_hash,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _forecast(messages: list, batch_size: int, max_output_tokens: int) -> dict[str, object]:
    if batch_size < 1 or max_output_tokens < 1:
        raise SystemExit("batch size and max output tokens must be positive")
    pricing = Pricing()
    unresolved = [message for message in messages if rule_gate(message.text) is None]
    from .budget import conservative_token_estimate

    input_tokens = 0
    reserved = Decimal("0")
    request_count = 0
    for start in range(0, len(unresolved), batch_size):
        batch = unresolved[start : start + batch_size]
        estimate = conservative_token_estimate(build_prompt(batch))
        input_tokens += estimate
        reserved += pricing.cost(estimate, max_output_tokens)
        request_count += 1
    return {
        "model": pricing.model,
        "eligible_messages": len(messages),
        "rule_gate_messages": len(messages) - len(unresolved),
        "model_fallback_messages": len(unresolved),
        "request_count": request_count,
        "conservative_input_tokens": input_tokens,
        "reserved_max_output_tokens": request_count * max_output_tokens,
        "worst_case_reserved_usd": f"{reserved:.6f}",
        "run_budget_usd": "0.80",
        "assessment_limit_usd": "1.00",
        "prompt_hash": prompt_hash(),
    }


def _configuration_hash(args: argparse.Namespace, pricing: Pricing) -> str:
    material = {
        "input_sha256": _file_sha256(args.input),
        "model": pricing.model,
        "input_usd_per_million": str(pricing.input_usd_per_million),
        "output_usd_per_million": str(pricing.output_usd_per_million),
        "budget_usd": str(args.budget_usd),
        "batch_size": args.batch_size,
        "max_output_tokens": args.max_output_tokens,
        "prompt_hash": prompt_hash(),
    }
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _prepare_run_state(
    args: argparse.Namespace, state_path: Path, configuration_hash: str
) -> None:
    paths = [args.output, args.ledger, state_path]
    if args.resume:
        if not state_path.exists():
            raise SystemExit(f"cannot resume without run state: {state_path}")
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("configuration_hash") != configuration_hash:
            if not args.accept_config_change:
                raise SystemExit(
                    "refusing resume because the run configuration has changed; "
                    "use --accept-config-change only for an audited recovery"
                )
            _accept_safe_config_change(args, state_path, state, configuration_hash)
        return
    if args.accept_config_change:
        raise SystemExit("--accept-config-change requires --resume")
    existing = [str(path) for path in paths if path.exists()]
    if existing:
        raise SystemExit(
            "refusing to overwrite prior run artifacts; use new paths or --resume: "
            + ", ".join(existing)
        )
    _write_state(
        state_path,
        {"status": "running", "configuration_hash": configuration_hash},
    )


def _write_state(path: Path, state: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(state, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def _accept_safe_config_change(
    args: argparse.Namespace,
    state_path: Path,
    state: dict[str, object],
    configuration_hash: str,
) -> None:
    if args.output.exists():
        with args.output.open(encoding="utf-8") as stream:
            for line in stream:
                if not line.strip():
                    continue
                item = json.loads(line)
                if item.get("decision_source") == "model_fallback":
                    raise SystemExit(
                        "cannot change configuration after accepting model-fallback results"
                    )
    previous = list(state.get("previous_configuration_hashes", []))
    previous.append(state.get("configuration_hash"))
    _write_state(
        state_path,
        {
            "status": "running",
            "configuration_hash": configuration_hash,
            "previous_configuration_hashes": previous,
            "recovery": "accepted config change before any model-fallback checkpoint",
        },
    )


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
