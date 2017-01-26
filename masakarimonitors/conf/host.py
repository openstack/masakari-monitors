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
from oslo_config import cfg

monitor_host_opts = [
    cfg.StrOpt('monitoring_driver',
               default='default',
               help='Driver that hostmonitor uses for monitoring hosts.'),
    cfg.IntOpt('monitoring_interval',
               default=60,
               help='Monitoring interval(in seconds) of node status.'),
    cfg.IntOpt('api_retry_max',
               default=12,
               help='Number of retries for send a notification in'
                    ' processmonitor.'),
    cfg.IntOpt('api_retry_interval',
               default=10,
               help='Trial interval of time of the notification processing'
                    ' is error(in seconds).'),
    cfg.BoolOpt('disable_ipmi_check',
                default=False,
                help='''
Do not check whether the host is completely down.

Possible values:

* True: Do not check whether the host is completely down.
* False: Do check whether the host is completely down.

If ipmi RA is not set in pacemaker, this value should be set True.
'''),
    cfg.IntOpt('ipmi_timeout',
               default=5,
               help='Timeout value(in seconds) of the ipmitool command.'),
    cfg.IntOpt('ipmi_retry_max',
               default=3,
               help='Number of ipmitool command retries.'),
    cfg.IntOpt('ipmi_retry_interval',
               default=10,
               help='Retry interval(in seconds) of the ipmitool command.'),
    cfg.IntOpt('stonith_wait',
               default=30,
               help='Standby time(in seconds) until activate STONITH.'),
    cfg.IntOpt('tcpdump_timeout',
               default=5,
               help='Timeout value(in seconds) of the tcpdump command when'
                    ' monitors the corosync communication.'),
    cfg.StrOpt('corosync_multicast_interfaces',
               help='''
The name of interface that corosync is using for mutual communication
between hosts.
If there are multiple interfaces, specify them in comma-separated
like 'enp0s3,enp0s8'.
The number of interfaces you specify must be equal to the number of
corosync_multicast_ports values and must be in correct order with relevant
ports in corosync_multicast_ports.
'''),
    cfg.StrOpt('corosync_multicast_ports',
               help='''
The port numbers that corosync is using for mutual communication
between hosts.
If there are multiple port numbers, specify them in comma-separated
like '5405,5406'.
The number of port numbers you specify must be equal to the number of
corosync_multicast_interfaces values and must be in correct order with
relevant interfaces in corosync_multicast_interfaces.
'''),
]


def register_opts(conf):
    conf.register_opts(monitor_host_opts, group='host')


def list_opts():
    return {
        'host': monitor_host_opts
    }
