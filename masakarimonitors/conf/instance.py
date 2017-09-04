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


monitor_callback_opts = [
    cfg.IntOpt('retry_max',
               default=12,
               help='Number of retries when the notification processing'
                    ' is error.'),
    cfg.IntOpt('retry_interval',
               default=10,
               help='Trial interval of time of the notification processing'
                    ' is error(in seconds).'),
]

libvirt_opts = [
    cfg.StrOpt('connection_uri',
               default='qemu:///system',
               help='Override the default libvirt URI.')
]


def register_opts(conf):
    conf.register_opts(monitor_callback_opts, group='callback')
    conf.register_opts(libvirt_opts, group='libvirt')


def list_opts():
    return {
        'callback': monitor_callback_opts,
        'libvirt': libvirt_opts
    }
