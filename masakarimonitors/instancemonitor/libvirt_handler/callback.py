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
from masakarimonitors.i18n import _LI


LOG = oslo_logging.getLogger(__name__)
CONF = masakarimonitors.conf.CONF
VMHA = "vmha"


class Callback(object):
    """Class of callback processing."""

    def _post_event(self, retry_max, retry_interval, event):

        # TODO(KengoTakahara): This method will be implemented after
        # fixing masakariclient.sdk.
        pass

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
