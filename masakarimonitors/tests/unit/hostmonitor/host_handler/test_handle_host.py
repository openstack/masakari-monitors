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

import socket
import testtools
from unittest import mock
from xml.etree import ElementTree

import eventlet
from oslo_utils import timeutils

import masakarimonitors.conf
from masakarimonitors.ha import masakari
from masakarimonitors.hostmonitor.host_handler import handle_host
from masakarimonitors.hostmonitor.host_handler import hold_host_status
from masakarimonitors.hostmonitor.host_handler import parse_cib_xml
from masakarimonitors.hostmonitor.host_handler import parse_crmmon_xml
from masakarimonitors.objects import event_constants as ec
from masakarimonitors import utils

eventlet.monkey_patch(os=False)

CONF = masakarimonitors.conf.CONF
STATUS_TAG_XML = '  <status>' \
                 '    <node_state crmd="online" uname="node1">' \
                 '      <test foo="foo"/>' \
                 '    </node_state>' \
                 '    <node_state crmd="online" uname="node2">' \
                 '      <test foo="foo"/>' \
                 '    </node_state>' \
                 '    <node_state crmd="online" uname="node3">' \
                 '      <test foo="foo"/>' \
                 '    </node_state>' \
                 '    <node_state crmd="offline" uname="node4">' \
                 '      <test foo="foo"/>' \
                 '    </node_state>' \
                 '    <node_state crmd="other" uname="node5">' \
                 '      <test foo="foo"/>' \
                 '    </node_state>' \
                 '  </status>'
CRMMON_NODES_TAG_XML = """
<nodes>
  <node name="member1" id="1002" online="true" standby="false"
        standby_onfail="false" maintenance="false" pending="false"
        unclean="false" shutdown="false" expected_up="true" is_dc="false"
        resources_running="2" type="member" />
  <node name="member2" id="1001" online="true" standby="false"
        standby_onfail="false" maintenance="false" pending="false"
        unclean="false" shutdown="false" expected_up="true" is_dc="true"
        resources_running="1" type="member" />
  <node name="remote1" id="remotehostname1" online="true" standby="false"
        standby_onfail="false" maintenance="false" pending="false"
        unclean="false" shutdown="false" expected_up="false"
        is_dc="false" resources_running="0" type="remote" />
  <node name="remote2" id="remotehostname2" online="true" standby="false"
        standby_onfail="false" maintenance="false" pending="false"
        unclean="false" shutdown="false" expected_up="false" is_dc="false"
        resources_running="0" type="remote" />
  <node name="remote3" id="remotehostname3" online="true" standby="false"
        standby_onfail="false" maintenance="false" pending="false"
        unclean="false" shutdown="false" expected_up="false" is_dc="false"
        resources_running="0" type="remote" />
  <node name="member3" id="1000" online="true" standby="false"
        standby_onfail="false" maintenance="false" pending="false"
        unclean="false" shutdown="false" expected_up="true" is_dc="false"
        resources_running="4" type="member" />
</nodes>
"""


class TestCibSchemaCompliantTag(testtools.TestCase):

    def setUp(self):
        super(TestCibSchemaCompliantTag, self).setUp()

    def test_init_offline(self):
        tag = handle_host.CibSchemaCompliantTag(
            {'name': 'test1', 'online': 'false'})
        self.assertEqual(tag['uname'], 'test1')
        self.assertEqual(tag['crmd'], 'offline')

    def test_init_online(self):
        tag = handle_host.CibSchemaCompliantTag(
            {'name': 'test1', 'online': 'true'})
        self.assertEqual(tag['uname'], 'test1')
        self.assertEqual(tag['crmd'], 'online')


