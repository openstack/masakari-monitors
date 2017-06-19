# Copyright(c) 2016 Nippon Telegraph and Telephone Corporation
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

import os
from stevedore import driver

from oslo_log import log as oslo_logging

import masakarimonitors.conf
from masakarimonitors import manager

LOG = oslo_logging.getLogger(__name__)
CONF = masakarimonitors.conf.CONF


class HostmonitorManager(manager.Manager):
    """Manages the masakari-hostmonitor."""

    def __init__(self, *args, **kwargs):
        super(HostmonitorManager, self).__init__(
            service_name="hostmonitor", *args, **kwargs)
        self.driver = None

    def init_host(self):
        """Initialization for hostmonitor."""
        try:
            # Determine dynamic load driver from configuration.
            driver_name = CONF.host.monitoring_driver

            # Load the driver to global.
            self.driver = driver.DriverManager(
                namespace='hostmonitor.driver',
                name=driver_name,
                invoke_on_load=True,
                invoke_args=(),
            )
        except Exception as e:
            LOG.exception(
                "Exception caught during initializing hostmonitor: %s", e)
            os._exit(1)

    def stop(self):
        self.driver.driver.stop()

    def main(self):
        """Main method."""

        try:
            # Call the host monitoring driver.
            self.driver.driver.monitor_hosts()

        except Exception as e:
            LOG.exception("Exception caught: %s", e)

        return
