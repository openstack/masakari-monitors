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
    cfg.StrOpt('api_version',
               default='v1',
               help='Masakari API Version.'),
    cfg.StrOpt('interface',
               default='public',
               help='Interface of endpoint.'),
]


monitor_keystone_opts = [
    cfg.StrOpt('project_domain_name',
               default='default',
               help='Domain name which the project belongs.'),
    cfg.StrOpt('username',
               default='masakari',
               help='The name of a user with administrative privileges.'),
    cfg.StrOpt('password',
               default='password',
               help='Administrator user\'s password.'),
    cfg.StrOpt('project_name',
               default='service',
               help='Project name.'),
    cfg.StrOpt('auth_url',
               default='http://localhost:5000',
               help='Address of Keystone.'),
    cfg.StrOpt('region',
               default='RegionOne',
               help='Region name.'),
]


def register_opts(conf):
    conf.register_opts(monitor_callback_opts, group='callback')
    conf.register_opts(monitor_keystone_opts, group='keystone')


def list_opts():
    return {
        'callback': monitor_callback_opts,
        'keystone': monitor_keystone_opts
    }
