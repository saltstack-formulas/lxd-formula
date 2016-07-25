# -*- coding: utf-8 -*-
'''
Module for managing the LXD daemon and its containers.

.. versionadded:: unknown

`LXD(1)`__ is a container "hypervisor". This execution module provides
several functions to help manage it and its containers.

.. note:

    - `pylxd(2)`__ version 2 is required to let this work,
      currently only available via pip.

        To install on Ubuntu:

        $ apt-get install libssl-dev python-pip
        $ pip install -U pylxd

    - you need lxd installed on the minion
      for the init() and version() methods.

    - for the config_get() and config_get() methods
      you need to have lxd-client installed.

.. __: https://linuxcontainers.org/lxd/
.. __: https://github.com/lxc/pylxd/blob/master/doc/source/installation.rst

:maintainer: René Jochum <rene@jochums.at>
:maturity: new
:depends: python-pylxd
:platform: Linux
'''

# Import python libs
from __future__ import absolute_import, print_function
import os
from distutils.version import LooseVersion

# Import salt libs
import salt.utils.decorators
from salt.exceptions import CommandExecutionError
from salt.exceptions import SaltInvocationError
import salt.ext.six as six

# Import 3rd-party libs
try:
    import pylxd
    PYLXD_AVAILABLE = True
except ImportError:
    PYLXD_AVAILABLE = False

# Set up logging
import logging
log = logging.getLogger(__name__)

__docformat__ = 'restructuredtext en'

# PEP8
__salt__ = {}

_pylxd_minimal_version = "2.0.4"

# Keep in sync with: https://github.com/lxc/lxd/blob/master/shared/architectures.go  # noqa
_architectures = {
    'unknown': '0',
    'i686': '1',
    'x86_64': '2',
    'armv7l': '3',
    'aarch64': '4',
    'ppc': '5',
    'ppc64': '6',
    'ppc64le': '7',
    's390x': '8'
}

# Keep in sync with: https://github.com/lxc/lxd/blob/master/shared/status.go
CONTAINER_STATUS_RUNNING = 103

__virtualname__ = 'lxd'

_connection_pool = {}


def __virtual__():
    if PYLXD_AVAILABLE:
        # Increment this once we use the new features of PyLXD (images!)
        if (LooseVersion(pylxd_version()) <
                LooseVersion(_pylxd_minimal_version)):
            return (
                False,
                ('The lxd execution module cannot be loaded:'
                 ' pylxd "{0}" is not supported,'
                 ' you need at least pylxd "{1}"').format(
                    pylxd_version(),
                    _pylxd_minimal_version)
            )

        return __virtualname__

    return (
        False,
        ('The lxd execution module cannot be loaded: '
         'the pylxd python module is not available.')
    )


################
# LXD Management
################
@salt.utils.decorators.which('lxd')
def version():
    '''
    Returns the actual lxd version.

    CLI Example:

    .. code-block:: bash

        salt '*' lxd.version

    '''
    return __salt__['cmd.run']('lxd --version')


def pylxd_version():
    '''
    Returns the actual pylxd version.

    CLI Example:

    .. code-block:: bash

        salt '*' lxd.pylxd_version

    '''
    return pylxd.__version__


@salt.utils.decorators.which('lxd')
def init(storage_backend='dir', trust_password=None, network_address=None,
         network_port=None, storage_create_device=None,
         storage_create_loop=None, storage_pool=None):
    '''
    Calls lxd init --auto -- opts

    storage_backend :
        Storage backend to use (zfs or dir, default: dir)

    trust_password :
        Password required to add new clients

    network_address : None
        Address to bind LXD to (default: none)

    network_port : None
        Port to bind LXD to (Default: 8443)

    storage_create_device : None
        Setup device based storage using this DEVICE

    storage_create_loop : None
        Setup loop based storage with this SIZE in GB

    storage_pool : None
        Storage pool to use or create

    CLI Examples:

    To listen on all IPv4/IPv6 Addresses:

    .. code-block:: bash

        salt '*' lxd.init dir PaSsW0rD [::]

    To not listen on Network:

    .. code-block:: bash

        salt '*' lxd.init
    '''

    cmd = ('lxd init --auto'
           ' --storage-backend="{0}"').format(
        storage_backend
    )

    if trust_password is not None:
        cmd = cmd + ' --trust-password="{0}"'.format(trust_password)

    if network_address is not None:
        cmd = cmd + ' --network-address="{0}"'.format(network_address)

    if network_port is not None:
        cmd = cmd + ' --network-port="{0}"'.format(network_port)

    if storage_create_device is not None:
        cmd = cmd + ' --storage-create-device="{0}"'.format(
            storage_create_device
        )

    if storage_create_loop is not None:
        cmd = cmd + ' --storage-create-loop="{0}"'.format(
            storage_create_loop
        )

    if storage_pool is not None:
        cmd = cmd + ' --storage-pool="{0}"'.format(storage_pool)

    try:
        output = __salt__['cmd.run'](cmd)
    except ValueError as e:
        raise CommandExecutionError(
            "Failed to call: '{0}', error was: {1}".format(cmd, str(e)),
        )

    if 'error:' in output:
        raise CommandExecutionError(
            output[output.index('error:') + 7:],
        )

    return output


