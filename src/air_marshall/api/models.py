"""Wire-format models for the air-marshall HTTP API."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Strict, model_validator

StrictBool = Annotated[bool, Strict()]
"""bool that rejects integer coercion (e.g. ``0``/``1`` → ``False``/``True``)."""

StrictFloat = Annotated[float, Strict()]
"""float that rejects string coercion."""


class HumidityRecord(BaseModel):
    """A humidity and temperature reading from a sensor."""

    sensor_id: str
    """Logical sensor identifier (e.g. ``"living_room"``)."""
    sensor_serial_number: str
    """Hardware serial number burned into the sensor."""
    timestamp: datetime
    """When the reading was taken (timezone-aware)."""
    temperature: StrictFloat
    """Degrees Celsius."""
    humidity: StrictFloat
    """Relative humidity, 0–100."""
    is_touched: StrictBool
    """True when the sensor was physically touched at sample time."""


class FanRecord(BaseModel):
    """A fan on/off state change event."""

    timestamp: datetime
    """When the state change occurred (timezone-aware)."""
    is_on: StrictBool
    """True when the fan transitioned to on; False when it turned off."""


class ControlRecord(BaseModel):
    """An HVAC control output state change event."""

    timestamp: datetime
    """When the state change occurred (timezone-aware)."""
    humidifier_on: StrictBool
    """True when the humidifier output is active."""
    fan_on: StrictBool
    """True when the fan output is active."""


class ConfigRecord(BaseModel):
    """A control parameter configuration event."""

    timestamp: datetime
    """When the configuration was applied (timezone-aware)."""
    humidity_low: StrictFloat
    """Lower bound of the target humidity range, 0–100."""
    humidity_high: StrictFloat
    """Upper bound of the target humidity range, 0–100."""

    @model_validator(mode="after")
    def _humidity_range_valid(self) -> "ConfigRecord":
        if self.humidity_low >= self.humidity_high:
            raise ValueError("humidity_low must be strictly less than humidity_high")
        return self


class LatestResponse(BaseModel):
    """The most recent record of each type.

    ``humidity`` contains one entry per distinct sensor (empty when no data).
    ``fan``, ``control``, and ``config`` are None when no data exists yet.
    """

    humidity: list[HumidityRecord] = []
    fan: FanRecord | None = None
    control: ControlRecord | None = None
    config: ConfigRecord | None = None


class HistoryResponse(BaseModel):
    """All records within the service's retention window."""

    humidity: list[HumidityRecord] = []
    fan: list[FanRecord] = []
    control: list[ControlRecord] = []
    config: list[ConfigRecord] = []
