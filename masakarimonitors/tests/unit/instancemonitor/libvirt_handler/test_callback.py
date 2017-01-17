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
from openstack import connection
from openstack import profile
from oslo_utils import timeutils

from masakarimonitors.instancemonitor.libvirt_handler import callback
from masakarimonitors.tests.unit.instancemonitor import fakes

eventlet.monkey_patch(os=False)


class TestCallback(testtools.TestCase):

    def setUp(self):
        super(TestCallback, self).setUp()

    @mock.patch.object(connection, 'Connection')
    @mock.patch.object(profile.Profile, 'set_interface')
    @mock.patch.object(profile.Profile, 'set_version')
    @mock.patch.object(profile.Profile, 'set_region')
    @mock.patch.object(profile.Profile, 'set_name')
    @mock.patch.object(profile.Profile, '_add_service')
    def test_vir_event_filter(self,
                              mock_add_service,
                              mock_set_name,
                              mock_set_region,
                              mock_set_version,
                              mock_set_interface,
                              mock_Connection):

        obj = callback.Callback()

        mock_add_service.return_value = None
        mock_set_name.return_value = None
        mock_set_region.return_value = None
        mock_set_version.return_value = None
        mock_set_interface.return_value = None
        mock_Connection.return_value = fakes.FakeConnection()

        eventID_val = 0
        detail_val = 5
        uuID = 'test_uuid'
        noticeType = 'VM'
        hostname = 'masakari-node'
        currentTime = timeutils.utcnow()
        obj.libvirt_event_callback(eventID_val,
                                   detail_val,
                                   uuID,
                                   noticeType,
                                   hostname,
                                   currentTime)
