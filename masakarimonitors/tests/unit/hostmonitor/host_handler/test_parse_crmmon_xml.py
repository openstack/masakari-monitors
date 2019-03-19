# Copyright(c) 2019 Canonical Ltd
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


import testtools

from masakarimonitors.hostmonitor.host_handler import parse_crmmon_xml


CRMMON_XML = '<?xml version="1.0"?>' \
             '<crm_mon version="1.1.18">' \
             '    <nodes>' \
             '        <node name="node-1" id="1001" online="true" />' \
             '        <node name="node-2" id="1002" online="false" />' \
             '        <node name="node-3" id="1003" online="true" />' \
             '    </nodes>' \
             '</crm_mon>'

CRMMON_NONODES_XML = '<?xml version="1.0"?>' \
                     '<crm_mon version="1.1.18">' \
                     '    <nodes>' \
                     '    </nodes>' \
                     '</crm_mon>'

CRMMON_NONODES_TAG_XML = '<?xml version="1.0"?>' \
                         '<crm_mon version="1.1.18">' \
                         '</crm_mon>'


class TestParseCrmMonXml(testtools.TestCase):

    def setUp(self):
        super(TestParseCrmMonXml, self).setUp()

    def test_set_crmmon_xml(self):
        obj = parse_crmmon_xml.ParseCrmMonXml()
        obj.set_crmmon_xml(CRMMON_XML)

    def test_get_node_state_tag_list(self):
        obj = parse_crmmon_xml.ParseCrmMonXml()
        obj.set_crmmon_xml(CRMMON_XML)

        node_state_tag_list = obj.get_node_state_tag_list()

        expected = {
            'node-1': 'true',
            'node-2': 'false',
            'node-3': 'true'}

        for node_state_tag in node_state_tag_list:
            self.assertEqual(
                expected[node_state_tag.get('name')],
                node_state_tag.get('online'))

    def test_get_node_state_tag_list_unset(self):
        obj = parse_crmmon_xml.ParseCrmMonXml()
        self.assertEqual(obj.get_node_state_tag_list(), [])

    def test_get_node_state_tag_list_nonodes(self):
        obj = parse_crmmon_xml.ParseCrmMonXml()
        obj.set_crmmon_xml(CRMMON_NONODES_XML)
        self.assertEqual(obj.get_node_state_tag_list(), [])

    def test_get_node_state_tag_list_nonodes_tag(self):
        obj = parse_crmmon_xml.ParseCrmMonXml()
        obj.set_crmmon_xml(CRMMON_NONODES_TAG_XML)
        self.assertEqual(obj.get_node_state_tag_list(), [])
