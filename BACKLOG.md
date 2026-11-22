# Project backlog

- [x] Reproducible synthetic sensor baseline.
- [x] CSV ingestion and validation for a single sensor stream.
- [x] Score imported readings and compare two detectors on chronological splits. Report false alerts per hour and detection delay for the labeled synthetic demo.
- [x] Evaluate on a measured benchmark and document provenance, coverage, and limitations.
- [ ] Serve scoring and alert history through FastAPI and PostgreSQL.
- [ ] Build an operator dashboard, containerize the application, and publish a reproducible demo.

## Try CSV ingestion

```sh
python anomaly_demo.py
python sensor_csv.py scored_readings.csv
```

The first command generates synthetic data with seeded Gaussian noise and injected temperature and vibration fault windows. The second validates the 300 generated rows. For your own UTF-8 CSV, supply `second,temperature_c,vibration_mm_s,current_a`. Seconds are nonnegative integers in strictly increasing order. Sensor values must be finite. Extra columns are allowed and ignored, including simulator labels. This validator expects one stream and allows gaps between timestamps.

## Compare detectors

```sh
python evaluate_detectors.py --output comparison.csv
python evaluate_detectors.py --training normal.csv --evaluation later.csv --output comparison.csv
```

Both detectors use the largest absolute standardized sensor deviation and a fixed threshold of 3.5. One fits the mean and sample standard deviation. The other uses the median and scaled median absolute deviation to reduce sensitivity to extreme training values. The evaluation CSV must start after training ends. External files produce scores and alert flags.

The synthetic demo uses 500 normal training rows and 300 evaluation rows at one row per second. Fault labels contribute only to metrics. False alerts per hour counts flagged normal rows divided by total observed hours. Delay is the time from the start of a fault window to its first alert, or null if missed. Two injected fault windows and independent Gaussian noise give limited evidence about field performance. The threshold has not been calibrated on operational data.

## Measured benchmark

Use the Numenta Anomaly Benchmark office ambient temperature series and its combined anomaly windows. Fetch these files from [NAB](https://github.com/numenta/NAB), which publishes an [MIT license](https://github.com/numenta/NAB/blob/master/LICENSE.txt). This project does not redistribute the readings or labels.

| NAB path | Git blob ID used |
| --- | --- |
| `data/realKnownCause/ambient_temperature_system_failure.csv` | `d9d6bb2d20221e5161e1655dbf120e67f949051a` |
| `labels/combined_windows.json` | `2f1be355750a2fefa8d781215d3275fda3d83d23` |

Run `python evaluate_nab.py ambient_temperature_system_failure.csv combined_windows.json`. The first 726 chronological rows fit the detectors. The following 6,541 rows are scored without tuning the existing 3.5 threshold. Both detect two of two labeled windows. Mean/standard deviation flags 14 readings outside the windows and median/MAD flags 15. The first alerts occur 9,420 and 20,640 minutes after their respective window starts for both methods.

These broad benchmark windows differ from exact fault onset. Outside-window alerts are flagged readings rather than distinct incidents, and the hourly rate uses elapsed time including gaps. This is a custom evaluation on one office sensor and two windows. It does not measure factory performance or use official NAB scoring.
