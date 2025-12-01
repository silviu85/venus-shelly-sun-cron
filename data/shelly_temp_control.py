#!/usr/bin/env python3
import os, sys, requests
from datetime import datetime, timedelta
from suntime import Sun, SunTimeException
from dotenv import load_dotenv

load_dotenv()

def require_env(varname: str) -> str:
    value = os.getenv(varname)
    if not value:
        print(f"ERROR: Missing {varname} in .env")
        sys.exit(1)
    return value

# Config din .env
LAT = float(require_env("LAT"))
LON = float(require_env("LON"))
CRON_FILE = require_env("CRON_FILE")

SHELLY_IP_TEMP = require_env("SHELLY_IP_TEMP")
RELAY_ID_TEMP = int(require_env("RELAY_ID_TEMP"))
SCRIPT_PATH = require_env("TEMP_SCRIPT")  # ex. /data/shelly_temp_control.py

def read_temps(ip: str):
    url = f"http://{ip}/status"
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        temps = []
        if "ext_temperature" in data:
            for k, v in data["ext_temperature"].items():
                temps.append(float(v["tC"]))
        return temps
    except Exception as e:
        print(f"Error reading sensors: {e}")
        return []

def shelly_switch(ip: str, relay: int, state: str):
    url = f"http://{ip}/relay/{relay}?turn={state}"
    try:
        r = requests.get(url, timeout=5)
        print(f"[{datetime.now()}] Shelly {ip} {state.upper()} → {r.status_code}")
    except Exception as e:
        print(f"Error sending command: {e}")

def schedule_jobs():
    sun = Sun(LAT, LON)
    now = datetime.now()

    try:
        sunrise = sun.get_sunrise_time(now).astimezone()
        trigger_time = sunrise - timedelta(minutes=30)

        try:
            with open(CRON_FILE, "r") as f:
                lines = f.readlines()
        except FileNotFoundError:
            lines = []

        # delete old jobs for the temperature script
        new_lines = [l for l in lines if SCRIPT_PATH not in l]

        # add the new job
        new_lines.append(f"{trigger_time.minute} {trigger_time.hour} * * * python3 {SCRIPT_PATH}\n")

        with open(CRON_FILE, "w") as f:
            f.writelines(new_lines)

        print(f"Updated cron: Temp check scheduled at {trigger_time}")

    except SunTimeException as e:
        print(f"Error calculating sun times: {e}")

def main():
    temps = read_temps(SHELLY_IP_TEMP)
    print(f"Temperatures: {temps}")

    if any(t < 5 for t in temps):
        shelly_switch(SHELLY_IP_TEMP, RELAY_ID_TEMP, "on")
    else:
        print("No need to switch ON (all temps >= 5°C)")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "schedule":
        schedule_jobs()
    else:
        main()