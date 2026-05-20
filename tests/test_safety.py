import unittest

from config import (
    OCEAN_SWELL_DANGER,
    OCEAN_WIND_DANGER,
    SHELTERED_SWELL_WARN,
    SHELTERED_WIND_WARN,
)
from domain.safety import assess_safety


class SafetyAssessmentTest(unittest.TestCase):
    def test_ocean_spot_is_coral_above_swell_threshold(self):
        result = assess_safety(
            {"water_type": "ocean"},
            {"swell_height": OCEAN_SWELL_DANGER + 0.1, "wind": 5},
        )
        self.assertEqual(result["color"], "coral")
        self.assertFalse(result["safe"])

    def test_ocean_spot_is_coral_above_wind_threshold(self):
        result = assess_safety(
            {"water_type": "ocean"},
            {"swell_height": 0.5, "wind": OCEAN_WIND_DANGER + 1},
        )
        self.assertEqual(result["color"], "coral")
        self.assertFalse(result["safe"])

    def test_harbour_spot_warns_above_sheltered_threshold(self):
        result = assess_safety(
            {"water_type": "harbour"},
            {"swell_height": SHELTERED_SWELL_WARN + 0.1, "wind": 5},
        )
        self.assertEqual(result["color"], "amber")
        self.assertTrue(result["safe"])

    def test_freshwater_ignores_swell_and_warns_on_wind(self):
        result = assess_safety(
            {"water_type": "freshwater"},
            {"swell_height": 5.0, "wind": SHELTERED_WIND_WARN + 1},
        )
        self.assertEqual(result["color"], "amber")
        self.assertTrue(result["safe"])

    def test_calm_harbour_is_recommended(self):
        result = assess_safety(
            {"water_type": "harbour"},
            {"swell_height": 0.5, "wind": 5},
        )
        self.assertEqual(result["color"], "sage")
        self.assertTrue(result["safe"])

    def test_sheltered_boat_spot_uses_sheltered_threshold(self):
        result = assess_safety(
            {"water_type": "boat", "sheltered": True},
            {"swell_height": SHELTERED_SWELL_WARN + 0.1, "wind": 5},
        )
        self.assertEqual(result["color"], "amber")
        self.assertTrue(result["safe"])
        self.assertNotIn("外海", result["advice"])

    def test_exposed_boat_spot_uses_ocean_threshold(self):
        result = assess_safety(
            {"water_type": "boat", "sheltered": False},
            {"swell_height": OCEAN_SWELL_DANGER + 0.1, "wind": 5},
        )
        self.assertEqual(result["color"], "coral")
        self.assertFalse(result["safe"])


if __name__ == "__main__":
    unittest.main()
