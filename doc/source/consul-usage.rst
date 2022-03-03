=============
Consul Usage
=============

Consul overview
================

Consul is a service mesh solution providing a full featured control plane
with service discovery, configuration, and segmentation functionality.
Each of these features can be used individually as needed, or they can be
used together to build a full service mesh.

The Consul agent is the core process of Consul. The Consul agent maintains
membership information, registers services, runs checks, responds to queries,
and more.

Consul clients can provide any number of health checks, either associated
with a given service or with the local node. This information can be used
by an operator to monitor cluster health.

Please refer to `Consul Agent Overview <https://www.consul.io/docs/agent>`_.

Test Environment
================

There are three controller nodes and two compute nodes in the test environment.
Every node has three network interfaces. The first interface is used for
management, with an ip such as '192.168.101.*'. The second interface is used
to connect to storage, with an ip such as '192.168.102.*'. The third interface
is used for tenant, with an ip such as '192.168.103.*'.


Download Consul
================

Download Consul package for CentOS. Other OS please refer to `Download Consul
<https://www.consul.io/downloads>`_.

  .. code-block:: console

    sudo yum install -y yum-utils
    sudo yum-config-manager --add-repo https://rpm.releases.hashicorp.com/RHEL/hashicorp.repo
    sudo yum -y install Consul

Configure Consul agent
======================

Consul agent must runs on every node. Consul server agent runs on controller
nodes, while Consul client agent runs on compute nodes, which makes up one
Consul cluster.

The following is an example of a config file for Consul server agent which
binds to management interface of the host.

management.json

  .. code-block:: ini

    {
        "bind_addr": "192.168.101.1",
        "datacenter": "management",
        "data_dir": "/tmp/consul_m",
        "log_level": "INFO",
        "server": true,
        "bootstrap_expect": 3,
        "node_name": "node01",
        "addresses": {
            "http": "192.168.101.1"
        },
        "ports": {
            "http": 8500,
            "serf_lan": 8501
        },
        "retry_join": ["192.168.101.1:8501", "192.168.101.2:8501", "192.168.101.3:8501"]
    }


The following is an example of a config file for Consul client agent which
binds to management interface of the host.

management.json

  .. code-block:: ini

    {
        "bind_addr": "192.168.101.4",
        "datacenter": "management",
        "data_dir": "/tmp/consul_m",
        "log_level": "INFO",
        "node_name": "node04",
        "addresses": {
            "http": "192.168.101.4"
        },
        "ports": {
            "http": 8500,
            "serf_lan": 8501
        },
        "retry_join": ["192.168.101.1:8501", "192.168.101.2:8501", "192.168.101.3:8501"]
    }

Use the tenant or storage interface ip and ports when config agent in tenant
or storage datacenter.

Please refer to `Consul Agent Configuration <https://www.consul.io/docs/agent/options#command-line-options>`_.

Start Consul agent
==================

The Consul agent is started by the following command.

  .. code-block:: console

    # Consul agent –config-file management.json

Test Consul installation
========================

After all Consul agents installed and started,
you can see all nodes in the cluster by the following command.

  .. code-block:: console

    # Consul members -http-addr=192.168.101.1:8500
    Node    Address              Status  Type    Build   Protocol  DC
    node01  192.168.101.1:8501   alive   server  1.10.2  2         management
    node02  192.168.101.2:8501   alive   server  1.10.2  2         management
    node03  192.168.101.3:8501   alive   server  1.10.2  2         management
    node04  192.168.101.4:8501   alive   client  1.10.2  2         management
    node05  192.168.101.5:8501   alive   client  1.10.2  2         management
