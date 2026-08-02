"""Fetch and render a 7-day weather forecast using Open-Meteo."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

DEFAULT_LOCATION_NAME = "Moraga, CA"
DEFAULT_LATITUDE = 37.83493
DEFAULT_LONGITUDE = -122.12969
DEFAULT_TIMEZONE = "America/Los_Angeles"
FORECAST_DAYS = 7
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


@dataclass(frozen=True)
class ForecastDay:
    date: str
    temperature_high_c: float
    temperature_low_c: float
    wind_speed_low_mph: float
    wind_speed_max_mph: float


def build_forecast_url(
    *,
    latitude: float,
    longitude: float,
    timezone: str = DEFAULT_TIMEZONE,
    forecast_days: int = FORECAST_DAYS,
) -> str:
    params = urlencode(
        {
            "latitude": latitude,
            "longitude": longitude,
            "daily": ",".join(
                [
                    "temperature_2m_max",
                    "temperature_2m_min",
                ]
            ),
            "hourly": "wind_speed_10m",
            "temperature_unit": "celsius",
            "wind_speed_unit": "mph",
            "timezone": timezone,
            "forecast_days": forecast_days,
        }
    )
    return f"{OPEN_METEO_FORECAST_URL}?{params}"


def fetch_forecast_payload(
    *,
    latitude: float,
    longitude: float,
    timezone: str = DEFAULT_TIMEZONE,
    forecast_days: int = FORECAST_DAYS,
) -> dict[str, Any]:
    url = build_forecast_url(
        latitude=latitude,
        longitude=longitude,
        timezone=timezone,
        forecast_days=forecast_days,
    )
    try:
        with urlopen(url, timeout=30) as response:
            return json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"Weather API returned HTTP {exc.code} for {url}") from exc
    except URLError as exc:
        raise RuntimeError(f"Failed to reach weather API at {url}: {exc.reason}") from exc


def build_daily_wind_extrema(payload: dict[str, Any]) -> dict[str, tuple[float, float]]:
    hourly = payload.get("hourly")
    if not isinstance(hourly, dict):
        raise ValueError("Forecast payload is missing an hourly section.")

    required_keys = ["time", "wind_speed_10m"]
    missing_keys = [key for key in required_keys if key not in hourly]
    if missing_keys:
        raise ValueError(f"Forecast payload is missing hourly keys: {', '.join(missing_keys)}")

    timestamps = hourly["time"]
    wind_speeds = hourly["wind_speed_10m"]
    if len(timestamps) != len(wind_speeds):
        raise ValueError("Forecast payload has inconsistent hourly series lengths.")

    daily_extrema: dict[str, tuple[float, float]] = {}
    for timestamp, wind_speed in zip(timestamps, wind_speeds, strict=True):
        date = str(timestamp).split("T", 1)[0]
        speed_value = float(wind_speed)
        existing = daily_extrema.get(date)
        if existing is None:
            daily_extrema[date] = (speed_value, speed_value)
            continue

        min_speed, max_speed = existing
        daily_extrema[date] = (min(min_speed, speed_value), max(max_speed, speed_value))

    return daily_extrema


def build_forecast_days(payload: dict[str, Any]) -> list[ForecastDay]:
    daily = payload.get("daily")
    if not isinstance(daily, dict):
        raise ValueError("Forecast payload is missing a daily section.")

    required_keys = [
        "time",
        "temperature_2m_max",
        "temperature_2m_min",
    ]
    missing_keys = [key for key in required_keys if key not in daily]
    if missing_keys:
        raise ValueError(f"Forecast payload is missing daily keys: {', '.join(missing_keys)}")

    dates = daily["time"]
    temp_highs = daily["temperature_2m_max"]
    temp_lows = daily["temperature_2m_min"]

    series_lengths = {
        len(dates),
        len(temp_highs),
        len(temp_lows),
    }
    if len(series_lengths) != 1:
        raise ValueError("Forecast payload has inconsistent daily series lengths.")

    wind_extrema_by_day = build_daily_wind_extrema(payload)
    forecast_days: list[ForecastDay] = []
    for date, temp_high, temp_low in zip(
        dates,
        temp_highs,
        temp_lows,
        strict=True,
    ):
        wind_extrema = wind_extrema_by_day.get(str(date))
        if wind_extrema is None:
            raise ValueError(f"Forecast payload is missing hourly wind data for {date}.")

        forecast_days.append(
            ForecastDay(
                date=str(date),
                temperature_high_c=float(temp_high),
                temperature_low_c=float(temp_low),
                wind_speed_low_mph=wind_extrema[0],
                wind_speed_max_mph=wind_extrema[1],
            )
        )

    return forecast_days


def render_forecast_markdown(location_name: str, forecast_days: list[ForecastDay]) -> str:
    forecast_length = len(forecast_days)
    lines = [
        f"# {forecast_length}-day weather forecast for {location_name}",
        "",
        "| Date | Temperature (C) | Max Wind (mph) |",
        "| --- | --- | --- |",
    ]
    for day in forecast_days:
        lines.append(
            "| "
            f"{day.date} | "
            f"High {day.temperature_high_c:.1f}, Low {day.temperature_low_c:.1f} | "
            f"{day.wind_speed_max_mph:.1f} |"
        )
    lines.append("")
    lines.append(
        "_Source: Open-Meteo daily forecast (`temperature_2m_max`, `temperature_2m_min`) "
        "with hourly wind aggregation from `wind_speed_10m`._"
    )
    return "\n".join(lines) + "\n"


def write_output(markdown: str, output_path: Path | None) -> None:
    if output_path is None:
        print(markdown, end="")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    print(output_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch a 7-day weather forecast.")
    parser.add_argument(
        "--location-name",
        default=DEFAULT_LOCATION_NAME,
        help="Display name used in the rendered markdown.",
    )
    parser.add_argument("--latitude", type=float, default=DEFAULT_LATITUDE)
    parser.add_argument("--longitude", type=float, default=DEFAULT_LONGITUDE)
    parser.add_argument("--timezone", default=DEFAULT_TIMEZONE)
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional markdown output path. Defaults to stdout.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = fetch_forecast_payload(
        latitude=args.latitude,
        longitude=args.longitude,
        timezone=args.timezone,
    )
    forecast_days = build_forecast_days(payload)
    markdown = render_forecast_markdown(args.location_name, forecast_days)
    write_output(markdown, args.output)


if __name__ == "__main__":
    main()
