"""Tests for air_marshall.monitor.__main__."""

import asyncio as _asyncio
import sys
import warnings as _warnings
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Capture the real asyncio.run before any test patches replace it on the module object.
# _asyncio_run patches asyncio.run on the asyncio module itself, so calling
# _asyncio.run() inside _asyncio_run would recurse; _real_asyncio_run is immune.
_real_asyncio_run = _asyncio.run


def _asyncio_run(coro: object) -> None:
    """asyncio.run wrapper that explicitly closes the pre-existing event loop.

    pytest-asyncio >=1.x saves and restores the current event loop around each async
    test via _temporary_event_loop_policy. In Python 3.12+, if no current loop exists,
    asyncio.get_event_loop() silently creates one. asyncio.run() ends by calling
    set_event_loop(None), dropping the policy's reference to that loop; it then gets
    GC'd mid-test with closed=False, triggering ResourceWarning -> test failure.

    Capturing the loop before asyncio.run() and explicitly closing it afterward ensures
    the loop is always closed cleanly, preventing the ResourceWarning.
    """
    with _warnings.catch_warnings():
        _warnings.simplefilter("ignore", DeprecationWarning)
        try:
            _old_loop = _asyncio.get_event_loop()
        except RuntimeError:
            _old_loop = None
    _real_asyncio_run(coro)  # type: ignore[arg-type]
    if _old_loop is not None and not _old_loop.is_closed():
        _old_loop.close()


_VALID_ZIP_MATCH = [{"lat": "39.0", "long": "-104.9", "zip_code": "80919"}]


class TestLogging:
    """Tests for logging configuration in main()."""

    def test_debug_log_level_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """AIR_MARSHALL_MONITOR_LOG_LEVEL=debug results in basicConfig called with level='DEBUG'."""
        monkeypatch.setenv("AIR_MARSHALL_BASE_URL", "http://pi:8000")
        monkeypatch.setenv("AIR_MARSHALL_API_KEY", "secret")
        monkeypatch.setenv("AIR_MARSHALL_MONITOR_LOG_LEVEL", "debug")
        monkeypatch.setattr(
            sys, "argv", ["cmd", "--publish", "humidity", "--humidity-name", "s1"]
        )

        mock_publisher_instance = MagicMock()
        mock_publisher_instance.run = AsyncMock()
        mock_publisher_cls = MagicMock(return_value=mock_publisher_instance)

        with (
            patch("air_marshall.monitor.__main__.SHT45Reader"),
            patch("air_marshall.monitor.__main__.AirMarshallClient"),
            patch("air_marshall.monitor.__main__.MonitorPublisher", mock_publisher_cls),
            patch("air_marshall.monitor.__main__.OpenMeteoReader"),
            patch("air_marshall.monitor.__main__.asyncio.run", _asyncio_run),
            patch(
                "air_marshall.monitor.__main__.logging.basicConfig"
            ) as mock_basicconfig,
        ):
            from air_marshall.monitor.__main__ import main

            main()

        mock_basicconfig.assert_called_once_with(level="DEBUG")

    def test_invalid_log_level_exits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """main() exits non-zero when AIR_MARSHALL_MONITOR_LOG_LEVEL is unrecognised."""
        monkeypatch.setenv("AIR_MARSHALL_BASE_URL", "http://pi:8000")
        monkeypatch.setenv("AIR_MARSHALL_API_KEY", "secret")
        monkeypatch.setenv("AIR_MARSHALL_MONITOR_LOG_LEVEL", "VERBOSE")
        monkeypatch.setattr(
            sys, "argv", ["cmd", "--publish", "humidity", "--humidity-name", "s1"]
        )

        from air_marshall.monitor.__main__ import main

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code != 0


class TestMissingEnvVars:
    """Tests for main() with missing environment variables."""

    def test_missing_base_url_exits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """main() exits non-zero when AIR_MARSHALL_BASE_URL is not set."""
        monkeypatch.delenv("AIR_MARSHALL_BASE_URL", raising=False)
        monkeypatch.delenv("AIR_MARSHALL_API_KEY", raising=False)
        monkeypatch.setattr(
            sys, "argv", ["cmd", "--publish", "humidity", "--humidity-name", "s1"]
        )
        from air_marshall.monitor.__main__ import main

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code != 0

    def test_missing_api_key_exits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """main() exits non-zero when AIR_MARSHALL_API_KEY is not set."""
        monkeypatch.setenv("AIR_MARSHALL_BASE_URL", "http://test")
        monkeypatch.delenv("AIR_MARSHALL_API_KEY", raising=False)
        monkeypatch.setattr(
            sys, "argv", ["cmd", "--publish", "humidity", "--humidity-name", "s1"]
        )
        from air_marshall.monitor.__main__ import main

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code != 0


