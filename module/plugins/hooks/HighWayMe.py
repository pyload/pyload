+# -*- coding: utf-8 -*-
+
+from module.common.json_layer import json_loads
+from module.plugins.internal.MultiHook import MultiHook
+
+
+class HighWayMeHook(MultiHook):
+    __name__    = "HighWayMeHook"
+    __type__    = "hook"
+    __version__ = "0.01"
+
+    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
+                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
+                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
+                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
+                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]
+
+    __description__ = """High-Way.Me hook plugin"""
+    __license__     = "GPLv3"
+    __authors__     = [("EvolutionClip", "evolutionclip@live.de")]
+
+
+    def getHosters(self):
+        json_data = self.getURL("https://high-way.me/api.php", get={'hoster': 1})
+        json_data = json_loads(json_data)
+
+        host_list = [element['name'] for element in json_data['hoster']]
+
+        return host_list
