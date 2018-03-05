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
from keystoneauth1.identity.generic import password as ks_password
from keystoneauth1 import session as ks_session
from openstack import connection
from openstack import exceptions
from openstack import version
if version.__version__.find('0.9.19') == 0 or \
    version.__version__.find('0.10.0') == 0:
    from openstack import profile
    _new_sdk = False
else:
    from masakariclient.sdk.ha.v1 import _proxy
    from openstack import service_description
    _new_sdk = True
from oslo_log import log as oslo_logging

from masakariclient.sdk.ha import ha_service
import masakarimonitors.conf

LOG = oslo_logging.getLogger(__name__)
CONF = masakarimonitors.conf.CONF

PROFILE_TYPE = "ha"
PROFILE_NAME = "masakari"


class SendNotification(object):

    def _make_client_new(self):
        auth = ks_password.Password(
            auth_url=CONF.api.auth_url,
            username=CONF.api.username,
            password=CONF.api.password,
            user_domain_id=CONF.api.user_domain_id,
            project_name=CONF.api.project_name,
            project_domain_id=CONF.api.project_domain_id)
        session = ks_session.Session(auth=auth)

        desc = service_description.ServiceDescription(
            service_type='ha', proxy_class=_proxy.Proxy)
        conn = connection.Connection(
            session=session, extra_services=[desc])
        conn.add_service(desc)

        if version.__version__.find('0.11.0') == 0:
            client = conn.ha
        else:
            client = conn.ha.proxy_class(
                session=session, service_type='ha')

        return client

    def _make_client_old(self):
        # Make profile.
        prof = profile.Profile()
        prof._add_service(ha_service.HAService(
            version=CONF.api.api_version))
        prof.set_name(PROFILE_TYPE, PROFILE_NAME)
        prof.set_region(PROFILE_TYPE, CONF.api.region)
        prof.set_version(PROFILE_TYPE, CONF.api.api_version)
        prof.set_interface(PROFILE_TYPE, CONF.api.api_interface)

        # Make connection.
        conn = connection.Connection(
            auth_url=CONF.api.auth_url,
            project_name=CONF.api.project_name,
            username=CONF.api.username,
            password=CONF.api.password,
            project_domain_id=CONF.api.project_domain_id,
            user_domain_id=CONF.api.user_domain_id,
            profile=prof)

        # Make client.
        client = conn.ha

        return client

    def _make_client(self):
        if _new_sdk:
            return self._make_client_new()
        else:
            return self._make_client_old()

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

        # Get client.
        client = self._make_client()

        # Send a notification.
        retry_count = 0
        while True:
            try:
                response = client.create_notification(
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
