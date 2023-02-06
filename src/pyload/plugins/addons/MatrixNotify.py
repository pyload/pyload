# -*- coding: utf-8 -*-

from ..base.notifier import Notifier
import json
from urllib.parse import quote as url_encode


class MatrixNotify(Notifier):
    __name__ = "MatrixNotify"
    __type__ = "addon"
    __version__ = "0.1"
    __status__ = "testing"

    __config__ = [
        ("enabled", "bool", "Activated", False),
        ("url", "str", "Server url", ""),
        ("token", "str", "Access Token", ""),
        ("room_id", "str", "Room id", ""),
        ("captcha", "bool", "Notify captcha request", True),
        ("reconnection", "bool", "Notify reconnection request", False),
        ("downloadfinished", "bool", "Notify download finished", True),
        ("downloadfailed", "bool", "Notify download failed", True),
        ("alldownloadsfinished", "bool", "Notify all downloads finished", True),
        ("alldownloadsprocessed", "bool", "Notify all downloads processed", True),
        ("packagefinished", "bool", "Notify package finished", True),
        ("packagefailed", "bool", "Notify package failed", True),
        ("update", "bool", "Notify pyLoad update", False),
        ("exit", "bool", "Notify pyLoad shutdown/restart", False),
        ("sendinterval", "int", "Interval in seconds between notifications", 1),
        ("sendpermin", "int", "Max notifications per minute", 60),
        ("ignoreclient", "bool", "Send notifications if client is connected", True),
    ]

    __description__ = (
        """Send push notifications to a matrix server"""
    )
    __license__ = "GPLv3"
    __authors__ = [
        ("Stefan Bischoff", "stefan.bischoff@lw-rulez.de"),
    ]

    def get_key(self):
        return self.config.get('token')

    def periodical_task(self):
        pass

    def send(self, event, msg, key):
        self.req.put_header('Content-Type', 'application/json;charset=utf-8')
        self.req.put_header('Accept', 'application/json, text/plain, */*')
        message_plain = f"{event}" if msg is None else f"{event}: {msg}"
        message_html = f"<b>{event}</b>" if msg is None else f"<b>{event}</b>: {msg}"
        self.load(
            f"{self.config.get('url')}"
            f"/_matrix/client/r0/rooms/{url_encode(self.config.get('room_id'))}"
            f"/send/m.room.message?access_token={url_encode(self.get_key())}",
            post=json.dumps(
                {
                    "format": "org.matrix.custom.html",
                    'body': message_plain,
                    "formatted_body": message_html,
                    'msgtype': "m.text"
                }
            )
        )
