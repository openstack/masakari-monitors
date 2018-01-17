# Copyright(c) 2018 WindRiver Systems
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

import eventlet
import libvirt
import mock
import testtools

from masakarimonitors.introspectiveinstancemonitor import instance

eventlet.monkey_patch(os=False)


class TestMonitorManager(testtools.TestCase):

    def setUp(self):
        super(TestMonitorManager, self).setUp()

    @mock.patch.object(libvirt, 'virEventRunDefaultImpl')
    def test_vir_event_loop_native_run(self, mock_virEventRunDefaultImpl):
        mock_virEventRunDefaultImpl.side_effect = Exception("Test exception.")

        obj = instance.IntrospectiveInstanceMonitorManager()
        exception_flag = False
        try:
            obj._vir_event_loop_native_run()
        except Exception:
            exception_flag = True

        self.assertTrue(exception_flag)
        mock_virEventRunDefaultImpl.assert_called_once()
