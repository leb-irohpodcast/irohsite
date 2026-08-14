import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "sync_instagram.py"
SPEC = importlib.util.spec_from_file_location("sync_instagram", SCRIPT_PATH)
sync_instagram = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync_instagram)


class InstagramTitleTests(unittest.TestCase):
    def test_extracts_and_cleans_response_title(self):
        payload = {
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": 'Title: "Timing-belt stand-down."',
                        }
                    ],
                }
            ]
        }

        title = sync_instagram.clean_generated_title(
            sync_instagram.response_output_text(payload)
        )

        self.assertEqual(title, "Timing-belt stand-down")

    def test_rejects_an_overlong_generated_title(self):
        self.assertEqual(
            sync_instagram.clean_generated_title("One two three four five six seven eight nine"),
            "",
        )

    def test_preserves_editorial_title_without_openai_call(self):
        existing = {
            "title": "The Reservoir Report",
            "caption": "The Reservoir Report accompanying media, for y'all.",
        }

        with patch.object(sync_instagram, "generate_title") as generate_title:
            title, source = sync_instagram.post_title("Updated caption", "PHOTO SET", existing)

        self.assertEqual((title, source), ("The Reservoir Report", "editorial"))
        generate_title.assert_not_called()

    def test_replaces_caption_fallback_with_generated_title(self):
        caption = "Some Stagea updates from the Juice Holler Garage."
        existing = {"title": caption, "caption": caption}

        with patch.object(
            sync_instagram,
            "generate_title",
            return_value="Stagea surgery at Juice Holler",
        ):
            title, source = sync_instagram.post_title(caption, "PHOTO SET", existing)

        self.assertEqual(title, "Stagea surgery at Juice Holler")
        self.assertEqual(source, "openai")

    def test_calls_responses_api_without_storing_response(self):
        response_payload = {
            "output": [
                {
                    "type": "message",
                    "content": [
                        {"type": "output_text", "text": "Garage dispatch from Knoxville"}
                    ],
                }
            ]
        }
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(
            response_payload
        ).encode("utf-8")

        with (
            patch.object(sync_instagram, "OPENAI_API_KEY", "test-key"),
            patch.object(sync_instagram, "urlopen", return_value=response) as urlopen,
        ):
            title = sync_instagram.generate_title("Working on the wagon", "PHOTO")

        request = urlopen.call_args.args[0]
        request_payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(title, "Garage dispatch from Knoxville")
        self.assertEqual(request_payload["model"], "gpt-5.6-luna")
        self.assertFalse(request_payload["store"])


if __name__ == "__main__":
    unittest.main()
