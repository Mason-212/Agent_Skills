"""Fetch and render daily weather forecasts from Open-Meteo."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

GEOCODING_API = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_API = "https://api.open-meteo.com/v1/forecast"
DEFAULT_DAYS = 7
MAX_FORECAST_DAYS = 16
KNOWN_LOCATIONS = {
    "moraga": {
        "name": "Moraga",
        "admin1": "California",
        "country": "United States",
        "latitude": 37.83493,
        "longitude": -122.12969,
        "timezone": "America/Los_Angeles",
    },
    "moraga, ca": {
        "name": "Moraga",
        "admin1": "California",
        "country": "United States",
        "latitude": 37.83493,
        "longitude": -122.12969,
        "timezone": "America/Los_Angeles",
    },
    "moraga, california": {
        "name": "Moraga",
        "admin1": "California",
        "country": "United States",
        "latitude": 37.83493,
        "longitude": -122.12969,
        "timezone": "America/Los_Angeles",
    },
}


class WeatherForecastError(RuntimeError):
    """Raised when the weather API cannot satisfy a request."""


@dataclass(frozen=True)
class Location:
    name: str
    admin1: str | None
    country: str | None
    latitude: float
    longitude: float
    timezone: str | None

    @property
    def display_name(self) -> str:
        parts = [self.name]
        if self.admin1:
            parts.append(self.admin1)
        if self.country:
            parts.append(self.country)
        return ", ".join(parts)


@dataclass(frozen=True)
class ForecastDay:
    date: str
    temp_max_c: float
    temp_min_c: float
    wind_speed_min_mph: float
    wind_speed_max_mph: float


def build_geocoding_url(query: str, *, count: int = 1) -> str:
    params = urlencode({"name": query, "count": count, "language": "en", "format": "json"})
    return f"{GEOCODING_API}?{params}"


def build_forecast_url(latitude: float, longitude: float, *, days: int) -> str:
    params = urlencode(
        {
            "latitude": latitude,
            "longitude": longitude,
            "forecast_days": days,
            "daily": ",".join(
                [
                    "temperature_2m_max",
                    "temperature_2m_min",
                ]
            ),
            "hourly": "wind_speed_10m",
            "temperature_unit": "celsius",
            "wind_speed_unit": "mph",
            "timezone": "auto",
        }
    )
    return f"{FORECAST_API}?{params}"


def fetch_json(url: str) -> dict[str, Any]:
    try:
        with urlopen(url, timeout=20) as response:
            return json.load(response)
    except HTTPError as exc:
        raise WeatherForecastError(f"HTTP error from weather service: {exc.code}") from exc
    except URLError as exc:
        raise WeatherForecastError(f"Unable to reach weather service: {exc.reason}") from exc
    except TimeoutError as exc:
        raise WeatherForecastError("Timed out while contacting weather service.") from exc
    except json.JSONDecodeError as exc:
        raise WeatherForecastError("Weather service returned invalid JSON.") from exc


def resolve_location(query: str) -> Location:
    payload = fetch_json(build_geocoding_url(query))
    results = payload.get("results") or []
    if not results:
        fallback = KNOWN_LOCATIONS.get(query.strip().lower())
        if fallback is None:
            raise WeatherForecastError(f"No location match found for {query!r}.")
        return Location(**fallback)

    best = results[0]
    return Location(
        name=best["name"],
        admin1=best.get("admin1"),
        country=best.get("country"),
        latitude=float(best["latitude"]),
        longitude=float(best["longitude"]),
        timezone=best.get("timezone"),
    )


def build_daily_wind_extrema(payload: dict[str, Any]) -> dict[str, tuple[float, float]]:
    hourly = payload.get("hourly")
    if not isinstance(hourly, dict):
        raise WeatherForecastError("Forecast response did not include hourly wind data.")

    times = hourly.get("time") or []
    wind_speeds = hourly.get("wind_speed_10m") or []
    if len(times) != len(wind_speeds):
        raise WeatherForecastError("Forecast response had inconsistent hourly wind series lengths.")
    if not times:
        raise WeatherForecastError("Forecast response did not include hourly wind samples.")

    daily_extrema: dict[str, tuple[float, float]] = {}
    for timestamp, speed in zip(times, wind_speeds, strict=True):
        date = str(timestamp).split("T", 1)[0]
        speed_value = float(speed)
        existing = daily_extrema.get(date)
        if existing is None:
            daily_extrema[date] = (speed_value, speed_value)
            continue

        min_speed, max_speed = existing
        daily_extrema[date] = (min(min_speed, speed_value), max(max_speed, speed_value))

    return daily_extrema


def parse_daily_forecast(payload: dict[str, Any], *, days: int) -> list[ForecastDay]:
    daily = payload.get("daily")
    if not isinstance(daily, dict):
        raise WeatherForecastError("Forecast response did not include daily data.")

    times = daily.get("time") or []
    temp_max = daily.get("temperature_2m_max") or []
    temp_min = daily.get("temperature_2m_min") or []

    available_days = min(len(times), len(temp_max), len(temp_min))
    if available_days == 0:
        raise WeatherForecastError("Forecast response was missing one or more daily series.")

    wind_extrema_by_day = build_daily_wind_extrema(payload)
    series_days = min(days, available_days)
    forecast: list[ForecastDay] = []
    for index in range(series_days):
        date = str(times[index])
        wind_extrema = wind_extrema_by_day.get(date)
        if wind_extrema is None:
            raise WeatherForecastError(f"Forecast response was missing hourly wind data for {date}.")

        min_wind_speed, max_wind_speed = wind_extrema
        forecast.append(
            ForecastDay(
                date=date,
                temp_max_c=float(temp_max[index]),
                temp_min_c=float(temp_min[index]),
                wind_speed_min_mph=min_wind_speed,
                wind_speed_max_mph=max_wind_speed,
            )
        )
    return forecast


def fetch_forecast(query: str, *, days: int = DEFAULT_DAYS) -> tuple[Location, list[ForecastDay]]:
    location = resolve_location(query)
    payload = fetch_json(build_forecast_url(location.latitude, location.longitude, days=days))
    return location, parse_daily_forecast(payload, days=days)


def format_forecast_table(location: Location, forecast_days: list[ForecastDay]) -> str:
    forecast_length = len(forecast_days)
    lines = [
        f"{forecast_length}-day weather forecast for {location.display_name}",
        "",
        "| Date | Temperature (C) | Wind (mph) |",
        "| --- | --- | --- |",
    ]
    for day in forecast_days:
        wind_text = f"low {day.wind_speed_min_mph:.1f}, max {day.wind_speed_max_mph:.1f}"
        lines.append(
            f"| {day.date} | high {day.temp_max_c:.1f}, low {day.temp_min_c:.1f} | {wind_text} |"
        )
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch a daily weather forecast from Open-Meteo.")
    parser.add_argument("--location", default="Moraga, CA", help='Named place to resolve, e.g. "Moraga, CA".')
    parser.add_argument(
        "--days",
        type=int,
        default=DEFAULT_DAYS,
        help=f"Number of forecast days to print (1-{MAX_FORECAST_DAYS}).",
    )
    parser.add_argument("--json", action="store_true", help="Print the resolved location and forecast as JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not 1 <= args.days <= MAX_FORECAST_DAYS:
        print(
            f"--days must be between 1 and {MAX_FORECAST_DAYS}; received {args.days}.",
            file=sys.stderr,
        )
        return 2

    try:
        location, forecast_days = fetch_forecast(args.location, days=args.days)
    except WeatherForecastError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        payload = {
            "location": asdict(location),
            "forecast_days": [asdict(day) for day in forecast_days],
        }
        print(json.dumps(payload, indent=2))
        return 0

    print(format_forecast_table(location, forecast_days))
    return 0

