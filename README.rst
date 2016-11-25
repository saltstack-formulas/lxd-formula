===
LXD
===

`LXD`_ is a container "hypervisor". This formulas provides
several states to help manage it and its containers.

This formula will allow you to:

- Initialize LXD with storage, authentication and network settings.
- Create some default settings for containers (profiles).
- Pull an image from various sources.
- Create a container with an image.
- Start/Stop/Restart/Freeze/Unfreeze/Migrate a container.
- And finaly undo all of the above.

Before we forget it, `LXD`_ and this formula allows you to
**migrate unprivliged containers** from one host to another!

.. _LXD: https://linuxcontainers.org/lxd/


TODOS
=====

- Add suppport for file pull/push (with salt:// support).
- Add support for container_exec.


Requirements
============

- There are currently only LXD packages for Ubuntu GNU/Linux so for the daemon
  you need Ubuntu.
- This has been tested with Saltstack `2016.3.1`, we don't know if it
  works with other versions.
- `PyLXD`_ version 2.0.5 from PIP (enable use_pip and it will get that version!).

.. _PyLXD: https://github.com/pcdummy/pylxd
.. _169: https://github.com/lxc/pylxd/pull/169

Installation
============

Clone and symlink
-----------------

- Put/symlink the contents of **_modules** into **salt/base/_modules/**.
- Put/symlink the contents of **_states** into **salt/base/_states/**.
- Put/symlink the directory **lxd** into **salt/base/**

Per git remote
--------------

.. code-block:: yaml

    gitfs_remotes:
      - https://github.com/pcdummy/saltstack-lxd-formula.git


Available states
================

.. contents::
    :local:

``lxd.init``
-------------

Does everthing below.


``lxd.lxd``
-----------

Installs lxd manages its settings.


Minimal examples
++++++++++++++++

To not listen on the network and use the default storage engine

.. code-block:: yaml

    lxd:
      lxd:
        run_init: True

      python:
        # Currently pylxd version 2 is required for the lxd module to work.
        use_pip: True

To listen on the network:

.. code-block:: yaml

    lxd:
      lxd:
        run_init: True

        init:
          trust_password: "PaSsW0rD"
          network_address: "[::]"
          network_port: "8443"


      python:
        # Currently pylxd version 2 is required for the lxd module to work.
        use_pip: True

Config examples
+++++++++++++++

.. code-block:: yaml

    lxd:
      lxd:
        run_init: True

        init:
          trust_password: "PaSsW0rD"
          network_address: "[::]"
          network_port: "8443"


        # Lets say you configured the password wrong on init or want to change it:
        config:
          password:
            key: core.trust_password
            value: "VerySecure!337"
            force_password: True    # Currently this will be executed every time
                                    # you execute this state.

        # Now lets say somewhere else you want to change the ip LXD is listening one
          network:
            key: core.https_address
            value: "[fd57:1:see:bad:c0de::14]:8443"


      python:
        # Currently pylxd version 2 is required for the lxd module to work.
        use_pip: True


``lxd.client``
--------------

Installs the lxd client - its a simple package installer for `lxd-client` (on Debian at least).


``lxd.python``
--------------

Installs pylxd, this requires the `pip-formula`_ if you enable "use_pip".

.. _pip-formula: https://github.com/saltstack-formulas/pip-formula


``lxd.remotes``
---------------

Manages pylxd server connections, this is usefull when you want
to create profiles/images/containers on remote LXD instances.

.. attention::

    Migrations and image copies don't work with provided "local" endpoint, overwrite it if you want to migrate from/to local.

Overwrite **local**:
++++++++++++++++++++

Migrations and image copies don't work with provided "local" endpoint, overwrite it.

.. code-block:: yaml

    lxd:
      remotes:
        local:
          type: lxd
          remote_addr : "https://srv02:8443"
          cert : "/root/.config/lxc/client.crt"
          key : "/root/.config/lxc/client.key"
          verify_cert : False
          password" : "PaSsW0rD"

A named remote
++++++++++++++

This is just here for other states to get its values.

.. code-block:: yaml

    lxd:
      remotes:
        srv01:
          type: lxd
          remote_addr : "https://srv01:8443"
          cert : "/root/.config/lxc/client.crt"
          key : "/root/.config/lxc/client.key"
          verify_cert : False

A remote we try to authenticate to
++++++++++++++++++++++++++++++++++

.. code-block:: yaml

    lxd:
      remotes:
        srv02:
          type: lxd
          remote_addr : "https://srv02:8443"
          cert : "/root/.config/lxc/client.crt"
          key" : "/root/.config/lxc/client.key"
          verify_cert : False
          password" : "PaSsW0rD"


``lxd.profiles``
----------------

Manages LXD profiles, profiles are something like defaults for a container,
you can add multible profiles to a single container.

Its general a good idea to look how profiles look on the `wire`_:

.. _wire: https://github.com/lxc/lxd/blob/master/doc/rest-api.md#post-10

Also:

.. code-block:: bash

   salt-call lxd.profile_list --out=json

   salt-call lxd.container_list --out=json

gives nice informations about profile config keys and devices.


A local profile that enables autostart
++++++++++++++++++++++++++++++++++++++


.. code-block:: yaml

    lxd:
      profiles:
        local:    # local is special it means local unix socket, not authentication needed.
          autostart:
            config:
              # Enable autostart
              boot.autostart: 1
              # Delay between containers in seconds.
              boot.autostart.delay: 2
              # The lesser the later it gets started on autostart.
              boot.autostart.priority: 1


The same profile on the "named" remote "srv01"
++++++++++++++++++++++++++++++++++++++++++++++

.. code-block:: yaml

    lxd:
      profiles:
        srv01:    # Notice the change from "local" to "srv01"
          autostart:
            config:
              # Enable autostart
              boot.autostart: 1
              # Delay between containers in seconds.
              boot.autostart.delay: 2
              # The lesser the later it gets started on autostart.
              boot.autostart.priority: 1


A local profile that adds a interface
+++++++++++++++++++++++++++++++++++++

.. code-block:: yaml

    lxd:
      profiles:
        local:
          add_eth1:
            devices:
              eth1:
                type: "nic"
                nictype": "bridged"
                parent": "br1"


A local profile that adds a shared mount point
++++++++++++++++++++++++++++++++++++++++++++++

.. code-block:: yaml

    lxd:
      profiles:
        local:
          shared_mount:
            devices:
              shared_mount:
                type: "disk"
                # Source on the host
                source: "/home/shared"
                # Path in the container
                path: "home/shared"


A limited container profile
+++++++++++++++++++++++++++

See `stgraber's blog`_

.. _stgraber's blog: https://www.stgraber.org/2016/03/26/lxd-2-0-resource-control-412/

.. code-block:: yaml

    lxd:
      profiles:
        local:
          small:
            config:
              limits.cpu: 1
              limits.memory: 512MB
              limits.read: 20Iops
              limits.write: 10Iops


MongoDB special case
++++++++++++++++++++

If you use the MongoDB ext_pillar you will notice that it doesn't like
dots in field names, this is why we added a special case for that:

.. code-block:: yaml

    lxd:
      profiles:
        local:
          autostart:
            config:
              # Notice the key/value style here
              - key: boot.autostart
                value: 1
              - key: boot.autostart.delay
                value: 2
              - key: boot.autostart.priority
                value: 1


To remove a profile
+++++++++++++++++++

.. code-block:: yaml

    lxd:
      profiles:
        local:
          autostart:
            absent: True


``lxd.images``
--------------

Manages LXD images.

To create an image from file on host 'local'
++++++++++++++++++++++++++++++++++++++++++++

.. code-block:: yaml

    lxd:
      images:
        local:
          busybox:
            name: busybox     # Its alias
            source:
              type: file
              filename: salt://lxd/files/busybox.tar.xz
              saltenv: base


To create an image from the provided "images" remote
++++++++++++++++++++++++++++++++++++++++++++++++++++

On `images.linuxcontainers.org`_ you see a list of images available.

.. _images.linuxcontainers.org: http://images.linuxcontainers.org/

And with ``lxc image list images:`` you get a list of aliases.

.. code-block:: yaml

    lxd:
      images:
        local:
          xenial_amd64:
            name: xenial/amd64    # Its alias
            source:
              name: ubuntu/xenial/amd64
              remote: images_linuxcontainers_org    # See map.jinja for it
            aliases: ['x', 'xa64']  # More aliases
            public: False
            auto_update: True


To create an image from "simplestreams"
+++++++++++++++++++++++++++++++++++++++

We also implemented a way to copy images from simplestreams, to do so:

.. code-block:: yaml

    lxd:
      images:
        local:
          trusty_amd64:
            source:
              name: trusty/amd64
              remote: ubuntu    # See map.jinja for it
            aliases: ['t', 'ta64']  # More aliases
            public: False
            auto_update: True

Those simplestreams images have cloud-init integrated! Use

    $ lxc image alias list ubuntu:

to get a list of available aliases.


To create an image from an URL
++++++++++++++++++++++++++++++

.. code-block:: yaml

    lxd:
      images:
        local:
          trusty_amd64:
            source:
              type: url
              url: https://dl.stgraber.org/lxd
            aliases: ['busbox-amd64']  # More aliases
            public: False
            auto_update: True


``lxd.containers``
------------------

Manages LXD containers, this includes `lxd.images`, `lxd.profiles` and `lxd.remotes`.


To create a container and start it
++++++++++++++++++++++++++++++++++

From the image alias "xenial/amd64"

.. code-block:: yaml

    lxd:
      containers:
        local:
          ubuntu-xenial:
            running: True
            source: xenial/amd64


Same with the profiles "default" and "autostart"
++++++++++++++++++++++++++++++++++++++++++++++++

We also add a higher start priority and a device eth1

.. code-block:: yaml

    lxd:
      containers:
        local:
          ubuntu-xenial2:
            running: True
            source: xenial/amd64
            profiles:
              - default
              - autostart
            config:
              boot.autostart.priority: 1000
            devices:
              eth1:
                type: "nic"
                nictype": "bridged"
                parent": "br1"
            opts:
              require:
                - lxd_profile: lxd_profile_local_autostart


Later you might want migrate "ubuntu-xenial" to "srv01"
+++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. code-block:: yaml

    lxd:
      containers:
        srv01:
          ubuntu-xenial:
            migrated: True
            stop_and_start: True    # No live-migration but start/stop.
            source: local       # Note that we've overwritten "local",
                                # else this wont work!


And finaly send it to /dev/null
+++++++++++++++++++++++++++++++

.. code-block:: yaml

    lxd:
      containers:
        srv01:
          ubuntu-xenial:
            absent: True
            stop: True


LXD execution Module
====================

Please see `execution_module doc`_ for it, or better directly the well documented
sourcecode of the `LXD Module`_.

.. _execution_module doc: doc/execution_module.rst
.. _LXD Module: _modules/lxd.py


Authors
=======

`René Jochum`_ <rene@jochums.at>

.. _René Jochum: https://rene.jochums.at

License
=======

Apache Version 2.0
