"""Wire-format models for the air-marshall HTTP API."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Strict, model_validator

StrictBool = Annotated[bool, Strict()]
"""bool that rejects integer coercion (e.g. ``0``/``1`` → ``False``/``True``)."""

StrictFloat = Annotated[float, Strict()]
"""float that rejects string coercion."""


class HumidityRecord(BaseModel):
    """A humidity and temperature reading from a sensor.

    Attributes:
        sensor_id: Logical sensor identifier (e.g. "living_room").
        sensor_serial_number: Hardware serial number burned into the sensor.
        timestamp: When the reading was taken (timezone-aware).
        temperature: Degrees Celsius.
        humidity: Relative humidity, 0–100.
        is_touched: True when the sensor was physically touched at sample time.
    """

    sensor_id: str
    sensor_serial_number: str
    timestamp: datetime
    temperature: StrictFloat
    humidity: StrictFloat
    is_touched: StrictBool


class FanRecord(BaseModel):
    """A fan on/off state change event."""

    timestamp: datetime
    is_on: StrictBool


class ControlRecord(BaseModel):
    """An HVAC control output state change event."""

    timestamp: datetime
    humidifier_on: StrictBool
    fan_on: StrictBool


class ConfigRecord(BaseModel):
    """A control parameter configuration event.

    Attributes:
        timestamp: When the configuration was applied (timezone-aware).
        humidity_low: Lower bound of the target humidity range, 0–100.
        humidity_high: Upper bound of the target humidity range, 0–100.
    """

    timestamp: datetime
    humidity_low: StrictFloat
    humidity_high: StrictFloat

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
