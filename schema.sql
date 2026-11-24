CREATE TABLE IF NOT EXISTS anomaly_alerts (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    recorded_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    second numeric NOT NULL CHECK (second >= 0),
    method text NOT NULL,
    sensor text NOT NULL,
    score double precision NOT NULL
);