class TestInvalidArgs:
    """Tests for main() with invalid CLI arguments."""

    def test_invalid_publish_value_exits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """main() exits when --publish is given an invalid value."""
        monkeypatch.setenv("AIR_MARSHALL_BASE_URL", "http://test")
        monkeypatch.setenv("AIR_MARSHALL_API_KEY", "key")
        monkeypatch.setattr(
            sys, "argv", ["cmd", "--publish", "invalid", "--humidity-name", "s1"]
        )
        from air_marshall.monitor.__main__ import main

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code != 0

    def test_missing_humidity_name_exits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """main() exits when --publish humidity is used without --humidity-name."""
        monkeypatch.setenv("AIR_MARSHALL_BASE_URL", "http://test")
        monkeypatch.setenv("AIR_MARSHALL_API_KEY", "key")
        monkeypatch.setattr(sys, "argv", ["cmd", "--publish", "humidity"])
        from air_marshall.monitor.__main__ import main

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code != 0

    def test_missing_fan_input_exits_when_publish_fan(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """main() exits when --publish fan is used without --fan-input."""
        monkeypatch.setenv("AIR_MARSHALL_BASE_URL", "http://test")
        monkeypatch.setenv("AIR_MARSHALL_API_KEY", "key")
        monkeypatch.setattr(sys, "argv", ["cmd", "--publish", "fan"])
        from air_marshall.monitor.__main__ import main

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code != 0

    def test_zero_sensor_interval_exits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """main() exits when --sensor-interval is 0."""
        monkeypatch.setenv("AIR_MARSHALL_BASE_URL", "http://test")
        monkeypatch.setenv("AIR_MARSHALL_API_KEY", "key")
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "cmd",
                "--publish",
                "humidity",
                "--humidity-name",
                "s1",
                "--sensor-interval",
                "0",
            ],
        )
        from air_marshall.monitor.__main__ import main

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code != 0

    def test_negative_weather_interval_exits(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """main() exits when --weather-interval is negative."""
        monkeypatch.setenv("AIR_MARSHALL_BASE_URL", "http://test")
        monkeypatch.setenv("AIR_MARSHALL_API_KEY", "key")
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "cmd",
                "--publish",
                "humidity",
                "--humidity-name",
                "s1",
                "--weather-interval",
                "-1",
            ],
        )
        from air_marshall.monitor.__main__ import main

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code != 0


