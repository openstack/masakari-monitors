# Copyright (c) 2018 WindRiver Systems
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
import libvirt
import socket
import sys
import threading
import time

from oslo_config import cfg
from oslo_log import log as oslo_logging
from oslo_utils import excutils
from oslo_utils import timeutils

from masakarimonitors.introspectiveinstancemonitor import qemu_utils
from masakarimonitors.introspectiveinstancemonitor import scheduler
from masakarimonitors import manager
from masakarimonitors.objects import event_constants as ec

LOG = oslo_logging.getLogger(__name__)
CONF = cfg.CONF


class IntrospectiveInstanceMonitorManager(manager.Manager):

    def __init__(self, *args, **kwargs):
        self.init_tgm()
        super(IntrospectiveInstanceMonitorManager, self).__init__(
            service_name="introspectiveinstancemonitor", *args, **kwargs)
        # This keeps track of what thread is running the event loop,
        # (if it is run in a background thread)
        self.event_loop_thread = None

    def _reset_journal(self, eventID, eventType, detail, uuID):
        """To reset the monitoring to discovery stage

        :param event_id: Event ID
        :param event_type: Event type
        :param detail: Event code
        :param domain_uuid: Uuid
        """

        noticeType = ec.EventConstants.TYPE_VM
        hostname = socket.gethostname()
        currentTime = timeutils.utcnow()

        def _reset_handler(event_id, event_type, detail, domain_uuid, msg):
            """Reset monitoring

            To reset monitoring to discovery stage for the following event:
            libvirt.VIR_DOMAIN_EVENT_STARTED
            """

            if (event_id == libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE) and \
               (event_type == libvirt.VIR_DOMAIN_EVENT_STARTED):
                LOG.debug(msg)
                qemu_utils.resetJournal(domain_uuid)

        # All Event Output if debug mode is on.
        msg = "libvirt Event Received.type = %s \
            hostname = %s uuid = %s time = %s eventID = %d eventType = %d \
            detail = %d" % (
            noticeType,
            hostname, uuID, currentTime, eventID,
            eventType, detail)

        LOG.debug("%s", msg)

        try:
            thread = threading.Thread(
                _reset_handler(eventID, eventType, detail, uuID, msg)
            )
            thread.start()
        except KeyError as e:
            LOG.error("virEventFilter KeyError: {0}".format(e))
        except IndexError as e:
            LOG.error("virEventFilter IndexError: {0}".format(e))
        except TypeError as e:
            LOG.error("virEventFilter TypeError: {0}".format(e))
        except Exception:
            with excutils.save_and_reraise_exception():
                LOG.error("Unexpected error: %s" % sys.exc_info()[0])

    def init_tgm(self):
        """Manages the masakari-introspectiveinstancemonitor."""
        self.TG = scheduler.ThreadGroupManager()

    def _vir_event_loop_native_run(self):
        # Directly run the event loop in the current thread
        while True:
            libvirt.virEventRunDefaultImpl()

    def _vir_event_loop_native_start(self):
        libvirt.virEventRegisterDefaultImpl()
        self.event_loop_thread = threading.Thread(
            target=self._vir_event_loop_native_run,
            name="lib_virt_eventLoop")
        self.event_loop_thread.setDaemon(True)
        self.event_loop_thread.start()

    def _my_domain_event_callback(self, conn, dom, event, detail, opaque):
        self._reset_journal(libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE,
        event, detail, dom.UUIDString())

    def _my_domain_event_reboot_callback(self, conn, dom, opaque):
        self._reset_journal(libvirt.VIR_DOMAIN_EVENT_ID_REBOOT,
        -1, -1, dom.UUIDString())

    def _err_handler(self, ctxt, err):
        LOG.warning("Error from libvirt : %s", err[2])

    def _virt_event(self, uri):
        # Run a background thread with the event loop
        self._vir_event_loop_native_start()

        event_callback_handlers = {
            libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE:
                self._my_domain_event_callback,
            libvirt.VIR_DOMAIN_EVENT_ID_REBOOT:
                self._my_domain_event_reboot_callback
        }
        # Connect to libvirt - If be disconnected, reprocess.
        self.running = True
        while self.running:
            vc = libvirt.openReadOnly(uri)

            # Event callback settings
            callback_ids = []
            for event, callback in event_callback_handlers.items():
                cid = vc.domainEventRegisterAny(None, event, callback, None)
                callback_ids.append(cid)

            # Connection monitoring.
            vc.setKeepAlive(5, 3)
            while vc.isAlive() == 1 and self.running:
                eventlet.greenthread.sleep(1)

            # If connection between libvirtd was lost,
            # clear callback connection.
            LOG.warning("Libvirt Connection Closed Unexpectedly.")
            for cid in callback_ids:
                try:
                    vc.domainEventDeregisterAny(cid)
                except Exception:
                    pass
            vc.close()
            del vc
            time.sleep(3)

    def stop(self):
        self.running = False

    def main(self):
        """Main method.

        Set the URI, error handler, and executes event loop processing.
        """

        uri = CONF.libvirt.connection_uri
        LOG.debug("Using uri:" + uri)

        # set error handler & do event loop
        libvirt.registerErrorHandler(self._err_handler, '_virt_event')
        self._virt_event(uri)
