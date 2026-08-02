from __future__ import annotations

import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from multi_agent_generator_evaluator_loop.weather_forecast import (
    build_forecast_days,
    build_forecast_url as build_loop_forecast_url,
    render_forecast_markdown,
)

from weather_forecast.cli import (
    DEFAULT_DAYS,
    ForecastDay,
    Location,
    build_forecast_url,
    build_geocoding_url,
    format_forecast_table,
    parse_args,
    parse_daily_forecast,
    resolve_location,
)


class LoopWeatherForecastTests(unittest.TestCase):
    def test_build_forecast_url_defaults_to_seven_days(self) -> None:
        url = build_loop_forecast_url(
            latitude=37.8349,
            longitude=-122.1297,
        )
        params = parse_qs(urlparse(url).query)

        self.assertEqual(params["forecast_days"], ["7"])

    def test_build_forecast_url_requests_celsius_and_hourly_wind(self) -> None:
        url = build_loop_forecast_url(
            latitude=37.8349,
            longitude=-122.1297,
        )
        params = parse_qs(urlparse(url).query)

        self.assertEqual(params["temperature_unit"], ["celsius"])
        self.assertEqual(params["wind_speed_unit"], ["mph"])
        self.assertEqual(params["hourly"], ["wind_speed_10m"])
        self.assertNotIn("wind_speed_10m_max", params["daily"][0])

    def test_builds_days_and_renders_markdown(self) -> None:
        payload = {
            "daily": {
                "time": ["2026-05-05", "2026-05-06"],
                "temperature_2m_max": [22.3, 21.0],
                "temperature_2m_min": [10.7, 9.9],
            },
            "hourly": {
                "time": [
                    "2026-05-05T00:00",
                    "2026-05-05T12:00",
                    "2026-05-06T00:00",
                    "2026-05-06T12:00",
                ],
                "wind_speed_10m": [4.2, 11.2, 3.5, 9.1],
            },
        }

        forecast_days = build_forecast_days(payload)
        markdown = render_forecast_markdown("Moraga, CA", forecast_days)

        self.assertEqual(2, len(forecast_days))
        self.assertIn("# 2-day weather forecast for Moraga, CA", markdown)
        self.assertIn("2026-05-05", markdown)
        self.assertIn("High 22.3, Low 10.7", markdown)
        self.assertIn("| 2026-05-05 | High 22.3, Low 10.7 | 11.2 |", markdown)
        self.assertIn("Temperature (C)", markdown)
        self.assertIn("Max Wind (mph)", markdown)


class WeatherForecastCliTests(unittest.TestCase):
    def test_parse_args_defaults_to_moraga_for_seven_day_forecast(self) -> None:
        args = parse_args([])

        self.assertEqual(args.location, "Moraga, CA")
        self.assertEqual(args.days, DEFAULT_DAYS)
        self.assertFalse(args.json)

    def test_build_geocoding_url_includes_query(self) -> None:
        url = build_geocoding_url("Moraga, CA")
        params = parse_qs(urlparse(url).query)
        self.assertEqual(params["name"], ["Moraga, CA"])
        self.assertEqual(params["count"], ["1"])

    def test_build_forecast_url_requests_daily_temperature_and_wind(self) -> None:
        url = build_forecast_url(37.8349, -122.1297, days=7)
        params = parse_qs(urlparse(url).query)
        self.assertEqual(params["forecast_days"], ["7"])
        self.assertEqual(params["temperature_unit"], ["celsius"])
        self.assertEqual(params["wind_speed_unit"], ["mph"])
        self.assertIn("temperature_2m_max", params["daily"][0])
        self.assertEqual(params["hourly"], ["wind_speed_10m"])

    def test_resolve_location_falls_back_for_moraga(self) -> None:
        with patch("weather_forecast.cli.fetch_json", return_value={"results": []}):
            location = resolve_location("Moraga, CA")

        self.assertEqual(location.name, "Moraga")
        self.assertEqual(location.admin1, "California")
        self.assertAlmostEqual(location.latitude, 37.83493)

    def test_parse_daily_forecast_trims_to_requested_days(self) -> None:
        payload = {
            "daily": {
                "time": ["2026-05-05", "2026-05-06"],
                "temperature_2m_max": [22.3, 23.1],
                "temperature_2m_min": [9.0, 10.2],
            },
            "hourly": {
                "time": [
                    "2026-05-05T00:00",
                    "2026-05-05T12:00",
                    "2026-05-06T00:00",
                    "2026-05-06T12:00",
                ],
                "wind_speed_10m": [3.1, 11.2, 4.0, 9.9],
            },
        }

        forecast = parse_daily_forecast(payload, days=1)

        self.assertEqual(len(forecast), 1)
        self.assertEqual(forecast[0].date, "2026-05-05")
        self.assertEqual(forecast[0].wind_speed_min_mph, 3.1)
        self.assertEqual(forecast[0].wind_speed_max_mph, 11.2)

    def test_format_forecast_table_renders_temperature_and_wind_columns(self) -> None:
        location = Location(
            name="Moraga",
            admin1="California",
            country="United States",
            latitude=37.8349,
            longitude=-122.1297,
            timezone="America/Los_Angeles",
        )
        forecast = [
            ForecastDay(
                date="2026-05-05",
                temp_max_c=22.3,
                temp_min_c=9.0,
                wind_speed_min_mph=3.1,
                wind_speed_max_mph=11.2,
            )
        ]

        table = format_forecast_table(location, forecast)

        self.assertIn("1-day weather forecast for Moraga, California, United States", table)
        self.assertIn("Temperature (C)", table)
        self.assertIn("Wind (mph)", table)
        self.assertIn("low 3.1, max 11.2", table)


if __name__ == "__main__":
    unittest.main()
