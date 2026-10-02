#!/usr/bin/env python3
"""Type supplied text into the active macOS app, one character at a time."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
import time


def escape_applescript(value: str) -> str:
    """Escape text embedded in an AppleScript string literal."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def applescript_for_character(character: str) -> str:
    """Return one System Events action for exactly one character."""
    if character == "\n":
        return 'tell application "System Events" to key code 36'
    escaped = escape_applescript(character)
    return (
        f'set the clipboard to "{escaped}"\n'
        'tell application "System Events" to keystroke "v" using command down\n'
        'delay 0.05'
    )


def character_scripts(text: str) -> list[str]:
    """Turn text into one macOS keyboard action per character."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return [applescript_for_character(character) for character in normalized]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Type text into the currently focused macOS app one character at a time."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text", help="Text to type.")
    source.add_argument("--file", type=Path, help="UTF-8 text file to type.")
    parser.add_argument(
        "--delay",
        type=float,
        default=5.0,
        help="Seconds to wait for the user to focus the target window (default: 5).",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.03,
        help="Seconds between characters (default: 0.03).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the number of keyboard actions without sending input.",
    )
    parser.add_argument("--app", help="Activate this macOS application before typing.")
    parser.add_argument("--click-x", type=int, help="Screen X coordinate to click before typing.")
    parser.add_argument("--click-y", type=int, help="Screen Y coordinate to click before typing.")
    parser.add_argument(
        "--document-end",
        action="store_true",
        help="Press Command+Down after focusing the target, before typing.",
    )
    parser.add_argument(
        "--strip-final-newline",
        action="store_true",
        help="Remove one final newline from file or text input before typing.",
    )
    args = parser.parse_args()
    if args.delay < 0 or args.interval < 0:
        parser.error("--delay and --interval must be zero or greater")
    if (args.click_x is None) != (args.click_y is None):
        parser.error("--click-x and --click-y must be provided together")
    return args


def text_from_args(args: argparse.Namespace) -> str:
    return args.text if args.text is not None else args.file.read_text(encoding="utf-8")


def focus_target(args: argparse.Namespace) -> None:
    """Optionally activate an app and focus a screen coordinate in one run."""
    lines: list[str] = []
    if args.app:
        app = escape_applescript(args.app)
        lines.append(f'tell application "{app}" to activate')
        lines.append("delay 0.5")
    if args.click_x is not None:
        lines.append(
            f'tell application "System Events" to click at {{{args.click_x}, {args.click_y}}}'
        )
        lines.append("delay 0.5")
    if args.document_end:
        lines.append('tell application "System Events" to key code 125 using command down')
        lines.append("delay 0.3")
    if lines:
        subprocess.run(["osascript", "-e", "\n".join(lines)], check=True)


def main() -> int:
    args = parse_args()
    text = text_from_args(args)
    if args.strip_final_newline and text.endswith(("\n", "\r")):
        text = text.rstrip("\r\n")
    scripts = character_scripts(text)

    if args.dry_run:
        print(f"Dry run: {len(scripts)} individual keyboard actions; no input was sent.")
        return 0

    print(
        f"Typing starts in {args.delay:g}s. Focus the target field now; press Control-C to cancel."
    )
    time.sleep(args.delay)
    saved_clipboard = subprocess.run(
        ["pbpaste"], capture_output=True, check=False
    ).stdout
    try:
        focus_target(args)
        for index, script in enumerate(scripts):
            subprocess.run(["osascript", "-e", script], check=True)
            if index + 1 < len(scripts):
                time.sleep(args.interval)
    except subprocess.CalledProcessError:
        print(
            "Typing stopped. Allow Accessibility access for the terminal or Python in macOS settings, "
            "then try again.",
            file=sys.stderr,
        )
        return 1
    finally:
        time.sleep(0.2)
        subprocess.run(["pbcopy"], input=saved_clipboard, check=False)

    print(f"Typed {len(scripts)} individual keyboard actions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