class TestHandleHost(testtools.TestCase):

    def setUp(self):
        super(TestHandleHost, self).setUp()

    @mock.patch.object(utils, 'execute')
    def test_check_pacemaker_services(self, mock_execute):

        mock_execute.return_value = ('test_stdout', '')

        obj = handle_host.HandleHost()
        ret = obj._check_pacemaker_services('corosync')

        self.assertTrue(ret)
        mock_execute.assert_called_once_with(
            'systemctl', 'status', 'corosync', run_as_root=True)

    @mock.patch.object(utils, 'execute')
    def test_check_pacemaker_services_stderr(self, mock_execute):

        mock_execute.return_value = ('test_stdout', 'test_stderr')

        obj = handle_host.HandleHost()
        ret = obj._check_pacemaker_services('corosync')

        self.assertFalse(ret)
        mock_execute.assert_called_once_with(
            'systemctl', 'status', 'corosync', run_as_root=True)

    @mock.patch.object(utils, 'execute')
    @mock.patch.object(handle_host.HandleHost, '_check_pacemaker_services')
    def test_check_hb_line(
        self, mock_check_pacemaker_services, mock_execute):

        mock_check_pacemaker_services.side_effect = [True, True, False]
        interfaces = "enp0s8"
        ports = "5405"
        CONF.host.corosync_multicast_interfaces = interfaces
        CONF.host.corosync_multicast_ports = ports
        mock_execute.return_value = ('', '')

        obj = handle_host.HandleHost()
        ret = obj._check_hb_line()

        self.assertEqual(0, ret)
        self.assertEqual(3, mock_check_pacemaker_services.call_count)
        mock_check_pacemaker_services.assert_any_call('corosync')
        mock_check_pacemaker_services.assert_any_call('pacemaker')
        mock_check_pacemaker_services.assert_any_call('pacemaker_remote')
        cmd_str = ("timeout %s tcpdump -n -c 1 -p -i %s port %s") \
            % (CONF.host.tcpdump_timeout, interfaces, ports)
        command = cmd_str.split(' ')
        mock_execute.assert_called_once_with(*command, run_as_root=True)

    @mock.patch.object(handle_host.HandleHost, '_check_pacemaker_services')
    def test_check_hb_line_pacemaker_not_running(
        self, mock_check_pacemaker_services):

        mock_check_pacemaker_services.side_effect = [False, False, False]

        obj = handle_host.HandleHost()
        ret = obj._check_hb_line()

        self.assertEqual(2, ret)
        self.assertEqual(3, mock_check_pacemaker_services.call_count)
        mock_check_pacemaker_services.assert_any_call('corosync')
        mock_check_pacemaker_services.assert_any_call('pacemaker')
        mock_check_pacemaker_services.assert_any_call('pacemaker_remote')

    @mock.patch.object(handle_host.HandleHost, '_check_pacemaker_services')
    def test_check_hb_line_work_on_pacemaker_remote(
        self, mock_check_pacemaker_services):

        mock_check_pacemaker_services.side_effect = [False, False, True]

        obj = handle_host.HandleHost()
        ret = obj._check_hb_line()

        self.assertEqual(0, ret)
        self.assertEqual(3, mock_check_pacemaker_services.call_count)
        mock_check_pacemaker_services.assert_any_call('corosync')
        mock_check_pacemaker_services.assert_any_call('pacemaker')
        mock_check_pacemaker_services.assert_any_call('pacemaker_remote')

    @mock.patch.object(handle_host.HandleHost, '_check_pacemaker_services')
    def test_check_hb_line_conf_interfaces_is_none(
        self, mock_check_pacemaker_services):

        mock_check_pacemaker_services.side_effect = [True, True, False]
        interfaces = None
        ports = "5405"
        CONF.host.corosync_multicast_interfaces = interfaces
        CONF.host.corosync_multicast_ports = ports

        obj = handle_host.HandleHost()
        ret = obj._check_hb_line()

        self.assertEqual(2, ret)
        self.assertEqual(3, mock_check_pacemaker_services.call_count)
        mock_check_pacemaker_services.assert_any_call('corosync')
        mock_check_pacemaker_services.assert_any_call('pacemaker')
        mock_check_pacemaker_services.assert_any_call('pacemaker_remote')

    @mock.patch.object(handle_host.HandleHost, '_check_pacemaker_services')
    def test_check_hb_line_conf_ports_is_none(
        self, mock_check_pacemaker_services):

        mock_check_pacemaker_services.side_effect = [True, True, False]
        interfaces = "enp0s8"
        ports = None
        CONF.host.corosync_multicast_interfaces = interfaces
        CONF.host.corosync_multicast_ports = ports

        obj = handle_host.HandleHost()
        ret = obj._check_hb_line()

        self.assertEqual(2, ret)
        self.assertEqual(3, mock_check_pacemaker_services.call_count)
        mock_check_pacemaker_services.assert_any_call('corosync')
        mock_check_pacemaker_services.assert_any_call('pacemaker')
        mock_check_pacemaker_services.assert_any_call('pacemaker_remote')

    @mock.patch.object(handle_host.HandleHost, '_check_pacemaker_services')
    def test_check_hb_line_incorrect_interfaces(
        self, mock_check_pacemaker_services):

        mock_check_pacemaker_services.side_effect = [True, True, False]
        interfaces = "enp0s3,enp0s8"
        ports = "5405"
        CONF.host.corosync_multicast_interfaces = interfaces
        CONF.host.corosync_multicast_ports = ports

        obj = handle_host.HandleHost()
        ret = obj._check_hb_line()

        self.assertEqual(2, ret)
        self.assertEqual(3, mock_check_pacemaker_services.call_count)
        mock_check_pacemaker_services.assert_any_call('corosync')
        mock_check_pacemaker_services.assert_any_call('pacemaker')
        mock_check_pacemaker_services.assert_any_call('pacemaker_remote')

    @mock.patch.object(handle_host.HandleHost, '_check_pacemaker_services')
    def test_check_hb_line_incorrect_ports(
        self, mock_check_pacemaker_services):

        mock_check_pacemaker_services.side_effect = [True, True, False]
        interfaces = "enp0s8"
        ports = "5405,5406"
        CONF.host.corosync_multicast_interfaces = interfaces
        CONF.host.corosync_multicast_ports = ports

        obj = handle_host.HandleHost()
        ret = obj._check_hb_line()

        self.assertEqual(2, ret)
        self.assertEqual(3, mock_check_pacemaker_services.call_count)
        mock_check_pacemaker_services.assert_any_call('corosync')
        mock_check_pacemaker_services.assert_any_call('pacemaker')
        mock_check_pacemaker_services.assert_any_call('pacemaker_remote')

    @mock.patch.object(utils, 'execute')
    @mock.patch.object(handle_host.HandleHost, '_check_pacemaker_services')
    def test_check_hb_line_tcpdump_fail(
        self, mock_check_pacemaker_services, mock_execute):

        mock_check_pacemaker_services.side_effect = [True, True, False]
        interfaces = "enp0s8"
        ports = "5405"
        CONF.host.corosync_multicast_interfaces = interfaces
        CONF.host.corosync_multicast_ports = ports

        mock_execute.side_effect = Exception("Test exception.")

        obj = handle_host.HandleHost()
        ret = obj._check_hb_line()

        self.assertEqual(1, ret)
        self.assertEqual(3, mock_check_pacemaker_services.call_count)
        mock_check_pacemaker_services.assert_any_call('corosync')
        mock_check_pacemaker_services.assert_any_call('pacemaker')
        mock_check_pacemaker_services.assert_any_call('pacemaker_remote')
        cmd_str = ("timeout %s tcpdump -n -c 1 -p -i %s port %s") \
            % (CONF.host.tcpdump_timeout, interfaces, ports)
        command = cmd_str.split(' ')
        mock_execute.assert_called_once_with(*command, run_as_root=True)

    @mock.patch.object(utils, 'execute')
    def test_check_host_status_by_crmadmin_idle(self, mock_execute):
        my_hostname = socket.gethostname()
        crmadmin_stdout = "Status of crmd@%s: S_IDLE (ok)" % my_hostname
        mock_execute.return_value = (crmadmin_stdout, '')

        obj = handle_host.HandleHost()
        ret = obj._check_host_status_by_crmadmin()

        self.assertEqual(0, ret)
        mock_execute.assert_called_once_with(
            'crmadmin', '-S', my_hostname, run_as_root=True)

    @mock.patch.object(utils, 'execute')
    def test_check_host_status_by_crmadmin_not_dc(self, mock_execute):
        my_hostname = socket.gethostname()
        crmadmin_stdout = "Status of crmd@%s: S_NOT_DC (ok)" % my_hostname
        mock_execute.return_value = (crmadmin_stdout, '')

        obj = handle_host.HandleHost()
        ret = obj._check_host_status_by_crmadmin()

        self.assertEqual(0, ret)
        mock_execute.assert_called_once_with(
            'crmadmin', '-S', my_hostname, run_as_root=True)

    @mock.patch.object(utils, 'execute')
    def test_check_host_status_by_crmadmin_output_stderr(self, mock_execute):
        my_hostname = socket.gethostname()
        mock_execute.return_value = ('', 'crmadmin: command not found')

        obj = handle_host.HandleHost()
        ret = obj._check_host_status_by_crmadmin()

        self.assertEqual(1, ret)
        mock_execute.assert_called_once_with(
            'crmadmin', '-S', my_hostname, run_as_root=True)

    @mock.patch.object(utils, 'execute')
    def test_check_host_status_by_crmadmin_output_unexpected_message(
        self, mock_execute):
        my_hostname = socket.gethostname()
        mock_execute.return_value = ('Unexpected message.', '')

        obj = handle_host.HandleHost()
        ret = obj._check_host_status_by_crmadmin()

        self.assertEqual(1, ret)
        mock_execute.assert_called_once_with(
            'crmadmin', '-S', my_hostname, run_as_root=True)

    @mock.patch.object(utils, 'execute')
    def test_get_cib_xml(self, mock_execute):
        mock_execute.return_value = ('test_stdout', '')

        obj = handle_host.HandleHost()
        ret = obj._get_cib_xml()

        self.assertEqual('test_stdout', ret)
        mock_execute.assert_called_once_with(
            'cibadmin', '--query', run_as_root=True)

    @mock.patch.object(utils, 'execute')
    def test_get_cib_xml_output_stderr(self, mock_execute):
        mock_execute.return_value = ('test_stdout', 'test_stderr')

        obj = handle_host.HandleHost()
        ret = obj._get_cib_xml()

        self.assertIsNone(ret)
        mock_execute.assert_called_once_with(
            'cibadmin', '--query', run_as_root=True)

    @mock.patch.object(utils, 'execute')
    def test_get_crmmon_xml(self, mock_execute):
        mock_execute.return_value = ('test_stdout', '')

        obj = handle_host.HandleHost()
        ret = obj._get_crmmon_xml()

        self.assertEqual('test_stdout', ret)
        mock_execute.assert_called_once_with(
            'crm_mon', '-X', run_as_root=True)

    @mock.patch.object(utils, 'execute')
    def test_get_crmmon_xml_stderr(self, mock_execute):
        mock_execute.return_value = ('test_stdout', 'test_stderr')

        obj = handle_host.HandleHost()
        ret = obj._get_crmmon_xml()

        self.assertIsNone(ret)
        mock_execute.assert_called_once_with(
            'crm_mon', '-X', run_as_root=True)

    @mock.patch.object(utils, 'execute')
    @mock.patch.object(parse_cib_xml.ParseCibXml, 'get_stonith_ipmi_params')
    def test_is_poweroff(self, mock_get_stonith_ipmi_params, mock_execute):
        ipmi_values = {
            'userid': 'admin',
            'passwd': 'password',
            'interface': 'lanplus',
            'ipaddr': '0.0.0.0'
        }
        mock_get_stonith_ipmi_params.return_value = ipmi_values
        mock_execute.return_value = ('Chassis Power is off', '')

        obj = handle_host.HandleHost()
        ret = obj._is_poweroff('test_hostname')

        self.assertTrue(ret)
        cmd_str = ("timeout %s ipmitool -U %s -P %s -I %s -H %s "
                   "power status") \
            % (str(CONF.host.ipmi_timeout), ipmi_values['userid'],
               ipmi_values['passwd'], ipmi_values['interface'],
               ipmi_values['ipaddr'])
        command = cmd_str.split(' ')
        mock_execute.assert_called_once_with(*command, run_as_root=False)

    @mock.patch.object(utils, 'execute')
    @mock.patch.object(parse_cib_xml.ParseCibXml, 'get_stonith_ipmi_params')
    def test_is_poweroff_ipmi_values_is_none(
        self, mock_get_stonith_ipmi_params, mock_execute):
        mock_get_stonith_ipmi_params.return_value = None
        mock_execute.return_value = ('Chassis Power is off', '')

        obj = handle_host.HandleHost()
        ret = obj._is_poweroff('test_hostname')

        self.assertFalse(ret)
        mock_execute.assert_not_called()

    @mock.patch.object(eventlet.greenthread, 'sleep')
    @mock.patch.object(utils, 'execute')
    @mock.patch.object(parse_cib_xml.ParseCibXml, 'get_stonith_ipmi_params')
    def test_is_poweroff_output_stderr(
        self, mock_get_stonith_ipmi_params, mock_execute, mock_sleep):
        ipmi_values = {
            'userid': 'admin',
            'passwd': 'password',
            'interface': 'lanplus',
            'ipaddr': '0.0.0.0'
        }
        mock_get_stonith_ipmi_params.return_value = ipmi_values
        mock_execute.return_value = ('Chassis Power is off', 'test_stderr')
        mock_sleep.return_value = None

        obj = handle_host.HandleHost()
        ret = obj._is_poweroff('test_hostname')

        self.assertFalse(ret)
        cmd_str = ("timeout %s ipmitool -U %s -P %s -I %s -H %s "
                   "power status") \
            % (str(CONF.host.ipmi_timeout), ipmi_values['userid'],
               ipmi_values['passwd'], ipmi_values['interface'],
               ipmi_values['ipaddr'])
        command = cmd_str.split(' ')
        calls = [mock.call(*command, run_as_root=False),
                 mock.call(*command, run_as_root=False),
                 mock.call(*command, run_as_root=False),
                 mock.call(*command, run_as_root=False)]
        mock_execute.assert_has_calls(calls)

    @mock.patch.object(eventlet.greenthread, 'sleep')
    @mock.patch.object(utils, 'execute')
    @mock.patch.object(parse_cib_xml.ParseCibXml, 'get_stonith_ipmi_params')
    def test_is_poweroff_output_unexpected_message(
        self, mock_get_stonith_ipmi_params, mock_execute, mock_sleep):
        ipmi_values = {
            'userid': 'admin',
            'passwd': 'password',
            'interface': 'lanplus',
            'ipaddr': '0.0.0.0'
        }
        mock_get_stonith_ipmi_params.return_value = ipmi_values
        mock_execute.return_value = ('Unexpected message.', '')
        mock_sleep.return_value = None

        obj = handle_host.HandleHost()
        ret = obj._is_poweroff('test_hostname')

        self.assertFalse(ret)
        cmd_str = ("timeout %s ipmitool -U %s -P %s -I %s -H %s "
                   "power status") \
            % (str(CONF.host.ipmi_timeout), ipmi_values['userid'],
               ipmi_values['passwd'], ipmi_values['interface'],
               ipmi_values['ipaddr'])
        command = cmd_str.split(' ')
        calls = [mock.call(*command, run_as_root=False),
                 mock.call(*command, run_as_root=False),
                 mock.call(*command, run_as_root=False),
                 mock.call(*command, run_as_root=False)]
        mock_execute.assert_has_calls(calls)

    @mock.patch.object(timeutils, 'utcnow')
    def test_make_event_online(self, mock_utcnow):
        current_time = timeutils.utcnow()
        mock_utcnow.return_value = current_time

        obj = handle_host.HandleHost()
        hostname = 'test_hostname'
        current_status = 'online'
        ret = obj._make_event(hostname, current_status)

        event_type = ec.EventConstants.EVENT_STARTED
        cluster_status = current_status.upper()
        host_status = ec.EventConstants.HOST_STATUS_NORMAL
        event = {
            'notification': {
                'type': ec.EventConstants.TYPE_COMPUTE_HOST,
                'hostname': hostname,
                'generated_time': current_time,
                'payload': {
                    'event': event_type,
                    'cluster_status': cluster_status,
                    'host_status': host_status
                }
            }
        }
        self.assertEqual(event, ret)

    @mock.patch.object(timeutils, 'utcnow')
    @mock.patch.object(handle_host.HandleHost, '_is_poweroff')
    def test_make_event_offline_disable_ipmi_check_false_poweroff(
        self, mock_is_poweroff, mock_utcnow):
        mock_is_poweroff.return_value = True
        current_time = timeutils.utcnow()
        mock_utcnow.return_value = current_time
        CONF.host.disable_ipmi_check = False

        obj = handle_host.HandleHost()
        hostname = 'test_hostname'
        current_status = 'offline'
        ret = obj._make_event(hostname, current_status)

        event_type = ec.EventConstants.EVENT_STOPPED
        cluster_status = current_status.upper()
        host_status = ec.EventConstants.HOST_STATUS_NORMAL
        event = {
            'notification': {
                'type': ec.EventConstants.TYPE_COMPUTE_HOST,
                'hostname': hostname,
                'generated_time': current_time,
                'payload': {
                    'event': event_type,
                    'cluster_status': cluster_status,
                    'host_status': host_status
                }
            }
        }
        self.assertEqual(event, ret)
        mock_is_poweroff.assert_called_once_with(hostname)

    @mock.patch.object(timeutils, 'utcnow')
    @mock.patch.object(handle_host.HandleHost, '_is_poweroff')
    def test_make_event_offline_disable_ipmi_check_false_poweron(
        self, mock_is_poweroff, mock_utcnow):
        mock_is_poweroff.return_value = False
        current_time = timeutils.utcnow()
        mock_utcnow.return_value = current_time
        CONF.host.disable_ipmi_check = False

        obj = handle_host.HandleHost()
        hostname = 'test_hostname'
        current_status = 'offline'
        ret = obj._make_event(hostname, current_status)

        event_type = ec.EventConstants.EVENT_STOPPED
        cluster_status = current_status.upper()
        host_status = ec.EventConstants.HOST_STATUS_UNKNOWN
        event = {
            'notification': {
                'type': ec.EventConstants.TYPE_COMPUTE_HOST,
                'hostname': hostname,
                'generated_time': current_time,
                'payload': {
                    'event': event_type,
                    'cluster_status': cluster_status,
                    'host_status': host_status
                }
            }
        }
        self.assertEqual(event, ret)
        mock_is_poweroff.assert_called_once_with(hostname)

    @mock.patch.object(timeutils, 'utcnow')
    def test_make_event_offline_disable_ipmi_check_true(self, mock_utcnow):
        current_time = timeutils.utcnow()
        mock_utcnow.return_value = current_time
        CONF.host.disable_ipmi_check = True

        obj = handle_host.HandleHost()
        hostname = 'test_hostname'
        current_status = 'offline'
        ret = obj._make_event(hostname, current_status)

        event_type = ec.EventConstants.EVENT_STOPPED
        cluster_status = current_status.upper()
        host_status = ec.EventConstants.HOST_STATUS_NORMAL
        event = {
            'notification': {
                'type': ec.EventConstants.TYPE_COMPUTE_HOST,
                'hostname': hostname,
                'generated_time': current_time,
                'payload': {
                    'event': event_type,
                    'cluster_status': cluster_status,
                    'host_status': host_status
                }
            }
        }
        self.assertEqual(event, ret)

    @mock.patch.object(masakari.SendNotification, 'send_notification')
    @mock.patch.object(handle_host.HandleHost, '_make_event')
    @mock.patch.object(hold_host_status.HostHoldStatus, 'set_host_status')
    @mock.patch.object(hold_host_status.HostHoldStatus, 'get_host_status')
    @mock.patch.object(socket, 'gethostname')
    def test_check_if_status_changed(
        self, mock_gethostname, mock_get_host_status, mock_set_host_status,
        mock_make_event, mock_send_notification):
        mock_gethostname.return_value = 'node1'
        mock_get_host_status.side_effect = \
            [None, 'online', 'online', 'online']
        mock_set_host_status.return_value = None
        test_event = {'notification': 'test'}
        mock_make_event.return_value = test_event

        status_tag = ElementTree.fromstring(STATUS_TAG_XML)
        node_state_tag_list = status_tag.getchildren()

        obj = handle_host.HandleHost()
        obj._check_if_status_changed(node_state_tag_list)

        node_state_node2 = node_state_tag_list[1]
        node_state_node3 = node_state_tag_list[2]
        node_state_node4 = node_state_tag_list[3]
        node_state_node5 = node_state_tag_list[4]
        node2 = node_state_node2.get('uname')
        node3 = node_state_node3.get('uname')
        node4 = node_state_node4.get('uname')
        node5 = node_state_node5.get('uname')
        calls_get_host_status = [mock.call(node2),
                                 mock.call(node3),
                                 mock.call(node4),
                                 mock.call(node5)]
        calls_set_host_status = [mock.call(node_state_node2),
                                 mock.call(node_state_node3),
                                 mock.call(node_state_node4),
                                 mock.call(node_state_node5)]
        mock_get_host_status.assert_has_calls(calls_get_host_status)
        mock_set_host_status.assert_has_calls(calls_set_host_status)
        mock_make_event.assert_called_once_with(node4, 'offline')
        mock_send_notification.assert_called_once_with(
            CONF.host.api_retry_max, CONF.host.api_retry_interval, test_event)

    @mock.patch.object(handle_host.HandleHost, '_check_if_status_changed')
    @mock.patch.object(parse_crmmon_xml.ParseCrmMonXml,
                       'get_node_state_tag_list')
    @mock.patch.object(parse_crmmon_xml.ParseCrmMonXml, 'set_crmmon_xml')
    @mock.patch.object(handle_host.HandleHost, '_get_crmmon_xml')
    def test_check_host_status_by_crm_mon(
        self, mock_get_crmmon_xml, mock_set_crmmon_xml,
        mock_get_node_state_tag_list, mock_check_if_status_changed):
        mock_get_crmmon_xml.return_value = CRMMON_NODES_TAG_XML
        mock_set_crmmon_xml.return_value = None
        status_tag = ElementTree.fromstring(CRMMON_NODES_TAG_XML)
        node_state_tag_list = status_tag.getchildren()
        mock_get_node_state_tag_list.return_value = node_state_tag_list
        mock_check_if_status_changed.return_value = None

        obj = handle_host.HandleHost()
        ret = obj._check_host_status_by_crm_mon()

        self.assertEqual(0, ret)
        mock_get_node_state_tag_list.assert_called_once_with()
        mock_set_crmmon_xml.assert_called_once_with(CRMMON_NODES_TAG_XML)
        mock_get_node_state_tag_list.assert_called_once_with()
        mock_check_if_status_changed.assert_called_once_with(
            [
                {'uname': 'remote1', 'crmd': 'online'},
                {'uname': 'remote2', 'crmd': 'online'},
                {'uname': 'remote3', 'crmd': 'online'}])

    @mock.patch.object(parse_crmmon_xml.ParseCrmMonXml,
                       'get_node_state_tag_list')
    @mock.patch.object(parse_crmmon_xml.ParseCrmMonXml, 'set_crmmon_xml')
    @mock.patch.object(handle_host.HandleHost, '_get_crmmon_xml')
    def test_check_host_status_by_crm_mon_not_have_node_state_tag(
        self, mock_get_crmmon_xml, mock_set_crmmon_xml,
        mock_get_node_state_tag_list):
        mock_get_crmmon_xml.return_value = CRMMON_NODES_TAG_XML
        mock_set_crmmon_xml.return_value = None
        mock_get_node_state_tag_list.return_value = []

        obj = handle_host.HandleHost()

        self.assertRaisesRegexp(
            Exception, "Failed to get nodes tag from crm_mon xml.",
            obj._check_host_status_by_crm_mon)
        mock_get_crmmon_xml.assert_called_once_with()
        mock_set_crmmon_xml.assert_called_once_with(CRMMON_NODES_TAG_XML)
        mock_get_node_state_tag_list.assert_called_once_with()

    @mock.patch.object(handle_host.HandleHost, '_get_crmmon_xml')
    def test_check_host_status_by_crm_mon_xml_is_None(
        self, mock_get_crmmon_xml):
        mock_get_crmmon_xml.return_value = None

        obj = handle_host.HandleHost()
        ret = obj._check_host_status_by_crm_mon()

        self.assertEqual(1, ret)
        mock_get_crmmon_xml.assert_called_once_with()

    @mock.patch.object(handle_host.HandleHost, '_check_if_status_changed')
    @mock.patch.object(parse_cib_xml.ParseCibXml, 'get_node_state_tag_list')
    @mock.patch.object(parse_cib_xml.ParseCibXml, 'have_quorum')
    @mock.patch.object(parse_cib_xml.ParseCibXml, 'set_cib_xml')
    @mock.patch.object(handle_host.HandleHost, '_get_cib_xml')
    def test_check_host_status_by_cibadmin(
        self, mock_get_cib_xml, mock_set_cib_xml, mock_have_quorum,
        mock_get_node_state_tag_list, mock_check_if_status_changed):
        mock_get_cib_xml.return_value = STATUS_TAG_XML
        mock_set_cib_xml.return_value = None
        mock_have_quorum.return_value = 1
        status_tag = ElementTree.fromstring(STATUS_TAG_XML)
        node_state_tag_list = status_tag.getchildren()
        mock_get_node_state_tag_list.return_value = node_state_tag_list
        mock_check_if_status_changed.return_value = None

        obj = handle_host.HandleHost()
        ret = obj._check_host_status_by_cibadmin()

        self.assertEqual(0, ret)
        mock_get_cib_xml.assert_called_once_with()
        mock_set_cib_xml.assert_called_once_with(STATUS_TAG_XML)
        mock_have_quorum.assert_called_once_with()
        mock_get_node_state_tag_list.assert_called_once_with()
        mock_check_if_status_changed.assert_called_once_with(
            node_state_tag_list)

    @mock.patch.object(handle_host.HandleHost, '_check_if_status_changed')
    @mock.patch.object(parse_cib_xml.ParseCibXml, 'get_node_state_tag_list')
    @mock.patch.object(parse_cib_xml.ParseCibXml, 'have_quorum')
    @mock.patch.object(parse_cib_xml.ParseCibXml, 'set_cib_xml')
    @mock.patch.object(handle_host.HandleHost, '_get_cib_xml')
    def test_check_host_status_by_cibadmin_no_quorum(
        self, mock_get_cib_xml, mock_set_cib_xml, mock_have_quorum,
        mock_get_node_state_tag_list, mock_check_if_status_changed):
        mock_get_cib_xml.return_value = STATUS_TAG_XML
        mock_set_cib_xml.return_value = None
        mock_have_quorum.return_value = 0
        status_tag = ElementTree.fromstring(STATUS_TAG_XML)
        node_state_tag_list = status_tag.getchildren()
        mock_get_node_state_tag_list.return_value = node_state_tag_list
        mock_check_if_status_changed.return_value = None

        obj = handle_host.HandleHost()
        ret = obj._check_host_status_by_cibadmin()

        self.assertEqual(0, ret)
        mock_get_cib_xml.assert_called_once_with()
        mock_set_cib_xml.assert_called_once_with(STATUS_TAG_XML)
        mock_have_quorum.assert_called_once_with()
        mock_get_node_state_tag_list.assert_called_once_with()
        mock_check_if_status_changed.assert_called_once_with(
            node_state_tag_list)

    @mock.patch.object(handle_host.HandleHost, '_get_cib_xml')
    def test_check_host_status_by_cibadmin_cib_xml_is_None(
        self, mock_get_cib_xml):
        mock_get_cib_xml.return_value = None

        obj = handle_host.HandleHost()
        ret = obj._check_host_status_by_cibadmin()

        self.assertEqual(1, ret)
        mock_get_cib_xml.assert_called_once_with()

    @mock.patch.object(parse_cib_xml.ParseCibXml, 'get_node_state_tag_list')
    @mock.patch.object(parse_cib_xml.ParseCibXml, 'have_quorum')
    @mock.patch.object(parse_cib_xml.ParseCibXml, 'set_cib_xml')
    @mock.patch.object(handle_host.HandleHost, '_get_cib_xml')
    def test_check_host_status_by_cibadmin_not_have_node_state_tag(
        self, mock_get_cib_xml, mock_set_cib_xml, mock_have_quorum,
        mock_get_node_state_tag_list):
        mock_get_cib_xml.return_value = STATUS_TAG_XML
        mock_set_cib_xml.return_value = None
        mock_have_quorum.return_value = 1
        mock_get_node_state_tag_list.return_value = []

        obj = handle_host.HandleHost()

        self.assertRaisesRegexp(
            Exception, "Failed to get node_state tag from cib xml.",
            obj._check_host_status_by_cibadmin)
        mock_get_cib_xml.assert_called_once_with()
        mock_set_cib_xml.assert_called_once_with(STATUS_TAG_XML)
        mock_have_quorum.assert_called_once_with()
        mock_get_node_state_tag_list.assert_called_once_with()

    def test_stop(self):

        obj = handle_host.HandleHost()
        obj.stop()

        self.assertFalse(obj.running)

    @mock.patch.object(eventlet.greenthread, 'sleep')
    @mock.patch.object(handle_host.HandleHost,
                       '_check_host_status_by_cibadmin')
    @mock.patch.object(handle_host.HandleHost,
                       '_check_host_status_by_crmadmin')
    @mock.patch.object(handle_host.HandleHost, '_check_pacemaker_services')
    @mock.patch.object(handle_host.HandleHost, '_check_hb_line')
    def test_monitor_hosts(self,
                           mock_check_hb_line,
                           mock_check_pacemaker_services,
                           mock_check_host_status_by_cibadmin,
                           mock_check_host_status_by_crmadmin,
                           mock_sleep):

        mock_check_hb_line.side_effect = \
            [0, 1, 2, 0, Exception("Test exception.")]
        mock_check_pacemaker_services.side_effect = [True, False, False]
        mock_check_host_status_by_cibadmin.side_effect = [0, 1]
        mock_check_host_status_by_crmadmin.side_effect = [0, 1]
        mock_sleep.return_value = None

        obj = handle_host.HandleHost()
        obj.monitor_hosts()

        self.assertEqual(5, mock_check_hb_line.call_count)
        self.assertEqual(3, mock_check_pacemaker_services.call_count)
        mock_check_pacemaker_services.assert_called_with('pacemaker_remote')
        self.assertEqual(2, mock_check_host_status_by_cibadmin.call_count)
        self.assertEqual(2, mock_check_host_status_by_crmadmin.call_count)

    @mock.patch.object(eventlet.greenthread, 'sleep')
    @mock.patch.object(handle_host.HandleHost,
                       '_check_host_status_by_crm_mon')
    @mock.patch.object(handle_host.HandleHost, '_check_pacemaker_services')
    @mock.patch.object(handle_host.HandleHost, '_check_hb_line')
    def test_monitor_hosts_remotes_only(self,
                                        mock_check_hb_line,
                                        mock_check_pacemaker_services,
                                        mock_check_host_status_by_crm_mon,
                                        mock_sleep):

        CONF.host.restrict_to_remotes = True
        mock_check_hb_line.side_effect = \
            [0, Exception("Test exception.")]
        mock_check_pacemaker_services.return_value = True
        mock_check_host_status_by_crm_mon.side_effect = 0
        mock_sleep.return_value = None

        obj = handle_host.HandleHost()
        obj.monitor_hosts()

        self.assertEqual(1, mock_check_hb_line.call_count)
        self.assertEqual(1, mock_check_pacemaker_services.call_count)
        mock_check_pacemaker_services.assert_called_with('pacemaker_remote')
        self.assertEqual(1, mock_check_host_status_by_crm_mon.call_count)
        mock_check_host_status_by_crm_mon.assert_called_once_with()
