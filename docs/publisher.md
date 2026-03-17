# air-marshall-publish

CLI tool for reading sensors on the monitor Raspberry Pi and publishing data to the
air-marshall database service.

## Installation

Install the package with the `monitor` extra to pull in the required libraries:

```sh
uv sync --extra monitor
```

On the monitor Raspberry Pi, also install the Automation HAT library manually (it requires
RPi hardware headers that cannot build on other platforms):

```sh
pip install automationhat
```

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `AIR_MARSHALL_BASE_URL` | Yes | Base URL of the database service (e.g. `http://pi4:8000`) |
| `AIR_MARSHALL_API_KEY` | Yes | Shared API key for authentication |
| `AIR_MARSHALL_MONITOR_LOG_LEVEL` | No | Log level: `debug`, `info`, `warning`, `error`, `critical` (default: `info`) |

## Debugging

To enable verbose logging for a single run:

```sh
AIR_MARSHALL_MONITOR_LOG_LEVEL=debug air-marshall-publish --publish humidity --humidity-name living-room
```

Or in the systemd `EnvironmentFile` (`/etc/air-marshall/publish.env`) for a persistent change:

```sh
AIR_MARSHALL_MONITOR_LOG_LEVEL=debug
```

## CLI reference

```text
air-marshall-publish --publish SENSOR [SENSOR ...] [--humidity-name NAME] [--sensor-interval SECONDS]
                     [--humidity-port PATH] [--fan-input {1,2,3}]
                     [--weather-zip ZIPCODE] [--weather-name NAME] [--weather-interval SECONDS]
```

| Flag | Default | Description |
|---|---|---|
| `--publish` | — | One or more of: `humidity`, `fan`, `weather` (required; multiple allowed) |
| `--humidity-name` | — | Logical sensor identifier stored in each humidity record (required with `--publish humidity`) |
| `--sensor-interval` | `30` | Seconds between hardware sensor publish cycles |
| `--humidity-port` | `/dev/ttyACM0` | Serial port for the SHT45 Trinkey |
| `--fan-input` | — | Automation HAT digital input number for the fan sensor (`1`, `2`, or `3`; required with `--publish fan`) |
| `--weather-zip` | `80919` | US zip code for outdoor weather publishing via Open-Meteo |
| `--weather-name` | `outdoor` | `sensor_id` stored in each outdoor weather record |
| `--weather-interval` | `300` | Seconds between outdoor weather publish cycles |

### Examples

Publish humidity only, every 30 seconds:

```sh
export AIR_MARSHALL_BASE_URL=http://pi4:8000
export AIR_MARSHALL_API_KEY=your-api-key-here
air-marshall-publish --publish humidity --humidity-name living-room --sensor-interval 30
```

Publish both humidity and fan state, every 60 seconds:

```sh
air-marshall-publish --publish humidity fan --humidity-name living-room --fan-input 1
```

Publish indoor humidity and outdoor weather simultaneously:

```sh
air-marshall-publish --publish humidity weather --humidity-name living-room \
  --weather-zip 80919 --weather-interval 300
```

The hardware sensor loop and the weather loop run independently at their own
cadences. Outdoor weather records land in the same humidity table under the
`sensor_id` set by `--weather-name` (default `outdoor`).

## Hardware wiring

### SHT45 Trinkey (humidity/temperature)

Plug the SHT45 Trinkey into a USB port on the monitor RPi. The CircuitPython firmware
emits one CSV line per reading over USB serial:

```text
<temperature_c>,<humidity_pct>,<is_touched_0_or_1>,<serial_number_hex>
```

The device typically appears as `/dev/ttyACM0`. Use `--humidity-port` to specify a
different path if multiple USB serial devices are present.

### Automation HAT (fan state)

The fan on/off signal is read from digital input 1 of the Pimoroni Automation HAT. No
additional configuration is required; the `automationhat` Python library is used directly.

## Library usage

`MonitorPublisher` is importable for embedding in other applications:

```python
import asyncio
from air_marshall.api.client import AirMarshallClient
from air_marshall.monitor import MonitorPublisher, SHT45Reader, AutomationHatFanReader

async def main() -> None:
    client = AirMarshallClient(base_url="http://pi4:8000", api_key="your-api-key-here")
    humidity_reader = SHT45Reader(port="/dev/ttyACM0", sensor_id="living-room")
    publisher = MonitorPublisher(client=client, humidity_reader=humidity_reader)
    await publisher.run(sensor_interval=30.0, weather_interval=300.0)

asyncio.run(main())
```

## Running as a systemd service

Create `/etc/air-marshall/publish.env` with the secrets (readable only by root):

```sh
sudo mkdir -p /etc/air-marshall
sudo tee /etc/air-marshall/publish.env > /dev/null <<'EOF'
AIR_MARSHALL_BASE_URL=http://pi4:8000
AIR_MARSHALL_API_KEY=your-api-key-here
EOF
sudo chmod 600 /etc/air-marshall/publish.env
```

Create `/etc/systemd/system/air-marshall-publish.service`:

```ini
[Unit]
Description=air-marshall monitor publisher
After=network.target

[Service]
Type=simple
User=pi
EnvironmentFile=/etc/air-marshall/publish.env
ExecStart=/home/pi/.venv/bin/air-marshall-publish --publish humidity fan weather --humidity-name living-room --sensor-interval 60 --fan-input 1 --weather-zip 80919
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```sh
sudo systemctl enable air-marshall-publish
sudo systemctl start air-marshall-publish
sudo journalctl -u air-marshall-publish -f
```
