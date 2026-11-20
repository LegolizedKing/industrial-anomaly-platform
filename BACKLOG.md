# Project backlog

- [x] Reproducible synthetic sensor baseline.
- [x] CSV ingestion and validation for a single sensor stream.
- [ ] Score imported readings and compare detectors on chronological splits. Track false alerts per hour and time to detection. Document the provenance and limitations of any real benchmark.
- [ ] Serve scoring and alert history through FastAPI and PostgreSQL.
- [ ] Build an operator dashboard, containerize the application, and publish a reproducible demo.

## Try CSV ingestion

```sh
python anomaly_demo.py
python sensor_csv.py scored_readings.csv
```

The first command generates synthetic data with seeded Gaussian noise and injected temperature and vibration fault windows. The second validates the 300 generated rows. For your own UTF-8 CSV, supply `second,temperature_c,vibration_mm_s,current_a`. Seconds are nonnegative integers in strictly increasing order. Sensor values must be finite. Extra columns are allowed and ignored, including simulator labels. This validator expects one stream and allows gaps between timestamps.
