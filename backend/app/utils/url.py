import ipaddress
import socket
from urllib.parse import urlparse

from fastapi import HTTPException, status


PRIVATE_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def normalize_domain(domain: str) -> str:
    domain = domain.lower().strip().rstrip(".")
    if domain.startswith("www."):
        return domain[4:]
    return domain


def parse_public_url(raw_url: str) -> tuple[str, str]:
    parsed = urlparse(raw_url)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only http and https URLs are allowed")
    if not parsed.hostname:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL must include a hostname")
    domain = normalize_domain(parsed.hostname)
    ensure_public_hostname(domain)
    return raw_url, domain


def ensure_public_hostname(hostname: str) -> None:
    try:
        ip = ipaddress.ip_address(hostname)
        _ensure_public_ip(ip)
        return
    except ValueError:
        pass

    try:
        results = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Hostname cannot be resolved") from exc

    for item in results:
        ip = ipaddress.ip_address(item[4][0])
        _ensure_public_ip(ip)


def _ensure_public_ip(ip: ipaddress._BaseAddress) -> None:
    if ip.is_private or ip.is_loopback or ip.is_link_local or any(ip in network for network in PRIVATE_NETWORKS):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Private or internal addresses are not allowed")


def domain_matches(rule_domain: str, domain: str) -> bool:
    rule = normalize_domain(rule_domain)
    current = normalize_domain(domain)
    return current == rule or current.endswith(f".{rule}")
