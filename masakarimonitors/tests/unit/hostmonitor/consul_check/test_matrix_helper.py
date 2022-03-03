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

import tempfile

from oslo_config import fixture as fixture_config
import testtools
import yaml

from masakarimonitors.hostmonitor.consul_check import matrix_helper


class TestMatrixManager(testtools.TestCase):

    def setUp(self):
        super(TestMatrixManager, self).setUp()
        self.CONF = self.useFixture(fixture_config.Config()).conf

    def test_get_matrix_and_sequence_from_file(self):
        matrix_cfg = {
            'sequence': ['manage', 'tenant', 'storage'],
            'matrix': [{"health": ["up", "up", "up"],
                        "action": ['test']}]
        }
        tmp_cfg = tempfile.NamedTemporaryFile(mode='w', delete=False)
        tmp_cfg.write(yaml.safe_dump(matrix_cfg))
        tmp_cfg.close()
        self.CONF.set_override('matrix_config_file',
                               tmp_cfg.name, group='consul')

        matrix_manager = matrix_helper.MatrixManager(self.CONF)
        self.assertEqual(matrix_cfg.get('sequence'),
                         matrix_manager.get_sequence())
        self.assertEqual(matrix_cfg.get('matrix'),
                         matrix_manager.get_matrix())

    def test_get_default_matrix_and_sequence(self):
        self.CONF.set_override('matrix_config_file', None, group='consul')

        matrix_manager = matrix_helper.MatrixManager(self.CONF)
        self.assertEqual(matrix_helper.DEFAULT_SEQUENCE,
                         matrix_manager.get_sequence())
        self.assertEqual(matrix_helper.DEFAULT_MATRIX,
                         matrix_manager.get_matrix())
