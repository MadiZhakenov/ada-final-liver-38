# -*- coding: utf-8 -*-
"""Entry point: python -m src.main [--full|--menu]."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow `python -m src.main` from project root.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.cli_menu import menu, run_full_pipeline  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ADA Topic 38 — Liver Disease project")
    parser.add_argument("--full", action="store_true", help="Run full pipeline once")
    parser.add_argument("--menu", action="store_true", help="Interactive console menu")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        if args.menu:
            menu()
        else:
            run_full_pipeline()
    except FileNotFoundError as exc:
        print(f"[ERROR] Missing file: {exc}")
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] {type(exc).__name__}: {exc}")
        sys.exit(2)


if __name__ == "__main__":
    main()
