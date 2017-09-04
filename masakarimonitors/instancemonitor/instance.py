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

import threading
import time

import eventlet
import libvirt
from oslo_config import cfg
from oslo_log import log as oslo_logging

from masakarimonitors.instancemonitor.libvirt_handler import eventfilter
from masakarimonitors import manager

LOG = oslo_logging.getLogger(__name__)
CONF = cfg.CONF


class InstancemonitorManager(manager.Manager):
    """Manages the masakari-instancemonitor."""

    def __init__(self, *args, **kwargs):
        super(InstancemonitorManager, self).__init__(
            service_name="instancemonitor", *args, **kwargs)
        self.evf = eventfilter.EventFilter()
        # This keeps track of what thread is running the event loop,
        # (if it is run in a background thread)
        self.event_loop_thread = None

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
        self.evf.vir_event_filter(libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE,
                                  event, detail, dom.UUIDString())

    def _my_domain_event_reboot_callback(self, conn, dom, opaque):
        self.evf.vir_event_filter(libvirt.VIR_DOMAIN_EVENT_ID_REBOOT,
                                  -1, -1, dom.UUIDString())

    def _my_domain_event_rtc_change_callback(self, conn, dom, utcoffset,
                                             opaque):
        self.evf.vir_event_filter(libvirt.VIR_DOMAIN_EVENT_ID_RTC_CHANGE,
                                  -1, -1, dom.UUIDString())

    def _my_domain_event_watchdog_callback(self, conn, dom, action, opaque):
        self.evf.vir_event_filter(libvirt.VIR_DOMAIN_EVENT_ID_WATCHDOG,
                                  action, -1, dom.UUIDString())

    def _my_domain_event_io_error_callback(self, conn, dom, srcpath,
                                           devalias, action, opaque):
        self.evf.vir_event_filter(libvirt.VIR_DOMAIN_EVENT_ID_IO_ERROR,
                                  action, -1, dom.UUIDString())

    def _my_domain_event_graphics_callback(self, conn, dom, phase, localAddr,
                                           remoteAddr, authScheme, subject,
                                           opaque):
        self.evf.vir_event_filter(libvirt.VIR_DOMAIN_EVENT_ID_GRAPHICS,
                                  -1, phase, dom.UUIDString())

    def _my_domain_event_disk_change_callback(self, conn, dom, oldSrcPath,
                                              newSrcPath, devAlias, reason,
                                              opaque):
        self.evf.vir_event_filter(libvirt.VIR_DOMAIN_EVENT_ID_DISK_CHANGE,
                                  -1, -1, dom.UUIDString())

    def _my_domain_event_io_error_reason_callback(self, conn, dom, srcPath,
                                                  devAlias, action, reason,
                                                  opaque):
        self.evf.vir_event_filter(libvirt.VIR_DOMAIN_EVENT_ID_IO_ERROR_REASON,
                                  -1, -1, dom.UUIDString())

    def _my_domain_event_generic_callback(self, conn, dom, opaque):
        self.evf.vir_event_filter(libvirt.VIR_DOMAIN_EVENT_ID_CONTROL_ERROR,
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
                self._my_domain_event_reboot_callback,
            libvirt.VIR_DOMAIN_EVENT_ID_RTC_CHANGE:
                self._my_domain_event_rtc_change_callback,
            libvirt.VIR_DOMAIN_EVENT_ID_IO_ERROR:
                self._my_domain_event_io_error_callback,
            libvirt.VIR_DOMAIN_EVENT_ID_WATCHDOG:
                self._my_domain_event_watchdog_callback,
            libvirt.VIR_DOMAIN_EVENT_ID_GRAPHICS:
                self._my_domain_event_graphics_callback,
            libvirt.VIR_DOMAIN_EVENT_ID_DISK_CHANGE:
                self._my_domain_event_disk_change_callback,
            libvirt.VIR_DOMAIN_EVENT_ID_IO_ERROR_REASON:
                self._my_domain_event_io_error_reason_callback,
            libvirt.VIR_DOMAIN_EVENT_ID_CONTROL_ERROR:
                self._my_domain_event_generic_callback
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
