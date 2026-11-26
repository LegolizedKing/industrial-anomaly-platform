"""Submit a simulated spike and verify it appears in alert history."""

import argparse
import json
import time
from urllib.request import Request, urlopen


def verify(base_url):
    reading = dict(
        second=time.time_ns() // 1_000_000 % 1_000_000_000, temperature_c=85, vibration_mm_s=2, current_a=120
    )
    request = Request(
        f"{base_url}/score",
        json.dumps(reading).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=10) as response:
        result = json.load(response)
    if not result["alert"] or result["sensor"] != "temperature_c":
        raise RuntimeError(f"Expected a temperature alert, received {result}")
    with urlopen(f"{base_url}/alerts?limit=25", timeout=10) as response:
        history = json.load(response)
    if not any(row["second"] == reading["second"] for row in history):
        raise RuntimeError("The submitted alert was missing from recent history")
    print(f"Temperature alert saved. Score: {result['score']:.2f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    verify(args.url.rstrip("/"))
