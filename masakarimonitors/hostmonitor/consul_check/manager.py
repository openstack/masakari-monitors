# Copyright(c) 2019 Inspur
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

import eventlet
import socket

from collections import deque
from oslo_log import log
from oslo_utils import timeutils

from masakarimonitors import conf
from masakarimonitors.ha import masakari
from masakarimonitors.hostmonitor.consul_check import consul_helper
from masakarimonitors.hostmonitor.consul_check import matrix_helper
from masakarimonitors.hostmonitor import driver
from masakarimonitors.objects import event_constants as ec

LOG = log.getLogger(__name__)
CONF = conf.CONF


class ConsulCheck(driver.DriverBase):
    """Check host status by consul"""

    def __init__(self):
        super(ConsulCheck, self).__init__()
        self.hostname = socket.gethostname()
        self.monitoring_interval = CONF.host.monitoring_interval
        self.monitoring_samples = CONF.host.monitoring_samples
        self.matrix_manager = matrix_helper.MatrixManager(CONF)
        self.consul_manager = consul_helper.ConsulManager(CONF)
        self.notifier = masakari.SendNotification()
        self._matrix = None
        self._sequence = None
        self.monitoring_data = {}
        self.last_host_health = {}

    @property
    def matrix(self):
        if not self._matrix:
            self._matrix = self.matrix_manager.get_matrix()
        return self._matrix

    @property
    def sequence(self):
        if not self._sequence:
            self._sequence = self.matrix_manager.get_sequence()
        return self._sequence

    def _formate_health(self, host_health):
        formate_health = {}
        for i in range(len(host_health)):
            layer = "%s-interface" % self.sequence[i]
            state = host_health[i]
            formate_health[layer] = state

        return formate_health

    def _event(self, host, host_health):
        host_status = ec.EventConstants.HOST_STATUS_NORMAL
        if 'down' not in host_health:
            event_type = ec.EventConstants.EVENT_STARTED
            cluster_status = ec.EventConstants.CLUSTER_STATUS_ONLINE
        else:
            actions = self.get_action_from_matrix(host_health)
            if 'recovery' in actions:
                LOG.info("Host %s needs recovery, health status: %s." %
                         (host, str(self._formate_health(host_health))))
                event_type = ec.EventConstants.EVENT_STOPPED
                cluster_status = ec.EventConstants.CLUSTER_STATUS_OFFLINE
            else:
                return None

        # TODO(suzhengwei): Add host status detail in the payload to show
        # host status in all Consul clusters.
        event = {
            'notification': {
                'type': ec.EventConstants.TYPE_COMPUTE_HOST,
                'hostname': host,
                'generated_time': timeutils.utcnow(),
                'payload': {
                    'event': event_type,
                    'cluster_status': cluster_status,
                    'host_status': host_status
                }
            }
        }

        return event

    def update_monitoring_data(self):
        '''update monitoring data from consul clusters'''
        LOG.debug("update monitoring data from consul.")
        # Get current host health in sequence [x, y, z]. The example of
        # the return value is {'node01':[x, y, z], 'node02':[x, y, z]...}
        cluster_health = self.consul_manager.get_health(self.sequence)
        LOG.debug("Current cluster state: %s.", cluster_health)
        # Reassemble host health history with the latest host health.
        # Example of 'host_health_history' is [[x, y, x], [x, y, z]...]
        for host, health in cluster_health.items():
            host_health_history = self.monitoring_data.get(
                host, deque([], maxlen=self.monitoring_samples))
            host_health_history.append(health)
            self.monitoring_data[host] = host_health_history

    def get_host_health(self, host):
        health_history = self.monitoring_data.get(host, [])
        if len(health_history) < self.monitoring_samples:
            LOG.debug("Not enough monitoring data for host %s", host)
            return None

        # Caculate host health from host health history.
        # Only continous 'down' represents the interface 'down',
        # while continous 'up' represents the interface 'up'.
        host_sequence_health = []
        host_health_history = list(zip(*health_history))
        for i in range(0, len(host_health_history)):
            if ('up' in host_health_history[i] and
                    'down' in host_health_history[i]):
                host_sequence_health.append(None)
            else:
                host_sequence_health.append(host_health_history[i][0])

        return host_sequence_health

    def _host_health_changed(self, host, health):
        last_health = self.last_host_health.get(host)
        if last_health is None:
            self.last_host_health[host] = health
            return False

        if health != last_health:
            self.last_host_health[host] = health
            return True
        else:
            return False

    def get_action_from_matrix(self, host_health):
        for health_action in self.matrix:
            matrix_health = health_action["health"]
            matrix_action = health_action["action"]
            if host_health == matrix_health:
                return matrix_action

        return []

    def poll_hosts(self):
        '''poll and check hosts health'''
        for host in self.monitoring_data.keys():

            if host == self.hostname:
                continue

            host_health = self.get_host_health(host)
            if host_health is None:
                continue

            if not self._host_health_changed(host, host_health):
                continue

            # it will send notifition to trigger host failure recovery
            # according to defined HA strategy
            event = self._event(host, host_health)
            if event:
                self.notifier.send_notification(
                    CONF.host.api_retry_max,
                    CONF.host.api_retry_interval,
                    event)

    def stop(self):
        self.running = False

    def monitor_hosts(self):
        self.running = True
        while self.running:
            try:
                self.update_monitoring_data()
                self.poll_hosts()
            except Exception as e:
                LOG.exception("Exception when host-monitor by consul: %s", e)

            eventlet.greenthread.sleep(self.monitoring_interval)
