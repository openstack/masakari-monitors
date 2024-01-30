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

import eventlet

from kubernetes import client
from kubernetes import config

from oslo_log import log
from oslo_utils import timeutils

import socket

from masakarimonitors import conf
from masakarimonitors.ha import masakari
from masakarimonitors.hostmonitor import driver
from masakarimonitors.objects import event_constants as ec

LOG = log.getLogger(__name__)
CONF = conf.CONF


class KubernetesCheck(driver.DriverBase):
    """Check host status by k8s"""

    def __init__(self):
        super(KubernetesCheck, self).__init__()
        self.hostname = socket.gethostname()
        self.monitoring_interval = CONF.host.monitoring_interval
        self.monitoring_samples = CONF.host.monitoring_samples
        self.notifier = masakari.SendNotification()
        self.monitoring_data = {}
        self.last_status = {}
        self.running = False

        config.load_incluster_config()
        self.kube_client = client.CoreV1Api()

    def update_monitoring_data(self):
        """update monitoring data from k8s"""
        LOG.debug("update monitoring data from k8s.")
        node_list = self.kube_client.list_node(
            label_selector=CONF.kubernetes.monitoring_node_labels
        ).items

        # Remove non-exist node from monitoring_data
        self.monitoring_data = {
            node: status for node, status in self.monitoring_data.items()
            if node in [i.metadata.name for i in node_list]
        }

        for host in node_list:
            hostname = host.metadata.name

            for condition in host.status.conditions:
                if condition.type != "Ready":
                    continue

                host_health_history = self.monitoring_data.get(
                    hostname, deque([], maxlen=self.monitoring_samples))
                host_health_history.appendleft(condition.status)
                LOG.debug("hostname: %s, condition: %s",
                          hostname, host_health_history)

                # Status is 'True' if node is healthy else 'False' or 'unknown'
                # Most up-to-date state is stored in index 0
                self.monitoring_data[hostname] = host_health_history

    @staticmethod
    def _event(host, host_health):
        LOG.info("Host %s needs recovery, health status: %s." %
                 (host, host_health))

        event = {
            'notification': {
                'type': ec.EventConstants.TYPE_COMPUTE_HOST,
                'hostname': host,
                'generated_time': timeutils.utcnow(),
                'payload': {
                    'event': ec.EventConstants.EVENT_STOPPED
                }
            }
        }

        return event

    def poll_hosts(self):
        """poll and check hosts health"""
        for host, health_history in self.monitoring_data.items():
            if not self.last_status:
                self.last_status[host] = self.monitoring_data[host][0]

            if host == self.hostname:
                continue

            if len(health_history) < self.monitoring_samples:
                continue

            is_host_alive = "True" in health_history

            if not is_host_alive and self.last_status.get(host):
                event = self._event(host, is_host_alive)
                self.notifier.send_notification(
                    CONF.host.api_retry_max,
                    CONF.host.api_retry_interval,
                    event)

            self.last_status[host] = is_host_alive

    def stop(self):
        self.running = False

    def monitor_hosts(self):
        self.running = True
        while self.running:
            try:
                self.update_monitoring_data()
                LOG.info("Monitoring data: %s", self.monitoring_data)
                self.poll_hosts()
            except Exception as e:
                LOG.exception("Exception when host-monitor by k8s: %s", e)

            eventlet.greenthread.sleep(self.monitoring_interval)
