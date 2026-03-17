"""Wire-format models for the air-marshall HTTP API."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, Strict, model_validator

StrictBool = Annotated[bool, Strict()]
"""bool that rejects integer coercion (e.g. ``0``/``1`` → ``False``/``True``)."""

StrictFloat = Annotated[float, Strict()]
"""float that rejects string coercion."""


class HumidityRecord(BaseModel):
    """A humidity and temperature reading from a sensor."""

    sensor_id: str = Field(
        description='Logical sensor identifier (e.g. "living_room").',
        examples=["living_room"],
    )
    sensor_serial_number: str = Field(
        description="Hardware serial number burned into the sensor.",
        examples=["ABCD1234"],
    )
    timestamp: datetime = Field(
        description="When the reading was taken (timezone-aware).",
        examples=["2024-01-15T10:30:00+00:00"],
    )
    temperature: StrictFloat = Field(
        description="Degrees Celsius.",
        examples=[21.5],
    )
    humidity: StrictFloat = Field(
        description="Relative humidity, 0–100.",
        examples=[45.2],
        ge=0.0,
        le=100.0,
    )
    is_touched: StrictBool = Field(
        description="True when the sensor was physically touched at sample time.",
        examples=[False],
    )


class FanRecord(BaseModel):
    """A fan on/off state change event."""

    timestamp: datetime = Field(
        description="When the state change occurred (timezone-aware).",
        examples=["2024-01-15T10:30:00+00:00"],
    )
    is_on: StrictBool = Field(
        description="True when the fan transitioned to on; False when it turned off.",
        examples=[True],
    )


class ControlRecord(BaseModel):
    """An HVAC control output state change event."""

    timestamp: datetime = Field(
        description="When the state change occurred (timezone-aware).",
        examples=["2024-01-15T10:30:00+00:00"],
    )
    humidifier_on: StrictBool = Field(
        description="True when the humidifier output is active.",
        examples=[True],
    )
    fan_on: StrictBool = Field(
        description="True when the fan output is active.",
        examples=[False],
    )


class ConfigRecord(BaseModel):
    """A control parameter configuration event."""

    timestamp: datetime = Field(
        description="When the configuration was applied (timezone-aware).",
        examples=["2024-01-15T10:30:00+00:00"],
    )
    humidity_low: StrictFloat = Field(
        description="Lower bound of the target humidity range, 0–100. Must be strictly less than humidity_high.",
        examples=[35.0],
        ge=0.0,
        le=100.0,
    )
    humidity_high: StrictFloat = Field(
        description="Upper bound of the target humidity range, 0–100. Must be strictly greater than humidity_low.",
        examples=[50.0],
        ge=0.0,
        le=100.0,
    )

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

    humidity: list[HumidityRecord] = Field(
        default=[],
        description="Most recent humidity reading from each sensor; one entry per distinct sensor. Empty when no data exists.",
    )
    fan: FanRecord | None = Field(
        default=None,
        description="Most recent fan state, or None if no record has been recorded yet.",
    )
    control: ControlRecord | None = Field(
        default=None,
        description="Most recent HVAC control state, or None if no record has been recorded yet.",
    )
    config: ConfigRecord | None = Field(
        default=None,
        description="Most recent configuration record, or None if no record has been recorded yet.",
    )


class HistoryResponse(BaseModel):
    """All records within the service's retention window."""

    humidity: list[HumidityRecord] = Field(
        default=[],
        description="All humidity readings within the retention window, ordered oldest-first.",
    )
    fan: list[FanRecord] = Field(
        default=[],
        description="All fan state records within the retention window, ordered oldest-first.",
    )
    control: list[ControlRecord] = Field(
        default=[],
        description="All HVAC control state records within the retention window, ordered oldest-first.",
    )
    config: list[ConfigRecord] = Field(
        default=[],
        description="All configuration records within the retention window, ordered oldest-first.",
    )
