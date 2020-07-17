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
from keystoneauth1 import loading as ks_loading
from oslo_config import cfg

API_GROUP = 'api'

api_group = cfg.OptGroup(
    API_GROUP,
    title='Api Options',
    help="""
Configuration options for sending notifications.
""")

monitor_api_opts = [
    cfg.StrOpt('region',
               default='RegionOne',
               help='Region name.'),
    cfg.StrOpt('api_version',
               default='v1',
               help='Masakari API Version.'),
    cfg.StrOpt('api_interface',
               default='public',
               help='Interface of endpoint.'),
]


def register_opts(conf):
    conf.register_group(api_group)
    conf.register_opts(monitor_api_opts, group=api_group)
    ks_loading.register_session_conf_options(conf, api_group)
    ks_loading.register_auth_conf_options(conf, api_group)
    conf.set_default('auth_type', 'password', group=api_group)


def list_opts():
    return {
        api_group: (
            monitor_api_opts +
            ks_loading.get_auth_plugin_conf_options('password'))
    }
