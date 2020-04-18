# Copyright(c) 2017 Nippon Telegraph and Telephone Corporation
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
import testtools
from unittest import mock

from stevedore import driver

from masakarimonitors.hostmonitor import host


class TestHostmonitorManager(testtools.TestCase):

    def setUp(self):
        super(TestHostmonitorManager, self).setUp()

    @mock.patch.object(driver, 'DriverManager')
    def test_init_host(self, mock_DriverManager):

        mock_driver = mock.Mock()
        mock_DriverManager.return_value = mock_driver

        host_manager = host.HostmonitorManager()
        host_manager.init_host()

        mock_DriverManager.assert_called_once_with(
            namespace='hostmonitor.driver',
            name='default',
            invoke_on_load=True,
            invoke_args=(),
        )

    @mock.patch.object(os, '_exit')
    @mock.patch.object(driver, 'DriverManager')
    def test_init_host_exception(self, mock_DriverManager, mock_exit):

        mock_DriverManager.side_effect = Exception("Test exception.")
        mock_exit.return_value = None

        host_manager = host.HostmonitorManager()
        host_manager.init_host()

        mock_DriverManager.assert_called_once_with(
            namespace='hostmonitor.driver',
            name='default',
            invoke_on_load=True,
            invoke_args=(),
        )
        mock_exit.assert_called_once_with(1)

    @mock.patch.object(driver, 'DriverManager')
    def test_stop(self, mock_DriverManager):

        mock_driver = mock.Mock()
        mock_DriverManager.return_value = mock_driver

        host_manager = host.HostmonitorManager()
        host_manager.init_host()
        host_manager.stop()

        mock_DriverManager.assert_called_once_with(
            namespace='hostmonitor.driver',
            name='default',
            invoke_on_load=True,
            invoke_args=(),
        )
        mock_driver.driver.stop.assert_called_once_with()

    @mock.patch.object(driver, 'DriverManager')
    def test_main(self, mock_DriverManager):

        mock_driver = mock.Mock()
        mock_DriverManager.return_value = mock_driver

        host_manager = host.HostmonitorManager()
        host_manager.init_host()
        ret = host_manager.main()

        mock_DriverManager.assert_called_once_with(
            namespace='hostmonitor.driver',
            name='default',
            invoke_on_load=True,
            invoke_args=(),
        )
        mock_driver.driver.monitor_hosts.assert_called_once_with()
        self.assertIsNone(ret)

    @mock.patch.object(driver, 'DriverManager')
    def test_main_exception(self, mock_DriverManager):

        mock_driver = mock.Mock()
        mock_DriverManager.return_value = mock_driver
        mock_driver.driver.monitor_hosts.side_effect = \
            Exception("Test exception.")

        host_manager = host.HostmonitorManager()
        host_manager.init_host()
        ret = host_manager.main()

        mock_DriverManager.assert_called_once_with(
            namespace='hostmonitor.driver',
            name='default',
            invoke_on_load=True,
            invoke_args=(),
        )
        mock_driver.driver.monitor_hosts.assert_called_once_with()
        self.assertIsNone(ret)
