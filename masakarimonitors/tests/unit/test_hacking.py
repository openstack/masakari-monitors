#    Copyright 2017 NTT Data.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import testtools

from masakarimonitors.hacking import checks


class HackingTestCase(testtools.TestCase):
    """This class tests the hacking checks in masakarimonitors.hacking.checks by
    passing strings to the check methods like the pep8/flake8 parser would.
    The parser loops over each line in the file and then passes the
    parameters to the check method. The parameter names in the check method
    dictate what type of object is passed to the check method.

    The parameter types are::

        logical_line: A processed line with the following modifications:
            - Multi-line statements converted to a single line.
            - Stripped left and right.
            - Contents of strings replaced with "xxx" of same length.
            - Comments removed.
        physical_line: Raw line of text from the input file.
        lines: a list of the raw lines from the input file
        tokens: the tokens that contribute to this logical line
        line_number: line number in the input file
        total_lines: number of lines in the input file
        blank_lines: blank lines before this one
        indent_char: indentation character in this file (" " or "\t")
        indent_level: indentation (with tabs expanded to multiples of 8)
        previous_indent_level: indentation on previous line
        previous_logical: previous logical line
        filename: Path of the file being run through pep8

    When running a test on a check method the return will be False/None if
    there is no violation in the sample input. If there is an error a tuple is
    returned with a position in the line, and a message. So to check the result
    just assertTrue if the check is expected to fail and assertFalse if it
    should pass.
    """
    def test_check_explicit_underscore_import(self):
        self.assertEqual(len(list(checks.check_explicit_underscore_import(
            "LOG.info(_('My info message'))",
            "masakarimonitors/tests/other_files.py"))), 1)
        self.assertEqual(len(list(checks.check_explicit_underscore_import(
            "msg = _('My message')",
            "masakarimonitors/tests/other_files.py"))), 1)
        self.assertEqual(len(list(checks.check_explicit_underscore_import(
            "from masakarimonitors.i18n import _",
            "masakarimonitors/tests/other_files.py"))), 0)
        self.assertEqual(len(list(checks.check_explicit_underscore_import(
            "LOG.info(_('My info message'))",
            "masakarimonitors/tests/other_files.py"))), 0)
        self.assertEqual(len(list(checks.check_explicit_underscore_import(
            "msg = _('My message')",
            "masakarimonitors/tests/other_files.py"))), 0)
        self.assertEqual(len(list(checks.check_explicit_underscore_import(
            "from masakarimonitors.i18n import _",
            "masakarimonitors/tests/other_files2.py"))), 0)
        self.assertEqual(len(list(checks.check_explicit_underscore_import(
            "msg = _('My message')",
            "masakarimonitors/tests/other_files2.py"))), 0)
        self.assertEqual(len(list(checks.check_explicit_underscore_import(
            "_ = translations.ugettext",
            "masakarimonitors/tests/other_files3.py"))), 0)
        self.assertEqual(len(list(checks.check_explicit_underscore_import(
            "msg = _('My message')",
            "masakarimonitors/tests/other_files3.py"))), 0)

    def test_no_translate_logs(self):
        self.assertEqual(1, len(list(checks.no_translate_logs(
            "LOG.error(_LE('foo'))"))))

        self.assertEqual(0, len(list(checks.no_translate_logs(
            "LOG.debug('foo')"))))

        self.assertEqual(1, len(list(checks.no_translate_logs(
            "LOG.info(_LI('foo'))"))))

        self.assertEqual(1, len(list(checks.no_translate_logs(
            "LOG.warning(_LW('foo'))"))))

        self.assertEqual(1, len(list(checks.no_translate_logs(
            "LOG.critical(_LC('foo'))"))))
