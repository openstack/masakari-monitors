# Copyright (c) 2018 WindRiver Systems
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
The code related to integration between oslo.cache module and masakarimonitors.

Use 'oslo_cache.dict'

i.e. dogpile.cache backend that uses dictionary for storage
Dogpile consists of two subsystems, one building on top of the other.
dogpile provides the concept of a dogpile lock, a control structure
which allows a single thread of execution to be selected as the creator
of some resource, while allowing other threads of execution to refer
to the previous version of this resource as the creation proceeds;
if there is no previous version, then those threads block until
the object is available.
"""
from oslo_cache import core
from oslo_config import cfg

WEEK = 604800


def register_cache_configurations(conf):
    """Register all configurations required for oslo.cache.

    The procedure registers all configurations required for oslo.cache.
    It should be called before configuring of cache region

    :param conf: instance of configuration
    :returns: updated configuration
    """
    # register global configurations for caching
    core.configure(conf)

    return conf


# variable that stores an initialized cache region
_REGION = None


def get_cache_region():
    global _REGION
    if not _REGION:
        _REGION = core.create_region()
        _REGION.configure('oslo_cache.dict',
            arguments={'expiration_time': WEEK})
        core.configure_cache_region(
            conf=register_cache_configurations(cfg.CONF),
            region=_REGION)
    return _REGION
