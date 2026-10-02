import importlib.util
from pathlib import Path
import unittest


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "type_text.py"
SPEC = importlib.util.spec_from_file_location("print_type_text", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class TypeTextTest(unittest.TestCase):
    def test_preserves_one_keyboard_action_per_character(self):
        scripts = MODULE.character_scripts("А\nБ")

        self.assertEqual(len(scripts), 3)
        self.assertEqual(scripts[1], 'tell application "System Events" to key code 36')
        self.assertIn('set the clipboard to "А"', scripts[0])
        self.assertIn('set the clipboard to "Б"', scripts[2])
        self.assertIn('keystroke "v" using command down', scripts[0])
        self.assertIn('keystroke "v" using command down', scripts[2])

    def test_escapes_backslash_and_quote_for_applescript(self):
        self.assertEqual(
            MODULE.escape_applescript('a\\"b'),
            "a" + "\\" * 3 + '"b',
        )
