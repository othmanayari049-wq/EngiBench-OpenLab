from __future__ import annotations

import ipaddress
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import psutil

from .phone import PhoneBridgeError, discover_phyphox_buffers


@dataclass(frozen=True, slots=True)
class DiscoveredPhone:
    base_url: str
    title: str
    buffers: tuple[str, ...]


def _candidate_networks() -> list[ipaddress.IPv4Network]:
    """Return private/link-local IPv4 networks on active local interfaces."""
    networks: list[ipaddress.IPv4Network] = []
    seen: set[str] = set()
    stats = psutil.net_if_stats()

    for interface, addresses in psutil.net_if_addrs().items():
        interface_stats = stats.get(interface)
        if interface_stats is not None and not interface_stats.isup:
            continue
        for address in addresses:
            if address.family != socket.AF_INET or not address.address or not address.netmask:
                continue
            try:
                ip = ipaddress.IPv4Address(address.address)
                network = ipaddress.IPv4Network(f"{address.address}/{address.netmask}", strict=False)
            except (ipaddress.AddressValueError, ipaddress.NetmaskValueError):
                continue
            if ip.is_loopback or not (ip.is_private or ip.is_link_local):
                continue
            key = str(network)
            if key not in seen:
                seen.add(key)
                networks.append(network)
    return networks


def _hosts_to_scan(network: ipaddress.IPv4Network, *, max_hosts: int = 512) -> list[str]:
    """Bound discovery work while preserving normal home/campus /24 networks."""
    hosts = list(network.hosts())
    if len(hosts) <= max_hosts:
        return [str(host) for host in hosts]

    # Large campus/VPN networks can contain tens of thousands of addresses. Probe the
    # /24 containing this computer instead of sweeping the entire network.
    local_addresses = {
        address.address
        for addresses in psutil.net_if_addrs().values()
        for address in addresses
        if address.family == socket.AF_INET
    }
    for local in local_addresses:
        try:
            local_ip = ipaddress.IPv4Address(local)
        except ipaddress.AddressValueError:
            continue
        if local_ip in network:
            local_24 = ipaddress.IPv4Network(f"{local}/24", strict=False)
            return [str(host) for host in local_24.hosts()]
    return []


def _probe_phone(host: str, timeout: float) -> DiscoveredPhone | None:
    """Probe the standard phyphox Remote Access ports on one host."""
    for port in (80, 8080):
        base_url = f"http://{host}" if port == 80 else f"http://{host}:{port}"
        request = Request(
            f"{base_url}/config",
            headers={"User-Agent": "EngiBench-OpenLab/0.2.1"},
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                if response.status != 200:
                    continue
                import json

                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, OSError, UnicodeDecodeError, ValueError):
            continue
        if not isinstance(payload, dict):
            continue
        # /config with a phyphox-style experiment definition is the identity check.
        if "buffers" not in payload or not ("title" in payload or "localTitle" in payload):
            continue
        title = str(payload.get("localTitle") or payload.get("title") or "phyphox experiment")
        buffers = tuple(discover_phyphox_buffers(payload))
        return DiscoveredPhone(base_url=base_url, title=title, buffers=buffers)
    return None


def discover_phyphox_phones(
    *,
    timeout_per_probe: float = 0.12,
    max_workers: int = 64,
) -> list[DiscoveredPhone]:
    """Discover phones exposing phyphox Remote Access on the local IPv4 network."""
    networks = _candidate_networks()
    if not networks:
        raise PhoneBridgeError("No usable private local IPv4 network was found on this computer.")

    hosts: list[str] = []
    seen_hosts: set[str] = set()
    for network in networks:
        for host in _hosts_to_scan(network):
            if host not in seen_hosts:
                seen_hosts.add(host)
                hosts.append(host)

    if not hosts:
        raise PhoneBridgeError("No local addresses are available to scan for a phone.")

    found: list[DiscoveredPhone] = []
    with ThreadPoolExecutor(max_workers=min(max_workers, len(hosts))) as executor:
        futures = {executor.submit(_probe_phone, host, timeout_per_probe): host for host in hosts}
        for future in as_completed(futures):
            phone = future.result()
            if phone is not None:
                found.append(phone)

    return sorted(found, key=lambda phone: phone.base_url)
