#!/usr/bin/env python3
"""Show configured Romanian briefing times in Bucharest and Kuala Lumpur; no network."""
import argparse
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

TIMES = ((8, "早间简报"), (13, "盘中简报"), (18, "收盘时点简报"))


def schedule_for(day):
    bucharest = ZoneInfo("Europe/Bucharest")
    malaysia = ZoneInfo("Asia/Kuala_Lumpur")
    result = []
    for hour, title in TIMES:
        ro = datetime.combine(day, time(hour, 0), tzinfo=bucharest)
        my = ro.astimezone(malaysia)
        result.append((title, ro, my))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=str(date.today()), help="Romanian calendar date YYYY-MM-DD")
    args = parser.parse_args()
    day = date.fromisoformat(args.date)
    for label, ro, my in schedule_for(day):
        print(f"{label}: Romania {ro.isoformat()} | Malaysia {my.isoformat()}")


if __name__ == "__main__":
    main()
