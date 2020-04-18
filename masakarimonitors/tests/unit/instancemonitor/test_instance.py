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

import libvirt
import testtools
import threading
import time
from unittest import mock
import uuid

import eventlet

from masakarimonitors.instancemonitor import instance
from masakarimonitors.instancemonitor.libvirt_handler import eventfilter

eventlet.monkey_patch(os=False)


class TestInstancemonitorManager(testtools.TestCase):

    def setUp(self):
        super(TestInstancemonitorManager, self).setUp()

    def _make_callback_params(self):
        mock_conn = mock.Mock()
        mock_dom = mock.Mock()
        test_uuid = uuid.uuid4()
        mock_dom.UUIDString.return_value = test_uuid
        mock_opaque = mock.Mock()

        return mock_conn, mock_dom, mock_opaque, test_uuid

    @mock.patch.object(libvirt, 'virEventRunDefaultImpl')
    def test_vir_event_loop_native_run(self, mock_virEventRunDefaultImpl):
        mock_virEventRunDefaultImpl.side_effect = Exception("Test exception.")

        obj = instance.InstancemonitorManager()
        exception_flag = False
        try:
            obj._vir_event_loop_native_run()
        except Exception:
            exception_flag = True

        self.assertTrue(exception_flag)
        mock_virEventRunDefaultImpl.assert_called_once()

    @mock.patch.object(eventfilter.EventFilter, 'vir_event_filter')
    def test_my_domain_event_callback(self, mock_vir_event_filter):
        mock_vir_event_filter.return_value = None
        mock_conn, mock_dom, mock_opaque, test_uuid = \
            self._make_callback_params()

        obj = instance.InstancemonitorManager()
        obj._my_domain_event_callback(mock_conn, mock_dom, 0, 1, mock_opaque)

        mock_vir_event_filter.assert_called_once_with(
            libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE, 0, 1, test_uuid)

    @mock.patch.object(eventfilter.EventFilter, 'vir_event_filter')
    def test_my_domain_event_reboot_callback(self, mock_vir_event_filter):
        mock_vir_event_filter.return_value = None
        mock_conn, mock_dom, mock_opaque, test_uuid = \
            self._make_callback_params()

        obj = instance.InstancemonitorManager()
        obj._my_domain_event_reboot_callback(mock_conn, mock_dom, mock_opaque)

        mock_vir_event_filter.assert_called_once_with(
            libvirt.VIR_DOMAIN_EVENT_ID_REBOOT, -1, -1, test_uuid)

    @mock.patch.object(eventfilter.EventFilter, 'vir_event_filter')
    def test_my_domain_event_rtc_change_callback(self, mock_vir_event_filter):
        mock_vir_event_filter.return_value = None
        mock_conn, mock_dom, mock_opaque, test_uuid = \
            self._make_callback_params()
        utcoffset = ""

        obj = instance.InstancemonitorManager()
        obj._my_domain_event_rtc_change_callback(
            mock_conn, mock_dom, utcoffset, mock_opaque)

        mock_vir_event_filter.assert_called_once_with(
            libvirt.VIR_DOMAIN_EVENT_ID_RTC_CHANGE, -1, -1, test_uuid)

    @mock.patch.object(eventfilter.EventFilter, 'vir_event_filter')
    def test_my_domain_event_watchdog_callback(self, mock_vir_event_filter):
        mock_vir_event_filter.return_value = None
        mock_conn, mock_dom, mock_opaque, test_uuid = \
            self._make_callback_params()
        action = 0

        obj = instance.InstancemonitorManager()
        obj._my_domain_event_watchdog_callback(
            mock_conn, mock_dom, action, mock_opaque)

        mock_vir_event_filter.assert_called_once_with(
            libvirt.VIR_DOMAIN_EVENT_ID_WATCHDOG, action, -1, test_uuid)

    @mock.patch.object(eventfilter.EventFilter, 'vir_event_filter')
    def test_my_domain_event_io_error_callback(self, mock_vir_event_filter):
        mock_vir_event_filter.return_value = None
        mock_conn, mock_dom, mock_opaque, test_uuid = \
            self._make_callback_params()
        srcpath = ""
        devalias = ""
        action = 0

        obj = instance.InstancemonitorManager()
        obj._my_domain_event_io_error_callback(
            mock_conn, mock_dom, srcpath, devalias, action, mock_opaque)

        mock_vir_event_filter.assert_called_once_with(
            libvirt.VIR_DOMAIN_EVENT_ID_IO_ERROR, action, -1, test_uuid)

    @mock.patch.object(eventfilter.EventFilter, 'vir_event_filter')
    def test_my_domain_event_graphics_callback(self, mock_vir_event_filter):
        mock_vir_event_filter.return_value = None
        mock_conn, mock_dom, mock_opaque, test_uuid = \
            self._make_callback_params()
        phase = 0
        localAddr = ""
        remoteAddr = ""
        authScheme = ""
        subject = ""

        obj = instance.InstancemonitorManager()
        obj._my_domain_event_graphics_callback(
            mock_conn, mock_dom, phase, localAddr, remoteAddr, authScheme,
            subject, mock_opaque)

        mock_vir_event_filter.assert_called_once_with(
            libvirt.VIR_DOMAIN_EVENT_ID_GRAPHICS, -1, phase, test_uuid)

    @mock.patch.object(eventfilter.EventFilter, 'vir_event_filter')
    def test_my_domain_event_disk_change_callback(
        self, mock_vir_event_filter):
        mock_vir_event_filter.return_value = None
        mock_conn, mock_dom, mock_opaque, test_uuid = \
            self._make_callback_params()
        oldSrcPath = ""
        newSrcPath = ""
        devAlias = ""
        reason = ""

        obj = instance.InstancemonitorManager()
        obj._my_domain_event_disk_change_callback(
            mock_conn, mock_dom, oldSrcPath, newSrcPath, devAlias, reason,
            mock_opaque)

        mock_vir_event_filter.assert_called_once_with(
            libvirt.VIR_DOMAIN_EVENT_ID_DISK_CHANGE, -1, -1, test_uuid)

    @mock.patch.object(eventfilter.EventFilter, 'vir_event_filter')
    def test_my_domain_event_io_error_reason_callback(
        self, mock_vir_event_filter):
        mock_vir_event_filter.return_value = None
        mock_conn, mock_dom, mock_opaque, test_uuid = \
            self._make_callback_params()
        srcPath = ""
        devAlias = ""
        action = ""
        reason = ""

        obj = instance.InstancemonitorManager()
        obj._my_domain_event_io_error_reason_callback(
            mock_conn, mock_dom, srcPath, devAlias, action, reason,
            mock_opaque)

        mock_vir_event_filter.assert_called_once_with(
            libvirt.VIR_DOMAIN_EVENT_ID_IO_ERROR_REASON, -1, -1, test_uuid)

    @mock.patch.object(eventfilter.EventFilter, 'vir_event_filter')
    def test_my_domain_event_generic_callback(self, mock_vir_event_filter):
        mock_vir_event_filter.return_value = None
        mock_conn, mock_dom, mock_opaque, test_uuid = \
            self._make_callback_params()

        obj = instance.InstancemonitorManager()
        obj._my_domain_event_generic_callback(
            mock_conn, mock_dom, mock_opaque)

        mock_vir_event_filter.assert_called_once_with(
            libvirt.VIR_DOMAIN_EVENT_ID_CONTROL_ERROR, -1, -1, test_uuid)

    def test_err_handler(self):
        obj = instance.InstancemonitorManager()
        obj._err_handler("Test context.", ('err0.', 'err1', 'err2'))

    def test_stop(self):
        obj = instance.InstancemonitorManager()
        obj.stop()
        self.assertFalse(obj.running)

    @mock.patch.object(time, 'sleep')
    @mock.patch.object(eventlet.greenthread, 'sleep')
    @mock.patch.object(libvirt, 'openReadOnly')
    @mock.patch.object(threading, 'Thread')
    @mock.patch.object(libvirt, 'virEventRegisterDefaultImpl')
    def test_main(self,
                  mock_virEventRegisterDefaultImpl,
                  mock_Thread,
                  mock_openReadOnly,
                  mock_greenthread_sleep,
                  mock_time_sleep):

        mock_virEventRegisterDefaultImpl.return_value = None
        mock_event_loop_thread = mock.Mock(return_value=None)
        mock_Thread.return_value = mock_event_loop_thread
        mock_vc = mock.Mock()
        mock_openReadOnly.return_value = mock_vc
        mock_vc.domainEventRegisterAny.side_effect = \
            [0, 0, 0, 0, 0, 0, 0, 0, 0]
        mock_vc.setKeepAlive.return_value = None
        mock_vc.isAlive.side_effect = [1, 0]
        mock_vc.domainEventDeregisterAny.side_effect = \
            [None, None, None, None, None, None, None, None,
             Exception("Test exception.")]
        mock_vc.close.return_value = None
        mock_greenthread_sleep.return_value = None
        mock_time_sleep.side_effect = Exception("Test exception.")

        obj = instance.InstancemonitorManager()
        exception_flag = False
        try:
            obj.main()
        except Exception:
            exception_flag = True

        handlers_count = 9
        self.assertTrue(exception_flag)
        mock_virEventRegisterDefaultImpl.assert_called_once()
        mock_event_loop_thread.setDaemon.assert_called_once_with(True)
        mock_event_loop_thread.start.assert_called_once()
        mock_openReadOnly.assert_called_once_with("qemu:///system")
        self.assertEqual(
            handlers_count, mock_vc.domainEventRegisterAny.call_count)
        mock_vc.setKeepAlive.assert_called_once_with(5, 3)
        self.assertEqual(2, mock_vc.isAlive.call_count)
        self.assertEqual(
            handlers_count, mock_vc.domainEventDeregisterAny.call_count)
        mock_vc.close.assert_called_once()
