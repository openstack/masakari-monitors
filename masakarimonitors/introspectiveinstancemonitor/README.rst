=========================================
masakarimonitors-introspectiveinstancemonitor
=========================================

Introspective instance monitor for Masakari
----------------------------------------
- masakarimonitors-introspectiveinstancemonitor, provides Virtual Machine
  High Availability (VMHA) service for OpenStack clouds by automatically
  detecting the system-level failure events via QEMU Guest Agent. If it
  detects VM heartbeat failure events, it sends notifications to the
  masakari-api.


- Based on the QEMU Guest Agent,
  masakarimonitors-introspectiveinstancemonitor aims to provide access
  to a system-level agent via standard qemu-ga protocol


How does it work?
----------------------------------------
- libvirt and QEMU Guest Agent are used as the underlying protocol for
  messaging to and from VM.

  - The host-side qemu-agent sockets are used to determine whether VMs are
    configured with QEMU Guest Agent.

  - qemu-guest-ping is used as the monitoring heartbeat.

- For the future release, we can pass through arbitrary guest agent commands
  to check the health of the applications inside a VM.

QEMU Guest Agent Installation notes
----------------------------------------

- Set image property: hw_qemu_guest_agent=yes.

  - This tells NOVA to setup the virtual serial interface thru QEMU to VM

  - e.g.

    $ openstack image create --public --disk-format qcow2 --container-format
    bare --file ~ubuntu/xenial-server-cloudimg-amd64-disk1.img --public
    --property hw_qemu_guest_agent=yes xenial-server-cloudimg

* Inside VM::

  $ sudo apt-get install qemu-guest-agent
  $ sudo systemctl  start qemu-guest-agent
  $ ubuntu@test:~$ ps -ef | fgrep qemu
  $ ...  /usr/sbin/qemu-ga --daemonize -m virtio-serial -p /dev/virtio-ports/org.qemu.guest_agent.0
  $ ubuntu@test:~$ ls /dev/virtio-ports/
  $ org.qemu.guest_agent.0


Configure masakarimonitors-introspectiveinstancemonitor
----------------------------------------------
#. Clone masakari-monitors using::

   $ git clone https://github.com/openstack/masakari-monitors.git

#. Create masakarimonitors directory in /etc/.

#. Run setup.py from masakari-monitors::

   $ sudo python setup.py install

#. Copy masakarimonitors.conf and process_list.yaml files from
   masakari-monitors/etc/ to /etc/masakarimonitors folder and make necessary
   changes to the masakarimonitors.conf and process_list.yaml files.
   To generate the sample masakarimonitors.conf file, run the following
   command from the top level of the masakari-monitors directory::

   $ tox -egenconfig

#. To run masakari-introspectiveinstancemonitor simply use following binary::

   $ masakari-introspectiveinstancemonitor

