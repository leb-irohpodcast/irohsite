import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "sync_instagram.py"
SPEC = importlib.util.spec_from_file_location("sync_instagram", SCRIPT_PATH)
sync_instagram = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync_instagram)


class InstagramTitleTests(unittest.TestCase):
    def test_generates_stagea_stand_down_title(self):
        caption = (
            "Some Stagea updates from the Juice Holler Garage. Nothing fun, "
            "of course. Suspension issues and timing belt struggles.\n\n-Justin"
        )

        self.assertEqual(
            sync_instagram.rule_generated_title(caption, "PHOTO SET"),
            "Stagea stand-down at Juice Holler",
        )

    def test_generates_known_hbi_title_patterns(self):
        examples = {
            "The Reservoir Report accompanying media, for y'all.": (
                "The Reservoir Report"
            ),
            "The Fleet added a Fiat after a trip to the market.": (
                "The Fleet adds a Fiat"
            ),
            "This week's happenings around the Brazilian Studio.": (
                "This week at the Brazilian Studio"
            ),
        }

        for caption, expected in examples.items():
            with self.subTest(caption=caption):
                self.assertEqual(
                    sync_instagram.rule_generated_title(caption, "PHOTO SET"),
                    expected,
                )

    def test_compacts_unfamiliar_caption(self):
        title = sync_instagram.rule_generated_title(
            "Quick evening dispatch covering unexpected developments at "
            "headquarters before tomorrow morning.",
            "PHOTO",
        )

        self.assertEqual(title, "Evening dispatch covering unexpected developments")
        self.assertLessEqual(len(title), 64)
        self.assertLessEqual(len(title.split()), 8)
        self.assertGreaterEqual(len(title.split()), 2)
        self.assertNotIn(title.split()[-1].lower(), {"at", "for", "of", "the", "to"})

    def test_preserves_editorial_title_without_rule_generation(self):
        existing = {
            "title": "The Reservoir Report",
            "caption": "The Reservoir Report accompanying media, for y'all.",
        }

        with patch.object(
            sync_instagram, "rule_generated_title"
        ) as rule_generated_title:
            title, source = sync_instagram.post_title("Updated caption", "PHOTO SET", existing)

        self.assertEqual((title, source), ("The Reservoir Report", "editorial"))
        rule_generated_title.assert_not_called()

    def test_preserves_existing_rule_title(self):
        existing = {
            "title": "Stagea stand-down at Juice Holler",
            "title_source": "rules",
            "caption": "An older caption",
        }

        title, source = sync_instagram.post_title(
            "An updated caption", "PHOTO SET", existing
        )

        self.assertEqual(title, "Stagea stand-down at Juice Holler")
        self.assertEqual(source, "rules")

    def test_replaces_caption_fallback_with_rule_title(self):
        caption = "Some Stagea updates from the Juice Holler Garage."
        existing = {
            "title": caption,
            "title_source": "caption",
            "caption": caption,
        }

        with patch.object(sync_instagram, "urlopen") as urlopen:
            title, source = sync_instagram.post_title(caption, "PHOTO SET", existing)

        self.assertEqual(title, "Stagea stand-down at Juice Holler")
        self.assertEqual(source, "rules")
        urlopen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
