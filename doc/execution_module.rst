====================
LXD execution Module
====================

The `LXD`_ execution Module is the base of the LXD formula
and we have designed it to let you run everthing the formula does
over salt/salt-call.

We first made the execution module and then the states and formula around it.

.. _LXD: https://linuxcontainers.org/lxd/


Requirements
============

See the lxd-formula `README`_.

.. _README: https://github.com/pcdummy/saltstack-lxd-formula/blob/master/README.rst#requirements


Parmeters available to the most of methods
==========================================

remote_addr :
    An URL to a remote Server, you also have to give cert and key if you
    provide remote_addr and its a TCP Address!

    Examples:
        - https://myserver.lan:8443
        - http+unix:///var/lib/mysocket.sock

cert :
    PEM Formatted SSL Zertifikate.

    Example:

        - $HOME/.config/lxc/client.crt

key :
    PEM Formatted SSL Key.

    Example:
        - $HOME/.config/lxc/client.key

verify_cert : True
    Wherever to verify the cert, this is by default True
    but in the most cases you want to set it off as LXD
    normaly uses self-signed certificates.

See the `requests-docs` for the SSL stuff.

.. _requests-docs: http://docs.python-requests.org/en/master/user/advanced/#ssl-cert-verification


Available methods
=================

The `LXD Module`_ is well documented, we don't want to copy its docs here to not have desync errors.

.. _LXD Module: ../_modules/lxd.py
