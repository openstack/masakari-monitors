=======================
masakari-processmonitor
=======================

Monitor Overview
------------------
The masakari-processmonitor, provides key process High Availability
for OpenStack clouds by automatically detecting the process failure.
If it detects process failure, it sends notifications to masakari-api.

If your OpenStack service runs in container(pod), this processmonitor
will not work as expected. It is recommended not to deploy processmonitor.


How does it work?
-------------------
- Processes to be monitored should be pre-configured in process_list.yaml
  file.

Define one process to be monitored as follows:

.. code-block:: ini

    process_name: [Name of the process as it in 'ps -ef'.]
    start_command: [Start command of the process.]
    pre_start_command: [Command which is executed before start_command.]
    post_start_command: [Command which is executed after start_command.]
    restart_command: [Restart command of the process.]
    pre_restart_command: [Command which is executed before restart_command.]
    post_restart_command: [Command which is executed after restart_command.]
    run_as_root: [Bool value whether to execute commands as root authority.]

Sample of definitions is shown as follows:

.. code-block:: ini

    # nova-compute
    process_name: /usr/local/bin/nova-compute
    start_command: systemctl start nova-compute
    pre_start_command:
    post_start_command:
    restart_command: systemctl restart nova-compute
    pre_restart_command:
    post_restart_command:
    run_as_root: True

- If masakari-processmonitor detects one process failure, it will try to
  restart it firstly. After several retries failed, it sends notification
  to masakari-api.


Related configurations
------------------------
This section in masakarimonitors.conf shows an example of how to configure
the monitor.

.. code-block:: ini

    [process]
    # Interval in seconds for checking a process.
    check_interval = 5

    # Number of retries when the failure of restarting a process.
    restart_retries = 3

    # Interval in seconds for restarting a process.
    restart_interval = 5

    # The file path of process list.
    process_list_path = /etc/masakarimonitors/process_list.yaml
