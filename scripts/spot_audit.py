#!/usr/bin/env python3
import json
import math
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.loader import load_spots

BASELINE_PATH = Path("data/spot_baseline.json")
REPORT_PATH = Path("reports/spot_audit_latest.json")

DRIFT_HIGH_METERS = 150.0
DRIFT_CRITICAL_METERS = 300.0

SYDNEY_BOUNDS = {"lat_min": -34.35, "lat_max": -33.45, "lon_min": 150.55, "lon_max": 151.40}


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dlat = p2 - p1
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


def severity_rank(level: str) -> int:
    return {"critical": 0, "high": 1, "medium": 2}.get(level, 9)


def classify_geofence_issue(spot: dict) -> Optional[str]:
    name = spot["name"]
    lat = spot.get("fishing_lat", spot["lat"])
    lon = spot.get("fishing_lon", spot["lon"])

    if (
        lat < SYDNEY_BOUNDS["lat_min"] or lat > SYDNEY_BOUNDS["lat_max"]
        or lon < SYDNEY_BOUNDS["lon_min"] or lon > SYDNEY_BOUNDS["lon_max"]
    ):
        return f"{name}: coordinate out of Sydney bounds"
    return None


def main() -> int:
    spots = load_spots()
    findings = []

    if BASELINE_PATH.exists():
        baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    else:
        baseline = {}

    for spot in spots:
        name = spot["name"]
        lat = spot.get("fishing_lat", spot["lat"])
        lon = spot.get("fishing_lon", spot["lon"])
        previous = baseline.get(name)

        geofence_reason = classify_geofence_issue(spot)
        if geofence_reason:
            findings.append(
                {
                    "spot_name": name,
                    "severity": "critical",
                    "reason": geofence_reason,
                    "current_coord": {"lat": lat, "lon": lon},
                    "previous_coord": previous or {"lat": lat, "lon": lon},
                }
            )

        if previous is None:
            findings.append(
                {
                    "spot_name": name,
                    "severity": "medium",
                    "reason": "missing baseline coordinate",
                    "current_coord": {"lat": lat, "lon": lon},
                    "previous_coord": {"lat": lat, "lon": lon},
                }
            )
            continue

        drift_m = haversine_meters(lat, lon, previous["lat"], previous["lon"])
        if drift_m > DRIFT_CRITICAL_METERS:
            severity = "critical"
        elif drift_m > DRIFT_HIGH_METERS:
            severity = "high"
        else:
            severity = None

        if severity:
            findings.append(
                {
                    "spot_name": name,
                    "severity": severity,
                    "reason": f"coordinate drift {drift_m:.1f}m exceeds threshold",
                    "current_coord": {"lat": lat, "lon": lon},
                    "previous_coord": {"lat": previous["lat"], "lon": previous["lon"]},
                }
            )

    findings.sort(key=lambda item: (severity_rank(item["severity"]), item["spot_name"]))
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(findings, ensure_ascii=False, indent=2), encoding="utf-8")

    critical_high_count = sum(1 for item in findings if item["severity"] in {"critical", "high"})
    medium_count = sum(1 for item in findings if item["severity"] == "medium")
    print(f"Spot audit complete: {critical_high_count} high/critical, {medium_count} medium")
    print(f"Report: {REPORT_PATH}")
    return 1 if critical_high_count > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
