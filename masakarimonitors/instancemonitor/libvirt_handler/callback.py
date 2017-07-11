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

from oslo_log import log as oslo_logging

import masakarimonitors.conf
from masakarimonitors.ha import masakari


LOG = oslo_logging.getLogger(__name__)
CONF = masakarimonitors.conf.CONF


class Callback(object):
    """Class of callback processing."""

    def __init__(self):
        self.notifier = masakari.SendNotification()

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
        LOG.info("Libvirt Event: type=%(notice_type)s,"
                 " hostname=%(hostname)s,"
                 " uuid=%(uuid)s, time=%(current_time)s,"
                 " event_id=%(event_id)s,"
                 " detail=%(detail)s)" % {'notice_type': notice_type,
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

        self.notifier.send_notification(CONF.callback.retry_max,
                                        CONF.callback.retry_interval,
                                        event)
