import unittest

from data.loader import load_spots, validate_spots


class SpotLoaderTest(unittest.TestCase):
    def test_current_spot_database_is_valid(self):
        self.assertGreater(len(load_spots()), 0)

    def test_validation_catches_unknown_water_type(self):
        errors = validate_spots([
            {
                "name": "Invalid Spot",
                "region": "Test",
                "type": "Test",
                "lat": -33.0,
                "lon": 151.0,
                "water_type": "reef",
                "tide_delay": 0,
                "fish_tags": [],
                "best_window": "Any",
                "family_friendly": "⭐⭐⭐⭐",
                "supported_methods": [],
                "method_tips": {},
                "route": "Test",
                "parking": "Test",
            }
        ])
        self.assertTrue(any("invalid water_type" in error for error in errors))

    def test_validation_requires_complete_map_coordinates(self):
        errors = validate_spots([
            {
                "name": "Incomplete Map Coords",
                "region": "Test",
                "type": "Test",
                "lat": -33.0,
                "lon": 151.0,
                "map_lat": -33.1,
                "water_type": "harbour",
                "tide_delay": 0,
                "fish_tags": [],
                "best_window": "Any",
                "family_friendly": "⭐⭐⭐⭐",
                "supported_methods": [],
                "method_tips": {},
                "route": "Test",
                "parking": "Test",
            }
        ])
        self.assertTrue(any("map_lat and map_lon" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
