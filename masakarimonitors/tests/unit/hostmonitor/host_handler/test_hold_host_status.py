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

import testtools
from xml.etree import ElementTree

import eventlet

from masakarimonitors.hostmonitor.host_handler import hold_host_status

eventlet.monkey_patch(os=False)

NODE_STATE_XML = '<node_state uname="masakari-node" crmd="online">' \
                 '  <test foo="foo"/>' \
                 '</node_state>'
NODE_STATE_TAG = ElementTree.fromstring(NODE_STATE_XML)


class TestHostHoldStatus(testtools.TestCase):

    def setUp(self):
        super(TestHostHoldStatus, self).setUp()

    def test_set_host_status(self):
        obj = hold_host_status.HostHoldStatus()
        obj.set_host_status(NODE_STATE_TAG)
        self.assertEqual('online', obj.get_host_status('masakari-node'))

    def test_get_host_status(self):
        obj = hold_host_status.HostHoldStatus()
        obj.set_host_status(NODE_STATE_TAG)
        self.assertEqual('online', obj.get_host_status('masakari-node'))
