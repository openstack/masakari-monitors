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

from oslo_log import log as oslo_logging

from masakarimonitors import manager

LOG = oslo_logging.getLogger(__name__)


class InstancemonitorManager(manager.Manager):
    """Manages the masakari-instancemonitor."""

    def __init__(self, *args, **kwargs):
        super(InstancemonitorManager, self).__init__(
            service_name="instancemonitor", *args, **kwargs)

    def main(self):
        """Main method.

        Set the URI, error handler, and executes event loop processing.

        """
        uri = "qemu:///system"
        LOG.debug("Using uri:" + uri)
