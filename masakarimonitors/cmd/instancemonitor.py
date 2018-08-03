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

"""Starter script for Masakari Instance Monitor."""

import pbr.version
import sys

from oslo_log import log as logging

import masakarimonitors.conf
from masakarimonitors import config
from masakarimonitors import service
from masakarimonitors import utils


CONF = masakarimonitors.conf.CONF


def main():
    config.parse_args(sys.argv)
    logging.setup(CONF, "masakarimonitors")
    utils.monkey_patch()

    # From openstacksdk version 0.11.1 onwards, there is no way
    # you can add service to the connection. Hence we need to monkey patch
    # _find_service_filter_class method from sdk to allow
    # to point to the correct service filter class implemented in
    # masakari-monitors.
    sdk_ver = pbr.version.VersionInfo('openstacksdk').version_string()
    if sdk_ver in ['0.11.1', '0.11.2', '0.11.3']:
        utils.monkey_patch_for_openstacksdk("openstack._meta:masakarimonitors."
                                            "cmd."
                                            "masakari_service_filter_class")
    if sdk_ver in ['0.12.0']:
        utils.monkey_patch_for_openstacksdk("openstack._meta.connection:"
                                            "masakarimonitors.cmd."
                                            "masakari_service_filter_class")

    server = service.Service.create(binary='masakarimonitors-instancemonitor')
    service.serve(server)
    service.wait()
