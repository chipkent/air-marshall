"""CLI entrypoint for the air-marshall monitor publisher."""

import argparse
import asyncio
import logging
import os
import sys

import zipcodes

from air_marshall.api.client import AirMarshallClient
from air_marshall.monitor.fan import AutomationHatFanReader
from air_marshall.monitor.humidity import SHT45Reader
from air_marshall.monitor.publisher import MonitorPublisher
from air_marshall.monitor.weather import OpenMeteoReader

_logger = logging.getLogger(__name__)

_DEFAULT_INTERVAL = 30.0
"""Default seconds between hardware sensor publishes."""

_DEFAULT_PORT = "/dev/ttyACM0"
"""Default serial port for the SHT45 Trinkey."""

_DEFAULT_WEATHER_INTERVAL = 300.0
"""Default seconds between outdoor weather publishes."""

_DEFAULT_ZIP = "80919"
"""Default US zip code used for outdoor weather lookups."""

_PUBLISH_CHOICES = frozenset({"humidity", "fan", "weather"})
"""Valid individual --publish values."""

_DEFAULT_LOG_LEVEL = "info"
"""Default logging level for the monitor publisher."""


def main() -> None:
    """Run the air-marshall monitor publisher CLI."""
    log_level = os.environ.get(
        "AIR_MARSHALL_MONITOR_LOG_LEVEL", _DEFAULT_LOG_LEVEL
    ).upper()
    logging.basicConfig(level=log_level)
    parser = argparse.ArgumentParser(
        description="Read sensors and publish to the air-marshall database service."
    )
    parser.add_argument(
        "--publish",
        nargs="+",
        choices=sorted(_PUBLISH_CHOICES),
        required=True,
        metavar="SENSOR",
        help="One or more sensors to publish: humidity, fan, weather.",
    )
    parser.add_argument(
        "--humidity-name",
        dest="humidity_name",
        default=None,
        help="Sensor identifier used as sensor_id in HumidityRecord (required with --publish humidity).",
    )
    parser.add_argument(
        "--sensor-interval",
        dest="sensor_interval",
        type=float,
        default=_DEFAULT_INTERVAL,
        help="Seconds between hardware sensor publish cycles (default: 30).",
    )
    parser.add_argument(
        "--humidity-port",
        dest="humidity_port",
        default=_DEFAULT_PORT,
        help="Serial port for SHT45 Trinkey (default: /dev/ttyACM0).",
    )
    parser.add_argument(
        "--fan-input",
        type=int,
        dest="fan_input",
        choices=[1, 2, 3],
        help="Automation HAT digital input number for the fan sensor (1–3).",
    )
    parser.add_argument(
        "--weather-zip",
        type=str,
        dest="weather_zip",
        default=_DEFAULT_ZIP,
        help=f"US zip code for outdoor weather publishing via Open-Meteo (default: {_DEFAULT_ZIP}).",
    )
    parser.add_argument(
        "--weather-name",
        type=str,
        default="outdoor",
        dest="weather_name",
        help="sensor_id for outdoor weather records (default: outdoor).",
    )
    parser.add_argument(
        "--weather-interval",
        type=float,
        default=_DEFAULT_WEATHER_INTERVAL,
        dest="weather_interval",
        help="Seconds between weather publishes (default: 300).",
    )
    args = parser.parse_args()

    publish = set(args.publish)

    if "humidity" in publish and args.humidity_name is None:
        parser.error("--humidity-name is required when publishing humidity")
    if "fan" in publish and args.fan_input is None:
        parser.error("--fan-input is required when publishing fan")

    base_url = os.environ.get("AIR_MARSHALL_BASE_URL")
    if not base_url:
        print(
            "Error: AIR_MARSHALL_BASE_URL environment variable is required.",
            file=sys.stderr,
        )
        sys.exit(1)

    api_key = os.environ.get("AIR_MARSHALL_API_KEY")
    if not api_key:
        print(
            "Error: AIR_MARSHALL_API_KEY environment variable is required.",
            file=sys.stderr,
        )
        sys.exit(1)

    humidity_reader: SHT45Reader | None = (
        SHT45Reader(port=args.humidity_port, sensor_id=args.humidity_name)
        if "humidity" in publish
        else None
    )
    fan_reader: AutomationHatFanReader | None = (
        AutomationHatFanReader(input_number=args.fan_input)
        if "fan" in publish
        else None
    )

    weather_reader: OpenMeteoReader | None = None
    if "weather" in publish:
        matches = zipcodes.matching(args.weather_zip)
        if not matches:
            parser.error(f"Unknown zip code: {args.weather_zip!r}")
        weather_reader = OpenMeteoReader(
            latitude=float(matches[0]["lat"]),
            longitude=float(matches[0]["long"]),
            sensor_id=args.weather_name,
        )

    async def _run() -> None:
        async with AirMarshallClient(base_url=base_url, api_key=api_key) as client:
            publisher = MonitorPublisher(
                client=client,
                humidity_reader=humidity_reader,
                fan_reader=fan_reader,
                weather_reader=weather_reader,
            )
            try:
                await publisher.run(
                    sensor_interval=args.sensor_interval,
                    weather_interval=args.weather_interval,
                )
            finally:
                if weather_reader is not None:
                    await weather_reader.close()
                if humidity_reader is not None:
                    humidity_reader.close()

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        _logger.info("Shutting down.")


if __name__ == "__main__":
    main()
