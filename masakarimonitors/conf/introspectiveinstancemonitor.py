# Copyright(c) 2018 WindRiver Systems
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


# Note: this string is being used for regex parsing later with re module.
#
# Use Python's raw string notation for regular expressions and
# uses the backslash character ('\') to indicate special
# forms or to allow special characters to be used without invoking
# their special meaning.
SOCK = r'/var/lib/libvirt/qemu/org\.qemu\.guest_agent\..*\.instance-.*\.sock'

monitor_opts = [
    cfg.IntOpt('guest_monitoring_interval',
               default=10,
               help='''
Guest monitoring interval of VM status (in seconds).
* The value should not be too low as there should not be false negative
* for reporting QEMU_GUEST_AGENT failures
* VM needs time to do powering-off.
* guest_monitoring_interval should be greater than
* the time to SHUTDOWN VM gracefully.
* e.g. | 565da9ba-3c0c-4087-83ca | iim1 | ACTIVE | powering-off | Running
'''),
    cfg.IntOpt('guest_monitoring_timeout',
               default=2,
               help='Guest monitoring timeout (in seconds).'),
    cfg.IntOpt('guest_monitoring_failure_threshold',
               default=3,
               help='Failure threshold before sending notification.'),
    cfg.StrOpt('qemu_guest_agent_sock_path',
               default=SOCK,
               help='''
* The file path of qemu guest agent sock.
* Please use Python raw string notation as regular expressions.
e.g.  r'/var/lib/libvirt/qemu/org\.qemu\.guest_agent\..*\.instance-.*\.sock'
'''),
    cfg.BoolOpt('callback_paused_event',
               default=True,
               help='''
* True: Callback for VM paused events.
* False: Do not callback for VM paused events.
'''),
]


def register_opts(conf):
    conf.register_opts(monitor_opts, group='introspectiveinstancemonitor')


def list_opts():
    return {
        'introspectiveinstancemonitor': monitor_opts
    }
