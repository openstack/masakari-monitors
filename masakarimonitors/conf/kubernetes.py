# Copyright(c) 2024 Samsung SDS
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

kubernetes_opts = [
    cfg.StrOpt('monitoring_node_labels',
               default='',
               help='''
Options for identifying the nodes to monitor. Only nodes with node labels
defined in this option are included in the monitor.

Example value:

monitoring_node_labels = "monitoring=true,compute-node=enabled,..."
'''),
]


def register_opts(conf):
    conf.register_opts(kubernetes_opts, group='kubernetes')


def list_opts():
    return {
        'kubernetes': kubernetes_opts
    }
