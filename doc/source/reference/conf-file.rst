.. _monitors-config-file:

-------------------------------------------
Masakari Monitors Sample Configuration File
-------------------------------------------

Configure Masakari Monitors by editing
/etc/masakarimonitors/masakarimonitors.conf.

No config file is provided with the source code, it will be created during
the installation. In case where no configuration file was installed, one
can be easily created by running::

    tox -e genconfig


To see configuration options available, please refer to :ref:`monitors-config`.

.. only:: html

   The following is a sample monitors configuration for adaptation and use.

   .. literalinclude:: ../_static/masakarimonitors.conf.sample
