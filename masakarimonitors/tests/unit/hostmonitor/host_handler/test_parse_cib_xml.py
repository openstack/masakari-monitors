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

import mock
import testtools
from xml.etree import ElementTree

import eventlet

from masakarimonitors.hostmonitor.host_handler import parse_cib_xml

eventlet.monkey_patch(os=False)

CIB_XML = '<cib have-quorum="1">' \
          '  <configuration>' \
          '    <crm_config>test</crm_config>' \
          '    <nodes>' \
          '      <node id="1084754452" uname="masakari-node"/>' \
          '      <node id="1084754453" uname="compute-node"/>' \
          '    </nodes>' \
          '    <resources>' \
          '      <group id="grpStonith1">' \
          '        <primitive id="stnt11" type="external/stonith-helper">' \
          '          <instance_attributes id="stnt11-instance_attributes">' \
          '            <nvpair name="hostlist" value="masakari-node"/>' \
          '          </instance_attributes>' \
          '          <operations>' \
          '            <op name="start"/>' \
          '            <op name="monitor"/>' \
          '            <op name="stop"/>' \
          '          </operations>' \
          '        </primitive>' \
          '        <primitive id="stnt12" type="external/ipmi">' \
          '          <instance_attributes id="stnt12-instance_attributes">' \
          '            <nvpair name="pcmk_reboot_timeout" value="60s"/>' \
          '            <nvpair name="hostname" value="masakari-node"/>' \
          '            <nvpair name="ipaddr" value="192.168.10.20"/>' \
          '            <nvpair name="userid" value="admin"/>' \
          '            <nvpair name="passwd" value="password"/>' \
          '            <nvpair name="interface" value="lanplus"/>' \
          '          </instance_attributes>' \
          '          <operations>' \
          '            <op name="start"/>' \
          '            <op name="monitor"/>' \
          '            <op name="stop"/>' \
          '          </operations>' \
          '        </primitive>' \
          '      </group>' \
          '      <group id="grpStonith2">' \
          '        <primitive id="stnt21" type="external/stonith-helper">' \
          '          <instance_attributes id="stnt21-instance_attributes">' \
          '            <nvpair name="hostlist" value="compute-node"/>' \
          '          </instance_attributes>' \
          '          <operations>' \
          '            <op name="start"/>' \
          '            <op name="monitor"/>' \
          '            <op name="stop"/>' \
          '          </operations>' \
          '        </primitive>' \
          '        <primitive id="stnt22" type="external/ipmi">' \
          '          <instance_attributes id="stnt22-instance_attributes">' \
          '            <nvpair name="pcmk_reboot_timeout" value="60s"/>' \
          '            <nvpair name="hostname" value="compute-node"/>' \
          '            <nvpair name="ipaddr" value="192.168.10.21"/>' \
          '            <nvpair name="userid" value="admin"/>' \
          '            <nvpair name="passwd" value="password"/>' \
          '            <nvpair name="interface" value="lanplus"/>' \
          '          </instance_attributes>' \
          '          <operations>' \
          '            <op name="start"/>' \
          '            <op name="monitor"/>' \
          '            <op name="stop"/>' \
          '          </operations>' \
          '        </primitive>' \
          '      </group>' \
          '    </resources>' \
          '    <constraints>' \
          '      <rsc_location id="loc_grpStonith1" rsc="grpStonith1">' \
          '        <rule test="foo"/>' \
          '      </rsc_location>' \
          '    </constraints>' \
          '  </configuration>' \
          '  <status>' \
          '    <node_state uname="masakari-node" crmd="online">' \
          '      <test foo="foo"/>' \
          '    </node_state>' \
          '    <node_state crmd="online" uname="compute-node">' \
          '      <test foo="foo"/>' \
          '    </node_state>' \
          '  </status>' \
          '</cib>'
CIB_TAG = ElementTree.fromstring(CIB_XML)


class TestParseCibXml(testtools.TestCase):

    def setUp(self):
        super(TestParseCibXml, self).setUp()

    @mock.patch.object(ElementTree, 'fromstring')
    def test_set_cib_xml(self,
                         mock_fromstring):

        obj = parse_cib_xml.ParseCibXml()
        mock_fromstring.return_value = CIB_TAG
        obj.set_cib_xml(CIB_XML)

    def test_have_quorum(self):

        obj = parse_cib_xml.ParseCibXml()
        obj.set_cib_xml(CIB_XML)
        self.assertEqual(1, obj.have_quorum())

    def test_get_node_state_tag_list(self):

        obj = parse_cib_xml.ParseCibXml()
        obj.set_cib_xml(CIB_XML)

        node_state_tag_list = obj.get_node_state_tag_list()

        for node_state_tag in node_state_tag_list:
            self.assertEqual('online', node_state_tag.get('crmd'))

    def test_get_stonith_ipmi_params(self):

        obj = parse_cib_xml.ParseCibXml()
        obj.set_cib_xml(CIB_XML)

        ipmi_values = obj.get_stonith_ipmi_params('compute-node')

        self.assertEqual('192.168.10.21', ipmi_values['ipaddr'])
        self.assertEqual('admin', ipmi_values['userid'])
        self.assertEqual('password', ipmi_values['passwd'])
        self.assertEqual('lanplus', ipmi_values['interface'])
