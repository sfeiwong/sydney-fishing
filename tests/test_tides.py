import unittest
from datetime import datetime
from unittest.mock import patch

from services import tides


class TideServiceTest(unittest.TestCase):
    def test_official_fort_denison_override_for_may_22(self):
        result = tides.get_tides_for_date(datetime(2026, 5, 22))
        self.assertEqual(
            [(x["time"].strftime("%H:%M"), x["height_m"], x["is_high"]) for x in result],
            [
                ("00:16", 1.89, True),
                ("07:19", 0.45, False),
                ("13:25", 1.36, True),
                ("18:51", 0.75, False),
            ],
        )
        self.assertEqual(result[0]["source"], "nsw_official")

    def test_official_delay_shifts_times_only(self):
        result = tides.get_tides_for_date(datetime(2026, 5, 22), delay_minutes=15)
        self.assertEqual(result[0]["time"].strftime("%H:%M"), "00:31")
        self.assertEqual(result[0]["height_m"], 1.89)

    def test_estimate_returns_four_events(self):
        result = tides.get_tides_for_date(datetime(2026, 5, 20), delay_minutes=10)
        self.assertEqual(len(result), 4)
        self.assertTrue(all("time" in x and "is_high" in x and "label" in x for x in result))

    @patch("services.tides._worldtides_key", return_value="abc")
    @patch("services.tides._fetch_worldtides_extremes")
    def test_worldtides_is_used_when_available(self, mock_fetch, _mock_key):
        mock_fetch.return_value = [
            {"time": datetime(2026, 5, 20, 2, 0), "is_high": True, "label": "🟢 满潮"},
            {"time": datetime(2026, 5, 20, 8, 10), "is_high": False, "label": "🔵 干潮"},
            {"time": datetime(2026, 5, 20, 14, 20), "is_high": True, "label": "🟢 满潮"},
            {"time": datetime(2026, 5, 20, 20, 30), "is_high": False, "label": "🔵 干潮"},
        ]
        result = tides.get_tides_for_date(datetime(2026, 5, 20), lat=-33.85, lon=151.2)
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0]["time"].hour, 2)
        mock_fetch.assert_called_once()

    @patch("services.tides._worldtides_key", return_value="abc")
    @patch("services.tides._fetch_worldtides_extremes", side_effect=RuntimeError("boom"))
    def test_falls_back_when_worldtides_fails(self, _mock_fetch, _mock_key):
        result = tides.get_tides_for_date(datetime(2026, 5, 20), delay_minutes=5, lat=-33.85, lon=151.2)
        self.assertEqual(len(result), 4)


if __name__ == "__main__":
    unittest.main()
