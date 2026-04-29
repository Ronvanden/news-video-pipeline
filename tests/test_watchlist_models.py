"""Unit-Tests für Watchlist-Pydantic-Modelle."""

import unittest

from pydantic import ValidationError

from app.watchlist.models import WatchlistChannelCreateRequest


class TestWatchlistModels(unittest.TestCase):
    def test_a_defaults(self):
        m = WatchlistChannelCreateRequest(
            channel_url="https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw"
        )
        self.assertEqual(m.check_interval, "manual")
        self.assertEqual(m.max_results, 5)
        self.assertFalse(m.auto_generate_script)
        self.assertTrue(m.auto_review_script)
        self.assertEqual(m.target_language, "de")
        self.assertEqual(m.duration_minutes, 10)
        self.assertEqual(m.min_score, 40)
        self.assertTrue(m.ignore_shorts)
        self.assertEqual(m.notes, "")

    def test_b_max_results_validation(self):
        with self.assertRaises(ValidationError):
            WatchlistChannelCreateRequest(
                channel_url="https://www.youtube.com/channel/UCxxxxxxxxxxxxxxxxxxxxxxxxxx",
                max_results=51,
            )
        with self.assertRaises(ValidationError):
            WatchlistChannelCreateRequest(
                channel_url="https://www.youtube.com/channel/UCxxxxxxxxxxxxxxxxxxxxxxxxxx",
                max_results=0,
            )

    def test_c_min_score_bounds(self):
        with self.assertRaises(ValidationError):
            WatchlistChannelCreateRequest(
                channel_url="https://www.youtube.com/channel/UCxxxxxxxxxxxxxxxxxxxxxxxxxx",
                min_score=-1,
            )
        with self.assertRaises(ValidationError):
            WatchlistChannelCreateRequest(
                channel_url="https://www.youtube.com/channel/UCxxxxxxxxxxxxxxxxxxxxxxxxxx",
                min_score=101,
            )

    def test_d_empty_channel_url(self):
        with self.assertRaises(ValidationError):
            WatchlistChannelCreateRequest(channel_url="")


if __name__ == "__main__":
    unittest.main()
