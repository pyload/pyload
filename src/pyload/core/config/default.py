# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from builtins import range
from copy import deepcopy

from future import standard_library

from pyload.config.types import InputType

standard_library.install_aliases()


def _gen_session_defaults():
    profile_section = (
        ('path', ('option', None, 'Path', None, None, InputType.Folder)),
        ('pid', ('option', None, 'PID', None, None, InputType.Int)),
        ('ctime', ('option', None, 'CTime', None, None, InputType.Float)),
    )
    cache_section = (
        ('path', ('option', None, 'Path', None, None, InputType.Folder)),
    )
    log_section = (
        ('path', ('option', None, 'Path', None, None, InputType.Folder)),
        ('name', ('option', None, 'Name', None, None, InputType.Str)),
    )

    current_config = (
        ('id', ('option', None, 'ID', None, None, InputType.Float)),
        ('profile', ('section', profile_section, 'Profile', None)),
        ('cache', ('section', cache_section, 'Cache', None)),
        ('log', ('section', log_section, 'Logging', None)),
    )
    previous_config = deepcopy(current_config)

    defaults = (
        ('current', ('section', current_config, 'Current', None)),
        ('previous', ('section', previous_config, 'Previous', None)),
    )
    return defaults


session_defaults = _gen_session_defaults()


# TODO: write descriptions
def _gen_config_defaults():
    general_config = (
        ('language', ('option', None, 'Language',
                      None, (None, 'english'), InputType.Str)),
        ('storage_folder', ('option', None, 'Storage folder',
                            None, None, InputType.Folder)),
        ('min_storage_size', ('option', 1024, 'Min storage space (in MiB)',
                              None, None, InputType.Size)),
        ('folder_pack', ('option', True, 'Create folder for each package',
                         None, None, InputType.Bool)),
        ('local_access', ('option', True, 'No authentication on local access',
                          None, None, InputType.Bool)),
        ('niceness', ('option', 0, 'Process priority',
                      None, range(-19, 20), InputType.Int)),
        ('ioniceness', ('option', 0, 'Process I/O priority',
                        None, range(0, 3), InputType.Int))
    )
    log_config = (
        ('activated', ('option', True, 'Activated',
                       None, None, InputType.Bool)),
        ('syslog', ('option', None, 'Sent log to syslog',
                    None, (None, 'remote', 'local'), InputType.Str)),
        ('syslog_folder', ('option', None, 'Syslog local folder',
                           None, None, InputType.Folder)),
        ('syslog_host', ('option', 'localhost:514', 'Syslog remote IP address',
                         None, None, InputType.Address)),
        ('logfile', ('option', False, 'Save log to file',
                     None, None, InputType.Bool)),
        ('logfile_size', ('option', 100, 'Max file size (in KiB)',
                          None, None, InputType.Size)),
        ('logfile_folder', ('option', None, 'File folder',
                            None, None, InputType.Folder)),
        ('logfile_name', ('option', None, 'File name',
                          None, None, InputType.File)),
        ('max_logfiles', ('option', 5, 'Max log files',
                          None, None, InputType.Int)),
        ('rotate', ('option', True, 'Log rotate',
                    None, None, InputType.Bool)),
        ('debug', ('option', False, 'Debug mode',
                   None, None, InputType.Bool)),
        ('verbose', ('option', False, 'Verbose mode',
                     None, None, InputType.Bool)),
        ('color_console', ('option', True, 'Color console',
                           None, None, InputType.Bool))
    )
    perm_config = (
        ('user', ('option', 'user', 'Username', None, None, InputType.Str)),
        ('group', ('option', 'users', 'Groupname', None, None, InputType.Str)),
        ('foldermode', ('option', 0o755, 'Folder mode',
                        None, None, InputType.Octal)),
        ('filemode', ('option', 0o644, 'File mode',
                      None, None, InputType.Octal)),
        ('change_user', ('option', False, 'Change user of pyLoad process',
                         None, None, InputType.Bool)),
        ('change_group', ('option', False, 'Change group of pyLoad process',
                          None, None, InputType.Bool)),
        ('change_fileowner', ('option', False,
                              'Change user and group of saved files',
                              None, None, InputType.Bool)),
        ('change_filemode', ('option', False,
                             'Change file mode of saved files',
                             None, None, InputType.Bool))
    )
    conn_config = (
        ('max_transfers', ('option', 5, 'Max parallel transfers',
                           None, None, InputType.Int)),
        ('max_speed', ('option', -1, 'Max transfer speed (in KiB/s)',
                       None, None, InputType.Size)),
        ('max_chunks', ('option', -1, 'Max connections for single transfer',
                        None, None, InputType.Int)),
        # TODO: Recheck...
        ('wait', ('option', 2, 'Active transfers while waiting',
                  None, None, InputType.Int)),
        ('skip', ('option', False, 'Skip existing files',
                  None, None, InputType.Bool)),
        ('preallocate', ('option', True, 'Pre-allocate files on disk',
                         None, None, InputType.Bool)),
        ('interface', ('option', None, 'Interface address to bind',
                       None, None, InputType.Address)),
        ('ipv6', ('option', False, 'Allow IPv6', None, None, InputType.Bool)),
    )
    ssl_config = (
        ('activated', ('option', False, 'Activated',
                       None, None, InputType.Bool)),
        ('cert', ('option', 'ssl.crt', 'Cert file',
                  None, None, InputType.File)),
        ('key', ('option', 'ssl.key', 'Key file', None, None, InputType.File))
    )
    reconn_config = (
        ('activated', ('option', False, 'Activated',
                       None, None, InputType.Bool)),
        ('script', ('option', None, 'Script file',
                    None, None, InputType.File)),
        ('wait', ('option', False, 'Don\'t reconnect while waiting',
                  None, None, InputType.Bool))
    )
    proxy_config = (
        ('activated', ('option', False, 'Activated',
                       None, None, InputType.Bool)),
        ('type', ('option', 'http', 'Protocol', None,
                  ('http', 'socks4', 'socks5'), InputType.Str)),
        ('host', ('option', 'localhost:7070',
                  'IP address', None, None, InputType.Address)),
        ('username', ('option', None, 'Username', None, None, InputType.Str)),
        ('password', ('option', None, 'Password',
                      None, None, InputType.Password))
    )
    up_config = (
        ('activated', ('option', False, 'Activated',
                       None, None, InputType.Bool)),
        ('nodebug', ('option', False, 'Don\'t update in debug mode',
                     None, None, InputType.Bool)),
        ('periodical', ('option', True, 'Check for updates on schedule',
                        None, None, InputType.Bool)),
        ('interval', ('option', 1, 'Check interval (in days)',
                      None, None, InputType.Int))
    )

    defaults = (
        ('general', ('section', general_config, 'General', None)),
        ('log', ('section', log_config, 'Logging', None)),
        ('permission', ('section', perm_config, 'Permissions', None)),
        ('connection', ('section', conn_config, 'Connections', None)),
        ('ssl', ('section', ssl_config, 'SSL', None)),
        ('reconnect', ('section', reconn_config, 'Reconnection', None)),
        ('proxy', ('section', proxy_config, 'Proxy', None)),
        ('update', ('section', up_config, 'Updates', None))
    )
    return defaults


config_defaults = _gen_config_defaults()
