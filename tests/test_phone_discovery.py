import ipaddress

from engibench.phone_discovery import _hosts_to_scan


def test_hosts_to_scan_preserves_small_network():
    hosts = _hosts_to_scan(ipaddress.IPv4Network("192.168.7.0/30"))
    assert hosts == ["192.168.7.1", "192.168.7.2"]
