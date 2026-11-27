"""PostgreSQL persistence for flagged sensor readings."""

import psycopg
from psycopg.rows import dict_row


def save_alert(dsn, result):
    with psycopg.connect(dsn, connect_timeout=3) as connection:
        connection.execute(
            """INSERT INTO anomaly_alerts (second, method, sensor, score)
               VALUES (%(second)s, %(method)s, %(sensor)s, %(score)s)""",
            result,
        )


def recent_alerts(dsn, limit):
    with psycopg.connect(dsn, connect_timeout=3, row_factory=dict_row) as connection:
        return connection.execute(
            """SELECT id, recorded_at, second, method, sensor, score
               FROM anomaly_alerts ORDER BY id DESC LIMIT %s""",
            (limit,),
        ).fetchall()
