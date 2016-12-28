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


class HostHoldStatus(object):
    """Hold host status.

    This class holds the host status.
    """

    def __init__(self):
        # host_status is dictionary like {'hostname': 'online'}.
        self.host_status = {}

    def set_host_status(self, node_state_tag):
        """Setter method.

        This method set host status by node_state tag of cib xml.

        :params node_state_tag: node_state tag of cib xml.
        """
        self.host_status[node_state_tag.get('uname')] = \
            node_state_tag.get('crmd')

    def get_host_status(self, hostname):
        """Getter method.

        This method returns the requested host status.
        host status is 'online' or 'offline'.

        :params hostname: Hostname to get status.

        :returns: Host status.
        """
        return self.host_status.get(hostname)
