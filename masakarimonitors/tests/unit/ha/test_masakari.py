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

import mock
import testtools

import eventlet
from openstack import connection
from openstack import exceptions
from openstack import profile
from oslo_utils import timeutils

from masakariclient.sdk.ha import ha_service
from masakarimonitors.ha import masakari
from masakarimonitors.objects import event_constants as ec

PROFILE_TYPE = "ha"
PROFILE_NAME = "masakari"


class TestSendNotification(testtools.TestCase):

    def setUp(self):
        super(TestSendNotification, self).setUp()
        self.api_retry_max = 3
        self.api_retry_interval = 1
        self.event = {
            'notification': {
                'type': ec.EventConstants.TYPE_COMPUTE_HOST,
                'hostname': 'compute-node1',
                'generated_time': timeutils.utcnow(),
                'payload': {
                    'event': ec.EventConstants.EVENT_STOPPED,
                    'cluster_status': 'OFFLINE',
                    'host_status': ec.EventConstants.HOST_STATUS_NORMAL
                }
            }
        }

    @mock.patch.object(connection, 'Connection')
    @mock.patch.object(profile, 'Profile')
    def test_send_notification(self,
                               mock_Profile,
                               mock_Connection):

        mock_prof = mock.Mock()
        mock_Profile.return_value = mock_prof
        mock_conn = mock.Mock()
        mock_Connection.return_value = mock_conn

        notifier = masakari.SendNotification()
        notifier.send_notification(
            self.api_retry_max, self.api_retry_interval, self.event)

        mock_prof._add_service.assert_called_once_with(
            ha_service.HAService(version='v1'))
        mock_prof.set_name.assert_called_once_with(
            PROFILE_TYPE, PROFILE_NAME)
        mock_prof.set_region.assert_called_once_with(
            PROFILE_TYPE, 'RegionOne')
        mock_prof.set_version.assert_called_once_with(
            PROFILE_TYPE, 'v1')
        mock_prof.set_interface.assert_called_once_with(
            PROFILE_TYPE, 'public')

        mock_Connection.assert_called_once_with(
            auth_url=None,
            project_name=None,
            username=None,
            password=None,
            project_domain_id=None,
            user_domain_id=None,
            profile=mock_prof)
        mock_conn.ha.create_notification.assert_called_once_with(
            type=self.event['notification']['type'],
            hostname=self.event['notification']['hostname'],
            generated_time=self.event['notification']['generated_time'],
            payload=self.event['notification']['payload'])

    @mock.patch.object(connection, 'Connection')
    @mock.patch.object(profile, 'Profile')
    def test_send_notification_409_error(self,
                                         mock_Profile,
                                         mock_Connection):

        mock_prof = mock.Mock()
        mock_Profile.return_value = mock_prof
        mock_conn = mock.Mock()
        mock_Connection.return_value = mock_conn
        mock_conn.ha.create_notification.side_effect = \
            exceptions.HttpException(http_status=409)

        notifier = masakari.SendNotification()
        notifier.send_notification(
            self.api_retry_max, self.api_retry_interval, self.event)

        mock_prof._add_service.assert_called_once_with(
            ha_service.HAService(version='v1'))
        mock_prof.set_name.assert_called_once_with(
            PROFILE_TYPE, PROFILE_NAME)
        mock_prof.set_region.assert_called_once_with(
            PROFILE_TYPE, 'RegionOne')
        mock_prof.set_version.assert_called_once_with(
            PROFILE_TYPE, 'v1')
        mock_prof.set_interface.assert_called_once_with(
            PROFILE_TYPE, 'public')

        mock_Connection.assert_called_once_with(
            auth_url=None,
            project_name=None,
            username=None,
            password=None,
            project_domain_id=None,
            user_domain_id=None,
            profile=mock_prof)
        mock_conn.ha.create_notification.assert_called_once_with(
            type=self.event['notification']['type'],
            hostname=self.event['notification']['hostname'],
            generated_time=self.event['notification']['generated_time'],
            payload=self.event['notification']['payload'])

    @mock.patch.object(eventlet.greenthread, 'sleep')
    @mock.patch.object(connection, 'Connection')
    @mock.patch.object(profile, 'Profile')
    def test_send_notification_500_error(self,
                                         mock_Profile,
                                         mock_Connection,
                                         mock_sleep):

        mock_prof = mock.Mock()
        mock_Profile.return_value = mock_prof
        mock_conn = mock.Mock()
        mock_Connection.return_value = mock_conn
        mock_conn.ha.create_notification.side_effect = \
            exceptions.HttpException(http_status=500)
        mock_sleep.return_value = None

        notifier = masakari.SendNotification()
        notifier.send_notification(
            self.api_retry_max, self.api_retry_interval, self.event)

        mock_prof._add_service.assert_called_once_with(
            ha_service.HAService(version='v1'))
        mock_prof.set_name.assert_called_once_with(
            PROFILE_TYPE, PROFILE_NAME)
        mock_prof.set_region.assert_called_once_with(
            PROFILE_TYPE, 'RegionOne')
        mock_prof.set_version.assert_called_once_with(
            PROFILE_TYPE, 'v1')
        mock_prof.set_interface.assert_called_once_with(
            PROFILE_TYPE, 'public')

        mock_Connection.assert_called_once_with(
            auth_url=None,
            project_name=None,
            username=None,
            password=None,
            project_domain_id=None,
            user_domain_id=None,
            profile=mock_prof)
        mock_conn.ha.create_notification.assert_called_with(
            type=self.event['notification']['type'],
            hostname=self.event['notification']['hostname'],
            generated_time=self.event['notification']['generated_time'],
            payload=self.event['notification']['payload'])
        self.assertEqual(self.api_retry_max + 1,
                         mock_conn.ha.create_notification.call_count)