class TestValidArgs:
    """Tests for main() with valid arguments and environment."""

    def _run_main(
        self,
        monkeypatch: pytest.MonkeyPatch,
        argv: list[str],
        zipcodes_result: list[dict[str, str]] = _VALID_ZIP_MATCH,
    ) -> tuple[MagicMock, MagicMock, MagicMock, MagicMock, MagicMock, MagicMock]:
        monkeypatch.setenv("AIR_MARSHALL_BASE_URL", "http://pi:8000")
        monkeypatch.setenv("AIR_MARSHALL_API_KEY", "secret")
        monkeypatch.setattr(sys, "argv", argv)

        mock_humidity_reader_cls = MagicMock()
        mock_fan_reader_cls = MagicMock()
        mock_weather_reader_cls = MagicMock()
        mock_weather_reader_cls.return_value.close = AsyncMock()
        mock_client_cls = MagicMock()
        mock_publisher_cls = MagicMock()
        mock_publisher_instance = MagicMock()
        mock_publisher_instance.run = AsyncMock()
        mock_publisher_cls.return_value = mock_publisher_instance

        with (
            patch(
                "air_marshall.monitor.__main__.SHT45Reader",
                mock_humidity_reader_cls,
            ),
            patch(
                "air_marshall.monitor.__main__.AutomationHatFanReader",
                mock_fan_reader_cls,
            ),
            patch(
                "air_marshall.monitor.__main__.AirMarshallClient",
                mock_client_cls,
            ),
            patch(
                "air_marshall.monitor.__main__.MonitorPublisher",
                mock_publisher_cls,
            ),
            patch(
                "air_marshall.monitor.__main__.OpenMeteoReader",
                mock_weather_reader_cls,
            ),
            patch(
                "air_marshall.monitor.__main__.zipcodes.matching",
                return_value=zipcodes_result,
            ),
            patch(
                "air_marshall.monitor.__main__.asyncio.run",
                _asyncio_run,
            ),
        ):
            from air_marshall.monitor.__main__ import main

            main()

        return (
            mock_humidity_reader_cls,
            mock_fan_reader_cls,
            mock_publisher_cls,
            mock_publisher_instance,
            mock_weather_reader_cls,
            mock_client_cls,
        )

    def test_publish_humidity_creates_humidity_reader(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--publish humidity creates an SHT45Reader but not an AutomationHatFanReader."""
        humidity_cls, fan_cls, _, _, weather_cls, _ = self._run_main(
            monkeypatch,
            ["cmd", "--publish", "humidity", "--humidity-name", "living-room"],
        )
        humidity_cls.assert_called_once()
        fan_cls.assert_not_called()
        weather_cls.assert_not_called()

    def test_publish_fan_creates_fan_reader(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--publish fan creates an AutomationHatFanReader but not an SHT45Reader."""
        humidity_cls, fan_cls, _, _, weather_cls, _ = self._run_main(
            monkeypatch,
            ["cmd", "--publish", "fan", "--fan-input", "1"],
        )
        fan_cls.assert_called_once()
        humidity_cls.assert_not_called()
        weather_cls.assert_not_called()

    def test_publish_humidity_fan_creates_both_readers(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--publish humidity fan creates both an SHT45Reader and AutomationHatFanReader."""
        humidity_cls, fan_cls, _, _, weather_cls, _ = self._run_main(
            monkeypatch,
            [
                "cmd",
                "--publish",
                "humidity",
                "fan",
                "--humidity-name",
                "living-room",
                "--fan-input",
                "1",
            ],
        )
        humidity_cls.assert_called_once()
        fan_cls.assert_called_once()
        weather_cls.assert_not_called()

    def test_publish_weather_creates_weather_reader_only(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--publish weather creates an OpenMeteoReader and no hardware readers."""
        humidity_cls, fan_cls, publisher_cls, _, weather_cls, _ = self._run_main(
            monkeypatch,
            ["cmd", "--publish", "weather"],
        )
        weather_cls.assert_called_once()
        humidity_cls.assert_not_called()
        fan_cls.assert_not_called()
        _, kwargs = publisher_cls.call_args
        assert kwargs["humidity_reader"] is None
        assert kwargs["fan_reader"] is None

    def test_publish_humidity_fan_weather_creates_all_readers(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--publish humidity fan weather creates all three readers."""
        humidity_cls, fan_cls, _, _, weather_cls, _ = self._run_main(
            monkeypatch,
            [
                "cmd",
                "--publish",
                "humidity",
                "fan",
                "weather",
                "--humidity-name",
                "s1",
                "--fan-input",
                "1",
            ],
        )
        humidity_cls.assert_called_once()
        fan_cls.assert_called_once()
        weather_cls.assert_called_once()

    def test_publish_humidity_does_not_call_zipcodes(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--publish humidity does not call zipcodes.matching."""
        monkeypatch.setenv("AIR_MARSHALL_BASE_URL", "http://pi:8000")
        monkeypatch.setenv("AIR_MARSHALL_API_KEY", "secret")
        monkeypatch.setattr(
            sys, "argv", ["cmd", "--publish", "humidity", "--humidity-name", "s1"]
        )

        mock_zipcodes = MagicMock()

        mock_publisher_instance = MagicMock()
        mock_publisher_instance.run = AsyncMock()
        mock_publisher_cls = MagicMock(return_value=mock_publisher_instance)

        with (
            patch("air_marshall.monitor.__main__.SHT45Reader"),
            patch("air_marshall.monitor.__main__.AirMarshallClient"),
            patch("air_marshall.monitor.__main__.MonitorPublisher", mock_publisher_cls),
            patch("air_marshall.monitor.__main__.OpenMeteoReader"),
            patch("zipcodes.matching", mock_zipcodes),
            patch("air_marshall.monitor.__main__.asyncio.run", _asyncio_run),
        ):
            from air_marshall.monitor.__main__ import main

            main()

        mock_zipcodes.assert_not_called()

    def test_fan_input_passed_to_fan_reader(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--fan-input is forwarded as input_number to AutomationHatFanReader."""
        _, fan_cls, *_ = self._run_main(
            monkeypatch,
            ["cmd", "--publish", "fan", "--fan-input", "2"],
        )
        _, kwargs = fan_cls.call_args
        assert kwargs["input_number"] == 2

    def test_humidity_name_passed_to_humidity_reader(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--humidity-name is forwarded as sensor_id to SHT45Reader."""
        humidity_cls, *_ = self._run_main(
            monkeypatch,
            ["cmd", "--publish", "humidity", "--humidity-name", "bedroom"],
        )
        _, kwargs = humidity_cls.call_args
        assert kwargs["sensor_id"] == "bedroom"

    def test_default_interval_used(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """run() is called with the default interval when --sensor-interval is omitted."""
        _, _, _, publisher_instance, _, _ = self._run_main(
            monkeypatch,
            ["cmd", "--publish", "humidity", "--humidity-name", "s1"],
        )
        _, kwargs = publisher_instance.run.call_args
        assert kwargs["sensor_interval"] == 30.0

    def test_custom_interval(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """run() is called with the interval provided via --sensor-interval."""
        _, _, _, publisher_instance, _, _ = self._run_main(
            monkeypatch,
            [
                "cmd",
                "--publish",
                "humidity",
                "--humidity-name",
                "s1",
                "--sensor-interval",
                "10",
            ],
        )
        _, kwargs = publisher_instance.run.call_args
        assert kwargs["sensor_interval"] == 10.0

    def test_humidity_port_passed_to_humidity_reader(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--humidity-port is forwarded as port to SHT45Reader."""
        humidity_cls, *_ = self._run_main(
            monkeypatch,
            [
                "cmd",
                "--publish",
                "humidity",
                "--humidity-name",
                "s1",
                "--humidity-port",
                "/dev/ttyACM1",
            ],
        )
        _, kwargs = humidity_cls.call_args
        assert kwargs["port"] == "/dev/ttyACM1"

    def test_client_constructed_with_env_vars(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AirMarshallClient receives base_url and api_key from environment."""
        *_, client_cls = self._run_main(
            monkeypatch,
            ["cmd", "--publish", "humidity", "--humidity-name", "s1"],
        )
        _, kwargs = client_cls.call_args
        assert kwargs["base_url"] == "http://pi:8000"
        assert kwargs["api_key"] == "secret"

    def test_keyboard_interrupt_handled_gracefully(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """KeyboardInterrupt during publisher.run does not propagate."""
        monkeypatch.setenv("AIR_MARSHALL_BASE_URL", "http://pi:8000")
        monkeypatch.setenv("AIR_MARSHALL_API_KEY", "secret")
        monkeypatch.setattr(
            sys, "argv", ["cmd", "--publish", "humidity", "--humidity-name", "s1"]
        )

        mock_publisher_instance = MagicMock()
        mock_publisher_instance.run = AsyncMock(side_effect=KeyboardInterrupt)
        mock_publisher_cls = MagicMock(return_value=mock_publisher_instance)

        with (
            patch("air_marshall.monitor.__main__.SHT45Reader"),
            patch("air_marshall.monitor.__main__.AirMarshallClient"),
            patch("air_marshall.monitor.__main__.MonitorPublisher", mock_publisher_cls),
            patch("air_marshall.monitor.__main__.OpenMeteoReader"),
            patch(
                "air_marshall.monitor.__main__.zipcodes.matching",
                return_value=_VALID_ZIP_MATCH,
            ),
            patch(
                "air_marshall.monitor.__main__.asyncio.run",
                _asyncio_run,
            ),
        ):
            from air_marshall.monitor.__main__ import main

            # Should not raise
            main()


class TestWeatherArgs:
    """Tests for main() weather-related CLI arguments."""

    def _run_main(
        self,
        monkeypatch: pytest.MonkeyPatch,
        argv: list[str],
        zipcodes_result: list[dict[str, str]] = _VALID_ZIP_MATCH,
    ) -> tuple[MagicMock, MagicMock, MagicMock]:
        monkeypatch.setenv("AIR_MARSHALL_BASE_URL", "http://pi:8000")
        monkeypatch.setenv("AIR_MARSHALL_API_KEY", "secret")
        monkeypatch.setattr(sys, "argv", argv)

        mock_weather_reader_cls = MagicMock()
        mock_weather_reader_cls.return_value.close = AsyncMock()
        mock_publisher_cls = MagicMock()
        mock_publisher_instance = MagicMock()
        mock_publisher_instance.run = AsyncMock()
        mock_publisher_cls.return_value = mock_publisher_instance

        with (
            patch("air_marshall.monitor.__main__.SHT45Reader"),
            patch("air_marshall.monitor.__main__.AutomationHatFanReader"),
            patch("air_marshall.monitor.__main__.AirMarshallClient"),
            patch(
                "air_marshall.monitor.__main__.OpenMeteoReader",
                mock_weather_reader_cls,
            ),
            patch(
                "air_marshall.monitor.__main__.MonitorPublisher",
                mock_publisher_cls,
            ),
            patch(
                "air_marshall.monitor.__main__.zipcodes.matching",
                return_value=zipcodes_result,
            ),
            patch("air_marshall.monitor.__main__.asyncio.run", _asyncio_run),
        ):
            from air_marshall.monitor.__main__ import main

            main()

        return mock_weather_reader_cls, mock_publisher_cls, mock_publisher_instance

    def test_publish_weather_creates_weather_reader(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--publish weather creates an OpenMeteoReader using the default zip."""
        weather_cls, _, _ = self._run_main(monkeypatch, ["cmd", "--publish", "weather"])
        weather_cls.assert_called_once()

    def test_weather_zip_creates_weather_reader_with_correct_coords(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--weather-zip resolves to lat/lon and constructs an OpenMeteoReader."""
        weather_cls, _, _ = self._run_main(
            monkeypatch,
            ["cmd", "--publish", "weather", "--weather-zip", "80919"],
        )
        weather_cls.assert_called_once()
        _, kwargs = weather_cls.call_args
        assert kwargs["latitude"] == 39.0
        assert kwargs["longitude"] == -104.9

    def test_weather_zip_default_sensor_id_is_outdoor(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--publish weather without --weather-name defaults sensor_id to 'outdoor'."""
        weather_cls, _, _ = self._run_main(
            monkeypatch, ["cmd", "--publish", "weather", "--weather-zip", "80919"]
        )
        _, kwargs = weather_cls.call_args
        assert kwargs["sensor_id"] == "outdoor"

    def test_weather_name_overrides_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--weather-name overrides the default 'outdoor' sensor_id."""
        weather_cls, _, _ = self._run_main(
            monkeypatch,
            [
                "cmd",
                "--publish",
                "weather",
                "--weather-zip",
                "80919",
                "--weather-name",
                "backyard",
            ],
        )
        _, kwargs = weather_cls.call_args
        assert kwargs["sensor_id"] == "backyard"

    def test_weather_interval_passed_to_run(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--weather-interval is forwarded to publisher.run()."""
        _, _, publisher_instance = self._run_main(
            monkeypatch,
            [
                "cmd",
                "--publish",
                "weather",
                "--weather-zip",
                "80919",
                "--weather-interval",
                "600",
            ],
        )
        _, kwargs = publisher_instance.run.call_args
        assert kwargs["weather_interval"] == 600.0

    def test_default_weather_interval_used(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """run() is called with the default weather_interval when --weather-interval is omitted."""
        _, _, publisher_instance = self._run_main(
            monkeypatch, ["cmd", "--publish", "weather"]
        )
        _, kwargs = publisher_instance.run.call_args
        assert kwargs["weather_interval"] == 300.0

    def test_unknown_zip_exits_with_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--weather-zip with an unrecognised zip code exits non-zero when publishing weather."""
        monkeypatch.setenv("AIR_MARSHALL_BASE_URL", "http://pi:8000")
        monkeypatch.setenv("AIR_MARSHALL_API_KEY", "secret")
        monkeypatch.setattr(
            sys, "argv", ["cmd", "--publish", "weather", "--weather-zip", "99999"]
        )

        with (
            patch("air_marshall.monitor.__main__.SHT45Reader"),
            patch("air_marshall.monitor.__main__.AirMarshallClient"),
            patch("air_marshall.monitor.__main__.MonitorPublisher"),
            patch(
                "air_marshall.monitor.__main__.zipcodes.matching",
                return_value=[],
            ),
        ):
            from air_marshall.monitor.__main__ import main

            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code != 0
