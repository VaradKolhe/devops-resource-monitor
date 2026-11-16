"""Dependency-light unit tests for metric collection and formatting."""

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock


def load_app_module():
    """Load app.py with UI/data packages stubbed when they are not installed."""
    psutil = types.ModuleType("psutil")
    psutil.cpu_percent = Mock(return_value=12.5)
    psutil.virtual_memory = Mock(return_value=types.SimpleNamespace(percent=50.0, available=1024, total=2048))
    psutil.disk_usage = Mock(return_value=types.SimpleNamespace(percent=25.0, free=512, total=2048))
    psutil.boot_time = Mock(return_value=1_700_000_000)
    psutil.cpu_count = Mock(return_value=4)
    psutil.Error = type("PsutilError", (Exception,), {})
    streamlit = types.ModuleType("streamlit")
    streamlit.session_state = {}
    streamlit.set_page_config = Mock()
    streamlit.fragment = None
    pandas = types.ModuleType("pandas")
    plotly = types.ModuleType("plotly")
    plotly.express = types.SimpleNamespace()
    sys.modules.update({"psutil": psutil, "streamlit": streamlit, "pandas": pandas, "plotly": plotly,
                       "plotly.express": plotly.express})
    spec = importlib.util.spec_from_file_location("app_under_test", Path(__file__).parents[1] / "app.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, psutil


class MetricsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app, cls.psutil = load_app_module()

    def test_collect_metrics_returns_live_api_values(self):
        metrics = self.app.collect_metrics()
        self.assertEqual(metrics["cpu_percent"], 12.5)
        self.assertEqual(metrics["memory_available"], 1024)
        self.assertEqual(metrics["disk_free"], 512)
        self.assertEqual(metrics["cpu_count"], 4)
        self.assertIsNotNone(metrics["timestamp"])

    def test_unavailable_metric_becomes_none(self):
        self.psutil.virtual_memory.side_effect = OSError("not available")
        metrics = self.app.collect_metrics()
        self.assertIsNone(metrics["memory_percent"])
        self.assertIsNone(metrics["memory_available"])
        self.psutil.virtual_memory.side_effect = None
        self.psutil.virtual_memory.return_value = types.SimpleNamespace(percent=50.0, available=1024, total=2048)

    def test_formatters_handle_values_and_missing_data(self):
        self.assertEqual(self.app._format_bytes(1024), "1.0 KB")
        self.assertEqual(self.app._format_bytes(None), "Unavailable")
        self.assertEqual(self.app._metric_label(None), "Unavailable")
        self.assertEqual(self.app._metric_label(12.34), "12.3%")


if __name__ == "__main__":
    unittest.main()
