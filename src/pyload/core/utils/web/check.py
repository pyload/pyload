import ipaddress
import random
import re
import time

from .convert import host_to_ip


_NAT64_WELL_KNOWN = ipaddress.IPv6Network("64:ff9b::/96")
_NAT64_DISCOVERY = ipaddress.IPv6Network("64:ff9b:1::/48")


def is_ipv4_address(value):
    """
    Check whether the provided string is a valid IPv4 address.

    Parameters:
    - value (str): The input string to validate as an IPv4 address.

    Returns:
    - bool: True if the value is a valid IPv4 address, False otherwise.
    """
    try:
        ipaddress.IPv4Address(value)
    except ipaddress.AddressValueError:
        return False
    else:
        return True


def is_ipv6_address(value):
    """
    Check whether the provided string is a valid IPv6 address.

    Parameters:
    - value (str): The input string to validate as an IPv6 address.

    Returns:
    - bool: True if the value is a valid IPv6 address, False otherwise.
    """
    try:
        ipaddress.IPv6Address(value)
    except ipaddress.AddressValueError:
        return False
    else:
        return True


def is_embedded_ipv4(value):
    """Extract an embedded IPv4 address from an IPv6 address, if present.

        This function identifies and returns the embedded IPv4 address from
        common IPv6 transition mechanisms:

        - IPv4-mapped IPv6 addresses (::ffff:0:0/96)
        - 6to4 addresses (2002::/16)
        - NAT64 addresses (well-known prefix 64:ff9b::/96 and discovery prefixes)

        Parameters:
            value (ipaddress.IPv6Address | str): An IPv6 address or string to inspect.

        Returns:
            ipaddress.IPv4Address | None: The embedded IPv4 address if found,
                otherwise None.

        Notes:
            - Returns None for regular IPv6 addresses that do not embed an IPv4 address.
            - For NAT64, it extracts the last 4 bytes of the IPv6 address.
            - This is typically used internally for handling dual-stack or
              IPv4-over-IPv6 scenarios.
        """
    try:
        addr = ipaddress.IPv6Address(value)
    except ipaddress.AddressValueError:
        return None

    if addr.ipv4_mapped is not None:
        return addr.ipv4_mapped
    if addr.sixtofour is not None:  # 2002::/16 6to4
        return addr.sixtofour
    if addr in _NAT64_WELL_KNOWN or addr in _NAT64_DISCOVERY:
        return ipaddress.IPv4Address(addr.packed[-4:])

    return None


def is_ip_address(value):
    """
    Check whether the provided string is a valid IPv4 or IPv6 address.

    Parameters:
    - value (str): The input string to validate as an IP address.

    Returns:
    - bool: True if the value is a valid IPv4 or IPv6 address, False otherwise.
    """
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def is_loopback_address(value):
    """
    Determine whether the provided address or hostname is a loopback address.

    This function supports IPv4, IPv6 and IPv6 transition-encoding forms (IPv4-mapped,
    6to4, NAT64) that wrap an IPv4 loopback. If the input cannot
    be parsed as an IP address, the function treats the string 'localhost'
    as a loopback host.

    Parameters:
    - value (str): The input address or hostname to check.

    Returns:
    - bool: True if the value is a loopback address/hostname, False otherwise.
    """
    try:
        addr = ipaddress.ip_address(value)
    except ValueError:
        return value == "localhost"

    if isinstance(addr, ipaddress.IPv6Address):
        embedded_addr = is_embedded_ipv4(addr)
        if embedded_addr is not None:
            addr = embedded_addr

    return addr.is_loopback


def is_global_address(value):
    """
    Check whether the provided address is a globally routable IP address.

    Parameters:
    - value (str): The input address to check (IPv4 or IPv6).

    Returns:
    - bool: True if the value is a global (publicly routable) IP address,
      False for non-global addresses or if the input is invalid.
    """
    try:
        addr = ipaddress.ip_address(value)
    except ValueError:
        return False

    if isinstance(addr, ipaddress.IPv6Address):
        embedded_addr = is_embedded_ipv4(addr)
        if embedded_addr is not None:
            addr = embedded_addr

    return addr.is_global


def is_global_host(value):
    """
    Check whether the provided host address resolves to a globally routable IP address.

    Parameters:
    - value (str): The input host to check.

    Returns:
    - bool: True if the value is a global (publicly routable) host,
      False for non-global addresses or if the input is invalid.
    """
    ips = host_to_ip(value)
    return ips and all((is_global_address(ip) for ip in ips))


def is_port(value):
    """
    Validate whether an integer is a valid TCP/UDP port number.

    Parameters:
    - value (int): The port number to validate.

    Returns:
    - bool: True if 0 <= value <= 65535, False otherwise.
    """
    return 0 <= value <= 65535


def get_public_address(addr_type="ipv4"):
    """
    Attempt to retrieve the machine's public IPv4 or IPv6 address.

    Returns:
    - str: The public IPv4 or IPv6 address as returned by the external service, or
      an empty string if all attempts fail.
    """
    from ...network.request_factory import get_url
    if addr_type == "ipv4":
        services = [
            ("https://ipv4.icanhazip.com/", r"(\S+)"),
            ("https://checkip.amazonaws.com/", r"(\S+)"),
            ("https://whatismyip.akamai.com/", r"(\S+)"),
            ("http://checkip.dyndns.org/", r".*Current IP Address: (\S+)</body>.*"),
            ("https://api4.ipify.org/", r"(\S+)"),
            ("https://v4.ident.me/", r"(\S+)"),
        ]

    elif addr_type == "ipv6":
        services = [
            ("https://ipv6.icanhazip.com/", r"(\S+)"),
            ("https://api6.ipify.org/", r"(\S+)"),
            ("https://v6.ident.me/", r"(\S+)"),
        ]

    else:
        raise TypeError(f"Unsupported IP address type: {addr_type}")

    ip = ""
    for i in range(10):
        try:
            sv = random.choice(services)
            ip = get_url(sv[0])
            ip = re.match(sv[1], ip).group(1)
            break
        except Exception:
            ip = ""
            time.sleep(0.5)

    return ip
