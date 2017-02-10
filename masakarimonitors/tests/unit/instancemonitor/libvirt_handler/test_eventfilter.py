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

from masakarimonitors.instancemonitor.libvirt_handler import callback
from masakarimonitors.instancemonitor.libvirt_handler import eventfilter

eventlet.monkey_patch(os=False)


class TestEventFilter(testtools.TestCase):

    def setUp(self):
        super(TestEventFilter, self).setUp()

    @mock.patch.object(callback.Callback, 'libvirt_event_callback')
    def test_vir_event_filter(self,
                              mock_libvirt_event_callback):

        obj = eventfilter.EventFilter()

        mock_libvirt_event_callback.return_value = 0

        eventID = 0
        eventType = 5
        detail = 5
        uuID = 'test_uuid'
        obj.vir_event_filter(eventID, eventType, detail, uuID)
