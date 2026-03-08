# air-marshall database service

A FastAPI/SQLite HTTP service that stores sensor readings and HVAC state events
from the monitor and controller devices and makes them available to the Flutter
app. It can run on any host reachable by those clients — a Raspberry Pi, a NAS,
a workstation, or a cloud VM.

## Running the service

Install the `database` extra and start the service:

```sh
uv sync --extra database
uv run air-marshall-db
```

Or via the module directly:

```sh
uv run python -m air_marshall.database
```

## Environment variables

All configuration is supplied through environment variables. `AIR_MARSHALL_DB_API_KEY`
is the only required variable; all others have defaults.

| Variable | Default | Description |
|---|---|---|
| `AIR_MARSHALL_DB_API_KEY` | *(required)* | Shared secret. Clients must send this in the `X-API-Key` header for all requests. |
| `AIR_MARSHALL_DB_DB_PATH` | `air_marshall.db` | Path to the SQLite database file. |
| `AIR_MARSHALL_DB_RETENTION_DAYS` | `30` | Records older than this many days are deleted by the pruning loop. |
| `AIR_MARSHALL_DB_PRUNING_INTERVAL_HOURS` | `6` | How often the pruning loop runs. |
| `AIR_MARSHALL_DB_HOST` | `0.0.0.0` | Host address passed to uvicorn. |
| `AIR_MARSHALL_DB_PORT` | `8000` | TCP port passed to uvicorn. |
| `AIR_MARSHALL_DB_LOG_LEVEL` | `info` | Uvicorn log level (`debug`, `info`, `warning`, `error`, `critical`). |

## Security

The service uses a shared `X-API-Key` header for authentication. Over plain HTTP
this key is transmitted in cleartext and can be intercepted by anyone on the same
network, allowing them to issue arbitrary authenticated requests.

**Do not expose the service over unencrypted HTTP on untrusted networks.**

For deployments beyond a fully trusted local network, place the service behind a
TLS-terminating reverse proxy (nginx, Caddy, Traefik, etc.) so that all traffic —
including the API key and sensor data — is encrypted in transit. Bind uvicorn to
`127.0.0.1` and let the proxy handle the public interface:

```sh
AIR_MARSHALL_DB_HOST=127.0.0.1 uv run air-marshall-db
```

## systemd setup

Create an environment file readable only by root:

```sh
sudo mkdir -p /etc/air-marshall
sudo tee /etc/air-marshall/db.env > /dev/null <<'EOF'
AIR_MARSHALL_DB_API_KEY=your-secret-key-here
AIR_MARSHALL_DB_DB_PATH=/var/lib/air-marshall/air_marshall.db
EOF
sudo chmod 600 /etc/air-marshall/db.env
```

Create the service unit at `/etc/systemd/system/air-marshall-db.service`:

```ini
[Unit]
Description=air-marshall database service
After=network.target

[Service]
User=air-marshall
EnvironmentFile=/etc/air-marshall/db.env
ExecStart=/path/to/venv/bin/air-marshall-db
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:

```sh
sudo systemctl enable --now air-marshall-db
```

## API endpoints

All endpoints are under `/data`.

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/data/humidity` | Required | Store a humidity reading. |
| `POST` | `/data/fan` | Required | Store a fan state event. |
| `POST` | `/data/control` | Required | Store a control state event. |
| `GET` | `/data/latest` | Required | Most recent record of each type. Accepts `?sensor_id=` to filter humidity. |
| `GET` | `/data/history` | Required | All records within the retention window. |

All requests must include `X-API-Key: <key>` matching `AIR_MARSHALL_DB_API_KEY`.

Interactive API docs are available at `http://<host>:<port>/docs` when the service is running.
