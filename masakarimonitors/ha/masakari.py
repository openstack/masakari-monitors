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
import pbr.version

from keystoneauth1.identity.generic import password as ks_password
from keystoneauth1 import session as ks_session
from openstack import connection
sdk_ver = pbr.version.VersionInfo('openstacksdk').version_string()
if sdk_ver in ['0.11.0']:
    from masakariclient.sdk.ha.v1 import _proxy
    from openstack import service_description
from openstack import exceptions
from oslo_log import log as oslo_logging

import masakarimonitors.conf

LOG = oslo_logging.getLogger(__name__)
CONF = masakarimonitors.conf.CONF

PROFILE_TYPE = "ha"
PROFILE_NAME = "masakari"


class SendNotification(object):

    def _get_connection(self, api_version, region, interface, auth_url,
                        project_name, username, password, project_domain_id,
                        user_domain_id):

        auth = ks_password.Password(
            auth_url=auth_url,
            username=username,
            password=password,
            user_domain_id=user_domain_id,
            project_name=project_name,
            project_domain_id=project_domain_id)
        session = ks_session.Session(auth=auth)

        # Get connection.
        if sdk_ver >= '0.11.1':
            conn = connection.Connection(session=session, interface=interface,
                                         region_name=region)
        elif sdk_ver in ['0.11.0']:
            desc = service_description.ServiceDescription(service_type='ha',
                                                    proxy_class=_proxy.Proxy)
            conn = connection.Connection(session=session, interface=interface,
                                         region_name=region)
            conn.add_service(desc)

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

        LOG.info("Send a notification. %s", event)

        # Get connection.
        conn = self._get_connection(
            api_version=CONF.api.api_version,
            region=CONF.api.region,
            interface=CONF.api.api_interface,
            auth_url=CONF.api.auth_url,
            project_name=CONF.api.project_name,
            username=CONF.api.username,
            password=CONF.api.password,
            project_domain_id=CONF.api.project_domain_id,
            user_domain_id=CONF.api.user_domain_id)

        # Send a notification.
        retry_count = 0
        while True:
            try:
                response = conn.ha.create_notification(
                    type=event['notification']['type'],
                    hostname=event['notification']['hostname'],
                    generated_time=event['notification']['generated_time'],
                    payload=event['notification']['payload'])

                LOG.info("Response: %s", response)
                break

            except Exception as e:
                if isinstance(e, exceptions.HttpException):

                    # TODO(samP): Remove attribute check and else case if
                    # openstacksdk is bumped up from '>=0.9.19' to '>=0.10.0'
                    # in global-requirements.
                    if hasattr(e, 'status_code'):
                        is_status_409 = e.status_code == 409
                    else:
                        is_status_409 = e.http_status == 409

                    if is_status_409:
                        msg = ("Stop retrying to send a notification because "
                               "same notification have been already sent.")
                        LOG.info("%s", msg)
                        break

                if retry_count < api_retry_max:
                    LOG.warning("Retry sending a notification. (%s)", e)
                    retry_count = retry_count + 1
                    eventlet.greenthread.sleep(api_retry_interval)
                else:
                    LOG.exception("Exception caught: %s", e)
                    break
