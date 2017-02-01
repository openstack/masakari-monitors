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

import eventlet

from masakarimonitors.processmonitor.process_handler import handle_process
from masakarimonitors import utils

eventlet.monkey_patch(os=False)

MOCK_PROCESS_LIST = [
    {
        'id': 1,
        'process_name': 'mock_process_name_A',
        'start_command': 'mock_start_command',
        'pre_start_command': 'mock_pre_start_command',
        'post_start_command': 'mock_post_start_command',
        'restart_command': 'mock_restart_command',
        'pre_restart_command': 'mock_pre_restart_command',
        'post_restart_command': 'mock_post_restart_command',
        'run_as_root': True
    },
]


class TestHandleProcess(testtools.TestCase):

    def setUp(self):
        super(TestHandleProcess, self).setUp()

    def test_set_process_list(self):
        process_list = MOCK_PROCESS_LIST
        obj = handle_process.HandleProcess()
        obj.set_process_list(process_list)

    @mock.patch.object(utils, 'execute')
    def test_start_processes(self,
                             mock_execute):
        process_list = MOCK_PROCESS_LIST
        obj = handle_process.HandleProcess()
        obj.set_process_list(process_list)

        mock_execute.return_value = ('test_stdout', 'test_stderr')

        obj.start_processes()

        mock_execute.assert_called_once_with(
            MOCK_PROCESS_LIST[0].get('start_command'),
            run_as_root=MOCK_PROCESS_LIST[0].get('run_as_root'))
