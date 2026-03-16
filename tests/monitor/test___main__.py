"""Tests for air_marshall.monitor.__main__."""

import asyncio as _asyncio
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _close_coro(coro: object) -> None:
    """Prevent 'coroutine never awaited' warning in sync test helpers."""
    if _asyncio.iscoroutine(coro):
        coro.close()  # type: ignore[union-attr]


class TestMissingEnvVars:
    """Tests for main() with missing environment variables."""

    def test_missing_base_url_exits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """main() exits non-zero when AIR_MARSHALL_BASE_URL is not set."""
        monkeypatch.delenv("AIR_MARSHALL_BASE_URL", raising=False)
        monkeypatch.delenv("AIR_MARSHALL_API_KEY", raising=False)
        monkeypatch.setattr(
            sys, "argv", ["cmd", "--publish", "humidity", "--name", "s1"]
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
            sys, "argv", ["cmd", "--publish", "humidity", "--name", "s1"]
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
            sys, "argv", ["cmd", "--publish", "invalid", "--name", "s1"]
        )
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
        monkeypatch.setattr(sys, "argv", ["cmd", "--publish", "fan", "--name", "s1"])
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
    ) -> tuple[MagicMock, MagicMock, MagicMock, MagicMock]:
        monkeypatch.setenv("AIR_MARSHALL_BASE_URL", "http://pi:8000")
        monkeypatch.setenv("AIR_MARSHALL_API_KEY", "secret")
        monkeypatch.setattr(sys, "argv", argv)

        mock_humidity_reader_cls = MagicMock()
        mock_fan_reader_cls = MagicMock()
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
                "air_marshall.monitor.__main__.asyncio.run",
                _close_coro,
            ),
        ):
            from air_marshall.monitor.__main__ import main

            main()

        return (
            mock_humidity_reader_cls,
            mock_fan_reader_cls,
            mock_publisher_cls,
            mock_publisher_instance,
        )

    def test_publish_humidity_creates_humidity_reader(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--publish humidity creates an SHT45Reader but not an AutomationHatFanReader."""
        humidity_cls, fan_cls, _, _ = self._run_main(
            monkeypatch,
            ["cmd", "--publish", "humidity", "--name", "living-room"],
        )
        humidity_cls.assert_called_once()
        fan_cls.assert_not_called()

    def test_publish_fan_creates_fan_reader(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--publish fan creates an AutomationHatFanReader but not an SHT45Reader."""
        humidity_cls, fan_cls, _, _ = self._run_main(
            monkeypatch,
            ["cmd", "--publish", "fan", "--name", "living-room", "--fan-input", "1"],
        )
        fan_cls.assert_called_once()
        humidity_cls.assert_not_called()

    def test_publish_both_creates_both_readers(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--publish both creates both an SHT45Reader and AutomationHatFanReader."""
        humidity_cls, fan_cls, _, _ = self._run_main(
            monkeypatch,
            ["cmd", "--publish", "both", "--name", "living-room", "--fan-input", "1"],
        )
        humidity_cls.assert_called_once()
        fan_cls.assert_called_once()

    def test_fan_input_passed_to_fan_reader(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--fan-input is forwarded as input_number to AutomationHatFanReader."""
        _, fan_cls, _, _ = self._run_main(
            monkeypatch,
            ["cmd", "--publish", "fan", "--name", "s1", "--fan-input", "2"],
        )
        _, kwargs = fan_cls.call_args
        assert kwargs["input_number"] == 2

    def test_sensor_name_passed_to_humidity_reader(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--name is forwarded as sensor_id to SHT45Reader."""
        humidity_cls, _, _, _ = self._run_main(
            monkeypatch,
            ["cmd", "--publish", "humidity", "--name", "bedroom"],
        )
        _, kwargs = humidity_cls.call_args
        assert kwargs["sensor_id"] == "bedroom"

    def test_default_interval_used(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """run() is called with the default interval when --interval is omitted."""
        _, _, _, publisher_instance = self._run_main(
            monkeypatch,
            ["cmd", "--publish", "humidity", "--name", "s1"],
        )
        _, kwargs = publisher_instance.run.call_args
        assert kwargs["interval"] == 30.0

    def test_custom_interval(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """run() is called with the interval provided via --interval."""
        _, _, _, publisher_instance = self._run_main(
            monkeypatch,
            ["cmd", "--publish", "humidity", "--name", "s1", "--interval", "30"],
        )
        _, kwargs = publisher_instance.run.call_args
        assert kwargs["interval"] == 30.0

    def test_keyboard_interrupt_handled_gracefully(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """KeyboardInterrupt during asyncio.run does not propagate."""
        monkeypatch.setenv("AIR_MARSHALL_BASE_URL", "http://pi:8000")
        monkeypatch.setenv("AIR_MARSHALL_API_KEY", "secret")
        monkeypatch.setattr(
            sys, "argv", ["cmd", "--publish", "humidity", "--name", "s1"]
        )

        with (
            patch("air_marshall.monitor.__main__.SHT45Reader"),
            patch("air_marshall.monitor.__main__.AirMarshallClient"),
            patch("air_marshall.monitor.__main__.MonitorPublisher"),
            patch(
                "air_marshall.monitor.__main__.asyncio.run",
                side_effect=KeyboardInterrupt,
            ),
        ):
            from air_marshall.monitor.__main__ import main

            # Should not raise
            main()
