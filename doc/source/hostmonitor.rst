====================
masakari-hostmonitor
====================

Monitor Overview
------------------
The masakari-hostmonitor provides compute node High Availability
for OpenStack clouds by automatically detecting compute nodes failure
via pacemaker & corosync.


How does it work?
----------------------------------------
- Pacemaker or pacemaker-remote is required to install into compute nodes
  to form a pacemaker cluster.

- The compute node's status is depending on the heartbeat between the compute
  node and the cluster. Once the node lost the heartbeat, masakari-hostmonitor
  in other nodes will detect the faiure and send notifications to masakari-api.


Related configurations
------------------------
This section in masakarimonitors.conf shows an example of how to configure
the monitor.

.. code-block:: ini

    [host]
    # Driver that hostmonitor uses for monitoring hosts.
    monitoring_driver = default

    # Monitoring interval(in seconds) of node status.
    monitoring_interval = 60

    # Do not check whether the host is completely down.
    # Possible values:
    # * True: Do not check whether the host is completely down.
    # * False: Do check whether the host is completely down.
    # If ipmi RA is not set in pacemaker, this value should be set True.
    disable_ipmi_check = False

    # Timeout value(in seconds) of the ipmitool command.
    ipmi_timeout = 5

    # Number of ipmitool command retries.
    ipmi_retry_max = 3

    # Retry interval(in seconds) of the ipmitool command.
    ipmi_retry_interval = 10

    # Only monitor pacemaker-remotes, ignore the status of full cluster
    # members.
    restrict_to_remotes = False

    # Standby time(in seconds) until activate STONITH.
    stonith_wait = 30

    # Timeout value(in seconds) of the tcpdump command when monitors
    # the corosync communication.
    tcpdump_timeout = 5

    # The name of interface that corosync is using for mutual communication
    # between hosts.
    # If there are multiple interfaces, specify them in comma-separated
    # like 'enp0s3,enp0s8'.
    # The number of interfaces you specify must be equal to the number of
    # corosync_multicast_ports values and must be in correct order with
    # relevant ports in corosync_multicast_ports.
    corosync_multicast_interfaces = enp0s3,enp0s8

    # The port numbers that corosync is using for mutual communication
    # between hosts.
    # If there are multiple port numbers, specify them in comma-separated
    # like '5405,5406'.
    # The number of port numbers you specify must be equal to the number of
    # corosync_multicast_interfaces values and must be in correct order with
    # relevant interfaces in corosync_multicast_interfaces.
    corosync_multicast_ports = 5405,5406
