"""Deterministic media fixtures. No service calls or agent delegation."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "video_qc.py"


class VideoQC(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.exists(), "video_qc.py has not been implemented")
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("FFmpeg tools are unavailable")
        self.temp = tempfile.TemporaryDirectory(prefix="video-quality-")
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def render(self, filter_graph, name="fixture.mp4", frames=30, extra=()):
        path = self.folder / name
        subprocess.run(["ffmpeg", "-v", "error", "-threads", "1", "-f", "lavfi",
                        "-i", filter_graph, "-frames:v", str(frames), "-an", "-c:v",
                        "libx264", "-threads", "1", "-pix_fmt", "yuv420p", *extra, str(path)], check=True)
        return path

    def inspect(self, path, *extra, plan=None):
        args = [sys.executable, str(SCRIPT), str(path), "--duration", "1", "--fps", "30",
                "--width", "96", "--height", "64", "--audio", "absent"]
        if plan:
            source = self.folder / "plan.json"
            source.write_text(json.dumps(plan), encoding="utf8")
            args += ["--plan", str(source)]
        result = subprocess.run(args + list(extra), capture_output=True, text=True)
        self.assertTrue(result.stdout.strip(), result.stderr)
        return result.returncode, json.loads(result.stdout)

    def test_valid_moving_clip(self):
        path = self.render("testsrc2=size=96x64:rate=30")
        code, report = self.inspect(path)
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "technical_pass")
        self.assertFalse(report["visual_review_complete"])

    def test_wrong_duration_fails(self):
        path = self.render("testsrc2=size=96x64:rate=30", frames=42)
        code, report = self.inspect(path)
        self.assertEqual(code, 2)
        self.assertIn("duration", {x["check"] for x in report["failures"]})

    def test_black_video_requires_review(self):
        path = self.render("color=black:size=96x64:rate=30")
        code, report = self.inspect(path)
        self.assertEqual(code, 3)
        self.assertIn("black_frames", {x["kind"] for x in report["review_flags"]})

    def test_static_video_requires_review(self):
        path = self.render("color=blue:size=96x64:rate=30")
        code, report = self.inspect(path)
        self.assertEqual(code, 3)
        self.assertIn("freeze", {x["kind"] for x in report["review_flags"]})

    def test_flicker_requires_review(self):
        path = self.render("nullsrc=size=96x64:rate=30,geq=lum='if(mod(N,2),230,70)':cb=128:cr=128")
        code, report = self.inspect(path)
        self.assertEqual(code, 3)
        self.assertIn("flicker", {x["kind"] for x in report["review_flags"]})

    def test_wrong_russian_branding_fails(self):
        path = self.render("testsrc2=size=96x64:rate=30")
        code, report = self.inspect(path, plan={"language":"ru", "text":True,
          "forbidden_strings":["Chess Arcade", "ChessArcade"],
          "text_blocks":[{"text":"CHESS ARCADE", "start":0, "end":1}]})
        self.assertEqual(code, 2)
        self.assertIn("localization", {x["check"] for x in report["failures"]})

    def test_no_text_variant_rejects_titles(self):
        path = self.render("testsrc2=size=96x64:rate=30")
        code, report = self.inspect(path, plan={"text":False,"text_blocks":[{"text":"Title","start":0,"end":1}]})
        self.assertEqual(code, 2)
        self.assertIn("no_text", {x["check"] for x in report["failures"]})

    def test_declared_text_outside_safe_area_fails(self):
        path = self.render("testsrc2=size=96x64:rate=30")
        code, report = self.inspect(path, plan={"text":True,"safe_area":[8,8,8,8],
          "text_blocks":[{"text":"Title","start":0,"end":1,"box":[1,2,90,20]}]})
        self.assertEqual(code, 2)
        self.assertIn("safe_area", {x["check"] for x in report["failures"]})

    def test_explicit_hold_is_not_an_unknown_freeze(self):
        path = self.render("color=blue:size=96x64:rate=30")
        code, report = self.inspect(path, plan={"intentional_holds":[[0,1]]})
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "technical_pass")

    def test_existing_report_is_not_overwritten(self):
        path = self.render("testsrc2=size=96x64:rate=30")
        target = self.folder / "report.json"
        target.write_text("preserve", encoding="utf8")
        code, report = self.inspect(path, "--report", str(target))
        self.assertEqual(code, 2)
        self.assertEqual(target.read_text(), "preserve")

    def test_variable_frame_intervals_are_reported(self):
        path = self.render("testsrc2=size=96x64:rate=30,setpts='if(gte(N,15),PTS+0.13333/TB,PTS)'",
                           extra=("-fps_mode", "vfr"))
        code, report = self.inspect(path)
        self.assertEqual(code, 2)
        self.assertIn("irregular_frame_timing", {x["kind"] for x in report["review_flags"]})
        self.assertGreater(report["measurements"]["max_frame_interval"], .06)

    def test_corrupt_container_is_not_a_green_result(self):
        path = self.folder / "bad.mp4"
        path.write_bytes(b"invalid media")
        code, report = self.inspect(path)
        self.assertEqual(code, 2)
        self.assertEqual(report["status"], "fail")

    def test_short_title_hold_fails(self):
        path = self.render("testsrc2=size=96x64:rate=30")
        code, report = self.inspect(path, plan={"text":True,
          "text_blocks":[{"text":"Title","start":0,"end":.1,"min_read_seconds":.5}]})
        self.assertEqual(code, 2)
        self.assertIn("reading_time", {x["check"] for x in report["failures"]})


if __name__ == "__main__":
    unittest.main()
