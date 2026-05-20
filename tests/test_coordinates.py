import math
import unittest

from data.loader import load_spots


SYDNEY_BOUNDS = {
    "lat_min": -34.35,
    "lat_max": -33.45,
    "lon_min": 150.55,
    "lon_max": 151.40,
}

MAP_OFFSET_MAX_KM = 5.0
NAV_OFFSET_MAX_KM = 12.0
WEATHER_OFFSET_MAX_KM = 50.0


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dlat = p2 - p1
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


class SpotCoordinateHealthTest(unittest.TestCase):
    def test_spot_coordinates_are_within_sydney_bounds(self):
        spots = load_spots()
        for spot in spots:
            lat = spot.get("fishing_lat", spot["lat"])
            lon = spot.get("fishing_lon", spot["lon"])
            self.assertGreaterEqual(lat, SYDNEY_BOUNDS["lat_min"], spot["name"])
            self.assertLessEqual(lat, SYDNEY_BOUNDS["lat_max"], spot["name"])
            self.assertGreaterEqual(lon, SYDNEY_BOUNDS["lon_min"], spot["name"])
            self.assertLessEqual(lon, SYDNEY_BOUNDS["lon_max"], spot["name"])

    def test_map_coordinate_offset_is_reasonable(self):
        spots = load_spots()
        for spot in spots:
            fish_lat = spot.get("fishing_lat", spot["lat"])
            fish_lon = spot.get("fishing_lon", spot["lon"])
            map_lat = spot.get("map_lat", fish_lat)
            map_lon = spot.get("map_lon", fish_lon)
            km = _haversine_km(fish_lat, fish_lon, map_lat, map_lon)
            self.assertLessEqual(km, MAP_OFFSET_MAX_KM, f"{spot['name']} map offset {km:.2f}km")

    def test_nav_coordinate_offset_is_reasonable(self):
        spots = load_spots()
        for spot in spots:
            fish_lat = spot.get("fishing_lat", spot["lat"])
            fish_lon = spot.get("fishing_lon", spot["lon"])
            nav_lat = spot.get("nav_lat", fish_lat)
            nav_lon = spot.get("nav_lon", fish_lon)
            km = _haversine_km(fish_lat, fish_lon, nav_lat, nav_lon)
            self.assertLessEqual(km, NAV_OFFSET_MAX_KM, f"{spot['name']} nav offset {km:.2f}km")

    def test_weather_coordinate_offset_is_reasonable(self):
        spots = load_spots()
        for spot in spots:
            fish_lat = spot.get("fishing_lat", spot["lat"])
            fish_lon = spot.get("fishing_lon", spot["lon"])
            weather_lat = spot.get("weather_lat", fish_lat)
            weather_lon = spot.get("weather_lon", fish_lon)
            km = _haversine_km(fish_lat, fish_lon, weather_lat, weather_lon)
            self.assertLessEqual(
                km,
                WEATHER_OFFSET_MAX_KM,
                f"{spot['name']} weather offset {km:.2f}km",
            )


if __name__ == "__main__":
    unittest.main()