@salt.utils.decorators.which('lxd')
@salt.utils.decorators.which('lxc')
def config_set(key, value):
    '''
    CLI Examples:

    To listen on IPv4 and IPv6 port 8443,
    you can omit the :8443 its the default:

    .. code-block:: bash

        salt '*' lxd.config_set core.https_address [::]:8443

    To set the server trust password:

    .. code-block:: bash

        salt '*' lxd.config_set core.trust_password blah

    '''
    cmd = 'lxc config set "{0}" "{1}"'.format(
        key,
        value,
    )

    output = __salt__['cmd.run'](cmd)
    if 'error:' in output:
        raise CommandExecutionError(
            output[output.index('error:') + 7:],
        )

    return 'Config value "{0}" successfully set.'.format(key),


@salt.utils.decorators.which('lxd')
@salt.utils.decorators.which('lxc')
def config_get(key):
    cmd = 'lxc config get "{0}"'.format(
        key
    )

    output = __salt__['cmd.run'](cmd)
    if 'error:' in output:
        raise CommandExecutionError(
            output[output.index('error:') + 7:],
        )

    return output


#######################
# Connection Management
#######################
def pylxd_client_get(remote_addr=None, cert=None, key=None, verify_cert=True):
    '''
    Get an pyxld client, this is not ment to be runned over the CLI.

    remote_addr :
        An URL to a remote Server, you also have to give cert and key if you
        provide remote_addr and its a TCP Address!

        Examples:
            https://myserver.lan:8443
            /var/lib/mysocket.sock

    cert :
        PEM Formatted SSL Zertifikate.

        Examples:
            ~/.config/lxc/client.crt

    key :
        PEM Formatted SSL Key.

        Examples:
            ~/.config/lxc/client.key

    verify_cert : True
        Wherever to verify the cert, this is by default True
        but in the most cases you want to set it off as LXD
        normaly uses self-signed certificates.

    See the `requests-docs`_ for the SSL stuff.

    .. _requests-docs: http://docs.python-requests.org/en/master/user/advanced/#ssl-cert-verification

    # noqa
    '''

    pool_key = '|'.join((six.text_type(remote_addr),
                         six.text_type(cert),
                         six.text_type(key),
                         six.text_type(verify_cert),))

    if pool_key in _connection_pool:
        log.debug((
            'Returning the client "{0}" from our connection pool'
        ).format(remote_addr))
        return _connection_pool[pool_key]

    try:
        if remote_addr is None:
            client = pylxd.Client()
        else:
            if remote_addr.startswith('/'):
                client = pylxd.Client(remote_addr)
            else:
                if cert is None or key is None:
                    raise SaltInvocationError(
                        ('You have to give a Cert and '
                         'Key file for remote endpoints.')
                    )

                cert = os.path.expanduser(cert)
                key = os.path.expanduser(key)

                if not os.path.isfile(cert):
                    raise SaltInvocationError(
                        ('You have given an invalid cert path: "{0}", '
                         'the file does not exists or is not a file.').format(
                            cert
                        )
                    )

                if not os.path.isfile(key):
                    raise SaltInvocationError(
                        ('You have given an invalid key path: "{0}", '
                         'the file does not exists or is not a file.').format(
                            key
                        )
                    )

                client = pylxd.Client(
                    endpoint=remote_addr,
                    cert=(cert, key,),
                    verify=verify_cert
                )
    except pylxd.exceptions.ClientConnectionFailed:
        raise CommandExecutionError(
            "Failed to connect to '{0}'".format(remote_addr)
        )

    except TypeError as e:
        # Happens when the verification failed.
        raise CommandExecutionError(
            ('Failed to connect to "{0}",'
             ' looks like the SSL verification failed, error was: {1}'
             ).format(remote_addr, str(e))
        )

    _connection_pool[pool_key] = client

    return client


