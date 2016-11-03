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

from masakariclient.sdk.vmha import vmha_service
import masakarimonitors.conf
from masakarimonitors.i18n import _LE
from masakarimonitors.i18n import _LI
from masakarimonitors.i18n import _LW


LOG = oslo_logging.getLogger(__name__)
CONF = masakarimonitors.conf.CONF
VMHA = "vmha"


class Callback(object):
    """Class of callback processing."""

    def _get_connection(self, api_version, region, interface, auth_url,
                        project_name, username, password, project_domain_id,
                        user_domain_id):

        prof = profile.Profile()
        prof._add_service(vmha_service.VMHAService(version=api_version))
        prof.set_name(VMHA, VMHA)
        prof.set_region(VMHA, region)
        prof.set_version(VMHA, api_version)
        prof.set_interface(VMHA, interface)

        conn = connection.Connection(auth_url=auth_url,
                                     project_name=project_name,
                                     username=username,
                                     password=password,
                                     project_domain_id=project_domain_id,
                                     user_domain_id=user_domain_id,
                                     profile=prof)
        return conn

    def _post_event(self, retry_max, retry_interval, event):

        LOG.info(_LI("%s"), "Send a notification.")

        # Set conf value.
        project_domain_name = CONF.keystone.project_domain_name
        project_name = CONF.keystone.project_name
        username = CONF.keystone.username
        password = CONF.keystone.password
        auth_url = CONF.keystone.auth_url
        region = CONF.keystone.region
        interface = CONF.callback.interface
        api_version = CONF.callback.api_version

        conn = self._get_connection(
            api_version=api_version, region=region,
            interface=interface, auth_url=auth_url,
            project_name=project_name, username=username,
            password=password, project_domain_id=project_domain_name,
            user_domain_id=project_domain_name)

        type = event['notification']['type']
        hostname = event['notification']['hostname']
        generated_time = event['notification']['generated_time']
        payload = event['notification']['payload']

        retry_count = 0
        while True:
            try:
                response = conn.sdk.create_notification(
                    type=type,
                    hostname=hostname,
                    generated_time=generated_time,
                    payload=payload)

                LOG.info(_LI("%s"), "response:%s" % (response))
                break

            except Exception as e:
                # TODO(rkmrHonjo):
                # We should determine retriable exceptions or not.
                if retry_count < retry_max:
                    LOG.warning(_LW("Retry sending a notification. (%s)"), e)
                    retry_count = retry_count + 1
                    time.sleep(int(retry_interval))
                else:
                    LOG.exception(_LE("%s"), e)
                    break

        return

    def libvirt_event_callback(self, eventID, detail, uuID, noticeType,
                               hostname, currentTime):
        """Callback method.

        Callback processing be executed as result of the
        libvirt event filter.

        :param eventID: Event ID notify to the callback function
        :param detail: Event code notify to the callback function
        :param uuID: Uuid notify to the callback function
        :param noticeType: Notice type notify to the callback function
        :param hostname: Server host name of the source an event occur
                         notify to the callback function
        :param currentTime: Event occurred time notify to the callback
                            function
        """

        # Output to the syslog.
        msg = "libvirt Event: type=%s hostname=%s uuid=%s \
            time=%s eventID=%s detail=%s " % (
            noticeType, hostname, uuID, currentTime, eventID, detail)
        LOG.info(_LI("%s"), msg)

        # Set the event to the dictionary.
        event = {
            'notification': {
                'type': noticeType,
                'hostname': hostname,
                'generated_time': currentTime,
                'payload': {
                    'event': eventID,
                    'instance_uuid': uuID,
                    'vir_domain_event': detail
                }
            }
        }

        retry_max = CONF.callback.retry_max
        retry_interval = float(CONF.callback.retry_interval)

        self._post_event(retry_max, retry_interval, event)
        return
