====================
masakari-hostmonitor
====================

Monitor Overview
------------------
The masakari-hostmonitor provides compute node High Availability
for OpenStack clouds by automatically detecting compute nodes failure
via monitor driver.


How does it work based on pacemaker & corosync?
------------------------------------------------
- Pacemaker or pacemaker-remote is required to install into compute nodes
  to form a pacemaker cluster.

- The compute node's status is depending on the heartbeat between the compute
  node and the cluster. Once the node lost the heartbeat, masakari-hostmonitor
  in other nodes will detect the failure and send notifications to masakari-api.


How does it work based on consul?
----------------------------------
- If the nodes in the cloud have multiple interfaces to connect to
  management network, tenant network or storage network, monitor driver based
  on consul is another choice. Consul agents are required to install into all
  noedes, which make up multiple consul clusters.

  Here is an example to show how to make up one consul cluster.

  .. toctree::
     :maxdepth: 1

     consul-usage

- The compute node's status is depending on assembly of multiple interfaces
  connectivity status, which are retrieved from multiple consul clusters. Then
  it sends notifition to trigger host failure recovery according to defined
  HA strategy - host states and the corresponding actions.


Related configurations
------------------------
This section in masakarimonitors.conf shows an example of how to configure
the hostmonitor if you choice monitor driver based on pacemaker.

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

If you want to use or test monitor driver based on consul, please modify
following configuration.

.. code-block:: ini

    [host]
    # Driver that hostmonitor uses for monitoring hosts.
    monitoring_driver = consul

    [consul]
    # Addr for local consul agent in management datacenter.
    # The addr is make up of the agent's bind_addr and http port,
    # such as '192.168.101.1:8500'.
    agent_manage = $(CONSUL_MANAGEMENT_ADDR)
    # Addr for local consul agent in tenant datacenter.
    agent_tenant = $(CONSUL_TENANT_ADDR)
    # Addr for local consul agent in storage datacenter.
    agent_storage = $(CONSUL_STORAGE_ADDR)
    # Config file for consul health action matrix.
    matrix_config_file = /etc/masakarimonitors/matrix.yaml

The ``matrix_config_file`` shows the HA strategy. Matrix is combined by host
health and actions. The 'health: [x, x, x]', repreasents assembly status of
SEQUENCE. Action, means which actions it will trigger if host health turns
into, while 'recovery' means it will trigger one host failure recovery
workflow. User can define the HA strategy according to the physical
environment. For example, if there is just 1 cluster to monitor management
network connectivity, the user just need to configurate
``$(CONSUL_MANAGEMENT_ADDR)`` in consul section of the hostmontior'
configuration file, and change the HA strategy in
``/etc/masakarimonitors/matrix.yaml`` as following:

.. code-block:: yaml

  sequence: ['manage']
  matrix:
    - health: ['up']
      action: []
    - health: ['down']
      action: ['recovery']


Then the hostmonitor by consul works as same as the hostmonitor by pacemaker.
