#!/usr/bin/env python3
"""Read-only media inspection; Python standard library + FFmpeg/FFprobe."""
import argparse
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import subprocess
import sys


def command(args):
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise ValueError(result.stderr.decode(errors="replace")[-1800:])
    return result.stdout


def intervals(mask, times, step):
    found, start = [], None
    for i, enabled in enumerate(mask + [False]):
        if enabled and start is None:
            start = i
        elif not enabled and start is not None:
            found.append([round(times[start], 6), round(times[i - 1] + step, 6)])
            start = None
    return found


def contained(span, allowed):
    return any(span[0] >= a - .035 and span[1] <= b + .035 for a, b in allowed)


def inspect(path, args):
    probe = shutil.which("ffprobe")
    ffmpeg = shutil.which("ffmpeg")
    if not probe or not ffmpeg:
        raise ValueError("FFmpeg and FFprobe are required; no dependencies were installed")
    plan = json.loads(Path(args.plan).read_text(encoding="utf8")) if args.plan else {}
    if not isinstance(plan, dict):
        raise ValueError("Plan must be a JSON object")
    meta = json.loads(command([probe, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]))
    video = next((x for x in meta.get("streams", []) if x["codec_type"] == "video"), None)
    if video is None:
        raise ValueError("No video stream")
    fps = float(Fraction(video.get("avg_frame_rate", "0/1")))
    if fps <= 0:
        raise ValueError("Cannot determine frame rate")
    duration = float(video.get("duration", meta.get("format", {}).get("duration", 0)))
    audio = [s for s in meta["streams"] if s["codec_type"] == "audio"]
    failures, flags = [], []
    expected = {"duration":args.duration, "fps":args.fps, "width":args.width, "height":args.height}
    for key in expected:
        if expected[key] is None:
            expected[key] = plan.get(key)
    actual = {"duration":duration, "fps":fps, "width":video["width"], "height":video["height"]}
    for key, wanted in expected.items():
        if wanted is None:
            continue
        tolerance = .5 / fps + .001 if key == "duration" else .01 if key == "fps" else 0
        if abs(float(actual[key]) - float(wanted)) > tolerance:
            failures.append({"check":key, "expected":wanted, "actual":actual[key]})
    wanted_audio = args.audio if args.audio is not None else plan.get("audio", "any")
    if wanted_audio == "required" and not audio or wanted_audio == "absent" and audio:
        failures.append({"check":"audio_presence", "expected":wanted_audio, "actual":bool(audio)})

    # Do not let a failed decoder produce a green report.
    decode = subprocess.run([ffmpeg, "-v", "error", "-threads", "2", "-i", str(path),
                             "-f", "null", "-"], capture_output=True)
    if decode.returncode or decode.stderr.strip():
        failures.append({"check":"full_decode", "detail":decode.stderr.decode(errors="replace")[-1800:]})

    frame_meta = json.loads(command([probe, "-v", "error", "-select_streams", "v:0", "-show_frames",
       "-show_entries", "frame=best_effort_timestamp_time", "-of", "json", str(path)]))["frames"]
    times = [float(f["best_effort_timestamp_time"]) for f in frame_meta if "best_effort_timestamp_time" in f]
    if not times:
        raise ValueError("No frame timestamps")
    relative = [t - times[0] for t in times]
    steps = [b - a for a, b in zip(times, times[1:])]
    if any(d <= 0 for d in steps):
        failures.append({"check":"timestamp_order", "detail":"Repeated or decreasing timestamps"})
    if expected["duration"] is not None and expected["fps"] is not None:
        count = round(float(expected["duration"]) * float(expected["fps"]))
        if len(times) != count:
            failures.append({"check":"frame_count", "expected":count, "actual":len(times)})
    irregular = [i for i, d in enumerate(steps) if abs(d - 1 / fps) > max(.002, .15 / fps)]
    if irregular:
        flags.append({"kind":"irregular_frame_timing", "count":len(irregular),
                      "times":[round(relative[i], 4) for i in irregular[:20]],
                      "note":"Variable timing is a measurement, not proof of dropped frames"})

    raw = command([ffmpeg, "-v", "error", "-threads", "2", "-i", str(path), "-an", "-sn", "-dn",
                   "-vf", "scale=96:54:flags=area", "-fps_mode", "passthrough", "-pix_fmt", "gray",
                   "-f", "rawvideo", "-"])
    size = 96 * 54
    if len(raw) % size:
        raise ValueError("Incomplete raw frame")
    frames = [raw[i:i + size] for i in range(0, len(raw), size)]
    if len(frames) != len(times):
        raise ValueError("Decoded frame count does not match timestamps")
    means = [sum(f) / size for f in frames]
    deltas = [sum(abs(x - y) for x, y in zip(a, b)) / size for a, b in zip(frames, frames[1:])]
    black = [sum(v < 12 for v in f) / size > .985 for f in frames]
    for span in intervals(black, relative, 1 / fps):
        if span[1] - span[0] >= .1 and not contained(span, plan.get("intentional_black", [])):
            flags.append({"kind":"black_frames", "span":span})
    quiet = [False] + [d < .15 for d in deltas]
    for span in intervals(quiet, relative, 1 / fps):
        if span[1] - span[0] >= .45 and not contained(span, plan.get("intentional_holds", [])):
            flags.append({"kind":"freeze", "span":span,
                          "note":"May be intentional; inspect motion inside the shot"})
    cuts = plan.get("cuts", [])
    def near_cut(t):
        return any(abs(t - c) <= 2 / fps for c in cuts)
    flicker = []
    for i in range(1, len(means) - 1):
        a, b = means[i] - means[i - 1], means[i + 1] - means[i]
        if a * b < 0 and min(abs(a), abs(b)) > 14 and not near_cut(relative[i]):
            flicker.append(round(relative[i], 4))
    if flicker:
        flags.append({"kind":"flicker", "count":len(flicker), "times":flicker[:30],
                      "note":"Brightness reversal; compare with the intended transition"})
    jumps = [round(relative[i + 1], 4) for i, d in enumerate(deltas) if d > 32 and not near_cut(relative[i + 1])]
    if jumps:
        flags.append({"kind":"abrupt_visual_change", "count":len(jumps), "times":jumps[:30]})

    # This checks declared source copy and boxes, not OCR or actual rendered glyph bounds.
    blocks = plan.get("text_blocks", [])
    if plan.get("text") is False and any(b.get("text", "").strip() for b in blocks):
        failures.append({"check":"no_text", "detail":"No-text variant contains authored titles"})
    forbidden = plan.get("forbidden_strings", [])
    margins = plan.get("safe_area", [0, 0, 0, 0])  # top,right,bottom,left, pixels
    if len(margins) != 4:
        raise ValueError("safe_area must contain top,right,bottom,left")
    for block in blocks:
        copy = block.get("text", "")
        for word in forbidden:
            if word.casefold() in copy.casefold():
                failures.append({"check":"localization", "found":word, "text":copy})
        start, end = block.get("start", 0), block.get("end", duration)
        if start < 0 or end <= start or end > duration + .001:
            failures.append({"check":"text_timing", "text":copy})
        if "box" in block:
            x, y, w, h = block["box"]
            if x < margins[3] or y < margins[0] or x + w > video["width"] - margins[1] or y + h > video["height"] - margins[2]:
                failures.append({"check":"safe_area", "text":copy, "declared_box":block["box"]})
        if end - start < block.get("min_read_seconds", 0):
            failures.append({"check":"reading_time", "text":copy})
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for part in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(part)
    return {"status":"fail" if failures else "review" if flags else "technical_pass",
       "file":str(path), "sha256":digest.hexdigest(), "checked_at":datetime.now(timezone.utc).isoformat(),
       "video":{**actual, "frames":len(frames), "codec":video["codec_name"], "pixel_format":video.get("pix_fmt")},
       "audio_streams":len(audio), "full_decode":not(decode.returncode or decode.stderr.strip()),
       "measurements":{"max_frame_interval":max(steps) if steps else 0,
        "median_frame_interval":statistics.median(steps) if steps else 0,
        "near_identical_frame_pairs":sum(d < .15 for d in deltas),
        "max_adjacent_pixel_delta":max(deltas) if deltas else 0},
       "failures":failures, "review_flags":flags, "visual_review_complete":False,
       "manual_checks":["Rendered text/fonts/localization/safe area", "Camera and object continuity at every cut",
                        "Music and action sync", "Art direction, readability and authenticity of game assets"],
       "limits":"Downsampled grayscale heuristics do not prove smoothness, detect all local layout jumps, verify speech timing or OCR titles"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--duration", type=float)
    parser.add_argument("--fps", type=float)
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--audio", choices=["required", "absent", "any"])
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        if not args.video.is_file():
            raise ValueError("Input video does not exist")
        if args.report and args.report.exists():
            raise ValueError("Report exists; choose a new report path")
        report = inspect(args.video.resolve(), args)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            with args.report.open("x", encoding="utf8") as target:
                json.dump(report, target, ensure_ascii=False, indent=2)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2 if report["failures"] else 3 if report["review_flags"] else 0
    except (ValueError, OSError, KeyError, TypeError, ZeroDivisionError, StopIteration, json.JSONDecodeError) as error:
        print(json.dumps({"status":"fail", "failures":[{"check":"inspection", "detail":str(error)}]}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
