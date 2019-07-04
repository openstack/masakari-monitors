========
Overview
========

Masakari-monitors provides Virtual Machine High Availability (VMHA) service
for OpenStack clouds by automatically detecting failure events. It provides
an alert for failure of either host, process or instance. If it detect such
events, notifications are sent to the masakari-api.

Masakari-monitors detects the four types of failures:

* process failure
   ``masakari-processmonitor`` service detects compute process failure, and
   sends notifications to the masakari-api.

* instance failure
   ``masakari-instancemonitor`` service detects VM/instance failure, and sends
   notifications to the masakari-api.

* instance system-level failure failure
   ``masakari-introspectiveinstancemonitor`` service detects system-level
   failure events via QEMU Guest Agent. When it does, it sends notifications
   to the masakari-api.

* compute host failure
   ``masakari-hostmonitor`` service detects nova-compute host failure.
