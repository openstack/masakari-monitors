=====================================
masakari-introspectiveinstancemonitor
=====================================

Monitor Overview
-----------------
The masakari-introspectiveinstancemonitor provides Virtual Machine HA for
OpenStack clouds by automatically detecting the system-level failure
events via QEMU Guest Agent. If it detects VM heartbeat failure events,
it sends notifications to the masakari-api.


How does it work?
----------------------------------------
- libvirt and QEMU Guest Agent are used as the underlying protocol for
  messaging to and from VM.

  - The host-side qemu-agent sockets are used to detemine whether VMs are
    configured with QEMU Guest Agent.

  - qemu-guest-ping is used as the monitoring heartbeat.

- For the future release, we can pass through arbitrary guest agent commands
  to check the health of the applications inside a VM.


Related configurations
------------------------
This section in masakarimonitors.conf shows an example of how to configure
the monitor.

.. code-block:: ini

    [libvirt]
    # Override the default libvirt URI.
    connection_uri = qemu:///system

    [introspectiveinstancemonitor]
    # Guest monitoring interval of VM status (in seconds).
    # * The value should not be too low as there should not be false negative
    # * for reporting QEMU_GUEST_AGENT failures
    # * VM needs time to do powering-off.
    # * guest_monitoring_interval should be greater than
    # * the time to SHUTDOWN VM gracefully.
    guest_monitoring_interval = 10

    # Guest monitoring timeout (in seconds).
    guest_monitoring_timeout = 2

    # Failure threshold before sending notification.
    guest_monitoring_failure_threshold = 3

    # The file path of qemu guest agent sock.
    qemu_guest_agent_sock_path = \
    /var/lib/libvirt/qemu/org\.qemu\.guest_agent\..*\.instance-.*\.sock
