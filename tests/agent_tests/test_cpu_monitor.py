import unittest
from unittest.mock import patch
from collections import namedtuple # Added for mocking psutil.cpu_times_percent return
import server_monitor.agent.cpu.cpu_monitor as cpu_monitor

class TestCPUMonitor(unittest.TestCase):

    @patch("psutil.cpu_percent")
    def test_get_cpu_usage_per_core(self, mock_cpu_percent):
        mock_cpu_percent.return_value = [10.5, 20.3, 30.2]
        result = cpu_monitor.get_cpu_usage_per_core()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)
        for val in result:
            self.assertIsInstance(val, float)
        mock_cpu_percent.assert_called_once_with(percpu=True)

    @patch("psutil.cpu_percent")
    def test_get_cpu_usage_average(self, mock_cpu_percent):
        mock_cpu_percent.return_value = 25.5
        result = cpu_monitor.get_cpu_usage_average()
        self.assertIsInstance(result, float)
        self.assertEqual(result, 25.5)
        mock_cpu_percent.assert_called_once_with(percpu=False)

    @patch("psutil.getloadavg")
    def test_get_load_average_unix(self, mock_getloadavg):
        mock_getloadavg.return_value = (0.5, 1.0, 1.5)
        result = cpu_monitor.get_load_average()
        self.assertIsInstance(result, dict)
        expected_result = {
            "load_1_min": 0.5,
            "load_5_min": 1.0,
            "load_15_min": 1.5,
        }
        self.assertEqual(result, expected_result)

    @patch("psutil.getloadavg", side_effect=AttributeError("Not available"))
    def test_get_load_average_non_unix(self, mock_getloadavg_attr_error):
        result = cpu_monitor.get_load_average()
        expected_result = {
            "load_1_min": -1.0,
            "load_5_min": -1.0,
            "load_15_min": -1.0,
        }
        self.assertEqual(result, expected_result)

    @patch("psutil.getloadavg", side_effect=NotImplementedError("Not available"))
    def test_get_load_average_not_implemented(self, mock_getloadavg_not_implemented):
        result = cpu_monitor.get_load_average()
        expected_result = {
            "load_1_min": -1.0,
            "load_5_min": -1.0,
            "load_15_min": -1.0,
        }
        self.assertEqual(result, expected_result)

    @patch("psutil.cpu_times_percent")
    def test_get_cpu_times_percent(self, mock_psutil_cpu_times_percent):
        # Test case 1: psutil returns a namedtuple with a subset of fields
        MockCPUTimesPartial = namedtuple('MockCPUTimesPartial', ['user', 'system', 'idle', 'iowait'])
        mock_psutil_cpu_times_percent.return_value = MockCPUTimesPartial(
            user=10.0, system=5.0, idle=80.0, iowait=2.5
        )
        
        result_partial = cpu_monitor.get_cpu_times_percent()
        self.assertIsInstance(result_partial, dict)
        
        expected_partial_result = {
            "user": 10.0,
            "system": 5.0,
            "idle": 80.0,
            "nice": 0.0,  # Defaulted
            "iowait": 2.5,
            "irq": 0.0,   # Defaulted
            "softirq": 0.0, # Defaulted
            "steal": 0.0, # Defaulted
            "guest": 0.0, # Defaulted
            "guest_nice": 0.0 # Defaulted
        }
        self.assertEqual(result_partial, expected_partial_result)

        # Test case 2: psutil returns a namedtuple with all expected fields
        MockCPUTimesFull = namedtuple('MockCPUTimesFull', [
            'user', 'system', 'idle', 'nice', 'iowait', 
            'irq', 'softirq', 'steal', 'guest', 'guest_nice'
        ])
        mock_psutil_cpu_times_percent.return_value = MockCPUTimesFull(
            user=1.0, system=2.0, idle=3.0, nice=4.0, iowait=5.0,
            irq=6.0, softirq=7.0, steal=8.0, guest=9.0, guest_nice=10.0
        )
        result_full = cpu_monitor.get_cpu_times_percent()
        self.assertIsInstance(result_full, dict)
        expected_full_result = {
            "user": 1.0, "system": 2.0, "idle": 3.0, "nice": 4.0, "iowait": 5.0,
            "irq": 6.0, "softirq": 7.0, "steal": 8.0, "guest": 9.0, "guest_nice": 10.0
        }
        self.assertEqual(result_full, expected_full_result)


    @patch("server_monitor.agent.cpu.cpu_monitor.get_cpu_usage_per_core")
    @patch("server_monitor.agent.cpu.cpu_monitor.get_cpu_usage_average")
    @patch("server_monitor.agent.cpu.cpu_monitor.get_load_average")
    @patch("server_monitor.agent.cpu.cpu_monitor.get_cpu_times_percent") # New mock
    def test_collect_cpu_metrics(self, mock_cpu_times, mock_load, mock_avg, mock_core): # mock_cpu_times added
        mock_core.return_value = [12.0, 34.0]
        mock_avg.return_value = 23.0
        
        expected_load_average = {"load_1_min": 0.9, "load_5_min": 1.2, "load_15_min": 1.5}
        mock_load.return_value = expected_load_average
        
        expected_cpu_times = {
            "user": 10.0, "system": 5.0, "idle": 80.0, "nice": 0.0, "iowait": 2.5,
            "irq": 0.0, "softirq": 0.0, "steal": 0.0, "guest": 0.0, "guest_nice": 0.0
        }
        mock_cpu_times.return_value = expected_cpu_times # Set return for the new mock

        # Mock time.time() for consistent timestamp
        with patch("time.time", return_value=1234567890.0):
            result = cpu_monitor.collect_cpu_metrics()

        self.assertIn("timestamp", result)
        self.assertEqual(result["timestamp"], 1234567890.0)
        self.assertIn("cpu_usage_per_core", result)
        self.assertIn("cpu_usage_average", result)
        self.assertIn("load_average", result)
        self.assertIn("cpu_times_percent", result) # New assertion

        self.assertEqual(result["cpu_usage_per_core"], [12.0, 34.0])
        self.assertEqual(result["cpu_usage_average"], 23.0)
        self.assertEqual(result["load_average"], expected_load_average)
        self.assertEqual(result["cpu_times_percent"], expected_cpu_times) # New assertion

if __name__ == "__main__":
    unittest.main()
