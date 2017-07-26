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

import eventlet
from oslo_log import log as oslo_logging

import masakarimonitors.conf
from masakarimonitors import manager
from masakarimonitors.processmonitor.process_handler import handle_process

LOG = oslo_logging.getLogger(__name__)
CONF = masakarimonitors.conf.CONF


class ProcessmonitorManager(manager.Manager):
    """Manages the masakari-processmonitor."""

    def __init__(self, *args, **kwargs):
        super(ProcessmonitorManager, self).__init__(
            service_name="processmonitor", *args, **kwargs)
        self.process_handler = handle_process.HandleProcess()

    def _load_process_list(self):
        try:
            process_list = yaml.load(open(CONF.process.process_list_path))
            LOG.debug("Loaded process list. %s" % process_list)

            return process_list
        except yaml.YAMLError as e:
            LOG.exception("YAMLError caught: %s", e)
            return
        except Exception as e:
            LOG.exception("Exception caught: %s", e)
            return

    def stop(self):
        self.running = False

    def main(self):
        """Main method."""

        try:
            # Load process list.
            process_list = self._load_process_list()
            if process_list is None:
                LOG.error("Failed to load process list file.")
                return

            # Set process_list object to the process handler.
            self.process_handler.set_process_list(process_list)

            # Initial start of processes.
            self.process_handler.start_processes()

            self.running = True
            while self.running:
                # Monitor processes.
                down_process_list = self.process_handler.monitor_processes()

                if len(down_process_list) != 0:
                    # Restart down processes.
                    self.process_handler.restart_processes(down_process_list)
                else:
                    # Since no down process, clear the restart_failure_list
                    self.process_handler.restart_failure_list[:] = []

                # Reload process list and set to the process handler.
                process_list = self._load_process_list()
                if process_list is None:
                    LOG.error("Failed to reload process list file.")
                    break
                self.process_handler.set_process_list(process_list)

                eventlet.greenthread.sleep(CONF.process.check_interval)

        except Exception as e:
            LOG.exception("Exception caught: %s", e)
            return

        return