def pylxd_save_object(obj):
    ''' Saves an object (profile/image/container) and
        translate its execpetion on failure.

    '''
    try:
        obj.save()
    except pylxd.exceptions.LXDAPIException as e:
        raise CommandExecutionError(str(e))

    return True


def authenticate(remote_addr, password, cert, key, verify_cert=True):
    '''
    Authenticate with a remote LXDaemon.

    remote_addr :
        An URL to a remote Server, you also have to give cert and key if you
        provide remote_addr and its a TCP Address!

        Examples:
            https://myserver.lan:8443

    password :
        The password of the remote.

    cert :
        PEM Formatted SSL Zertifikate.

        Examples:
            ~/.config/lxc/client.crt

    key :
        PEM Formatted SSL Key.

        Examples:
            ~/.config/lxc/client.key

    verify_cert : True
        Wherever to verify the cert, this is by default True
        but in the most cases you want to set it off as LXD
        normaly uses self-signed certificates.

    CLI Example:

    .. code-block:: bash

        $ salt '*' lxd.authenticate https://srv01:8443 <yourpass> ~/.config/lxc/client.crt ~/.config/lxc/client.key false

    See the `requests-docs`_ for the SSL stuff.

    .. _requests-docs: http://docs.python-requests.org/en/master/user/advanced/#ssl-cert-verification

    # noqa
    '''
    client = pylxd_client_get(remote_addr, cert, key, verify_cert)

    if client.trusted:
        return True

    try:
        client.authenticate(password)
    except pylxd.exceptions.LXDAPIException as e:
        # Wrong password
        raise CommandExecutionError(str(e))

    return client.trusted


######################
# Container Management
######################
def container_list(list_names=False, remote_addr=None,
                   cert=None, key=None, verify_cert=True):
    '''

    CLI Examples:

    Full dict with all available informations:

    .. code-block:: bash

        salt '*' lxd.container_list

    For a list of names:

    .. code-block:: bash

        salt '*' lxd.container_list true

    # See: https://github.com/lxc/pylxd/blob/master/doc/source/containers.rst#container-attributes

    # noqa
    '''

    client = pylxd_client_get(remote_addr, cert, key, verify_cert)
    containers = client.containers.all()
    if list_names:
        return [c.name for c in containers]

    return [c.dict() for c in containers]


def container_create(name, source, profiles=['default'],
                     config={}, devices={}, architecture='x86_64',
                     ephemeral=False, wait=True,
                     remote_addr=None, cert=None, key=None, verify_cert=True,
                     _raw=False):
    '''
    CLI Examples:

    .. code-block:: bash

        salt '*' lxd.container_create test xenial/amd64

    # See: https://github.com/lxc/lxd/blob/master/doc/rest-api.md#post-1
    '''
    client = pylxd_client_get(remote_addr, cert, key, verify_cert)

    if not isinstance(profiles, (list, tuple, set,)):
        raise SaltInvocationError(
            "'profiles' must be formatted as list/tuple/set."
        )

    if architecture not in _architectures:
        raise SaltInvocationError(
            ("Unknown architecture '{0}' "
             "given for the container '{1}'").format(architecture, name)
        )

    if isinstance(source, six.string_types):
        source = {'type': 'image', 'alias': source}

    config, devices, normalize_input_values(
        config,
        devices
    )

    try:
        container = client.containers.create(
            {
                'name': name,
                'architecture': _architectures[architecture],
                'profiles': profiles,
                'source': source,
                'config': config,
                'ephemeral': ephemeral
            },
            wait=wait
        )
    except pylxd.exceptions.LXDAPIException as e:
        raise CommandExecutionError(
            str(e)
        )

    if not wait:
        return container.json()['operation']

    if _raw:
        return container

    return container.dict()


def container_get(name, remote_addr=None,
                  cert=None, key=None, verify_cert=True, _raw=False):
    ''' Gets a container from the LXD

        name :
            The name of the container to get.

        remote_addr, cert, key, verify_cert:
            See pylxd_client_get

        _raw :
            Return the pylxd object, this is internal and by states in use.
    '''
    client = pylxd_client_get(remote_addr, cert, key, verify_cert)

    container = None
    try:
        container = client.containers.get(name)
    except pylxd.exceptions.LXDAPIException:
        raise SaltInvocationError(
            'Container \'{0}\' not found'.format(name)
        )

    if _raw:
        return container

    return container.dict()


