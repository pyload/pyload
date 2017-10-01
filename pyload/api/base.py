# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from builtins import object
from types import MethodType

from future import standard_library

from pyload.core.datatype.base import DownloadState, DownloadStatus, Permission
from pyload.core.datatype.user import User
from pyload.utils.convert import to_str

standard_library.install_aliases()


# Workaround to let code-completion think, this is subclass of AbstractApi
AbstractApi = object


class BaseApi(AbstractApi):

    def __init__(self, core, user):
        # Only for auto completion, this class can not be instantiated
        from pyload.core import Core
        from pyload.core.datatype.user import User
        assert isinstance(core, Core)
        assert issubclass(BaseApi, AbstractApi)
        self.pyload = core
        self._ = core._
        assert isinstance(user, User)
        self.user = user
        # No instantiating!
        raise Exception


class AbstractApi(object):

    def add_links(self, pid, links):
        pass

    def add_local_file(self, pid, name, path):
        pass

    def add_package(self, name, links, password):
        pass

    def add_package_child(self, name, links, password, root, paused):
        pass

    def addPackageP(self, name, links, password, paused):
        pass

    def add_user(self, username, password):
        pass

    def check_container(self, filename, data):
        pass

    def check_html(self, html, url):
        pass

    def check_links(self, links):
        pass

    def create_account(self, plugin, loginname, password):
        pass

    def create_package(self, name, folder, root,
                       password, site, comment, paused):
        pass

    # def delete_config(self, plugin):
        # pass

    def delete_files(self, fids):
        pass

    def delete_packages(self, pids):
        pass

    def find_files(self, pattern):
        pass

    def find_packages(self, tags):
        pass

    def avail_space(self):
        pass

    def generate_download_link(self, fid, timeout):
        pass

    def generate_packages(self, links):
        pass

    def get_account_info(self, aid, plugin, refresh):
        pass

    def get_account_types(self):
        pass

    def get_accounts(self):
        pass

    def get_addon_handler(self):
        pass

    def get_all_files(self):
        pass

    def get_all_info(self):
        pass

    def get_all_user_data(self):
        pass

    # def get_available_plugins(self):
        # pass

    # def get_config(self):
        # pass

    def get_config_value(self, section, option):
        pass

    # def get_core_config(self):
        # pass

    def get_file_info(self, fid):
        pass

    def get_file_tree(self, pid, full):
        pass

    def get_filtered_file_tree(self, pid, full, state):
        pass

    def get_filtered_files(self, state):
        pass

    def get_info_by_plugin(self, plugin):
        pass

    def get_interaction_tasks(self, mode):
        pass

    def get_log(self, offset):
        pass

    def get_package_content(self, pid):
        pass

    def get_package_info(self, pid):
        pass

    # def get_plugin_config(self):
        # pass

    def get_progress_info(self):
        pass

    def get_quota(self):
        pass

    def get_server_version(self):
        pass

    def get_status_info(self):
        pass

    def get_user_data(self):
        pass

    # def get_ws_address(self):
        # pass

    def invoke_addon(self, plugin, func, func_args):
        pass

    def invoke_addon_handler(self, plugin, func, pid_or_fid):
        pass

    def is_interaction_waiting(self, mode):
        pass

    # def load_config(self, name):
        # pass

    def login(self, username, password):
        pass

    def move_files(self, fids, pid):
        pass

    def move_package(self, pid, root):
        pass

    def order_files(self, fids, pid, position):
        pass

    def order_package(self, pids, position):
        pass

    def parse_links(self, links):
        pass

    def pause_server(self):
        pass

    def poll_results(self, rid):
        pass

    def exit(self):
        pass

    def recheck_package(self, pid):
        pass

    def remove_account(self, account):
        pass

    def remove_files(self, fids):
        pass

    def remove_packages(self, pids):
        pass

    def remove_user(self, uid):
        pass

    def restart(self):
        pass

    def restart_failed(self):
        pass

    def restart_file(self, fid):
        pass

    def restart_package(self, pid):
        pass

    # def save_config(self, config):
        # pass

    def search_suggestions(self, pattern):
        pass

    def set_config_value(self, section, option, value):
        pass

    def set_interaction_result(self, iid, result):
        pass

    def set_package_paused(self, pid, paused):
        pass

    def set_password(self, username, old_password, new_password):
        pass

    def stop_all_downloads(self):
        pass

    def stop_downloads(self, fids):
        pass

    def toggle_pause(self):
        pass

    def toggle_reconnect(self):
        pass

    def unpause_server(self):
        pass

    def update_account(self, aid, plugin, loginname, password):
        pass

    def update_account_info(self, account):
        pass

    def update_package(self, pack):
        pass

    def update_user_data(self, data):
        pass

    def upload_container(self, filename, data):
        pass


