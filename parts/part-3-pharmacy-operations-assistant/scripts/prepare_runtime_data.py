#!/usr/bin/env python3
"""Build the compact, trusted runtime dataset used by the worker image."""

from __future__ import annotations

import argparse
from pathlib import Path

from app.analytics import OperationsRepository


def prepare_runtime_data(source: Path, destination: Path) -> None:
    """Validate the source workbook and write its memory-efficient runtime frame."""

    repository = OperationsRepository.from_path(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    repository.frame.to_csv(destination, index=False, compression="gzip")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    prepare_runtime_data(args.source, args.destination)
    print(f"Prepared runtime data at {args.destination}.")


if __name__ == "__main__":
    main()
