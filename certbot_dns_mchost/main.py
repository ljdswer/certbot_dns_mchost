"""
The certbot Authenticator implementation for McHost.
"""

from typing import Any, Callable

from certbot import errors
from certbot.plugins import dns_common
from typing_extensions import override

from .client import McHostClient


class Authenticator(dns_common.DNSAuthenticator):
    """
    Authenticator class to handle dns-01 challenge for McHost.
    """

    description: str = "Obtain certificates using a DNS TXT record for McHost."

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.credentials: dns_common.CredentialsConfiguration | None = None
        self.client: McHostClient | None = None

    @classmethod
    @override
    def add_parser_arguments(
        cls,
        add: Callable[..., None],
        default_propagation_seconds: int = 30,
    ) -> None:
        super().add_parser_arguments(add, default_propagation_seconds)
        add("credentials", help="McHost credentials INI file.")

    @override
    def more_info(self) -> str:
        return "This plugin configures a DNS TXT record to respond to a dns-01 challenge for the McHost."

    @override
    def _setup_credentials(self) -> None:
        self.credentials = self._configure_credentials(
            "credentials",
            "McHost credendials INI file.",
            {
                "user": "McHost account username",
                "pass": "McHost account password",
            },
        )

    @override
    def _perform(self, domain: str, validation_name: str, validation: str) -> None:
        client = self._get_client()
        client.add_txt_record(domain, validation_name, validation)

    @override
    def _cleanup(self, domain: str, validation_name: str, validation: str) -> None:
        client = self._get_client()
        client.del_txt_record(domain, validation_name, validation)

    def _get_client(self):
        if self.client:
            return self.client

        if not self.credentials:
            raise errors.PluginError(
                "Tried to use the plugin before proper initialization"
            )

        user = self.credentials.conf("user")
        passwd = self.credentials.conf("pass")

        if not user or not passwd:
            raise errors.PluginError("Missing McHost credentials")

        self.client = McHostClient(user, passwd)
        return self.client
