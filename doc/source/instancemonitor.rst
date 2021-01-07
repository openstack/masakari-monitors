========================
masakari-instancemonitor
========================

Monitor Overview
------------------
The masakari-instancemonitor provides Virtual Machine High Availability
for OpenStack clouds by automatically detecting VMs domain events
via libvirt. If it detects specific libvirt events, it sends notifications
to the masakari-api.


How does it work?
----------------------------------------
- It runs libvirt event loop in a background thread.

  - Invoking libvirt.virEventRegisterDefaultImpl() will register libvirt's
    default event loop implementation.

  - Invoking libvirt.virEventRunDefaultImpl() will perform one iteration
    of the libvirt default event loop.

  - Invoking conn.domainEventRegisterAny() will register event callbacks
    against libvirt connection instances. The callbacks registered will be
    triggered from the execution context of libvirt.virEventRunDefaultImpl(),
    which will send notifications to the masakari-api.

- It will reconnect to libvirt and reprocess if disconnected.


Related configurations
------------------------
This section in masakarimonitors.conf shows an example of how to configure
the monitor.

.. code-block:: ini

    [libvirt]
    # Override the default libvirt URI.
    connection_uri = qemu:///system
