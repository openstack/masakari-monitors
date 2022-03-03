# Copyright(c) 2019 Inspur
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


consul_opts = [
    cfg.StrOpt('agent_manage',
               help='Addr for local consul agent in management datacenter.'),
    cfg.StrOpt('agent_tenant',
               help='Addr for local consul agent in tenant datacenter.'),
    cfg.StrOpt('agent_storage',
               help='Addr for local consul agent in storage datacenter.'),
    cfg.StrOpt('matrix_config_file',
               help='Config file for consul health action matrix.'),
]


def register_opts(conf):
    conf.register_opts(consul_opts, group='consul')


def list_opts():
    return {
        'consul': consul_opts
    }
