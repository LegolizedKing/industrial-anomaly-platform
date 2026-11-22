"""Evaluate both fixed-reference detectors on the NAB ambient-temperature series."""

import argparse
import csv
import json
import math
from datetime import datetime
from pathlib import Path

from evaluate_detectors import METHODS, score

SERIES = "realKnownCause/ambient_temperature_system_failure.csv"


def evaluate(csv_path, windows_path):
    windows = [
        tuple(datetime.fromisoformat(value) for value in pair)
        for pair in json.loads(windows_path.read_text(encoding="utf-8"))[SERIES]
    ]
    with csv_path.open(newline="", encoding="utf-8") as stream:
        samples = [
            (datetime.fromisoformat(row["timestamp"]), float(row["value"]))
            for row in csv.DictReader(stream)
        ]
    if len(samples) < 10 or any(not math.isfinite(value) for _, value in samples):
        raise ValueError("expected at least ten finite observations")
    timestamps = [timestamp for timestamp, _ in samples]
    if any(left >= right for left, right in zip(timestamps, timestamps[1:])):
        raise ValueError("timestamps must strictly increase")
    origin = timestamps[0]
    readings = [
        {"second": (timestamp - origin).total_seconds(), "temperature": value}
        for timestamp, value in samples
    ]
    split = len(samples) // 10
    if min(start for start, _ in windows) <= timestamps[split - 1]:
        raise ValueError("a labeled window starts in the training period")

    later = timestamps[split:]
    hours = (later[-1] - later[0]).total_seconds() / 3600
    report = {"training_rows": split, "evaluation_rows": len(later), "detectors": {}}
    for method in METHODS:
        alerts = [
            timestamp for timestamp, result in zip(
                later, score(readings[:split], readings[split:], method, sensors=("temperature",))
            ) if result["alert"]
        ]
        outside = sum(not any(start <= alert <= end for start, end in windows) for alert in alerts)
        delays = {}
        for start, end in windows:
            first = next((alert for alert in alerts if start <= alert <= end), None)
            delays[start.isoformat(sep=" ")] = (
                None if first is None else (first - start).total_seconds() / 60
            )
        report["detectors"][method] = {
            "windows_detected": sum(delay is not None for delay in delays.values()),
            "labeled_windows": len(windows),
            "alerts_outside_windows": outside,
            "outside_window_alerts_per_elapsed_hour": outside / hours,
            "minutes_from_window_start": delays,
        }
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("windows", type=Path)
    args = parser.parse_args()
    print(json.dumps(evaluate(args.csv, args.windows), indent=2))
