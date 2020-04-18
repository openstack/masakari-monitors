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
import testtools
from unittest import mock

import eventlet
from oslo_utils import timeutils

import masakarimonitors.conf
from masakarimonitors.ha import masakari
from masakarimonitors.objects import event_constants as ec
from masakarimonitors.processmonitor.process_handler import handle_process
from masakarimonitors import utils

CONF = masakarimonitors.conf.CONF
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

        self.assertEqual(process_list, obj.process_list)

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
    def test_start_processes_pre_cmd_fail(self, mock_execute):
        process_list = MOCK_PROCESS_LIST
        obj = handle_process.HandleProcess()
        obj.set_process_list(process_list)

        mock_execute.return_value = ('test_stdout', 'test_stderr')

        obj.start_processes()

        mock_execute.assert_called_once_with(
            MOCK_PROCESS_LIST[0].get('pre_start_command'),
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
        mock_execute.assert_called_once_with(
            'ps', '-ef', run_as_root=False)

    @mock.patch.object(utils, 'execute')
    def test_monitor_processes_not_found(self, mock_execute):
        process_list = MOCK_PROCESS_LIST
        obj = handle_process.HandleProcess()
        obj.set_process_list(process_list)

        mock_execute.return_value = ('', '')

        down_process_list = obj.monitor_processes()
        self.assertEqual(MOCK_PROCESS_LIST, down_process_list)
        mock_execute.assert_called_once_with(
            'ps', '-ef', run_as_root=False)

    @mock.patch.object(utils, 'execute')
    def test_monitor_processes_exception(self, mock_execute):
        process_list = MOCK_PROCESS_LIST
        obj = handle_process.HandleProcess()
        obj.set_process_list(process_list)

        mock_execute.side_effect = Exception("Test exception.")

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
            down_process_list[0].get('pre_restart_command'),
            run_as_root=down_process_list[0].get('run_as_root'))
        mock_execute.assert_any_call(
            down_process_list[0].get('restart_command'),
            run_as_root=down_process_list[0].get('run_as_root'))
        mock_execute.assert_any_call(
            down_process_list[0].get('post_restart_command'),
            run_as_root=down_process_list[0].get('run_as_root'))
        self.assertEqual([], obj.restart_failure_list)

    @mock.patch.object(utils, 'execute')
    def test_restart_processes_failed_to_restart_previously(
        self, mock_execute):
        process_list = MOCK_PROCESS_LIST
        obj = handle_process.HandleProcess()
        obj.set_process_list(process_list)
        restart_failure_list = [MOCK_DOWN_PROCESS_LIST[0].get('process_name')]
        obj.restart_failure_list = restart_failure_list
        down_process_list = MOCK_DOWN_PROCESS_LIST

        obj.restart_processes(down_process_list)

        self.assertEqual(restart_failure_list, obj.restart_failure_list)
        mock_execute.assert_not_called()

    @mock.patch.object(masakari.SendNotification, 'send_notification')
    @mock.patch.object(timeutils, 'utcnow')
    @mock.patch.object(eventlet.greenthread, 'sleep')
    @mock.patch.object(utils, 'execute')
    def test_restart_processes_pre_restart_command_retry_over(
        self, mock_execute, mock_sleep, mock_utcnow, mock_send_notification):
        process_list = MOCK_PROCESS_LIST
        obj = handle_process.HandleProcess()
        obj.set_process_list(process_list)
        down_process_list = MOCK_DOWN_PROCESS_LIST

        mock_execute.side_effect = [('test_stdout', 'test_stderr'),
                                    ('test_stdout', 'test_stderr'),
                                    ('test_stdout', 'test_stderr'),
                                    ('test_stdout', 'test_stderr')]
        mock_sleep.return_value = None
        current_time = timeutils.utcnow()
        mock_utcnow.return_value = current_time
        mock_send_notification.return_value = None

        obj.restart_processes(down_process_list)

        pre_execute_count = CONF.process.restart_retries + 1
        self.assertEqual(pre_execute_count, mock_execute.call_count)

        for var in range(0, mock_execute.call_count):
            args, kwargs = mock_execute.call_args_list[var]
            self.assertEqual(
                (down_process_list[0].get('pre_restart_command'),),
                args)
            self.assertEqual({'run_as_root': True}, kwargs)

        event = {
            'notification': {
                'type': ec.EventConstants.TYPE_PROCESS,
                'hostname': socket.gethostname(),
                'generated_time': current_time,
                'payload': {
                    'event': ec.EventConstants.EVENT_STOPPED,
                    'process_name': down_process_list[0].get('process_name')
                }
            }
        }
        mock_send_notification.assert_called_once_with(
            CONF.process.api_retry_max,
            CONF.process.api_retry_interval,
            event)

        self.assertEqual(
            [down_process_list[0].get('process_name')],
            obj.restart_failure_list)

    @mock.patch.object(masakari.SendNotification, 'send_notification')
    @mock.patch.object(timeutils, 'utcnow')
    @mock.patch.object(eventlet.greenthread, 'sleep')
    @mock.patch.object(utils, 'execute')
    def test_restart_processes_restart_command_retry_over(
        self, mock_execute, mock_sleep, mock_utcnow, mock_send_notification):
        process_list = MOCK_PROCESS_LIST
        obj = handle_process.HandleProcess()
        obj.set_process_list(process_list)
        down_process_list = MOCK_DOWN_PROCESS_LIST

        mock_execute.side_effect = [('test_stdout', ''),
                                    ('test_stdout', 'test_stderr'),
                                    ('test_stdout', ''),
                                    ('test_stdout', 'test_stderr'),
                                    ('test_stdout', ''),
                                    ('test_stdout', 'test_stderr'),
                                    ('test_stdout', ''),
                                    ('test_stdout', 'test_stderr')]
        mock_sleep.return_value = None
        current_time = timeutils.utcnow()
        mock_utcnow.return_value = current_time
        mock_send_notification.return_value = None

        obj.restart_processes(down_process_list)

        pre_execute_count = CONF.process.restart_retries + 1
        execute_count = CONF.process.restart_retries + 1
        total_execute_count = pre_execute_count + execute_count
        self.assertEqual(total_execute_count, mock_execute.call_count)

        for var in range(0, mock_execute.call_count):
            # Execute order of restart_command is the second.
            execute_order = 2

            if (var + 1) % execute_order == 0:
                args, kwargs = mock_execute.call_args_list[var]
                self.assertEqual(
                    (down_process_list[0].get('restart_command'),),
                    args)
                self.assertEqual({'run_as_root': True}, kwargs)

        event = {
            'notification': {
                'type': ec.EventConstants.TYPE_PROCESS,
                'hostname': socket.gethostname(),
                'generated_time': current_time,
                'payload': {
                    'event': ec.EventConstants.EVENT_STOPPED,
                    'process_name': down_process_list[0].get('process_name')
                }
            }
        }
        mock_send_notification.assert_called_once_with(
            CONF.process.api_retry_max,
            CONF.process.api_retry_interval,
            event)
        self.assertEqual(
            [down_process_list[0].get('process_name')],
            obj.restart_failure_list)

    @mock.patch.object(masakari.SendNotification, 'send_notification')
    @mock.patch.object(timeutils, 'utcnow')
    @mock.patch.object(eventlet.greenthread, 'sleep')
    @mock.patch.object(utils, 'execute')
    def test_restart_processes_post_restart_command_retry_over(
        self, mock_execute, mock_sleep, mock_utcnow, mock_send_notification):
        process_list = MOCK_PROCESS_LIST
        obj = handle_process.HandleProcess()
        obj.set_process_list(process_list)
        down_process_list = MOCK_DOWN_PROCESS_LIST

        mock_execute.side_effect = [('test_stdout', ''),
                                    ('test_stdout', ''),
                                    ('test_stdout', 'test_stderr'),
                                    ('test_stdout', ''),
                                    ('test_stdout', ''),
                                    ('test_stdout', 'test_stderr'),
                                    ('test_stdout', ''),
                                    ('test_stdout', ''),
                                    ('test_stdout', 'test_stderr'),
                                    ('test_stdout', ''),
                                    ('test_stdout', ''),
                                    ('test_stdout', 'test_stderr')]
        mock_sleep.return_value = None
        current_time = timeutils.utcnow()
        mock_utcnow.return_value = current_time
        mock_send_notification.return_value = None

        obj.restart_processes(down_process_list)

        pre_execute_count = CONF.process.restart_retries + 1
        execute_count = CONF.process.restart_retries + 1
        post_execute_count = CONF.process.restart_retries + 1
        total_execute_count = \
            pre_execute_count + execute_count + post_execute_count
        self.assertEqual(total_execute_count, mock_execute.call_count)

        for var in range(0, mock_execute.call_count):
            # Execute order of restart_command is the third.
            execute_order = 3

            if (var + 1) % execute_order == 0:
                args, kwargs = mock_execute.call_args_list[var]
                self.assertEqual(
                    (down_process_list[0].get('post_restart_command'),),
                    args)
                self.assertEqual({'run_as_root': True}, kwargs)

        event = {
            'notification': {
                'type': ec.EventConstants.TYPE_PROCESS,
                'hostname': socket.gethostname(),
                'generated_time': current_time,
                'payload': {
                    'event': ec.EventConstants.EVENT_STOPPED,
                    'process_name': down_process_list[0].get('process_name')
                }
            }
        }
        mock_send_notification.assert_called_once_with(
            CONF.process.api_retry_max,
            CONF.process.api_retry_interval,
            event)
        self.assertEqual(
            [down_process_list[0].get('process_name')],
            obj.restart_failure_list)

    @mock.patch.object(utils, 'execute')
    def test_execute_cmd_exception(self, mock_execute):
        mock_execute.side_effect = Exception("Test exception.")

        obj = handle_process.HandleProcess()
        ret = obj._execute_cmd(MOCK_PROCESS_LIST[0].get('start_command'),
                               MOCK_PROCESS_LIST[0].get('run_as_root'))

        self.assertEqual(ret, 1)
