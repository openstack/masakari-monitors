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

import time

from openstack import connection
from openstack import profile
from oslo_log import log as oslo_logging

from masakariclient.sdk.ha import ha_service
import masakarimonitors.conf
from masakarimonitors.i18n import _LE
from masakarimonitors.i18n import _LI
from masakarimonitors.i18n import _LW


LOG = oslo_logging.getLogger(__name__)
CONF = masakarimonitors.conf.CONF
TYPE = "ha"
NAME = "masakari"


class Callback(object):
    """Class of callback processing."""

    def _get_connection(self, api_version, region, interface, auth_url,
                        project_name, username, password, project_domain_id,
                        user_domain_id):

        prof = profile.Profile()
        prof._add_service(ha_service.HAService(version=api_version))
        prof.set_name(TYPE, NAME)
        prof.set_region(TYPE, region)
        prof.set_version(TYPE, api_version)
        prof.set_interface(TYPE, interface)

        conn = connection.Connection(auth_url=auth_url,
                                     project_name=project_name,
                                     username=username,
                                     password=password,
                                     project_domain_id=project_domain_id,
                                     user_domain_id=user_domain_id,
                                     profile=prof)
        return conn

    def _post_event(self, event):

        type = event['notification']['type']
        hostname = event['notification']['hostname']
        generated_time = event['notification']['generated_time']
        payload = event['notification']['payload']

        LOG.info(_LI("Send notification for hostname '%(hostname)s',"
                     " type '%(type)s' ") % {'hostname': hostname,
                                             'type': type})

        # Set conf value.
        project_domain_name = CONF.api.project_domain_name
        project_name = CONF.api.project_name
        username = CONF.api.username
        password = CONF.api.password
        auth_url = CONF.api.auth_url
        region = CONF.api.region
        interface = CONF.api.api_interface
        api_version = CONF.api.api_version
        retry_max = CONF.callback.retry_max
        retry_interval = CONF.callback.retry_interval

        conn = self._get_connection(
            api_version=api_version, region=region,
            interface=interface, auth_url=auth_url,
            project_name=project_name, username=username,
            password=password, project_domain_id=project_domain_name,
            user_domain_id=project_domain_name)

        retry_count = 0
        while True:
            try:
                response = conn.ha.create_notification(
                    type=type,
                    hostname=hostname,
                    generated_time=generated_time,
                    payload=payload)

                LOG.info(_LI("Notification response received : %s"), response)
                break

            except Exception as e:
                # TODO(rkmrHonjo):
                # We should determine retriable exceptions or not.
                if retry_count < retry_max:
                    LOG.warning(_LW("Retry sending a notification. (%s)"), e)
                    retry_count = retry_count + 1
                    time.sleep(retry_interval)
                else:
                    LOG.exception(_LE("Failed to send notification for type"
                                      " '%(type)s' for hostname"
                                      " '%(hostname)s'") %
                                  {'type': type, 'hostname': hostname})
                    break

    def libvirt_event_callback(self, event_id, details, domain_uuid,
                               notice_type, hostname, current_time):
        """Callback method.

        Callback processing be executed as result of the
        libvirt event filter.

        :param event_id: Event ID notify to the callback function
        :param details: Event code notify to the callback function
        :param domain_uuid: Uuid notify to the callback function
        :param notice_type: Notice type notify to the callback function
        :param hostname: Server host name of the source an event occur
                         notify to the callback function
        :param current_time: Event occurred time notify to the callback
                            function
        """

        # Output to the syslog.
        LOG.info(_LI("Libvirt Event: type=%(notice_type)s,"
                     " hostname=%(hostname)s,"
                     " uuid=%(uuid)s, time=%(current_time)s,"
                     " event_id=%(event_id)s,"
                     " detail=%(detail)s)") % {'notice_type': notice_type,
                                               'hostname': hostname,
                                               'uuid': domain_uuid,
                                               'current_time': current_time,
                                               'event_id': event_id,
                                               'detail': details})

        # Set the event to the dictionary.
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

        self._post_event(event)
