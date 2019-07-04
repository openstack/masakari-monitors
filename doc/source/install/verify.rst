Verify operation
~~~~~~~~~~~~~~~~

Verify Masakari and Masakari-monitors installation.

#. Source the ``admin`` credentials to gain access to admin-only CLI commands:

   .. code-block:: console

      $ . admin-openrc

#. List Masakari services on ``controller node``: On controller node only
   Masakari services needs to be installed/listed.

   .. code-block:: console

      $ systemctl list-unit-files devstack@masakari*.service

      UNIT FILE                        STATE
      devstack@masakari-api.service    enabled
      devstack@masakari-engine.service enabled

#. List masakari services on ``compute node/s``: On compute nodes only
   Masakari-monitors services needs to be installed/listed.

   .. code-block:: console

      $ systemctl list-unit-files devstack@masakari*.service

      UNIT FILE                                              STATE
      devstack@masakari-hostmonitor.service                  enabled
      devstack@masakari-instancemonitor.service              enabled
      devstack@masakari-introspectiveinstancemonitor.service enabled
      devstack@masakari-processmonitor.service               enabled

#. List API endpoints in the Identity service to verify connectivity with the
   Identity service:

   .. note::

      Endpoints below list may differ depending on the installation of
      OpenStack components.

   .. code-block:: console

      $ openstack endpoint list

      +-------------+----------------+--------------------------------------------------------+
      | Name        | Type           | Endpoints                                              |
      +-------------+----------------+--------------------------------------------------------+
      | nova_legacy | compute_legacy | RegionOne                                              |
      |             |                |   public: http://controller/compute/v2/<tenant_id>     |
      |             |                |                                                        |
      | nova        | compute        | RegionOne                                              |
      |             |                |   public: http://controller/compute/v2.1               |
      |             |                |                                                        |
      | cinder      | block-storage  | RegionOne                                              |
      |             |                |   public: http://controller/volume/v3/<tenant_id>      |
      |             |                |                                                        |
      | glance      | image          | RegionOne                                              |
      |             |                |   public: http://controller/image                      |
      |             |                |                                                        |
      | cinderv3    | volumev3       | RegionOne                                              |
      |             |                |   public: http://controller/volume/v3/<tenant_id>      |
      |             |                |                                                        |
      | masakari    | instance-ha    | RegionOne                                              |
      |             |                | internal: http://controller/instance-ha/v1/<tenant_id> |
      |             |                | RegionOne                                              |
      |             |                |  admin: http://controller/instance-ha/v1/<tenant_id>   |
      |             |                | RegionOne                                              |
      |             |                |  public: http://controller/instance-ha/v1/<tenant_id>  |
      |             |                |                                                        |
      | keystone    | identity       | RegionOne                                              |
      |             |                |   public: http://controller/identity                   |
      |             |                | RegionOne                                              |
      |             |                |   admin: http://controller/identity                    |
      |             |                |                                                        |
      | cinderv2    | volumev2       | RegionOne                                              |
      |             |                |   public: http://controller/volume/v2/<tenant_id>      |
      |             |                |                                                        |
      | placement   | placement      | RegionOne                                              |
      |             |                |   public: http://controller/placement                  |
      |             |                |                                                        |
      | neutron     | network        | RegionOne                                              |
      |             |                |   public: http://controller:9696/                      |
      |             |                |                                                        |
      +-------------+----------------+--------------------------------------------------------+

#. Check CRM status

   .. code-block:: console

      $ sudo crm status

      Stack: corosync
      Current DC: controller (version 1.1.18-2b07d5c5a9) - partition with quorum
      Last updated: Thu Jul 11 13:33:17 2019

      2 nodes configured
      2 resources configured

      Online: [ compute-1, compute-2 ]
      OFFLINE: [ ]

      Full list of resources:

       st-null        (stonith:null): Started compute
