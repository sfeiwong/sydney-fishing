# ============================================================
# data/loader.py — 钓点数据加载器
# ============================================================

import json
import os

_DATA_PATH = os.path.join(os.path.dirname(__file__), "spots.json")


def load_spots() -> list[dict]:
    """从 spots.json 加载所有钓点数据，返回 list[dict]。"""
    with open(_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
