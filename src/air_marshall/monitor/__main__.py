"""CLI entrypoint for the air-marshall monitor publisher."""

import argparse
import asyncio
import logging
import os
import sys

from air_marshall.api.client import AirMarshallClient
from air_marshall.monitor.fan import AutomationHatFanReader
from air_marshall.monitor.humidity import SHT45Reader
from air_marshall.monitor.publisher import MonitorPublisher

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)

_DEFAULT_INTERVAL = 30.0
"""Default seconds between sensor publishes."""

_DEFAULT_PORT = "/dev/ttyACM0"
"""Default serial port for the SHT45 Trinkey."""


def main() -> None:
    """Run the air-marshall monitor publisher CLI."""
    parser = argparse.ArgumentParser(
        description="Read sensors and publish to the air-marshall database service."
    )
    parser.add_argument(
        "--publish",
        choices=["humidity", "fan", "both"],
        required=True,
        help="Which sensors to publish: humidity, fan, or both.",
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Sensor identifier used as sensor_id in HumidityRecord.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=_DEFAULT_INTERVAL,
        help="Seconds between publishes (default: 30).",
    )
    parser.add_argument(
        "--port",
        default=_DEFAULT_PORT,
        help="Serial port for SHT45 Trinkey (default: /dev/ttyACM0).",
    )
    parser.add_argument(
        "--fan-input",
        type=int,
        dest="fan_input",
        help="Automation HAT digital input number for the fan sensor (1–3).",
    )
    args = parser.parse_args()

    if args.publish in ("fan", "both") and args.fan_input is None:
        parser.error("--fan-input is required when --publish is 'fan' or 'both'")

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

    humidity_reader: SHT45Reader | None = None
    if args.publish in ("humidity", "both"):
        humidity_reader = SHT45Reader(port=args.port, sensor_id=args.name)

    fan_reader: AutomationHatFanReader | None = None
    if args.publish in ("fan", "both"):
        fan_reader = AutomationHatFanReader(input_number=args.fan_input)

    client = AirMarshallClient(base_url=base_url, api_key=api_key)
    publisher = MonitorPublisher(
        client=client,
        humidity_reader=humidity_reader,
        fan_reader=fan_reader,
    )

    try:
        asyncio.run(publisher.run(interval=args.interval))
    except KeyboardInterrupt:
        _logger.info("Shutting down.")


if __name__ == "__main__":
    main()
