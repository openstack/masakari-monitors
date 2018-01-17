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

from masakarimonitors.conf import api
from masakarimonitors.conf import base
from masakarimonitors.conf import host
from masakarimonitors.conf import instance
from masakarimonitors.conf import introspectiveinstancemonitor
from masakarimonitors.conf import process
from masakarimonitors.conf import service

CONF = cfg.CONF

api.register_opts(CONF)
base.register_opts(CONF)
host.register_opts(CONF)
instance.register_opts(CONF)
introspectiveinstancemonitor.register_opts(CONF)
process.register_opts(CONF)
service.register_opts(CONF)