def container_delete(name, remote_addr=None,
                     cert=None, key=None, verify_cert=True):
    container = container_get(
        name, remote_addr, cert, key, verify_cert, _raw=True
    )
    container.delete(wait=True)
    return True


def container_rename(name, newname, remote_addr=None,
                     cert=None, key=None, verify_cert=True):
    container = container_get(
        name, remote_addr, cert, key, verify_cert, _raw=True
    )

    if container.status_code == CONTAINER_STATUS_RUNNING:
        raise SaltInvocationError(
            "Can't rename the running container '{0}'.".format(name)
        )

    return container.rename(newname, wait=True).dict()


def container_start(name, remote_addr=None,
                    cert=None, key=None, verify_cert=True):
    '''
    It will always return status=True even if the container is running.
    '''
    container = container_get(
        name, remote_addr, cert, key, verify_cert, _raw=True
    )
    return container.start(wait=True).dict()


def container_stop(name, timeout=30, force=True, remote_addr=None,
                   cert=None, key=None, verify_cert=True):
    '''
    It will always return status=True even if the container is stopped.
    '''
    container = container_get(
        name, remote_addr, cert, key, verify_cert, _raw=True
    )
    return container.stop(timeout, force, wait=True).dict()


def container_restart(name, remote_addr=None,
                      cert=None, key=None, verify_cert=True):
    container = container_get(
        name, remote_addr, cert, key, verify_cert, _raw=True
    )
    return container.restart(wait=True).dict()


def container_freeze(name, remote_addr=None,
                     cert=None, key=None, verify_cert=True):
    '''
    It will always return status=True even if the container is frozen.
    '''
    container = container_get(
        name, remote_addr, cert, key, verify_cert, _raw=True
    )
    return container.freeze(wait=True).dict()


def container_unfreeze(name, remote_addr=None,
                       cert=None, key=None, verify_cert=True):
    '''
    It will always return status=True even if the container is unfrozen.
    '''
    container = container_get(
        name, remote_addr, cert, key, verify_cert, _raw=True
    )
    return container.unfreeze(wait=True).dict()


def container_migrate(name,
                      stop_and_start=False,
                      remote_addr=None,
                      cert=None,
                      key=None,
                      verify_cert=True,
                      src_remote_addr=None,
                      src_cert=None,
                      src_key=None,
                      src_verify_cert=None):
    ''' Migrate a container.

        If the container is running, it either must be shut down
        first (use stop_and_start=True) or criu must be installed
        on the source and destination machines.

        For this operation both certs need to be authenticated,
        use :mod:`lxd.authenticate <salt.modules.lxd.authenticate`
        to authenticate your cert(s).

        name :
            Name of the container to migrate

        stop_and_start :
            Stop the container on the source and start it on dest

        CLI Example:

        .. code-block:: bash

            # Authorize
            salt '*' lxd.authenticate https://srv01:8443 <yourpass> ~/.config/lxc/client.crt ~/.config/lxc/client.key false
            salt '*' lxd.authenticate https://srv02:8443 <yourpass> ~/.config/lxc/client.crt ~/.config/lxc/client.key false

            # Migrate phpmyadmin from srv01 to srv02
            salt '*' lxd.container_migrate phpmyadmin stop_and_start=true remote_addr=https://srv02:8443 cert=~/.config/lxc/client.crt key=~/.config/lxc/client.key verify_cert=False src_remote_addr=https://srv01:8443

    # noqa
    '''
    if src_cert is None:
        src_cert = cert

    if src_key is None:
        src_key = key

    if src_verify_cert is None:
        src_verify_cert = verify_cert

    container = container_get(
        name, src_remote_addr, src_cert, src_key, src_verify_cert, _raw=True
    )

    was_running = container.status_code == CONTAINER_STATUS_RUNNING
    if stop_and_start and was_running:
        container.stop(wait=True)

    dest_client = pylxd_client_get(
        remote_addr, cert, key, verify_cert
    )

    try:
        dest_container = container.migrate(dest_client, wait=True)
    except pylxd.exceptions.LXDAPIException as e:
        raise CommandExecutionError(str(e))

    # Remove the source container
    container.delete(wait=True)

    if stop_and_start and was_running:
        dest_container.start(wait=True)

    return dest_container.dict()


def container_config_get(name, config_key, remote_addr=None,
                         cert=None, key=None, verify_cert=True):
    container = container_get(
        name, remote_addr, cert, key, verify_cert, _raw=True
    )
    return _get_property_dict_item(container, 'config', config_key)


