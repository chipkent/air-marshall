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

## CLI reference

```text
air-marshall-publish --publish {humidity|fan|both} --name SENSOR_NAME [--interval SECONDS] [--port PATH]
```

| Flag | Default | Description |
|---|---|---|
| `--publish` | — (required) | `humidity`, `fan`, or `both` |
| `--name` | — (required) | Logical sensor identifier stored in each record |
| `--interval` | `30` | Seconds between publish cycles |
| `--port` | `/dev/ttyACM0` | Serial port for the SHT45 Trinkey (ignored when `--publish fan`) |

### Examples

Publish humidity only, every 30 seconds:

```sh
export AIR_MARSHALL_BASE_URL=http://pi4:8000
export AIR_MARSHALL_API_KEY=your-api-key-here
air-marshall-publish --publish humidity --name living-room --interval 30
```

Publish both humidity and fan state, every 60 seconds:

```sh
air-marshall-publish --publish both --name living-room --fan-input 1
```

## Hardware wiring

### SHT45 Trinkey (humidity/temperature)

Plug the SHT45 Trinkey into a USB port on the monitor RPi. The CircuitPython firmware
emits one CSV line per reading over USB serial:

```text
<temperature_c>,<humidity_pct>,<is_touched_0_or_1>,<serial_number_hex>
```

The device typically appears as `/dev/ttyACM0`. Use `--port` to specify a different path
if multiple USB serial devices are present.

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
    await publisher.run(interval=30.0)

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
ExecStart=/home/pi/.venv/bin/air-marshall-publish --publish both --name living-room --interval 60 --fan-input 1
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
