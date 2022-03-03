# Copyright(c) 2021 Inspur
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
from unittest import mock

from oslo_config import fixture as fixture_config

from masakarimonitors.hostmonitor.consul_check import consul_helper


class FakerAgentMembers(object):

    def __init__(self):
        self.agent_members = []

    def create_agent(self, name, status=1):
        agent = {
            'Name': name,
            'Status': status,
            'Port': 'agent_lan_port',
            'Addr': 'agent_ip',
            'Tags': {
                'dc': 'storage',
                'role': 'consul',
                'port': 'agent_server_port',
                'wan_join_port': 'agent_wan_port',
                'expect': '3',
                'id': 'agent_id',
                'vsn_max': '3',
                'vsn_min': '2',
                'vsn': '2',
                'raft_vsn': '2',
            },
            'ProtocolMax': 5,
            'ProtocolMin': 1,
            'ProtocolCur': 2,
            'DelegateMax': 5,
            'DelegateMin': 2,
            'DelegateCur': 4,
        }

        self.agent_members.append(agent)

    def generate_agent_members(self):
        return self.agent_members


class TestConsulManager(testtools.TestCase):

    def setUp(self):
        super(TestConsulManager, self).setUp()
        self.CONF = self.useFixture(fixture_config.Config()).conf
        self.consul_manager = consul_helper.ConsulManager(self.CONF)
        self.consul_manager.agents = {
            'manage': consul_helper.ConsulAgent('manage'),
            'tenant': consul_helper.ConsulAgent('tenant'),
            'storage': consul_helper.ConsulAgent('storage'),
        }

    def test_get_health(self):
        fake_manage_agents = FakerAgentMembers()
        fake_manage_agents.create_agent('node01', status=1)
        fake_manage_agents.create_agent('node02', status=1)
        fake_manage_agents.create_agent('node03', status=1)
        agent_manage_members = fake_manage_agents.generate_agent_members()

        fake_tenant_agents = FakerAgentMembers()
        fake_tenant_agents.create_agent('node01', status=1)
        fake_tenant_agents.create_agent('node02', status=1)
        fake_tenant_agents.create_agent('node03', status=1)
        agent_tenant_members = fake_tenant_agents.generate_agent_members()

        fake_storage_agents = FakerAgentMembers()
        fake_storage_agents.create_agent('node01', status=1)
        fake_storage_agents.create_agent('node02', status=1)
        fake_storage_agents.create_agent('node03', status=3)
        agent_storage_members = fake_storage_agents.generate_agent_members()

        with mock.patch.object(self.consul_manager.agents['manage'],
                'get_agents', return_value=agent_manage_members):
            with mock.patch.object(self.consul_manager.agents['tenant'],
                    'get_agents', return_value=agent_tenant_members):
                with mock.patch.object(self.consul_manager.agents['storage'],
                        'get_agents', return_value=agent_storage_members):
                    excepted_health = {
                        "node01": ['up', 'up', 'up'],
                        "node02": ['up', 'up', 'up'],
                        "node03": ['up', 'up', 'down'],
                    }
                    sequence = ['manage', 'tenant', 'storage']
                    agents_health = self.consul_manager.get_health(sequence)
                    self.assertEqual(excepted_health, agents_health)


class TestConsulAgent(testtools.TestCase):

    def setUp(self):
        super(TestConsulAgent, self).setUp()
        self.consul_agent = consul_helper.ConsulAgent('test')

    def test_get_health(self):
        fake_agents = FakerAgentMembers()
        fake_agents.create_agent('node01', status=1)
        fake_agents.create_agent('node02', status=1)
        fake_agents.create_agent('node03', status=3)
        agent_members = fake_agents.generate_agent_members()

        with mock.patch.object(self.consul_agent, 'get_agents',
                return_value=agent_members):
            excepted_health = {
                "node01": 'up',
                "node02": 'up',
                "node03": 'down',
            }
            agents_health = self.consul_agent.get_health()
            self.assertEqual(excepted_health, agents_health)
