===============================
masakari-monitors
===============================

Monitors for Masakari
=====================

Monitors for Masakari provides Virtual Machine High Availability (VMHA) service
for OpenStack clouds by automatically detecting the failure events
such as VM process down, provisioning process down, and nova-compute host failure.
If it detect the events, it sends notifications to the masakari-api.

Original version of Masakari: https://github.com/ntt-sic/masakari

Tokyo Summit Session: https://www.youtube.com/watch?v=BmjNKceW_9A

Monitors for Masakari is distributed under the terms of the Apache License,
Version 2.0. The full terms and conditions of this license are
detailed in the LICENSE file.

* Free software: Apache license
* Documentation: https://docs.openstack.org/masakari-monitors
* Source: https://git.openstack.org/cgit/openstack/masakari-monitors
* Bugs: https://bugs.launchpad.net/masakari-monitors


Configure masakari-monitors
---------------------------

#. Clone masakari using::

   $ git clone https://github.com/openstack/masakari-monitors.git

#. Create masakarimonitors directory in /etc/.

#. Run setup.py from masakari-monitors::

   $ sudo python setup.py install

#. Copy masakarimonitors.conf and process_list.yaml files from
   masakari-monitors/etc/ to /etc/masakarimonitors folder and make necessary
   changes to the masakarimonitors.conf and process_list.yaml files.
   To generate the sample masakarimonitors.conf file, run the following
   command from the top level of the masakari-monitors directory::

   $ tox -egenconfig

#. To run masakari-processmonitor, masakari-hostmonitor and
   masakari-instancemonitor simply use following binary::

   $ masakari-processmonitor
   $ masakari-hostmonitor
   $ masakari-instancemonitor


Features
--------

* TODO
