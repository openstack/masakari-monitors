.. _install-ubuntu:

Install and configure for Ubuntu
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This section describes how to install and configure Masakari-monitors for
Ubuntu 18.04 (bionic).

Prerequisites
-------------

Before you install and configure Masakari-monitors, you must verify
installations below:

#. To install and confirm Masakari installation:

   * Masakari - is an OpenStack project designed to ensure high availability
     of instances and compute processes running on hosts. For detailed
     installation steps please refer to `masakari documentation
     <https://docs.openstack.org/masakari/latest/>`_

   * Verify Masakari installation by verifying status of services:

     .. code-block:: console

        $ systemctl list-unit-files devstack@masakari-*.service

        UNIT FILE                                              STATE
        devstack@masakari-api.service                          enabled
        devstack@masakari-engine.service                       enabled

        2 unit files listed.

#. IPMI support is needed for ``masakari-hostmonitor service`` which is a
   remote hardware health monitoring and management system that defines
   interfaces for use in monitoring the physical health of servers.

   #. Check if IPMI Hardware support is enabled:

      .. code-block:: console

         $ stonith -L | grep external/ipmi
         external/ipmi

   #. Install ipmitool and verify:

      * `IPMItool <https://docs.oracle.com/cd/E19464-01/820-6850-11/IPMItool.html>`_
         utility is an open-source command-line interface (CLI)
         for controlling IPMI (Intelligent Platform Management Interface)
         enabled devices.

        .. code-block:: console

           $ sudo apt-get -y install ipmitool
           $ sudo ipmitool -V

        .. note::
           Check for `IPMI Hardware support <https://linux.die.net/man/1/ipmitool>`_
           with the command: ``sudo ipmitool lan print 1``.

           If IPMI configuration found, then proceed to steps below.

   #. Install crm and verify:

      * `crm <https://manpages.ubuntu.com/manpages/bionic/man8/crm.8.html>`_
        is a Pacemaker command line interface for configuration and management.

        .. code-block:: console

           $ sudo apt-get -y install crmsh
           $ sudo crm --version

   #. Install pacemaker and corosync and verify:
      Refer `Ubuntu Manpage <https://manpages.ubuntu.com/manpages/bionic/man8/pcs.8.html>`_
      for control and configure pacemaker and corosync.

      * corosync - It is a Cluster Engine and a Group Communication System
        with additional features for implementing high availability within
        applications.

        .. code-block:: console

           $ sudo apt-get -y install corosync
           $ sudo corosync -v

      * pacemaker - It is an open-source high availability resource
        manager software used on computer clusters.

        .. code-block:: console

           $ sudo apt-get -y install pacemaker
           $ sudo crmadmin --version

      * Edit the ``/etc/corosync/corosync.conf`` file as described below:

        * Configure ``bindnetaddr`` value as network address of the interface
          to bind:

          .. code-block:: bash

               totem {
                   ...
                       interface {
                       ...
                           bindnetaddr: BINDNETADDR

               Replace ``BINDNETADDR`` with network address used for mutual
               communication between hosts.

        * Add the service section at end of file:

          .. code-block:: bash

           service {
               name: pacemaker
               ver: 0
               use_mgmtd: yes
           }

      * Edit the ``/etc/default/corosync`` file as described below:

        .. code-block:: console

         # Start corosync at boot [yes|no]
         START=yes

      * Start corosync and pacemaker services:

        .. code-block:: console

         # systemctl start corosync.service
         # systemctl start pacemaker.service

   #. Install and confirm STONITH resource:

      * `STONITH <https://clusterlabs.org/pacemaker/doc/en-US/Pacemaker/1.1/html/Clusters_from_Scratch/ch08.html>`_
        (Shoot The Other Node In The Head) is a Linux service for
        maintaining the integrity of nodes in a high-availability (HA)
        cluster. More description on how to create STONITH resource is here
        `cluster resources <https://www.suse.com/documentation/sle-ha-12/book_sleha/data/sec_ha_config_crm_resources.html#sec_ha_manual_create_stonith>`_

Install and configure Masakari Monitors
---------------------------------------

.. note::

   * Masakari-monitors can be installed on the ComputeNodes only.

#. Clone masakari-monitors using:

   .. code-block:: console

      # git clone https://opendev.org/openstack/masakari-monitors.git

#. Prepare masakari-monitors configuration files:

   #. Generate via tox:
      Go to ‘opt/stack/masakari-monitors’ and execute the command below, this
      will generate ``masakarimonitors.conf.sample``, sample configuration file at
      ``/opt/stack/masakari-monitors/etc/masakarimonitors/``

      .. code-block:: console

         # tox -egenconfig

   #. Or download them:

      # :download:`masakarimonitors.conf.sample </_static/masakarimonitors.conf.sample>`

   #. Rename ``masakarimonitors.conf.sample`` to file to ``masakarimonitors.conf``,
      and edit as described below:

      * In the ``[api]`` section, verify keys below for sending notifications:

        .. code-block:: bash

           [api]
           ...
           auth_url = http://CONTROLLER/identity
           project_name = service
           project_domain_name = default
           username = masakari
           password = MASAKARI_PASS

        Replace ``CONTROLLER`` with the IP address or hostname of
        ControllerNode. And replace ``MASAKARI_PASS`` with the password
        you chose for the ``masakari`` user in the Identity service.

      * In the ``[host]`` section, configure about pacemaker:

        .. code-block:: bash

          [host]
          ...
          corosync_multicast_interfaces = MULTICAST_INTERFACES
          corosync_multicast_ports = MULTICAST_PORTS

        * Replace ``MULTICAST_INTERFACES`` with the interface that corosync is
          using for mutual communication between hosts.
          You can find the interface from the value of ``bindnetaddr`` in
          /etc/corosync/corosync.conf.
          If there are multiple interfaces, specify them by comma-separated
          like 'corosync_multicast_interfaces = enp0s3,enp0s8'.

        * Replace ``MULTICAST_PORTS`` with the ``mcastport`` described in
          /etc/corosync/corosync.conf.
          If there are multiple ``mcastport``, specify them by comma-separated
          like 'corosync_multicast_ports = 5405,5406'.

   #. Rename ``process_list.yaml.sample``, sample configuration file at
      ``/opt/stack/masakari-monitors/etc/masakarimonitors/``. Edit the file
      for the processes to be monitored.

   #. Create ``masakarimonitors`` directory in /etc/. Copy
      ``masakarimonitors.conf`` and ``process_list.yaml`` files to
      ``/etc/masakarimonitors/``

      .. code-block:: console

         # cp -p etc/masakarimonitors/masakarimonitors.conf.sample /etc/masakarimonitors/masakarimonitors.conf
         # cp -p etc/masakarimonitors/process_list.yaml.sample /etc/masakarimonitors/process_list.yaml

#. To install masakari-monitors run setup.py from the directory
   masakari-monitors:

   .. code-block:: console

      # cd masakari-monitors
      # sudo python3 setup.py install

Finalize installation
---------------------

* Restart the masakari-monitors services:

  .. code-block:: console

     # masakari-hostmonitor
     # masakari-introspectiveinstancemonitor
     # masakari-processmonitor
     # masakari-instancemonitor
