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
            LOG.error("Cib xml doesn't have status tag.")
            return []

        # Get node_state tag list.
        node_state_tag_list = self._get_node_states(status_tag)
        if len(node_state_tag_list) == 0:
            LOG.error("Cib xml doesn't have node_state tag.")

        return node_state_tag_list

    def _parse_instance_attributes_tag(self,
                                       instance_attributes_tag, hostname):
        # Parse nvpair tag under the instance_attributes tag.
        is_target_ipmi = False
        ipmi_values = {}

        nvpair_tag_list = instance_attributes_tag.getchildren()
        for nvpair_tag in nvpair_tag_list:
            if nvpair_tag.get('name') == 'hostname' and \
                nvpair_tag.get('value') == hostname:
                is_target_ipmi = True
            elif nvpair_tag.get('name') == 'ipaddr':
                ipmi_values['ipaddr'] = nvpair_tag.get('value')
            elif nvpair_tag.get('name') == 'userid':
                ipmi_values['userid'] = nvpair_tag.get('value')
            elif nvpair_tag.get('name') == 'passwd':
                ipmi_values['passwd'] = nvpair_tag.get('value')
            elif nvpair_tag.get('name') == 'interface':
                ipmi_values['interface'] = nvpair_tag.get('value')

        if is_target_ipmi is True:
            return ipmi_values
        else:
            return None

    def _parse_primitive_tag(self, primitive_tag, hostname):
        if primitive_tag.get('type') != 'external/ipmi':
            return None

        # Parse instance_attributes tag under the primitive tag.
        child_list = primitive_tag.getchildren()
        for child in child_list:
            if child.tag == 'instance_attributes':
                ipmi_values = self._parse_instance_attributes_tag(
                    child, hostname)
                if ipmi_values is not None:
                    return ipmi_values
        return None

    def _parse_group_tag(self, group_tag, hostname):
        # Parse primitive tag under the group tag.
        child_list = group_tag.getchildren()
        for child in child_list:
            if child.tag == 'primitive':
                ipmi_values = self._parse_primitive_tag(child, hostname)
                if ipmi_values is not None:
                    return ipmi_values
        return None

    def get_stonith_ipmi_params(self, hostname):
        """Get stonith ipmi params from cib xml.

        This method gets params of ipmi resource agent(RA) which is set on
        resources tag.
        The resources tag exsists under the configuration tag.
        And it is assumed that ipmi RA belongs to some resource group.

        :params hostname: hostname

        :returns: Dictionary of ipmi RA's params.
                  They are ipaddr, userid, passwd and interface.
        """
        # Get configuration tag from cib tag.
        configuration_tag = None
        child_list = self.cib_tag.getchildren()
        for child in child_list:
            if child.tag == 'configuration':
                configuration_tag = child
                break
        if configuration_tag is None:
            LOG.error("Cib xml doesn't have configuration tag.")
            return None

        # Get resources tag from configuration tag.
        resources_tag = None
        child_list = configuration_tag.getchildren()
        for child in child_list:
            if child.tag == 'resources':
                resources_tag = child
                break
        if resources_tag is None:
            LOG.error("Cib xml doesn't have resources tag.")
            return None

        # They are set at nvpair tag which exists under the
        # instance_attributes of primitive of group tag.
        ipmi_values = None
        child_list = resources_tag.getchildren()
        for child in child_list:
            if child.tag == 'group':
                ipmi_values = self._parse_group_tag(child, hostname)
                if ipmi_values is not None:
                    break

        return ipmi_values