def container_config_set(name, config_key, config_value, remote_addr=None,
                         cert=None, key=None, verify_cert=True):
    container = container_get(
        name, remote_addr, cert, key, verify_cert, _raw=True
    )

    return _set_property_dict_item(
        container, 'config', config_key, config_value
    )


def container_config_delete(name, config_key, remote_addr=None,
                            cert=None, key=None, verify_cert=True):
    container = container_get(
        name, remote_addr, cert, key, verify_cert, _raw=True
    )

    return _delete_property_dict_item(
        container, 'config', config_key
    )


def container_device_get(name, device_name, remote_addr=None,
                         cert=None, key=None, verify_cert=True):
    container = container_get(
        name, remote_addr, cert, key, verify_cert, _raw=True
    )

    return _get_property_dict_item(container, 'devices', device_name)


def container_device_add(name, device_name, device_type='disk',
                         remote_addr=None,
                         cert=None, key=None, verify_cert=True,
                         **kwargs):
    container = container_get(
        name, remote_addr, cert, key, verify_cert, _raw=True
    )

    kwargs['type'] = device_type
    return _set_property_dict_item(
        container, 'devices', device_name, kwargs
    )


def container_device_delete(name, device_name, remote_addr=None,
                            cert=None, key=None, verify_cert=True):
    container = container_get(
        name, remote_addr, cert, key, verify_cert, _raw=True
    )

    return _delete_property_dict_item(
        container, 'devices', device_name
    )


def container_file_put(name, src, dst, recurse=False, remove_existing=False,
                       remote_addr=None,
                       cert=None, key=None, verify_cert=True):
    ''' TODO: This is a WIP.
    '''
    src = os.path.expanduser(src)

    if not os.path.isabs(src):
        raise SaltInvocationError('File path must be absolute.')

    if not os.path.exists(src):
        raise CommandExecutionError(
            'No such file or directory \'{0}\''.format(src)
        )

    try:
        if os.path.isdir(src):
            if not recurse:
                raise SaltInvocationError(
                    ("Cannot copy overwriting a directory "
                     "without recurse flag set to true!")
                )
    except OSError:
        pass


def container_file_get(name, src, dst, remote_addr=None,
                       cert=None, key=None, verify_cert=True):
    ''' TODO: This is a WIP.
    '''
    dst = os.path.expanduser(dst)


####################
# Profile Management
####################
def profile_list(list_names=False, remote_addr=None,
                 cert=None, key=None, verify_cert=True):
    ''' Lists all profiles from the LXD.

        list_names :

            Return a list of names instead of full blown dicts.

        remote_addr, cert, key, verify_cert:
            See pylxd_client_get

        CLI Examples:

        .. code-block:: bash

            salt '*' lxd.profile_list true --out=json
            salt '*' lxd.profile_list --out=json
    '''

    client = pylxd_client_get(remote_addr, cert, key, verify_cert)

    profiles = client.profiles.all()
    if list_names:
        return [p.name for p in profiles]

    return [p.dict() for p in profiles]


def profile_create(name, config=None, devices=None, description=None,
                   remote_addr=None,
                   cert=None, key=None, verify_cert=True):
    ''' Creates a profile.

        name :
            The name of the profile to get.

        config :
            A config dict or None (None = unset).

            Can also be a list:
                [{'key': 'boot.autostart', 'value': 1},
                 {'key': 'security.privileged', 'value': '1'}]

        devices :
            A device dict or None (None = unset).

        description :
            A description string or None (None = unset).

        remote_addr, cert, key, verify_cert:
            See pylxd_client_get

        CLI Examples:

        .. code-block:: bash

            $ salt '*' lxd.profile_create autostart config="{boot.autostart: 1, boot.autostart.delay: 2, boot.autostart.priority: 1}"
            $ salt '*' lxd.profile_create shared_mounts devices="{shared_mount: {type: 'disk', source: '/home/shared', path: '/home/shared'}}"

        See the `lxd-docs`_ for the details about the config and devices dicts.

        .. _lxd-docs: https://github.com/lxc/lxd/blob/master/doc/rest-api.md#post-10

        # noqa
    '''
    client = pylxd_client_get(remote_addr, cert, key, verify_cert)

    config, devices = normalize_input_values(
        config,
        devices
    )

    profile = client.profiles.create(name, config, devices)
    if description is not None:
        profile.description = description
        pylxd_save_object(profile)

    return profile.dict()


