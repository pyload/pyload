import re
from typing import Dict, Iterator, List, Optional

from ...utils.convert import to_bytes, to_str

RE_HEADERLINE = re.compile(r"^ *(?P<name>[!#$%&'*+-.^_`|~0-9a-zA-Z]+) *: *(?P<value>[^ ]+) *$")

class HttpHeaders:
    """Mutable HTTP/1.1 header collection.

    - Header names are case-insensitive; original casing is preserved for output.
    - Multiple values per header are preserved in insertion order (last one wins for get/indexing).
    - Values are stored as stripped strings.
    """

    def __init__(self):
        self._headers: Dict[str, List[str]] = {}
        self._original_case: Dict[str, str] = {}

    def clear(self, use_defaults=False) -> None:
        """Remove all headers and reset internal state.
        """
        self._headers = {}
        self._original_case = {}

        if use_defaults:
            defaults = [
                ("Accept", "*/*"),
                ("Accept-Language", "en-US,en"),
                ("Accept-Charset", "ISO-8859-1,utf-8;q=0.7,*;q=0.7"),
                ("Connection", "keep-alive"),
                ("Keep-Alive", "300"),
                ("Expect", ""),
            ]
            for name, value in defaults:
                self.add(name, value)

    def add(self, name: str, value: str) -> None:
        """Append a value to a header name without replacing existing ones.

        Parameters:
            name: Header field name (case-insensitive).
            value: Header value; leading/trailing whitespace is stripped.
        """
        key = name.lower()
        if key not in self._headers:
            self._headers[key] = []
            self._original_case[key] = name
        self._headers[key].append(value.strip())

    def remove(self, name: str, value: Optional[str] = None) -> bool:
        """Remove header(s).

        Parameters:
            name: Header field name to remove.
            value: If provided, only remove matching value(s) for the header. If omitted,
                remove the entire header.

        Returns:
            True if any removal occurred; False if the header did not exist or no values matched.
        """
        key = name.lower()
        if key not in self._headers:
            return False

        if value is None:
            # Remove entire header
            del self._headers[key]
            self._original_case.pop(key, None)
            return True
        else:
            # Remove only specific value(s)
            cleaned = [v for v in self._headers[key] if v != value.strip()]
            is_removed = len(cleaned) < len(self._headers[key])

            if not cleaned:
                # Last value removed → delete the header completely
                del self._headers[key]
                del self._original_case.pop[key]
            else:
                self._headers[key] = cleaned

            return is_removed

    def get(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Return the last value for a header or a default if the header is missing.

        Follows the convention that the most recently set value takes precedence.
        """
        values = self.get_list(name)
        return values[-1] if values else default   # last one wins (common convention)

    def set(self, name: str, value: str) -> None:
        """Set a header to a single value, replacing all existing values for the name."""
        key = name.lower()
        self._headers[key] = [value.strip()]
        self._original_case[key] = name

    def keys(self) -> Iterator[str]:
        """Iterate header names using their original case when possible."""
        for norm_key in self._headers:
            yield self._original_case.get(norm_key, norm_key)

    def get_list(self, name: str) -> List[str]:
        """Return all values for a header name, or an empty list if not present."""
        return self._headers.get(name.lower(), [])

    def as_lines(self) -> List[str]:
        """Return headers formatted as a list of "Name: Value" strings in insertion order."""
        lines = []
        for key in self._headers:
            name = self._original_case.get(key, key)
            for value in self._headers[key]:
                lines.append(f"{name}: {value}")

        return lines

    def parse(self, raw_headers: bytes, reset=True) -> None:
        """Parse an HTTP/1.1 header block from raw bytes and load the fields.

        Decoding uses ISO-8859-1 per RFC 7230.

        Parameters:
            raw_headers: Raw header block as bytes.
            reset: If True, the previous headers are cleared

            Bad Formatted lines are ignored!
        """
        if reset:
            self.clear()

        for header_line in to_str(raw_headers, encoding="iso-8859-1").splitlines():
            m = RE_HEADERLINE.match(header_line)
            if m is not None:
                self.add(m.group("name"), m.group("value"))

    def to_wire(self) -> bytes:
        """Serialize headers to a wire-format HTTP/1.1 header block.

        The output is encoded using ISO-8859-1 per RFC 7230.

        Returns:
            Bytes ready to send: b"Name: Value\r\n...\r\n\r\n".
        """
        lines = self.as_lines()
        header_block = "\r\n".join(lines) + "\r\n\r\n"
        return to_bytes(header_block, encoding="iso-8859-1")

    def to_pycurl(self) -> List[bytes]:
        """Serialize headers into a list of bytes lines suitable for pycurl's HTTPHEADER option."""
        lines = self.as_lines()
        return [to_bytes(line, encoding="iso-8859-1") for line in lines]

    def __getitem__(self, name: str) -> str:
        """Dictionary-like access; returns the last value for a header or raises KeyError."""
        values = self.get_list(name)
        if not values:
            raise KeyError(name)
        return values[-1]

    def __setitem__(self, name: str, value: str) -> None:
        """Dictionary-like assignment; replaces all values for the header with a single value."""
        self.set(name, value)  # replace all previous values

    def __contains__(self, key: str) -> bool:
        """Return True if a header name exists (case-insensitive)."""
        return key.lower() in self._headers

    def __bool__(self):
        """Return True if actually has some headers."""
        return bool(self._headers)

    def __str__(self) -> str:
        """Human-readable CRLF-joined header lines (without trailing CRLF)."""
        return "\r\n".join(self.as_lines())

    def __bytes__(self) -> bytes:
        """Alias for to_wire(); returns the serialized header block as bytes."""
        return self.to_wire()
