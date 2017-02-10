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


class FakeLibvirtOpenReadOnly(object):
    def domainEventRegisterAny(self, dom, eventID, cb, opaque):
        return 1

    def setKeepAlive(self, interval, count):
        return None

    def isAlive(self):
        return 0

    def domainEventDeregisterAny(self, cid):
        return None

    def close(self):
        raise EnvironmentError("Test Exception.")


class FakeConnection(object):
    def __init__(self):
        class Ha(object):
            def create_notification(self, type, hostname, generated_time,
                                    payload):
                return {}
        self.ha = Ha()
