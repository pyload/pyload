# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from future import standard_library
standard_library.install_aliases()


__all__ = ['make_config']


# TODO: write tooltips and descriptions
# TODO: use apis config related classes
def make_config(config):
    """
    Configuration layout for default base config.
    """
    desc = _('Description')
    expl = _('Long description')

    config.add_config_section('general', _('General'), desc, expl,
    [
        ('language', 'en|de|fr|it|es|nl|sv|ru|pl|cs|sr|pt', _('Language'), 'en'),
        ('storage_folder', 'folder', _('Storage folder'), ''),
        ('min_storage_size', 'int', _('Min storage space (in MiB)'), '1024'),
        ('folder_pack', 'bool', _('Create folder for each package'), 'True'),
        ('local_access', 'bool', _('No authentication on local access'), 'True'),
        ('niceness', 'int', _('Process priority'), '0'),
        ('ioniceness', '0|1|2|3', _('Process I/O priority'), '0')
    ])

    config.add_config_section('log', _('Logging'), desc, expl,
    [
        ('activated', 'bool', _('Activated'), 'True'),
        ('syslog', 'no|remote|local', _('Sent log to syslog'), 'no'),
        ('syslog_folder', 'folder', _('Syslog local folder'), ''),
        ('syslog_host', 'str', _('Syslog remote IP address'), 'localhost'),
        ('syslog_port', 'port', _('Syslog remote port'), ''),
        ('logfile', 'bool', _('Save log to file'), 'True'),
        ('logfile_size', 'int', _('Max file size (in KiB)'), '100'),
        ('logfile_folder', 'folder', _('File folder'), ''),
        ('max_logfiles', 'int', _('Max log files'), '5'),
        ('rotate', 'bool', _('Log rotate'), 'True'),
        ('debug', 'bool', _('Debug mode'), 'False'),
        ('verbose', 'bool', _('Verbose mode'), 'False'),
        ('color_console', 'bool', _('Color console'), 'True')
    ])

    config.add_config_section('permission', _('Permissions'), desc, expl,
    [
        ('user', 'str', _('Username'), 'user'),
        ('group', 'str', _('Groupname'), 'users'),
        ('foldermode', 'str', _('Folder mode'), '0o755'),
        ('filemode', 'str', _('File mode'), '0o644'),
        ('change_user', 'bool', _('Change user of pyLoad process'), 'False'),
        ('change_group', 'bool', _('Change group of pyLoad process'), 'False'),
        ('change_fileowner', 'bool', _(
            'Change user and group of saved files'), 'False'),
        ('change_filemode', 'bool', _('Change file mode of saved files'), 'False')
    ])

    config.add_config_section('connection', _('Connections'), desc, expl,
    [
        ('max_transfers', 'int', _('Max parallel transfers'), '5'),
        ('max_speed', 'int', _('Max transfer speed (in KiB/s)'), '-1'),
        ('max_chunks', 'int', _('Max connections for single transfer'), '-1'),
        ('wait', 'int', _('Active transfers while waiting'), '2'),  # TODO: Recheck
        ('skip', 'bool', _('Skip existing files'), 'False'),
        ('preallocate', 'bool', _('Pre-allocate files on disk'), 'True'),
        ('interface', 'str', _('Interface address to bind'), ''),
        ('ipv6', 'bool', _('Allow IPv6'), 'False')
    ])

    config.add_config_section('ssl', _('SSL'), desc, expl,
    [
        ('activated', 'bool', _('Activated'), 'False'),
        ('cert', 'file', _('Cert file'), 'ssl.crt'),
        ('key', 'file', _('Key file'), 'ssl.key')
    ])

    config.add_config_section('reconnect', _('Reconnection'), desc, expl,
    [
        ('activated', 'bool', _('Activated'), 'False'),
        ('script', 'str', _('Script file'), ''),
        ('wait', 'str', _('Don\'t reconnect while waiting'), 'False')
    ])

    config.add_config_section('proxy', _('Proxy'), desc, expl,
    [
        ('activated', 'bool', _('Activated'), 'False'),
        ('type', 'http|socks4|socks5', _('Protocol'), 'http'),
        ('host', 'str', _('IP address'), 'localhost'),
        ('port', 'port', _('Port'), '7070'),
        ('username', 'str', _('Username'), ''),
        ('password', 'str', _('Password'), '')
    ])

    config.add_config_section('webui', _('Web User Interface'), desc, expl,
    [
        ('activated', 'bool', _('Activated'), 'True'),
        ('server', 'auto|threaded|fallback|fastcgi', _('Webserver'), 'auto'),
        ('host', 'str', _('IP address'), 'localhost'),
        ('port', 'port', _('Port'), '8010'),
        ('force_server', 'str', _('Forced webserver'), ''),
        ('external', 'bool', _('Served external'), 'False'),
        ('prefix', 'str', _('Path prefix'), ''),
        # ('debug', 'bool', _('Debug mode'), 'False')
    ])

    config.add_config_section('rpc', _('REST API Interface'), desc, expl,
    [
        ('activated', 'bool', _('Activated'), 'False'),
        ('host', 'str', _('IP address'), '0.0.0.0'),
        ('port', 'port', _('Port'), '7227')
    ])

    config.add_config_section('update', _('Updates'), desc, expl,
    [
        ('activated', 'bool', _('Activated'), 'True'),
        ('nodebug', 'bool', _('Don\'t update in debug mode'), 'False'),
        ('periodical', 'bool', _('Check for updates on schedule'), 'True'),
        ('interval', 'int', _('Check interval (in days)'), '1')
    ])
