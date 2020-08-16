# -*- coding: utf-8 -*-

PROPRIETARY_RESPONSES = {
    440: "Login Timeout - The client's session has expired and must log in again.",
    449: "Retry With - The server cannot honour the request because the user has not provided the required information",
    451: "Redirect - Unsupported Redirect Header",
    509: "Bandwidth Limit Exceeded",
    520: "Unknown Error",
    521: "Web Server Is Down - The origin server has refused the connection from CloudFlare",
    522: "Connection Timed Out - CloudFlare could not negotiate a TCP handshake with the origin server",
    523: "Origin Is Unreachable - CloudFlare could not reach the origin server",
    524: "A Timeout Occurred - CloudFlare did not receive a timely HTTP response",
    525: "SSL Handshake Failed - CloudFlare could not negotiate a SSL/TLS handshake with the origin server",
    526: "Invalid SSL Certificate - CloudFlare could not validate the SSL/TLS certificate that the origin server presented",
    527: "Railgun Error - CloudFlare requests timeout or failed after the WAN connection has been established",
    530: "Site Is Frozen - Used by the Pantheon web platform to indicate a site that has been frozen due to inactivity",
}


class BadHeader(Exception):
    def __init__(self, code, header=b"", content=b""):
        int_code = int(code)
        response = responses.get(
            int_code, PROPRIETARY_RESPONSES.get(int_code, "unknown error code")
        )
        super().__init__(f"Bad server response: {code} {response}")
        self.code = int_code
        self.header = header
        self.content = content
