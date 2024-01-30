# Copyright(c) 2024 Samsung SDS
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
from collections import deque
from unittest import mock

from kubernetes import client
from kubernetes.client import V1Node
from kubernetes.client import V1NodeCondition
from kubernetes.client import V1NodeList
from kubernetes.client import V1NodeStatus
from kubernetes.client import V1ObjectMeta
from kubernetes import config

from oslo_config import fixture as fixture_config

import testtools

import masakarimonitors.conf
from masakarimonitors.ha import masakari
from masakarimonitors.hostmonitor.kubernetes_check import manager

CONF = masakarimonitors.conf.CONF


class TestKubernetesCheck(testtools.TestCase):

    @mock.patch.object(config, 'load_incluster_config')
    @mock.patch.object(client, 'CoreV1Api')
    def setUp(self, mock_core_v1_api, mock_load_incluster_config):
        super(TestKubernetesCheck, self).setUp()
        self.CONF = self.useFixture(fixture_config.Config()).conf
        self.CONF.kubernetes.monitoring_node_labels = \
            'openstack-compute-node=enabled'
        self.host_monitor = manager.KubernetesCheck()
        self.host_monitor.monitoring_samples = 1
        self.host_monitor.monitoring_data = {}
        self.last_status = {}

    def test_update_monitoring_data(self):
        mock_list_node = V1NodeList(
            items=[
                V1Node(
                    metadata=V1ObjectMeta(
                        name="node0" + str(num),
                        labels={
                            "openstack-compute-node": "enabled"
                        }
                    ),
                    status=V1NodeStatus(conditions=[
                        V1NodeCondition(status="False", type="MemoryPressure"),
                        V1NodeCondition(status="False", type="DiskPressure"),
                        V1NodeCondition(status="False", type="PIDPressure"),
                        V1NodeCondition(status="True", type="Ready")
                    ])
                )
                for num in range(1, 4)
            ]
        )

        with mock.patch.object(self.host_monitor.kube_client, 'list_node',
                               return_value=mock_list_node):
            self.host_monitor.update_monitoring_data()
            excepted_monitoring_data = {
                "node01": deque(['True'],
                                maxlen=self.host_monitor.monitoring_samples),
                "node02": deque(['True'],
                                maxlen=self.host_monitor.monitoring_samples),
                "node03": deque(['True'],
                                maxlen=self.host_monitor.monitoring_samples)
            }
        self.assertEqual(excepted_monitoring_data,
                         self.host_monitor.monitoring_data)

    def test_update_monitoring_data_exclude_node(self):

        mock_list_node = V1NodeList(
            items=[
                V1Node(
                    metadata=V1ObjectMeta(
                        name="node0" + str(num),
                        labels={
                            "openstack-compute-node": "enabled",
                            "monitoring": "enabled"
                        }
                    ),
                    status=V1NodeStatus(conditions=[
                        V1NodeCondition(status="False", type="MemoryPressure"),
                        V1NodeCondition(status="False", type="DiskPressure"),
                        V1NodeCondition(status="False", type="PIDPressure"),
                        V1NodeCondition(status="True", type="Ready")
                    ])
                )
                for num in range(1, 4)
            ]
        )

        with mock.patch.object(self.host_monitor.kube_client, 'list_node',
                               return_value=mock_list_node):
            self.host_monitor.update_monitoring_data()

            mock_list_node.items.pop()

            self.host_monitor.update_monitoring_data()
            excepted_monitoring_data = {
                "node01": deque(['True', 'True'],
                                maxlen=self.host_monitor.monitoring_samples),
                "node02": deque(['True', 'True'],
                                maxlen=self.host_monitor.monitoring_samples)
            }

        self.assertEqual(2, len(self.host_monitor.monitoring_data))
        self.assertEqual(excepted_monitoring_data,
                         self.host_monitor.monitoring_data)

    @mock.patch.object(masakari.SendNotification, 'send_notification')
    def test_poll_hosts_with_healthy_nodes(self, mock_send_notification):
        self.host_monitor.monitoring_data = {
            "node01": deque(['True'],
                            maxlen=self.host_monitor.monitoring_samples),
            "node02": deque(['True'],
                            maxlen=self.host_monitor.monitoring_samples),
            "node03": deque(['True'],
                            maxlen=self.host_monitor.monitoring_samples),
        }

        self.host_monitor.poll_hosts()
        mock_send_notification.assert_not_called()

    @mock.patch.object(masakari.SendNotification, 'send_notification')
    def test_poll_hosts_with_healthy_nodes_3samples(
            self, mock_send_notification):
        self.host_monitor.monitoring_samples = 3
        self.host_monitor.monitoring_data = {
            "node01": deque(['True', 'True', 'True'],
                            maxlen=self.host_monitor.monitoring_samples),
            "node02": deque(['Unknown', 'True', 'True'],
                            maxlen=self.host_monitor.monitoring_samples),
            "node03": deque(['True', 'Unknown', 'Unknown'],
                            maxlen=self.host_monitor.monitoring_samples),
        }

        self.host_monitor.poll_hosts()
        mock_send_notification.assert_not_called()

    @mock.patch.object(masakari.SendNotification, 'send_notification')
    @mock.patch.object(manager.KubernetesCheck, '_event')
    def test_poll_hosts_with_unhealthy_node(self, mock_event,
                                            mock_send_notification):
        self.host_monitor.last_status = {
            "node01": True,
            "node02": True,
            "node03": True
        }
        self.host_monitor.monitoring_samples = 3
        self.host_monitor.monitoring_data = {
            "node01": deque(['True', 'True', 'True'],
                            maxlen=self.host_monitor.monitoring_samples),
            "node02": deque(['Unknown', 'Unknown', 'Unknown'],
                            maxlen=self.host_monitor.monitoring_samples),
            "node03": deque(['Unknown', 'True', 'Unknown'],
                            maxlen=self.host_monitor.monitoring_samples),
        }

        test_event = {'notification': 'test'}
        mock_event.return_value = test_event

        self.host_monitor.poll_hosts()
        mock_send_notification.assert_called_once_with(
            CONF.host.api_retry_max, CONF.host.api_retry_interval, test_event)

    @mock.patch.object(masakari.SendNotification, 'send_notification')
    def test_poll_hosts_with_having_less_healthy_history_than_samples(
            self, mock_send_notification):
        self.host_monitor.monitoring_samples = 3
        self.host_monitor.monitoring_data = {
            "node01": deque(['True', 'True'],
                            maxlen=self.host_monitor.monitoring_samples),
            "node02": deque(['True', 'Unknown'],
                            maxlen=self.host_monitor.monitoring_samples),
            "node03": deque(['Unknown', 'Unknown'],
                            maxlen=self.host_monitor.monitoring_samples),
        }

        self.host_monitor.poll_hosts()
        mock_send_notification.assert_not_called()
