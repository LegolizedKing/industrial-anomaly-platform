# Industrial Anomaly Detection Platform

A portfolio project for detecting unusual industrial sensor readings and showing which sensor drives each alert. The initial demo uses reproducible simulated data.

## Run the baseline

Run `python anomaly_demo.py` with Python 3. The script reports precision, recall and error counts and writes `scored_readings.csv`.

The detector fits a mean and standard deviation to 500 normal readings per sensor. On 300 later readings, it alerts when any sensor deviates by at least 3.5 standard deviations. Injected fault labels are used only for evaluation. Results describe the simulation and need validation on measured data.

## Roadmap

1. Add CSV validation and compare detectors on chronological splits using false alerts per hour and time to detection.
2. Add a FastAPI service and PostgreSQL alert history.
3. Add an operator dashboard and package the demo with Docker and automated checks.
