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

MOCK_DOWN_PROCESS_LIST = [
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

PS_RESULT = "\n" \
            "UID  PID   PPID C STIME TTY TIME     CMD\n" \
            "root 11187 1    0 18:52 ?   00:00:00 mock_process_name_A\n"


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

        mock_execute.side_effect = [('test_stdout', ''),
                                    ('test_stdout', ''),
                                    ('test_stdout', 'test_stderr')]

        obj.start_processes()

        mock_execute.assert_any_call(
            MOCK_PROCESS_LIST[0].get('pre_start_command'),
            run_as_root=MOCK_PROCESS_LIST[0].get('run_as_root'))
        mock_execute.assert_any_call(
            MOCK_PROCESS_LIST[0].get('start_command'),
            run_as_root=MOCK_PROCESS_LIST[0].get('run_as_root'))
        mock_execute.assert_any_call(
            MOCK_PROCESS_LIST[0].get('post_start_command'),
            run_as_root=MOCK_PROCESS_LIST[0].get('run_as_root'))

    @mock.patch.object(utils, 'execute')
    def test_monitor_processes(self,
                               mock_execute):
        process_list = MOCK_PROCESS_LIST
        obj = handle_process.HandleProcess()
        obj.set_process_list(process_list)

        mock_execute.return_value = (PS_RESULT, '')

        down_process_list = obj.monitor_processes()
        self.assertEqual([], down_process_list)

    @mock.patch.object(utils, 'execute')
    def test_restart_processes(self,
                               mock_execute):
        process_list = MOCK_PROCESS_LIST
        obj = handle_process.HandleProcess()
        obj.set_process_list(process_list)
        down_process_list = MOCK_DOWN_PROCESS_LIST

        mock_execute.side_effect = [('test_stdout', ''),
                                    ('test_stdout', ''),
                                    ('test_stdout', '')]

        obj.restart_processes(down_process_list)

        mock_execute.assert_any_call(
            MOCK_DOWN_PROCESS_LIST[0].get('pre_restart_command'),
            run_as_root=MOCK_DOWN_PROCESS_LIST[0].get('run_as_root'))
        mock_execute.assert_any_call(
            MOCK_DOWN_PROCESS_LIST[0].get('restart_command'),
            run_as_root=MOCK_DOWN_PROCESS_LIST[0].get('run_as_root'))
        mock_execute.assert_any_call(
            MOCK_DOWN_PROCESS_LIST[0].get('post_restart_command'),
            run_as_root=MOCK_DOWN_PROCESS_LIST[0].get('run_as_root'))
