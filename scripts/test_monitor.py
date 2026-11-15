import unittest
from monitor import alerts_for


class MonitoringTest(unittest.TestCase):
    def test_queue_failure_and_backup_gap_raise_alerts(self):
        metrics = {'api_ready': True, 'gateway_connected': True, 'worker_present': True,
                   'backup_recent': False, 'pending_count': 20, 'dead_letters': 1}
        self.assertEqual(['pending_count', 'dead_letters', 'backup_recent'],
                         alerts_for(metrics, {'pending_count': 10, 'dead_letters': 0}))

    def test_healthy_snapshot_has_no_alert(self):
        metrics = {name: True for name in ('api_ready', 'gateway_connected', 'worker_present', 'backup_recent')}
        self.assertEqual([], alerts_for(metrics, {'pending_count': 100}))


if __name__ == '__main__':
    unittest.main()
