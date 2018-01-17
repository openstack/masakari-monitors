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

from oslo_config import cfg

service_opts = [
    cfg.StrOpt('host',
               default=socket.gethostname(),
               help='''
Hostname, FQDN or IP address of this host. Must be valid within AMQP key.

Possible values:

* String with hostname, FQDN or IP address. Default is hostname of this host.
'''),
    cfg.StrOpt('instancemonitor_manager',
               default='masakarimonitors.instancemonitor.instance'
                       '.InstancemonitorManager',
               help='Full class name for the Manager for instancemonitor.'),
    cfg.StrOpt('introspectiveinstancemonitor_manager',
               default='masakarimonitors.introspectiveinstancemonitor.instance'
                       '.IntrospectiveInstanceMonitorManager',
               help='Full class name for introspectiveinstancemonitor.'),
    cfg.StrOpt('processmonitor_manager',
               default='masakarimonitors.processmonitor.process'
                       '.ProcessmonitorManager',
               help='Full class name for the Manager for processmonitor.'),
    cfg.StrOpt('hostmonitor_manager',
               default='masakarimonitors.hostmonitor.host'
                       '.HostmonitorManager',
               help='Full class name for the Manager for hostmonitor.'),
    ]


def register_opts(conf):
    conf.register_opts(service_opts)


def list_opts():
    return {'DEFAULT': service_opts}
