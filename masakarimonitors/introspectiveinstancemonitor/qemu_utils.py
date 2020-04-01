# Copyright (c) 2018 WindRiver Systems
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# Introspective instance monitoring depends on the qemu guest agent to
# monitoring what inside of a VM.
#
# A few items to get in the way of the design:
#
# - After VM is active, it needs time to start qemu-guest-agent.
# Before error/failure is reported, we need a discovery phase to wait
# until VM is guest_pingable.
#
# - Debouncing is needed to enforce that masakari_notifier function
# not calling twice or more for the same failure.
#
# After reported a masakari notification, sent_notification flag will
# need to be reset when there is a QEMU LIFECYCLE event like:
#  STARTED_BOOTED
#  SUSPENDED_PAUSED

import eventlet
import libvirt
import libvirtmod_qemu
import logging
import re
import socket
import time
import traceback

# Machine module contains the state machine logic, state and transition events
from automaton import machines
from dogpile.cache.api import NoValue
from lxml import etree
from oslo_config import cfg
from oslo_utils import timeutils

from masakarimonitors.ha import masakari
from masakarimonitors.introspectiveinstancemonitor import cache
from masakarimonitors.objects import event_constants as ec
from masakarimonitors import utils

CONF = cfg.CONF
ICONF = cfg.CONF.introspectiveinstancemonitor

# The VM QEMU Quest Agent states
#
# discovery = initial state of VM,
#   remains in this state until it is determined that
#   the VM has a qemu-agent interface enabling intrusive-instance-monitoring
#
# healthy = no failure event is detected
#
# error = An error is recorded on every audit cycle where
#  the VM is in the error state
#
# reported = a transient state
#   to keep track of reporting of notification
#

# Transitions
#
#   Representation of a transition managed by a ``Machine`` instance.
#   source (str): Source state of the transition.
#   dest (str): Destination state of the transition.
#   trigger (str): The type of triggering event
#     that advances to the next state in the sequence.


def action_on_enter(new_state, triggered_event):
    pass


def action_on_exit(old_state, triggered_event):
    pass


STATE_SPACE = [
    {
        'name': 'discovery',
        'next_states': {
            'guest_pingable': 'healthy',
            'guest_not_pingable': 'discovery',
        },
        'on_enter': action_on_enter,
        'on_exit': action_on_exit,
    },
    {
        'name': 'healthy',
        'next_states': {
            'guest_pingable': 'healthy',
            'guest_not_pingable': 'error',
        },
        'on_enter': action_on_enter,
        'on_exit': action_on_exit,
    },
    {
        'name': 'error',
        'next_states': {
            'report': 'reported',
            'guest_pingable': 'healthy',
            'guest_not_pingable': 'error',
        },
        'on_enter': action_on_enter,
        'on_exit': action_on_exit,
    },
    {
        'name': 'reported',
        'next_states': {
            'guest_pingable': 'discovery',
            'guest_not_pingable': 'reported',
        },
        'on_enter': action_on_enter,
        'on_exit': action_on_exit,
    },
]


#   Journal representation of a managed ``Machine`` instance.
class Journal(machines.FiniteMachine):

    # Factory pattern to create a Journal object
    @classmethod
    def factory(cls, domain_uuid):
        jo = cls.build(STATE_SPACE)
        jo.default_start_state = 'discovery'
        jo.initialize()
        jo.failedCount = 0
        # Conditions to reset sent_notification
        jo.sent_notification = False
        jo.domain_uuid = domain_uuid
        jo.lastUsed = time.time()
        LOG.debug(str(domain_uuid) + ':Journal:__init__:')
        return jo

    def resetState(self):
        self.default_start_state = 'discovery'
        self.initialize()
        self.failedCount = 0
        self.sent_notification = False
        LOG.debug(str(self.domain_uuid) + '__resetState__:')

    def processEvent(self, event):
        self.process_event(event)
        self.lastUsed = time.time()

    def getFailedCount(self):
        return self.failedCount

    def incrementFailedCount(self):
        if (self.current_state == 'error'):
            self.failedCount += 1

    def resetFailedCount(self):
        self.failedCount = 0

    def setSentNotification(self, boolean):
        self.sent_notification = boolean

    def getSentNotification(self):
        return self.sent_notification


