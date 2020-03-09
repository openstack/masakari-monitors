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

"""Generic Node base class for all workers that run on hosts."""

import os
import sys

from oslo_log import log as logging
from oslo_service import service
from oslo_utils import importutils

import masakarimonitors.conf
from masakarimonitors.i18n import _
from masakarimonitors import utils


LOG = logging.getLogger(__name__)

CONF = masakarimonitors.conf.CONF


class Service(service.Service):
    """Service object for binaries running on hosts.

       A service takes a manager.
    """

    def __init__(self, host, binary, manager):
        super(Service, self).__init__()
        self.host = host
        self.binary = binary
        self.manager_class_name = manager
        manager_class = importutils.import_class(self.manager_class_name)
        self.manager = manager_class(host=self.host)

    def __repr__(self):
        return "<%(cls_name)s: host=%(host)s, binary=%(binary)s, " \
               "manager_class_name=%(manager)s>" %\
               {
                   'cls_name': self.__class__.__name__,
                   'host': self.host,
                   'binary': self.binary,
                   'manager': self.manager_class_name
               }

    def start(self):
        LOG.info('Starting %s', self.binary)
        self.basic_config_check()
        self.manager.init_host()
        self.manager.main()

    def __getattr__(self, key):
        manager = self.__dict__.get('manager', None)
        return getattr(manager, key)

    @classmethod
    def create(cls, host=None, binary=None, manager=None):
        """Instantiates class and passes back application object.

        :param host: defaults to CONF.hostname
        :param binary: defaults to basename of executable
        :param manager: defaults to CONF.<Latter part of binary>_manager

        """
        if not host:
            host = CONF.hostname
        if not binary:
            binary = os.path.basename(sys.argv[0])

        if not manager:
            manager_cls = ('%s_manager' %
                           binary.rpartition('masakarimonitors-')[2])
            manager = CONF.get(manager_cls, None)

        service_obj = cls(host, binary, manager)

        return service_obj

    def kill(self):
        """Destroy the service object in the datastore.

        NOTE: Although this method is not used anywhere else than tests, it is
        convenient to have it here, so the tests might easily and in clean way
        stop and remove the service_ref.

        """
        self.stop()

    def stop(self):
        LOG.info('Stopping %s', self.binary)
        self.manager.stop()
        super(Service, self).stop()

    def basic_config_check(self):
        """Perform basic config checks before starting processing."""
        # Make sure the tempdir exists and is writable
        try:
            with utils.tempdir():
                pass
        except Exception as e:
            LOG.error('Temporary directory is invalid: %s', e)
            sys.exit(1)

    def reset(self):
        self.manager.reset()


# NOTE: the global launcher is to maintain the existing
#       functionality of calling service.serve +
#       service.wait
_launcher = None


def serve(server, workers=None):
    global _launcher
    if _launcher:
        raise RuntimeError(_('serve() can only be called once'))

    _launcher = service.launch(CONF, server, workers=workers)


def wait():
    _launcher.wait()
