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

import libvirt

# If is not defined internal , -1 is stored.
DUMMY = -1

# Enumerate all event that can get.
# Comment out events that is not targeted in the callback.
event_filter_dic = {
    libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE:
    {
        libvirt.VIR_DOMAIN_EVENT_SUSPENDED:
        (
            libvirt.VIR_DOMAIN_EVENT_SUSPENDED_IOERROR,
            libvirt.VIR_DOMAIN_EVENT_SUSPENDED_WATCHDOG,
            libvirt.VIR_DOMAIN_EVENT_SUSPENDED_API_ERROR
        ),
        libvirt.VIR_DOMAIN_EVENT_STOPPED:
        (
            libvirt.VIR_DOMAIN_EVENT_STOPPED_SHUTDOWN,
            libvirt.VIR_DOMAIN_EVENT_STOPPED_DESTROYED,
            libvirt.VIR_DOMAIN_EVENT_STOPPED_FAILED,
        ),
        libvirt.VIR_DOMAIN_EVENT_SHUTDOWN:
        (
            libvirt.VIR_DOMAIN_EVENT_SHUTDOWN_FINISHED,
        )
    },
    libvirt.VIR_DOMAIN_EVENT_ID_REBOOT: {DUMMY: (DUMMY,)},
    libvirt.VIR_DOMAIN_EVENT_ID_WATCHDOG:
    {
        libvirt.VIR_DOMAIN_EVENT_WATCHDOG_NONE: (DUMMY,),
        libvirt.VIR_DOMAIN_EVENT_WATCHDOG_PAUSE: (DUMMY,),
        libvirt.VIR_DOMAIN_EVENT_WATCHDOG_RESET: (DUMMY,),
        libvirt.VIR_DOMAIN_EVENT_WATCHDOG_POWEROFF: (DUMMY,),
        libvirt.VIR_DOMAIN_EVENT_WATCHDOG_SHUTDOWN: (DUMMY,),
        libvirt.VIR_DOMAIN_EVENT_WATCHDOG_DEBUG: (DUMMY,)
    },
    libvirt.VIR_DOMAIN_EVENT_ID_IO_ERROR:
    {
        libvirt.VIR_DOMAIN_EVENT_IO_ERROR_NONE: (DUMMY,),
        libvirt.VIR_DOMAIN_EVENT_IO_ERROR_PAUSE: (DUMMY,),
        libvirt.VIR_DOMAIN_EVENT_IO_ERROR_REPORT: (DUMMY,)
    },
    libvirt.VIR_DOMAIN_EVENT_ID_IO_ERROR_REASON: {DUMMY: (DUMMY,)},
    libvirt.VIR_DOMAIN_EVENT_ID_CONTROL_ERROR: {DUMMY: (DUMMY,)}

}

eventID_dic = {
    libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE: 'LIFECYCLE',
    libvirt.VIR_DOMAIN_EVENT_ID_REBOOT: 'REBOOT',
    libvirt.VIR_DOMAIN_EVENT_ID_WATCHDOG: 'WATCHDOG',
    libvirt.VIR_DOMAIN_EVENT_ID_IO_ERROR: 'IO_ERROR',
    libvirt.VIR_DOMAIN_EVENT_ID_IO_ERROR_REASON: 'IO_ERROR_REASON',
    libvirt.VIR_DOMAIN_EVENT_ID_CONTROL_ERROR: 'CONTROL_ERROR'}

detail_dic = {
    libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE: {
        libvirt.VIR_DOMAIN_EVENT_SUSPENDED: {
            libvirt.VIR_DOMAIN_EVENT_SUSPENDED_IOERROR:
            'SUSPENDED_IOERROR',
            libvirt.VIR_DOMAIN_EVENT_SUSPENDED_WATCHDOG:
            'SUSPENDED_WATCHDOG',
            libvirt.VIR_DOMAIN_EVENT_SUSPENDED_API_ERROR:
            'SUSPENDED_API_ERROR'},
        libvirt.VIR_DOMAIN_EVENT_STOPPED: {
            libvirt.VIR_DOMAIN_EVENT_STOPPED_SHUTDOWN:
            'STOPPED_SHUTDOWN',
            libvirt.VIR_DOMAIN_EVENT_STOPPED_DESTROYED:
            'STOPPED_DESTROYED',
            libvirt.VIR_DOMAIN_EVENT_STOPPED_FAILED:
            'STOPPED_FAILED'},
        libvirt.VIR_DOMAIN_EVENT_SHUTDOWN: {
            libvirt.VIR_DOMAIN_EVENT_SHUTDOWN_FINISHED:
            'SHUTDOWN_FINISHED'}
    },
    libvirt.VIR_DOMAIN_EVENT_ID_REBOOT: {
        DUMMY: {
            DUMMY: 'UNKNOWN'}},
    libvirt.VIR_DOMAIN_EVENT_ID_WATCHDOG: {
        libvirt.VIR_DOMAIN_EVENT_WATCHDOG_NONE: {
            DUMMY: 'WATCHDOG_NONE'},
        libvirt.VIR_DOMAIN_EVENT_WATCHDOG_PAUSE: {
            DUMMY: 'WATCHDOG_PAUSE'},
        libvirt.VIR_DOMAIN_EVENT_WATCHDOG_RESET: {
            DUMMY: 'WATCHDOG_RESET'},
        libvirt.VIR_DOMAIN_EVENT_WATCHDOG_POWEROFF: {
            DUMMY: 'WATCHDOG_POWEROFF'},
        libvirt.VIR_DOMAIN_EVENT_WATCHDOG_SHUTDOWN: {
            DUMMY: 'WATCHDOG_SHUTDOWN'},
        libvirt.VIR_DOMAIN_EVENT_WATCHDOG_DEBUG: {
            DUMMY: 'WATCHDOG_DEBUG'}},
    libvirt.VIR_DOMAIN_EVENT_ID_IO_ERROR: {
        libvirt.VIR_DOMAIN_EVENT_IO_ERROR_NONE: {
            DUMMY: 'IO_ERROR_NONE'},
        libvirt.VIR_DOMAIN_EVENT_IO_ERROR_PAUSE: {
            DUMMY: 'IO_ERROR_PAUSE'},
        libvirt.VIR_DOMAIN_EVENT_IO_ERROR_REPORT: {
            DUMMY: 'IO_ERROR_REPORT'}},
    libvirt.VIR_DOMAIN_EVENT_ID_IO_ERROR_REASON: {
        DUMMY: {
            DUMMY: 'UNKNOWN'}},
    libvirt.VIR_DOMAIN_EVENT_ID_CONTROL_ERROR: {
        DUMMY: {
            DUMMY: 'UNKNOWN'}}
}
