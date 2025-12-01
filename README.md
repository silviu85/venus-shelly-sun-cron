# Outdoor Light Automation with Shelly & Venus OS

## Description

This Python script controls a Shelly relay to **turn outdoor lights on
and off** based on the **sunrise and sunset** of each day.\
It is designed to run on **Venus OS**, where cron jobs are managed
through the `root` file inside `/var/spool/cron/`.

------------------------------------------------------------------------

## Requirements

-   **Python 3** installed on Venus OS\
-   Python packages:
    -   `requests` (for HTTP communication with Shelly)
    -   `suntime` (for calculating sunrise and sunset times)
    -   `python-dotenv` (for reading variables from `.env`)
-   Access to a Shelly relay on the network (static IP or DHCP
    reservation)
-   Cron active on Venus OS (`crond` must be running)

------------------------------------------------------------------------

## Required Files

-   `/data/shelly_control.py` → the main script\
-   `/data/.env` → configuration file with required variables

Example `.env`:

``` env
SHELLY_IP=192.168.1.50
RELAY_ID=0
LAT=44.42
LON=26.10
CRON_FILE=/var/spool/cron/root
SHELLY_SCRIPT=/data/shelly_control.py
TIME_MODE=local
```

------------------------------------------------------------------------

## How to Run

1.  **Copy the script to Venus OS** (e.g. `/data/shelly_control.py`).
2.  **Create the `.env` file** in the same directory as the script.
3.  **Run the script manually to generate the cron jobs:**

``` bash
python3 /data/shelly_control.py
```

4.  **Check the cron file:**

``` bash
cat /var/spool/cron/root
```

Must set up the script in crontab at an hour before the sun is rising. i set it up at 00:05 to be run daily.
After the script is run, you will see that it add two more jobs in crontab. at the time of sunrise and sunset.
**Cron** will automatically execute these commands daily.

------------------------------------------------------------------------

## Why the Script Works This Way

### 1. Root crontab in `/var/spool/cron/root`

On Venus OS, the `/etc` directory is **read-only**, so `/etc/cron.d/`
cannot be used.

`crond` reads jobs from `/var/spool/cron/root`, which is **writeable**
and **persistent**.

The script writes directly to this file to ensure: - correct execution\
- persistence of cron jobs across reboots\
- safety: it does not remove existing cron jobs that are unrelated to
the Python script

------------------------------------------------------------------------

### 2. Strict Configuration via `.env`

There are no hardcoded values in the script.

Everything is defined in `.env`: - Shelly IP\
- Relay ID\
- Geographic coordinates\
- Cron file path\
- Script path

If any variable is missing, the script **stops immediately** with an
error message → *fail loudly*, with no fallback defaults.

------------------------------------------------------------------------

### 3. Main Purpose

To automate outdoor lighting based on **sunrise** and **sunset**.

Benefits: - lights only turn on in the evening - they turn off in the
morning - energy savings - no need for fixed schedules

------------------------------------------------------------------------

## Advantages

-   Daily automation adjusted to seasonal sunlight changes\
-   Clear and easy configuration using `.env`\
-   100% compatible with Venus OS\
-   Safe script design: no default values used

------------------------------------------------------------------------

## 🔍 Testing

To verify:

1.  Run the script → cron jobs are generated.
2.  Run manually:

``` bash
python3 /data/shelly_control.py on
python3 /data/shelly_control.py off
```

3.  Check cron logs:

``` bash
tail -f /var/log/syslog | grep CRON
```

------------------------------------------------------------------------

## License

Script created for personal use and adapted for Venus OS.\
It can be freely modified and reused for similar systems.
