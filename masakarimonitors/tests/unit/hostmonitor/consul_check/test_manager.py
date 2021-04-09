# Copyright(c) 2021 Inspur
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import testtools
from unittest import mock

from collections import deque
import eventlet
from oslo_config import fixture as fixture_config

import masakarimonitors.conf
from masakarimonitors.ha import masakari
from masakarimonitors.hostmonitor.consul_check import consul_helper
from masakarimonitors.hostmonitor.consul_check import manager
from masakarimonitors.hostmonitor.consul_check import matrix_helper

eventlet.monkey_patch(os=False)

CONF = masakarimonitors.conf.CONF


class TestConsulCheck(testtools.TestCase):

    def setUp(self):
        super(TestConsulCheck, self).setUp()
        self.CONF = self.useFixture(fixture_config.Config()).conf
        self.host_monitor = manager.ConsulCheck()
        self.host_monitor.matrix_manager = \
            matrix_helper.MatrixManager(self.CONF)
        self.host_monitor._matrix = matrix_helper.DEFAULT_MATRIX
        self.host_monitor.consul_manager = \
            consul_helper.ConsulManager(self.CONF)
        self.host_monitor._sequence = ['manage', 'tenant', 'storage']
        self.host_monitor.monitoring_data = {
            "node01": deque([['up', 'up', 'up'],
                             ['up', 'up', 'up'],
                             ['up', 'up', 'up']],
                            maxlen=3),
            "node02": deque([['up', 'up', 'up'],
                             ['up', 'up', 'up'],
                             ['up', 'up', 'down']],
                            maxlen=3),
            "node03": deque([['up', 'up', 'up'],
                             ['down', 'up', 'up'],
                             ['down', 'up', 'up']],
                            maxlen=3),
        }

    def test_update_monitoring_data(self):
        mock_health = {
            'node01': ['up', 'up', 'up'],
            'node02': ['up', 'up', 'up'],
            'node03': ['up', 'up', 'up']
        }

        with mock.patch.object(self.host_monitor.consul_manager, 'get_health',
                return_value=mock_health):
            self.host_monitor.update_monitoring_data()
            excepted_monitoring_data = {
                "node01": deque([['up', 'up', 'up'],
                                 ['up', 'up', 'up'],
                                 ['up', 'up', 'up']],
                                maxlen=3),
                "node02": deque([['up', 'up', 'up'],
                                 ['up', 'up', 'down'],
                                 ['up', 'up', 'up']],
                                maxlen=3),
                "node03": deque([['down', 'up', 'up'],
                                 ['down', 'up', 'up'],
                                 ['up', 'up', 'up']],
                                maxlen=3),
            }
            self.assertEqual(excepted_monitoring_data,
                             self.host_monitor.monitoring_data)

    def test_get_host_statistical_health(self):
        self.assertEqual(['up', 'up', 'up'],
                         self.host_monitor.get_host_health('node01'))
        self.assertEqual(['up', 'up', None],
                         self.host_monitor.get_host_health('node02'))
        self.assertEqual([None, 'up', 'up'],
                         self.host_monitor.get_host_health('node03'))

    def test_host_statistical_health_changed(self):
        self.host_monitor.last_host_health = {
            'node02': ['up', 'up', None],
            'node03': ['up', 'up', 'down']
        }

        self.assertFalse(self.host_monitor._host_health_changed(
            'node01', ['up', 'up', 'up']))
        self.assertTrue(self.host_monitor._host_health_changed(
            'node02', ['up', 'up', 'up']))
        self.assertTrue(self.host_monitor._host_health_changed(
            'node03', ['up', 'up', 'up']))
        last_host_health = {
            'node01': ['up', 'up', 'up'],
            'node02': ['up', 'up', 'up'],
            'node03': ['up', 'up', 'up']
        }
        self.assertEqual(self.host_monitor.last_host_health,
                         last_host_health)

    def test_get_action_from_matrix_by_host_health(self):
        self.assertEqual(
            [],
            self.host_monitor.get_action_from_matrix(['up', 'up', 'up']))
        self.assertEqual(
            ["recovery"],
            self.host_monitor.get_action_from_matrix(['up', 'up', 'down']))
        self.assertEqual(
            [],
            self.host_monitor.get_action_from_matrix(['down', 'up', 'up']))
        self.assertEqual(
            ["recovery"],
            self.host_monitor.get_action_from_matrix(['down', 'down', 'down']))

    @mock.patch.object(masakari.SendNotification, 'send_notification')
    @mock.patch.object(manager.ConsulCheck, '_event')
    def test_poll_hosts(self, mock_event, mock_send_notification):
        self.host_monitor.monitoring_data = {
            "node01": deque([['up', 'up', 'up'],
                             ['up', 'up', 'up'],
                             ['up', 'up', 'up']],
                            maxlen=3),
            "node02": deque([['up', 'up', 'down'],
                             ['up', 'up', 'down'],
                             ['up', 'up', 'down']],
                            maxlen=3),
            "node03": deque([['up', 'up', 'up'],
                             ['up', 'up', 'up'],
                             ['up', 'up', 'up']],
                            maxlen=3),
        }

        self.host_monitor.last_host_health = {
            'node02': ['up', 'up', None],
            'node03': ['up', 'up', 'up']
        }

        test_event = {'notification': 'test'}
        mock_event.return_value = test_event

        self.host_monitor.poll_hosts()
        mock_send_notification.assert_called_once_with(
            CONF.host.api_retry_max, CONF.host.api_retry_interval, test_event)
