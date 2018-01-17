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

"""Utilities and helper functions."""

import contextlib
import inspect
import pyclbr
import shutil
import sys
import tempfile

from oslo_concurrency import lockutils
from oslo_concurrency import processutils
from oslo_log import log as logging
from oslo_utils import importutils
import six

import masakarimonitors.conf
from masakarimonitors.i18n import _
from masakarimonitors import privsep


CONF = masakarimonitors.conf.CONF

LOG = logging.getLogger(__name__)


def monkey_patch():
    """monkey_patch function.

    If the CONF.monkey_patch set as True,
    this function patches a decorator
    for all functions in specified modules.
    You can set decorators for each modules
    using CONF.monkey_patch_modules.
    The format is "Module path:Decorator function".
    name - name of the function
    function - object of the function
    """
    # If CONF.monkey_patch is not True, this function do nothing.
    if not CONF.monkey_patch:
        return
    if six.PY2:
        is_method = inspect.ismethod
    else:
        def is_method(obj):
            # Unbound methods became regular functions on Python 3
            return inspect.ismethod(obj) or inspect.isfunction(obj)
    # Get list of modules and decorators
    for module_and_decorator in CONF.monkey_patch_modules:
        md_value = module_and_decorator.split(':')
        if len(md_value) != 2:
            msg = _("'monkey_patch_modules' config option is not configured "
                    "correctly")
            raise Exception(msg)
        module, decorator_name = md_value
        # import decorator function
        decorator = importutils.import_class(decorator_name)
        __import__(module)
        # Retrieve module information using pyclbr
        module_data = pyclbr.readmodule_ex(module)
        for key, value in module_data.items():
            # set the decorator for the class methods
            if isinstance(value, pyclbr.Class):
                clz = importutils.import_class("%s.%s" % (module, key))
                for method, func in inspect.getmembers(clz, is_method):
                    setattr(clz, method,
                            decorator("%s.%s.%s" % (module, key,
                                                    method), func))
            # set the decorator for the function
            if isinstance(value, pyclbr.Function):
                func = importutils.import_class("%s.%s" % (module, key))
                setattr(sys.modules[module], key,
                        decorator("%s.%s" % (module, key), func))


@contextlib.contextmanager
def tempdir(**kwargs):
    argdict = kwargs.copy()
    if 'dir' not in argdict:
        argdict['dir'] = CONF.tempdir
    tmpdir = tempfile.mkdtemp(**argdict)
    try:
        yield tmpdir
    finally:
        try:
            shutil.rmtree(tmpdir)
        except OSError as e:
            LOG.error('Could not remove tmpdir: %s', e)


@privsep.monitors_priv.entrypoint
def privsep_execute(*cmd, **kwargs):
    return processutils.execute(*cmd, **kwargs)


def execute(*cmd, **kwargs):
    """Convenience wrapper around oslo's execute() method."""
    if 'run_as_root' in kwargs and kwargs.get('run_as_root'):
        return privsep_execute(*cmd, **kwargs)
    else:
        return processutils.execute(*cmd, **kwargs)


def synchronized(name, semaphores=None, blocking=False):
    def wrap(f):
        @six.wraps(f)
        def inner(*args, **kwargs):
            lock_str = 'masakarimonitors-%s' % name
            int_lock = lockutils.internal_lock(lock_str,
                                               semaphores=semaphores)
            msg = "Lock blocking: %s on resource %s " % (lock_str, f.__name__)
            """Acquiring lock: %(lock_str)s on resource """
            if not int_lock.acquire(blocking=blocking):
                raise Exception(msg)
            try:
                return f(*args, **kwargs)
            finally:
                """Releasing lock: %(lock_str)s on resource """
                int_lock.release()
        return inner
    return wrap
