"""Validate a single chronological stream of industrial sensor readings."""

import argparse
import csv
import math
from pathlib import Path

from anomaly_demo import SENSORS

REQUIRED_COLUMNS = {"second", *SENSORS}


def read_sensor_csv(path):
    """Read finite sensor values at strictly increasing nonnegative seconds."""
    readings = []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        headers = reader.fieldnames or []
        missing = REQUIRED_COLUMNS.difference(headers)
        if missing:
            raise ValueError(f"missing columns: {', '.join(sorted(missing))}")
        if len(set(headers)) != len(headers):
            raise ValueError("duplicate column names")
        for row in reader:
            try:
                if None in row or any(value is None for value in row.values()):
                    raise ValueError("row length differs from the header")
                second = int(row["second"])
                if second < 0 or (readings and second <= readings[-1]["second"]):
                    raise ValueError("second must be nonnegative and strictly increasing")
                values = {sensor: float(row[sensor]) for sensor in SENSORS}
                if not all(math.isfinite(value) for value in values.values()):
                    raise ValueError("sensor values must be finite")
            except ValueError as error:
                raise ValueError(f"line {reader.line_num}: {error}") from error
            readings.append({"second": second, **values})
    if not readings:
        raise ValueError("no sensor readings found")
    return readings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="UTF-8 sensor CSV")
    args = parser.parse_args()
    try:
        readings = read_sensor_csv(args.input)
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(2, f"{args.input}: {error}\n")
    print(f"Validated {len(readings)} readings from second "
          f"{readings[0]['second']} to {readings[-1]['second']}.")


if __name__ == "__main__":
    main()
