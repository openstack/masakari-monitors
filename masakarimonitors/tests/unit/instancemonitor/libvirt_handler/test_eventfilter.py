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
import socket
import testtools
import threading
import uuid

import eventlet
from oslo_utils import excutils
from oslo_utils import timeutils

from masakarimonitors.instancemonitor.libvirt_handler import callback
from masakarimonitors.instancemonitor.libvirt_handler import eventfilter
from masakarimonitors.instancemonitor.libvirt_handler \
    import eventfilter_table as evft
from masakarimonitors.objects import event_constants as ec

eventlet.monkey_patch(os=False)


class TestEventFilter(testtools.TestCase):

    def setUp(self):
        super(TestEventFilter, self).setUp()

    @mock.patch.object(excutils, 'save_and_reraise_exception')
    @mock.patch.object(callback.Callback, 'libvirt_event_callback')
    @mock.patch.object(timeutils, 'utcnow')
    def test_vir_event_filter(self, mock_utcnow, mock_libvirt_event_callback,
        mock_save_and_reraise_exception):

        current_time = timeutils.utcnow()
        mock_utcnow.return_value = current_time
        mock_libvirt_event_callback.return_value = None
        mock_save_and_reraise_exception.return_value = None

        obj = eventfilter.EventFilter()
        eventID = 0
        eventType = 5
        detail = 5
        uuID = uuid.uuid4()
        obj.vir_event_filter(eventID, eventType, detail, uuID)

        mock_libvirt_event_callback.assert_called_once_with(
            evft.eventID_dic[eventID],
            evft.detail_dic[eventID][eventType][detail],
            uuID,
            ec.EventConstants.TYPE_VM,
            socket.gethostname(),
            current_time)
        mock_save_and_reraise_exception.assert_not_called()

    @mock.patch.object(excutils, 'save_and_reraise_exception')
    @mock.patch.object(callback.Callback, 'libvirt_event_callback')
    def test_vir_event_filter_unmatched(self, mock_libvirt_event_callback,
        mock_save_and_reraise_exception):

        mock_libvirt_event_callback.return_value = None
        mock_save_and_reraise_exception.return_value = None

        obj = eventfilter.EventFilter()
        eventID = 0
        eventType = 5
        detail = 2
        uuID = uuid.uuid4()
        obj.vir_event_filter(eventID, eventType, detail, uuID)

        mock_libvirt_event_callback.assert_not_called()
        mock_save_and_reraise_exception.assert_not_called()

    @mock.patch.object(excutils, 'save_and_reraise_exception')
    @mock.patch.object(callback.Callback, 'libvirt_event_callback')
    def test_vir_event_filter_key_error(self, mock_libvirt_event_callback,
        mock_save_and_reraise_exception):

        mock_libvirt_event_callback.return_value = None
        mock_save_and_reraise_exception.return_value = None

        obj = eventfilter.EventFilter()
        eventID = 0
        eventType = 0
        detail = 0
        uuID = uuid.uuid4()
        obj.vir_event_filter(eventID, eventType, detail, uuID)

        mock_libvirt_event_callback.assert_not_called()
        mock_save_and_reraise_exception.assert_not_called()

    @mock.patch.object(excutils, 'save_and_reraise_exception')
    @mock.patch.object(callback.Callback, 'libvirt_event_callback')
    @mock.patch.object(threading, 'Thread')
    def test_vir_event_filter_type_error(self, mock_Thread,
        mock_libvirt_event_callback, mock_save_and_reraise_exception):

        mock_Thread.side_effect = TypeError("Threading exception.")
        mock_libvirt_event_callback.return_value = None
        mock_save_and_reraise_exception.return_value = None

        obj = eventfilter.EventFilter()
        eventID = 0
        eventType = 5
        detail = 5
        uuID = uuid.uuid4()
        obj.vir_event_filter(eventID, eventType, detail, uuID)

        mock_libvirt_event_callback.assert_not_called()
        mock_save_and_reraise_exception.assert_not_called()

    @mock.patch.object(excutils, 'save_and_reraise_exception')
    @mock.patch.object(callback.Callback, 'libvirt_event_callback')
    @mock.patch.object(threading, 'Thread')
    def test_vir_event_filter_index_error(self, mock_Thread,
        mock_libvirt_event_callback, mock_save_and_reraise_exception):

        mock_Thread.side_effect = IndexError("Threading exception.")
        mock_libvirt_event_callback.return_value = None
        mock_save_and_reraise_exception.return_value = None

        obj = eventfilter.EventFilter()
        eventID = 0
        eventType = 5
        detail = 5
        uuID = uuid.uuid4()
        obj.vir_event_filter(eventID, eventType, detail, uuID)

        mock_libvirt_event_callback.assert_not_called()
        mock_save_and_reraise_exception.assert_not_called()

    @mock.patch.object(callback.Callback, 'libvirt_event_callback')
    @mock.patch.object(threading, 'Thread')
    def test_vir_event_filter_other_exception(self, mock_Thread,
        mock_libvirt_event_callback):

        mock_Thread.side_effect = NameError("Threading exception.")
        mock_libvirt_event_callback.return_value = None

        obj = eventfilter.EventFilter()
        eventID = 0
        eventType = 5
        detail = 5
        uuID = uuid.uuid4()
        self.assertRaises(NameError, obj.vir_event_filter, eventID, eventType,
            detail, uuID)

        mock_libvirt_event_callback.assert_not_called()