def profile_get(name, remote_addr=None,
                cert=None, key=None, verify_cert=True, _raw=False):
    ''' Gets a profile from the LXD

        name :
            The name of the profile to get.

        remote_addr, cert, key, verify_cert:
            See pylxd_client_get

        _raw :
            Return the pylxd object, this is internal and by states in use.

        CLI Examples:

        .. code-block:: bash

            $ salt '*' lxd.profile_get autostart
    '''
    client = pylxd_client_get(remote_addr, cert, key, verify_cert)

    profile = None
    try:
        profile = client.profiles.get(name)
    except pylxd.exceptions.LXDAPIException:
        raise SaltInvocationError(
            'Profile \'{0}\' not found'.format(name)
        )

    if _raw:
        return profile

    return profile.dict()


def profile_delete(name, remote_addr=None,
                   cert=None, key=None, verify_cert=True):
    ''' Deletes a profile.

        name :
            The name of the profile to delete.

        remote_addr, cert, key, verify_cert:
            See pylxd_client_get

        CLI Example:

        .. code-block:: bash

            $ salt '*' lxd.profile_delete shared_mounts
    '''
    profile = profile_get(
        name,
        remote_addr,
        cert,
        key,
        verify_cert,
        _raw=True
    )

    profile.delete()
    return True


def profile_config_get(name, config_key, remote_addr=None,
                       cert=None, key=None, verify_cert=True):
    ''' Get a profile config item.

        name :
            The name of the profile to get the config item from.

        config_key :
            The key for the item to retrieve.

        remote_addr, cert, key, verify_cert:
            See pylxd_client_get

        CLI Example:

        .. code-block:: bash

            $ salt '*' lxd.profile_config_get autostart boot.autostart
    '''
    profile = profile_get(
        name,
        remote_addr,
        cert,
        key,
        verify_cert,
        _raw=True
    )

    return _get_property_dict_item(profile, 'config', config_key)


def profile_config_set(name, config_key, config_value,
                       remote_addr=None,
                       cert=None, key=None, verify_cert=True):
    ''' Set a profile config item.

        name :
            The name of the profile to set the config item to.

        config_key :
            The items key.

        config_value :
            Its items value.

        remote_addr, cert, key, verify_cert:
            See pylxd_client_get

        CLI Example:

        .. code-block:: bash

            $ salt '*' lxd.profile_config_set autostart boot.autostart 0
    '''
    profile = profile_get(
        name,
        remote_addr,
        cert,
        key,
        verify_cert,
        _raw=True
    )

    return _set_property_dict_item(
        profile, 'config', config_key, config_value
    )


def profile_config_delete(name, config_key, remote_addr=None,
                          cert=None, key=None, verify_cert=True):
    ''' Delete a profile config item.

        name :
            The name of the profile to delete the config item.

        config_key :
            The config key for the value to retrieve.

        remote_addr, cert, key, verify_cert:
            See pylxd_client_get

        CLI Example:

        .. code-block:: bash

            $ salt '*' lxd.profile_config_delete autostart boot.autostart.delay
    '''
    profile = profile_get(
        name,
        remote_addr,
        cert,
        key,
        verify_cert,
        _raw=True
    )

    return _delete_property_dict_item(
        profile, 'config', config_key
    )


def profile_device_get(name, device_name, remote_addr=None,
                       cert=None, key=None, verify_cert=True):
    ''' Get a profile device.

        name :
            The name of the profile to get the device from.

        device_name :
            The name of the device to retrieve.

        remote_addr, cert, key, verify_cert:
            See pylxd_client_get

        CLI Example:

        .. code-block:: bash

            $ salt '*' lxd.profile_device_get default eth0
    '''
    profile = profile_get(
        name,
        remote_addr,
        cert,
        key,
        verify_cert,
        _raw=True
    )

    return _get_property_dict_item(profile, 'devices', device_name)


def profile_device_set(name, device_name, device_type='disk',
                       remote_addr=None,
                       cert=None, key=None, verify_cert=True,
                       **kwargs):
    ''' Set a profile device.

        name :
            The name of the profile to set the device to.

        device_name :
            The name of the device to set.

        remote_addr, cert, key, verify_cert:
            See pylxd_client_get

        CLI Example:

        .. code-block:: bash

            $ salt '*' lxd.profile_device_set autostart eth1 nic nictype=bridged parent=lxdbr0

        # noqa
    '''
    profile = profile_get(
        name,
        remote_addr,
        cert,
        key,
        verify_cert,
        _raw=True
    )

    kwargs['type'] = device_type

    for k, v in six.iteritems(kwargs):
        kwargs[k] = six.text_type(v)

    return _set_property_dict_item(
        profile, 'devices', device_name, kwargs
    )


