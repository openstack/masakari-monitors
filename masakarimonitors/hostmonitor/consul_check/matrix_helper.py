# Copyright(c) 2021 Inspur
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

import os
import yaml


DEFAULT_SEQUENCE = ['manage', 'tenant', 'storage']

# matrix is combined by health and actions.
# health: [x, x, x], repreasents status of DEFAULT_SEQUENCE.
# action, means which actions it will trigge if host health turns into.
# action choice: 'recovery'.
# 'recovery' means it will trigge one host recovery event.
DEFAULT_MATRIX = [
    {"health": ["up", "up", "up"],
     "action": []},
    {"health": ["up", "up", "down"],
     "action": ["recovery"]},
    {"health": ["up", "down", "up"],
     "action": []},
    {"health": ["up", "down", "down"],
     "action": ["recovery"]},
    {"health": ["down", "up", "up"],
     "action": []},
    {"health": ["down", "up", "down"],
     "action": ["recovery"]},
    {"health": ["down", "down", "up"],
     "action": []},
    {"health": ["down", "down", "down"],
     "action": ["recovery"]},
]


class MatrixManager(object):
    """Matrix Manager"""

    def __init__(self, CONF):
        cfg_file = CONF.consul.matrix_config_file
        matrix_conf = self.load_config(cfg_file)
        if not matrix_conf:
            self.sequence = DEFAULT_SEQUENCE
            self.matrix = DEFAULT_MATRIX
        else:
            self.sequence = matrix_conf.get("sequence")
            self.matrix = matrix_conf.get("matrix")

            self.valid_matrix(self.matrix, self.sequence)

    def load_config(self, cfg_file):
        if not cfg_file or not os.path.exists(cfg_file):
            return None

        with open(cfg_file) as f:
            data = f.read()
        matrix_conf = yaml.safe_load(data)
        return matrix_conf

    def get_sequence(self):
        return self.sequence

    def get_matrix(self):
        return self.matrix

    def valid_matrix(self, matrix, sequence):
        pass
