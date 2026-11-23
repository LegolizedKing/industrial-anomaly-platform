"""Local HTTP interface for the synthetic sensor baseline."""

import math
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat

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


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/score", response_model=Result)
def score_sensor_reading(reading: Reading):
    result = score_reading(reading.model_dump(), reading.method, references[reading.method])
    if not math.isfinite(result["score"]):
        raise HTTPException(status_code=422, detail="Reading exceeds the scoring range")
    return result
