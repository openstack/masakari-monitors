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

import socket

import eventlet
from oslo_log import log as oslo_logging

import masakarimonitors.conf
import masakarimonitors.hostmonitor.host_handler.driver as driver
from masakarimonitors.hostmonitor.host_handler import parse_cib_xml
from masakarimonitors.i18n import _LE
from masakarimonitors.i18n import _LW
from masakarimonitors import utils

LOG = oslo_logging.getLogger(__name__)
CONF = masakarimonitors.conf.CONF


class HandleHost(driver.DriverBase):
    """Handle hosts.

    This class handles the host status.
    """

    def __init__(self):
        super(HandleHost, self).__init__()
        self.my_hostname = socket.gethostname()
        self.xml_parser = parse_cib_xml.ParseCibXml()

    def _check_host_status_by_crmadmin(self):
        try:
            # Execute crmadmin command.
            out, err = utils.execute('crmadmin', '-S', self.my_hostname,
                                     run_as_root=True)

            if err:
                msg = ("crmadmin command output stderr: %s") % err
                raise Exception(msg)

            # If own host is stable status, crmadmin outputs
            # 'S_IDLE' or 'S_NOT_DC'
            if 'S_IDLE' in out or 'S_NOT_DC' in out:
                return 0
            else:
                raise Exception(
                    "crmadmin command output unexpected host status.")

        except Exception as e:
            LOG.warning(_LW("Exception caught: %s"), e)
            LOG.warning(_LW("'%s' is unstable state on cluster."),
                        self.my_hostname)
            return 1

    def _get_cib_xml(self):
        try:
            # Execute cibadmin command.
            out, err = utils.execute('cibadmin', '--query', run_as_root=True)

            if err:
                msg = ("cibadmin command output stderr: %s") % err
                raise Exception(msg)

        except Exception as e:
            LOG.warning(_LW("Exception caught: %s"), e)
            return

        return out

    def _check_host_status_by_cibadmin(self):
        # Get xml of cib info.
        cib_xml = self._get_cib_xml()
        if cib_xml is None:
            # cibadmin command failure.
            return 1

        # Set to the ParseCibXml object.
        self.xml_parser.set_cib_xml(cib_xml)

        # Check if pacemaker cluster have quorum.
        if self.xml_parser.have_quorum() == 0:
            msg = "Pacemaker cluster doesn't have quorum."
            LOG.warning(_LW("%s"), msg)

        # Get node_state tag list.
        node_state_tag_list = self.xml_parser.get_node_state_tag_list()
        if len(node_state_tag_list) == 0:
            # If cib xml doesn't have node_state tag,
            # it is an unexpected result.
            raise Exception(
                "Failed to get node_state tag from cib xml.")

        return 0

    def stop(self):
        self.running = False

    def monitor_hosts(self):
        """Host monitoring main method.

        This method monitors hosts.
        """
        try:
            self.running = True
            while self.running:

                # Check the host status is stable or unstable by crmadmin.
                if self._check_host_status_by_crmadmin() != 0:
                    LOG.warning(_LW("hostmonitor skips monitoring hosts."))
                    eventlet.greenthread.sleep(CONF.host.monitoring_interval)
                    continue

                # Check the host status is online or offline by cibadmin.
                if self._check_host_status_by_cibadmin() != 0:
                    LOG.warning(_LW("hostmonitor skips monitoring hosts."))
                    eventlet.greenthread.sleep(CONF.host.monitoring_interval)
                    continue

                eventlet.greenthread.sleep(CONF.host.monitoring_interval)

        except Exception as e:
            LOG.exception(_LE("Exception caught: %s"), e)

        return