# contains function names mapped to their permissions
# unlisted functions are for admins only
perm_map = {}

# decorator only called on init, never initialized, so has no effect on runtime


def requireperm(bits):
    class _Dec(object):

        def __new__(cls, func, *args, **kwargs):
            perm_map[func.__name__] = bits
            return func
    return _Dec


statemap = {
    DownloadState.All:
        frozenset(getattr(DownloadStatus, x)
                  for x in dir(DownloadStatus) if not x.startswith('_')),
    DownloadState.Finished:
        frozenset((DownloadStatus.Finished, DownloadStatus.Skipped)),
    DownloadState.Unfinished: None,  # set below
    DownloadState.Failed:
        frozenset((DownloadStatus.Failed, DownloadStatus.TempOffline,
                   DownloadStatus.Aborted, DownloadStatus.NotPossible,
                   DownloadStatus.FileMismatch)),
    DownloadState.Unmanaged: None,
}
statemap[DownloadState.Unfinished] = frozenset(
    statemap[DownloadState.All].difference(statemap[DownloadState.Finished]))


def statestring(state):
    return ','.join(map(to_str, statemap[state]))


class Api(AbstractApi):
    """
    **pyLoads API**

    This is accessible either internal via core.api,
    websocket backend or json api.

    see Thrift specification file rpc/thriftbackend/pyload.thrift
    for information about data structures and what methods are usable with rpc.

    Most methods requires specific permissions,
    please look at the source code if you need to know.
    These can be configured via web interface.
    Admin user have all permissions, and are the only ones who can access
    the methods with no specific permission
    """
    EXTERNAL = AbstractApi  # let the json api know which methods are external
    EXTEND = False  # only extendable when set too true

    def __init__(self, core):
        self.pyload = core
        self._ = core._
        self.user_apis = {}

    @property
    def user(self):
        return  # TODO: return default user?

    # @property
    # def primary_uid(self):
        # return self.user.primary if self.user else None

    def has_access(self, obj):
        """Helper method to determine if a user has access to a resource.

        Works for obj that provides .owner attribute. Core admin has
        always access.

        """
        return self.user is None or self.user.has_access(obj)

    @classmethod
    def extend(cls, api):
        """Takes all params from api and extends cls with it. Api class can be
        removed afterwards.

        :param api: Class with methods to extend

        """
        if cls.EXTEND:
            for name, func in api.__dict__.items():
                if name.startswith('_'):
                    continue
                setattr(cls, name, MethodType(func, None, cls))
        return cls.EXTEND

    def with_user_context(self, uid):
        """Returns a proxy version of the api, to call method in user context.

        :param uid: user or userData instance or uid
        :return: :class:`UserApi`

        """
        if isinstance(uid, User):
            uid = uid.uid

        if uid not in self.user_apis:
            user = self.pyload.db.get_user_data(uid=uid)
            if not user:  # TODO: anonymous user?
                return

            self.user_apis[uid] = UserApi(
                self.pyload, User.from_user_data(self, user))

        return self.user_apis[uid]

    #############################
    #  Auth+User Information
    #############################

    @requireperm(Permission.All)
    def login(self, username, password, remoteip=None):
        """Login into pyLoad, this **must** be called when using rpc before any
        methods can be used.

        :param username:
        :param password:
        :param remoteip: Omit this argument, its only used internal
        :return: bool indicating login was successful

        """
        return True if self.check_auth(username, password, remoteip) else False

    def check_auth(self, username, password, remoteip=None):
        """Check authentication and returns details.

        :param username:
        :param password:
        :param remoteip:
        :return: dict with info, empty when login is incorrect

        """
        self.pyload.log.info(
            self._("User '{0}' tries to log in").format(username))

        return self.pyload.db.check_auth(username, password)

    @staticmethod
    def is_authorized(func, user):
        """Checks if the user is authorized for specific method.

        :param func: function name
        :param user: `User`
        :return: boolean

        """
        if user.is_admin():
            return True
        elif func in perm_map and user.has_permission(perm_map[func]):
            return True
        else:
            return False


class UserApi(Api):
    """Proxy object for api that provides all methods in user context."""

    def __init__(self, core, user):
        # No need to init super class
        self.pyload = core
        self._user = user

    def with_user_context(self, uid):
        raise Exception('Not allowed')

    @property
    def user(self):
        return self._user
