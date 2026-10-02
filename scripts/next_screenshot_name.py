#!/usr/bin/env python3
"""Print an unused screenshot filename; never create, capture or upload a file."""
import argparse
from pathlib import Path


def next_path(directory: Path) -> Path:
    index = 1
    while (directory / f"test{index}.png").exists():
        index += 1
    return directory / f"test{index}.png"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path.home() / "Downloads")
    args = parser.parse_args()
    print(next_path(args.directory.expanduser()))
