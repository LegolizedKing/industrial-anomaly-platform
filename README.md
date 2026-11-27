# Industrial Anomaly Detection Platform

Score industrial sensor readings, identify the sensor driving each alert, and review saved alerts in an operator dashboard.

## Local demo

From the development branch, run:

```sh
docker compose up --build -d
python demo.py
```

Open [the dashboard](http://127.0.0.1:8000/) and submit the prefilled temperature spike. The API returns the score, alert flag and largest contributing sensor. PostgreSQL keeps flagged readings across normal Compose shutdowns. The demo script submits its own simulated temperature spike and verifies that it appears in history. Run `docker compose down` to stop both services.

The Compose configuration uses demo credentials, publishes only the dashboard and API on localhost, and initializes the schema on a fresh database volume. These settings are intended for a local portfolio demo.

## Evaluation and data

Run `python evaluate_detectors.py --output comparison.csv` for the reproducible synthetic comparison. Both detectors fit on 500 seeded normal readings and score 300 later readings with two injected fault windows. The threshold is fixed at 3.5. The mean-based detector flagged 39 of 45 anomalous readings, and the median-based detector flagged 38. Neither flagged a normal reading in this simulation.

The [project backlog](BACKLOG.md) includes CSV ingestion, the separate measured office-temperature benchmark, data provenance, and setup without Docker. The API uses synthetic reference data. Field performance on factory machinery remains unverified.
