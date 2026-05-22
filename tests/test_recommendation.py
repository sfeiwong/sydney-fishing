import unittest
from datetime import date

from domain.recommendation import (
    editorial_reputation_score,
    log_reputation_score,
    recommendation_score,
)


class RecommendationScoringTest(unittest.TestCase):
    def test_calm_reputed_spot_beats_calm_plain_spot(self):
        weather = {"swell_height": 0.4, "wind": 6, "rain_prob": 10, "uv": 4}
        safety = {"color": "sage"}
        tides = [{"is_high": True}]
        plain = {
            "water_type": "harbour",
            "family_friendly": "⭐⭐⭐",
            "supported_methods": ["无铅漂钓"],
            "fish_tags": ["Bream (鳊鱼)"],
            "best_window": "白天均可",
            "method_tips": {"无铅漂钓": "可用虾肉作钓。"},
        }
        reputed = {
            **plain,
            "family_friendly": "⭐⭐⭐⭐⭐",
            "best_window": "🌅 破晓至上午 9 点最佳。",
            "method_tips": {"无铅漂钓": "🎯 顶级推荐！这里是稳定出产大 Bream 的核心钓点。"},
        }

        self.assertGreater(
            recommendation_score(reputed, safety, weather, tides),
            recommendation_score(plain, safety, weather, tides),
        )

    def test_log_reputation_rewards_recent_catches(self):
        entries = [
            {
                "fish_date": "2026-05-01",
                "author": "A",
                "fish_caught": ["Bream (鳊鱼)", "Squid (鱿鱼)"],
                "photos": [b"img"],
                "notes": "夜钓两小时有稳定咬口，码头灯下表现不错。",
            },
            {
                "fish_date": "2026-04-20",
                "author": "B",
                "fish_caught": ["Bream (鳊鱼)"],
                "photos": [],
                "notes": "涨潮前后有口。",
            },
        ]

        self.assertGreater(log_reputation_score(entries, date(2026, 5, 22)), 0)

    def test_editorial_reputation_has_cap(self):
        spot = {
            "method_tips": {
                "a": "🎯 顶级推荐！最佳核心圣地高产稳定密度高频繁常年出产纪录不稀奇",
                "b": "🎯 顶级推荐！最佳核心圣地高产稳定密度高频繁常年出产纪录不稀奇",
            }
        }

        self.assertLessEqual(editorial_reputation_score(spot), 12)


if __name__ == "__main__":
    unittest.main()
