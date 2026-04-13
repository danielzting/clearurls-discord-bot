import urllib.parse
import ipaddress
import socket


class URL(str):


    def __init__(self, url):

        self.url = url

        (
            self.scheme, self.netloc, self.path,
            self.params, self.query, self.fragment
        ) = urllib.parse.urlparse(url)

        # Use urllib.parse for correct IPv6 bracket handling
        parsed = urllib.parse.urlparse(url)
        self.port = parsed.port
        self.netloc = parsed.hostname or self.netloc

        if self.port is None:
            if self.scheme == "http":
                self.port = 80
            elif self.scheme == "https":
                self.port = 443


    def islocal(self) -> bool:

        local_domains = (
            "localhost",
            "localhost.localdomain",
            "ip6-localhost",
            "ip6-loopback"
        )

        # Cloud metadata service hostnames (SSRF targets)
        metadata_domains = (
            "metadata.google.internal",
            "metadata.goog",
            "169.254.169.254",
        )

        hostname = self.netloc

        if hostname in local_domains or hostname in metadata_domains:
            return True

        if hostname.endswith(".internal"):
            return True

        # Check if it's a raw IP address first
        try:
            address = ipaddress.ip_address(hostname)
            return address.is_private or address.is_loopback or address.is_link_local
        except ValueError:
            pass

        # Resolve DNS to check if hostname points to a private IP
        try:
            resolved = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
            for family, stype, proto, canonname, sockaddr in resolved:
                ip = sockaddr[0]
                try:
                    address = ipaddress.ip_address(ip)
                    if address.is_private or address.is_loopback or address.is_link_local:
                        return True
                except ValueError:
                    continue
        except socket.gaierror:
            pass

        return False


    def geturl(self):

        if self.port is not None and self.port not in (80, 443):
            netloc = f"{self.netloc}:{self.port}"
        else:
            netloc = self.netloc

        return urllib.parse.urlunparse((
            self.scheme, netloc, self.path,
            self.params, self.query, self.fragment
        ))


    # https://github.com/psf/requests/blob/2c2138e811487b13020eb331482fb991fd399d4e/requests/utils.py#L903
    def prepend_scheme_if_needed(self):

        (
            scheme, netloc, path,
            params, query, fragment
        ) = urllib.parse.urlparse(self.geturl(), "http")

        if not netloc:
            netloc, path = path, netloc

        return URL(
            urllib.parse.urlunparse((scheme, netloc, path, params, query, fragment)).replace("http:///", "http://")
        )


URL_TYPES = (URL, urllib.parse.ParseResult)
