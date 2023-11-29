# Copyright(c) 2018 Nippon Telegraph and Telephone Corporation
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
from unittest import mock
import uuid


from masakarimonitors.introspectiveinstancemonitor import instance as object
from masakarimonitors.introspectiveinstancemonitor import qemu_utils


class TestQemuUtils(testtools.TestCase):

    def setup(self):
        super(TestQemuUtils, self).setUp()

    @mock.patch.object(qemu_utils.libvirt, 'virDomain')
    def test_getVmFsm(self, mock_domain):
        """To test the state machines

        Initial stage should be dicovery and will advance to a
        healthy stage after enough pingable events. Also,
        it should reach an error stage from healthy after
        a pingable event failure.
        """

        reference = qemu_utils.QemuGuestAgent()
        mock_domain.UUID.return_value = uuid.uuid4()
        reference.getVmFsm(mock_domain)
        self.assertEqual(reference.getVmFsm(mock_domain).current_state,
            'discovery')
        reference.getVmFsm(mock_domain).process_event('guest_not_pingable')
        self.assertEqual(reference.getVmFsm(mock_domain).current_state,
            'discovery')
        reference.getVmFsm(mock_domain).process_event('guest_pingable')
        self.assertEqual(reference.getVmFsm(mock_domain).current_state,
            'healthy')
        reference.getVmFsm(mock_domain).process_event('guest_pingable')
        self.assertEqual(reference.getVmFsm(mock_domain).current_state,
            'healthy')
        reference.getVmFsm(mock_domain).process_event('guest_not_pingable')
        self.assertEqual(reference.getVmFsm(mock_domain).current_state,
            'error')

    @mock.patch.object(qemu_utils.libvirt, 'virDomain')
    def test_hasQemuGuestAgent(self, mock_domain):
        mock_domain.UUID.return_value = 'testuuid'
        mock_domain.state.return_value = libvirt.VIR_DOMAIN_RUNNING, 'reason'
        mock_domain.XMLDesc.return_value = """<domain>
  <devices>
    <interface type="network">
      <target dev="vnet0"/>
    </interface>
    <interface type="network">
      <target dev="vnet1"/>
    </interface>
  </devices>
</domain>"""
        obj = qemu_utils.QemuGuestAgent()
        self.assertFalse(obj._hasQemuGuestAgent(mock_domain))
        mock_domain.XMLDesc.return_value = """<domain>
  <devices>
    <interface type="network">
      <target dev="vnet0"/>
    </interface>
    <interface type="network">
      <target dev="vnet1"/>
    </interface>
    <channel type='unix'>
      <source
        mode='bind'
        path=
        '/var/lib/libvirt/qemu/org.qemu.guest_agent.0.instance-00000003.sock'/>
      <target
        type='virtio'
        name='org.qemu.guest_agent.0' state='disconnected'/>
      <alias name='channel0'/>
      <address type='virtio-serial' controller='0' bus='0' port='1'/>
    </channel>
  </devices>
</domain>"""
        obj = qemu_utils.QemuGuestAgent()
        self.assertTrue(obj._hasQemuGuestAgent(mock_domain))

    @mock.patch.object(qemu_utils, 'resetJournal')
    def test_resetJournal(self, mock_resetJournal):

        mock_resetJournal.return_value = None

        obj = object.IntrospectiveInstanceMonitorManager()

        event_id = 0
        domain_uuid = uuid.uuid4()
        event_type = libvirt.VIR_DOMAIN_EVENT_STARTED
        detail = libvirt.VIR_DOMAIN_EVENT_STARTED_BOOTED

        obj._reset_journal(event_id, event_type, detail, domain_uuid)

        mock_resetJournal.assert_called_once_with(domain_uuid)
