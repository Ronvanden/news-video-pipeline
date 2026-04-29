"""Tests für Watchlist-Service mit gemocktem Firestore-Repository."""

import unittest
from unittest.mock import MagicMock, patch

from app.watchlist.firestore_repo import FirestoreWatchlistRepository
from app.watchlist.models import WatchlistChannelCreateRequest
from app.watchlist import service as watchlist_service


class TestWatchlistService(unittest.TestCase):
    @patch.object(watchlist_service, "fetch_channel_feed_entries")
    @patch.object(watchlist_service, "resolve_channel_id")
    def test_e_mocked_firestore_create_and_list(
        self, mock_resolve, mock_feed
    ):
        cid = "UC_x5XG1OV2P6uZZ5FSM9Ttw"
        mock_resolve.return_value = (cid, [])
        mock_feed.return_value = ("Channel Name - YouTube", [], [])

        stored: dict = {}

        repo = MagicMock(spec=FirestoreWatchlistRepository)

        def get_doc(x: str):
            if x == cid and cid in stored:
                return dict(stored[cid])
            return None

        def upsert(x: str, data: dict) -> None:
            row = dict(data)
            row["id"] = x
            stored[x] = row

        def list_docs():
            rows = []
            for kid, row in stored.items():
                r = dict(row)
                if "id" not in r:
                    r["id"] = kid
                rows.append(r)
            return rows

        repo.get_watch_channel_doc.side_effect = get_doc
        repo.upsert_watch_channel.side_effect = upsert
        repo.list_watch_channel_docs.side_effect = list_docs

        req = WatchlistChannelCreateRequest(
            channel_url=f"https://www.youtube.com/channel/{cid}",
        )

        cre = watchlist_service.create_channel(req, repo=repo)
        mock_resolve.assert_called()
        mock_feed.assert_called_with(cid, 1)
        self.assertIsNotNone(cre.channel)

        lst = watchlist_service.list_channels(repo=repo)
        self.assertEqual(len(lst.channels), 1)
        self.assertEqual(lst.channels[0].channel_id, cid)
        self.assertEqual(lst.channels[0].channel_name, "Channel Name")


if __name__ == "__main__":
    unittest.main()
