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

import libvirt
import mock
import testtools

import eventlet

from masakarimonitors.instancemonitor import instance
from masakarimonitors.instancemonitor.libvirt_handler import eventfilter
from masakarimonitors.tests.unit.instancemonitor import fakes

eventlet.monkey_patch(os=False)


class TestInstancemonitorManager(testtools.TestCase):

    def setUp(self):
        super(TestInstancemonitorManager, self).setUp()

    @mock.patch.object(libvirt, 'openReadOnly')
    @mock.patch.object(eventfilter.EventFilter, 'vir_event_filter')
    @mock.patch.object(instance.InstancemonitorManager,
                       '_vir_event_loop_native_start')
    def test_main(self,
                  mock_vir_event_loop_native_start,
                  mock_vir_event_filter,
                  mock_openReadOnly):

        obj = instance.InstancemonitorManager()

        mock_vir_event_loop_native_start.return_value = None
        mock_vir_event_filter.return_value = None
        mock_openReadOnly.return_value = fakes.FakeLibvirtOpenReadOnly()

        exception_flag = False
        try:
            obj.main()
        except EnvironmentError:
            exception_flag = True

        self.assertTrue(exception_flag)
