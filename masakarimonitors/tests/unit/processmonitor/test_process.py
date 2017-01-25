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

import mock
import testtools
import yaml

import eventlet

from masakarimonitors.processmonitor import process as processmonitor_manager
from masakarimonitors.processmonitor.process_handler import handle_process

eventlet.monkey_patch(os=False)

MOCK_PROCESS_LIST = [
    {
        'process_name': 'mock_process_name_A',
        'start_command': 'mock_start_command',
        'pre_start_command': 'mock_pre_start_command',
        'post_start_command': 'mock_post_start_command',
        'restart_command': 'mock_restart_command',
        'pre_restart_command': 'mock_pre_restart_command',
        'post_restart_command': 'mock_post_restart_command',
        'run_as_root': True
    },
    {
        'id': 2,
        'process_name': 'mock_process_name_B',
        'start_command': 'mock_start_command',
        'pre_start_command': 'mock_pre_start_command',
        'post_start_command': 'mock_post_start_command',
        'restart_command': 'mock_restart_command',
        'pre_restart_command': 'mock_pre_restart_command',
        'post_restart_command': 'mock_post_restart_command',
        'run_as_root': True
    },
]


class TestProcessmonitorManager(testtools.TestCase):

    def setUp(self):
        super(TestProcessmonitorManager, self).setUp()

    def _get_mock_process_list(self, call_count):
        if call_count == 0:
            return MOCK_PROCESS_LIST
        else:
            return

    @mock.patch.object(handle_process.HandleProcess, 'monitor_processes')
    @mock.patch.object(handle_process.HandleProcess, 'start_processes')
    @mock.patch.object(handle_process.HandleProcess, 'set_process_list')
    @mock.patch.object(yaml, 'load')
    def test_main(self,
                  mock_load,
                  mock_set_process_list,
                  mock_start_processes,
                  mock_monitor_processes):

        mock_load.side_effect = [self._get_mock_process_list(0),
                                 self._get_mock_process_list(1)]
        mock_set_process_list.return_value = None
        mock_start_processes.return_value = None
        mock_monitor_processes.return_value = []

        obj = processmonitor_manager.ProcessmonitorManager()
        obj.main()
