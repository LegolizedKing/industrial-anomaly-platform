"""Local HTTP interface for the synthetic sensor baseline."""

import math
import os
from datetime import datetime
from pathlib import Path
from typing import Literal

import psycopg
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat

from alert_store import recent_alerts, save_alert
from anomaly_demo import simulate
from evaluate_detectors import METHODS, fit_reference, score_reading

app = FastAPI(title="Industrial Anomaly Detection")
training = list(simulate(0, 500, seed=17))
references = {method: fit_reference(training, method) for method in METHODS}


class Reading(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    second: int = Field(ge=0)
    temperature_c: FiniteFloat
    vibration_mm_s: FiniteFloat
    current_a: FiniteFloat
    method: Literal["z_score", "median_mad"] = "z_score"


class Result(BaseModel):
    second: int
    method: str
    sensor: str
    score: float
    alert: bool


class Alert(BaseModel):
    id: int
    recorded_at: datetime
    second: int
    method: str
    sensor: str
    score: float


@app.get("/alerts", response_model=list[Alert])
def alert_history(limit: int = Query(50, ge=1, le=200)):
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise HTTPException(status_code=503, detail="Alert storage is not configured")
    try:
        return recent_alerts(dsn, limit)
    except psycopg.Error as error:
        raise HTTPException(status_code=503, detail="Alert storage is unavailable") from error


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/score", response_model=Result)
def score_sensor_reading(reading: Reading):
    result = score_reading(reading.model_dump(), reading.method, references[reading.method])
    if not math.isfinite(result["score"]):
        raise HTTPException(status_code=422, detail="Reading exceeds the scoring range")
    dsn = os.getenv("DATABASE_URL")
    if dsn and result["alert"]:
        try:
            save_alert(dsn, result)
        except psycopg.Error as error:
            raise HTTPException(status_code=503, detail="Alert could not be saved") from error
    return result


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(Path(__file__).with_name("dashboard.html"), media_type="text/html")
