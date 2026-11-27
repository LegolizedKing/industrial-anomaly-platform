FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY api.py alert_store.py anomaly_demo.py evaluate_detectors.py sensor_csv.py dashboard.html ./
USER 65534:65534
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0"]
