#!/bin/bash
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

SCRIPT_DIR=/usr/local/lib/python2.7/dist-packages/masakarimonitors/processmonitor
SCRIPT_FILE=${SCRIPT_DIR}/processmonitor.sh

# Argument check
if [ $# -ne 2 ]; then
    echo "Usage: $0 <configuration file path> <proc.list file path>"
    exit 1
else
    SCRIPT_CONF_FILE=$1
    PROC_LIST=$2
fi

sudo bash ${SCRIPT_FILE} ${SCRIPT_CONF_FILE} ${PROC_LIST}
