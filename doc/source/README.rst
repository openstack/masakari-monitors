=====================
Monitors for Masakari
=====================

Configure masakari-monitors
---------------------------

#. Clone masakari using::

   $ git clone https://opendev.org/openstack/masakari-monitors

#. Create masakarimonitors directory in /etc/.

#. Run setup.py from masakari-monitors::

   $ sudo python3 setup.py install

#. Copy masakarimonitors.conf and process_list.yaml files from
   masakari-monitors/etc/ to /etc/masakarimonitors folder and make necessary
   changes to the masakarimonitors.conf and process_list.yaml files.
   To generate the sample masakarimonitors.conf file, run the following
   command from the top level of the masakari-monitors directory::

   $ tox -egenconfig

#. To run masakari-processmonitor, masakari-hostmonitor and
   masakari-instancemonitor simply use following binary::

   $ masakari-processmonitor
   $ masakari-hostmonitor
   $ masakari-instancemonitor
