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
          '  <status>' \
          '    <node_state uname="masakari-node" crmd="online">' \
          '      <test hoge="hoge"/>' \
          '    </node_state>' \
          '    <node_state crmd="online" uname="compute-node">' \
          '      <test hoge="hoge"/>' \
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
