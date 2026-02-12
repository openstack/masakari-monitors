=============================================
Welcome to Masakari-monitors's documentation!
=============================================

Masakari is an OpenStack project designed to ensure high availability of
instances and compute processes running on hosts. Masakari-monitors
are the components which detects faults in the cloud.

Operator Guide
==============

Architecture Overview
---------------------

* :doc:`Masakari Monitors architecture </user/architecture>`: An overview
  of how all the components in masakari work together.

Installation
------------

A detailed install guide for Masakari-monitors.

.. toctree::
   :maxdepth: 2

   install/index
   hostmonitor.rst
   instancemonitor.rst
   introspectiveinstancemonitor.rst
   processmonitor.rst

Deployment Considerations
-------------------------

This documentation is based on the assumption that the basic openstack
installation is done with DevStack along with Masakari and its services
enabled to proceed for Masakari-monitors installation.

.. note::
   * OpenStack installation with DevStack services are installed using
     ``Systemd``. The ``systemctl`` is a tool to control the systemd and its
     services. This documentation refers ``systemctl`` commands for dealing
     with service related information.

   * If OpenStack installed with DevStack ``stable/train`` with Masakari
     service enabled in local configuration file, then it also installs
     Masakari-monitors along with it.

Reference Material
------------------

* :doc:`Configuration Guide <configuration/index>`: Information on configuration files.
* `Masakari Docs <https://docs.openstack.org/masakari/latest/>`_: A collection of guides for Masakari.
* `Nova Docs <https://docs.openstack.org/nova/latest/index.html>`_: A collection of guides for Nova.

.. # NOTE(shilpasd): This is the section where we hide things that we don't
   # actually want in the table of contents but sphinx build would fail if
   # they aren't in the toctree somewhere.

.. toctree::
   :hidden:

   configuration/index.rst
   configuration/config.rst
   configuration/process-list.rst
   configuration/sample-config.rst
   user/architecture.rst

Search
======

* :ref:`search`: Search the contents of this document.
* `OpenStack wide search <https://docs.openstack.org>`_: Search the wider
  set of OpenStack documentation, including forums.
