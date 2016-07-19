# -*- coding: utf-8 -*-
'''
Manage LXD containers.

.. versionadded:: unknown

:maintainer: René Jochum <rene@jochums.at>
:maturity: new
:depends: python-pylxd
:platform: Linux
'''

# Import python libs
from __future__ import absolute_import, print_function
import os.path

# Import salt libs
from salt.exceptions import CommandExecutionError
from salt.exceptions import SaltInvocationError

# Set up logging
import logging
log = logging.getLogger(__name__)

__docformat__ = 'restructuredtext en'

# PEP8
__opts__ = {}
__salt__ = {}

__virtualname__ = 'lxd_container'


def __virtual__():
    '''
    Only load if the lxd module is available in __salt__
    '''
    return __virtualname__ if 'lxd.version' in __salt__ else False


def present(name, running=None):
    pass


def absent(name, stop=False):
    pass


def running(name, restart=False):
    pass


def frozen(name, start=True):
    pass


def stopped(name, kill=False):
    pass


def migrate(name):
    pass
