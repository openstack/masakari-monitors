# Copyright (c) 2017, NTT Data
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import re

from hacking import core

"""
Guidelines for writing new hacking checks

 - Use only for masakarimonitors specific tests. OpenStack general tests
   should be submitted to the common 'hacking' module.
 - Pick numbers in the range M3xx. Find the current test with
   the highest allocated number and then pick the next value.
 - Keep the test method code in the source file ordered based
   on the M3xx value.
 - List the new rule in the top level HACKING.rst file
 - Add test cases for each new rule to masakarimonitors/tests/unit/
   test_hacking.py

"""

UNDERSCORE_IMPORT_FILES = []

translated_log = re.compile(
    r"(.)*LOG\.(audit|error|info|critical|exception)"
    r"\(\s*_\(\s*('|\")")
string_translation = re.compile(r"[^_]*_\(\s*('|\")")
underscore_import_check = re.compile(r"(.)*import _(.)*")
underscore_import_check_multi = re.compile(r"(.)*i18n\s+import(.)* _, (.)*")
# We need this for cases where they have created their own _ function.
custom_underscore_check = re.compile(r"(.)*_\s*=\s*(.)*")
log_translation = re.compile(
    r"(.)*LOG\."
    r"(audit|debug|error|info|warn|warning|critical|exception)"
    r"\("
    r"(_|_LC|_LE|_LI|_LW)"
    r"\(")
yield_not_followed_by_space = re.compile(r"^\s*yield(?:\(|{|\[|\"|').*$")


@core.flake8ext
def check_explicit_underscore_import(logical_line, filename):
    """Check for explicit import of the _ function

    We need to ensure that any files that are using the _() function
    to translate logs are explicitly importing the _ function.  We
    can't trust unit test to catch whether the import has been
    added so we need to check for it here.
    """

    # Build a list of the files that have _ imported.  No further
    # checking needed once it is found.
    for file in UNDERSCORE_IMPORT_FILES:
        if file in filename:
            return
    if (underscore_import_check.match(logical_line) or
            underscore_import_check_multi.match(logical_line) or
            custom_underscore_check.match(logical_line)):
        UNDERSCORE_IMPORT_FILES.append(filename)
    elif(translated_log.match(logical_line) or
         string_translation.match(logical_line)):
        yield (0, "M301: Found use of _() without explicit import of _ !")


@core.flake8ext
def no_translate_logs(logical_line):
    """Check that logging doesn't translate messages
    M302
    """
    if log_translation.match(logical_line):
        yield (0, "M302 Don't translate log messages!")


@core.flake8ext
def yield_followed_by_space(logical_line):
    """Yield should be followed by a space.

    Yield should be followed by a space to clarify that yield is
    not a function. Adding a space may force the developer to rethink
    if there are unnecessary parentheses in the written code.

    Not correct: yield(x), yield(a, b)
    Correct: yield x, yield (a, b), yield a, b

    M303
    """
    if yield_not_followed_by_space.match(logical_line):
        yield (0,
               "M303: Yield keyword should be followed by a space.")
