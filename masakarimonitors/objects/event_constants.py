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


class EventConstants(object):
    # Define event types.
    TYPE_PROCESS = "PROCESS"
    TYPE_COMPUTE_HOST = "COMPUTE_HOST"
    TYPE_VM = "VM"

    # Define event details.
    EVENT_STARTED = "STARTED"
    EVENT_STOPPED = "STOPPED"

    # Define host status.
    HOST_STATUS_NORMAL = "NORMAL"
    HOST_STATUS_UNKNOWN = "UNKNOWN"

    # Define cluster status.
    CLUSTER_STATUS_ONLINE = "ONLINE"
    CLUSTER_STATUS_OFFLINE = "OFFLINE"
