from unittest.mock import MagicMock

import pytest

from get_resources_info.get_cpu_info import GetCPUInfo


@pytest.fixture
def process_cache():
    return {}


@pytest.fixture
def cpu_info(process_cache):
    return GetCPUInfo(process_cache)


def test_get_process_cpu_usage_primes_on_first_call(cpu_info, process_cache):
    mock_process = MagicMock()
    mock_process.is_running.return_value = True
    mock_process.status.return_value = "running"

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "get_resources_info.get_cpu_info.psutil.Process",
            lambda pid: mock_process,
        )

        first_reading = cpu_info.get_process_cpu_usage(1234)
        second_reading = cpu_info.get_process_cpu_usage(1234)

    mock_process.cpu_percent.assert_any_call(interval=None)
    assert first_reading == {"process_cpu_usage": 0.0}
    assert second_reading == {"process_cpu_usage": mock_process.cpu_percent.return_value}
    assert process_cache["1234_cpu_primed"] is True


def test_get_process_cpu_usage_reuses_cached_process(cpu_info, process_cache):
    mock_process = MagicMock()
    mock_process.is_running.return_value = True
    mock_process.status.return_value = "running"
    process_cache[999] = mock_process
    process_cache["999_cpu_primed"] = True
    mock_process.cpu_percent.return_value = 42.5

    result = cpu_info.get_process_cpu_usage(999)

    assert result == {"process_cpu_usage": 42.5}
    mock_process.cpu_percent.assert_called_once_with(interval=None)
