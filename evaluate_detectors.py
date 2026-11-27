"""Compare two fixed-reference detectors on later sensor readings."""

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import mean, median, stdev

from anomaly_demo import SENSORS, simulate
from sensor_csv import read_sensor_csv

THRESHOLD = 3.5
METHODS = ("z_score", "median_mad")


def score(training, readings, method, *, sensors=SENSORS):
    if len(training) < 2:
        raise ValueError("at least two training readings are required")
    if training[-1]["second"] >= readings[0]["second"]:
        raise ValueError("training must end before the first evaluation reading")

    reference = fit_reference(training, method, sensors=sensors)
    for row in readings:
        yield score_reading(row, method, reference)


def fit_reference(training, method, *, sensors=SENSORS):
    reference = {}
    for sensor in sensors:
        values = [row[sensor] for row in training]
        if method == "z_score":
            center, spread = mean(values), stdev(values)
        else:
            center = median(values)
            spread = 1.4826 * median(abs(value - center) for value in values)
        if not math.isfinite(spread) or spread <= 0:
            raise ValueError(f"{method}: {sensor} needs a positive finite training spread")
        reference[sensor] = center, spread
    return reference


def score_reading(row, method, reference):
    deviations = {
        sensor: abs(row[sensor] - center) / spread
        for sensor, (center, spread) in reference.items()
    }
    driver = max(deviations, key=deviations.__getitem__)
    magnitude = deviations[driver]
    return {
        "second": row["second"], "method": method, "sensor": driver,
        "score": magnitude, "alert": magnitude >= THRESHOLD,
    }


def compare(training, readings):
    return [result for method in METHODS for result in score(training, readings, method)]


def demo_metrics(results, readings):
    faults = {row["second"] for row in readings if row["fault"]}
    metrics = {}
    for method in METHODS:
        alerts = {row["second"] for row in results if row["method"] == method and row["alert"]}
        true_alerts = alerts & faults
        delays = {}
        for start, stop in ((580, 600), (700, 725)):
            first = min((second for second in true_alerts if start <= second < stop), default=None)
            delays[str(start)] = None if first is None else first - start
        metrics[method] = {
            "precision": len(true_alerts) / len(alerts) if alerts else None,
            "recall": len(true_alerts) / len(faults),
            "false_alerts_per_hour": len(alerts - faults) * 3600 / len(readings),
            "fault_detection_delay_seconds": delays,
        }
    return metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--training", type=Path, help="CSV from a known-normal period")
    parser.add_argument("--evaluation", type=Path, help="CSV from a later period")
    parser.add_argument("--output", type=Path, required=True, help="Destination for scored rows")
    args = parser.parse_args()
    if (args.training is None) != (args.evaluation is None):
        parser.error("provide both input files or neither for the synthetic demo")
    if args.output.resolve() in {path.resolve() for path in (args.training, args.evaluation) if path}:
        parser.error("output must differ from both input files")

    try:
        if args.training is None:
            training = list(simulate(0, 500, seed=17))
            readings = list(simulate(500, 300, seed=29, inject_faults=True))
        else:
            training = read_sensor_csv(args.training)
            readings = read_sensor_csv(args.evaluation)
        results = compare(training, readings)
        with args.output.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(results[0]))
            writer.writeheader()
            writer.writerows(results)
    except (ValueError, OSError, csv.Error) as error:
        parser.exit(2, f"{error}\n")
    if args.training is None:
        print(json.dumps(demo_metrics(results, readings), indent=2))
    else:
        print(f"Wrote {len(results)} scores to {args.output}")


if __name__ == "__main__":
    main()
