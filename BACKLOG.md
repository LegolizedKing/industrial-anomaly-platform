# Project backlog

- [x] Reproducible synthetic sensor baseline.
- [x] CSV ingestion and validation for a single sensor stream.
- [x] Score imported readings and compare two detectors on chronological splits. Report false alerts per hour and detection delay for the labeled synthetic demo.
- [x] Evaluate on a measured benchmark and document provenance, coverage, and limitations.
- [x] Serve individual sensor scores through FastAPI.
- [x] Persist alerts and expose history through PostgreSQL.
- [x] Build an operator dashboard for scoring and recent alerts.
- [ ] Containerize the application and publish a reproducible demo.

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

## Run the scoring API

```sh
python -m pip install -r requirements.txt
python -m uvicorn api:app
```

Open http://127.0.0.1:8000/docs and try POST /score with:

```json
{"second": 500, "temperature_c": 85, "vibration_mm_s": 2, "current_a": 120}
```

The service fits both detector references once per process from 500 synthetic normal readings (seed 17). Each request is scored independently. The optional method field accepts z_score or median_mad. The supplied second is returned for correlation. The response identifies the sensor with the largest absolute standardized deviation. Calibration for measured factory streams is pending.

## Enable PostgreSQL alert history

Install the API dependencies as above. Set `DATABASE_URL` to a PostgreSQL connection URI and apply the schema before starting the API.

```sh
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f schema.sql
python -m uvicorn api:app
```

Submit a temperature spike using the example above, then call `GET /alerts?limit=10`. Each flagged submission creates an alert record. Repeating a submission can create another record. The endpoint returns the latest inserted records first. Its default limit is 50 and its maximum is 200. Normal readings are scored without being stored. Without a configured database, scoring works on its own and history returns HTTP 503. With a configured but unavailable database, a flagged submission returns HTTP 503 if its alert cannot be saved.

## Open the operator dashboard

Start the API as above and visit http://127.0.0.1:8000/. The form starts with a synthetic temperature spike. Submit it to see the score and sensor with the largest deviation. With PostgreSQL configured, the dashboard displays the latest 25 saved alerts. History can be refreshed independently.
