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

from xml.etree import ElementTree

from oslo_log import log as oslo_logging

LOG = oslo_logging.getLogger(__name__)


class ParseCrmMonXml(object):
    """ParseCrmMonXml class

    This class parses the crmmon xml.
    """

    def __init__(self):
        self.crmmon_tag = None

    def set_crmmon_xml(self, crmmon_xml):
        """Set xml.etree.ElementTree.Element object.

        This method receives string of crmmon xml, and convert it
        to xml.etree.ElementTree.Element object.

        :params crmmon_xml: String of crmmon xml
        """
        # Convert xml.etree.ElementTree.Element object.
        self.crmmon_tag = ElementTree.fromstring(crmmon_xml)

    def _get_nodes(self):
        # status tag exists in the crmmon tag.
        if self.crmmon_tag is None:
            return None
        child_list = self.crmmon_tag.getchildren()
        for child in child_list:
            if child.tag == 'nodes':
                return child
        return None

    def _get_node_states(self, nodes_tag):
        node_state_tag_list = []

        # node_state tag exists in the status tag.
        child_list = nodes_tag.getchildren()
        for child in child_list:
            if child.tag == 'node':
                node_state_tag_list.append(child)

        return node_state_tag_list

    def get_node_state_tag_list(self):
        """Get node_state tag list.

        This method gets node_state tag list from crmmon xml.

        :returns: node_state tag list
        """
        # Get status tag.
        nodes_tag = self._get_nodes()
        if nodes_tag is None:
            LOG.error("crm_mon xml doesn't have nodes tag.")
            return []

        # Get node_state tag list.
        node_state_tag_list = self._get_node_states(nodes_tag)
        if len(node_state_tag_list) == 0:
            LOG.error("crm_mon xml doesn't have online tag.")

        return node_state_tag_list
