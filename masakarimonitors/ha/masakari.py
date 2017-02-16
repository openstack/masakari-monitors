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

import eventlet
from openstack import connection
from openstack import exceptions
from openstack import profile
from oslo_log import log as oslo_logging

from masakariclient.sdk.ha import ha_service
import masakarimonitors.conf
from masakarimonitors.i18n import _LE
from masakarimonitors.i18n import _LI
from masakarimonitors.i18n import _LW

LOG = oslo_logging.getLogger(__name__)
CONF = masakarimonitors.conf.CONF

PROFILE_TYPE = "ha"
PROFILE_NAME = "masakari"


class SendNotification(object):

    def _get_connection(self, api_version, region, interface, auth_url,
                        project_name, username, password, project_domain_id,
                        user_domain_id):

        # Create profile object.
        prof = profile.Profile()
        prof._add_service(ha_service.HAService(version=api_version))
        prof.set_name(PROFILE_TYPE, PROFILE_NAME)
        prof.set_region(PROFILE_TYPE, region)
        prof.set_version(PROFILE_TYPE, api_version)
        prof.set_interface(PROFILE_TYPE, interface)

        # Get connection.
        conn = connection.Connection(
            auth_url=auth_url,
            project_name=project_name,
            username=username,
            password=password,
            project_domain_id=project_domain_id,
            user_domain_id=user_domain_id,
            profile=prof)

        return conn

    def send_notification(self, api_retry_max, api_retry_interval, event):
        """Send a notification.

        This method sends a notification to the masakari-api.

        :param api_retry_max: Number of retries when the notification
            processing is error.
        :param api_retry_interval: Trial interval of time of the notification
            processing is error.
        :param event: dictionary of event that included in notification.
        """

        LOG.info(_LI("Send a notification. %s"), event)

        # Get connection.
        conn = self._get_connection(
            api_version=CONF.api.api_version,
            region=CONF.api.region,
            interface=CONF.api.api_interface,
            auth_url=CONF.api.auth_url,
            project_name=CONF.api.project_name,
            username=CONF.api.username,
            password=CONF.api.password,
            project_domain_id=CONF.api.project_domain_name,
            user_domain_id=CONF.api.project_domain_name)

        # Send a notification.
        retry_count = 0
        while True:
            try:
                response = conn.ha.create_notification(
                    type=event['notification']['type'],
                    hostname=event['notification']['hostname'],
                    generated_time=event['notification']['generated_time'],
                    payload=event['notification']['payload'])

                LOG.info(_LI("Response: %s"), response)
                break

            except Exception as e:
                if isinstance(e, exceptions.HttpException):
                    # If http_status is 409, skip the retry processing.
                    if e.http_status == 409:
                        msg = ("Stop retrying to send a notification because "
                               "same notification have been already sent.")
                        LOG.info(_LI("%s"), msg)
                        break

                if retry_count < api_retry_max:
                    LOG.warning(_LW("Retry sending a notification. (%s)"), e)
                    retry_count = retry_count + 1
                    eventlet.greenthread.sleep(api_retry_interval)
                else:
                    LOG.exception(_LE("Exception caught: %s"), e)
                    break
