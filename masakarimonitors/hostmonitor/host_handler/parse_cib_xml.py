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

from xml.etree import ElementTree

from oslo_log import log as oslo_logging

from masakarimonitors.i18n import _LE

LOG = oslo_logging.getLogger(__name__)


class ParseCibXml(object):
    """ParseCibXml class

    This class parses the cib xml.
    """

    def __init__(self):
        self.cib_tag = None

    def set_cib_xml(self, cib_xml):
        """Set xml.etree.ElementTree.Element object.

        This method recieves string of cib xml, and convert it
        to xml.etree.ElementTree.Element object.

        :params cib_xml: String of cib xml
        """
        # Convert xml.etree.ElementTree.Element object.
        self.cib_tag = ElementTree.fromstring(cib_xml)

    def have_quorum(self):
        """Returns if cluster has quorum or not.

        :returns: 0 on no-quorum, 1 if cluster has quorum.
        """
        return int(self.cib_tag.get('have-quorum'))

    def _get_status_tag(self):
        # status tag exists in the cib tag.
        child_list = self.cib_tag.getchildren()
        for child in child_list:
            if child.tag == 'status':
                return child
        return None

    def _get_node_states(self, status_tag):
        node_state_tag_list = []

        # node_state tag exists in the status tag.
        child_list = status_tag.getchildren()
        for child in child_list:
            if child.tag == 'node_state':
                node_state_tag_list.append(child)

        return node_state_tag_list

    def get_node_state_tag_list(self):
        """Get node_state tag list.

        This method gets node_state tag list from cib xml.

        :returns: node_state tag list
        """
        # Get status tag.
        status_tag = self._get_status_tag()
        if status_tag is None:
            LOG.error(_LE("Cib xml doesn't have status tag."))
            return []

        # Get node_state tag list.
        node_state_tag_list = self._get_node_states(status_tag)
        if len(node_state_tag_list) == 0:
            LOG.error(_LE("Cib xml doesn't have node_state tag."))

        return node_state_tag_list
