# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from future import standard_library

from .check import OnlineCheck
from .file import FileInfo
from .init import *
from .package import PackageInfo, PackageStats
from .task import InteractionTask
from .user import UserData

standard_library.install_aliases()


enums = [
    "DownloadState",
    "DownloadStatus",
    "FileStatus",
    "InputType",
    "Interaction",
    "MediaType",
    "PackageStatus",
    "Permission",
    "ProgressType",
    "Role"
]

classes = {
    'AccountInfo':
        [int, str, str, int, bool, int, int, int, bool, bool, bool,
         (list, ConfigItem)],
    'AddonInfo': [str, str, str],
    'AddonService': [str, str, str, (list, str), bool, int],
    'ConfigHolder':
        [str, str, str, str, (list, ConfigItem), (None, (list, AddonInfo))],
    'ConfigInfo': [str, str, str, str, bool, (None, bool)],
    'ConfigItem': [str, str, str, Input, str],
    'DownloadInfo': [str, str, str, int, str, str],
    'DownloadProgress': [int, int, int, int, int],
    'EventInfo': [str, (list, str)],
    'FileDoesNotExist': [int],
    'FileInfo':
        [int, str, int, int, int, int, int, int, int, (None, DownloadInfo)],
    'Input': [int, (None, str), (None, str)],
    'InteractionTask': [int, int, Input, str, str, str],
    'InvalidConfigSection': [str],
    'LinkStatus': [str, str, int, int, (None, str), (None, str)],
    'OnlineCheck': [int, (dict, str, LinkStatus)],
    'PackageDoesNotExist': [int],
    'PackageInfo':
        [int, str, str, int, int, str, str, str, int, (list, str), int, bool,
         int, PackageStats, (list, int), (list, int)],
    'PackageStats': [int, int, int, int],
    'ProgressInfo':
        [str, str, str, int, int, int, int, int, (None, DownloadProgress)],
    'ServiceDoesNotExist': [str, str],
    'ServiceException': [str],
    'StatusInfo': [int, int, int, int, int, bool, bool, bool, bool, int],
    'TreeCollection':
        [PackageInfo, (dict, int, FileInfo), (dict, int, PackageInfo)],
    'UserData': [int, str, str, int, int, str, int, int, str, int, int, str],
    'UserDoesNotExist': [str]
}

methods = {
    'add_links': None,
    'add_local_file': None,
    'add_package': int,
    'add_package_child': int,
    'add_packagep': int,
    'add_user': UserData,
    'check_container': OnlineCheck,
    'check_html': OnlineCheck,
    'check_links': OnlineCheck,
    'create_account': AccountInfo,
    'create_package': int,
    'delete_config': None,
    'delete_files': bool,
    'delete_packages': bool,
    'find_files': TreeCollection,
    'find_packages': TreeCollection,
    'free_space': int,
    'generate_download_link': str,
    'generate_packages': (dict, str, list),
    'get_account_info': AccountInfo,
    'get_account_types': (list, str),
    'get_accounts': (list, AccountInfo),
    'get_addon_handler': (dict, str, list),
    'get_all_files': TreeCollection,
    'get_all_info': (dict, str, list),
    'get_all_user_data': (dict, int, UserData),
    # 'get_available_plugins': (list, ConfigInfo),
    # 'get_config': (dict, str, ConfigHolder),
    'get_config_value': str,
    # 'get_core_config': (list, ConfigInfo),
    'get_file_info': FileInfo,
    'get_file_tree': TreeCollection,
    'get_filtered_file_tree': TreeCollection,
    'get_filtered_files': TreeCollection,
    'get_info_by_plugin': (list, AddonInfo),
    'get_interaction_tasks': (list, InteractionTask),
    'get_log': (list, str),
    'get_package_content': TreeCollection,
    'get_package_info': PackageInfo,
    # 'get_plugin_config': (list, ConfigInfo),
    'get_progress_info': (list, ProgressInfo),
    'get_quota': int,
    'get_server_version': str,
    'get_status_info': StatusInfo,
    'get_user_data': UserData,
    'get_ws_address': str,
    'invoke_addon': str,
    'invoke_addon_handler': str,
    'is_interaction_waiting': bool,
    'load_config': ConfigHolder,
    'login': bool,
    'move_files': bool,
    'move_package': bool,
    'order_files': None,
    'order_package': None,
    'parse_links': (dict, str, list),
    'pause_server': None,
    'poll_results': OnlineCheck,
    'quit': None,
    'recheck_package': None,
    'remove_account': None,
    'remove_files': None,
    'remove_packages': None,
    'remove_user': None,
    'restart': None,
    'restart_failed': None,
    'restart_file': None,
    'restart_package': None,
    'save_config': None,
    'search_suggestions': (list, str),
    'set_config_value': None,
    'set_interaction_result': None,
    'set_package_paused': int,
    'set_password': bool,
    'stop_all_downloads': None,
    'stop_downloads': None,
    'toggle_pause': bool,
    'toggle_reconnect': bool,
    'unpause_server': None,
    'update_account': AccountInfo,
    'update_account_info': None,
    'update_package': PackageInfo,
    'update_user_data': None,
    'upload_container': int
}
