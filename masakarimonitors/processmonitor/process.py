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

import yaml

from oslo_log import log as oslo_logging

import masakarimonitors.conf
from masakarimonitors.i18n import _LE
from masakarimonitors import manager

LOG = oslo_logging.getLogger(__name__)
CONF = masakarimonitors.conf.CONF


class ProcessmonitorManager(manager.Manager):
    """Manages the masakari-processmonitor."""

    def __init__(self, *args, **kwargs):
        super(ProcessmonitorManager, self).__init__(
            service_name="processmonitor", *args, **kwargs)

    def _load_process_list(self):
        try:
            process_list = yaml.load(file(CONF.process.process_list_path))
            LOG.debug("Loaded process list. %s" % process_list)

            return process_list
        except yaml.YAMLError as e:
            LOG.exception(_LE("YAMLError caught: %s"), e)
            return
        except Exception as e:
            LOG.exception(_LE("Exception caught: %s"), e)
            return

    def main(self):
        """Main method."""

        try:
            # Load process list.
            process_list = self._load_process_list()
            if process_list is None:
                LOG.error(_LE("Failed to load process list file."))
                return

        except Exception as e:
            LOG.exception(_LE("Exception caught: %s"), e)
            return

        return
