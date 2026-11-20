"""Run a reproducible industrial sensor anomaly-detection baseline."""

import csv
import json
import random
from pathlib import Path
from statistics import mean, stdev

SENSORS = ("temperature_c", "vibration_mm_s", "current_a")


def simulate(start, count, seed, inject_faults=False):
    rng = random.Random(seed)
    for index in range(count):
        fault = inject_faults and (80 <= index < 100 or 200 <= index < 225)
        yield {
            "second": start + index,
            "temperature_c": rng.gauss(65, 1.5) + (7 if fault and index < 100 else 0),
            "vibration_mm_s": rng.gauss(2, 0.25) + (1.3 if fault and index >= 200 else 0),
            "current_a": rng.gauss(120, 3),
            "fault": fault,
        }


def evaluate(output):
    training = list(simulate(0, 500, seed=17))
    reference = {}
    for sensor in SENSORS:
        values = [row[sensor] for row in training]
        reference[sensor] = mean(values), stdev(values)

    scored = []
    for row in simulate(500, 300, seed=29, inject_faults=True):
        deviations = {
            sensor: (row[sensor] - center) / spread
            for sensor, (center, spread) in reference.items()
        }
        driver = max(deviations, key=lambda sensor: abs(deviations[sensor]))
        score = abs(deviations[driver])
        scored.append({**row, "score": score, "driver": driver, "alert": score >= 3.5})

    tp = sum(row["alert"] and row["fault"] for row in scored)
    fp = sum(row["alert"] and not row["fault"] for row in scored)
    fn = sum(not row["alert"] and row["fault"] for row in scored)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(scored[0]))
        writer.writeheader()
        writer.writerows(scored)
    return {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": tp / (tp + fp) if tp + fp else 0,
        "recall": tp / (tp + fn) if tp + fn else 0,
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(Path("scored_readings.csv")), indent=2))
