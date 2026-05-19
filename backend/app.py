import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
from datetime import datetime, timedelta, timezone

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

API_KEY = os.environ.get("HC_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "HC_API_KEY environment variable is not set. "
        "Create backend/.env with HC_API_KEY=<your healthchecks api key> "
        "or export it in your shell."
    )

ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def format_relative(delta_seconds: int) -> str:
    """Format a signed seconds delta as 'in 1h 5m' / '2m ago' / 'overdue 3m'."""
    if delta_seconds == 0:
        return "now"

    overdue = delta_seconds < 0
    secs = abs(delta_seconds)

    days = secs // 86400
    hours = (secs % 86400) // 3600
    minutes = (secs % 3600) // 60

    if days > 0:
        body = f"{days}d {hours}h"
    elif hours > 0:
        body = f"{hours}h {minutes}m"
    else:
        body = f"{max(minutes, 1)}m"

    if overdue:
        return f"overdue {body}"
    return f"in {body}"


def format_age(delta_seconds: int) -> str:
    """Format an elapsed positive seconds delta as '2m ago' / '1h 5m ago'."""
    if delta_seconds < 60:
        return "just now"

    days = delta_seconds // 86400
    hours = (delta_seconds % 86400) // 3600
    minutes = (delta_seconds % 3600) // 60

    if days > 0:
        return f"{days}d {hours}h ago"
    if hours > 0:
        return f"{hours}h {minutes}m ago"
    return f"{minutes}m ago"


def format_period(seconds: int) -> str:
    """Format a period like 3600 -> 'every 1h'."""
    if seconds <= 0:
        return ""
    if seconds % 86400 == 0:
        return f"every {seconds // 86400}d"
    if seconds % 3600 == 0:
        return f"every {seconds // 3600}h"
    if seconds % 60 == 0:
        return f"every {seconds // 60}m"
    return f"every {seconds}s"


def format_grace(seconds: int) -> str:
    if seconds <= 0:
        return ""

    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60

    if days > 0:
        if hours > 0:
            return f"{days}d {hours}h grace"
        return f"{days}d grace"
    if hours > 0:
        if minutes > 0:
            return f"{hours}h {minutes}m grace"
        return f"{hours}h grace"
    if minutes > 0:
        return f"{minutes}m grace"
    return f"{seconds}s grace"


@app.get("/")
def root():
    return {"status": "running"}


@app.get("/checks")
def get_checks():

    try:
        res = requests.get(
            "https://healthchecks.io/api/v3/checks/",
            headers={"X-Api-Key": API_KEY},
            timeout=10,
        )

        data = res.json()
        now = datetime.now(timezone.utc)

        for check in data.get("checks", []):

            # -----------------------------------
            # PARSE TIMESTAMPS
            # -----------------------------------
            last_ping = check.get("last_ping")
            next_ping = check.get("next_ping")

            last_ping_dt = None
            if last_ping:
                last_ping_dt = datetime.fromisoformat(
                    last_ping.replace("Z", "+00:00")
                )

            next_ping_dt = None
            if next_ping:
                next_ping_dt = datetime.fromisoformat(
                    next_ping.replace("Z", "+00:00")
                )

            # -----------------------------------
            # LAST RUN AGE
            # -----------------------------------
            if last_ping_dt:
                age_secs = int((now - last_ping_dt).total_seconds())
                check["last_run_age"] = format_age(age_secs)
            else:
                check["last_run_age"] = "Never"

            # -----------------------------------
            # NEXT EXPECTED
            # -----------------------------------
            period = check.get("timeout") or 0   # seconds, simple checks
            grace = check.get("grace") or 0

            # Prefer healthchecks' own next_ping; fall back to last_ping + period
            if next_ping_dt is None and last_ping_dt and period:
                next_ping_dt = last_ping_dt + timedelta(seconds=period)

            if next_ping_dt:
                delta = int((next_ping_dt - now).total_seconds())
                check["next_expected"] = next_ping_dt.isoformat()
                check["next_expected_relative"] = format_relative(delta)

                # Grace deadline: when it flips from DELAYED to DEAD
                grace_deadline = next_ping_dt + timedelta(seconds=grace)
                check["grace_deadline"] = grace_deadline.isoformat()
            else:
                check["next_expected"] = None
                check["next_expected_relative"] = "—"
                check["grace_deadline"] = None

            # -----------------------------------
            # RUNTIME STATUS
            # -----------------------------------
            hc_status = check.get("status", "unknown")
            check["runtime_status"] = {
                "up": "HEALTHY",
                "grace": "DELAYED",
                "down": "DEAD",
                "paused": "PAUSED",
                "new": "NEW",
            }.get(hc_status, "UNKNOWN")

            # -----------------------------------
            # FORMATTED PERIOD / GRACE
            # -----------------------------------
            schedule = check.get("schedule")
            if schedule and schedule != "* * * * *":
                check["period_label"] = schedule
            elif period:
                check["period_label"] = format_period(period)
            else:
                check["period_label"] = ""

            check["grace_label"] = format_grace(grace)

            # -----------------------------------
            # MISC
            # -----------------------------------
            check["total_runs"] = check.get("n_pings", 0)

        return data

    except Exception as e:
        return {"error": str(e)}
