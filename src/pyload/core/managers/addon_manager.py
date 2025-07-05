# -*- coding: utf-8 -*-


from functools import wraps
from threading import RLock
from types import MethodType

from _thread import start_new_thread

from ..threads.addon_thread import AddonThread
from ..utils.struct.lock import lock
from .plugin_manager import literal_eval


def try_catch(func):
    @wraps(func)
    def wrapper(self, *args):
        try:
            return func(self, *args)
        except Exception as exc:
            self.pyload.log.error(
                exc, exc_info=self.pyload.debug > 1, stack_info=self.pyload.debug > 2
            )

    return wrapper


class AddonManager:
    """
    Manages addons, delegates and handles Events.

    Every plugin can define events, \
    but some very useful events are called by the Core.
    Contrary to overwriting addon methods you can use event listener,
    which provides additional entry point in the control flow.
    Only do very short tasks or use threads.

    **Known Events:**
    Most addon methods exists as events. These are the additional known events.

    ===================== ============== ==================================
    Name                     Arguments      Description
    ===================== ============== ==================================
    download_preparing     fid            A download was just queued and will be prepared now.
    download_starts        fid            A plugin will immediately start the download afterwards.
    links_added            links, pid     Someone just added links, you are able to modify the links.
    all_downloads_processed                Every link was handled, pyload would idle afterwards.
    all_downloads_finished                 Every download in queue is finished.
    unrar_finished         folder, fname  An Unrar job finished
    config_changed                        The config was changed via the api.
    plugin_config_changed                  The plugin config changed, due to api or internal process.
    ===================== ============== ==================================

    | Notes:
    |    all_downloads_processed is *always* called before all_downloads_finished.
    |    config_changed is *always* called before plugin_config_changed.
    """

    def __init__(self, core):
        self.pyload = core
        self._ = core._

        self.plugins = []
        self.plugin_map = {}
        self.rpc_methods = {}  #: dict of plugin names and list of methods usable by rpc

        self.events = {}  #: contains events

        # registering callback for config event
        self.pyload.config.plugin_cb = MethodType(
            self.dispatch_event, "plugin_config_changed"
        )

        self.add_event("plugin_config_changed", self._config_change_callback)

        self.lock = RLock()
        self.create_index()

    def _config_change_callback(self, plugin_name, config_name, config_value):
        if config_name == "enabled" and config_value:
            self.activate_addon(plugin_name)
        elif config_name == "enabled" and not config_value:
            self.deactivate_addon(plugin_name)

    def _add_module_rpcs(self, plugin_module):
        rpc_methods = getattr(plugin_module, "rpc_methods", [])
        for rpc_method in rpc_methods:
            self.add_rpc(*rpc_method)

    def add_rpc(self, plugin_name, method_name, doc):
        plugin_name = plugin_name.rpartition(".")[2]
        doc = doc.strip() if doc else ""

        if plugin_name in self.rpc_methods:
            if method_name not in self.rpc_methods[plugin_name]:
                self.rpc_methods[plugin_name][method_name] = doc

            else:
                self.pyload.log.error(
                    self._("Cannot expose RPC.. method {}.{}() already exposed").format(plugin_name, method_name),
                    exc_info=self.pyload.debug > 1,
                    stack_info=self.pyload.debug > 2,
                )
        else:
            self.rpc_methods[plugin_name] = {method_name: doc}

    def call_rpc(self, plugin_name, method_name, args, parse):
        if not args:
            args = tuple()
        if parse:
            args = tuple(literal_eval(x) for x in args)

        plugin = self.plugin_map[plugin_name]
        f = getattr(plugin, method_name)
        return f(*args)

    def create_index(self):
        plugins = []

        active = []
        inactive = []

        for plugin_name in self.pyload.plugin_manager.addon_plugins:
            try:
                # addon_class = getattr(plugin, plugin.__name__)

                if self.pyload.config.get_plugin(plugin_name, "enabled"):
                    plugin_module = self.pyload.plugin_manager.load_module(
                        "addon", plugin_name
                    )
                    if not plugin_module:
                        continue
                    plugin_class = getattr(plugin_module, plugin_name)
                    if not plugin_class:
                        continue

                    plugin = plugin_class(self.pyload, self)
                    plugins.append(plugin)
                    self.plugin_map[plugin_name] = plugin
                    active.append(plugin_name)

                    self._add_module_rpcs(plugin_module)

                else:
                    inactive.append(plugin_name)

            except Exception:
                self.pyload.log.warning(
                    self._("Failed activating {}").format(plugin_name),
                    exc_info=self.pyload.debug > 1,
                    stack_info=self.pyload.debug > 2,
                )

        self.pyload.log.info(
            self._("Activated addons: {}").format(", ".join(sorted(active)))
        )
        self.pyload.log.info(
            self._("Deactivate addons: {}").format(", ".join(sorted(inactive)))
        )

        self.plugins = plugins

    def activate_addon(self, plugin_name):

        # check if already loaded
        for inst in self.plugins:
            if inst.__name__ == plugin_name:
                return

        plugin_module = self.pyload.plugin_manager.load_module(
            "addon", plugin_name
        )
        if not plugin_module:
            return
        plugin_class = getattr(plugin_module, plugin_name)
        if not plugin_class:
            return

        self.pyload.log.debug(f"Addon loaded: {plugin_name}")

        plugin = plugin_class(self.pyload, self)
        self.plugins.append(plugin)
        self.plugin_map[plugin_name] = plugin

        self._add_module_rpcs(plugin_module)

        # call core Ready
        start_new_thread(plugin.core_ready, tuple())

    def deactivate_addon(self, plugin_name):
        for inst in self.plugins:
            if inst.__name__ == plugin_name:
                addon = inst
                break
        else:
            return

        self.pyload.log.debug(f"Addon unloaded: {plugin_name}")

        addon.unload()

        # remove periodic call
        res = self.pyload.scheduler.remove_job(addon.cb)
        self.pyload.log.debug(f"Removed callback {res}")

        # remove rpc calls
        try:
            del self.rpc_methods[plugin_name]
        except KeyError:
            pass

        self.plugins.remove(addon)
        del self.plugin_map[addon.__name__]

    @try_catch
    def core_ready(self):
        for plugin in self.plugins:
            if plugin.is_activated():
                plugin.core_ready()

        self.dispatch_event("core_ready")

    @try_catch
    def core_exiting(self):
        for plugin in self.plugins:
            if plugin.is_activated():
                plugin.core_exiting()

        self.dispatch_event("core_exiting")

    @lock
    def download_preparing(self, pyfile):
        for plugin in self.plugins:
            if plugin.is_activated():
                plugin.download_preparing(pyfile)

        self.dispatch_event("download_preparing", pyfile)

    @lock
    def download_finished(self, pyfile):
        for plugin in self.plugins:
            if plugin.is_activated():
                plugin.download_finished(pyfile)

        self.dispatch_event("download_finished", pyfile)

    @lock
    @try_catch
    def download_failed(self, pyfile):
        for plugin in self.plugins:
            if plugin.is_activated():
                plugin.download_failed(pyfile)

        self.dispatch_event("download_failed", pyfile)

    @lock
    def package_finished(self, package):
        for plugin in self.plugins:
            if plugin.is_activated():
                plugin.package_finished(package)

        self.dispatch_event("package_finished", package)

    @lock
    def before_reconnect(self, ip):
        for plugin in self.plugins:
            plugin.before_reconnect(ip)

        self.dispatch_event("before_reconnect", ip)

    @lock
    def after_reconnect(self, ip, old_ip):
        for plugin in self.plugins:
            if plugin.is_activated():
                plugin.after_reconnect(ip, old_ip)

        self.dispatch_event("after_reconnect", old_ip, ip)

    def start_thread(self, function, *args, **kwargs):
        return AddonThread(self.pyload.thread_manager, function, args, kwargs)

    def active_plugins(self):
        """
        returns all active plugins.
        """
        return [x for x in self.plugins if x.is_activated()]

    def get_all_info(self):
        """
        returns info stored by addon plugins.
        """
        info = {}
        for name, plugin in self.plugin_map.items():
            if plugin.info:
                # copy and convert so str
                info[name] = {x: str(y) for x, y in plugin.info.items()}
        return info

    def get_info(self, plugin):
        info = {}
        if plugin in self.plugin_map and self.plugin_map[plugin].info:
            info = {x: str(y) for x, y in self.plugin_map[plugin].info.items()}

        return info

    def add_event(self, event, func):
        """
        Adds an event listener for event name.
        """
        if event in self.events:
            if func not in self.events[event]:
                self.events[event].append(func)
        else:
            self.events[event] = [func]

    def remove_event(self, event, func):
        """
        removes previously added event listener.
        """
        if event in self.events:
            if func in self.events[event]:
                self.events[event].remove(func)

    def dispatch_event(self, event, *args):
        """
        dispatches event with args.
        """
        if event in self.events:
            for f in self.events[event]:
                try:
                    f(*args)
                except Exception as exc:
                    self.pyload.log.warning(
                        self._("Error calling event handler {}: {}, {}, {}").format(
                            event, f, args, exc
                        ),
                        exc_info=self.pyload.debug > 1,
                        stack_info=self.pyload.debug > 2,
                    )