def profile_device_delete(name, device_name, remote_addr=None,
                          cert=None, key=None, verify_cert=True):
    ''' Delete a profile device.

        name :
            The name of the profile to delete the device.

        device_name :
            The name of the device to delete.

        remote_addr, cert, key, verify_cert:
            See pylxd_client_get

        CLI Example:

        .. code-block:: bash

            $ salt '*' lxd.profile_device_delete autostart eth1

        # noqa

    '''
    profile = profile_get(
        name,
        remote_addr,
        cert,
        key,
        verify_cert,
        _raw=True
    )

    return _delete_property_dict_item(
        profile, 'devices', device_name
    )


##################
# Image Management
##################
def image_list(list_aliases=False, remote_addr=None,
               cert=None, key=None, verify_cert=True):
    ''' Lists all images from the LXD.

        list_aliases :

            Return a dict with the fingerprint as key and
            a list of aliases as value instead.

        remote_addr, cert, key, verify_cert:
            See pylxd_client_get

        CLI Examples:

        .. code-block:: bash

            salt '*' lxd.image_list true --out=json
            salt '*' lxd.image_list --out=json
    '''
    client = pylxd_client_get(remote_addr, cert, key, verify_cert)

    images = client.images.all()
    if list_aliases:
        return {i.fingerprint: [a['name'] for a in i.aliases] for i in images}

    return [i.dict() for i in images]


'''
# This needs pcdummy's version of pylxd.
def image_copy(source, wait=True, remote_addr=None,
               cert=None, key=None, verify_cert=True, **kwargs):
    ''

        CLI Examples:

        .. code-block:: bash

            salt-call lxd.image_copy "{type: 'image', mode: 'pull', server: 'https://srv01:8443', fingerprint: 'f452cda3bccb2903e56d53e402b9d35334b4276783d098a879be5d74b04e62e2', certificate: '-----BEGIN CERTIFICATE-----MIIGED-----END CERTIFICATE-----'}" true auto_update=true filename=ubuntu-16.04-server-cloudimg-amd64-lxd.tar.xz

        You need to provide a certificate for private images.
        See: https://github.com/lxc/lxd/blob/3207c2c67d02b3c7504c118f9af6262747103d65/doc/rest-api.md#post-6

    # noqa
    ''
    if not isinstance(source, dict):
        raise SaltInvocationError('Argument source must be a dict')

    if 'fingerprint' not in source:
        raise SaltInvocationError(
            'pylxd requires a fingerprint for the source'
        )

    client = pylxd_client_get(remote_addr, cert, key, verify_cert)

    try:
        image = client.images.copy(source, wait, **kwargs)
    except pylxd.exceptions.LXDAPIException as e:
        raise CommandExecutionError(
            'Failed to copy the image, error was: {0}'.format(str(e))
        )

    if not wait:
        return image.json()['operation']

    return image.dict()
'''


################
# Helper Methods
################
def normalize_input_values(config, devices):
    # This is special for pcdummy and his ext_pillar mongo usage.
    #
    # It translates:
    #    [{key: key1, value: value1}, {key: key2, value: value2}]
    # to:
    #    {key1: value1, key2: value2}
    #
    # MongoDB doesn't like dots in field names.
    if isinstance(config, list):
        if (len(config) > 0 and
                'key' in config[0] and
                'value' in config[0]):
            config = {d['key']: d['value'] for d in config}
        else:
            config = {}

    if isinstance(config, six.string_types):
        raise SaltInvocationError(
            "config can't be a string, validate your YAML input."
        )

    if isinstance(devices, six.string_types):
        raise SaltInvocationError(
            "devices can't be a string, validate your YAML input."
        )

    # Golangs wants strings
    if config is not None:
        for k, v in six.iteritems(config):
            config[k] = six.text_type(v)
    if devices is not None:
        for dn in devices:
            for k, v in six.iteritems(devices[dn]):
                devices[dn][k] = v

    return (config, devices,)


