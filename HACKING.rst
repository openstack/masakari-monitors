masakari-monitors Style Commandments
===============================================

Read the OpenStack Style Commandments http://docs.openstack.org/developer/hacking/

masakari-monitors Specific Commandments
---------------------------------------

- [M301] Ensure that the _() function is explicitly imported to ensure proper translations.
- [M302] Validate that log messages are not translated.
- [M303] Yield must always be followed by a space when yielding a value.
- [M304] Check for usage of deprecated assertRaisesRegexp
- [M305] LOG.warn is deprecated. Enforce use of LOG.warning.
