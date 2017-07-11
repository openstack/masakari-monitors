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
from oslo_utils import timeutils

import masakarimonitors.conf
from masakarimonitors.ha import masakari
from masakarimonitors.objects import event_constants as ec
from masakarimonitors import utils

LOG = oslo_logging.getLogger(__name__)
CONF = masakarimonitors.conf.CONF


class HandleProcess(object):
    """Handle process."""

    def __init__(self):
        self.process_list = None
        self.restart_failure_list = []
        self.notifier = masakari.SendNotification()

    def set_process_list(self, process_list):
        """Set process list object.

        :param process_list: process list object
        """
        self.process_list = process_list

    def _execute_cmd(self, cmd_str, run_as_root):

        # Split command string and delete empty elements.
        command = cmd_str.split(' ')
        command = filter(lambda x: x != '', command)

        try:
            # Execute start command.
            out, err = utils.execute(*command,
                                     run_as_root=run_as_root)

            if out:
                msg = ("CMD '%s' output stdout: %s") % (cmd_str, out)
                LOG.info("%s", msg)

            if err:
                msg = ("CMD '%s' output stderr: %s") % (cmd_str, err)
                LOG.warning("%s", msg)
                return 1

        except Exception as e:
            msg = ("CMD '%s' raised exception: %s") % (cmd_str, e)
            LOG.error("%s", e)
            return 1

        return 0

    def start_processes(self):
        """Initial start of processes.

        This method starts the processes using start command written in the
        process list.
        """
        for process in self.process_list:
            cmd_str = process['start_command']
            pre_cmd_str = process['pre_start_command']
            post_cmd_str = process['post_start_command']

            # Execute pre start command.
            if pre_cmd_str:
                ret = self._execute_cmd(pre_cmd_str, process['run_as_root'])
                if ret != 0:
                    continue

            # Execute start command.
            LOG.info("Start of process with executing command: %s", cmd_str)
            self._execute_cmd(cmd_str, process['run_as_root'])

            # Execute post start command.
            if post_cmd_str:
                ret = self._execute_cmd(post_cmd_str, process['run_as_root'])

    def monitor_processes(self):
        """Monitor processes.

        This method monitors the processes using process name written in the
        process list.

        :returns: List of down process
        """
        down_process_list = []
        for process in self.process_list:
            process_name = process['process_name']

            try:
                # Execute monitoring command.
                out, err = utils.execute('ps', '-ef', run_as_root=False)
                if process_name in out:
                    LOG.debug("Process '%s' is found." % process_name)
                else:
                    # Append down_process_list.
                    down_process_list.append(process)
                    LOG.warning("Process '%s' is not found.", process_name)
            except Exception as e:
                LOG.error("Monitoring command raised exception: %s", e)

        return down_process_list

    def _make_event(self, process_name):

        hostname = socket.gethostname()
        current_time = timeutils.utcnow()
        event = {
            'notification': {
                'type': ec.EventConstants.TYPE_PROCESS,
                'hostname': hostname,
                'generated_time': current_time,
                'payload': {
                    'event': ec.EventConstants.EVENT_STOPPED,
                    'process_name': process_name
                }
            }
        }

        return event

    def restart_processes(self, down_process_list):
        """Restart processes.

        This method restarts the processes using restart command written in
        the process list.

        :param down_process_list: down process list object
        """
        tmp_restart_failure_list = []
        for down_process in down_process_list:
            # The process which failed to restart previously doesn't restart.
            if down_process['process_name'] in self.restart_failure_list:
                msg = "Process '%s' doesn't be restarted because it failed" \
                      " to restart previously." % down_process['process_name']
                LOG.warning("%s", msg)
                tmp_restart_failure_list.append(down_process['process_name'])
                continue

            cmd_str = down_process['restart_command']
            pre_cmd_str = down_process['pre_restart_command']
            post_cmd_str = down_process['post_restart_command']

            LOG.info("Restart of process with executing command: %s", cmd_str)

            for retries in range(0, CONF.process.restart_retries + 1):

                # Execute pre start command.
                if pre_cmd_str:
                    ret = self._execute_cmd(pre_cmd_str,
                                            down_process['run_as_root'])
                    if ret != 0:
                        # Failed to restart process.
                        eventlet.greenthread.sleep(
                            CONF.process.restart_interval)
                        continue

                # Execute start command.
                ret = self._execute_cmd(cmd_str, down_process['run_as_root'])
                if ret != 0:
                    # Failed to restart process.
                    eventlet.greenthread.sleep(CONF.process.restart_interval)
                    continue

                # Execute post start command.
                if post_cmd_str:
                    ret = self._execute_cmd(post_cmd_str,
                                            down_process['run_as_root'])
                    if ret != 0:
                        # Failed to restart process.
                        eventlet.greenthread.sleep(
                            CONF.process.restart_interval)
                        continue

                # Succeeded in restarting process.
                break

            if retries == CONF.process.restart_retries:
                # Send a notification.
                event = self._make_event(down_process['process_name'])
                self.notifier.send_notification(
                    CONF.process.api_retry_max,
                    CONF.process.api_retry_interval,
                    event)
                # Add the process name which failed to restart to the
                # failure list.
                tmp_restart_failure_list.append(down_process['process_name'])

        # Replace the old restart_failure_list with new one
        self.restart_failure_list = tmp_restart_failure_list[:]
