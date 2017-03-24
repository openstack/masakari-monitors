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
import uuid

import eventlet
from oslo_utils import timeutils

from masakarimonitors.ha import masakari
from masakarimonitors.instancemonitor.libvirt_handler import callback
from masakarimonitors.objects import event_constants as ec

eventlet.monkey_patch(os=False)


class TestCallback(testtools.TestCase):

    def setUp(self):
        super(TestCallback, self).setUp()

    @mock.patch.object(masakari.SendNotification, 'send_notification')
    def test_libvirt_event_callback(self, mock_send_notification):

        mock_send_notification.return_value = None

        obj = callback.Callback()

        event_id = 0
        details = 5
        domain_uuid = uuid.uuid4()
        notice_type = ec.EventConstants.TYPE_VM
        hostname = socket.gethostname()
        current_time = timeutils.utcnow()

        obj.libvirt_event_callback(event_id, details, domain_uuid,
            notice_type, hostname, current_time)

        retry_max = 12
        retry_interval = 10
        event = {
            'notification': {
                'type': notice_type,
                'hostname': hostname,
                'generated_time': current_time,
                'payload': {
                    'event': event_id,
                    'instance_uuid': domain_uuid,
                    'vir_domain_event': details
                }
            }
        }
        mock_send_notification.assert_called_once_with(
            retry_max, retry_interval, event)
