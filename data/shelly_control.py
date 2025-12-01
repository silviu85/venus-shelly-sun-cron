#!/usr/bin/env python3
import os
import sys
import requests
from datetime import datetime, timedelta
from suntime import Sun, SunTimeException
from dotenv import load_dotenv

load_dotenv()

def require_env(varname: str) -> str:
    value = os.getenv(varname)
    if value is None or value.strip() == "":
        print(f"ERROR: Environment variable {varname} is missing in .env")
        sys.exit(1)
    return value

# Required configuration
SHELLY_IP     = require_env("SHELLY_IP")
RELAY_ID      = int(require_env("RELAY_ID"))
LAT           = float(require_env("LAT"))
LON           = float(require_env("LON"))
CRON_FILE     = require_env("CRON_FILE")
SHELLY_SCRIPT = require_env("SHELLY_SCRIPT")

# Time conversion mode: 'local' or 'offset'
TIME_MODE = require_env("TIME_MODE").lower()  # 'local' or 'offset'
if TIME_MODE not in ("local", "offset"):
    print("ERROR: TIME_MODE must be 'local' or 'offset'")
    sys.exit(1)

# If using offset mode, require TZ_OFFSET (hours)
TZ_OFFSET = None
if TIME_MODE == "offset":
    TZ_OFFSET = float(require_env("TZ_OFFSET"))

def shelly_switch(state: str):
    url = f"http://{SHELLY_IP}/relay/{RELAY_ID}?turn={state}"
    try:
        r = requests.get(url, timeout=5)
        print(f"[{datetime.now()}] Shelly {state.upper()} → {r.status_code}")
    except Exception as e:
        print(f"ERROR: Shelly command failed: {e}")
        sys.exit(1)

def convert_time(dt_utc: datetime) -> datetime:
    # suntime returns aware UTC datetimes
    if TIME_MODE == "local":
        return dt_utc.astimezone()  # uses OS timezone (you set Europe/Bucharest)
    else:
        return dt_utc + timedelta(hours=TZ_OFFSET)

def schedule_jobs():
    sun = Sun(LAT, LON)
    now = datetime.now()

    try:
        sunrise_utc = sun.get_sunrise_time(now)
        sunset_utc  = sun.get_sunset_time(now)
    except SunTimeException as e:
        print(f"ERROR: Sun times calculation failed: {e}")
        sys.exit(1)

    sunrise = convert_time(sunrise_utc)
    sunset  = convert_time(sunset_utc)

    # Read existing crontab for root (per-user crontab does NOT include the 'root' field)
    try:
        with open(CRON_FILE, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = []

    # Remove previous Shelly jobs (both on/off) based on script path
    filtered = [l for l in lines if SHELLY_SCRIPT not in l]

    # Add new jobs (minute hour day-of-month month day-of-week command)
    off_line = f"{sunrise.minute} {sunrise.hour} * * * python3 {SHELLY_SCRIPT} off\n"
    on_line  = f"{sunset.minute} {sunset.hour} * * * python3 {SHELLY_SCRIPT} on\n"
    filtered.append(off_line)
    filtered.append(on_line)

    # Write back
    try:
        with open(CRON_FILE, "w") as f:
            f.writelines(filtered)
    except Exception as e:
        print(f"ERROR: Writing cron file failed: {e}")
        sys.exit(1)

    print(f"Updated cron: OFF at {sunrise}, ON at {sunset}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        shelly_switch(sys.argv[1])
    else:
        schedule_jobs()
