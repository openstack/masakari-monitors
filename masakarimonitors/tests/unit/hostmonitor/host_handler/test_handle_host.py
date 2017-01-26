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

import eventlet

from masakarimonitors.hostmonitor.host_handler import handle_host
from masakarimonitors.hostmonitor.host_handler import parse_cib_xml
from masakarimonitors import utils

eventlet.monkey_patch(os=False)

EXECUTE_RETURN = 'Status of crmd@masakari-node: S_NOT_DC (ok)'


class TestHandleHost(testtools.TestCase):

    def setUp(self):
        super(TestHandleHost, self).setUp()

    @mock.patch.object(parse_cib_xml.ParseCibXml, 'get_node_state_tag_list')
    @mock.patch.object(parse_cib_xml.ParseCibXml, 'have_quorum')
    @mock.patch.object(parse_cib_xml.ParseCibXml, 'set_cib_xml')
    @mock.patch.object(utils, 'execute')
    @mock.patch.object(handle_host.HandleHost, '_check_pacemaker_services')
    @mock.patch.object(handle_host.HandleHost, '_check_hb_line')
    def test_monitor_hosts(self,
                           mock_check_hb_line,
                           mock_check_pacemaker_services,
                           mock_execute,
                           mock_set_cib_xml,
                           mock_have_quorum,
                           mock_get_node_state_tag_list):

        obj = handle_host.HandleHost()

        mock_check_hb_line.return_value = 0
        mock_check_pacemaker_services.return_value = False
        mock_execute.return_value = (EXECUTE_RETURN, '')
        mock_set_cib_xml.return_value = None
        mock_have_quorum.return_value = 0
        mock_get_node_state_tag_list.return_value = []

        ret = obj.monitor_hosts()
        self.assertEqual(None, ret)

    @mock.patch.object(utils, 'execute')
    def test_check_hb_line(self,
                           mock_execute):

        obj = handle_host.HandleHost()

        mock_execute.return_value = ('', '')

        ret = obj._check_hb_line()
        self.assertEqual(2, ret)
