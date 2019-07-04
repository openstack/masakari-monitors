Masakari Monitors System Architecture
=====================================

Masakari-monitors provides Virtual Machine High Availability (VMHA) service
for OpenStack clouds by detecting the failure events such as VM
unavailability, VM internal faults, provisioning process unavailability and
nova-compute host failure. If it detect these events, it sends notifications
to the masakari-api which in turn, delegates them to masakari-engine for
further processing via novaclient and nova.

Masakari Components
-------------------

The Masakari components described below are those which actually process
the notifications received from Masakari-monitors:

* DB: sql database for data storage for masakari, where all notifications
  received from monitors are getting stored.
* masakari-api: component that receives notification from Masakari-monitors
  and delegates to masakari-engine.
* masakari-engine: processes the notification request with the help of
  novaclient and nova.

Masakari Monitors Components
----------------------------

Below are Masakari-monitors's key components.

.. image:: /_static/images/masakari-monitors.jpg
   :width: 100%

* masakari-instancemonitor: Detects the failure of VM/instance.
* masakari-introspectiveinstancemonitor: Monitors the VMs, in order to detect,
  report and recover VMs from internal faults.
* masakari-processmonitor: Detects the failure of process listed in
  process_list.yaml configuration file.
* masakari-hostmonitor: Detects the nova-compute host failure.