def sync_config_devices(obj, newconfig, newdevices, test=False):
    ''' Syncs the given config and devices with the object
        (a profile or a container)
        returns a changes dict with all changes made.

        obj :
            The object to sync with / or just test with.

        newconfig:
            The new config to check with the obj.

        newdevices:
            The new devices to check with the obj.

        test:
            Wherever to not change anything and give "Would change" message.
    '''
    changes = {}

    #
    # config changes
    #
    if newconfig is None:
        newconfig = {}

    if True:
        newconfig = dict(zip(
            map(six.text_type, newconfig.keys()),
            map(six.text_type, newconfig.values())
        ))
        cck = set(newconfig.keys())

        obj.config = dict(zip(
            map(six.text_type, obj.config.keys()),
            map(six.text_type, obj.config.values())
        ))
        ock = set(obj.config.keys())

        config_changes = {}
        # Removed keys
        for k in ock.difference(cck):
            # Ignore LXD internals.
            if k.startswith('volatile.'):
                continue

            if not test:
                config_changes[k] = (
                    'Removed config key "{0}", its value was "{1}"'
                ).format(k, obj.config[k])
                del obj.config[k]
            else:
                config_changes[k] = (
                    'Would remove config key "{0} with value "{1}"'
                ).format(k, obj.config[k])

        # same keys
        for k in cck.intersection(ock):
            # Ignore LXD internals.
            if k.startswith('volatile.'):
                continue

            if newconfig[k] != obj.config[k]:
                if not test:
                    config_changes[k] = (
                        'Changed config key "{0}" to "{1}", '
                        'its value was "{2}"'
                    ).format(k, newconfig[k], obj.config[k])
                    obj.config[k] = newconfig[k]
                else:
                    config_changes[k] = (
                        'Would change config key "{0}" to "{1}", '
                        'its current value is "{2}"'
                    ).format(k, newconfig[k], obj.config[k])

        # New keys
        for k in cck.difference(ock):
            # Ignore LXD internals.
            if k.startswith('volatile.'):
                continue

            if not test:
                config_changes[k] = (
                    'Added config key "{0}" = "{1}"'
                ).format(k, newconfig[k])
                obj.config[k] = newconfig[k]
            else:
                config_changes[k] = (
                    'Would add config key "{0}" = "{1}"'
                ).format(k, newconfig[k])

        if config_changes:
            changes['config'] = config_changes

    else:
        if obj.config != {}:
            if not test:
                changes['config_removed'] = 'Removed the config'
            else:
                changes['config_removed'] = 'Would remove the config'

    #
    # devices changes
    #
    if newdevices is None:
        newdevices = {}

    if True:
        dk = set(obj.devices.keys())
        dk.difference(newdevices.keys())

        devices_changes = {}
        for k in dk:
            # Ignore LXD internals.
            if k == u'root':
                continue

            if not test:
                devices_changes[k] = (
                    'Removed device "{0}"'
                ).format(k)
                del obj.devices[k]
            else:
                devices_changes[k] = (
                    'Would remove device "{0}"'
                ).format(k)

        for k, v in six.iteritems(obj.devices):
            # Ignore LXD internals also for new devices.
            if k == u'root':
                continue

            if newdevices[k] != v:
                if not test:
                    devices_changes[k] = (
                        'Changed device "{0}"'
                    ).format(k)
                    obj.devices[k] = v
                else:
                    devices_changes[k] = (
                        'Would change device "{0}"'
                    ).format(k)

        if devices_changes:
            changes['devices'] = devices_changes

    else:
        if obj.devices != {}:
            if not test:
                changes['devices_removed'] = 'Removed the devices'
            else:
                changes['devices_removed'] = 'Would remove the devices'

    return changes


def _set_property_dict_item(obj, prop, key, value):
    ''' Sets the dict item key of the attr from obj.

        Basicaly it does getattr(obj, prop)[key] = value.


        For the disk device we added some checks to make
        device changes on the CLI saver.
    '''
    attr = getattr(obj, prop)
    if prop == 'devices':
        device_type = value['type']
        if device_type == 'disk' and 'source' not in value:
            raise SaltInvocationError(
                "source must be given as parameter"
            )

        if device_type == 'disk' and 'path' not in value:
            raise SaltInvocationError(
                "path must be given as parameter"
            )

        for k in value.keys():
            if k.startswith('__'):
                del value[k]

        attr[key] = value

    else:  # config
        attr[key] = str(value)

    pylxd_save_object(obj)

    return obj.dict()


def _get_property_dict_item(obj, prop, key):
    attr = getattr(obj, prop)
    if key not in attr:
        raise SaltInvocationError(
            "'{0}' doesn't exists".format(key)
        )

    return attr[key]


def _delete_property_dict_item(obj, prop, key):
    attr = getattr(obj, prop)
    if key not in attr:
        raise SaltInvocationError(
            "'{0}' doesn't exists".format(key)
        )

    del attr[key]
    pylxd_save_object(obj)

    return True
