"""Tests for utility modules."""

import pytest
from wrkmon.utils.stealth import StealthManager


class TestStealthManager:
    """Tests for StealthManager."""

    def test_get_fake_process_name(self):
        stealth = StealthManager()

        # Normal title
        name = stealth.get_fake_process_name("Lofi Hip Hop Beats")
        assert name == "lofi-hip-hop-beats"

        # Title with special characters
        name = stealth.get_fake_process_name("Track [Official Video] (HD)")
        assert "-" in name
        assert "[" not in name
        assert "]" not in name

        # Long title should be truncated
        name = stealth.get_fake_process_name("A" * 50)
        assert len(name) <= 30

    def test_get_fake_pid(self):
        stealth = StealthManager()
        pid = stealth.get_fake_pid()
        assert 1000 <= pid <= 65535

    def test_get_fake_stats(self):
        stealth = StealthManager()

        cpu = stealth.get_fake_cpu()
        assert stealth.CPU_RANGE[0] <= cpu <= stealth.CPU_RANGE[1]

        mem = stealth.get_fake_memory()
        assert stealth.MEM_RANGE[0] <= mem <= stealth.MEM_RANGE[1]

    def test_format_status(self):
        stealth = StealthManager()

        assert stealth.format_status("playing") == "RUNNING"
        assert stealth.format_status("paused") == "SUSPENDED"
        assert stealth.format_status("stopped") == "STOPPED"
        assert stealth.format_status("unknown") == "UNKNOWN"

    def test_format_duration(self):
        stealth = StealthManager()

        assert stealth.format_duration(0) == "0:00"
        assert stealth.format_duration(65) == "1:05"
        assert stealth.format_duration(3661) == "1:01:01"
        assert stealth.format_duration(-1) == "--:--"

    def test_get_mpv_args(self):
        stealth = StealthManager()
        args = stealth.get_mpv_args()

        assert "--no-video" in args
        assert "--idle=yes" in args
        assert any("input-ipc-server" in arg for arg in args)
