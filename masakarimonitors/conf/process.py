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


monitor_process_opts = [
    cfg.StrOpt('process_list_path',
               default='/etc/masakarimonitors/process_list.yaml',
               help='The file path of process list.'),
]


def register_opts(conf):
    conf.register_opts(monitor_process_opts, group='process')


def list_opts():
    return {
        'process': monitor_process_opts
    }
