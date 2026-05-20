import unittest

from data.loader import load_spots


class SpotIntegrityTest(unittest.TestCase):
    def test_unique_spot_names(self):
        spots = load_spots()
        names = [spot["name"] for spot in spots]
        self.assertEqual(len(names), len(set(names)), "duplicate spot names detected")

    def test_boat_spots_must_define_sheltered(self):
        spots = load_spots()
        missing = [
            spot["name"]
            for spot in spots
            if spot.get("water_type") == "boat" and "sheltered" not in spot
        ]
        self.assertFalse(missing, f"boat spots missing sheltered: {', '.join(missing)}")

    def test_core_coordinates_are_numeric_and_in_range(self):
        spots = load_spots()
        for spot in spots:
            lat = spot["lat"]
            lon = spot["lon"]
            self.assertIsInstance(lat, (int, float), f"{spot['name']} lat must be numeric")
            self.assertIsInstance(lon, (int, float), f"{spot['name']} lon must be numeric")
            self.assertGreaterEqual(lat, -90, f"{spot['name']} lat out of range")
            self.assertLessEqual(lat, 90, f"{spot['name']} lat out of range")
            self.assertGreaterEqual(lon, -180, f"{spot['name']} lon out of range")
            self.assertLessEqual(lon, 180, f"{spot['name']} lon out of range")


if __name__ == "__main__":
    unittest.main()
