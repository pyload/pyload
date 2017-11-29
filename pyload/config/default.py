# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from collections import OrderedDict

from future import standard_library
from future.builtins import range

from pyload.config.types import InputType

standard_library.install_aliases()


# def _gen_session_defaults():
# profile_section = (
# ('path',
# (False, None, 'Path', None, None, InputType.Folder)),
# ('pid',
# (False, None, 'PID', None, None, InputType.Int)),
# ('ctime',
# (False, None, 'CTime', None, None, InputType.Float)),
# )
# cache_section = (
# ('path',
# (False, None, 'Path', None, None, InputType.Folder)),
# )
# log_section = (
# ('path',
# (False, None, 'Path', None, None, InputType.Folder)),
# ('name',
# (False, None, 'Name', None, None, InputType.Str)),
# )

# current_config = (
# ('id',
# (False, None, 'ID', None, None, InputType.Float)),
# ('profile',
# (True, profile_section, 'Profile', None)),
# ('cache',
# (True, cache_section, 'Cache', None)),
# ('log',
# (True, log_section, 'Logging', None)),
# )
# previous_config = deepcopy(current_config)

# defaults = (
# ('current', (True, current_config, 'Current', None)),
# ('previous', (True, previous_config, 'Previous', None)),
# )
# return defaults


# session_defaults = _gen_session_defaults()


# TODO: write descriptions
def _gen_config():
    general_config = (
        ('language',
            (None, 'Language', None, (None, 'english'), InputType.Str)),
        ('storage_folder',
            ('.', 'Storage folder', None, None, InputType.Folder)),
        ('min_storage_size',
            ('1024 MiB', 'Min storage space in bytes or use a unit', None, None, InputType.Size)),
        ('folder_pack',
            ('True', 'Create folder for each package', None, None, InputType.Bool)),
        ('local_access',
            ('True', 'No authentication on local access', None, None, InputType.Bool)),
        ('niceness',
            ('0', 'Process priority', None, range(-19, 20), InputType.Int)),
        ('ioniceness',
            ('0', 'Process I/O priority', None, range(0, 3), InputType.Int))
    )
    log_config = (
        ('console',
            ('True', 'Print log to console', None, None, InputType.Bool)),
        ('syslog',
            (None, 'Sent log to syslog', None, (None, 'remote', 'local'), InputType.Str)),
        ('syslog_folder',
            (None, 'Syslog local folder', None, None, InputType.Folder)),
        ('syslog_host',
            ('localhost:514', 'Syslog remote IP address', None, None, InputType.Address)),
        ('filelog',
            ('False', 'Save log to file', None, None, InputType.Bool)),
        ('filelog_size',
            ('100 KiB', 'Max file size in bytes or use unit', None, None, InputType.Size)),
        ('filelog_folder',
            ('logs', 'File folder', None, None, InputType.Folder)),
        ('filelog_name',
            ('pyload.log', 'File name', None, None, InputType.File)),
        ('max_logfiles',
            ('5', 'Max log files', None, None, InputType.Int)),
        ('rotate',
            ('True', 'Log rotate', None, None, InputType.Bool)),
        ('debug',
            ('False', 'Debug mode', None, None, InputType.Bool)),
        # ('verbose',
        # (False, 'Verbose mode', None, None, InputType.Bool)),
        ('colorlog',
            ('True', 'Color log (console only)', None, None, InputType.Bool))
    )
    perm_config = (
        ('user',
            ('user', 'Username', None, None, InputType.Str)),
        ('group',
            ('users', 'Groupname', None, None, InputType.Str)),
        ('foldermode',
            ('755', 'Folder mode', None, None, InputType.Octal)),
        ('filemode',
            ('644', 'File mode', None, None, InputType.Octal)),
        ('change_user',
            ('False', 'Change user of pyLoad process', None, None, InputType.Bool)),
        ('change_group',
            ('False', 'Change group of pyLoad process', None, None, InputType.Bool)),
        ('change_fileowner',
            ('False', 'Change user and group of saved files', None, None, InputType.Bool)),
        ('change_filemode',
            ('False', 'Change file mode of saved files', None, None, InputType.Bool))
    )
    conn_config = (
        ('max_transfers',
            ('5', 'Max parallel transfers', None, None, InputType.Int)),
        ('max_speed',
            ('-1', 'Max transfer speed (in KiB/s)', None, None, InputType.Size)),
        ('max_chunks',
            ('-1', 'Max connections for single transfer', None, None, InputType.Int)),
        # TODO: Recheck...
        ('wait',
            ('2', 'Active transfers while waiting', None, None, InputType.Int)),
        ('skip',
            ('False', 'Skip existing files', None, None, InputType.Bool)),
        ('preallocate',
            ('True', 'Pre-allocate files on disk', None, None, InputType.Bool)),
        ('interface',
            (None, 'Interface address to bind', None, None, InputType.Address)),
        ('ipv6',
            ('False', 'Allow IPv6', None, None, InputType.Bool)),
    )
    ssl_config = (
        ('activated',
            ('False', 'Activated', None, None, InputType.Bool)),
        ('cert',
            ('ssl.crt', 'Cert file', None, None, InputType.File)),
        ('key',
            ('ssl.key', 'Key file', None, None, InputType.File))
    )
    reconn_config = (
        ('activated',
            ('False', 'Activated', None, None, InputType.Bool)),
        ('script',
            (None, 'Script file', None, None, InputType.File)),
        ('wait',
            ('False', 'Don\'t reconnect while waiting', None, None, InputType.Bool))
    )
    proxy_config = (
        ('activated',
            ('False', 'Activated', None, None, InputType.Bool)),
        ('type',
            ('http', 'Protocol', None, ('http', 'socks4', 'socks5'), InputType.Str)),
        ('host',
            ('localhost:7070', 'IP address', None, None, InputType.Address)),
        ('username',
            (None, 'Username', None, None, InputType.Str)),
        ('password',
            (None, 'Password', None, None, InputType.Password))
    )
    up_config = (
        ('activated',
            ('False', 'Activated', None, None, InputType.Bool)),
        ('nodebug',
            ('False', 'Don\'t update in debug mode', None, None, InputType.Bool)),
        ('periodical',
            ('True', 'Check for updates on schedule', None, None, InputType.Bool)),
        ('interval',
            ('1', 'Check interval (in days)', None, None, InputType.Int))
    )

    root_config = (
        ('general',
            (general_config, 'General', None)),
        ('log',
            (log_config, 'Logging', None)),
        ('permission',
            (perm_config, 'Permissions', None)),
        ('connection',
            (conn_config, 'Connections', None)),
        ('ssl',
            (ssl_config, 'SSL', None)),
        ('reconnect',
            (reconn_config, 'Reconnection', None)),
        ('proxy',
            (proxy_config, 'Proxy', None)),
        ('update',
            (up_config, 'Updates', None))
    )
    return root_config


config = _gen_config()
