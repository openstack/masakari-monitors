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

"""
Main abstraction layer for retrieving node status from consul
"""

import consul

from masakarimonitors.i18n import _


class ConsulException(Exception):
    """Base Consul Exception"""
    msg_fmt = _("An unknown exception occurred.")

    def __init__(self, message=None, **kwargs):
        if not message:
            message = self.msg_fmt % kwargs

        super(ConsulException, self).__init__(message)


class ConsulAgentNotExist(ConsulException):
    msg_fmt = _("Consul agent of %(cluster)s not exist.")


class ConsulGetMembersException(ConsulException):
    msg_fmt = _("Failed to get members of %(cluster)s: %(err)s.")


class ConsulManager(object):
    """Consul manager class

    This class helps to pull health data from all consul clusters,
    and return health data in sequence.
    """

    def __init__(self, CONF):
        self.agents = {}
        self.init_agents(CONF)

    def init_agents(self, CONF):
        if CONF.consul.agent_manage:
            addr, port = CONF.consul.agent_manage.split(':')
            self.agents['manage'] = ConsulAgent('manage', addr, port)
        if CONF.consul.agent_tenant:
            addr, port = CONF.consul.agent_tenant.split(':')
            self.agents['tenant'] = ConsulAgent('tenant', addr, port)
        if CONF.consul.agent_storage:
            addr, port = CONF.consul.agent_storage.split(':')
            self.agents['storage'] = ConsulAgent('storage', addr, port)

    def valid_agents(self, sequence):
        for name in sequence:
            if self.agents.get(name) is None:
                raise ConsulAgentNotExist(cluster=name)

    def get_health(self, sequence):
        hosts_health = {}
        all_agents = []
        for name in sequence:
            consul_agent = self.agents.get(name)
            agent_health = consul_agent.get_health()
            hosts_health[name] = agent_health
            if not all_agents:
                all_agents = agent_health.keys()

        sequence_hosts_health = {}
        for host in all_agents:
            sequence_hosts_health[host] = []
            for name in sequence:
                state = hosts_health[name].get(host)
                if state:
                    sequence_hosts_health[host].append(state)
                else:
                    continue

        return sequence_hosts_health


class ConsulAgent(object):
    """Agent to consul cluster"""

    def __init__(self, name, addr=None, port=None):
        self.name = name
        self.addr = addr
        self.port = port
        # connection to consul cluster
        self.cluster = consul.Consul(host=addr, port=self.port)

    def get_agents(self):
        try:
            members = self.cluster.agent.members()
        except Exception as e:
            raise ConsulGetMembersException(cluster=self.name, err=str(e))

        return members

    def get_health(self):
        agents_health = {}
        agents = self.get_agents()
        for agent in agents:
            host = agent.get('Name')
            status = agent.get('Status')
            if status == 1:
                agents_health[host] = 'up'
            else:
                agents_health[host] = 'down'

        return agents_health