# libvirt state verbose dictionary
STATES = {
    libvirt.VIR_DOMAIN_NOSTATE: 'no state',
    libvirt.VIR_DOMAIN_RUNNING: 'running',
    libvirt.VIR_DOMAIN_BLOCKED: 'blocked on resource',
    libvirt.VIR_DOMAIN_PAUSED: 'paused by user',
    libvirt.VIR_DOMAIN_SHUTDOWN: 'being shut down',
    libvirt.VIR_DOMAIN_SHUTOFF: 'shut off',
    libvirt.VIR_DOMAIN_CRASHED: 'crashed',
}

LOG = logging.getLogger(__name__)


def get_function_name():
    return traceback.extract_stack(None, 2)[0][2]


# To reset journal object by domain uuid
def resetJournal(domain_uuid):
    # To get the VM Journal object from the dictionary
    #    :param domain: QEMU domain UUID
    dict = cache.get_cache_region()
    jo = None
    if type(dict.get(domain_uuid)) is NoValue:
        jo = Journal.factory(domain_uuid)
        dict.set(domain_uuid, jo)
    else:
        jo = dict.get(domain_uuid)

    jo.resetState()


#  Qemu guest agent is used to check VM status
#  The checking pre-conditions are as follows:
#  - VM is running
#  - VM has Qemu guest agent installed
#
#  then status is determined by
#  - VM is guest-agent-pingable or not
#
# Note: checkGuests function is called by the scheduler
class QemuGuestAgent(object):

    def __init__(self):
        super(QemuGuestAgent, self).__init__()
        self.notifier = masakari.SendNotification()

    # _thresholdsCrossing
    #
    # We only issue a notification
    # to masakari-engine if the VM is 'already' in the error state
    # when there are consecutive guest_ping failures.
    # Suggested value for guest_monitoring_failure_threshold >= 3
    #
    # Note: When operators are trying to gracefully shutdown VM,
    # QEMU may take time to powering-off.
    # E.g. When you do <nova list> or <openstack server show>
    # you may see that QEMU is active but monitoring may fail
    # due to VM is still "powering-off"
    #  Status  | Task State   | Power State
    #  ACTIVE  | powering-off | Running
    def _thresholdsCrossing(self, domain):
        if (((self.getVmFsm(domain.UUIDString()).current_state) == 'error')
            and
            (self._getJournalObject(domain.UUIDString()).getFailedCount()
                > ICONF.guest_monitoring_failure_threshold)):
            LOG.debug('_thresholdsCrossing:' + domain.UUIDString())
            LOG.debug(self._getJournalObject(
                domain.UUIDString()).getFailedCount())
            return True
        else:
            return False

    def _masakari_notifier(self, domain_uuid):
        if self._getJournalObject(domain_uuid).getSentNotification():
            LOG.debug('notifier.send_notification Skipped:' + domain_uuid)
        else:
            hostname = socket.gethostname()
            noticeType = ec.EventConstants.TYPE_VM
            current_time = timeutils.utcnow()
            event = {
                'notification': {
                    'type': noticeType,
                    'hostname': hostname,
                    'generated_time': current_time,
                    'payload': {
                        'event': 'QEMU_GUEST_AGENT_ERROR',
                        'instance_uuid': domain_uuid,
                        'vir_domain_event': 'STOPPED_FAILED'
                    }
                }
            }
            try:
                self.notifier.send_notification(CONF.callback.retry_max,
                                        CONF.callback.retry_interval,
                                        event)
                self._getJournalObject(domain_uuid).processEvent('report')
                self._getJournalObject(domain_uuid).setSentNotification(True)
            except Exception:
                LOG.warn('Exception :' + domain_uuid +
                    ' @ ' + get_function_name())
                pass

    def _qemuAgentGuestPing(self, domain, timeout, flags=0):
        def _no_heartbeat(domain_uuid):
            # Also advance the FSM
            self.getVmFsm(domain_uuid).processEvent('guest_not_pingable')
            self._getJournalObject(domain_uuid).incrementFailedCount()

        def _with_heartbeat(domain_uuid):
            #The order matters as we want to decrease the counter first
            self._getJournalObject(domain_uuid).resetFailedCount()
            self.getVmFsm(domain_uuid).processEvent('guest_pingable')

        def _record(result):
            if result is None:
                LOG.debug(domain.UUIDString()
                    + '\tqemu-ga_guest-ping is not responding.')

                if self._thresholdsCrossing(domain):
                    self._masakari_notifier(domain.UUIDString())

                _no_heartbeat(domain.UUIDString())
            else:
                _with_heartbeat(domain.UUIDString())

        """Send a Guest Agent ping to domain """
        # must pass domain._o to the c library as virDomainPtr
        ret = libvirtmod_qemu.virDomainQemuAgentCommand(domain._o,
            '{"execute": "guest-ping"}', timeout, flags)

        _record(ret)

    def _getJournalObject(self, domain_uuid):
        """Function: To get the dictionary

        :param domain: QEMU domain
        :return: the journal object referred by domain_uuid
        """

        dict = cache.get_cache_region()
        if type(dict.get(domain_uuid)) is NoValue:
            jo = Journal.factory(domain_uuid)
            dict.set(domain_uuid, jo)
            return jo
        else:
            return dict.get(domain_uuid)

    def getVmFsm(self, domain_uuid):
        """Function: To get the VM Finite State Machine from
        the dictionary

        :param domain: QEMU domain
        :return: FSM object
        """
        dict = cache.get_cache_region()

        if type(dict.get(domain_uuid)) is NoValue:
            jo = Journal.factory(domain_uuid)
            dict.set(domain_uuid, jo)
            return jo
        else:
            return dict.get(domain_uuid)

    def _hasQemuGuestAgent(self, domain):
        """Function: To check whether the VM has an QEMU Guest Agent
        by examining the qemu.guest_agent sock

        First check if libvirt is running or not, then sock

        :param domain: QEMU domain
        :return: true or false
        """

        def qemuGuestAgentPathMatch(path):
            SOCK = ICONF.qemu_guest_agent_sock_path
            return re.match('%s' % SOCK, path)

        state, reason = domain.state()
        # First check if libvirt is running or not
        if state != libvirt.VIR_DOMAIN_RUNNING:
            return False

        xmlDesc = domain.XMLDesc()
        tree = etree.fromstring(xmlDesc)
        ''' Example
        <channel type='unix'>
         <source mode='bind' path=
          '/var/lib/libvirt/qemu/org.qemu.guest_agent.0.instance-00000004.sock'/>
         <target type=
          'virtio' name='org.qemu.guest_agent.0' state='connected'/>
         <alias name='channel0'/>
         <address type='virtio-serial' controller='0' bus='0' port='1'/>
        </channel>
        '''
        try:
            source = tree.find("devices/channel/source")
            if (source is not None):
                mode = source.get('mode')
                path = source.get('path')
                # There should be a bind for a sock file for qemu guest_agent
                if (qemuGuestAgentPathMatch(path) and mode == 'bind'):
                    return True
        except Exception:
            pass

        return False

    def checkGuests(self):
        """Function: Check QEMU Guests

        Condition: VM under intrusive monitoring must have QEMU agent client
        configured, installed and qemu "guest-agent-pingable".
        """

        try:
            conn = libvirt.open(None)  # LIBVIRT_DEFAULT_URI
            ids = conn.listDomainsID()
            running = map(conn.lookupByID, ids)

            columns = 3

            for row in map(None, *[iter(running)] * columns):
                for domain in row:
                    if domain:
                        try:
                            if self._hasQemuGuestAgent(domain):
                                @utils.synchronized(domain.UUIDString())
                                def do_qemuAgentGuestPing(domain, timeout):
                                    self._qemuAgentGuestPing(domain, timeout)
                                do_qemuAgentGuestPing(domain,
                                    ICONF.guest_monitoring_timeout)
                        except libvirt.libvirtError as le:
                            LOG.warn(le)
                            continue
        except Exception as e:
            LOG.warn(e)
            pass


def reschedule(action, sleep_time=1):
    """Eventlet Sleep for the specified number of seconds.

    :param sleep_time: seconds to sleep; if None, no sleep;
    """
    LOG.debug('At reschedule')
    if sleep_time is not None:
        LOG.debug('Action %s sleep for %s seconds' % (
            action.id, sleep_time))
        eventlet.sleep(sleep_time)


def sleep(sleep_time):
    """Interface for sleeping."""

    eventlet.sleep(sleep_time)
