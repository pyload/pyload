# -*- coding: utf-8 -*-

import time
from threading import Lock

from ..utils.old import lock


class CaptchaManager:
    def __init__(self, core):
        self.lock = Lock()
        self.pyload = core
        self._ = core._
        self.tasks = []  #: Task store, for outgoing tasks only

        self.ids = 0  #: Only for internal purpose

    def new_task(self, format, params, result_type):
        task = CaptchaTask(self.ids, format, params, result_type)
        self.ids += 1
        return task

    @lock
    def remove_task(self, task):
        if task in self.tasks:
            self.tasks.remove(task)

    @lock
    def get_task(self):
        for task in self.tasks:
            if task.status in ("waiting", "shared-user"):
                return task
        return None

    @lock
    def get_task_by_id(self, tid):
        for task in self.tasks:
            if task.id == str(tid):  #: Task ids are strings
                return task
        return None

    def handle_captcha(self, task, timeout):
        cli = self.pyload.is_client_connected()

        task.set_waiting(timeout)

        # if cli:  #: Client connected -> should solve the captcha
        #     task.set_waiting(50)  #: Wait minimum 50 sec for response

        for plugin in self.pyload.addon_manager.active_plugins():
            try:
                plugin.new_captcha_task(task)
            except Exception:
                pass

        if task.handler or cli:  #: The captcha was handled
            self.tasks.append(task)
            return True

        task.error = self._("No Client connected for captcha decrypting")

        return False


class CaptchaTask:
    def __init__(self, id, format, params={}, result_type="textual"):
        self.id = str(id)
        self.captcha_params = params
        self.captcha_format = format
        self.captcha_result_type = result_type
        self.handler = []  #: the addon plugins that will take care of the solution
        self.result = None
        self.wait_until = None
        self.error = None  #: error message

        self.status = "init"
        self.data = {}  #: handler can store data here

    def get_captcha(self):
        return self.captcha_params, self.captcha_format, self.captcha_result_type

    def set_result(self, result):
        if self.is_textual() or self.is_interactive():
            self.result = result

        elif self.is_positional():
            try:
                parts = result.split(",")
                self.result = (int(parts[0]), int(parts[1]))
            except Exception:
                self.result = None

    def get_result(self):
        return self.result

    def get_status(self):
        return self.status

    def set_waiting(self, sec):
        """
        let the captcha wait secs for the solution.
        """
        self.wait_until = max(time.time() + sec, self.wait_until)
        self.status = "waiting"

    def is_waiting(self):
        if self.result or self.error or time.time() > self.wait_until:
            return False

        return True

    def is_textual(self):
        """
        returns if text is written on the captcha.
        """
        return self.captcha_result_type == "textual"

    def is_positional(self):
        """
        returns if user have to click a specific region on the captcha.
        """
        return self.captcha_result_type == "positional"

    def is_interactive(self):
        """
        returns if user has to solve the captcha in an interactive iframe.
        """
        return self.captcha_result_type == "interactive"

    def set_wating_for_user(self, exclusive):
        if exclusive:
            self.status = "user"
        else:
            self.status = "shared-user"

    def timed_out(self):
        return time.time() > self.wait_until

    def invalid(self):
        """
        indicates the captcha was not correct.
        """
        [x.captcha_invalid(self) for x in self.handler]

    def correct(self):
        [x.captcha_correct(self) for x in self.handler]

    def __str__(self):
        return f"<CaptchaTask '{self.id}'>"
