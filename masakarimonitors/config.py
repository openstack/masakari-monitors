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
from oslo_log import log

import masakarimonitors.conf
from masakarimonitors import version


CONF = masakarimonitors.conf.CONF


def parse_args(argv, default_config_files=None):
    log.register_options(CONF)
    # We use the oslo.log default log levels which includes suds=INFO
    # and add only the extra levels that Masakari needs
    log.set_defaults(default_log_levels=log.get_default_log_levels())

    CONF(argv[1:],
         project='masakarimonitors',
         version=version.version_string(),
         default_config_files=default_config_files)
