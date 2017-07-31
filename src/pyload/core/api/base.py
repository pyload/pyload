# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from builtins import object

from future import standard_library

standard_library.install_aliases()


# Workaround to let code-completion think, this is subclass of AbstractApi
AbstractApi = object


class BaseApi(AbstractApi):

    def __init__(self, core, user):
        # Only for auto completion, this class can not be instantiated
        from ..init import Core
        from ..datatype.user import User
        assert isinstance(core, Core)
        assert issubclass(BaseApi, AbstractApi)
        self.__pyload = core
        self._ = core._
        assert isinstance(user, User)
        self.user = user
        # No instantiating!
        raise Exception

    @property
    def pyload_core(self):
        return self.__pyload


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

    def shutdown(self):
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
